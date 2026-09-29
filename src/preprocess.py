"""Clean the raw data and split into train/test (stage 2)."""
import pandas as pd
from sklearn.model_selection import train_test_split
from src.config import ROOT, load_params, TARGET, FEATURES, NUMERIC_FEATURES


def main():
    params = load_params()
    df = pd.read_csv(ROOT / params["data"]["raw_path"])
    df = df.drop_duplicates(subset="student_id").dropna(subset=[TARGET])

    # validity rules
    df = df[(df["attendance_pct"].isna()) | df["attendance_pct"].between(0, 100)]
    df = df[df["age"].between(15, 40)]

    df = df[FEATURES + [TARGET]]
    train, test = train_test_split(
        df, test_size=params["split"]["test_size"],
        random_state=params["split"]["random_state"], stratify=df[TARGET],
    )
    out = ROOT / params["data"]["processed_dir"]
    out.mkdir(parents=True, exist_ok=True)
    train.to_csv(out / "train.csv", index=False)
    test.to_csv(out / "test.csv", index=False)
    # reference sample used later for drift monitoring
    train[NUMERIC_FEATURES].to_csv(out / "reference.csv", index=False)
    print(f"train={len(train)} test={len(test)}")


if __name__ == "__main__":
    main()
