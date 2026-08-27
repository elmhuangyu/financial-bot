"""Deterministic Canadian & Ontario Tax Engine with Inflation Indexing."""


def get_rrif_minimum_rate(age: int) -> float:
  """CRA RRIF Minimum Withdrawal Percentage table."""
  if age < 71:
    return 1.0 / (90 - age)
  rates = {
    71: 0.0528,
    72: 0.0540,
    73: 0.0553,
    74: 0.0567,
    75: 0.0582,
    76: 0.0598,
    77: 0.0617,
    78: 0.0636,
    79: 0.0658,
    80: 0.0682,
    81: 0.0708,
    82: 0.0738,
    83: 0.0771,
    84: 0.0808,
    85: 0.0851,
    86: 0.0899,
    87: 0.0955,
    88: 0.1021,
    89: 0.1099,
    90: 0.1192,
    91: 0.1306,
    92: 0.1449,
    93: 0.1634,
    94: 0.1879,
    95: 0.2000,
  }
  return rates.get(age, 0.20)


def calculate_ontario_tax(taxable_income: float, cumulative_inflation: float = 1.0) -> float:
  """
  Calculate combined Federal and Ontario income tax for an individual.
  All brackets and Basic Personal Amounts (BPA) are dynamically indexed to cumulative inflation.
  """
  if taxable_income <= 0:
    return 0.0

  bpa_fed_2026 = 15705.0
  bracket1_2026 = 53359.0
  bracket2_2026 = 106717.0
  bracket3_2026 = 165430.0

  bpa_eff = bpa_fed_2026 * cumulative_inflation
  b1 = bracket1_2026 * cumulative_inflation
  b2 = bracket2_2026 * cumulative_inflation
  b3 = bracket3_2026 * cumulative_inflation

  if taxable_income <= bpa_eff:
    return 0.0

  tax = 0.0
  # Tier 1 (approx 20.05% effective)
  if taxable_income > bpa_eff:
    t1 = min(taxable_income, b1) - bpa_eff
    tax += t1 * 0.2005
  # Tier 2 (approx 29.65% - 31.48%)
  if taxable_income > b1:
    t2 = min(taxable_income, b2) - b1
    tax += t2 * 0.30
  # Tier 3 (approx 37.91% - 43.41%)
  if taxable_income > b2:
    t3 = min(taxable_income, b3) - b2
    tax += t3 * 0.40
  # Tier 4 (> 165k indexed, ~48%)
  if taxable_income > b3:
    t4 = taxable_income - b3
    tax += t4 * 0.48

  return max(0.0, tax)


def calculate_oas_clawback(
  net_income: float, oas_benefit: float, cumulative_inflation: float = 1.0
) -> float:
  """
  Calculate OAS Recovery Tax (15% clawback above inflation-indexed threshold).
  """
  threshold_2026 = 93200.0
  eff_threshold = threshold_2026 * cumulative_inflation

  if net_income <= eff_threshold or oas_benefit <= 0:
    return 0.0

  clawback = (net_income - eff_threshold) * 0.15
  return min(oas_benefit, max(0.0, clawback))
