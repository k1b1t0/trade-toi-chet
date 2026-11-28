"""
keo du lieu gia lich su ohlcv cho 30 ma vn30 va chi so vnindex.
kiem tra watermark [min_date, max_date] trong sqlite truoc khi goi api va xuat prices.parquet.
"""

from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from src.config import (
    BENCHMARK_TICKER,
    DATA_RAW_DIR,
    END_DATE,
    SECTOR_MAP,
    SQLITE_DB_PATH,
    START_DATE,
    VN30_TICKERS,
)
from src.ingestion.db import (
    get_connection,
    get_ticker_price_bounds,
    init_db,
    upsert_prices,
)
from src.ingestion.http_client import fetch_url


def _date_to_unix(date_str: str, end_of_day: bool = False) -> int:
    """chuyen chuoi ngay YYYY-MM-DD sang unix timestamp (giay); end_of_day=True lay 23:59:59 UTC."""
    dt = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=UTC)
    return int(dt.timestamp()) + (86399 if end_of_day else 0)


def fetch_single_ticker_ohlcv(ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
    """goi api entrade dnse de lay du lieu nen ngay ohlcv cua 1 ma co phieu hoac chi so."""
    start_ts = _date_to_unix(start_date, end_of_day=False)
    end_ts = _date_to_unix(end_date, end_of_day=True)
    kind = "index" if ticker == BENCHMARK_TICKER else "stock"
    url = (
        f"https://services.entrade.com.vn/chart-api/v2/ohlcs/{kind}"
        f"?from={start_ts}&to={end_ts}&symbol={ticker}&resolution=1D"
    )
    payload = fetch_url(url, as_json=True, min_delay=0.15, max_delay=0.35)
    timestamps = payload.get("t", [])
    if not timestamps:
        return pd.DataFrame()

    # chuyen unix timestamp sang ngay giao dich theo mui gio viet nam (UTC+7)
    dates = (
        pd.to_datetime(timestamps, unit="s", utc=True)
        .tz_convert("Asia/Ho_Chi_Minh")
        .tz_localize(None)
        .normalize()
    )
    df = pd.DataFrame(
        {
            "date": dates,
            "ticker": ticker,
            "open": pd.to_numeric(payload.get("o", []), errors="coerce").astype("float64"),
            "high": pd.to_numeric(payload.get("h", []), errors="coerce").astype("float64"),
            "low": pd.to_numeric(payload.get("l", []), errors="coerce").astype("float64"),
            "close": pd.to_numeric(payload.get("c", []), errors="coerce").astype("float64"),
            "volume": pd.to_numeric(payload.get("v", []), errors="coerce").astype("float64"),
            "sector": SECTOR_MAP.get(ticker, "Other"),
        }
    )
    df = df.dropna(subset=["date", "close"]).drop_duplicates(subset=["date", "ticker"], keep="last")
    return df.sort_values("date").reset_index(drop=True)


def sync_all_prices(
    start_date: str = START_DATE,
    end_date: str = END_DATE,
    output_dir: Path = DATA_RAW_DIR,
    db_path: Path = SQLITE_DB_PATH,
) -> pd.DataFrame:
    """dong bo gia 30 ma vn30 va vnindex theo incremental 2 dau [start_date, end_date]."""
    init_db(db_path)
    all_tickers = VN30_TICKERS + [BENCHMARK_TICKER]
    req_start, req_end = pd.Timestamp(start_date), pd.Timestamp(end_date)
    for idx, ticker in enumerate(all_tickers, start=1):
        db_min, db_max = get_ticker_price_bounds(ticker, db_path=db_path)
        if db_min is None or db_max is None:
            print(f"[{idx:02d}/{len(all_tickers)}] Fetching full OHLCV for {ticker} ({start_date} -> {end_date})...")
            upsert_prices(fetch_single_ticker_ohlcv(ticker, start_date, end_date), db_path=db_path)
            continue

        missing_ranges: list[tuple[str, str]] = []
        if (pd.Timestamp(db_min) - req_start).days > 7:
            missing_ranges.append((start_date, db_min))
        if (req_end - pd.Timestamp(db_max)).days > 0:
            missing_ranges.append((db_max, end_date))

        if not missing_ranges:
            print(f"[{idx:02d}/{len(all_tickers)}] Cache hit in SQLite for {ticker} ({db_min} -> {db_max}).")
            continue
        for r_start, r_end in missing_ranges:
            print(f"[{idx:02d}/{len(all_tickers)}] Incremental OHLCV fetch for {ticker} ({r_start} -> {r_end})...")
            upsert_prices(fetch_single_ticker_ohlcv(ticker, r_start, r_end), db_path=db_path)

    with get_connection(db_path) as conn:
        df_all = pd.read_sql_query(
            "SELECT date, ticker, open, high, low, close, volume, sector "
            "FROM prices WHERE date >= ? AND date <= ?",
            conn,
            params=[start_date, end_date],
        )
    df_all["date"] = pd.to_datetime(df_all["date"]).astype("datetime64[ns]")
    df_all = df_all.sort_values(["ticker", "date"]).reset_index(drop=True)

    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / "prices.parquet"
    df_all.to_parquet(out_path, index=False)
    print(f"[OK] Saved {len(df_all):,} rows ({df_all['ticker'].nunique()} tickers) to {out_path}")
    return df_all
