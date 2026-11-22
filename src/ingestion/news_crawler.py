"""
web scraper cao tin tuc chung khoan tieng viet tu cafef theo tung ma vn30.
su dung beautifulsoup4 boc tach html dom, luu sqlite cache va xuat news_sentiment.parquet.
"""

from pathlib import Path
from bs4 import BeautifulSoup
import pandas as pd
from src.config import DATA_RAW_DIR, END_DATE, SQLITE_DB_PATH, START_DATE, VN30_TICKERS
from src.ingestion.db import (
    get_connection,
    has_ticker_news,
    init_db,
    insert_news_records,
)
from src.ingestion.http_client import fetch_url
from src.ingestion.sentiment import score_vietnamese_headline


def parse_cafef_news_html(html: str, ticker: str) -> list[tuple[str, str, str, float]]:
    """
    phan tich cay dom html tu trang ajax tin tuc cafef bang beautifulsoup4.
    tra ve danh sach (ticker, pub_date_iso, headline, sentiment_score).
    """
    if not html:
        return []
    soup = BeautifulSoup(html, "html.parser")
    records: list[tuple[str, str, str, float]] = []

    for li in soup.find_all("li"):
        time_span = li.find("span", class_="timeTitle")
        link_tag = li.find("a", class_="docnhanhTitle") or li.find("a")
        if not time_span or not link_tag:
            continue

        raw_time = time_span.get_text(strip=True)
        headline = link_tag.get("title") or link_tag.get_text(strip=True)
        if not raw_time or not headline:
            continue

        # chuyen dinh dang ngay dd/MM/yyyy HH:mm sang YYYY-MM-DD
        date_part = raw_time.split()[0]
        dt = pd.to_datetime(date_part, format="%d/%m/%Y", errors="coerce")
        if pd.isna(dt):
            continue

        pub_date = dt.strftime("%Y-%m-%d")
        clean_title = " ".join(headline.split())
        score = score_vietnamese_headline(clean_title)
        records.append((ticker, pub_date, clean_title, score))

    return records


def crawl_ticker_news(
    ticker: str,
    max_pages: int = 3,
    page_size: int = 30,
    db_path: Path = SQLITE_DB_PATH,
) -> int:
    """cao tin tuc cua 1 ma co phieu qua nhieu trang va luu ngay vao sqlite cache."""
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
            insert_news_records(records, db_path=db_path)
            total_inserted += len(records)
        except Exception as exc:
            print(f"[WARN] Failed scraping {ticker} page {page}: {exc}")
            break
    return total_inserted


def sync_all_news(
    tickers: list[str] = VN30_TICKERS,
    max_pages_per_ticker: int = 3,
    output_dir: Path = DATA_RAW_DIR,
    db_path: Path = SQLITE_DB_PATH,
) -> pd.DataFrame:
    """
    cao tin tuc cho toan bo danh sach vn30 (bo qua ma da co trong sqlite cache).
    tong hop theo (date, ticker) va xuat ra file news_sentiment.parquet chuan hop dong.
    """
    init_db(db_path)
    for idx, ticker in enumerate(tickers, start=1):
        if has_ticker_news(ticker, min_rows=15, db_path=db_path):
            print(
                f"[{idx:02d}/{len(tickers)}] Cache hit in SQLite for {ticker} news, skipping crawl."
            )
            continue
        print(
            f"[{idx:02d}/{len(tickers)}] Crawling CafeF news for {ticker} (up to {max_pages_per_ticker} pages)..."
        )
        count = crawl_ticker_news(
            ticker, max_pages=max_pages_per_ticker, db_path=db_path
        )
        print(f"    -> Parsed {count} articles for {ticker}")

    # doc toan bo tin tuc tu sqlite va gom nhom theo (date, ticker)
    with get_connection(db_path) as conn:
        df_raw = pd.read_sql_query(
            "SELECT pub_date AS date, ticker, headline, sentiment_score FROM raw_news",
            conn,
        )

    if df_raw.empty:
        df_agg = pd.DataFrame(
            columns=[
                "date",
                "ticker",
                "news_count",
                "sentiment_score",
                "sample_headline",
            ]
        )
    else:
        # neu ngay dang tin roi vao thu 7 / chu nhat thi quy ve thu 2 ke tiep de khop ngay giao dich
        dt_series = pd.to_datetime(df_raw["date"])
        weekday = dt_series.dt.weekday
        dt_series = dt_series + pd.to_timedelta(
            (weekday == 5) * 2 + (weekday == 6) * 1, unit="D"
        )
        df_raw["date"] = dt_series.dt.normalize()

        # loc trong pham vi start_date -> end_date (hoac giu toan bo tin da cao)
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
        df_agg["news_count"] = df_agg["news_count"].astype("int64")
        df_agg["sentiment_score"] = df_agg["sentiment_score"].round(4).astype("float64")

    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / "news_sentiment.parquet"
    df_agg.to_parquet(out_path, index=False)
    print(
        f"[OK] Saved {len(df_agg):,} daily ticker-news rows (from {len(df_raw):,} articles) to {out_path}"
    )
    return df_agg
