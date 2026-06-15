"""
extract_fossil_ch4_marginals_3brick.py

FOSSIL CH4 SLR marginal, by linear superposition of the existing CH4 and CO2
pulse arms (FaIR 2.2.4 has no native fossil-CH4 option; a fossil CH4 pulse =
CH4 + co-emitted oxidation CO2). Superposition validated at the GMST level to
0.007 % by FaIRtoFrEDI/test_fossil_ch4_pulse.py, and BRICK is linear in the
small pulse forcing by the Step-0 sanity battery -> the fossil SLR marginal is
exact to <1 %.

Per cell, per component c, the per-TgCH4 marginals are:
    nonfossil_c = (ch4_pulse_c  - baseline_c)              # cm per 1 TgCH4
    fossil_c    = nonfossil_c + OX_FACTOR*(co2_pulse_c - baseline_c)
where OX_FACTOR = (oxidation CO2 per TgCH4) / (CO2 pulse size)
                = (1 Tg CH4 * 44.009/16.043 / 1000 GtCO2) / 0.01 GtCO2
                = 2.7432e-3 / 0.01 = 0.27432.
(1 g CH4 -> 44.009/16.043 = 2.7432 g CO2 on full oxidation; the CO2 arm pulse is
0.01 GtCO2, so 0.27432 of it equals the oxidation CO2 of a 1-TgCH4 pulse.)

Weighted quantiles: pre93/brick2 Wong (wong_weights_{v}.csv); mengel uniform.

Output: outputs/pulse3brick_v145/marginals_fossil_ch4_summary.csv
  cols: version, basis(nonfossil|fossil), unit, component, year, n, ess_fraction,
        q05, q50, q95, mean   (cm per TgCH4)
"""
from pathlib import Path
import numpy as np
import pandas as pd

_TORCH = Path("/scratch/ms17839/SLR-RFF-BRICK")
ROOT = _TORCH if _TORCH.exists() else Path(__file__).resolve().parents[2]
PULSE_DIR = ROOT / "outputs" / "pulse3brick_v145"
OUT_CSV = PULSE_DIR / "marginals_fossil_ch4_summary.csv"

VERSIONS = ["pre93", "brick2", "mengel"]
WONG_WEIGHTED = {"pre93", "brick2"}

M_CO2, M_CH4 = 44.009, 16.043
CO2_PULSE_GT = 0.01                                   # CO2 arm pulse size (GtCO2)
OX_CO2_PER_TGCH4_GT = 1.0 * (M_CO2 / M_CH4) / 1000.0  # 2.7432e-3 GtCO2 per TgCH4
OX_FACTOR = OX_CO2_PER_TGCH4_GT / CO2_PULSE_GT        # 0.27432

COMPONENTS = [("total", "slr"), ("ais", "ais"), ("gsic", "gsic"),
              ("gis", "gis"), ("te", "te"), ("lws", "lws")]
YEARS = [2100, 2150, 2300]
PAIR_KEYS = ["rff_idx", "fair_cfg_idx", "seed_idx", "post_idx"]
UNIT = "cm/TgCH4"


def weighted_quantile(values, weights, qs=(0.05, 0.50, 0.95)):
    order = np.argsort(values)
    v, w = values[order], weights[order]
    cdf = np.cumsum(w) / w.sum()
    return np.interp(qs, cdf, v)


def ess_fraction(w):
    s1, s2 = w.sum(), (w ** 2).sum()
    return float((s1 ** 2) / s2 / len(w)) if s2 > 0 else float("nan")


def load_weights(version, paired_keys):
    n = len(paired_keys)
    if version not in WONG_WEIGHTED:
        return np.full(n, 1.0 / n)
    w = pd.read_csv(PULSE_DIR.parent / f"wong_weights_{version}.csv",
                    usecols=PAIR_KEYS + ["w_norm"])
    m = paired_keys.merge(w, on=PAIR_KEYS, how="left", validate="one_to_one")
    if m["w_norm"].isna().any():
        raise RuntimeError(f"{version}: missing Wong weight for some cells")
    return m["w_norm"].to_numpy()


def main():
    print(f"OX_FACTOR = {OX_FACTOR:.5f}  (oxidation CO2 {OX_CO2_PER_TGCH4_GT:.4e} GtCO2/TgCH4 "
          f"/ {CO2_PULSE_GT} GtCO2 pulse)")
    rows = []
    for version in VERSIONS:
        cm_cols = None
        base = pd.read_csv(PULSE_DIR / f"{version}_baseline.csv")
        co2 = pd.read_csv(PULSE_DIR / f"{version}_co2.csv")
        ch4 = pd.read_csv(PULSE_DIR / f"{version}_ch4.csv")
        cm_cols = [c for c in base.columns if c.endswith("_cm")]
        keep = PAIR_KEYS + cm_cols
        m = (base[keep].merge(co2[keep], on=PAIR_KEYS, suffixes=("_b", "_co2"),
                              how="inner", validate="one_to_one")
             .merge(ch4[keep].rename(columns={c: f"{c}_ch4" for c in cm_cols}),
                    on=PAIR_KEYS, how="inner", validate="one_to_one"))
        assert len(m) == 10000, f"{version}: paired {len(m)} != 10000"

        w = load_weights(version, m[PAIR_KEYS])
        ess = ess_fraction(w)
        wmode = "Wong" if version in WONG_WEIGHTED else "UNIFORM"

        for comp_label, prefix in COMPONENTS:
            for y in YEARS:
                col = f"{prefix}_{y}_cm"
                b = m[f"{col}_b"].to_numpy()
                co2_raw = m[f"{col}_co2"].to_numpy() - b      # cm per 0.01 GtCO2
                ch4_raw = m[f"{col}_ch4"].to_numpy() - b      # cm per 1 TgCH4
                nonfossil = ch4_raw
                fossil = ch4_raw + OX_FACTOR * co2_raw
                for basis, marg in (("nonfossil", nonfossil), ("fossil", fossil)):
                    q = weighted_quantile(marg, w)
                    rows.append(dict(
                        version=version, basis=basis, unit=UNIT,
                        component=comp_label, year=y, n=len(m),
                        ess_fraction=round(ess, 4),
                        q05=q[0], q50=q[1], q95=q[2],
                        mean=float(np.average(marg, weights=w))))
        print(f"  {version:7s}: paired=10000  weights={wmode}  ESS/N={ess:.3f}")

    df = pd.DataFrame(rows)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_CSV, index=False)
    print(f"\n[save] {OUT_CSV}  ({len(df)} rows)")

    # quick view: total, fossil vs nonfossil median, per version/year
    print("\n=== Total CH4 SLR marginal (cm/TgCH4), weighted median: nonfossil -> fossil ===")
    tot = df[df.component == "total"]
    print(f"{'version':7s} {'year':>4s} {'nonfossil':>11s} {'fossil':>11s} {'fossil/nonfossil':>17s}")
    for v in VERSIONS:
        for y in YEARS:
            nf = float(tot[(tot.version==v)&(tot.basis=="nonfossil")&(tot.year==y)].q50.iloc[0])
            fo = float(tot[(tot.version==v)&(tot.basis=="fossil")&(tot.year==y)].q50.iloc[0])
            print(f"{v:7s} {y:>4d} {nf:>11.3e} {fo:>11.3e} {fo/nf:>16.3f}x")


if __name__ == "__main__":
    raise SystemExit(main())
