from __future__ import annotations

import csv
from pathlib import Path
from typing import List, Mapping

from .importer import BaseBankImporter, Transaction, parse_amount, parse_date


class CCBImporter:
    """Importer for China Construction Bank statement exports.

    The bank often provides Excel files; tests rely on tab-delimited text to
    avoid binary dependencies, but the column mapping mirrors the spreadsheet
    layout.
    """

    bank_name = "CCB"
    file_extensions = {".txt", ".tsv"}

    def parse(self, source: Path) -> List[Mapping[str, str]]:
        with open(source, "r", encoding="utf-8") as handle:
            # skip metadata line starting with "CCB"
            first = handle.readline()
            delimiter = "\t"
            if first.lower().startswith("ccb pdf"):
                # PDF text export separates fields with two spaces
                delimiter = "  "
            reader = csv.DictReader(handle, delimiter=delimiter)
            return [row for row in reader]

    def normalize(self, source: Path) -> List[Transaction]:
        transactions: List[Transaction] = []
        for row in self.parse(source):
            flow = row.get("in_out", "").lower() or row.get("收支") or ""
            amount = parse_amount(row.get("amount", "0"), debit_indicator="debit" if flow == "out" else None)
            transactions.append(
                Transaction(
                    date=parse_date(row.get("date", "")),
                    category=row.get("category", "").strip(),
                    amount=amount,
                    channel=row.get("channel", "").strip(),
                    memo=row.get("note", "").strip() or row.get("memo", "").strip(),
                    reference=row.get("ref", "").strip() or row.get("reference", "").strip(),
                )
            )
        return transactions


__all__ = ["CCBImporter"]
