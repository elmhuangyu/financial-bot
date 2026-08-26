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
  horizon_cvar_95: dict[str, float] = field(default_factory=dict)


class MonteCarloEngine:
  """Multivariate Geometric Brownian Motion (GBM) Monte Carlo simulator supporting fat-tail Student's t and regime switching."""

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
    distribution: str = "gbm",
    degrees_of_freedom: float = 5.0,
    regime_p_calm_to_calm: float = 0.96,
    regime_p_crisis_to_crisis: float = 0.80,
    regime_crisis_vol_multiplier: float = 2.0,
    regime_crisis_return_shift: float = -0.15,
  ) -> SimulationResult:
    """Simulate multivariate asset prices under correlated GBM with periodic rebalancing and optional fat tails.

    :param num_simulations: Number of simulation paths (e.g. 1000)
    :param time_horizon_years: Number of years to simulate (e.g. 30)
    :param steps_per_year: Steps per year (default 252)
    :param rebalance_frequency_steps: Steps between rebalancings (default 252 for annual rebalancing)
    :param distribution: Random shock distribution ('gbm' for Gaussian, 't_student' for fat-tail t, 'regime_switching' for 2-state Markov)
    :param degrees_of_freedom: Degrees of freedom nu for Student's t distribution (default 5.0, lower means fatter tails)
    :param regime_p_calm_to_calm: Probability of remaining in calm state (default 0.96)
    :param regime_p_crisis_to_crisis: Probability of remaining in crisis state (default 0.80)
    :param regime_crisis_vol_multiplier: Volatility multiplier during crisis regime (default 2.0)
    :param regime_crisis_return_shift: Annualized drift reduction during crisis regime (default -0.15)
    """
    if self.seed is not None:
      np.random.seed(self.seed)

    total_steps = int(time_horizon_years * steps_per_year)
    dt = 1.0 / steps_per_year
    n_assets = len(self.assets)

    # Base annualized drift (mu) and diffusion (sigma) per asset
    mu_base = self.ann_returns_arr
    sigma_base = self.ann_vol_arr

    # Cholesky of correlation matrix to generate correlated standard normals
    R = self.corr_matrix.values
    L_corr = np.linalg.cholesky(R)

    # Storage for portfolio paths: shape (num_simulations, total_steps + 1)
    trajectories = np.zeros((num_simulations, total_steps + 1))
    trajectories[:, 0] = self.initial_value

    for sim_idx in range(num_simulations):
      # Current dollar holdings in each asset
      current_holdings = self.initial_value * self.weights_arr.copy()
      regime_state = 0  # 0: Calm, 1: Crisis

      for step in range(1, total_steps + 1):
        # Determine regime if regime switching
        if distribution == "regime_switching":
          if regime_state == 0:
            regime_state = 0 if np.random.rand() < regime_p_calm_to_calm else 1
          else:
            regime_state = 1 if np.random.rand() < regime_p_crisis_to_crisis else 0

          if regime_state == 1:
            mu = mu_base + regime_crisis_return_shift
            sigma = sigma_base * regime_crisis_vol_multiplier
          else:
            mu = mu_base
            sigma = sigma_base
        else:
          mu = mu_base
          sigma = sigma_base

        # Generate correlated shocks
        z_uncorr = np.random.standard_normal(n_assets)
        z_corr = np.dot(L_corr, z_uncorr)

        if distribution == "t_student":
          # Multivariate Student's t shock: scale by normalized chi-square variable
          # Scaled so that Var(shock) = 1.0 (preserving calibrated annualized volatility while injecting pure excess kurtosis)
          nu = max(degrees_of_freedom, 2.01)
          w = np.random.chisquare(nu)
          t_scale = np.sqrt((nu - 2.0) / w)
          z_corr = z_corr * t_scale

        # Asset returns over dt via SDE: S_{t+dt} = S_t * exp((mu - 0.5 * sigma^2)*dt + sigma*sqrt(dt)*z)
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

    # Calculate horizon-specific loss probabilities and CVaR_95
    check_years = [1, 2, 3, 5, 7, 10, 15, 20, 25, 30]
    horizon_loss_probabilities = {}
    horizon_cvar_95 = {}
    for y in check_years:
      if y <= time_horizon_years:
        step_idx = int(y * steps_per_year)
        val_at_y = trajectories[:, step_idx]
        loss_prob = float(np.mean(val_at_y < self.initial_value))
        horizon_loss_probabilities[f"year_{y}"] = loss_prob

        # CVaR at 95% (Expected Shortfall: average value of bottom 5% tail)
        p5_cutoff = np.percentile(val_at_y, 5)
        tail_vals = val_at_y[val_at_y <= p5_cutoff]
        cvar_val = float(np.mean(tail_vals)) if len(tail_vals) > 0 else float(p5_cutoff)
        horizon_cvar_95[f"year_{y}"] = cvar_val

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

    # 30-Year Terminal CVaR_95
    terminal_p5 = percentiles["p5"]
    terminal_tail = final_values[final_values <= terminal_p5]
    cvar_95_final = float(np.mean(terminal_tail)) if len(terminal_tail) > 0 else float(terminal_p5)

    # Skewness and Kurtosis of terminal values
    final_std = float(np.std(final_values))
    final_mean = float(np.mean(final_values))
    skewness = (
      float(np.mean(((final_values - final_mean) / (final_std + 1e-9)) ** 3))
      if final_std > 0
      else 0.0
    )
    excess_kurtosis = (
      float(np.mean(((final_values - final_mean) / (final_std + 1e-9)) ** 4)) - 3.0
      if final_std > 0
      else 0.0
    )

    summary_metrics = {
      "mean_final_value": final_mean,
      "median_final_value": float(np.median(final_values)),
      "min_final_value": float(np.min(final_values)),
      "max_final_value": float(np.max(final_values)),
      "std_final_value": final_std,
      "cvar_95_final_value": cvar_95_final,
      "cvar_95_cagr": float(
        (cvar_95_final / self.initial_value) ** (1.0 / time_horizon_years) - 1.0
      ),
      "mean_cagr": float(np.mean(cagr_list)),
      "median_cagr": float(np.median(cagr_list)),
      "min_cagr": float(np.min(cagr_list)),
      "max_cagr": float(np.max(cagr_list)),
      "probability_of_loss": float(np.mean(final_values < self.initial_value)),
      "mean_max_drawdown": float(np.mean(max_drawdowns)),
      "median_max_drawdown": float(np.median(max_drawdowns)),
      "worst_max_drawdown": float(np.max(max_drawdowns)),
      "terminal_skewness": skewness,
      "terminal_excess_kurtosis": excess_kurtosis,
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
      horizon_cvar_95=horizon_cvar_95,
    )
