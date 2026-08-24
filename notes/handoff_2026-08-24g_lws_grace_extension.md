# Handoff — LWS is extended with GRACE, the fiat turned out to be right, and the curvature arc still has no error bars

**Start here.** Repo `SLR-RFF-BRICK`, branch `ladrillo-dev`, commits **`306b348`** (the
error-bar diagnostic), **`28240c7`** / **`d219b76`** (its CHANGELOG + handoff), **`d2e23d3`**
(the LWS extension), and the CHANGELOG entry `2026-08-24n`. Written 2026-08-24, to be picked up
cold. **Continues** `handoff_2026-08-24f_curvature_has_no_error_bar.md`, whose §9 open items
**1 (the model's own deficits) is unchanged and still top**, and whose LWS thread is now closed.

**No chains were read this whole session.** Everything here is target-side.

---

## 0. THE ONE-PARAGRAPH VERSION

Two things happened, and the second corrects the first. **(1)** The post-splice curvature
halving was priced: LWS's hold-flat fiat was charged **52.3%** of the drop, and — more
importantly — **nothing in the curvature arc has ever carried an error bar**, so the 1.3%
budget closure (0.02 σ, bar = **78%** of the value being closed), the 1.83× reconstruction gap
(**0.97 σ**) and the halving itself (**1.78 σ**) are all **unresolved**. **(2)** Marcus then
asked where the LWS observations end, which led to fetching the JPL mascons and building a real
LWS series — and **the real data says the fiat was not an artifact at all**: GRACE differs from
the hold by **mean +0.018 cm**, and swapping it in moves the halving only **0.492 → 0.498**. The
halving is essentially **all real**, my extrapolation arms were **wrong**, and the 1.78 σ verdict
stands.

---

## 1. WHAT WAS BUILT

* `python/diag_curvature_postsplice_halving.py` — 8 blocks, 3 gates, ~4 s, no chains.
  Outputs `outputs/diag_curvature_postsplice_{decomp,arms,windows,recon,sweep,se}_L14.csv`.
* `python/build_lws_grace_extension.py` — the LWS extension, ~40 s.
  Outputs `outputs/lws_grace_extension_L14.{csv,png}` and its log.
* **New data on disk:** `data/observations/raw/GRCTellus.JPL.200204_202606.GLO.RL06.3M.MSCNv04CRI.nc`
  (JPL GRACE/GRACE-FO mascon RL06.3Mv04 CRI, **doi 10.5067/TEMSC-3JC634**, 44 MB) and
  `data/observations/raw/glambie_calendar_years/` (unzipped from `glambie_data.zip`).
* **New dependency:** `pyshp` in `~/climate-env` (pure Python, reads the GTN-G shapefile).

---

## 2. THE HEADLINE THAT SURVIVES — the curvature estimator is underpowered

AR(1)-inflated OLS se of 2·b₂, validated against a matched Monte Carlo and **required to be
conservative** (1.03–1.22×). It is a **lower bound** — it counts only scatter about the quadratic,
not the reconstructions' published bands.

| claim the arc rests on | difference | σ | verdict |
|---|---|---|---|
| "the components close on their own total to **1.3%**" | −0.000096 ± 0.005598 | **0.02** | bar is **78%** of the value being closed |
| "Dangendorf is **1.83×** Frederikse" | +0.006066 ± 0.006269 | **0.97** | UNRESOLVED |
| "our sum falls short of Dangendorf" | −0.006162 ± 0.004689 | **1.31** | UNRESOLVED |
| the **halving** (nested-window null) | +0.003655 | **1.78** (p 0.073) | not resolved |

And **"1.83×" does not survive its own window**: sweeping start years over windows ending 2018,
the ratio spans **0.53–1.53**, the difference changes sign, and **Dangendorf is LOWER in 10 of 13
windows**. Frederikse's *total* carries **2.8×** the year-to-year scatter of either smooth series
(first-difference sd 0.674 vs 0.244 / 0.252 cm), so its 26-yr quadratic swings **3.7×** on the
start year — the 1.83× sat on a spike in its **denominator**.

⚠ **The shipped window label was also wrong:** 0.003533 is **1993–2023**, not 1993–2024. `gsic`
ends 2023, so the five-component sum has **no 2024 value at all**.

---

## 3. THE CORRECTION — the LWS fiat was not an artifact

**Where the observations end:** the Frederikse ensemble is **1900–2018** for every variable, TWS
included. `prep_recalib_targets_ext.py:311` then holds `lws`, `lws_lo`, `lws_hi` at their 2018
values (**0.5324 cm, σ 0.2016**) through 2026. **LWS was the only component with no modern
extension.**

**Why it is not cosmetic:** LWS enters the likelihood **twice**, both on the total stream —
`calibrate_mcmc_ext.jl:1387` adds **observed** LWS to the **modelled** total (the model has no
land-water component) and `:568` folds its band into the total's observation σ. So 2019+ was told,
as data, that land water storage contributed exactly zero, **with a real-data error bar**.

**What GRACE says:**

| year | GRACE | fiat | diff |
|---|---|---|---|
| 2019 | 0.656 | 0.532 | +0.123 |
| 2020 | 0.428 | 0.532 | −0.105 |
| 2021 | 0.513 | 0.532 | −0.020 |
| 2022 | 0.506 | 0.532 | −0.026 |
| 2023 | 0.601 | 0.532 | +0.069 |

**mean +0.018 cm, sd 0.076, max 0.123.** The halving moves **0.492 → 0.498**.

⇒ **"LWS is charged 52.3% of the drop" was arithmetically right and causally misleading.** Its
acceleration does collapse (+0.001925 → +0.000058 over 1993–2023) — but it does that with the
**real** data too. **The halving is essentially all real.**
⇒ **My linear/quadratic continuation arms (+0.19 to +0.35 cm by 2024) were WRONG.** Two
parametric extrapolations agreed with each other and both missed. `use real data when you have it`.
⇒ **What extending buys:** the fiat leaves the likelihood; the frozen σ can become a real GRACE
uncertainty; and the **interannual variance** the hold removed (sd 0.076 cm) is restored — the part
a last-window quadratic is most sensitive to.

---

## 4. THE RECIPE, AND EVERY TRAP IN IT

**LWS = (GRACE land mass, both ice sheets masked) − (GlaMBIE glaciers, 17 regions).**

* **Everything is inside the one netCDF** — `land_mask`, `scale_factor`, `mascon_ID`,
  `uncertainty`. The catalog's "provided in the same directory" wording is **stale for v04**; no
  second download is needed.
* ⚠ **1 cm over 1 km² = 1e-5 Gt**, not 1e-8. The wrong factor made the Greenland gate read
  **0.0010** — a clean 1/1000 tell. *A −0.26 Gt/yr trend against a published −257 is a bug.*
* ⚠ **The GTN-G "Antarctic Mainland" polygon misses 398 land cells** (Ross/Ronne margins) worth
  **−28.9 Gt/yr = 22%** of the Antarctic trend. Sweep with `lat < −60` as well.
* ⚠ **GTN-G o1 files are REGION outlines, not glacier outlines.** Region 16 "Low Latitudes" spans
  a **134 Mkm² bbox for 1770 km²** of glacier (75000:1); region 10, 41 Mkm² for 2270 km².
  **Glaciers cannot be masked spatially at all** without RGI glacier outlines — this killed the
  `-24f` "mask the 10 resolvable regions, subtract GlaMBIE for the 9 small ones" hybrid.
* **Scope:** all **19** RGI regions lose mass 2019–2023, so Marcus's "exclude any region with
  loss" rule resolves to *mask all glaciers* — the exempt set is **empty**. Region **5** is inside
  the Greenland mask, region **19** has **zero** land cells at 0.5°, so exactly **17** are
  subtracted. No double-count, no gap.
* ⚠ **Deseasonalise before annual means.** 2011–2018 have as few as **5 months**; a raw annual
  mean there averages the wrong *seasons*. Two harmonics remove a **5943 Gt** peak-to-peak cycle
  and restore the overlap from 7 yrs to **16**.
* ⚠ **The 0.022 cm overlap rms is NOT an independent validation.** Frederikse's natural-TWS term
  comes from a **GRACE-calibrated** reconstruction, so the two share a source over 2003–2018. Read
  it as *"the splice introduces no discontinuity"*, nothing more.
* `scale_factor` is **NaN over 100% of both ice sheets** and **0% of land 60S–60N** — the gain
  factors are defined exactly where hydrology lives and cannot leak onto ice. **Not applied** in
  the shipped build; available if sub-mascon recovery is ever wanted.
* **GIA:** the mascon solution removes it with **ICE-6G_D (Peltier et al. 2017)**. ⚠ **Whether
  that matches Frederikse's convention has NOT been checked** — open, and it would bias the
  post-2018 trend if they differ.

**Gates, all passing and all worth keeping:** `[GRL]` the Greenland mask reproduces **JPL's own
published series from the same solution** at **1.0038** (rms 11.1 Gt); `[ANT]` **1.0036** (rms 7.3);
`[AREA]` the grid sums to the Earth's area; `[SCOPE]` region 19 contributes zero land cells;
`[SEAS]` reports the removed cycle.

---

## 5. DECISIONS TAKEN (Marcus, 2026-08-24)

* **2024 is held flat from 2023** — GlaMBIE ends 2023. **One** fiat year, against six.
* **No recalibration yet** — *"wait until we have something else worth recalibrating."*
  ⚠ **`outputs/recalib_targets_ext.csv` is UNCHANGED and the calibration still sees the fiat.**
  A pointer comment now sits at `prep_recalib_targets_ext.py`'s hold-flat block so the next person
  finds the ready replacement. **When it is wired, `lws_lo`/`lws_hi` must be replaced at the same
  time** — they are frozen too, so the fit currently carries a fiat value with a real-data error bar.
* The mixing decision (score components on Frederikse's own total, or move them to Dangendorf) is
  **still open and still Marcus's**, but §2 **demotes it from blocking**: at these window lengths
  the estimator does not resolve the differences either way.

---

## 6. NON-OBVIOUS STATE

* `build_lws_grace_extension.py` **deliberately does not read or write the target file.** If you
  wire it in, do it in `prep_recalib_targets_ext.py`, not here.
* The `_SMOKE` / `_CTRLONLY` suffix traps from `-24e` §7 and `-24d` §4 still apply to the AIS
  diagnostics; nothing in this session used them.
* `diag_curvature_postsplice_halving.py`'s estimator **NaNs on any missing value in the window,
  deliberately** — that is what exposed the 2024 label. Do not "fix" it to skip NaNs.
* `SE_MC_SEED = 2026` / `SE_MC_N = 20000` are **gate parameters**, not tuning knobs.
* The `[7]` contrasts add the two ses **in quadrature**, i.e. treat the reconstructions as
  independent; a shared-method correlation would only **shrink** the bar (`shared_method_error`).
* Every trap in `-24f` §8, `-24e` §7, `-24d` §4, `-24c` §4 and `-24b` §3 still applies.

---

## 7. OPEN, IN PRIORITY ORDER

1. **Re-measure the model's own deficits WITH an error bar** (unchanged from `-24f`, still top).
   The **0.65×** (gis), **0.727×** (ais) and **0.571×** (total) started the whole arc and their
   point values sit *inside* §2's bars. If they are 1 σ effects the conclusion changes from
   "explained by the reconstruction gap" to "never measurable". Needs a chain read;
   `diag_curvature_deficit_2x2.jl` already produces the ensemble.
2. **The GIA convention check** — ICE-6G_D on the GRACE side vs whatever Frederikse used. Cheap
   (their Methods are in `~/Documents/2026/ClaudeDocs/Papers/Frederikse.2020.s41586-020-2591-3.pdf`)
   and it gates the post-2018 LWS trend.
3. **The reconstruction mixing** — real, no longer blocking, Marcus's call.
4. **The anchored net's counterintuitive sign** at ssp585 @2300 (`-24e` §8 item 2) — contrast
   0.249, unexplained. The per-draw table is on disk; joining parameters needs a cheap column-only
   chain extraction, **not** the 12-min diagnostic read.
5. **Widen the hindcast-vs-projection independence measurement** to the whole `S.ais` 1900–2018
   stream (`-24e` §8 item 3). Needs model runs.
6. **Re-read the other shipped Antarctic headlines at 2100/2150** (`-24e` §8 item 4), in particular
   `UNRESOLVED_AMPLIFICATION`'s λ = 0.014280.
7. **The AIS observed driver**, **FrEDI linearity**, **Marcus's prose** — unchanged.

---

## 8. FILES AND COMMITS

**New:** `python/diag_curvature_postsplice_halving.py`, `python/build_lws_grace_extension.py`,
`outputs/diag_curvature_postsplice_*_L14.csv`, `outputs/lws_grace_extension_L14.{csv,png}`,
two logs, the mascon netCDF and `glambie_calendar_years/`.
**Modified:** `CHANGELOG.md` (`2026-08-24m`, `2026-08-24n`), `python/prep_recalib_targets_ext.py`
(a pointer comment only — no code change).
**Memories:** `curvature_needs_an_error_bar` (working convention, in the root index),
`postsplice_halving_priced` (written, then **corrected** by the real data — its description now
leads with the correction), `curvature_deficit_is_recon_gap` **revised** with a CORRECTION section;
`INDEX_slr.md` line rewritten in place and `MEMORY.md` extended.
**Commits:** `306b348`, `28240c7`, `d219b76`, `d2e23d3`, the `2026-08-24n` CHANGELOG commit, and
this note.
