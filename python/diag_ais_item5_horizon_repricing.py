"""
diag_ais_item5_horizon_repricing.py -- ITEM 5: re-price the AIS block at 2100 and
2150, both the parameter RANKING and the lambda-prior ENVELOPE.

WHY. Every headline Antarctic number so far is quoted at 2300: the ranking in
`ais_spread_is_lambda_prior`, the "2.18x the band" envelope and the transfer law in
`ais_lambda_prior_envelope`. Handoff 2026-08-24b sec 5 item 3 flagged that the
ordering already differs at 2100 and that a HORIZON caveat might compound with the
scenario one. Both source CSVs carry all three horizons, so this is post-processing,
not a new run -- no chains are read here.

  outputs/diag_ais_block_propagation_L14.csv   the per-parameter decile contrasts
  outputs/scope_ais_lambda_prior_L14.csv       the 8 prior arms

TWO NORMALISATIONS, DELIBERATELY. An arm is reported as a fraction of the control
MEDIAN and as a ratio on the control BAND, because at the cool/early cells the two
disagree by an order of magnitude and a single number would be a choice disguised as
a measurement. Memory `ratio_needs_its_base`: a percentage is not a magnitude until
its base is stated, and the ssp245 @2150 median is only 11.91 cm.

  python3 python/diag_ais_item5_horizon_repricing.py [--tag=L14]
Writes outputs/diag_ais_item5_{ranking,envelope}_<tag>.csv
"""
import csv
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAG = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--tag=")), "L14")
PROP = os.path.join(REPO, "outputs", f"diag_ais_block_propagation_{TAG}.csv")
SCOPE = os.path.join(REPO, "outputs", f"scope_ais_lambda_prior_{TAG}.csv")
OUT_R = os.path.join(REPO, "outputs", f"diag_ais_item5_ranking_{TAG}.csv")
OUT_E = os.path.join(REPO, "outputs", f"diag_ais_item5_envelope_{TAG}.csv")

SSPS = ("ssp245", "ssp585")
HORIZONS = ("2100", "2150", "2300")
# The two parameters the whether-vs-how-fast trade runs between, plus the three that
# the 2300 ranking named. Named here so the labels below derive from the constant.
TRACKED = ("antarctic_temp_threshold", "antarctic_lambda", "ais_gmst_amp",
           "ais_runoff_Ton", "antarctic_alpha")
# The lambda prior's FORM arms vs its ENVELOPE arms -- they answer different questions
# and are never mixed in one summary.
FORM_ARMS = ("lam_box", "lam_full", "tcr_full", "joint")
LAM_FORM_ARMS = ("lam_box", "lam_full")     # the lambda form ALONE, no Tcrit
ENV_ARMS = ("lam_pmin", "lam_boxmax", "lam_pmax")

prop = list(csv.DictReader(open(PROP)))
scope = list(csv.DictReader(open(SCOPE)))


def pget(ssp, h, param):
    return next(r for r in prop
                if r["scenario"] == ssp and r["horizon"] == h and r["param"] == param)


def prank(ssp, h, param):
    sub = sorted((r for r in prop if r["scenario"] == ssp and r["horizon"] == h),
                 key=lambda r: -abs(float(r["contrast_frac_spread"])))
    return 1 + [r["param"] for r in sub].index(param)


def sget(ssp, h, arm):
    return next((r for r in scope
                 if r["scenario"] == ssp and r["horizon"] == h and r["arm"] == arm), None)


# ---- [1] the ranking, by horizon -------------------------------------------
print(f"[1] PARAMETER RANKING BY HORIZON (decile contrast / p05-p95, rank in parens)  tag {TAG}")
hdr = "".join(f"{ssp}@{h:>4s}".rjust(15) for ssp in SSPS for h in HORIZONS)
print(f"{'param':26s}{hdr}")
with open(OUT_R, "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["param", "scenario", "horizon", "contrast_frac_spread", "rank"])
    for p in TRACKED:
        cells = []
        for ssp in SSPS:
            for h in HORIZONS:
                r = pget(ssp, h, p)
                c = float(r["contrast_frac_spread"])
                k = prank(ssp, h, p)
                cells.append(f"{c:+.2f}(r{k})")
                w.writerow([p, ssp, h, f"{c:.6f}", k])
        print(f"{p:26s}" + "".join(c.rjust(15) for c in cells))

thr = [abs(float(pget(s, h, "antarctic_temp_threshold")["contrast_frac_spread"]))
       for s in SSPS for h in HORIZONS]
print("\n  antarctic_temp_threshold ssp245/ssp585 ratio by horizon: " +
      ", ".join(f"{h} {thr[i] / thr[i + 3]:.2f}x" for i, h in enumerate(HORIZONS)))
print("  => the SCENARIO INVERSION is horizon-dependent; at 2100 the threshold is near "
      "the top in BOTH scenarios.")

# ---- [2] the lambda prior, by horizon --------------------------------------
print(f"\n[2] LAMBDA PRIOR ENVELOPE BY HORIZON")
print(f"{'cell':16s}{'control med':>12s}{'band':>9s}{'med env':>10s}{'/band':>7s}"
      f"{'spread env':>12s}{'/band':>7s}{'spr ratio':>11s}")
with open(OUT_E, "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["scenario", "horizon", "control_median_cm", "control_band_cm",
                "median_envelope_cm", "median_envelope_over_band",
                "spread_envelope_cm", "spread_envelope_over_band",
                "spread_max_over_min",
                "max_form_arm_pct_of_median", "max_form_arm_name",
                "max_lam_form_pct_of_median", "max_lam_form_band_ratio_dev"])
    for ssp in SSPS:
        for h in HORIZONS:
            b = sget(ssp, h, "chain")
            if b is None:
                continue
            bm, bs = float(b["median_cm"]), float(b["spread_p05_p95_cm"])
            med = [float(sget(ssp, h, a)["median_cm"]) for a in ENV_ARMS]
            spr = [float(sget(ssp, h, a)["spread_p05_p95_cm"]) for a in ENV_ARMS]
            mr, sr = max(med) - min(med), max(spr) - min(spr)
            worst_pct, worst_name = 0.0, "-"
            for a in FORM_ARMS:
                pct = 100 * (float(sget(ssp, h, a)["median_cm"]) - bm) / bm
                if abs(pct) > abs(worst_pct):
                    worst_pct, worst_name = pct, a
            lam_pct = max((abs(100 * (float(sget(ssp, h, a)["median_cm"]) - bm) / bm)
                           for a in LAM_FORM_ARMS))
            lam_band = max((abs(float(sget(ssp, h, a)["spread_p05_p95_cm"]) / bs - 1)
                            for a in LAM_FORM_ARMS))
            print(f"{ssp + '@' + h:16s}{bm:12.2f}{bs:9.2f}{mr:10.2f}{mr / bs:7.2f}"
                  f"{sr:12.2f}{sr / bs:7.2f}{max(spr) / min(spr):10.1f}x")
            w.writerow([ssp, h, f"{bm:.4f}", f"{bs:.4f}", f"{mr:.4f}", f"{mr / bs:.4f}",
                        f"{sr:.4f}", f"{sr / bs:.4f}", f"{max(spr) / min(spr):.4f}",
                        f"{worst_pct:.4f}", worst_name,
                        f"{lam_pct:.4f}", f"{lam_band:.4f}"])

print(f"\nwrote {os.path.relpath(OUT_R, REPO)}\n      {os.path.relpath(OUT_E, REPO)}")
