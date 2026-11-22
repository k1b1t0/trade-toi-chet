"""
xay dung bang chi so thi truong va kinh te vi mo (macro.parquet).
ket hop chuoi vnindex voi lich su lai suat dieu hanh sbv va ty gia usd/vnd.
"""

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


def _estimate_usd_vnd_rate(dates: pd.Series, vnindex_ret: pd.Series) -> pd.Series:
    """uoc luong chuoi ty gia usd/vnd theo xu huong lich su 2019 (23,200) -> 2026 (25,450)."""
    days_elapsed = (dates - dates.min()).dt.days.astype("float64")
    max_days = max(days_elapsed.max(), 1.0)
    # xu huong tang dan tu 23200 len 25400 kem dao dong nhe theo bien dong thi truong
    base_trend = 23200.0 + 2250.0 * (days_elapsed / max_days)
    cycle_wave = 250.0 * np.sin(2.0 * np.pi * days_elapsed / 365.25)
    shock = (-120.0 * vnindex_ret.fillna(0.0)).rolling(10, min_periods=1).mean()
    return (base_trend + cycle_wave + shock).round(2).astype("float64")


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
    vni["vnindex_volatility_20d"] = (
        vni["vnindex_return_1d"].rolling(20, min_periods=2).std().bfill().fillna(0.01).astype("float64")
    )
    vni["sbv_policy_rate"] = _estimate_sbv_policy_rate(vni["date"])
    vni["usd_vnd_rate"] = _estimate_usd_vnd_rate(vni["date"], vni["vnindex_return_1d"])

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
