# STRUCTURE.md — Kiến Trúc Thư Mục & Bản Đồ Sở Hữu File (`projects/capstone/`)

> Tài liệu này định nghĩa cấu trúc cây thư mục chuẩn của dự án và phân định rõ **ai là chủ sở hữu (Owner)** của từng file để 5 thành viên làm việc song song không bao giờ bị xung đột code (Git Merge Conflict).

---

## 1. Cây Thư Mục Tổng Thể (Directory Tree)

```text
projects/capstone/
├── AGENTS.md                     # Quy tắc viết code, chống look-ahead bias, chuẩn công nghệ
├── PLAN.md                       # Kế hoạch tổng thể, lộ trình, ánh xạ môn 02-ds (L1-L12)
├── STRUCTURE.md                  # Cấu trúc thư mục & quyền sở hữu file (file này)
├── FLOW.md                       # Sơ đồ luồng dữ liệu, luồng phối hợp nhóm & kiến trúc thực thi
├── API_CONTRACTS.md              # Hợp đồng Schema dữ liệu (.parquet/.csv) & chữ ký hàm Python
├── SOTA_PAPERS.md                # Tóm tắt 2 bài báo Nature 2024 & PLOS ONE 2025 để trích dẫn
├── CHECKLIST.md                  # Bảng theo dõi tiến độ tổng của cả 5 thành viên
├── CHECKLIST-A.md                # Đặc tả công việc chi tiết của Người A (Data & Web Crawling)
├── CHECKLIST-B.md                # Đặc tả công việc chi tiết của Người B (Prep, EDA, Clustering & Graph)
├── CHECKLIST-C.md                # Đặc tả công việc chi tiết của Người C (ML Models & SOTA Benchmark)
├── CHECKLIST-D.md                # Đặc tả công việc chi tiết của Người D (Backtesting & T+2.5 Simulation)
├── CHECKLIST-E.md                # Đặc tả công việc chi tiết của Người E (Streamlit UI, Automation & Report)
│
├── pyproject.toml                # Khai báo dependencies chuẩn cho uv
├── requirements.txt              # Danh sách thư viện cài đặt nhanh cho pip
├── .gitignore                    # Chặn commit data nặng, .venv, cache
├── main.py                       # [Người E] Script chạy tự động toàn bộ pipeline đầu-cuối (CLI/Cron)
│
├── scripts/
│   └── generate_mock_data.py     # [Dùng chung Ngày 1] Sinh bộ dữ liệu mẫu đúng 100% Schema Contract
│
├── data/                         # Thư mục chứa dữ liệu (đã chặn gitignore các file parquet nặng)
│   ├── raw/                      # [Output của Người A -> Input của Người B]
│   │   ├── prices.parquet        # Giá lịch sử OHLCV của 30 mã VN30 + VNINDEX
│   │   ├── news_sentiment.parquet# Tiêu đề tin tức cào về & điểm sentiment_score theo ngày
│   │   └── macro.parquet         # Chỉ số vĩ mô (Lãi suất, Tỷ giá, VN-Index return)
│   │
│   └── processed/                # [Output của Người B, C, D -> Input của Người E]
│       ├── features_all.parquet  # [Người B] Bảng gộp sạch + 25+ chỉ báo kỹ thuật + nhãn target
│       ├── clusters_pca.csv      # [Người B] Bảng phân cụm K-Means & tọa độ PCA 2D của 30 mã VN30
│       ├── graph_pagerank.csv    # [Người B] Điểm PageRank & danh sách cạnh đồ thị tương quan VN30
│       ├── predictions.parquet   # [Người C] Dự báo xác suất & lợi nhuận của các mô hình trên tập Test
│       ├── sota_benchmark.csv    # [Người C] Bảng metric so sánh các mô hình với 2 bài báo SOTA
│       ├── feature_importance.csv# [Người C] Top 20 đặc trưng quan trọng nhất từ Random Forest/LightGBM
│       ├── threshold_tuning.csv  # [Người D] Bảng quét ngưỡng xác suất (0.50 -> 0.70) vs Precision & CAGR
│       ├── backtest_summary.csv  # [Người D] Tổng hợp hiệu quả các chiến lược (CAGR, Sharpe, MDD, WinRate)
│       └── equity_curve.parquet  # [Người D] Chuỗi tài sản từng ngày của các chiến lược vs Buy & Hold
│
├── src/                          # Mã nguồn nghiệp vụ đã module hóa
│   ├── __init__.py
│   ├── config.py                 # [Dùng chung] Danh sách 30 mã VN30, mốc ngày Train/Val/Test, đường dẫn
│   ├── ingest.py                 # [Người A] Kéo dữ liệu OHLCV VN30 & chỉ số vĩ mô
│   ├── crawler.py                # [Người A] Web Scraper cào tin tức CafeF/Vietstock & chấm điểm cảm xúc
│   ├── features.py               # [Người B] Làm sạch, ghép bảng, tính 25+ technical indicators & target
│   ├── eda_graph.py              # [Người B] Phân cụm K-Means/PCA & Phân tích đồ thị mạng lưới PageRank
│   ├── models.py                 # [Người C] Huấn luyện Regression, Classification & SOTA LSTM nhẹ
│   └── backtest.py               # [Người D] Mô phỏng giao dịch T+2.5, tính phí 0.15% + thuế 0.1%
│
├── notebooks/                    # Jupyter Notebooks phục vụ trình bày báo cáo & thí nghiệm từng phần
│   ├── 01_data_crawling.ipynb    # [Người A] Minh họa quá trình thu thập dữ liệu & cào web (L2)
│   ├── 02_eda_and_graph.ipynb    # [Người B] Minh họa làm sạch, EDA, PCA/K-Means & Đồ thị liên kết (L3-6, L10-11)
│   ├── 03_modeling_sota.ipynb    # [Người C] Minh họa huấn luyện ML & đối sánh 2 bài báo SOTA (L7, L12)
│   └── 04_backtest_sim.ipynb     # [Người D] Minh họa tinh chỉnh ngưỡng & mô phỏng chiến lược đầu tư (L12)
│
├── app/                          # Giao diện sản phẩm Demo
│   └── streamlit_app.py          # [Người E] Web Dashboard đa tab đọc trực tiếp từ data/processed/
│
└── docs/                         # Tài liệu báo cáo nộp trường
    ├── report_outline.md         # [Người E] Khung báo cáo PDF chuẩn 6 chương nộp giảng viên
    └── slide_outline.md          # [Người E] Khung slide thuyết trình 15 phút cho cả 5 thành viên
```

---

## 2. Bảng Phân Quyền Sở Hữu File (File Ownership Matrix)

Quy tắc vàng: **Ai là Owner của file nào thì chỉ người đó commit vào file đó**.

| Thành viên | File Code chính (`src/`, `app/`) | File Notebook (`notebooks/`) | File Dữ liệu xuất ra (`data/`) |
|---|---|---|---|
| **Người A** | `src/ingest.py`<br>`src/crawler.py` | `notebooks/01_data_crawling.ipynb` | `data/raw/prices.parquet`<br>`data/raw/news_sentiment.parquet`<br>`data/raw/macro.parquet` |
| **Người B** | `src/features.py`<br>`src/eda_graph.py` | `notebooks/02_eda_and_graph.ipynb` | `data/processed/features_all.parquet`<br>`data/processed/clusters_pca.csv`<br>`data/processed/graph_pagerank.csv` |
| **Người C** | `src/models.py` | `notebooks/03_modeling_sota.ipynb` | `data/processed/predictions.parquet`<br>`data/processed/sota_benchmark.csv`<br>`data/processed/feature_importance.csv` |
| **Người D** | `src/backtest.py` | `notebooks/04_backtest_sim.ipynb` | `data/processed/threshold_tuning.csv`<br>`data/processed/backtest_summary.csv`<br>`data/processed/equity_curve.parquet` |
| **Người E** | `app/streamlit_app.py`<br>`main.py`<br>`src/config.py` | *(Tổng hợp hình ảnh từ 4 notebooks trên vào Báo cáo)* | `docs/report_outline.md`<br>`docs/slide_outline.md` |
