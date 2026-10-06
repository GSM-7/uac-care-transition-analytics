"""Core metrics for the Care Transition Efficiency & Placement Outcome Analytics project.

Shared by analysis.py (paper figures) and app.py (Streamlit dashboard) so that both
always report identical numbers.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

RAW_COLS = {
    "Date": "date",
    "Children apprehended and placed in CBP custody*": "apprehended",
    "Children in CBP custody": "cbp_census",
    "Children transferred out of CBP custody": "transferred",
    "Children in HHS Care": "hhs_census",
    "Children discharged from HHS Care": "discharged",
}
NUM = ["apprehended", "cbp_census", "transferred", "hhs_census", "discharged"]


def load_data(path_or_buffer) -> pd.DataFrame:
    """Load, clean and sort the raw HHS UAC export (drops the empty trailing rows,
    converts '2,484'-style strings to numbers, parses dates)."""
    df = pd.read_csv(path_or_buffer).dropna(how="all")
    df = df.rename(columns=RAW_COLS)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    for c in NUM:
        df[c] = pd.to_numeric(df[c].astype(str).str.replace(",", ""), errors="coerce")
    df = df.dropna(subset=["date"] + NUM).drop_duplicates("date")
    return df.sort_values("date").reset_index(drop=True)


def add_metrics(df: pd.DataFrame, window: int = 7, stab_window: int = 30) -> pd.DataFrame:
    d = df.copy()
    d["gap_days"] = d["date"].diff().dt.days
    d["post_gap"] = d["gap_days"] >= 3          # report that follows a 3+ day gap
    d["weekday"] = d["date"].dt.day_name()

    # --- Stage ratios (per report) -------------------------------------------------
    d["transfer_eff"] = d["transferred"] / d["cbp_census"]            # Transfers / CBP custody
    d["discharge_eff"] = d["discharged"] / d["hhs_census"]            # Discharges / HHS care

    # --- Flow balance --------------------------------------------------------------
    d["cbp_net_flow"] = d["apprehended"] - d["transferred"]           # >0 => CBP backlog builds
    d["hhs_net_flow"] = d["transferred"] - d["discharged"]            # >0 => HHS backlog builds
    d["hhs_census_change"] = d["hhs_census"].diff()
    d["cum_hhs_net_flow"] = d["hhs_net_flow"].cumsum()

    # --- Rolling (ratio of sums, so busy days weigh more than quiet ones) ----------
    r = d[NUM].rolling(window, min_periods=max(3, window // 2)).sum()
    d["transfer_eff_roll"] = r["transferred"] / d["cbp_census"].rolling(window, min_periods=3).sum()
    d["discharge_eff_roll"] = r["discharged"] / d["hhs_census"].rolling(window, min_periods=3).sum()
    d["hhs_backlog_rate"] = d["hhs_net_flow"].rolling(window, min_periods=3).mean()   # children / report
    d["cbp_backlog_rate"] = d["cbp_net_flow"].rolling(window, min_periods=3).mean()

    # --- Pipeline throughput (exits / entries), 30-report window --------------------
    r30 = d[NUM].rolling(stab_window, min_periods=10).sum()
    d["thr_cbp_stage"] = r30["transferred"] / r30["apprehended"].replace(0, np.nan)
    d["thr_hhs_stage"] = r30["discharged"] / r30["transferred"].replace(0, np.nan)
    d["thr_end_to_end"] = r30["discharged"] / r30["apprehended"].replace(0, np.nan)

    # --- Outcome stability: 100 * (1 - CV of discharge effectiveness), rolling ------
    roll = d["discharge_eff"].rolling(stab_window, min_periods=10)
    cv = roll.std() / roll.mean()
    d["stability_score"] = (100 * (1 - cv.clip(upper=1))).clip(lower=0)
    return d


# ------------------------------------------------------------------------------------
def kpi_summary(d: pd.DataFrame) -> dict:
    tot = d[NUM].sum()
    return {
        "reports": len(d),
        "start": d["date"].min(),
        "end": d["date"].max(),
        "transfer_efficiency": d["transferred"].sum() / d["cbp_census"].sum(),
        "discharge_effectiveness": d["discharged"].sum() / d["hhs_census"].sum(),
        "throughput_cbp_stage": tot["transferred"] / tot["apprehended"] if tot["apprehended"] else np.nan,
        "throughput_hhs_stage": tot["discharged"] / tot["transferred"] if tot["transferred"] else np.nan,
        "throughput_end_to_end": tot["discharged"] / tot["apprehended"] if tot["apprehended"] else np.nan,
        "backlog_rate": d["hhs_net_flow"].mean(),
        "cbp_backlog_rate": d["cbp_net_flow"].mean(),
        "stability": d["stability_score"].mean(),
        "total_apprehended": tot["apprehended"],
        "total_transferred": tot["transferred"],
        "total_discharged": tot["discharged"],
    }


def monthly_table(d: pd.DataFrame) -> pd.DataFrame:
    g = d.groupby(d["date"].dt.to_period("M"))
    m = g.agg(reports=("date", "size"), apprehended=("apprehended", "sum"),
              transferred=("transferred", "sum"), discharged=("discharged", "sum"),
              hhs_avg=("hhs_census", "mean"), cbp_avg=("cbp_census", "mean"),
              cbp_sum=("cbp_census", "sum"), hhs_sum=("hhs_census", "sum"),
              de_std=("discharge_eff", "std"), de_mean=("discharge_eff", "mean"))
    m["transfer_eff"] = m["transferred"] / m["cbp_sum"]
    m["discharge_eff"] = m["discharged"] / m["hhs_sum"]
    m["discharged_per_report"] = m["discharged"] / m["reports"]      # normalises uneven report counts
    m["net_flow_per_report"] = (m["transferred"] - m["discharged"]) / m["reports"]
    m["stability"] = 100 * (1 - (m["de_std"] / m["de_mean"]).clip(upper=1))
    m["discharged_mom_pct"] = m["discharged_per_report"].pct_change() * 100
    m.index = m.index.to_timestamp()
    return m.drop(columns=["cbp_sum", "hhs_sum", "de_std", "de_mean"])


def weekday_table(d: pd.DataFrame) -> pd.DataFrame:
    order = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    g = d.groupby("weekday")
    t = g.agg(reports=("date", "size"), transferred=("transferred", "mean"),
              discharged=("discharged", "mean"), apprehended=("apprehended", "mean"),
              cbp=("cbp_census", "sum"), hhs=("hhs_census", "sum"),
              tr_sum=("transferred", "sum"), dis_sum=("discharged", "sum"))
    t["transfer_eff"] = t["tr_sum"] / t["cbp"]
    t["discharge_eff"] = t["dis_sum"] / t["hhs"]
    t = t.drop(columns=["cbp", "hhs", "tr_sum", "dis_sum"])
    return t.reindex([x for x in order if x in t.index])


def gap_table(d: pd.DataFrame) -> pd.DataFrame:
    """Reports that follow a 3+ day gap (the closest thing to a 'weekend effect' this
    dataset supports - see README on the missing Friday/Saturday records)."""
    x = d.dropna(subset=["gap_days"]).copy()
    x["type"] = np.where(x["post_gap"], "After 3+ day gap", "Consecutive day")
    g = x.groupby("type")
    t = g.agg(reports=("date", "size"), transferred=("transferred", "mean"),
              discharged=("discharged", "mean"), tr=("transferred", "sum"), cbp=("cbp_census", "sum"),
              dis=("discharged", "sum"), hhs=("hhs_census", "sum"))
    t["transfer_eff"] = t["tr"] / t["cbp"]
    t["discharge_eff"] = t["dis"] / t["hhs"]
    return t.drop(columns=["tr", "cbp", "dis", "hhs"])


def _runs(mask: pd.Series) -> list[tuple[int, int]]:
    out, start = [], None
    for i, v in enumerate(mask.to_numpy()):
        if v and start is None:
            start = i
        if not v and start is not None:
            out.append((start, i - 1)); start = None
    if start is not None:
        out.append((start, len(mask) - 1))
    return out


def sustained_imbalance(d: pd.DataFrame, col: str = "hhs_backlog_rate", min_len: int = 14,
                        threshold: float = 0.0) -> pd.DataFrame:
    """Periods where the rolling net flow stays above `threshold` for >= min_len reports."""
    rows = []
    for a, b in _runs(d[col] > threshold):
        if b - a + 1 >= min_len:
            seg = d.iloc[a:b + 1]
            rows.append({"start": seg["date"].iloc[0], "end": seg["date"].iloc[-1],
                         "reports": len(seg), "avg_net_flow": seg[col].mean(),
                         "hhs_census_start": d["hhs_census"].iloc[a],
                         "hhs_census_end": seg["hhs_census"].iloc[-1],
                         "census_change": seg["hhs_census"].iloc[-1] - d["hhs_census"].iloc[a]})
    return pd.DataFrame(rows)


def stagnation_periods(d: pd.DataFrame, quantile: float = 0.25, min_len: int = 10) -> pd.DataFrame:
    """Prolonged stretches where 7-report discharge effectiveness sits in its bottom quartile."""
    thr = d["discharge_eff_roll"].quantile(quantile)
    rows = []
    for a, b in _runs(d["discharge_eff_roll"] < thr):
        if b - a + 1 >= min_len:
            seg = d.iloc[a:b + 1]
            rows.append({"start": seg["date"].iloc[0], "end": seg["date"].iloc[-1],
                         "reports": len(seg), "avg_discharge_eff": seg["discharge_eff_roll"].mean(),
                         "avg_hhs_census": seg["hhs_census"].mean()})
    return pd.DataFrame(rows)


def sudden_drops(d: pd.DataFrame, window: int = 7, drop_pct: float = 35.0) -> pd.DataFrame:
    """Episodes where the `window`-report mean discharge effectiveness falls >= drop_pct %
    versus the preceding window."""
    cur = d["discharge_eff"].rolling(window).mean()
    prev = cur.shift(window)
    chg = (cur / prev - 1) * 100
    rows = []
    for a, b in _runs(chg <= -drop_pct):
        seg = chg.iloc[a:b + 1]
        i = seg.idxmin()
        rows.append({"date": d["date"].iloc[i], "worst_drop_pct": seg.min(),
                     "discharge_eff_before": prev.iloc[i], "discharge_eff_after": cur.iloc[i],
                     "hhs_census": d["hhs_census"].iloc[i]})
    return pd.DataFrame(rows)


def reconciliation(d: pd.DataFrame) -> dict:
    """Does the reported HHS census change match transfers - discharges?
    Only consecutive-day reports are compared (a gap would mix several days of flow)."""
    g = d[d["gap_days"] == 1].copy()
    g["expected"] = g["transferred"] - g["discharged"]
    g["residual"] = g["hhs_census_change"] - g["expected"]
    return {"n": len(g), "corr": float(np.corrcoef(g["hhs_census_change"], g["expected"])[0, 1]),
            "mean_residual": float(g["residual"].mean()), "median_residual": float(g["residual"].median()),
            "share_positive": float((g["residual"] > 0).mean()),
            "cum_residual": float(g["residual"].sum())}
