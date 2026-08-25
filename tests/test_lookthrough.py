"""Unit tests for ETF Look-Through Engine."""

import pytest

from src.core.lookthrough import ETFConstituentProfile, ETFLookThroughEngine
from src.core.models import EnrichedHolding


def test_custom_fund_profile():
  custom_profiles = {
    "ML_8322": ETFConstituentProfile(
      symbol="ML_8322",
      sector_weights={"Technology": 0.374, "Financial Services": 0.122},
      top_holdings={"NVDA": ("NVIDIA Corp", 0.0754)},
    )
  }
  engine = ETFLookThroughEngine(custom_fund_profiles=custom_profiles)
  profile = engine.get_etf_profile("ML_8322")
  assert "Technology" in profile.sector_weights
  assert profile.sector_weights["Technology"] == pytest.approx(0.374)
  assert "NVDA" in profile.top_holdings


def test_compute_sector_lookthrough():
  custom_profiles = {
    "ML_8322": ETFConstituentProfile(
      symbol="ML_8322",
      sector_weights={"Technology": 0.374, "Financial Services": 0.122},
      top_holdings={"NVDA": ("NVIDIA Corp", 0.0754)},
    )
  }
  engine = ETFLookThroughEngine(custom_fund_profiles=custom_profiles)

  holdings = [
    EnrichedHolding(
      source="IBKR",
      account_id="U1",
      account_label="Test",
      owner="John",
      account_type="Taxable",
      tax_treatment="Taxable",
      symbol="NVDA",
      asset_name="NVIDIA Corp",
      asset_class="US Equities",
      asset_subclass="Individual Stock",
      sector="Technology",
      industry="Semiconductors",
      currency="USD",
      quantity=10,
      close_price_local=100.0,
      cost_basis_local=1000.0,
      market_value_local=1000.0,
      unrealized_pl_local=0.0,
      market_value_usd=1000.0,
      cost_basis_usd=1000.0,
      unrealized_pl_usd=0.0,
      market_value_cad=1300.0,
      cost_basis_cad=1300.0,
      unrealized_pl_cad=0.0,
    ),
    EnrichedHolding(
      source="Manulife",
      account_id="M1",
      account_label="Group Plan",
      owner="John",
      account_type="RRSP",
      tax_treatment="Tax-Deferred",
      symbol="ML_8322",
      asset_name="S&P 500 Index Fund",
      asset_class="US Equities",
      asset_subclass="Index Mutual Fund",
      sector="Broad Market / Diversified",
      industry="S&P 500",
      currency="CAD",
      quantity=100,
      close_price_local=100.0,
      cost_basis_local=10000.0,
      market_value_local=10000.0,
      unrealized_pl_local=0.0,
      market_value_usd=10000.0,
      cost_basis_usd=10000.0,
      unrealized_pl_usd=0.0,
      market_value_cad=13000.0,
      cost_basis_cad=13000.0,
      unrealized_pl_cad=0.0,
    ),
  ]

  total_usd = 11000.0
  sector_allocs = engine.compute_sector_lookthrough(holdings, total_usd)

  tech_alloc = next(s for s in sector_allocs if s.sector == "Technology")
  assert tech_alloc.direct_value_usd == pytest.approx(1000.0)
  assert tech_alloc.indirect_value_usd == pytest.approx(3740.0)
  assert tech_alloc.total_value_usd == pytest.approx(4740.0)


def test_compute_stock_lookthrough():
  custom_profiles = {
    "ML_8322": ETFConstituentProfile(
      symbol="ML_8322",
      sector_weights={"Technology": 0.374},
      top_holdings={"NVDA": ("NVIDIA Corp", 0.0754)},
    )
  }
  engine = ETFLookThroughEngine(custom_fund_profiles=custom_profiles)

  holdings = [
    EnrichedHolding(
      source="IBKR",
      account_id="U1",
      account_label="Test",
      owner="John",
      account_type="Taxable",
      tax_treatment="Taxable",
      symbol="NVDA",
      asset_name="NVIDIA Corp",
      asset_class="US Equities",
      asset_subclass="Individual Stock",
      sector="Technology",
      industry="Semiconductors",
      currency="USD",
      quantity=10,
      close_price_local=100.0,
      cost_basis_local=1000.0,
      market_value_local=1000.0,
      unrealized_pl_local=0.0,
      market_value_usd=1000.0,
      cost_basis_usd=1000.0,
      unrealized_pl_usd=0.0,
      market_value_cad=1300.0,
      cost_basis_cad=1300.0,
      unrealized_pl_cad=0.0,
    ),
    EnrichedHolding(
      source="Manulife",
      account_id="M1",
      account_label="Group Plan",
      owner="John",
      account_type="RRSP",
      tax_treatment="Tax-Deferred",
      symbol="ML_8322",
      asset_name="S&P 500 Index Fund",
      asset_class="US Equities",
      asset_subclass="Index Mutual Fund",
      sector="Broad Market / Diversified",
      industry="S&P 500",
      currency="CAD",
      quantity=100,
      close_price_local=100.0,
      cost_basis_local=10000.0,
      market_value_local=10000.0,
      unrealized_pl_local=0.0,
      market_value_usd=10000.0,
      cost_basis_usd=10000.0,
      unrealized_pl_usd=0.0,
      market_value_cad=13000.0,
      cost_basis_cad=13000.0,
      unrealized_pl_cad=0.0,
    ),
  ]

  total_usd = 11000.0
  stock_exposures = engine.compute_stock_lookthrough(holdings, total_usd)

  nvda_exp = next(s for s in stock_exposures if s.symbol == "NVDA")
  assert nvda_exp.direct_value_usd == pytest.approx(1000.0)
  assert nvda_exp.indirect_value_usd == pytest.approx(754.0)
  assert nvda_exp.total_value_usd == pytest.approx(1754.0)
  assert "ML_8322" in nvda_exp.etf_contributors
