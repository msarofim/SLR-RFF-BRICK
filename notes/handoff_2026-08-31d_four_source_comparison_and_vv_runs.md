# Handoff — the four-source component figure, the joint-band correction, and the van Vuuren runs

**Start here.** Repo `SLR-RFF-BRICK`, branch `ladrillo-dev`. Written 2026-08-31, continuing
`handoff_2026-08-31c_ladrillo_figure_suite.md`. HEAD = `6807d5b`.

⚠ **THIS SESSION SPANS THREE REPOS.** Code lives with the model it drives:
| what | where |
|---|---|
| the figure, the comparison table, this note | `SLR-RFF-BRICK/` |
| the FACTS climate builder + 10 experiment dirs | `~/Documents/2026/CodeProjects/facts/` |
| the MAGICC emissions builder + frozen run notebook | `~/Documents/2026/CodeProjects/MAGICC/slr-refresh/` |
Only the first is committed. **The other two repos have UNCOMMITTED new files** — see §6.

---

## 1. What was asked, in order

1. Generate SLR-by-component figures at 2100 / 2150 / 2300 across Ladrillo L21, BRICK 2.0,
   FACTS and MAGICC. → §2
2. *"Didn't we try making a version of Ladrillo L21 and BRICK to make them comparable to the
   uncertainty in MAGICC and FACTS?"* → §3. **I was wrong; the correction is the main result.**
3. *"Is it possible to make MAGICC and FACTS analyses for the van Vuuren scenarios too?"* → §4.
4. *"Start the vv runs, and update with a shared climate-driver convention."* → §5.
5. *"Can't we run MAGICC (and FACTS) on the van Vuuren emissions throughout? Why do we need
   the SSP emissions?"* → §5.2. **Also right; it dissolved a problem I had just raised.**
6. *"Are the Ladrillo GSIC and Greenland formulations unique?"* → §7. **Glaciers: NO.**
7. *"Always consider whether Torch is a reasonable alternative."* → standing, saved to memory
   as `consider_torch_first`; verdict for these two jobs in §8.

---

## 2. THE FIGURE (`1f12c0d`, `360d5da`)

`python/plot_model_comparison_components.py` → `figures/model_comparison_components_L21_{2100,2150,2300}.png`

First figure carrying all four sources, and the first to carry 2300 (FACTS does not reach it;
MAGICC-SLR stands alone there). **No new model runs were needed** — the table
`outputs/ladrillo_model_comparison_L21.csv` already existed on the joint arm since 08-30 and
was merely untracked; it is committed now.

Year = the figure, scenario = the x axis, component = the panel. Three horizons inside one
panel lets 2300 squash 2100 flat.

**FACTS is drawn per MODULE, never as a median across modules** — they disagree up to 8x, so
that median summarises nothing (`median_needs_agreement`). `sej` modules (bamber19, wf4) take
an open marker, classified from `benchmark/comparator_classes.csv`, never a list typed in the
plot script.

---

## 3. ⚠ THE MAIN CORRECTION: A STALE CONSTANT SUPPRESSED 3 OF THE 4 BANDS (`243fbfa`)

The first version drew error bars only for Ladrillo and BRICK 2.0, inheriting
`ladrillo_figs.WIDTH_SRCS` and its caveat *"MAGICC/FACTS bands ALSO carry climate uncertainty,
so their MEDIANS are comparable and their WIDTHS are not."*

**That sentence was true only while both our arms ran on MEAN forcing.** The joint arms (built
2026-08-30) propagate both posteriors across the SAME 841 FaIR configs, which is the entire
reason they exist — memory `brick20_joint_band` says it outright: *"every column of the
comparison now carries climate uncertainty, so the WIDTHS are like-for-like for the first
time."* I inherited an 8-day-old constant into the one figure built to make that comparison.

**Fix:** the source-name set is replaced by a PREDICATE on each row's own `band_basis`,
`ladrillo_figs.band_is_comparable`, which **raises on a basis string it does not recognise**
rather than guessing. A cell falling back to the fixed arm now loses its bar and weakens the
caption by itself. Verified against that memory's own table — total p17–p83 at ssp126/2100
comes back Ladrillo 12.6 / BRICK 35.8 / MAGICC 21.5 / FACTS wf1f 17.4 cm. Exact.

**A mutation test caught a real bug**: the parameter-only branch of the caption had never
executed and its literal `%` broke the format string.

**Elicited whiskers are clipped and quantified.** bamber19's 5–95% at gis/ssp585/2100 spans
93.2 cm vs 17.1 for the next-widest module; limits come from the sampling quantiles and any
elicited whisker past them is annotated WITH ITS VALUE.

---

## 4. ⚠ "MAGICC AND FACTS ARE NOT DRIVABLE ON VAN VUUREN" WAS FALSE

`vv_model_comparison.py`'s header said so. It read the two comparators as fixed data files
because that is all *this* repo holds. **Both are installed and driven on this machine.**
Header corrected in place; memory `vv_marker_cubes` corrected; lesson saved as
`runnable_is_not_undrivable`. Say **RUN / RUNNABLE / IMPOSSIBLE** — collapsing the middle into
the third froze this for a month.

---

## 5. THE RUNS

### 5.1 The shared climate-driver convention (the thing to quote)

> **Ladrillo L21 / BRICK 2.0 / FACTS** — ONE climate: FaIR 2.2.4 calib 1.6.0 + CMIP7, the same
> 841-config cubes, the same 2014 splice, the same 1995–2014 reference, on every scenario.
> **MAGICC-SLR** — its OWN climate, from emissions. Not a gap in the convention; the point of
> keeping one independent arm.

`facts/build_shared_climate_nc.py` reproduces the Julia splice (`scope_slr_fair_uncertainty.jl`
`convention()`, ~:226) in Python: `y<=2014` = the shipped MEAN driver untouched, `y>2014` =
`mean(REF) + (config − mean_cfg(REF))`, REF = 1995–2014. **Feeding FACTS the RAW cube while
Ladrillo/BRICK get spliced would have made "shared" false at the moment of writing it down.**

Gates, all passing: `[SPLICE-MATCH]` **4.985e-07 °C** against the committed ssp585 cube — the
IDENTICAL figure the Julia driver reports, so the two implementations agree; `[CONFIG-AXIS]`
all 10 cubes carry the same 841-config order (so the n=200 subsample is the same 200 configs
everywhere); `[BASELINE]`; `[HORIZON]` (the 2300→2500 pad must never reach a reported year).

### 5.2 ⚠ VAN VUUREN THROUGHOUT; THE SSPs ARE A **CONTROL**, NOT A COMPARISON AXIS

Marcus's question was right and it **dissolved the RCMIP-vs-CMIP7 vintage straddle I had just
flagged** — that only existed while both sets sat in one comparison. Once we drive these
models ourselves the seven markers are a complete four-model set on ONE emissions vintage,
and are richer (7 scenarios, 4 peak-and-decline, vs 3 SSPs with 1).

The SSPs are kept for exactly one job: they are the only scenarios where a prior result exists
to check the pipeline against. **They therefore KEEP their original RCMIP inputs** —
reproducing an old run requires the old inputs, not harmonised ones.

### 5.3 MAGICC — ✅ DONE (`6807d5b`)

`MAGICC/slr-refresh/build_vv_scenarios.py` → `data/processed/emissions/slr_vv_and_ssps.csv`
(10 scenarios, 52 variables). Run via the **frozen copy** `notebooks/302_run-magicc-vv.py`
(never edit a script an interpreter is reading). Output **500 MB**,
`data/processed/VVandSSPs_Nauels2025_withOCH_2026_08_31_073153.csv`, 600 members × 10
scenarios, ~15 min. Extracted by `python/extract_magicc_vv_components.py` →
`data/comparison/magicc_nauels_components_vv.csv`.

Unit conversions are done by the pipeline's own library, never typed constants, and the
realised factors are PRINTED: CO2→C 0.272727, N2O→N2ON 0.636364, SO2→S 0.500000, NOx 1.0 under
a declared `NOx_conversions` context. `[OVERLAP]` then checks each marker against its host SSP
at 2015 (all 35 pairs inside 0.5–2.0×), which is the physical check on those factors.

**⚠ THE FINDING: MAGICC-SLR IS ULP-SENSITIVE AT ssp585.** The control fired at 6.1e-3 cm
against a 1e-6 cm identity bound. Running it down:
* raw output is **BIT-IDENTICAL** for ssp126 and ssp245 — 0 of 3.3M cells differ;
* **ssp585 differs on all 600 members**, worst 0.096 mm on Sea Level Rise;
* cause = **two emissions cells differing by ONE ULP** (~1e-16) between the reference and my
  scmdata round-trip of it, one being ssp585 CO2 FFI at 2130. ssp245's perturbed cell (CH4 at
  2190) moved the output **not at all**.
⇒ a 1e-16 input change moves ssp585 SLR ~1e-5 relative: a **~1e11 amplification**, i.e. a
THRESHOLD CROSSING flipping for some members — the same behaviour already documented for
BRICK's DAIS hard annual step (`dais_fastdynamics_quant`). **The bound was wrong, not the run.**
It is now derived from reporting precision (a tenth of the 0.1 cm last quoted digit) and the
sensitivity PRINTS on every run.

Two builder bugs the gates caught, both surfacing as MAGICC "NaN forcing" — which reads like a
MAGICC problem and was entirely ours: the emissions append **unioned two different time axes**
(van Vuuren also has a 3-year gap at its 2020 harmonisation seam), and **the reference SSP file
is itself sparse** because notebook 302 densifies it internally. The `[NAN]` gate that should
have existed before the first launch now does.

**MAGICC medians, total GMSL, cm rel 1995–2014:**

| marker | 2100 | 2150 | 2300 |
|---|---|---|---|
| vvVL | 30.6 | 37.4 | 45.7 |
| vvLN | 34.4 | 39.0 | **27.0** |
| vvL | 34.6 | 43.5 | 53.4 |
| vvML | 45.4 | 61.0 | 55.6 |
| vvM | 51.9 | 99.4 | 266.1 |
| vvHL | 57.1 | 79.2 | **88.9** |
| vvH | 62.3 | 140.4 | 569.8 |

⚠ **vvHL (88.9) lands far below vvM (266.1) at 2300** despite being hotter at 2100 — the
peak-and-decline signal the SSPs cannot produce. **vvLN goes negative** in TE (−5.3) and AIS
(−0.4) at 2300, as a low-to-negative pathway should against a 1995–2014 baseline.

### 5.4 FACTS — ⏳ INPUTS READY, NOT LAUNCHED. **THIS IS THE NEXT STEP.**

Climate written for all 10 scenarios into
`facts/experiments/global.shared.<key>.n200/input/shared_<key>_{climate,gsat,ohc}.nc`.

⚠ **THE SCENARIO STRING IS A GROUP KEY, NOT A PHYSICS INPUT.** An earlier draft keyed each
marker to a host SSP; that was wrong-headed and is fixed — each marker is keyed by itself. The
driving path is `van Vuuren emissions → FaIR 2.2.4 calib 1.6.0 (841 cfgs) → GMST+OHC → FACTS`
and **nothing on it consults an SSP**. The three places a scenario string still reaches a
number, all checked in the FACTS sources:
* `ipccar5` icesheets has `if scenario in ['rcp85','ssp585']`, but it sets the **Greenland**
  dynamics range and our config runs that module through `pipeline.AIS.global.yml`, which
  emits only AIS/EAIS/WAIS. **INERT.**
* `emulandice` genuinely reads the label to pick per-SSP-**trained** GP emulators, and is
  2100-capped. ⇒ **the "e" workflows are NOT run on van Vuuren.** Faking a label would be
  inventing a training scenario.
* `ssp/landwaterstorage` takes `ssp1..ssp5` for a **population** pathway (reservoirs +
  groundwater). Real, and not climate — but the markers carry their own socioeconomic basis in
  their filenames, so `lws_ssp` in the builder is the marker's OWN SSP, not a climate proxy.
* `bamber19` in injected mode **skips its scenario_map branch entirely** and picks its H/L core
  from integrated SAT 2000–2099 of our climate (`pickScenario`). Label-free.

**To launch:** `colima start --cpu 8 --memory 8 --disk 100 --vm-type vz --mount-type virtiofs`
(host is 16 GB — do NOT exceed ~8–10), then per scenario a config.yml modelled on
`experiments/global.coupling.ssp245.n200/config.yml` with a `facts/dummy` climate_step pointing
at the three NetCDFs, workflows **wf1f / wf2f / wf3f / wf4 only**. See `facts_install_scope`
memory for the pip-neutering fix and the `docker run -lc` invocation.

---

## 6. FILES — what is committed and what is NOT

**Committed in SLR-RFF-BRICK** (`1f12c0d`, `360d5da`, `243fbfa`, `6807d5b`):
`python/plot_model_comparison_components.py` (new) · `python/extract_magicc_vv_components.py`
(new) · `python/ladrillo_figs.py` (band predicate + `GLACIER_LINEAGE_NOTE`) ·
`python/vv_model_comparison.py` (header corrected) · `data/comparison/magicc_nauels_components_vv.csv`
· `outputs/ladrillo_model_comparison_L21{,_spread}.csv` · the three figures · `CHANGELOG.md`.

⚠ **UNCOMMITTED, IN OTHER REPOS — commit or they are lost:**
* `facts/build_shared_climate_nc.py` (+ the 10 `experiments/global.shared.*` dirs)
* `MAGICC/slr-refresh/build_vv_scenarios.py`
* `MAGICC/slr-refresh/notebooks/302_run-magicc-vv.py`
* both repos also carry pre-existing modifications from earlier sessions (`facts/docker/Dockerfile`,
  `slr-refresh/notebooks/302_run-magicc-scenarios-SSPs.py`) — **check before committing blind.**

---

## 7. ⚠ THE GLACIER FORMULATION IS SHARED WITH MAGICC — GREENLAND IS NOT

Asked whether Ladrillo's GSIC and Greenland formulations are unique. **Glaciers: NO, and the
overlap is with MAGICC specifically.** `julia/glaciers_nu_component.jl:14` states it:

> `transient: dS/dt = κ · (S_eq − S) · max(T − T_eq, 0)^ν   (Nauels 2017 Eq. 3)`

with the header naming the law "Nauels-2017 (MAGICC Eq. 3)". MAGICC-SLR here **is** Nauels
(v7.5.3 + Nauels 2025). Ladrillo differs in reservoir count (3 vs 1), driver (glacier-frame T,
amp_g=1.8, vs GMST), the positive-part clamp (the header notes Nauels 2017 states no
convention), and the posterior. The equilibrium curve is a third lineage: Mengel 2016 PNAS.

⇒ **At the glaciers panel, Ladrillo-vs-MAGICC agreement is weaker evidence than agreement
anywhere else on the figure.** The independent glacier comparators there are BRICK 2.0
(Wigley-Raper) and FACTS (ar5glaciers, emuglaciers). Stamped on the panel and in the caption.

**Greenland: no comparator shares the formulation.** Ours = two-basin A+B commitment cell with
the shipped tap, fitted offline here; MAGICC/Nauels = SMB+SID split; FACTS = FittedISMIP /
emuGrIS / bamber19; BRICK 2.0 = SIMPLE. Four formulations, four lineages.

⚠ **NOT VERIFIED:** that Nauels **2025**'s glacier module is unchanged from Nauels **2017**. I
have Ladrillo's side from source and MAGICC's by the citation Ladrillo names. **Check this
before the claim goes in writing.**

---

## 8. TORCH VERDICT (standing instruction, memory `consider_torch_first`)

* **MAGICC → laptop, and it stayed there.** Embarrassingly parallel and a good technical fit,
  but two blockers outrank cores: the binary and the AR6 drawnset are the **sensitive** items
  in this project (members-only, DO_NOT_MAKE_PUBLIC guards — copying them to NYU shared storage
  is **Marcus's call**), and our binary is a local arm64 gfortran-15 build against Torch's
  x86_64. It ran in 15 min here; the question is moot for this job.
* **FACTS → laptop for this run; the port is worth SCOPING if FACTS becomes a repeated arm.**
  It runs under Docker/Colima and HPC generally forbids Docker — it needs Apptainer conversion
  plus RADICAL-EnTK under SLURM. A porting project, not a job submission; one 10-experiment run
  does not repay it. Pulse experiments or further scenario sets would.

---

## 9. OPEN ITEMS

1. **Launch the FACTS runs** (§5.4). The only thing standing between here and the four-source
   van Vuuren figure.
2. **Build the van Vuuren four-source figure** once FACTS lands — `plot_model_comparison_components.py`
   currently reads `ladrillo_model_comparison_<TAG>.csv` (SSP set). The vv sibling is
   `vv_model_comparison.py`; it needs the two new arms merged in and the same `--set=` treatment
   `plot_future_components.py` already has.
3. **Verify Nauels 2025 vs 2017 glacier module** (§7) before writing the lineage claim down.
4. **Commit the two other repos** (§6).
5. Inherited and untouched from `31c`: the `ais@2300` CONTROL exceedance; the hindcast
   driver-file mismatch; `plot_ladrillo_memo_figures.py` SystemExit on `--tag=L21`;
   `scope_ladrillo_vs_brick20_scorecard.py` has no L21 run; `plot_ssps_gsic_wr_vs_mengel.py`
   still carries the extA108 arms.
6. **`INDEX_slr.md` is ~17.0 KB** against a 14 KB soft / 18 KB hard budget. Close to the ceiling.
