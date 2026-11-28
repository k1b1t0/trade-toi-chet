# TradeToiChet — Hệ Thống Dự Báo Lợi Nhuận & Mô Phỏng Giao Dịch Định Lượng VN30

[![CI Pipeline](https://github.com/k1b1t0/TradeToiChet/actions/workflows/ci.yml/badge.svg)](https://github.com/k1b1t0/TradeToiChet/actions/workflows/ci.yml)

Đồ án Khoa học Dữ liệu (**IT4930**) xây dựng đường ống đầu-cuối cho thị trường chứng khoán Việt Nam (rổ **VN30 + VN-Index**, giai đoạn `2019–2026`): thu thập dữ liệu đa nguồn, phân tích cảm xúc tin tức tiếng Việt (LLM Distillation), kỹ nghệ đặc trưng, phân cụm PCA / đồ thị PageRank, học máy đối sánh SOTA và mô phỏng giao dịch định lượng.

---

## 1. Cấu Trúc Thư Mục

```text
TradeToiChet/
├── README.md                     # Hướng dẫn cài đặt & tái lập pipeline
├── AGENTS.md                     # Bản đồ hệ thống, quy chuẩn code & DoD
├── pyproject.toml                # Quản lý phụ thuộc bằng uv
├── docs/
│   ├── architecture/             # PLAN, STRUCTURE, FLOW, API_CONTRACTS, SOTA_PAPERS
│   ├── checklists/               # CHECKLIST.md và CHECKLIST-A..E.md
│   ├── modules/                  # Tài liệu kỹ thuật từng phân hệ (01-ingestion.md, ...)
│   └── papers/                   # Bài báo tham khảo (PLOS ONE 2025, Nature 2024)
├── src/
│   ├── config.py                 # Hằng số dùng chung (VN30, mốc ngày, phí & thuế HOSE)
│   ├── ingestion/                # [01] Giá OHLCV, vĩ mô, cào CafeF & sentiment TF-IDF
│   ├── processing/               # [02] Làm sạch, 25+ chỉ báo, PCA/K-Means & PageRank
│   ├── modeling/                 # [03] Regression, Classification & SOTA Benchmark
│   ├── backtesting/              # [04] Threshold Tuning & mô phỏng giao dịch T+3 (T+2.5)
│   └── dashboard/                # [05] Web App Streamlit 5 Tabs
├── tests/                        # Bộ kiểm thử tự động (pytest)
├── notebooks/                    # Jupyter Notebooks phân tích & báo cáo
└── data/
    ├── raw/                      # prices, macro, news_sentiment, sentiment_labels (.parquet)
    ├── models/                   # sentiment_tfidf.joblib (fit <= 2023-12-31, leak-free)
    └── processed/                # Đầu ra của Phân hệ 02–04
```

> **Lưu ý**: File cache cục bộ `data/tradetoichet.db` được đưa vào `.gitignore` để giữ repo nhẹ; toàn bộ dataset chuẩn đầu ra đã có sẵn trong `data/raw/` và `data/models/`.

---

## 2. Tái Lập Ingestion Pipeline Từ Repo Gốc

```bash
# 1. Clone repo và cài đặt môi trường ảo bằng uv
git clone https://github.com/k1b1t0/TradeToiChet.git
cd TradeToiChet
uv sync

# 2. (Tùy chọn) Kiểm tra ngay bộ dữ liệu sẵn có trong data/raw/
uv run pytest tests/test_ingestion.py -v

# 3. Tái lập lại toàn bộ dữ liệu từ nguồn thật (Entrade OHLCV + Yahoo USD/VND + CafeF News)
# Tự động tạo cache cục bộ data/tradetoichet.db và xuất lại data/raw/*.parquet
uv run python -m src.ingestion.cli

# 4. (Tùy chọn) Chạy từng phần độc lập
uv run python -m src.ingestion.cli --skip-news          # Chỉ kéo giá OHLCV & dựng macro.parquet
uv run python -m src.ingestion.cli --skip-prices        # Chỉ cào bổ sung tin CafeF
uv run python -m src.ingestion.cli --retrain-sentiment  # Train lại model cảm xúc (<= 2023-12-31) từ sentiment_labels.parquet & chấm lại tin

# 5. Kiểm tra chất lượng code & schema hợp đồng
ruff check src/ tests/ && uvx ty check --python .venv src/ tests/ && uv run pytest -v
```

---

## 3. Tài Liệu Chính

- **Phân hệ đã hoàn thành**: [docs/modules/01-ingestion.md](docs/modules/01-ingestion.md) | [notebooks/01_data_crawling.ipynb](notebooks/01_data_crawling.ipynb)
- **Kiến trúc & Hợp đồng**: [API_CONTRACTS.md](docs/architecture/API_CONTRACTS.md) | [PLAN.md](docs/architecture/PLAN.md) | [FLOW.md](docs/architecture/FLOW.md) | [SOTA_PAPERS.md](docs/architecture/SOTA_PAPERS.md)
- **Checklists triển khai**: [CHECKLIST.md](docs/checklists/CHECKLIST.md) (`CHECKLIST-A` → `CHECKLIST-E`)
