# AGENTS.md — System Map, Routing Table & Engineering Rules (`TradeToiChet`)

> **BẮT BUỘC ĐỌC ĐẦU TIÊN**: Tài liệu này là bản đồ trung tâm cho mọi thành viên và AI Coding Agents làm việc trên repository `TradeToiChet`. Mọi agent khi nhận task **phải tra cứu Routing Table ở Mục 1** để đọc đúng tài liệu quy chuẩn trước khi viết code, và **phải bàn giao đủ 4 thành phần (Code + Test + Notebook + Module Doc)** theo Mục 4.

---

## 1. Bảng Định Tuyến Toàn Dự Án (Project Routing Table)

Khi thực hiện bất kỳ tác vụ nào dưới đây, Agent **bắt buộc phải đọc** cột `Must Read` và chỉ sửa đổi các file trong cột `Target Scope`:

| Task / Phân hệ | Sub-package (`Target Scope`) | Must Read (Đọc trước khi code) | Output Artifacts (Đầu ra bắt buộc) |
|---|---|---|---|
| **Tổng quan & Kiến trúc hệ thống** | `docs/architecture/` | `README.md`, `docs/architecture/PLAN.md`, `docs/architecture/STRUCTURE.md`, `docs/architecture/FLOW.md` | Cập nhật tài liệu kiến trúc & sơ đồ luồng |
| **1. Data Ingestion & Web Crawling** *(Phân hệ 01)* | `src/ingestion/`<br>`tests/test_ingestion.py`<br>`notebooks/01_data_crawling.ipynb`<br>`docs/modules/01-ingestion.md` | `docs/checklists/CHECKLIST-A.md`<br>`docs/architecture/API_CONTRACTS.md` (Mục 1, 2, 6)<br>`src/config.py` | - `data/tradetoichet.db`<br>- `data/raw/prices.parquet`<br>- `data/raw/news_sentiment.parquet`<br>- `data/raw/macro.parquet` |
| **2. Data Processing, EDA, PCA & Graph PageRank** *(Phân hệ 02)* | `src/processing/`<br>`tests/test_processing.py`<br>`notebooks/02_eda_and_graph.ipynb`<br>`docs/modules/02-processing.md` | `docs/checklists/CHECKLIST-B.md`<br>`docs/architecture/API_CONTRACTS.md` (Mục 2, 3, 6)<br>`docs/modules/01-ingestion.md`<br>`src/config.py` | - `data/processed/features_all.parquet`<br>- `data/processed/clusters_pca.csv`<br>- `data/processed/graph_pagerank.csv` |
| **3. ML Modeling & SOTA Paper Benchmark** *(Phân hệ 03)* | `src/modeling/`<br>`tests/test_modeling.py`<br>`notebooks/03_modeling_sota.ipynb`<br>`docs/modules/03-modeling.md` | `docs/checklists/CHECKLIST-C.md`<br>`docs/architecture/API_CONTRACTS.md` (Mục 3, 4, 6)<br>`docs/architecture/SOTA_PAPERS.md`<br>`docs/papers/*.txt` | - `data/processed/predictions.parquet`<br>- `data/processed/sota_benchmark.csv`<br>- `data/processed/feature_importance.csv` |
| **4. Quantitative Backtesting & T+2.5 Simulation** *(Phân hệ 04)* | `src/backtesting/`<br>`tests/test_backtesting.py`<br>`notebooks/04_backtest_sim.ipynb`<br>`docs/modules/04-backtesting.md` | `docs/checklists/CHECKLIST-D.md`<br>`docs/architecture/API_CONTRACTS.md` (Mục 4, 5, 6)<br>`docs/modules/03-modeling.md`<br>`src/config.py` | - `data/processed/threshold_tuning.csv`<br>- `data/processed/backtest_summary.csv`<br>- `data/processed/equity_curve.parquet` |
| **5. Streamlit Dashboard, CLI & Final Report** *(Phân hệ 05)* | `src/dashboard/`<br>`main.py`<br>`tests/test_dashboard.py`<br>`docs/modules/05-dashboard.md` | `docs/checklists/CHECKLIST-E.md`<br>`docs/architecture/API_CONTRACTS.md` (Toàn bộ)<br>`docs/architecture/FLOW.md` (Mục 3, 4)<br>`docs/modules/01..04-*.md` | - Web App `src/dashboard/app.py`<br>- Pipeline `main.py`<br>- Báo cáo tổng hợp trong `docs/` |

---

## 2. Bản Đồ Thư Mục Tài Liệu (`Where to Read & Write Docs`)

```text
docs/
├── architecture/                 # [READ-ONLY KHI CODE MODULE] Quy chuẩn toàn hệ thống
│   ├── PLAN.md                   # Kế hoạch tổng thể & ánh xạ bài giảng L1-L12 môn IT4930 (02-ds)
│   ├── STRUCTURE.md              # Cấu trúc cây thư mục & phân quyền file
│   ├── FLOW.md                   # Sơ đồ luồng dữ liệu 5 tầng & thiết kế 5 Tab Streamlit
│   ├── API_CONTRACTS.md          # HỢP ĐỒNG CỨNG: Tên cột, kiểu dữ liệu (.parquet/.csv) & chữ ký hàm
│   └── SOTA_PAPERS.md            # Tóm tắt học thuật & bảng metric của 2 bài báo Nature 2024 & PLOS ONE 2025
│
├── checklists/                   # [READ-ONLY] Đặc tả yêu cầu chi tiết từng phân hệ
│   ├── CHECKLIST.md              # Bảng điều phối tiến độ tổng
│   └── CHECKLIST-A.md .. E.md    # Hướng dẫn từng bước cho 5 phân hệ (A -> E)
│
├── papers/                       # [READ-ONLY] Toàn văn PDF & Text của 2 bài báo SOTA chứng khoán VN
│   ├── nature-2024-vn30-ml-prediction.pdf / .txt
│   └── plosone-2025-vn-stock-ml.pdf / .txt
│
└── modules/                      # [WRITE REQUIRED] Tài liệu kỹ thuật chi tiết sau khi code xong mỗi phân hệ
    ├── 01-ingestion.md           # Tài liệu kỹ thuật của src/ingestion/
    ├── 02-processing.md          # Tài liệu kỹ thuật của src/processing/
    ├── 03-modeling.md            # Tài liệu kỹ thuật của src/modeling/
    ├── 04-backtesting.md         # Tài liệu kỹ thuật của src/backtesting/
    └── 05-dashboard.md           # Tài liệu kỹ thuật của src/dashboard/ & main.py
```

---

## 3. Quy Tắc Viết Code Bắt Buộc (Strict Coding Standards)

1. **Chia Sub-Package & File Nhỏ Gọn (< 130 dòng/file)**:
   - Mỗi phân hệ nằm gọn trong sub-package riêng (`src/ingestion/`, `src/processing/`, `src/modeling/`, `src/backtesting/`, `src/dashboard/`).
   - Mỗi file `.py` chỉ đảm nhận 1 trách nhiệm rõ ràng (Single Responsibility), độ dài từ **40 đến tối đa 130 dòng**. Không tạo các file "God object" hàng trăm dòng.
2. **Quy Tắc Ngôn Ngữ & Cấm Ghi Tên Cá Nhân Vào Code**:
   - **Tên hàm, tên biến, tên file, CLI log messages (`print`/`logging`)**: Tiếng Anh ngắn gọn, rõ ràng (`snake_case`).
   - **Comment giải thích (`# ...`) và Docstring (`"""..."""`)**: Viết bằng **tiếng Việt không dấu**, ngắn gọn, đi thẳng vào bản chất kỹ thuật/nghiệp vụ.
   - **TUYỆT ĐỐI CẤM** đưa các chữ placeholder phân công như `Member A/B/C/D/E`, `Ong A`, `Nguoi B` vào trong code `src/`, `tests/` hoặc `notebooks/`. Chỉ sử dụng tên phân hệ kỹ thuật: `[INGESTION]`, `[PROCESSING]`, `[MODELING]`, `[BACKTESTING]`, `[DASHBOARD]`.
3. **Tuân Thủ Tuyệt Đối Hợp Đồng Dữ Liệu (`docs/architecture/API_CONTRACTS.md`)**:
   - Không tự ý đổi tên file, tên cột hay kiểu dữ liệu (`dtype`) của các file `.parquet` và `.csv` trong `data/raw/` và `data/processed/`.
4. **Chống Rò Rỉ Dữ Liệu Tương Lai (Zero Look-Ahead Bias)**:
   - Dữ liệu chuỗi thời gian tài chính bắt buộc chia theo mốc ngày (**Temporal Split**: `train <= 2023-12-31`, `validation == 2024`, `test >= 2025-01-01`).
   - Cấm dùng `shuffle=True` hoặc `bfill()` xuyên qua tương lai. Bộ `Imputer` / `Scaler` / `Vectorizer` chỉ được `.fit()` trên dữ liệu huấn luyện.

---

## 4. Quy Trình Bàn Giao 4 Thành Phần Bắt Buộc Cho Mọi Phân Hệ (Definition of Done)

Bất kỳ Agent hay thành viên nào khi triển khai một phân hệ (`ingestion`, `processing`, `modeling`, `backtesting`, `dashboard`) **chỉ được coi là hoàn thành** khi bàn giao đủ 4 hạng mục sau:

1. **Modular Source Code (`src/<module>/`)**:
   - Các file `.py` nhỏ gọn, có type hints, docstring tiếng Việt không dấu, và có `cli.py` để chạy độc lập bằng `uv run python -m src.<module>.cli`.
2. **Automated Pytest Suite (`tests/test_<module>.py`)**:
   - **Bắt buộc viết Unit Tests** cho các hàm xử lý logic cốt lõi VÀ **Data Contract Tests** kiểm tra các file `.parquet` / `.csv` đầu ra khớp 100% với `docs/architecture/API_CONTRACTS.md`.
   - Chạy `uv run pytest -v` phải **PASS 100%**.
3. **Executed Jupyter Notebook (`notebooks/0X_<name>.ipynb`)**:
   - Notebook minh họa kết quả thực nghiệm và biểu đồ phục vụ báo cáo môn IT4930.
   - Bắt buộc chạy sạch từ trên xuống dưới bằng lệnh:
     `uv run jupyter nbconvert --to notebook --execute --inplace notebooks/0X_<name>.ipynb`
4. **Detailed Technical Documentation (`docs/modules/0X-<module>.md`)**:
   - Viết tài liệu kỹ thuật chi tiết, trình bày sạch đẹp (theo mẫu `docs/modules/01-ingestion.md`), gồm:
     - Ánh xạ với bài giảng môn `02-ds` (L1 $\to$ L12).
     - Sơ đồ kiến trúc & luồng dữ liệu (ASCII Art / Mermaid).
     - Bảng đặc tả từng file & từng hàm trong package.
     - Công thức toán học / thuật toán sử dụng.
     - Thống kê kết quả dữ liệu đầu ra và câu lệnh CLI / Pytest để kiểm tra.
   - Cập nhật đường dẫn tài liệu mới vào `README.md`.

---

## 5. Quy Tắc Git Commit (Atomic Conventional Commits)

- Không gộp cả một phân hệ lớn vào 1 commit duy nhất. Phải chia nhỏ thành các commit nguyên tử theo từng bước:
  1. `feat(<module>): ...` (implement core logic files)
  2. `test(<module>): add pytest unit and schema contract tests`
  3. `docs(<module>): add executed notebook and technical module documentation`
- Luôn chạy kiểm tra chất lượng code & test trước và sau mỗi lần sửa code / commit:
  - `ruff check src/ tests/` (0 lỗi lint/import/exception)
  - `uvx ty check --python .venv src/ tests/` (hoặc `ty check` với môi trường `.venv` để đảm bảo 0 lỗi type/import)
  - `uv run pytest -v` (PASS 100%)
  - `git status` (working tree sạch sẽ)
