"""Unit tests for IBKR CSV Parser."""

from pathlib import Path

import pytest

from src.core.models import TaxTreatment
from src.core.parsers.ibkr import IBKRParser, parse_ibkr_csv

FIXTURES_DIR = Path(__file__).parent / "data"


def test_parse_fixture_ibkr_file():
  fixture_file = FIXTURES_DIR / "sample_ibkr.csv"
  assert fixture_file.exists(), f"Missing fixture file {fixture_file}"

  statement = parse_ibkr_csv(fixture_file)

  assert statement.broker_name == "Interactive Brokers Canada Inc."
  assert statement.period == "August 21, 2026"
  assert statement.base_currency == "USD"
  assert statement.master_account == "F1000000"
  assert len(statement.accounts) == 4

  # Check account tax treatments
  assert statement.accounts["F1000000"].tax_treatment == TaxTreatment.MASTER
  assert statement.accounts["U1000001/tsfa"].tax_treatment == TaxTreatment.TAX_FREE
  assert statement.accounts["U1000002/rrsp"].tax_treatment == TaxTreatment.TAX_DEFERRED
  assert statement.accounts["U1000003/joint"].tax_treatment == TaxTreatment.TAXABLE

  # Check CAD FX rate: 8250.0 / 11000.0 = 0.75
  assert statement.cad_to_usd_rate == pytest.approx(0.75)

  # Check positions (aggregate summary rows filtered out)
  # Account positions: CCO (U1), ENB (U3), AAPL (U1), AAPL (U2), MSFT (U2), NVDA (U1), SPYM (U2) = 7 positions
  assert len(statement.positions) == 7

  # Check total NAV
  assert statement.total_nav == pytest.approx(367100.0)

  # Check derived cash balances
  # F1000000: NAV 100.0, 0 positions -> 100.0 cash
  # U1000001/tsfa: NAV 105000.0, positions: CCO (6000 CAD * 0.75 = 4500 USD) + AAPL (15000 USD) + NVDA (30000 USD) = 49500 USD -> Cash = 55500.0 USD
  # U1000002/rrsp: NAV 210000.0, positions: AAPL (15000 USD) + MSFT (35000 USD) + SPYM (50000 USD) = 100000.0 USD -> Cash = 110000.0 USD
  # U1000003/joint: NAV 52000.0, positions: ENB (5000 CAD * 0.75 = 3750 USD) -> Cash = 48250.0 USD
  cash_by_acc = {p.account_id: p.market_value for p in statement.cash_positions}
  assert cash_by_acc["F1000000"] == pytest.approx(100.0)
  assert cash_by_acc["U1000001/tsfa"] == pytest.approx(55500.0)
  assert cash_by_acc["U1000002/rrsp"] == pytest.approx(110000.0)
  assert cash_by_acc["U1000003/joint"] == pytest.approx(48250.0)


def test_parse_string_stream():
  parser = IBKRParser()
  sample_csv = """Statement,Header,Field Name,Field Value
Statement,Data,BrokerName,Test Broker
Statement,Data,Period,January 2026
Account Information,Header,Name,Master Account,Accounts Included,Base Currency
Account Information,Data,Alice,F999,"F999, U999",USD
NAV Summary,Header,Currency,Name,Account,Account Type,Starting Net Asset Value,Ending Net Asset Value,Time Weighted Rate of Return
NAV Summary,Data,USD,Alice,U999/tfsa,Advisor Client,1000.0,1200.0,20%
Open Positions,Header,Asset Category,Currency,Symbol,Account,Quantity,Cost Basis,Close Price,Value,Unrealized P/L
Open Positions,Data,Stocks,USD,AAPL,U999/tfsa,10,1000.0,120.0,1200.0,200.0
"""
  statement = parser.parse_string(sample_csv)
  assert statement.broker_name == "Test Broker"
  assert len(statement.accounts) == 1
  assert len(statement.positions) == 1
  assert statement.positions[0].symbol == "AAPL"
