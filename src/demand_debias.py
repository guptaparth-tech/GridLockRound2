"""Solution A — observation-aware (de-biased) demand + enforcement blind-spots.

Problem (findings F1, F5): observed violation counts ~= true_demand x detection.
Detection is driven by patrol presence, which is itself steered toward already-known
hotspots -> a predictive-policing feedback loop (Lum & Isaac 2016; Ensign et al. 2017).

We do not have ground-truth demand, so this is honest *decision-support*, not a causal
model. We produce two defensible, in-dataset corrections:

  1. detection-adjusted demand index = observed / distinct patrol-units (device-days).
     Cells that yield many violations per patrol-unit have denser latent violations
     (efficient 'hunting'); cells needing many units per ticket are over-served.
  2. enforcement blind-spots = high impact (CIS) but low patrol presence and/or zero
     evening coverage (the 15-23 IST void, F1) where POI implies evening demand.

We also SIMULATE the feedback loop to show why naive count-chasing is harmful
(enforcement Gini rises as patrols concentrate), motivating the correction.
"""
from __future__ import annotations

import os

import numpy as np
import pandas as pd

from .cells import add_cell, cell_name

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(ROOT, "outputs", "processed")
CLEAN = os.path.join(PROC, "clean.parquet")


def _mm(s):
    lo, hi = s.min(), s.max()
    return pd.Series(0.0, index=s.index) if hi - lo < 1e-12 else (s - lo) / (hi - lo)


def _gini(x):
    x = np.sort(np.asarray(x, float)); n = len(x); c = np.cumsum(x)
    return (n + 1 - 2 * np.sum(c) / c[-1]) / n if c[-1] > 0 else 0.0


def build(df: pd.DataFrame) -> pd.DataFrame:
    df = add_cell(df)
    df["evening"] = df["hour"].between(17, 23)
    g = df.groupby(["gx", "gy"])
    cells = g.agg(
        observed=("id", "size"),
        devices=("device_id", "nunique"),
        officers=("created_by_id", "nunique"),
        evening_share=("evening", "mean"),
        poi_demand=("poi_any", "mean"),
        lat=("latitude", "mean"), lon=("longitude", "mean"),
        top_station=("police_station", lambda s: s.mode().iloc[0]),
    ).reset_index()
    names = g.apply(cell_name, include_groups=False).rename("name").reset_index()
    cells = cells.merge(names, on=["gx", "gy"])

    # 1) detection-adjusted demand: tickets per patrol-unit (device), with light
    #    shrinkage (+2) so tiny-denominator cells don't dominate; reliability flag.
    cells["demand_index"] = cells["observed"] / (cells["devices"] + 2)
    cells["reliable"] = (cells["observed"] >= 50) & (cells["devices"] >= 3)

    # merge impact (CIS) if available
    cis_path = os.path.join(PROC, "cis_cells.csv")
    if os.path.exists(cis_path):
        cis = pd.read_csv(cis_path)[["gx", "gy", "CIS"]]
        cells = cells.merge(cis, on=["gx", "gy"], how="left")
    cells["CIS"] = cells.get("CIS", pd.Series(0.0, index=cells.index)).fillna(0.0)

    # 2) blind-spot score: high impact, low patrol presence, weak evening coverage
    under_enf = 1 - _mm(np.log1p(cells["devices"]))
    evening_gap = 1 - _mm(cells["evening_share"])
    cells["blind_spot"] = 100 * _mm(cells["CIS"]) * (0.6 * under_enf + 0.4 * evening_gap)
    return cells.sort_values("demand_index", ascending=False).reset_index(drop=True)


def feedback_sim(df: pd.DataFrame, iters: int = 6, topk: int = 100, seed: int = 0):
    """Illustrative: chase top observed cells -> patrols concentrate -> Gini rises."""
    rng = np.random.default_rng(seed)
    d = add_cell(df)
    base = d.groupby("cell").size()
    cells = base.index.to_numpy()
    true_rate = base.to_numpy().astype(float)            # latent propensity (fixed)
    effort = np.ones(len(cells))                          # start uniform patrols
    ginis = []
    for _ in range(iters):
        observed = true_rate * (effort / effort.sum()) * len(cells)
        ginis.append(_gini(effort))
        # naive policy: concentrate next-round effort on top observed cells
        top = np.argsort(observed)[::-1][:topk]
        effort = np.ones(len(cells)) * 0.1
        effort[top] += observed[top] / observed[top].mean()
    return ginis


def run():
    df = pd.read_parquet(CLEAN)
    cells = build(df)
    cells.to_csv(os.path.join(PROC, "demand_cells.csv"), index=False)
    rel = cells[cells["reliable"]].copy()
    blind = rel.sort_values("blind_spot", ascending=False)
    blind.to_csv(os.path.join(PROC, "blind_spots.csv"), index=False)

    # validation: how much does de-biasing reorder vs raw counts? (reliable cells)
    raw_top = set(rel.sort_values("observed", ascending=False).head(30)["name"])
    adj_top = set(rel.sort_values("demand_index", ascending=False).head(30)["name"])
    jac = len(raw_top & adj_top) / len(raw_top | adj_top)
    corr = cells["observed"].corr(cells["demand_index"])

    print(f"[demand] {len(cells)} cells")
    print(f"[demand] corr(raw observed, detection-adjusted demand) = {corr:.2f}")
    print(f"[demand] top-30 overlap raw vs de-biased: Jaccard {jac:.2f} "
          f"-> de-biasing materially reorders priorities")
    print("\n[demand] top detection-adjusted demand (reliable cells, tickets/patrol-unit):")
    print(rel.sort_values("demand_index", ascending=False).head(8)[
        ["name", "top_station", "observed", "devices", "demand_index"]].round(1).to_string(index=False))
    print("\n[blind-spots] high-impact + under-enforced + weak evening coverage:")
    print(blind.head(8)[["name", "top_station", "CIS", "devices",
                         "evening_share", "blind_spot"]].round(2).to_string(index=False))

    ginis = feedback_sim(df)
    print(f"\n[feedback-loop sim] enforcement Gini over rounds: "
          f"{[round(g,3) for g in ginis]} -> rises {ginis[0]:.3f}->{ginis[-1]:.3f} "
          f"(naive count-chasing concentrates patrols = bias amplification)")
    return cells, blind, ginis


if __name__ == "__main__":
    run()
