"""Shared ~500 m grid-cell utilities used across Solutions A-E."""
from __future__ import annotations

import numpy as np
import pandas as pd

GRID_DEG = 0.0045  # ~500 m


def add_cell(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["gx"] = np.floor(df["longitude"] / GRID_DEG).astype(int)
    df["gy"] = np.floor(df["latitude"] / GRID_DEG).astype(int)
    df["cell"] = df["gx"].astype(str) + "_" + df["gy"].astype(str)
    return df


def cell_name(sub: pd.DataFrame) -> str:
    """Human label for a cell: dominant junction, else first address segment."""
    jn = sub.loc[sub["at_junction"], "junction_name"]
    if len(jn):
        return jn.mode().iloc[0]
    loc = sub["location"].dropna().str.split(",").str[0]
    return loc.mode().iloc[0] if len(loc) else "Unnamed area"
