"""Streamlit dashboard.  Run: streamlit run app.py"""
import json
import pandas as pd
import streamlit as st
from src.config import FEATURES, METRICS_PATH, DRIFT_PATH, PRED_LOG_PATH, MODEL_PATH

st.set_page_config(page_title="Student Performance MLOps", page_icon="🎓", layout="wide")
st.title("🎓 Student Performance Prediction")
st.caption("MLOps pipeline: DVC • MLflow • FastAPI • Docker • Jenkins CI/CD • Drift monitoring")

if not MODEL_PATH.exists():
    st.error("No trained model found. Run `scripts\\run_pipeline.bat` (or `dvc repro`) first.")
    st.stop()

from src.predictor import predict_df  # noqa: E402  (import after model check)

tab1, tab2, tab3, tab4 = st.tabs(["🔮 Predict", "📂 Batch upload", "📈 Model & metrics", "🩺 Monitoring"])

with tab1:
    c1, c2, c3 = st.columns(3)
    with c1:
        gender = st.selectbox("Gender", ["Male", "Female"])
        age = st.slider("Age", 17, 30, 20)
        study = st.slider("Study hours / week", 0.0, 40.0, 14.0, 0.5)
        attend = st.slider("Attendance %", 0.0, 100.0, 78.0)
    with c2:
        prev = st.slider("Previous score", 0.0, 100.0, 60.0)
        assign = st.slider("Assignments completed %", 0.0, 100.0, 75.0)
        mid = st.slider("Midterm score", 0.0, 100.0, 55.0)
        sleep = st.slider("Sleep hours", 3.0, 10.0, 7.0, 0.5)
    with c3:
        stress = st.slider("Stress level (1-5)", 1, 5, 3)
        parent = st.selectbox("Parental education", ["School", "Graduate", "Postgraduate"])
        internet = st.radio("Internet access", ["Yes", "No"], horizontal=True)
        tutor = st.radio("Tutoring", ["Yes", "No"], horizontal=True)
        extra = st.radio("Extracurricular", ["Yes", "No"], horizontal=True)

    if st.button("Predict", type="primary"):
        row = pd.DataFrame([{
            "gender": gender, "age": age, "study_hours_per_week": study, "attendance_pct": attend,
            "previous_score": prev, "assignments_completed_pct": assign, "sleep_hours": sleep,
            "stress_level": stress, "midterm_score": mid, "internet_access": internet,
            "parental_education": parent, "tutoring": tutor, "extracurricular": extra}])
        r = predict_df(row).iloc[0]
        p = float(r["pass_probability"])
        m1, m2, m3 = st.columns(3)
        m1.metric("Prediction", "PASS ✅" if r["prediction"] == 1 else "FAIL ❌")
        m2.metric("Pass probability", f"{p:.1%}")
        m3.metric("Risk level", r["risk_level"])
        st.progress(p)

with tab2:
    st.write("Upload a CSV with these columns:", ", ".join(FEATURES))
    up = st.file_uploader("CSV file", type="csv")
    if up:
        df = pd.read_csv(up)
        missing = [c for c in FEATURES if c not in df.columns]
        if missing:
            st.error(f"Missing columns: {missing}")
        else:
            res = predict_df(df)
            st.dataframe(res, use_container_width=True)
            st.bar_chart(res["risk_level"].value_counts())
            st.download_button("Download predictions", res.to_csv(index=False), "predictions.csv")

with tab3:
    if METRICS_PATH.exists():
        m = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
        st.subheader(f"Champion model: {m['champion']}")
        cols = st.columns(5)
        for col, k in zip(cols, ["accuracy", "precision", "recall", "f1", "roc_auc"]):
            col.metric(k.upper(), f"{m[k]:.3f}")
        st.caption(f"MLflow run id: {m['run_id']}  •  open the MLflow UI with `scripts\\start_mlflow.bat`")
    try:
        import mlflow
        from src.config import TRACKING_URI
        mlflow.set_tracking_uri(TRACKING_URI)
        runs = mlflow.search_runs(experiment_names=["student-performance"], order_by=["start_time DESC"], max_results=15)
        if len(runs):
            keep = [c for c in ["tags.mlflow.runName", "metrics.test_f1", "metrics.test_roc_auc",
                                "metrics.test_accuracy", "metrics.cv_f1", "start_time"] if c in runs.columns]
            st.subheader("Recent MLflow experiment runs")
            st.dataframe(runs[keep], use_container_width=True)
    except Exception as e:
        st.info(f"MLflow runs unavailable: {e}")

with tab4:
    if DRIFT_PATH.exists():
        d = json.loads(DRIFT_PATH.read_text(encoding="utf-8"))
        st.subheader("Data drift (PSI vs training data)")
        st.write(f"Source: **{d['source']}**  •  threshold: {d['threshold']}")
        if d["drift_detected"]:
            st.error(f"Drift detected in: {', '.join(d['drifted_features'])}  → retrain recommended")
        else:
            st.success("No significant drift detected.")
        st.bar_chart(pd.Series(d["psi"], name="PSI"))
    else:
        st.info("No drift report yet. Run `python -m src.monitor`.")
    if PRED_LOG_PATH.exists():
        log = pd.read_csv(PRED_LOG_PATH)
        st.subheader("Live prediction log")
        c1, c2 = st.columns(2)
        c1.metric("Total predictions logged", len(log))
        c2.metric("Avg pass probability", f"{log['pass_probability'].mean():.1%}")
        st.line_chart(log["pass_probability"].tail(200))
