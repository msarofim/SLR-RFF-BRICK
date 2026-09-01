#!/usr/bin/env python3
"""diag_proposal_seed_by_vintage.py — WHICH PROPOSAL COVARIANCE DID EACH VINTAGE ACTUALLY USE?

Written 2026-09-01 after `scope_amp_likelihood_tilt.jl` measured the glacier law to be inert
in the calibration likelihood (<=7.3e-5 log units), which left the L21->L23 shift in
`ais_gmst_amp` with no mechanism. This reads the answer straight out of the seed diagnostics
each run wrote at startup, so it is evidence from the runs themselves, not a reconstruction.

WHAT IT FOUND. L21/L22 were launched with --adcov=adapted_cov_L14tune_seed2026.csv, a NAMED
58-column file mapped by name, 58 of 58. L23/L23b/L24 carry no --adcov and fall through to the
head of the default preference list, adapted_cov_L11tune3_seed2026.csv -- whose columns are
x1..x57, i.e. NAMELESS, mapped POSITIONALLY "as L11 layout" onto a 58-parameter model.

That is the exact hazard calibrate_mcmc_ext.jl documents against itself at the adapted_cov
write: "A nameless covariance can only be re-read through a hardcoded vintage table, and
getting one of those orderings wrong is silent (it is a valid permutation of a valid matrix)
-- that is how L13's ais_c was seeded with ais_slope's variance."

    python python/diag_proposal_seed_by_vintage.py
Reads outputs/mcmc/seed_diag_<TAG>_seed<SEED>.txt
"""
import os, re, glob

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MC = os.path.join(REPO, "outputs", "mcmc")
VINTAGES = [("L21", 2026), ("L22", 2026), ("L23", 2026), ("L23b", 3026), ("L24", 2026)]

print("=" * 100)
print("PROPOSAL COVARIANCE AND AIS-BLOCK SCALES, BY VINTAGE")
print("=" * 100)
scales = {}
for tag, seed in VINTAGES:
    f = os.path.join(MC, f"seed_diag_{tag}_seed{seed}.txt")
    if not os.path.exists(f):
        print(f"\n{tag}: no seed diagnostic on disk")
        continue
    txt = open(f).read()
    adcov = re.search(r"ADCOV = (\S+)", txt)
    mapped = re.search(r"seeding proposal: (.+?)\)", txt)
    print(f"\n{tag}  (seed {seed})")
    print(f"   cov    {os.path.basename(adcov.group(1)) if adcov else '?'}")
    print(f"   map    {mapped.group(1) if mapped else '?'}")
    d = {}
    for m in re.finditer(r"^\s+(ais_\w+|gis_s_high)\s+([\d.eE+-]+)\s+floor", txt, re.M):
        d[m.group(1)] = float(m.group(2))
    scales[tag] = d

ref = scales.get("L21", {})
if ref and "L23" in scales:
    print("\n" + "=" * 100)
    print("AIS-BLOCK PROPOSAL SCALE, L23 RELATIVE TO L21  (sqrt of the covariance diagonal)")
    print("=" * 100)
    print(f"\n{'parameter':22s} {'L21/L22':>12s} {'L23/L24':>12s} {'ratio':>10s}")
    for k, v in ref.items():
        w = scales["L23"].get(k)
        if w is None:
            continue
        print(f"{k:22s} {v:12.4g} {w:12.4g} {v/w if w else float('nan'):10.2f}x")
    print("\n⚠ A 3-5x TIGHTER proposal on the AIS block, in a sampler where 17-19 marginals fail")
    print("  R-hat on every vintage, is a mechanism for moving a POOLED MEDIAN without changing")
    print("  a width the prior sets. L23b shares this covariance, so the RNG-only replicate")
    print("  could not have detected it (two_statistics_can_be_blind).")
