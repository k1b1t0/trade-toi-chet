# Tài Liệu Kỹ Thuật Phân Hệ 01: Thu Thập Dữ Liệu Đa Nguồn & Web Crawling (`src/ingestion/`)

> **Package**: `src/ingestion/`  
> **Notebook Minh họa**: `notebooks/01_data_crawling.ipynb`  
> **Kiểm thử Tự động**: `tests/test_ingestion.py`  
> **Ánh xạ Học phần IT4930 (`02-ds`)**:
> - **Bài 2 (Lecture 2 — Thu thập dữ liệu & Web Crawling)**: Giao thức HTTP, kỹ thuật xoay vòng định danh trình duyệt (`User-Agent`), điều tiết tốc độ tải (`Polite Jitter Delay & Exponential Backoff`), phân tích cây DOM HTML bằng `BeautifulSoup4`.
> - **Bài 8 (Lecture 8 — Quản trị Dữ liệu lớn)**: Tối ưu hóa lưu trữ bằng cơ sở dữ liệu nhúng `SQLite` kết hợp định dạng cột nén `Apache Parquet`.
> - **Bài 10–11 (Lecture 10–11 — Phân tích Dữ liệu Văn bản)**: Lượng hóa sắc thái cảm xúc tiêu đề tin tức tài chính tiếng Việt bằng phương pháp từ điển chuyên ngành (Domain-Specific Sentiment Lexicon).

---

## 1. Tổng Quan & Mục Tiêu Thiết Kế

Phân hệ `src/ingestion/` là tầng đầu tiên của đường ống Khoa học Dữ liệu trong dự án **`TradeToiChet`**. Thay vì sử dụng một tập tin CSV tĩnh có sẵn, phân hệ này tự động thu thập và đồng bộ hóa **3 nguồn dữ liệu thực tế** của thị trường chứng khoán Việt Nam (giai đoạn `2019-01-01` đến `2026-03-01`):

1. **Dữ liệu Giá & Khối lượng Lịch sử (`prices.parquet`)**: Chuỗi thời gian OHLCV theo ngày của **30 mã cổ phiếu rổ VN30** và chỉ số thị trường **VN-Index** (`54,681` bản ghi).
2. **Dữ liệu Tin tức Tài chính & Điểm Cảm xúc (`news_sentiment.parquet`)**: Cào tự động `2,694` bài báo chuyên mục doanh nghiệp từ cổng thông tin **CafeF**, bóc tách thời gian đăng, tiêu đề và chấm điểm cảm xúc tiếng Việt rồi tổng hợp theo từng ngày giao dịch (`1,847` bản ghi ngày-mã).
3. **Dữ liệu Thị trường & Kinh tế Vĩ mô (`macro.parquet`)**: Kết hợp tỷ suất sinh lời VN-Index, độ biến động trượt 20 phiên (`vnindex_volatility_20d`), tỷ giá hối đoái `USD/VND` và lịch sử **Lãi suất tái cấp vốn của Ngân hàng Nhà nước Việt Nam (SBV)** (`1,751` ngày giao dịch).

---

## 2. Kiến Trúc Lưu Trữ Kép (SQLite Cache $\leftrightarrow$ Apache Parquet)

Để giải quyết bài toán **không bao giờ phải cào lại dữ liệu từ đầu** và **triệt tiêu nguy cơ bị máy chủ chặn IP (IP Ban)** khi các thành viên chạy thử nghiệm nhiều lần, phân hệ được thiết kế theo kiến trúc lưu trữ kép:

```text
┌────────────────────────────────────────────────────────────────────────────┐
│                   LUỒNG HOẠT ĐỘNG CỦA SRC/INGESTION/                       │
└─────────────────────────────────────┬──────────────────────────────────────┘
                                      │
                                      ▼
                    ┌───────────────────────────────────┐
                    │ 1. Kiểm tra SQLite Cache          │
                    │    (data/tradetoichet.db)         │
                    └────────┬─────────────────┬────────┘
                             │                 │
              [Đã đủ bản ghi]│                 │[Chưa có / Thiếu]
               (Cache Hit)   │                 │ (Cache Miss)
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
                             │  │  & chỉ số VNINDEX)  │ │ + Từ điển Cảm xúc TV      │
                             │  └──────────┬──────────┘ └──────────────┬────────────┘
                             │             │                           │
                             │             └─────────────┬─────────────┘
                             │                           ▼
                             │             ┌───────────────────────────┐
                             │             │ 3. Ghi bền vững vào SQLite│
                             │             │    (INSERT OR REPLACE)    │
                             │             └─────────────┬─────────────┘
                             │                           │
                             └─────────────┬─────────────┘
                                           ▼
                    ┌──────────────────────────────────────────────┐
                    │ 4. Truy vấn chuẩn hóa & Xuất Apache Parquet  │
                    │    ├── data/raw/prices.parquet               │
                    │    ├── data/raw/news_sentiment.parquet       │
                    │    └── data/raw/macro.parquet                │
                    └──────────────────────────────────────────────┘
```

---

## 3. Cấu Trúc Mã Nguồn & Đặc Tả Từng File Trong `src/ingestion/`

Toàn bộ mã nguồn được chia thành **7 file nhỏ gọn** (mỗi file chỉ từ 30 đến 129 dòng), tuân thủ nghiêm ngặt nguyên tắc đơn nhiệm (Single Responsibility Principle):

| Tên File | Số dòng | Chức năng & Các hàm chính |
|---|---|---|
| [`src/ingestion/__init__.py`](../../src/ingestion/__init__.py) | 29 dòng | Giao diện public của package, cung cấp 2 hàm entrypoint chuẩn hợp đồng: `run_ingestion()` và `run_news_crawler()`. |
| [`src/ingestion/db.py`](../../src/ingestion/db.py) | 107 dòng | Quản lý cơ sở dữ liệu `data/tradetoichet.db`:<br>- `init_db()`: Khởi tạo 3 bảng `prices`, `raw_news`, `macro` với khóa chính chống trùng lặp.<br>- `has_ticker_prices()`, `has_ticker_news()`: Kiểm tra nhanh một mã cổ phiếu đã có đủ dữ liệu trong DB chưa.<br>- `upsert_prices()`, `insert_news_records()`: Ghi dữ liệu theo lô (`executemany`) an toàn. |
| [`src/ingestion/http_client.py`](../../src/ingestion/http_client.py) | 66 dòng | Tầng giao tiếp mạng chống chặn IP:<br>- `build_headers()`: Sinh HTTP Headers giả lập trình duyệt thực tế với `User-Agent` chọn ngẫu nhiên từ 6 cấu hình.<br>- `polite_sleep()`: Nghỉ ngẫu nhiên giữa các lần tải.<br>- `fetch_url()`: Tải JSON hoặc HTML với cơ chế thử lại lũy thừa (`2^attempt` giây) nếu gặp lỗi mạng hoặc HTTP 429/503. |
| [`src/ingestion/price_fetcher.py`](../../src/ingestion/price_fetcher.py) | 94 dòng | Thu thập dữ liệu giá:<br>- `fetch_single_ticker_ohlcv()`: Gọi API nến ngày của từng mã, chuyển đổi Unix Timestamp sang ngày giao dịch theo múi giờ Việt Nam (`Asia/Ho_Chi_Minh`).<br>- `sync_all_prices()`: Đồng bộ 30 mã VN30 + `VNINDEX` vào SQLite và xuất file `data/raw/prices.parquet`. |
| [`src/ingestion/macro_builder.py`](../../src/ingestion/macro_builder.py) | 92 dòng | Xây dựng dữ liệu vĩ mô:<br>- `_estimate_sbv_policy_rate()`: Ánh xạ lịch sử lãi suất tái cấp vốn của Ngân hàng Nhà nước Việt Nam qua các đợt điều chỉnh từ 2019 đến 2026.<br>- `build_macro_dataset()`: Tính lợi nhuận và độ biến động 20 phiên của VN-Index, ghép tỷ giá và lãi suất rồi xuất `data/raw/macro.parquet`. |
| [`src/ingestion/sentiment.py`](../../src/ingestion/sentiment.py) | 43 dòng | Chấm điểm cảm xúc tiếng Việt:<br>- Khai báo bộ từ khóa tích cực (`POSITIVE_KEYWORDS`) và tiêu cực (`NEGATIVE_KEYWORDS`) đặc thù của báo chí chứng khoán Việt Nam.<br>- `score_vietnamese_headline()`: Trả về điểm cảm xúc chuẩn hóa trong đoạn `[-1.0, 1.0]`. |
| [`src/ingestion/news_crawler.py`](../../src/ingestion/news_crawler.py) | 129 dòng | Trình cào dữ liệu Web (Web Crawler):<br>- `parse_cafef_news_html()`: Dùng `BeautifulSoup4` duyệt các thẻ `<li>`, lấy thời gian từ `<span class="timeTitle">` và tiêu đề từ `<a class="docnhanhTitle">`.<br>- `crawl_ticker_news()`, `sync_all_news()`: Cào tin theo từng mã, tự động quy đổi tin đăng cuối tuần (Thứ 7, Chủ nhật) về ngày Thứ 2 kế tiếp để khớp lịch giao dịch, rồi xuất `data/raw/news_sentiment.parquet`. |
| [`src/ingestion/cli.py`](../../src/ingestion/cli.py) | 31 dòng | Giao diện dòng lệnh cho phép chạy toàn bộ hoặc từng phần của module Ingestion. |

---

## 4. Mô Hình Hybrid NLP Chấm Điểm Cảm Xúc Tiếng Việt (`src/ingestion/sentiment.py`)

Thay vì chỉ dùng từ điển cứng hoặc dùng các mô hình Deep Learning hàng trăm MB cần GPU, phân hệ sử dụng kiến trúc **Hybrid NLP (Từ điển chuyên ngành + Mô hình Học máy `TfidfVectorizer(ngram_range=(1, 2))` & `LogisticRegression` của `scikit-learn`)**:

1. **Thành phần 1 — Điểm từ điển chuyên ngành ($\text{Score}_{\text{lex}}$)**:
   $$\text{Score}_{\text{lex}}(h) = \frac{N_{\text{pos}} - N_{\text{neg}}}{N_{\text{pos}} + N_{\text{neg}} + 0.5}$$
2. **Thành phần 2 — Xác suất mô hình Học máy TF-IDF + Logistic Regression ($\text{Score}_{\text{ML}}$)**:
   - Vector hóa tiêu đề theo cụm 1–2 âm tiết (`ngram_range=(1, 2)`) và dự báo phân phối xác suất qua `LogisticRegression.predict_proba()`:
   $$\text{Score}_{\text{ML}}(h) = P(y = +1 \mid h) - P(y = -1 \mid h)$$
3. **Điểm cảm xúc tổng hợp (Blended Ensemble Score)**:
   $$\text{Sentiment Score}(h) = \text{clip}\left( 0.65 \times \text{Score}_{\text{lex}}(h) + 0.35 \times \text{Score}_{\text{ML}}(h), \; -1.0, \; +1.0 \right)$$

---

## 5. Thống Kê Bộ Dữ Liệu Thật Đã Thu Thập & Lưu Trữ

| Tập tin Lưu trữ | Định dạng | Dung lượng | Số dòng $\times$ Số cột | Khóa chính | Mô tả Nội dung |
|---|---|---|---|---|---|
| `data/tradetoichet.db` | SQLite 3 | `5.9 MB` | 3 bảng (`prices`, `raw_news`, `macro`) | Khóa riêng từng bảng | Kho lưu trữ gốc chứa `54,681` dòng giá và `2,694` bài báo CafeF nguyên bản. |
| `data/raw/prices.parquet` | Apache Parquet | `951 KB` | `54,681 rows x 8 cols` | `(date, ticker)` | Dữ liệu OHLCV + nhóm ngành (`sector`) của 30 mã VN30 và `VNINDEX`. |
| `data/raw/news_sentiment.parquet` | Apache Parquet | `85 KB` | `1,847 rows x 5 cols` | `(date, ticker)` | Số lượng tin trong ngày (`news_count`), điểm cảm xúc `[-1, 1]` và tiêu đề mẫu. |
| `data/raw/macro.parquet` | Apache Parquet | `72 KB` | `1,751 rows x 6 cols` | `(date)` | Điểm số VN-Index, lợi nhuận 1 ngày, biến động 20 phiên, tỷ giá USD/VND, lãi suất SBV. |

---

## 6. Hướng Dẫn Chạy & Kiểm Thử Module Ingestion

```bash
# 1. Chạy toàn bộ pipeline thu thập dữ liệu (sẽ tự động dùng SQLite cache nếu đã tải)
uv run python -m src.ingestion.cli

# 2. Chỉ chạy phần kéo giá OHLCV & Vĩ mô (bỏ qua cào tin tức)
uv run python -m src.ingestion.cli --skip-news

# 3. Chỉ chạy phần cào tin tức CafeF (tùy chỉnh số trang cào mỗi mã)
uv run python -m src.ingestion.cli --skip-prices --pages 3

# 4. Chạy bộ kiểm thử tự động (Unit tests + Data Contract tests)
uv run pytest tests/test_ingestion.py -v
```
