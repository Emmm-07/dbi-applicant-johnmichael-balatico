"""SQLite helper. Pre-wired so you don't spend time on boilerplate.
You may replace SQLite with Postgres if you prefer - say so in DECISIONS.md."""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "tenant_sales.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn
