from decimal import Decimal
from datetime import date
from pathlib import Path

import pytest

from mobile_app import Ledger, PaymentEvent, RealTimePromptManager
from banks.importer import Transaction


FIXTURE_DIR = Path(__file__).parent / "fixtures"


def test_statement_import_and_deduplication():
    ledger = Ledger()
    # importing both statements should add four entries
    added = ledger.import_statements([FIXTURE_DIR / "icbc.csv", FIXTURE_DIR / "ccb.txt"])
    assert added == 4

    # re-importing the same files should not create duplicates
    added_again = ledger.import_statements([FIXTURE_DIR / "icbc.csv", FIXTURE_DIR / "ccb.txt"])
    assert added_again == 0
    assert len(ledger.entries) == 4


def test_real_time_prompt_and_confirm():
    ledger = Ledger()
    manager = RealTimePromptManager(ledger)
    event = PaymentEvent(
        amount=Decimal("-36.50"),
        channel="WeChat",
        memo="便利店购物",
        reference="WX1001",
        category_hint="日用百货",
    )

    prompt = manager.build_prompt(event)
    assert "支出 ￥36.50" in prompt
    assert "WeChat" in prompt

    confirmed = manager.confirm_event(event, category="日用百货")
    assert confirmed is True
    assert len(ledger.entries) == 1
    entry = ledger.entries[0]
    assert entry.transaction.category == "日用百货"
    assert entry.net_amount == Decimal("-36.50")

    # confirming the same event again should be ignored as duplicate
    duplicate = manager.confirm_event(event, category="日用百货")
    assert duplicate is False


def test_red_envelope_annotation():
    ledger = Ledger()
    txn = Transaction(
        date=date(2024, 1, 1),
        category="餐饮",
        amount=Decimal("-50.00"),
        channel="Alipay",
        memo="午餐",
        reference="ALI2001",
    )
    ledger.add_entry(txn, source="Alipay")

    updated = ledger.annotate_red_envelope("ALI2001", Decimal("10.00"))
    assert updated is True
    assert ledger.entries[0].red_envelope == Decimal("10.00")
    assert ledger.entries[0].net_amount == Decimal("-40.00")

    missing = ledger.annotate_red_envelope("NOT_FOUND", Decimal("5"))
    assert missing is False
