from pathlib import Path
from decimal import Decimal

import pytest

from banks.icbc import ICBCImporter
from banks.ccb import CCBImporter
from banks.importer import Transaction
from banks.router import detect_bank, get_importer


FIXTURE_DIR = Path(__file__).parent / "fixtures"


def test_icbc_normalization():
    importer = ICBCImporter()
    transactions = importer.normalize(FIXTURE_DIR / "icbc.csv")
    assert len(transactions) == 2
    first, second = transactions

    assert isinstance(first, Transaction)
    assert first.date.isoformat() == "2024-01-02"
    assert first.amount == Decimal("-123.45")
    assert first.category == "餐饮"
    assert first.channel == "POS"
    assert first.memo.startswith("超市")
    assert first.reference == "A1001"

    assert second.amount == Decimal("2000.00")
    assert second.category == "收入"


def test_ccb_normalization():
    importer = CCBImporter()
    transactions = importer.normalize(FIXTURE_DIR / "ccb.txt")
    assert len(transactions) == 2
    first, second = transactions

    assert first.amount == Decimal("-88.00")
    assert first.channel == "Online"
    assert first.category == "餐饮"
    assert first.reference == "C2001"

    assert second.amount == Decimal("1500.00")
    assert second.memo.startswith("二月")


def test_router_detects_and_routes():
    icbc_path = FIXTURE_DIR / "icbc.csv"
    ccb_path = FIXTURE_DIR / "ccb.txt"

    assert detect_bank(icbc_path) == "icbc"
    assert detect_bank(ccb_path) == "ccb"

    importer = get_importer(icbc_path)
    assert isinstance(importer, ICBCImporter)
    importer = get_importer(ccb_path)
    assert isinstance(importer, CCBImporter)

    # user hint should bypass detection
    importer = get_importer(ccb_path, bank_hint="ICBC")
    assert isinstance(importer, ICBCImporter)


def test_router_errors_on_unknown_bank(tmp_path: Path):
    dummy = tmp_path / "unknown.txt"
    dummy.write_text("mystery bank\n", encoding="utf-8")
    with pytest.raises(ValueError):
        get_importer(dummy)
