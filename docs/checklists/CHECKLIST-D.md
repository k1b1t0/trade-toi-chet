# CHECKLIST-D.md — Đặc Tả Công Việc Của Người D: Quantitative Backtesting & T+2.5 Simulation Engineer

> **Vai trò của bạn**: Chịu trách nhiệm toàn bộ **Tầng 4 (Tinh chỉnh Ngưỡng Quyết định Threshold Tuning & Mô phỏng Chiến lược Giao dịch Thực tế trên Thị trường Chứng khoán Việt Nam)**.
> - **Bao phủ kiến thức môn `02-ds` & `SMA Zoomcamp`**: **Bài L12** (Đánh giá thực nghiệm trên miền ứng dụng thực tế) và **Toàn bộ tinh hoa Module 4 & Module 5 của SMA Zoomcamp** (Threshold Tuning, Phí giao dịch, Quản trị rủi ro Stop-loss/Take-profit, Chọn lọc Top-K và Tái đầu tư lãi kép).
> - **Điểm sáng tạo giúp đồ án ăn điểm tuyệt đối**: Khắc phục hạn chế của các bài báo lý thuyết bằng cách đưa **luật giao dịch thực tế của sàn HOSE Việt Nam** vào mô phỏng: Chu kỳ thanh toán **T+2.5** (giữ tối thiểu 3 phiên), phí môi giới `0.15%/chiều`, thuế bán chứng khoán `0.10%` và biên độ cắt lỗ/chốt lời.

---

## 1. Các File Bạn Sở Hữu (Chỉ mình bạn code vào các file này)

1. `src/backtesting/` — Sub-package (chia file `< 130` dòng, export `run_backtest_simulations` tại `__init__.py`, có `cli.py`) thực hiện quét ngưỡng xác suất và mô phỏng danh mục đầu tư theo thời gian thực trên tập Test.
2. `tests/test_backtesting.py` — Unit tests logic T+2.5 / phí-thuế / SL-TP & Data Contract tests khớp `API_CONTRACTS.md`.
3. `notebooks/04_backtest_sim.ipynb` — Notebook trình bày bài toán đánh đổi giữa `Precision` vs `Số lệnh giao dịch/ngày` vs `CAGR`, biểu đồ đường cong tài sản (Equity Curve) và phân tích sụt giảm vốn (Drawdown) để đưa vào Chương 5 của Báo cáo PDF.
4. `docs/modules/04-backtesting.md` — Tài liệu kỹ thuật chi tiết của phân hệ.

---

## 2. Công Nghệ & Các Công Thức Tài Chính Chuẩn

- **Thư viện**: `pandas`, `numpy`, `plotly.express`, `plotly.graph_objects`.
- **Bộ chỉ số tài chính bắt buộc tính trong `src/backtest.py`**:
  1. **Chi phí giao dịch ròng cho 1 vòng lệnh (Round-trip Cost tại Việt Nam)**:
     $$\text{Total Fee Rate} = \text{Phí mua } (0.15\%) + \text{Phí bán } (0.15\%) + \text{Thuế bán } (0.10\%) = 0.40\%$$
  2. **Tỷ suất sinh lời kép hàng năm (CAGR)**:
     $$\text{CAGR} = \left(\frac{V_{\text{final}}}{V_{\text{initial}}}\right)^{\frac{252}{N_{\text{trading\_days}}}} - 1$$
  3. **Tỷ số Sharpe (Annualized Sharpe Ratio — Lãi suất phi rủi ro VN $R_f = 4.5\%/\text{năm}$)**:
     $$\text{Sharpe} = \frac{\overline{r_d - r_{f,d}}}{\sigma(r_d)} \times \sqrt{252}$$
  4. **Mức sụt giảm vốn tối đa từ đỉnh (Maximum Drawdown — MDD)**:
     $$\text{Drawdown}_t = \frac{\text{NAV}_t - \max_{s \le t} \text{NAV}_s}{\max_{s \le t} \text{NAV}_s}, \quad \text{MDD} = \min_t (\text{Drawdown}_t)$$

---

## 3. Lộ Trình Các Bước Thực Hiện Chi Tiết (Step-by-Step Checklist)

### Bước 1: Viết Hàm Quét Ngưỡng Xác Suất (`Threshold Tuning` trên tập `validation` — 0% Data Leak)
- [ ] Đọc `data/processed/predictions.parquet` và lọc lấy tập **`split == "validation"` (2024)** để quét chọn ngưỡng tối ưu $\tau^*$ (tuyệt đối không tune trên `test`).
- [ ] Với 2 mô hình chính (`proba_rf` và `proba_lgbm`), quét ngưỡng xác suất $\tau \in [0.50, 0.52, 0.54, \dots, 0.70]$:
  - Tại mỗi ngưỡng $\tau$, xác định các lệnh mua khi `proba >= tau` (khớp mua ở **`open_{t+1}`** của phiên kế tiếp).
  - Tính:
    - Tổng số lệnh (`total_trades`) và Số lệnh trung bình mỗi ngày (`avg_trades_per_day`).
    - Độ chuẩn (`precision`: tỷ lệ lệnh đạt lợi nhuận $> +1.5\%$) và Tỷ lệ thắng sau phí (`win_rate`: tỷ lệ lệnh có lợi nhuận ròng sau khi trừ $0.40\%$ phí/thuế $> 0$).
    - Lợi nhuận ròng và chỉ số `CAGR` theo mô phỏng vốn cố định (Fixed Capital Simulation giống Module 4).
- [ ] Lưu bảng kết quả quét ngưỡng ra `data/processed/threshold_tuning.csv` và khóa ngưỡng tối ưu $\tau^*$ để chạy ở Bước 2 trên tập `test`.

### Bước 2: Viết Engine Mô Phỏng Danh Mục Chuẩn T+3 (Xấp xỉ bảo thủ T+2.5) & Export `simulate_strategy()`
- [ ] Thiết lập vốn khởi đầu chuẩn: `initial_capital_vnd = 100_000_000` (100 triệu VNĐ), giới hạn tối đa **10 vị thế mở cùng lúc** (bỏ qua lô 100 & trần/sàn để giữ engine gọn). Đọc `sbv_policy_rate` trực tiếp từ `data/raw/macro.parquet` và giá OHLC từng phiên từ `data/raw/prices.parquet`.
- [ ] Export 1 hàm dùng chung `simulate_strategy(...)` tại `src/backtesting/` để cả CLI và Tab 4 Streamlit slider cùng gọi.
- [ ] Thực hiện mô phỏng so sánh **6 Chiến lược** trên tập **`split == "test"` (`>= 2025-01-01`)** với giá khớp mua tại **`open_{t+1}`**:
  1. **`Savings Benchmark (SBV Policy Rate)`**: Lãi kép theo từng phiên từ `sbv_policy_rate` trong `macro.parquet` ($r_{f,\text{daily}} = (1 + r_{\text{annual}})^{1/252} - 1$), Drawdown = `0%`.
  2. **`Buy & Hold VN-Index`**: Mua và nắm giữ chỉ số thị trường chung từ đầu đến cuối kỳ Test.
  3. **`Equal-Weight VN30`**: Phân bổ đều vào 30 mã VN30.
  4. **`Random Forest (Val-Tuned Threshold)`**: Mua các mã có `proba_rf >= tau*`, giữ cố định 10 phiên, trừ phí & thuế `0.40%`.
  5. **`MLP Neural Net (PLOS ONE 2025)`**: Mua theo tín hiệu `proba_mlp_sota >= tau*`, trừ phí & thuế `0.40%`.
  6. **`Best-Model Top-3 + Quản trị rủi ro T+3` (Chiến lược Đề xuất — chọn động model quán quân theo kết quả `Validation 2024`, thường là `LightGBM` hoặc `Random Forest`)**:
     - Mỗi ngày `T`, lọc các mã có `proba_best >= tau*`, chọn tối đa **Top 3 mã xác suất cao nhất** (không vượt quá 10 slot đang mở), khớp mua ở **`open_{t+1}`**.
     - **Quy tắc nắm giữ tối thiểu `T+3` (xấp xỉ bảo thủ cho luật T+2.5 của HOSE do dữ liệu chỉ có nến ngày) & Stop-loss/Take-profit**:
       - Khóa không bán trong 2 phiên đầu sau khi mua; từ phiên thứ 3 đến phiên thứ 10, quét tuần tự từng phiên theo `prices.parquet` (nếu mở cửa gap down quá `-7%` thì cắt lỗ theo đúng giá `open` thực tế; nếu chạm cả SL `-7%` và TP `+15%` trong cùng 1 phiên thì ưu tiên tính Stop-loss trước để thận trọng).
       - Hết phiên thứ 10 chưa chạm SL/TP $\to$ đóng lệnh theo giá `close`, trừ phí & thuế `0.40%`.
     - **Tái đầu tư lãi kép (Compounding)**: Cập nhật `NAV` theo từng ngày giao dịch.

### Bước 3: Xuất Bảng Tổng Hợp & Đường Cong Vốn Cho Người E
- [ ] Xuất bảng so sánh 5 chiến lược ra `data/processed/backtest_summary.csv`.
- [ ] Xuất chuỗi thời gian tài sản ròng hàng ngày (`NAV`) và mức sụt giảm (`Drawdown %`) ra `data/processed/equity_curve.parquet`.

### Bước 4: Hoàn thiện `notebooks/04_backtest_sim.ipynb`
- [ ] Vẽ biểu đồ 2 trục (Dual-axis Chart) hoặc Bubble Chart: `Threshold` vs `Precision` vs `CAGR` vs `Số lệnh/ngày` (chứng minh vì sao ngưỡng `0.55 - 0.58` là vùng tối ưu Sweet Spot).
- [ ] Vẽ biểu đồ đường cong vốn (`Equity Curve`) so sánh 5 chiến lược với `VN-Index`.
- [ ] Vẽ biểu đồ `Underwater Drawdown Chart` chứng minh cơ chế `Top-3 + Stop-loss` giúp giảm thiểu rủi ro sụt giảm tài khoản khi thị trường điều chỉnh.

---

## 4. Tiêu Chí Nghiệm Thu Bàn Giao Cho Người E (Definition of Done)

```bash
python -c "
import pandas as pd
bt = pd.read_csv('data/processed/backtest_summary.csv')
eq = pd.read_parquet('data/processed/equity_curve.parquet')
tt = pd.read_csv('data/processed/threshold_tuning.csv')
print('OK backtest_summary.csv:\n', bt[['strategy_name','cagr_pct','sharpe_ratio','max_drawdown_pct','win_rate_pct']])
print('OK equity_curve.parquet:', eq.shape)
print('OK threshold_tuning.csv:', tt.shape)
"
```
