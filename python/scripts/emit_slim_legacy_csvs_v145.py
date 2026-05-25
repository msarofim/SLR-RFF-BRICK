"""
emit_slim_legacy_csvs_v145.py
=============================

Take the v1.4.5 Wong-pipeline outputs (baseline_weighted + per-arm pulse
CSVs) and emit *slim, legacy-schema* CSVs for downstream plotting:

  * keys: rff_idx, fair_cfg_idx, seed_idx, post_idx
  * w_norm (only on baseline-weighted CSVs; pulse arms inherit via merge)
  * bare-year total SLR columns: "1850", "1851", ..., "2300"
    (renamed from "slr_1850" etc — matches the existing apply_wong_weights
    convention so gaussian_vs_empirical_slr.py, run_pulse_4way_slr_decomp.py,
    run_4way_slr_decomp.py, and slr_band.py work unchanged once their
    BASELINE_CSV / PULSE_CSV constants are pointed at these files.)

This drops the ~451 × 5-component trajectory columns from the on-disk file
(~25× smaller). The full component-rich CSVs stay on /scratch for any
diagnostic-style consumers (e.g. component_overlay_obsdriven.py).

Outputs (all under --out-dir):
  brick_lhs10k_baseline_to2300_weighted.csv       (slim, with w_norm)
  brick_lhs10k_pulse_<arm>_to2300.csv             (slim, no w_norm — pulse arms
                                                   inherit from baseline)
  brick_anova18k_baseline_to2300_weighted.csv
  brick_anova18k_pulse_<arm>_to2300.csv

Usage:
  python python/scripts/emit_slim_legacy_csvs_v145.py \
      --brick-dir outputs/brick_v145 \
      --weighted-dir outputs/brick_v145_summaries \
      --out-dir outputs/brick_v145_slim
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


KEY_COLS = ["rff_idx", "fair_cfg_idx", "seed_idx", "post_idx"]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--brick-dir",    required=True,
                   help="dir with brick_<arm>.csv (raw flat-cube driver outputs)")
    p.add_argument("--weighted-dir", required=True,
                   help="dir with brick_<family>_baseline_weighted.csv (Wong pipeline outputs)")
    p.add_argument("--out-dir",      required=True, help="output dir for slim CSVs")
    p.add_argument("--families", default="lhs10k,anova18k",
                   help="comma-separated families to process")
    return p.parse_args()


def make_slim_baseline(weighted_csv: Path, out_csv: Path) -> None:
    """Read full baseline_weighted CSV; emit slim (keys + w_norm + bare-year SLR)."""
    df = pd.read_csv(weighted_csv)
    slr_cols = sorted([c for c in df.columns if c.startswith("slr_")
                        and c[len("slr_"):].isdigit()],
                       key=lambda c: int(c[len("slr_"):]))
    keep = KEY_COLS + ["w_norm"] + slr_cols
    sub = df[keep].copy()
    sub = sub.rename(columns={c: c[len("slr_"):] for c in slr_cols})
    sub.to_csv(out_csv, index=False)
    print(f"  wrote {out_csv}  rows={len(sub)} cols={len(sub.columns)}")


def make_slim_pulse(brick_csv: Path, out_csv: Path) -> None:
    """Read raw pulse CSV; emit slim (keys + bare-year SLR; no w_norm)."""
    df = pd.read_csv(brick_csv)
    slr_cols = sorted([c for c in df.columns if c.startswith("slr_")
                        and c[len("slr_"):].isdigit()],
                       key=lambda c: int(c[len("slr_"):]))
    keep = KEY_COLS + slr_cols
    sub = df[keep].copy()
    sub = sub.rename(columns={c: c[len("slr_"):] for c in slr_cols})
    sub.to_csv(out_csv, index=False)
    print(f"  wrote {out_csv}  rows={len(sub)} cols={len(sub.columns)}")


def main() -> None:
    args = parse_args()
    brick_dir    = Path(args.brick_dir)
    weighted_dir = Path(args.weighted_dir)
    out_dir      = Path(args.out_dir); out_dir.mkdir(parents=True, exist_ok=True)

    for family in [f.strip() for f in args.families.split(",")]:
        print(f"\n=== family: {family} ===")
        # Baseline (slim, with w_norm) — from the weighted CSV
        w_csv = weighted_dir / f"brick_{family}_baseline_weighted.csv"
        if w_csv.exists():
            make_slim_baseline(w_csv, out_dir / f"brick_{family}_baseline_to2300_weighted.csv")
        else:
            print(f"  no weighted baseline at {w_csv}; skipping")

        # Pulse arms (slim, no w_norm) — from the raw brick CSVs
        for p_csv in sorted(brick_dir.glob(f"brick_{family}_pulse_*.csv")):
            arm = p_csv.stem.replace(f"brick_{family}_", "")
            make_slim_pulse(p_csv, out_dir / f"brick_{family}_{arm}_to2300.csv")


if __name__ == "__main__":
    main()
