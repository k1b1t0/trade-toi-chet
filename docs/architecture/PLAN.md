# PLAN.md — Kế Hoạch Tổng Thể Đồ Án Capstone (`projects/capstone/`)

> **Tên Đề Tài**: *Hệ thống Thu thập Dữ liệu Đa nguồn, Dự báo Lợi nhuận và Mô phỏng Chiến lược Giao dịch Tự động trên Rổ Cổ phiếu VN30 ứng dụng Học máy*
> - **Mục tiêu 1**: Đạt **9.5+ điểm** Bài tập lớn môn **IT4930 (Nhập môn Khoa học Dữ liệu)** — Bao phủ 100% slide bài giảng L1–L12 + Có Web Crawling thực tế + So sánh 2 bài báo SOTA + Có Web App Streamlit Demo.
> - **Mục tiêu 2**: Nộp đồ án thực hành môn **IT3190 (Nhập môn Học máy & Khai phá Dữ liệu)**.
> - **Mục tiêu 3**: Đạt điểm tối đa Rubric Capstone Project của **Stock Markets Analytics Zoomcamp 2026**.

---

## 1. Giải Mã 5 Tiêu Chí Cốt Lõi Để Đạt Điểm 9.5 Môn IT4930

Dựa trên bảng điểm và nhận xét trực tiếp của hội đồng chấm kỳ trước ([sources/reports-sample/summary-ds-grading-insights.txt](../../sources/reports-sample/summary-ds-grading-insights.txt)):

| Tiêu chí chấm của Giảng viên | Lỗi khiến các nhóm kỳ trước bị hạ xuống 8.0–8.5 | Thiết kế trong Dự án của nhóm chúng ta (Đạt 9.5) |
|---|---|---|
| **1. So sánh State of the Art (SOTA) & Bài báo khoa học** | Không có đối sánh bài báo, chỉ chạy 1-2 model cơ bản (Nhóm 21, 23 được nhắc bổ sung SOTA mới lên 9.5). | Đã cào sẵn 2 bài báo quốc tế (Nature 2024 & PLOS ONE 2025) nghiên cứu đúng trên **chứng khoán Việt Nam (VN30/HOSE)**. Lập bảng thực nghiệm đối đầu giữa Baseline (Linear/Logistic) vs Tree ML (RF/LightGBM) vs Deep Learning (LSTM) theo đúng bộ chỉ số của 2 bài báo. Xem [SOTA_PAPERS.md](SOTA_PAPERS.md). |
| **2. Giao diện Demo tương tác (Web App)** | Chỉ nộp Jupyter Notebook hoặc giao diện chưa hoàn thiện (Nhóm 14). | Xây dựng ứng dụng **Streamlit Dashboard 5 Tabs** bằng Python thuần, trực quan hóa từ dữ liệu thô, đồ thị mạng lưới đến mô phỏng đầu tư T+2.5. |
| **3. Tự thu thập dữ liệu đa nguồn (Web Crawling)** | Chỉ tải 1 file CSV có sẵn trên Kaggle (Nhóm 12 chỉ được 8.0–8.2). | Tích hợp 3 nguồn: (1) Giá lịch sử 30 mã VN30 qua API `vnstock`, (2) **Web Scraper (`BeautifulSoup`)** tự động cào tin tức tài chính tiếng Việt từ CafeF/Vietstock, (3) Dữ liệu vĩ mô & chỉ số VN-Index. |
| **4. Cơ chế Đánh giá Đa chiều (Evaluation Metrics)** | Chỉ đo Accuracy đơn lẻ, thiếu cơ chế đánh giá nghiệp vụ (Nhóm 4 bị trừ còn 8.0). | Đánh giá 3 tầng: **Hồi quy** (`RMSE`, `MAE`, `MAPE`, `R2`), **Phân loại** (`Accuracy`, `Precision`, `Recall`, `F1`, `ROC-AUC`), và **Tài chính thực tế** (`CAGR`, `Sharpe Ratio`, `Max Drawdown`, `Win Rate` sau khi trừ phí 0.15%, thuế 0.1% và độ trễ T+2.5). |
| **5. Bao phủ toàn diện chương trình môn học `02-ds`** | Thiếu các kỹ thuật đặc trưng dạy trong môn học như Phân cụm, Giảm chiều hay Phân tích mạng lưới. | Bao phủ trọn vẹn từ **L1 đến L12** (có cả K-Means + PCA ở Bài L4 và Đồ thị tương quan PageRank ở Bài L10–11). |

---

## 2. Bản Đồ Ánh Xạ Chi Tiết Từng Bài Giảng Môn `02-ds` (L1 $\to$ L12)

Bảng này được dùng làm khung sườn trực tiếp cho **Báo cáo PDF** và **Slide Bảo vệ** để giảng viên nhìn thấy nhóm đã vận dụng triệt để kiến thức trên lớp:

1. **Lecture 1 (Tổng quan Khoa học Dữ liệu)**:
   - Phát biểu bài toán hỗ trợ ra quyết định đầu tư định lượng trên rổ VN30.
   - Thiết kế quy trình khép kín: `Thu thập -> Tích hợp & Làm sạch -> Khám phá & Đồ thị -> Học máy & SOTA -> Mô phỏng & Triển khai`.
2. **Lecture 2 (Thu thập dữ liệu & Web Crawling)**:
   - Xây dựng trình thu thập dữ liệu web (`src/crawler.py`) gửi HTTP Request, phân tích cây DOM HTML bằng `BeautifulSoup4` để bóc tách tiêu đề, thời gian và mã cổ phiếu từ chuyên mục chứng khoán CafeF/Vietstock.
   - Kết hợp thu thập dữ liệu có cấu trúc từ API tài chính (`src/ingest.py`).
3. **Lecture 3 (Làm sạch & Tích hợp dữ liệu — Data Integration & Preprocessing)**:
   - **Tích hợp dữ liệu (Schema Integration)**: Đồng bộ 3 nguồn có tần suất khác nhau (Giá theo ngày giao dịch, Tin tức phát sinh bất kỳ lúc nào kể cả cuối tuần, Vĩ mô theo tháng/ngày) về chung khóa `(date, ticker)`.
   - **Xử lý khuyết thiếu (Imputation)**: Áp dụng `forward-fill` theo từng mã cổ phiếu (tuyệt đối không dùng `backward-fill` gây rò rỉ tương lai).
   - **Xử lý ngoại lai (Outlier Detection)**: Phát hiện và cắt ngưỡng (Winsorization / IQR clipping) các phiên biến động dị biệt do lỗi dữ liệu hoặc chia tách cổ phiếu.
   - **Chuẩn hóa (Scaling)**: Sử dụng `StandardScaler` (chỉ `fit` trên tập Train).
4. **Lecture 4 (Phân tích khám phá dữ liệu — EDA, PCA & Clustering)**:
   - Tính toán thống kê mô tả (Mean, Median, IQR, Skewness, Kurtosis) chứng minh phân phối lợi nhuận chứng khoán có đuôi dày (Fat-tailed).
   - **Giảm chiều dữ liệu (PCA)**: Nén các đặc trưng tài chính về mặt phẳng 2D (`pca_1`, `pca_2`).
   - **Phân cụm không giám sát (K-Means Clustering)**: Tự động gom 30 mã VN30 thành 4 cụm đặc trưng (VD: Cụm Ngân hàng dẫn dắt, Cụm Tăng trưởng Beta cao, Cụm Phòng thủ cổ tức ổn định, Cụm Biến động đầu cơ).
5. **Lecture 5 & Lecture 6 (Trực quan hóa đơn biến & đa biến)**:
   - Đơn biến: Histogram & Boxplot phân phối lợi nhuận theo ngành/quý.
   - Đa biến: Biểu đồ Nến (Candlestick + Bollinger Bands + Volume), Ma trận nhiệt tương quan (Correlation Heatmap), Biểu đồ bong bóng đa chiều (Bubble Chart: `Số lệnh/ngày` vs `CAGR` vs `Quy mô vốn`).
6. **Lecture 7 (Học máy cơ bản — Hồi quy & Rừng ngẫu nhiên)**:
   - Cài đặt đúng 2 trụ cột trọng tâm trong Slide L7: **Hồi quy tuyến tính (Linear / Logistic Regression)** làm Baseline và **Rừng ngẫu nhiên (Random Forest)** làm mô hình cốt lõi, kèm trích xuất độ quan trọng đặc trưng (`Feature Importance`).
7. **Lecture 8 (Quản trị và Phân tích Dữ liệu lớn)**:
   - Lưu trữ dữ liệu định dạng cột nén **Apache Parquet** (nhanh gấp 10 lần và nhẹ hơn 75% so với CSV).
   - Giải quyết bài toán **Lời nguyền số chiều (Curse of Dimensionality)**: Thực nghiệm chứng minh việc loại bỏ các biến giả One-Hot dư thừa giúp mô hình hội tụ nhanh và tăng CAGR (kế thừa trực tiếp kết quả Question 1 của Homework 4).
8. **Lecture 10 & Lecture 11 (Phân tích kiểu dữ liệu đặc thù: Phân tích Liên kết Đồ thị & Văn bản)**:
   - **Link Analysis (Đồ thị mạng lưới)**: Biểu diễn 30 mã VN30 thành một đồ thị $G = (V, E)$, trong đó cạnh nối giữa 2 mã tồn tại nếu hệ số tương quan lợi nhuận Pearson $> 0.6$. Áp dụng thuật toán **PageRank** và **Bậc của đỉnh (Degree Centrality)** để tìm ra cổ phiếu trung tâm dẫn dắt toàn thị trường.
   - **Text Analytics**: Tiền xử lý tiêu đề tin tức tiếng Việt và lượng hóa thành chỉ số `sentiment_score` mỗi ngày.
9. **Lecture 12 (Đánh giá kết quả phân tích — Evaluation Strategies & Metrics)**:
   - Thiết kế chiến lược **Temporal Hold-out Split** (70% Train, 15% Validation, 15% Test) phù hợp với chuỗi thời gian.
   - Đo lường đầy đủ bộ chỉ số học máy và thực hiện tinh chỉnh ngưỡng quyết định (**Threshold Tuning** trên `predict_proba`) gắn liền với mô phỏng tài chính thực tế.

---

## 3. Lộ Trình Thực Hiện 3 Giai Đoạn (Fast-Track Timeline cho 5 Người)

Nhờ cơ chế **Mock Data theo đúng `API_CONTRACTS.md`**, cả 5 người làm việc song song theo 3 mốc ngắn gọn:

### Giai đoạn 1: Khởi tạo & Chạy Song Song trên Mock Data (Ngày 1 – Ngày 2)
- **Người E** tạo khung repo, cấu hình `src/config.py` và chạy script sinh dữ liệu mẫu vào `data/raw/` và `data/processed/`.
- **Người A** viết `src/ingest.py` và `src/crawler.py` để kéo dữ liệu thật từ `vnstock` và cào tin tức CafeF.
- **Người B, C, D, E** dùng ngay dữ liệu mẫu để viết xong 80% logic của `features.py`, `eda_graph.py`, `models.py`, `backtest.py` và giao diện `streamlit_app.py`.

### Giai đoạn 2: Đổ Dữ Liệu Thật & Chạy Thực Nghiệm SOTA (Ngày 3 – Ngày 4)
- **Người A** bàn giao bộ 3 file dữ liệu thật trong `data/raw/`.
- **Người B** chạy `features.py` và `eda_graph.py` trên dữ liệu thật, xuất `features_all.parquet`, `clusters_pca.csv`, `graph_pagerank.csv` và hoàn thiện Notebook 02.
- **Người C** chạy `models.py` huấn luyện toàn bộ mô hình, xuất bảng `sota_benchmark.csv` đối chiếu 2 bài báo khoa học và hoàn thiện Notebook 03.
- **Người D** chạy `backtest.py` mô phỏng chiến lược T+2.5 trên dự báo thật của Người C, xuất `backtest_summary.csv`, `equity_curve.parquet` và hoàn thiện Notebook 04.

### Giai đoạn 3: Đóng Gói Giao Diện, Viết Báo Cáo PDF & Tổng Duyệt (Ngày 5 – Ngày 6)
- **Người E** chạy `python main.py` kiểm tra luồng tự động đầu-cuối, kết nối toàn bộ bảng kết quả thật lên 5 Tab của **Streamlit Dashboard**.
- Cả 5 thành viên ghép nội dung từ 4 Notebook vào Báo cáo PDF chuẩn 6 chương và Slide thuyết trình 15 phút (mỗi người trình bày đúng 3 phút về phân hệ mình làm).
