"""Unit tests for Manulife Parser."""

from pathlib import Path

import pytest

from src.core.parsers.manulife import ManulifeParser

FIXTURES_DIR = Path(__file__).parent / "data"


def test_parse_fixture_manulife_file():
  fixture_file = FIXTURES_DIR / "sample_manulife.txt"
  assert fixture_file.exists(), f"Missing fixture file {fixture_file}"

  parser = ManulifeParser()
  positions = parser.parse_file(fixture_file)
  assert len(positions) == 2

  p1 = positions[0]
  assert p1.symbol == "ML_8322"
  assert p1.currency == "CAD"
  assert p1.market_value == pytest.approx(100000.0)
  assert p1.quantity == pytest.approx(50.0 + 950.0)
  assert p1.close_price == pytest.approx(100.0)

  p2 = positions[1]
  assert p2.symbol == "ML_8321"
  assert p2.currency == "CAD"
  assert p2.market_value == pytest.approx(50000.0)
  assert p2.quantity == pytest.approx(1000.0)
  assert p2.close_price == pytest.approx(50.0)

  total_cad = sum(p.market_value for p in positions)
  assert total_cad == pytest.approx(150000.0)


def test_parse_string_content():
  sample_text = """Investment details
Current value: $10,000.00
Breakdown by investments
Image icon 9999 - Custom Index Fund
Contribution category	Number	Unit value	Current value ($)
Member required	100.00	100.00	10,000.00
  TOTAL	$10,000.00
"""
  parser = ManulifeParser()
  positions = parser.parse_text(sample_text)
  assert len(positions) == 1
  assert positions[0].symbol == "ML_9999"
  assert positions[0].market_value == pytest.approx(10000.0)
