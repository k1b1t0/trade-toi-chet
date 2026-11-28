"""
xay dung bang chi so thi truong va kinh te vi mo (macro.parquet).
ket hop chuoi vnindex voi lich su lai suat dieu hanh sbv va ty gia usd/vnd.
"""

import json
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

from src.config import BENCHMARK_TICKER, DATA_RAW_DIR, SQLITE_DB_PATH
from src.ingestion.db import get_connection, init_db


def _estimate_sbv_policy_rate(dates: pd.Series) -> pd.Series:
    """
    anh xa lai suat tai cap von cua ngan hang nha nuoc (sbv) theo tung giai doan lich su.
    nguon: quyet dinh dieu hanh lai suat cua sbv giai doan 2019 - 2026.
    """
    conds = [
        dates < "2019-09-16",
        (dates >= "2019-09-16") & (dates < "2020-03-17"),
        (dates >= "2020-03-17") & (dates < "2020-05-13"),
        (dates >= "2020-05-13") & (dates < "2020-10-01"),
        (dates >= "2020-10-01") & (dates < "2022-09-23"),
        (dates >= "2022-09-23") & (dates < "2022-10-25"),
        (dates >= "2022-10-25") & (dates < "2023-04-03"),
        (dates >= "2023-04-03") & (dates < "2023-05-25"),
        (dates >= "2023-05-25") & (dates < "2023-06-19"),
        dates >= "2023-06-19",
    ]
    rates = [6.25, 6.00, 5.00, 4.50, 4.00, 5.00, 6.00, 5.50, 5.00, 4.50]
    return pd.Series(np.select(conds, rates, default=4.50), index=dates.index, dtype="float64")


def _fetch_yahoo_usdvnd(start_ts: int, end_ts: int) -> pd.DataFrame:
    """keo chuoi ty gia usd/vnd (VND=X) truc tiep tu api yahoo finance khong can api key."""
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/VND=X?period1={start_ts}&period2={end_ts}&interval=1d"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=12) as resp:
        data = json.loads(resp.read().decode())
    chart = data["chart"]["result"][0]
    ts = chart["timestamp"]
    closes = chart["indicators"]["quote"][0]["close"]
    df = pd.DataFrame({"ts": ts, "usd_vnd_rate": closes}).dropna(subset=["usd_vnd_rate"])
    df["date"] = pd.to_datetime(df["ts"], unit="s", utc=True).dt.tz_convert("Asia/Ho_Chi_Minh").dt.tz_localize(None).dt.normalize()
    return df[["date", "usd_vnd_rate"]].drop_duplicates(subset=["date"]).sort_values("date")


def _estimate_usd_vnd_rate(dates: pd.Series) -> pd.Series:
    """
    lay ty gia usd/vnd that tu yahoo finance (VND=X), dien khuyet bang ffill.
    neu loi mang hoac api khong co du lieu, raise ngoai le va dung chuong trinh de chay lai.
    """
    clean_dates = pd.to_datetime(dates).dt.normalize()
    df_target = pd.DataFrame({"date": clean_dates}, index=dates.index)
    start_ts = int(clean_dates.min().timestamp()) - 86400 * 7
    end_ts = int(clean_dates.max().timestamp()) + 86400 * 7

    try:
        df_yf = _fetch_yahoo_usdvnd(start_ts, end_ts)
    except Exception as exc:
        raise RuntimeError(
            f"[FATAL] Khong the tai du lieu ty gia USD/VND tu Yahoo Finance (VND=X): {exc}. "
            "Vui long kiem tra lai ket noi Internet va chay lai."
        ) from exc

    if df_yf.empty:
        raise RuntimeError(
            "[FATAL] Du lieu ty gia USD/VND tu Yahoo Finance bi rong. Vui long chay lai sau."
        )

    merged = df_target.merge(df_yf, on="date", how="left")
    # chi dung ffill() de lay gia qua khu, tuyet doi khong dung bfill() de tranh ro ri du lieu tuong lai
    rate_series = merged["usd_vnd_rate"].ffill()
    if rate_series.isna().any() or rate_series.min() < 10000.0:
        raise ValueError("[FATAL] Du lieu ty gia USD/VND bi khuyet sau khi ffill hoac co gia tri khong hop le.")

    rate_series.index = dates.index
    return rate_series.round(2).astype("float64")


def build_macro_dataset(
    df_prices: pd.DataFrame,
    output_dir: Path = DATA_RAW_DIR,
    db_path: Path = SQLITE_DB_PATH,
) -> pd.DataFrame:
    """trich xuat bien dong vnindex, ghep lai suat sbv va ty gia, luu sqlite + macro.parquet."""
    init_db(db_path)
    vni = df_prices[df_prices["ticker"] == BENCHMARK_TICKER].sort_values("date").copy()
    if vni.empty:
        raise ValueError("VNINDEX data not found in prices DataFrame.")

    vni["vnindex_close"] = vni["close"].astype("float64")
    vni["vnindex_return_1d"] = vni["vnindex_close"].pct_change().fillna(0.0).astype("float64")
    # do bien dong 20 phien chuan toan hoc: 19 ngay dau de NaN tu nhien, tuyet doi khong bfill (se dropna o Tang 2)
    vni["vnindex_volatility_20d"] = (
        vni["vnindex_return_1d"].rolling(20, min_periods=20).std().astype("float64")
    )
    vni["sbv_policy_rate"] = _estimate_sbv_policy_rate(vni["date"])
    vni["usd_vnd_rate"] = _estimate_usd_vnd_rate(vni["date"])

    cols = [
        "date",
        "vnindex_close",
        "vnindex_return_1d",
        "vnindex_volatility_20d",
        "usd_vnd_rate",
        "sbv_policy_rate",
    ]
    df_macro = vni[cols].drop_duplicates(subset=["date"]).sort_values("date").reset_index(drop=True)

    # luu vao sqlite cache
    db_rows = df_macro.copy()
    db_rows["date"] = db_rows["date"].dt.strftime("%Y-%m-%d")
    with get_connection(db_path) as conn:
        conn.executemany(
            """
            INSERT OR REPLACE INTO macro
            (date, vnindex_close, vnindex_return_1d, vnindex_volatility_20d, usd_vnd_rate, sbv_policy_rate)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            db_rows.itertuples(index=False, name=None),
        )
        conn.commit()

    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / "macro.parquet"
    df_macro.to_parquet(out_path, index=False)
    print(f"[OK] Saved {len(df_macro):,} rows of macro indicators to {out_path}")
    return df_macro
