# AGENTS.md — Coding Rules, Sub-package Architecture & Git Conventions (`TradeToiChet`)

> **Dành cho**: Cả 5 thành viên trong nhóm (Ông A, B, C, D, E) và các AI Coding Assistants khi phát triển mã nguồn trong repository `TradeToiChet`.

---

## 1. Kiến Trúc Phân Tách 5 Sub-Packages (1 Thành Viên = 1 Thư Mục Module)

Mỗi thành viên chỉ làm việc trong **đúng sub-package của mình** bên trong `src/`:

| Thành viên | Sub-package sở hữu | Trách nhiệm chính |
|---|---|---|
| **Ông A** | `src/ingestion/` | Kéo giá OHLCV 30 mã VN30 + VN-Index, vĩ mô, cào tin tức CafeF (có SQLite cache & chống ban IP), xuất `data/raw/*.parquet`. |
| **Ông B** | `src/processing/` | Ghép bảng, làm sạch, tính 25+ biến kỹ thuật, chạy PCA/K-Means và đồ thị tương quan PageRank, xuất `data/processed/`. |
| **Ông C** | `src/modeling/` | Chia Temporal Split, huấn luyện Regression, Classification và mô hình SOTA đối sánh 2 bài báo Nature (2024) & PLOS ONE (2025). |
| **Ông D** | `src/backtesting/` | Quét ngưỡng xác suất (Threshold Tuning) và mô phỏng chiến lược giao dịch T+2.5 (phí 0.15%, thuế 0.1%, Stop-loss/Take-profit). |
| **Ông E** | `src/dashboard/` & `main.py` | Giao diện Web App Streamlit 5 Tabs, script điều phối tự động và tổng hợp Báo cáo PDF. |

---

## 2. Quy Tắc Viết Code Bắt Buộc (Strict Coding Standards)

1. **File Code Nhỏ Gọn & Đơn Nhiệm (Small, Focused Files)**:
   - Mỗi file `.py` **chỉ nên dài từ 50 đến tối đa 130 dòng**.
   - Nếu một module có nhiều bước (ví dụ: kết nối DB, tải HTTP, bóc tách HTML, chấm điểm cảm xúc), **bắt buộc phải tách thành các file nhỏ riêng biệt** trong sub-package đó (`db.py`, `http_client.py`, `sentiment.py`, `news_crawler.py`).
2. **Quy Tắc Ngôn Ngữ Trong Code**:
   - **Tên hàm, tên biến, tên file, log messages (`print`/`logging`)**: Tiếng Anh ngắn gọn, chuẩn `snake_case`.
   - **Comment giải thích trong code (`# ...`) và Docstring**: Viết bằng **tiếng Việt không dấu**, ngắn gọn, giải thích rõ ý nghĩa nghiệp vụ/kỹ thuật (ví dụ: `# kiem tra sqlite cache truoc khi goi request de tranh bi ban ip`).
   - **Cấm dùng tên placeholder cá nhân trong Code & Notebook**: Các nhãn `Người A/B/C/D/E`, `Ông A`, `Member A` chỉ dùng trong `docs/checklists/` để phân chia công việc. Trong toàn bộ mã nguồn `src/`, `tests/` và `notebooks/`, tuyệt đối chỉ dùng tên phân hệ kỹ thuật (`ingestion`, `processing`, `modeling`, `backtesting`, `dashboard`).
3. **Chống Rò Rỉ Dữ Liệu Tương Lai (Zero Look-Ahead Bias)**:
   - Tuyệt đối không dùng `shuffle=True` hoặc `bfill()` trên dữ liệu chuỗi thời gian.
   - Chỉ được `.fit()` bộ `Imputer`/`Scaler` trên tập `train`, sau đó `.transform()` trên `validation` và `test`.
4. **Quy Tắc Git Commit (Atomic Conventional Commits)**:
   - Commit từng thay đổi nhỏ, rõ ràng ngay sau khi hoàn thành một thành phần.
   - Message commit viết bằng **tiếng Anh ngắn gọn** theo chuẩn Conventional Commits:
     - `chore: ...` (khởi tạo môi trường, cấu hình)
     - `docs: ...` (cập nhật tài liệu, kiến trúc, báo cáo)
     - `feat(ingestion): ...` (tính năng mới trong package `ingestion`)
     - `feat(processing): ...`, `feat(modeling): ...`, `feat(backtesting): ...`, `feat(dashboard): ...`
     - `fix(...): ...` (sửa lỗi)
