"""Unit tests for Markowitz Efficient Frontier engine."""

import numpy as np
import pandas as pd
import pytest

from src.core.efficient_frontier import EfficientFrontierEngine


@pytest.fixture
def sample_returns_df():
  # Deterministic synthetic daily returns for 3 assets
  np.random.seed(42)
  dates = pd.date_range("2021-01-01", periods=500, freq="B")
  means = [0.0004, 0.0007, 0.0010]  # ~10%, ~17.6%, ~25.2% annualized
  cov = [
    [0.0001, 0.00003, 0.00001],
    [0.00003, 0.0002, 0.00004],
    [0.00001, 0.00004, 0.0004],
  ]
  data = np.random.multivariate_normal(means, cov, size=500)
  return pd.DataFrame(data, index=dates, columns=["EQ_US", "EQ_INTL", "CRYPTO"])


@pytest.fixture
def custom_market_data():
  returns = {"SPY": 0.12, "QQQ": 0.16, "BND": 0.04, "GLD": 0.08}
  vols = {"SPY": 0.15, "QQQ": 0.20, "BND": 0.06, "GLD": 0.14}
  corr_data = [
    [1.0, 0.85, 0.10, 0.05],
    [0.85, 1.0, 0.05, 0.02],
    [0.10, 0.05, 1.0, 0.20],
    [0.05, 0.02, 0.20, 1.0],
  ]
  corr_df = pd.DataFrame(corr_data, index=list(returns.keys()), columns=list(returns.keys()))
  return returns, vols, corr_df


def test_efficient_frontier_init_with_returns_df(sample_returns_df):
  engine = EfficientFrontierEngine(returns_df=sample_returns_df, risk_free_rate=0.03)
  assert len(engine.assets) == 3
  assert engine.risk_free_rate == 0.03
  assert engine.ann_cov_matrix.shape == (3, 3)
  assert len(engine.ann_returns_arr) == 3
  assert len(engine.ann_vol_arr) == 3


def test_efficient_frontier_init_with_custom_parameters(custom_market_data):
  returns, vols, corr_df = custom_market_data
  engine = EfficientFrontierEngine(
    custom_asset_returns=returns,
    custom_asset_volatilities=vols,
    custom_correlation_matrix=corr_df,
    risk_free_rate=0.035,
  )
  assert len(engine.assets) == 4
  assert engine.ann_returns_arr[0] == 0.12
  assert engine.ann_vol_arr[2] == 0.06
  assert np.allclose(np.diag(engine.corr_matrix.values), 1.0)


def test_optimize_min_variance(custom_market_data):
  returns, vols, corr_df = custom_market_data
  engine = EfficientFrontierEngine(
    custom_asset_returns=returns,
    custom_asset_volatilities=vols,
    custom_correlation_matrix=corr_df,
    risk_free_rate=0.035,
  )
  gmv = engine.optimize_min_variance()
  assert np.isclose(sum(gmv.weights.values()), 1.0, atol=1e-3)
  # GMV portfolio volatility must be <= single asset volatilities (e.g. BND vol is 0.06)
  assert gmv.volatility <= 0.06 + 1e-4
  assert gmv.expected_return > 0
  assert gmv.sharpe_ratio >= 0


def test_optimize_max_sharpe(custom_market_data):
  returns, vols, corr_df = custom_market_data
  engine = EfficientFrontierEngine(
    custom_asset_returns=returns,
    custom_asset_volatilities=vols,
    custom_correlation_matrix=corr_df,
    risk_free_rate=0.035,
  )
  max_sr = engine.optimize_max_sharpe()
  assert np.isclose(sum(max_sr.weights.values()), 1.0, atol=1e-3)

  # Check that Max Sharpe portfolio Sharpe ratio is strictly >= any individual asset Sharpe ratio
  for a in engine.assets:
    single_ret = returns[a]
    single_vol = vols[a]
    single_sr = (single_ret - 0.035) / single_vol
    assert max_sr.sharpe_ratio >= single_sr - 1e-4


def test_optimize_target_return(custom_market_data):
  returns, vols, corr_df = custom_market_data
  engine = EfficientFrontierEngine(
    custom_asset_returns=returns,
    custom_asset_volatilities=vols,
    custom_correlation_matrix=corr_df,
    risk_free_rate=0.035,
  )
  target = 0.10
  opt = engine.optimize_target_return(target)
  assert opt is not None
  assert np.isclose(opt.expected_return, target, atol=1e-3)
  assert np.isclose(sum(opt.weights.values()), 1.0, atol=1e-3)


def test_optimize_target_volatility(custom_market_data):
  returns, vols, corr_df = custom_market_data
  engine = EfficientFrontierEngine(
    custom_asset_returns=returns,
    custom_asset_volatilities=vols,
    custom_correlation_matrix=corr_df,
    risk_free_rate=0.035,
  )
  target_vol = 0.12
  opt = engine.optimize_target_volatility(target_vol)
  assert opt is not None
  assert opt.volatility <= target_vol + 1e-3
  assert np.isclose(sum(opt.weights.values()), 1.0, atol=1e-3)


def test_calculate_efficient_frontier_curve(custom_market_data):
  returns, vols, corr_df = custom_market_data
  current_weights = {"SPY": 0.40, "QQQ": 0.30, "BND": 0.20, "GLD": 0.10}
  engine = EfficientFrontierEngine(
    custom_asset_returns=returns,
    custom_asset_volatilities=vols,
    custom_correlation_matrix=corr_df,
    risk_free_rate=0.035,
  )
  res = engine.calculate_efficient_frontier(
    num_points=20,
    current_weights=current_weights,
    include_random_portfolios=100,
    seed=42,
  )

  assert len(res.frontier_points) > 0
  assert res.current_portfolio is not None
  assert np.isclose(sum(res.current_portfolio.weights.values()), 1.0, atol=1e-3)

  # Check efficiency gap metrics
  assert "return_gap" in res.efficiency_gap
  assert "volatility_reduction" in res.efficiency_gap
  assert res.efficiency_gap["return_gap"] >= -1e-4

  # Check capital allocation line
  assert len(res.capital_allocation_line) == 20
  assert res.capital_allocation_line[0]["volatility"] == 0.0
  assert np.isclose(res.capital_allocation_line[0]["expected_return"], 0.035)

  # Check random portfolios
  assert res.random_portfolios is not None
  assert len(res.random_portfolios) == 100
  assert "expected_return" in res.random_portfolios.columns
  assert "volatility" in res.random_portfolios.columns


def test_weight_bounds_enforcement(custom_market_data):
  returns, vols, corr_df = custom_market_data
  # Enforce maximum weight of 30% for any single asset
  engine = EfficientFrontierEngine(
    custom_asset_returns=returns,
    custom_asset_volatilities=vols,
    custom_correlation_matrix=corr_df,
    weight_bounds=(0.0, 0.35),
  )
  max_sr = engine.optimize_max_sharpe()
  for w in max_sr.weights.values():
    assert w <= 0.35 + 1e-4
    assert w >= 0.0 - 1e-4
