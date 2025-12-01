#!/usr/bin/env python3
"""Fetch investment property balance for a given A-share code from Sina Finance.

Usage:
    python sina_investment_property.py 600000

The script downloads the balance sheet for 2024 and extracts the line item
"投资性房地产" as of 2024-12-31. It requires the `requests` and `pandas`
packages. If they are not available, install them with:
    pip install requests pandas lxml
"""
from __future__ import annotations

import argparse
import sys
from typing import Optional

import pandas as pd
import requests

YEAR = 2024
REPORT_DAY_MARKERS = ("12-31", "12/31")
LINE_LABEL = "投资性房地产"


def build_url(stock_code: str, year: int = YEAR) -> str:
    """Build the Sina Finance balance-sheet URL for the given stock code."""
    code = stock_code.strip()
    if not code.isdigit() or len(code) != 6:
        raise ValueError("stock code must be a 6-digit number")
    return (
        "http://money.finance.sina.com.cn/corp/go.php/vFD_BalanceSheet/"
        f"stockid/{code}/ctrl/{year}/displaytype/4.phtml"
    )


def fetch_balance_sheet(url: str) -> pd.DataFrame:
    """Download the balance-sheet page and return it as a DataFrame."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0 Safari/537.36"
        )
    }
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    tables = pd.read_html(resp.text)
    if not tables:
        raise ValueError("No tables found on the balance-sheet page.")
    return tables[0]


def find_report_column(columns) -> Optional[str]:
    """Return the column that matches the 2024-12-31 report date."""
    for col in columns:
        col_str = str(col)
        if str(YEAR) in col_str and any(marker in col_str for marker in REPORT_DAY_MARKERS):
            return col
    return None


def extract_investment_property(df: pd.DataFrame) -> Optional[str]:
    """Extract the investment-property balance from the DataFrame."""
    if df.empty:
        return None

    date_column = find_report_column(df.columns)
    if date_column is None:
        return None

    label_col = df.columns[0]
    matched_rows = df[df[label_col].astype(str).str.contains(LINE_LABEL, na=False)]
    if matched_rows.empty:
        return None

    value = matched_rows.iloc[0][date_column]
    if pd.isna(value):
        return None
    return str(value)


def query_investment_property(stock_code: str) -> str:
    """Query Sina Finance for the investment-property balance."""
    url = build_url(stock_code)
    sheet = fetch_balance_sheet(url)
    value = extract_investment_property(sheet)
    if value is None:
        raise RuntimeError(
            "未能在报表中找到 2024-12-31 的投资性房地产数据，"
            "可能是数据尚未发布或页面结构发生变化。"
        )
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="查询A股公司投资性房地产余额（2024-12-31）")
    parser.add_argument("stock_code", help="6位股票代码，如 600000 或 000001")
    args = parser.parse_args(argv)

    try:
        balance = query_investment_property(args.stock_code)
        print(f"股票 {args.stock_code} 在 2024-12-31 的投资性房地产余额：{balance}")
    except Exception as exc:  # noqa: BLE001
        print(f"查询失败：{exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
