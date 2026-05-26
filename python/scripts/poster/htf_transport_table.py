"""
htf_transport_table.py
======================

Render the Panel I figure for the SLR poster:
  Top inset:  small bar chart comparing Coastal Properties vs HTF
              Transportation annual damages at 2100 and 2150, with P5–P95
              whiskers.
  Main:       quantile table for the two sectors plus a TOTAL row computed
              statistically correctly from per-draw sums (CP + HTF per
              (draw_idx, year)), then re-quantiled — not naively additive
              percentile sums.

Inputs (v1.4.5 SIR-resampled 1000-draw rerun; v1.4.1 quarantined):
  outputs/fredi_slr_phaseC_rff_baseline_v145_quantiles.csv  (per-sector quantiles)
  outputs/fredi_slr_phaseC_rff_baseline_v145_long.csv       (per-draw values; used
                                                             to derive the TOTAL
                                                             row's correct quantiles)

Output:
  outputs/poster/htf_transport_table.{png,pdf}
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "outputs" / "poster"
OUT.mkdir(parents=True, exist_ok=True)

QUANTILES_CSV = ROOT / "outputs" / "fredi_slr_phaseC_rff_baseline_v145_quantiles.csv"
LONG_CSV      = ROOT / "outputs" / "fredi_slr_phaseC_rff_baseline_v145_long.csv"

# Years to show on the poster table.  2050/2075/2125 dropped per poster review
# (May 16, 2026): 2050 N=284/500 due to BRICK lower tail < Sweet 'Low' floor;
# 2075 N=472. 2100 (N=490) and 2150 (N=500) clear FrEDI's floor for ~all
# draws, so they are the only honest reports.
YEARS = [2100, 2150]

SECTOR_CP  = ("Coastal Properties", "Reactive Adaptation")
SECTOR_HTF = ("Transportation Impacts from High Tide Flooding",
              "Reasonably Anticipated Adaptation")
SECTORS = [SECTOR_CP, SECTOR_HTF]
SECTOR_LABEL = {
    SECTOR_CP:  "Coastal Properties",
    SECTOR_HTF: "HTF Transportation",
}
SECTOR_COLOR = {
    SECTOR_CP:  "#1F4E79",
    SECTOR_HTF: "#E67E22",
}
TOTAL_COLOR = "#A6361C"


# ----------------------------------------------------------------------------
def fmt_b(usd):
    """Format dollars as $X.X B or $XX B."""
    if np.isnan(usd):
        return "—"
    b = usd / 1e9
    if b < 10:
        return f"${b:.1f} B"
    return f"${b:.0f} B"


def weighted_quantile(values, weights, q):
    mask = np.isfinite(values) & np.isfinite(weights) & (weights > 0)
    v = values[mask].astype(float)
    w = weights[mask].astype(float)
    if len(v) == 0 or w.sum() == 0:
        return float("nan")
    order = np.argsort(v)
    v, w = v[order], w[order]
    cw = np.cumsum(w)
    idx = np.searchsorted(cw, q * cw[-1])
    return float(v[min(idx, len(v) - 1)])


def compute_total_quantiles(long_df, years):
    """Sum (CP + HTF) annual_impacts per (draw_idx, year), then weighted
    quantiles. Returns DataFrame with columns year/P5/P50/P95/mean/N."""
    cp = long_df[(long_df.sector == SECTOR_CP[0])
                 & (long_df.variant == SECTOR_CP[1])
                 & (long_df.year.isin(years))]
    htf = long_df[(long_df.sector == SECTOR_HTF[0])
                  & (long_df.variant == SECTOR_HTF[1])
                  & (long_df.year.isin(years))]
    # Inner-join on (draw_idx, year) so we sum only when BOTH have data.
    merged = cp.merge(htf, on=["draw_idx", "year", "w_norm"],
                      suffixes=("_cp", "_htf"))
    merged["total"] = merged["annual_impacts_cp"] + merged["annual_impacts_htf"]
    rows = []
    for y in years:
        sub = merged[merged.year == y]
        v = sub["total"].to_numpy()
        w = sub["w_norm"].to_numpy()
        rows.append({
            "year": y,
            "P5":   weighted_quantile(v, w, 0.05),
            "P50":  weighted_quantile(v, w, 0.50),
            "P95":  weighted_quantile(v, w, 0.95),
            "mean": float(np.average(v, weights=w)) if w.sum() > 0 else np.nan,
            "N":    int(len(v)),
        })
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------
def draw_bar_inset(ax_bar, quant_df, total_df):
    """Vertical grouped bar chart: P5-P95 whiskers + median bar for CP, HTF,
    Total at each of the YEARS."""
    n_year = len(YEARS)
    # x positions for each year group
    x_year = np.arange(n_year)
    bar_w = 0.24
    offsets = {SECTOR_CP: -bar_w, SECTOR_HTF: 0.0, "Total": +bar_w}

    def _get_row(sec_tuple, y):
        sub = quant_df[(quant_df.sector == sec_tuple[0])
                       & (quant_df.variant == sec_tuple[1])
                       & (quant_df.year == y)]
        return sub.iloc[0] if len(sub) else None

    for sec in SECTORS:
        color = SECTOR_COLOR[sec]
        medians, errs_lo, errs_hi = [], [], []
        for y in YEARS:
            r = _get_row(sec, y)
            if r is None:
                medians.append(np.nan); errs_lo.append(0); errs_hi.append(0)
            else:
                m = r["P50"] / 1e9
                medians.append(m)
                errs_lo.append(m - r["P5"] / 1e9)
                errs_hi.append(r["P95"] / 1e9 - m)
        xs = x_year + offsets[sec]
        ax_bar.bar(xs, medians, bar_w, color=color, alpha=0.85,
                   edgecolor="white", linewidth=0.8,
                   label=SECTOR_LABEL[sec])
        ax_bar.errorbar(xs, medians, yerr=[errs_lo, errs_hi],
                        fmt="none", color="#333", capsize=3,
                        linewidth=1.0)

    # Total bars
    medians_tot, lo_tot, hi_tot = [], [], []
    for y in YEARS:
        r = total_df[total_df.year == y].iloc[0]
        m = r["P50"] / 1e9
        medians_tot.append(m)
        lo_tot.append(m - r["P5"] / 1e9)
        hi_tot.append(r["P95"] / 1e9 - m)
    xs_tot = x_year + offsets["Total"]
    ax_bar.bar(xs_tot, medians_tot, bar_w, color=TOTAL_COLOR, alpha=0.85,
               edgecolor="white", linewidth=0.8, label="Total (CP + HTF)")
    ax_bar.errorbar(xs_tot, medians_tot, yerr=[lo_tot, hi_tot],
                    fmt="none", color="#333", capsize=3, linewidth=1.0)

    ax_bar.set_xticks(x_year)
    ax_bar.set_xticklabels([str(y) for y in YEARS], fontsize=10)
    ax_bar.set_ylabel("Annual damages\n(2015 USD billions)", fontsize=9)
    ax_bar.legend(loc="upper left", fontsize=8.5, framealpha=0.92, ncol=3)
    ax_bar.grid(axis="y", alpha=0.3, linewidth=0.5)
    ax_bar.spines[["top", "right"]].set_visible(False)
    # Buffer above tallest whisker so legend doesn't overlap the bars
    max_top = max(
        max(r["P95"] / 1e9 for _, r in quant_df.iterrows()),
        total_df["P95"].max() / 1e9,
    )
    ax_bar.set_ylim(0, max_top * 1.30)
    ax_bar.set_title("Bars = median;  whiskers = 5th–95th percentile",
                     fontsize=9, color="#555", loc="left")


# ----------------------------------------------------------------------------
def main():
    if not QUANTILES_CSV.exists():
        raise SystemExit(f"Missing quantile CSV: {QUANTILES_CSV}")
    if not LONG_CSV.exists():
        raise SystemExit(f"Missing long CSV: {LONG_CSV}")
    df = pd.read_csv(QUANTILES_CSV)
    df = df[df["year"].isin(YEARS)].copy()

    # Per-draw sums → Total quantiles (statistically correct, not P50_cp + P50_htf)
    long_df = pd.read_csv(LONG_CSV)
    total_df = compute_total_quantiles(long_df, YEARS)
    print("Per-draw Total quantiles:")
    print(total_df.to_string(index=False))

    # ============================================================== figure
    # 2-row × 3-col gridspec: bar chart sits in the centered middle column
    # of the top row (narrower than full width per poster review May 18);
    # table spans the full width of the bottom row.
    fig = plt.figure(figsize=(11.0, 7.0))
    gs = fig.add_gridspec(2, 3,
                          height_ratios=[0.5, 1.0],
                          width_ratios=[0.15, 0.70, 0.15],
                          hspace=0.35, wspace=0.0)
    ax_bar   = fig.add_subplot(gs[0, 1])
    ax_table = fig.add_subplot(gs[1, :])
    ax_table.axis("off")

    draw_bar_inset(ax_bar, df, total_df)

    # ============================================================== table
    # N column dropped (2026-05-25): with the v1.4.5 SIR-resampled
    # 1000-draw ensemble, all draws clear FrEDI's floor at every
    # reported year, so N is invariant and a column slot was wasted.
    header = ["", "Year", "P5", "Median (P50)", "P95", "Mean"]
    rows = []
    for sec_tuple in SECTORS:
        sub = df[(df["sector"] == sec_tuple[0])
                 & (df["variant"] == sec_tuple[1])]
        if sub.empty:
            continue
        sec_label = SECTOR_LABEL[sec_tuple]
        rows.append([sec_label, "", "", "", "", ""])
        for _, r in sub.iterrows():
            rows.append([
                "", f"{int(r['year'])}",
                fmt_b(r["P5"]), fmt_b(r["P50"]), fmt_b(r["P95"]),
                fmt_b(r["mean"]),
            ])

    # TOTAL section
    rows.append(["Total (CP + HTF)", "", "", "", "", ""])
    for _, r in total_df.iterrows():
        rows.append([
            "", f"{int(r['year'])}",
            fmt_b(r["P5"]), fmt_b(r["P50"]), fmt_b(r["P95"]),
            fmt_b(r["mean"]),
        ])

    table_data = [header] + rows
    col_widths = [0.24, 0.10, 0.14, 0.18, 0.14, 0.14]
    table = ax_table.table(cellText=table_data, colWidths=col_widths,
                           cellLoc="center", loc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 1.55)

    for r in range(len(table_data)):
        for c in range(len(col_widths)):
            cell = table[(r, c)]
            cell.set_edgecolor("#cccccc")
            cell.set_linewidth(0.6)
            if r == 0:
                cell.set_facecolor("#1F4E79")
                cell.set_text_props(color="white", fontweight="bold")
            elif table_data[r][1] == "" and table_data[r][0] != "":
                # Section-header row
                cell.set_facecolor("#E0E6EE")
                cell.set_text_props(color="#1F4E79", fontweight="bold",
                                    style="italic")
                if "Total" in table_data[r][0]:
                    cell.set_facecolor("#FFE9DC")
                    cell.set_text_props(color=TOTAL_COLOR, fontweight="bold",
                                        style="italic")
            if c == 0 and table_data[r][1] == "":
                cell.set_text_props(ha="left")

    fig.tight_layout(rect=[0, 0.02, 1, 0.97])
    fig.savefig(OUT / "htf_transport_table.png", dpi=300, bbox_inches="tight")
    fig.savefig(OUT / "htf_transport_table.pdf", bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {OUT / 'htf_transport_table.png'}")


if __name__ == "__main__":
    main()
