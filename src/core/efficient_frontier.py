"""Markowitz Efficient Frontier & Mean-Variance Optimization Engine."""

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy.optimize import minimize


@dataclass
class PortfolioStats:
  """Statistics for an individual asset portfolio allocation."""

  expected_return: float
  volatility: float
  sharpe_ratio: float
  weights: dict[str, float]


@dataclass
class FrontierPoint:
  """A discrete optimal point along the Efficient Frontier curve."""

  expected_return: float
  volatility: float
  sharpe_ratio: float
  weights: dict[str, float]


@dataclass
class EfficientFrontierResult:
  """Complete result set from an Efficient Frontier analysis."""

  assets: list[str]
  asset_returns: dict[str, float]
  asset_volatilities: dict[str, float]
  correlation_matrix: pd.DataFrame
  covariance_matrix: pd.DataFrame
  risk_free_rate: float
  min_variance_portfolio: PortfolioStats
  max_sharpe_portfolio: PortfolioStats
  frontier_points: list[FrontierPoint]
  current_portfolio: PortfolioStats | None = None
  capital_allocation_line: list[dict[str, float]] = field(default_factory=list)
  efficiency_gap: dict[str, float] = field(default_factory=dict)
  random_portfolios: pd.DataFrame | None = None


class EfficientFrontierEngine:
  """Modern Portfolio Theory (MPT) Markowitz Efficient Frontier Engine.

  Supports:
  - Global Minimum Variance (GMV) portfolio optimization
  - Maximum Sharpe Ratio (Tangency) portfolio optimization
  - Target Return minimum-variance optimization
  - Target Volatility maximum-return optimization
  - Full Efficient Frontier curve tracing
  - Custom upper/lower weight bounds per asset
  - Efficiency gap benchmarking against current allocations
  """

  def __init__(
    self,
    assets: list[str] | None = None,
    returns_df: pd.DataFrame | None = None,
    custom_asset_returns: dict[str, float] | None = None,
    custom_asset_volatilities: dict[str, float] | None = None,
    custom_correlation_matrix: pd.DataFrame | None = None,
    custom_covariance_matrix: pd.DataFrame | None = None,
    risk_free_rate: float = 0.035,
    periods_per_year: int = 252,
    weight_bounds: tuple[float, float] | dict[str, tuple[float, float]] = (0.0, 1.0),
  ):
    """Initialize EfficientFrontierEngine.

    :param assets: List of ticker / asset identifiers
    :param returns_df: Historical daily or periodic returns DataFrame
    :param custom_asset_returns: Explicit annualized expected returns per asset
    :param custom_asset_volatilities: Explicit annualized volatilities per asset
    :param custom_correlation_matrix: Explicit empirical correlation matrix
    :param custom_covariance_matrix: Optional explicit annualized covariance matrix
    :param risk_free_rate: Annualized risk-free rate for Sharpe ratio calculation (e.g. 0.035 for 3.5%)
    :param periods_per_year: Periods per year (default 252)
    :param weight_bounds: Default (min_weight, max_weight) for all assets or dict mapping asset -> (min, max)
    """
    self.risk_free_rate = float(risk_free_rate)
    self.periods_per_year = periods_per_year

    if custom_asset_returns is not None and custom_asset_volatilities is not None:
      self.assets = list(custom_asset_returns.keys()) if assets is None else list(assets)
      self.ann_returns_arr = np.array([custom_asset_returns[a] for a in self.assets], dtype=float)
      self.ann_vol_arr = np.array([custom_asset_volatilities[a] for a in self.assets], dtype=float)

      if custom_covariance_matrix is not None:
        self.ann_cov_matrix = custom_covariance_matrix.loc[self.assets, self.assets].values
        # Compute correlation from cov
        vol_outer = np.outer(self.ann_vol_arr, self.ann_vol_arr)
        corr_vals = np.clip(self.ann_cov_matrix / (vol_outer + 1e-12), -1.0, 1.0)
        np.fill_diagonal(corr_vals, 1.0)
        self.corr_matrix = pd.DataFrame(corr_vals, index=self.assets, columns=self.assets)
      elif custom_correlation_matrix is not None:
        self.corr_matrix = custom_correlation_matrix.loc[self.assets, self.assets]
        vol_outer = np.outer(self.ann_vol_arr, self.ann_vol_arr)
        self.ann_cov_matrix = vol_outer * self.corr_matrix.values
      elif returns_df is not None:
        self.corr_matrix = returns_df[self.assets].dropna().corr()
        vol_outer = np.outer(self.ann_vol_arr, self.ann_vol_arr)
        self.ann_cov_matrix = vol_outer * self.corr_matrix.values
      else:
        self.corr_matrix = pd.DataFrame(
          np.eye(len(self.assets)), index=self.assets, columns=self.assets
        )
        vol_outer = np.outer(self.ann_vol_arr, self.ann_vol_arr)
        self.ann_cov_matrix = vol_outer * self.corr_matrix.values

    elif returns_df is not None:
      self.assets = list(returns_df.columns) if assets is None else list(assets)
      clean_returns = returns_df[self.assets].dropna()
      mean_periodic = clean_returns.mean().values
      periodic_cov = clean_returns.cov().values

      self.ann_returns_arr = mean_periodic * self.periods_per_year
      self.ann_cov_matrix = periodic_cov * self.periods_per_year
      self.ann_vol_arr = np.sqrt(np.diag(self.ann_cov_matrix))
      self.corr_matrix = clean_returns.corr()
    else:
      raise ValueError(
        "Must provide either returns_df or (custom_asset_returns and custom_asset_volatilities)."
      )

    self.num_assets = len(self.assets)
    if self.num_assets < 2:
      raise ValueError("Markowitz optimization requires at least 2 assets.")

    # Configure bounds per asset
    if isinstance(weight_bounds, dict):
      self.bounds = [weight_bounds.get(a, (0.0, 1.0)) for a in self.assets]
    else:
      self.bounds = [weight_bounds for _ in range(self.num_assets)]

    self.cov_df = pd.DataFrame(self.ann_cov_matrix, index=self.assets, columns=self.assets)

  def portfolio_return(self, weights: np.ndarray) -> float:
    """Calculate annualized expected portfolio return."""
    return float(np.dot(weights, self.ann_returns_arr))

  def portfolio_volatility(self, weights: np.ndarray) -> float:
    """Calculate annualized portfolio volatility."""
    var = float(np.dot(weights.T, np.dot(self.ann_cov_matrix, weights)))
    return float(np.sqrt(max(var, 0.0)))

  def portfolio_sharpe(self, weights: np.ndarray) -> float:
    """Calculate annualized Sharpe ratio."""
    vol = self.portfolio_volatility(weights)
    if vol <= 1e-8:
      return 0.0
    return float((self.portfolio_return(weights) - self.risk_free_rate) / vol)

  def evaluate_weights(self, weights_dict: dict[str, float]) -> PortfolioStats:
    """Compute performance stats for an explicit weight dictionary."""
    weights_arr = np.array([weights_dict.get(a, 0.0) for a in self.assets], dtype=float)
    total_w = np.sum(weights_arr)
    if not np.isclose(total_w, 1.0, atol=1e-3) and total_w > 0:
      weights_arr = weights_arr / total_w
    ret = self.portfolio_return(weights_arr)
    vol = self.portfolio_volatility(weights_arr)
    sr = (ret - self.risk_free_rate) / vol if vol > 1e-8 else 0.0
    normalized_dict = {a: float(w) for a, w in zip(self.assets, weights_arr, strict=False)}
    return PortfolioStats(
      expected_return=ret,
      volatility=vol,
      sharpe_ratio=sr,
      weights=normalized_dict,
    )

  def _get_initial_guesses(self) -> list[np.ndarray]:
    """Generate diverse initial guesses to ensure global convergence."""
    guesses = []
    # 1. Equal weight
    guesses.append(np.ones(self.num_assets) / self.num_assets)
    # 2. Inverse volatility
    inv_vol = 1.0 / (self.ann_vol_arr + 1e-8)
    guesses.append(inv_vol / np.sum(inv_vol))
    # 3. Concentrated single assets
    for i in range(self.num_assets):
      w = np.zeros(self.num_assets)
      w[i] = 1.0
      guesses.append(w)
    return guesses

  def optimize_min_variance(self) -> PortfolioStats:
    """Find the Global Minimum Variance (GMV) portfolio."""

    def objective(w: np.ndarray) -> float:
      return np.dot(w.T, np.dot(self.ann_cov_matrix, w))

    constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1.0}]

    best_res = None
    best_val = float("inf")

    for x0 in self._get_initial_guesses():
      res = minimize(
        objective,
        x0=x0,
        method="SLSQP",
        bounds=self.bounds,
        constraints=constraints,
        options={"ftol": 1e-12, "maxiter": 1000},
      )
      if res.success and res.fun < best_val:
        best_val = res.fun
        best_res = res

    if best_res is None or not best_res.success:
      x0 = np.ones(self.num_assets) / self.num_assets
      best_res = minimize(
        objective, x0=x0, method="SLSQP", bounds=self.bounds, constraints=constraints
      )

    w_opt = best_res.x
    w_opt = np.clip(w_opt, 0.0, 1.0)
    w_opt = w_opt / np.sum(w_opt)

    ret = self.portfolio_return(w_opt)
    vol = self.portfolio_volatility(w_opt)
    sr = (ret - self.risk_free_rate) / vol if vol > 1e-8 else 0.0
    w_dict = {a: float(w) for a, w in zip(self.assets, w_opt, strict=False)}

    return PortfolioStats(
      expected_return=ret,
      volatility=vol,
      sharpe_ratio=sr,
      weights=w_dict,
    )

  def optimize_max_sharpe(self) -> PortfolioStats:
    """Find the Maximum Sharpe Ratio (Tangency) portfolio."""

    def objective(w: np.ndarray) -> float:
      vol = np.sqrt(np.dot(w.T, np.dot(self.ann_cov_matrix, w)))
      if vol <= 1e-8:
        return 0.0
      ret = np.dot(w, self.ann_returns_arr)
      # Negative Sharpe for minimization
      return -(ret - self.risk_free_rate) / vol

    constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1.0}]

    best_res = None
    best_sr = -float("inf")

    for x0 in self._get_initial_guesses():
      res = minimize(
        objective,
        x0=x0,
        method="SLSQP",
        bounds=self.bounds,
        constraints=constraints,
        options={"ftol": 1e-12, "maxiter": 1000},
      )
      if res.success and -res.fun > best_sr:
        best_sr = -res.fun
        best_res = res

    if best_res is None or not best_res.success:
      x0 = np.ones(self.num_assets) / self.num_assets
      best_res = minimize(
        objective, x0=x0, method="SLSQP", bounds=self.bounds, constraints=constraints
      )

    w_opt = best_res.x
    w_opt = np.clip(w_opt, 0.0, 1.0)
    w_opt = w_opt / np.sum(w_opt)

    ret = self.portfolio_return(w_opt)
    vol = self.portfolio_volatility(w_opt)
    sr = (ret - self.risk_free_rate) / vol if vol > 1e-8 else 0.0
    w_dict = {a: float(w) for a, w in zip(self.assets, w_opt, strict=False)}

    return PortfolioStats(
      expected_return=ret,
      volatility=vol,
      sharpe_ratio=sr,
      weights=w_dict,
    )

  def optimize_target_return(self, target_return: float) -> PortfolioStats | None:
    """Find minimum variance portfolio that achieves a given target return."""

    def objective(w: np.ndarray) -> float:
      return np.dot(w.T, np.dot(self.ann_cov_matrix, w))

    constraints = [
      {"type": "eq", "fun": lambda w: np.sum(w) - 1.0},
      {"type": "eq", "fun": lambda w: np.dot(w, self.ann_returns_arr) - target_return},
    ]

    best_res = None
    best_val = float("inf")

    for x0 in self._get_initial_guesses():
      res = minimize(
        objective,
        x0=x0,
        method="SLSQP",
        bounds=self.bounds,
        constraints=constraints,
        options={"ftol": 1e-12, "maxiter": 1000},
      )
      if res.success and res.fun < best_val:
        best_val = res.fun
        best_res = res

    if best_res is None or not best_res.success:
      return None

    w_opt = best_res.x
    w_opt = np.clip(w_opt, 0.0, 1.0)
    w_opt = w_opt / np.sum(w_opt)

    ret = self.portfolio_return(w_opt)
    vol = self.portfolio_volatility(w_opt)
    sr = (ret - self.risk_free_rate) / vol if vol > 1e-8 else 0.0
    w_dict = {a: float(w) for a, w in zip(self.assets, w_opt, strict=False)}

    return PortfolioStats(
      expected_return=ret,
      volatility=vol,
      sharpe_ratio=sr,
      weights=w_dict,
    )

  def optimize_target_volatility(self, target_volatility: float) -> PortfolioStats | None:
    """Find maximum expected return portfolio subject to a target volatility ceiling."""

    def objective(w: np.ndarray) -> float:
      return -float(np.dot(w, self.ann_returns_arr))

    constraints = [
      {"type": "eq", "fun": lambda w: np.sum(w) - 1.0},
      {
        "type": "ineq",
        "fun": lambda w: target_volatility**2 - float(np.dot(w.T, np.dot(self.ann_cov_matrix, w))),
      },
    ]

    best_res = None
    best_ret = -float("inf")

    for x0 in self._get_initial_guesses():
      res = minimize(
        objective,
        x0=x0,
        method="SLSQP",
        bounds=self.bounds,
        constraints=constraints,
        options={"ftol": 1e-12, "maxiter": 1000},
      )
      if res.success and -res.fun > best_ret:
        best_ret = -res.fun
        best_res = res

    if best_res is None or not best_res.success:
      return None

    w_opt = best_res.x
    w_opt = np.clip(w_opt, 0.0, 1.0)
    w_opt = w_opt / np.sum(w_opt)

    ret = self.portfolio_return(w_opt)
    vol = self.portfolio_volatility(w_opt)
    sr = (ret - self.risk_free_rate) / vol if vol > 1e-8 else 0.0
    w_dict = {a: float(w) for a, w in zip(self.assets, w_opt, strict=False)}

    return PortfolioStats(
      expected_return=ret,
      volatility=vol,
      sharpe_ratio=sr,
      weights=w_dict,
    )

  def calculate_efficient_frontier(
    self,
    num_points: int = 50,
    current_weights: dict[str, float] | None = None,
    include_random_portfolios: int = 0,
    seed: int | None = 42,
    grid_mode: str = "volatility",
  ) -> EfficientFrontierResult:
    """Compute the continuous Markowitz Efficient Frontier curve.

    :param num_points: Number of discrete optimal frontier points to calculate
    :param current_weights: User's current asset allocation weights for benchmark comparison
    :param include_random_portfolios: Number of random portfolios to generate for distribution cloud
    :param seed: Random seed for portfolio generation
    :param grid_mode: 'volatility' for uniform risk spacing (ideal for charts) or 'return' for uniform return spacing
    """
    gmv = self.optimize_min_variance()
    max_sharpe = self.optimize_max_sharpe()

    frontier_points: list[FrontierPoint] = []

    if grid_mode == "volatility":
      min_vol = gmv.volatility
      max_vol = float(np.max(self.ann_vol_arr))
      target_vols = np.linspace(min_vol, max_vol, num_points)
      for vol_target in target_vols:
        pt = self.optimize_target_volatility(vol_target)
        if pt is not None:
          frontier_points.append(
            FrontierPoint(
              expected_return=pt.expected_return,
              volatility=pt.volatility,
              sharpe_ratio=pt.sharpe_ratio,
              weights=pt.weights,
            )
          )
    else:
      # Return grid mode
      max_possible_return = float(np.max(self.ann_returns_arr))
      min_frontier_return = gmv.expected_return
      target_returns = np.linspace(min_frontier_return, max_possible_return, num_points)
      for ret_target in target_returns:
        pt = self.optimize_target_return(ret_target)
        if pt is not None:
          frontier_points.append(
            FrontierPoint(
              expected_return=pt.expected_return,
              volatility=pt.volatility,
              sharpe_ratio=pt.sharpe_ratio,
              weights=pt.weights,
            )
          )

    # Sort frontier points by volatility ascending
    frontier_points.sort(key=lambda p: p.volatility)

    # Capital Allocation Line (CAL) from (0, rf) through Max Sharpe
    cal_points = []
    max_vol_limit = max(p.volatility for p in frontier_points) * 1.2 if frontier_points else 0.5
    cal_vols = np.linspace(0.0, max_vol_limit, 20)
    for v in cal_vols:
      cal_ret = self.risk_free_rate + max_sharpe.sharpe_ratio * v
      cal_points.append({"volatility": float(v), "expected_return": float(cal_ret)})

    # Current Portfolio Evaluation & Efficiency Gap Analysis
    current_port_stats = None
    efficiency_gap: dict[str, float] = {}
    if current_weights is not None:
      current_port_stats = self.evaluate_weights(current_weights)

      # 1. Return enhancement at same risk level
      same_vol_opt = self.optimize_target_volatility(current_port_stats.volatility)
      if same_vol_opt is not None:
        efficiency_gap["optimal_return_at_current_vol"] = same_vol_opt.expected_return
        efficiency_gap["return_gap"] = (
          same_vol_opt.expected_return - current_port_stats.expected_return
        )
      else:
        efficiency_gap["optimal_return_at_current_vol"] = current_port_stats.expected_return
        efficiency_gap["return_gap"] = 0.0

      # 2. Risk reduction at same return level
      same_ret_opt = self.optimize_target_return(current_port_stats.expected_return)
      if same_ret_opt is not None:
        efficiency_gap["optimal_vol_at_current_return"] = same_ret_opt.volatility
        efficiency_gap["volatility_reduction"] = (
          current_port_stats.volatility - same_ret_opt.volatility
        )
      else:
        efficiency_gap["optimal_vol_at_current_return"] = current_port_stats.volatility
        efficiency_gap["volatility_reduction"] = 0.0

      efficiency_gap["current_sharpe"] = current_port_stats.sharpe_ratio
      efficiency_gap["max_sharpe"] = max_sharpe.sharpe_ratio
      efficiency_gap["sharpe_gap"] = max_sharpe.sharpe_ratio - current_port_stats.sharpe_ratio

    # Optional Random Portfolios Cloud
    random_df = None
    if include_random_portfolios > 0:
      if seed is not None:
        np.random.seed(seed)
      alpha = np.ones(self.num_assets)
      raw_weights = np.random.dirichlet(alpha, size=include_random_portfolios)
      rand_rets = np.dot(raw_weights, self.ann_returns_arr)
      rand_vols = np.sqrt(np.einsum("ij,jk,ik->i", raw_weights, self.ann_cov_matrix, raw_weights))
      rand_sharpes = np.where(rand_vols > 1e-8, (rand_rets - self.risk_free_rate) / rand_vols, 0.0)

      data = {
        "expected_return": rand_rets,
        "volatility": rand_vols,
        "sharpe_ratio": rand_sharpes,
      }
      for idx, a in enumerate(self.assets):
        data[f"weight_{a}"] = raw_weights[:, idx]
      random_df = pd.DataFrame(data)

    return EfficientFrontierResult(
      assets=self.assets,
      asset_returns={a: float(r) for a, r in zip(self.assets, self.ann_returns_arr, strict=False)},
      asset_volatilities={a: float(v) for a, v in zip(self.assets, self.ann_vol_arr, strict=False)},
      correlation_matrix=self.corr_matrix,
      covariance_matrix=self.cov_df,
      risk_free_rate=self.risk_free_rate,
      min_variance_portfolio=gmv,
      max_sharpe_portfolio=max_sharpe,
      frontier_points=frontier_points,
      current_portfolio=current_port_stats,
      capital_allocation_line=cal_points,
      efficiency_gap=efficiency_gap,
      random_portfolios=random_df,
    )
