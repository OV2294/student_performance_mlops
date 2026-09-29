"""Basic monitoring: data drift via Population Stability Index (PSI) (stage 5).

python -m src.monitor              # compare logged API predictions vs training reference
python -m src.monitor --simulate   # simulate a drifted incoming batch (for demos)
"""
import argparse
import json
import numpy as np
import pandas as pd
from src.config import ROOT, load_params, NUMERIC_FEATURES, PRED_LOG_PATH, DRIFT_PATH
from src.generate_data import make_students


def psi(expected: pd.Series, actual: pd.Series, bins: int = 10) -> float:
    expected, actual = expected.dropna(), actual.dropna()
    edges = np.unique(np.quantile(expected, np.linspace(0, 1, bins + 1)))
    edges[0], edges[-1] = -np.inf, np.inf
    e = np.histogram(expected, edges)[0] / len(expected)
    a = np.histogram(actual, edges)[0] / len(actual)
    e, a = np.clip(e, 1e-4, None), np.clip(a, 1e-4, None)
    return float(np.sum((a - e) * np.log(a / e)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--simulate", action="store_true")
    args = ap.parse_args()
    params = load_params()
    thr = params["monitor"]["psi_threshold"]
    ref = pd.read_csv(ROOT / params["data"]["processed_dir"] / "reference.csv")

    if args.simulate:
        cur, source = make_students(600, seed=7, drift=True), "simulated drifted batch"
    elif PRED_LOG_PATH.exists() and len(pd.read_csv(PRED_LOG_PATH)) >= 30:
        cur, source = pd.read_csv(PRED_LOG_PATH), "logged API predictions"
    else:
        cur, source = make_students(600, seed=99), "fresh healthy sample (no live traffic yet)"

    rows = {f: round(psi(ref[f], cur[f]), 4) for f in NUMERIC_FEATURES}
    drifted = [f for f, v in rows.items() if v > thr]
    report = {"source": source, "n_current": len(cur), "threshold": thr,
              "psi": rows, "drifted_features": drifted, "drift_detected": bool(drifted)}
    DRIFT_PATH.parent.mkdir(exist_ok=True)
    DRIFT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
