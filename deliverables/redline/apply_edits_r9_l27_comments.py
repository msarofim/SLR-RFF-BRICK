"""Round 9 (2026-09-21): Marcus's three comments on r8, each answered with an L27 re-run and a tracked edit.
  #1  "Do we need to rerun?" (the per-sigma Antarctic-amplification leverage)  -> diag_ais_amp_leverage.jl --tag=L27
  #11 "Retime for L27."                                                          -> diag_runtime_ladrillo_vs_brick20.jl --tag=L27 (x2)
  #9  "I inserted the updated #s, I don't know what version yielded 60 cm."      -> the joint-arm AIS medians vs BRICK 2.0, all
                                                                                    ten scenarios; the 31 cm is confirmed, the
                                                                                    plural "peak-and-decline scenarios" is not.
Base = r8 as on disk (Marcus accepted every earlier round and edited with tracking off). Every number is read from the
tagged L27 outputs; the value each edit replaces is asserted first."""
import re
import pandas as pd
from redline import *
import redline

redline.DATE = "2026-09-21T15:00:00Z"        # distinct from r7 (00:00) and r8 (12:00): validate keys on author+date+text
REPO = HERE.parent.parent; OUT = REPO / "outputs"
x = load()
x = x.replace("<w:lastRenderedPageBreak/>", "").replace("<w:t>", '<w:t xml:space="preserve">')
x = re.sub(r'</w:t><w:t xml:space="preserve">', "", x)
start_ids_above(x)
def chk(c, m):
    if not c: raise SystemExit("[r9 ABORT] " + m)

# ---- 1. the per-sigma amplification leverage (comment #1) -----------------------------------------------
LEV = pd.read_csv(OUT / "diag_ais_amp_leverage_L27.csv")
LEV24 = pd.read_csv(OUT / "diag_ais_amp_leverage_L24.csv")
def lev(df, ssp, h, defn, kind="posterior"):
    r = df[(df.ssp == ssp) & (df.horizon == h) & (df.definition == defn) & (df.sigma_kind == kind)].iloc[0]
    return r
# The draft's 58 / 24 were the regression x posterior sd on L24: assert that basis reproduces before swapping the vintage.
chk(abs(lev(LEV24, "ssp245", 2300, "regression").leverage_cm - 58) < 2 and abs(lev(LEV24, "ssp585", 2300, "regression").leverage_cm - 24) < 2,
    "L24 basis reproduces the draft's 58 / 24 (got %.1f / %.1f)" % (lev(LEV24, "ssp245", 2300, "regression").leverage_cm, lev(LEV24, "ssp585", 2300, "regression").leverage_cm))
r245, r585 = lev(LEV, "ssp245", 2300, "regression"), lev(LEV, "ssp585", 2300, "regression")
p245, p585 = lev(LEV, "ssp245", 2300, "perturbation", "prior"), lev(LEV, "ssp585", 2300, "perturbation", "prior")
chk(r585.share_of_total_pct < 5, "SSP5-8.5 share still under 5%% (%.1f)" % r585.share_of_total_pct)
old_amp = ("a one-sigma change moves Antarctic sea level at 2300 by about 58 cm on SSP2-4.5 (roughly 23% of that scenario's "
           "total) but only about 24 cm on SSP5-8.5 (under 5%)")
new_amp = ("a one-sigma change moves Antarctic sea level at 2300 by about %.0f cm on SSP2-4.5 (roughly %.0f%% of that scenario's "
           "total) but only about %.0f cm on SSP5-8.5 (under 5%%)" % (r245.leverage_cm, r245.share_of_total_pct, r585.leverage_cm))
chk(esc(old_amp) in x, "amp sentence is the L24 one")
x = replace_text(x, old_amp, new_amp)
D = pd.read_csv(OUT / "diag_ais_amp_leverage_draws_L27.csv")
d245 = D[D.ssp == "ssp245"]; d585 = D[D.ssp == "ssp585"]
big = 40.0
f_plus, f_minus = (d245.d_plus_2300 > big).mean(), (d245.d_minus_2300 < -big).mean()
f585 = (d585.d_plus_2300.abs() > big).mean()
x = add_reply(x, 0,   # thread root (#0); Marcus's #1 hangs off it
    "Re-run on L27 (julia/diag_ais_amp_leverage.jl --tag=L27; outputs/diag_ais_amp_leverage_L27.csv). The draft's 58 / 24 were the "
    "regression of Antarctic SLR at 2300 on the amplification across the posterior draws, times the posterior sd (0.17; the prior's "
    "0.18 gives the same to 0.3 cm) — the L24 basis reproduces to 59 / 25. On L27 it is %.0f cm on SSP2-4.5 (%.0f%% of the "
    "%.0f cm total) and %.0f cm on SSP5-8.5 (%.1f%% of %.0f) — essentially unchanged, so my earlier '~3/4' guess was wrong; the revert "
    "arm moved because it is a different quantity. The same run also perturbs each draw by ±1σ with everything else held: the "
    "per-draw median is %.0f cm on SSP2-4.5 and %.0f on SSP5-8.5 (2300), but on SSP2-4.5 the response is bimodal — +1σ pushes %.0f%% "
    "of the draws across the DAIS thresholds (>%.0f cm, up to ~190), −1σ pulls %.0f%% back; on SSP5-8.5 only %.0f%% move that far. "
    "So the 'because SSP5-8.5 is already past the thresholds' clause is now measured, and if you want it in one sentence: 'on SSP2-4.5 "
    "the leverage is a threshold effect — a one-sigma increase moves the median draw by %.0f cm but tips about %.0f%% of the draws into "
    "collapse by 2300.' Text updated with the L27 numbers; wording yours."
    % (r245.leverage_cm, r245.share_of_total_pct, r245.total_med_cm, r585.leverage_cm, r585.share_of_total_pct, r585.total_med_cm,
       p245.leverage_cm, p585.leverage_cm, 100 * f_plus, big, 100 * f_minus, 100 * f585, p245.leverage_cm, 100 * f_plus))

# ---- 2. runtime (comment #11) -------------------------------------------------------------------------
RT = pd.read_csv(OUT / "diag_runtime_ladrillo_vs_brick20_L27.csv"); RT1 = pd.read_csv(OUT / "diag_runtime_ladrillo_vs_brick20_L27_rep1_0706.csv")
def ms(df, model, mode, col="ms_per_draw_median", span="1850-2300"):
    return float(df[(df.model == model) & (df.span == span) & (df["mode"] == mode)][col].iloc[0])
la, ba = ms(RT, "Ladrillo L27", "apply_draw+run"), ms(RT, "BRICK 2.0", "apply_draw+run")
lr, br = ms(RT, "Ladrillo L27", "run_only"), ms(RT, "BRICK 2.0", "run_only")
la1, ba1 = ms(RT1, "Ladrillo L27", "apply_draw+run"), ms(RT1, "BRICK 2.0", "apply_draw+run")
chk(abs(la - la1) < 0.2 and abs(ba - ba1) < 0.2, "the two L27 timing runs agree to 0.2 ms (%.2f/%.2f vs %.2f/%.2f)" % (la, ba, la1, ba1))
ratio = la / ba
old_rt = ("Ladrillo runs at only 1.2× BRICK 2.0's time per posterior draw on an 1850–2300 projection (6.2 against 5.0 ms on a laptop, "
          "most of it parameter handling; the model evaluation itself is 0.78 against 0.65 ms), so a 10,000-draw scenario takes about a minute.")
new_rt = ("Ladrillo runs at only %.1f× BRICK 2.0's time per posterior draw on an 1850–2300 projection (%.1f against %.1f ms on a laptop, "
          "most of it parameter handling; the model evaluation itself is %.2f against %.2f ms), so a 10,000-draw scenario takes about a minute."
          % (ratio, la, ba, lr, br))
chk(esc(old_rt) in x, "runtime sentence is the L24 one")
x = replace_text(x, old_rt, new_rt)
x = add_reply(x, 10,  # thread root (#10)
    "Re-timed on L27, twice (julia/diag_runtime_ladrillo_vs_brick20.jl --tag=L27, 300 draws each, 07:06 and 11:24 today; "
    "outputs/diag_runtime_ladrillo_vs_brick20_L27{,_rep1_0706}.csv). Medians over draws, 1850–2300: apply+run %.2f vs %.2f ms "
    "(run 1: %.2f vs %.2f), model evaluation alone %.2f vs %.2f; ratio %.2f×. Text updated to the second run; the draft's L24 "
    "figures were within 0.1 ms of these." % (la, ba, la1, ba1, lr, br, ratio))

# ---- 3. the Conclusions' "up to 31 cm" (comment #9) ---------------------------------------------------
TAP = "_tap4p69K_V5p64m_tau800"
SCEN = [("ssp126", "SSP1-2.6"), ("ssp245", "SSP2-4.5"), ("ssp585", "SSP5-8.5"), ("vvVL", "Very Low"), ("vvL", "Low"),
        ("vvLN", "Low-Negative"), ("vvML", "Medium-to-Low"), ("vvM", "Medium"), ("vvH", "High"), ("vvHL", "High-to-Low")]
def cell(f, arm, comp, h):
    d = pd.read_csv(f); return float(d[(d.arm == arm) & (d.component == comp) & (d.horizon == h)].med_cm.iloc[0])
diffs = {}
for sc, name in SCEN:
    fl = OUT / ("scope_slr_fairunc_cells_%s_spliced_L27%s.csv" % (sc, TAP)); fb = OUT / ("scope_slr_fairunc_cells_%s_spliced_oldbrick.csv" % sc)
    chk("lws observed" in pd.read_csv(fl).provenance.iloc[0] and "observed" in pd.read_csv(fb).provenance.iloc[0], "%s arms on the observed LWS" % sc)
    diffs[name] = cell(fl, "joint", "ais", 2300) - cell(fb, "joint", "ais", 2300)
worst = max(diffs.values(), key=abs)
chk(abs(round(abs(worst)) - 31) < 0.6, "the largest joint-arm AIS difference at 2300 rounds to 31 (%.1f)" % worst)
rank = sorted(diffs.items(), key=lambda kv: -abs(kv[1]))
chk(rank[0][0] == "SSP2-4.5" and rank[1][0] == "High-to-Low", "SSP2-4.5 then High-to-Low lead: %s" % rank[:3])
old_c = "(the changes are largest for SSP2-4.5 and the peak-and-decline scenarios)"
new_c = "(the changes are largest for SSP2-4.5 and the High-to-Low peak-and-decline scenario)"
chk(esc(old_c) in x, "conclusions clause as Marcus wrote it")
x = replace_text(x, old_c, new_c)
table = "; ".join("%s %+.0f" % (k, v) for k, v in rank)
x = add_reply(x, 8,   # thread root (#8)
    "Confirmed on L27: the Antarctic median, joint arm (the paper's arm), Ladrillo minus BRICK 2.0 at 2300, cm — %s "
    "(outputs/scope_slr_fairunc_cells_<scenario>_spliced_L27_tap…csv vs …_oldbrick.csv, both on the observed land-water series). "
    "So 'up to 31 cm' holds and SSP2-4.5 is the largest; but of the three peak-and-decline scenarios only High-to-Low is close "
    "(−27) — Medium-to-Low is −5 and Low-Negative −3 — so I changed the plural to 'the High-to-Low peak-and-decline scenario'. "
    "The 60 was never in any current output on either arm (fixed-arm maximum is −29 at SSP2-4.5); it predates L24 and I would "
    "not try to trace it." % table)
save(x)
print("r9 applied: amp %.1f/%.1f cm (%.1f%%/%.1f%%), pert med %.1f/%.1f, tipped %.0f%%/%.0f%%; runtime %.2f/%.2f (%.2fx), run-only %.2f/%.2f; AIS diffs %s"
      % (r245.leverage_cm, r585.leverage_cm, r245.share_of_total_pct, r585.share_of_total_pct, p245.leverage_cm, p585.leverage_cm,
         100 * f_plus, 100 * f_minus, la, ba, ratio, lr, br, table))
