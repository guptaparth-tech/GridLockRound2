"""Solution B/D — near-repeat space-time risk + vehicle recidivism hazard.

Grounded in findings F6/F7 and the near-repeat literature (Townsley 2003; Johnson &
Bowers 2004). Two models, each validated on a held-out time split (no leakage):

  B. Cell short-horizon risk: a self-exciting (decayed) recent-event intensity per
     ~500m cell. Validated by whether it predicts next-7-day activity vs a static
     baseline (total historical count). Reported honestly — for persistent parking
     hotspots the static baseline is strong, so we show the *added* lift.

  D. Vehicle recidivism hazard: logistic model predicting whether a known repeat
     vehicle re-offends within 30 days, from frequency/recency/spread features.
     Output = a ranked re-offense watchlist (methodology; plates are anonymised).
"""
from __future__ import annotations

import os

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

from .cells import add_cell

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(ROOT, "outputs", "processed")
CLEAN = os.path.join(PROC, "clean.parquet")

CUTOFF = pd.Timestamp("2024-03-01", tz="UTC")
TAU_DAYS = 14.0       # self-exciting decay
HORIZON_CELL = 7      # days
HORIZON_VEH = 30      # days


def _load():
    df = pd.read_parquet(CLEAN)
    df["ts"] = pd.to_datetime(df["created_ist"], utc=True)
    return df


# ----------------------------------------------------------- B: cell risk
def cell_risk(df: pd.DataFrame):
    df = add_cell(df)
    train = df[df["ts"] <= CUTOFF]
    test = df[(df["ts"] > CUTOFF) & (df["ts"] <= CUTOFF + pd.Timedelta(days=HORIZON_CELL))]

    age = (CUTOFF - train["ts"]).dt.total_seconds() / 86400.0
    train = train.assign(decay=np.exp(-age / TAU_DAYS))
    risk = train.groupby("cell")["decay"].sum().rename("risk")
    base = train.groupby("cell").size().rename("base_count")
    feat = pd.concat([risk, base], axis=1).fillna(0)
    feat["target"] = feat.index.isin(test["cell"].unique()).astype(int)

    auc_risk = roc_auc_score(feat["target"], feat["risk"])
    auc_base = roc_auc_score(feat["target"], feat["base_count"])
    # combined (recency + volume)
    feat["combo"] = feat["risk"].rank() + feat["base_count"].rank()
    auc_combo = roc_auc_score(feat["target"], feat["combo"])
    feat.sort_values("risk", ascending=False).to_csv(os.path.join(PROC, "cell_risk.csv"))
    return dict(auc_base=auc_base, auc_risk=auc_risk, auc_combo=auc_combo,
                n_cells=len(feat), pos_rate=feat["target"].mean())


# ----------------------------------------------------------- D: vehicle hazard
def vehicle_hazard(df: pd.DataFrame):
    df = add_cell(df).sort_values(["plate", "ts"])
    hist = df[df["ts"] <= CUTOFF]
    fut = df[(df["ts"] > CUTOFF) & (df["ts"] <= CUTOFF + pd.Timedelta(days=HORIZON_VEH))]

    counts = hist.groupby("plate").size()
    cand = counts[counts >= 2].index            # known repeat vehicles at cutoff
    h = hist[hist["plate"].isin(cand)]
    g = h.groupby("plate")
    feats = pd.DataFrame({
        "prior_count": g.size(),
        "days_since_last": (CUTOFF - g["ts"].max()).dt.total_seconds() / 86400.0,
        "mean_gap": g["ts"].apply(lambda s: s.diff().dt.total_seconds().mean() / 86400.0),
        "distinct_cells": g["cell"].nunique(),
        "mean_severity": g["vehicle_severity"].mean(),
    }).fillna({"mean_gap": 999})
    feats["target"] = feats.index.isin(fut["plate"].unique()).astype(int)

    X = feats[["prior_count", "days_since_last", "mean_gap", "distinct_cells", "mean_severity"]]
    y = feats["target"]
    # cross-sectional prediction at cutoff: features use only pre-cutoff data, target
    # uses post-cutoff -> a random candidate split is leakage-free and avoids the
    # distribution shift of splitting by recency.
    from sklearn.model_selection import train_test_split
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.3, random_state=0, stratify=y)
    model = LogisticRegression(max_iter=1000, class_weight="balanced")
    model.fit(Xtr, ytr)
    p = model.predict_proba(Xte)[:, 1]
    auc = roc_auc_score(yte, p)

    # precision@top-k vs base rate
    k = max(1, int(0.1 * len(Xte)))
    topk = pd.Series(p, index=Xte.index).sort_values(ascending=False).head(k).index
    prec_at_k = yte.loc[topk].mean()

    # watchlist: score all candidates, attach modal location + expected window
    feats["risk"] = model.predict_proba(X)[:, 1]
    modal_cell = h.groupby("plate")["junction_name"].agg(lambda s: s.mode().iloc[0])
    feats["likely_location"] = modal_cell
    feats["expected_days_to_next"] = feats["mean_gap"].clip(upper=90)
    wl = feats.sort_values("risk", ascending=False)
    wl.to_csv(os.path.join(PROC, "vehicle_watchlist.csv"))
    return dict(n_candidates=len(feats), base_rate=y.mean(), auc=auc,
                prec_at_10pct=prec_at_k, k=k), wl


def run():
    df = _load()
    print(f"[near-repeat] cutoff={CUTOFF.date()}  tau={TAU_DAYS}d")
    cr = cell_risk(df)
    print(f"[B cell-risk] {cr['n_cells']} cells, next-{HORIZON_CELL}d active rate={cr['pos_rate']:.2f}")
    print(f"   AUC  base_count={cr['auc_base']:.3f} | self-exciting risk={cr['auc_risk']:.3f} "
          f"| combined={cr['auc_combo']:.3f}")
    vh, wl = vehicle_hazard(df)
    print(f"\n[D vehicle-hazard] candidates={vh['n_candidates']:,} "
          f"base re-offense rate (30d)={vh['base_rate']:.3f}")
    print(f"   AUC={vh['auc']:.3f} | precision@top-10% ({vh['k']})={vh['prec_at_10pct']:.3f} "
          f"-> {vh['prec_at_10pct']/vh['base_rate']:.1f}x base rate")
    print("\n[D watchlist] top re-offense risks:")
    print(wl.head(8)[["prior_count", "days_since_last", "risk",
                      "likely_location"]].round(2).to_string())
    return cr, vh, wl


if __name__ == "__main__":
    run()
