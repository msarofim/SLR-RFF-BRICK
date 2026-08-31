# Handoff — the glacier gap is a CLIMATE gap, the separation verdict is directional, and the one analysis that would settle the rest

**Start here.** Repo `SLR-RFF-BRICK`, branch `ladrillo-dev`, HEAD **`bf43043`**, **PUSHED** (this
is the first push in this arc — `origin/ladrillo-dev` is level). Written 2026-08-31, continuing
`handoff_2026-08-31e_shared_machinery_and_glaciers.md`.

⚠ **STILL THREE REPOS, and only one is pushed — on Marcus's instruction.**

| what | where | branch | state |
|---|---|---|---|
| figures, tables, scopes, benchmark, this note | `SLR-RFF-BRICK/` | `ladrillo-dev` | clean, **PUSHED** |
| FACTS climate builder, configs, extractor, 10 experiments | `~/.../CodeProjects/facts/` | `slr-comparison-arm` | 3 ahead of `main`, **local by instruction** |
| MAGICC vv emissions builder + frozen run notebook | `~/.../MAGICC/slr-refresh/` | `vv-slr-runs` | 1 ahead of `main`, **local by instruction** |

**Marcus 2026-08-31: "Push Ladrillo. Don't push anything to shared repos with MAGICC or Nauels
GitLab."** That is a standing instruction, not a one-off — do not push `facts` or `slr-refresh`
without asking again.

---

## 1. What was asked, in order

1. Read `31e` and continue. → §2 (the equilibrium scope), §4 (the clamp comment).
2. Ruling on the §6.2 benchmark regression. → §3. **The GATE was wrong, not the number.**
3. Ruling on pushing. → above.
4. *"Are there any findings that are actually relevant to Nauels or MAGICC beyond our
   workstream?"* → §5. **One, clearly; one weaker.**
5. *"Consider a separate analysis that is MAGICC-climate used for both Ladrillo and
   MAGICC-slr."* → **§6. This is the next piece of work and it is mostly a PORT, not a build.**

---

## 2. THE EQUILIBRIUM SCOPE (`df7ecb4`, corrected by `f24821c`)

`python/scope_glacier_equilibrium.py` (+ `python/extract_magicc_vv_gmst.py`) →
`outputs/scope_glacier_equilibrium_L21{,_ladder}.csv`, `outputs/log_scope_glacier_equilibrium.txt`.
**Scoping only; no model file changed.**

`31e` handed forward a guess: that MAGICC's 8.5 cm glacier drawdown and Ladrillo's low 2100
glacier level were **one finding in the Mengel-2016 equilibrium curve**. **Neither half survives,
and the curve is not implicated in either.**

### 2.1 ⚠ THE COMPARISON WAS NEVER LIKE-FOR-LIKE — this is the load-bearing finding

Every earlier statement compared Ladrillo at **FaIR's** temperature against MAGICC at **MAGICC's**.
MAGICC-SLR computes its own climate from the van Vuuren emissions — the very property that makes
its agreement with the three FaIR-driven arms non-circular — so a module difference and a driving
temperature difference were confounded. `like_for_like_forcing`, and it had inverted the reading.

**MAGICC is 0.38–0.93 K COLDER at 2300 on all four DECLINING markers.** At vvLN the two ensembles'
5–95 % ranges **do not overlap** (MAGICC −0.67 [−1.25, −0.30] vs FaIR +0.25 [0.03, 0.65]). The two
models agree closely through ~2050 and separate only on the decline — i.e. exactly where the
markers are interesting.

> ⚠ **TWO FaIR STATISTICS, AND THEY ARE NOT INTERCHANGEABLE.** My first version of this table used
> `fair_mean_gmst_*.csv` — the MEAN-CONFIG trajectory, which is what actually drives the module —
> against MAGICC's 600-member ensemble MEDIAN. They differ by up to 0.4 K and on the RISING
> markers the SIGN of the difference flips between them (vvH: −0.12 on mean-config, **+0.27** on
> ensemble medians). **"Colder on all seven markers" is WITHDRAWN.** §1 of the script now prints
> both columns with each model's own 5–95 % band and claims no direction on the rising markers.

### 2.2 The controlled swap, and what it does

`scope_glacier_regrowth.build_drivers` gained a **`gmst_override`** hook so Ladrillo's *unchanged*
glacier module runs on another model's climate — one axis, same posterior, same law, same clamp,
same draws. cm at 2300:

| | FaIR climate | MAGICC climate |
|---|---|---|
| worst headroom `H = S − S_eq` | 2.40 | **16.28** (6.8×) |
| same, `S_eq` floored at pre-industrial | 2.40 | **9.97** |
| realisable regrowth at R = 1 | 0.24 | **2.94** |

Floored, the bound **covers MAGICC's own drawdown on the two largest markers** (vvLN 9.97 vs 8.54;
vvML 6.57 vs 6.25) and falls short on vvVL, vvL, vvHL. So `31e`'s "4× too small" was an artefact of
the two temperatures. **What remains is a RATE gap**: R = 1 (symmetric relaxation, the fastest this
law allows) delivers 34 % of MAGICC's drawdown, and matching it needs regrowth *faster than melt*,
which a shared-κ form cannot express at any asymmetry. Structural, not miscalibrated.

> ⚠ **`S_eq` GOES NEGATIVE BELOW `T_off`** — 48 % of block × draw cells at vvLN/2300 on MAGICC's
> climate — i.e. equilibrium *below* the 1850 state. The exponential permits it; the GlacierMIP3
> rungs start at +1.2 K and say nothing about it. **Both bounds are reported and only the FLOORED
> one is used to argue.** Anyone extending this must keep that discipline.

### 2.3 The curve is HIGH against its own external anchor, not low

First check of the committed ladder on the **POSTERIOR** — the `d1d_fourrung_seam` four-rung fit
only set priors, and the MCMC moved things a long way (SLOWP `T_off` 0.34 → −1.65). % of
2020-remaining volume:

| rung | posterior [p05, p95] | GlacierMIP3 central | likely range | |
|---|---|---|---|---|
| +1.2 K | **49.3** [38.4, 61.9] | 37.4 | [11.8, 54.0] | inside |
| +1.5 K | **57.0** [45.5, 68.3] | 46.3 | [17.2, 63.2] | inside |
| +2.0 K | **66.9** [54.8, 76.8] | 63.0 | [41.5, 75.5] | inside |
| +3.0 K | **80.0** [68.5, 87.5] | 75.5 | [58.5, 83.9] | inside |

**0 of 4 outside**, and above the central at every rung. The `as_run` frame (adding the shipped
driver offset to the d1d `T_b = amp_b·L` convention) changes it by ≤ 0.4 pct-pt. **Lowering `S_eq`
is not indicated by the anchor.**

### 2.4 The 2100 level is RATE-limited

Saturation `S/S_eq` at 2100 = **0.53–0.57** on all seven markers; the instant-equilibrium ceiling —
where L21 would sit at 2100 if the rate were infinite — is **11.0–13.6 cm above** the shipped
median, against a largest comparator gap of **4.31 cm**. Three times more room in the approach than
the gap needs, so the curve cannot be what holds 2100 down. Independent cross-check: the
single-reservoir Mengel arm reported 62 % realised-of-committed at 2100 on a different structure
(`outputs/mengel_hightemp_melt_summary.md`).

⇒ **Both gaps live in (κ, ν), not (a, b, T_off), and they remain TWO findings, not one.**

### 2.5 Extrapolation is at the COLD end

The rungs span 1.2–3.0 K. **51 % of vvLN's FaIR projection years (64 % of its MAGICC ones) sit
BELOW 1.2 K.** The drawdown question lives almost entirely outside the span the curve was fitted
on. vvM/vvH sit 69–78 % *above* 3.0 K.

### 2.6 Gates — one earned itself immediately

* **`[SPLICE]`** is an **identity** bound (1e-9 cm) because the re-anchored override leaves the two
  arms bit-identical through `last_obs`. Its first version substituted the GMST **level** and fired
  at **0.137 cm** — a pre-1850 frame offset leaking through the projection formula into a
  comparison meant to be about the future. Fixed by transplanting the **anomaly**, re-anchored on
  the FaIR 2014–2024 mean. ⚠ **Anyone reusing `gmst_override` must know it transplants the ANOMALY,
  not the LEVEL** — see §6.3 for when that is the wrong choice.
* **`[DRAWDOWN]`** recomputes MAGICC's drawdown from the comparison table and asserts it against
  the recorded 8.58 cm, so a stale constant cannot pass as agreement. Bound 0.10 cm = the horizon
  grid's own discretisation (the record is the path peak at 2144; the table has 2100/2150/2300).
* **Coverage counting excludes markers with no drawdown.** Counting them turned 2-of-5 into
  4-of-7 — a pass manufactured out of cells the question does not apply to.

---

## 3. THE BENCHMARK RULING — the GATE was mis-specified (`bf43043`)

**Marcus:** *"I'm okay with L21 having a wider future range than FACTS: that's not a failure the
way that not matching observations or having a non-physical trend would be."*

Implemented in `bench_ladrillo.block_separation` rather than annotated around it. The verdict is
now **DIRECTIONAL**:

* **above** every comparator → **`CHECK(wide)`**, ranked with the passes in the [V] roll-up and
  given its own list in the run summary (a three-valued verdict that only prints on FAIL hides its
  middle value — `gate_bound_matches_its_claim`);
* **below** every comparator → **keeps FAIL**, because under-responding to a forcing change *is*
  the direction the comparators contradict.
* The exceedance now prints **the bracket's own width** beside it, since it can be thinner than the
  miss: this cell is 0.14 outside a two-point bracket spanning 0.14.

**Mutation-tested on the real function** (`joint_stats` stubbed per frame, `block_separation`
called for real — not a retyped copy of the verdict expression): 2.068 → `CHECK(wide)` rank 0,
1.86 → `PASS`, **1.20 → `FAIL` rank 2.** The glaciers V block is non-failing again and the 14
improvements from the machinery unification stand.

---

## 4. THE STALE CLAMP COMMENT IS FIXED (`31e` open item 5)

`julia/glaciers_nu_component.jl` no longer says the clamp "only binds under strong-cooling
scenarios". It binds on 4 of 7 markers and in the hindcast, and is now justified on **PRICE**
(≤ 0.24 cm at 2300 on our forcing, exactly 0 at 2100/2150; ~10 cm on MAGICC's, so the price is a
statement about our forcing, not about the law). `glaciers_nu3_component.jl` — the **shipped**
module — now points at that block explicitly, since it carries no conventions of its own and
reading `nu` instead of `nu3` is a mistake I already made once.

---

## 5. WHAT IS WORTH TELLING NAUELS / MAGICC (Marcus's question)

**One, clearly: MAGICC-SLR is ULP-SENSITIVE at ssp585.** A 1e-16 relative change in ONE emissions
cell (ssp585's CO₂ FFI at 2130) moves SLR by ~1e-5 relative on all 600 members — a ~1e11
amplification, and the signature is a **threshold crossing flipping for some members**, not smooth
error propagation. ssp126 and ssp245 were bit-identical under the same scmdata round-trip (0 of
3.3 M cells). That is a reproducibility property of *their* model and would matter to anyone
re-running their published numbers. ⚠ **It needs a minimal reproducer before being sent** — the
evidence currently sits inside our control run and the diagnosis (threshold crossing) is ours.

**One weaker: the decline-phase cooling.** §2.1 — 0.38–0.93 K colder than FaIR calib 1.6.0 at 2300
on the declining markers, disjoint 5–95 % at vvLN. That is a comparison observation, not a defect,
and it cuts both ways: **nothing here says which model is right.** It is worth raising only
alongside a reason to think one of them is.

**Not worth sending:** the two "MAGICC NaN forcing" incidents were our builder (unioned time axes
+ a sparse reference file), and the glacier-regrowth capability finding is about *our* clamp.

**Still open and relevant to them:** whether the Nauels **2025** glacier module differs from the
**2017** one — inherited from `31d`, still unverified, and it is the single claim behind "MAGICC
has no clamp". If that turns out false, §2.2's whole framing changes.

---

## 6. ⭐ THE NEXT ANALYSIS: MAGICC'S CLIMATE FOR BOTH ARMS

Marcus's suggestion, and it is the right one — §2 only swapped the climate for the **glacier
module's bound**. The same swap for the **whole model** would separate the module axis from the
climate axis for *every* component at once. **Most of the machinery already exists.**

### 6.1 It is a PORT, not a build

* `ladrillo_setup(; gmst=, ohc=)` **already accepts an injected climate** — the docstring says so
  in as many words ("that is how the MAGICC-hybrid and per-member arms inject their own climate").
* There is a **full precedent**: `julia/project_magicc_hybrid_ssp245_mengel.jl` — the off-diagonal
  cell of a climate × SLR-emulator 2 × 2, per-member MAGICC GSAT + OHC, random pairing (valid
  because the MAGICC and BRICK posteriors are independent calibrations), fixed seed so the
  parameter draws line up with the matched run. It is **BRICK-Mengel on ssp245 only**.
* The wide per-member CSVs are built by
  `FaIRtoFrEDI/magicc_comparison/magicc_to_wide.py` → `processed/magicc_{gmst,ohc}_ssp245_wide*.csv`.
  It already reads exactly this source format and both variables (verified 2026-08-31).
  ⚠ **Only ssp245 exists**, and from an OLDER source file. The 2026-08-31 run
  (`VVandSSPs_Nauels2025_withOCH_2026_08_31_073153.csv`, 477 MB) carries all 10 scenarios and both
  variables — `Surface Air Temperature Change` and `Heat Content|Ocean`.

⇒ **The work is: (a) run the wide-CSV builder on the new source for 7 markers + 3 SSPs; (b) port
Track C from BRICK-Mengel/ssp245 to Ladrillo L21 / van Vuuren.** Not a new model.

### 6.2 What it would settle, and what it would not

**Would settle.** Whether the Ladrillo-vs-MAGICC differences at 2150/2300 in **TE, Greenland,
Antarctica and the total** are module differences or the same climate difference §2.1 found in the
glaciers — and MAGICC's colder decline should move TE and GIS too, so this is not a glacier-only
question. It would also re-test the **vvHL-vs-vvM crossover** with the climate axis held, which is
currently the arc's headline result and rests on 7/7 agreement across two climates.

**Would NOT settle.** Which climate is right. It isolates the axis; it does not adjudicate it.

**The reverse arm is IMPOSSIBLE without a hack** (say this explicitly, per
`runnable_is_not_undrivable`): MAGICC-SLR is *inside* MAGICC and consumes MAGICC's own climate
module. There is no supported way to inject FaIR's GMST into it. So the comparison can only be run
on MAGICC's climate, never on FaIR's for all four.

**BRICK 2.0 and FACTS can come along.** Both already take injected drivers — FACTS through
`build_shared_climate_nc.py`, BRICK 2.0 through `set_forcing!(m, gmst, ohc)` as used by
`scope_slr_fairunc_oldbrick.jl` (both verified 2026-08-31, not assumed). Running all four on
MAGICC's climate would make the set 4-on-1 the other way, and **the difference between the two
views is the climate axis, measured.** That is the version worth doing if the budget is there.

### 6.3 ⚠ THE DESIGN DECISION THAT MUST BE MADE FIRST — and it is not the one §2 made

There are two defensible ways to inject MAGICC's climate, and **§2's choice is not automatically
right for a full run**:

| | (a) **SPLICED** — obs history + MAGICC future anomaly | (b) **RAW** — MAGICC's own full path, rebased 1850-1900 |
|---|---|---|
| consistent with | our shared climate-driver convention (`build_shared_climate_nc.py`: `y ≤ 2014` untouched, uncertainty enters the FUTURE only) — and with §2's `gmst_override` | what MAGICC-SLR **actually saw** |
| hindcast | preserved exactly; the calibrated fit still holds | **broken** — Ladrillo is calibrated against observations, not against MAGICC's history |
| isolates | the future climate axis | the whole climate axis, history included |
| precedent | the FACTS/BRICK/Ladrillo shared convention | `project_magicc_hybrid_ssp245_mengel.jl` (Track C) uses this |

**Recommendation: run (a) as primary and (b) as a check**, and report the difference between them —
it is the size of the history disagreement, which nobody has measured. ⚠ Do NOT silently pick one:
this is exactly the class of methodological choice that is supposed to be flagged and awaited.

### 6.4 Other things to settle before running

* **Pairing.** 600 MAGICC members cannot pair with 841 FaIR configs. Track C's answer — sample
  members with replacement against the posterior draws, fixed seed — is valid *because the
  calibrations are independent*, and it is the honest analogue of the existing joint band. Reuse
  it; do not invent a second scheme.
* **⚠ OHC UNITS — a factor of 10, already defused on the consumer side but NOT in the builder.**
  MAGICC reports `Heat Content|Ocean` in **ZJ = 1e21 J**; BRICK/Ladrillo's `set_forcing!` wants
  **`ohc_1e22J`**. `project_magicc_hybrid_ssp245_mengel.jl` gets this right — `ZJ_TO_1E22J = 0.1`,
  with a note that the slr-refresh memory claim "1e22 J = ZJ" was wrong — but
  `magicc_to_wide.py`'s docstring still said the wide CSVs were "already BRICK's ohc_1e22J
  convention", which is false. **Corrected 2026-08-31 in `FaIRtoFrEDI/magicc_comparison/
  magicc_to_wide.py` (uncommitted — that repo was not part of this session's commits).**
  Magnitude check at vvM: MAGICC ZJ is **7.7–11.3×** the FaIR `ohc_1e22J` value — the factor of 10
  PLUS a real, horizon-growing difference in ocean heat uptake (11.3× @2020 → 7.7× @2300). ⚠ That
  drift means **the ratio cannot be used to infer the unit**; scale by 0.1 because ZJ is 1e21 J,
  not by whatever closes the gap.
* **OHC baseline.** Track C verified that a constant OHC offset cancels (the TE module
  re-references SLR to 1995–2014; `--ohc rel1750` and `rel1850` gave identical SLR). **Re-verify
  rather than inherit** — it was checked on BRICK-Mengel, not on Ladrillo L21.
* **Band basis string.** Any new arm must declare a `band_basis` that
  `ladrillo_figs.band_is_comparable` recognises, or it will raise — by design.
* **Horizon.** 2300 (`end_year_2300`). MAGICC covers 2000–2300 for SLR and carries GMST from 1750,
  so the axis is fine; the FaIR marker files run to 2301 and the last year is never read by the
  recurrence (see the `load_magicc_gmst` note in `scope_glacier_equilibrium.py`).

---

## 7. OPEN ITEMS

1. **⭐ §6 — the MAGICC-climate arm for the whole model.** Scoped above; decide 6.3 first.
2. **Verify Nauels 2025 vs 2017 glacier module** — inherited from `31d`, still open, and now the
   single claim behind "MAGICC has no clamp" (§5).
3. **Is MAGICC's colder decline right?** A climate question that is now carrying a glacier
   conclusion. Needs its own check against the calib 1.6.0 forcing.
4. **The κ/ν scope** — §2.4 says both glacier gaps live there. Not started.
5. **The phantom `wf*e` files** in `facts/experiments/global.coupling.ssp245.fairv145.noemu/output/`
   are still on disk and still look like real workflow totals (`31e` item 7).
6. Inherited and untouched: the `ais@2300` CONTROL exceedance; the hindcast driver-file mismatch;
   `plot_ladrillo_memo_figures.py` SystemExit on `--tag=L21`;
   `scope_ladrillo_vs_brick20_scorecard.py` has no L21 run; `plot_ssps_gsic_wr_vs_mengel.py` still
   carries the extA108 arms.

## 8. NON-OBVIOUS STATE

* **Colima may still be running** (8 GB) from the FACTS work. `colima stop` to reclaim it.
* `data/comparison/magicc_gmst_vv.csv` is **new and committed** — MAGICC's own GMST, K rel
  1850-1900, 10 scenarios. `extract_magicc_vv_gmst.py` caches it; pass `--force` to rebuild
  (it reads the 477 MB source, ~1 min).
* `python/scope_glacier_equilibrium.py` **imports** `scope_glacier_regrowth` for the drivers, the
  recurrence and the port gate — deliberately, so the two scopes cannot drift. Editing
  `build_drivers` changes both.
* `MEMORY.md` is **15.0 KB against a 12 KB soft budget** (hard 18 KB). Over soft, not over hard —
  merge when convenient.
* Memories written/updated this session: `magicc_colder_than_fair_2300` (new),
  `glacier_gap_is_rate_not_curve` (new), `glacier_regrowth_capability` (**amended** — its
  attribution was superseded within a day), `shared_machinery_ssp_facts` (ruling recorded, and its
  `description:` frontmatter refreshed, which is the field recall actually reads),
  `INDEX_cmp.md` + `MEMORY.md` pointers.
