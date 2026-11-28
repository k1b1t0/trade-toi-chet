# SOTA_PAPERS.md — Hồ Sơ 2 Bài Báo Khoa Học Quốc Tế Đối Chiếu Trong Đồ Án (`projects/capstone/`)

> **Mục đích**: Cung cấp toàn bộ thông tin học thuật, kiến trúc mô hình, chỉ số đánh giá và bảng đối chiếu mẫu từ **2 bài báo khoa học quốc tế (Q1/Q2 Open Access)** nghiên cứu trực tiếp trên **Thị trường Chứng khoán Việt Nam (HOSE / VN30)**.
> - **File PDF & Text nguyên bản** đã được tải về sẵn tại thư mục: `docs/papers/`.
> - **Phân hệ 03 (ML & SOTA)** benchmark chính theo bài **PLOS ONE (2025)** (`Linear/Logistic`, `Decision Tree`, `Random Forest`, `LightGBM`, `MLP` — thuần `scikit-learn` + `LightGBM`), và trích dẫn bài **Nature (2024)** ở phần Related Work.

---

## 1. Bài Báo Số 1: Nature Portfolio (2024) — Chuẩn Đối Sánh Nhánh Deep Learning (LSTM) & VN30

### 1.1. Thông tin trích dẫn chuẩn IEEE / APA
- **Tiêu đề**: *Applying machine learning algorithms to predict the stock price trend in the stock market – The case of Vietnam*
- **Tác giả**: Tran Phuoc, Pham Thi Kim Anh, Phan Huy Tam, & Chien V. Nguyen (2024).
- **Tạp chí**: *Humanities and Social Sciences Communications* (Nature Portfolio), 11(1), Article 393.
- **DOI**: `https://doi.org/10.1057/s41599-024-02807-x`
- **File trong kho**:
  - PDF: `docs/papers/nature-2024-vn30-ml-prediction.pdf`
  - Text: `docs/papers/nature-2024-vn30-ml-prediction.txt`

### 1.2. Tóm tắt Phương pháp & Kết quả của Bài báo
1. **Tập dữ liệu**: Lấy đúng danh sách **30 cổ phiếu rổ VN30** (ACB, BID, CTG, FPT, GAS, HDB, HPG, MBB, MSN, MWG, SSI, STB, TCB, VCB, VHM, VIC, VNM, VPB...) và chỉ số **VN-Index** trên sàn HOSE.
2. **Đặc trưng đầu vào (Features)**: Giá đóng cửa lịch sử kết hợp 3 chỉ báo phân tích kỹ thuật kinh điển:
   - `SMA` (Simple Moving Average)
   - `MACD` (Moving Average Convergence Divergence)
   - `RSI` (Relative Strength Index)
3. **Kiến trúc mô hình trong bài báo**:
   - Mạng **LSTM (Long Short-Term Memory)** gồm 4 lớp ẩn tuần tự: `30 -> 40 -> 50 -> 60 units`, hàm kích hoạt `ReLU`, `Dropout(0.1)` sau mỗi lớp, tối ưu bằng `Adam`, hàm mất mát `MSE`, dùng `EarlyStopping(patience=8)`.
4. **Cách đánh giá và hạn chế của bài báo (Điểm để nhóm mình phân tích ăn điểm 9.5)**:
   - Bài báo đánh giá sai số dự báo giá ngày tiếp theo so với biên độ trần/sàn $\pm 7\%$ của sàn HOSE (đạt độ chính xác giá ~93%,即 sai số tuyệt đối $< 7\%$).
   - **Hạn chế lớn mà nhóm chúng ta chỉ ra và khắc phục**:
     1. Dự báo mức giá tuyệt đối ngày $t+1$ có độ tự tương quan rất cao với giá ngày $t$ (mô hình Naive đoán giá ngày mai bằng giá hôm nay trên sàn HOSE cũng đã đạt độ chính xác $>93\%$ vì biên độ tối đa chỉ $\pm 7\%$). Do đó cần phải đo bằng **Tỷ suất sinh lời kỳ hạn 10 phiên (`target_return_10d`)** và **Độ chính xác phân loại xu hướng vượt ngưỡng phí (`Precision` & `ROC-AUC`)**.
     2. Bài báo chỉ dùng 3 chỉ báo kỹ thuật đơn lẻ, chưa tích hợp **Điểm cảm xúc tin tức tiếng Việt (News Sentiment)**, **Biến vĩ mô** và chưa mô phỏng **chi phí giao dịch 0.15% + thuế 0.1% + chu kỳ T+2.5**.

---

## 2. Bài Báo Số 2: PLOS ONE (9/2025) — Chuẩn Đối Sánh Nhánh Tree-Based ML & Feature Engineering

### 2.1. Thông tin trích dẫn chuẩn IEEE / APA
- **Tiêu đề**: *Predicting stock returns using machine learning combined with data envelopment analysis and automatic feature engineering: A case study on the Vietnamese stock market*
- **Tác giả**: Hoang Thanh Nhon, Nga Do-Thi, & Thao Nguyen-Trang (2025).
- **Tạp chí**: *PLOS ONE*, 20(9), e0332154.
- **DOI**: `https://doi.org/10.1371/journal.pone.0332154`
- **File trong kho**:
  - PDF: `docs/papers/plosone-2025-vn-stock-ml.pdf`
  - Text: `docs/papers/plosone-2025-vn-stock-ml.txt`

### 2.2. Tóm tắt Phương pháp & Kết quả của Bài báo
1. **Tập dữ liệu**: Các doanh nghiệp niêm yết trên sàn **HOSE (Việt Nam)** giai đoạn **2019–2024**.
2. **Các mô hình được đưa lên bàn cân so sánh (Table 4, trang 10 của bài báo)**:
   - `GLM` (Generalized Linear Model — Mô hình tuyến tính Baseline)
   - `SVR` (Support Vector Regression)
   - `RF` (Random Forest — Rừng ngẫu nhiên)
   - `GBT` (Gradient Boosted Trees / LightGBM)
   - `DANN` (Deep Artificial Neural Network)
3. **Kết quả thực nghiệm đắt giá từ Bài báo (Dùng để bảo vệ kết quả của nhóm)**:
   - Khi chưa có Feature Engineering tốt, mạng nơ-ron sâu `DANN` bị quá khớp nặng trên dữ liệu bảng chứng khoán Việt Nam với sai số lớn (`RMSE = 0.926`, `MAE = 0.337`), thua xa các mô hình cây như `Random Forest (RMSE = 0.155, MAE = 0.132)` và `Gradient Boosted Trees (RMSE = 0.158, MAE = 0.131)`.
   - Khi kết hợp **Kỹ nghệ Đặc trưng (Feature Engineering)**, mô hình **Gradient Boosted Trees (`F-DEA-GBT`) đạt hiệu năng xuất sắc nhất toàn cục** với `MAE = 0.122` và `MAPE = 103.19`, vượt qua cả mạng nơ-ron sâu (`MAE = 0.153`).
   - Bài báo cũng phát hiện yếu tố mùa vụ theo **Quý (`Quarter`)** tại Việt Nam: Quý 1 (trùng dịp Tết Nguyên Đán) có biến động mạnh và thanh khoản giảm, trong khi Quý 2 và Quý 4 ổn định hơn. (Đây là căn cứ trực tiếp để Người B đưa biến `quarter` và `month` vào bảng `features_all.parquet`).

---

## 3. Khung Bảng Đối Sánh Thực Nghiệm (Dùng Cho Người C & Báo Cáo Chương 4)

Trong báo cáo và trên Tab 3 của ứng dụng Streamlit, nhóm sẽ trình bày 2 bảng đối sánh chuẩn mực sau:

### Bảng 3.1: Đối sánh Nhánh Dự báo Lợi nhuận (Regression Benchmark — Tham chiếu PLOS ONE 2025)
| Mô hình (Model) | Nhóm phương pháp | RMSE (Thấp là tốt) | MAE (Thấp là tốt) | R² / Корреляция | Đối chiếu phát hiện từ Paper PLOS ONE (2025) |
|---|---|---|---|---|---|
| **Linear Regression (GLM)** | Baseline (Bài L7) | *Do Người C chạy* | *Do Người C chạy* | *Do Người C chạy* | Trong paper: `RMSE = 0.158, MAE = 0.129`. Mô hình đơn giản nhưng không bắt được tương tác phi tuyến theo Quý. |
| **Random Forest Regressor** | Tree Ensemble (Bài L7) | *Do Người C chạy* | *Do Người C chạy* | *Do Người C chạy* | Trong paper: `RMSE = 0.155, MAE = 0.132`. Ổn định, kháng nhiễu tốt trên dữ liệu bảng HOSE. |
| **LightGBM / GBT (25+ Features)** | Boosting + Feature Eng. | *Do Người C chạy* | *Do Người C chạy* | *Do Người C chạy* | Trong paper: **Đạt MAE tốt nhất (`0.122`)** nhờ kết hợp đặc trưng phi tuyến và yếu tố mùa vụ (`Quarter`). |

### Bảng 3.2: Đối sánh Nhánh Phân loại Xu hướng & Giao dịch (Classification & SOTA — Tham chiếu Nature 2024)
| Mô hình (Model) | Tham chiếu học thuật | Accuracy | Precision (`@0.50`) | Precision (`@0.55`) | ROC-AUC | CAGR Sau Phí (T+2.5) |
|---|---|---|---|---|---|---|
| **Logistic Regression** | Baseline phân loại (Bài L7) | *Người C* | *Người C* | *Người C* | *Người C* | *Người D* |
| **Decision Tree (`depth=10`)** | Cây đơn lẻ (SMA Module 3) | *Người C* | *Người C* | *Người C* | *Người C* | *Người D* |
| **Random Forest (`depth=13`)** | Rừng ngẫu nhiên (Bài L7 & SMA M4) | *Người C* | *Người C* | *Người C* | *Người C* | *Người D* |
| **LightGBM Classifier (+News)** | Đề xuất của nhóm (Multi-source) | *Người C* | *Người C* | *Người C* | *Người C* | *Người D* |
| **LSTM / MLP (SMA+MACD+RSI)** | Cài đặt theo Paper Nature (2024) | *Người C* | *Người C* | *Người C* | *Người C* | *Người D* |
