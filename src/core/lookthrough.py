"""Generic ETF Look-Through Analysis Engine without hardcoded tickers."""

from dataclasses import dataclass, field

import yfinance as yf
from yfinance.exceptions import YFException

from src.core.enrichment import IBKR_TO_YFINANCE_MAP, normalize_sector_name
from src.core.models import EnrichedHolding


@dataclass
class ETFConstituentProfile:
  symbol: str
  sector_weights: dict[str, float] = field(default_factory=dict)
  top_holdings: dict[str, tuple[str, float]] = field(default_factory=dict)  # sym -> (name, weight)


@dataclass
class LookThroughStockExposure:
  symbol: str
  name: str
  sector: str
  direct_value_usd: float = 0.0
  indirect_value_usd: float = 0.0
  total_value_usd: float = 0.0
  pct_of_portfolio: float = 0.0
  etf_contributors: dict[str, float] = field(default_factory=dict)  # etf_sym -> indirect_usd


@dataclass
class LookThroughSectorAllocation:
  sector: str
  direct_value_usd: float = 0.0
  indirect_value_usd: float = 0.0
  total_value_usd: float = 0.0
  pct_of_portfolio: float = 0.0


class ETFLookThroughEngine:
  """Generic engine for computing look-through sector distributions and constituent exposures dynamically."""

  def __init__(
    self,
    custom_fund_profiles: dict[str, ETFConstituentProfile] | None = None,
    ticker_map: dict[str, str] | None = None,
  ):
    self.custom_fund_profiles = custom_fund_profiles or {}
    self.ticker_map = {**IBKR_TO_YFINANCE_MAP, **(ticker_map or {})}
    self._etf_cache: dict[str, ETFConstituentProfile] = dict(self.custom_fund_profiles)

  def get_etf_profile(self, symbol: str) -> ETFConstituentProfile:
    if symbol in self._etf_cache:
      return self._etf_cache[symbol]

    profile = ETFConstituentProfile(symbol=symbol)
    yf_sym = self.ticker_map.get(symbol, symbol)

    # Dynamically query Yahoo Finance for ETF funds_data
    try:
      t = yf.Ticker(yf_sym)
      fd = t.funds_data
      if fd:
        try:
          if hasattr(fd, "sector_weightings") and fd.sector_weightings:
            for raw_sec, weight in fd.sector_weightings.items():
              if weight and weight > 0:
                norm_sec = normalize_sector_name(raw_sec)
                profile.sector_weights[norm_sec] = float(weight)
        except KeyError, ValueError, OSError, RuntimeError, AttributeError, TypeError, YFException:
          pass

        try:
          if hasattr(fd, "top_holdings") and fd.top_holdings is not None:
            th_df = fd.top_holdings
            for constituent_sym, row in th_df.iterrows():
              c_sym = str(constituent_sym)
              c_name = str(row.get("Name", c_sym))
              c_weight = float(row.get("Holding Percent", 0.0))
              if c_weight > 0:
                profile.top_holdings[c_sym] = (c_name, c_weight)
        except KeyError, ValueError, OSError, RuntimeError, AttributeError, TypeError, YFException:
          pass
    except KeyError, ValueError, OSError, RuntimeError, AttributeError, TypeError, YFException:
      pass

    self._etf_cache[symbol] = profile
    return profile

  def compute_sector_lookthrough(
    self, holdings: list[EnrichedHolding], total_portfolio_usd: float
  ) -> list[LookThroughSectorAllocation]:
    """Computes true sector exposure by decomposing ETF holdings into their constituent sector weights."""
    sector_direct: dict[str, float] = {}
    sector_indirect: dict[str, float] = {}

    for h in holdings:
      val = h.market_value_usd
      if val <= 0:
        continue

      if h.asset_subclass in ["Individual Stock", "Cash"]:
        sector = h.sector
        sector_direct[sector] = sector_direct.get(sector, 0.0) + val

      elif h.asset_subclass in ["Crypto ETF"] or h.asset_class == "Digital Assets":
        sector = "Digital Assets"
        sector_direct[sector] = sector_direct.get(sector, 0.0) + val

      else:
        # ETF or Index Fund -> Look-through
        profile = self.get_etf_profile(h.symbol)
        if profile.sector_weights:
          for sec, weight in profile.sector_weights.items():
            allocated_val = val * weight
            sector_indirect[sec] = sector_indirect.get(sec, 0.0) + allocated_val
        else:
          # Fallback to ETF declared sector
          sec = h.sector
          sector_direct[sec] = sector_direct.get(sec, 0.0) + val

    all_sectors = set(sector_direct.keys()) | set(sector_indirect.keys())
    results = []

    for sec in all_sectors:
      d_val = sector_direct.get(sec, 0.0)
      ind_val = sector_indirect.get(sec, 0.0)
      tot_val = d_val + ind_val
      pct = (tot_val / total_portfolio_usd * 100.0) if total_portfolio_usd > 0 else 0.0
      results.append(
        LookThroughSectorAllocation(
          sector=sec,
          direct_value_usd=round(d_val, 2),
          indirect_value_usd=round(ind_val, 2),
          total_value_usd=round(tot_val, 2),
          pct_of_portfolio=round(pct, 2),
        )
      )

    results.sort(key=lambda x: x.total_value_usd, reverse=True)
    return results

  def compute_stock_lookthrough(
    self, holdings: list[EnrichedHolding], total_portfolio_usd: float
  ) -> list[LookThroughStockExposure]:
    """Computes total single-stock economic exposure combining direct positions and underlying ETF constituents."""
    stocks_map: dict[str, LookThroughStockExposure] = {}

    # 1. Map direct individual stock positions
    for h in holdings:
      val = h.market_value_usd
      if h.asset_subclass == "Individual Stock":
        sym = h.symbol
        norm_sym = "GOOG/GOOGL" if sym in ["GOOG", "GOOGL"] else sym
        if norm_sym not in stocks_map:
          stocks_map[norm_sym] = LookThroughStockExposure(
            symbol=norm_sym,
            name=h.asset_name,
            sector=h.sector,
            direct_value_usd=0.0,
            indirect_value_usd=0.0,
            total_value_usd=0.0,
            pct_of_portfolio=0.0,
          )
        stocks_map[norm_sym].direct_value_usd += val

    # 2. Decompose ETF constituents
    for h in holdings:
      val = h.market_value_usd
      if h.asset_subclass in [
        "Broad Index ETF",
        "Sector ETF",
        "Factor / Strategy ETF",
        "Thematic ETF",
        "Index Mutual Fund",
        "ETF",
      ]:
        profile = self.get_etf_profile(h.symbol)
        for c_sym, (c_name, weight) in profile.top_holdings.items():
          norm_c_sym = "GOOG/GOOGL" if c_sym in ["GOOG", "GOOGL"] else c_sym
          if norm_c_sym == "BRK-B" and "BRK B" in stocks_map:
            norm_c_sym = "BRK B"

          indirect_val = val * weight
          if norm_c_sym not in stocks_map:
            stocks_map[norm_c_sym] = LookThroughStockExposure(
              symbol=norm_c_sym,
              name=c_name,
              sector="Look-Through Constituent",
              direct_value_usd=0.0,
              indirect_value_usd=0.0,
              total_value_usd=0.0,
              pct_of_portfolio=0.0,
            )
          stocks_map[norm_c_sym].indirect_value_usd += indirect_val
          stocks_map[norm_c_sym].etf_contributors[h.symbol] = (
            stocks_map[norm_c_sym].etf_contributors.get(h.symbol, 0.0) + indirect_val
          )

    # 3. Finalize totals and percentages
    for exposure in stocks_map.values():
      exposure.total_value_usd = round(exposure.direct_value_usd + exposure.indirect_value_usd, 2)
      exposure.direct_value_usd = round(exposure.direct_value_usd, 2)
      exposure.indirect_value_usd = round(exposure.indirect_value_usd, 2)
      exposure.pct_of_portfolio = round(
        (exposure.total_value_usd / total_portfolio_usd * 100.0)
        if total_portfolio_usd > 0
        else 0.0,
        2,
      )

    results = list(stocks_map.values())
    results.sort(key=lambda x: x.total_value_usd, reverse=True)
    return results
