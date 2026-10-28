"""Reproducible AIS extraction, audit, and retrospective storm alignment."""

from pathlib import Path
import hashlib
import json
import sys
import numpy as np
import pandas as pd
import h3

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "atlas"
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT))


def distance_nm(lat, lon, lat2, lon2):
    a, b, c, d = map(np.radians, [lat, lon, lat2, lon2])
    hav = np.sin((c - a) / 2) ** 2 + np.cos(a) * np.cos(c) * np.sin((d - b) / 2) ** 2
    return 3440.065 * 2 * np.arcsin(np.sqrt(np.clip(hav, 0, 1)))


def storm_track():
    lines = (ROOT / "data/hurdat2.txt").read_text().splitlines()
    start = next(i for i, x in enumerate(lines) if x.startswith("AL102023"))
    count = int(lines[start].split(",")[2])
    rows = []
    for line in lines[start + 1 : start + count + 1]:
        p = [v.strip() for v in line.split(",")]
        rows.append(
            dict(
                timestamp=pd.to_datetime(p[0] + p[1], format="%Y%m%d%H%M").isoformat(),
                lat=float(p[4][:-1]) * (-1 if p[4][-1] == "S" else 1),
                lon=float(p[5][:-1]) * (-1 if p[5][-1] == "W" else 1),
                wind_knots=int(p[6]),
                status=p[3],
            )
        )
    return rows


def main():
    source = ROOT / "data/AIS_2023_08_28.csv"
    cols = [
        "MMSI",
        "BaseDateTime",
        "LAT",
        "LON",
        "SOG",
        "COG",
        "VesselName",
        "VesselType",
        "Length",
        "Width",
        "Draft",
        "Status",
    ]
    raw_count = region_count = sample_count = 0
    chunks = []
    for chunk in pd.read_csv(source, usecols=cols, chunksize=250000, low_memory=False):
        raw_count += len(chunk)
        region = chunk[chunk.LAT.between(20, 35) & chunk.LON.between(-90, -75)].copy()
        region_count += len(region)
        # Deterministic vessel-level cohort: retains full trajectories, not random pings.
        region = region[pd.to_numeric(region.MMSI, errors="coerce").mod(13).eq(0)]
        sample_count += len(region)
        chunks.append(region)
    df = pd.concat(chunks, ignore_index=True)
    missing = {c: int(df[c].isna().sum()) for c in cols}
    df["BaseDateTime"] = pd.to_datetime(df.BaseDateTime, errors="coerce")
    invalid = (
        df.BaseDateTime.isna()
        | ~df.SOG.between(0, 60)
        | ~df.COG.between(0, 360, inclusive="left")
        | df.MMSI.isna()
    )
    invalid_count = int(invalid.sum())
    df = df[~invalid].copy()
    duplicates = int(df.duplicated(["MMSI", "BaseDateTime"]).sum())
    df = df.drop_duplicates(["MMSI", "BaseDateTime"]).sort_values(
        ["MMSI", "BaseDateTime"]
    )
    df["bucket"] = df.BaseDateTime.dt.floor("5min")
    before = len(df)
    df = df.drop_duplicates(["MMSI", "bucket"], keep="first").drop(columns="bucket")
    df = df.rename(
        columns=dict(
            MMSI="mmsi",
            BaseDateTime="timestamp",
            LAT="lat",
            LON="lon",
            SOG="speed",
            COG="course",
            VesselName="name",
            VesselType="type_code",
            Length="length",
            Width="width",
            Draft="draft",
            Status="nav_status",
        )
    )
    df["mmsi"] = df.mmsi.astype(int).astype(str)
    df["name"] = df.name.fillna("Unnamed vessel")
    df["type_code"] = df.type_code.fillna(0).astype(int)

    def category(n):
        if 70 <= n <= 79:
            return "Cargo"
        if 80 <= n <= 89:
            return "Tanker"
        if 60 <= n <= 69:
            return "Passenger"
        return {
            30: "Fishing",
            31: "Tug",
            32: "Tug",
            36: "Sailing",
            37: "Pleasure",
            52: "Tug",
        }.get(n, "Other")

    df["vessel_type"] = df.type_code.map(category)
    track = storm_track()
    st = pd.DataFrame(track)
    st["seconds"] = pd.to_datetime(st.timestamp).astype("int64") / 1e9
    times = df.timestamp.astype("int64") / 1e9
    df["storm_lat"] = np.interp(times, st.seconds, st.lat)
    df["storm_lon"] = np.interp(times, st.seconds, st.lon)
    df["storm_distance_nm"] = distance_nm(
        df.lat, df.lon, df.storm_lat, df.storm_lon
    ).round(2)
    df["h3"] = [h3.latlng_to_cell(a, b, 5) for a, b in zip(df.lat, df.lon)]
    df["course_sin"] = np.sin(np.radians(df.course))
    df["course_cos"] = np.cos(np.radians(df.course))
    grouped = df.groupby("mmsi", sort=False)
    df["next_speed"] = grouped.speed.shift(-1)
    df["next_minutes"] = (
        grouped.timestamp.shift(-1) - df.timestamp
    ).dt.total_seconds() / 60
    df["timestamp"] = df.timestamp.dt.strftime("%Y-%m-%dT%H:%M:%S")
    df.to_csv(OUT / "observations.csv", index=False)
    (OUT / "storm.json").write_text(json.dumps(track, indent=2))
    manifest = dict(
        source=source.name,
        source_url="https://coast.noaa.gov/htdata/CMSP/AISDataHandler/2023/index.html",
        source_bytes=source.stat().st_size,
        raw_rows=raw_count,
        region_rows=region_count,
        cohort_rows=sample_count,
        invalid_rows=invalid_count,
        duplicate_rows=duplicates,
        resampled_rows_removed=before - len(df),
        observations=len(df),
        vessels=int(df.mmsi.nunique()),
        missing_fields=missing,
        start=df.timestamp.min(),
        end=df.timestamp.max(),
        sampling="Gulf / Florida bounding box 20–35 N, 90–75 W; MMSI modulo 13 = 0; first valid observation per vessel per 5-minute bin.",
        caveats=[
            "Historical snapshot, not live tracking.",
            "Vessel cohort is deterministic but not a statistically representative fleet sample.",
            "HURDAT2 is retrospective best-track data, not a forecast available at observation time.",
            "No arrival-time or verified delay labels are available.",
            "AIS messages are self-reported and may contain errors.",
        ],
        sha256=hashlib.sha256((OUT / "observations.csv").read_bytes()).hexdigest(),
    )
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
