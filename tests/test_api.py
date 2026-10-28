"""Behavioral checks for the research API and scenario contract."""

import json
import math
import sqlite3
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from backend import main


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    main.DB = tmp_path_factory.mktemp("db") / "test.sqlite"
    with TestClient(main.app) as c:
        yield c


def test_health_and_dataset_counts(client):
    assert client.get("/api/health").json()["status"] == "ready"
    d = client.get("/api/overview").json()
    assert d["metrics"]["observations"] == d["manifest"]["observations"]
    assert len(d["fleet"]) == d["manifest"]["vessels"]
    assert sum(x["count"] for x in d["histogram"]) == d["metrics"]["observations"]
    assert sum(x["observations"] for x in d["hourly"]) == d["metrics"]["observations"]
    assert sum(x["observations"] for x in d["cells"]) == d["metrics"]["observations"]


def test_deployed_frontend_cors(client):
    origin = "https://agentic-geo-spatial-intelligence.vercel.app"
    headers = {
        "Origin": origin,
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "content-type",
    }
    response = client.options("/api/overview", headers=headers)
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin
    response = client.get("/api/overview", headers={"Origin": origin})
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin
    headers["Origin"] = "https://unrelated.example"
    response = client.options("/api/overview", headers=headers)
    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers



def test_filters_and_replay(client):
    data = client.get("/api/overview?vessel_type=Cargo&hour=4").json()
    assert all(
        x["vessel_type"] == "Cargo" and int(x["timestamp"][11:13]) <= 4
        for x in data["fleet"]
    )
    assert (
        len(data["fleet"]) <= client.get("/api/overview").json()["metrics"]["vessels"]
    )
    assert client.get("/api/overview?hour=24").status_code == 422


def test_empty_search_and_literal_regex(client):
    assert client.get("/api/vessels?q=%5Bno-such-vessel%5D").json()["total"] == 0
    assert client.get("/api/vessels?page=0").status_code == 422
    assert client.get("/api/vessels/invalid").status_code == 404


def test_vessel_detail_is_consistent(client):
    row = client.get("/api/vessels?limit=1").json()["items"][0]
    d = client.get("/api/vessels/" + row["mmsi"]).json()
    assert d["vessel"]["mmsi"] == row["mmsi"]
    assert len(d["track"]) > 0
    assert 0 <= d["predicted_next_speed"] <= 60
    assert d["track"] == sorted(d["track"], key=lambda x: x["timestamp"])


def test_model_split_and_metrics(client):
    d = client.get("/api/benchmark").json()
    assert d["overlapping_vessels"] == 0
    assert len(d["results"]) == 5
    assert all(x["mae"] >= 0 and x["rmse"] >= x["mae"] for x in d["results"])


@pytest.mark.parametrize(
    "payload",
    [
        {"speed": 0},
        {"distance_nm": 0},
        {"wind": -1},
        {"waves": 21},
        {"congestion": 101},
        {"fuel_price": 0},
        {"invented_feature": 1},
        {"name": ""},
    ],
)
def test_scenario_rejects_invalid_inputs(client, payload):
    assert client.post("/api/scenarios/evaluate", json=payload).status_code == 422


def test_scenario_monotonic_exposure_and_units(client):
    calm = client.post(
        "/api/scenarios/evaluate",
        json={"wind": 0, "waves": 0, "congestion": 0, "storm_distance_nm": 600},
    ).json()
    storm = client.post(
        "/api/scenarios/evaluate",
        json={"wind": 100, "waves": 10, "congestion": 100, "storm_distance_nm": 0},
    ).json()
    assert calm["score"] == 0 and storm["score"] == 100
    assert storm["recommendation"] == "Illustrative detour"
    a = calm["alternatives"][0]
    assert a["hours"] == round(300 / 14, 2)
    assert abs(a["co2_tons"] - a["fuel_tons"] * 3.114) < 0.03
    assert calm["alternatives"][1]["fuel_tons"] < a["fuel_tons"]
    assert calm["alternatives"][1]["hours"] > a["hours"]


def test_save_load_delete_round_trip(client):
    payload = {"name": "Test experiment", "wind": 64, "waves": 5}
    response = client.post("/api/scenarios", json=payload)
    assert response.status_code == 201
    saved = response.json()
    found = client.get("/api/scenarios").json()[0]
    assert found == saved
    assert client.delete("/api/scenarios/" + saved["id"]).status_code == 204
    assert client.delete("/api/scenarios/" + saved["id"]).status_code == 404


def test_export_respects_filters(client):
    response = client.get("/api/export?vessel_type=Cargo&hour=0")
    assert (
        response.status_code == 200 and "text/csv" in response.headers["content-type"]
    )
    import csv, io

    rows = list(csv.DictReader(io.StringIO(response.text)))
    assert rows and all(
        r["vessel_type"] == "Cargo" and r["timestamp"][11:13] == "00" for r in rows
    )


def test_hurricane_alignment_and_fingerprint():
    df = main.STATE["df"]
    # Idalia was near Cuba on 28 August, not at its eventual Florida landfall.
    assert df.storm_lat.between(19, 24).all()
    import hashlib

    manifest = json.loads((main.DATA / "manifest.json").read_text())
    assert (
        manifest["sha256"]
        == hashlib.sha256((main.DATA / "observations.csv").read_bytes()).hexdigest()
    )
