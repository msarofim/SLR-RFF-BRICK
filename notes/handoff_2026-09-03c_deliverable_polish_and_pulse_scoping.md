# Handoff — L24 deliverable is in good shape but not exhaustively audited; pulse analysis is still unscoped

**Start here.** Repo `SLR-RFF-BRICK`, branch `ladrillo-dev`, all pushed to local commits (not
pushed to remote — check before assuming a remote copy is current). Written 2026-09-03, evening.
Supersedes `handoff_2026-09-03b_docx_canonical_and_pulse_next.md` for the deliverable's status;
that file's §3 (pulse scoping) is reproduced and refreshed below rather than superseded, since
no pulse work has happened since it was written.

⭐ **TWO THREADS, as before.** (1) Keep polishing
`deliverables/LadrilloUpdateDescription_L24.docx` — real content, real error risk, worth more
passes. (2) **Scope the pulse comparison work** — still genuinely unstarted. Neither blocks the
other.

---

## 1. WHAT HAPPENED THIS SESSION — six real fixes, not just prose edits

Marcus drove this session by reacting to specific sentences in the doc and asking for receipts.
Each one turned up something real:

1. **The depth-scope correction was already live in `bench_ladrillo.py` (2026-09-02) but invisible
   anywhere a reader would see it.** Surfaced it in Fig 1's caption and a footnote under the RMSE
   table; reworded the prose sentence to state it as a BOUND, not a point ("narrows to as little
   as 1.15×... still a FAIL even there"), matching the benchmark's own verdict exactly.
2. **`sync_filled_from_docx.py`'s `--verify` had a real bug**: `--resource-path` pointed at
   `deliverables/` instead of the repo root `build_l24_deliverable_doc.sh` actually `cd`s to, so
   every verify run silently swapped all 9 images for text placeholders and produced 9
   false-positive diff lines. Fixed, mutation-tested (reverting the line reproduces the failure).
3. **The "19 parameter marginals fail R̂ < 1.05" claim was independently verified for real**,
   against the canonical receipt (`outputs/log_l24_postprocess_driver.txt`), not just trusted
   because it "sounded internally consistent." A quick from-scratch Python replica of the check
   under-counted (14 vs 19) because it omitted the ESS half of the gate — a useful reminder that a
   verification method has to match the ORIGINAL method's criteria, not just compute something
   plausible-sounding with the same name.
4. **Fig 9b (`plot_ladrillo_memo_figures.py`) was missing BRICK 2.0 from its legend** even though
   BRICK was being plotted; also sat 7 FACTS-workflow columns away from Ladrillo. Fixed both.
5. **Made the document standalone** (Marcus: "delete all comparisons to previous lineages, this is
   meant to be a standalone document"). The lineage language lived in two shared caption dicts
   (`ladrillo_figs.py` `TAG_DESC["L24"]["note"]`, `plot_ladrillo_memo_figures.py`
   `TAG_DESC["L24"]`), not in the markdown body. Fixed both, regenerated all 9 figures. Caught a
   real bug along the way: `plot_vv_gsic_wr_vs_ladrillo.py`'s caption hardcoded "L21 chains"
   regardless of `--tag`, silently mislabeling Fig 6's own L24 chains.
6. **Launched the FACTS-to-2300 extension for the 7 van Vuuren markers**, for Fig 4. Cost was
   ~7 minutes total (Docker + `runFACTS.py`, 7 experiments), not the multi-hour job estimated
   without measuring first — should have checked the log timestamps of the existing 2-experiment
   2300 extension before guessing. Mechanism: new `*2300` experiment keys in
   `facts/build_shared_climate_nc.py` (same underlying FaIR cubes, longer `pyear_end`, exact
   pattern already used for the matched-dT pair), merged into the base marker names in
   `outputs/facts_components_shared_n200.csv`. Both integrity gates (COMPOSITION, DRIVER) passed
   on the extraction. `facts/run_vv_facts_2300.sh` reproduces it.

Then two follow-ups from Marcus's own reading of the results:

7. **Restored the traceable-numbers finding, as BOTH timescales, not the short one alone.**
   Marcus: report either the 100-year framing or both, never the 20-year framing by itself. The
   doc now states both: cumulative 1920–2024 (obs +19.45, Ladrillo +18.83, BRICK +22.09 — Ladrillo
   undershoots) AND the level at 2024 rel. the 1995–2005 calibration baseline (obs +7.81, Ladrillo
   +8.55, BRICK +8.45, IGCC +8.33 — both models run slightly high there instead). Both are real,
   verified numbers (the second is `plot_hindcast_components.py`'s own `@2024` console
   diagnostic) — they tell different, non-contradictory stories at different timescales.
8. ⭐ **The "Ladrillo's equilibrium regrowth is similar to MAGICC's" claim was WRONG, and finding
   that out required catching my own bug.** Wrote `python/verify_ladrillo_vs_magicc_equilibrium.py`:
   Ladrillo's real calibrated glacier law (via `scope_glacier_regrowth.py`'s `gmst_override` hook,
   unchanged machinery) driven by MAGICC's own GMST, compared against MAGICC's own 600-member
   equilibrium drawnset (`slr_gl_equitemp`/`slr_gl_equislr`), both evaluated at the SAME
   temperature so climate differences are removed. First pass said Ladrillo regrows *more* at
   vvLN (ratio 1.24×). **Marcus caught it from the printed table**: MAGICC's own domain starts at
   0 K (equilibrium undefined below pre-industrial) and vvLN cools to −0.67 K — below the domain —
   so `np.interp`'s default clamping was silently reporting MAGICC's FLOOR value as if it were a
   real equilibrium at a colder T. Confirmed by vvLN and vvML (also below the floor) producing the
   *identical* MAGICC value (−11.65 cm) despite different temperatures. Fixed to flag rather than
   clamp (`magicc_seq_at` now returns an `in_domain` bool). **Corrected result: on the three
   markers where a genuine comparison is possible (vvVL, vvL, vvHL), Ladrillo's equilibrium is
   LESS than MAGICC's (ratio 0.06–0.86), not similar; the two coldest markers admit no comparison
   at all.** Deliverable text corrected to say so. `outputs/verify_ladrillo_vs_magicc_equilibrium_L24.csv`
   has the numbers.

**Commits, in order** (repo `SLR-RFF-BRICK` unless noted):
`d074e40` (sync fix + TE placeholder) → `0a5daed` (depth-scope caption/table, Fig 9b, High-scenario
fix) → `64661fe` (standalone/lineage strip + Fig 6 bug) → `a1341eb` (FACTS at 2300) →
`f235251` (both timescales + MAGICC-equilibrium correction) → `775b86c` (figure re-save). Repo
`facts`: `92317d53` (the 7-marker 2300 extension) — ⚠ that repo has no `user.name`/`user.email`
configured, so the commit landed under an auto-detected identity
(`Marcus Sarofim <MarcusMarcus@MacBook-Pro-2.local>`), not the usual "Marcus C. Sarofim" — cosmetic,
not touched (never change git config unasked), but worth Marcus fixing once if he cares about the
`facts` repo's commit history matching the rest.

## 2. THE CANONICAL DOCX WORKFLOW — same rule as last time, still binding

**Before ANY edit to the deliverable's text:**
```bash
cd deliverables && python3 sync_filled_from_docx.py --verify
```
Marcus edits the `.docx` directly in Word and re-edits within minutes of receiving a rebuilt copy
— check `ls -la`/`git status` on the docx before assuming your in-context copy is current; it
changed under me at least twice again this session. Only after a clean `--verify` should
`FILLED.md` be edited; rebuild with `build_l24_deliverable_doc.sh`'s pandoc invocation (or
reproduce it: `sed 's|../figures/|figures/|g' ... | pandoc --resource-path=. --from=gfm+pipe_tables
--to=docx`), verify again, then `SendUserFile`. The sync script's bugs are now fixed and
mutation-tested (§1 item 2) — no known issues remain in it.

## 3. OPEN ITEMS ON THE DOCUMENT

1. **FIG 3 (the 2150 van Vuuren panel) is still an undecided cut candidate.** Flagged two
   handoffs ago; Marcus has not weighed in. Leave it unless asked.
2. ⚠ **This session's review was REACTIVE, not systematic.** Every fix above came from Marcus
   flagging a specific sentence and me chasing the receipt — a good, high-signal way to work, but
   it means large parts of the document have NOT been independently re-checked this session:
   the GSIC/Greenland structural-update prose, the calibration-data-updates table, the DAIS
   geometry paragraph, and — notably — the "Low scenarios" and "Peak-and-decline scenarios"
   paragraphs under "Physical intuition", which Marcus himself condensed this session (removing
   the 2.55×/1.48× Antarctic-band numbers and the melt-only-ratchet comparison numbers) without
   those condensed versions being independently re-verified against source data. If "keep
   polishing" continues, a genuine line-by-line pass over those untouched sections — not waiting
   for Marcus to flag the next sentence — is the highest-value next step, following the same
   discipline as §1: find the actual receipt (a script, a log, a CSV), don't trust that a claim
   "sounds internally consistent."
3. The two stray untracked docx files at the `SLR-RFF-BRICK` repo root
   (`LadrilloUpdateDescription.docx`, `LadrilloUpdateDescription_L24.docx`, dated 2026-09-02,
   pre-dating the docx-canonical rule) are still there, still harmless, still not part of the
   canonical path (`deliverables/LadrilloUpdateDescription_L24.docx`). Leave them unless Marcus
   asks to clean up.

## 4. ⭐ PULSE ANALYSIS — SCOPING, STILL NOT STARTED (refreshed from handoff 09-03b §3)

Nothing changed on this thread since it was last scoped. Reproducing that scoping here, with one
addition (§4.3) from what this session's FACTS work demonstrates.

### 4.1 What exists

**FaIRtoFrEDI `scripts/pulse_calib_compare.py` → `fair_outputs/pulse_calib_v160.npz`**
(unchanged, still dated 2026-08-28): a paired baseline/pulse CO2 experiment across the full
841-config posterior on calib 1.6.0, with same-config/same-seed pairing so internal variability
cancels exactly (zero-pulse test verifies this), plus peak-response and doubling-ratio sanity
checks already in the npz. This is the right FaIR-side starting point for any Ladrillo pulse arm —
likely needs only a scenario/year check before its dT/dC marginals can drive one.

### 4.2 What does not exist

**No Ladrillo pulse driver at all.** Nothing in `julia/` computes a Ladrillo SLR response to a
FaIR pulse on the current (calib 1.6.0, CMIP7, L24) stack. Everything that superficially looks
like pulse machinery in this repo (`diag_a108_pulse_perdraw.jl`, `project_pulse_hybrid_mengel.jl`,
`wong_cond_pulse_pairs_*.parquet`, `outputs/pulse3brick_v145/`, the poster/substack pulse figures)
is on the OLD BRICK-Mengel model, OLD calib 1.4.5, mostly OLD MimiBRICK lineage — a worked example
of the pairing/gating discipline, not a comparator. Read `diag_a108_pulse_perdraw.jl` first if you
want the cleanest template, but do not assume its numbers, climate driver, or model apply to L24.

**The old FACTS pulse PoC is the same kind of worked-example-only reference** (2026-07-14/15,
memory `facts_install_scope`): CO2 pulse marginal, 10 GtCO2 @2030, paired, cm/GtCO2 @2100 median —
wf1f-IPCC 5.66e-3, wf2f-LARMIP 7.73e-3, wf3f-DeConto 6.26e-3, wf4-SEJ 4.82e-3, FaIR→BRICK 5.08e-3,
MAGICC-native 1.54e-2 (~3× higher than both). Old BRICK-Mengel, old calib — a magnitude sanity
check and a demonstrated result pattern (two independent SLR emulators agree to 10–20%; MAGICC's
own SLR module is the pulse-sensitive outlier), not a number to carry forward. The plumbing
(`FaIRtoFrEDI/fairtable7_v145_pulse.py` + `facts/build_pulse_climate.py`) is probably reusable with
arguments pointed at v160.

### 4.3 NEW: this session demonstrated the FACTS-extension pattern works cleanly on the current stack

Not pulse-specific, but directly relevant if a pulse comparison wants a FACTS arm: §1 item 6 above
just ran a brand-new FACTS extension (7 new experiment keys, ~1 min each, clean COMPOSITION/DRIVER
gates) on L24-vintage climate driving conventions. The mechanism (`build_shared_climate_nc.py`'s
`SCENARIOS`/`HORIZON_BY_KEY` pattern, `build_shared_configs.py`, `extract_facts_shared_components.py`'s
`KEYS` list) is now a proven, cheap template for adding a pulse-driven FACTS arm too, if the design
questions below land on wanting one. Building the actual pulse driver netCDF is a different task
(a paired baseline/pulse climate, not a scenario swap) but the FACTS-side plumbing to consume it is
now demonstrated fresh, not just theorized.

### 4.4 Design questions to settle before building — still Marcus's call, not a default

- **Which specie and pulse size.** CO2 is the obvious first case; the old FACTS PoC needed
  ≥~10 GtCO2 because smaller pulses sit below FACTS's float32 climate precision — check whether
  that bites Ladrillo too (Julia, presumably higher precision, but confirm rather than assume).
- **Pulse year and scenario(s).** The van Vuuren markers and the matched-dT pair are the freshest
  candidate backdrops. A pulse ON an already-declining marker vs a still-warming one would speak
  directly to this session's regrowth-mechanism findings (§1 items 6 and 8: does a pulse on a
  marker with spare glacier headroom get absorbed differently than one without, now that we know
  Ladrillo's equilibrium is somewhat SMALLER than MAGICC's, not similar?) — worth considering as
  the first pulse experiment precisely because the mechanism it would test is now better
  characterized than it was two handoffs ago.
- **Climate driver convention: spliced vs raw, joint vs fixed.** Same axis that mattered
  throughout the overshoot work and the FACTS extension this session (`FORCING CONVENTION:
  SPLICED` headers throughout). State which is used for a pulse arm explicitly.
- **Comparators.** BRICK 2.0 (same lineage/driver — corroboration not independence) and FACTS
  (genuinely independent on ice-sheet method, and now proven cheap to extend) are the two live
  comparators. MAGICC's glacier module is NOT independent (shares Ladrillo's Nauels-2017
  transient law — and per §1 item 8, the two laws' EQUILIBRIA now measurably differ too), so a
  MAGICC pulse comparison on glaciers specifically would need that caveat stated; it's still fine
  for Antarctica/Greenland/TE.

## 5. GOTCHAS CARRIED FORWARD

- **Torch verdict: say it out loud every time.** Everything this session ran locally (docx
  rebuilds, figure regeneration, the R̂ verification on 4×2M-draw chains via chunked pandas reads,
  the FACTS Docker runs) and all of it was fast enough to be the right call — the R̂ check read
  ~9 GB across 4 chains in a few minutes, the FACTS extension took ~7 min total. A pulse-comparison
  ensemble across 841 configs × many draws might change that calculus — check before assuming
  local, per §4.4's open questions.
- **The marker policy is still binding**: van Vuuren markers use marker-based forcing (they ARE
  the CMIP7 markers); SSPs use marker-free. Keep the two regimes separate in any figure/table.
- `memory/INDEX_slr.md` was ~600 bytes over its soft budget as of the last handoff; not rechecked
  this session — worth a `wc -c` before it drifts further.
