# Handoff — the dynamics-constraint question is ANSWERED (no), and the colourblind sweep found the handoff before it pointed at the wrong palette (09-22 ~16:00 → 18:30)

**Start here.** Continues `handoff_2026-09-22c_null_shipped_figures_and_L27vL30.md`, which is still the reference for the
null's provenance and whose §4 traps stand in full (as do 09-22b §8's). Records: CHANGELOG **09-22j** (the dynamics answer)
and **09-22k** (the palette sweep). Commit `a5662a9` on `ladrillo-dev`, pushed. Memory:
`ais_dynamics_channel_is_the_weaker_one` (new), `objective_scores_levels_not_rates` (REVISED in place — its shape table now
carries two limits), `INDEX_ais_imbie.md` updated.

## 0. STATE AT HANDOFF
- **Champion and paper posterior remain L27.** Nothing was refitted; `champions.json` and the draft are untouched.
- **Nothing is running.** Every result below is a fixed-parameter diagnostic.
- The calibration target is unchanged (`recalib_targets_ext.csv`, md5 `eb768cd9…`).
- The three stale `outputs/*_L24.*` modifications from an earlier session are still in the tree; still not mine to resolve.
- **Marcus ruled on the VV palette this session: DIRECT-LABEL the lines** (§3 below). **LANDED and both figures
  regenerated** — `lf.direct_label()` in `ladrillo_figs.py`, wired into FIG 4 (`plot_future_components.py`) and FIG 5
  (`plot_vv_gsic_wr_vs_ladrillo.py`); `figures/paper/future_components_vv_L27_joint.png` and
  `figures/paper/vv_gsic_ladrillo_L27_2300.png` rebuilt at `--tag=L27 --paper`.

## 1. ⭐⭐ THE ANSWER: a dynamics constraint would NOT help, and the premise it rested on was WRONG

Marcus asked: *"Consider whether adding a dynamics constraint could help with making a good model."*

### 1a. ⚠⚠ First, the correction — do not rebuild the argument on the old premise
The case for a dynamics channel rested on reading `diag_ais_objective_shape_sensitivity_L30.csv` as "the level channel is
blind to discharge SHAPE": at ρ 0.966, constant offset q **2.5343** vs late divergence **2.5308**, ratio **1.001**. Both
halves of that reading are wrong for this purpose:

1. **The indifference is a FUNCTION OF ρ, and `rho_ais` is SAMPLED.** The same ratio is **1.74 at ρ 0.90** and **2.03 at
   ρ 0.60**. And ρ_ais went **0.893 (L27) → 0.966 (L28/L30)** when the target became the IMBIE level. So the blindness is
   not a property of the objective — it is a property of where the refit put ρ.
2. ⭐ **It does not transfer to a physically realisable move.** Those are abstract unit shapes normalised to 0.1 cm at the
   final year. A real move along the DAIS discharge ridge changes the whole 1900–2025 trajectory and the level channel sees
   it plainly. **General lesson, now in memory: never price a degeneracy on abstract shapes when the parameters that would
   produce it can be perturbed directly.**

### 1b. The test that replaced it — `julia/diag_ais_isocumulative_channels.jl` (NEW)
Hold the **1979–2023 cumulative FIXED** and vary only discharge SHAPE, so any preference a channel expresses cannot be the
cumulative re-read with a sign flip — which, by `ais_net_dynamics_tradeoff_identity`, is exactly what an arm-to-arm
comparison *cannot* rule out. Two independent axes, `ais_iceflow0`/`anto_beta` solved by **secant** against each:
- `--axis=alpha` → `antarctic_alpha`, the flux law's temperature-INDEPENDENT `(1−α)` vs temperature-TRACKING `α·r(t)²` split
- `--axis=anto` → `anto_alpha`/`anto_beta`, the ocean-temperature response's slope and offset

⚠ `ISO_TOL` is **derived from the sampled spread** (0.05 sd of cum_1979_2023, measured at run time = 0.0016 cm), per the
standing tolerance rule. L27, n = 100. `alpha` 500/500 cells converged, `anto` 498/500.

| axis `alpha` (α×) | 2018–23 dyn anom | d LEVEL | d DYN ind | d DYN ar1 | d DYN win |
|---|---|---|---|---|---|
| 0.50 | −63.4 | −2.56 ± 0.37 | −3.46 ± 0.17 | −0.94 ± 0.05 | −3.20 ± 0.14 |
| 0.75 | −92.0 | **+0.28 ± 0.17** | −1.02 ± 0.12 | −0.28 ± 0.03 | −1.00 ± 0.09 |
| 1.00 (control) | −119.1 | 0 | 0 | 0 | 0 |
| 1.30 | −150.4 | −4.12 ± 0.37 | −0.47 ± 0.24 | −0.12 ± 0.06 | −0.22 ± 0.20 |
| 1.60 | −180.8 | **−12.27 ± 1.29** | −2.79 ± 0.74 | −0.73 ± 0.20 | −2.01 ± 0.61 |

| total discrimination across the contour | LEVEL | DYN ind | DYN ar1 | DYN win |
|---|---|---|---|---|
| axis `alpha` | **12.55** | 3.46 | 0.94 | 3.20 |
| axis `anto` | **16.48** | 4.15 | 1.05 | 3.59 |

**Three findings, both axes agreeing:**
1. **The level channel is NOT degenerate along this direction** — 12.6–16.5 log-units, rejecting the accelerating end hard
   and ASYMMETRICALLY (α×1.6 costs 12.3, α×0.5 only 2.6). Consistent with `ais_ramp_rejected_by_the_pause`.
2. **The dynamics channel is the WEAKER of the two everywhere** — **3.6–4.0× (IND)**, **13.4–15.7× (AR1)**. σ_dyn (76 Gt/yr
   typically, 150 over 2020–23) is why, the same reason D1 priced at ≤3 against the ramp.
3. ⭐⭐ **DECISIVE: both channels share an optimum (α×0.75–1.00) and both penalise α×1.30 and α×1.60 — the cells that
   bracket IMBIE's own −167.2 Gt/yr.** A dynamics constraint is a **weaker copy of the pull the level channel already
   exerts**, not a corrective. Mechanism = the identity: at fixed cumulative, steepening 2018–23 forces the earlier decades
   weaker, and the channel scores all 45 years.

⇒ **Third independent confirmation that DAIS has no direction reaching IMBIE's acceleration** (the ρ-cap side and the ramp
side being the other two).

### 1c. ⛔ And the ρ-cap route is dead too — L29 already ran it
L29 (same IMBIE target, ρ capped at 0.90, p50 0.885 pressed on the bound) is **indistinguishable from L28 on every
channel**: DYN ind 0.0 ± 0.6, LEV 0.3 ± 0.4. And its projections move **further** from L27, not back:
SSP1-2.6 **2300 AIS p95** = L27 **65.8**, L28 44.9, **L29 28.7**, L30 53.3 cm (fixed-climate arm).
⚠ Read that spread with `ais_amp_leverage_is_a_threshold` in hand — it is a **tipped share crossing 5 %**, not a smooth
sensitivity. Do not quote it as "the projection changed 2×".

### 1d. The arm-level companion — `julia/diag_ais_channel_separation.jl` (NEW)
L27/L28/L29/L30, n = 100 each, both channels, ⚠ each arm's own (sd_ais, ρ_ais) applied to **every** arm in turn (a
log-likelihood LEVEL is not comparable across arms that sampled different σ).

| arm | ρ_ais | cum 79–23 cm | baseline discharge | 2018–23 dyn anom |
|---|---|---|---|---|
| IMBIE 2026 | — | ~1.33 | — | **−167.2** |
| L27 | 0.893 | 0.948 ± 0.008 | −1918.5 ± 11.8 | **−119.1 ± 4.6** |
| L28 | 0.966 | 1.224 ± 0.011 | −1928.8 ± 10.7 | −74.6 ± 4.4 |
| L29 | 0.885 | 1.300 ± 0.007 | −1952.5 ± 10.6 | −73.4 ± 4.2 |
| L30 | 0.967 | 1.214 ± 0.010 | −1945.5 ± 11.1 | −102.0 ± 5.7 |

⭐ **The identity is visible straight down these columns**: cumulative 0.948 → 1.300 cm as the dynamics anomaly degrades
−119 → −73. Level channel L28 − L27 = **+7.4 ± 0.4**; dynamics channel L27 − L28 = **+3.1 ± 0.5** (IND).
⛔ **NEVER QUOTE THIS COMPARISON ALONE.** It cannot separate "the dynamics channel carries independent information" from
"the dynamics channel is the cumulative with a sign flip" — which is the whole reason §1b exists.

## 2. ⚠ TRAPS IN THE NEW CODE (09-22c §4 and 09-22b §8 still apply in full)
- ⛔ **`ndrop += 1` inside the draw loop created a NEW LOCAL** under Julia's soft-scope rule, so non-converged
  iso-cumulative cells would have reported **0 dropped** regardless — a silent gate of exactly the family `INDEX_diag`
  catalogues. Julia's own warning caught it before the production run; it now says `global ndrop += 1`. **If you copy this
  script, copy that.**
- ⚠ **A frozen copy must live in `julia/`, not a subdirectory** — the scripts `include(joinpath(@__DIR__, …))`, so
  `julia/_frozen/…` cannot find `ladrillo_projection.jl`. The repo convention is `julia/_frozen_<name>.jl`; these are
  **gitignored**, so the frozen copies are not in the commit (the source files are).
- ⚠ **The likelihood in both new scripts is a RE-IMPLEMENTATION** of `hetero_logl_ar1`, same as the 09-22f/g family.
  ⭐ **The 09-22c handoff's claim that the calibrator cannot be included is STALE** — `calibrate_mcmc_ext.jl` has had a
  `if abspath(PROGRAM_FILE) == @__FILE__` guard since ~line 2349 and six scripts already include it. But its top-level
  `const`s parse `ARGS`, so an includer inherits its own flags and pays the full target-read plus Mimi build. Re-implementing
  is still the right call; the reason is different from the one recorded.
- ⚠ **`diag_ais_flux_split_vs_imbie.jl:30` reads `ice_flux` ONLY** and `run_L30.sh` runs it under `--tag=L30`, so
  `outputs/diag_ais_flux_split_vs_imbie_L30.csv`'s `net_gt` excludes L30's ramp discharge while `ais_cm` in the same file
  includes it. Still **not fixed, still Marcus's call** (other results rest on it). There is also a fourth state term,
  **`ISO`**, that neither that script nor the new ones carry — immaterial in the no-ramp hindcast, wrong in a response arm
  or a tipping projection.
- ⚠ **The level target is the IMBIE one for EVERY arm, including L27**, because `recalib_targets_ext.csv` has carried
  `AIS_SOURCE = "imbie2026"` since L28 and the Frederikse-era file L27 was fitted to is gone. That is correct for a common
  channel, but **L27's level score is out-of-sample and must never be read as "L27 fits worse"**.
- ⚠ **L30 is NOT the clean IMBIE-level refit — L28 is.** L30 = L28's objective PLUS `--ais-ramp`, so L27→L30 conflates the
  target change with the ramp. The 09-22c handoff's L27-vs-L30 framing is the confounded pair; use **L27 vs L28**.

## 3. THE COLOURBLIND SWEEP — the handoff pointed at the wrong palette
⚠ **The priority is the reverse of what 09-22c §1a assumed.** It flagged `#1b7837` green / `#b2182b` red (deutan ΔE 2.7).
Real, but the paper's **six live figures** (confirmed by md5-matching the docx media against `figures/`; the duplicate
images in FIG 3–6 are tracked DELETIONS of the L24 originals, not a defect) draw from `SRC_COLOR` and `VV_SET`. The SSP
triple is the **memo** path only.

| palette | verdict (`python python/validate_palette.py`) |
|---|---|
| `SRC_COLOR` (4 models) | all 6 pairs **PASS**; `#ff9900` contrast 2.14:1 but already has distinct markers + linestyles |
| `SSP_SET` (3) | **2 FAIL** — green/red deutan 2.7, green/blue tritan 5.5 |
| `VV_SET` (7) | **3 FAIL** — worst `#f69320` ML / `#c8a000` M at ΔE **8.4 in NORMAL vision** (floor 15), **1.4 protan** |

⭐ **The failures LOCALISE**: the four colours that recur repo-wide (`#00a9cf`, `#003466`, `#f69320`, `#df0000` — they look
like the IPCC AR6 scenario palette, but ⚠ **no provenance comment exists in-repo and that identification is recollection,
not a receipt**; worth confirming before citing) are mutually safe, and so are the three in-fill colours invented to stretch
them over seven markers. **Every failure is an anchor-vs-infill collision.**

**LANDED in `a5662a9`:** `SSP_SET` → `#003466` / `#f69320` / `#df0000` (all pairs PASS, and the SSP and vv figures now speak
one palette); the duplicated palettes in `plot_ladrillo_memo_figures.py` and `plot_vv_gsic_wr_vs_ladrillo.py` now **derive
from `ladrillo_figs`**. **No figure has been regenerated.**

**MARCUS RULED (09-22): DIRECT-LABEL the lines** for the seven van Vuuren markers, rather than re-colouring. Rationale
measured this session: a sequential ramp **cannot** fix n = 7 (usable OKLab L* under a ≥3:1 contrast cap spans 70.7, giving
**11.8 per adjacent gap against a floor of 15**; the best ramp tested reaches min contrast 1.05:1), and a categorical set
that *does* clear the floors returns magenta/black/olive/lime and destroys the scenario reading. Direct labelling keeps all
seven colours and removes the legend lookup entirely — the recipe `figures/diag_imbie2026_dynamics_null_L30.png` already uses.
**Affected: FIG 4 (`plot_future_components.py`) and FIG 5 (`plot_vv_gsic_wr_vs_ladrillo.py`).**
⚠ **Linestyle is NOT available as a second channel in either** — it already encodes model (Ladrillo solid vs BRICK dashed).
⚠ **Regenerating a figure re-runs its data path**; check each script's inputs still exist at the tags the paper uses before
assuming a label-only edit is label-only.

## 4. NEXT
1. ✅ **Direct labelling is DONE** on FIG 4 and FIG 5 and both are regenerated. Two design points worth knowing if you
   touch `lf.direct_label()`: it must be called **AFTER** the axis limits are final (it derives its minimum label gap from
   the y-range and extends the x-limit to make room), and it **collapses to ONE label** when the whole set fits inside one
   gap — which is what the Land-water storage panel needs, since LWS is identical across every scenario by construction and
   seven stacked leader lines there asserted a distinction that does not exist. ⚠ The remaining figure work is Marcus's
   eye, not a gate: the labels are placed, but panel crowding in FIG 4's Glaciers and Thermal-expansion panels is a
   judgement call.
2. `SRC_COLOR`'s `#ff9900` contrast 2.14:1 — leave it (markers + linestyles carry it) or darken; not urgent.
3. The three optional §1b follow-ups from 09-22c are now **largely overtaken**: `ρ_ais` as a secondary contributor is
   answered by L29 (§1c); the window-by-window identity check is partly answered by the arm table (§1d). What remains
   genuinely open is whether OTHER components absorbed part of the Antarctic level (L27 vs L28 component hindcast stats
   were never compared — cheap).
4. The standing list: comment #12 (code availability), venue (GMD), package extraction for Tony's team, `facts` remote,
   FACTS/MAGICC scope, pulse analysis. And `deliverables/GMD_imbie2026_null_INSERT.md` still needs Marcus's `[MCS]`
   sentences before it can go into the draft.

## 5. SCOPE OF THE NEGATIVE RESULT — state it this way, not more strongly
Two axes, one arm (L27), one noise-model family, nothing refitted, and **no change to the objective is proposed** — what
Ladrillo is fitted to is methodological and Marcus's. The finding **bounds the VALUE of a dynamics channel**; it does not
prove that no reformulation of the Antarctic likelihood could help.
