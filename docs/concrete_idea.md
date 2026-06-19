# Concrete Idea — ParkPulse: Congestion-Debt & Enforcement-Intelligence Engine

_Synthesised 2026-06-19 from the 6-idea set + existing analysis (F1–F7) + sourced evidence (research.md #6–16). Theme 1. Solo prototype._

## One-line pitch
Bengaluru's 298K parking-enforcement records aren't a map of *where illegal parking happens* — they're a map of *where officers were standing*. ParkPulse corrects that bias, converts every violation into a measurable **Congestion Debt** (vehicle-hours of delay), and **measures whether enforcement actually deters** — turning reactive, unaccountable patrols into targeted, impact-ranked, verifiable action.

## Why this framing wins
The defining, *provable* property of the data is that it is **enforcement-supply biased** (F1: 85.5% of records in one 03–13 IST shift; device fleet mirrors counts; F5: 30.1% rejection, effort Gini 0.56–0.79) and has **zero closure data** (verified: closed/action timestamps 0.00% filled). So the obvious "predict tickets → send patrols there" is **circular** (Lum & Isaac 2016; Ensign et al. 2017). Every other team will build that hotspot-forecaster. We build the honest version *and* the two things no one else will: a defensible impact unit, and an effectiveness audit.

## Three pillars (each = a user idea, each evidence-anchored)

### Pillar 1 — Congestion Debt Score (CDS)  [user Idea 1 + 6]
Convert each violation into estimated congestion cost, not just a count.
`CDS = VehicleFootprint × RoadCriticality × ExposureWindow × LaneBlockageFactor`
- **Anchored, not invented:** on-street parking cuts road capacity ~23–24%, illegal double-parking adds ~26% (≈50% combined); removal raises capacity ~49.9% / cuts travel time ~36% (research.md #12). Illegal parking ≈ 3rd-largest US congestion cause, ~47M veh-hrs/yr (#13). These calibrate the Lane-Blockage coefficients.
- **In-dataset inputs only:** vehicle_type (footprint), F3 road-class + POI from address text (criticality), violation_type criticality, junction flag. Report weight-sensitivity (already done: top-30 Jaccard 0.42–0.64).
- Output: city-wide **Congestion-Debt heatmap** in interpretable units → justifies 3× enforcement at true high-*cost* (not just high-*count*) zones.

### Pillar 2 — De-biased Demand + Blind-Spot Map  [the original core; absorbs Idea 5 honestly]
Model latent demand = observed / detection_probability (detection ∝ distinct active devices; corr 0.63, F7).
- Surfaces the **enforcement blind-spot map**: high estimated demand, near-zero observed enforcement — the evening void (only 1.44% of records 15–23 IST) and peripheral corridors (Hosur Rd/Electronic City, ITPL/Whitefield) CBD patrols miss.
- **Integrity audit (recast Idea 5):** 30.1% rejection, effort Gini 0.56–0.79, 14% never sent to SCITA → counts ≠ confirmed demand. ⚠️ Do **not** claim "30-second impossible filings" — seconds are anonymised to `:46` (F1); that anomaly cannot exist in this data.
- Backs the feedback-loop sim (enforcement Gini 0.00→0.38 over 6 naive rounds).

### Pillar 3 — Enforcement Effectiveness Index (EEI)  [user Idea 2 — the boldest, most original]
The 0% closure rate is the hook (**verified exact**). Since outcomes aren't logged, measure deterrence by **re-offense gap at the same ~200m spot** after a violation.
- **Anchored:** deterrence = certainty + celerity + severity; PNAS 2021 shows **frequency/certainty of enforcement beats penalty severity** (#14, #15). So EEI scores locations/stations by whether ticketing actually lengthens the re-offense gap.
- Uses only timestamps + location (F6: median re-offense 7.9d; 48% <7d, 75% <30d; 49% within 200m). Constructive framing: identify where enforcement *deters* vs where it just re-files for quota → recommends **revisit cadence**, not bigger fines.

### Supporting modules
- **Chronic-Violator tiers (Idea 4):** 35,587 repeat plates = 34.5% of all tickets; 711 with ≥10; worst = 55. Hazard score → Yellow/Orange/Red + likely-next-spot. (Use these numbers; "917" and "36 open" don't reproduce.) Plates anonymised → methodology demo + escalation/notice action (#16).
- **De-biased near-repeat routing (reframed Idea 3):** vehicle-anchored self-exciting risk (Knox 1.08×, z=10.2), NOT naive count-chasing — sidesteps the feedback loop.

## What to drop / fix from the original 6 ideas
- ❌ "Ghost Patrol — 30-second impossible filings": unsupportable (timestamp anonymisation). Recast as selection-bias/label-noise audit inside Pillar 2.
- ⚠️ Predictive Patrol Routing as headline: circular; keep only as the de-biased near-repeat module.
- Correct all numbers per research.md verification table before any slide/claim.

## Maps to the submission form (from the requirements screenshot)
Title • Description • Theme=1 • Snapshots (CDS heatmap, blind-spot map, EEI chart) • Video URL (demo walkthrough) • Presentation (deck) • Demo Link (Streamlit) • Repository URL • Source Code zip • Instructions to Run (`pip install -r requirements.txt → python run_all.py → streamlit run app.py`). Most is already built (BUILD v2); remaining work = CDS unit calibration, EEI module, deck/video.
