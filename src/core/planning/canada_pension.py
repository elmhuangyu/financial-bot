"""Canadian Government Pension (CPP, CPP2, OAS) Calculation Module."""


def calculate_cpp(
  retire_year: int,
  start_claim_age: int = 70,
  cpp_start_year: int = 2016,
  base_max_2026: float = 16375.0,
  enhanced_max_2026: float = 7500.0,
  birth_year: int = 1989,
) -> float:
  """
  Calculate annual CPP benefit (in 2026 constant dollars).

  Args:
      retire_year: Year the individual stops contributing to CPP.
      start_claim_age: Age to begin claiming (between 60 and 70).
      cpp_start_year: Year individual started max contributions.
      base_max_2026: 2026 full base CPP maximum.
      enhanced_max_2026: 2026 full enhanced CPP maximum.
      birth_year: Birth year.

  Returns:
      Annual CPP benefit in 2026 constant dollars.
  """
  contributed_years = max(1, retire_year - cpp_start_year + 1)
  # 17% drop-out leaves 39 contributory years denominator
  base_cpp = base_max_2026 * min(1.0, contributed_years / 39.0)

  # Enhanced CPP (funded tier started in 2019)
  enhanced_years = max(0, retire_year - 2019 + 1)
  enhanced_cpp = enhanced_max_2026 * min(1.0, enhanced_years / 40.0)

  total_at_65 = base_cpp + enhanced_cpp

  if start_claim_age == 65:
    return total_at_65
  elif start_claim_age < 65:
    # 0.6% reduction per month prior to age 65 (36% max at age 60)
    months_early = (65 - start_claim_age) * 12
    return total_at_65 * (1.0 - months_early * 0.006)
  else:
    # 0.7% increase per month after age 65 (42% max at age 70)
    months_delayed = (min(70, start_claim_age) - 65) * 12
    return total_at_65 * (1.0 + months_delayed * 0.007)


def calculate_oas(
  residence_years_at_65: int,
  claim_age: int = 65,
  full_oas_2026: float = 8600.0,
  current_age: int = 65,
) -> float:
  """
  Calculate annual OAS benefit (in 2026 constant dollars).

  Args:
      residence_years_at_65: Number of years resident in Canada between 18 and 65.
      claim_age: Age when OAS is initiated (65 to 70).
      full_oas_2026: Full OAS at age 65.
      current_age: The age for the evaluated year (applies +10% at 75+).

  Returns:
      Annual OAS benefit in 2026 constant dollars.
  """
  proration = min(1.0, residence_years_at_65 / 40.0)
  base_at_65 = full_oas_2026 * proration

  if claim_age > 65:
    months_delayed = (min(70, claim_age) - 65) * 12
    base_at_65 *= 1.0 + months_delayed * 0.006

  if current_age >= 75:
    base_at_65 *= 1.10

  return base_at_65
