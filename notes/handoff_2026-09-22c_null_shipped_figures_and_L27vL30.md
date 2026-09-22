# Handoff — the null is SHIPPED (Marcus: "A"); next session = COLORBLIND-SAFE FIGURES, then the L27-vs-L30 puzzle (09-22 13:00 → 18:00)

**Start here.** Self-contained for the IMBIE-2026 arc's close-out. Continues
`handoff_2026-09-22b_L30_ramp_not_taken.md` (which is still the reference for how L30 was built and what its traps are —
its §8 stands in full) and does not supersede it. Records: CHANGELOG **09-22f** (power + attribution + shape),
**09-22g** (D1 tested), **09-22h** (n=100 re-measurement + the paper insert); scoping note
`notes/scoping_2026-09-21_dais_structure_vs_imbie2026.md` **§9, §10**. Commits `196034e`, `2507475`, `4f9b4c1` on
`ladrillo-dev`, all pushed. Memory: `ais_ramp_rejected_by_the_pause`, `imbie_partition_is_an_identity` (both new),
`objective_scores_levels_not_rates` (REVISED in place), `INDEX_ais_imbie.md` updated.

## 0. STATE AT HANDOFF (2026-09-22 ~18:00)
- **Champion and paper posterior are L27** and Marcus has now RULED on it (option "A", ship the null). Draft r9
  (`deliverables/GMD.Ladrillo.v1_review-2026-09-21c_L27.docx`) is unchanged; `champions.json` untouched.
- **Nothing is running.** No chains were run in any of 09-22f/g/h — every result is a fixed-parameter diagnostic.
- L28/L29/L30 remain landed and unpromoted. The calibration target is unchanged (`recalib_targets_ext.csv`, md5 `eb768cd9…`).
- The three stale `outputs/*_L24.*` modifications from an earlier session are still in the tree; still not mine to resolve.

## 1. ⭐ NEXT — §1a is the live task; §1b was answered before this handoff was filed (Marcus, 09-22)

### 1a. Make ALL figures colorblind-friendly
**The defect is measured, not eyeballed.** The paper's figure scripts pair `#1b7837` green with `#b2182b` red; that pair is
**OKLab ΔE 2.7 under deuteranopia** — effectively one colour. `#2166ac` blue / `#1b7837` green is **5.5 under tritanopia**.
Blue / red / grey are mutually **≥ 12.8** and are safe.
- The palette lives in `python/plot_ladrillo_memo_figures.py`: `SSP_COLOR` (`ssp126` green / `ssp245` blue / `ssp585` red),
  `LADRILLO_COLOR`, `SOURCE_COLOR`. Other figure scripts in `python/` need the same sweep — **enumerate them first**, do not
  assume that one file is all of them.
- ⚠ **`SSP_COLOR` is the hard case**: three SSPs with green in the middle of a sequence. A diverging/sequential ramp on
  ONE hue (or blue/grey/red) is the fix, not a re-shuffle of the same three hues. Scenario order is ordinal, so a
  sequential ramp is defensible where categorical hues are not.
- ⚠ **Identity must not rest on colour alone** — `figures/diag_imbie2026_dynamics_null_L30.png` shows the pattern to copy:
  two baselines separated by LINESTYLE, only three hues, direct labels.
- **Validator**: there is no `node` on this machine, so `dataviz`'s `scripts/validate_palette.js` will not run. A working
  Python implementation (Viénot 1999 dichromat simulation + OKLab ΔE + WCAG contrast) was written inline this session —
  **it is now SAVED as `python/validate_palette.py`** (Viénot 1999 dichromat simulation + OKLab ΔE + WCAG contrast; exits 1
  on failure so it can gate a build). Run it on each palette before and after editing. Targets: CVD ΔE ≥ 8, normal-vision ≥ 15, contrast ≥ 3:1 on white.
- ⚠ **Regenerating a figure re-runs its data path.** Check each script's inputs still exist at the tags the paper uses
  before assuming a colour-only edit is colour-only.

### 1b. ✅ THE L27-vs-L30 PUZZLE — ANSWERED 09-22i (kept here for the reasoning; only the three optional follow-ups below remain)
> *"I am surprised that calibrating to updated data actually makes the fit worse to that updated data."*

**State the fact precisely first, because the compressed version overstates it.** Refitting to the IMBIE **level**
target improved the fit to the LEVEL (1979–2023 cumulative z **−2.64 → −0.77**) — the thing it was fitted to got better,
as it must. What got WORSE is the **dynamics anomaly**, which was NOT in the likelihood:

| dynamics misfit, Gt yr⁻¹ (n=100) | 1979–91 | 1992–2002 | 2003–10 | 2011–17 | 2018–23 |
|---|---|---|---|---|---|
| **L27 (shipped)** | +3.3 | −8.3 | +21.8 | **+13.4** | **+48.1** |
| L30 (refit to the IMBIE level) | −4.0 | −8.5 | +38.7 | +39.8 | **+85.8** |

So it is **not** "fitting data makes the fit to that data worse". It is: **IMBIE's total and IMBIE's partition are different
observations, the refit saw only the total, and it bought the total by the route the partition says is wrong.**

**⭐⭐ ANSWERED 09-22i — the dig was done this session; §1b is now CLOSED. It is an IDENTITY.**
2018–23 anomalies vs 1979–2008 (Gt/yr): IMBIE dynamics **−167.2**, SMB **+141.0**, net −26.2. Since `net ≡ smb + dyn`,
**`dyn_misfit = net_misfit − smb_misfit`**. Ladrillo's SMB produces window anomalies of only **−20 … +27** against the
record's **+141**, so `smb_misfit` is pinned in **[−161, −114]** and cannot approach zero. Therefore fitting the net exactly
forces a dynamics understatement of **≥ 114 Gt/yr**, and fitting the dynamics forces the net to lose 114 Gt/yr MORE than
observed. **L27 and L30 are two points on ONE constraint line; neither is better calibrated.**
⛔ **The obvious hypothesis — that the refit bought the cumulative by cutting accumulation — was REFUTED**: over 1979–2023,
**96.4 %** of L30's extra net loss came from MORE DISCHARGE, 3.6 % from less accumulation. What it actually did was add
discharge EARLY (−31.0 Gt/yr over 1979–2008) and REMOVE it LATE (+7.8 over 2018–23) — it **flattened the discharge trend**
to reproduce a net that flattens. The objective permits this because it is only ~2× more sensitive to a level offset than to
a smooth late ramp, so it cannot strongly tell "more discharge throughout" from "accelerating discharge".
⇒ memory [[ais_net_dynamics_tradeoff_identity]], CHANGELOG **09-22i**. The paper insert's result paragraph was CORRECTED to
state the identity; its `[MCS]` note now flags that what is demonstrated is **the six-year snowfall excursion lying outside
the module's representable behaviour, NOT that DAIS's discharge law is wrong**.

**What is LEFT of §1b, if anything** (all optional, none blocking the paper):
  1. **ρ_ais** was never ruled out as a secondary contributor — `diag_ais_dynamics_channel_profile.jl --tag=L29` is still the
     one-line test (L29 caps ρ at 0.90). The identity explains the bulk, so expect this to be small.
  2. **Other components** may have absorbed part of the Antarctic level; the component hindcast stats L27 vs L30 were not
     compared. Cheap, and it would close the last alternative.
  3. The identity was measured on the 2018–23 window only. Whether it holds window-by-window across the record is unchecked.

**Tools that already exist for this**: `julia/diag_ais_dynamics_channel_profile.jl` (takes `--tag`, prints absolute SMB and
dynamics per window), `outputs/diag_ais_flux_split_vs_imbie_L{27,28,29,30}.csv`, `outputs/ladrillo_prior_posterior_L*.csv`
(parameter medians), `outputs/diag_refit_precision_L28_L29_L30.csv`, `bench_ladrillo_L*.{md,csv}`.

### 1c. Then the standing list
Comment #12 (code availability) is still open. Venue (GMD), package extraction for Tony's team, `facts` remote, FACTS/MAGICC
scope, pulse analysis. And the paper insert (§2) needs Marcus's `[MCS]` sentences before it can go into the draft.

## 2. WHAT WAS DONE 09-22 f/g/h, AND THE NUMBERS THAT SURVIVE
Four new diagnostics, **no refits**, all run from `julia/_frozen_*` copies:
- **`diag_ais_ramp_objective_power.jl`** — synthetic-truth power test, **seed 20260922** stamped in both artifacts. A record
  that genuinely contains the 6e-4 @ 0.75 K response is recovered **95.7 %** of the time at the posterior's own ρ, at the
  exact cell (3e-4 @ 0.60 K: 84.5 %). ⭐ **The objective is not blind, so the null is informative.** Upper bound on power
  (other parameters fixed).
- **`diag_ais_ramp_penalty_attribution.jl`** — exact per-year split of `res'Σ⁻¹res`. The penalty is **2018–25**.
- **`diag_ais_objective_shape_sensitivity.jl`** — across SMOOTH shapes the objective's per-cm sensitivity spans only ~2×
  (1.32–2.53 per 0.1 cm); 11.7× applies only to a true discontinuity, which a monotone ramp never produces. ⇒ the rejection
  is **amplitude²**, and memory `objective_scores_levels_not_rates` was REVISED (its mechanism claim was too strong).
- **`diag_ais_dynamics_channel_profile.jl`** — option D1 priced. IMBIE's partition is an **IDENTITY** (`smb+dyn==mb` to
  4e-8), so D1 = level + ONE channel. The dynamics channel wants a response but carries ≲3 log-units against the level
  channel's −10.6.

**⚠⚠ THE NUMBERS WERE RE-MEASURED AND THE FIRST ONES ARE SUPERSEDED.** 09-22f/g quoted log-likelihoods from **3–5 draws**.
At **n = 100, mean ± SE**: level 6e-4 **−10.62 ± 0.73** (was −11.85), 3e-4 **−3.52 ± 0.60**; dynamics 3e-4
**+2.83 ± 0.44** (was +1.77), 6e-4 **+1.83 ± 0.58** (was +0.25). ⛔ **At n = 25 the 3e-4 NET came out +0.28 — the opposite
sign to n=5 (−1.49) and n=100 (−0.69). That cell's sign is inside the noise and must not be quoted.** The VERDICT is robust
at every n: large response rejected by ≈9–10, intermediate ≈0 to −3, only the small early one mildly positive.

## 3. DELIVERABLES PRODUCED
- `deliverables/GMD_imbie2026_null_INSERT.md` — placement (against the existing *"Deliberately removed: IMBIE, and the
  total"* paragraph, which already makes IMBIE 2026 out-of-sample by construction), technical caption, two methods
  paragraphs, a result paragraph, Table X, reference stub. **Framing sentences are marked `[MCS]` and deliberately blank.**
  ⚠ The Otosaka **author list and exact title are NOT verified** — taken from the data file header; pull from the paper.
- `figures/diag_imbie2026_dynamics_null_L30.png` + `python/plot_imbie2026_dynamics_null.py`.

## 4. ⚠ NON-OBVIOUS STATE / TRAPS (09-22b §8 still applies IN FULL; these are additional)
- ⛔ **A log-likelihood difference averaged over posterior draws needs its SE MEASURED.** This session quoted two decimals
  off 3 draws and had to correct them; one cell changed sign at an intermediate n. Compute the per-draw SE, always.
- ⛔ **Model dynamics is `ice_flux + disintegration_rate`**, because the additional discharge response lands in the
  fast-dynamics term (`disintegration_rate += ramp_rate`). Reading `ice_flux` alone made the response move the dynamics
  anomaly by 0.2 Gt/yr and **nearly produced a false negative on D1** — the suspicious-uniformity rule caught it.
  ⚠ **`diag_ais_flux_split_vs_imbie.jl`'s `net_gt` column has the same omission (plus `ISO`)** — immaterial in the no-ramp
  historical window (the paleo binary does not tip in 1979–2023) but WRONG in a response arm or a tipping projection.
  **Not fixed; other results rest on that script, so it is Marcus's call.**
- ⚠ **`diag_imbie2026_vs_targets_windows_*.csv` carries a STALE provenance string for the AIS column** ("Frederikse 2020
  <= 2018, GRACE-FO after"). The AIS target has been IMBIE from 1979 on since L28. The column is right; the string is not.
- ⚠ **The AIS level target equals IMBIE to machine precision from 1992 on** (`ais[2002] − ais[1991]` = 0.242471…, identical
  to `imbie_cm`), and the windows that differ are exactly those anchored at 1978. Any window-rate likelihood term would
  therefore double-count. This is why option C was not recommended.
- ⚠ The `diag_ais_ramp_likelihood_profile.jl` −33.8 is the **0.45 K** cell; the attribution's −10.62 is the **0.75 K** cell.
  **Always name the onset with the slope** — these look like a contradiction and are not.
- ⚠ The three superseded CSVs were **regenerated in place** at n=100 rather than quarantined: they are deterministic given
  the draws and the 20260920 paleo seed, so the 3–5 draw versions are reproducible from the same scripts. The logs
  (`outputs/log_diag_*`) are untracked.
- ⚠ The likelihood in the power/attribution/profile scripts is a **re-implementation** of `hetero_logl_ar1` (the calibrator
  runs a chain on load, so it cannot be imported). Differences BETWEEN settings are exact; the LEVEL is not the logpost.
  **If the calibrator's noise model changes, those copies must follow.**
