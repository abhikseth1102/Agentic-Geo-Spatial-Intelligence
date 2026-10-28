"""Compare next-observed-speed models on vessel-disjoint held-out data."""

from pathlib import Path
import json
import time
import platform
import numpy as np
import pandas as pd
import sklearn
from sklearn.model_selection import GroupShuffleSplit
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.ensemble import (
    RandomForestRegressor,
    HistGradientBoostingRegressor,
    IsolationForest,
)
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.inspection import permutation_importance
import joblib

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/atlas"
FEATURES = ["speed", "course_sin", "course_cos", "lat", "lon", "type_code"]


def main():
    df = pd.read_csv(OUT / "observations.csv", dtype={"mmsi": str})
    eligible = df[df.next_minutes.between(2, 30) & df.next_speed.notna()].copy()
    train, test = next(
        GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=42).split(
            eligible, groups=eligible.mmsi
        )
    )
    a, b = eligible.iloc[train], eligible.iloc[test]
    X, y = a[FEATURES], a.next_speed
    Xt, yt = b[FEATURES], b.next_speed
    models = {
        "Ridge regression": make_pipeline(StandardScaler(), Ridge(alpha=10)),
        "Random forest": RandomForestRegressor(
            n_estimators=100,
            max_depth=14,
            min_samples_leaf=8,
            n_jobs=2,
            random_state=42,
        ),
        "Gradient boosting": HistGradientBoostingRegressor(
            max_iter=140, max_leaf_nodes=20, l2_regularization=2, random_state=42
        ),
    }
    results = []
    predictions = {
        "Persistence baseline": b.speed.to_numpy(),
        "Training median": np.full(len(b), y.median()),
    }
    durations = {k: 0 for k in predictions}
    for name, model in models.items():
        start = time.perf_counter()
        model.fit(X, y)
        durations[name] = time.perf_counter() - start
        predictions[name] = np.clip(model.predict(Xt), 0, 60)
    for name, pred in predictions.items():
        results.append(
            dict(
                model=name,
                mae=round(mean_absolute_error(yt, pred), 4),
                rmse=round(float(np.sqrt(mean_squared_error(yt, pred))), 4),
                r2=round(r2_score(yt, pred), 4),
                train_seconds=round(durations[name], 3),
            )
        )
    # Fixed model selected in advance, not chosen by its test-set rank.
    model = models["Gradient boosting"]
    joblib.dump(model, OUT / "speed_model.joblib")
    rng = np.random.default_rng(42)
    error = np.abs(yt.to_numpy() - predictions["Gradient boosting"])
    # Bootstrap vessels as clusters, respecting dependence among repeated pings.
    grouped = (
        pd.DataFrame({"mmsi": b.mmsi.to_numpy(), "error": error})
        .groupby("mmsi")
        .error.agg(["sum", "count"])
    )
    boot = []
    for _ in range(500):
        sample = grouped.iloc[rng.integers(0, len(grouped), len(grouped))]
        boot.append(sample["sum"].sum() / sample["count"].sum())
    take = Xt.sample(min(2000, len(Xt)), random_state=42)
    imp = permutation_importance(
        model,
        take,
        yt.loc[take.index],
        n_repeats=5,
        random_state=42,
        scoring="neg_mean_absolute_error",
    )
    isolation = IsolationForest(
        n_estimators=100, contamination=0.03, random_state=42, n_jobs=2
    )
    anomaly_features = ["speed", "lat", "lon", "course_sin", "course_cos"]
    isolation.fit(a[anomaly_features])
    df["anomaly_score"] = -isolation.score_samples(df[anomaly_features])
    df["anomaly"] = isolation.predict(df[anomaly_features]) == -1
    df.to_csv(OUT / "observations.csv", index=False)
    import hashlib

    manifest = json.loads((OUT / "manifest.json").read_text())
    manifest["sha256"] = hashlib.sha256(
        (OUT / "observations.csv").read_bytes()
    ).hexdigest()
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2))
    scatter = (
        pd.DataFrame({"actual": yt, "predicted": predictions["Gradient boosting"]})
        .sample(min(300, len(yt)), random_state=42)
        .round(3)
        .to_dict("records")
    )
    subgroup = []
    for label, mask in [
        ("Stationary or slow (<0.5 kn)", b.speed < 0.5),
        ("Moving (>=0.5 kn)", b.speed >= 0.5),
        ("Short horizon (2–10 min)", b.next_minutes <= 10),
        ("Longer horizon (>10–30 min)", b.next_minutes > 10),
    ]:
        subgroup.append(
            dict(
                group=label,
                n=int(mask.sum()),
                persistence_mae=round(mean_absolute_error(yt[mask], b.speed[mask]), 4),
                boosting_mae=round(
                    mean_absolute_error(
                        yt[mask], predictions["Gradient boosting"][mask]
                    ),
                    4,
                ),
            )
        )
    report = dict(
        task="Next observed speed (knots), 2–30 minutes ahead",
        features=FEATURES,
        seed=42,
        train_rows=len(a),
        test_rows=len(b),
        train_vessels=a.mmsi.nunique(),
        test_vessels=b.mmsi.nunique(),
        overlapping_vessels=len(set(a.mmsi) & set(b.mmsi)),
        split="One fixed vessel-disjoint 75/25 GroupShuffleSplit; no hyperparameter search.",
        selected_model="Gradient boosting (specified before evaluation)",
        results=results,
        mae_cluster_bootstrap_95ci=[
            round(float(x), 4) for x in np.quantile(boot, [0.025, 0.975])
        ],
        feature_importance=[
            dict(feature=f, increase_mae=round(float(v), 4), std=round(float(s), 4))
            for f, v, s in zip(FEATURES, imp.importances_mean, imp.importances_std)
        ],
        scatter=scatter,
        subgroups=subgroup,
        python=platform.python_version(),
        sklearn=sklearn.__version__,
        limitations=[
            "One day and one geographic cohort; no evidence of cross-season generalization.",
            "Variable next-observation horizon, not a fixed 15-minute forecast.",
            "Test data were used only for evaluation, not parameter tuning.",
            "Weather distance is excluded from predictive features because best-track data are retrospective.",
            "Isolation Forest flags unusual feature combinations, not verified dangerous behavior.",
        ],
    )
    (OUT / "benchmark.json").write_text(json.dumps(report, indent=2))
    print(json.dumps({k: v for k, v in report.items() if k != "scatter"}, indent=2))


if __name__ == "__main__":
    main()
