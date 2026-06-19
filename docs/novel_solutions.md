# Theme 1 — Gaps & Novel Solution Directions

_Derived from the provable patterns in `findings.md` (F1–F6) and the sourced literature in `research.md` (#6–11). Last updated: 2026-06-16. This is analysis/ideation — no build yet._

## The gaps (why the "obvious" solution is weak)
1. **G1 — Circularity / feedback loop.** The temporal-spatial signal is *enforcement supply* (F1: 85.5% of records in a single 03–13 IST shift; device fleet mirrors it; F5: effort Gini 0.56–0.79). A model that "predicts where violations will be and sends patrols there" mostly re-predicts the existing roster and, per the predictive-policing literature (Lum & Isaac 2016; Ensign et al. 2017), **amplifies bias in a runaway loop**. Most parking-prediction papers (sources 9–10) ignore this.
2. **G2 — No measured congestion impact.** No duration/speed field; `closed/action` timestamps 0% filled. "Impact" must be inferred, and naive density over-credits over-patrolled CBD cells.
3. **G3 — Label noise.** 30.1% of reviewed tickets are rejected, 42% unverified (F5). Counts ≠ confirmed violations.
4. **G4 — Evening blind spot.** Only 1.44% of records fall 15:00–23:00 IST (F1), the worst congestion window — the data is silent exactly when it matters most.

## Novel solutions (each tied to a finding + a source)

### A. Observation-aware (de-biased) violation-demand estimation  ⭐ flagship novelty
**Idea:** Don't model ticket counts; model **latent violation propensity** while explicitly modelling the **enforcement observation process**. Treat each cell-hour's expected tickets as `demand × detection_probability`, where detection ∝ patrol presence (proxy: distinct active `device_id` / officer-hours in that cell-time, available in data). Estimate demand by down-weighting heavily-patrolled cells and up-weighting lightly-patrolled ones — the Ensign et al. (2017) reweighting trick, adapted to parking.
- **Why novel:** parking-violation prediction has not applied feedback-loop correction; we *prove* the bias exists here (F1, F5).
- **Provable validation:** show naive vs de-biased hotspot rankings diverge; demonstrate the naive model's feedback loop in simulation (re-patrol → re-observe).
- **Output:** a "true-demand" hotspot map + an explicit **enforcement-blind-spot map** (high estimated demand, low observed enforcement) — directly answers G1/G4.
- **Risk/limit:** detection proxy is imperfect (device presence ≈ patrol). Frame as decision-support, validate sensitivity.

### B. Near-repeat parking-risk engine (space–time recidivism)  ⭐ strong, well-grounded
**Idea:** Port the **near-repeat** crime model (Townsley 2003; Johnson & Bowers 2004) to parking. F6 shows the exact signature: 49% of repeat violations recur within ~200m, 48% within 7 days, 75% within 30. Build a **self-exciting (Hawkes-style) space–time risk surface**: each violation raises short-term risk in a ~200m / ~2-week kernel, which decays.
- **Why novel:** near-repeat is established for burglary/robbery, **not parking**; our data matches the canonical pattern strikingly.
- **Provable validation:** Knox test / near-repeat calculator for space–time clustering significance; compare Hawkes forecast vs F4 baseline on held-out time split.
- **Output:** short-horizon "where next" risk for proactive patrols — and it is *demand*-driven (event-triggered), partly sidestepping G1.

### C. Two-tier impact proxy from in-dataset signals (no external data)
**Idea:** Replace the flat CIS with a defensible **road-criticality × demand** proxy built from F3: parse road class (main road/cross/ring/flyover) + POI trip-generators (market/metro/mall/…) from the address text, combine with vehicle-severity and violation-criticality. Calibrate weights, report sensitivity.
- **Why it helps:** addresses G2 fully inside the dataset; the F3 link (market→94.5% at-junction) gives an empirical anchor.
- **Relation to prior art:** sources 9–10 use *external* POI/mobility; we derive POI **in-dataset** (data-constraint-compliant) — a meaningful twist, not a copy.

### D. Habitual-offender recidivism scoring (methodology demo)
**Idea:** From F6, score each vehicle's **next-offense hazard** (time-to-next, likely location) — 15.5% of plates drive 34.5% of tickets. Survival/hazard model on inter-violation intervals.
- **Caveat:** plates are anonymised (`FKN…`) → present as a *scoring methodology* (escalation tiers, expected ticket-volume reduction), not real targeting.

### E. Archetype-specific intervention recommender (policy layer)
**Idea:** Use F4 archetypes to map each hotspot to the *right* lever, citing SFpark (source 11): footpath-encroachment → physical/bollard + enforcement; loading corridors → designated bays + timed access; two-wheeler spillover → two-wheeler supply; CBD → occupancy-responsive measures.

## Recommended synthesis for the build
**Lead with A + B** (the genuinely novel, defensible core: de-biased demand + near-repeat risk), **support with C** (honest in-dataset impact proxy), **layer E** (policy translation), and **include D** as a methodology module. This directly converts every gap (G1–G4) into a differentiated, sourced contribution rather than another ticket-count hotspot map.

## Open questions — now resolved (see F7)
- **Detection proxy for A?** ✅ Viable. corr(cell count, distinct devices)=0.63 → device density tracks patrol presence and can drive the observation model.
- **Near-repeat significance for B?** ✅ Confirmed. Knox permutation test: 1.08× expected, z=10.2 (significant). Caveat: cross-incident effect is modest; the dominant signal is **same-vehicle** habit (F6), so B should be **vehicle-anchored** (fuse with D) rather than pure neighbour-contagion.
- **Responsible recidivism (D)?** Plates are anonymised → present as a scoring methodology with aggregate impact (expected ticket-volume reduction), never as individual targeting.

## Bottom line
The data's defining feature is that it is **enforcement-generated and biased** (F1, F5) — the obvious "predict tickets → send patrols" solution is circular and risks a documented feedback loop. The defensible, novel build is: **(A) de-biased demand + blind-spot map** and **(B/D) vehicle-anchored near-repeat risk**, with **(C)** an honest in-dataset impact proxy and **(E)** archetype→policy translation. Every piece is tied to a proven pattern (F1–F7) and a citable source (research.md #6–11).
