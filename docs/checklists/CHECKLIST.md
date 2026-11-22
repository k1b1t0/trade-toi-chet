# CHECKLIST.md — Bảng Điều Phối Tổng & Kiểm Soát Tiến Độ 5 Thành Viên (`projects/capstone/`)

> Tài liệu này giúp cả nhóm theo dõi tiến độ tổng thể, điểm bàn giao (Handoff Checkpoints) giữa 5 thành viên **Người A, Người B, Người C, Người D, Người E**, và danh mục kiểm tra cuối cùng trước khi nộp đồ án đạt mục tiêu **9.5+ điểm**.

---

## 1. Bảng Phân Công Tổng Quan 5 Thành Viên

| Thành viên | Vai trò (Role) | Bài giảng `02-ds` phụ trách | File đặc tả chi tiết | File Code & Notebook sở hữu |
|---|---|---|---|---|
| **Người A** | **Data Ingestion & Web Crawling Engineer** | **L2** (Web Crawling), **L8** (Parquet Storage), **L10-11** (Text Sentiment) | [CHECKLIST-A.md](CHECKLIST-A.md) | `src/ingest.py`, `src/crawler.py`<br>`notebooks/01_data_crawling.ipynb` |
| **Người B** | **Data Integration, EDA, Clustering & Graph Analyst** | **L3** (Cleaning/Integration), **L4** (EDA/PCA/K-Means), **L5-6** (DataViz), **L10-11** (Link Analysis PageRank) | [CHECKLIST-B.md](CHECKLIST-B.md) | `src/features.py`, `src/eda_graph.py`<br>`notebooks/02_eda_and_graph.ipynb` |
| **Người C** | **Machine Learning & SOTA Paper Benchmark Engineer** | **L7** (Linear/Logistic & Random Forest), **L12** (Model Evaluation & SOTA Benchmark) | [CHECKLIST-C.md](CHECKLIST-C.md) | `src/models.py`<br>`notebooks/03_modeling_sota.ipynb` |
| **Người D** | **Quantitative Backtesting & Risk Simulation Engineer** | **L12** (Experimental Evaluation & Threshold Tuning), **SMA Module 4 & 5** (Backtest T+2.5) | [CHECKLIST-D.md](CHECKLIST-D.md) | `src/backtest.py`<br>`notebooks/04_backtest_sim.ipynb` |
| **Người E** | **Streamlit UI, Automation & Final Report Lead** | **L1** (Overview & Problem), **L5-6** (Interactive Dashboard), **E2E Automation** | [CHECKLIST-E.md](CHECKLIST-E.md) | `app/streamlit_app.py`, `main.py`, `src/config.py`<br>`docs/report_outline.md` |

---

## 2. Checklist Phối Hợp Theo Từng Mốc (Team Milestones)

### Mốc 0: Khởi tạo Môi trường & Mock Data (Làm ngay trong 15 phút đầu tiên)
- [ ] **Người E** khởi tạo `src/config.py`, `pyproject.toml`, `requirements.txt` và `scripts/generate_mock_data.py`.
- [ ] Cả 5 thành viên kéo repo về, cài môi trường (`uv sync` hoặc `pip install -r requirements.txt`) và chạy `python scripts/generate_mock_data.py`.
- [ ] Kiểm tra thư mục `data/raw/` và `data/processed/` đã có đủ các file mẫu đúng chuẩn [API_CONTRACTS.md](API_CONTRACTS.md).

### Mốc 1: Phát triển Độc lập & Song song (Ngày 1 – Ngày 2)
- [ ] **Người A**: Hoàn thành `src/ingest.py` (kéo 30 mã VN30 + VN-Index + Vĩ mô) và `src/crawler.py` (cào tin tức CafeF/Vietstock + chấm điểm cảm xúc).
- [ ] **Người B**: Hoàn thành `src/features.py` (ghép bảng, khử missing/outliers, tính 25+ biến kỹ thuật) và `src/eda_graph.py` (PCA + K-Means + Đồ thị PageRank) chạy mượt trên dữ liệu mẫu.
- [ ] **Người C**: Hoàn thành `src/models.py` (huấn luyện nhánh Regression 3 models + nhánh Classification 5 models gồm cả LSTM nhẹ, xuất bảng đối sánh 2 bài báo SOTA) chạy mượt trên dữ liệu mẫu.
- [ ] **Người D**: Hoàn thành `src/backtest.py` (quét ngưỡng Threshold 0.50–0.70, mô phỏng giao dịch T+2.5 có phí 0.15% + thuế 0.1% + Stop-loss/Take-profit) chạy mượt trên dữ liệu mẫu.
- [ ] **Người E**: Hoàn thành `app/streamlit_app.py` (5 Tabs tương tác đọc từ `data/processed/`) và `main.py`.

### Mốc 2: Ghép nối Dữ liệu Thật & Chạy Thực Nghiệm (Ngày 3 – Ngày 4)
- [ ] **Người A** bàn giao 3 file thật vào `data/raw/` (`prices.parquet`, `news_sentiment.parquet`, `macro.parquet`) và chạy sạch `notebooks/01_data_crawling.ipynb`.
- [ ] **Người B** chạy code trên dữ liệu thật của Người A, bàn giao `features_all.parquet`, `clusters_pca.csv`, `graph_pagerank.csv` và chạy sạch `notebooks/02_eda_and_graph.ipynb`.
- [ ] **Người C** chạy huấn luyện trên `features_all.parquet` thật, bàn giao `predictions.parquet`, `sota_benchmark.csv`, `feature_importance.csv` và chạy sạch `notebooks/03_modeling_sota.ipynb`.
- [ ] **Người D** chạy mô phỏng trên `predictions.parquet` thật, bàn giao `threshold_tuning.csv`, `backtest_summary.csv`, `equity_curve.parquet` và chạy sạch `notebooks/04_backtest_sim.ipynb`.

### Mốc 3: Kiểm tra Tiêu chuẩn Điểm 9.5 & Đóng gói Nộp bài (Ngày 5 – Ngày 6)
- [ ] **Kiểm định Tiêu chí 1 (Web Crawling - Bài L2)**: Trong Notebook 01 và Tab 1 Streamlit có bảng tin tức tiếng Việt thực tế cào từ CafeF/Vietstock kèm điểm cảm xúc.
- [ ] **Kiểm định Tiêu chí 2 (EDA, PCA/K-Means & Đồ thị PageRank - Bài L3, L4, L10-11)**: Trong Notebook 02 và Tab 2 Streamlit có biểu đồ phân cụm 30 mã VN30 và đồ thị mạng lưới tương quan PageRank.
- [ ] **Kiểm định Tiêu chí 3 (Đối sánh 2 Bài báo SOTA - Bài L7, L12)**: Trong Notebook 03, Tab 3 Streamlit và Chương 4 Báo cáo có bảng đối đầu kết quả thực nghiệm của nhóm với Paper Nature (2024) và Paper PLOS ONE (2025).
- [ ] **Kiểm định Tiêu chí 4 (Đánh giá Đa chiều & Thực chiến T+2.5)**: Trong Notebook 04 và Tab 4 Streamlit có đủ chỉ số ML (`RMSE`, `MAE`, `Precision`, `F1`, `ROC-AUC`) và chỉ số Tài chính (`CAGR`, `Sharpe`, `Max Drawdown`).
- [ ] **Kiểm định Tiêu chí 5 (Web App & Hồ sơ bàn giao)**: Chạy `python main.py --mode offline` dưới 30 giây không lỗi; `streamlit run app/streamlit_app.py` hiển thị đẹp cả 5 Tab; xuất file Báo cáo PDF và file nén mã nguồn kèm `README.md`.
