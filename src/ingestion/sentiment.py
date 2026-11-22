"""
mo hinh phan tich cam xuc tin tuc tai chinh tieng viet (hybrid tf-idf + logistic regression & lexicon).
ket hop tu dien chuyen nganh chung khoan va mo hinh hoc may scikit-learn chay sieu nhanh tren cpu.
"""

from functools import lru_cache
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

# tu khoa tich cuc va tieu cuc trong tin tuc chung khoan viet nam
POSITIVE_KEYWORDS: tuple[str, ...] = (
    " tăng ", "tang truong", "tăng trưởng", "kỷ lục", "ky luc", "đột biến", "dot bien",
    "lãi lớn", "lai lon", "lãi ròng", "lợi nhuận tăng", "vượt kế hoạch", "vuot ke hoach",
    "cổ tức", "co tuc", "chia thưởng", "mua vào", "mua ròng", "gom hàng", "tích cực",
    "bứt phá", "but pha", "khởi sắc", "khoi sac", "đỉnh mới", "vượt đỉnh", "hồi phục",
    "phục hồi", "thắng lớn", "tăng trần", "tím lịm", "hưởng lợi", "triển vọng",
    "ký kết", "hợp đồng lớn", "mở rộng", "đầu tư mới", "nâng hạng", "khả quan",
)

NEGATIVE_KEYWORDS: tuple[str, ...] = (
    " giảm ", "sụt giảm", "sut giam", "thua lỗ", "báo lỗ", "lỗ nặng", "lỗ ròng",
    "lao dốc", "lao doc", "bốc hơi", "boc hoi", "xả hàng", "xa hang", "bán tháo",
    "bán ròng", "ban rong", "bị phạt", "xử phạt", "vi phạm", "nợ xấu", "no xau",
    "phá sản", "đình chỉ", "hủy niêm yết", "cảnh báo", "kiểm soát", "bi quan",
    "thấp nhất", "đáy mới", "thủng đáy", "giảm sàn", "lau sàn", "rủi ro",
    "khó khăn", "đình trệ", "suy thoái", "thanh tra", "khởi tố", "bắt tạm giam",
)

# tap du lieu hat giong (seed corpus) de huan luyen pipeline tf-idf + logistic regression
SEED_CORPUS: tuple[tuple[str, int], ...] = (
    ("lợi nhuận sau thuế tăng trưởng kỷ lục vượt kế hoạch năm", 1),
    ("doanh thu bứt phá mạnh chia cổ tức tiền mặt tỷ lệ cao", 1),
    ("khối ngoại mua ròng mạnh cổ phiếu tăng trần khởi sắc", 1),
    ("ký kết hợp đồng lớn mở rộng đầu tư triển vọng khả quan", 1),
    ("cổ phiếu hồi phục vượt đỉnh mới nhờ kết quả kinh doanh tích cực", 1),
    ("lãi lớn quý này nhờ biên lợi nhuận cải thiện đột biến", 1),
    ("doanh nghiệp báo lỗ nặng lợi nhuận sụt giảm lao dốc", -1),
    ("cổ phiếu bị bán tháo xả hàng bốc hơi vốn hóa giảm sàn", -1),
    ("bị xử phạt vi phạm hành chính cảnh báo rủi ro nợ xấu tăng", -1),
    ("khối ngoại bán ròng liên tiếp thủng đáy mới đầy khó khăn", -1),
    ("đình chỉ giao dịch kiểm soát đặc biệt do thua lỗ kéo dài", -1),
    ("thanh tra khởi tố vi phạm công bố thông tin suy thoái", -1),
    ("thông báo lịch họp đại hội đồng cổ đông thường niên năm nay", 0),
    ("nghị quyết hội đồng quản trị về việc thay đổi địa chỉ trụ sở", 0),
    ("báo cáo tình hình quản trị công ty 6 tháng đầu năm", 0),
    ("thông báo ngày đăng ký cuối cùng để thực hiện quyền tham dự họp", 0),
)


@lru_cache(maxsize=1)
def get_tfidf_sentiment_model() -> Pipeline:
    """khoi tao va huan luyen pipeline tf-idf (1-2 ngrams) + logistic regression tren seed corpus."""
    texts = [item[0] for item in SEED_CORPUS]
    labels = [item[1] for item in SEED_CORPUS]
    model = Pipeline(
        [
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), lowercase=True)),
            ("clf", LogisticRegression(C=2.0, random_state=42)),
        ]
    )
    model.fit(texts, labels)
    return model


def score_vietnamese_headline(headline: str) -> float:
    """
    tinh diem cam xuc [-1.0, 1.0] ket hop (ensemble):
    60% tu diem tu dien chuyen nganh + 40% tu xac suat mo hinh tf-idf logistic regression.
    """
    if not headline or not isinstance(headline, str):
        return 0.0

    text = f" {headline.lower().strip()} "
    pos_hits = sum(1 for kw in POSITIVE_KEYWORDS if kw in text)
    neg_hits = sum(1 for kw in NEGATIVE_KEYWORDS if kw in text)
    if pos_hits == 0 and neg_hits == 0:
        return 0.0

    lex_score = (pos_hits - neg_hits) / float(pos_hits + neg_hits + 0.5)
    model = get_tfidf_sentiment_model()
    probs = model.predict_proba([text])[0]
    classes = list(model.classes_)
    p_pos = probs[classes.index(1)] if 1 in classes else 0.0
    p_neg = probs[classes.index(-1)] if -1 in classes else 0.0
    ml_score = float(p_pos - p_neg)

    blended = 0.65 * lex_score + 0.35 * ml_score
    return round(max(-1.0, min(1.0, blended)), 4)
