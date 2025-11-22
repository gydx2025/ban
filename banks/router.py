from __future__ import annotations

from pathlib import Path
from typing import Dict, Type

from .ccb import CCBImporter
from .icbc import ICBCImporter
from .importer import BaseBankImporter

REGISTRY: Dict[str, Type[BaseBankImporter]] = {
    "icbc": ICBCImporter,
    "ccb": CCBImporter,
}


def detect_bank(source: Path) -> str | None:
    """Infer bank from filename or file header."""

    name = source.name.lower()
    if "icbc" in name or "gongshang" in name:
        return "icbc"
    if "ccb" in name or "jianshe" in name:
        return "ccb"

    try:
        with open(source, "r", encoding="utf-8") as handle:
            head = handle.readline().lower()
            if "icbc" in head or "工商银行" in head:
                return "icbc"
            if "ccb" in head or "建设银行" in head:
                return "ccb"
    except FileNotFoundError:  # pragma: no cover - defensive
        return None
    return None


def get_importer(source: Path, bank_hint: str | None = None) -> BaseBankImporter:
    """Return an importer instance based on hint or detection."""

    code = bank_hint.lower() if bank_hint else detect_bank(source)
    if not code:
        raise ValueError("Unable to determine bank for provided file")

    importer_cls = REGISTRY.get(code)
    if not importer_cls:
        raise ValueError(f"No importer registered for bank {code}")
    return importer_cls()


__all__ = ["get_importer", "detect_bank", "REGISTRY"]
