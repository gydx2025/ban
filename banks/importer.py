from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Iterable, List, Mapping, Protocol


@dataclass
class Transaction:
    """Normalized transaction structure shared across importers."""

    date: date
    category: str
    amount: Decimal
    channel: str
    memo: str
    reference: str


class BaseBankImporter(Protocol):
    """Interface for bank importers.

    Each importer should parse its own statement format and expose normalized
    :class:`Transaction` objects via :meth:`normalize`.
    """

    bank_name: str
    file_extensions: Iterable[str]

    def parse(self, source: Path) -> List[Mapping[str, str]]:  # pragma: no cover - interface
        """Parse raw records from a statement file."""

    def normalize(self, source: Path) -> List[Transaction]:  # pragma: no cover - interface
        """Return normalized transactions."""


def parse_amount(raw_amount: str, debit_indicator: str | None = None) -> Decimal:
    """Parse monetary values and apply debit/credit sign.

    Args:
        raw_amount: string representation of the numeric value.
        debit_indicator: if provided, values of ``"debit"`` or ``"支出"`` are
            treated as negative.
    """

    cleaned = raw_amount.replace(",", "").strip()
    try:
        value = Decimal(cleaned)
    except (InvalidOperation, AttributeError) as exc:  # pragma: no cover - defensive
        raise ValueError(f"Invalid amount: {raw_amount}") from exc

    if debit_indicator and debit_indicator.lower() in {"debit", "支出", "out"}:
        return -value
    return value


def parse_date(raw: str, fmt: str | None = None) -> date:
    """Parse date strings with optional format override."""

    guess_formats = [fmt] if fmt else ["%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d"]
    for candidate in guess_formats:
        try:
            return datetime.strptime(raw.strip(), candidate).date()
        except (ValueError, TypeError):
            continue
    raise ValueError(f"Unsupported date format: {raw}")
