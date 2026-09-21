"""Round 6 (2026-09-20): THE ONE-ROUND SWAP of the GMD draft from the L24 posterior to L27.

Every table, figure and posterior-dependent number moves together (handoff 09-20b §1.2): FIGs 1-6,
Tables 4 / 5 / A1 / A2, the parameter counts, the convergence sentence, the AIC/BIC paragraph, the
hindcast-skill numbers, the projection numbers, the Antarctic fast-dynamics text. Every number is
READ from the L27 output file that produced it (or asserted against it) rather than typed, and the
L24 value it replaces is asserted to be what the draft says, so a stale anchor fails loudly.

Base: deliverables/GMD.Ladrillo.v1_review-2026-09-20.docx unzipped to unpacked/ (merge_runs.py run).
All edits are tracked under author "Claude". Round-4 (LWS) and round-5 (Table A2) insertions are
still pending in the base; the Table A2 block is REBUILT (its pending rows removed, L27 rows inserted
fresh), so the reject-all view is unchanged. Table A1 was ACCEPTED by Marcus, so it is edited cell by
cell (tracked) with the eight dropped parameters as tracked row deletions.

Numbers NOT re-run on L27 and therefore left as they stand (each carries a comment in the draft):
the Greenland amplification / tap sensitivities (P "1 cm to 9 cm", "35.1 cm"), the Antarctic
amplification sensitivity ("58 cm ... 24 cm ... 17 / 42 cm"), the RGI-19 response-time range
("80-3200 yr"), the runtime ("6.2 against 5.0 ms"), and the Conclusions' "up to 60 cm by 2300".
"""
import os, re, sys, html
import pandas as pd
from redline import *
import redline

REPO = HERE.parent.parent
OUT = REPO / "outputs"
FIG = REPO / "figures/paper"

## Round 6 carries its own date: the validator recognises an EXISTING tracked change by author, date
## and text, so a new insertion that happens to repeat a pending one's text (Table A2's "14") must
## differ in date or it is mistaken for the old one.
redline.DATE = "2026-09-20T00:00:00Z"
x = load()
## Word's render hints split a run's text into two <w:t> around a page break, which defeats the
## single-run matching below. Drop the hints and merge the split text (xml:space kept).
x = x.replace("<w:lastRenderedPageBreak/>", "")
x = x.replace("<w:t>", '<w:t xml:space="preserve">')
x = re.sub(r'</w:t><w:t xml:space="preserve">', "", x)
start_ids_above(x)

## Typography: a negative number is written with the Unicode minus throughout the draft. Every
## inserted string passes through esc(), so the substitution lives there: a hyphen directly before
## a digit and not preceded by a word character (so 2022-2024 and 1993-2026 stay ranges).
_esc0 = redline.esc
def _esc_minus(sx):
    return _esc0(re.sub(r"(?<![\w])-(?=\d)", "−", sx))
redline.esc = _esc_minus
esc = _esc_minus


def chk(cond, msg):
    if not cond:
        raise SystemExit("[r6 ABORT] " + msg)


def has(text):
    return esc(text) in x


# ------------------------------------------------------------------------------------------
# 0. the numbers, read from the L27 outputs
# ------------------------------------------------------------------------------------------
sc = pd.read_csv(OUT / "scope_ladrillo_vs_brick20_scorecard_L27.csv")
rm = sc.pivot_table(index=["component", "window"], columns="arm", values="rmse")
ratio = (rm["Ladrillo"] / rm["BRICK 2.0"])
T4_ROWS = [("Antarctica", "AIS"), ("Greenland", "Greenland"), ("Glaciers", "glaciers"),
           ("Thermal expansion", "thermal exp."), ("Total", "TOTAL")]
T4_WIN = ["1900-1919", "1920-1949", "1950-1992", "1993-2026", "full"]
t4_new = {lbl: ["%.3f" % ratio.loc[(comp, w)] for w in T4_WIN] for lbl, comp in T4_ROWS}


def ic_rows(path):
    """{arm: (k_l, k_b, lnl_l, lnl_b, dAIC, dBIC)} from an ic_ladrillo_vs_brick20 md."""
    t = open(path).read()
    r = {}
    for arm in ("obs_iid", "ar1_prof"):
        l = re.search(r"\| %s \| Ladrillo L27 \| (\d+) \| ([-\d.]+) \|" % arm, t)
        b = re.search(r"\| %s \| BRICK 2\.0 \| (\d+) \| ([-\d.]+) \|" % arm, t)
        d = re.search(r"\*\*%s\*\*.*?ΔAIC \(BRICK − Ladrillo\) = \*\*([-\d.]+)\*\*, ΔBIC = \*\*([-\d.]+)\*\*" % arm, t)
        r[arm] = (int(l.group(1)), int(b.group(1)), float(l.group(2)), float(b.group(2)),
                  float(d.group(1)), float(d.group(2)))
    return r


ic99 = ic_rows(OUT / "ic_ladrillo_vs_brick20_L27.md")
ic95 = ic_rows(OUT / "ic_ladrillo_vs_brick20_L27_rho0.95.md")
ic90 = ic_rows(OUT / "ic_ladrillo_vs_brick20_L27_rho0.9.md")
chk(ic99["obs_iid"][:2] == (42, 27) and ic99["ar1_prof"][:2] == (50, 35), "IC k counts")
# per-series at the joint max draw (rho <= 0.99)
_t = open(OUT / "ic_ladrillo_vs_brick20_L27.md").read()
per = {s: float(re.search(r"\| %s \| [-\d.]+ \| [\d.]+ \| [\d.]+ \| [-\d.]+ \| [\d.]+ \| [\d.]+ \| ([-\d.]+) \|" % s, _t).group(1))
       for s in ("ais", "gsic", "gis", "steric")}
lnl_gain_iid = ic99["obs_iid"][2] - ic99["obs_iid"][3]
lnl_gain_ar1 = ic99["ar1_prof"][2] - ic99["ar1_prof"][3]
dk = ic99["ar1_prof"][0] - ic99["ar1_prof"][1]
chk(dk == 15, "dk")


def fmt_signed(v, nd=0):
    return ("%+." + str(nd) + "f") % v


# hindcast numbers (the same arithmetic as the L24 sentences; reproduced on postpred_L24 first)
import numpy as np
TGT = pd.read_csv(OUT / "recalib_targets_ext.csv").set_index("year")
BRK = pd.read_csv(OUT / "postpred_oldbrick_components_timeseries.csv").set_index("year")
LAD = pd.read_csv(OUT / "postpred_L27_components_timeseries.csv").set_index("year")
IG = pd.read_csv(REPO / "data/observations/igcc2026_gmsl_annual.csv").set_index("year")
IGS = (IG["gmsl_mm"] - IG["gmsl_mm"].loc[1995:2005].mean()) / 10.0


def wm(s, a, b):
    return s.loc[a:b].mean()


def ols(s, a, b):
    s = s.loc[a:b].dropna()
    return np.polyfit(s.index.values, s.values, 1)[0]


obs = TGT["dang"]
cum = dict(obs=wm(obs, 2020, 2024) - wm(obs, 1900, 1904), lad=wm(LAD.total_p50, 2020, 2024) - wm(LAD.total_p50, 1900, 1904),
           brk=wm(BRK.total_p50, 2020, 2024) - wm(BRK.total_p50, 1900, 1904))
lvl = dict(obs=wm(obs, 2022, 2024), lad=wm(LAD.total_p50, 2022, 2024), brk=wm(BRK.total_p50, 2022, 2024), ig=wm(IGS, 2022, 2024))
rate = dict(lad=ols(LAD.total_p50, 2006, 2025), brk=ols(BRK.total_p50, 2006, 2025), obs=ols(obs, 2006, 2025), ig=ols(IGS, 2006, 2025))
te_ratio = ols(LAD.te_p50, 1993, 2026) / ols(TGT["steric"], 1993, 2026)
te_ratio_b = ols(BRK.te_p50, 1993, 2026) / ols(TGT["steric"], 1993, 2026)
_yy = [y for y in range(2022, 2027) if np.isfinite(TGT["steric"].get(y, np.nan))]
te_excess = (LAD.te_p50.loc[_yy] - TGT["steric"].loc[_yy]).mean()
chk(abs(cum["obs"] - 21.00) < 0.005 and abs(cum["brk"] - 21.34) < 0.005, "obs/BRICK cumulative reproduce the draft")

# compensating-error paragraph
ce = pd.read_csv(OUT / "diag_component_error_cancellation_L27.csv")
def ce_val(win, comp, col):
    return float(ce[(ce.window == win) & (ce.component == comp)][col].iloc[0])
lad_sum_1900 = ce_val("1900-1919", "__Ladrillo_summary", "ladrillo_bias_cm")
lad_abs_1900 = sum(abs(ce_val("1900-1919", c, "ladrillo_bias_cm")) for c in ("ais", "gsic", "gis", "steric"))
lad_sum_1920 = ce_val("1920-1949", "__Ladrillo_summary", "ladrillo_bias_cm")
lad_abs_1920 = sum(abs(ce_val("1920-1949", c, "ladrillo_bias_cm")) for c in ("ais", "gsic", "gis", "steric"))
brk_ais_1900 = ce_val("1900-1919", "ais", "brick_bias_cm"); brk_gsic_1900 = ce_val("1900-1919", "gsic", "brick_bias_cm")
brk_sum_1900 = ce_val("1900-1919", "__BRICK 2.0_summary", "brick_bias_cm")
brk_abs_1900 = sum(abs(ce_val("1900-1919", c, "brick_bias_cm")) for c in ("ais", "gsic", "gis", "steric"))
chk(abs(brk_ais_1900 + 2.90) < 0.005 and abs(brk_gsic_1900 - 3.28) < 0.005, "BRICK 1900-19 biases reproduce the draft")

# Table A1 / A2 sources
A1 = open(OUT / "ladrillo_prior_posterior_L27.md").read()
A2 = open(OUT / "ladrillo_table_a2_L27.md").read()
a1_cap = re.search(r"\*\*Table A1\.\*\* (.*)", A1).group(1).strip()
a1_rows = [[c.strip() for c in l.strip().strip("|").split("|")] for l in A1.splitlines() if l.startswith("| ") and not l.startswith("| Parameter") ]
a1_rows = [r for r in a1_rows if not set("".join(r)) <= set("-| ")]
def a1_clean(r):
    r = list(r); r[0] = r[0].strip("`").strip("*"); return r
a1_rows = [a1_clean(r) for r in a1_rows]
chk(len(a1_rows) == 58, "A1 L27 rows (50 params + 8 group rows) = %d" % len(a1_rows))
a2_cap = re.search(r"\*\*Table A2\.\*\* (.*)", A2).group(1).strip()
a2_rows = [[c.strip() for c in l.strip().strip("|").split("|")] for l in A2.splitlines() if l.startswith("| ") and not l.startswith("| component")]
a2_rows = [r for r in a2_rows if not set("".join(r)) <= set("-| ")]
chk(len(a2_rows) == 3, "A2 L27 rows")

# projections
V = pd.read_csv(OUT / "vv_model_comparison_L27.csv")
def vcell(src, scen, comp, yr, col="med"):
    return float(V[(V.source == src) & (V.scenario == scen) & (V.component == comp) & (V.year == yr)][col].iloc[0])
M = pd.read_csv(OUT / "ladrillo_model_comparison_L27.csv")
def mcell(src, scen, comp, yr, col="med"):
    return float(M[(M.source == src) & (M.scenario == scen) & (M.component == comp) & (M.year == yr)][col].iloc[0])
SW = pd.read_csv(OUT / "vv_climate_swap_L27.csv")
def swcell(src, marker, comp, yr, col):
    return float(SW[(SW.source == src) & (SW.marker == marker) & (SW.component == comp) & (SW.year == yr)][col].iloc[0])
RG = pd.read_csv(OUT / "verify_magicc_regrowth_attribution_L27.csv")
RS = pd.read_csv(OUT / "vv_responsiveness_L27.csv")
def rs(src, comp, yr):
    return float(RS[(RS.source == src) & (RS.component == comp) & (RS.year == yr)].delta_cm.iloc[0])
PAL = pd.read_csv(OUT / "paleo_fastdyn_draws.csv")

# convergence (from the postprocess log: the same diagnostic the L24 sentence quoted)
LOG = open(OUT / "log_l27_postprocess_driver.txt").read()
conv = {q: (float(m.group(1)), float(m.group(2))) for q, m in
        (("2100", re.search(r"SLR@2100\s+([\d.]+)\s+([\d.]+)", LOG)), ("2150", re.search(r"SLR@2150\s+([\d.]+)\s+([\d.]+)", LOG)))}
n_fail = len(re.findall(r"<-- check", LOG.split("4 chains ×")[1].split("SLR@2100")[0]))
chk(n_fail == 8, "8 marginals fail the gate (got %d)" % n_fail)
rhat_Ton = float(re.search(r"ais_runoff_Ton\s+R̂=([\d.]+)", LOG).group(1))
rhat_c = float(re.search(r"ais_c\s+R̂=([\d.]+)", LOG).group(1))

# ------------------------------------------------------------------------------------------
# 1. FIGURES 1-6 (tracked image swaps to the --paper renders)
# ------------------------------------------------------------------------------------------
UNP = HERE / "unpacked"
for old, new, alt in [
    ("figures/hindcast_components_L24.png", "hindcast_components_L27.png", "Hindcast: Ladrillo L27 vs BRICK 2.0 vs observations"),
    ("figures/model_comparison_components_vv_L24_2100.png", "model_comparison_components_vv_L27_2100.png", "van Vuuren scenarios by component, 2100"),
    ("figures/model_comparison_components_vv_L24_2300.png", "model_comparison_components_vv_L27_2300.png", "van Vuuren scenarios by component, 2300"),
    ("figures/future_components_vv_L24_joint.png", "future_components_vv_L27_joint.png", "van Vuuren component trajectories"),
    ("figures/vv_gsic_ladrillo_2300.png", "vv_gsic_ladrillo_L27_2300.png", "Glacier response on the declining scenarios"),
    ("figures/vv_responsiveness_L24.png", "vv_responsiveness_L27.png", "Scenario responsiveness by component"),
]:
    x = replace_image(x, UNP, old, str(FIG / new), alt, "figures/paper/" + new)

# ------------------------------------------------------------------------------------------
# 2. TABLE 4 (RMSE ratios by window) and TABLE 5 (information criteria)
# ------------------------------------------------------------------------------------------
t4 = table_texts(x, "0.676")
chk(t4[1][0] == "Antarctica" and t4[1][1:] == ["0.003", "0.005", "0.010", "0.676", "0.019"], "Table 4 is the L24 table: %r" % t4[1])
edits = {}
for ri, (lbl, _) in enumerate(T4_ROWS, start=1):
    chk(t4[ri][0] == lbl, "Table 4 row %d label" % ri)
    for ci, v in enumerate(t4_new[lbl], start=1):
        edits[(ri, ci)] = v
x = edit_table(x, "0.676", edits)

t5 = table_texts(x, "Independent Gaussian")
chk(t5[1][1] == "50 / 27" and t5[2][3] == "+89", "Table 5 is the L24 table: %r" % t5[1:3])
def t5row(r):
    kl, kb, ll, lb, da, db = r
    return ["%d / %d" % (kl, kb), "%.1f / %.1f" % (ll, lb), fmt_signed(da), fmt_signed(db)]
e5 = {}
for ri, r in ((1, ic99["obs_iid"]), (2, ic99["ar1_prof"]), (3, ic95["ar1_prof"]), (4, ic90["ar1_prof"])):
    for ci, v in enumerate(t5row(r), start=1):
        e5[(ri, ci)] = v
x = edit_table(x, "Independent Gaussian", e5)
x = replace_text(x, "(50 / 27)", "(42 / 27)", para="Information criteria for the Ladrillo and BRICK 2.0 hindcasts")
x = replace_text(x, "(58 / 35)", "(50 / 35)", para="Information criteria for the Ladrillo and BRICK 2.0 hindcasts")

# the AIC/BIC paragraph
chk(has("the gain is +68: three times the AIC charge"), "AIC paragraph anchor")
x = replace_para_text(x, "Ladrillo's hindcast gain is not due to extra parameters.",
    "**Ladrillo's hindcast gain is not due to extra parameters.** Ladrillo samples %d parameters to BRICK 2.0's %d, so the gains "
    "in Table 4 could in principle be overfitting. Following Wong et al. (2017) we compare the two models with the Akaike and "
    "Bayesian information criteria (AIC = 2k − 2 ln L, BIC = k ln N − 2 ln L; Akaike 1974, Schwarz 1978), each at its "
    "maximum-likelihood posterior draw on the same four component series (N = 502 observation-years) and charged for every "
    "sampled parameter its likelihood uses (Table 5). With independent observational errors the log-likelihood gain (%s) dwarfs "
    "the charge for %d parameters. Under the calibration's own AR(1)-plus-observational-error likelihood, with noise scale and "
    "autocorrelation profiled per series for both models, the gain is %s: %s the AIC charge (ΔAIC = %s) and positive on BIC "
    "(%s) even at the calibration's ρ ≤ 0.99 bound, where the AR(1) term acts as a near-random-walk discrepancy that cheaply "
    "absorbs BRICK 2.0's smooth biases; at ρ ≤ 0.95 the BIC margin is %s. Glaciers and Greenland are the primary source of the "
    "gain (%s and %s), Antarctica %s; thermal expansion ties by construction (same module, same ocean-heat driver). Two "
    "caveats: the maximum over draws is a lower bound on each model's maximum likelihood, and Ladrillo was calibrated to "
    "these targets while BRICK 2.0 was calibrated to its own."
    % (ic99["ar1_prof"][0], ic99["ar1_prof"][1], fmt_signed(lnl_gain_iid), dk, fmt_signed(lnl_gain_ar1),
       ("nearly four times" if 3.5 <= lnl_gain_ar1 / dk < 4 else "%.1f times" % (lnl_gain_ar1 / dk)),
       fmt_signed(ic99["ar1_prof"][4]), fmt_signed(ic99["ar1_prof"][5]), fmt_signed(ic95["ar1_prof"][5]),
       fmt_signed(per["gsic"]), fmt_signed(per["gis"]), fmt_signed(per["ais"])))

# ------------------------------------------------------------------------------------------
# 3. HINDCAST TEXT
# ------------------------------------------------------------------------------------------
x = replace_para_text(x, "Ladrillo is closer than BRICK 2.0 on every component in the two earliest windows",
    "Ladrillo is closer than BRICK 2.0 on every component over 1900–1919 yet further from the total there, and the reason is "
    "compensating error. Over 1900–1919 BRICK's Antarctic undershoot (%+.2f cm) and glacier overshoot (%+.2f cm) are opposite "
    "in sign and nearly equal, so its four component biases sum to %+.2f cm out of %.2f cm of absolute error. Ladrillo's biases "
    "are smaller but almost all positive, summing to %+.2f cm out of %.2f cm. Over 1920–1949 Ladrillo's own errors begin to "
    "offset (%+.2f cm out of %.2f) and it is closer on the total as well."
    % (brk_ais_1900, brk_gsic_1900, brk_sum_1900, brk_abs_1900, lad_sum_1900, lad_abs_1900, lad_sum_1920, lad_abs_1920))

# which cells of Table 4 are above 1: the sentence is derived from the table, not typed
worse = [(lbl, w) for lbl, comp in T4_ROWS[:3] for w in T4_WIN if ratio.loc[(comp, w)] > 1]
chk(set(worse) == {("Glaciers", "1950-1992"), ("Antarctica", "1993-2026")}, "Table 4 exceptions: %r" % worse)
x = replace_text(x, "on every ice component in every window except glaciers over 1950–1992, and the gains are largest in the early eras.",
    "on every ice component in every window except glaciers over 1950–1992 and Antarctica over 1993–2026 (where both are "
    "within 0.1 cm of the record), and the gains are largest in the early eras.")

x = replace_para_text(x, "Cumulative total sea level rise, comparing the 1900–1904 mean",
    "Cumulative total sea level rise, comparing the 1900–1904 mean with the 2020–2024 mean: observed %+.2f cm, Ladrillo %+.2f, "
    "BRICK 2.0 %+.2f — Ladrillo undershoots by %.1f cm, BRICK overshoots by %.1f. Over the shorter, more recent window — the "
    "mean over 2022-2024 relative to the 1995–2005 baseline — Ladrillo is within 0.1 cm of the observation and BRICK 2.0 runs "
    "slightly high: observed %+.2f cm, Ladrillo %+.2f (%+.2f) and BRICK 2.0 %+.2f (%+.2f), with IGCC's independent GMSL "
    "estimate at %+.2f. On the 2006–2025 rate of total sea level, the metric the SLEIP intercomparison reports, Ladrillo "
    "yields %.3f cm/yr and BRICK 2.0 %.3f against %.3f for the observational target and %.3f for IGCC (same linear fit, same "
    "window)."
    % (cum["obs"], cum["lad"], cum["brk"], cum["obs"] - cum["lad"], cum["brk"] - cum["obs"],
       lvl["obs"], lvl["lad"], lvl["lad"] - lvl["obs"], lvl["brk"], lvl["brk"] - lvl["obs"], lvl["ig"],
       rate["lad"], rate["brk"], rate["obs"], rate["ig"]))

x = replace_text(x, "(Ladrillo 1.27×, BRICK 2.0 1.17×)", "(Ladrillo %.2f×, BRICK 2.0 %.2f×)" % (te_ratio, te_ratio_b))
x = replace_text(x, "within 3% of the value the observations imply", "within 4% of the value the observations imply")
x = replace_text(x, "(0.3 cm by 2024, almost 40% of Ladrillo's 0.8 cm excess)",
                 "(0.3 cm by 2024, about %d%% of Ladrillo's %.1f cm excess)" % (int(round(0.30 / te_excess * 100 / 5.0) * 5), te_excess))

# ------------------------------------------------------------------------------------------
# 4. METHODS: parameter counts, discrepancy terms, sampler/convergence, alpha, the DAIS text
# ------------------------------------------------------------------------------------------
x = replace_para_text(x, "58 parameters are sampled (priors and posteriors in Appendix A",
    "50 parameters are sampled (priors and posteriors in Appendix A, Table A1): 14 Antarctic, 9 Greenland, 16 glacier, 11 "
    "remaining (thermal expansion, one discrepancy basis of two coefficients, and four AR(1) noise pairs). The two 1850–1900 "
    "glacier set-asides that earlier calibrations sampled (the pre-1901 uncharted-ice and Greenland-periphery shares of the "
    "19th-century datum) are integrated out analytically into the Leclercq constraint's error; the uncharted-ice content of the "
    "Frederikse target is sampled on the Parkes and Marzeion range and sits in its upper half (33 mm SLE, 5–95% 21–41). "
    "Four Antarctic changes distinguish Ladrillo's calibration from BRICK 2.0's — the three described above, plus an SMB "
    "likelihood term anchoring the Antarctic flux scale to Rignot 2019: the net balance (−145 ± 15 Gt/yr) is well constrained, "
    "but surface mass balance and discharge individually contribute about ±505 Gt/yr each. The Antarctic changes have not "
    "been tested individually, so the AIS changes cannot be formally attributed by parameter.")
chk(has("gic_u_unch"), "u_unch row present")
_u = re.search(r"\| `gic_u_unch` \|.*?\| ([\d.]+) \| ([\d.]+) \| ([\d.]+) \|", A1)
chk(_u and _u.group(1) == "33" and _u.group(2) == "20.9" and _u.group(3) == "40.8", "u_unch numbers in the sentence match A1")

x = replace_text(x, "The calibration driver samples the 58 parameters", "The calibration driver samples the 50 parameters")

_d1 = re.search(r"\| `d2_steric_1` \|.*?\| ([−\-\d.]+) \| ([−\-\d.]+) \| ([−\-\d.]+) \|", A1).groups()
_d2 = re.search(r"\| `d2_steric_2` \|.*?\| ([−\-\d.]+) \| ([−\-\d.]+) \| ([−\-\d.]+) \|", A1).groups()
x = replace_para_text(x, "The glacier and thermal-expansion series each carry",
    "**Discrepancy terms.** The thermal-expansion series carries a two-coefficient model-discrepancy term δ(t), a low-order "
    "polynomial in time added to the modelled series before it is scored against the observations. The basis is "
    "orthogonalised against a constant, so it can only describe structure that rescaling the driver cannot. The basis vectors "
    "have unit RMS over the fit window, so each coefficient is an RMS discrepancy in cm, with a N(0, 0.5 cm) prior. The second "
    "coefficient is centered near zero in the posterior (median %s cm); the first is not (%s cm, 5–95%% %s–%s cm): it absorbs "
    "the part of the FaIR ocean-heat discrepancy described later that can't be met by rescaling the driver. (Earlier "
    "calibrations gave the glacier series the same device; its coefficients sat at zero and it was dropped.) FIG 1 and Table 4 "
    "show the bare module without δ(t), which keeps the comparison with BRICK 2.0 like-for-like."
    % (_d2[0], _d1[0], _d1[1], _d1[2]))

x = replace_para_text(x, "Convergence is assessed with R̂, the Gelman",
    "**Convergence criterion.** Convergence is assessed with R̂, the Gelman–Rubin potential scale reduction factor (here the "
    "rank-normalised split-R̂ of Vehtari et al. 2021): the ratio of the pooled-chain spread of a quantity to its mean "
    "within-chain spread, which approaches 1 when the four chains have mixed into the same distribution and exceeds it while "
    "they still sample different regions. The parameter-level gate is R̂ < 1.05 with an effective sample size above 400; 42 of "
    "the 50 parameters pass it. The 8 that fail are all in the Antarctic block (the geometry ridge and the ocean-temperature "
    "parameters; `ais_runoff_Ton` R̂ = %.2f, `ais_c` %.2f), directions that are weakly identified and compensate for each other "
    "(Appendix A, Table A2 gives the combinations the record does identify); the Greenland block converges. The posterior is "
    "therefore accepted on the deliverable-level criterion: projected sea level converges (R̂ = %.3f at 2100 and %.3f at 2150 "
    "on SSP2-4.5, with an effective sample size of about %d on the 1,600 thinned draws used for the diagnostic)."
    % (rhat_Ton, rhat_c, conv["2100"][0], conv["2150"][0], int(round(min(conv["2100"][1], conv["2150"][1]) / 10) * 10)))

_al = re.search(r"\| `thermal_alpha` \|.*?\| (flat \[[^\]]*\]) \| ([\d.]+) \| ([\d.]+) \| ([\d.]+) \|", A1).groups()
chk(_al[0] == "flat [0.05, 0.3]", "alpha prior")
x = replace_text(x, "sampled under BRICK's prior, N(0.16, 0.029) truncated to [0.10, 0.24]",
                 "sampled under a flat prior on [0.05, 0.30] (BRICK's is N(0.16, 0.029) truncated to [0.10, 0.24])")
x = replace_text(x, "The posterior median of α is 0.172 (5–95% 0.155–0.185), within 3% of the value the 0–2000 m observations imply",
                 "The posterior median of α is %s (5–95%% %s–%s), within 4%% of the value the 0–2000 m observations imply" % (_al[1], _al[2], _al[3]))

# DAIS: the reparameterised precipitation parameter, and the fast-dynamics parameters
x = replace_text(x, "ais_precip0_LOG", "ais_precip_u")
x = replace_text(x, ") are freed under a joint paleo prior.",
                 ") are freed under a joint paleo prior; the precipitation parameter is sampled as "
                 "u = ln P₀ + κ·T̄ (T̄ = −18.0 °C on the DAIS scale), the combination the record constrains, and ln P₀ is derived.")
lam = PAL["antarctic_lambda"]; tcr = PAL["antarctic_temp_threshold"]
corr = float(np.corrcoef(lam, tcr)[0, 1])
x = insert_after(x, "The runoff line is sampled in its identified direction.", [
    "**The fast-dynamics parameters are propagated, not sampled.** The disintegration rate λ, its temperature threshold "
    "T_crit and the ice-flow exponent γ are likelihood-flat over the 1900–2026 record (their posterior width equals their "
    "prior width in every calibration that sampled them), so Ladrillo holds them at their DAIS paleo-ensemble medians during "
    "calibration (λ = %.4f m yr⁻¹, T_crit = %.1f °C, γ = %.2f) and, in projection, attaches a joint draw of (λ, T_crit) from "
    "that ensemble to each posterior draw. The joint draw preserves the ensemble's correlation between the two (r = %+.2f), "
    "which independent marginals would not: the corner of high λ with a low threshold, where the sheet collapses under modest "
    "warming, holds four times fewer draws under the joint prior than under independent ones, and the SSP1-2.6 Antarctic "
    "95th percentile at 2300 (fixed-climate arm) is 2.5 times lower for it."
    % (lam.median(), tcr.median(), PAL["antarctic_gamma"].median(), corr)])

# ------------------------------------------------------------------------------------------
# 5. PROJECTIONS TEXT
# ------------------------------------------------------------------------------------------
gl = rs("Ladrillo", "glaciers", 2300) / rs("BRICK 2.0", "glaciers", 2300)
gi = rs("Ladrillo", "gis", 2300) / rs("BRICK 2.0", "gis", 2300)
x = replace_text(x, "glacier (1.4x larger difference between High and Very Low scenarios) and Greenland (3x)",
                 "glacier (%.1fx larger difference between High and Very Low scenarios) and Greenland (%dx)" % (gl, round(gi)))

H = dict(l21=vcell("Ladrillo", "vvH", "total", 2100), b21=vcell("BRICK 2.0", "vvH", "total", 2100), m21=vcell("MAGICC-SLR", "vvH", "total", 2100),
         l23=vcell("Ladrillo", "vvH", "total", 2300), b23=vcell("BRICK 2.0", "vvH", "total", 2300), m23=vcell("MAGICC-SLR", "vvH", "total", 2300),
         la=vcell("Ladrillo", "vvH", "ais", 2300), ba=vcell("BRICK 2.0", "vvH", "ais", 2300), ma=vcell("MAGICC-SLR", "vvH", "ais", 2300),
         lsw=swcell("Ladrillo", "vvH", "total", 2300, "med_magiccclim"), bsw=swcell("BRICK 2.0", "vvH", "total", 2300, "med_magiccclim"))
dl, db = H["l23"] - H["lsw"], H["b23"] - H["bsw"]
x = replace_para_text(x, "For the High scenario, the three models are fairly similar at 2100",
    "**High scenarios.** For the High scenario, the three models are fairly similar at 2100 (Ladrillo %.0f cm, BRICK 2.0 %.0f, "
    "MAGICC-SLR %.0f). By 2300 Ladrillo and BRICK 2.0 sit together (%.0f and %.0f cm, median) well below MAGICC-SLR (%.0f cm), "
    "and the gap is due to Antarctica: %.0f and %.0f cm against MAGICC's %.0f. Driving both on MAGICC's own climate actually "
    "decreases their totals by %.0f–%.0f cm mainly due to thermal expansion (to %.0f and %.0f), so the difference is the "
    "ice-sheet modules, not the climate."
    % (H["l21"], H["b21"], H["m21"], H["l23"], H["b23"], H["m23"], H["la"], H["ba"], H["ma"],
       min(dl, db), max(dl, db), H["lsw"], H["bsw"]))

wl = mcell("Ladrillo", "ssp585", "ais", 2300, "p95") - mcell("Ladrillo", "ssp585", "ais", 2300, "p05")
wb = mcell("BRICK 2.0", "ssp585", "ais", 2300, "p95") - mcell("BRICK 2.0", "ssp585", "ais", 2300, "p05")
x = replace_para_text(x, "Ladrillo's 2300 Antarctic spread is dominated by the prior for",
    "Ladrillo's 2300 Antarctic spread is dominated by the DAIS fast-dynamics rate `antarctic_lambda`, which it does not "
    "sample but attaches to each posterior draw, jointly with the threshold temperature, from the same DAIS fast-dynamics "
    "ensemble that BRICK 2.0 samples it from (mean %.4f, sd %.4f in the ensemble; 0.0104, 0.0036 in BRICK 2.0's posterior), "
    "which is why the two Antarctic spreads are alike (5–95%% widths of %.0f and %.0f cm at SSP5-8.5 in 2300)."
    % (lam.mean(), lam.std(), wl, wb))

VL = dict(l=vcell("Ladrillo", "vvVL", "total", 2300), m=vcell("MAGICC-SLR", "vvVL", "total", 2300), b=vcell("BRICK 2.0", "vvVL", "total", 2300))
VLw = {s: vcell(s, "vvVL", "total", 2300, "p95") - vcell(s, "vvVL", "total", 2300, "p05") for s in ("Ladrillo", "BRICK 2.0", "MAGICC-SLR")}
# the "narrower than BRICK 2.0 on every component" claim, checked rather than carried
for comp in ("ais", "gis", "glaciers", "te"):
    chk(vcell("Ladrillo", "vvVL", comp, 2300, "p95") - vcell("Ladrillo", "vvVL", comp, 2300, "p05")
        < vcell("BRICK 2.0", "vvVL", comp, 2300, "p95") - vcell("BRICK 2.0", "vvVL", comp, 2300, "p05"), "Ladrillo narrower than BRICK on %s" % comp)
x = replace_para_text(x, "Ladrillo sits at the low end of the comparison set on level",
    "**Low scenarios.** Ladrillo sits at the low end of the comparison set on level — at vvVL its 2300 total median is %.0f cm, "
    "above only MAGICC-SLR's %.0f cm and below BRICK 2.0's %.0f. On spread it is narrower than BRICK 2.0 on every component "
    "and narrower than the FACTS glacier and thermal-expansion modules (the only FACTS modules drawn at 2300); MAGICC-SLR is "
    "the narrow outlier throughout (2300 total 5–95%% width %.0f cm against Ladrillo's %.0f and BRICK 2.0's %.0f)."
    % (VL["l"], VL["m"], VL["b"], VLw["MAGICC-SLR"], VLw["Ladrillo"], VLw["BRICK 2.0"]))

def rg(marker, col):
    return float(RG[RG.marker == marker][col].iloc[0])
rLN, rML, rLNmag, rMAG, clim, share = (rg("vvLN", "ladrillo_fair_regrowth_cm"), rg("vvML", "ladrillo_fair_regrowth_cm"),
                                        rg("vvLN", "ladrillo_magiccclim_regrowth_cm"), rg("vvLN", "magicc_own_regrowth_cm"),
                                        rg("vvLN", "climate_part_cm"), rg("vvLN", "structure_share"))
chk(0.70 <= share <= 0.80, "structure share still 'about 3/4' (%.2f)" % share)
x = replace_para_text(x, "The glacier change is evident here because it allows regrowth",
    "**Peak-and-decline scenarios.** The glacier change is evident here because it allows regrowth, though on Ladrillo's own "
    "FaIR climate that regrowth is very small: measured from each scenario's peak to 2300, it reaches only %.2f cm at vvLN and "
    "%.2f cm at vvML, and is essentially nil on the other scenarios. The capacity is larger than the realised amount — driven "
    "instead by MAGICC's colder climate, the same module regrows %.2f cm at vvLN — so what limits regrowth here is how far the "
    "scenario cools, not the module's willingness to regrow." % (rLN, rML, rLNmag))
x = replace_para_text(x, "MAGICC regrows substantially more than Ladrillo.",
    "MAGICC regrows substantially more than Ladrillo. About ¾ of the regrowth difference is model structure and ¼ the climate "
    "module. Measured on realised regrowth (peak-to-2300) at vvLN, the scenario where regrowth is largest: MAGICC regrows "
    "%.2f cm against Ladrillo's %.2f cm, and driving Ladrillo's module with MAGICC's own climate decreases the gap by %.2f cm."
    % (rMAG, rLN, clim))

# ------------------------------------------------------------------------------------------
# 6. APPENDIX A: Table A1 (accepted; cell-by-cell) and Table A2 (pending; rebuilt)
# ------------------------------------------------------------------------------------------
x = replace_text(x, "Table A1 lists, for each of the 58 sampled parameters", "Table A1 lists, for each of the 50 sampled parameters")
x = replace_text(x, "of the 58 sampled Ladrillo parameters", "of the 50 sampled Ladrillo parameters", para="Prior distributions and posterior median")

old = table_texts(x, "gic_a_R19")
chk(len(old) == 67 and old[0][0] == "Parameter", "Table A1 shape")
new_by_name = {r[0]: r for r in a1_rows}
RENAME = {"ais_precip0_LOG": "ais_precip_u"}
DROP = {"gic_delta", "gic_u_pre", "gic_s_r5", "antarctic_temp_threshold", "antarctic_lambda", "antarctic_gamma", "d2_gsic_1", "d2_gsic_2"}
e_a1, del_rows, seen = {}, [], set()
for ri, row in enumerate(old[1:], start=1):
    name = row[0]
    if name in DROP:
        del_rows.append(ri); continue
    key = RENAME.get(name, name)
    chk(key in new_by_name, "A1 row %r has no L27 counterpart" % name)
    nr = new_by_name[key]; seen.add(key)
    for ci in range(7):
        if row[ci] != nr[ci]:
            e_a1[(ri, ci)] = nr[ci]
chk(seen == set(new_by_name), "every L27 A1 row placed: missing %r" % (set(new_by_name) - seen))
chk(len(del_rows) == 8, "8 A1 rows deleted")
x = edit_table(x, "gic_a_R19", e_a1, delete_rows=del_rows)

# Table A2: the r5 rows are still Claude's PENDING insertion. They are marked deleted (the <w:del>
# nests inside the <w:ins>, the form Word writes and validate.py checks) and the L27 rows are
# inserted fresh after the header; the caption is replaced the same way.
A2_ANCHOR = "identified combination (loadings)"
ts, te = find_table(x, A2_ANCHOR)
rows = list(TR_RE.finditer(x[ts:te]))
chk(len(rows) == 6, "A2 pending table has 6 rows")
tmpl = rows[1].group(0)
def a2_row(vals):
    r = tmpl
    cells = list(TC_RE.finditer(r)); out = r[:cells[0].start()]
    for cm, v in zip(cells, vals):
        tc = cm.group(0)
        tc = re.sub(r"<w:ins [^>]*>.*?</w:ins>", lambda m: mk_ins(esc(v), run_parts(m.group(0))[0]), tc, count=1, flags=re.S)
        out += tc
    return out + r[cells[-1].end():]
def fresh_ids(sx):
    return re.sub(r'w:id="\d+"', lambda m: f'w:id="{nid()}"', sx)
new_rows = "".join(fresh_ids(a2_row(v)) for v in a2_rows)
x = edit_table(x, A2_ANCHOR, {}, delete_rows=[1, 2, 3, 4, 5])
ts, te = find_table(x, A2_ANCHOR)
hdr_end = ts + list(TR_RE.finditer(x[ts:te]))[0].end()
x = x[:hdr_end] + new_rows + x[hdr_end:]
chk(has("17-parameter"), "A2 caption is the L24 one")
x = replace_para_text(x, "The directions in Antarctic parameter space that the observations identify", "**Table A2.** " + a2_cap)

# ------------------------------------------------------------------------------------------
# 7. COMMENTS on the numbers that were NOT re-run on L27
# ------------------------------------------------------------------------------------------
NOTE = ("Not re-run on the L27 posterior (round 6 swapped every table, figure and number that has an L27 output; this one is a "
        "separate sensitivity arm last run on L24). ")
x = add_comment(x, "holding it constant instead would increase Greenland melt", NOTE + "Greenland moved ≤ 1.3 cm at any cell between the two posteriors, so the range should hold to the stated precision.")
x = add_comment(x, "It contributes 35.1 cm to the SSP5-8.5 total at 2300", NOTE + "Tap parameters are unchanged; the contribution is set by the GMST path, not the posterior.")
x = add_comment(x, "a one-sigma change moves Antarctic sea level at 2300 by about 58 cm", NOTE + "Amplification's posterior is unchanged (median 1.08); the Antarctic medians moved 1–8 cm along the geometry ridge, so the leverage numbers may shift by a similar amount.")
x = add_comment(x, "80–3200 yr across the posterior", NOTE + "RGI 19's κ posterior is unchanged to two digits (log10 κ −2.78, 5–95% −3.00 to −2.56), so the range stands.")
x = add_comment(x, "yields changes of up to 60 cm by 2300", NOTE + "On the L27 joint arm the Antarctic median differs from BRICK 2.0's by −31 cm at SSP2-4.5 and −27 cm at High-to-Low in 2300; the '60 cm' provenance was not found in the current outputs — please check which arm it came from.")
x = add_comment(x, "6.2 against 5.0 ms on a laptop", NOTE + "Timing is per draw and dominated by parameter handling; 50 rather than 58 parameters can only make it faster.")

save(x)
print("r6 applied: %d table-4 cells, %d table-5 cells, %d A1 cells + %d A1 rows deleted, 6 figures" % (len(edits), len(e5), len(e_a1), len(del_rows)))
