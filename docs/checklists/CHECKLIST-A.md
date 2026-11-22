# CHECKLIST-A.md — Đặc Tả Công Việc Của Người A: Data Ingestion & Web Crawling Engineer

> **Vai trò của bạn**: Chịu trách nhiệm toàn bộ **Tầng 1 (Thu thập Dữ liệu Đa nguồn & Cào Tin tức Web)** của hệ thống.
> - **Bao phủ kiến thức môn `02-ds`**: **Bài L2** (Thu thập dữ liệu & Web Crawling), **Bài L8** (Lưu trữ định dạng cột nén Parquet), và phần dữ liệu văn bản của **Bài L10–11**.
> - **Tại sao phần của bạn cực kỳ quan trọng để đạt 9.5 điểm**: Hội đồng chấm môn Khoa học Dữ liệu đánh giá thấp các nhóm chỉ tải 1 file CSV có sẵn trên Kaggle (chỉ được ~8.0 điểm). Phần cào tin tức chứng khoán tiếng Việt và kéo API đa nguồn của bạn là bằng chứng sống động nhất chứng minh nhóm tự xây dựng Data Pipeline thực tế.

---

## 1. Các File Bạn Sở Hữu (Chỉ mình bạn code vào các file này)

1. `src/ingest.py` — Script kéo giá lịch sử OHLCV của 30 mã VN30, chỉ số VN-Index và dữ liệu vĩ mô.
2. `src/crawler.py` — Web Scraper (`requests` + `BeautifulSoup4`) cào tiêu đề tin tức tài chính và chấm điểm cảm xúc (`sentiment_score`).
3. `notebooks/01_data_crawling.ipynb` — Notebook trình bày trực quan quá trình thu thập dữ liệu, cấu trúc DOM HTML khi cào web và thống kê sơ bộ nguồn dữ liệu để đưa vào Chương 2 của Báo cáo PDF.

---

## 2. Công Nghệ & Thư Viện Sử Dụng

- **Kéo giá chứng khoán Việt Nam**: Thư viện `vnstock` (nguồn TCBS / VCI / SSI) hoặc API JSON công khai của CafeF / Entrade DNSE (rất nhẹ, không cần API key trả phí).
- **Web Scraping tin tức**: `requests` + `beautifulsoup4` (cào các trang danh sách tin tức theo mã cổ phiếu trên CafeF hoặc Vietstock).
- **Chấm điểm cảm xúc tiếng Việt (Siêu nhẹ, chạy CPU tức thì)**: Bộ từ điển từ khóa tài chính tiếng Việt (Vietnamese Financial Sentiment Lexicon: nhóm từ tích cực như *"lãi kỷ lục", "vượt kế hoạch", "tăng trưởng", "cổ tức cao", "mua ròng"* vs nhóm từ tiêu cực như *"thua lỗ", "sụt giảm", "bị phạt", "bán tháo", "nợ xấu"*) kết hợp trọng số TF-IDF đơn giản để tính điểm trong đoạn `[-1.0, 1.0]`.
- **Lưu trữ**: `pandas` + `pyarrow` (`df.to_parquet(..., index=False)`).

---

## 3. Lộ Trình Các Bước Thực Hiện Chi Tiết (Step-by-Step Checklist)

### Bước 1: Viết `src/ingest.py` tạo `prices.parquet` và `macro.parquet`
- [ ] Đọc danh sách 30 mã `VN30_TICKERS`, `START_DATE = "2019-01-01"`, `END_DATE = "2026-03-01"` từ `src/config.py`.
- [ ] Viết vòng lặp tải lịch sử giá theo ngày (`open`, `high`, `low`, `close`, `volume`) cho từng mã trong 30 mã VN30 và chỉ số `VNINDEX`.
- [ ] Thêm cột `sector` (ánh xạ từ dictionary cố định, ví dụ: `VCB, BID, CTG, TCB, MBB, ACB, VPB, HDB, STB, TPB, VIB, SHB, SSB -> "Banking"`, `FPT -> "Technology"`, `HPG -> "Steel"`, `VHM, VIC, VRE, BCM -> "RealEstate"`, `MWG, MSN, VNM, SAB -> "Consumer"`, `GAS, PLX, POW -> "Energy"`, `SSI, BVH -> "Financials"`, `GVR, VJC -> "Industrial"`).
- [ ] Chuẩn hóa kiểu dữ liệu theo đúng [API_CONTRACTS.md](API_CONTRACTS.md):
  - `date` ép về `pd.to_datetime(df['date']).dt.tz_localize(None)`.
  - Sắp xếp theo `['ticker', 'date']`, xóa trùng lặp `drop_duplicates(subset=['date', 'ticker'])`.
- [ ] Lưu bảng giá ra `data/raw/prices.parquet`.
- [ ] Từ dữ liệu `VNINDEX` vừa tải, tính `vnindex_close`, `vnindex_return_1d`, `vnindex_volatility_20d`, ghép thêm cột tỷ giá `usd_vnd_rate` và lãi suất `sbv_policy_rate` (có thể lấy từ bảng mốc lãi suất điều hành SBV theo từng giai đoạn 2019–2026), lưu ra `data/raw/macro.parquet`.

### Bước 2: Viết `src/crawler.py` tạo `news_sentiment.parquet` (Trọng tâm Bài L2)
- [ ] Viết hàm `fetch_stock_news_html(ticker: str, max_pages: int = 5)` dùng `requests.get(url, headers={"User-Agent": "Mozilla/5.0..."})` kèm `time.sleep(0.3)` lịch sự để tải trang tin tức doanh nghiệp theo từng mã VN30.
- [ ] Dùng `BeautifulSoup(html, "html.parser")` bóc tách danh sách các thẻ chứa:
  - Ngày đăng tin (`date`)
  - Tiêu đề bài báo (`headline`)
- [ ] Viết cơ chế **Fallback thông minh**: Lưu bản cache các tin đã cào ra file CSV nhẹ để nếu lúc chấm bài không có mạng Internet thì vẫn đọc được ngay dữ liệu tin tức đã cào.
- [ ] Viết hàm `score_vietnamese_headline(text: str) -> float`:
  - Đếm số từ khóa tích cực ($N_{pos}$) và tiêu cực ($N_{neg}$) trong tiêu đề (đã chuyển về chữ thường).
  - Tính điểm: `score = (N_pos - N_neg) / max(N_pos + N_neg, 1)` $\in [-1.0, 1.0]$.
- [ ] Gom nhóm theo `(date, ticker)`:
  - `news_count`: tổng số tin trong ngày.
  - `sentiment_score`: trung bình điểm cảm xúc trong ngày.
  - `sample_headline`: tiêu đề bài đầu tiên trong ngày.
- [ ] Lưu kết quả ra `data/raw/news_sentiment.parquet`.

### Bước 3: Hoàn thiện `notebooks/01_data_crawling.ipynb`
- [ ] Trình bày sơ đồ kiến trúc Crawler (Request $\to$ HTML DOM $\to$ BeautifulSoup Parser $\to$ Lexicon Scoring $\to$ Parquet).
- [ ] In bảng 10 dòng đầu của `prices.parquet`, `news_sentiment.parquet`, `macro.parquet`.
- [ ] Vẽ 1 biểu đồ Bar chart thống kê số lượng dòng dữ liệu theo từng mã VN30 và phân phối điểm cảm xúc tin tức (Tích cực / Trung lập / Tiêu cực).

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
