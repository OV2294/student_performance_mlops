"""Train candidate models, track every run in MLflow, register the champion (stage 3)."""
import json
import joblib
import mlflow
import mlflow.sklearn
import pandas as pd
from mlflow.models import infer_signature
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import cross_val_score

from src.config import ROOT, load_params, TARGET, MODEL_PATH, METRICS_PATH, TRACKING_URI
from src.pipeline import build_pipeline


def score(pipe, X, y) -> dict:
    pred, proba = pipe.predict(X), pipe.predict_proba(X)[:, 1]
    return {
        "accuracy": accuracy_score(y, pred), "precision": precision_score(y, pred),
        "recall": recall_score(y, pred), "f1": f1_score(y, pred), "roc_auc": roc_auc_score(y, proba),
    }


def main():
    params = load_params()
    tp = params["train"]
    proc = ROOT / params["data"]["processed_dir"]
    train, test = pd.read_csv(proc / "train.csv"), pd.read_csv(proc / "test.csv")
    Xtr, ytr = train.drop(columns=TARGET), train[TARGET]
    Xte, yte = test.drop(columns=TARGET), test[TARGET]

    mlflow.set_tracking_uri(TRACKING_URI)
    mlflow.set_experiment(tp["experiment_name"])

    best = {"metric": -1, "name": None, "pipe": None, "run_id": None, "scores": None}
    for name, mp in tp["candidates"].items():
        with mlflow.start_run(run_name=name) as run:
            pipe = build_pipeline(name, mp).fit(Xtr, ytr)
            m = score(pipe, Xte, yte)
            cv = cross_val_score(build_pipeline(name, mp), Xtr, ytr, cv=5, scoring="f1").mean()
            mlflow.log_param("model_type", name)
            mlflow.log_params(mp)
            mlflow.log_params({"n_train": len(Xtr), "n_test": len(Xte)})
            mlflow.log_metrics({**{f"test_{k}": v for k, v in m.items()}, "cv_f1": cv})
            try:  # artifact logging must never break the DVC pipeline (e.g. odd Windows paths)
                mlflow.log_artifact(str(proc / "train.csv"), artifact_path="data")
                sig = infer_signature(Xtr, pipe.predict(Xtr))
                mlflow.sklearn.log_model(pipe, name="model", signature=sig, serialization_format="cloudpickle")
            except Exception as e:
                print(f"  [warn] MLflow artifact logging skipped for {name}: {e}")
            print(f"{name:20s} " + " ".join(f"{k}={v:.3f}" for k, v in m.items()) + f" cv_f1={cv:.3f}")
            if m[tp["select_metric"]] > best["metric"]:
                best = {"metric": m[tp["select_metric"]], "name": name, "pipe": pipe,
                        "run_id": run.info.run_id, "scores": {**m, "cv_f1": cv}}

    # champion -> disk (served by FastAPI/Streamlit) + MLflow model registry
    MODEL_PATH.parent.mkdir(exist_ok=True)
    joblib.dump(best["pipe"], MODEL_PATH)
    try:
        mlflow.register_model(f"runs:/{best['run_id']}/model", tp["registered_model_name"])
    except Exception as e:  # registry is a nice-to-have, never break the pipeline
        print("Model registry skipped:", e)

    METRICS_PATH.parent.mkdir(exist_ok=True)
    METRICS_PATH.write_text(json.dumps(
        {"champion": best["name"], "run_id": best["run_id"], **best["scores"]}, indent=2), encoding="utf-8")
    print(f"Champion: {best['name']} ({tp['select_metric']}={best['metric']:.3f})")


if __name__ == "__main__":
    main()
