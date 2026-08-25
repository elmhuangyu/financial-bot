"""Manulife Group Retirement Statement Parser."""

import re
from pathlib import Path
from typing import TextIO

from src.core.models import Position


class ManulifeParser:
  """Parser for Manulife group retirement text exports."""

  def parse_file(
    self,
    file_path: str | Path,
    account_id: str = "MANULIFE/group-rrsp",
    currency: str = "CAD",
  ) -> list[Position]:
    path = Path(file_path)
    with path.open("r", encoding="utf-8") as f:
      return self.parse_stream(f, account_id=account_id, currency=currency)

  def parse_stream(
    self,
    stream: TextIO,
    account_id: str = "MANULIFE/group-rrsp",
    currency: str = "CAD",
  ) -> list[Position]:
    text = stream.read()
    return self.parse_text(text, account_id=account_id, currency=currency)

  def parse_text(
    self,
    text: str,
    account_id: str = "MANULIFE/group-rrsp",
    currency: str = "CAD",
  ) -> list[Position]:
    positions = []

    # Pattern looks for:
    # (Image icon )?(\d{4}) - (ML [^\n]+)
    # followed by rows with units, unit value, total
    fund_blocks = re.split(r"(?:Image icon\s+)?(\d{4})\s*-\s*([^\n]+)", text)

    # If splitting yields blocks: [preamble, fund_code, fund_name, text_after, ...]
    if len(fund_blocks) >= 4:
      for i in range(1, len(fund_blocks), 3):
        fund_code = fund_blocks[i].strip()
        _fund_name = fund_blocks[i + 1].strip()
        block_content = fund_blocks[i + 2]

        total_match = re.search(r"TOTAL\s+\$([\d,]+\.?\d*)", block_content)
        if not total_match:
          continue

        total_value = float(total_match.group(1).replace(",", ""))

        # Find unit value and sum of units
        unit_values = re.findall(
          r"(\d+[\d,]*\.\d+)\s+(\d+[\d,]*\.\d+)\s+([\d,]+\.\d+)",
          block_content,
        )
        total_quantity = 0.0
        unit_price = 0.0

        if unit_values:
          for units_str, price_str, _ in unit_values:
            total_quantity += float(units_str.replace(",", ""))
            unit_price = float(price_str.replace(",", ""))
        else:
          total_quantity = 1.0
          unit_price = total_value

        symbol = f"ML_{fund_code}"
        positions.append(
          Position(
            source="Manulife",
            account_id=account_id,
            symbol=symbol,
            asset_category="Mutual Funds",
            currency=currency,
            quantity=total_quantity,
            cost_basis=total_value,
            close_price=unit_price,
            market_value=total_value,
            unrealized_pl=0.0,
          )
        )

    return positions
