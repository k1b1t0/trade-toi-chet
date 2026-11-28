"""
huan luyen va suy luan cam xuc tin tuc tai chinh tieng viet (llm distillation -> tfidf + logistic regression).
khong chua bat ky tu khoa hay cau mau gan cung nao; doc nhan llm tu sqlite va luu model ra .joblib.
"""

from functools import lru_cache
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.pipeline import Pipeline

from src.config import RANDOM_SEED, SENTIMENT_MODEL_PATH, SQLITE_DB_PATH, VAL_END_DATE
from src.ingestion.db import get_connection


def build_sentiment_pipeline() -> Pipeline:
    """tao pipeline tfidf (1-3 ngrams, sublinear_tf, min_df=2) + logistic regression can bang trong so lop."""
    return Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    ngram_range=(1, 3),
                    sublinear_tf=True,
                    min_df=2,
                    max_features=30000,
                    lowercase=True,
                ),
            ),
            (
                "clf",
                LogisticRegression(
                    C=5.0,
                    class_weight="balanced",
                    max_iter=1000,
                    random_state=RANDOM_SEED,
                ),
            ),
        ]
    )


def train_and_save_sentiment_model(
    db_path: Path = SQLITE_DB_PATH,
    model_path: Path = SENTIMENT_MODEL_PATH,
    train_cutoff: str = VAL_END_DATE,
) -> dict[str, float]:
    """
    doc bang sentiment_labels ket hop ngay dang tu raw_news, chia temporal split chong ro ri:
    train tren <= train_cutoff (2019-2024), danh gia out-of-time tren > train_cutoff (2025-2026),
    va luu model chi fit tren tap train ra file .joblib.
    """
    query = """
        SELECT s.headline, s.llm_label, MIN(r.pub_date) AS first_date
        FROM sentiment_labels s
        INNER JOIN raw_news r ON s.headline = r.headline
        GROUP BY s.headline, s.llm_label
    """
    with get_connection(db_path) as conn:
        df = pd.read_sql_query(query, conn)

    train_df = df[df["first_date"] <= train_cutoff]
    test_df = df[df["first_date"] > train_cutoff]
    if len(train_df) < 50 or len(test_df) < 50:
        raise ValueError(
            f"Insufficient temporal labels (train={len(train_df)}, test={len(test_df)})."
        )

    X_train = train_df["headline"].astype(str).to_numpy(dtype=object)
    y_train = train_df["llm_label"].astype(int).to_numpy(dtype=int)
    X_test = test_df["headline"].astype(str).to_numpy(dtype=object)
    y_test = test_df["llm_label"].astype(int).to_numpy(dtype=int)

    model = build_sentiment_pipeline()
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    acc = float(accuracy_score(y_test, y_pred))
    macro_f1 = float(f1_score(y_test, y_pred, average="macro"))
    weighted_f1 = float(f1_score(y_test, y_pred, average="weighted"))
    print(
        f"[SENTIMENT] Temporal Out-of-Time Eval "
        f"(train <= {train_cutoff}: {len(X_train)}, test > {train_cutoff}: {len(X_test)}):"
    )
    print(f"    Accuracy: {acc:.4f} | Macro-F1: {macro_f1:.4f} | Weighted-F1: {weighted_f1:.4f}")
    print(classification_report(y_test, y_pred, digits=4))

    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_path)
    load_sentiment_model.cache_clear()
    print(f"[OK] Saved leak-free TF-IDF sentiment model (fit on <= {train_cutoff}) to {model_path}")
    return {
        "accuracy": acc,
        "macro_f1": macro_f1,
        "weighted_f1": weighted_f1,
        "train_samples": float(len(X_train)),
        "test_samples": float(len(X_test)),
    }


@lru_cache(maxsize=2)
def load_sentiment_model(model_path: Path = SENTIMENT_MODEL_PATH) -> Pipeline:
    """load model .joblib tu o dia va luu vao bo nho cache de suy luan < 0.1ms/cau."""
    if not model_path.exists():
        train_and_save_sentiment_model(model_path=model_path)
    return joblib.load(model_path)


def score_headlines_batch(headlines: list[str], model_path: Path = SENTIMENT_MODEL_PATH) -> np.ndarray:
    """cham diem cam xuc hang loat P(y=+1) - P(y=-1) trong doan [-1.0, 1.0]."""
    if not headlines:
        return np.array([], dtype="float64")
    model = load_sentiment_model(model_path)
    probs = model.predict_proba(headlines)
    classes = list(model.classes_)
    pos_idx = classes.index(1) if 1 in classes else -1
    neg_idx = classes.index(-1) if -1 in classes else -1
    p_pos = probs[:, pos_idx] if pos_idx >= 0 else np.zeros(len(headlines))
    p_neg = probs[:, neg_idx] if neg_idx >= 0 else np.zeros(len(headlines))
    scores = np.clip(p_pos - p_neg, -1.0, 1.0)
    return np.round(scores, 4)


def score_vietnamese_headline(headline: str, model_path: Path = SENTIMENT_MODEL_PATH) -> float:
    """tinh diem cam xuc [-1.0, 1.0] cho 1 tieu de tin tuc bang model .joblib da train."""
    if not headline or not isinstance(headline, str) or not headline.strip():
        return 0.0
    return float(score_headlines_batch([headline.strip()], model_path=model_path)[0])
