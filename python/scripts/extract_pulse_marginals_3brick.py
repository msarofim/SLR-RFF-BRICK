"""
extract_pulse_marginals_3brick.py
==================================

Step 6 of the CO2/CH4 pulse->SLR / 3-BRICK-version study: paired per-cell
marginal SLR, weighted, per BRICK version × species × component × horizon.

For every BRICK version v in {pre93, brick2, mengel} and species in {co2, ch4}:

  1. Pair the pulse arm to the baseline arm on the 4 cell keys
     (rff_idx, fair_cfg_idx, seed_idx, post_idx) -- NOT row order (the driver
     is robust to order; we merge on keys and assert 10000 paired rows).
  2. Per component c in {total, ais, gsic, gis, te, lws} and horizon year
     y in {2100, 2150, 2300}:
        marginal_c(y) = (pulse[c_y_cm] - baseline[c_y_cm]) / SIZE
     SIZE = 0.01 GtCO2 for co2 (-> cm / GtCO2), 1.0 Tg for ch4 (-> cm / Tg).
     ('total' reads the slr_<y>_cm column.)
  3. WEIGHTED quantiles (q05/q50/q95) + weighted mean over the 10000 cells:
        - pre93, brick2 -> Wong weights from outputs/wong_weights_{v}.csv
          (per-cell w_norm), merged on the 4 keys.
        - mengel        -> UNIFORM weights (EQUAL-weighted; its posterior was
          MCMC-calibrated directly to Dangendorf, so Wong would double-count;
          locked decision 2026-06-15).
     Unweighted quantiles are ALSO emitted (q05u/q50u/q95u) for the §0 sanity
     check (for mengel weighted==unweighted by construction).

Output (one tidy long CSV):
  outputs/pulse3brick_v145/marginals_summary.csv              (all 10k draws)
  outputs/pulse3brick_v145/marginals_summary_sub2k.csv        (2k subsample, if --subset used)
  cols: version, species, unit, component, year, n, ess_fraction,
        q05, q50, q95, mean, q05u, q50u, q95u, meanu

Optional --subset: CSV with one column 'rff_idx' listing draws to include.
  Generates a _sub2k (or user-named) output for the MAGICC comparison arm.
  Subset must be a subset of the full 10k; run without flag for the full summary.

Runs on Torch (data live there); pull the small summary CSV to laptop to plot.

  python python/scripts/extract_pulse_marginals_3brick.py
  python python/scripts/extract_pulse_marginals_3brick.py --subset outputs/rff_subset_2k.csv
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

# --- named constants (labels/filenames derive from these) -------------------
_TORCH = Path("/scratch/ms17839/SLR-RFF-BRICK")
ROOT = _TORCH if _TORCH.exists() else Path(__file__).resolve().parents[2]
PULSE_DIR = ROOT / "outputs" / "pulse3brick_v145"
OUT_CSV = PULSE_DIR / "marginals_summary.csv"

VERSIONS = ["pre93", "brick2", "mengel"]
WONG_WEIGHTED = {"pre93", "brick2"}          # mengel = uniform (no Wong)

# species -> (pulse-arm file infix, pulse size, per-unit label)
SPECIES = {
    "co2": dict(arm="co2", size=0.01, unit="cm/GtCO2"),   # 0.01 GtCO2 pulse
    "ch4": dict(arm="ch4", size=1.0,  unit="cm/Tg"),      # 1.0 Tg pulse
}

# component label -> snapshot-column prefix ('total' is the summed slr_<y>_cm)
COMPONENTS = [("total", "slr"), ("ais", "ais"), ("gsic", "gsic"),
              ("gis", "gis"), ("te", "te"), ("lws", "lws")]
YEARS = [2100, 2150, 2300]
PAIR_KEYS = ["rff_idx", "fair_cfg_idx", "seed_idx", "post_idx"]

# §0 unweighted-median sanity targets (cm per unit), for the total component.
SANITY_TOTAL_Q50U = {
    ("pre93", "co2"):  {2100: 1.15e-2, 2300: 3.11e-2},
    ("brick2", "co2"): {2100: 5.07e-3, 2300: 1.00e-2},
    ("mengel", "co2"): {2100: 4.69e-3, 2300: 1.15e-2},
    ("pre93", "ch4"):  {2100: 7.27e-4, 2300: 5.94e-4},
    ("brick2", "ch4"): {2100: 3.07e-4, 2300: 1.74e-4},
    ("mengel", "ch4"): {2100: 2.80e-4, 2300: 2.12e-4},
}


def weighted_quantile(values: np.ndarray, weights: np.ndarray,
                      qs=(0.05, 0.50, 0.95)) -> np.ndarray:
    """Linear-interpolated weighted quantiles (same impl as apply_wong_weights)."""
    order = np.argsort(values)
    v = values[order]
    w = weights[order]
    cdf = np.cumsum(w) / w.sum()
    return np.interp(qs, cdf, v)


def ess_fraction(w: np.ndarray) -> float:
    s1, s2 = w.sum(), (w ** 2).sum()
    return float((s1 ** 2) / s2 / len(w)) if s2 > 0 else float("nan")


def load_weights(version: str, paired_keys: pd.DataFrame) -> np.ndarray:
    """Return per-cell weights aligned to `paired_keys` row order.
    Wong-weighted versions merge outputs/wong_weights_{v}.csv on the 4 keys;
    mengel gets uniform weights."""
    n = len(paired_keys)
    if version not in WONG_WEIGHTED:
        return np.full(n, 1.0 / n)
    wf = PULSE_DIR.parent / f"wong_weights_{version}.csv"
    w = pd.read_csv(wf, usecols=PAIR_KEYS + ["w_norm"])
    merged = paired_keys.merge(w, on=PAIR_KEYS, how="left", validate="one_to_one")
    if merged["w_norm"].isna().any():
        raise RuntimeError(f"{version}: {int(merged.w_norm.isna().sum())} cells "
                           f"have no Wong weight (key mismatch vs {wf.name}).")
    return merged["w_norm"].to_numpy()


def main() -> int:
    ap = argparse.ArgumentParser(description="Extract 3-BRICK SLR pulse marginals.")
    ap.add_argument("--subset", type=Path, default=None,
                    help="CSV with 'rff_idx' column: restrict to this draw subset. "
                         "Default: use all 10000 draws.")
    args = ap.parse_args()

    # Optional draw subsample
    if args.subset is not None:
        sub_df = pd.read_csv(args.subset, usecols=["rff_idx"])
        subset_ids = set(sub_df["rff_idx"].astype(int).tolist())
        n_expected = len(subset_ids)
        out_csv = PULSE_DIR / f"marginals_summary_{args.subset.stem}.csv"
        print(f"[subset] {args.subset.name}: {n_expected} draws -> {out_csv.name}")
    else:
        subset_ids = None
        n_expected = 10000
        out_csv = OUT_CSV

    rows = []
    print(f"[setup] pulse dir: {PULSE_DIR}")
    for version in VERSIONS:
        base = pd.read_csv(PULSE_DIR / f"{version}_baseline.csv")
        wmode = "Wong" if version in WONG_WEIGHTED else "UNIFORM"
        for sp, meta in SPECIES.items():
            size = meta["size"]
            pul = pd.read_csv(PULSE_DIR / f"{version}_{meta['arm']}.csv")
            # Pair on the 4 keys (NOT row order).
            cols_keep = PAIR_KEYS + [c for c in base.columns if c.endswith("_cm")]
            m = base[cols_keep].merge(
                pul[cols_keep], on=PAIR_KEYS, suffixes=("_b", "_p"),
                how="inner", validate="one_to_one")
            assert len(m) == 10000, f"{version}/{sp}: full-pair {len(m)} != 10000"

            # Apply optional draw subset
            if subset_ids is not None:
                m = m[m["rff_idx"].isin(subset_ids)].copy()
                assert len(m) == n_expected, (
                    f"{version}/{sp}: subset gave {len(m)}, expected {n_expected}")

            # Weights aligned to the merged row order.
            w = load_weights(version, m[PAIR_KEYS])
            w_unif = np.full(len(m), 1.0 / len(m))
            ess = ess_fraction(w)

            for comp_label, prefix in COMPONENTS:
                for y in YEARS:
                    col = f"{prefix}_{y}_cm"
                    marg = (m[f"{col}_p"].to_numpy() - m[f"{col}_b"].to_numpy()) / size
                    qw = weighted_quantile(marg, w)
                    qu = weighted_quantile(marg, w_unif)
                    rows.append(dict(
                        version=version, species=sp, unit=meta["unit"],
                        component=comp_label, year=y, n=len(m),
                        ess_fraction=round(ess, 4),
                        q05=qw[0], q50=qw[1], q95=qw[2],
                        mean=float(np.average(marg, weights=w)),
                        q05u=qu[0], q50u=qu[1], q95u=qu[2],
                        meanu=float(marg.mean()),
                    ))
            print(f"  {version:7s} {sp}: paired={len(m)}  weights={wmode}  ESS/N={ess:.3f}")

    df = pd.DataFrame(rows)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_csv, index=False)
    print(f"\n[save] {out_csv}  ({len(df)} rows)")

    # ---- §0 sanity: unweighted total q50u vs handoff targets (full 10k only) ----
    if subset_ids is None:
        print("\n=== SANITY: total-SLR unweighted median (q50u) vs handoff §0 (cm/unit) ===")
        print(f"{'version':7s} {'sp':3s} {'yr':>4s} {'q50u_computed':>15s} {'expected':>11s} {'ratio':>7s}")
        tot = df[df.component == "total"]
        for (version, sp), yexp in SANITY_TOTAL_Q50U.items():
            for y, exp in yexp.items():
                got = float(tot[(tot.version == version) & (tot.species == sp)
                                & (tot.year == y)].q50u.iloc[0])
                print(f"{version:7s} {sp:3s} {y:>4d} {got:>15.3e} {exp:>11.3e} {got/exp:>7.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
