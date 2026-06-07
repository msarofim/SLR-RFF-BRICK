"""
rennels_7panel_figure.py

7-panel SLR figure for Lisa Rennels (2026-05-30).

LEFT panel:   SSP2-4.5 total GMSLR projection, relative to 2005, with median +
              75% (12.5-87.5) and 90% (5-95) probability bands. The band is the
              UNWEIGHTED spread over (841 FaIR v1.4.5 configs x BRICK posterior
              members) around the deterministic SSP2-4.5 emissions pathway
              (climate + ice-sheet uncertainty; no RFF importance weights, since
              SSP2-4.5 is a single fixed scenario).

RIGHT 2x3:    Sea-level-rise impulse response to a CO2 pulse at 2020, decomposed
              into TE, GSIC, GIS, AIS, LWS, and Total GMSLR. Each panel overlays
              two independent estimates of the per-GtC sensitivity:
                - solid : from a +0.01 GtC pulse (numerically safe), scaled /GtC
                - dashed: from a +1e-4 GtC pulse (Lisa's exact request), scaled /GtC
              Their agreement demonstrates the response is linear and that the
              1e-4 GtC pulse is resolvable through BRICK (float64). Central line
              is the MEDIAN across the ensemble (pulse-size-invariant; robust to
              the AIS-tipping tail). Units: mm of SLR per GtC of CO2 pulse.

Pulse unit:  Lisa specified GtC (carbon mass). FaIR v1.4.5 CO2 FFI input_unit is
             GtCO2, so 1 GtC = 44/12 = 3.6667 GtCO2 was applied in the driver.
             Per-GtC sensitivity here = (per-GtCO2 sensitivity) x 3.6667.

Inputs (from rennels_build_ssp245_cubes.py + run_mimibrick_flatcube.jl):
    outputs/rennels/brick_full_baseline.csv
    outputs/rennels/brick_full_pulse_p001.csv     (+0.01 GtC)
    outputs/rennels/brick_full_pulse_p1em4.csv     (+1e-4 GtC)

Outputs:
    outputs/rennels/slr_7panel_ssp245.{png,pdf}
    outputs/rennels/rennels_pulse_response_summary.csv

Run:
    source ~/climate-env/bin/activate
    python python/scripts/rennels/rennels_7panel_figure.py
"""

from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

# ── Named constants (labels/filters derive from these) ──────────────────────────
ROOT     = Path("/Users/MarcusMarcus/Documents/2026/CodeProjects/SLR-RFF-BRICK")
OUT_DIR  = ROOT / "outputs" / "rennels"
KEYS     = ["rff_idx", "fair_cfg_idx", "seed_idx", "post_idx"]
COMPS    = ["te", "gsic", "gis", "ais", "lws"]
COMP_LABEL = {"te": "Thermal expansion (TE)", "gsic": "Glaciers (GSIC)",
              "gis": "Greenland (GIS)", "ais": "Antarctica (AIS)",
              "lws": "Land water storage (LWS)", "total": "Total GMSLR"}

SCENARIO   = "SSP2-4.5"
FAIR_LABEL = "FaIR v2.2.4 (v1.4.5 calibration, 841 configs)"
BRICK_LABEL = "MimiBRICK post-PR#93 posterior (Wong 2026)"
REBASE_YEAR = 2005          # left panel: SLR relative to this year
LEFT_END    = 2150          # left panel x-max
PULSE_YEAR  = 2020          # impulse-response start
RIGHT_END   = 2300          # right panels x-max

C_TO_CO2    = 44.0 / 12.0
P001_GTC    = 0.01          # GtC
P1EM4_GTC   = 1.0e-4        # GtC
CM_TO_MM    = 10.0

# colours (mirror poster/slr_band.py house style)
BAND_C   = "#1F4E79"
MEAN_C   = "#A6361C"
P001_C   = "#1F4E79"        # 0.01 GtC arm (reference)
P1EM4_C  = "#A6361C"        # 1e-4 GtC arm (Lisa's request)

YEARS = np.arange(1850, 2301)


def load(arm):
    df = pd.read_csv(OUT_DIR / f"brick_full_{arm}.csv").sort_values(KEYS).reset_index(drop=True)
    return df


def comp_traj(df, comp):
    cols = [f"{comp}_{y}" for y in range(1850, 2301)]
    return df[cols].to_numpy()                       # (n_cells, n_year), cm rel 2000


def total_traj(df):
    return sum(comp_traj(df, c) for c in COMPS)      # cm rel 2000


def main():
    base  = load("baseline")
    p001  = load("pulse_p001")
    p1em4 = load("pulse_p1em4")
    for arm in (p001, p1em4):
        assert (base[KEYS].values == arm[KEYS].values).all(), "pairing mismatch"
    n = len(base)
    print(f"Loaded {n} paired draws (= {base.fair_cfg_idx.nunique()} cfg "
          f"x {n // base.fair_cfg_idx.nunique()} posts).")

    # ── LEFT panel data: total SLR rel 2005, unweighted percentiles ─────────────
    tot = total_traj(base)                            # (n, n_year), cm rel 2000
    i_rebase = int(np.where(YEARS == REBASE_YEAR)[0][0])
    tot = tot - tot[:, [i_rebase]]                    # rel 2005, per draw
    qs = {q: np.percentile(tot, q, axis=0) for q in (5, 12.5, 50, 87.5, 95)}

    # ── RIGHT panels data: per-cell marginal (cm) for each arm ──────────────────
    # marginal(t) = pulse - baseline (cm); 2000-anchor cancels (pulse==base pre-2020)
    tot_raw = total_traj(base)                        # baseline total rel 2000 (un-rebased)

    def marg_cm(arm_df, comp):
        if comp == "total":
            return total_traj(arm_df) - tot_raw
        return comp_traj(arm_df, comp) - comp_traj(base, comp)   # (n_cells, n_year), cm

    panel_order = ["total", "te", "gsic", "gis", "ais", "lws"]
    positions = [(0, 2), (0, 3), (0, 4), (1, 2), (1, 3), (1, 4)]
    yr_mask_r = (YEARS >= PULSE_YEAR) & (YEARS <= RIGHT_END)
    yr_r = YEARS[yr_mask_r]

    # Two presentation modes:
    #   per_gtc  : both arms normalised per GtC (mm/GtC) -> overlap == linearity
    #   abs1em4  : absolute SLR response to the literal +1e-4 GtC pulse (metres);
    #              direct 1e-4 (markers) vs 0.01-arm-scaled-down (line); divergence
    #              of the direct 1e-4 markers = float/seed noise floor.
    MODES = {
        "per_gtc": dict(
            ref=lambda m: np.median(m, axis=0) / P001_GTC * CM_TO_MM,        # mm/GtC
            ref_all=lambda m: m / P001_GTC * CM_TO_MM,
            direct=lambda m: np.median(m, axis=0) / P1EM4_GTC * CM_TO_MM,
            ylabel="SLR response\n(mm per GtC pulse)",
            ref_label="median, +0.01 GtC (per GtC)",
            dir_label="median, +1e-4 GtC (per GtC)",
            band_label="5–95% (0.01 GtC arm)",
            note="two pulse sizes agree\n→ linear & resolvable",
            fname="slr_7panel_ssp245", sci=False,
            sub="per-GtC normalised impulse response (mm / GtC)"),
        "abs1em4": dict(
            ref=lambda m: np.median(m, axis=0) * (P1EM4_GTC / P001_GTC) / 100.0,  # m
            ref_all=lambda m: m * (P1EM4_GTC / P001_GTC) / 100.0,
            direct=lambda m: np.median(m, axis=0) / 100.0,                        # m (literal)
            ylabel="SLR response to\n+1e-4 GtC pulse (m)",
            ref_label="median, +0.01 GtC ÷100 (clean ref)",
            dir_label="median, +1e-4 GtC (direct)",
            band_label="5–95% (0.01 GtC ÷100)",
            note="direct 1e-4 vs 0.01÷100:\nagreement ⇒ real signal",
            fname="slr_7panel_ssp245_abs1em4", sci=True,
            sub="absolute response to a +1e-4 GtC pulse (m)"),
    }

    summary_rows = []
    for mode, cfg in MODES.items():
        fig = plt.figure(figsize=(17, 8.5))
        gs = GridSpec(2, 5, figure=fig, width_ratios=[1.9, 0.15, 1, 1, 1],
                      height_ratios=[1, 1], hspace=0.32, wspace=0.34,
                      left=0.05, right=0.985, top=0.86, bottom=0.09)

        # ── LEFT (shared) ────────────────────────────────────────────────────────
        axL = fig.add_subplot(gs[:, 0])
        yr_mask = (YEARS >= REBASE_YEAR) & (YEARS <= LEFT_END)
        yy = YEARS[yr_mask]
        axL.fill_between(yy, qs[5][yr_mask], qs[95][yr_mask], color=BAND_C, alpha=0.16,
                         label="90% (5–95%)")
        axL.fill_between(yy, qs[12.5][yr_mask], qs[87.5][yr_mask], color=BAND_C, alpha=0.34,
                         label="75% (12.5–87.5%)")
        axL.plot(yy, qs[50][yr_mask], color=BAND_C, lw=2.6, label="Median")
        for ytxt in (2050, 2100, 2150):
            if ytxt <= LEFT_END:
                j = int(np.where(YEARS == ytxt)[0][0])
                axL.annotate(f"{qs[50][j]:.0f} cm\n[{qs[5][j]:.0f}–{qs[95][j]:.0f}]",
                             (ytxt, qs[50][j]), fontsize=8.5, ha="center", va="bottom",
                             color=BAND_C, xytext=(0, 6), textcoords="offset points")
        axL.set_xlim(REBASE_YEAR, LEFT_END)
        axL.set_ylim(bottom=min(0, qs[5][yr_mask].min()))
        axL.set_xlabel("Year")
        axL.set_ylabel(f"Global mean sea-level rise (cm, rel. {REBASE_YEAR})")
        axL.set_title(f"{SCENARIO} sea-level rise\nclimate + ice-sheet uncertainty",
                      fontsize=11, loc="left")
        axL.grid(alpha=0.3, lw=0.5)
        axL.legend(loc="upper left", fontsize=9, framealpha=0.92)
        axL.text(0.03, 0.62,
                 "Unweighted spread over\n841 configs × 8 BRICK posteriors.\n"
                 "No obs. importance-weighting:\nruns above AR6 SSP2-4.5\n"
                 "(BRICK posterior, this project).",
                 transform=axL.transAxes, fontsize=7.3, ha="left", va="top",
                 color="0.4", style="italic")

        # ── RIGHT 2x3 ──────────────────────────────────────────────────────────────
        mk = (yr_r >= PULSE_YEAR) & ((yr_r - PULSE_YEAR) % 20 == 0)
        for comp, (r, c) in zip(panel_order, positions):
            ax = fig.add_subplot(gs[r, c])
            m001 = marg_cm(p001, comp)
            m1em4 = marg_cm(p1em4, comp)
            ref_med = cfg["ref"](m001)
            ref_all = cfg["ref_all"](m001)
            dir_med = cfg["direct"](m1em4)
            p5 = np.percentile(ref_all, 5, axis=0)
            p95 = np.percentile(ref_all, 95, axis=0)
            ax.fill_between(yr_r, p5[yr_mask_r], p95[yr_mask_r], color=P001_C, alpha=0.12,
                            label=cfg["band_label"])
            ax.plot(yr_r, ref_med[yr_mask_r], color=P001_C, lw=2.2, label=cfg["ref_label"])
            ax.plot(yr_r[mk], dir_med[yr_mask_r][mk], color=P1EM4_C, ls="none",
                    marker="o", ms=4.5, mfc="none", mew=1.3, label=cfg["dir_label"])
            ax.axhline(0, color="0.6", lw=0.6)
            ax.set_title(COMP_LABEL[comp], fontsize=9.5)
            ax.grid(alpha=0.3, lw=0.5)
            ax.tick_params(labelsize=8)
            if cfg["sci"]:
                ax.ticklabel_format(axis="y", style="sci", scilimits=(0, 0))
                ax.yaxis.get_offset_text().set_fontsize(7)
            if r == 1:
                ax.set_xlabel("Year", fontsize=9)
            if c == 2:
                ax.set_ylabel(cfg["ylabel"], fontsize=9)
            if comp == "total":
                ax.legend(loc="upper left", fontsize=7.0, framealpha=0.9)
                ax.text(0.97, 0.05, cfg["note"], transform=ax.transAxes, fontsize=7,
                        ha="right", va="bottom", style="italic", color="0.35")
            if comp == "lws":
                ax.text(0.5, 0.5, "≈ 0\n(LWS = 0 pre-2019\nby calibration)",
                        transform=ax.transAxes, fontsize=8, ha="center", va="center",
                        color="0.45")

            if mode == "per_gtc":   # collect summary once
                for yv in (2100, 2150, 2300):
                    j = int(np.where(YEARS == yv)[0][0])
                    summary_rows.append(dict(
                        component=comp, year=yv,
                        mm_per_GtC_from_001=np.median(m001, axis=0)[j] / P001_GTC * CM_TO_MM,
                        mm_per_GtC_from_1em4=np.median(m1em4, axis=0)[j] / P1EM4_GTC * CM_TO_MM,
                        cm_per_GtCO2_from_001=np.median(m001, axis=0)[j] / P001_GTC / C_TO_CO2,
                        abs_m_for_1em4_from_001=np.median(m001, axis=0)[j] * (P1EM4_GTC / P001_GTC) / 100.0,
                        abs_m_for_1em4_direct=np.median(m1em4, axis=0)[j] / 100.0,
                    ))

        fig.suptitle(
            f"SSP2-4.5 sea-level rise and the SLR impulse response to a {PULSE_YEAR} CO₂ pulse\n"
            f"{cfg['sub']}  •  {FAIR_LABEL}  •  {BRICK_LABEL}  •  1 GtC = 44/12 GtCO₂",
            fontsize=11, y=0.985)
        png = OUT_DIR / f"{cfg['fname']}.png"
        pdf = OUT_DIR / f"{cfg['fname']}.pdf"
        fig.savefig(png, dpi=200)
        fig.savefig(pdf)
        plt.close(fig)
        print(f"Wrote {png}\nWrote {pdf}")

    summ = pd.DataFrame(summary_rows)
    summ_path = OUT_DIR / "rennels_pulse_response_summary.csv"
    summ.to_csv(summ_path, index=False)
    print(f"Wrote {summ_path}")
    print("\n── Absolute SLR response to a +1e-4 GtC pulse (median, metres) ──")
    piv = summ.pivot(index="component", columns="year", values="abs_m_for_1em4_direct")
    print(piv.reindex(panel_order).map(lambda v: f"{v:+.3e}").to_string())
    print("\nDirect-1e-4 vs 0.01÷100 agreement, % diff @2150 (per-cell-median):")
    for comp in panel_order:
        a = summ[(summ.component == comp) & (summ.year == 2150)].iloc[0]
        d = abs(a.abs_m_for_1em4_direct - a.abs_m_for_1em4_from_001) / max(abs(a.abs_m_for_1em4_from_001), 1e-30) * 100
        print(f"   {comp:>5}: direct={a.abs_m_for_1em4_direct:+.3e} m  ref={a.abs_m_for_1em4_from_001:+.3e} m  diff={d:6.2f}%")


if __name__ == "__main__":
    main()
