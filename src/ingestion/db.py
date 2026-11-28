"""
quan ly sqlite database cache de luu tru du lieu da keo va cao.
giup tranh cao lai tu dau va chong trung lap bang khoa chinh.
"""

import sqlite3
from pathlib import Path

import pandas as pd

from src.config import SQLITE_DB_PATH


def get_connection(db_path: Path = SQLITE_DB_PATH) -> sqlite3.Connection:
    """mo ket noi sqlite va dam bao thu muc cha ton tai."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(db_path)


def init_db(db_path: Path = SQLITE_DB_PATH) -> None:
    """khoi tao 4 bang prices, raw_news, macro, sentiment_labels va tu dong bo sung cot pub_time."""
    with get_connection(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS prices (
                date TEXT NOT NULL, ticker TEXT NOT NULL,
                open REAL, high REAL, low REAL, close REAL, volume REAL, sector TEXT,
                PRIMARY KEY (date, ticker)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS raw_news (
                ticker TEXT NOT NULL, pub_date TEXT NOT NULL,
                pub_time TEXT DEFAULT '', headline TEXT NOT NULL,
                sentiment_score REAL NOT NULL,
                PRIMARY KEY (ticker, pub_date, headline)
            )
            """
        )
        cols = {r[1] for r in conn.execute("PRAGMA table_info(raw_news)").fetchall()}
        if "pub_time" not in cols:
            conn.execute("ALTER TABLE raw_news ADD COLUMN pub_time TEXT DEFAULT ''")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS macro (
                date TEXT PRIMARY KEY, vnindex_close REAL, vnindex_return_1d REAL,
                vnindex_volatility_20d REAL, usd_vnd_rate REAL, sbv_policy_rate REAL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sentiment_labels (
                headline TEXT PRIMARY KEY, llm_label INTEGER NOT NULL
            )
            """
        )
        conn.commit()


def has_ticker_prices(ticker: str, min_rows: int = 500, db_path: Path = SQLITE_DB_PATH) -> bool:
    """kiem tra xem ma co phieu da co du du lieu gia trong sqlite chua."""
    with get_connection(db_path) as conn:
        count = conn.execute("SELECT COUNT(*) FROM prices WHERE ticker = ?", (ticker,)).fetchone()[0]
    return count >= min_rows


def get_ticker_price_bounds(ticker: str, db_path: Path = SQLITE_DB_PATH) -> tuple[str | None, str | None]:
    """tra ve moc ngay (min_date, max_date) hien co trong bang prices cua 1 ma."""
    with get_connection(db_path) as conn:
        row = conn.execute("SELECT MIN(date), MAX(date) FROM prices WHERE ticker = ?", (ticker,)).fetchone()
    return (row[0], row[1]) if row else (None, None)


def has_ticker_news(ticker: str, min_rows: int = 15, db_path: Path = SQLITE_DB_PATH) -> bool:
    """kiem tra xem ma co phieu da cao du tin tuc trong sqlite chua."""
    with get_connection(db_path) as conn:
        count = conn.execute("SELECT COUNT(*) FROM raw_news WHERE ticker = ?", (ticker,)).fetchone()[0]
    return count >= min_rows


def upsert_prices(df: pd.DataFrame, db_path: Path = SQLITE_DB_PATH) -> None:
    """luu bang gia cua 1 ticker vao sqlite, ghi de dong trung khoa chinh."""
    if df.empty:
        return
    rows = df[["date", "ticker", "open", "high", "low", "close", "volume", "sector"]].copy()
    rows["date"] = pd.to_datetime(rows["date"]).dt.strftime("%Y-%m-%d")
    with get_connection(db_path) as conn:
        conn.executemany(
            """
            INSERT OR REPLACE INTO prices (date, ticker, open, high, low, close, volume, sector)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows.itertuples(index=False, name=None),
        )
        conn.commit()


def insert_news_records(
    records: list[tuple[str, str, str, str, float]], db_path: Path = SQLITE_DB_PATH
) -> int:
    """luu danh sach tin tuc (ticker, pub_date, pub_time, headline, score), bo qua trung."""
    if not records:
        return 0
    with get_connection(db_path) as conn:
        before = conn.total_changes
        conn.executemany(
            """
            INSERT OR IGNORE INTO raw_news (ticker, pub_date, pub_time, headline, sentiment_score)
            VALUES (?, ?, ?, ?, ?)
            """,
            records,
        )
        conn.commit()
        return conn.total_changes - before
