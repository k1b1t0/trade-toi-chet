# CHECKLIST.md — Bảng Điều Phối Tổng & Kiểm Soát Tiến Độ 5 Thành Viên (`projects/capstone/`)

> Tài liệu này giúp cả nhóm theo dõi tiến độ tổng thể, điểm bàn giao (Handoff Checkpoints) giữa 5 thành viên **Người A, Người B, Người C, Người D, Người E**, và danh mục kiểm tra cuối cùng trước khi nộp đồ án đạt mục tiêu **9.5+ điểm**.

---

## 1. Bảng Phân Công Tổng Quan 5 Thành Viên

| Thành viên | Vai trò (Role) | Bài giảng `02-ds` phụ trách | File đặc tả chi tiết | File Code & Notebook sở hữu |
|---|---|---|---|---|
| **Người A** | **Data Ingestion & Web Crawling Engineer** | **L2** (Web Crawling), **L8** (Parquet Storage), **L10-11** (Text Sentiment) | [CHECKLIST-A.md](CHECKLIST-A.md) | `src/ingestion/`, `tests/test_ingestion.py`<br>`notebooks/01_data_crawling.ipynb`, `docs/modules/01-ingestion.md` |
| **Người B** | **Data Integration, EDA, Clustering & Graph Analyst** | **L3** (Cleaning/Integration), **L4** (EDA/PCA/K-Means), **L5-6** (DataViz), **L10-11** (Link Analysis PageRank) | [CHECKLIST-B.md](CHECKLIST-B.md) | `src/processing/`, `tests/test_processing.py`<br>`notebooks/02_eda_and_graph.ipynb`, `docs/modules/02-processing.md` |
| **Người C** | **Machine Learning & SOTA Paper Benchmark Engineer** | **L7** (Linear/Logistic & Random Forest), **L12** (Model Evaluation & SOTA Benchmark) | [CHECKLIST-C.md](CHECKLIST-C.md) | `src/modeling/`, `tests/test_modeling.py`<br>`notebooks/03_modeling_sota.ipynb`, `docs/modules/03-modeling.md` |
| **Người D** | **Quantitative Backtesting & Risk Simulation Engineer** | **L12** (Experimental Evaluation & Threshold Tuning), **SMA Module 4 & 5** (Backtest T+2.5) | [CHECKLIST-D.md](CHECKLIST-D.md) | `src/backtesting/`, `tests/test_backtesting.py`<br>`notebooks/04_backtest_sim.ipynb`, `docs/modules/04-backtesting.md` |
| **Người E** | **Streamlit UI, Automation & Final Report Lead** | **L1** (Overview & Problem), **L5-6** (Interactive Dashboard), **E2E Automation** | [CHECKLIST-E.md](CHECKLIST-E.md) | `src/dashboard/`, `main.py`, `tests/test_dashboard.py`<br>`docs/modules/05-dashboard.md` |

---

## 2. Checklist Phối Hợp Theo Từng Mốc (Team Milestones)

### Mốc 0: Khởi tạo Môi trường & Hợp đồng Dữ liệu
- [x] Khởi tạo `src/config.py`, `pyproject.toml` và kiểm tra hợp đồng [API_CONTRACTS.md](../architecture/API_CONTRACTS.md).
- [x] Cả 5 thành viên kéo repo về và cài môi trường bằng `uv sync`.

### Mốc 1: Phát triển Độc lập & Song song theo Sub-packages
- [x] **Phân hệ 01 (`src/ingestion/`)**: Kéo giá 30 mã VN30 + VN-Index (Entrade/DNSE), vĩ mô (Yahoo Finance `VND=X` + SBV) và cào tin CafeF kèm `pub_time` + model cảm xúc leak-free (`<= 2023-12-31`).
- [ ] **Phân hệ 02 (`src/processing/`)**: Ghép bảng, làm sạch OHLC vector hóa, tính 25+ biến kỹ thuật không đơn vị, giữ 10 phiên cuối (`split='live'`), PCA/K-Means và Đồ thị PageRank (`<= 2024-12-31`).
- [ ] **Phân hệ 03 (`src/modeling/`)**: Huấn luyện 1-Pass (purge 10 phiên cuối `train`) gồm Regression 3 models + Classification 5 models (`Logistic`, `DT`, `RF`, `LightGBM`, `MLP`), đối sánh `PLOS ONE 2025` và xuất `sota_benchmark.csv` (dùng `sMAPE`).
- [ ] **Phân hệ 04 (`src/backtesting/`)**: Quét ngưỡng trên `validation` (đã purge 10 phiên cuối 2024), mô phỏng 6 chiến lược trên `test` (khớp `open_{t+1}`, T+3 xấp xỉ T+2.5, max 10 slot) và export `simulate_strategy()`.
- [ ] **Phân hệ 05 (`src/dashboard/app.py` & `main.py`)**: 5 Tabs tương tác và pipeline chạy tự động (`--mode offline` / `--mode live`).

### Mốc 2: Ghép nối Dữ liệu Thật & Chạy Thực Nghiệm
- [x] **Phân hệ 01** bàn giao `data/raw/{prices,news_sentiment,macro,sentiment_labels}.parquet` + `sentiment_tfidf.joblib` và chạy sạch `notebooks/01_data_crawling.ipynb`.
- [ ] **Phân hệ 02** bàn giao `features_all.parquet`, `clusters_pca.csv`, `graph_pagerank.csv` và chạy sạch `notebooks/02_eda_and_graph.ipynb`.
- [ ] **Phân hệ 03** bàn giao `predictions.parquet`, `sota_benchmark.csv`, `feature_importance.csv` và chạy sạch `notebooks/03_modeling_sota.ipynb`.
- [ ] **Phân hệ 04** bàn giao `threshold_tuning.csv`, `backtest_summary.csv`, `equity_curve.parquet` và chạy sạch `notebooks/04_backtest_sim.ipynb`.

### Mốc 3: Kiểm tra Tiêu chuẩn Điểm 9.5 & Đóng gói Nộp bài
- [x] **Tiêu chí 1 (Web Crawling - Bài L2)**: Notebook 01 & `news_sentiment.parquet` chứa tin tức CafeF thực tế kèm `pub_time` và điểm cảm xúc leak-free.
- [ ] **Tiêu chí 2 (EDA, PCA/K-Means & PageRank - Bài L3, L4, L10-11)**: Notebook 02 & Tab 2 Streamlit có biểu đồ phân cụm 30 mã VN30 và đồ thị mạng lưới tương quan PageRank.
- [ ] **Tiêu chí 3 (Đối sánh SOTA - Bài L7, L12)**: Notebook 03, Tab 3 Streamlit và Chương 4 Báo cáo có bảng đối sánh thực nghiệm với `PLOS ONE (2025)` (nhắc thêm `Nature 2024` ở Related Work).
- [ ] **Tiêu chí 4 (Đánh giá Đa chiều & Thực chiến T+3/T+2.5)**: Notebook 04 & Tab 4 Streamlit có đủ ML metrics (`RMSE`, `MAE`, `sMAPE`, `Precision`, `F1`, `ROC-AUC`) và Financial metrics (`CAGR`, `Sharpe`, `Sortino`, `Max Drawdown`, `Win Rate`).
- [ ] **Tiêu chí 5 (Web App & DoD)**: `ruff check`, `ty check`, `uv run pytest -v` PASS 100%; `uv run streamlit run src/dashboard/app.py` hiển thị đẹp cả 5 Tabs.
