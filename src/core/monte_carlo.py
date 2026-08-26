"""Monte Carlo Simulation Engine with correlated assets and drawdown analytics."""

from dataclasses import dataclass, field

import numpy as np
import pandas as pd


@dataclass
class SimulationResult:
  initial_value: float
  num_simulations: int
  time_horizon_years: int
  steps_per_year: int
  asset_weights: dict[str, float]
  asset_returns: dict[str, float]
  asset_volatilities: dict[str, float]
  correlation_matrix: pd.DataFrame
  portfolio_expected_annual_return: float
  portfolio_expected_annual_volatility: float
  # Trajectories: shape (num_simulations, total_steps + 1)
  trajectories: np.ndarray
  # Final values summary
  final_values: np.ndarray
  # Max drawdown per simulation path: shape (num_simulations,)
  max_drawdowns: np.ndarray
  percentiles: dict[str, float] = field(default_factory=dict)
  summary_metrics: dict[str, float] = field(default_factory=dict)
  horizon_loss_probabilities: dict[str, float] = field(default_factory=dict)


class MonteCarloEngine:
  """Multivariate Geometric Brownian Motion (GBM) Monte Carlo simulator."""

  def __init__(
    self,
    initial_value: float,
    asset_weights: dict[str, float],
    returns_df: pd.DataFrame | None = None,
    custom_asset_returns: dict[str, float] | None = None,
    custom_asset_volatilities: dict[str, float] | None = None,
    custom_correlation_matrix: pd.DataFrame | None = None,
    periods_per_year: int = 252,
    seed: int | None = 42,
  ):
    """Initialize MonteCarloEngine.

    :param initial_value: Initial total portfolio value (e.g. in USD)
    :param asset_weights: Mapping of ticker/asset -> target weight (must sum to ~1.0)
    :param returns_df: Historical daily or periodic returns DataFrame for the assets
    :param custom_asset_returns: Optional explicit annualized expected returns per asset
    :param custom_asset_volatilities: Optional explicit annualized volatilities per asset
    :param custom_correlation_matrix: Optional explicit empirical correlation matrix
    :param periods_per_year: Number of periods in a year (default 252 for daily trading)
    :param seed: Random seed for reproducibility
    """
    self.initial_value = float(initial_value)
    self.asset_weights = asset_weights
    self.periods_per_year = periods_per_year
    self.seed = seed

    # Validate assets
    self.assets = list(asset_weights.keys())
    self.weights_arr = np.array([asset_weights[a] for a in self.assets], dtype=float)
    if not np.isclose(np.sum(self.weights_arr), 1.0, atol=1e-3):
      raise ValueError(f"Asset weights must sum to 1.0, got {np.sum(self.weights_arr)}")

    if custom_asset_returns is not None and custom_asset_volatilities is not None:
      # Use explicit parameters
      self.ann_returns_arr = np.array([custom_asset_returns[a] for a in self.assets], dtype=float)
      self.ann_vol_arr = np.array([custom_asset_volatilities[a] for a in self.assets], dtype=float)
      if custom_correlation_matrix is not None:
        self.corr_matrix = custom_correlation_matrix.loc[self.assets, self.assets]
      elif returns_df is not None:
        self.corr_matrix = returns_df[self.assets].dropna().corr()
      else:
        self.corr_matrix = pd.DataFrame(
          np.eye(len(self.assets)), index=self.assets, columns=self.assets
        )
      # Build covariance matrix
      vol_outer = np.outer(self.ann_vol_arr, self.ann_vol_arr)
      self.ann_cov_matrix = vol_outer * self.corr_matrix.values
    else:
      if returns_df is None:
        raise ValueError(
          "Either returns_df or (custom_asset_returns and custom_asset_volatilities) must be provided."
        )
      for a in self.assets:
        if a not in returns_df.columns:
          raise ValueError(f"Asset '{a}' not found in historical returns DataFrame.")
      self.clean_returns = returns_df[self.assets].dropna()
      self.mean_periodic_returns = self.clean_returns.mean().values
      self.periodic_cov_matrix = self.clean_returns.cov().values
      self.corr_matrix = self.clean_returns.corr()

      self.ann_returns_arr = self.mean_periodic_returns * self.periods_per_year
      self.ann_cov_matrix = self.periodic_cov_matrix * self.periods_per_year
      self.ann_vol_arr = np.sqrt(np.diag(self.ann_cov_matrix))

    self.portfolio_ann_return = float(np.dot(self.weights_arr, self.ann_returns_arr))
    self.portfolio_ann_vol = float(
      np.sqrt(np.dot(self.weights_arr.T, np.dot(self.ann_cov_matrix, self.weights_arr)))
    )

  def simulate_portfolio_gbm(
    self,
    num_simulations: int = 1000,
    time_horizon_years: int = 30,
    steps_per_year: int = 252,
    rebalance_frequency_steps: int = 252,
  ) -> SimulationResult:
    """Simulate multivariate asset prices under correlated GBM with periodic rebalancing.

    :param num_simulations: Number of simulation paths (e.g. 1000)
    :param time_horizon_years: Number of years to simulate (e.g. 30)
    :param steps_per_year: Steps per year (default 252)
    :param rebalance_frequency_steps: Steps between rebalancings (default 252 for annual rebalancing)
    """
    if self.seed is not None:
      np.random.seed(self.seed)

    total_steps = int(time_horizon_years * steps_per_year)
    dt = 1.0 / steps_per_year
    n_assets = len(self.assets)

    # Annualized drift (mu) and diffusion (sigma) per asset
    mu = self.ann_returns_arr
    sigma = self.ann_vol_arr

    # Cholesky of correlation matrix to generate correlated standard normals
    R = self.corr_matrix.values
    L_corr = np.linalg.cholesky(R)

    # Storage for portfolio paths: shape (num_simulations, total_steps + 1)
    trajectories = np.zeros((num_simulations, total_steps + 1))
    trajectories[:, 0] = self.initial_value

    for sim_idx in range(num_simulations):
      # Current dollar holdings in each asset
      current_holdings = self.initial_value * self.weights_arr.copy()

      for step in range(1, total_steps + 1):
        # Generate correlated standard normal shocks
        z_uncorr = np.random.standard_normal(n_assets)
        z_corr = np.dot(L_corr, z_uncorr)

        # Asset returns over dt via GBM: S_{t+dt} = S_t * exp((mu - 0.5 * sigma^2)*dt + sigma*sqrt(dt)*z)
        growth_factors = np.exp((mu - 0.5 * (sigma**2)) * dt + sigma * np.sqrt(dt) * z_corr)
        current_holdings = current_holdings * growth_factors

        # Periodic rebalancing if specified
        if (
          rebalance_frequency_steps > 0
          and step % rebalance_frequency_steps == 0
          and step < total_steps
        ):
          total_val = np.sum(current_holdings)
          current_holdings = total_val * self.weights_arr.copy()

        trajectories[sim_idx, step] = np.sum(current_holdings)

    final_values = trajectories[:, -1]

    # Calculate Max Drawdown for each path: max((peak - val) / peak)
    running_max = np.maximum.accumulate(trajectories, axis=1)
    drawdowns = (running_max - trajectories) / running_max
    max_drawdowns = np.max(drawdowns, axis=1)

    # Calculate horizon-specific loss probabilities (e.g., Year 1, 3, 5, 10, 20, 30)
    check_years = [1, 3, 5, 10, 15, 20, 25, 30]
    horizon_loss_probabilities = {}
    for y in check_years:
      if y <= time_horizon_years:
        step_idx = int(y * steps_per_year)
        val_at_y = trajectories[:, step_idx]
        loss_prob = float(np.mean(val_at_y < self.initial_value))
        horizon_loss_probabilities[f"year_{y}"] = loss_prob

    # Metrics
    percentiles = {
      "p5": float(np.percentile(final_values, 5)),
      "p10": float(np.percentile(final_values, 10)),
      "p25": float(np.percentile(final_values, 25)),
      "p50": float(np.percentile(final_values, 50)),
      "p75": float(np.percentile(final_values, 75)),
      "p90": float(np.percentile(final_values, 90)),
      "p95": float(np.percentile(final_values, 95)),
    }

    cagr_list = (final_values / self.initial_value) ** (1.0 / time_horizon_years) - 1.0

    summary_metrics = {
      "mean_final_value": float(np.mean(final_values)),
      "median_final_value": float(np.median(final_values)),
      "min_final_value": float(np.min(final_values)),
      "max_final_value": float(np.max(final_values)),
      "std_final_value": float(np.std(final_values)),
      "mean_cagr": float(np.mean(cagr_list)),
      "median_cagr": float(np.median(cagr_list)),
      "min_cagr": float(np.min(cagr_list)),
      "max_cagr": float(np.max(cagr_list)),
      "probability_of_loss": float(np.mean(final_values < self.initial_value)),
      "mean_max_drawdown": float(np.mean(max_drawdowns)),
      "median_max_drawdown": float(np.median(max_drawdowns)),
      "worst_max_drawdown": float(np.max(max_drawdowns)),
    }

    return SimulationResult(
      initial_value=self.initial_value,
      num_simulations=num_simulations,
      time_horizon_years=time_horizon_years,
      steps_per_year=steps_per_year,
      asset_weights=self.asset_weights,
      asset_returns={a: float(r) for a, r in zip(self.assets, self.ann_returns_arr, strict=False)},
      asset_volatilities={a: float(v) for a, v in zip(self.assets, self.ann_vol_arr, strict=False)},
      correlation_matrix=self.corr_matrix,
      portfolio_expected_annual_return=self.portfolio_ann_return,
      portfolio_expected_annual_volatility=self.portfolio_ann_vol,
      trajectories=trajectories,
      final_values=final_values,
      max_drawdowns=max_drawdowns,
      percentiles=percentiles,
      summary_metrics=summary_metrics,
      horizon_loss_probabilities=horizon_loss_probabilities,
    )
