"""ParkPulse v2 — functional demo for Solutions A-E (kept minimal by design).
Run: python run_all.py  then  streamlit run app.py
"""
import os

import pandas as pd
import streamlit as st

PROC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "outputs", "processed")
st.set_page_config(page_title="ParkPulse v2", layout="wide")


@st.cache_data
def load(name):
    return pd.read_csv(os.path.join(PROC, name))


st.title("ParkPulse v2 — de-biased parking-congestion intelligence (Bengaluru)")
st.caption("Solutions A–E. Functional prototype; not styled. Data = 298K enforcement records (Theme 1).")

try:
    cells = load("parkpulse_cells.csv")
    blind = load("blind_spots.csv")
    watch = load("vehicle_watchlist.csv")
except FileNotFoundError:
    st.error("Run `python run_all.py` first."); st.stop()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Cells", f"{len(cells):,}")
c2.metric("Actionable archetyped", int((cells['archetype'] != '(low-volume cell)').sum()))
c3.metric("Blind-spots flagged", len(blind))
c4.metric("Vehicle watchlist", f"{len(watch):,}")

tabs = st.tabs(["A · De-biased demand", "A · Blind-spots", "C · Impact (CIS)",
                "E · Archetypes", "B/D · Vehicle watchlist", "Notes"])

with tabs[0]:
    st.subheader("Detection-adjusted demand (tickets per patrol-unit)")
    st.write("Corrects raw counts for enforcement intensity (F1/F5). Reliable cells only.")
    rel = cells[cells["reliable"] == True].sort_values("demand_index", ascending=False)
    st.dataframe(rel[["name", "top_station", "observed", "devices", "demand_index",
                      "archetype"]].head(40), hide_index=True, use_container_width=True)
    st.map(rel.head(100).rename(columns={"lat": "latitude", "lon": "longitude"})[["latitude", "longitude"]])

with tabs[1]:
    st.subheader("Enforcement blind-spots: high impact, low patrol presence, weak evening coverage")
    st.dataframe(blind[["name", "top_station", "CIS", "devices", "evening_share",
                        "blind_spot"]].head(40), hide_index=True, use_container_width=True)
    st.map(blind.head(60).rename(columns={"lat": "latitude", "lon": "longitude"})[["latitude", "longitude"]])

with tabs[2]:
    st.subheader("Congestion-Impact Score (in-dataset proxy: density·recurrence·road-class·POI·severity·criticality)")
    station = st.selectbox("Filter station", ["All"] + sorted(cells["top_station"].dropna().unique()))
    v = cells if station == "All" else cells[cells["top_station"] == station]
    st.dataframe(v.sort_values("CIS", ascending=False)[
        ["CIS_rank", "name", "top_station", "CIS", "n_violations", "road_class",
         "dominant_poi", "archetype"]].head(40), hide_index=True, use_container_width=True)

with tabs[3]:
    st.subheader("Functional archetypes → recommended intervention")
    act = cells[cells["archetype"] != "(low-volume cell)"]
    st.bar_chart(act["archetype"].value_counts())
    arch = st.selectbox("Show cells for archetype", sorted(act["archetype"].unique()))
    st.dataframe(act[act["archetype"] == arch].sort_values("n_violations", ascending=False)[
        ["name", "top_station", "n_violations", "intervention"]].head(30),
        hide_index=True, use_container_width=True)

with tabs[4]:
    st.subheader("Vehicle re-offense watchlist (hazard model; plates anonymised — methodology demo)")
    st.write("Top-10% by risk re-offend at ~3.2× base rate (held-out AUC 0.70).")
    st.dataframe(watch.rename(columns={watch.columns[0]: "plate"}).sort_values("risk", ascending=False)[
        ["plate", "prior_count", "days_since_last", "risk", "likely_location"]].head(40),
        hide_index=True, use_container_width=True)

with tabs[5]:
    st.markdown("""
**Honest notes**
- Data is *enforcement-supply*, not violation-demand (F1): 85% of records in a single 03–13 IST shift. Solution A corrects for this; blind-spots flag the evening/peripheral void.
- Cell-level near-repeat ≈ persistence (AUC 0.86); the strong recidivism signal is *per-vehicle* (Solution D).
- Impact (CIS) is a transparent in-dataset proxy, not measured congestion.
- See `analysis/findings.md` and `analysis/novel_solutions.md` for full provenance.
""")
