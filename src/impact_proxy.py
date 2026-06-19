"""Solution C — in-dataset Congestion-Impact Score (refined).

No measured congestion exists, so impact is a transparent composite built ONLY from
in-dataset signals (see findings F2/F3):
  density      log volume of violations in the cell
  recurrence   distinct active days (chronic vs one-off)
  road_class   road-hierarchy weight parsed from address (main road/cross/ring/flyover)
  poi_demand   share of violations tagged to a POI trip-generator (market/metro/mall/...)
  severity     mean vehicle severity (bigger vehicles block more)
  criticality  mean violation criticality (footpath/main-road/junction)

CIS = 100 * sum(w_i * minmax_i). Weights explicit + sensitivity-tested.
"""
from __future__ import annotations

import os

import numpy as np
import pandas as pd

from .cells import add_cell, cell_name

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(ROOT, "outputs", "processed")
CLEAN = os.path.join(PROC, "clean.parquet")

WEIGHTS = {
    "density": 0.25, "recurrence": 0.20, "road_class": 0.15,
    "poi_demand": 0.15, "severity": 0.10, "criticality": 0.15,
}
POI_COLS = ["poi_market", "poi_metro", "poi_mall", "poi_hospital",
            "poi_school", "poi_transit", "poi_techpark"]


def _mm(s):
    lo, hi = s.min(), s.max()
    return pd.Series(0.0, index=s.index) if hi - lo < 1e-12 else (s - lo) / (hi - lo)


def build_cells(df: pd.DataFrame) -> pd.DataFrame:
    df = add_cell(df)
    g = df.groupby(["gx", "gy"])
    cells = g.agg(
        n_violations=("id", "size"),
        n_days_active=("date", "nunique"),
        road_class=("road_weight", "mean"),
        poi_demand=("poi_any", "mean"),
        severity=("vehicle_severity", "mean"),
        criticality=("violation_criticality", "mean"),
        lat=("latitude", "mean"), lon=("longitude", "mean"),
        top_station=("police_station", lambda s: s.mode().iloc[0]),
        peak_hour=("hour", lambda s: int(s.mode().iloc[0])),
    ).reset_index()
    cells["dominant_poi"] = g[POI_COLS].sum().reset_index(drop=True).idxmax(axis=1).where(
        g[POI_COLS].sum().reset_index(drop=True).max(axis=1) > 0, "none")
    names = g.apply(cell_name, include_groups=False).rename("name").reset_index()
    return cells.merge(names, on=["gx", "gy"])


def score(cells: pd.DataFrame, weights=None) -> pd.DataFrame:
    w = weights or WEIGHTS
    cells = cells.copy()
    scaled = pd.DataFrame({
        "density": _mm(np.log1p(cells["n_violations"])),
        "recurrence": _mm(cells["n_days_active"]),
        "road_class": _mm(cells["road_class"]),
        "poi_demand": _mm(cells["poi_demand"]),
        "severity": _mm(cells["severity"]),
        "criticality": _mm(cells["criticality"]),
    })
    cells["CIS"] = 100 * sum(w[k] * scaled[k] for k in w)
    cells["CIS_rank"] = cells["CIS"].rank(ascending=False, method="first").astype(int)
    return cells.sort_values("CIS", ascending=False).reset_index(drop=True)


def sensitivity(cells, top_n=30):
    base = set(score(cells).head(top_n)["name"])
    scen = {
        "equal": {k: 1 / len(WEIGHTS) for k in WEIGHTS},
        "density_heavy": {**WEIGHTS, "density": 0.45, "poi_demand": 0.05, "road_class": 0.05},
        "impact_heavy": {**WEIGHTS, "road_class": 0.30, "criticality": 0.25, "density": 0.10},
    }
    rows = []
    for name, w in scen.items():
        tot = sum(w.values()); w = {k: v / tot for k, v in w.items()}
        alt = set(score(cells, w).head(top_n)["name"])
        rows.append({"scenario": name, "jaccard": round(len(base & alt) / len(base | alt), 3)})
    return pd.DataFrame(rows)


def run():
    df = pd.read_parquet(CLEAN)
    cells = build_cells(df)
    scored = score(cells)
    scored.to_csv(os.path.join(PROC, "cis_cells.csv"), index=False)
    print(f"[impact] scored {len(scored)} cells")
    print(scored[["CIS_rank", "name", "top_station", "CIS", "n_violations",
                  "road_class", "dominant_poi"]].head(12).to_string(index=False))
    print("\n[impact] weight sensitivity (top-30 Jaccard vs base):")
    print(sensitivity(cells).to_string(index=False))
    return scored


if __name__ == "__main__":
    run()
