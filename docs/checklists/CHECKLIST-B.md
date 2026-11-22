# CHECKLIST-B.md — Đặc Tả Công Việc Của Người B: Data Prep, EDA, Clustering & Graph Analyst

> **Vai trò của bạn**: Chịu trách nhiệm toàn bộ **Tầng 2 (Làm sạch, Tích hợp Dữ liệu, Kỹ nghệ Đặc trưng, Phân cụm K-Means/PCA và Đồ thị Liên kết PageRank)**.
> - **Bao phủ kiến thức môn `02-ds`**: **Bài L3** (Làm sạch & Tích hợp dữ liệu), **Bài L4** (Khám phá dữ liệu EDA, Giảm chiều PCA, Phân cụm K-Means), **Bài L5–6** (Trực quan hóa đa biến), và **Bài L10–11** (Phân tích Liên kết Đồ thị — Link Analysis & PageRank).
> - **Tại sao bạn có thể code ngay từ Ngày 1**: Dùng dữ liệu mẫu từ `scripts/generate_mock_data.py` trong `data/raw/` để viết xong toàn bộ hàm trước khi Người A cào xong dữ liệu thật.

---

## 1. Các File Bạn Sở Hữu (Chỉ mình bạn code vào các file này)

1. `src/features.py` — Module tích hợp 3 bảng từ `data/raw/`, xử lý khuyết thiếu/ngoại lai và sinh 25+ chỉ báo kỹ thuật + nhãn dự báo.
2. `src/eda_graph.py` — Module chạy phân cụm không giám sát (`PCA` + `KMeans`) và phân tích mạng lưới tương quan cổ phiếu (`networkx` + `PageRank`).
3. `notebooks/02_eda_and_graph.ipynb` — Notebook trình bày toàn bộ thống kê mô tả, biểu đồ EDA, mặt phẳng phân cụm PCA và đồ thị mạng lưới VN30 để đưa vào Chương 2 & Chương 3 của Báo cáo PDF.

---

## 2. Công Nghệ & Thư Viện Sử Dụng

- **Xử lý bảng & Chuỗi thời gian**: `pandas`, `numpy` (tự viết các công thức vector hóa cho SMA, EMA, RSI, MACD, Bollinger Bands, ATR, OBV bằng `rolling()` và `ewm()` của Pandas — **không cần cài `ta-lib` C++** để tránh lỗi biên dịch trên máy các bạn trong nhóm).
- **Giảm chiều & Phân cụm**: `sklearn.preprocessing.StandardScaler`, `sklearn.decomposition.PCA`, `sklearn.cluster.KMeans`.
- **Phân tích Đồ thị Liên kết (Bài L10–11)**: `networkx` (`nx.Graph()`, `nx.pagerank()`, `nx.degree_centrality()`).
- **Trực quan hóa**: `plotly.express`, `plotly.graph_objects`, `seaborn`, `matplotlib`.

---

## 3. Lộ Trình Các Bước Thực Hiện Chi Tiết (Step-by-Step Checklist)

### Bước 1: Viết `src/features.py` tạo `data/processed/features_all.parquet`
- [ ] **Tích hợp dữ liệu (Data Integration - Bài L3)**:
  - Đọc `prices.parquet`, `news_sentiment.parquet`, `macro.parquet` từ `data/raw/`.
  - Lọc bảng `prices` giữ lại 30 mã cổ phiếu trong `VN30_TICKERS`.
  - Left-join `prices` với `macro` theo `date`.
  - Left-join tiếp với `news_sentiment` theo `(date, ticker)`. Những ngày không có tin tức của mã đó thì điền `sentiment_score = 0.0` và `news_count = 0`.
- [ ] **Làm sạch & Xử lý Ngoại lai (Data Cleaning - Bài L3)**:
  - Sắp xếp đúng thứ tự `['ticker', 'date']`.
  - Điền khuyết cho các cột vĩ mô/giá bằng `groupby('ticker').ffill()` (**Tuyệt đối không dùng `bfill()`** để tránh rò rỉ dữ liệu tương lai).
  - Tính lợi nhuận ngày `return_1d` và dùng phương pháp **IQR Clipping** (hoặc cắt ngưỡng biên độ sàn HOSE $\pm 7\%$) để khử các điểm dị biệt (Outliers).
- [ ] **Kỹ nghệ Đặc trưng (Feature Engineering — 25+ biến)**:
  - Tính theo từng `ticker` (`groupby('ticker')`):
    - **Lag Returns**: `return_1d`, `return_3d`, `return_5d`, `return_10d`, `return_20d`, `return_60d`.
    - **Trend (khớp Paper Nature 2024)**: `sma_10`, `sma_20`, `sma_50`, `ema_12`, `ema_26`, `price_to_sma20 = close / sma_20 - 1`, `sma10_to_sma50 = sma_10 / sma_50 - 1`, `macd = ema_12 - ema_26`, `macd_signal = macd.ewm(span=9).mean()`, `macd_hist = macd - macd_signal`.
    - **Momentum & Volatility**: `rsi_14`, `stoch_k`, `stoch_d`, `bb_upper_ratio`, `bb_lower_ratio`, `bb_width`, `atr_14`, `natr_14 = atr_14 / close`, `volatility_10d`, `volatility_20d`.
    - **Volume & Flow**: `ln_volume = np.log(volume + 1.0)`, `volume_to_sma20`, `obv_slope_5d`.
    - **Sentiment & Macro**: `sentiment_ma5` (trung bình trượt 5 phiên của `sentiment_score`), `vnindex_return_10d`, `relative_strength_vs_vnindex = return_10d - vnindex_return_10d`.
    - **Seasonality (khớp Paper PLOS ONE 2025)**: `month`, `weekday`, `quarter`.
- [ ] **Tạo Nhãn Dự báo (Targets) & Chia Tập (`split`)**:
  - `target_return_10d = groupby('ticker')['close'].shift(-10) / close - 1`.
  - `target_class = (target_return_10d > 0.015).astype('int32')`.
  - `max_high_next_10d` và `min_low_next_10d`: Giá cao nhất / thấp nhất trong cửa sổ từ `t+3` đến `t+10` (sau khi cổ phiếu về tài khoản theo chu kỳ T+2.5).
  - Gán cột `split`: `"train"` nếu `date <= "2023-12-31"`, `"validation"` nếu `"2024-01-01" <= date <= "2024-12-31"`, `"test"` nếu `date >= "2025-01-01"`.
  - Loại bỏ các dòng đầu/cuối bị `NaN` do cửa sổ trượt, lưu ra `data/processed/features_all.parquet`.

### Bước 2: Viết `src/eda_graph.py` tạo `clusters_pca.csv` và `graph_pagerank.csv`
- [ ] **Phân cụm K-Means & Giảm chiều PCA (Bài L4)**:
  - Trên tập dữ liệu lịch sử, tính cho mỗi mã trong 30 mã VN30: Lợi nhuận trung bình năm (`mean_annual_return`), Độ biến động năm (`annual_volatility`), Tỷ số Sharpe (`sharpe_hist`), Beta so với VN-Index, và Thanh khoản trung bình.
  - Chuẩn hóa bằng `StandardScaler`, chiếu xuống 2 chiều `pca_1`, `pca_2` bằng `PCA(n_components=2, random_state=42)`.
  - Phân thành 4 cụm bằng `KMeans(n_clusters=4, random_state=42)` và lưu ra `data/processed/clusters_pca.csv`.
- [ ] **Phân tích Liên kết Đồ thị — Link Analysis & PageRank (Bài L10–11)**:
  - Lập ma trận tương quan Pearson $30 \times 30$ giữa lợi nhuận ngày (`return_1d`) của 30 mã VN30.
  - Khởi tạo đồ thị vô hướng `G = nx.Graph()`. Thêm cạnh `(u, v, weight=corr)` nếu hai mã $u \neq v$ có hệ số tương quan `corr >= 0.60`.
  - Chạy thuật toán `nx.pagerank(G, weight='weight')` và `nx.degree_centrality(G)` để tìm ra các cổ phiếu có sức lan tỏa lớn nhất rổ VN30.
  - Lưu bảng xếp hạng ra `data/processed/graph_pagerank.csv`.

### Bước 3: Hoàn thiện `notebooks/02_eda_and_graph.ipynb`
- [ ] Vẽ biểu đồ Boxplot & Histogram phân phối lợi nhuận theo Nhóm ngành và theo Quý (chứng minh hiệu ứng Quý 1 Tết Nguyên Đán như bài báo PLOS ONE 2025).
- [ ] Vẽ biểu đồ Scatter 2D các cụm cổ phiếu trên mặt phẳng `(pca_1, pca_2)`.
- [ ] Vẽ đồ thị mạng lưới liên kết VN30 (kích thước nút tỷ lệ với điểm `PageRank`) và Heatmap tương quan.

---

## 4. Tiêu Chí Nghiệm Thu Bàn Giao Cho Người C & E (Definition of Done)

```bash
python -c "
import pandas as pd
df = pd.read_parquet('data/processed/features_all.parquet')
assert set(df['split'].unique()) == {'train', 'validation', 'test'}
assert df.isna().sum().sum() == 0, 'Still contains NaN values!'
print('OK features_all.parquet:', df.shape)
print('OK clusters_pca.csv:', pd.read_csv('data/processed/clusters_pca.csv').shape)
print('OK graph_pagerank.csv:', pd.read_csv('data/processed/graph_pagerank.csv').shape)
"
```
