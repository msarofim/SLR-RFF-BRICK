#!/usr/bin/env python3
"""What re-centring the RGI 19 glacier amplification prior from 0.72 to 0.68 would do to the projections.

  python3 python/diag_r19_amp_prior_reweight.py

Marcus 2026-11-07: "Dig into the source of 0.72, or determine if we should switch to 0.68." 0.72 entered with the
sampled-amp mode (calibrate_mcmc_ext.jl, commit 02150d8, 2026-08-09) citing "cross-dataset ranges"; no derivation is
recorded. The three products' through-origin fits over 1901-2024 are HadCRUT5 0.615, Berkeley Earth 0.847, GISTEMP 0.580
(outputs/diag_amp_dataset_comparison.csv); their mean is 0.68, the rule Greenland's prior uses.

Re-centring is priced EXACTLY by importance reweighting: only the amp's marginal prior changes (the likelihood, which
reads amp through the GlacierMIP3 frame conversion, and the kappa-prior centre, a conditional prior, are unchanged as
functions), so the new posterior is the old one times N(a; NEW, SD) / N(a; OLD, SD) on the same truncation bounds (the
normalizing constants cancel when the weights are normalized). Corrected 2026-11-09: this said amp enters "only through
its own prior and the kappa-prior centre"; it also enters the GlacierMIP3 likelihood (calibrate_mcmc_ext.jl @43d84aa:
1582-1590), which does not affect the reweighting. The weights are applied to the paper's joint-arm draws (draw k = posterior row 1 + 5(k - 1)).
Writes outputs/diag_r19_amp_prior_reweight_L27.csv.
"""
import os

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(REPO)
LADRILLO = os.path.join(os.path.dirname(REPO), "Ladrillo")
POSTERIOR = os.path.join(LADRILLO, "data/posterior/ladrillo_L27_posterior.csv")
STEM = "L27_tap4p69K_V5p64m_tau800"
DRAWS = "outputs/scope_slr_fairunc_draws_{m}_spliced_%s.csv" % STEM
OUT = "outputs/diag_r19_amp_prior_reweight_L27.csv"
OLD_MU, NEW_MU, SD = 0.72, 0.68, 0.15
ROW_STEP = 5                                     # the joint arm reads posterior rows 1:5:10000
SCEN = [("vvVL", "Very Low"), ("vvLN", "Low-to-Negative"), ("vvL", "Low"), ("vvML", "Medium-to-Low"),
        ("vvM", "Medium"), ("vvHL", "High-to-Low"), ("vvH", "High")]
COMPONENTS, HORIZONS = ("glaciers", "total"), (2100, 2300)


def wmedian(x, w):
    o = np.argsort(x)
    c = np.cumsum(w[o]) / w.sum()
    return float(np.interp(0.5, c, x[o]))


amp = pd.read_csv(POSTERIOR)["gic_amp_R19"].values
rows = []
for m, lab in SCEN:
    d = pd.read_csv(DRAWS.format(m=m))
    d = d[d.arm == "joint"]
    for comp in COMPONENTS:
        for h in HORIZONS:
            x = d[(d.component == comp) & (d.horizon == h)].sort_values("draw")
            a = amp[(x.draw.values - 1) * ROW_STEP]
            w = np.exp(-0.5 * ((a - NEW_MU) / SD) ** 2 + 0.5 * ((a - OLD_MU) / SD) ** 2)
            v = x.value_cm.values
            rows.append(dict(scenario=m, label=lab, component=comp, horizon=h, n=len(v), median_old_cm=np.median(v),
                             median_new_cm=wmedian(v, w), shift_cm=wmedian(v, w) - np.median(v),
                             ess=w.sum() ** 2 / (w ** 2).sum()))
r = pd.DataFrame(rows)
r["provenance"] = ("diag_r19_amp_prior_reweight.py | Ladrillo L27 joint arm (%s) | importance weights N(a; %.2f, %.2f) / "
                   "N(a; %.2f, %.2f) on gic_amp_R19 (same bounds [0.58, 0.88]) | weighted median by linear interpolation of "
                   "the cumulative weights | cm rel 1995-2014 | no RNG" % (STEM, NEW_MU, SD, OLD_MU, SD))
r.to_csv(OUT, index=False)
pd.set_option("display.width", 200)
print(r.drop(columns="provenance").round(3).to_string(index=False))
for comp in COMPONENTS:
    print("max |shift| %s: %.3f cm" % (comp, r[r.component == comp].shift_cm.abs().max()))
print("posterior gic_amp_R19: median %.3f, 5-95 %.3f-%.3f" % (np.median(amp), *np.quantile(amp, [0.05, 0.95])))
print("wrote " + OUT)
