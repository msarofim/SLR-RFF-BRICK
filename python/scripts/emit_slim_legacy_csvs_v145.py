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
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from column_helpers import KEY_COLS, detect_year_columns  # noqa: E402


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


def make_slim(in_csv: Path, out_csv: Path, *, include_w_norm: bool) -> None:
    """Read a v1.4.5 BRICK CSV; emit a slim legacy-schema copy.

    Output schema:
      - the four `KEY_COLS` (rff_idx, fair_cfg_idx, seed_idx, post_idx)
      - `w_norm` if `include_w_norm` (baseline-weighted CSVs only)
      - bare-year SLR columns "1850"..."2300" (renamed from "slr_1850" etc.)

    Component columns (te_<y>, ais_<y>, gis_<y>, gsic_<y>, lws_<y>) are
    dropped; consumers that need them read the full Wong-pipeline CSV.
    """
    df = pd.read_csv(in_csv)
    years = detect_year_columns(df, prefix="slr_")
    if not years:
        raise RuntimeError(f"{in_csv}: no `slr_<year>` columns found")
    slr_cols = [f"slr_{y}" for y in years]
    extra = ["w_norm"] if include_w_norm else []
    keep = list(KEY_COLS) + extra + slr_cols
    sub = df[keep].rename(columns={f"slr_{y}": str(y) for y in years})
    sub.to_csv(out_csv, index=False)
    print(f"  wrote {out_csv}  rows={len(sub)} cols={len(sub.columns)}")


def main() -> None:
    args = parse_args()
    brick_dir    = Path(args.brick_dir)
    weighted_dir = Path(args.weighted_dir)
    out_dir      = Path(args.out_dir); out_dir.mkdir(parents=True, exist_ok=True)

    for family in [f.strip() for f in args.families.split(",")]:
        print(f"\n=== family: {family} ===")
        # Baseline: slim file carries w_norm (the Wong importance weights).
        baseline_in = weighted_dir / f"brick_{family}_baseline_weighted.csv"
        if baseline_in.exists():
            baseline_out = out_dir / f"brick_{family}_baseline_to2300_weighted.csv"
            make_slim(baseline_in, baseline_out, include_w_norm=True)
        else:
            print(f"  no weighted baseline at {baseline_in}; skipping")

        # Pulse arms: paired with the baseline by (rff,cfg,seed,post); they
        # inherit w_norm via that join in downstream scripts, so the slim
        # pulse CSV is keys + SLR-only.
        for pulse_in in sorted(brick_dir.glob(f"brick_{family}_pulse_*.csv")):
            arm = pulse_in.stem.replace(f"brick_{family}_", "")
            pulse_out = out_dir / f"brick_{family}_{arm}_to2300.csv"
            make_slim(pulse_in, pulse_out, include_w_norm=False)


if __name__ == "__main__":
    main()
