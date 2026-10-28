"""Local-first maritime analysis API. No external credentials required."""

from pathlib import Path
from contextlib import asynccontextmanager
from functools import lru_cache
import json
import sqlite3
from datetime import datetime, timezone
import uuid
import numpy as np
import pandas as pd
import h3
import joblib
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, ConfigDict

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/atlas"
DB = DATA / "scenarios.sqlite"
STATE = {}


def records(df):
    return json.loads(df.to_json(orient="records"))


@asynccontextmanager
async def lifespan(app):
    if (DATA / "observations.csv").exists():
        STATE["df"] = pd.read_csv(DATA / "observations.csv", dtype={"mmsi": str})
        STATE["manifest"] = json.loads((DATA / "manifest.json").read_text())
        STATE["benchmark"] = (
            json.loads((DATA / "benchmark.json").read_text())
            if (DATA / "benchmark.json").exists()
            else None
        )
        STATE["storm"] = json.loads((DATA / "storm.json").read_text())
        STATE["model"] = (
            joblib.load(DATA / "speed_model.joblib")
            if (DATA / "speed_model.joblib").exists()
            else None
        )
        with sqlite3.connect(DB) as con:
            con.execute(
                "CREATE TABLE IF NOT EXISTS scenarios (id TEXT PRIMARY KEY, created TEXT, name TEXT, payload TEXT, result TEXT)"
            )
    yield
    STATE.clear()
    overview_cached.cache_clear()


app = FastAPI(
    title="Agentic Geo-Spatial Intelligence",
    version="2.0.0",
    lifespan=lifespan,
    description="Historical AIS analytics, reproducible forecasting benchmarks, and transparent decision-support scenarios.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type"],
)


def dataset():
    if "df" not in STATE:
        raise HTTPException(
            503,
            "Dataset not built. Run scripts/build_dataset.py and scripts/train_benchmark.py.",
        )
    return STATE["df"]


def filtered(vessel_type="All", hour=23):
    df = dataset()
    df = df[df.timestamp.str[11:13].astype(int) <= hour]
    if vessel_type != "All":
        df = df[df.vessel_type == vessel_type]
    return df


@app.get("/api/health")
def health():
    return dict(
        status="ready" if "df" in STATE else "setup_required",
        model_ready=STATE.get("model") is not None,
        version="2.0.0",
    )


@lru_cache(maxsize=192)
def overview_cached(vessel_type, hour):
    df = filtered(vessel_type, hour)
    latest = df.sort_values("timestamp").groupby("mmsi", sort=False).tail(1)
    counts = (
        df.groupby("vessel_type")
        .agg(vessels=("mmsi", "nunique"), observations=("mmsi", "size"))
        .reset_index()
        .sort_values("vessels", ascending=False)
    )
    hourly = (
        df.assign(hour=df.timestamp.str[11:13])
        .groupby("hour")
        .agg(
            observations=("mmsi", "size"),
            vessels=("mmsi", "nunique"),
            speed=("speed", "mean"),
        )
        .reset_index()
    )
    hist, bins = np.histogram(df.speed, bins=[0, 0.5, 3, 6, 10, 15, 20, 30, 60])
    density = (
        df.groupby("h3")
        .agg(
            vessels=("mmsi", "nunique"),
            observations=("mmsi", "size"),
            speed=("speed", "mean"),
        )
        .reset_index()
        .sort_values("vessels", ascending=False)
    )
    cells = [dict(**r, boundary=h3.cell_to_boundary(r["h3"])) for r in records(density)]
    corr = (
        df[["speed", "lat", "lon", "storm_distance_nm", "length", "draft"]]
        .corr()
        .round(3)
    )
    return dict(
        metrics=dict(
            observations=len(df),
            vessels=len(latest),
            mean_speed=round(float(df.speed.mean()), 2) if len(df) else 0,
            moving=int((latest.speed >= 0.5).sum()),
            flagged=int(latest.anomaly.sum()) if "anomaly" in latest else 0,
            cells=len(cells),
        ),
        types=records(counts),
        hourly=records(hourly),
        histogram=[
            dict(bin=f"{bins[i]:g}–{bins[i+1]:g}", count=int(v))
            for i, v in enumerate(hist)
        ],
        fleet=(
            records(
                latest[
                    [
                        "mmsi",
                        "name",
                        "vessel_type",
                        "lat",
                        "lon",
                        "speed",
                        "course",
                        "timestamp",
                        "storm_distance_nm",
                        "anomaly",
                    ]
                ]
            )
            if "anomaly" in latest
            else []
        ),
        cells=cells,
        correlation=dict(
            columns=corr.columns.tolist(),
            values=json.loads(corr.to_json(orient="values")),
        ),
        scatter=records(
            df.sample(min(400, len(df)), random_state=42)[
                ["speed", "storm_distance_nm", "vessel_type"]
            ]
        ),
        manifest=STATE["manifest"],
        storm=STATE["storm"],
    )


@app.get("/api/overview")
def overview(vessel_type: str = "All", hour: int = Query(23, ge=0, le=23)):
    dataset()
    return overview_cached(vessel_type, hour)


@app.get("/api/vessels")
def vessels(
    q: str = Query("", max_length=100),
    vessel_type: str = "All",
    hour: int = Query(23, ge=0, le=23),
    page: int = Query(1, ge=1),
    limit: int = Query(12, ge=1, le=100),
    flagged: bool = False,
):
    df = (
        filtered(vessel_type, hour)
        .sort_values("timestamp")
        .groupby("mmsi", sort=False)
        .tail(1)
    )
    if q:
        df = df[
            df.name.str.contains(q, case=False, regex=False)
            | df.mmsi.str.contains(q, regex=False)
        ]
    if flagged:
        df = df[df.anomaly]
    df = df.sort_values(["speed", "mmsi"], ascending=[False, True])
    return dict(
        total=len(df),
        page=page,
        items=records(df.iloc[(page - 1) * limit : page * limit]),
    )


@app.get("/api/vessels/{mmsi}")
def vessel(mmsi: str, hour: int = Query(23, ge=0, le=23)):
    df = filtered(hour=hour)
    df = df[df.mmsi == mmsi].sort_values("timestamp")
    if df.empty:
        raise HTTPException(404, "Vessel not found in the selected historical window.")
    prediction = None
    if STATE.get("model") is not None:
        features = ["speed", "course_sin", "course_cos", "lat", "lon", "type_code"]
        prediction = round(
            float(np.clip(STATE["model"].predict(df[features].tail(1))[0], 0, 60)), 2
        )
    return dict(
        vessel=records(df.tail(1))[0],
        track=records(
            df[["timestamp", "lat", "lon", "speed", "storm_distance_nm", "anomaly"]]
        ),
        predicted_next_speed=prediction,
        prediction_note="Next observed speed estimate, trained on 2–30 minute intervals. This vessel may be in the training cohort; benchmark scores use held-out vessels.",
    )


@app.get("/api/benchmark")
def benchmark():
    dataset()
    if not STATE.get("benchmark"):
        raise HTTPException(503, "Run scripts/train_benchmark.py first.")
    return STATE["benchmark"]


class Scenario(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    name: str = Field("Untitled scenario", min_length=1, max_length=80)
    distance_nm: float = Field(300, gt=0, le=5000)
    speed: float = Field(14, ge=1, le=35)
    wind: float = Field(25, ge=0, le=150)
    waves: float = Field(2, ge=0, le=20)
    congestion: float = Field(35, ge=0, le=100)
    storm_distance_nm: float = Field(160, ge=0, le=2000)
    fuel_tons_day: float = Field(24, gt=0, le=500)
    fuel_price: float = Field(650, gt=0, le=3000)
    carbon_factor: float = Field(3.114, ge=2, le=4)


def evaluate(s: Scenario):
    components = [
        dict(factor="Wind exposure", points=round(min(s.wind / 64, 1) * 30, 2)),
        dict(factor="Wave exposure", points=round(min(s.waves / 8, 1) * 25, 2)),
        dict(factor="Traffic assumption", points=round(s.congestion * 0.2, 2)),
        dict(
            factor="Storm proximity",
            points=round(max(0, 1 - s.storm_distance_nm / 300) * 25, 2),
        ),
    ]
    risk = round(sum(x["points"] for x in components), 2)
    alternatives = []
    for label, speed_factor, distance_factor, weather_factor in [
        ("Maintain course", 1, 1, 1),
        ("Economy speed", 0.8, 1, 1),
        ("Illustrative detour", 1, 1.2, 0.55),
    ]:
        speed = s.speed * speed_factor
        hours = (
            s.distance_nm
            * distance_factor
            / speed
            * (1 + s.waves * 0.025 * weather_factor + s.congestion * 0.001)
        )
        fuel = (
            hours
            / 24
            * s.fuel_tons_day
            * (speed / 14) ** 3
            * (1 + s.waves * 0.04 * weather_factor)
        )
        alternatives.append(
            dict(
                name=label,
                speed=round(speed, 2),
                distance_nm=round(s.distance_nm * distance_factor, 2),
                hours=round(hours, 2),
                fuel_tons=round(fuel, 2),
                co2_tons=round(fuel * s.carbon_factor, 2),
                fuel_cost=round(fuel * s.fuel_price, 2),
                exposure_score=round(risk * weather_factor, 2),
            )
        )
    recommendation = (
        "Illustrative detour"
        if risk >= 60
        else "Economy speed" if risk < 35 else "Maintain course"
    )
    return dict(
        score=risk,
        level="High" if risk >= 60 else "Moderate" if risk >= 35 else "Low",
        components=components,
        alternatives=alternatives,
        recommendation=recommendation,
        explanation="Deterministic decision support: exposure ≥60 favors the hypothetical lower-exposure corridor; exposure <35 favors economy speed; otherwise maintain the baseline for review.",
        assumptions=[
            "Exposure is a weighted score, not a calibrated delay probability.",
            "Detour assumes 20% more distance and 45% less weather exposure; no navigable route is computed.",
            "Fuel scales with speed cubed relative to 14 knots; actual ship performance varies.",
            "CO₂ uses a configurable tonnes-CO₂/tonne-fuel factor; default 3.114 represents residual fuel.",
            "Fuel price is a user assumption, not a market quote.",
        ],
        trace=[
            dict(
                agent="Input validator", finding="All units and input ranges validated."
            ),
            dict(
                agent="Exposure analyst",
                finding=f"Weighted scenario exposure: {risk}/100.",
            ),
            dict(
                agent="Voyage estimator",
                finding="Compared three explicit speed/distance assumptions.",
            ),
            dict(
                agent="Decision policy",
                finding=f"{recommendation} proposed for human review. No vessel control action taken.",
            ),
        ],
    )


@app.post("/api/scenarios/evaluate")
def scenario_evaluate(s: Scenario):
    return evaluate(s)


@app.post("/api/scenarios", status_code=201)
def save_scenario(s: Scenario):
    dataset()
    result = evaluate(s)
    ident = str(uuid.uuid4())
    created = datetime.now(timezone.utc).isoformat()
    with sqlite3.connect(DB) as con:
        con.execute(
            "INSERT INTO scenarios VALUES (?,?,?,?,?)",
            (ident, created, s.name, s.model_dump_json(), json.dumps(result)),
        )
    return dict(
        id=ident, created=created, name=s.name, payload=s.model_dump(), result=result
    )


@app.get("/api/scenarios")
def scenarios():
    dataset()
    with sqlite3.connect(DB) as con:
        rows = con.execute(
            "SELECT * FROM scenarios ORDER BY created DESC LIMIT 100"
        ).fetchall()
    return [
        dict(
            id=r[0],
            created=r[1],
            name=r[2],
            payload=json.loads(r[3]),
            result=json.loads(r[4]),
        )
        for r in rows
    ]


@app.delete("/api/scenarios/{ident}", status_code=204)
def delete_scenario(ident: str):
    dataset()
    with sqlite3.connect(DB) as con:
        cursor = con.execute("DELETE FROM scenarios WHERE id=?", (ident,))
        if not cursor.rowcount:
            raise HTTPException(404, "Scenario not found.")
    return Response(status_code=204)


@app.get("/api/export")
def export(vessel_type: str = "All", hour: int = Query(23, ge=0, le=23)):
    df = filtered(vessel_type, hour).copy()
    for col in df.select_dtypes(include=["object", "str"]).columns:
        df[col] = df[col].map(
            lambda x: (
                "'" + x
                if isinstance(x, str) and x.startswith(("=", "+", "-", "@", "\t", "\r"))
                else x
            )
        )
    return Response(
        df.to_csv(index=False),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="ais_observations.csv"'},
    )


if (ROOT / "frontend/dist").exists():
    app.mount(
        "/", StaticFiles(directory=ROOT / "frontend/dist", html=True), name="frontend"
    )
