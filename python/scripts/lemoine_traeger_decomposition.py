"""
lemoine_traeger_decomposition.py
================================

DIAGNOSTIC UTILITY (2026-05-26): The project standardized on empirical
importance-weighted p5/p50/p95 quantiles for all pulse-marginal SLR
figures, because that approach is both threshold-invariant and
pulse-size-invariant. The L-T decomposition implemented here is retained
as a methodological reference and for anyone auditing or revisiting the
decomposition framework — but NO ACTIVE FIGURE in the substack/poster
pipeline calls these functions. The previous active consumer
(`gaussian_vs_empirical_slr.py`) was retired to
`outputs/quarantine/20260526_lt_to_empirical/`.

Reference implementation of the Lemoine-Traeger probabilistic tipping-point
decomposition applied to a paired BRICK SLR ensemble (or any analogous paired
marginal-SLR analysis).

The decomposition splits the expected marginal SLR response to a forcing pulse
into:

  1. A LINEAR (no-tipping) baseline:

        E[ΔSLR | no tipping]

     = the mean marginal response in a "quiescent" subset of the ensemble
       where each draw's baseline state is *not* pre-positioned near an AIS
       (Antarctic Ice Sheet) tipping threshold. By construction this subset
       responds linearly in the small-pulse limit.

  2. A TIPPING INSURANCE PREMIUM:

        P(tipping) × ( E[ΔSLR | tipping] − E[ΔSLR | no tipping] )

     = the additional expected response from the probability that the pulse
       pushes a near-threshold draw over the AIS tipping point. This is the
       "extra" expected damage attributable to the nonlinear tipping
       mechanism, in the framing of Lemoine & Traeger 2014.

By construction these are additive:

        E[ΔSLR | full ensemble] = (linear baseline) + (tipping insurance premium)

i.e. linear_plus_premium ≡ E_marginal_total to within floating-point noise.


CONCEPTUAL REFERENCE
--------------------
Lemoine, D. and Traeger, C.P. 2014. "Watch Your Step: Optimal Policy in a
Tipping Climate." American Economic Journal: Economic Policy 6(1):137-166.
doi:10.1257/pol.6.1.137

The Lemoine-Traeger framework was developed for economic damage modeling of
climate tipping points; the same probabilistic decomposition transfers
cleanly to physical-quantity tipping (here: AIS instability driving SLR).


PROJECT-SPECIFIC CLASSIFIER
---------------------------
In the SLR-RFF-BRICK project (Sarofim et al., msarofim/SLR-RFF-BRICK on
GitHub), we operationalize "near tipping" as:

        baseline ais_2100_cm > 20

i.e. a draw whose BRICK baseline run has Antarctic ice-sheet contribution to
year-2100 SLR exceeding 20 cm. This was calibrated empirically against the
LHS-10k ensemble:

  - Higher thresholds (~25+ cm) miss the small population of draws that tip
    only at the upper end of the pulse, including a single CH4-pulse-induced
    tipping event we observed at baseline ais_2100 = 29.6 cm.
  - Lower thresholds (~15 cm) over-classify and dilute the "linear" subset.

The 20 cm threshold captures ~5% of draws in our LHS-10k weighted ensemble,
matching the prior expectation that AIS tipping is a low-probability,
high-magnitude tail event.

The classifier is fully configurable in this script (see
`classifier_threshold_cm` and `classifier_column` arguments). For non-SLR
applications, replace `ais_2100_cm` with any per-draw baseline-state
variable that distinguishes near-tipping from quiescent regimes.


USAGE
-----

    import pandas as pd
    from lemoine_traeger_decomposition import lemoine_decompose

    baseline = pd.read_csv("brick_lhs10k_baseline_to2300_weighted.csv")
    pulse    = pd.read_csv("brick_lhs10k_pulse_to2300_weighted.csv")

    result = lemoine_decompose(
        baseline_df=baseline,
        pulse_df=pulse,
        year=2100,
        classifier_threshold_cm=20.0,
        weight_col="w_norm",       # or None for unweighted
        pulse_size_gtc=1.0,        # pulse magnitude, for per-unit reporting
    )
    print(result)

For convenience, `lemoine_decompose_by_year` runs the decomposition over a
list of years and returns a tidy DataFrame.

The CSVs above are publicly archived at
https://doi.org/10.5281/zenodo.20312325 (SLR-RFF-FaIR-BRICK intermediate
data v1.0; license CC-BY-4.0). For non-Zenodo ensembles, the function
accepts any paired (baseline_df, pulse_df) with matching row keys plus a
classifier column.


DEPENDENCIES
------------
pandas, numpy. No project-specific dependencies.


LICENSE
-------
MIT (matches the parent SLR-RFF-BRICK repo).


CITATION
--------
If you adapt this in published work, please cite both:

  - Sarofim et al. SLR-RFF-BRICK code repository.
    https://github.com/msarofim/SLR-RFF-BRICK

  - Lemoine, D. and Traeger, C.P. 2014. Am Econ J Econ Pol 6(1):137-166.
    doi:10.1257/pol.6.1.137
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Iterable, Optional

import numpy as np
import pandas as pd


@dataclass
class LemoineDecomposition:
    """One year's worth of Lemoine-Traeger decomposition output."""
    year: int
    E_marginal_total: float          # full-ensemble weighted mean marginal
    E_marginal_no_tipping: float     # linear baseline (quiescent subset mean)
    E_marginal_tipping: float        # tipping-subset mean
    P_tipping: float                 # weighted probability of tipping
    tipping_insurance_premium: float # P_tipping * (E_tipping - E_no_tipping)
    linear_plus_premium: float       # should equal E_marginal_total
    n_tipping: int                   # unweighted count of tipping draws
    n_no_tipping: int                # unweighted count of quiescent draws

    def as_dict(self):
        return asdict(self)


def lemoine_decompose(
    baseline_df: pd.DataFrame,
    pulse_df: pd.DataFrame,
    year: int,
    classifier_threshold_cm: float = 20.0,
    classifier_column: str = "ais_2100_cm",
    weight_col: Optional[str] = "w_norm",
    pulse_size_gtc: float = 1.0,
    key_columns: Iterable[str] = ("rff_idx", "fair_cfg_idx", "seed_idx", "post_idx"),
) -> LemoineDecomposition:
    """Apply the Lemoine-Traeger tipping decomposition to a paired ensemble.

    Parameters
    ----------
    baseline_df : pandas.DataFrame
        Per-draw baseline BRICK output. Must contain:
          - one or more pairing-key columns (default: rff_idx, fair_cfg_idx,
            seed_idx, post_idx). Used to align baseline and pulse rows.
          - a string-named year column (e.g., '2100') with the SLR value at
            that year. cm rel year 2000 is the SLR-RFF-BRICK convention.
          - `classifier_column` with the per-draw baseline classifier value.
          - `weight_col` if weighted (default 'w_norm'; pass None to disable).

    pulse_df : pandas.DataFrame
        Per-draw pulse BRICK output. Same schema as baseline_df. Paired by
        the key_columns. Rows are aligned by sorting on the key columns,
        then verified to match before subtraction.

    year : int
        Year at which to evaluate the marginal (e.g., 2100). Must exist as
        a string-named column in both DataFrames.

    classifier_threshold_cm : float, default 20.0
        Threshold on `classifier_column` above which a draw is classified
        as "tipping-prone". 20.0 cm is the SLR-RFF-BRICK project default.

    classifier_column : str, default 'ais_2100_cm'
        Column in baseline_df used for tipping classification. Can be
        replaced with any per-draw baseline-state variable for non-SLR
        applications.

    weight_col : str or None, default 'w_norm'
        Per-draw weight column. Pass None for equal weights.

    pulse_size_gtc : float, default 1.0
        Pulse magnitude in the units of the run, used to normalize the
        marginal to a per-unit (per-GtC) basis. Set to the actual pulse
        size (e.g., 0.01 for a small-pulse small-magnitude run, or 3.667
        if you ran a 1 GtCO2 pulse and want per-GtC marginals).

    key_columns : iterable of str
        Pairing keys to align baseline_df and pulse_df rows. Only those
        columns that exist in BOTH DataFrames are used (so you can pass
        a superset; missing ones are silently dropped).

    Returns
    -------
    LemoineDecomposition (dataclass) with the per-year decomposition.
    Use `.as_dict()` to convert to a plain dict for JSON / DataFrame use.

    Raises
    ------
    ValueError if pairing keys cannot be aligned, year column is missing,
    or DataFrames are inconsistent.

    Notes
    -----
    Weighted means use np.average with the weight column. Subset means
    discard rows with zero (or NaN) weight automatically. The
    `linear_plus_premium` field is an algebraic identity (always equal to
    E_marginal_total within floating-point noise); it's included as a
    sanity-check column.
    """
    # ---- 1. align baseline and pulse on shared keys ---------------------
    keys = [c for c in key_columns
            if c in baseline_df.columns and c in pulse_df.columns]
    if not keys:
        raise ValueError(
            f"None of {list(key_columns)} found in both DataFrames. "
            f"Provide at least one pairing key column."
        )
    b = baseline_df.sort_values(keys).reset_index(drop=True)
    p = pulse_df.sort_values(keys).reset_index(drop=True)
    if len(b) != len(p):
        raise ValueError(
            f"Length mismatch after sort: baseline={len(b)}, pulse={len(p)}"
        )
    if not (b[keys].values == p[keys].values).all():
        raise ValueError(
            f"Pairing key columns {keys} do not match between baseline and "
            f"pulse after sort. Are the two DataFrames from the same ensemble?"
        )

    # ---- 2. extract marginal at the requested year ----------------------
    year_col = str(year)
    if year_col not in b.columns or year_col not in p.columns:
        raise ValueError(f"Year column '{year_col}' not in one or both DataFrames.")
    slr_b = b[year_col].to_numpy(dtype=float)
    slr_p = p[year_col].to_numpy(dtype=float)
    marginal = (slr_p - slr_b) / pulse_size_gtc

    # ---- 3. classify by baseline AIS state ------------------------------
    if classifier_column not in b.columns:
        raise ValueError(
            f"Classifier column '{classifier_column}' not in baseline_df. "
            f"Available columns: {list(b.columns)[:15]}..."
        )
    classifier_vals = b[classifier_column].to_numpy(dtype=float)
    is_tipping = classifier_vals > classifier_threshold_cm

    # ---- 4. weights -----------------------------------------------------
    if weight_col is None or weight_col not in b.columns:
        w = np.ones(len(b), dtype=float)
    else:
        w = b[weight_col].to_numpy(dtype=float)
    w_total = float(w.sum())
    if w_total <= 0:
        raise ValueError("Weights sum to zero; cannot compute weighted moments.")

    # ---- 5. compute weighted means + premium ----------------------------
    def _wmean(arr: np.ndarray, mask: np.ndarray) -> float:
        sub_w = w[mask]
        sub_w_sum = sub_w.sum()
        if sub_w_sum <= 0:
            return float("nan")
        return float(np.average(arr[mask], weights=sub_w))

    E_total       = float(np.average(marginal, weights=w))
    E_no_tipping  = _wmean(marginal, ~is_tipping)
    E_tipping     = _wmean(marginal,  is_tipping)
    P_tipping     = float(w[is_tipping].sum() / w_total)
    premium       = P_tipping * (E_tipping - E_no_tipping)

    return LemoineDecomposition(
        year=int(year),
        E_marginal_total=E_total,
        E_marginal_no_tipping=E_no_tipping,
        E_marginal_tipping=E_tipping,
        P_tipping=P_tipping,
        tipping_insurance_premium=premium,
        linear_plus_premium=E_no_tipping + premium,
        n_tipping=int(is_tipping.sum()),
        n_no_tipping=int((~is_tipping).sum()),
    )


def lemoine_decompose_by_year(
    baseline_df: pd.DataFrame,
    pulse_df: pd.DataFrame,
    years: Iterable[int],
    classifier_threshold_cm: float = 20.0,
    classifier_column: str = "ais_2100_cm",
    weight_col: Optional[str] = "w_norm",
    pulse_size_gtc: float = 1.0,
    key_columns: Iterable[str] = ("rff_idx", "fair_cfg_idx", "seed_idx", "post_idx"),
) -> pd.DataFrame:
    """Run `lemoine_decompose` over a list of years and return one DataFrame
    with one row per year. Useful for the typical 'decomposition over a
    horizon' plot."""
    rows = []
    for y in years:
        result = lemoine_decompose(
            baseline_df=baseline_df,
            pulse_df=pulse_df,
            year=y,
            classifier_threshold_cm=classifier_threshold_cm,
            classifier_column=classifier_column,
            weight_col=weight_col,
            pulse_size_gtc=pulse_size_gtc,
            key_columns=key_columns,
        )
        rows.append(result.as_dict())
    return pd.DataFrame(rows)


# ============================================================================
# DEMO / self-test
# ============================================================================
if __name__ == "__main__":
    """Demo: run the decomposition on the v1.4.5 LHS-10k CO2 +0.01-GtCO₂
    small-pulse ensemble.

    The `pulse_size_gtc` keyword name on `lemoine_decompose_by_year` is a
    legacy holdover from the v1.4.1 era when CO2 pulses were sized in GtC;
    the underlying function is unit-agnostic — it just divides the per-draw
    SLR marginal by whatever scalar you pass. For v1.4.5 we pass the
    actual GtCO₂ pulse magnitude (0.01) and report cm per GtCO₂.

    Expects the v1.4.5 FULL per-component CSVs (with `ais_2100_cm` for
    the tipping-state classifier) at:
      outputs/brick_v145/brick_lhs10k_baseline.csv
      outputs/brick_v145/brick_lhs10k_pulse_co2_pos_001gt.csv

    These are NOT in the slim CSVs at outputs/brick_v145_slim/ — those
    drop per-component columns to save disk. If absent locally, pull the
    full CSVs from Torch:
      rsync torch:/scratch/ms17839/SLR-RFF-BRICK/outputs/brick_v145/brick_lhs10k_*.csv outputs/brick_v145/
    """
    from pathlib import Path

    ROOT = Path(__file__).resolve().parents[2]
    BASELINE = ROOT / "outputs/brick_v145/brick_lhs10k_baseline.csv"
    PULSE    = ROOT / "outputs/brick_v145/brick_lhs10k_pulse_co2_pos_001gt.csv"
    if not BASELINE.exists() or not PULSE.exists():
        raise SystemExit(
            "Missing full per-component CSVs at outputs/brick_v145/. "
            "The slim CSVs at outputs/brick_v145_slim/ do NOT carry "
            "`ais_2100_cm` (the AIS-tipping-state classifier this "
            "decomposition needs). See module docstring for the rsync "
            "command to pull from Torch."
        )

    print(f"Loading paired v1.4.5 ensemble from {BASELINE.parent}/")
    baseline_df = pd.read_csv(BASELINE)
    pulse_df    = pd.read_csv(PULSE)
    # Full per-component CSVs name year columns `slr_<y>` (e.g. `slr_2030`);
    # lemoine_decompose expects bare-year names (the slim-CSV convention).
    # Rename in place to bridge the two schemas.
    def _bare_year_rename(df):
        return df.rename(columns={c: c[4:] for c in df.columns
                                   if c.startswith("slr_") and c[4:].isdigit()})
    baseline_df = _bare_year_rename(baseline_df)
    pulse_df    = _bare_year_rename(pulse_df)
    print(f"  baseline: {len(baseline_df)} draws")
    print(f"  pulse:    {len(pulse_df)} draws (0.01 GtCO₂ small-pulse arm)")
    print()

    # Per-year decomposition, +0.01 GtCO₂ CO2 pulse at 2030. Divisor 0.01
    # yields per-GtCO₂ marginal directly (FaIR v1.4.5 CO2 FFI input unit is
    # GtCO₂; see ~/.claude/skills/climate-modeling "Unit checks: GtC vs
    # GtCO₂" + memory `project_fair_v145_co2ffi_is_gtco2.md`).
    df = lemoine_decompose_by_year(
        baseline_df=baseline_df,
        pulse_df=pulse_df,
        years=[2030, 2050, 2075, 2100, 2125, 2150, 2200, 2300],
        classifier_threshold_cm=20.0,
        classifier_column="ais_2100_cm",
        weight_col="w_norm",
        pulse_size_gtc=0.01,   # actually GtCO₂ magnitude under v1.4.5
    )

    # Pretty-print
    pd.set_option("display.float_format", lambda x: f"{x:+.5f}")
    pd.set_option("display.width", 160)
    pd.set_option("display.max_columns", None)
    print("Lemoine-Traeger decomposition of the +0.01 GtCO₂ CO2 pulse at 2030 "
          "(reported per GtCO₂)")
    print("Classifier: baseline ais_2100_cm > 20 cm  =>  tipping-prone")
    print()
    print(df.to_string(index=False))

    # Algebraic-identity sanity check
    print()
    max_resid = (df["E_marginal_total"] - df["linear_plus_premium"]).abs().max()
    print(f"Max |E_marginal_total − linear_plus_premium|: {max_resid:.2e}")
    print("(should be ~1e-15; this is the floating-point identity check)")
