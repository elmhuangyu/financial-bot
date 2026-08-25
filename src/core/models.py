"""Core data models for financial-bot."""

from dataclasses import dataclass, field
from enum import StrEnum


class TaxTreatment(StrEnum):
  TAXABLE = "Taxable"
  TAX_DEFERRED = "Tax-Deferred"
  TAX_FREE = "Tax-Free"
  MASTER = "Master"
  UNKNOWN = "Unknown"


class AssetClass(StrEnum):
  US_EQUITIES = "US Equities"
  CANADIAN_EQUITIES = "Canadian Equities"
  INTERNATIONAL_EQUITIES = "International Equities"
  DIGITAL_ASSETS = "Digital Assets"
  FIXED_INCOME = "Fixed Income"
  CASH_EQUIVALENTS = "Cash & Equivalents"
  REAL_ESTATE = "Real Estate"
  COMMODITIES = "Commodities"
  OTHER = "Other"


@dataclass
class Account:
  account_id: str
  name: str
  owner: str = "Unknown"
  account_type: str = "Unknown"
  tax_treatment: TaxTreatment = TaxTreatment.UNKNOWN
  label: str = ""
  base_currency: str = "USD"
  starting_nav: float = 0.0
  ending_nav: float = 0.0
  time_weighted_return: float = 0.0

  def __post_init__(self):
    if not self.label:
      self.label = self.account_id


@dataclass
class Position:
  source: str
  account_id: str
  symbol: str
  asset_category: str
  currency: str
  quantity: float
  cost_basis: float
  close_price: float
  market_value: float
  unrealized_pl: float = 0.0


@dataclass
class EnrichedHolding:
  source: str
  account_id: str
  account_label: str
  owner: str
  account_type: str
  tax_treatment: str
  symbol: str
  asset_name: str
  asset_class: str
  asset_subclass: str
  sector: str
  industry: str
  currency: str
  quantity: float
  close_price_local: float
  cost_basis_local: float
  market_value_local: float
  unrealized_pl_local: float
  market_value_usd: float
  cost_basis_usd: float
  unrealized_pl_usd: float
  market_value_cad: float
  cost_basis_cad: float
  unrealized_pl_cad: float


@dataclass
class IBKRStatement:
  broker_name: str = ""
  period: str = ""
  generated_at: str = ""
  base_currency: str = "USD"
  master_account: str = ""
  cad_to_usd_rate: float = 1.0
  accounts: dict[str, Account] = field(default_factory=dict)
  positions: list[Position] = field(default_factory=list)
  cash_positions: list[Position] = field(default_factory=list)

  @property
  def total_nav(self) -> float:
    return sum(acc.ending_nav for acc in self.accounts.values())

  @property
  def all_positions(self) -> list[Position]:
    return self.positions + self.cash_positions
