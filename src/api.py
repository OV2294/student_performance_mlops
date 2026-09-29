"""FastAPI model-serving layer.  Run: uvicorn src.api:app --port 8000"""
import time
from typing import List, Literal
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from src.config import METRICS_PATH, MODEL_PATH
from src.predictor import predict_df
import json

app = FastAPI(title="Student Performance Prediction API", version="1.0.0")
STATS = {"requests": 0, "predictions": 0, "errors": 0, "total_latency_ms": 0.0, "started": time.time()}


class Student(BaseModel):
    gender: Literal["Male", "Female"]
    age: int = Field(ge=15, le=40)
    study_hours_per_week: float = Field(ge=0, le=80)
    attendance_pct: float = Field(ge=0, le=100)
    previous_score: float = Field(ge=0, le=100)
    assignments_completed_pct: float = Field(ge=0, le=100)
    sleep_hours: float = Field(ge=0, le=16)
    stress_level: int = Field(ge=1, le=5)
    midterm_score: float = Field(ge=0, le=100)
    internet_access: Literal["Yes", "No"]
    parental_education: Literal["School", "Graduate", "Postgraduate"]
    tutoring: Literal["Yes", "No"]
    extracurricular: Literal["Yes", "No"]


class Prediction(BaseModel):
    prediction: int
    pass_probability: float
    risk_level: str


def _run(students: List[Student]) -> List[Prediction]:
    t0 = time.perf_counter()
    try:
        df = pd.DataFrame([s.model_dump() for s in students])
        res = predict_df(df)
    except FileNotFoundError:
        STATS["errors"] += 1
        raise HTTPException(503, "Model not trained yet. Run the pipeline first.")
    STATS["requests"] += 1
    STATS["predictions"] += len(students)
    STATS["total_latency_ms"] += (time.perf_counter() - t0) * 1000
    return [Prediction(prediction=int(r.prediction), pass_probability=float(r.pass_probability),
                       risk_level=r.risk_level) for r in res.itertuples()]


@app.get("/health")
def health():
    return {"status": "ok", "model_loaded": MODEL_PATH.exists()}


@app.get("/model-info")
def model_info():
    if not METRICS_PATH.exists():
        raise HTTPException(404, "No metrics found")
    return json.loads(METRICS_PATH.read_text(encoding="utf-8"))


@app.post("/predict", response_model=Prediction)
def predict(student: Student):
    return _run([student])[0]


@app.post("/predict-batch", response_model=List[Prediction])
def predict_batch(students: List[Student]):
    return _run(students)


@app.get("/metrics")
def metrics():
    n = max(STATS["requests"], 1)
    return {"requests": STATS["requests"], "predictions": STATS["predictions"], "errors": STATS["errors"],
            "avg_latency_ms": round(STATS["total_latency_ms"] / n, 2),
            "uptime_s": int(time.time() - STATS["started"])}
