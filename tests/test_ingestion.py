"""
bo kiem thu tu dong (unit tests & data schema contract tests) cho package src.ingestion.
cach chay: uv run pytest -v
"""

from pathlib import Path

import pandas as pd

from src.config import (
    BENCHMARK_TICKER,
    DATA_RAW_DIR,
    END_DATE,
    SENTIMENT_MODEL_PATH,
    SQLITE_DB_PATH,
    START_DATE,
    VN30_TICKERS,
)
from src.ingestion.db import (
    get_connection,
    get_ticker_price_bounds,
    has_ticker_news,
    has_ticker_prices,
    init_db,
    insert_news_records,
    upsert_prices,
)
from src.ingestion.news_crawler import parse_cafef_news_html
from src.ingestion.sentiment import score_vietnamese_headline


def test_sentiment_scorer_polarity() -> None:
    """kiem tra model .joblib da train tu nhan llm distillation (<= 2023-12-31) phan biet dung 3 lop."""
    assert SENTIMENT_MODEL_PATH.exists(), "Missing pre-trained sentiment_tfidf.joblib model"
    if SQLITE_DB_PATH.exists():
        with get_connection(SQLITE_DB_PATH) as conn:
            label_count = conn.execute("SELECT COUNT(*) FROM sentiment_labels").fetchone()[0]
        assert label_count >= 2500, f"Expected >= 2500 distilled labels, got {label_count}"

    pos_score = score_vietnamese_headline("FPT báo lãi kỷ lục, lợi nhuận sau thuế tăng trưởng mạnh")
    neg_score = score_vietnamese_headline("Cổ phiếu giảm sàn, doanh nghiệp thua lỗ nặng và bị xử phạt")
    neu_score = score_vietnamese_headline("Thông báo ngày đăng ký cuối cùng để thực hiện quyền tham dự ĐHĐCĐ thường niên")

    assert pos_score > 0.15
    assert neg_score < -0.10
    assert abs(neu_score) < 0.25


def test_parse_cafef_news_html_offline() -> None:
    """kiem tra parser beautifulsoup4 boc tach dung ngay, tieu de va diem cam xuc tu html mau."""
    sample_html = """
    <div id="divEvents">
      <ul class="News_Title_Link">
        <li>
          <span class="timeTitle">20/11/2025 14:30</span>
          <a class="docnhanhTitle" title="HPG lãi lớn kỷ lục trong quý 3">HPG lãi lớn kỷ lục trong quý 3</a>
        </li>
        <li>
          <span class="timeTitle">18/11/2025 09:15</span>
          <a class="docnhanhTitle" title="Cổ phiếu bị bán tháo mạnh">Cổ phiếu bị bán tháo mạnh</a>
        </li>
      </ul>
    </div>
    """
    records = parse_cafef_news_html(sample_html, ticker="HPG")
    assert len(records) == 2
    assert records[0][0] == "HPG"
    assert records[0][1] == "2025-11-20"
    assert records[0][2] == "14:30"
    assert "HPG lãi lớn" in records[0][3]
    assert records[0][4] > 0.0
    assert records[1][4] < 0.0


def test_sqlite_cache_operations(tmp_path: Path) -> None:
    """kiem tra sqlite cache khoi tao bang, luu du lieu va chong trung lap khoa chinh."""
    db_file = tmp_path / "test_cache.db"
    init_db(db_file)

    assert not has_ticker_prices("FPT", min_rows=1, db_path=db_file)
    df_sample = pd.DataFrame(
        {
            "date": pd.to_datetime(["2025-01-02", "2025-01-03"]),
            "ticker": ["FPT", "FPT"],
            "open": [100.0, 101.0],
            "high": [102.0, 103.0],
            "low": [99.0, 100.0],
            "close": [101.5, 102.5],
            "volume": [1500000.0, 1800000.0],
            "sector": ["Technology", "Technology"],
        }
    )
    upsert_prices(df_sample, db_path=db_file)
    # goi upsert lan 2 voi cung khoa chinh de dam bao idempotent (khong sinh dong trung)
    upsert_prices(df_sample, db_path=db_file)
    assert has_ticker_prices("FPT", min_rows=2, db_path=db_file)
    assert get_ticker_price_bounds("FPT", db_path=db_file) == ("2025-01-02", "2025-01-03")
    assert get_ticker_price_bounds("UNKNOWN", db_path=db_file) == (None, None)

    news_rows = [
        ("FPT", "2025-01-02", "10:15", "FPT tăng trưởng mạnh lợi nhuận quý 4", 0.6667),
        ("FPT", "2019-06-15", "15:30", "FPT chi cổ tức tiền mặt tỷ lệ cao", 0.5000),
    ]
    assert insert_news_records(news_rows, db_path=db_file) == 2
    assert insert_news_records(news_rows, db_path=db_file) == 0
    assert has_ticker_news("FPT", min_rows=2, db_path=db_file)


def test_raw_parquet_data_contracts() -> None:
    """kiem tra 3 file parquet trong data/raw/ khop 100% voi hop dong API_CONTRACTS.md."""
    prices_path = DATA_RAW_DIR / "prices.parquet"
    news_path = DATA_RAW_DIR / "news_sentiment.parquet"
    macro_path = DATA_RAW_DIR / "macro.parquet"

    assert prices_path.exists(), "Missing data/raw/prices.parquet"
    assert news_path.exists(), "Missing data/raw/news_sentiment.parquet"
    assert macro_path.exists(), "Missing data/raw/macro.parquet"

    # 1. kiem tra prices.parquet
    df_p = pd.read_parquet(prices_path)
    p_cols = ["date", "ticker", "open", "high", "low", "close", "volume", "sector"]
    assert list(df_p.columns) == p_cols
    assert pd.api.types.is_datetime64_any_dtype(df_p["date"])
    assert set(df_p["ticker"].unique()) == set(VN30_TICKERS + [BENCHMARK_TICKER])
    assert df_p[["date", "ticker", "close"]].isna().sum().sum() == 0
    assert df_p.duplicated(subset=["date", "ticker"]).sum() == 0
    assert df_p["date"].min() >= pd.Timestamp(START_DATE)
    assert df_p["date"].max() <= pd.Timestamp(END_DATE)
    assert df_p["date"].max() >= pd.Timestamp(END_DATE) - pd.Timedelta(days=7)
    assert len(df_p) > 55000

    # 2. kiem tra news_sentiment.parquet
    df_n = pd.read_parquet(news_path)
    n_cols = ["date", "ticker", "news_count", "sentiment_score", "sample_headline"]
    assert list(df_n.columns) == n_cols
    assert pd.api.types.is_datetime64_any_dtype(df_n["date"])
    assert df_n["sentiment_score"].between(-1.0, 1.0).all()
    assert (df_n["news_count"] >= 1).all()
    assert df_n.duplicated(subset=["date", "ticker"]).sum() == 0
    assert df_n["date"].min() >= pd.Timestamp(START_DATE)
    assert df_n["date"].max() <= pd.Timestamp(END_DATE)
    assert len(df_n) > 15000

    # 3. kiem tra macro.parquet
    df_m = pd.read_parquet(macro_path)
    m_cols = ["date", "vnindex_close", "vnindex_return_1d", "vnindex_volatility_20d", "usd_vnd_rate", "sbv_policy_rate"]
    assert list(df_m.columns) == m_cols
    assert pd.api.types.is_datetime64_any_dtype(df_m["date"])
    # 19 ngay dau tien de NaN tu nhien cho rolling(20) de chong look-ahead bias (khong dung bfill)
    assert df_m["vnindex_volatility_20d"].iloc[:19].isna().all()
    assert df_m["vnindex_volatility_20d"].iloc[19:].isna().sum() == 0
    # cac cot khac khong duoc chua NaN
    other_cols = ["date", "vnindex_close", "vnindex_return_1d", "usd_vnd_rate", "sbv_policy_rate"]
    assert df_m[other_cols].isna().sum().sum() == 0
    assert df_m.duplicated(subset=["date"]).sum() == 0
    assert df_m["date"].max() >= pd.Timestamp(END_DATE) - pd.Timedelta(days=7)
    assert len(df_m) > 1800
