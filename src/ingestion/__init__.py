"""
package src.ingestion: thu thap du lieu gia ohlcv, vi mo va cao tin tuc cafef.
cung cap 2 ham entrypoint chuan hop dong: run_ingestion() va run_news_crawler().
"""

from pathlib import Path

from src.config import DATA_RAW_DIR, END_DATE, START_DATE, VN30_TICKERS
from src.ingestion.macro_builder import build_macro_dataset
from src.ingestion.news_crawler import sync_all_news
from src.ingestion.price_fetcher import sync_all_prices


def run_ingestion(
    start_date: str = START_DATE,
    end_date: str = END_DATE,
    output_dir: Path = DATA_RAW_DIR,
) -> None:
    """tai prices.parquet va macro.parquet vao output_dir (data/raw/)."""
    df_prices = sync_all_prices(start_date=start_date, end_date=end_date, output_dir=output_dir)
    build_macro_dataset(df_prices=df_prices, output_dir=output_dir)


def run_news_crawler(
    tickers: list[str] = VN30_TICKERS,
    output_dir: Path = DATA_RAW_DIR,
    start_date: str = START_DATE,
    end_date: str = END_DATE,
    max_pages: int = 60,
) -> None:
    """dong bo tin tuc cafef trong khoang [start_date, end_date], luu news_sentiment.parquet."""
    sync_all_news(
        tickers=tickers,
        start_date=start_date,
        end_date=end_date,
        max_pages_per_ticker=max_pages,
        output_dir=output_dir,
    )
