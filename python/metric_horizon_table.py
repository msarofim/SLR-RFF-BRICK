"""Headline metric table: SLR-based vs temperature-based CH4:CO2 equivalence by horizon.

THE KEY MESSAGE this table quantifies (Marcus 2026-08-02): CH4's sea-level impact is
much longer-lasting than its temperature impact. An SLR-based equivalence metric values
CH4 ABOVE its GWP-100; a GTP-style endpoint-temperature metric values it WELL BELOW.

Both metrics are formed identically -- ensemble MEAN marginal per GWP-100-equivalent
tonne, so CO2 is 1.0 by construction and the CH4 entry IS the metric ratio:

    metric(CH4, H) = [ mean d<X> per Tg CH4 @H / GWP ] / [ mean d<X> per GtCO2 @H ]

with X = total SLR (cm) for the SLR metric and GMST (degC) for the temperature metric.

Horizons are PULSE-RELATIVE (years since the 2030 emission), per the GWP-100 framing:
70/100/120/150/270 yr = calendar 2100/2130/2150/2180/2300. The 100- and 150-yr SLR cells
require a driver run with --horizons covering 2130/2180 (out-tag _pr); with the default
4-horizon outputs (_subann) this script reports the 3 horizons that exist and says so.

Basis conventions (all settled 2026-08-02, handoff_2026-08-02_ch4co2_metric_horizons):
  * MEAN, not median -- the pooled median is sample-fragile under the AIS tip mode.
  * INDEPENDENT (equal-weight) is the production basis; conditional weighting is a
    documented consistency check and is reported alongside, not as the headline.
  * Sub-annual DAIS integrator is mandatory for quotable pulse numbers.
GWP basis is an OPEN reporting choice (research plan Sec 9.5) -- reported here as a
first-class function over GWP_BASES, never collapsed to a single silent default.
"""
import argparse
import csv
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
MCMC_DIR = REPO / "outputs" / "mcmc"
FAIR_DIR = Path.home() / "Documents/2026/CodeProjects/FaIRtoFrEDI/fair_outputs"

PULSE_YEAR = 2030
CO2_PULSE_GT = 10.0          # driver pulse size, GtCO2  -> per-GtCO2 = /CO2_PULSE_GT
CH4_PULSE_TG = 1.0           # driver pulse size, Tg CH4 = Mt CH4
SLR_UNIT = "cm"
TEMP_UNIT = "degC"

# GWP-100 AR6. Biogenic CH4 carries no fossil-carbon oxidation term; fossil does.
GWP_BASES = {"GWP-100 biogenic": 27.0, "GWP-100 fossil": 29.8, "GWP-20 biogenic": 79.7}
HEADLINE_GWP = "GWP-100 biogenic"   # matches the biogenic CH4 pulse arm actually run

# calendar year -> years since the pulse
def yr_rel(cal):
    return cal - PULSE_YEAR


ARMS = {  # label -> (slr basis suffix, fair npz stem)
    "stochastic": ("", "fair_ensemble_v145_ssp245_pulse{gas}_2030"),
    "deterministic": ("_nonoise_flatsolar",
                      "fair_ensemble_v145_ssp245_pulse{gas}_2030_nonoise_flatsolar"),
}
CO2_GAS_STEM = "co2_10gt"
CH4_GAS_STEM = "ch4bio_1tg"
CH4_SLR_BASIS = "_ch4bio1tg"


def pairs_path(basis, tag):
    return MCMC_DIR / f"wong_cond_pulse_pairs{basis}{tag}.csv"


def runmeta_path(basis, tag):
    return MCMC_DIR / f"wong_cond_runmeta{basis}{tag}.csv"


def total_horizons(path):
    """Calendar years with a d_total@<year> column, in file order."""
    with open(path) as f:
        header = next(csv.reader(f))
    return [int(c.split("@")[1]) for c in header if c.startswith("d_total@")]


def slr_means(path, years):
    """MEAN marginal total SLR at each horizon, equal-weight (INDEPENDENT, production
    basis) and importance-weighted (COUPLED, consistency check)."""
    cols = ["w"] + [f"d_total@{y}" for y in years]
    df = pd.read_csv(path, usecols=cols)
    w = df["w"].to_numpy()
    out = {}
    for y in years:
        d = df[f"d_total@{y}"].to_numpy()
        out[y] = (float(d.mean()), float(np.average(d, weights=w)))
    return out, len(df)


def temp_means(stem, years):
    """MEAN marginal GMST at each horizon from the paired FaIR ensemble dump."""
    z = np.load(FAIR_DIR / f"{stem}.npz")
    yrs = z["years"]
    out = {}
    for y in years:
        i = int(np.argmin(np.abs(yrs - (y + 0.5))))   # FaIR timepoints are mid-year
        out[y] = float(z["temp_delta"][i].mean())
    return out


def read_provenance(path):
    if not path.exists():
        return {}
    with open(path) as f:
        rows = list(csv.reader(f))
    return {r[0]: r[1] for r in rows if len(r) >= 2}


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tag", default="_pr",
                    help="driver --out-tag of the runs to read (default _pr = the "
                         "pulse-relative-horizon production runs; _subann = the "
                         "default-4-horizon runs, which lack 2130/2180)")
    ap.add_argument("--arm", default="stochastic", choices=list(ARMS),
                    help="FaIR forcing basis for the headline table (both are written)")
    ap.add_argument("--out-stem", default=None,
                    help="output stem under outputs/ (default metric_horizon_table<tag>)")
    args = ap.parse_args()

    stem = args.out_stem or f"metric_horizon_table{args.tag}"
    rows = []
    for arm, (slr_basis, fair_stem) in ARMS.items():
        co2_p = pairs_path(slr_basis, args.tag)
        ch4_p = pairs_path(CH4_SLR_BASIS + slr_basis, args.tag)
        if not (co2_p.exists() and ch4_p.exists()):
            print(f"[skip] {arm}: missing {co2_p.name if not co2_p.exists() else ch4_p.name}")
            continue

        years = total_horizons(co2_p)
        ch4_years = total_horizons(ch4_p)
        if years != ch4_years:
            raise SystemExit(f"horizon mismatch {arm}: CO2 {years} vs CH4 {ch4_years}")

        co2_slr, n_co2 = slr_means(co2_p, years)
        ch4_slr, n_ch4 = slr_means(ch4_p, years)
        co2_t = temp_means(fair_stem.format(gas=CO2_GAS_STEM), years)
        ch4_t = temp_means(fair_stem.format(gas=CH4_GAS_STEM), years)
        prov = read_provenance(runmeta_path(slr_basis, args.tag))

        print(f"\n=== {arm} | SLR basis '{slr_basis or '(none)'}' | "
              f"{n_co2:,} CO2 pairs, {n_ch4:,} CH4 pairs | horizons {years} ===")
        print(f"{'yr':>4} {'cal':>5} | {'CO2 SLR':>10} {'CH4 SLR':>10} | "
              f"{'CO2 dT':>10} {'CH4 dT':>10} | {'SLR met':>8} {'T met':>8} {'SLR/T':>7}")
        print(f"{'':>4} {'':>5} | {'cm/GtCO2':>10} {'cm/Tg':>10} | "
              f"{'degC/GtCO2':>10} {'degC/Tg':>10} | {'ratio':>8} {'ratio':>8} {'x':>7}")
        for y in years:
            c_slr = co2_slr[y][0] / CO2_PULSE_GT
            h_slr = ch4_slr[y][0] / CH4_PULSE_TG
            c_dt = co2_t[y] / CO2_PULSE_GT
            h_dt = ch4_t[y] / CH4_PULSE_TG
            gwp = GWP_BASES[HEADLINE_GWP]
            m_slr = (h_slr / (gwp * 1e-3)) / c_slr    # Tg -> GtCO2e via GWP (1 Tg = 1e-3 Gt)
            m_t = (h_dt / (gwp * 1e-3)) / c_dt
            print(f"{yr_rel(y):>4} {y:>5} | {c_slr:>10.4e} {h_slr:>10.4e} | "
                  f"{c_dt:>10.4e} {h_dt:>10.4e} | {m_slr:>8.3f} {m_t:>8.3f} "
                  f"{m_slr / m_t:>7.2f}")

            row = dict(arm=arm, years_since_pulse=yr_rel(y), calendar_year=y,
                       co2_slr_cm_per_gtco2=c_slr, ch4_slr_cm_per_tg=h_slr,
                       co2_slr_cm_per_gtco2_coupled=co2_slr[y][1] / CO2_PULSE_GT,
                       ch4_slr_cm_per_tg_coupled=ch4_slr[y][1] / CH4_PULSE_TG,
                       co2_dtemp_degc_per_gtco2=c_dt, ch4_dtemp_degc_per_tg=h_dt,
                       gwp_basis_headline=HEADLINE_GWP,
                       slr_metric_ch4=m_slr, temp_metric_ch4=m_t,
                       slr_over_temp=m_slr / m_t, n_pairs=n_co2)
            for label, g in GWP_BASES.items():
                key = label.lower().replace("-", "").replace(" ", "_")
                row[f"slr_metric_ch4_{key}"] = (h_slr / (g * 1e-3)) / c_slr
                row[f"temp_metric_ch4_{key}"] = (h_dt / (g * 1e-3)) / c_dt
            row.update(prov_model_lineage=prov.get("model_lineage", ""),
                       prov_dais_integrator=prov.get("dais_integrator", ""),
                       prov_forcing_basis=prov.get("forcing_basis", ""),
                       prov_weighting="INDEPENDENT (equal-weight) headline; "
                                      "coupled columns = conditional-weighting check",
                       prov_units=f"SLR {SLR_UNIT}; temperature {TEMP_UNIT}; "
                                  f"per GtCO2 / per Tg CH4; metrics dimensionless",
                       prov_statistic="ensemble MEAN (median is tip-mode fragile)",
                       prov_code_git_commit=prov.get("code_git_commit", ""))
            rows.append(row)

        missing = [y for y in (2130, 2180) if y not in years]
        if missing:
            print(f"  NOTE: pulse-relative 100/150-yr cells missing (no {missing} "
                  f"horizon in this run); re-run driver with --horizons including them.")

    if not rows:
        raise SystemExit(f"no arms found for tag '{args.tag}' -- run the driver first")

    df = pd.DataFrame(rows)
    csv_out = REPO / "outputs" / f"{stem}.csv"
    df.to_csv(csv_out, index=False)
    print(f"\nWrote {csv_out}")

    md = REPO / "outputs" / f"{stem}.md"
    head = df[df.arm == args.arm]
    with open(md, "w") as f:
        f.write(f"# CH4:CO2 equivalence by pulse-relative horizon "
                f"({PULSE_YEAR} pulse, SSP2-4.5, BRICK-AM)\n\n")
        f.write(f"Ensemble MEAN marginal per {HEADLINE_GWP}-equivalent tonne; CO2 = 1.0 by "
                f"construction. FaIR basis: {args.arm}. INDEPENDENT (equal-weight) pipeline.\n\n")
        f.write("| years after pulse | calendar | temperature (GTP-style) | total SLR | "
                "SLR / temperature |\n|---|---|---|---|---|\n")
        for _, r in head.iterrows():
            f.write(f"| {int(r.years_since_pulse)} | {int(r.calendar_year)} | "
                    f"{r.temp_metric_ch4:.2f} | {r.slr_metric_ch4:.2f} | "
                    f"{r.slr_over_temp:.1f}x |\n")
        f.write(f"\nGWP basis is a reporting choice; the same table on the other bases "
                f"({', '.join(k for k in GWP_BASES if k != HEADLINE_GWP)}) is in "
                f"`{csv_out.name}`. Metrics scale exactly as 1/GWP, so the SLR/temperature "
                f"column is GWP-INVARIANT.\n")
    print(f"Wrote {md}")


if __name__ == "__main__":
    main()
