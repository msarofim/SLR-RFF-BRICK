#!/usr/bin/env python3
"""
scope_ais_module_assessment.py — STEP 1: HOW GOOD IS OUR AIS MODULE, against
                                 old BRICK (= BRICK 2.0) and against the literature,
                                 given that some of the uncertainty is irreducible?

Marcus 2026-08-25, step 1 of 5. Scored on his own 2026-08-14 acceptance criteria:
(1) formulation at least as credible as BRICK 2.0's, (2) hindcast match at least as
good, (3) projection spread at least as good (FACTS/MAGICC match, or more physical).
Criterion (4), the joint calibration, is step 5 and is NOT scored here.

THE FINDING THAT REFRAMES CRITERION (1). Ladrillo's AIS component IS BRICK 2.0's.
`replace!` is applied only to the GLACIER and GREENLAND slots
(`brick_mengel.jl:57,117,173,238,267`); the AIS slot is never replaced, so the
shipped model runs stock MimiBRICK v2.0.0 `antarctic_icesheet_component.jl` out of
the depot, unmodified. Criterion (1) is therefore satisfied by identity, and the
real question is not "is our module better" but "is our CALIBRATION better" —
what Ladrillo changes is the posterior plus two reparameterisations applied per
draw in `ladrillo_apply_draw!`:
    ais_runoffline_snowheight0 = -ais_runoff_Ton * ais_c   (sampled along T_on)
    ais_temperature_coefficient = 1/amp, intercept = -TANT0/amp   (anchor-preserving)

WHY CRITERION (2) CANNOT DECIDE ANYTHING FOR AIS, AND IS REPORTED ANYWAY. Two
independent reasons, both measured:
  * the comparison is IN-SAMPLE for Ladrillo and OUT-OF-SAMPLE for BRICK 2.0 —
    Ladrillo was calibrated on `recalib_targets_ext.csv`, BRICK 2.0 runs its own
    published posterior (`scope_ladrillo_vs_brick20_scorecard.py` header);
  * the observations have almost no power to separate AIS models at all. The AIS
    calibration target spans 1.404 cm over 1900-2025, and IMBIE's whole-sheet loss
    rate is only 0.95-1.44 sigma from zero across four windows
    (`diag_ais_region_lit_check.py`). A hindcast that cannot reject zero cannot
    rank two models.

THE SPREAD COMPARISON USES THE *JOINT* BAND. FACTS and MAGICC-SLR bands carry
climate-forcing uncertainty; ours did not until 2026-08-25
(`ais_share_was_a_fixed_driver_artifact`). Comparing our fixed-driver band to
theirs would be the `like_for_like_forcing` error again, so the joint band is the
one scored and the fixed one is shown beside it to price the difference.

IRREDUCIBILITY IS SCORED, NOT ASSUMED. Marcus asked for the assessment
"recognizing that there are irreducible uncertainties". Reported: the observed
signal-to-noise above, and the share of our own band that is the `antarctic_lambda`
PRIOR rather than an inference (`ais_spread_is_lambda_prior`: 78% of the ssp585
2300 band is that one parameter, whose posterior sits 0.027 prior sd from its paleo
prior, and which is identified by the LIG alone).

    source ~/climate-env/bin/activate
    python python/scope_ais_module_assessment.py
Writes outputs/scope_ais_module_assessment_L14.csv
"""
import os
import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAG = "L14"
OUT = os.path.join(REPO, "outputs", f"scope_ais_module_assessment_{TAG}.csv")
CMP = os.path.join(REPO, "outputs", f"ladrillo_model_comparison_{TAG}.csv")
SCORECARD = os.path.join(REPO, "outputs", f"scope_ladrillo_vs_brick20_scorecard_{TAG}.csv")
DRAWS = os.path.join(REPO, "outputs", "scope_slr_fairunc_draws_{ssp}_spliced_" + TAG + ".csv")
SSPS = ["ssp126", "ssp245", "ssp585"]
HORIZONS = [2100, 2150]           # the horizons FACTS/MAGICC actually cover
COMPONENT = "ais"
# IMBIE whole-sheet |loss|/sigma across the four windows, diag_ais_region_lit_check.py
IMBIE_SNR = (0.95, 1.44)
AIS_TARGET_SPAN_CM = 1.404
# ais_spread_is_lambda_prior: share of the ssp585 2300 AIS band that is antarctic_lambda
LAMBDA_SHARE_2300 = 0.78

rows = []
def emit(block, **kw):
    rows.append(dict(block=block, **kw))

cmp_ = pd.read_csv(CMP)
cmp_ = cmp_[cmp_.component == COMPONENT]
print("=" * 104)
print(f"STEP 1 — AIS MODULE ASSESSMENT ({TAG}) vs BRICK 2.0 and the literature")
print("=" * 104)

# ---------------------------------------------------------------- criterion 1
print("\n[1] FORMULATION — is it at least as credible as BRICK 2.0's?")
print("    Ladrillo's AIS component IS BRICK 2.0's: the AIS slot is never `replace!`d,")
print("    so the shipped model runs stock MimiBRICK v2.0.0 DAIS from the depot.")
print("    What differs is the POSTERIOR plus two per-draw reparameterisations")
print("    (runoff line sampled along T_on; anchor-preserving T_ant map).")
print("    => criterion (1) holds BY IDENTITY. The open question is the CALIBRATION.")
emit("formulation", key="component_identical_to_brick20", value=1,
     note="AIS slot never replace!d; stock MimiBRICK v2.0.0 antarctic_icesheet_component.jl")

# ---------------------------------------------------------------- criterion 2
print("\n[2] HINDCAST — and why it cannot decide this comparison")
if os.path.exists(SCORECARD):
    sc = pd.read_csv(SCORECARD)
    a = sc[sc.get("component", "").astype(str).str.contains("AIS", case=False, na=False)]
    for _, r in a.iterrows():
        w, arm = r.get("window", "?"), r.get("arm", "?")
        print(f"    {str(w):12s} {str(arm):10s} bias {r.get('mean_bias', np.nan):+7.3f}  "
              f"RMSE {r.get('rmse', np.nan):6.3f} cm")
        emit("hindcast", key=f"{w}_{arm}", value=float(r.get("rmse", np.nan)),
             note=f"bias {r.get('mean_bias', np.nan):+.4f} cm")
print(f"    ⚠ IN-SAMPLE for Ladrillo, OUT-OF-SAMPLE for BRICK 2.0.")
print(f"    ⚠ AND THE DATA CANNOT SEPARATE THEM: IMBIE whole-sheet loss is only")
print(f"      {IMBIE_SNR[0]}-{IMBIE_SNR[1]} sigma from ZERO across four windows, on a target")
print(f"      spanning {AIS_TARGET_SPAN_CM} cm. A hindcast that cannot reject zero cannot rank models.")
print("    => criterion (2) is NOT DECIDABLE for AIS. Report it; do not rank on it.")
emit("hindcast", key="imbie_wholesheet_snr_lo", value=IMBIE_SNR[0], note="|loss|/sigma, 1992-2020")
emit("hindcast", key="imbie_wholesheet_snr_hi", value=IMBIE_SNR[1], note="|loss|/sigma, 2012-2018")
emit("hindcast", key="decidable", value=0, note="observations cannot reject zero AIS loss")

# ---------------------------------------------------------------- criterion 3
def joint_spread(ssp, H):
    p = DRAWS.format(ssp=ssp)
    if not os.path.exists(p):
        return np.nan, np.nan, np.nan
    d = pd.read_csv(p)
    out = {}
    for arm in ("fixed", "joint"):
        v = d[(d.horizon == H) & (d.component == COMPONENT) & (d.arm == arm)].value_cm.values
        out[arm] = (float(np.percentile(v, 95) - np.percentile(v, 5)), float(np.median(v)))
    return out["fixed"][0], out["joint"][0], out["joint"][1]

print("\n[3] PROJECTION — level and spread, against MAGICC-SLR and every FACTS module")
print("    ⚠ scored on our JOINT band (climate uncertainty IN), because theirs carry it.")
for H in HORIZONS:
    for ssp in SSPS:
        sub = cmp_[(cmp_.scenario == ssp) & (cmp_.year == H)]
        if sub.empty:
            continue
        ours = sub[sub.source == "Ladrillo"]
        if ours.empty:
            continue
        omed = float(ours.med.iloc[0])
        fsp, jsp, jmed = joint_spread(ssp, H)
        print(f"\n    --- {ssp} @{H} " + "-" * 66)
        print(f"    {'source':12s} {'module':14s} {'median':>9s} {'p05':>9s} {'p95':>9s} {'spread':>9s}")
        print(f"    {'Ladrillo':12s} {'L14 fixed':14s} {omed:9.2f} "
              f"{float(ours.p05.iloc[0]):9.2f} {float(ours.p95.iloc[0]):9.2f} {fsp:9.2f}")
        print(f"    {'Ladrillo':12s} {'L14 JOINT':14s} {jmed:9.2f} {'':>9s} {'':>9s} {jsp:9.2f}   <= scored")
        lits = []
        for _, r in sub[sub.source != "Ladrillo"].iterrows():
            sp = float(r.p95) - float(r.p05)
            lits.append((r.source, r.module, float(r.med), sp))
            print(f"    {r.source:12s} {r.module:14s} {float(r.med):9.2f} "
                  f"{float(r.p05):9.2f} {float(r.p95):9.2f} {sp:9.2f}")
            emit("projection", key=f"{ssp}_{H}_{r.module}_med", value=round(float(r.med), 3),
                 note=f"{r.source} spread {sp:.2f}")
        if lits:
            meds = [x[2] for x in lits]; sps = [x[3] for x in lits]
            print(f"    -> our JOINT median is {jmed/np.median(meds):.2f}x the literature median "
                  f"({np.min(meds):.1f}-{np.max(meds):.1f}); our spread is "
                  f"{jsp/np.median(sps):.2f}x theirs ({np.min(sps):.1f}-{np.max(sps):.1f})")
            emit("projection", key=f"{ssp}_{H}_ours_joint_med", value=round(jmed, 3),
                 note=f"x lit median {jmed/np.median(meds):.3f}")
            emit("projection", key=f"{ssp}_{H}_ours_joint_spread", value=round(jsp, 3),
                 note=f"x lit median spread {jsp/np.median(sps):.3f}; fixed was {fsp:.2f}")

# ---------------------------------------------------------------- irreducible
print("\n\n[4] IRREDUCIBLE UNCERTAINTY — how much of our band could evidence ever move?")
print(f"    * observations: IMBIE whole-sheet {IMBIE_SNR[0]}-{IMBIE_SNR[1]} sigma from zero;")
print(f"      EAIS indistinguishable from zero (0.02-0.25 sigma); WAIS carries 89-100%.")
print(f"    * our own band at ssp585@2300 is {100*LAMBDA_SHARE_2300:.0f}% ONE parameter,")
print(f"      `antarctic_lambda`, whose posterior sits 0.027 prior sd from its PALEO PRIOR")
print(f"      and which three of Ruckert's four constraints leave EXACTLY inert (LIG only).")
print(f"    => most of the AIS band is a PRIOR, not an inference. No recalibration on")
print(f"       these data narrows it, and a narrower band would be a worse model.")
emit("irreducible", key="lambda_share_of_2300_band", value=LAMBDA_SHARE_2300,
     note="ais_spread_is_lambda_prior; posterior 0.027 prior sd from the paleo prior")

# ---------------------------------------------------------------- separation
# The per-scenario ratios above are LOW at the cool scenarios and HIGH at ssp585 in
# every cell. That is one statement, not six: our SCENARIO SEPARATION is too wide.
# It is scored here directly, per source, because a ratio of two of our own numbers
# is anchor-free in a way the levels are not.
print("\n\n[5] SCENARIO SEPARATION — the pattern the per-scenario ratios are pointing at")
for H in HORIZONS:
    print(f"\n    --- ssp585 / ssp126, AIS median @{H} " + "-" * 46)
    lo = cmp_[(cmp_.scenario == "ssp126") & (cmp_.year == H)]
    hi = cmp_[(cmp_.scenario == "ssp585") & (cmp_.year == H)]
    _, _, jlo = joint_spread("ssp126", H)
    _, _, jhi = joint_spread("ssp585", H)
    print(f"    {'Ladrillo L14 JOINT':24s} {jhi:8.2f} / {jlo:6.2f} = {jhi/jlo:7.2f}x   <= ours")
    emit("separation", key=f"ours_joint_585_over_126_{H}", value=round(jhi/jlo, 3), note="AIS median")
    rs = []
    for m in sorted(set(lo.module) & set(hi.module)):
        a = float(hi[hi.module == m].med.iloc[0]); b = float(lo[lo.module == m].med.iloc[0])
        if b > 0:
            rs.append(a / b)
            src = hi[hi.module == m].source.iloc[0]
            print(f"    {src + ' ' + m:24s} {a:8.2f} / {b:6.2f} = {a/b:7.2f}x")
            emit("separation", key=f"{m}_585_over_126_{H}", value=round(a / b, 3), note=src)
    if rs:
        print(f"    -> literature {min(rs):.2f}x to {max(rs):.2f}x (median {np.median(rs):.2f}x);"
              f" ours is {(jhi/jlo)/np.median(rs):.2f}x the literature median")
        emit("separation", key=f"ours_vs_lit_median_{H}", value=round((jhi/jlo)/np.median(rs), 3),
             note=f"lit range {min(rs):.2f}-{max(rs):.2f}")

print("\n\n" + "=" * 104)
print("VERDICT — STEP 1")
print("=" * 104)
print("  (1) FORMULATION      PASS BY IDENTITY. It is BRICK 2.0's component, unmodified.")
print("  (2) HINDCAST         NOT DECIDABLE. In-sample for us, out-of-sample for BRICK 2.0,")
print("                       and the observations are 0.95-1.44 sigma from zero regardless.")
print("  (3) PROJECTION       MIXED, and the pattern is ONE defect, not six:")
print("                       LOW at the cool scenarios (0.31-0.51x the literature median),")
print("                       HIGH at ssp585 (2.16-2.49x) => OVER-SEPARATED by scenario.")
print("                       Spread is comparable at ssp245/ssp585 (0.40-1.12x) but")
print("                       BADLY NARROW at ssp126 (0.24-0.33x) -- nothing tips there,")
print("                       so the band has no tipping tail at all while every")
print("                       literature module retains one.")
print("  (4) IRREDUCIBLE      Most of the ssp585 band is the antarctic_lambda PRIOR (78%),")
print("                       and the observations cannot reject zero AIS loss. The WIDTH")
print("                       at ssp585 should NOT be narrowed; the ssp126 width is the")
print("                       defect, and it is a MODEL-FORM problem, not a data problem.")
print("\n  => The AIS module is as credible as BRICK 2.0's by construction and better")
print("     calibrated on a hindcast that cannot arbitrate. Against the literature it is")
print("     over-separated across scenarios and under-dispersed at ssp126. Both trace to")
print("     the BINARY fast-dynamics threshold (ais_binary_form_priced): below it the")
print("     term is EXACTLY zero, above it saturated.")

pd.DataFrame(rows).to_csv(OUT, index=False)
print(f"\nwrote {OUT}")
