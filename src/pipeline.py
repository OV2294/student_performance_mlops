"""Sklearn feature pipeline builder (imputation + scaling + one-hot)."""
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from src.config import NUMERIC_FEATURES, CATEGORICAL_FEATURES

MODELS = {
    "logistic_regression": lambda p: LogisticRegression(**p),
    "random_forest": lambda p: RandomForestClassifier(random_state=42, n_jobs=-1, **p),
    "gradient_boosting": lambda p: GradientBoostingClassifier(random_state=42, **p),
}


def build_pipeline(model_name: str, model_params: dict) -> Pipeline:
    pre = ColumnTransformer([
        ("num", Pipeline([("imp", SimpleImputer(strategy="median")), ("sc", StandardScaler())]), NUMERIC_FEATURES),
        ("cat", Pipeline([("imp", SimpleImputer(strategy="most_frequent")),
                          ("oh", OneHotEncoder(handle_unknown="ignore"))]), CATEGORICAL_FEATURES),
    ])
    return Pipeline([("pre", pre), ("model", MODELS[model_name](model_params))])
