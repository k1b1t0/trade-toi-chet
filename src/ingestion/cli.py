"""
giao dien dong lenh (cli) de chay doc lap package src.ingestion.
cach chay: uv run python -m src.ingestion.cli
"""

import argparse
import time
from src.config import DATA_RAW_DIR, END_DATE, START_DATE, VN30_TICKERS
from src.ingestion import run_ingestion, run_news_crawler


def main() -> None:
    """diem khoi chay cli cho pipeline thu thap du lieu va cao tin tuc."""
    parser = argparse.ArgumentParser(description="TradeToiChet — Data Ingestion & Web Crawler CLI")
    parser.add_argument("--skip-prices", action="store_true", help="Skip OHLCV and macro ingestion")
    parser.add_argument("--skip-news", action="store_true", help="Skip CafeF news crawling")
    parser.add_argument("--pages", type=int, default=3, help="Max news pages per ticker (default: 3)")
    args = parser.parse_args()

    t0 = time.time()
    print("=== [INGESTION] Starting Data Ingestion & Web Crawling Pipeline ===")
    if not args.skip_prices:
        run_ingestion(start_date=START_DATE, end_date=END_DATE, output_dir=DATA_RAW_DIR)
    if not args.skip_news:
        run_news_crawler(tickers=VN30_TICKERS, output_dir=DATA_RAW_DIR, max_pages=args.pages)
    elapsed = time.time() - t0
    print(f"=== [INGESTION] Pipeline completed successfully in {elapsed:.2f}s ===")


if __name__ == "__main__":
    main()
