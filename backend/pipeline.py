"""Tenant sales pipeline.

Reads data/tenant_sales_raw.csv, cleans it, and loads it into SQLite.

    python pipeline.py

Written in a hurry by someone who has since left. It runs and it produces
numbers. The numbers are wrong.
"""
import csv
import re
import sqlite3
from datetime import date, datetime
from pathlib import Path

from db import get_conn

RAW_CSV = Path(__file__).parent.parent / "data" / "tenant_sales_raw.csv"

MALLS = {
    "sm north edsa": "SM North EDSA",
    "sm nort edsa": "SM North EDSA",
    "sm megamall": "SM Megamall",
    "sm mega mall": "SM Megamall",
    "sm mall of asia": "SM Mall of Asia",
    "mall of asia": "SM Mall of Asia",
    "sm southmall": "SM Southmall",
    "sm south mall": "SM Southmall",
}

CATEGORIES = {
    "f&b": "Food & Beverage",
    "food & beverage": "Food & Beverage",
    "food and beverage": "Food & Beverage",
    "f and b": "Food & Beverage",
    "food and bev": "Food & Beverage",
    "apparel": "Apparel",
    "fashion/apparel": "Apparel",
    "services": "Services",
    "service": "Services",
    "electronics": "Electronics",
    "gadgets/electronics": "Electronics",
    "home": "Home",
    "home & living": "Home",
}

NULLS = {"", "N/A", "n/a", "NULL", "-", "#N/A", "none"}

SCHEMA = """
CREATE TABLE IF NOT EXISTS sales (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_code     TEXT,
    tenant_name     TEXT,
    mall            TEXT,
    category        TEXT,
    report_month    TEXT,
    gross_sales     REAL,
    floor_area_sqm  REAL
);
"""


def is_null(value):
    return value.strip() in NULLS


def parse_money(value):
    """Turn '1,234.50', '₱1,234.50' or '(1,234.50)' into a float."""
    if is_null(value):
        return None
    text = value.strip().replace("₱", "").replace(",", "")
    negative = text.startswith("(") and text.endswith(")")
    text = text.replace("(", "").replace(")", "")
    try:
        result = float(text)
        return -result if negative else result
    except ValueError:
        return None


def parse_date(value):
    """Handle the date formats we have seen in this feed."""
    if is_null(value):
        return None
    text = value.strip()
    match = re.fullmatch(r"(\d{4})[-/](\d{1,2})[-/](\d{1,2})", text)
    if match:
        year, month, day = (int(g) for g in match.groups())
        return date(year, month, day)
    match = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{4})", text)
    if match:
        day, month, year = (int(g) for g in match.groups())
        return date(year, month, day)
    match = re.fullmatch(r"([A-Za-z]{3})\s+(\d{4})", text)
    if match:
        return datetime.strptime(f"01 {match.group(1)} {match.group(2)}", "%d %b %Y").date()
    return None


def clean_rows(raw_rows):
    cleaned = []
    seen = set()
    rejected = {"duplicate": 0, "no_sales": 0, "bad_date": 0}

    for row in raw_rows:
        code = row["tenant_code"].strip()
        key = (code, row["report_month"])
        if key in seen:
            rejected["duplicate"] += 1
            continue
        seen.add(key)

        sales = parse_money(row["gross_sales"])
        if sales is None:
            rejected["no_sales"] += 1
            continue

        month = parse_date(row["report_month"])
        if month is None:
            rejected["bad_date"] += 1
            continue

        cleaned.append({
            "tenant_code": code,
            "tenant_name": row["tenant_name"].strip(),
            "mall": MALLS.get(row["mall"].strip().lower(), row["mall"].strip()),
            "category": CATEGORIES.get(row["category"].strip().lower(), row["category"].strip()),
            "report_month": month.isoformat()[:7],
            "gross_sales": sales,
            "floor_area_sqm": parse_money(row["floor_area_sqm"]),
        })

    return cleaned, rejected


def load(rows):
    conn = get_conn()
    conn.executescript(SCHEMA)
    conn.execute("DELETE FROM sales")
    conn.executemany(
        """INSERT INTO sales
           (tenant_code, tenant_name, mall, category, report_month,
            gross_sales, floor_area_sqm)
           VALUES (:tenant_code, :tenant_name, :mall, :category,
                   :report_month, :gross_sales, :floor_area_sqm)""",
        rows,
    )
    conn.commit()
    return conn


def summarise(conn):
    print("\nTop 5 tenants by total sales")
    for name, total in conn.execute(
        """SELECT tenant_name, SUM(gross_sales) AS total
             FROM sales
         GROUP BY LOWER(tenant_name)
         ORDER BY total DESC
            LIMIT 5"""
    ):
        print(f"  {name:<28} {total:>18,.2f}")

    print("\nTotal sales by mall")
    for mall, total in conn.execute(
        """SELECT mall, SUM(gross_sales) AS total
             FROM sales
         GROUP BY mall
         ORDER BY total DESC"""
    ):
        print(f"  {str(mall):<28} {total:>18,.2f}")


def main():
    with open(RAW_CSV, newline="", encoding="utf-8") as handle:
        raw_rows = list(csv.DictReader(handle))

    rows, rejected = clean_rows(raw_rows)
    conn = load(rows)

    print(f"rows read:     {len(raw_rows)}")
    print(f"rows loaded:   {len(rows)}")
    print(f"rows rejected: {sum(rejected.values())}  {rejected}")
    summarise(conn)
    conn.close()


if __name__ == "__main__":
    main()
