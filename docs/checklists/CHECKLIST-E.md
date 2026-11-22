# CHECKLIST-E.md — Đặc Tả Công Việc Của Người E: Streamlit UI, Automation & Report Lead

> **Vai trò của bạn**: Chịu trách nhiệm **Tầng 5 (Tích hợp Hệ thống, Xây dựng Web App Dashboard bằng Streamlit, Tự động hóa Pipeline và Biên tập Báo cáo PDF / Slide Bảo vệ)**.
> - **Bao phủ kiến thức môn `02-ds`**: **Bài L1** (Tổng quan quy trình & Sản phẩm hỗ trợ ra quyết định), **Bài L5–6** (Thiết kế Dashboard trực quan hóa đa chiều), và tiêu chí bắt buộc của giảng viên: *"Cần hoàn thiện giao diện mới được 9.5"* + *"Hệ thống chạy thử nghiệm dễ sử dụng, có hướng dẫn cài đặt rõ ràng"*.
> - **Tại sao việc của bạn rất nhàn và không bao giờ bị nghẽn**: Ngay từ Ngày 1, bạn viết `scripts/generate_mock_data.py` sinh ra các file kết quả mẫu trong `data/processed/`. Giao diện `app/streamlit_app.py` của bạn **chỉ đọc các file `.parquet` và `.csv` đó để vẽ biểu đồ**, không cần chờ A, B, C, D chạy xong thuật toán!

---

## 1. Các File Bạn Sở Hữu (Chỉ mình bạn code vào các file này)

1. `src/config.py` & `scripts/generate_mock_data.py` — Cấu hình hằng số dùng chung và script khởi tạo dữ liệu mẫu Ngày 1 cho cả nhóm.
2. `app/streamlit_app.py` — Ứng dụng Web Dashboard tương tác gồm 5 Tabs trình diễn toàn bộ kết quả của nhóm.
3. `main.py` — Script CLI tự động chạy nối tiếp các hàm của Người A $\to$ B $\to$ C $\to$ D bằng 1 câu lệnh duy nhất.
4. `docs/report_outline.md` & `docs/slide_outline.md` — Khung báo cáo PDF 6 chương và Slide thuyết trình 15 phút.

---

## 2. Công Nghệ & Thư Viện Sử Dụng

- **Web App Framework**: `streamlit` (`st.set_page_config(layout="wide")`, `st.tabs`, `st.metric`, `st.plotly_chart`, `st.dataframe`).
- **Đồ thị tương tác**: `plotly.express`, `plotly.graph_objects` (Biểu đồ nến Candlestick, Scatter PCA, Đồ thị mạng lưới Network Graph, Đường cong tài sản Equity Curve).
- **Điều phối CLI**: `argparse`, `logging`, `time` trong `main.py`.

---

## 3. Lộ Trình Các Bước Thực Hiện Chi Tiết (Step-by-Step Checklist)

### Bước 1: Khởi tạo `src/config.py` và `scripts/generate_mock_data.py` (Làm đầu tiên trong 15 phút)
- [ ] Tạo `src/config.py` chứa đúng các hằng số quy định trong [API_CONTRACTS.md](API_CONTRACTS.md).
- [ ] Viết `scripts/generate_mock_data.py` sinh nhanh bộ dữ liệu giả lập (đúng 100% tên cột và kiểu dữ liệu) vào `data/raw/` và `data/processed/`.
- [ ] Thông báo cho A, B, C, D kéo code về chạy thử để có dữ liệu mẫu làm việc song song ngay lập tức.

### Bước 2: Xây dựng Giao diện `app/streamlit_app.py` (5 Tabs Chuẩn Rubric 9.5 Điểm)
Thiết kế giao diện sáng sủa, có Sidebar bên trái chọn Mã cổ phiếu VN30 và Tham số mô phỏng, phần chính chia làm **5 Tabs** khớp với 5 phần báo cáo:

- [ ] **Tab 1 — Thu Thập Đa Nguồn & Tin Tức (Bài L2 - Người A)**:
  - Hiển thị 4 thẻ `st.metric`: Số mã cổ phiếu (30 mã VN30), Khoảng thời gian (2019–2026), Tổng số bản ghi giá, Tổng số tin tức tài chính đã cào.
  - Biểu đồ Nến (`go.Candlestick`) của mã cổ phiếu được chọn + Đường `SMA20`, `SMA50` + Khối lượng giao dịch.
  - Bảng tin tức CafeF/Vietstock của mã đó kèm cột màu sắc `sentiment_score` (Xanh: Tích cực, Xám: Trung lập, Đỏ: Tiêu cực).
- [ ] **Tab 2 — Khám Phá EDA, Phân Cụm K-Means & Đồ Thị Liên Kết (Bài L3, L4, L10-11 - Người B)**:
  - Biểu đồ Scatter 2D mặt phẳng `PCA (pca_1 vs pca_2)` tô màu theo 4 cụm `K-Means` của 30 mã VN30 (đọc từ `clusters_pca.csv`).
  - Biểu đồ Đồ thị Mạng lưới (`Network Graph` tương quan VN30) và Bảng xếp hạng điểm **PageRank** chỉ ra cổ phiếu dẫn dắt thị trường (đọc từ `graph_pagerank.csv`).
- [ ] **Tab 3 — Học Máy & Đối Sánh 2 Bài Báo Khoa Học SOTA (Bài L7, L12 - Người C)**:
  - Hộp thông tin (`st.info`) trích dẫn rõ 2 bài báo: **Nature Portfolio (2024)** và **PLOS ONE (2025)**.
  - Bảng Benchmark đối sánh trực tiếp các mô hình (`Linear`, `Logistic`, `Decision Tree`, `Random Forest`, `LightGBM`, `LSTM SOTA`) đọc từ `sota_benchmark.csv`.
  - Biểu đồ cột ngang `Top 15 Feature Importance` đọc từ `feature_importance.csv`.
- [ ] **Tab 4 — Mô Phỏng Chiến Lược Giao Dịch T+2.5 (Bài L12 & SMA M4-5 - Người D)**:
  - Biểu đồ ảnh hưởng của ngưỡng xác suất (`Threshold 0.50 -> 0.70`) tới `Precision`, `Số lệnh/ngày` và `CAGR` (đọc từ `threshold_tuning.csv`).
  - Bộ thanh trượt tương tác (`st.slider`): Cho phép giảng viên kéo thử *Ngưỡng xác suất Mua* và *Vốn đầu tư ban đầu (VNĐ)* để xem kết quả thay đổi trực tiếp!
  - Bảng tổng hợp hiệu quả tài chính (`CAGR`, `Sharpe Ratio`, `Max Drawdown`, `Win Rate` sau khi trừ phí 0.15% + thuế 0.1%) đọc từ `backtest_summary.csv`.
  - Biểu đồ Đường cong tăng trưởng vốn (`Equity Curve`) so sánh chiến lược AI với `Buy & Hold VN-Index` (đọc từ `equity_curve.parquet`).
- [ ] **Tab 5 — Khuyến Nghị Tín Hiệu Giao Dịch Hôm Nay (Automation - Người E)**:
  - Lọc ngày mới nhất trong `predictions.parquet`, xếp hạng giảm dần theo `proba_lgbm` và hiển thị **Top 3 Cổ phiếu VN30 khuyến nghị giải ngân**, kèm điểm cảm xúc tin tức và mức giá cắt lỗ (`-7%`) / chốt lời (`+15%`) dự kiến.

### Bước 3: Viết `main.py` Chạy Tự Động Toàn Bộ Pipeline
- [ ] Kết nối 4 hàm entrypoint của Người A, B, C, D theo đúng thứ tự trong [API_CONTRACTS.md](API_CONTRACTS.md).
- [ ] Hỗ trợ cờ `--mode mock` (sinh data mẫu và chạy kiểm thử toàn hệ thống trong 10 giây), `--mode offline` (chạy từ data thật đã lưu trong `data/raw/`), và `--mode live` (kéo data mới nhất rồi chạy toàn bộ pipeline).

### Bước 4: Tổng hợp Báo cáo PDF & Slide Thuyết trình (`docs/`)
- [ ] Biên tập Báo cáo PDF khoảng 20–25 trang theo đúng 6 chương yêu cầu trong Slide `L0-course-inf-vn.pdf` của môn học:
  1. *Chương 1*: Phát biểu bài toán & Tổng quan hệ thống (Người E).
  2. *Chương 2*: Thu thập dữ liệu đa nguồn, Web Crawling & Tiền xử lý (Người A & B).
  3. *Chương 3*: Phân tích khám phá (EDA), Phân cụm PCA/K-Means & Đồ thị PageRank (Người B).
  4. *Chương 4*: Mô hình hóa Học máy & Đối sánh 2 Bài báo SOTA Nature/PLOS ONE (Người C).
  5. *Chương 5*: Tinh chỉnh ngưỡng & Mô phỏng giao dịch thực tế T+2.5 (Người D).
  6. *Chương 6*: Kiến trúc triển khai Web App Streamlit, Khó khăn & Kết luận (Người E).

---

## 4. Tiêu Chí Nghiệm Thu Toàn Hệ Thống (Definition of Done)

```bash
# 1. Chạy thử toàn bộ pipeline đầu-cuối
python main.py --mode offline

# 2. Khởi động giao diện Web Dashboard kiểm tra cả 5 Tabs
streamlit run app/streamlit_app.py
```
