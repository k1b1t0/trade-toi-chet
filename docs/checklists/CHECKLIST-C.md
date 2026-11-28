# CHECKLIST-C.md — Đặc Tả Công Việc Của Người C: Machine Learning & SOTA Paper Benchmark Engineer

> **Vai trò của bạn**: Chịu trách nhiệm toàn bộ **Tầng 3 (Mô hình hóa Học máy & Đối sánh Thực nghiệm với 2 Bài báo Khoa học Quốc tế)**.
> - **Bao phủ kiến thức môn `02-ds`**: **Bài L7** (Học máy cơ bản: Hồi quy tuyến tính & Rừng ngẫu nhiên) và **Bài L12** (Chiến lược đánh giá mô hình & Bộ chỉ số thực nghiệm).
> - **Tại sao phần của bạn là "Chìa khóa 9.5 điểm"**: Giảng viên chấm môn IT4930 ghi rất rõ trong bảng điểm kỳ trước: *"Nếu nhóm so sánh được State of the Art / Bài báo thì điểm 9.5"*. Bạn đã có sẵn toàn bộ thông tin và thông số của 2 bài báo chứng khoán Việt Nam trong file [SOTA_PAPERS.md](SOTA_PAPERS.md) để cài đặt và xuất bảng `sota_benchmark.csv`.

---

## 1. Các File Bạn Sở Hữu (Chỉ mình bạn code vào các file này)

1. `src/modeling/` — Sub-package (chia file `< 130` dòng, export `train_and_evaluate_all_models` tại `__init__.py`, có `cli.py`) huấn luyện cả 2 nhánh mô hình (**Regression** & **Classification / SOTA**) và xuất dự báo cùng bảng metric.
2. `tests/test_modeling.py` — Unit tests & Data Contract tests kiểm tra 3 file đầu ra khớp `API_CONTRACTS.md`.
3. `notebooks/03_modeling_sota.ipynb` — Notebook trình bày chi tiết phương pháp chia dữ liệu chuỗi thời gian, quá trình huấn luyện, bảng so sánh đối đầu với 2 bài báo `Nature (2024)` và `PLOS ONE (2025)`, biểu đồ ROC Curve và Feature Importance để đưa thẳng vào Chương 4 của Báo cáo PDF.
4. `docs/modules/03-modeling.md` — Tài liệu kỹ thuật chi tiết của phân hệ.

---

## 2. Công Nghệ & Thư Viện Sử Dụng

- **Tiền xử lý cho ML**: `sklearn.impute.SimpleImputer(strategy='median')`, `sklearn.preprocessing.StandardScaler()`.
- **Mô hình trong Slide Bài L7 & SMA Zoomcamp**:
  - `LinearRegression`, `LogisticRegression(max_iter=1000)`
  - `DecisionTreeClassifier(max_depth=10, random_state=42)`
  - `RandomForestRegressor(n_estimators=100, max_depth=12, random_state=42, n_jobs=-1)`
  - `RandomForestClassifier(n_estimators=100, max_depth=13, random_state=42, n_jobs=-1)`
- **Mô hình Boosting & Neural SOTA (Đối sánh 1 Paper chính: PLOS ONE 2025 — không cần cài PyTorch/XGBoost)**:
  - `lightgbm.LGBMRegressor` & `lightgbm.LGBMClassifier` (đại diện họ Gradient Boosted Trees quán quân trong bài báo PLOS ONE 2025).
  - `MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=200, early_stopping=True, random_state=42)` (đại diện nhánh Neural Net trong bài báo PLOS ONE 2025, chạy thuần `scikit-learn` trên CPU).

---

## 3. Lộ Trình Các Bước Thực Hiện Chi Tiết (Step-by-Step Checklist)

### Bước 1: Chuẩn bị Tập Đặc trưng & Chia Temporal Split (Chống Look-ahead Bias)
- [ ] Đọc `data/processed/features_all.parquet`.
- [ ] Định nghĩa danh sách các cột `FEATURE_COLS` (chỉ dùng các chỉ báo **tỷ lệ `%` không đơn vị / đã chuẩn hóa** theo chuẩn `sma-zoomcamp`; loại bỏ các cột định danh `date, ticker, sector, split`, giá thô & chỉ báo đơn vị VNĐ tuyệt đối `open, high, low, close, volume, sma_10, sma_20, sma_50, ema_12, ema_26, atr_14, macd, macd_signal, macd_hist`, và các cột nhãn `target_return_10d, target_class, max_high_next_10d, min_low_next_10d`).
- [ ] Tách dữ liệu theo cột `split` theo **quy trình 1-Pass + Purge 10 phiên cuối `train`** (0% data leak, gọn đúng chuẩn `sma-zoomcamp`):
  - `train_df = df[df['split'] == 'train']` → **Purge bỏ 10 phiên cuối cùng của mỗi mã trong `train_df`** (vì nhãn `target_return_10d` của 10 phiên cuối 2023 dùng giá đầu 01/2024 của tập Validation).
  - `val_df = df[df['split'] == 'validation']` (2024 — dùng để so sánh và cho Phần 4 quét chọn ngưỡng $\tau^*$).
  - `test_df = df[df['split'] == 'test']` (2025–2026 — khóa kín, chỉ dự báo đánh giá cuối cùng).
- [ ] Fit `SimpleImputer`, `StandardScaler` và toàn bộ mô hình **chỉ 1 lần trên `train_df` đã purge**, sau đó `.transform()` & `.predict()` ra cả `val_df` và `test_df`.

### Bước 2: Huấn luyện Nhánh 1 — Dự báo Lợi nhuận (`Regression` — Đối sánh Paper PLOS ONE 2025)
- [ ] Nhãn mục tiêu: `y_reg = target_return_10d`.
- [ ] Huấn luyện 3 mô hình:
  1. `LinearRegression` (tương ứng mô hình `GLM` trong Paper PLOS ONE 2025).
  2. `RandomForestRegressor` (tương ứng mô hình `RF` trong Paper PLOS ONE 2025).
  3. `LGBMRegressor` / `HistGradientBoostingRegressor` (tương ứng mô hình quán quân `F-DEA-GBT` trong Paper PLOS ONE 2025).
- [ ] Dự báo trên tập Validation & Test, lưu vào 3 cột: `pred_reg_linear`, `pred_reg_rf`, `pred_reg_lgbm`.
- [ ] Tính bộ chỉ số trên tập Test: `RMSE`, `MAE`, `sMAPE` (tránh chia cho 0 khi `target_return_10d == 0`), `R2` và hệ số tương quan Pearson giữa lợi nhuận dự báo và thực tế.

### Bước 3: Huấn luyện Nhánh 2 — Phân loại Xu hướng (`Classification & SOTA` — Đối sánh Paper PLOS ONE 2025)
- [ ] Nhãn mục tiêu: `y_clf = target_class` (`1` nếu lợi nhuận 10 phiên $> +1.5\%$, ngược lại `0`).
- [ ] Huấn luyện 5 mô hình và trích xuất xác suất Lớp 1 bằng `.predict_proba(X)[:, 1]`:
  1. `LogisticRegression` $\to$ lưu cột `proba_logistic`.
  2. `DecisionTreeClassifier(max_depth=10)` $\to$ lưu cột `proba_dt`.
  3. `RandomForestClassifier(n_estimators=100, max_depth=13)` $\to$ lưu cột `proba_rf`.
  4. `LGBMClassifier(n_estimators=150, max_depth=8, learning_rate=0.05)` $\to$ lưu cột `proba_lgbm`.
  5. `MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=200, early_stopping=True)` $\to$ lưu cột `proba_mlp_sota`.
- [ ] Tính bộ chỉ số trên tập Test cho cả 5 mô hình:
  - `Accuracy`
  - `Precision @ threshold 0.50` và `Precision @ threshold 0.55`
  - `Recall @ threshold 0.55` và `F1-Score @ threshold 0.55`
  - `ROC-AUC Score`
  - Thời gian huấn luyện (`train_time_sec`).

### Bước 4: Xuất 3 File Kết Quả Chuẩn Hợp Đồng Cho Người D & Người E
- [ ] Xuất `data/processed/predictions.parquet` (gồm các dòng `validation` và `test` kèm đầy đủ 8 cột dự báo).
- [ ] Xuất `data/processed/sota_benchmark.csv` (bảng tổng hợp metric của cả nhánh Regression và Classification kèm cột `paper_reference` đối chiếu trực tiếp với `Nature 2024` và `PLOS ONE 2025`).
- [ ] Trích xuất độ quan trọng đặc trưng từ `RandomForest` và `LightGBM`, lưu ra `data/processed/feature_importance.csv`.

### Bước 5: Hoàn thiện `notebooks/03_modeling_sota.ipynb`
- [ ] Trình bày bảng so sánh kết quả thực nghiệm của nhóm đặt cạnh số liệu trong 2 bài báo khoa học.
- [ ] Viết đoạn phân tích học thuật: Giải thích vì sao trên dữ liệu bảng tài chính kết hợp tin tức và vĩ mô, `Random Forest` và `Gradient Boosted Trees` đạt tỷ lệ `Precision @ 0.55` và độ ổn định cao hơn mạng nơ-ron thuần túy (đồng nhất với kết luận của bài báo PLOS ONE 2025).
- [ ] Vẽ biểu đồ `ROC Curve` so sánh 5 mô hình và biểu đồ ngang `Top 15 Feature Importance`.

---

## 4. Tiêu Chí Nghiệm Thu Bàn Giao Cho Người D & E (Definition of Done)

```bash
python -c "
import pandas as pd
pred = pd.read_parquet('data/processed/predictions.parquet')
req_cols = ['date','ticker','close','target_return_10d','target_class','proba_rf','proba_lgbm','proba_lstm_sota']
assert all(c in pred.columns for c in req_cols), 'Missing prediction columns!'
bench = pd.read_csv('data/processed/sota_benchmark.csv')
fi = pd.read_csv('data/processed/feature_importance.csv')
print('OK predictions.parquet:', pred.shape)
print('OK sota_benchmark.csv:\n', bench[['model_name','task_type','paper_reference','rmse','precision_at_55','roc_auc']])
"
```
