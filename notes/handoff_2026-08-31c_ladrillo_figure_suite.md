# Handoff — the Ladrillo figure suite, and the glacier arm that was misnamed

**Start here.** Repo `SLR-RFF-BRICK`, branch `ladrillo-dev`. Written 2026-08-31.
Extends `handoff_2026-08-31b_vv_comparison_and_glacier.md`, whose §2 (glacier figure) it
**partly supersedes** — read §1 below before using anything from that section.

---

## 1. ⚠ THE GLACIER FIGURE'S SECOND ARM WAS NOT LADRILLO (commit `da04f36`)

Marcus asked whether `vv_gsic_wr_vs_mengel` is "really BRICK2.0 (Wigley-Raper) vs Ladrillo
(3 glaciers, Mengel)". **Half right — and the wrong half mattered.** The arm was
`glaciers_mengel` on the `extA108` posterior = the single-reservoir Mengel-2016 emulator
inside BRICK (BRICK-AM), **Ladrillo's predecessor**. Four axes differ, not a label:

| | extA108 plain Mengel | Ladrillo L21 |
|---|---|---|
| structure | ONE global reservoir pair | **THREE** reservoirs R19/SLOWP/FAST |
| rate law | fixed `τ_fast`/`τ_slow`, split by `f` | `min(κ_b·exc^ν_b,1)(S_eq,b − S_b)` |
| driver | global GMST | per-block glacier-frame temperature |
| posterior | `..._extA108.csv` | the **L21 chains** |

Ladrillo runs `glaciers_nu3` via `build_brick_nu3*` (`ladrillo_projection.jl:696`).
**Mengel-2016 is the ancestor of the EQUILIBRIUM FORM only.**

**NAMING (the answer to the question asked): "Ladrillo L21"** — L14's config on the calib
1.6.0 + CMIP7 drivers, its OWN chain set (`outputs/mcmc/chain_L21_seed*_n2000000.csv`), NOT
the `parameters_subsample_brick_mengel_L14.csv` thinning. ⚠ **45.01 cm @2100 stays an L14
number.** The glacier module is the **3-reservoir Nauels-ν**.

Rebuilt as `plot_vv_gsic_wr_vs_ladrillo.py`; both extA108 arms dropped on Marcus's call.
Their CSVs stay on disk as provenance. **No new runs were needed.**

**The result got sharper.** Melt rate @2300 (cm/century) — Ladrillo `0.55 / 0.00 / 0.01 /
0.25` on the four decline pathways against WR `4.75 / 1.69 / 1.90 / 2.95`, while Ladrillo is
still at **1.96 on both rising markers**. So it tracks temperature rather than being
uniformly slower. ⚠ **Ladrillo's scenario spread @2300 is the WIDER one (15.1 vs 10.0 cm)** —
WR saturates toward a common ceiling and compresses its own. **That independently retires the
b=0.52 arm**, which existed only to restore a spread plain Mengel had collapsed to 3.5 cm.

---

## 2. THE SUITE (commits `f9fbd20`, `095ebb0`)

| figure | script |
|---|---|
| `figures/hindcast_components_L21.png` | `plot_hindcast_components.py` |
| `figures/future_components_ssp_L21_joint.png` | `plot_future_components.py --set=ssp` |
| `figures/future_components_vv_L21_joint.png` | `plot_future_components.py --set=vv` |

Same 2×3 grid, component order, palette and gate style, so they read as one study.
`python/ladrillo_figs.py` holds the shared constants — including the **three baseline
windows** and a `TAG_DESC` that refuses an undeclared tag.

**Blocker removed first: BRICK 2.0 had NO joint-arm trajectory output at all.**
`scope_slr_fairunc_oldbrick.jl` stored three horizon slices only. It now stores the full year
axis and emits `paths` in the Ladrillo schema. **Cells and draws verified bit-identical**
before the other nine scenarios ran.

**Genuinely new:** per-component projection figures (there were NONE on either set — the
component view was tables only); any van Vuuren projection figure beyond glaciers; an LWS
panel (obs-only, stated — neither model emits an LWS hindcast); the PREDICTIVE band on L21;
and the IGCC 2024 GMSL ensemble, never before overlaid on a Ladrillo figure and **not in the
fit**, so agreement with it is evidence rather than circularity.

---

## 3. ⚠ THREE GATE LESSONS, ALL FROM GATES FIRING ON REAL DATA

1. **A `CHECK` is not a `FAIL`, and not a `PASS` either.** The gate first REFUSED ssp585 over
   the known `ais@2300` exceedance. Refusing is disproportionate; allowing silently is worse.
   CHECK rows are now returned and **stamped on the caption**; unrecognised verdicts stay fatal.
2. **An identity bound on a non-identity is a broken gate.** The baseline check demanded
   `1e-6 cm` and fired on `2.5e-3` — the postpred files are re-referenced PER DRAW so the
   ensemble MEDIAN need not be exactly zero. The bound is now **derived**: a tenth of the
   smallest wrong-window displacement in these data (0.0974 cm). Mutation-tested.
3. **A console summary that contradicts its own figure is worse than none.** The table read
   the raw glacier target while the panel plots the r19-corrected one.

**Reported, never asserted:** the component sum vs `total` is printed, not gated — medians do
not add. Informative: **BRICK 2.0 runs ~8 cm apart at ssp245/2300 vs Ladrillo's 3 cm**, its
AIS tipping decorrelating from the rest.

---

## 4. FOR MARCUS — open items, none decided here

1. **`ais @2300` CONTROL exceedance** (−0.518 cm vs `CONTROL_TOL_CM = 0.5`). Now STAMPED on
   the SSP figure rather than hidden. Still undecided: is the tolerance wrong, or the
   cross-driver gap? AIS@2300 is a headline number.
2. **The two hindcast arms were forced from DIFFERENT driver files** — BRICK 2.0 from
   `fair_mean_{gmst,ohc}.csv`, Ladrillo from `ssp245harm`. Stated on the figure, not fixed.
   Any Ladrillo-minus-BRICK reading of the hindcast carries that gap.
3. **`plot_ladrillo_memo_figures.py` still `SystemExit`s on `--tag=L21`** (undeclared in its
   own `TAG_DESC`). One declared entry unblocks the memo total-trajectory figure. Not done
   here because the entry must be a DECLARED description, and the memo figure's captions
   would need re-reading against L21 first.
4. **`scope_ladrillo_vs_brick20_scorecard.py` has no L21 run** (L10/L11/L14 only).
5. **`plot_ssps_gsic_wr_vs_mengel.py` still carries the extA108 arms** and the mixed-vintage
   dagger. If the b→0.89/b=0.52 arms are being retired everywhere, that figure is the
   remaining place they live — but its SSP set genuinely straddles calib 1.4.5/1.6.0, so it
   is not a copy of the van Vuuren fix.
6. **`INDEX_slr.md` is ~15.9 KB against a 14 KB soft budget** (15.4 KB before this session).
   Under the 18 KB hard ceiling.
