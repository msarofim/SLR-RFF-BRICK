# Handoff — the deliverable is stable under a docx-canonical workflow; pulse comparisons are next

**Start here.** Repo `SLR-RFF-BRICK`, branch `ladrillo-dev`, all pushed. Written 2026-09-03.
Supersedes `handoff_2026-09-03_gic_regrow_done_antarctica_next.md` for pickup purposes — that
file's technical content (GIC_REGROW, the matched-dT pair, FACTS at 2150/2300) is all still live
and is summarized in §1 below; read it in full only if you need the original measurements.

⭐ **TWO THREADS NOW, NOT ONE.** (1) Keep improving `deliverables/LadrilloUpdateDescription_L24.docx`
— Marcus edits it directly and it is production content with real error risk, so review passes
on it are worth continuing. (2) **Start pulse comparisons** — genuinely new work, scoped in §3.
Neither blocks the other.

---

## 1. STATE OF THE MODEL WORK (compressed — see the superseded handoff for full detail)

**L24 is champion**, all six modules, promoted on provenance not skill (L23's config, amp prior
widened to its shipped N(1.09, 0.180) width; 3/304 cells change verdict).

**The overshoot arc is closed and the finding survived every stress test:**
- The floored glacier law is NOT why Ladrillo's native overshoot penalty reads ~0 (ruled out
  with power, ≤6.2e-05 cm on the SSPs).
- Neither is Antarctic regrowth — the AIS **never regrows** on any pathway we run. The native
  `ssp534over`/`ssp126` pair inverts in temperature (ours ends 0.126 K COOLER at 2300) and that
  artifact alone accounts for the near-zero penalty.
- Built `ssp534overMATCH` (forcing-space construction: `ERF_126 + max(ERF_534−ERF_126, 0)`) to
  remove the artifact. On it, Ladrillo (+2.21 cm @2300) and BRICK 2.0 (+2.58) **agree**, and both
  sit **inside** the spread of four independent FACTS process-based workflows run to **2300**
  (1.65–5.39 cm — FACTS reaches 2300 fine; "it stops at 2150" was a stale assumption I had to
  retract, see `facts/build_shared_climate_nc.py`'s `FACTS_REPORT_MAX` comment).
- The models split **3–3 on whether the penalty decays** 2150→2300: Ladrillo decays fastest,
  but an independent process-based workflow (Bamber SEJ) decays right beside it — so decay is
  not a Ladrillo peculiarity.
- ⭐ **Why MAGICC regrows more than Ladrillo, mechanistically**: it is a RATE limit, not an
  equilibrium one. At vvLN on MAGICC's climate, Ladrillo's own glacier equilibrium has 16.9 cm
  of headroom by 2300 and realises only 2.1 of it — because the two big-headroom blocks (SLOWP
  ~275 yr, R19 ~465 yr) can't traverse their headroom inside the horizon. MAGICC has no regional
  split, so it has no slow block to bottleneck it. **The regionalisation that makes Ladrillo fit
  the historical record better is the same feature that makes it slower to regrow.**

All of this is in `LADRILLO.md` §4 and the deliverable. Full numbers, gates, and the two things I
got wrong along the way (an overstated "FACTS stops at 2150" claim, an overstated "common-mode,
not independent" characterization of Ladrillo/BRICK that Marcus corrected) are in
`notes/note_2026-09-02_matched_dt_overshoot_pair.md` and its ADDENDUM.

## 2. ⭐⭐ THE DOCX IS CANONICAL — READ THIS BEFORE TOUCHING THE DELIVERABLE

**Marcus edits `deliverables/LadrilloUpdateDescription_L24.docx` directly in Word.**
`LadrilloUpdateDescription_FILLED.md` is a GENERATED pandoc intermediate, not a source. This
reversed twice before the rule was made explicit (2026-09-03): I rebuilt the docx from a
hand-maintained `FILLED.md` and silently reverted Marcus's own condensing edits.

**Before ANY edit to the deliverable's text:**
```bash
cd deliverables && python3 sync_filled_from_docx.py --verify
```
This overwrites `FILLED.md` from whatever is CURRENTLY in the `.docx`, then round-trips the
result back through the exact pandoc build the deliverable uses and diffs the text against the
source — not a check that the script ran, a check that the two documents actually agree. If
`--verify` fails, READ the diff; do not force past it.

**Only after that sync**, edit `FILLED.md`, rebuild
(`sed 's|\.\./figures/|figures/|g' ... | pandoc ... --from=gfm+pipe_tables --to=docx`, or just
call the sync script's own pandoc invocation — see its docstring), verify again, and send Marcus
the rebuilt file with `SendUserFile`. **He typically edits again within minutes of receiving it**
— check `git status`/`ls -la` on the docx before assuming your copy is current; it changed under
me three times in one session on 2026-09-03.

⚠ **The sync script itself had two real bugs, both caught by its own `--verify` gate on first
genuine use** (mutation-testing a tool the day you write it is not optional): a docx pandoc
rebuilds from scratch names images by relationship ID (`media/rId14.png`) rather than Word's
sequential `imageN.png`, and my first fix for that chained two regex passes where the second
re-matched the first's own output. Both fixed; the current script handles Word-saved, pandoc-
rebuilt, and bare-markdown image forms in one single-pass regex. If you touch the regex again,
re-run the four-case mutation test in the commit that fixed it (`git log --oneline -- 
deliverables/sync_filled_from_docx.py`) before trusting a change.

### Open items on the document itself

1. **A cumulative-total claim was found untraceable and replaced** (2026-09-03): the original
   "observed 7.81 cm, Ladrillo 8.55, BRICK 2.0 8.45, IGCC check 8.33" traced to my very first
   draft and matched no single metric under any window I could find — a systematic search hit
   different numbers on DIFFERENT components. Replaced with a verified 1920–2024 comparison
   (obs +19.45, Ladrillo +18.83, BRICK 2.0 +22.09). **If Marcus has the actual source for the
   original numbers, ask before assuming the replacement is final** — I could not identify what
   they were meant to measure, so I substituted the nearest defensible like-for-like quantity
   rather than guess at his intent.
2. **FIG 3 (the 2150 van Vuuren panel) may be a cut candidate** — flagged, not decided. It sits
   between FIG 2 (2100) and FIG 4 (2300) and nothing in the current text specifically depends on
   the 2150 snapshot now that the peak-and-decline narrative references 2300. Marcus has not
   weighed in either way.
3. **The "19 parameter marginals fail R̂ < 1.05" claim is NOT independently re-verified this
   session** — it matches `LADRILLO.md`'s own convergence language, which I trust as internally
   consistent, but I did not find a dedicated per-parameter R̂ table to check it against directly.
   Worth doing if a per-parameter convergence CSV surfaces.
4. Every OTHER checkable number in the current document was re-verified against source data on
   2026-09-03 and holds: the 58-parameter breakdown (17/9/19/13, including the 13's own
   sub-breakdown), SLOWP/R19 amplification priors (2.50, 0.72), the RMSE table (all 20 cells),
   FIG 9's totals, the MAGICC parameter counts (17 total, 9 vary, each of those 4 discrete
   values), and the tap's contribution (0 / 0 / 41.8 cm by SSP at 2300).

## 3. ⭐ NEXT: PULSE COMPARISONS — SCOPING, NOT A PLAN

Marcus wants to start pulse-comparison work. **This is genuinely new for Ladrillo/L24** — there
is no reversion risk here, just groundwork. What exists and what doesn't:

**EXISTS, calib 1.6.0, verified.** FaIRtoFrEDI `scripts/pulse_calib_compare.py` →
`fair_outputs/pulse_calib_v160.npz`: a paired baseline/pulse CO2 experiment across the full
841-config posterior on the CURRENT calibration, with the discipline the `climate-modeling`
skill requires already built in — same config, same seed, so internal variability is common-mode
and cancels in the difference; a zero-pulse test verifies it cancels EXACTLY, not approximately;
peak-response and doubling-ratio sanity checks are in the npz (`check_peak_mK_per_GtCO2`,
`check_doubling_ratio_2100`, etc.). This is the right FaIR-side starting point — it likely needs
only a scenario/year check before its dT/dC marginals can drive a Ladrillo pulse arm.

**DOES NOT EXIST.** No Ladrillo pulse driver at all — nothing in `julia/` computes a Ladrillo SLR
response to a FaIR pulse on the current (calib 1.6.0, CMIP7) stack. All the existing pulse
machinery in this repo (`diag_a108_pulse_perdraw.jl`, `project_pulse_hybrid_mengel.jl`,
`wong_cond_pulse_pairs_*.parquet`, the whole `outputs/pulse3brick_v145/` tree, the poster/substack
pulse figures) is on the OLD BRICK-Mengel model, OLD calib 1.4.5, and mostly OLD MimiBRICK
lineage — useful as a WORKED EXAMPLE of the pairing/gating discipline, not as a comparator. Read
one before writing a new one (`diag_a108_pulse_perdraw.jl` is probably the cleanest), but do not
assume its numbers, its climate driver, or its model apply to L24.

**A reference point exists for the cross-model comparison, on the SAME caveat.** FACTS pulse PoC
(2026-07-14/15, memory `facts_install_scope`): CO2 pulse marginal, 10 GtCO2 @2030, paired,
cm/GtCO2 @2100 median — wf1f-IPCC 5.66e-3, wf2f-LARMIP 7.73e-3, wf3f-DeConto 6.26e-3, wf4-SEJ
4.82e-3, **FaIR→BRICK 5.08e-3**, **MAGICC-native 1.54e-2 (~3× higher than both)**. This is old
BRICK-Mengel and old calib — a magnitude sanity check and a demonstrated result pattern (two
independent SLR emulators agree to 10–20%; MAGICC's own SLR module is the pulse-sensitive
outlier), not a number to carry forward. ⚠ Also: **`FaIRtoFrEDI/fairtable7_v145_pulse.py` +
`facts/build_pulse_climate.py`** is the worked pipeline that produced it — the same worked-example
caveat applies, but the plumbing between FaIR's NPZ and FACTS's climate NetCDF is real and
probably reusable with the arguments changed to point at v160.

### Design questions to settle before building, not silently

Per the standing rule (methodological choices are explicit): these need Marcus's call, not a
default.
- **Which specie and pulse size.** CO2 is the obvious first case; the FACTS PoC needed ≥~10 GtCO2
  because smaller pulses are below FACTS's float32 climate precision — check whether that bites
  Ladrillo too (Ladrillo runs in Julia at presumably higher precision, so it may not, but confirm
  rather than assume).
- **Pulse year and scenario(s).** The overshoot work's van Vuuren markers and matched-dT pair are
  the freshest candidate backdrops; a pulse ON an already-declining marker vs a still-warming one
  would speak directly to the regrowth-mechanism finding in §1 (does a pulse on a marker with
  spare glacier headroom get absorbed differently than one without?) — worth considering as the
  FIRST pulse experiment precisely because §1 already characterizes the mechanism it would test.
- **Climate driver convention: spliced vs raw, joint vs fixed.** Same axis that mattered
  throughout the overshoot work. State which is used for a pulse arm explicitly; don't inherit a
  default from a script written for a different question.
- **Comparators.** BRICK 2.0 (same lineage, same driver — corroboration not independence, per
  Marcus's 2026-09-02 correction) and FACTS (genuinely independent on ice-sheet method) are the
  two live comparators from the overshoot work; MAGICC's glacier module is NOT independent
  (shares Ladrillo's Nauels-2017 transient law), so a MAGICC pulse comparison speaks to
  Antarctica/Greenland/TE, not to glaciers.

## 4. GOTCHAS CARRIED FORWARD

- **Torch verdict: say it out loud every time**, per the standing rule. Everything this session
  ran locally (short Julia arms against local chains, FACTS in local Docker) and that was
  correct; a pulse-comparison ensemble across 841 configs × many draws might change that
  calculus — check before assuming local.
- **Chains ~2.2 GB each.** Every L24 arm is TAPPED; L21/L23 have no untapped van Vuuren or MAGICC
  arms (L24 now does, built 2026-09-02, 14 arms, `run_l24_vv_magiccclim.sh`).
- **The marker policy is binding**: van Vuuren markers use marker-based forcing (they ARE the
  CMIP7 markers); SSPs use marker-free (`calculated` land use) because they predate CMIP7. Keep
  the two sets separate in any figure or table — a pulse comparison spanning both needs to say
  which regime each arm is in.
- `memory/INDEX_slr.md` is ~600 bytes over its soft budget (hard ceiling 18 KB, not urgent).
  `MEMORY.md` is compliant on content (measure with HTML comments stripped, not file size — that
  was itself a live bug this session, see `l24_deliverable_docx_canonical` for the pattern and
  `runnable_is_not_undrivable` for the general class).
