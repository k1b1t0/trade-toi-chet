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
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from src.config import RANDOM_SEED, SENTIMENT_MODEL_PATH, SQLITE_DB_PATH
from src.ingestion.db import get_connection


def build_sentiment_pipeline() -> Pipeline:
    """tao pipeline tfidf (1-3 ngrams, sublinear_tf, min_df=1) + logistic regression can bang trong so lop."""
    return Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    ngram_range=(1, 3),
                    sublinear_tf=True,
                    min_df=1,
                    max_features=25000,
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
) -> dict[str, float]:
    """
    doc bang sentiment_labels do llm gan nhan trong sqlite, danh gia 80/20 train/test,
    sau do fit tren toan bo tap nhan va luu model ra file .joblib.
    """
    with get_connection(db_path) as conn:
        df = pd.read_sql_query("SELECT headline, llm_label FROM sentiment_labels", conn)

    if len(df) < 50:
        raise ValueError(f"Insufficient distilled labels in sentiment_labels table ({len(df)} rows).")

    X = df["headline"].astype(str).to_numpy(dtype=object)
    y = df["llm_label"].astype(int).to_numpy(dtype=int)

    # danh gia tren tap hold-out 80/20 co phan tang (stratified split)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_SEED, stratify=y
    )
    eval_pipe = build_sentiment_pipeline()
    eval_pipe.fit(X_train, y_train)
    y_pred = eval_pipe.predict(X_test)

    acc = float(accuracy_score(y_test, y_pred))
    macro_f1 = float(f1_score(y_test, y_pred, average="macro"))
    weighted_f1 = float(f1_score(y_test, y_pred, average="weighted"))
    print(f"[SENTIMENT] 80/20 Hold-out Evaluation on {len(X_test)} headlines:")
    print(f"    Accuracy: {acc:.4f} | Macro-F1: {macro_f1:.4f} | Weighted-F1: {weighted_f1:.4f}")
    print(classification_report(y_test, y_pred, digits=4))

    # fit tren 100% du lieu da gan nhan va xuat ra file .joblib
    final_pipe = build_sentiment_pipeline()
    final_pipe.fit(X, y)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(final_pipe, model_path)
    load_sentiment_model.cache_clear()
    print(f"[OK] Saved distilled TF-IDF sentiment model to {model_path}")
    return {"accuracy": acc, "macro_f1": macro_f1, "weighted_f1": weighted_f1, "total_samples": float(len(df))}


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
