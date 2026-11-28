# CHECKLIST-A.md — Đặc Tả Công Việc Của Người A: Data Ingestion & Web Crawling Engineer

> **Vai trò của bạn**: Chịu trách nhiệm toàn bộ **Tầng 1 (Thu thập Dữ liệu Đa nguồn & Cào Tin tức Web)** của hệ thống.
> - **Bao phủ kiến thức môn `02-ds`**: **Bài L2** (Thu thập dữ liệu & Web Crawling), **Bài L8** (Lưu trữ định dạng cột nén Parquet), và phần dữ liệu văn bản của **Bài L10–11**.
> - **Tại sao phần của bạn cực kỳ quan trọng để đạt 9.5 điểm**: Hội đồng chấm môn Khoa học Dữ liệu đánh giá thấp các nhóm chỉ tải 1 file CSV có sẵn trên Kaggle (chỉ được ~8.0 điểm). Phần cào tin tức chứng khoán tiếng Việt và kéo API đa nguồn của bạn là bằng chứng sống động nhất chứng minh nhóm tự xây dựng Data Pipeline thực tế.

---

## 1. Các File Bạn Sở Hữu (Chỉ mình bạn code vào các file này)

1. `src/ingestion/` — Sub-package (`price_fetcher.py`, `macro_builder.py`, `news_crawler.py`, `sentiment.py`, `db.py`, `http_client.py`, `cli.py`).
2. `tests/test_ingestion.py` — Unit tests & Data Contract tests.
3. `notebooks/01_data_crawling.ipynb` & `docs/modules/01-ingestion.md` — Notebook trình bày trực quan và tài liệu kỹ thuật chi tiết.

---

## 2. Công Nghệ & Thư Viện Sử Dụng

- **Kéo giá chứng khoán Việt Nam**: API JSON công khai của Entrade DNSE (`services.entrade.com.vn/chart-api/v2/ohlcs`) + tỷ giá USD/VND từ Yahoo Finance (`VND=X`).
- **Web Scraping tin tức**: `requests` + `beautifulsoup4` cào tin doanh nghiệp CafeF (kèm `pub_time` `HH:mm`, dời tin `>= 14:45` & lễ/Tết sang phiên kế tiếp).
- **Chấm điểm cảm xúc tiếng Việt**: LLM Knowledge Distillation (`4,917` nhãn lưu trong `data/raw/sentiment_labels.parquet`) → `TfidfVectorizer + LogisticRegression` train leak-free trên `<= 2023-12-31` (`sentiment_tfidf.joblib`).
- **Lưu trữ**: `SQLite` (local cache trong `.gitignore`) + `Apache Parquet` (`datetime64[ns]`).

---

## 3. Lộ Trình Các Bước Thực Hiện Chi Tiết (Step-by-Step Checklist)

### Bước 1: Viết module thu thập dữ liệu giá và vĩ mô tạo `prices.parquet` và `macro.parquet`
- [x] Đọc danh sách 30 mã `VN30_TICKERS`, `START_DATE = "2019-01-01"`, `END_DATE = "2026-11-20"` từ `src/config.py`.
- [x] Tải lịch sử giá OHLCV 30 mã VN30 và `VNINDEX` theo cơ chế incremental 2 đầu (`end_ts` `23:59:59 UTC`).
- [x] Thêm cột `sector` và chuẩn hóa `date` thành `datetime64[ns]` theo đúng [API_CONTRACTS.md](../architecture/API_CONTRACTS.md).
- [x] Lưu `data/raw/prices.parquet` (`60,385` dòng) và dựng `data/raw/macro.parquet` (`1,968` phiên reindex đủ lịch VN30 + `ffill`, tỷ giá Yahoo `VND=X`, lãi suất SBV).

### Bước 2: Viết module cào tin tức tạo `news_sentiment.parquet` (Trọng tâm Bài L2)
- [x] Cào tin tức CafeF (`requests` xoay User-Agent, jitter delay `0.25–0.55s`, retry exponential backoff) kèm `pub_time` (`HH:mm`), ưu tiên `get_text()`.
- [x] Train mô hình cảm xúc leak-free (`<= 2023-12-31`, `2,022` mẫu train → `2,895` mẫu eval đạt `83.90%` Accuracy / `0.8443` Weighted-F1), đóng gói ra `data/models/sentiment_tfidf.joblib` và xuất `data/raw/sentiment_labels.parquet`.
- [x] Dời tin `>= 14:45`, cuối tuần và lễ/Tết sang phiên giao dịch kế tiếp, gom nhóm theo `(date, ticker)` và lưu `data/raw/news_sentiment.parquet` (`18,160` dòng, `0` dòng lệch lịch phiên).

### Bước 3: Hoàn thiện `notebooks/01_data_crawling.ipynb`
- [x] Trình bày sơ đồ kiến trúc Crawler (Request -> HTML DOM -> BeautifulSoup Parser -> Distilled Sentiment Model -> Parquet).
- [x] In bảng các dòng đầu của `prices.parquet`, `news_sentiment.parquet`, `macro.parquet`.
- [x] Trực quan hóa Bar chart số lượng bản ghi theo 30 mã VN30 và biểu đồ phân phối điểm cảm xúc tin tức.

---

## 4. Tiêu Chí Nghiệm Thu Bàn Giao Cho Người B (Definition of Done)

Chạy đoạn kiểm tra sau không báo lỗi là bạn đã hoàn thành 100% nhiệm vụ:

```bash
python -c "
import pandas as pd
for name, cols in [
    ('prices.parquet', ['date','ticker','open','high','low','close','volume','sector']),
    ('news_sentiment.parquet', ['date','ticker','news_count','sentiment_score','sample_headline']),
    ('macro.parquet', ['date','vnindex_close','vnindex_return_1d','vnindex_volatility_20d','usd_vnd_rate','sbv_policy_rate'])
]:
    df = pd.read_parquet(f'data/raw/{name}')
    assert all(c in df.columns for c in cols), f'Missing cols in {name}'
    print(f'OK {name}: {df.shape}')
"
```
