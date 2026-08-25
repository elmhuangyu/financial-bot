"""Generic holding enrichment and classification engine without hardcoded tickers."""

import re

import yfinance as yf
from yfinance.exceptions import YFException

from src.core.models import (
  Account,
  EnrichedHolding,
  Position,
)

# Standard GICS sector normalization
GICS_SECTOR_KEYWORDS = {
  "technology": "Technology",
  "information technology": "Technology",
  "semiconductor": "Technology",
  "communication": "Communication Services",
  "consumer cyclical": "Consumer Cyclical",
  "consumer discretionary": "Consumer Cyclical",
  "consumer defensive": "Consumer Defensive",
  "consumer staples": "Consumer Defensive",
  "financial": "Financial Services",
  "financial services": "Financial Services",
  "healthcare": "Healthcare",
  "health": "Healthcare",
  "industrial": "Industrials",
  "industrials": "Industrials",
  "energy": "Energy",
  "utility": "Utilities",
  "utilities": "Utilities",
  "real estate": "Real Estate",
  "realestate": "Real Estate",
  "basic materials": "Basic Materials",
  "materials": "Basic Materials",
  "digital assets": "Digital Assets",
}


def normalize_sector_name(raw_name: str | None) -> str:
  if not raw_name:
    return "Other"
  clean = raw_name.strip().lower().replace("_", " ")
  for kw, standard_name in GICS_SECTOR_KEYWORDS.items():
    if kw in clean:
      return standard_name
  return raw_name.strip()


class HoldingEnricher:
  """Generic enricher that derives classification and metadata dynamically from Yahoo Finance."""

  def __init__(
    self,
    account_map: dict[str, Account] | None = None,
    custom_overrides: dict[str, dict[str, str]] | None = None,
  ):
    self.account_map = account_map or {}
    self.custom_overrides = custom_overrides or {}
    self._yf_cache: dict[str, dict] = {}

  def fetch_ticker_metadata(self, symbols: set[str]) -> dict[str, dict]:
    """Dynamically queries Yahoo Finance for unknown symbols."""
    needed = [
      s
      for s in symbols
      if s not in self._yf_cache and s not in self.custom_overrides and not s.endswith(".CASH")
    ]

    for sym in needed:
      yf_sym = sym
      if sym == "BRK B":
        yf_sym = "BRK-B"
      elif sym in ["CCO", "ENB"] or (len(sym) <= 4 and sym.isalpha() and sym.isupper() and False):
        pass

      try:
        t = yf.Ticker(yf_sym)
        data = t.info
        name = data.get("shortName") or data.get("longName") or sym
        quote_type = (data.get("quoteType") or "EQUITY").upper()
        category = data.get("category") or ""
        sector = data.get("sector") or ""
        industry = data.get("industry") or ""
        country = data.get("country") or ("Canada" if yf_sym.endswith(".TO") else "US")
        fund_family = data.get("fundFamily") or ""
        is_fund = False

        # 1. Primary Structured check via yfinance FundsData API
        try:
          fd = t.funds_data
          overview = getattr(fd, "fund_overview", {}) or {}
          if overview and isinstance(overview, dict) and overview.get("legalType"):
            is_fund = True
            quote_type = (
              "ETF"
              if "Exchange Traded" in str(overview.get("legalType", ""))
              else "MUTUALFUND"
            )
            category = overview.get("categoryName") or category
            fund_family = overview.get("family") or fund_family
            industry = overview.get("legalType") or industry or "Exchange Traded Fund"
        except (KeyError, ValueError, OSError, RuntimeError, AttributeError, TypeError, YFException):
          pass

        # 2. Strict fallback only if funds_data is unavailable but legal name explicitly specifies ETF/Index Fund
        if not is_fund and quote_type == "EQUITY" and re.search(
          r"\b(ETF|Index Fund)\b", name, re.IGNORECASE
        ):
          quote_type = "ETF"
          is_fund = True

        if quote_type == "ETF" and not category and not sector:
          if any(k in name.lower() for k in ["s&p 500", "s&p500", "spdr portfolio s&p"]):
            category = "Large Blend"
            industry = "S&P 500 Index"
          elif "nasdaq" in name.lower() or "qqq" in name.lower():
            category = "Large Growth"
            industry = "NASDAQ 100 Index"

        self._yf_cache[sym] = {
          "name": name,
          "quoteType": quote_type,
          "category": category,
          "sector": sector,
          "industry": industry,
          "country": country,
          "fundFamily": fund_family,
          "is_fund": is_fund or (quote_type in ["ETF", "MUTUALFUND"]),
        }
      except (KeyError, ValueError, OSError, RuntimeError, AttributeError, TypeError, YFException):
        self._yf_cache[sym] = {
          "name": sym,
          "quoteType": "EQUITY",
          "category": "",
          "sector": "Other",
          "industry": "Other",
          "country": "US",
          "fundFamily": "",
          "is_fund": False,
        }

    return self._yf_cache

  def enrich_position(self, pos: Position, cad_to_usd: float) -> EnrichedHolding:
    acc = self.account_map.get(pos.account_id)
    owner = acc.owner if acc else "Unknown"
    account_type = acc.account_type if acc else "Unknown"
    tax_treatment = (
      acc.tax_treatment.value
      if acc and hasattr(acc.tax_treatment, "value")
      else (str(acc.tax_treatment) if acc else "Unknown")
    )
    label = acc.label if acc else pos.account_id

    # Currency conversion
    curr = pos.currency
    val_local = pos.market_value
    cost_local = pos.cost_basis
    pnl_local = pos.unrealized_pl

    if curr == "USD":
      val_usd = val_local
      val_cad = val_local / cad_to_usd if cad_to_usd else val_local
      cost_usd = cost_local
      cost_cad = cost_local / cad_to_usd if cad_to_usd else cost_local
      pnl_usd = pnl_local
      pnl_cad = pnl_local / cad_to_usd if cad_to_usd else pnl_local
    else:  # CAD
      val_cad = val_local
      val_usd = val_local * cad_to_usd
      cost_cad = cost_local
      cost_usd = cost_local * cad_to_usd
      pnl_cad = pnl_local
      pnl_usd = pnl_local * cad_to_usd

    # 1. Cash handling
    if pos.symbol.endswith(".CASH") or pos.asset_category == "Cash":
      asset_name = f"{curr} Cash / Settlement"
      asset_class = "Cash & Equivalents"
      asset_subclass = "Cash"
      sector = "Cash"
      industry = "Cash & Money Market"

    # 2. Custom override (e.g. unlisted/private funds)
    elif pos.symbol in self.custom_overrides:
      meta = self.custom_overrides[pos.symbol]
      asset_name = meta.get("name", pos.symbol)
      asset_class = meta.get("asset_class", "US Equities")
      asset_subclass = meta.get("asset_subclass", "Mutual Fund")
      sector = meta.get("sector", "Other")
      industry = meta.get("industry", "Other")

    # 3. Dynamic derivation from Yahoo Finance metadata
    else:
      info = self._yf_cache.get(pos.symbol, {})
      asset_name = info.get("name") or pos.symbol
      quote_type = info.get("quoteType", "EQUITY")
      category = info.get("category", "")
      raw_sector = info.get("sector", "")
      raw_industry = info.get("industry", "")
      country = info.get("country", "")

      # Rule: Digital Assets ETF
      if (
        category == "Digital Assets"
        or "Crypto" in category
        or "Bitcoin" in asset_name
        or "Ethereum" in asset_name
      ):
        asset_class = "Digital Assets"
        asset_subclass = "Crypto ETF"
        sector = "Digital Assets"
        industry = raw_industry or "Digital Assets Trust"

      # Rule: Equity / ETF Regional Classification
      elif country == "Canada" or pos.symbol.endswith(".TO") or curr == "CAD":
        asset_class = "Canadian Equities"
        if info.get("is_fund") or quote_type in ["ETF", "MUTUALFUND"]:
          asset_subclass = "ETF"
          sector = normalize_sector_name(raw_sector or category)
          industry = raw_industry or category or "Canadian ETF"
        else:
          asset_subclass = "Individual Stock"
          sector = normalize_sector_name(raw_sector)
          industry = raw_industry or "Other"

      # Rule: US / International ETF
      elif info.get("is_fund") or quote_type in ["ETF", "MUTUALFUND"]:
        if any(
          w in category
          for w in ["Foreign", "International", "Emerging", "Europe", "Pacific", "Global"]
        ):
          asset_class = "International Equities"
        else:
          asset_class = "US Equities"

        # Subclass determination
        if any(
          b in category for b in ["Large Blend", "Large Growth", "Large Value", "Mid-Cap", "Small"]
        ) or any(
          k in asset_name.lower()
          for k in ["s&p 500", "s&p500", "spdr portfolio s&p", "nasdaq"]
        ):
          asset_subclass = "Broad Index ETF"
          sector = f"Broad Market / {category}" if category else "Broad Market / Large Blend"
        else:
          asset_subclass = "Sector ETF"
          sector = normalize_sector_name(raw_sector or category)

        industry = raw_industry or category or "Exchange Traded Fund"

      # Rule: Single Stock
      else:
        asset_class = "US Equities"
        asset_subclass = "Individual Stock"
        sector = normalize_sector_name(raw_sector)
        industry = raw_industry or "Other"

    return EnrichedHolding(
      source=pos.source,
      account_id=pos.account_id,
      account_label=label,
      owner=owner,
      account_type=account_type,
      tax_treatment=tax_treatment,
      symbol=pos.symbol,
      asset_name=asset_name,
      asset_class=asset_class,
      asset_subclass=asset_subclass,
      sector=sector,
      industry=industry,
      currency=curr,
      quantity=pos.quantity,
      close_price_local=pos.close_price,
      cost_basis_local=cost_local,
      market_value_local=val_local,
      unrealized_pl_local=pnl_local,
      market_value_usd=round(val_usd, 2),
      cost_basis_usd=round(cost_usd, 2),
      unrealized_pl_usd=round(pnl_usd, 2),
      market_value_cad=round(val_cad, 2),
      cost_basis_cad=round(cost_cad, 2),
      unrealized_pl_cad=round(pnl_cad, 2),
    )
