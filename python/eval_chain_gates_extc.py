#!/usr/bin/env python3
"""Per-draw gate evaluation for extC chains (3-reservoir + sampled amp + D-ledger).

REPLACES eval_chain_gates.py for extC-family chains (the old script assumes the
extB3 single-reservoir 5-param glacier block and is kept as provenance for those
chains). This one exec-inherits the d1e prefix (-> d1d -> d0) and REUSES
metrics_d, so gates/ladder/spread/ledger have exactly one implementation.

Per thinned draw: per-block (a, b, T_off) and sampled amp_b from the chain
override the C_both structure copies; kappa = 10^gic_log10_kappa_*; nu is FIXED
at the anchored value (obsfit basis — the calibrator's FIT_BASIS in sampled
mode); (sigma, rho) = (sd_gsic, rho_gsic); (u_mm, delta, u_pre, s_r5) from the
gic_* scope params. metrics_d then yields the four gates (inv / lec-ledger /
ladder / spread), SSP levels, ledger decomposition, per-reservoir rates, and
rate_modern_hind. Deficit columns are NaN (the pathological comparator is an
offline-cell construct; not a gate).

SELF-TEST (must pass before any chain is read): the stored d1e
C_both/ANCH/unc_t5d theta evaluated through this script's draw path (regchar
amps) reproduces the d1e CSV row's S1900/inv_z/spread/npass.

Usage:
  python3 python/eval_chain_gates_extc.py [--chain=outputs/mcmc/chain_extC1_seed2026_n500000.csv]
                                          [--ndraw=200] [--burn-frac=0.5]
Outputs: outputs/eval_gates_<chaintag>.csv + console summary.
"""
import glob
import os
import re
import sys

import numpy as np
import pandas as pd

REPO_EG = os.path.expanduser("~/Documents/2026/CodeProjects/SLR-RFF-BRICK")
D1E_SRC = os.path.join(REPO_EG, "python/d1e_dside_ledger.py")

_src_e = open(D1E_SRC).read()
_MARKER_E = "# ---------------------------------------------------------------- run\n"
assert _src_e.count(_MARKER_E) == 1
exec(_src_e.split(_MARKER_E)[0])


def _argval(pfx, default=None):
    for a in sys.argv[1:]:
        if a.startswith(pfx):
            return a[len(pfx):]
    return default


CHAIN = _argval("--chain=")
if CHAIN is None:
    cands = sorted(glob.glob(os.path.join(REPO, "outputs/mcmc/chain_extC*_seed*_n*.csv")))
    assert cands, "no extC chain found; pass --chain="
    CHAIN = cands[-1]
NDRAW = int(_argval("--ndraw=", "200"))
BURN_FRAC = float(_argval("--burn-frac=", "0.5"))
CTAG = re.search(r"chain_(.+?)_seed(\d+)_n(\d+)\.csv", os.path.basename(CHAIN))
OUT_EVAL = os.path.join(REPO, f"outputs/eval_gates_{CTAG.group(1)}_seed{CTAG.group(2)}.csv")

BC = pd.read_csv(os.path.join(REPO, "outputs/extc_block_constants.csv")).set_index("block")
NU_FIXED = {b: float(BC.loc[b, "nu_anch_obsfit"]) for b in SPEC_3RES}   # FIT_BASIS=obsfit

# base structures (same build order as d1d/d1e for the cached ladders + rung data)
res3_raw = {n: build_reservoir(n, m, farinotti_basis=True)
            for n, m in SPEC_3RES.items()}
blk2_raw = {n: build_reservoir(n, m, farinotti_basis=False)
            for n, m in SPEC_2BLK.items()}
_ = {n: four_rung_fit(b) for n, b in blk2_raw.items()}
_ = {n: two_rung_anchor(b) for n, b in res3_raw.items()}
cboth_base = {n: four_rung_fit(b) for n, b in res3_raw.items()}


def draw_metrics(row, label):
    """Evaluate one chain draw (or a synthetic one) through metrics_d."""
    resv = {}
    for n in SPEC_3RES:
        resv[n] = dict(cboth_base[n],
                       a=float(row[f"gic_a_{n}"]), b=float(row[f"gic_b_{n}"]),
                       T_off=float(row[f"gic_T_off_{n}"]),
                       amp_b=float(row.get(f"gic_amp_{n}", cboth_base[n]["amp_b"])))
    th = dict(sigma=float(row["sd_gsic"]), rho=float(row["rho_gsic"]),
              delta=float(row["gic_delta"]), u_mm=float(row["gic_u_unch"]),
              u_pre_mm=float(row["gic_u_pre"]), s_r5_mm=float(row["gic_s_r5"]))
    for n in SPEC_3RES:
        th[f"kappa_{n}"] = 10.0 ** float(row[f"gic_log10_kappa_{n}"])
        th[f"nu_{n}"] = NU_FIXED[n]
    m = metrics_d(resv, th, "unc_t5d", "CHAIN", np.nan, np.nan, HIND_D1E, OBS_ADJ,
                  label=label)
    return None if m is None else m[0]


# ---------------------------------------------------------------- self-test
print(f"eval_chain_gates_extc | commit={COMMIT} | chain={os.path.basename(CHAIN)} "
      f"| ndraw={NDRAW} burn={BURN_FRAC}")
d1e_rows = pd.read_csv(os.path.join(REPO, "outputs/d1e_dside_ledger.csv"))
ref = d1e_rows[d1e_rows.label == "C_both/ANCH/unc_t5d"].iloc[0]
synth = {f"gic_a_{n}": cboth_base[n]["a"] for n in SPEC_3RES}
synth.update({f"gic_b_{n}": cboth_base[n]["b"] for n in SPEC_3RES})
synth.update({f"gic_T_off_{n}": cboth_base[n]["T_off"] for n in SPEC_3RES})
synth.update({f"gic_amp_{n}": cboth_base[n]["amp_b"] for n in SPEC_3RES})
synth.update({f"gic_log10_kappa_{n}": np.log10(ref[f"kappa_{n}"]) for n in SPEC_3RES})
synth.update(sd_gsic=ref["sigma"], rho_gsic=ref["rho"], gic_delta=ref["delta"],
             gic_u_unch=ref["u_mm"], gic_u_pre=ref["u_pre_mm"], gic_s_r5=ref["s_r5_mm"])
st = draw_metrics(synth, "SELFTEST")
# NB the self-test nu differs from the d1e ANCH nu only at the regchar-vs-obsfit
# anchored level (identical to 3 s.f.); tolerances account for it
checks = [("s1900_inv_mm", 0.2), ("inv_z", 0.05), ("spread", 0.2), ("lec_z", 0.05)]
ok = all(abs(st[c] - ref[c]) < tol for c, tol in checks)
# nu difference caveat: d1e ANCH used the REGCHAR-anchored nu; the chain uses obsfit
for c, tol in checks:
    print(f"  selftest {c}: {st[c]:.4f} vs d1e {ref[c]:.4f} "
          f"{'PASS' if abs(st[c] - ref[c]) < tol else 'FAIL'}")
if not ok:
    raise SystemExit("SELF-TEST FAILED - do not trust chain evaluation")

# ---------------------------------------------------------------- chain eval
ch = pd.read_csv(CHAIN)
ch = ch.iloc[int(len(ch) * BURN_FRAC):]
idxs = np.linspace(0, len(ch) - 1, min(NDRAW, len(ch))).astype(int)
rows = []
for i, ix in enumerate(idxs):
    r = draw_metrics(ch.iloc[ix], f"draw{ix}")
    if r is not None:
        for n in SPEC_3RES:
            r[f"amp_{n}"] = float(ch.iloc[ix].get(f"gic_amp_{n}", np.nan))
        r["log_post"] = float(ch.iloc[ix]["log_post"])
        rows.append(r)
ev = pd.DataFrame(rows)
ev.to_csv(OUT_EVAL, index=False, float_format="%.5f")

# ---------------------------------------------------------------- summary
gates = ["g_inv", "g_lec", "g_lad", "g_spread"]
print(f"\n=== gate pass fractions over {len(ev)} draws ===")
for g in gates:
    print(f"  {g:9s} {ev[g].mean():.3f}")
print(f"  npass==4  {(ev.npass == 4).mean():.3f}")
med = ev.median(numeric_only=True)
print(f"\n  medians: S1900_inv {med.s1900_inv_mm:.1f} + s_r5 {med.s_r5_mm:.1f} + "
      f"u_pre {med.u_pre_mm:.1f} = ledger {med.s1900_ledger_mm:.1f} (z {med.lec_z:+.2f}) | "
      f"inv_z {med.inv_z:+.2f} | spread {med.spread:.2f} | "
      f"ds126/245/585 {med.ds126:.1f}/{med.ds245:.1f}/{med.ds585:.1f} | "
      f"rate_hind {med.rate_modern_hind:.3f} (obs_adj "
      f"{obs_era_rate(OBS_ADJ, *RATE_WIN):.3f}) | U {med.u_mm:.1f} | "
      f"delta {med.delta:+.2f} ({med.delta_sigmas:.1f}sig)")
print(f"  amp medians: " + " ".join(f"{n} {ev[f'amp_{n}'].median():.2f}"
                                    for n in SPEC_3RES if ev[f"amp_{n}"].notna().any()))
print(f"  per-res rates 2000-23 (obs R19 {BC.loc['R19','glambie_rate']:.3f} / "
      f"SLOWP {BC.loc['SLOWP','glambie_rate']:.3f} / FAST {BC.loc['FAST','glambie_rate']:.3f}): "
      + " ".join(f"{n} {ev[f'rate0023_{n}'].median():.3f}" for n in SPEC_3RES))
print(f"  legacy S1900_all median {ev.s1900_legacy_mm.median():.1f} "
      f"(old box verdict {'in' if ev.g_s1900_legacy_box.mean() > 0.5 else 'OUT'} "
      f"for {ev.g_s1900_legacy_box.mean():.0%})")
print(f"\nWrote {os.path.relpath(OUT_EVAL, REPO)}")
