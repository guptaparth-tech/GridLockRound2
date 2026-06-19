# Theme 1 — Deep Analysis Findings (provable patterns)

_Workspace for rigorous, reproducible findings on `Theme1/dataset.csv` (298,450 rows). Each finding lists the evidence/statistic and the analysis script that produces it. Last updated: 2026-06-16._

---

## F1. The data is a record of ENFORCEMENT SUPPLY, not violation demand (foundational)
**Script:** `analysis/01_temporal_semantics.py`

**Evidence:**
- `created` and `modified` timestamps give **near-identical** IST hour profiles (both peak 10–11 IST ~11%, both ≈0% during 15:00–23:00) → the daily cycle is real, not a single-field artifact.
- **85.5%** of all records fall in **03:00–13:00 IST**; only **1.44%** fall in **15:00–23:00 IST** (the evening, when parking congestion is worst).
- Active **enforcement devices per hour mirror the violation count**: ~1,400–1,770 devices on-shift 03:00–12:00 IST, collapsing to 96 (17h), 31 (18h), 12 (19h). Total fleet = 3,070 devices.
- The evening void is **systemic across ~31 stations** (most <0.5% evening share; max "City Market" 3.4%).

**Implication (reframes the project):** The temporal distribution is the **patrol schedule**, not when illegal parking happens. Therefore:
- "Forecast when violations spike → schedule patrols" is **partly circular** — it re-predicts the existing roster.
- Evening/night parking violations are **near-invisible** (enforcement blind window) despite being the worst for congestion.
- Any honest model must separate **enforcement intensity (observation process)** from **true violation propensity (latent demand)**. This is the key gap → see novel-solutions doc.

**Timestamp reliability caveat (provable):** `created_datetime` is anonymised — **seconds are constant `:46`** for all 298,445 rows, minutes are ~uniform (0.0157–0.0176 vs uniform 0.0167), and `modified < created` in 0.1% of rows. So **sub-hour precision is meaningless**; only **date and hour** are usable, and even hour should be read as "enforcement hour." `modified_datetime` carries real microsecond granularity (258k distinct).

---

## F2. Spatial concentration is extreme, scale-invariant, and statistically real
**Script:** `analysis/02_concentration.py`

**Evidence:**
- **Gini of violations across grid cells ≈ 0.84–0.86** at 100m / 500m / 1km — concentration is *not* a grid-size artifact.
- **Top 1% of cells hold ~32%** of records; **top 5% hold ~63%** (consistent across scales).
- **Moran's I = 0.385** on the ~500m queen-contiguity grid (E[I]≈ −0.0006) → strong, significant positive spatial autocorrelation; hotspots cluster together, they are not scattered.

**Implication:** Spatial prioritisation is well-founded (a small set of contiguous zones dominates). Caveat per F1: this is partly *enforcement* concentration; clustering reflects both true demand and where patrols concentrate.

---

## F3. The free-text address encodes a usable road-class + POI (demand) signal
**Script:** `analysis/03_address_signals.py`

**Evidence (share of rows whose `location`+`junction_name` contains the keyword):**
- Road class: main road 22.9%, cross 13.2%, ring road/ORR 5.5%, flyover/bridge 3.1%.
- POI trip-generators: mall 5.8%, market 4.4%, school/college 3.9%, hospital 2.5%, temple 2.5%, metro 1.9%, tech-park 1.8%.
- **Provable demand link:** rows near a **market are 94.5% at-junction** and near a **metro 78.6%**, vs **50.4% baseline** → POI-driven parking disproportionately lands on flow-critical junctions.

**Implication:** We can build an **in-dataset impact/demand proxy** (road-class weight + POI trip-generator flags) without any external data — directly addressing the "no measured congestion" gap. Honest limit: POI keyword coverage is sparse (reverse-geocoded text doesn't always name the POI), so these are categorical *enrichments*, not exhaustive labels.

---

## F4. Hotspots fall into interpretable functional archetypes (by composition, not hour)
**Script:** `analysis/04_archetypes.py`

Clustered 246 actionable cells (≥200 violations) on **demand-side composition** (vehicle mix, violation mix, weekend ratio) — deliberately excluding the enforcement-confounded hour profile (F1). KMeans, k=4.

**Evidence (silhouette ≈0.20 — modest; composition is a continuum, but centroids are distinct & policy-relevant):**
- **A0 Two-wheeler spillover** (103 cells): 68% two-wheelers, high no-parking.
- **A1 Car / CBD** (65 cells): 56% cars, slightly higher weekend share.
- **A2 Footpath & main-road encroachment** (8 cells): **15% footpath, 9.5% main-road** violations — the most flow-critical, rare but distinctive.
- **A3 Commercial / loading corridor** (70 cells): **22.5% commercial vehicles, 20.5% autos**, elevated main-road parking.

**Implication:** Different archetypes need different interventions (footpath → bollards/enforcement; loading corridors → designated bays + time windows; two-wheeler spillover → two-wheeler parking supply). One-size enforcement is suboptimal — a provable basis for **archetype-specific policy**.

---

## F5. Heavy, structured selection bias + label noise in the enforcement records
**Script:** `analysis/05_selection_bias.py`

**Evidence:**
- **30.1% rejection rate** among reviewed tickets (approved 115,400 vs rejected 49,754); a further **125,254 (42%) are unverified**. Raw counts are *noisy*, not clean ground truth.
- Rejection is **non-random by vehicle type**: passenger-auto 37.0%, LGV 32.4%, two-wheelers ~31%, **car 24.6%** → systematic differences (contested/mislabelled classes).
- **Enforcement effort is highly unequal**: Gini(records per station)=0.556 (top-5 of 55 stations = 41.3%, bottom-10 = 2.3%); Gini(per officer)=0.776; Gini(per device)=0.789.
- 14% of records (`data_sent_to_scita`=FALSE) never reach downstream processing.

**Implication:** Spatial/temporal counts conflate **true violation propensity** with **enforcement intensity** and **label noise**. Treating counts as demand over-weights heavily-patrolled CBD stations and under-weights everything else — the core methodological gap (→ novel solution: observation-aware demand estimation; validation-status as a label-quality model).

---

## F6. Recidivism is fast, spatially-habitual, and concentrated (highly predictable)
**Script:** `analysis/06_recidivism.py`

**Evidence (231,405 plates):**
- Repeat offenders are **15.5% of plates but 34.5% of all tickets**; top 1% of plates = 7.2% of tickets.
- Inter-violation gap: **median 7.9 days**; **48.3% re-offend within 7 days, 75.5% within 30 days**.
- **49.1% of repeat violations occur within ~200m of the previous one** → strong spatial habit (offenders re-park illegally at the same spot).

**Implication:** A small, identifiable set of habitual vehicles drives a third of all violations, re-offending quickly at the same locations. **Vehicle-level recidivism prediction** (next-offense risk + likely location/time) is feasible and high-leverage — and complements location-based enforcement. Note: plates are anonymised (`FKN…`), so this is a methodology/scoring demo, not real-vehicle targeting.

---

## F7. Near-repeat clustering is statistically significant; de-biasing proxy is viable
**Scripts:** `analysis/07_knox_nearrepeat.py`, inline checks

**Evidence:**
- **Knox permutation test** (sample 4,000; <200m & <14d; 30 shuffles): observed 15,773 space-time-close pairs vs expected **14,539 ± 122** → **ratio 1.08×, z = 10.2** (significant). Space-time co-clustering exceeds chance.
- Nuance (honest): the *cross-incident* near-repeat effect is modest (1.08×); the strong recurrence is **same-vehicle habit** (F6: 49% within 200m). So parking near-repeat is more "personal recidivism" than burglary-style spatial contagion → favours **vehicle-anchored** risk (Solution B/D) over pure neighbour-contagion.
- **De-biasing proxy viability (Solution A):** across 534 cells (≥50 violations), **corr(violation count, distinct active devices) = 0.63** → counts measurably track patrol presence; `device_id` density is a usable detection proxy for the observation model.

---

## Summary table
| # | Pattern | Headline stat | Provable via |
|---|---|---|---|
| F1 | Data = enforcement supply, not demand | 85.5% of records in 03–13 IST; device fleet mirrors it | created/modified agreement, device-by-hour |
| F2 | Extreme, scale-invariant spatial concentration | Gini 0.84–0.86; Moran's I 0.385 | grid Gini + autocorrelation |
| F3 | Address text → road-class + POI demand signal | market rows 94.5% at-junction vs 50.4% | keyword parse + cross-tab |
| F4 | Functional hotspot archetypes | 4 policy-distinct types (footpath/loading/2-wheeler/CBD) | KMeans on composition |
| F5 | Selection bias + label noise | 30.1% rejection; effort Gini 0.56–0.79 | validation_status, per-station/officer |
| F6 | Fast, habitual, concentrated recidivism | 15.5% plates = 34.5% tickets; 49% reoffend <200m | inter-event interval + spatial diff |
| F7 | Significant near-repeat; de-bias proxy works | Knox 1.08× z=10.2; corr(count,devices)=0.63 | Knox permutation + cell correlation |
