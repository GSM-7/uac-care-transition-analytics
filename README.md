# Care Transition Efficiency & Placement Outcome Analytics

Process-efficiency analysis of the HHS Unaccompanied Children (UAC) Program: CBP custody → HHS care → sponsor placement.

**Live app:** `<paste your Streamlit URL here>`
**Research paper:** `docs/Research_Paper_UAC_Care_Transition_Analytics.pdf`
**Executive summary:** `docs/Executive_Summary_UAC.pdf`

## What's inside
| Path | Purpose |
|---|---|
| `app.py` | Streamlit dashboard (pipeline flow, efficiency panels, bottleneck detection, outcome trends, date range, ratio toggles, threshold alerts) |
| `uac_metrics.py` | Data cleaning + all KPI logic (shared by app and analysis) |
| `analysis.py` | Regenerates every figure in `figures/` and `results.json` used in the paper |
| `data/` | Source CSV |
| `docs/` | Research paper and executive summary (DOCX + PDF) |

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py        # dashboard
python analysis.py          # figures + results.json
```

## KPIs
Transfer Efficiency Ratio (transfers ÷ CBP custody) · Discharge Effectiveness (discharges ÷ HHS care) · Pipeline Throughput (exits ÷ entries) · Backlog Accumulation Rate (mean transfers − discharges) · Outcome Stability Score (100 × (1 − CV of discharge effectiveness), 30-report window).

## Headline findings (Jan 2023 – Dec 2025, 720 reports)
* HHS census fell from 11,516 (Dec 2023) to ~2,000–2,500 in 2025, driven mainly by ~90% lower intake.
* Discharge effectiveness fell 2.9% → 1.1% per report (2024 → 2025): ~2.6× slower turnover.
* Four sustained 2024 imbalance periods added ~2,500 children to HHS care; the bottleneck is discharge, not CBP→HHS transfer.
* Stability score fell ~77 → 55 in 2025, with abrupt discharge drops on 25 Feb and 23 Mar 2025.

## Data caveats
~5 reports/week (no Friday/Saturday rows, gaps up to 10 days); census changes do not fully reconcile with transfers − discharges (r = 0.22); aggregate counts only. See the paper §2.2 and §4.
