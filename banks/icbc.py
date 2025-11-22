from __future__ import annotations

import csv
from pathlib import Path
from typing import List, Mapping

from .importer import BaseBankImporter, Transaction, parse_amount, parse_date


class ICBCImporter:
    """Importer for Industrial and Commercial Bank of China CSV exports."""

    bank_name = "ICBC"
    file_extensions = {".csv"}

    def parse(self, source: Path) -> List[Mapping[str, str]]:
        with open(source, "r", encoding="utf-8") as handle:
            lines = handle.readlines()

        # Skip metadata line such as "ICBC export 2024"
        if lines and "date" not in lines[0].lower():
            lines = lines[1:]

        reader = csv.DictReader(lines)
        return [row for row in reader]

    def normalize(self, source: Path) -> List[Transaction]:
        records = self.parse(source)
        transactions: List[Transaction] = []
        for row in records:
            debit_credit = row.get("type", "").lower() or row.get("收支")
            amount = parse_amount(row.get("amount", "0"), debit_indicator=debit_credit)
            transactions.append(
                Transaction(
                    date=parse_date(row.get("date", "")),
                    category=row.get("category", "").strip() or "",
                    amount=amount,
                    channel=row.get("channel", "").strip(),
                    memo=row.get("memo", "").strip(),
                    reference=row.get("reference", "").strip(),
                )
            )
        return transactions


__all__ = ["ICBCImporter"]
