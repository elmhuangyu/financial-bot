"""Unit tests for Monte Carlo simulation engine."""

import numpy as np
import pandas as pd
import pytest

from src.core.monte_carlo import MonteCarloEngine


@pytest.fixture
def sample_returns_df():
  # Generate deterministic synthetic returns for 3 assets
  np.random.seed(42)
  dates = pd.date_range("2021-01-01", periods=500, freq="B")
  # 3 assets with known means and correlated noise
  means = [0.0005, 0.0008, 0.0012]
  cov = [
    [0.0001, 0.00005, 0.00002],
    [0.00005, 0.0002, 0.00006],
    [0.00002, 0.00006, 0.0005],
  ]
  data = np.random.multivariate_normal(means, cov, size=500)
  df = pd.DataFrame(data, index=dates, columns=["ASSET_A", "ASSET_B", "ASSET_C"])
  return df


def test_monte_carlo_engine_init(sample_returns_df):
  weights = {"ASSET_A": 0.5, "ASSET_B": 0.3, "ASSET_C": 0.2}
  engine = MonteCarloEngine(
    initial_value=100000.0,
    asset_weights=weights,
    returns_df=sample_returns_df,
    seed=42,
  )

  assert engine.initial_value == 100000.0
  assert len(engine.assets) == 3
  assert engine.portfolio_ann_return > 0
  assert engine.portfolio_ann_vol > 0
  assert engine.corr_matrix.shape == (3, 3)


def test_monte_carlo_engine_weight_validation(sample_returns_df):
  weights = {"ASSET_A": 0.5, "ASSET_B": 0.3}  # Sums to 0.8 != 1.0
  with pytest.raises(ValueError, match="Asset weights must sum to 1.0"):
    MonteCarloEngine(
      initial_value=100000.0,
      asset_weights=weights,
      returns_df=sample_returns_df,
    )


def test_monte_carlo_simulation_run(sample_returns_df):
  weights = {"ASSET_A": 0.5, "ASSET_B": 0.3, "ASSET_C": 0.2}
  engine = MonteCarloEngine(
    initial_value=100000.0,
    asset_weights=weights,
    returns_df=sample_returns_df,
    seed=42,
  )

  num_sims = 10
  years = 5
  res = engine.simulate_portfolio_gbm(
    num_simulations=num_sims,
    time_horizon_years=years,
    steps_per_year=252,
  )

  assert res.num_simulations == num_sims
  assert res.time_horizon_years == years
  assert res.trajectories.shape == (num_sims, years * 252 + 1)
  assert len(res.final_values) == num_sims
  assert len(res.max_drawdowns) == num_sims
  assert np.all(res.max_drawdowns >= 0.0)
  assert np.all(res.trajectories[:, 0] == 100000.0)
  assert np.all(res.final_values > 0)
  assert "p50" in res.percentiles
  assert "mean_final_value" in res.summary_metrics
  assert "mean_max_drawdown" in res.summary_metrics
  assert "year_1" in res.horizon_loss_probabilities
