"""Solution E — functional archetypes -> policy interventions.

Clusters actionable cells on demand-side composition (vehicle mix, violation mix,
weekend ratio; see finding F4), labels each archetype, and maps it to a concrete
intervention (benchmarked to SFpark-style curb management). Output: archetype +
recommendation per cell.
"""
from __future__ import annotations

import os

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

from .cells import add_cell

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(ROOT, "outputs", "processed")
CLEAN = os.path.join(PROC, "clean.parquet")
MIN_VIOL = 200

TWO = ["SCOOTER", "MOTOR CYCLE", "MOPED"]
COMM = ["LGV", "HGV", "LORRY/GOODS VEHICLE", "GOODS AUTO", "TEMPO", "MAXI-CAB",
        "PRIVATE BUS", "BUS (BMTC/KSRTC)", "VAN"]

# label rule -> (archetype name, recommended intervention)
INTERVENTIONS = {
    "footpath_encroachment": ("Footpath / main-road encroachment",
        "Physical deterrents (bollards/chains) + sustained pedestrian-priority enforcement"),
    "loading_corridor": ("Commercial / loading corridor",
        "Designated timed loading bays + off-peak delivery windows; enforce during peak"),
    "two_wheeler_spillover": ("Two-wheeler spillover",
        "Add two-wheeler parking supply; mark legal bays near transit/markets"),
    "cbd_car": ("CBD car parking",
        "Occupancy-responsive paid parking (SFpark-style) + clear signage"),
}


def _label(row):
    if row["pct_footpath"] > 0.05 or row["pct_mainroad"] > 0.07:
        return "footpath_encroachment"
    if row["pct_commercial"] > 0.15 or row["pct_auto"] > 0.15:
        return "loading_corridor"
    if row["pct_two_wheeler"] > 0.5:
        return "two_wheeler_spillover"
    return "cbd_car"


def build(df: pd.DataFrame) -> pd.DataFrame:
    import ast
    import json

    def pl(x):
        try:
            return json.loads(x)
        except Exception:
            try:
                return ast.literal_eval(x)
            except Exception:
                return []
    # primary_violation already parsed in pipeline; reconstruct mix from it + vehicle
    df = add_cell(df)
    df["veh"] = df["vehicle_type"]
    g = df.groupby("cell")
    big = g.size()
    cells = big[big >= MIN_VIOL].index
    d = df[df["cell"].isin(cells)]
    g = d.groupby("cell")
    F = g.apply(lambda x: pd.Series({
        "pct_two_wheeler": x["veh"].isin(TWO).mean(),
        "pct_commercial": x["veh"].isin(COMM).mean(),
        "pct_car": x["veh"].eq("CAR").mean(),
        "pct_auto": x["veh"].eq("PASSENGER AUTO").mean(),
        "pct_footpath": x["primary_violation"].eq("PARKING ON FOOTPATH").mean(),
        "pct_mainroad": x["primary_violation"].eq("PARKING IN A MAIN ROAD").mean(),
        "weekend_ratio": x["is_weekend"].mean(),
        "n": len(x),
    }), include_groups=False)

    # unsupervised structure (reported) + interpretable rule labels (used)
    feat = ["pct_two_wheeler", "pct_commercial", "pct_car", "pct_auto",
            "pct_footpath", "pct_mainroad", "weekend_ratio"]
    X = StandardScaler().fit_transform(F[feat])
    km = KMeans(4, n_init=10, random_state=0).fit(X)
    sil = silhouette_score(X, km.labels_)
    F["kmeans_cluster"] = km.labels_
    F["archetype_key"] = F.apply(_label, axis=1)
    F["archetype"] = F["archetype_key"].map(lambda k: INTERVENTIONS[k][0])
    F["intervention"] = F["archetype_key"].map(lambda k: INTERVENTIONS[k][1])
    return F.reset_index(), sil


def run():
    df = pd.read_parquet(CLEAN)
    F, sil = build(df)
    F.to_csv(os.path.join(PROC, "archetypes.csv"), index=False)
    print(f"[archetypes] {len(F)} actionable cells | kmeans silhouette={sil:.3f}")
    print(F["archetype"].value_counts().to_string())
    print("\n[archetypes] sample assignments:")
    print(F.sort_values("n", ascending=False).head(8)[
        ["cell", "archetype", "n", "intervention"]].to_string(index=False))
    return F


if __name__ == "__main__":
    run()
