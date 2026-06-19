# ParkPulse — De-biased Parking-Congestion Intelligence (Bengaluru)

**Flipkart Gridlock Hackathon 2.0 — Round 2 · Theme 1: Poor Visibility on Parking-Induced Congestion**

ParkPulse turns **298,450 real Bengaluru parking-enforcement records** (Nov 2023 – Apr 2024)
into an enforcement decision tool. Its core insight: this data records **where officers were
standing, not where illegal parking happens** — so ParkPulse *corrects that bias*, scores the
**congestion impact** of each hotspot, and flags the **enforcement blind-spots** everyone else misses.

> For a plain-language, non-technical explanation of the whole solution, read **`SIMPLE.txt`**.

---

## 1. Requirements
- **Python 3.9 – 3.12** (any OS: Windows, macOS, Linux).
- ~1 GB free disk, ~2 GB RAM. No GPU, no internet, no API keys.
- That's it. All Python packages install from prebuilt wheels (no compiler needed).

## 2. Quick start

### Windows (PowerShell or CMD)
```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python run_all.py
streamlit run app.py
```

### macOS / Linux
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run_all.py
streamlit run app.py
```

### One-shot helper scripts (optional)
- Windows: double-click **`run.bat`**
- macOS / Linux: `bash run.sh`

`python run_all.py` runs the full analysis pipeline (~15 s) and writes results to
`outputs/processed/`. `streamlit run app.py` then opens the interactive demo in your browser
(usually http://localhost:8501).

> The folder ships with results already generated in `outputs/processed/`, so you can run
> `streamlit run app.py` **immediately** without running the pipeline first. Re-run
> `python run_all.py` any time to reproduce everything from the raw CSV.

## 3. What's inside
```
ParkPulse_Submission/
├── SIMPLE.txt              ← detailed plain-language explanation of the solution
├── README.md               ← this file
├── requirements.txt        ← 5 cross-platform packages
├── run_all.py              ← runs the whole pipeline end-to-end
├── app.py                  ← Streamlit interactive demo
├── run.bat / run.sh        ← one-click launch helpers
├── src/                    ← the solution modules (A–E, see below)
│   ├── data_pipeline.py    ← clean + feature-engineer the raw records
│   ├── cells.py            ← shared ~500 m grid utilities
│   ├── impact_proxy.py     ← [C] Congestion-Impact Score
│   ├── demand_debias.py    ← [A] de-biased demand + blind-spots + feedback-loop sim
│   ├── near_repeat.py      ← [B/D] near-repeat risk + vehicle re-offense watchlist
│   └── archetypes.py       ← [E] hotspot archetypes → policy interventions
├── Theme1/
│   └── dataset.csv         ← the provided Theme-1 dataset (298,450 records)
├── outputs/processed/      ← generated results (CSV + parquet)
└── docs/                   ← methodology & evidence
    ├── concrete_idea.md    ← the full idea + how each part is evidence-backed
    ├── findings.md         ← the 7 provable data findings (F1–F7)
    ├── novel_solutions.md  ← why the naive approach fails + the novel directions
    └── research.md         ← cited research papers + data-claim verification
```

## 4. The pipeline (Solutions A–E)
| Module | What it does | Key output file |
|---|---|---|
| `data_pipeline.py` | Clean rows, parse violations, derive time/road/POI/severity features | `outputs/processed/clean.parquet` |
| `impact_proxy.py` **[C]** | Transparent **Congestion-Impact Score** per cell (in-dataset only) | `cis_cells.csv` |
| `demand_debias.py` **[A]** | **De-bias** counts by patrol presence → demand index + **blind-spots** | `demand_cells.csv`, `blind_spots.csv` |
| `near_repeat.py` **[B/D]** | Cell near-repeat risk + **vehicle re-offense watchlist** (hazard model) | `cell_risk.csv`, `vehicle_watchlist.csv` |
| `archetypes.py` **[E]** | Cluster hotspots into 4 functional types → **recommended intervention** | `archetypes.csv` |
| `run_all.py` | Runs all of the above, then merges into one master table | `parkpulse_cells.csv` |
| `app.py` | Streamlit demo assembling everything | — |

## 5. Honest limitations (stated, not hidden)
- The data is **enforcement-generated** (85% of records fall in one 03–13 IST shift), so raw
  counts mix true demand with patrol intensity. Solution A corrects for this; we never claim
  the corrected demand is ground truth — it is decision-support.
- No measured congestion exists (`closed_datetime` / `action_taken_timestamp` are 0% filled),
  so the Congestion-Impact Score is a **transparent, sensitivity-tested proxy**, not a measurement.
- Vehicle numbers are anonymised (`FKN…`), so the offender watchlist is a **scoring methodology
  demonstration**, never real-person targeting.

## 6. Data / submission note
`Theme1/dataset.csv` is 109 MB. If a submission portal caps the **Source Code** upload at 50 MB,
upload the code without the CSV and attach `dataset.csv` separately (e.g. as the Custom
Attachment), or place the provided CSV into `Theme1/` before running.
