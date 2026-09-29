"""Quality gate: fail the pipeline (and Jenkins build) if the champion is too weak (stage 4)."""
import json
import sys
from src.config import METRICS_PATH

MIN_F1, MIN_AUC = 0.75, 0.80


def main():
    m = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
    print(json.dumps(m, indent=2))
    if m["f1"] < MIN_F1 or m["roc_auc"] < MIN_AUC:
        print(f"QUALITY GATE FAILED (need f1>={MIN_F1}, roc_auc>={MIN_AUC})")
        sys.exit(1)
    print("Quality gate passed.")


if __name__ == "__main__":
    main()
