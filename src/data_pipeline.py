"""ParkPulse data pipeline (Theme 1).

Loads the raw Bengaluru parking-enforcement records, parses the JSON
`violation_type` arrays, normalises vehicle/violation categories, derives
time features, and writes a clean feature table to outputs/processed/clean.parquet.

Dataset discipline: trains/evaluates ONLY on Theme1/dataset.csv.
"""
from __future__ import annotations

import ast
import json
import os

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "Theme1", "dataset.csv")
OUT_DIR = os.path.join(ROOT, "outputs", "processed")
OUT = os.path.join(OUT_DIR, "clean.parquet")

# IST offset; raw timestamps are tagged +00 but represent Bengaluru local activity.
# We convert to IST for human-readable hour-of-day patterns and document the caveat.
IST_OFFSET = pd.Timedelta(hours=5, minutes=30)

# Bengaluru bounding box (drop obvious geo errors).
BLR_BBOX = dict(lat_min=12.7, lat_max=13.25, lon_min=77.3, lon_max=77.85)

# Impact weight by vehicle type: larger vehicles obstruct more carriageway.
VEHICLE_SEVERITY = {
    "HGV": 3.0, "LORRY/GOODS VEHICLE": 3.0, "PRIVATE BUS": 3.0,
    "BUS (BMTC/KSRTC)": 3.0, "TEMPO": 2.5, "LGV": 2.5, "MAXI-CAB": 2.0,
    "VAN": 2.0, "GOODS AUTO": 2.0, "JEEP": 1.8, "CAR": 1.5,
    "PASSENGER AUTO": 1.5, "MOTOR CYCLE": 1.0, "SCOOTER": 1.0, "MOPED": 1.0,
}
DEFAULT_VEHICLE_SEVERITY = 1.5

# Criticality weight by violation type: footpath/main-road/junction obstructions
# hurt flow more than generic no-parking.
VIOLATION_CRITICALITY = {
    "PARKING ON FOOTPATH": 3.0,
    "PARKING NEAR ROAD CROSSING": 3.0,
    "PARKING NEAR TRAFFIC LIGHT OR ZEBRA CROSS": 3.0,
    "PARKING IN A MAIN ROAD": 2.5,
    "PARKING NEAR BUSTOP/SCHOOL/HOSPITAL ETC": 2.5,
    "DOUBLE PARKING": 2.5,
    "PARKING OPPOSITE TO ANOTHER PARKED VEHICLE": 2.0,
    "WRONG PARKING": 1.5,
    "NO PARKING": 1.2,
    "PARKING OTHER THAN BUS STOP": 1.2,
}
DEFAULT_VIOLATION_CRITICALITY = 1.0


def _parse_list(x):
    """Parse a stringified JSON/py list like '[\"WRONG PARKING\"]' robustly."""
    if not isinstance(x, str) or x in ("", "NULL"):
        return []
    try:
        return json.loads(x)
    except Exception:
        try:
            return ast.literal_eval(x)
        except Exception:
            return []


def load_clean(write: bool = True) -> pd.DataFrame:
    df = pd.read_csv(RAW, dtype=str, keep_default_na=False, na_values=["NULL", ""])

    # --- coordinates ---
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    n0 = len(df)
    df = df.dropna(subset=["latitude", "longitude"])
    df = df[
        df["latitude"].between(BLR_BBOX["lat_min"], BLR_BBOX["lat_max"])
        & df["longitude"].between(BLR_BBOX["lon_min"], BLR_BBOX["lon_max"])
    ].copy()

    # --- violation types (multi-label) ---
    df["violations"] = df["violation_type"].apply(_parse_list)
    df["n_violations"] = df["violations"].apply(len)
    # primary violation = highest criticality among the listed ones
    df["primary_violation"] = df["violations"].apply(
        lambda vs: max(vs, key=lambda v: VIOLATION_CRITICALITY.get(v, DEFAULT_VIOLATION_CRITICALITY))
        if vs else "UNKNOWN"
    )
    df["violation_criticality"] = df["violations"].apply(
        lambda vs: max((VIOLATION_CRITICALITY.get(v, DEFAULT_VIOLATION_CRITICALITY) for v in vs),
                       default=DEFAULT_VIOLATION_CRITICALITY)
    )

    # --- vehicle ---
    df["vehicle_type"] = df["vehicle_type"].fillna("UNKNOWN").str.upper()
    df["vehicle_severity"] = df["vehicle_type"].map(VEHICLE_SEVERITY).fillna(DEFAULT_VEHICLE_SEVERITY)
    # best available plate (prefer corrected)
    df["plate"] = df["updated_vehicle_number"].fillna(df["vehicle_number"])

    # --- time (UTC tag -> IST for human cycles) ---
    dt = pd.to_datetime(df["created_datetime"], errors="coerce", utc=True)
    df["created_ist"] = dt + IST_OFFSET
    df = df.dropna(subset=["created_ist"]).copy()
    df["date"] = df["created_ist"].dt.date
    df["hour"] = df["created_ist"].dt.hour
    df["dow"] = df["created_ist"].dt.dayofweek       # 0=Mon
    df["is_weekend"] = df["dow"].isin([5, 6])
    df["month"] = df["created_ist"].dt.tz_localize(None).dt.to_period("M").astype(str)

    # --- categoricals ---
    df["police_station"] = df["police_station"].fillna("UNKNOWN")
    df["junction_name"] = df["junction_name"].fillna("No Junction")
    df["at_junction"] = (df["junction_name"].str.lower() != "no junction")
    df["validation_status"] = df["validation_status"].fillna("unverified")

    # --- enforcement-process fields (for de-biasing, Solution A) ---
    df["device_id"] = df["device_id"].fillna("UNKNOWN")
    df["created_by_id"] = df["created_by_id"].fillna("UNKNOWN")

    # --- address-derived road-class + POI signals (Solution C, see F3) ---
    text = (df["location"].fillna("") + " " + df["junction_name"].fillna("")).str.lower()
    df["road_weight"] = (
        1.0
        + 2.0 * text.str.contains("flyover|bridge|underpass", regex=True)
        + 1.5 * text.str.contains("ring road|orr|nice road", regex=True)
        + 1.0 * text.str.contains(r"\bmain road\b", regex=True)
        + 0.5 * text.str.contains(r"\bcross\b", regex=True)
    )
    POI_PATTERNS = {
        "poi_market": "market|bazaar|mandi", "poi_metro": "metro", "poi_mall": "mall",
        "poi_hospital": "hospital|clinic", "poi_school": "school|college|university|institute",
        "poi_transit": "bus stand|bus station|bmtc|ksrtc|railway",
        "poi_techpark": "tech park|sez|electronic city|itpl|manyata",
    }
    for col, pat in POI_PATTERNS.items():
        df[col] = text.str.contains(pat, regex=True).astype(int)
    df["poi_any"] = df[list(POI_PATTERNS)].max(axis=1)

    keep = [
        "id", "latitude", "longitude", "location", "plate", "vehicle_type",
        "vehicle_severity", "primary_violation", "violation_criticality",
        "n_violations", "police_station", "junction_name", "at_junction",
        "validation_status", "device_id", "created_by_id",
        "road_weight", "poi_any", *POI_PATTERNS.keys(),
        "created_ist", "date", "hour", "dow", "is_weekend", "month",
    ]
    clean = df[keep].reset_index(drop=True)

    if write:
        os.makedirs(OUT_DIR, exist_ok=True)
        clean.to_parquet(OUT, index=False)

    print(f"[data_pipeline] raw rows: {n0:,} -> clean rows: {len(clean):,}")
    print(f"[data_pipeline] date range (IST): {clean['date'].min()} -> {clean['date'].max()}")
    print(f"[data_pipeline] unique plates: {clean['plate'].nunique():,} | "
          f"police stations: {clean['police_station'].nunique()}")
    print(f"[data_pipeline] wrote {OUT}")
    return clean


if __name__ == "__main__":
    load_clean()
