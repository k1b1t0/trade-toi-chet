"""
cau hinh hang so dung chung cho toan bo he thong tradetoichet.
cac sub-package trong he thong import truc tiep tu file nay.
"""

from pathlib import Path

# duong dan thu muc goc va cac thu muc du lieu
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DATA_RAW_DIR = DATA_DIR / "raw"
DATA_PROCESSED_DIR = DATA_DIR / "processed"
SQLITE_DB_PATH = DATA_DIR / "tradetoichet.db"

# danh sach 30 ma co phieu trong ro vn30 va chi so vnindex
VN30_TICKERS: list[str] = [
    "ACB", "BCM", "BID", "BVH", "CTG", "FPT", "GAS", "GVR", "HDB", "HPG",
    "MBB", "MSN", "MWG", "PLX", "POW", "SAB", "SHB", "SSB", "SSI", "STB",
    "TCB", "TPB", "VCB", "VHM", "VIB", "VIC", "VJC", "VNM", "VPB", "VRE",
]
BENCHMARK_TICKER: str = "VNINDEX"

# phan nhom nganh cho 30 ma vn30 va chi so thi truong
SECTOR_MAP: dict[str, str] = {
    "ACB": "Banking", "BID": "Banking", "CTG": "Banking", "HDB": "Banking",
    "MBB": "Banking", "SHB": "Banking", "SSB": "Banking", "STB": "Banking",
    "TCB": "Banking", "TPB": "Banking", "VCB": "Banking", "VIB": "Banking",
    "VPB": "Banking",
    "BCM": "RealEstate", "VHM": "RealEstate", "VIC": "RealEstate", "VRE": "RealEstate",
    "MSN": "Consumer", "MWG": "Consumer", "SAB": "Consumer", "VNM": "Consumer",
    "GAS": "Energy", "PLX": "Energy", "POW": "Energy",
    "BVH": "Financials", "SSI": "Financials",
    "FPT": "Technology",
    "HPG": "Steel",
    "GVR": "Industrial", "VJC": "Industrial",
    "VNINDEX": "Index",
}

# khoang thoi gian lay du lieu va moc chia temporal split (chong look-ahead bias)
START_DATE: str = "2019-01-01"
END_DATE: str = "2026-03-01"
TRAIN_END_DATE: str = "2023-12-31"
VAL_END_DATE: str = "2024-12-31"

# tham so giao dich thuc te tren san hose viet nam
HOLDING_DAYS: int = 10
TARGET_THRESHOLD: float = 0.015
VN_BUY_FEE: float = 0.0015
VN_SELL_FEE: float = 0.0015
VN_SELL_TAX: float = 0.0010
MIN_HOLD_T_PLUS: int = 3
RANDOM_SEED: int = 42
