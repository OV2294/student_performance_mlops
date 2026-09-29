"""Create a reproducible synthetic student dataset (stage 1 of the DVC pipeline)."""
import numpy as np
import pandas as pd
from src.config import ROOT, load_params


def make_students(n: int, seed: int, drift: bool = False) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    study = np.clip(rng.normal(14 if not drift else 8, 6, n), 0, 40)
    attend = np.clip(rng.normal(78 if not drift else 62, 14, n), 20, 100)
    prev = np.clip(rng.normal(60, 15, n), 0, 100)
    assign = np.clip(rng.normal(75, 18, n), 0, 100)
    sleep = np.clip(rng.normal(6.9 if not drift else 5.8, 1.2, n), 3, 10)
    stress = rng.integers(1, 6, n)
    tutoring = rng.choice(["Yes", "No"], n, p=[0.3, 0.7])
    extra = rng.choice(["Yes", "No"], n, p=[0.4, 0.6])
    internet = rng.choice(["Yes", "No"], n, p=[0.88, 0.12])
    gender = rng.choice(["Male", "Female"], n)
    parent = rng.choice(["School", "Graduate", "Postgraduate"], n, p=[0.4, 0.4, 0.2])
    age = rng.integers(17, 25, n)
    midterm = np.clip(0.55 * prev + 0.25 * attend + 0.6 * study + rng.normal(0, 8, n) - 10, 0, 100)

    final = (
        0.30 * midterm + 0.20 * prev + 0.15 * attend + 0.10 * assign
        + 0.45 * study + 1.2 * (tutoring == "Yes") + 1.0 * (internet == "Yes")
        + 1.5 * (parent == "Postgraduate") - 1.8 * (stress - 3) + 0.8 * (sleep - 7)
        - 0.5 * (extra == "Yes") + rng.normal(0, 5, n) - 12
    )
    final = np.clip(final, 0, 100)

    df = pd.DataFrame({
        "student_id": np.arange(1, n + 1), "gender": gender, "age": age,
        "study_hours_per_week": study.round(1), "attendance_pct": attend.round(1),
        "previous_score": prev.round(1), "assignments_completed_pct": assign.round(1),
        "sleep_hours": sleep.round(1), "stress_level": stress, "midterm_score": midterm.round(1),
        "internet_access": internet, "parental_education": parent,
        "tutoring": tutoring, "extracurricular": extra,
        "final_score": final.round(1),
    })
    df["passed"] = (df["final_score"] >= 40).astype(int)

    # inject ~2% missing values so the preprocessing stage has real work to do
    for col in ["sleep_hours", "attendance_pct", "parental_education"]:
        df.loc[rng.random(n) < 0.02, col] = np.nan
    return df


def main():
    p = load_params()["data"]
    out = ROOT / p["raw_path"]
    out.parent.mkdir(parents=True, exist_ok=True)
    df = make_students(p["n_samples"], p["seed"])
    df.to_csv(out, index=False)
    print(f"Wrote {len(df)} rows -> {out}  (pass rate {df['passed'].mean():.2%})")


if __name__ == "__main__":
    main()
