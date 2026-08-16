#!/usr/bin/env python3
"""
diag_d2_stream_attribution.py — WHICH D2 stream moves `thermal_alpha`?

THE QUESTION. L10 -> L11 moved thermal_alpha +1.31 L10 sd at a mix ratio of 19.7
(diag_l10_vs_l11_projection.py). D1 alone accounts for only 19% of that
(22635dd), so the other 81% is D2 -- but D2 has TWO streams and no chain in the
repo separated them: D2chk, D2chk2 and D2chk3 all carry both d2_gsic_* and
d2_steric_*.

  H-A  the STERIC basis couples to alpha. It is orthogonalised against S(t)
       ITSELF (cb21def), so delta cannot mimic a rescaling of alpha in the PLAIN
       inner product -- but the likelihood metric is the AR(1)-correlated
       heteroskedastic precision, in which that orthogonality does not hold, and
       d2_basis documents exactly this.
  H-B  the GSIC term moves alpha indirectly, e.g. by a partition trade. NOTE
       this was weaker than the first 2026-08-16 handoff claimed: D1 removed the
       total from the likelihood, so nothing rewards the component sum and there
       is no obvious pathway. The near-cancellation in the projected total
       (glaciers -1.2, steric +1.1 at 2100) may be two independent effects.

THE ARMS, from julia/run_d2_stream_attribution.sh, 4 x 250k each:
  D2S  --d2-streams=steric   = D1 + D2-steric  (55 params)
  D2G  --d2-streams=gsic     = D1 + D2-gsic    (55 params)
Both are the full L11 configuration minus one stream, so BOTH include D1. The
marginal contribution of a D2 stream is therefore (arm - L10) minus D1's own
+0.24 sd, and the two arms do NOT decompose additively -- the script reports the
non-additivity rather than hiding it.

THE GATE is 22635dd's: a between-arm shift is reportable only if it exceeds the
worst between-CHAIN disagreement within either arm by MIX_RATIO_MIN. An arm that
fails the gate has NOT shown an effect; it has shown that 250k is too short to
resolve one.

STALE-CHAIN HAZARD. per_chain_medians globs chain_<TAG>_seed*.csv, so a short
smoke run with the same tag silently pollutes the median. The pre-fix smoke
chains are in outputs/quarantine/20260816_adcov_size_collision/. This script
asserts every chain it reads is the expected length.

  source ~/climate-env/bin/activate && python3 python/diag_d2_stream_attribution.py
Writes outputs/diag_d2_stream_attribution.csv
"""
import glob
import os

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "outputs/diag_d2_stream_attribution.csv")

PARAM = "thermal_alpha"
MIX_RATIO_MIN = 2.0                  # 22635dd's gate
BURN_FRAC = 0.5
# tag -> (what it is, stride, minimum acceptable chain length)
ARMS = [("L10", "no D2, total IN", 100, 2_000_000),
        ("L11", "both streams", 100, 2_000_000),
        ("D2S", "steric stream only", 1, 250_000),
        ("D2G", "gsic stream only", 1, 250_000)]
# D1-only arm, recorded in 22635dd (chains since deleted). Both arms tightly
# mixed there. Used to net D1 out of the two one-stream arms.
ALPHA_D1 = (0.15023, 0.15205)


def per_chain_medians(tag, param, stride, min_len):
    out = {}
    for f in sorted(glob.glob(os.path.join(REPO, f"outputs/mcmc/chain_{tag}_seed*.csv"))):
        d = pd.read_csv(f, usecols=[param])
        if len(d) < min_len:
            raise SystemExit(
                f"{os.path.basename(f)} has {len(d)} rows, expected >= {min_len}. "
                "A short smoke chain shares this glob and would pollute the median — "
                "move it to outputs/quarantine/ before rerunning.")
        out[os.path.basename(f).split("seed")[1][:4]] = \
            float(d[param].iloc[int(len(d) * BURN_FRAC)::stride].median())
    if not out:
        raise SystemExit(f"no chains for tag {tag}")
    return out


def main():
    sd = pd.read_csv(os.path.join(REPO, "data/MimiBRICK/parameters_subsample_brick_mengel_L10.csv"),
                     usecols=[PARAM])[PARAM].std()
    chains = {t: per_chain_medians(t, PARAM, st, ml) for t, _, st, ml in ARMS}
    med = {t: float(np.median(list(v.values()))) for t, v in chains.items()}
    base = med["L10"]
    l10_spread = max(chains["L10"].values()) - min(chains["L10"].values())

    print(f"{PARAM} by arm — per-chain post-burn medians\n")
    for t, what, _, _ in ARMS:
        print(f"  {t:4s} {what:20s} " + "  ".join(f"{s}:{x:.5f}" for s, x in chains[t].items()))

    print(f"\n  {'arm':5s}{'what':22s}{'median':>9s}{'vs L10':>10s}{'L10 sd':>9s}"
          f"{'spread':>10s}{'MIX':>7s}  verdict")
    rows = []
    for t, what, _, _ in ARMS:
        shift = med[t] - base
        spread = max(max(chains[t].values()) - min(chains[t].values()), l10_spread)
        mix = abs(shift) / spread if spread > 0 else np.inf
        verdict = "—" if t == "L10" else (
            "REPORTABLE" if mix > MIX_RATIO_MIN else "NOT RESOLVED at 250k")
        print(f"  {t:5s}{what:22s}{med[t]:9.5f}{shift:+10.5f}{shift / sd:+9.2f}"
              f"{spread:10.5f}{mix:7.1f}  {verdict}")
        rows.append(dict(arm=t, what=what, median=med[t], shift=shift,
                         shift_in_L10_sd=shift / sd, chain_spread=spread,
                         mix_ratio=mix, verdict=verdict))

    full = med["L11"] - base
    s, g = med["D2S"] - base, med["D2G"] - base
    d1 = ALPHA_D1[1] - ALPHA_D1[0]
    print(f"\n  ATTRIBUTION of the joint L10->L11 move ({full:+.5f} = {full / sd:+.2f} L10 sd)")
    print(f"    D2S (D1 + steric) {s / full * 100:6.1f}%   "
          f"netting out D1's {d1 / sd:+.2f} sd -> steric alone {(s - d1) / sd:+.2f} L10 sd")
    print(f"    D2G (D1 + gsic)   {g / full * 100:6.1f}%   "
          f"netting out D1's {d1 / sd:+.2f} sd -> gsic alone   {(g - d1) / sd:+.2f} L10 sd")
    print(f"    arms sum to {(s + g) / full * 100:.0f}% of the joint move — "
          f"{'ADDITIVE' if abs(s + g - full) < 0.3 * abs(full) else 'SUB-ADDITIVE: the streams interact'}")

    pd.DataFrame(rows).to_csv(OUT, index=False)
    print(f"\nwrote {os.path.relpath(OUT, REPO)}")


if __name__ == "__main__":
    main()
