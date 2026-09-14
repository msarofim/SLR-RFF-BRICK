#!/usr/bin/env python3
"""diag_gsic_blocks_vs_emulandice.py — Ladrillo L24 glacier blocks vs FACTS emulandice, per
block, on the SAME 200 FaIR configs (sample-matched), 2005-2100.

WHAT IS COMPARED. emulandice (Edwards et al. 2021: GP emulators of the GlacierMIP2
transient runs, one per RGI region, GSAT-driven, 2015-2100) as FACTS ran it on the shared
climate (facts/experiments/global.shared.<scen>.n200, per-region outputs glac1..glac19,
decadal 2020-2100, base year 2005). Regions are summed to Ladrillo's blocks:
    SLOWG (code SLOWP) = RGI 03, 09, 07, 06
    FASTG (code FAST)  = the 13 others except 05 and 19
    RGI19              = 19
    RGI05 is dropped from emulandice (Ladrillo carries it in the Greenland target).
Ladrillo: julia/diag_gsic_blocks_vs_emulandice.jl, arm `joint` = posterior draw k on shared
sample k (the like-for-like arm), arm `fixed` = every draw on the mean shared path, arm
`joint_cmip6amp` = joint with each block's amplification overridden by the CMIP6
regional-characteristic ratio (the driver lever; table columns only).

BASELINE. Both series are re-referenced to 2005: FACTS by construction (baseyear 2005),
Ladrillo by subtracting its own 2005 value. A single-year rebase is acceptable here ONLY
because both are deterministic smooth model series on a smooth spliced driver (no
interannual noise to alias); it is not the convention for observational series.

PAIRING. Ladrillo sample k and emulandice sample k saw the same GSAT path, so the paired
difference (Ladrillo_k - emulandice_k) removes the climate spread; its median and 5-95%
are reported per block next to the unpaired medians.

Writes outputs/diag_gsic_blocks_vs_emulandice.csv and figures/diag_gsic_blocks_vs_emulandice.png.
    python3 python/diag_gsic_blocks_vs_emulandice.py [--scens=ssp126,ssp245,ssp585,vvVL,vvH]
"""
import os
import sys
import subprocess
import numpy as np
import pandas as pd
import netCDF4 as nc4
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FACTS = os.path.expanduser("~/Documents/2026/CodeProjects/facts/experiments")
IN_DIR = os.path.join(REPO, "outputs", "diag_emu_blocks")
OUT_CSV = os.path.join(REPO, "outputs", "diag_gsic_blocks_vs_emulandice.csv")
OUT_PNG = os.path.join(REPO, "figures", "diag_gsic_blocks_vs_emulandice.png")
SCENS_DEFAULT = ["ssp126", "ssp245", "ssp585", "vvVL", "vvH"]
LABEL = {"ssp126": "SSP1-2.6", "ssp245": "SSP2-4.5", "ssp585": "SSP5-8.5",
         "vvVL": "vv Very Low", "vvH": "vv High"}
BLOCKS = {"SLOWG": [3, 9, 7, 6],
          "FASTG": [1, 2, 4, 8, 10, 11, 12, 13, 14, 15, 16, 17, 18],
          "RGI19": [19]}
CODE_NAME = {"SLOWG": "SLOWP", "FASTG": "FAST", "RGI19": "R19"}   # names in the Julia output
BASE_YEAR = 2005
EMU_YEARS = list(range(2020, 2101, 10))
ARM = "joint"                     # the like-for-like arm; `fixed` is reported in the table only
EMU_LABEL = "FACTS emulandice (GlacierMIP2 GP, GSAT-driven)"
LAD_LABEL = "Ladrillo L24 (joint: draw k on shared sample k)"
TITLE = "Glacier melt since 2005 by block — Ladrillo L24 vs emulandice on the SAME 200 FaIR configs"


def commit():
    return subprocess.run(["git", "-C", REPO, "rev-parse", "--short", "HEAD"],
                          capture_output=True, text=True).stdout.strip() or "UNKNOWN"


def emulandice_blocks(scen):
    """{block: array (samples x EMU_YEARS)} in cm rel 2005, summed over the block's regions."""
    d = os.path.join(FACTS, f"global.shared.{scen}.n200", "output")
    out = {}
    for b, regs in BLOCKS.items():
        acc = None
        for r in regs:
            f = os.path.join(d, f"global.shared.{scen}.n200.emuglaciers.emulandice.glaciers_glac{r}_globalsl.nc")
            if not os.path.exists(f):
                raise SystemExit(f"missing {f}")
            ds = nc4.Dataset(f)
            yrs = [int(y) for y in ds.variables["years"][:]]
            assert yrs == EMU_YEARS, f"{f}: years {yrs}"
            assert int(ds.baseyear) == BASE_YEAR, f"{f}: baseyear {ds.baseyear}"
            x = np.asarray(ds.variables["sea_level_change"][:, :, 0], dtype=float) / 10.0   # mm -> cm
            acc = x if acc is None else acc + x
        out[b] = acc
    return out


def ladrillo_blocks(scen, arm):
    """{block: array (samples x EMU_YEARS)} in cm rel 2005 from the Julia dump."""
    f = os.path.join(IN_DIR, f"ladrillo_blocks_{scen}.csv")
    if not os.path.exists(f):
        raise SystemExit(f"missing {f} — run julia/diag_gsic_blocks_vs_emulandice.jl --scen={scen}")
    d = pd.read_csv(f)
    d = d[d.arm == arm]
    out = {}
    for b, code in CODE_NAME.items():
        w = d[d.block == code].pivot(index="sample", columns="year", values="melt_cm").sort_index()
        base = w[BASE_YEAR].values[:, None]
        out[b] = (w[EMU_YEARS].values - base)
    prov = open(f.replace('.csv', '_provenance.txt')).read().strip()
    return out, prov


def summarise(scens):
    rows = []
    fig, axes = plt.subplots(len(BLOCKS) + 1, len(scens), figsize=(3.6 * len(scens), 2.9 * (len(BLOCKS) + 1)),
                             sharex=True)
    prov = None
    for j, scen in enumerate(scens):
        emu = emulandice_blocks(scen)
        lad, prov = ladrillo_blocks(scen, ARM)
        ladf, _ = ladrillo_blocks(scen, "fixed")
        lada, _ = ladrillo_blocks(scen, "joint_cmip6amp")
        n = min(emu["SLOWG"].shape[0], lad["SLOWG"].shape[0])
        # [SAMPLE-COUNT] the pairing is by index; both sides must carry the same n
        assert emu["SLOWG"].shape[0] == lad["SLOWG"].shape[0] == n, (scen, emu["SLOWG"].shape, lad["SLOWG"].shape)
        panels = list(BLOCKS) + ["sum (excl. RGI 05)"]
        for i, b in enumerate(panels):
            if b in BLOCKS:
                e, l, lf, la = emu[b], lad[b], ladf[b], lada[b]
            else:
                e = sum(emu[k] for k in BLOCKS); l = sum(lad[k] for k in BLOCKS)
                lf = sum(ladf[k] for k in BLOCKS); la = sum(lada[k] for k in BLOCKS)
            i21 = EMU_YEARS.index(2100)
            diff = l[:, i21] - e[:, i21]
            rows.append(dict(scen=scen, block=b, year=2100, n=n,
                             emu_med=np.median(e[:, i21]), emu_p05=np.percentile(e[:, i21], 5), emu_p95=np.percentile(e[:, i21], 95),
                             lad_med=np.median(l[:, i21]), lad_p05=np.percentile(l[:, i21], 5), lad_p95=np.percentile(l[:, i21], 95),
                             lad_fixed_med=np.median(lf[:, i21]), lad_fixed_p05=np.percentile(lf[:, i21], 5), lad_fixed_p95=np.percentile(lf[:, i21], 95),
                             lad_cmip6amp_med=np.median(la[:, i21]), lad_cmip6amp_p05=np.percentile(la[:, i21], 5), lad_cmip6amp_p95=np.percentile(la[:, i21], 95),
                             ratio_cmip6amp=np.median(la[:, i21]) / np.median(e[:, i21]),
                             paired_diff_med=np.median(diff), paired_diff_p05=np.percentile(diff, 5), paired_diff_p95=np.percentile(diff, 95),
                             ratio_of_medians=np.median(l[:, i21]) / np.median(e[:, i21]),
                             frac_samples_lad_below=np.mean(diff < 0)))
            ax = axes[i, j]
            for arr, c, lab in ((e, "#1f77b4", EMU_LABEL), (l, "#d62728", LAD_LABEL)):
                ax.plot(EMU_YEARS, np.median(arr, 0), color=c, lw=2, label=lab)
                ax.fill_between(EMU_YEARS, np.percentile(arr, 5, 0), np.percentile(arr, 95, 0), color=c, alpha=0.15)
            if i == 0:
                ax.set_title(LABEL[scen])
            if j == 0:
                ax.set_ylabel(f"{b}\ncm since {BASE_YEAR}")
            ax.grid(alpha=0.3)
    axes[0, 0].legend(fontsize=7, loc="upper left")
    fig.suptitle(f"{TITLE}\nmedian and 5–95% over the {n} matched samples; emulandice regions summed to Ladrillo's blocks, RGI 05 dropped; commit {commit()}", fontsize=9)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    os.makedirs(os.path.dirname(OUT_PNG), exist_ok=True)
    fig.savefig(OUT_PNG, dpi=130)
    t = pd.DataFrame(rows)
    t["provenance"] = (f"{os.path.basename(__file__)} @ {commit()}; emulandice from FACTS global.shared.<scen>.n200 "
                       f"per-region glac*.nc (base {BASE_YEAR}, mm->cm); Ladrillo: {prov}")
    t.to_csv(OUT_CSV, index=False, float_format="%.4f")
    return t


if __name__ == "__main__":
    scens = [a.split("=", 1)[1].split(",") for a in sys.argv[1:] if a.startswith("--scens=")]
    scens = scens[0] if scens else SCENS_DEFAULT
    t = summarise(scens)
    print(f"\n2100 glacier melt since {BASE_YEAR} (cm), {ARM} arm vs emulandice, matched samples")
    print(f"{'scen':8s} {'block':18s} {'emu med [5-95]':22s} {'Ladrillo med [5-95]':22s} {'ratio':>6s} {'paired diff med [5-95]':>26s} {'frac<0':>7s} {'CMIP6-amp med':>14s} {'ratio':>6s}")
    for r in t.itertuples():
        print(f"{r.scen:8s} {r.block:18s} {r.emu_med:5.2f} [{r.emu_p05:5.2f},{r.emu_p95:5.2f}]     "
              f"{r.lad_med:5.2f} [{r.lad_p05:5.2f},{r.lad_p95:5.2f}]     {r.ratio_of_medians:6.2f} "
              f"{r.paired_diff_med:8.2f} [{r.paired_diff_p05:6.2f},{r.paired_diff_p95:6.2f}]   {r.frac_samples_lad_below:5.2f} "
              f"{r.lad_cmip6amp_med:14.2f} {r.ratio_cmip6amp:6.2f}")
    print(f"\nwrote {os.path.relpath(OUT_CSV, REPO)} and {os.path.relpath(OUT_PNG, REPO)}")
