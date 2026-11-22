"""
bo tu dien cam xuc tai chinh tieng viet (vietnamese financial sentiment lexicon).
cham diem tieu de tin tuc chung khoan ve doan [-1.0, 1.0] chay tuc thi tren cpu.
"""

# tu khoa tich cuc trong tin tuc tai chinh - chung khoan viet nam (co dau va khong dau)
POSITIVE_KEYWORDS: tuple[str, ...] = (
    " tăng ", "tang truong", "tăng trưởng", "kỷ lục", "ky luc", "đột biến", "dot bien",
    "lãi lớn", "lai lon", "lãi ròng", "lợi nhuận tăng", "vượt kế hoạch", "vuot ke hoach",
    "cổ tức", "co tuc", "chia thưởng", "mua vào", "mua ròng", "gom hàng", "tích cực",
    "bứt phá", "but pha", "khởi sắc", "khoi sac", "đỉnh mới", "vượt đỉnh", "hồi phục",
    "phục hồi", "thắng lớn", "tăng trần", "tím lịm", "hưởng lợi", "triển vọng",
    "ký kết", "hợp đồng lớn", "mở rộng", "đầu tư mới", "nâng hạng", "khả quan",
)

# tu khoa tieu cuc trong tin tuc tai chinh - chung khoan viet nam
NEGATIVE_KEYWORDS: tuple[str, ...] = (
    " giảm ", "sụt giảm", "sut giam", "thua lỗ", "báo lỗ", "lỗ nặng", "lỗ ròng",
    "lao dốc", "lao doc", "bốc hơi", "boc hoi", "xả hàng", "xa hang", "bán tháo",
    "bán ròng", "ban rong", "bị phạt", "xử phạt", "vi phạm", "nợ xấu", "no xau",
    "phá sản", "đình chỉ", "hủy niêm yết", "cảnh báo", "kiểm soát", "bi quan",
    "thấp nhất", "đáy mới", "thủng đáy", "giảm sàn", "lau sàn", "rủi ro",
    "khó khăn", "đình trệ", "suy thoái", "thanh tra", "khởi tố", "bắt tạm giam",
)


def score_vietnamese_headline(headline: str) -> float:
    """
    tinh diem cam xuc cua 1 tieu de tin tuc chung khoan tieng viet trong doan [-1.0, 1.0].
    cong thuc: (so_tu_tich_cuc - so_tu_tieu_cuc) / (so_tu_tich_cuc + so_tu_tieu_cuc + 1).
    """
    if not headline or not isinstance(headline, str):
        return 0.0

    text = f" {headline.lower().strip()} "
    pos_hits = sum(1 for kw in POSITIVE_KEYWORDS if kw in text)
    neg_hits = sum(1 for kw in NEGATIVE_KEYWORDS if kw in text)

    if pos_hits == 0 and neg_hits == 0:
        return 0.0

    raw_score = (pos_hits - neg_hits) / float(pos_hits + neg_hits + 0.5)
    return round(max(-1.0, min(1.0, raw_score)), 4)
