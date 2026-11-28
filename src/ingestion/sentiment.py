"""
huan luyen va suy luan cam xuc tin tuc tai chinh tieng viet (llm distillation -> tfidf + logistic regression).
chi fit tren tap train <= TRAIN_END_DATE (2023-12-31) de chong leak cho ca validation (2024) va test (2025+).
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

from src.config import (
    RANDOM_SEED,
    SENTIMENT_LABELS_PATH,
    SENTIMENT_MODEL_PATH,
    SQLITE_DB_PATH,
    TRAIN_END_DATE,
)
from src.ingestion.db import get_connection


def build_sentiment_pipeline() -> Pipeline:
    """tao pipeline tfidf (1-3 ngrams, sublinear_tf, min_df=2) + logistic regression can bang lop."""
    return Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    ngram_range=(1, 3), sublinear_tf=True, min_df=2, max_features=30000, lowercase=True
                ),
            ),
            (
                "clf",
                LogisticRegression(C=5.0, class_weight="balanced", max_iter=1000, random_state=RANDOM_SEED),
            ),
        ]
    )


def _load_labeled_headlines(db_path: Path, labels_path: Path) -> pd.DataFrame:
    """doc nhan llm tu sqlite (va export ra parquet nhe) hoac doc tu parquet neu chua co sqlite."""
    if db_path.exists():
        query = """
            SELECT s.headline, s.llm_label, MIN(r.pub_date) AS first_date
            FROM sentiment_labels s
            INNER JOIN raw_news r ON s.headline = r.headline
            GROUP BY s.headline, s.llm_label
        """
        with get_connection(db_path) as conn:
            df = pd.read_sql_query(query, conn)
        if not df.empty:
            labels_path.parent.mkdir(parents=True, exist_ok=True)
            df.to_parquet(labels_path, index=False)
            return df
    if labels_path.exists():
        return pd.read_parquet(labels_path)
    raise FileNotFoundError(f"Missing sentiment labels in both {db_path} and {labels_path}.")


def train_and_save_sentiment_model(
    db_path: Path = SQLITE_DB_PATH,
    model_path: Path = SENTIMENT_MODEL_PATH,
    labels_path: Path = SENTIMENT_LABELS_PATH,
    train_cutoff: str = TRAIN_END_DATE,
) -> dict[str, float]:
    """train tren <= train_cutoff (2019-2023), danh gia out-of-time tren > train_cutoff (2024-2026)."""
    df = _load_labeled_headlines(db_path=db_path, labels_path=labels_path)
    train_df = df[df["first_date"] <= train_cutoff]
    eval_df = df[df["first_date"] > train_cutoff]
    if len(train_df) < 50 or len(eval_df) < 50:
        raise ValueError(f"Insufficient temporal labels (train={len(train_df)}, eval={len(eval_df)}).")

    X_train = train_df["headline"].astype(str).to_numpy(dtype=object)
    y_train = train_df["llm_label"].astype(int).to_numpy(dtype=int)
    X_eval = eval_df["headline"].astype(str).to_numpy(dtype=object)
    y_eval = eval_df["llm_label"].astype(int).to_numpy(dtype=int)

    model = build_sentiment_pipeline()
    model.fit(X_train, y_train)
    y_pred = model.predict(X_eval)

    acc = float(accuracy_score(y_eval, y_pred))
    macro_f1 = float(f1_score(y_eval, y_pred, average="macro"))
    weighted_f1 = float(f1_score(y_eval, y_pred, average="weighted"))
    print(f"[SENTIMENT] Leak-free Out-of-Time Eval (train <= {train_cutoff}: {len(X_train)}, eval: {len(X_eval)}):")
    print(f"    Accuracy: {acc:.4f} | Macro-F1: {macro_f1:.4f} | Weighted-F1: {weighted_f1:.4f}")
    print(classification_report(y_eval, y_pred, digits=4))

    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_path)
    load_sentiment_model.cache_clear()
    print(f"[OK] Saved leak-free TF-IDF sentiment model (fit <= {train_cutoff}) to {model_path}")
    return {"accuracy": acc, "macro_f1": macro_f1, "weighted_f1": weighted_f1}


@lru_cache(maxsize=2)
def load_sentiment_model(model_path: Path = SENTIMENT_MODEL_PATH) -> Pipeline:
    """load model .joblib tu o dia va luu cache bo nho."""
    if not model_path.exists():
        train_and_save_sentiment_model(model_path=model_path)
    return joblib.load(model_path)


def score_headlines_batch(headlines: list[str], model_path: Path = SENTIMENT_MODEL_PATH) -> np.ndarray:
    """cham diem cam xuc hang loat P(y=+1) - P(y=-1) trong [-1.0, 1.0]."""
    if not headlines:
        return np.array([], dtype="float64")
    model = load_sentiment_model(model_path)
    probs = model.predict_proba(headlines)
    classes = list(model.classes_)
    p_pos = probs[:, classes.index(1)] if 1 in classes else np.zeros(len(headlines))
    p_neg = probs[:, classes.index(-1)] if -1 in classes else np.zeros(len(headlines))
    return np.round(np.clip(p_pos - p_neg, -1.0, 1.0), 4)


def score_vietnamese_headline(headline: str, model_path: Path = SENTIMENT_MODEL_PATH) -> float:
    """tinh diem cam xuc [-1.0, 1.0] cho 1 tieu de tin tuc."""
    if not headline or not isinstance(headline, str) or not headline.strip():
        return 0.0
    return float(score_headlines_batch([headline.strip()], model_path=model_path)[0])


def rescore_all_news_in_db(db_path: Path = SQLITE_DB_PATH, model_path: Path = SENTIMENT_MODEL_PATH) -> int:
    """cham lai sentiment_score cho toan bo bang raw_news bang model .joblib moi."""
    with get_connection(db_path) as conn:
        rows = conn.execute("SELECT rowid, headline FROM raw_news").fetchall()
        if not rows:
            return 0
        scores = score_headlines_batch([r[1] for r in rows], model_path=model_path)
        conn.executemany(
            "UPDATE raw_news SET sentiment_score = ? WHERE rowid = ?",
            [(float(s), r[0]) for s, r in zip(scores, rows, strict=True)],
        )
        conn.commit()
    print(f"[OK] Re-scored {len(rows):,} articles in raw_news using {model_path.name}")
    return len(rows)
