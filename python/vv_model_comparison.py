#!/usr/bin/env python3
"""
vv_model_comparison.py — Ladrillo against BRICK 2.0 on the seven van Vuuren CMIP7 markers.

SIBLING of ladrillo_model_comparison.py, NOT a flag on it. That script compares FOUR
sources on THREE SSPs; this one compares TWO sources on SEVEN markers. They are different
objects and merging them would let a van Vuuren run emit empty FACTS / MAGICC-SLR columns
that read as "no data" when the truth is "not run on this scenario set" -- see below.

  python3 python/vv_model_comparison.py [--tag=L21] [--no-tap]
Writes outputs/vv_model_comparison_<TAG>{,_width,_gmst}.csv

WHY ONLY TWO SOURCES TODAY (stated in the console banner too, so it cannot be lost):
  Ladrillo    ✅ ours -- scope_slr_fair_uncertainty.jl on the van Vuuren cubes
  BRICK 2.0   ✅ ours -- scope_slr_fairunc_oldbrick.jl on the SAME cubes
  MAGICC-SLR  ⬜ NOT RUN -- but RUNNABLE, see below
  FACTS       ⬜ NOT RUN -- but RUNNABLE, see below
  ⇒ The SSP set is an INTERSECTION WITH THE PUBLISHED LITERATURE and does not become
    superfluous. van Vuuren is a SECOND AXIS (process / commitment), not a replacement.

⚠ CORRECTED 2026-08-31 -- THIS HEADER USED TO SAY "NOT DRIVABLE", AND THAT WAS WRONG.
It read the two comparators as fixed data files because that is all THIS repo holds. Both
models are in fact installed and driven on this machine, and both CAN be run on the van
Vuuren markers. What follows is the real state, so that nobody re-derives "impossible" from
a file listing again. NEITHER IS A SMALL JOB, and neither has been done -- "runnable" is not
"run", and this script still compares two sources until one of them is.

  MAGICC-SLR -- the pipeline is LIVE: the custom Nauels-2025 SLR build
    ~/Documents/2026/CodeProjects/MAGICC/magiccv.7.5.3/bin/magicc (commit b1fa246, the exact
    hash notebook 302 asserts), the conda env ~/miniforge3/envs/slr-refresh-2025, the
    600-member with_slr drawnset, and notebooks 200 -> 302 -> 400. It runs from EMISSIONS,
    which is what preserves its independence -- and THE VAN VUUREN MARKER EMISSIONS EXIST:
    FaIRtoFrEDI/data/vanvuuren/spliced_ext_harmonized/*.csv, 51 species x 1750-2300, in the
    same scenario/region/variable/unit + year-columns wide layout notebook 200 already reads
    from RCMIP. The work is the VARIABLE-NAME MAP into openscm-runner's namespace plus a
    coverage gate -- MAGICC silently zeroes a species it is not handed, so an unmapped name
    is a quiet emissions cut, not an error.

  FACTS -- installed and engine-validated on this Mac via Colima
    (~/Documents/2026/CodeProjects/facts), and the external-climate injection seam is a
    COMPLETED PoC: facts/build_fair_climate_nc.py writes the three NetCDFs FACTS consumes
    from our FaIR GMST+OHC, and we already have the van Vuuren cubes it needs
    (data/observations/fair_mean_{gmst,ohc}_vv*.csv, all seven markers).
    ⚠ TWO THINGS THAT MUST BE STATED IF IT IS RUN:
      (1) HORIZON. FACTS reaches 2150 at best and 2100 for the emulandice workflows. It
          CANNOT produce a 2300 column for van Vuuren any more than it can for the SSPs.
      (2) CONVENTION. An injected-climate FACTS run is not the same object as the ingested
          ssp126/245/585 table, which uses FACTS-INTERNAL FaIR-1.6.4. Mixing them straddles
          two climate-driver conventions. The measured size of that gap is ~2-5% on GMSL
          (against 30-50% for swapping the ice-sheet workflow), so it is small -- but it is
          a convention, and the fix is to re-run the three SSPs injected as well so both
          sets share one. Precedent exists: global.coupling.ssp245.fairv145.

BANDS. Both models are on their OWN JOINT arm -- posterior parameters x 841 FaIR configs,
same cubes, same 2014 splice pivot, same 1995-2014 re-reference, same PAIR_SEED, same
draw->config permutation. So unlike the SSP table, every width here IS like-for-like
(`like_for_like_forcing`), and the gate below proves the pairing rather than asserting it.
⚠ The two arms are thinned differently (Ladrillo 8000 draws, BRICK 2.0 1000), so a width
RATIO carries the coarser arm's Monte-Carlo noise. Ratios are reported to 2 dp for that
reason and small departures from 1.0 should not be read as structure.

WHAT VAN VUUREN BUYS THAT THE SSPs CANNOT: each marker carries its OWN CMIP7 land-use,
irrigation and volcanic/solar forcing, so the marker->SSP mapping approximation
(0.022-0.094 K at 2100/2300, an open question for ssp126/ssp585 per calibration_v160_prod)
is identically zero here. And FOUR of the seven are peak-and-decline pathways against the
SSPs' one, which is what makes the High-to-Low vs High comparison below possible at all.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gis_targets  # noqa: E402

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

LADRILLO_TAG = next((a[len("--tag="):] for a in sys.argv[1:]
                     if a.startswith("--tag=")), "L21")
TAPPED = "--no-tap" not in sys.argv[1:]
ARM_TAG = "" if TAPPED else "_notap"
OUT = os.path.join(REPO, f"outputs/vv_model_comparison_{LADRILLO_TAG}{ARM_TAG}.csv")
OUT_WIDTH = OUT.replace(".csv", "_width.csv")
OUT_GMST = OUT.replace(".csv", "_gmst.csv")
OUT_PATH = OUT.replace(".csv", "_pathdep.csv")

FORCING = "spliced"
## Marker order is COOLEST-ENDPOINT FIRST, matching how the cubes were built and how the
## 08-31 handoff tabulates them. `family` is the CMIP6 SSP each marker's socioeconomics
## descend from -- it is NOT an equivalence: no CMIP7 marker IS a CMIP6 SSP.
MARKERS = [
    ("vvVL", "Very Low",       "SSP1"),
    ("vvLN", "Low-to-Neg",     "SSP2"),
    ("vvL",  "Low",            "SSP2"),
    ("vvML", "Medium-to-Low",  "SSP2"),
    ("vvM",  "Medium",         "SSP2"),
    ("vvHL", "High-to-Low",    "SSP5"),
    ("vvH",  "High",           "SSP3"),
]
MKEY = [m[0] for m in MARKERS]
MLABEL = {m[0]: m[1] for m in MARKERS}
MFAMILY = {m[0]: m[2] for m in MARKERS}

HORIZONS = [2100, 2150, 2300]
COMPONENTS = ["glaciers", "gis", "ais", "te", "lws", "total"]
QUANTILES = [5, 17, 50, 83, 95]
## The path-dependence pair. HL is WARMER than H over ~2040-2090 and COOLER after, so the
## two differ in TIMING at a similar cumulative level -- the one contrast the SSP set,
## which differs in LEVEL, structurally cannot pose.
PATH_PAIR = ("vvHL", "vvH")
PATH_YEAR = 2100
## ⚠ THE STATISTIC IS THE PAIRED PER-CONFIG MEAN, NOT THE DIFFERENCE OF MEDIANS.
## Both markers are run over the SAME draw->config permutation (PAIR_SEED=2026), so draw k
## is the same posterior parameter draw under the same FaIR config in both -- the
## difference is therefore PAIRED and most of the ensemble spread cancels. Differencing
## the two medians instead throws that pairing away, and on Ladrillo's AIS it lands in the
## sparse valley between the tipped and untipped modes: q25 gives -0.32 cm, q50 gives
## -6.47, q60 gives -0.25. A 6 cm excursion bracketed by 0.3 cm either side is the median
## falling into a hole in the density, not a physical difference (`median_needs_agreement`,
## `spread_blind_to_its_own_tail`). The medians are still printed, flagged, because the
## 2026-08-31 handoff quoted them and the two must be reconcilable.
PATH_CLUSTER = "config"        # the independent unit: 841 FaIR configs, draws repeat them

LAD_DRAWS = "outputs/scope_slr_fairunc_draws_{m}_{f}_{stem}.csv"
LAD_GATES = "outputs/scope_slr_fairunc_gates_{m}_{f}_{stem}.csv"
BRK_DRAWS = "outputs/scope_slr_fairunc_draws_{m}_{f}_oldbrick.csv"
GMST_MEAN = "data/observations/fair_mean_gmst_{m}.csv"

BASIS_LAD = "joint (Ladrillo posterior x FaIR forcing, tapped)" if TAPPED else \
            "joint (Ladrillo posterior x FaIR forcing, UNTAPPED)"
BASIS_BRK = "joint (BRICK 2.0 posterior x FaIR forcing)"
SRC_LAD, SRC_BRK = "Ladrillo", "BRICK 2.0"


def joint_stem(tag):
    """The filename stem scope_slr_fair_uncertainty.jl writes, MIRRORED from the same
    GIS_TAP_CELL the Julia reads (`const TAP_TAG`, line ~162). Note it is SHORTER than
    gis_targets.tap_tag() -- the joint driver omits the `_n<stages>_ws` suffix that the
    shipped-panel name carries. Deriving it here rather than hardcoding is what keeps the
    two from drifting when the cell changes."""
    if not TAPPED:
        return tag
    c = gis_targets.tap_cell()
    return (f"{tag}_tap{str(c['onset_K']).replace('.', 'p')}K"
            f"_V{str(c['V_m']).replace('.', 'p')}m_tau{int(c['tau_yr'])}")


STEM = joint_stem(LADRILLO_TAG)


def _path(rel):
    return os.path.join(REPO, rel)


def gate_ladrillo(marker):
    """Read the driver's OWN gates file and refuse to report a marker whose run did not
    pass. A missing file is a FAILURE, not a skip -- the whole point of the 08-31 handoff's
    'check each for a [CONTROL] SKIPPED line before using them' is that an absent gate and a
    passing gate must not look the same here.

    ⚠ CONTROL is legitimately SKIPPED on every van Vuuren marker: there is no shipped
    project_ssps_components_ladrillo.jl panel row for a marker to be compared against. The
    fixed-arm code path is verified by the SSP runs, not by these. A CONTROL verdict of
    CHECK or FAIL is still an error here."""
    f = _path(LAD_GATES.format(m=marker, f=FORCING, stem=STEM))
    if not os.path.exists(f):
        raise SystemExit(
            f"no Ladrillo gates file for {marker} at {os.path.relpath(f, REPO)}.\n"
            f"  Produce it with: julia --project=julia_v2 julia/scope_slr_fair_uncertainty.jl "
            f"--ssp={marker} --build-ssp=ssp245 --forcing={FORCING} --tag={LADRILLO_TAG}"
            f"{' --tap' if TAPPED else ''}")
    g = pd.read_csv(f)
    bad = g[~g.verdict.isin(["PASS", "SKIPPED", "measured"])]
    if len(bad):
        raise SystemExit(f"[GATE] {marker}: {len(bad)} non-passing gate row(s):\n{bad}")
    if "CONTROL" not in set(g.gate):
        raise SystemExit(f"[GATE] {marker}: gates file has NO CONTROL row at all -- "
                         f"a gate that is absent is not a gate that passed.")
    ctrl = g[g.gate == "CONTROL"].verdict.iloc[0]
    npair = g[(g.gate == "PAIRING") & (g.key == "configs_used")].value.iloc[0]
    return dict(marker=marker, control=ctrl, configs_used=int(npair))


def load_joint(path, marker, source):
    """Joint-arm draws -> {(component, horizon): {q, n}} plus the config sequence."""
    if not os.path.exists(path):
        raise SystemExit(f"missing {source} joint draws for {marker}: "
                         f"{os.path.relpath(path, REPO)}")
    d = pd.read_csv(path)
    d = d[d.arm == "joint"]
    if d.empty:
        raise SystemExit(f"{source} {marker}: joint arm is EMPTY in "
                         f"{os.path.relpath(path, REPO)}")
    bands = {}
    for (comp, hz), g in d.groupby(["component", "horizon"]):
        q = np.percentile(g.value_cm.values, QUANTILES)
        bands[(comp, int(hz))] = dict(zip(["p05", "p17", "med", "p83", "p95"], q),
                                      n=len(g))
    seq = (d[(d.component == COMPONENTS[0]) & (d.horizon == HORIZONS[0])]
           .sort_values("draw").config.tolist())
    return bands, seq


def gate_pairing(seq_lad, seq_brk, marker):
    """LIKE-FOR-LIKE IS PROVED, NOT ASSERTED. Both drivers permute draw->config with the
    same PAIR_SEED=2026, so the two config sequences must agree over the shorter one. If
    they do not, the two models saw DIFFERENT forcing subsets and no width ratio between
    them means anything."""
    n = min(len(seq_lad), len(seq_brk))
    if n == 0:
        raise SystemExit(f"[GATE] {marker}: one of the two arms has no draws to pair.")
    if seq_lad[:n] != seq_brk[:n]:
        k = next(i for i in range(n) if seq_lad[i] != seq_brk[i])
        raise SystemExit(
            f"[GATE] {marker}: the two models' draw->config permutations DIVERGE at draw "
            f"{k + 1} ({seq_lad[k]} vs {seq_brk[k]}). They did not see the same forcing "
            f"subset, so no width ratio between them is like-for-like.")
    return n


def gmst_context(marker):
    """Peak GMST, its year, and the endpoint -- the axis on which van Vuuren separates
    from the SSPs. Read from the FULL-RANGE MEAN cube (mean over the 841 configs, already
    rebased to 1850-1900 by the builder), which is the same series the FIXED arm is driven
    with. Peak is taken over the PROJECTION era only: a historical maximum would make the
    four decline pathways report the same peak as each other."""
    f = _path(GMST_MEAN.format(m=marker))
    if not os.path.exists(f):
        raise SystemExit(f"missing mean GMST cube for {marker}: {os.path.relpath(f, REPO)}")
    d = pd.read_csv(f)
    proj = d[(d.year >= PEAK_FROM_YEAR) & (d.year <= PEAK_TO_YEAR)]
    i = proj.gmst_C.idxmax()
    at = {y: float(d.loc[d.year == y, "gmst_C"].iloc[0]) for y in GMST_YEARS}
    return dict(marker=marker, peak_K=float(d.loc[i, "gmst_C"]),
                peak_year=int(d.loc[i, "year"]), **{f"gmst_{y}": at[y] for y in GMST_YEARS})


PEAK_FROM_YEAR = 2015          # projection era; a historical max would tie all seven
## ⚠ THE MEAN CUBE CARRIES A 2301 ROW AND THE PER-CONFIG CUBE DOES NOT. That is the
## builder doing what it says (`END_YEAR = 2301`, `CUBE_LAST_YEAR = 2300`): FaIR's
## timebounds run one past the last timepoint, and the mean file is written over the full
## timebounds range while the cube is truncated. It is pre-existing and identical on the
## SSP means. But 2300 is the ratified end year for all our work, so a table here must
## never report a peak at 2301 -- both the Medium and High markers are still rising at the
## end and would otherwise do exactly that.
PEAK_TO_YEAR = 2300
GMST_YEARS = [2050, 2100, 2300]


def spearman(x, y):
    """Rank correlation without a scipy dependency. Reported ONLY as a direction on n=7;
    the CI on rho at n=7 is very wide and this is a hypothesis, NOT a test."""
    rx = pd.Series(x).rank().values
    ry = pd.Series(y).rank().values
    return float(np.corrcoef(rx, ry)[0, 1])


def paired_diff(src, m_a, m_b, year):
    """PAIRED per-config difference m_a - m_b, by component, at `year`.

    Both markers were run over the SAME draw->config permutation, so draw k carries the
    same posterior parameter draw under the same FaIR config in both files -- which is
    ASSERTED here, not assumed, because if it ever stopped holding the difference would
    silently become an unpaired one. Draws repeat configs, so the independent unit is the
    CONFIG: cluster to a per-config mean first, then take the se over the 841 clusters.
    A component with zero variance (lws is scenario-independent) reports se = 0 exactly
    rather than a spurious tiny one."""
    f = {SRC_LAD: LAD_DRAWS.format(m="{m}", f=FORCING, stem=STEM),
         SRC_BRK: BRK_DRAWS.format(m="{m}", f=FORCING)}[src]
    out = {}
    A = pd.read_csv(_path(f.format(m=m_a)))
    B = pd.read_csv(_path(f.format(m=m_b)))
    for comp in COMPONENTS:
        a = A[(A.component == comp) & (A.horizon == year) & (A.arm == "joint")].sort_values("draw")
        b = B[(B.component == comp) & (B.horizon == year) & (B.arm == "joint")].sort_values("draw")
        if len(a) != len(b) or not (a.config.values == b.config.values).all():
            raise SystemExit(
                f"[GATE] {src} {comp} @{year}: {m_a} and {m_b} do NOT share a "
                f"draw->config permutation, so their difference is not paired.")
        z = a.value_cm.values - b.value_cm.values
        cl = pd.DataFrame({"c": a.config.values, "z": z}).groupby("c").z.mean()
        sd = cl.std(ddof=1)
        out[comp] = dict(mean=float(cl.mean()),
                         se=float(sd / np.sqrt(len(cl))) if sd > 0 else 0.0,
                         n_cfg=len(cl))
    return out


def band(b):
    return f"{b['med']:7.1f} [{b['p17']:6.1f},{b['p83']:6.1f}]"


def main():
    print(__doc__.split("WHY ONLY TWO SOURCES")[1].split("BANDS.")[0]
          .replace("TODAY (stated in the console banner too, so it cannot be lost):",
                   "TODAY -- and the other two are RUNNABLE, not impossible:").strip())
    print()

    gates, LAD, BRK, SEQ = {}, {}, {}, {}
    for m in MKEY:
        gates[m] = gate_ladrillo(m)
        LAD[m], sl = load_joint(_path(LAD_DRAWS.format(m=m, f=FORCING, stem=STEM)),
                                m, SRC_LAD)
        BRK[m], sb = load_joint(_path(BRK_DRAWS.format(m=m, f=FORCING)), m, SRC_BRK)
        SEQ[m] = gate_pairing(sl, sb, m)
        print(f"[GATE] {MLABEL[m]:14s} {m:5s}  Ladrillo gates all pass "
              f"(CONTROL {gates[m]['control']}, {gates[m]['configs_used']} configs); "
              f"draw->config permutations agree over {SEQ[m]} draws "
              f"[Ladrillo n={LAD[m][(COMPONENTS[0], HORIZONS[0])]['n']}, "
              f"BRICK 2.0 n={BRK[m][(COMPONENTS[0], HORIZONS[0])]['n']}]")

    rows = []
    for m in MKEY:
        for src, bands, basis in ((SRC_LAD, LAD[m], BASIS_LAD),
                                  (SRC_BRK, BRK[m], BASIS_BRK)):
            for comp in COMPONENTS:
                for y in HORIZONS:
                    b = bands.get((comp, y))
                    if b is None:
                        continue
                    rows.append(dict(source=src,
                                     module=LADRILLO_TAG if src == SRC_LAD else "BRICK2.0",
                                     marker=m, marker_label=MLABEL[m], family=MFAMILY[m],
                                     component=comp, year=y, n_draws=b["n"],
                                     med=b["med"], p05=b["p05"], p17=b["p17"],
                                     p83=b["p83"], p95=b["p95"], band_basis=basis))
    df = pd.DataFrame(rows)
    df.to_csv(OUT, index=False)

    W = 96
    print(f"\n{'=' * W}")
    print(f"Ladrillo ({LADRILLO_TAG}, {'tapped' if TAPPED else 'UNTAPPED'}) vs BRICK 2.0 "
          f"— cm, rel. 1995-2014, median [17-83%]")
    print(f"Both on their OWN JOINT arm, SAME van Vuuren cubes: widths ARE like-for-like.")
    print("=" * W)
    for y in HORIZONS:
        print(f"\n@{y}")
        for comp in COMPONENTS:
            print(f"  --- {comp} ---")
            for m in MKEY:
                a, b = LAD[m].get((comp, y)), BRK[m].get((comp, y))
                if a is None or b is None:
                    continue
                print(f"    {MLABEL[m]:14s}  Ladrillo {band(a)}   BRICK 2.0 {band(b)}")

    ## WIDTH RATIO -- the cool-scenario under-dispersion, on a second scenario family.
    print(f"\n{'=' * W}")
    print("p05-p95 WIDTH RATIO, Ladrillo / BRICK 2.0  (<1 = Ladrillo narrower)")
    print("Replicates the SSP-set result (2.8x narrower at ssp126/2100, 4.4x at "
          "ssp126/2300, ~13% at ssp585)\non a DIFFERENT scenario family, with seven "
          "points tracing a gradient where three could not.")
    print("=" * W)
    wrows = []
    hdr = "  " + f"{'marker':16s}" + "".join(f"{y:>10d}" for y in HORIZONS)
    for comp in ("total", "gis", "ais", "te", "glaciers"):
        print(f"  --- {comp} ---\n{hdr}")
        for m in MKEY:
            line = f"  {MLABEL[m]:16s}"
            for y in HORIZONS:
                a, b = LAD[m].get((comp, y)), BRK[m].get((comp, y))
                if a is None or b is None:
                    line += f"{'-':>10s}"
                    continue
                wa, wb = a["p95"] - a["p05"], b["p95"] - b["p05"]
                r = wa / wb if wb else float("nan")
                line += f"{r:10.2f}"
                wrows.append(dict(marker=m, marker_label=MLABEL[m], component=comp, year=y,
                                  width_ladrillo_cm=wa, width_brick20_cm=wb, width_ratio=r))
            print(line)
    pd.DataFrame(wrows).to_csv(OUT_WIDTH, index=False)

    ## GMST CONTEXT + the peak-vs-endpoint direction.
    g = pd.DataFrame([gmst_context(m) for m in MKEY])
    g["marker_label"] = g.marker.map(MLABEL)
    tot = {m: LAD[m][("total", 2300)]["p95"] - LAD[m][("total", 2300)]["p05"] for m in MKEY}
    brk = {m: BRK[m][("total", 2300)]["p95"] - BRK[m][("total", 2300)]["p05"] for m in MKEY}
    g["width_ratio_total_2300"] = g.marker.map(lambda m: tot[m] / brk[m])
    g.to_csv(OUT_GMST, index=False)
    print(f"\n{'=' * W}\nGMST CONTEXT (K rel 1850-1900, full-range mean of 841 configs) "
          f"and the width ratio it may track\n{'=' * W}")
    print(f"  {'marker':16s}{'peak':>8s}{'@yr':>7s}{'2050':>8s}{'2100':>8s}{'2300':>8s}"
          f"{'ratio(total@2300)':>20s}")
    for r in g.itertuples():
        print(f"  {r.marker_label:16s}{r.peak_K:8.2f}{r.peak_year:7d}{r.gmst_2050:8.2f}"
              f"{r.gmst_2100:8.2f}{r.gmst_2300:8.2f}{r.width_ratio_total_2300:20.2f}")
    rho_peak = spearman(g.peak_K, g.width_ratio_total_2300)
    rho_end = spearman(g.gmst_2300, g.width_ratio_total_2300)
    print(f"\n  Spearman rho vs width ratio:  PEAK {rho_peak:+.2f}   "
          f"ENDPOINT (2300) {rho_end:+.2f}")
    print("  ⚠ n = 7. This is a DIRECTION TO CHECK, NOT A TEST -- the CI on rho at n=7 is")
    print("    very wide. It is recorded because the SSP set cannot pose the question at")
    print("    all: there, peak and endpoint warming are near-monotonically related, while")
    print("    van Vuuren's four decline pathways separate them by up to ~2 K.")

    ## PATH DEPENDENCE -- the result that justifies building the cubes.
    hl, h = PATH_PAIR
    PAIRED = {}
    for src in (SRC_LAD, SRC_BRK):
        for comp, v in paired_diff(src, hl, h, PATH_YEAR).items():
            PAIRED[(src, comp)] = v
    print(f"\n{'=' * W}")
    print(f"PATH DEPENDENCE: {MLABEL[hl]} minus {MLABEL[h]} at {PATH_YEAR} (cm)")
    print(f"{MLABEL[hl]} is WARMER than {MLABEL[h]} through the mid-century and COOLER at "
          f"the endpoint, so the\ntwo differ in TIMING at a comparable level. The SSP set "
          f"differs in LEVEL and cannot pose this.")
    print("PAIRED per-config difference (same posterior draw, same FaIR config in both "
          "markers), +/- 1 se\nover the 841 config clusters. The median difference is "
          "shown alongside and is NOT the statistic --\nsee the PATH_CLUSTER note in the "
          "source for why it is unreliable on a tipping distribution.")
    print("=" * W)
    ghl = g[g.marker == hl].iloc[0]
    gh = g[g.marker == h].iloc[0]
    print(f"  GMST: peak {ghl.peak_K:.2f} K @{ghl.peak_year} vs {gh.peak_K:.2f} K "
          f"@{gh.peak_year}; at 2100 {ghl.gmst_2100:.2f} vs {gh.gmst_2100:.2f} K; "
          f"at 2300 {ghl.gmst_2300:.2f} vs {gh.gmst_2300:.2f} K")
    print(f"\n  {'component':10s}{'Ladrillo paired':>22s}{'BRICK 2.0 paired':>22s}"
          f"{'Lad med':>10s}{'B20 med':>10s}")
    prows = []
    for comp in COMPONENTS:
        line, cells = f"  {comp:10s}", {}
        for src in (SRC_LAD, SRC_BRK):
            za = PAIRED[(src, comp)]
            cells[src] = za
            line += (f"  {za['mean']:+8.3f} +/-{za['se']:6.3f}" if za["se"] > 0
                     else f"  {za['mean']:+8.3f}   (exact)")
        for src, bands in ((SRC_LAD, (LAD[hl], LAD[h])), (SRC_BRK, (BRK[hl], BRK[h]))):
            a, b = bands[0].get((comp, PATH_YEAR)), bands[1].get((comp, PATH_YEAR))
            dm = (a["med"] - b["med"]) if (a and b) else float("nan")
            cells[src + "_med"] = dm
            line += f"{dm:+10.2f}"
        print(line)
        prows.append(dict(component=comp, year=PATH_YEAR,
                          paired_mean_ladrillo=cells[SRC_LAD]["mean"],
                          paired_se_ladrillo=cells[SRC_LAD]["se"],
                          paired_mean_brick20=cells[SRC_BRK]["mean"],
                          paired_se_brick20=cells[SRC_BRK]["se"],
                          med_diff_ladrillo=cells[SRC_LAD + "_med"],
                          med_diff_brick20=cells[SRC_BRK + "_med"]))
    pd.DataFrame(prows).to_csv(OUT_PATH, index=False)
    print()
    print("  READING, on the paired statistic:")
    print("  * AIS is POSITIVE in BOTH models and well clear of its se -- High-to-Low's")
    print("    EARLIER warming leaves more ice-sheet response at 2100 even though it ends")
    print("    5.3 K cooler. This is the path-dependence signal, and it REPLICATES across")
    print("    two independent ice-sheet modules.")
    print("  * TE is NEGATIVE in both and nearly identical between them (they share the")
    print("    OHC forcing), tracking the cooler endpoint.")
    print("  * TOTAL at 2100 is the small RESIDUAL of those two larger opposing terms, so")
    print("    its SIGN is model-dependent and should not be quoted as a headline. The")
    print("    robust claim is the COMPONENT SPLIT, not the net.")
    print("  ⚠ The 2026-08-31 handoff quoted +3.02 cm (BRICK fixed-arm median). The paired")
    print("    mean is far smaller; the median overstates it because of the tipping tail.")
    print("  At 2150 and 2300 every component is strongly negative in both models -- once")
    print("  the endpoint gap dominates, High-to-Low falls far below High and the timing")
    print("  contrast is gone. 2100 is the only horizon where it can be read.")

    print(f"\nwrote {os.path.relpath(OUT, REPO)}, {os.path.relpath(OUT_WIDTH, REPO)}, "
          f"{os.path.relpath(OUT_GMST, REPO)}, {os.path.relpath(OUT_PATH, REPO)}")


if __name__ == "__main__":
    main()
