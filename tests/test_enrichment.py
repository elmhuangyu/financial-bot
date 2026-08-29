"""Unit tests for Holding Enrichment."""

import pytest

from src.core.enrichment import IBKR_TO_YFINANCE_MAP, HoldingEnricher
from src.core.models import Account, Position, TaxTreatment


def test_enrich_with_dynamic_metadata():
  account_map = {
    "U1000001/tsfa": Account(
      account_id="U1000001/tsfa",
      name="Alice Smith",
      owner="Alice Smith",
      account_type="TFSA",
      tax_treatment=TaxTreatment.TAX_FREE,
      label="Alice TFSA",
    )
  }

  enricher = HoldingEnricher(account_map=account_map)
  enricher.fetch_ticker_metadata({"IBIT"})

  pos_ibit = Position(
    source="IBKR",
    account_id="U1000001/tsfa",
    symbol="IBIT",
    asset_category="ETFs",
    currency="USD",
    quantity=100,
    cost_basis=4000.0,
    close_price=45.0,
    market_value=4500.0,
    unrealized_pl=500.0,
  )

  enriched = enricher.enrich_position(pos_ibit, cad_to_usd=0.75)

  assert "Bitcoin" in enriched.asset_name
  assert enriched.asset_class == "Digital Assets"
  assert enriched.asset_subclass == "Crypto ETF"
  assert enriched.sector == "Digital Assets"
  assert enriched.owner == "Alice Smith"
  assert enriched.tax_treatment == "Tax-Free"
  assert enriched.market_value_usd == pytest.approx(4500.0)
  assert enriched.market_value_cad == pytest.approx(6000.0)  # 4500 / 0.75


def test_enrich_with_custom_overrides():
  custom_overrides = {
    "PRIVATE_FUND_1": {
      "name": "Custom Private Pension Fund",
      "asset_class": "International Equities",
      "asset_subclass": "Index Mutual Fund",
      "sector": "Broad Market / Diversified",
      "industry": "Global Index",
    }
  }
  enricher = HoldingEnricher(custom_overrides=custom_overrides)

  pos = Position(
    source="PrivateSource",
    account_id="ACC1",
    symbol="PRIVATE_FUND_1",
    asset_category="Funds",
    currency="CAD",
    quantity=50,
    cost_basis=5000.0,
    close_price=100.0,
    market_value=5000.0,
    unrealized_pl=0.0,
  )

  enriched = enricher.enrich_position(pos, cad_to_usd=0.75)
  assert enriched.asset_name == "Custom Private Pension Fund"
  assert enriched.asset_class == "International Equities"
  assert enriched.asset_subclass == "Index Mutual Fund"
  assert enriched.market_value_usd == pytest.approx(3750.0)


def test_enrich_cash_position():
  account_map = {
    "F1000000": Account(
      account_id="F1000000",
      name="John Doe",
      owner="John Doe",
      account_type="Advisor Master",
      tax_treatment=TaxTreatment.MASTER,
      label="Master Account",
    )
  }

  enricher = HoldingEnricher(account_map=account_map)

  cash_pos = Position(
    source="IBKR",
    account_id="F1000000",
    symbol="USD.CASH",
    asset_category="Cash",
    currency="USD",
    quantity=100.0,
    cost_basis=100.0,
    close_price=1.0,
    market_value=100.0,
    unrealized_pl=0.0,
  )

  enriched = enricher.enrich_position(cash_pos, cad_to_usd=0.75)
  assert enriched.asset_class == "Cash & Equivalents"
  assert enriched.sector == "Cash"
  assert enriched.market_value_usd == 100.0


def test_enrich_etf_with_equity_quote_type():
  enricher = HoldingEnricher()
  enricher._yf_cache["SPYM"] = {
    "name": "State Street SPDR Portfolio S&P 500 ETF",
    "quoteType": "ETF",
    "category": "Large Blend",
    "sector": "",
    "industry": "S&P 500 Index",
    "country": "US",
    "fundFamily": "SPDR",
  }

  pos = Position(
    source="IBKR",
    account_id="ACC1",
    symbol="SPYM",
    asset_category="Stocks",
    currency="USD",
    quantity=100,
    cost_basis=8000.0,
    close_price=90.0,
    market_value=9000.0,
    unrealized_pl=1000.0,
  )

  enriched = enricher.enrich_position(pos, cad_to_usd=0.75)
  assert enriched.asset_class == "US Equities"
  assert enriched.asset_subclass == "Broad Index ETF"
  assert enriched.sector == "Broad Market / Large Blend"
  assert enriched.industry == "S&P 500 Index"


def test_ibkr_to_yfinance_ticker_map():
  assert IBKR_TO_YFINANCE_MAP["CCO"] == "CCO.TO"
  assert IBKR_TO_YFINANCE_MAP["BRK B"] == "BRK-B"

  enricher = HoldingEnricher()
  enricher._yf_cache["CCO"] = {
    "name": "Cameco Corporation",
    "quoteType": "EQUITY",
    "category": "",
    "sector": "Energy",
    "industry": "Uranium",
    "country": "Canada",
    "fundFamily": "",
    "is_fund": False,
  }

  pos = Position(
    source="IBKR",
    account_id="ACC1",
    symbol="CCO",
    asset_category="Stocks",
    currency="CAD",
    quantity=100,
    cost_basis=5000.0,
    close_price=60.0,
    market_value=6000.0,
    unrealized_pl=1000.0,
  )

  enriched = enricher.enrich_position(pos, cad_to_usd=0.75)
  assert enriched.asset_name == "Cameco Corporation"
  assert enriched.asset_class == "Canadian Equities"
  assert enriched.asset_subclass == "Individual Stock"
  assert enriched.sector == "Energy"
  assert enriched.industry == "Uranium"
