"""Generates every figure and number used in the research paper.  Run: python analysis.py"""
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import uac_metrics as u

plt.rcParams.update({"figure.dpi": 150, "axes.spines.top": False, "axes.spines.right": False,
                     "font.size": 9, "axes.grid": True, "grid.alpha": .25})
d = u.add_metrics(u.load_data("data/HHS_Unaccompanied_Alien_Children_Program.csv"))
m = u.monthly_table(d)
imb = u.sustained_imbalance(d)
stag = u.stagnation_periods(d)
drops = u.sudden_drops(d)

# Fig 1 - pipeline census
fig, ax = plt.subplots(2, 1, figsize=(8, 5.2), sharex=True)
ax[0].plot(d.date, d.hhs_census, color="#1f4e79"); ax[0].set_title("Children in HHS care (stage 2 stock)")
ax[1].plot(d.date, d.cbp_census, color="#c0504d", lw=.8, label="In CBP custody")
ax[1].plot(d.date, d.apprehended.rolling(7).mean(), color="#888", lw=.8, label="Apprehended (7-report avg)")
ax[1].set_title("CBP custody (stage 1 stock) and intake"); ax[1].legend(frameon=False)
fig.tight_layout(); fig.savefig("figures/fig1_census.png"); plt.close()

# Fig 2 - flows
fig, ax = plt.subplots(figsize=(8, 3.4))
for c, l, col in [("apprehended", "Apprehended", "#888"), ("transferred", "Transferred CBP→HHS", "#c0504d"),
                  ("discharged", "Discharged to sponsors", "#2e7d32")]:
    ax.plot(d.date, d[c].rolling(14).mean(), label=l, color=col, lw=1.2)
ax.set_title("Daily flows between pipeline stages (14-report moving average)"); ax.legend(frameon=False)
fig.tight_layout(); fig.savefig("figures/fig2_flows.png"); plt.close()

# Fig 3 - efficiency ratios
fig, ax = plt.subplots(2, 1, figsize=(8, 5), sharex=True)
ax[0].plot(d.date, d.transfer_eff_roll, color="#c0504d"); ax[0].set_title("Transfer Efficiency Ratio (transfers ÷ CBP custody, 7-report)")
ax[1].plot(d.date, d.discharge_eff_roll * 100, color="#2e7d32"); ax[1].set_title("Discharge Effectiveness (discharges ÷ HHS care, % per report, 7-report)")
fig.tight_layout(); fig.savefig("figures/fig3_efficiency.png"); plt.close()

# Fig 4 - backlog with sustained imbalance shading
fig, ax = plt.subplots(2, 1, figsize=(8, 5), sharex=True)
ax[0].plot(d.date, d.hhs_backlog_rate, color="#1f4e79", lw=.9); ax[0].axhline(0, color="k", lw=.7)
for _, r in imb.iterrows():
    ax[0].axvspan(r.start, r.end, color="#e57373", alpha=.25)
ax[0].set_title("HHS backlog rate: transfers − discharges per report (red = sustained imbalance)", fontsize=9)
ax[1].plot(d.date, d.cum_hhs_net_flow, color="#6a1b9a"); ax[1].set_title("Cumulative (transfers − discharges)")
fig.tight_layout(); fig.savefig("figures/fig4_backlog.png"); plt.close()

# Fig 5 - monthly discharges per report
fig, ax = plt.subplots(figsize=(8, 3.3))
ax.bar(m.index, m.discharged_per_report, width=22, color="#2e7d32")
ax.set_title("Average discharges per reporting day, by month")
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %y"))
fig.tight_layout(); fig.savefig("figures/fig5_monthly.png"); plt.close()

# Fig 6 - stability
fig, ax = plt.subplots(figsize=(8, 3.2))
ax.plot(d.date, d.stability_score, color="#00695c")
for _, r in drops.iterrows():
    ax.axvline(r.date, color="#d32f2f", ls="--", lw=.9)
ax.set_title("Outcome Stability Score (30-report rolling; dashed = sudden-drop episodes)")
ax.set_ylim(0, 100)
fig.tight_layout(); fig.savefig("figures/fig6_stability.png"); plt.close()

# Fig 7 - weekday pattern
w = u.weekday_table(d)
w = w[w.reports > 10]
fig, ax = plt.subplots(figsize=(6, 3))
ax.bar(w.index, w.discharged, color="#2e7d32")
ax.set_title("Mean discharges by reporting weekday")
fig.tight_layout(); fig.savefig("figures/fig7_weekday.png"); plt.close()

k = u.kpi_summary(d)
rec = u.reconciliation(d)
phase = {}
for name, a, b in [("2023", "2023-01-01", "2023-12-31"), ("2024", "2024-01-01", "2024-12-31"),
                   ("2025", "2025-01-01", "2025-12-31")]:
    s = u.kpi_summary(d[(d.date >= a) & (d.date <= b)])
    phase[name] = {x: (float(y) if not isinstance(y, pd.Timestamp) else str(y.date())) for x, y in s.items()}
out = {"kpi": {x: (float(y) if not isinstance(y, pd.Timestamp) else str(y.date())) for x, y in k.items()},
       "by_year": phase, "reconciliation": rec,
       "imbalance": imb.astype(str).to_dict("records"), "stagnation": stag.astype(str).to_dict("records"),
       "drops": drops.astype(str).to_dict("records"),
       "peak": {"date": str(d.loc[d.hhs_census.idxmax(), "date"].date()), "hhs": float(d.hhs_census.max())},
       "trough": {"date": str(d.loc[d.hhs_census.idxmin(), "date"].date()), "hhs": float(d.hhs_census.min())},
       "ter_gt1_share": float((d.transfer_eff > 1).mean()),
       "weekday": w.round(4).reset_index().to_dict("records"), "gap": u.gap_table(d).round(4).reset_index().to_dict("records"),
       "zero_discharge_reports": int((d.discharged == 0).sum()),
       "corr_ter_de": float(d[["transfer_eff", "discharge_eff"]].corr().iloc[0, 1])}
json.dump(out, open("results.json", "w"), indent=2, default=str)
m.round(4).to_csv("monthly_summary.csv")
print(json.dumps(out["by_year"], indent=1)); print(out["peak"], out["trough"], out["ter_gt1_share"], out["zero_discharge_reports"])
