# API_CONTRACTS.md — Hợp Đồng Dữ Liệu (Data Schemas) & Giao Diện Hàm Python (`projects/capstone/`)

> **TÀI LIỆU QUAN TRỌNG NHẤT ĐỂ LÀM VIỆC SONG SONG**:
> Cả 5 thành viên (A, B, C, D, E) **BẮT BUỘC** tuân thủ đúng 100% tên file, tên cột, kiểu dữ liệu (`dtype`) và chữ ký hàm (function signatures) trong tài liệu này. Chỉ cần đúng hợp đồng này, code của 5 người viết độc lập sẽ ghép vào nhau chạy trơn tru ngay lần đầu tiên.

---

## 1. Hằng Số Dùng Chung (`src/config.py`)

```python
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

# Danh sách 30 mã cổ phiếu rổ VN30 + chỉ số chuẩn VNINDEX
VN30_TICKERS = [
    "ACB", "BCM", "BID", "BVH", "CTG", "FPT", "GAS", "GVR", "HDB", "HPG",
    "MBB", "MSN", "MWG", "PLX", "POW", "SAB", "SHB", "SSB", "SSI", "STB",
    "TCB", "TPB", "VCB", "VHM", "VIB", "VIC", "VJC", "VNM", "VPB", "VRE"
]
BENCHMARK_TICKER = "VNINDEX"

# Khoảng thời gian lấy dữ liệu & Mốc chia Temporal Split (Chống Look-ahead Bias)
START_DATE = "2019-01-01"
END_DATE = "2026-03-01"

TRAIN_END_DATE = "2023-12-31"   # ~70% dữ liệu: 2019 - 2023
VAL_END_DATE   = "2024-12-31"   # ~15% dữ liệu: năm 2024
# Tập Test: từ "2025-01-01" trở đi (~15% dữ liệu)

# Tham số thị trường chứng khoán Việt Nam (dùng cho nhãn & Backtest)
HOLDING_DAYS = 10               # Chu kỳ dự báo & nắm giữ cơ sở: 10 phiên giao dịch (~2 tuần)
TARGET_THRESHOLD = 0.015        # Nhãn Class 1 nếu lợi nhuận 10 phiên > +1.5% (vượt phí + lãi phi rủi ro)
VN_BUY_FEE = 0.0015             # Phí giao dịch chiều mua: 0.15%
VN_SELL_FEE = 0.0015            # Phí giao dịch chiều bán: 0.15%
VN_SELL_TAX = 0.0010            # Thuế thu nhập bán chứng khoán tại VN: 0.10% (Tổng phí 2 chiều = 0.40%)
MIN_HOLD_T_PLUS = 3             # Quy định T+2.5: Mua ngày T thì tối thiểu ngày T+3 mới được bán
RANDOM_SEED = 42
```

---

## 2. Hợp Đồng Bảng Dữ Liệu — Tầng 1: `data/raw/` (Output của Người A $\to$ Input của Người B)

### 2.1. File `data/raw/prices.parquet`
Chứa dữ liệu giá lịch sử theo ngày của 30 mã `VN30_TICKERS` và `VNINDEX`.
- **Khóa chính (Primary Key)**: `(date, ticker)` — đã sắp xếp tăng dần theo `ticker, date`, không có dòng trùng lặp.

| Tên cột | Kiểu dữ liệu (`dtype`) | Mô tả & Quy chuẩn |
|---|---|---|
| `date` | `datetime64[ns]` | Ngày giao dịch (không có giờ/timezone, định dạng `YYYY-MM-DD`). |
| `ticker` | `string` / `object` | Mã cổ phiếu viết hoa (VD: `"FPT"`, `"HPG"`, `"VNINDEX"`). |
| `open` | `float64` | Giá mở cửa (đồng hoặc nghìn đồng, miễn là đồng nhất với `close`). |
| `high` | `float64` | Giá cao nhất trong phiên. |
| `low` | `float64` | Giá thấp nhất trong phiên. |
| `close` | `float64` | Giá đóng cửa đã điều chỉnh (Adjusted Close). |
| `volume` | `float64` | Khối lượng khớp lệnh trong phiên ($\ge 0$). |
| `sector` | `string` / `object` | Nhóm ngành của cổ phiếu (VD: `"Banking"`, `"Technology"`, `"RealEstate"`, `"Steel"`, `"Retail"`, `"Energy"`, `"Index"`). |

### 2.2. File `data/raw/news_sentiment.parquet`
Chứa dữ liệu tin tức cào được từ CafeF/Vietstock và điểm cảm xúc đã tổng hợp theo từng `(date, ticker)`.

| Tên cột | Kiểu dữ liệu (`dtype`) | Mô tả & Quy chuẩn |
|---|---|---|
| `date` | `datetime64[ns]` | Ngày đăng bài viết (nếu đăng cuối tuần thì quy về phiên giao dịch kế tiếp). |
| `ticker` | `string` / `object` | Mã cổ phiếu liên quan (hoặc `"MARKET"` nếu là tin chung toàn thị trường). |
| `news_count` | `int64` | Số lượng tin tức xuất hiện trong ngày của mã đó ($\ge 1$). |
| `sentiment_score` | `float64` | Điểm cảm xúc trung bình trong ngày, nằm trong đoạn `[-1.0, 1.0]` (`> 0.1`: Tích cực, `< -0.1`: Tiêu cực, còn lại Trung lập). |
| `sample_headline` | `string` / `object` | Tiêu đề bài báo tiêu biểu nhất trong ngày (để hiển thị lên bảng tin Streamlit). |

### 2.3. File `data/raw/macro.parquet`
Chứa các chỉ số thị trường chung và kinh tế vĩ mô theo từng ngày `date`.

| Tên cột | Kiểu dữ liệu (`dtype`) | Mô tả & Quy chuẩn |
|---|---|---|
| `date` | `datetime64[ns]` | Ngày giao dịch. |
| `vnindex_close` | `float64` | Điểm số đóng cửa của chỉ số VN-Index. |
| `vnindex_return_1d` | `float64` | Tỷ suất sinh lời 1 ngày của VN-Index: `(close_t / close_{t-1}) - 1`. |
| `vnindex_volatility_20d`| `float64` | Độ biến động (độ lệch chuẩn 20 phiên) của `vnindex_return_1d`. |
| `usd_vnd_rate` | `float64` | Tỷ giá USD/VND (hoặc chỉ số DXY). |
| `sbv_policy_rate` | `float64` | Lãi suất điều hành / lãi suất liên ngân hàng Việt Nam (%/năm, VD: `4.5`). |

---

## 3. Hợp Đồng Bảng Dữ Liệu — Tầng 2: `data/processed/` (Output của Người B $\to$ Input của Người C & E)

### 3.1. File `data/processed/features_all.parquet`
Bảng trung tâm đã gộp 3 nguồn của Người A, làm sạch, tính toán >25 đặc trưng và gán nhãn `split`, `target`. Chỉ giữ lại 30 mã cổ phiếu trong `VN30_TICKERS` (đã tách `VNINDEX` sang cột macro).

| Nhóm cột | Danh sách tên cột bắt buộc | Kiểu dữ liệu | Mô tả |
|---|---|---|---|
| **Định danh & Chia tập** | `date`, `ticker`, `sector`, `split` | `datetime64[ns]`, `str`, `str`, `str` | `split` nhận đúng 1 trong 3 giá trị: `"train"`, `"validation"`, `"test"`. |
| **Giá gốc (để Backtest)** | `open`, `high`, `low`, `close`, `volume` | `float64` | Giữ nguyên giá thực tế để Người D tính lời/lỗ. |
| **Đặc trưng Lợi nhuận trễ (Lag Returns)** | `return_1d`, `return_3d`, `return_5d`, `return_10d`, `return_20d`, `return_60d` | `float64` | `(close_t / close_{t-k}) - 1`. |
| **Chỉ báo Xu hướng (Trend)** | `sma_10`, `sma_20`, `sma_50`, `ema_12`, `ema_26`, `price_to_sma20`, `sma10_to_sma50`, `macd`, `macd_signal`, `macd_hist`, `macd_norm`, `macd_hist_norm` | `float64` | Giữ `sma/ema/macd` gốc để vẽ biểu đồ; đưa vào ML chỉ dùng tỷ lệ không đơn vị (`price_to_sma20 = close/sma_20 - 1`, `sma10_to_sma50 = sma_10/sma_50 - 1`, `macd_norm = macd/close`, `macd_hist_norm = macd_hist/close`). |
| **Chỉ báo Động lượng & Biến động** | `rsi_14`, `stoch_k`, `stoch_d`, `bb_upper_ratio`, `bb_lower_ratio`, `bb_width`, `atr_14`, `natr_14`, `volatility_10d`, `volatility_20d` | `float64` | RSI (0-100), Bollinger Ratios (`(close - bb)/close`, `bb_width = (upper-lower)/sma_20`), `natr_14 = atr_14/close` (dùng cho ML; giữ `atr_14` gốc để vẽ chart). |
| **Đặc trưng Khối lượng & Dòng tiền** | `ln_volume`, `volume_to_sma20`, `obv_slope_5d` | `float64` | Logarit khối lượng, tỷ lệ khối lượng `volume / sma20(volume)`, độ dốc dòng tiền OBV chuẩn hóa. |
| **Đặc trưng Tin tức & Vĩ mô** | `sentiment_score`, `sentiment_ma5`, `news_count`, `vnindex_return_1d`, `vnindex_return_10d`, `vnindex_volatility_20d`, `relative_strength_vs_vnindex`, `usd_vnd_rate`, `sbv_policy_rate` | `float64` | Yêu cầu backfill tin CafeF từ `2019-01-01`; ngày không có tin điền `sentiment_score = 0.0`, `news_count = 0`. `return_1d` chỉ clip an toàn `±15%` (giữ nguyên lịch sử HNX/UPCOM 2019–2021, không sửa `close`). |
| **Biến Thời gian** | `month`, `weekday`, `quarter` | `int32` | Tháng (1-12), Thứ trong tuần (0-4), Quý (1-4) (khớp phát hiện Quý 1 Tết âm lịch của Paper PLOS ONE 2025). |
| **Nhãn Dự báo (Targets)** | `target_return_10d`<br>`target_class`<br>`max_high_next_10d`<br>`min_low_next_10d` | `float64`<br>`int32`<br>`float64`<br>`float64` | - `target_return_10d = (close_{t+10} / close_t) - 1` (Dùng cho Regression).<br>- `target_class = 1` nếu `target_return_10d > 0.015` ngược lại `0` (Dùng cho Classification).<br>- `max_high_next_10d`, `min_low_next_10d`: Giá cao/thấp nhất từ `t+3` đến `t+10` (để Phân hệ 04 mô phỏng Take-profit / Stop-loss sau khi hàng T+2.5 về). |

### 3.2. File `data/processed/clusters_pca.csv` (Phục vụ Bài L4: Phân cụm & Giảm chiều)
Bảng 30 dòng (ứng với 30 mã VN30), **chỉ tính trên tập lịch sử `split in ("train", "validation")` (`date <= 2024-12-31`)** để tuyệt đối chống Look-ahead Bias.
- **Các cột**: `ticker`, `sector`, `mean_annual_return`, `annual_volatility`, `sharpe_hist`, `pca_1`, `pca_2`, `cluster_id` (`int`: 0, 1, 2, 3), `cluster_name` (`str`: VD `"Cụm Tăng trưởng cao"`, `"Cụm Phòng thủ ổn định"`...).

### 3.3. File `data/processed/graph_pagerank.csv` (Phục vụ Bài L10-11: Phân tích liên kết mạng lưới)
Bảng xếp hạng mức độ ảnh hưởng (PageRank & Degree Centrality) của 30 mã VN30 trong đồ thị tương quan, **chỉ tính trên tập lịch sử `split in ("train", "validation")` (`date <= 2024-12-31`)**.
- **Các cột**: `ticker`, `sector`, `pagerank_score` (`float64`), `degree_centrality` (`float64`), `connected_peers` (`str`: danh sách các mã có tương quan $\ge 0.6$ cách nhau bởi dấu phẩy, VD `"CTG,MBB,TCB"`).

---

## 4. Hợp Đồng Bảng Dữ Liệu — Tầng 3: `data/processed/` (Output của Người C $\to$ Input của Người D & E)

### 4.1. File `data/processed/predictions.parquet`
Chứa toàn bộ các dòng của tập `"validation"` và `"test"` từ `features_all.parquet`, kèm theo kết quả dự báo của các mô hình học máy.

| Tên cột | Kiểu dữ liệu | Mô tả |
|---|---|---|
| `date`, `ticker`, `sector`, `split` | `datetime64[ns]`, `str`, `str`, `str` | Giữ nguyên từ bảng `features_all.parquet`. |
| `close`, `target_return_10d`, `target_class`, `max_high_next_10d`, `min_low_next_10d`, `vnindex_return_1d` | `float64` / `int32` | Các cột thực tế để Người D chấm điểm mô phỏng tài chính. |
| `pred_reg_linear` | `float64` | Lợi nhuận 10 phiên dự báo bởi Linear Regression. |
| `pred_reg_rf` | `float64` | Lợi nhuận 10 phiên dự báo bởi Random Forest Regressor. |
| `pred_reg_lgbm` | `float64` | Lợi nhuận 10 phiên dự báo bởi LightGBM Regressor (Mô hình tốt nhất theo Paper PLOS ONE 2025). |
| `proba_logistic` | `float64` | Xác suất `target_class == 1` `[0.0, 1.0]` của Logistic Regression. |
| `proba_dt` | `float64` | Xác suất `target_class == 1` `[0.0, 1.0]` của Decision Tree (`max_depth=10`). |
| `proba_rf` | `float64` | Xác suất `target_class == 1` `[0.0, 1.0]` của Random Forest (`n_estimators=100, max_depth=13`). |
| `proba_lgbm` | `float64` | Xác suất `target_class == 1` `[0.0, 1.0]` của LightGBM Classifier. |
| `proba_lstm_sota` | `float64` | Xác suất `target_class == 1` `[0.0, 1.0]` của mạng chuỗi thời gian LSTM/MLP (Đối sánh Paper Nature 2024). |

### 4.2. File `data/processed/sota_benchmark.csv`
Bảng tổng hợp kết quả đánh giá mô hình trên tập Test để hiển thị lên Tab 3 của Streamlit và đưa thẳng vào Báo cáo PDF.
- **Các cột**:
  `model_name`, `task_type` (`"Regression"` hoặc `"Classification"`), `paper_reference` (VD: `"Baseline (L7)"`, `"PLOS ONE 2025 SOTA"`, `"Nature 2024 SOTA"`), `rmse`, `mae`, `mape`, `r2`, `accuracy`, `precision_at_50`, `precision_at_55`, `recall_at_55`, `f1_at_55`, `roc_auc`, `train_time_sec`.

### 4.3. File `data/processed/feature_importance.csv`
- **Các cột**: `feature_name`, `importance_rf`, `importance_lgbm`, `feature_group` (`"Technical"`, `"Macro"`, `"Sentiment"`, `"LagReturn"`).

---

## 5. Hợp Đồng Bảng Dữ Liệu — Tầng 4: `data/processed/` (Output của Người D $\to$ Input của Người E)

### 5.1. File `data/processed/threshold_tuning.csv`
Kết quả quét ngưỡng xác suất từ `0.50` đến `0.70` (bước nhảy `0.02`) cho mô hình tốt nhất (`proba_rf` và `proba_lgbm`).
- **Các cột**: `model_col`, `threshold`, `total_trades`, `avg_trades_per_day`, `precision`, `win_rate`, `net_return_pct`, `cagr`, `sharpe_ratio`, `max_drawdown_pct`.

### 5.2. File `data/processed/backtest_summary.csv`
Bảng so sánh hiệu quả tài chính trên tập Test giữa 6 chiến lược (gồm thêm Baseline gửi tiết kiệm theo lãi suất SBV).
- **Các cột**:
  `strategy_id`, `strategy_name` (VD: `"Savings Benchmark (SBV Policy Rate)"`, `"Buy & Hold VN-Index"`, `"Equal-Weight VN30"`, `"Random Forest (Threshold 0.55)"`, `"LightGBM Top-3 + T+2.5 StopLoss/TakeProfit"`, `"LSTM SOTA (Nature 2024)"`), `initial_capital_vnd`, `final_capital_vnd`, `total_return_pct`, `cagr_pct`, `sharpe_ratio`, `sortino_ratio`, `max_drawdown_pct`, `total_trades`, `win_rate_pct`, `total_fees_and_tax_vnd`.

### 5.3. File `data/processed/equity_curve.parquet`
Chuỗi giá trị tài sản theo từng ngày trên tập Test để vẽ biểu đồ đường cong vốn (Equity Curve & Underwater Drawdown Chart).
- **Các cột**: `date`, `sbv_savings_nav`, `vnindex_nav`, `rf_rule55_nav`, `lgbm_top3_nav`, `lstm_sota_nav`, `lgbm_drawdown_pct`, `vnindex_drawdown_pct`.

---

## 6. Hợp Đồng Chữ Ký Hàm Python (Sub-Package Entrypoints)

Để `main.py` gọi tự động từ đầu đến cuối, mỗi sub-package trong `src/` **bắt buộc export đúng hàm entrypoint tại `__init__.py`** (khớp `AGENTS.md`):

```python
# 1. Phân hệ 01 — src/ingestion/__init__.py
def run_ingestion(start_date: str, end_date: str, output_dir: Path) -> None:
    """Tải prices.parquet và macro.parquet vào output_dir (data/raw/)."""

def run_news_crawler(tickers: list[str], output_dir: Path) -> None:
    """Cào tin tức CafeF (backfill từ 2019) & tính điểm cảm xúc, lưu news_sentiment.parquet."""

# 2. Phân hệ 02 — src/processing/__init__.py
def build_feature_dataset(raw_dir: Path, processed_dir: Path) -> pd.DataFrame:
    """Đọc 3 file từ raw_dir, làm sạch, tính 25+ features, lưu features_all.parquet."""

def run_eda_and_graph_analysis(features_path: Path, processed_dir: Path) -> None:
    """Tính PCA/K-Means (clusters_pca.csv) và Đồ thị PageRank (graph_pagerank.csv) trên tập <= 2024-12-31."""

# 3. Phân hệ 03 — src/modeling/__init__.py
def train_and_evaluate_all_models(features_path: Path, processed_dir: Path) -> None:
    """Huấn luyện Regression + Classification + SOTA (chỉ dùng FEATURE_COLS không đơn vị), xuất predictions.parquet, sota_benchmark.csv, feature_importance.csv."""

# 4. Phân hệ 04 — src/backtesting/__init__.py
def run_backtest_simulations(predictions_path: Path, processed_dir: Path) -> None:
    """Chạy quét ngưỡng và mô phỏng T+2.5 (kèm Baseline SBV), xuất threshold_tuning.csv, backtest_summary.csv, equity_curve.parquet."""
```
