# TradeToiChet — Hệ Thống Dự Báo Lợi Nhuận & Mô Phỏng Giao Dịch Định Lượng VN30

> **Đồ án Khoa học Dữ liệu (IT4930) · Học máy (IT3190) · SMA Zoomcamp Capstone**
> Hệ thống thu thập dữ liệu đa nguồn (API giá OHLCV + Web Crawling tin tức CafeF + Vĩ mô SBV), phân tích mạng lưới liên kết PageRank, học máy đối sánh 2 bài báo khoa học SOTA (Nature 2024 & PLOS ONE 2025) và mô phỏng chiến lược giao dịch T+2.5 trên rổ cổ phiếu VN30.

---

## 1. Cấu Trúc Thư Mục & Phân Chia 5 Sub-Packages (5 Thành Viên)

```text
TradeToiChet/
├── README.md                     # Tài liệu hướng dẫn tổng quan
├── AGENTS.md                     # Quy chuẩn code, comment tiếng Việt không dấu, git rules
├── pyproject.toml                # Cấu hình quản lý thư viện bằng uv
├── main.py                       # Điểm kích hoạt chạy toàn bộ pipeline
│
├── docs/
│   ├── architecture/             # PLAN.md, STRUCTURE.md, FLOW.md, API_CONTRACTS.md, SOTA_PAPERS.md
│   ├── checklists/               # CHECKLIST.md và CHECKLIST-A.md -> CHECKLIST-E.md
│   └── papers/                   # File PDF & TXT của 2 bài báo Nature (2024) và PLOS ONE (2025)
│
├── src/
│   ├── config.py                 # Hằng số dùng chung (30 mã VN30, mốc ngày, phí & thuế)
│   ├── ingestion/                # [Ông A] Kéo giá OHLCV, vĩ mô & cào tin tức CafeF (SQLite + Parquet)
│   ├── processing/               # [Ông B] Làm sạch, tính 25+ biến kỹ thuật, PCA/K-Means & PageRank
│   ├── modeling/                 # [Ông C] Huấn luyện Regression, Classification & SOTA Benchmark
│   ├── backtesting/              # [Ông D] Tinh chỉnh ngưỡng & mô phỏng giao dịch T+2.5
│   └── dashboard/                # [Ông E] Giao diện Web App Streamlit 5 Tabs
│
├── notebooks/                    # 4 Jupyter Notebooks phục vụ trình bày báo cáo
└── data/
    ├── tradetoichet.db           # SQLite cache lưu dữ liệu đã kéo/cào (chống ban IP & cào lại)
    ├── raw/                      # prices.parquet, news_sentiment.parquet, macro.parquet
    └── processed/                # Các bảng đặc trưng, dự báo và kết quả backtest
```

---

## 2. Hướng Dẫn Cài Đặt & Chạy Nhanh Với `uv`

```bash
# 1. Cài đặt môi trường ảo và toàn bộ thư viện
uv sync

# 2. Chạy phân hệ Ông A (Kéo giá VN30 + Vĩ mô + Cào tin tức CafeF có SQLite cache)
uv run python -m src.ingestion.cli
```

---

## 3. Tài Liệu Kiến Trúc, Phân Hệ & Phân Công Nhóm

- **Tài liệu Kỹ thuật từng Phân hệ (`docs/modules/`)**:
  - [Phân hệ 01: Thu thập Dữ liệu Đa nguồn & Anti-Ban Web Crawling (`src/ingestion/`)](docs/modules/01-ingestion.md)
- **Tài liệu Kiến trúc Hệ thống (`docs/architecture/`)**:
  - [Kế hoạch Tổng thể & Ánh xạ môn học 02-ds (L1-L12)](docs/architecture/PLAN.md)
- [Cấu trúc Thư mục & Quyền sở hữu File](docs/architecture/STRUCTURE.md)
- [Sơ đồ Luồng dữ liệu & Luồng phối hợp](docs/architecture/FLOW.md)
- [Hợp đồng Schema Dữ liệu & Giao diện Hàm](docs/architecture/API_CONTRACTS.md)
- [Hồ sơ 2 Bài báo Khoa học SOTA (Nature 2024 & PLOS ONE 2025)](docs/architecture/SOTA_PAPERS.md)
- [Bảng Điều phối Tổng 5 Thành viên](docs/checklists/CHECKLIST.md):
  - [CHECKLIST-A.md (Ông A — Ingestion & Web Crawling)](docs/checklists/CHECKLIST-A.md)
  - [CHECKLIST-B.md (Ông B — Cleaning, EDA, PCA & Graph PageRank)](docs/checklists/CHECKLIST-B.md)
  - [CHECKLIST-C.md (Ông C — ML Models & SOTA Benchmark)](docs/checklists/CHECKLIST-C.md)
  - [CHECKLIST-D.md (Ông D — Backtesting & T+2.5 Simulation)](docs/checklists/CHECKLIST-D.md)
  - [CHECKLIST-E.md (Ông E — Streamlit Dashboard & Report)](docs/checklists/CHECKLIST-E.md)
