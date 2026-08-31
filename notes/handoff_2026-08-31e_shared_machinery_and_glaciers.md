# Handoff — the FACTS runs, the four-source vv figure, one machinery, and the glacier-regrowth scope

**Start here.** Repo `SLR-RFF-BRICK`, branch `ladrillo-dev`, HEAD **`9d5f372`**. Written
2026-08-31, continuing `handoff_2026-08-31d_four_source_comparison_and_vv_runs.md`.

⚠ **THREE REPOS AGAIN, and two are on NEW BRANCHES that did not exist yesterday.**

| what | where | branch | state |
|---|---|---|---|
| figures, tables, the scope, this note | `SLR-RFF-BRICK/` | `ladrillo-dev` | clean, **62 ahead of origin** |
| FACTS climate builder, config generator, extractor, 10 experiments | `~/Documents/2026/CodeProjects/facts/` | **`slr-comparison-arm`** (new) | clean, 3 ahead of `main` |
| MAGICC vv emissions builder + frozen run notebook | `~/.../MAGICC/slr-refresh/` | **`vv-slr-runs`** (new) | clean, 1 ahead of `main` |

**NOTHING IS PUSHED.** `slr-refresh`'s origin is the members-only Nauels GitLab and the binary
and drawnset are the sensitive items — pushing that one is **Marcus's call**. Both new branches
were cut because their repos sat on their default branch; `facts/main` tracks upstream
radical-collaboration.

---

## 1. What was asked, in order

1. Clean up memory, then launch FACTS. → §2, §3
2. Build the four-source van Vuuren figure. → §4
3. *"Ladrillo is now the lowest model for glaciers in 2100. MAGICC seems like it might have more
   glacier regrowth in the peak-and-decline scenarios: is that something that can even happen in
   Ladrillo? Is it something that should be added if not?"* → §5
4. *"I would also update so that everything is using the same machinery where possible (e.g. for
   FACTS SSP)."* → §6
5. *"BRICK presumably doesn't regrow because its GSIC model continues to melt at all temperatures
   above pre-industrial."* → §5.2. **Correct, and it overturned my first reading.**
6. Scope glacier regrowth. → §7. **The answer changed again, on numbers.**

---

## 2. MEMORY (done)

`INDEX_slr.md` was 16.4 KB against a 14 KB soft budget. Split **forward, not to archive**: the
four-model comparison arc moved to a new **`INDEX_cmp.md`**, because an archive split would have
left `slr` still over soft AND had nowhere to put the day's results. `INDEX_slr` → 12.0 KB.

Also fixed a **stale fact**: `vv_marker_cubes.md`'s body was corrected on 08-31 but its
`description:` frontmatter — the field recall actually reads — still said "only 2 of the 4
comparison models can be driven", the claim the previous handoff retracted.

New memories: `magicc_vv_slr_medians`, `facts_shared_climate_arm`, `vv_crossover_four_sources`,
`paired_mean_crosses_on_a_tail`, `glacier_regrowth_capability`, `shared_machinery_ssp_facts`.

---

## 3. FACTS IS RUN — 10 experiments, ~56 s each

`facts/build_shared_climate_nc.py` → `build_shared_configs.py` → `extract_facts_shared_components.py`
→ `outputs/facts_components_shared_n200.csv`. Colima `--cpu 8 --memory 8` (host is 16 GB).

**ssp245 control PASSES**: reproduces the prior calib-1.4.5 run to within 0.5–2.5% on all 8
workflow × horizon cells (`wf1f`@2100 49.8 vs 50.0).

⚠ **A trap killed in the config generator.** The predecessor config
`global.coupling.ssp245.fairv145.noemu` dropped the emulandice MODULES but left `wf1e/wf2e/wf3e`
in the surviving modules' `include_in_workflow`, so FACTS emitted
`total.workflow.wf1e/wf2e/wf3e.global.nc` — **workflow totals with no ice sheets in them**,
indistinguishable by filename from real ones. **Those files still exist in that experiment
directory.** The generator now rejects any workflow outside its declared set.

**Horizon is 2150** (pyear_end), the convention every prior FACTS run used. 2300 is untested for
these modules; MAGICC-SLR still stands alone there.

---

## 4. THE FOUR-SOURCE VAN VUUREN FIGURE (`af0ae17`)

`figures/model_comparison_components_vv_L21_{2100,2150,2300}.png`.
`vv_model_comparison.py` gained the FACTS and MAGICC arms; `plot_model_comparison_components.py`
gained the `--set=` treatment `plot_future_components.py` already had.

**THE RESULT: the peak-and-decline crossover holds in 7/7 model-module totals.** vvHL is above
vvM at 2100 and below it at 2150 in Ladrillo L21, BRICK 2.0, MAGICC-SLR and all four FACTS
workflows. Three share the FaIR driver; **MAGICC computes its own climate from emissions**, which
is what makes the agreement non-circular.

⚠ **The paired MEAN would have inverted this for 2 of 4 FACTS workflows.** MICI/SEJ upper tails
drag it across zero: wf3f's mean is +27.79 cm against a median of −6.30 with 84% of configs
negative, and its t was 4.4. Use the paired median + sign test on tailed differences.
**But `vv_model_comparison.py`'s own path-dependence test deliberately uses the paired MEAN**,
because Ladrillo's AIS median falls into the sparse valley between tipped and untipped modes.
**Two arms, two opposite right answers — check mean against median every time, do not adopt a rule.**

---

## 5. GLACIERS — the question, and TWO corrections to my own answers

### 5.1 Can Ladrillo regrow? NO, structurally

`glaciers_nu3_component.jl:79`: `exc = max(T − T_eq(S), 0)`, and `T_eq(S)` is the INVERSE of
`S_eq(T)`, so `exc > 0` ⟺ `S_eq > S`. The clamp fires precisely and only where regrowth would
occur — a hard ratchet, not damping. 0 of 8000 draws × 7 markers decreases.
(⚠ I first read `glaciers_nu_component.jl`, the SINGLE-reservoir sibling. The shipped module is
the 3-reservoir `glaciers_nu3`; the step function is identical, so the conclusion held — but
read `nu3`.)

MAGICC regrows in **5 of 7** markers; vvLN peaks 11.04 @2144 and falls to 2.46 @2300.

### 5.2 ⚠ CORRECTION — the other comparators are BLIND, not agreeing

I first read BRICK's monotonicity as independent physical agreement (3-to-1 against MAGICC).
Marcus's GSIC point is right and it inverts that: **`gsic_teq = −0.15 °C`, FIXED in
`MimiBRICK.jl:109`, not sampled, BELOW pre-industrial.** The coldest any marker reaches is
**+0.26 °C** — a 0.41 °C margin never approached. And above `teq` the only stationary point is
`S = v₀`: Wigley-Raper's equilibrium **is total loss**. FACTS stops at 2150, before the cooling.

⇒ Three of four models **cannot express regrowth**; one can and does.
[[two_statistics_can_be_blind]].

### 5.3 Not to be confused with the 2100 level

Ladrillo is the lowest glacier arm at 2100 and 2150 in **7/7** markers — **including vvM and vvH,
which never cool and never clamp.** The 2100 lowness is a level/calibration matter, NOT the
ratchet. (At 2300 it is lowest in only 3/7, because MAGICC draws down past it.)

---

## 6. ONE MACHINERY (`591650d`, `facts@0442964f`)

The SSP FACTS arm moved off FACTS-internal FaIR 1.6.4 onto the shared injected driver, so both
scenario sets now run one builder → one config generator → one extractor → one convention.
**emulandice added back for the CONTROLS ONLY** (per-SSP-trained; meaningless on a marker) —
without it, unification would have silently dropped `emuAIS`/`emuGrIS`/`emuglaciers` and the
`e` workflows.

**Comparator move**: FACTS rows only (MAGICC byte-identical), 90/150 literature rows changed,
median **5.8%**, positive at ssp126/245 and negative at ssp585. The superseded frozen arm is
preserved verbatim with that accounting at
`benchmark/reference/_fixed_archive_20260831_facts_internal_fair164/`.

### ⚠ 6.1 A BUG I INTRODUCED AND CAUGHT — read this before touching the configs

Giving every shared module `include_in_workflow: <all workflows for this key>` reads as the safe
default and is **wrong**: `ar5glaciers` must NOT be in the emulandice workflows, because
`emuglaciers` supplies glaciers there. Granting both made `wf1e/wf2e/wf3e` **sum two glacier
modules, +11 cm (+27% at ssp245@2100)**. **Every per-module number stayed correct** — nothing
local looked wrong. It surfaced only because nine `e` cells moved the same way by nearly the same
amount, and was confirmed by the total sitting +10.72 cm above its own component sum.

Two gates now, **both mutation-tested**: `[REFERENCE]` (generated config vs the untouched
`global.coupling.ssp245.n200/config.yml` — external, not self-agreement) and `[COMPOSITION]`
(per-sample `total == Σ modules`, a true identity because FACTS adds the arrays — unlike
`sum of medians == median of total`, which is false unless comonotonic and must never be gated).
**The van Vuuren results were never affected** (markers carry no `e` workflows; verified by
parsed-YAML comparison against the configs the committed results came from).

### ⚠ 6.2 ONE BENCHMARK VERDICT REGRESSED AND WAS NOT ADJUSTED — **OPEN, needs a ruling**

`S / glaciers / ssp585-over-ssp126 / 2150 separation`: **PASS → FAIL**, taking the V block
WARN → FAIL. **L21's own value barely moved (2.0694 → 2.0676).** The COMPARATOR BRACKET narrowed:
the shared driver compresses FACTS' glacier scenario separation (`ar5glaciers` ssp585/ssp126
**2.37 → 1.93** @2150), so `[1.79, 2.37]` became `[1.79, 1.93]` and L21 sits 0.14 outside =
**105% of the bracket's own width**.

My reading: this is like-for-like working. The old PASS compared L21-on-calib-1.6.0 against
FACTS-on-FaIR-1.6.4 and **masked** the finding that on a common climate L21 separates the
scenarios more strongly than either comparator. Net across the benchmark: 25 verdict changes,
**14 improvements** (WARN→PASS 11, FAIL→PASS 3), this one regression. ⚠ The new bracket is **two
points spanning 0.14** — thin evidence either way. **Marcus's call.**

---

## 7. THE GLACIER-REGROWTH SCOPE (`9d5f372`) — the answer changed AGAIN, on numbers

`python/scope_glacier_regrowth.py` → `outputs/scope_glacier_regrowth_L21{,_headroom}.csv`.
**Scoping only; no model file changed.**

Method is a **BOUND, not a counterfactual run**: under any relaxation scheme the stock can only
move toward `S_eq`, so `H = S − S_eq(T)` bounds every cm regrowth could remove, independent of
rate law and asymmetry. A **PORT GATE** checks the reconstruction against the shipped glacier
median first (worst 0.408 cm against half the joint p05–p95 there, 2.696 cm — the tolerance is
DERIVED from the spread the two arms differ by).

* **MAGNITUDE: ≤ 0.23 cm at 2300** removing the clamp entirely (symmetric relaxation, the most
  this law can produce); 0.08 cm at a 3× asymmetry. **At 2100 and 2150 the headroom is EXACTLY
  ZERO on every marker** — the option cannot move any headline number we report.
* **POWER: the clamp DOES bind in the hindcast** for SLOWP and FAST (I expected not) — but
  removing it shifts the in-scope hindcast by **0.0140 cm = 3% of the gsic target's median
  1-sigma**. Active and invisible ([[no_power_null]]). It could not be fitted.
  (R19 binds from 2025 but is OUTSIDE the hindcast scope — `gsic_hind` = SLOWP+FAST, the target
  assumes zero R19 melt — so its binding is not identifiability.)
* ⚠ **IT DOES NOT EXPLAIN THE MAGICC GAP.** MAGICC draws down up to **8.58 cm**; Ladrillo's
  entire headroom is **2.30 cm** and the realisable part **0.23 cm** — **4× and 37× too small**.
  MAGICC's drawdown exceeds our whole equilibrium headroom, so it implies a **far lower S_eq**
  than the Mengel-2016 curve gives us.
* **RECOMMENDATION: do not add regrowth.** The clamp's stated justification IS stale ("only binds
  under strong-cooling scenarios"; it binds on 4 of 7 markers) but the mechanism is worth
  ≤ 0.23 cm. **Fix the comment, not the model.**

⇒ **NEXT SCOPE: the EQUILIBRIUM CURVE** (Mengel-2016 `S_eq = a(1−exp(−b(T−T_off)))`), which is
where the 4× sits. That is also the likely home of the 2100 level gap in §5.3 — the two may be
one finding.

Two defects in the scope script, both caught by its own numbers before anything was read off it:
the counterfactual was rebaselined on its own 1995–2014 mean while R19 binds inside that window
(folding a baseline shift into the difference, producing positive deltas where headroom was
exactly zero), and the identifiability test asked whether ANY block binds in the hindcast when
the hindcast scope excludes R19.

---

## 8. OPEN ITEMS

1. **The §6.2 benchmark regression** — needs a ruling, not more analysis.
2. **Scope the glacier EQUILIBRIUM curve** (§7). The 4× headroom gap and the 2100 level gap are
   probably the same finding.
3. **Verify Nauels 2025 vs 2017 glacier module** — inherited, still open, and now load-bearing:
   it is the one claim behind "MAGICC has no clamp".
4. **Push, or decide not to** — three repos, nothing pushed; `slr-refresh` is the sensitive one.
5. **Fix the stale clamp comment** in `glaciers_nu3_component.jl` (§7) — a one-line change,
   deliberately not made here because the scope's job was to price the option, not edit the model.
6. Inherited and untouched from `31c`/`31d`: the `ais@2300` CONTROL exceedance; the hindcast
   driver-file mismatch; `plot_ladrillo_memo_figures.py` SystemExit on `--tag=L21`;
   `scope_ladrillo_vs_brick20_scorecard.py` has no L21 run; `plot_ssps_gsic_wr_vs_mengel.py`
   still carries the extA108 arms.
7. **The phantom `wf*e` files** in `experiments/global.coupling.ssp245.fairv145.noemu/output/`
   (§3) are still on disk and still look like real workflow totals.

## 9. NON-OBVIOUS STATE

* **Colima is running** (8 GB). `colima stop` to reclaim it.
* The FACTS image has **pip neutered** (`exit 0`) in `docker/Dockerfile` — required, because
  FACTS' per-task `pip install --upgrade pip` races and corrupts the shared `/factsVe` venv.
* FACTS runs need `--user root`; virtiofs maps outputs back to the host user.
* `outputs/facts_components_shared_n200.csv` is the live FACTS arm for **both** scenario sets.
* Input `*.nc` under `experiments/global.shared.*/input/` are **gitignored** — regenerate with
  `python3 build_shared_climate_nc.py --all`.
