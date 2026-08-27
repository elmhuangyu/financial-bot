import pytest

from src.core.planning.canada_pension import calculate_cpp, calculate_oas
from src.core.planning.canada_tax_engine import (
  calculate_oas_clawback,
  calculate_ontario_tax,
  get_rrif_minimum_rate,
)


def test_pension_cpp_calculation():
  # Bob retires in 2033 (18 years worked)
  cpp_65 = calculate_cpp(retire_year=2033, start_claim_age=65)
  assert 10000 < cpp_65 < 12000

  # Delay to 70 (+42%)
  cpp_70 = calculate_cpp(retire_year=2033, start_claim_age=70)
  assert cpp_70 == pytest.approx(cpp_65 * 1.42, rel=1e-3)


def test_pension_oas_calculation():
  # 40 years full OAS
  oas_full = calculate_oas(residence_years_at_65=40, claim_age=65)
  assert oas_full == 8600.0

  # 29 years OAS (Alice)
  oas_alice = calculate_oas(residence_years_at_65=29, claim_age=65)
  assert oas_alice == pytest.approx(8600.0 * 29.0 / 40.0, rel=1e-3)


def test_tax_engine_brackets_and_inflation():
  # Income below BPA
  tax_low = calculate_ontario_tax(15000, cumulative_inflation=1.0)
  assert tax_low == 0.0

  # Indexed BPA
  tax_inflated = calculate_ontario_tax(20000, cumulative_inflation=1.5)
  assert tax_inflated == 0.0  # 20k is below 15.7k * 1.5 = 23.55k

  # OAS clawback
  claw = calculate_oas_clawback(net_income=100000, oas_benefit=8600, cumulative_inflation=1.0)
  assert claw == pytest.approx((100000 - 93200) * 0.15, rel=1e-3)


def test_rrif_minimum_table():
  assert get_rrif_minimum_rate(71) == 0.0528
  assert get_rrif_minimum_rate(95) == 0.2000
