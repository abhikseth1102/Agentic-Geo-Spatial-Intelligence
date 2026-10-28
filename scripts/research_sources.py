"""Retrieve bibliographic metadata; does not claim full-text review."""

import json
import urllib.request
import urllib.parse
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/research"
OUT.mkdir(parents=True, exist_ok=True)
queries = [
    "AIS ship trajectory prediction",
    "AIS maritime anomaly detection",
    "automatic identification system maritime data quality",
    "ship fuel consumption machine learning prediction",
    "maritime vessel traffic AIS review",
]


def fetch(q):
    url = "https://api.crossref.org/works?" + urllib.parse.urlencode(
        {
            "query.title": q,
            "filter": "type:journal-article,from-pub-date:2020-01-01,until-pub-date:2025-12-31",
            "rows": 30,
        }
    )
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "MaritimeStudentResearch/1.0 (bibliography verification)"
        },
    )
    for attempt in range(5):
        try:
            data = json.load(urllib.request.urlopen(req, timeout=60))
            break
        except Exception:
            if attempt == 4:
                raise
            time.sleep(5 * (attempt + 1))
    return q, data["message"]["items"]


all_items = []
with ThreadPoolExecutor(max_workers=1) as pool:
    for q, items in pool.map(fetch, queries):
        for item in items:
            item["research_query"] = q
            all_items.append(item)
(OUT / "crossref_candidates.json").write_text(
    json.dumps(all_items, indent=2), encoding="utf-8"
)
seen = set()
selected = []
for q in queries:
    group = [i for i in all_items if i["research_query"] == q]
    count = 0
    for i in group:
        title = i.get("title", [""])[0]
        if i["DOI"] in seen or not i.get("author") or not i.get("container-title"):
            continue
        if not any(
            t in title.lower()
            for t in ["ship", "vessel", "maritime", "ais", "automatic identification"]
        ):
            continue
        if not any(
            t in i.get("publisher", "").lower()
            for t in [
                "elsevier",
                "springer",
                "ieee",
                "wiley",
                "taylor",
                "mdpi",
                "sage",
                "ios",
                "world scientific",
            ]
        ):
            continue
        seen.add(i["DOI"])
        selected.append(i)
        count += 1
        if count == 5:
            break
(OUT / "references.json").write_text(json.dumps(selected, indent=2), encoding="utf-8")
for j, i in enumerate(selected, 1):
    print(
        j,
        i["title"][0],
        "|",
        i["DOI"],
        "|",
        i["container-title"][0],
        "| abstract:",
        bool(i.get("abstract")),
    )
