# Tài Liệu Kỹ Thuật Phân Hệ 01: Thu Thập Dữ Liệu Đa Nguồn & Web Crawling (`src/ingestion/`)

> **Package**: `src/ingestion/`  
> **Notebook Minh họa**: `notebooks/01_data_crawling.ipynb`  
> **Kiểm thử Tự động**: `tests/test_ingestion.py`  
> **Ánh xạ Học phần IT4930 (`02-ds`)**:
> - **Bài 2 (Lecture 2 — Thu thập dữ liệu & Web Crawling)**: Giao thức HTTP, xoay vòng định danh trình duyệt (`User-Agent`), điều tiết tốc độ tải (`Polite Jitter Delay & Exponential Backoff`), phân tích cây DOM HTML bằng `BeautifulSoup4`, đồng bộ gia tăng (Incremental Watermark Sync).
> - **Bài 8 (Lecture 8 — Quản trị Dữ liệu lớn)**: Kiến trúc lưu trữ kép kết hợp cơ sở dữ liệu nhúng `SQLite` (chống trùng lặp bằng khóa chính) và định dạng cột nén `Apache Parquet`.
> - **Bài 10–11 (Lecture 10–11 — Phân tích Dữ liệu Văn bản)**: Lượng hóa sắc thái cảm xúc tiêu đề tin tức tài chính tiếng Việt bằng **LLM Knowledge Distillation** sang mô hình thống kê nhẹ **`TfidfVectorizer + LogisticRegression`** chia theo **Temporal Split** chống rò rỉ dữ liệu tương lai.

---

## 1. Tổng Quan & Mục Tiêu Thiết Kế

Phân hệ `src/ingestion/` là tầng đầu tiên của đường ống Khoa học Dữ liệu trong dự án **`TradeToiChet`**, tự động thu thập và đồng bộ hóa **3 nguồn dữ liệu thực tế** của thị trường chứng khoán Việt Nam (giai đoạn `2019-01-01` đến `2026-11-20`):

1. **Dữ liệu Giá & Khối lượng Lịch sử (`prices.parquet`)**: Chuỗi thời gian OHLCV theo ngày của **30 mã cổ phiếu rổ VN30** và chỉ số thị trường **VN-Index** (`60,385` bản ghi, `2019-01-02 → 2026-11-20`, `datetime64[ns]`) từ API Entrade/DNSE.
2. **Dữ liệu Tin tức Tài chính & Điểm Cảm xúc (`news_sentiment.parquet`)**: Cào tự động **`28,828` bài báo** doanh nghiệp thực tế từ cổng thông tin **CafeF** kèm giờ đăng `HH:mm` (dời tin `>= 14:45` sau giờ đóng cửa HOSE, cuối tuần và lễ/Tết sang phiên giao dịch kế tiếp gần nhất), chấm điểm cảm xúc bằng mô hình `.joblib` leak-free và tổng hợp theo ngày giao dịch (`18,160` bản ghi ngày–mã, 0 dòng lệch lịch phiên).
3. **Dữ liệu Thị trường & Kinh tế Vĩ mô (`macro.parquet`)**: Kết hợp lợi nhuận VN-Index (reindex theo đủ **`1,968`** phiên giao dịch VN30 + `ffill` lấp 33 ngày thiếu từ API, không `bfill`), độ biến động trượt 20 phiên (`vnindex_volatility_20d` với 19 ngày đầu `NaN` tự nhiên), tỷ giá **`USD/VND` thực tế từ Yahoo Finance (`VND=X`)** và lịch sử **Lãi suất tái cấp vốn của Ngân hàng Nhà nước Việt Nam (SBV)**.

---

## 2. Kiến Trúc Lưu Trữ Kép & Đồng Bộ Gia Tăng (SQLite Cache $\leftrightarrow$ Apache Parquet)

Để không bao giờ phải cào lại dữ liệu từ đầu, tránh quá tải API và triệt tiêu nguy cơ bị chặn IP (IP Ban), phân hệ sử dụng cơ chế **Incremental Watermark Sync** theo mốc ngày:

```text
┌────────────────────────────────────────────────────────────────────────────┐
│                   LUỒNG HOẠT ĐỘNG CỦA SRC/INGESTION/                       │
└─────────────────────────────────────┬──────────────────────────────────────┘
                                      │
                                      ▼
                    ┌───────────────────────────────────┐
                    │ 1. Kiểm tra Watermark trong SQLite│
                    │    (data/tradetoichet.db)         │
                    │  • Giá: [db_min, db_max] 2 đầu    │
                    │  • Tin: dừng khi trùng hoặc < start│
                    └────────┬─────────────────┬────────┘
                             │                 │
            [Đã phủ đủ ngày] │                 │[Thiếu đoạn start/end]
              (Cache Hit)    │                 │ (Incremental Fetch)
                             │                 ▼
                             │   ┌──────────────────────────────────────────┐
                             │   │ 2. Anti-Ban HTTP Client (http_client.py) │
                             │   │    • Xoay ngẫu nhiên 6 User-Agents       │
                             │   │    • Nghỉ Jitter Delay (0.25s - 0.65s)   │
                             │   │    • Tự động Retry Exponential Backoff   │
                             │   └─────────────────────┬────────────────────┘
                             │                         │
                             │         ┌───────────────┴───────────────┐
                             │         ▼                               ▼
                             │  ┌─────────────────────┐ ┌───────────────────────────┐
                             │  │ API Entrade / DNSE  │ │ HTML CafeF News Ajax      │
                             │  │ (OHLCV 30 mã VN30   │ │ BeautifulSoup4 DOM Parser │
                             │  │  & chỉ số VNINDEX)  │ │ + TF-IDF Sentiment .joblib│
                             │  └──────────┬──────────┘ └──────────────┬────────────┘
                             │             │                           │
                             │             └─────────────┬─────────────┘
                             │                           ▼
                             │             ┌───────────────────────────┐
                             │             │ 3. Ghi bền vững vào SQLite│
                             │             │ (INSERT OR REPLACE/IGNORE)│
                             │             └─────────────┬─────────────┘
                             │                           │
                             └─────────────┬─────────────┘
                                           ▼
                    ┌──────────────────────────────────────────────┐
                    │ 4. Lọc [start_date, end_date] & Xuất Parquet │
                    │    ├── data/raw/prices.parquet               │
                    │    ├── data/raw/news_sentiment.parquet       │
                    │    └── data/raw/macro.parquet                │
                    └──────────────────────────────────────────────┘
```

---

## 3. Cấu Trúc Mã Nguồn & Đặc Tả Từng File Trong `src/ingestion/`

Toàn bộ mã nguồn được tổ chức thành **8 file gọn nhẹ**, phân tách trách nhiệm rõ ràng:

| Tên File | Số dòng | Chức năng & Các hàm chính |
|---|---|---|
| [`src/ingestion/__init__.py`](../../src/ingestion/__init__.py) | 38 dòng | Giao diện public của package, cung cấp 2 entrypoint chuẩn hợp đồng: `run_ingestion()` và `run_news_crawler()`. |
| [`src/ingestion/db.py`](../../src/ingestion/db.py) | 117 dòng | Quản lý `data/tradetoichet.db` gồm 4 bảng (`prices`, `raw_news` có `pub_time`, `macro`, `sentiment_labels`):<br>- `get_ticker_price_bounds()`: Trả về `(min_date, max_date)` hiện có để kéo incremental 2 đầu.<br>- `upsert_prices()`, `insert_news_records()`: Ghi theo lô an toàn, chống trùng lặp bằng khóa chính. |
| [`src/ingestion/http_client.py`](../../src/ingestion/http_client.py) | 71 dòng | Tầng giao tiếp mạng chống chặn IP: `build_headers()` (xoay 6 User-Agents), `polite_sleep()` và `fetch_url()` (retry exponential backoff `2^attempt` giây). |
| [`src/ingestion/price_fetcher.py`](../../src/ingestion/price_fetcher.py) | 116 dòng | Thu thập OHLCV từ Entrade/DNSE (`fetch_single_ticker_ohlcv()`, `end_ts` `23:59:59 UTC`), chuẩn hóa `Asia/Ho_Chi_Minh` + `datetime64[ns]`. `sync_all_prices()` kéo incremental 2 đầu `[start_date, db_min]` và `[db_max, end_date]`. |
| [`src/ingestion/macro_builder.py`](../../src/ingestion/macro_builder.py) | 124 dòng | Xây dựng bảng vĩ mô `macro.parquet`:<br>- Reindex `VNINDEX` theo đủ `1,968` phiên VN30 + `ffill()` (lấp 33 ngày thiếu, không `bfill()`).<br>- `_fetch_yahoo_usdvnd()`, `_estimate_usd_vnd_rate()`: Tải tỷ giá USD/VND thật từ Yahoo Finance (`VND=X`).<br>- `_estimate_sbv_policy_rate()`: Ánh xạ lịch sử lãi suất tái cấp vốn NHNN theo Quyết định chính thức. |
| [`src/ingestion/sentiment.py`](../../src/ingestion/sentiment.py) | 141 dòng | Chấm điểm cảm xúc tiếng Việt không dùng từ điển cứng:<br>- `train_and_save_sentiment_model()`: Đọc `sentiment_labels` (SQLite hoặc `sentiment_labels.parquet`), chia **Temporal Split** (`<= 2023-12-31` train, `>= 2024-01-01` eval), lưu `sentiment_tfidf.joblib`.<br>- `score_headlines_batch()`, `rescore_all_news_in_db()`: Suy luận `< 0.1 ms/câu` qua `@lru_cache`. |
| [`src/ingestion/news_crawler.py`](../../src/ingestion/news_crawler.py) | 153 dòng | Trình cào CafeF bằng `BeautifulSoup4` (ưu tiên `get_text()`, bỏ tiêu đề `< 15` ký tự, lưu `pub_time` `HH:mm`), dời tin `>= 14:45` + cuối tuần + lễ/Tết sang phiên giao dịch kế tiếp theo `prices.parquet` và xuất `news_sentiment.parquet`. |
| [`src/ingestion/cli.py`](../../src/ingestion/cli.py) | 53 dòng | Giao diện dòng lệnh hỗ trợ `--skip-prices`, `--skip-news`, `--retrain-sentiment`, `--start-date`, `--end-date`, `--pages`, `--tickers`. |

---

## 4. Quy Trình LLM Knowledge Distillation & Mô Hình Sentiment (`src/ingestion/sentiment.py`)

Thay vì viết tay từ điển từ khóa cứng hay gọi LLM nặng lúc runtime, phân hệ áp dụng **LLM Knowledge Distillation** sang mô hình nhẹ **`TfidfVectorizer + LogisticRegression`** tuân thủ nghiêm ngặt **Zero Look-Ahead Bias**:

1. **Kho Nhãn Vàng (`data/raw/sentiment_labels.parquet` & SQLite)**:
   - Tổng cộng **`4,917` tiêu đề độc nhất** được gán nhãn ngữ cảnh tài chính `{-1: Tiêu cực, 0: Trung lập, +1: Tích cực}` qua các batch AI Subagents (`Gemini Flash Lite`).
   - Giai đoạn `2019–2023` được lấy mẫu phân tầng đều **`~400 bài/năm`** phủ đủ cả `30/30` mã VN30 (`2,022` mẫu huấn luyện).
2. **Huấn luyện & Đánh giá Out-of-Time (Temporal Split — 0% Leak cho cả Val 2024 & Test 2025–2026)**:
   - Pipeline: `TfidfVectorizer(ngram_range=(1, 3), sublinear_tf=True, min_df=2, max_features=30000)` + `LogisticRegression(C=5.0, class_weight="balanced", random_state=42)`.
   - **Tập Train (`first_date <= 2023-12-31`)**: `2,022` tiêu đề (`2019–2023`). Model lưu ra `data/models/sentiment_tfidf.joblib` **chỉ fit trên tập Train này** (0% rò rỉ vào tập Validation 2024 lẫn Test 2025–2026).
   - **Tập Out-of-Time Eval (`first_date >= 2024-01-01`)**: `2,895` tiêu đề (`2024–2026`):
     - **Accuracy**: **`83.90%`** | **Macro-F1**: **`0.7305`** | **Weighted-F1**: **`0.8443`**
     - Class `-1` F1: `0.5050` (`support=125`), Class `0` F1: `0.8883` (`support=1,886`), Class `+1` F1: `0.7983` (`support=884`).
3. **Công thức Suy luận Điểm Liên tục**:
   $$\text{Sentiment Score}(h) = P(y = +1 \mid h) - P(y = -1 \mid h) \in [-1.0, +1.0]$$

---

## 5. Trích Dẫn Nguồn Lãi Suất Điều Hành SBV & Lưu Ý Học Thuật

### 5.1. Lịch sử Lãi suất Tái cấp vốn NHNN Việt Nam (`sbv_policy_rate`)
Vì cổng thông tin Ngân hàng Nhà nước Việt Nam (`sbv.gov.vn`) chỉ công bố Quyết định dưới dạng văn bản pháp quy (không có public JSON API lịch sử theo ngày), cột `sbv_policy_rate` ánh xạ chính xác hàm bậc thang theo từng Quyết định điều hành chính thức của SBV giai đoạn `2019–2026`:

| Ngày hiệu lực | Mức lãi suất tái cấp vốn (%/năm) | Nguồn Quyết định SBV |
|---|---:|---|
| Trước `2019-09-16` | `6.25%` | QĐ 1424/QĐ-NHNN (2017) |
| `2019-09-16` | `6.00%` | QĐ 1870/QĐ-NHNN |
| `2020-03-17` | `5.00%` | QĐ 418/QĐ-NHNN |
| `2020-05-13` | `4.50%` | QĐ 918/QĐ-NHNN |
| `2020-10-01` | `4.00%` | QĐ 1728/QĐ-NHNN |
| `2022-09-23` | `5.00%` | QĐ 1606/QĐ-NHNN |
| `2022-10-25` | `6.00%` | QĐ 1809/QĐ-NHNN |
| `2023-04-03` | `5.50%` | QĐ 574/QĐ-NHNN |
| `2023-05-25` | `5.00%` | QĐ 950/QĐ-NHNN |
| `2023-06-19` → `2026-11-20` | `4.50%` | QĐ 1123/QĐ-NHNN (giữ ổn định xuyên suốt `2024–2026`) |

### 5.2. Lưu ý Học thuật (Limitations)
- **Survivorship Bias (Thiên lệch kẻ sống sót)**: Danh mục `VN30_TICKERS` trong `src/config.py` sử dụng rổ 30 mã VN30 cố định tại thời điểm nghiên cứu để truy xuất ngược về `2019` (tương đồng với phương pháp của các nghiên cứu SOTA `Nature 2024` và `PLOS ONE 2025`), chưa mô phỏng sự thay đổi thành phần rổ VN30 qua từng kỳ tái cơ cấu lịch sử.

---

## 6. Thống Kê Bộ Dữ Liệu Thật Đã Thu Thập & Lưu Trữ

| Tập tin Lưu trữ | Định dạng | Dung lượng | Số dòng $\times$ Số cột | Khung ngày | Mô tả Nội dung |
|---|---|---|---|---|---|
| `data/raw/prices.parquet` | Apache Parquet | `1,032.3 KB` | `60,385 rows x 8 cols` | `2019-01-02 → 2026-11-20` | Dữ liệu OHLCV + nhóm ngành (`sector`) của 30 mã VN30 và `VNINDEX` (`datetime64[ns]`). |
| `data/raw/news_sentiment.parquet` | Apache Parquet | `785.6 KB` | `18,160 rows x 5 cols` | `2019-01-02 → 2026-11-20` | Số lượng tin (`news_count`), điểm cảm xúc `[-1, 1]` và tiêu đề mẫu (đã dời `>= 14:45` & lễ/Tết). |
| `data/raw/macro.parquet` | Apache Parquet | `73.9 KB` | `1,968 rows x 6 cols` | `2019-01-02 → 2026-11-20` | Điểm số VN-Index (reindex đủ 1,968 phiên + `ffill`), lợi nhuận 1d, vol 20d, USD/VND, SBV. |
| `data/raw/sentiment_labels.parquet` | Apache Parquet | `~150 KB` | `4,917 rows x 3 cols` | `2019-01-02 → 2026-11-20` | Kho nhãn vàng LLM (`headline`, `llm_label`, `first_date`) để tái lập model mà không cần commit SQLite. |
| `data/models/sentiment_tfidf.joblib` | Joblib | `~450 KB` | Pipeline TF-IDF + LR | Fit `<= 2023-12-31` | Mô hình cảm xúc tiếng Việt leak-free cho cả Val (2024) và Test (2025–2026). |
| `data/tradetoichet.db` *(local cache, `.gitignore`)* | SQLite 3 | `~17 MB` | 4 bảng | Local only | Cache cục bộ tránh cào lại, không push lên Git để giữ repo nhẹ. |

---

## 7. Hướng Dẫn Chạy & Kiểm Thử Module Ingestion

```bash
# 1. Chạy toàn bộ pipeline thu thập dữ liệu (tự động incremental sync từ SQLite cache)
uv run python -m src.ingestion.cli

# 2. Chỉ chạy phần kéo giá OHLCV & Vĩ mô (bỏ qua cào tin tức)
uv run python -m src.ingestion.cli --skip-news

# 3. Chỉ chạy phần cào tin tức CafeF (tùy chỉnh số trang tối đa mỗi mã)
uv run python -m src.ingestion.cli --skip-prices --pages 60

# 4. Chạy bộ kiểm thử tự động (Unit tests + Data Contract tests)
uv run pytest tests/test_ingestion.py -v
```
