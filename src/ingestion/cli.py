"""
giao dien dong lenh (cli) de chay doc lap package src.ingestion.
cach chay: uv run python -m src.ingestion.cli
"""

import argparse
import time

from src.config import DATA_RAW_DIR, END_DATE, START_DATE, VN30_TICKERS
from src.ingestion import run_ingestion, run_news_crawler
from src.ingestion.news_crawler import export_news_sentiment_parquet
from src.ingestion.sentiment import (
    rescore_all_news_in_db,
    train_and_save_sentiment_model,
)


def main() -> None:
    """diem khoi chay cli cho pipeline thu thap du lieu va cao tin tuc."""
    parser = argparse.ArgumentParser(description="TradeToiChet — Data Ingestion & Web Crawler CLI")
    parser.add_argument("--skip-prices", action="store_true", help="Skip OHLCV and macro ingestion")
    parser.add_argument("--skip-news", action="store_true", help="Skip CafeF news crawling")
    parser.add_argument("--retrain-sentiment", action="store_true", help="Retrain leak-free sentiment model (<=2023) & rescore DB")
    parser.add_argument("--start-date", type=str, default=START_DATE, help=f"Start date YYYY-MM-DD (default: {START_DATE})")
    parser.add_argument("--end-date", type=str, default=END_DATE, help=f"End date YYYY-MM-DD (default: {END_DATE})")
    parser.add_argument("--pages", type=int, default=60, help="Max news pages per ticker (default: 60)")
    parser.add_argument("--tickers", type=str, default=None, help="Comma-separated tickers for news crawl (e.g. FPT,HPG)")
    args = parser.parse_args()

    t0 = time.time()
    print("=== [INGESTION] Starting Data Ingestion & Web Crawling Pipeline ===")
    if args.retrain_sentiment:
        train_and_save_sentiment_model()
        rescore_all_news_in_db()
        export_news_sentiment_parquet(start_date=args.start_date, end_date=args.end_date, output_dir=DATA_RAW_DIR)
        print(f"=== [INGESTION] Sentiment retrain & rescore completed in {time.time() - t0:.2f}s ===")
        return

    if not args.skip_prices:
        run_ingestion(start_date=args.start_date, end_date=args.end_date, output_dir=DATA_RAW_DIR)
    if not args.skip_news:
        target_tickers = (
            [t.strip().upper() for t in args.tickers.split(",") if t.strip()] if args.tickers else VN30_TICKERS
        )
        run_news_crawler(
            tickers=target_tickers, output_dir=DATA_RAW_DIR,
            start_date=args.start_date, end_date=args.end_date, max_pages=args.pages,
        )
    print(f"=== [INGESTION] Pipeline completed successfully in {time.time() - t0:.2f}s ===")


if __name__ == "__main__":
    main()
