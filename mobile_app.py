"""Mobile-first bookkeeping helpers built on top of bank importers."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from banks.importer import Transaction
from banks.router import get_importer


@dataclass
class LedgerEntry:
    """Wrap a :class:`Transaction` with mobile-specific metadata."""

    transaction: Transaction
    source: str
    confirmed: bool = True
    red_envelope: Decimal = Decimal("0")

    @property
    def net_amount(self) -> Decimal:
        """Return the amount after red-envelope deduction."""

        return self.transaction.amount + self.red_envelope


class Ledger:
    """In-memory ledger that deduplicates imported and real-time entries."""

    def __init__(self):
        self.entries: List[LedgerEntry] = []
        self._dedupe_keys: set[tuple] = set()

    def _fingerprint(self, txn: Transaction) -> tuple:
        return (
            txn.date,
            txn.amount,
            txn.reference or txn.memo,
            txn.channel,
        )

    def add_entry(
        self,
        txn: Transaction,
        source: str,
        confirmed: bool = True,
        red_envelope: Decimal = Decimal("0"),
    ) -> bool:
        """Add a transaction if it is not a duplicate.

        Returns ``True`` if inserted, ``False`` if ignored as duplicate.
        """

        fingerprint = self._fingerprint(txn)
        if fingerprint in self._dedupe_keys:
            return False

        self._dedupe_keys.add(fingerprint)
        self.entries.append(
            LedgerEntry(
                transaction=txn,
                source=source,
                confirmed=confirmed,
                red_envelope=red_envelope,
            )
        )
        return True

    def import_statements(
        self, sources: Iterable[Path], bank_hints: Optional[Dict[Path, str]] = None
    ) -> int:
        """Import multiple statements with duplicate elimination.

        Args:
            sources: iterable of paths to bank or payment platform statements.
            bank_hints: optional mapping from path to bank code to speed up detection.

        Returns the number of unique transactions added.
        """

        added = 0
        for source in sources:
            hint = None
            if bank_hints and source in bank_hints:
                hint = bank_hints[source]
            importer = get_importer(source, bank_hint=hint)
            for txn in importer.normalize(source):
                if self.add_entry(txn, source=str(source)):
                    added += 1
        return added

    def annotate_red_envelope(self, reference: str, deduction: Decimal) -> bool:
        """Attach a red-envelope deduction to an existing entry."""

        for entry in self.entries:
            if entry.transaction.reference == reference:
                entry.red_envelope = deduction
                return True
        return False


@dataclass
class PaymentEvent:
    """Real-time payment event emitted by mobile wallets or banks."""

    amount: Decimal
    channel: str
    memo: str
    reference: str
    category_hint: str = ""
    happened_at: date = field(default_factory=lambda: datetime.now().date())


class RealTimePromptManager:
    """Generate confirmation prompts and commit real-time events."""

    def __init__(self, ledger: Ledger):
        self.ledger = ledger

    def build_prompt(self, event: PaymentEvent) -> str:
        """Return a human-readable summary for confirmation dialogs."""

        direction = "收入" if event.amount > 0 else "支出"
        amount_display = f"￥{abs(event.amount):.2f}"
        return (
            f"{event.happened_at.isoformat()} {direction} {amount_display} "
            f"通过{event.channel}：{event.memo}"
        )

    def confirm_event(
        self,
        event: PaymentEvent,
        category: str,
        red_envelope: Decimal = Decimal("0"),
    ) -> bool:
        """Convert a confirmed event into a ledger entry."""

        txn = Transaction(
            date=event.happened_at,
            category=category or event.category_hint,
            amount=event.amount,
            channel=event.channel,
            memo=event.memo,
            reference=event.reference,
        )
        return self.ledger.add_entry(txn, source=event.channel, red_envelope=red_envelope)


__all__ = [
    "Ledger",
    "LedgerEntry",
    "PaymentEvent",
    "RealTimePromptManager",
]
