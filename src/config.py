"""Central config + shared constants (all paths are Windows-safe via pathlib)."""
from pathlib import Path
import os
import yaml

ROOT = Path(__file__).resolve().parents[1]

NUMERIC_FEATURES = [
    "age", "study_hours_per_week", "attendance_pct", "previous_score",
    "assignments_completed_pct", "sleep_hours", "stress_level", "midterm_score",
]
CATEGORICAL_FEATURES = [
    "gender", "internet_access", "parental_education", "tutoring", "extracurricular",
]
FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES
TARGET = "passed"

MODEL_PATH = ROOT / "models" / "model.joblib"
METRICS_PATH = ROOT / "reports" / "metrics.json"
DRIFT_PATH = ROOT / "reports" / "drift_report.json"
PRED_LOG_PATH = ROOT / "logs" / "predictions.csv"
TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", f"sqlite:///{(ROOT / 'mlflow.db').as_posix()}")


def load_params(path: Path = ROOT / "params.yaml") -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)
