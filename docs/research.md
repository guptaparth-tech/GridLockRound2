# research.md — Sources & Evidence

_Last updated: 2026-06-16_

## Dataset-derived evidence (firsthand, read-only profiling)
- **Theme1** `dataset.csv`: 298,450 rows; 100% lat/long populated; created_datetime spans 2023-11 → 2024-04.
  - Violation types ~95% parking (WRONG PARKING 164,977; NO PARKING 139,050; PARKING IN A MAIN ROAD 23,943; footpath/bus-stop/near-crossing/double smaller).
  - Vehicle types: SCOOTER 94,856; CAR 88,870; MOTOR CYCLE 40,811; PASSENGER AUTO 37,813; MAXI-CAB, LGV, buses, HGV present.
  - Spatial concentration: top 50 ~110 m grid cells = 25.9% of all violations; top 500 = 68.5% (7,816 cells total).
  - Temporal: strong hour-of-day + day-of-week cycle.
  - Repeat offenders: 15.5% of 231,405 vehicles have >1 violation; max 55.
  - **Gaps:** `closed_datetime` & `action_taken_timestamp` 0% filled. `validation_status` mix: NULL 125k, approved 115k, rejected 50k.
- **Theme2** `dataset.csv`: 8,173 rows. event_type mostly `unplanned` (7,706); causes dominated by vehicle_breakdown (4,896), pot_holes, construction, water_logging, accident. Only ~660 rows are rallies/processions/protests/VIP. Duration derivable for 3,432 rows; varies by cause (breakdown median 0.7h vs potholes 95h) and road-closure (2.5h vs 1.1h). No manpower/impact label.

## Online sources
| # | Source | Key claim | Relevance |
|---|---|---|---|
| 1 | ScienceDirect S0965856422001458 — curb-lane monitoring via queueing + CV | "rank, detect, quantify impacts" of illegal parking; hotspot identification | Validates the impact-quantification framing; their angle is camera-based → our enforcement-record angle is differentiated |
| 2 | ScienceDirect S0167865522002938 — predicting on-street parking violation rate (deep ResNet) | Geospatial features (road centrality, land use, POI) improve violation-rate prediction | Justifies optional OSM auxiliary enrichment + forecasting feasibility |
| 3 | MDPI Urban Sci 2413-8851/9/10/411 — space-time cube + emerging hotspot | Space-time-cube + Getis-Ord emerging hotspot analysis | Method blueprint for spatiotemporal hotspots |
| 4 | ResearchGate STNKDE / KDE+Getis-Ord+DBSCAN papers | KDE visualizes, Getis-Ord Gi* gives significance, DBSCAN clusters | Method stack for hotspot module |
| 5 | GitHub topic `traffic-enforcement` + multiple violation-detection repos | All are CV/YOLO+DeepSORT detectors with dashboards | Confirms Theme 3 saturation; no enforcement-record analytics project found → Theme 1 originality |

## Round-2 deep research (sourced) — for the novel directions
| # | Source (citation) | Claim we rely on | Links to finding |
|---|---|---|---|
| 6 | Lum & Isaac (2016), "To predict and serve?", *Significance* 13(1) | Training on police-recorded data reproduces enforcement bias; predicted areas get more patrols, generating self-confirming data. | F1, F5 — our temporal/spatial counts are enforcement-driven |
| 7 | Ensign, Friedler, Neville, Scheidegger, Venkatasubramanian (2017), "Runaway Feedback Loops in Predictive Policing", *PMLR/FAT* (arXiv:1706.09847) | Formalises the feedback loop; proposes reweighting discovered incidents by detection probability to break it. | Method basis for bias-correction (Solution A) |
| 8 | Townsley, Homel & Chaseling (2003); Johnson & Bowers (2004) — near-repeat phenomenon | After an incident, nearby risk rises then decays (~UK burglary: within ~400m for ~1 month). | F6 — parking: 49% within ~200m, 75% within 30 days |
| 9 | "Predicting the spatiotemporal legality of on-street parking using open data and ML" (2019), *Annals of GIS* (T&F 10.1080/19475683.2019.1679882) | RF on NYC tickets + POI + mobility predicts ticket counts / legality. | Prior art for Solution C; we differ by deriving POI in-dataset + bias-correction |
| 10 | "Deep Learning for On-Street Parking Violation Prediction" (2025, arXiv:2505.06818); "Spatio-temporal heterogeneity in street illegal parking: NYC" (2025, ScienceDirect S096669232500153X) | Fine-grained DL violation-rate prediction; strong spatiotemporal heterogeneity. | Confirms forecasting feasibility + heterogeneity (F2, F4) |
| 11 | SFpark / LA ExpressPark curb-pricing experiments (2010s) | Occupancy-responsive pricing cut double-parking & cruising. | Policy benchmark for archetype-specific interventions (F4) |

## Round-2b research (2026-06-19) — evidence to harden the impact (CDS) and effectiveness (EEI) framing
| # | Source (citation) | Claim we rely on | Links to idea |
|---|---|---|---|
| 12 | Cao & Menendez / on-street parking capacity studies (ResearchGate 46212892; ScienceDirect S0967070X22000609 double-parking) | On-street parking cuts effective road capacity ~23–24%; **illegal double-parking adds ~26% more** → combined ~50% capacity loss; removing it can raise capacity ~49.9% and cut travel time ~36%. | Empirical anchor for the **Lane-Blockage Factor** coefficients in CDS (Idea 1) — defensible, not invented. |
| 13 | US congestion attribution stats (cited in CHAPTER-I review) | Illegal parking ≈ **3rd leading cause of US urban congestion; ~47M vehicle-hours of delay/yr**. | Justifies framing violations as *congestion debt*, gives an order-of-magnitude unit (vehicle-hours). |
| 14 | "Frequency of enforcement is more important than the severity of punishment in reducing violation behaviors", **PNAS 2021** (10.1073/pnas.2108507118) | **Certainty/frequency of enforcement deters more than severity of penalty.** | Core justification for **EEI** (Idea 2) + the patrol-frequency recommender: re-visit cadence > bigger fines. |
| 15 | Deterrence theory — certainty, celerity, severity (deterrence reviews); speeding-recidivism studies (PubMed 26311201) | Deterrence = how likely caught (certainty), how fast penalty follows (celerity), how big (severity); severity alone shows weak marginal deterrence. | EEI metric design: measure deterrence via **re-offense gap** as a celerity/certainty proxy. |
| 16 | "Social norms or enforcement? A natural field experiment…parking fine compliance", *J. Econ. Behav. Organ.* 2023 (S0167268123001002) | Enforcement/reminder letters raise parking-fine compliance more than social-norm appeals. | Supports an action layer (escalation/notice) for chronic violators (Idea 4). |

## Data-claim verification (2026-06-19, against raw `Theme1/dataset.csv`, n=298,450) — for the new 6-idea set
| Idea claim | Raw-data verdict | Use this instead |
|---|---|---|
| "0% closure rate" | ✅ **EXACT** — `closed_datetime` 0.00% filled, `action_taken_timestamp` 0.00% filled. | Headline hook — strongest single fact. |
| "3,070 tracked devices" | ✅ **EXACT** (3,070 distinct `device_id`). | Keep. |
| "single device filed >4,000 records" | ✅ TRUE — max device = **4,344**; exactly **1** device >4,000. | Say "one device logged 4,344 records." |
| "KR Market hotspot" | ✅ STRONG — **11,826** rows mention KR Market / Krishna Rajendra. | Keep; flagship example. |
| "Hosahalli Metro 4,101" | ≈ OK — **4,398** rows mention "Hosahalli". | Say "~4,400 near Hosahalli." |
| "917 repeat offenders" | ⚠️ **NOT REPRODUCIBLE.** >1 viol = 35,587; ≥8 = 1,206; ≥10 = **711**; ≥15 = 236. | Use **35,587 repeat plates (15.3% of plates = 34.5% of tickets)** or **711 vehicles with ≥10**. Drop "917". |
| "one vehicle 36 open violations" | ⚠️ off — max for any plate = **55**. ("Open" is undefinable: closure field is 0% filled.) | Say "worst plate = 55 violations." |
| "stations reject 24%" | ⚠️ off — worst station = **22.9%** (Byatarayanapura); 24.6% is the **car-type** rate. Overall reviewed = **30.1%**. | Say "30.1% of reviewed tickets rejected; up to ~23% at some stations." |
| "one grid cell 24,378 violations" | ⚠️ **NOT at cell scale** — busiest ~110m cell = **4,411** (24k only appears at corridor/DBSCAN scale). | Say "busiest 110m cell = 4,411" or "top DBSCAN corridor ≈ 24k" — name the scale. |
| "Ghost Patrol: multiple filings <30s apart = impossible" | ❌ **UNSUPPORTABLE** — `created_datetime` seconds are anonymised to constant `:46` (F1). Sub-minute timing does not exist in this data. | **Do not claim sub-minute anomalies.** Recast integrity audit as: 30.1% rejection + effort Gini 0.56–0.79 + 14% never-sent-to-SCITA. |

**Net:** Idea 5's signature evidence (30-second impossible filings) is killed by the timestamp anonymisation — recast as a legitimate selection-bias/label-noise audit. Ideas 1, 2, 4 are well-supported once numbers are corrected as above.

**Gap this research exposes:** Existing parking-violation-prediction work (sources 9–10) trains on tickets **without** correcting for the enforcement observation process, even though the predictive-policing literature (6–7) proves that biases predictions. **Applying feedback-loop correction + near-repeat modelling to parking enforcement is under-served** — and our data (F1/F5/F6) makes the case unusually cleanly.

## Novelty statement
Prior art for "parking impact" is overwhelmingly **camera/CV-driven** (detect a parked car from video). ParkPulse instead mines a large **real enforcement-record dataset** to produce a hotspot → impact → forecast → enforcement-prioritization decision tool, Bengaluru-specific. This is under-served in open source.
