"""
web scraper cao tin tuc chung khoan tieng viet tu cafef theo tung ma vn30.
uu tien lay full text tieu de, luu pub_time (HH:mm), doi tin >=14:45 va ngay le sang phien ke tiep.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup

from src.config import DATA_RAW_DIR, END_DATE, SQLITE_DB_PATH, START_DATE, VN30_TICKERS
from src.ingestion.db import get_connection, init_db, insert_news_records
from src.ingestion.http_client import fetch_url
from src.ingestion.sentiment import score_vietnamese_headline

HOSE_CLOSE_TIME = "14:45"
MIN_HEADLINE_LEN = 15


def parse_cafef_news_html(html: str, ticker: str) -> list[tuple[str, str, str, str, float]]:
    """boc tach DOM html cafef -> danh sach (ticker, pub_date, pub_time, headline, sentiment_score)."""
    if not html:
        return []
    soup = BeautifulSoup(html, "html.parser")
    records: list[tuple[str, str, str, str, float]] = []
    for li in soup.find_all("li"):
        time_span = li.find("span", class_="timeTitle")
        link_tag = li.find("a", class_="docnhanhTitle") or li.find("a")
        if not time_span or not link_tag:
            continue
        raw_time = time_span.get_text(strip=True)
        # uu tien get_text() de tranh loi cat cut attribute title="..." chua dau ngoac kep
        headline = link_tag.get_text(strip=True) or link_tag.get("title") or ""
        clean_title = " ".join(str(headline).split())
        if not raw_time or len(clean_title) < MIN_HEADLINE_LEN:
            continue
        parts = raw_time.split()
        dt = pd.to_datetime(parts[0], format="%d/%m/%Y", errors="coerce")
        if pd.isna(dt):
            continue
        pub_time = parts[1][:5] if len(parts) > 1 and ":" in parts[1] else ""
        records.append((ticker, dt.strftime("%Y-%m-%d"), pub_time, clean_title, score_vietnamese_headline(clean_title)))
    return records


def crawl_ticker_news(
    ticker: str,
    start_date: str = START_DATE,
    end_date: str = END_DATE,
    max_pages: int = 60,
    page_size: int = 30,
    db_path: Path = SQLITE_DB_PATH,
) -> int:
    """cao tin tuc theo watermark trong [start_date, end_date], dung som khi trung hoac het tin."""
    total_inserted = 0
    for page in range(1, max_pages + 1):
        url = (
            f"https://cafef.vn/du-lieu/Ajax/Events_RelatedNews_New.aspx"
            f"?symbol={ticker}&floorID=0&configID=0&PageIndex={page}&PageSize={page_size}&Type=2"
        )
        try:
            html = fetch_url(url, as_json=False, min_delay=0.25, max_delay=0.55)
            records = parse_cafef_news_html(html, ticker)
            if not records:
                break
            oldest_date = min(r[1] for r in records)
            in_range = [r for r in records if start_date <= r[1] <= end_date]
            inserted = insert_news_records(in_range, db_path=db_path)
            total_inserted += inserted
            if (in_range and inserted == 0) or oldest_date < start_date:
                break
        except (requests.RequestException, RuntimeError, ValueError) as exc:
            print(f"[WARN] Failed scraping {ticker} page {page}: {exc}")
            break
    return total_inserted


def _map_to_next_trading_day(dates: pd.Series, prices_path: Path) -> pd.Series:
    """anh xa ngay tin tuc sang phien giao dich ke tiep gan nhat (xu ly ca cuoi tuan & le Tet)."""
    if prices_path.exists():
        trading_dates = np.sort(pd.read_parquet(prices_path, columns=["date"])["date"].unique())
        idx = np.searchsorted(trading_dates, dates.to_numpy(dtype="datetime64[ns]"), side="left")
        mapped = [trading_dates[i] if i < len(trading_dates) else pd.NaT for i in idx]
        return pd.Series(pd.to_datetime(mapped), index=dates.index)
    weekday = dates.dt.weekday
    return (dates + pd.to_timedelta((weekday == 5) * 2 + (weekday == 6) * 1, unit="D")).dt.normalize()


def export_news_sentiment_parquet(
    start_date: str = START_DATE,
    end_date: str = END_DATE,
    output_dir: Path = DATA_RAW_DIR,
    db_path: Path = SQLITE_DB_PATH,
) -> pd.DataFrame:
    """xuat news_sentiment.parquet tu raw_news: bo tieu de cut, doi tin >=14:45 & le sang phien sau."""
    with get_connection(db_path) as conn:
        df_raw = pd.read_sql_query(
            "SELECT pub_date AS date, COALESCE(pub_time, '') AS pub_time, ticker, headline, sentiment_score "
            "FROM raw_news WHERE pub_date >= ? AND pub_date <= ? AND LENGTH(headline) >= ?",
            conn,
            params=[start_date, end_date, MIN_HEADLINE_LEN],
        )
    if df_raw.empty:
        df_agg = pd.DataFrame(columns=["date", "ticker", "news_count", "sentiment_score", "sample_headline"])
    else:
        eff_date = pd.to_datetime(df_raw["date"])
        # tin dang sau gio dong cua hose (14:45) duoc tinh vao phien giao dich ngay hom sau
        after_close = df_raw["pub_time"].astype(str).str.slice(0, 5) >= HOSE_CLOSE_TIME
        eff_date = eff_date + pd.to_timedelta(after_close.astype(int), unit="D")
        df_raw["date"] = _map_to_next_trading_day(eff_date, output_dir / "prices.parquet")
        df_raw = df_raw.dropna(subset=["date"])
        df_raw = df_raw[df_raw["date"] <= pd.Timestamp(end_date)]

        df_agg = (
            df_raw.groupby(["date", "ticker"], as_index=False)
            .agg(
                news_count=("headline", "count"),
                sentiment_score=("sentiment_score", "mean"),
                sample_headline=("headline", "first"),
            )
            .sort_values(["ticker", "date"])
            .reset_index(drop=True)
        )
        df_agg["date"] = pd.to_datetime(df_agg["date"]).astype("datetime64[ns]")
        df_agg["news_count"] = df_agg["news_count"].astype("int64")
        df_agg["sentiment_score"] = df_agg["sentiment_score"].round(4).astype("float64")

    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / "news_sentiment.parquet"
    df_agg.to_parquet(out_path, index=False)
    print(f"[OK] Saved {len(df_agg):,} daily ticker-news rows (from {len(df_raw):,} articles) to {out_path}")
    return df_agg


def sync_all_news(
    tickers: list[str] = VN30_TICKERS,
    start_date: str = START_DATE,
    end_date: str = END_DATE,
    max_pages_per_ticker: int = 60,
    output_dir: Path = DATA_RAW_DIR,
    db_path: Path = SQLITE_DB_PATH,
) -> pd.DataFrame:
    """dong bo tin tuc cafef trong [start_date, end_date] va xuat news_sentiment.parquet."""
    init_db(db_path)
    for idx, ticker in enumerate(tickers, start=1):
        print(f"[{idx:02d}/{len(tickers)}] Syncing CafeF news for {ticker} ({start_date} -> {end_date})...")
        new_count = crawl_ticker_news(
            ticker, start_date=start_date, end_date=end_date, max_pages=max_pages_per_ticker, db_path=db_path
        )
        print(f"    -> Inserted {new_count} new articles for {ticker}")
    return export_news_sentiment_parquet(start_date=start_date, end_date=end_date, output_dir=output_dir, db_path=db_path)
