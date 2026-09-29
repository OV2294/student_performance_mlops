"""Shared inference + prediction logging used by both FastAPI and Streamlit."""
from datetime import datetime, timezone
import joblib
import pandas as pd
from src.config import MODEL_PATH, FEATURES, PRED_LOG_PATH

_model = None


def get_model():
    global _model
    if _model is None:
        _model = joblib.load(MODEL_PATH)
    return _model


def predict_df(df: pd.DataFrame, log: bool = True) -> pd.DataFrame:
    X = df[FEATURES]
    proba = get_model().predict_proba(X)[:, 1]
    out = df.copy()
    out["pass_probability"] = proba.round(4)
    out["prediction"] = (proba >= 0.5).astype(int)
    out["risk_level"] = pd.cut(proba, [-0.01, 0.4, 0.65, 1.01], labels=["High risk", "Medium risk", "Low risk"]).astype(str)
    if log:
        log_predictions(out)
    return out


def log_predictions(df: pd.DataFrame) -> None:
    PRED_LOG_PATH.parent.mkdir(exist_ok=True)
    rec = df[FEATURES + ["pass_probability", "prediction"]].copy()
    rec.insert(0, "timestamp", datetime.now(timezone.utc).isoformat(timespec="seconds"))
    rec.to_csv(PRED_LOG_PATH, mode="a", header=not PRED_LOG_PATH.exists(), index=False)
