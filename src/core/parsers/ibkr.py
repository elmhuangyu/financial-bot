"""IBKR (Interactive Brokers) CSV Statement Parser."""

import csv
import io
from pathlib import Path
from typing import TextIO

from src.core.models import Account, IBKRStatement, Position, TaxTreatment


class IBKRParser:
  """Parser for Interactive Brokers Account Summary / Activity CSV statement exports."""

  def __init__(self, account_metadata_overrides: dict[str, dict] | None = None):
    self.account_metadata_overrides = account_metadata_overrides or {}

  def parse_file(self, file_path: str | Path) -> IBKRStatement:
    path = Path(file_path)
    with path.open("r", encoding="utf-8-sig") as f:
      return self.parse_stream(f)

  def parse_string(self, content: str) -> IBKRStatement:
    return self.parse_stream(io.StringIO(content))

  def parse_stream(self, stream: TextIO) -> IBKRStatement:
    statement = IBKRStatement()
    reader = csv.reader(stream)

    raw_positions = []
    last_total_value = None
    inferred_cad_rate = None

    for row in reader:
      if not row or len(row) < 2:
        continue

      section = row[0].strip()
      record_type = row[1].strip()

      if section == "Statement" and record_type == "Data":
        self._parse_statement_field(statement, row)

      elif section == "Account Information" and record_type == "Data":
        self._parse_account_info(statement, row)

      elif section == "NAV Summary" and record_type == "Data":
        self._parse_nav_summary_row(statement, row)

      elif section == "Open Positions" and record_type == "Data":
        self._parse_open_position_row(row, raw_positions)
        if len(row) >= 3:
          record_tag = row[2].strip()
          if record_tag == "Total" and len(row) >= 10:
            try:
              last_total_value = float(row[9].strip())
            except ValueError:
              last_total_value = None
          elif record_tag == "Total in USD" and len(row) >= 10:
            try:
              val_in_usd = float(row[9].strip())
              if last_total_value and last_total_value > 0:
                inferred_cad_rate = val_in_usd / last_total_value
            except ValueError:
              pass

    # Assign inferred FX rate
    statement.cad_to_usd_rate = inferred_cad_rate if inferred_cad_rate else 1.0

    statement.positions = raw_positions

    # Compute account-level cash balances
    self._calculate_cash_positions(statement)

    return statement

  def _parse_statement_field(self, statement: IBKRStatement, row: list[str]) -> None:
    if len(row) < 4:
      return
    field_name = row[2].strip()
    field_value = ", ".join(r.strip() for r in row[3:])

    if field_name == "BrokerName":
      statement.broker_name = field_value
    elif field_name == "Period":
      statement.period = field_value
    elif field_name == "WhenGenerated":
      statement.generated_at = field_value

  def _parse_account_info(self, statement: IBKRStatement, row: list[str]) -> None:
    if len(row) < 6:
      return
    # row: Account Information,Data,Name,Master Account,Accounts Included,Base Currency
    statement.master_account = row[3].strip()
    statement.base_currency = row[5].strip()

  def _parse_nav_summary_row(self, statement: IBKRStatement, row: list[str]) -> None:
    if len(row) < 8:
      return
    if row[2].strip() == "Total":
      return

    # row: NAV Summary,Data,Currency,Name,Account,Account Type,Starting NAV,Ending NAV,[TWR]
    currency = row[2].strip()
    name = row[3].strip()
    account_id = row[4].strip()
    account_type = row[5].strip()

    try:
      starting_nav = float(row[6].strip())
    except ValueError:
      starting_nav = 0.0

    try:
      ending_nav = float(row[7].strip())
    except ValueError:
      ending_nav = 0.0

    twr = 0.0
    if len(row) >= 9 and row[8].strip().endswith("%"):
      try:
        twr = float(row[8].strip().rstrip("%")) / 100.0
      except ValueError:
        twr = 0.0

    meta = self.account_metadata_overrides.get(account_id, {})
    owner = meta.get("owner", name)
    acc_type = meta.get("account_type", account_type)
    tax_treatment = meta.get("tax_treatment", self._infer_tax_treatment(account_id, acc_type))
    label = meta.get("label", account_id)

    statement.accounts[account_id] = Account(
      account_id=account_id,
      name=name,
      owner=owner,
      account_type=acc_type,
      tax_treatment=tax_treatment,
      label=label,
      base_currency=currency,
      starting_nav=starting_nav,
      ending_nav=ending_nav,
      time_weighted_return=twr,
    )

  def _parse_open_position_row(
    self,
    row: list[str],
    positions: list[Position],
  ) -> None:
    if len(row) < 11:
      return

    asset_cat = row[2].strip()
    if asset_cat in ["Total", "Total in USD"]:
      return

    if asset_cat not in ["Stocks", "ETFs", "Options", "Bonds", "Funds"]:
      return

    currency = row[3].strip()
    symbol = row[4].strip()
    account_id = row[5].strip()

    # If account_id is empty, this is an aggregate row across all accounts in the statement
    if not account_id:
      return

    try:
      quantity = float(row[6].strip())
      cost_basis = float(row[7].strip())
      close_price = float(row[8].strip())
      value = float(row[9].strip())
      unrealized_pl = float(row[10].strip())
    except ValueError:
      return

    positions.append(
      Position(
        source="IBKR",
        account_id=account_id,
        symbol=symbol,
        asset_category=asset_cat,
        currency=currency,
        quantity=quantity,
        cost_basis=cost_basis,
        close_price=close_price,
        market_value=value,
        unrealized_pl=unrealized_pl,
      )
    )

  def _calculate_cash_positions(self, statement: IBKRStatement) -> None:
    """Computes cash / money market balances for each account from NAV Summary minus total position values."""
    account_pos_val_base = {}

    for pos in statement.positions:
      val_base = pos.market_value
      if pos.currency == "CAD" and statement.base_currency == "USD":
        val_base = pos.market_value * statement.cad_to_usd_rate
      elif pos.currency == "USD" and statement.base_currency == "CAD":
        val_base = pos.market_value / statement.cad_to_usd_rate

      account_pos_val_base[pos.account_id] = (
        account_pos_val_base.get(pos.account_id, 0.0) + val_base
      )

    statement.cash_positions.clear()
    for acc_id, account in statement.accounts.items():
      pos_val = account_pos_val_base.get(acc_id, 0.0)
      cash_val = round(account.ending_nav - pos_val, 4)

      # If residual cash is non-zero (greater than 0.005 USD/CAD)
      if abs(cash_val) >= 0.005:
        statement.cash_positions.append(
          Position(
            source="IBKR",
            account_id=acc_id,
            symbol=f"{account.base_currency}.CASH",
            asset_category="Cash",
            currency=account.base_currency,
            quantity=cash_val,
            cost_basis=cash_val,
            close_price=1.0,
            market_value=cash_val,
            unrealized_pl=0.0,
          )
        )

  @staticmethod
  def _infer_tax_treatment(account_id: str, account_type: str) -> TaxTreatment:
    lower_id = account_id.lower()
    lower_type = account_type.lower()

    if "master" in lower_type or "master" in lower_id:
      return TaxTreatment.MASTER
    if "tfsa" in lower_id or "tsfa" in lower_id or "tfsa" in lower_type:
      return TaxTreatment.TAX_FREE
    if "rrsp" in lower_id or "srsp" in lower_id or "rrsp" in lower_type:
      return TaxTreatment.TAX_DEFERRED
    if "margin" in lower_id or "cash" in lower_id or "taxable" in lower_type:
      return TaxTreatment.TAXABLE
    return TaxTreatment.TAXABLE


def parse_ibkr_csv(
  file_path: str | Path, account_metadata_overrides: dict[str, dict] | None = None
) -> IBKRStatement:
  """Convenience helper to parse an IBKR CSV statement file."""
  parser = IBKRParser(account_metadata_overrides=account_metadata_overrides)
  return parser.parse_file(file_path)
