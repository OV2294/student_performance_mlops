import pandas as pd
from fastapi.testclient import TestClient
from src.generate_data import make_students
from src.pipeline import build_pipeline
from src.monitor import psi
from src.config import FEATURES, TARGET


def test_data_generation_shape_and_target():
    df = make_students(300, 1)
    assert len(df) == 300 and set(FEATURES + [TARGET]).issubset(df.columns)
    assert 0.2 < df[TARGET].mean() < 0.95


def test_pipeline_fits_and_predicts_with_missing_values():
    df = make_students(400, 2)
    pipe = build_pipeline("logistic_regression", {"max_iter": 500}).fit(df[FEATURES], df[TARGET])
    proba = pipe.predict_proba(df[FEATURES])[:, 1]
    assert proba.min() >= 0 and proba.max() <= 1


def test_psi_detects_shift():
    a = pd.Series(range(1000)); b = a + 400
    assert psi(a, a) < 0.01 and psi(a, b) > 0.2


def test_api_health_and_predict(tmp_path):
    from src.api import app
    from src.config import MODEL_PATH
    c = TestClient(app)
    assert c.get("/health").status_code == 200
    payload = {"gender": "Male", "age": 20, "study_hours_per_week": 12, "attendance_pct": 80,
               "previous_score": 60, "assignments_completed_pct": 70, "sleep_hours": 7,
               "stress_level": 3, "midterm_score": 55, "internet_access": "Yes",
               "parental_education": "Graduate", "tutoring": "No", "extracurricular": "Yes"}
    r = c.post("/predict", json=payload)
    assert r.status_code == (200 if MODEL_PATH.exists() else 503)
    assert c.post("/predict", json={**payload, "age": 3}).status_code == 422
