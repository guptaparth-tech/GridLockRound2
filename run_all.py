"""ParkPulse v2 — end-to-end pipeline (Solutions A-E).

Usage: python run_all.py     # runs on Theme1/dataset.csv
Then:  streamlit run app.py

Order: data pipeline -> C impact proxy -> A de-biased demand -> B/D near-repeat
-> E archetypes -> integrate into one master cell table for the demo.
"""
import os
import time

import pandas as pd

from src import data_pipeline, impact_proxy, demand_debias, near_repeat, archetypes

PROC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "outputs", "processed")


def integrate():
    """Merge per-cell outputs of C, A, E into one master table for the app."""
    cis = pd.read_csv(os.path.join(PROC, "cis_cells.csv"))
    dem = pd.read_csv(os.path.join(PROC, "demand_cells.csv"))
    arch = pd.read_csv(os.path.join(PROC, "archetypes.csv"))

    for d in (cis, dem):
        d["cell"] = d["gx"].astype(str) + "_" + d["gy"].astype(str)
    master = cis[["cell", "name", "lat", "lon", "top_station", "CIS", "CIS_rank",
                  "n_violations", "road_class", "dominant_poi", "peak_hour"]].merge(
        dem[["cell", "demand_index", "blind_spot", "reliable", "devices",
             "evening_share", "observed"]], on="cell", how="left")
    master = master.merge(arch[["cell", "archetype", "intervention"]], on="cell", how="left")
    master["archetype"] = master["archetype"].fillna("(low-volume cell)")
    master.to_csv(os.path.join(PROC, "parkpulse_cells.csv"), index=False)
    print(f"[integrate] master table: {len(master)} cells -> parkpulse_cells.csv")
    return master


def main():
    t0 = time.time()
    print("=" * 60, "\n1/5 DATA PIPELINE"); data_pipeline.load_clean()
    print("=" * 60, "\n2/5 [C] IMPACT PROXY"); impact_proxy.run()
    print("=" * 60, "\n3/5 [A] DE-BIASED DEMAND + BLIND-SPOTS"); demand_debias.run()
    print("=" * 60, "\n4/5 [B/D] NEAR-REPEAT + VEHICLE HAZARD"); near_repeat.run()
    print("=" * 60, "\n5/5 [E] ARCHETYPES -> POLICY"); archetypes.run()
    print("=" * 60, "\nINTEGRATE"); integrate()
    print("=" * 60, f"\nDONE in {time.time()-t0:.1f}s. Run: streamlit run app.py")


if __name__ == "__main__":
    main()
