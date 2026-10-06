"""Care Transition Efficiency & Placement Outcome Analytics - Streamlit dashboard.
Run locally:  streamlit run app.py
"""
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

import uac_metrics as u

st.set_page_config(page_title="UAC Care Transition Analytics", page_icon="🧭", layout="wide")
BASE = Path(__file__).parent


def find_csv():
    """Locate the dataset wherever it was uploaded (data/ folder or repo root)."""
    preferred = BASE / "data" / "HHS_Unaccompanied_Alien_Children_Program.csv"
    if preferred.exists():
        return preferred
    for pattern in ("data/*.csv", "*.csv", "**/*.csv"):
        hits = sorted(BASE.glob(pattern))
        if hits:
            return hits[0]
    return None


DATA = find_csv()


@st.cache_data
def get_data(src):
    return u.load_data(src)


# ------------------------------------------------------------------ sidebar
st.sidebar.title("Controls")
upload = st.sidebar.file_uploader("Optional: upload a newer HHS CSV", type="csv")
if upload is None and DATA is None:
    st.error("Dataset not found in the repository. Add `HHS_Unaccompanied_Alien_Children_Program.csv` "
             "to the repo (in a `data/` folder or the root), or upload the CSV using the sidebar.")
    st.stop()
raw = get_data(upload if upload else DATA)

lo, hi = raw["date"].min().date(), raw["date"].max().date()
rng = st.sidebar.date_input("Date range", (lo, hi), min_value=lo, max_value=hi)
if not isinstance(rng, (tuple, list)) or len(rng) != 2:
    st.info("Select both a start and an end date in the sidebar.")
    st.stop()

window = st.sidebar.select_slider("Smoothing window (reports)", [1, 3, 7, 14, 30], value=7)
view = st.sidebar.radio("Ratio view", ["Rolling (smoothed)", "Per-report (raw)"])
show_cbp = st.sidebar.toggle("Show CBP-stage metrics", True)
show_hhs = st.sidebar.toggle("Show HHS-stage metrics", True)

st.sidebar.markdown("---")
st.sidebar.subheader("Alert thresholds")
ter_min = st.sidebar.slider("Min transfer efficiency", 0.0, 1.5, 0.50, 0.05)
de_min = st.sidebar.slider("Min discharge effectiveness (% of HHS care / report)", 0.0, 5.0, 1.0, 0.1) / 100
bk_max = st.sidebar.slider("Max backlog accumulation (children / report)", -50, 150, 25, 5)
st_min = st.sidebar.slider("Min outcome stability score", 0, 100, 50, 5)

full = u.add_metrics(raw, window=window)
d = full[(full["date"].dt.date >= rng[0]) & (full["date"].dt.date <= rng[1])].reset_index(drop=True)
if len(d) < 10:
    st.warning("Please select a longer date range (at least ~10 reports).")
    st.stop()

ter_col = "transfer_eff_roll" if view.startswith("Rolling") else "transfer_eff"
de_col = "discharge_eff_roll" if view.startswith("Rolling") else "discharge_eff"
k = u.kpi_summary(d)

st.title("🧭 Care Transition Efficiency & Placement Outcome Analytics")
st.caption(f"HHS Unaccompanied Children Program · {k['reports']} reports · "
           f"{k['start']:%d %b %Y} → {k['end']:%d %b %Y}")

# ------------------------------------------------------------------ KPI cards + alerts
last = d.iloc[-1]
c = st.columns(5)
c[0].metric("Transfer Efficiency", f"{k['transfer_efficiency']:.2f}", help="Transfers ÷ CBP custody (a turnover ratio; can exceed 1 because custody is a point-in-time count)")
c[1].metric("Discharge Effectiveness", f"{k['discharge_effectiveness']*100:.2f}%", help="Discharges ÷ HHS care, per report")
c[2].metric("Pipeline Throughput", f"{k['throughput_end_to_end']:.2f}", help="Total discharges ÷ total CBP apprehensions in range (>1 means exits exceed CBP-recorded entries)")
c[3].metric("Backlog Accumulation", f"{k['backlog_rate']:+.1f}/report", help="Mean (transfers − discharges). Positive = HHS backlog building")
c[4].metric("Outcome Stability", f"{k['stability']:.0f}/100", help="100 × (1 − CV of discharge effectiveness), 30-report rolling, averaged")

alerts = []
if last[ter_col] < ter_min: alerts.append(f"Transfer efficiency {last[ter_col]:.2f} is below {ter_min:.2f}")
if last[de_col] < de_min: alerts.append(f"Discharge effectiveness {last[de_col]*100:.2f}% is below {de_min*100:.1f}%")
if last["hhs_backlog_rate"] > bk_max: alerts.append(f"HHS backlog rate {last['hhs_backlog_rate']:+.0f}/report exceeds {bk_max}")
if pd.notna(last["stability_score"]) and last["stability_score"] < st_min: alerts.append(f"Stability score {last['stability_score']:.0f} is below {st_min}")
if alerts:
    st.error("**Alerts on latest report (" + f"{last['date']:%d %b %Y}" + "):**  \n" + "  \n".join("⚠️ " + a for a in alerts))
else:
    st.success(f"✅ All metrics within thresholds on latest report ({last['date']:%d %b %Y}).")

tabs = st.tabs(["Pipeline flow", "Transfer & discharge efficiency", "Bottleneck detection", "Outcome trends", "Data notes"])


def breach(fig, series, op, thr, row=None):
    """Mark points that breach a threshold on a plotly figure."""
    m = series < thr if op == "lt" else series > thr
    kw = {} if row is None else {"row": row, "col": 1}
    fig.add_trace(go.Scatter(x=d.loc[m, "date"], y=series[m], mode="markers", name="Threshold breach",
                             marker=dict(color="red", size=5), showlegend=False), **kw)


# ------------------------------------------------------------------ tab 1: pipeline
with tabs[0]:
    l, r = st.columns([1.1, 1])
    with l:
        st.subheader("Care pipeline: CBP → HHS → Sponsor")
        a, t, dis = k["total_apprehended"], k["total_transferred"], k["total_discharged"]
        fig = go.Figure(go.Sankey(
            node=dict(label=["Apprehended (CBP intake)", "CBP custody", "HHS care", "Sponsor placement"],
                      color=["#888", "#c0504d", "#1f4e79", "#2e7d32"], pad=25),
            link=dict(source=[0, 1, 2], target=[1, 2, 3], value=[a, t, dis],
                      label=["Intake", "Transferred to HHS", "Discharged to sponsors"],
                      color=["rgba(136,136,136,.35)", "rgba(192,80,77,.35)", "rgba(46,125,50,.35)"])))
        fig.update_layout(height=340, margin=dict(l=0, r=0, t=10, b=10))
        st.plotly_chart(fig, width="stretch")
        st.caption("Link widths = total children moving between stages in the selected range. "
                   "Transfers and discharges exceed CBP-recorded intake; see *Data notes*.")
    with r:
        st.subheader("Stage throughput (exits ÷ entries)")
        t1 = pd.DataFrame({"Stage": ["CBP stage (transfers ÷ apprehended)", "HHS stage (discharges ÷ transfers)", "End-to-end (discharges ÷ apprehended)"],
                           "Throughput": [k["throughput_cbp_stage"], k["throughput_hhs_stage"], k["throughput_end_to_end"]]})
        fig = go.Figure(go.Bar(x=t1["Throughput"], y=t1["Stage"], orientation="h", marker_color=["#c0504d", "#1f4e79", "#2e7d32"],
                               text=t1["Throughput"].round(2), textposition="outside"))
        fig.add_vline(x=1, line_dash="dash", line_color="grey")
        fig.update_layout(height=340, margin=dict(l=0, r=30, t=10, b=10), yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig, width="stretch")
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=.08,
                        subplot_titles=("Stock: children in each stage", "Flow: daily movement (moving average)"))
    fig.add_trace(go.Scatter(x=d.date, y=d.hhs_census, name="In HHS care", line=dict(color="#1f4e79")), 1, 1)
    fig.add_trace(go.Scatter(x=d.date, y=d.cbp_census, name="In CBP custody", line=dict(color="#c0504d")), 1, 1)
    for col, nm, colr in [("apprehended", "Apprehended", "#888"), ("transferred", "Transferred", "#c0504d"), ("discharged", "Discharged", "#2e7d32")]:
        fig.add_trace(go.Scatter(x=d.date, y=d[col].rolling(max(window, 3)).mean(), name=nm, line=dict(color=colr)), 2, 1)
    fig.update_layout(height=520, margin=dict(t=40, b=10), legend=dict(orientation="h", y=-.08))
    st.plotly_chart(fig, width="stretch")

# ------------------------------------------------------------------ tab 2: efficiency
with tabs[1]:
    n = int(show_cbp) + int(show_hhs)
    if n == 0:
        st.info("Turn on CBP- or HHS-stage metrics in the sidebar.")
    else:
        titles, row = [], 1
        if show_cbp: titles.append("Transfer Efficiency Ratio (transfers ÷ CBP custody)")
        if show_hhs: titles.append("Discharge Effectiveness (% of HHS care discharged per report)")
        fig = make_subplots(rows=n, cols=1, shared_xaxes=True, vertical_spacing=.12, subplot_titles=titles)
        if show_cbp:
            fig.add_trace(go.Scatter(x=d.date, y=d[ter_col], line=dict(color="#c0504d"), name="Transfer efficiency"), row, 1)
            fig.add_hline(y=ter_min, line_dash="dot", line_color="red", row=row, col=1)
            breach(fig, d[ter_col], "lt", ter_min, row); row += 1
        if show_hhs:
            fig.add_trace(go.Scatter(x=d.date, y=d[de_col] * 100, line=dict(color="#2e7d32"), name="Discharge effectiveness (%)"), row, 1)
            fig.add_hline(y=de_min * 100, line_dash="dot", line_color="red", row=row, col=1)
            fig.add_trace(go.Scatter(x=d.date[d[de_col] < de_min], y=d[de_col][d[de_col] < de_min] * 100, mode="markers",
                                     marker=dict(color="red", size=5), showlegend=False), row, 1)
        fig.update_layout(height=250 * n + 120, margin=dict(t=40, b=10), showlegend=False)
        st.plotly_chart(fig, width="stretch")
        st.caption("Red dotted line = your alert threshold; red markers = reports breaching it.")
    w = u.weekday_table(d)
    g = u.gap_table(d)
    l, r = st.columns(2)
    with l:
        st.subheader("By reporting weekday")
        st.dataframe(w[w.reports > 10].style.format({"transferred": "{:.0f}", "discharged": "{:.0f}", "apprehended": "{:.0f}", "transfer_eff": "{:.2f}", "discharge_eff": "{:.2%}"}), width="stretch")
    with r:
        st.subheader("Consecutive-day vs after-gap reports")
        st.dataframe(g.style.format({"transferred": "{:.0f}", "discharged": "{:.0f}", "transfer_eff": "{:.2f}", "discharge_eff": "{:.2%}"}), width="stretch")
    st.caption("The dataset has no Friday/Saturday reports, so a true weekday-vs-weekend test isn't possible; "
               "reports following a 3+ day gap are the closest proxy.")

# ------------------------------------------------------------------ tab 3: bottlenecks
with tabs[2]:
    min_len = st.slider("Minimum length of a 'sustained' imbalance (reports)", 5, 40, 14)
    imb = u.sustained_imbalance(d, "hhs_backlog_rate", min_len)
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=.1,
                        subplot_titles=("Backlog accumulation rate: transfers − discharges (children/report)", "Cumulative net flow into HHS care"))
    fig.add_trace(go.Bar(x=d.date, y=d.hhs_backlog_rate, marker_color=["#d32f2f" if v > bk_max else "#1f4e79" for v in d.hhs_backlog_rate], name="HHS backlog rate"), 1, 1)
    fig.add_trace(go.Scatter(x=d.date, y=d.cbp_backlog_rate, line=dict(color="#c0504d", width=1), name="CBP backlog rate (intake − transfers)"), 1, 1)
    fig.add_hline(y=bk_max, line_dash="dot", line_color="red", row=1, col=1)
    for _, r_ in imb.iterrows():
        fig.add_vrect(x0=r_.start, x1=r_.end, fillcolor="red", opacity=.08, line_width=0, row=1, col=1)
    fig.add_trace(go.Scatter(x=d.date, y=d.hhs_net_flow.cumsum(), line=dict(color="#6a1b9a"), name="Cumulative net flow"), 2, 1)
    fig.update_layout(height=560, margin=dict(t=40, b=10), legend=dict(orientation="h", y=-.08))
    st.plotly_chart(fig, width="stretch")
    st.subheader("Sustained imbalance periods (HHS inflow > exits)")
    if imb.empty:
        st.write("None found in this range at the chosen length.")
    else:
        st.dataframe(imb.assign(start=imb.start.dt.date, end=imb.end.dt.date).round(1), width="stretch", hide_index=True)
    st.subheader("Prolonged low-discharge (stagnation) periods")
    sp = u.stagnation_periods(d)
    st.dataframe(sp.assign(start=sp.start.dt.date, end=sp.end.dt.date).round(4), width="stretch", hide_index=True) if len(sp) else st.write("None in this range.")

# ------------------------------------------------------------------ tab 4: outcomes
with tabs[3]:
    mt = u.monthly_table(d)
    l, r = st.columns(2)
    with l:
        fig = go.Figure(go.Bar(x=mt.index, y=mt.discharged_per_report, marker_color="#2e7d32"))
        fig.update_layout(title="Avg discharges per reporting day, by month", height=340, margin=dict(t=40, b=10))
        st.plotly_chart(fig, width="stretch")
    with r:
        fig = go.Figure(go.Scatter(x=d.date, y=d.stability_score, line=dict(color="#00695c")))
        fig.add_hline(y=st_min, line_dash="dot", line_color="red")
        fig.update_layout(title="Outcome Stability Score (30-report rolling)", yaxis=dict(range=[0, 100]), height=340, margin=dict(t=40, b=10))
        st.plotly_chart(fig, width="stretch")
    dr_pct = st.slider("Sudden-drop sensitivity: min fall in 7-report discharge effectiveness (%)", 20, 80, 35)
    sd = u.sudden_drops(d, 7, dr_pct)
    st.subheader("Sudden drops in reunification success")
    st.dataframe(sd.assign(date=sd.date.dt.date).round(4), width="stretch", hide_index=True) if len(sd) else st.write("No drops at this sensitivity.")
    st.subheader("Monthly summary")
    st.dataframe(mt.round(3), width="stretch")
    st.download_button("Download monthly summary (CSV)", mt.round(4).to_csv().encode(), "monthly_summary.csv")

# ------------------------------------------------------------------ tab 5: notes
with tabs[4]:
    rec = u.reconciliation(d)
    st.markdown(f"""
### How the metrics are defined
| KPI | Definition |
|---|---|
| Transfer Efficiency Ratio | Transfers out of CBP ÷ children in CBP custody |
| Discharge Effectiveness | Discharges from HHS ÷ children in HHS care |
| Pipeline Throughput | Exits ÷ entries per stage and end-to-end (discharges ÷ apprehensions) |
| Backlog Accumulation Rate | Mean of (transfers − discharges) per report; positive = backlog building |
| Outcome Stability Score | 100 × (1 − coefficient of variation of discharge effectiveness) over 30 reports |

### Data caveats (important for interpretation)
* **Reports are not daily.** Only ~5 reports/week, with no Friday/Saturday rows and gaps up to 10 days. Flows are per *report*, not per calendar day.
* **Transfers ÷ custody can exceed 1** (in {(full.transfer_eff > 1).mean():.0%} of reports) because custody is a point-in-time count while transfers happen through the day: treat it as a turnover ratio.
* **Flows don't fully reconcile with the HHS census.** On consecutive-day reports, the census change correlates only r = {rec['corr']:.2f} with (transfers − discharges), and the census rises faster than that in {rec['share_positive']:.0%} of cases: children appear to enter HHS care through routes not captured in the CBP-transfer column, or reporting is timed differently.
* Transfers and discharges both exceed recorded CBP apprehensions, so end-to-end throughput > 1 is not "better than perfect"; it reflects those other entry routes.
* These are aggregate counts: **no length-of-stay or individual outcomes**, so results describe flow efficiency, not case-level delay.
""")
