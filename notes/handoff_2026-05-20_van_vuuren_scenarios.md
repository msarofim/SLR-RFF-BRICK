# Handoff — 2026-05-20 — van Vuuren scenarios through FaIR + BRICK

This is a project-launch handoff. A fresh Claude session should be able
to start cold by reading this note plus `~/.claude/CLAUDE.md`, the
project's `CLAUDE.md`, and the user's auto-memory at
`~/.claude/projects/-Users-MarcusMarcus-Documents-2026-CodeProjects-FaIRtoFrEDI/memory/`.

## 1. Project scope

Run the **new van Vuuren scenarios** through the FaIR-BRICK pipeline
already built in SLR-RFF-BRICK, and compare the resulting GMST / GMSL
projections against the RFF-SP-based projections.

The headline question: do the van Vuuren scenarios envelope (or contradict,
or supplement) the RFF-SP probabilistic distribution? Specifically:

- Do the van Vuuren high-emissions scenarios land at the upper tail of
  the RFF-SP distribution, or beyond it?
- Are the low-emissions scenarios consistent with the RFF-SP cold tail?
- For Hawkins-Sutton: with a scenario set (a few discrete trajectories),
  the "emissions" variance source becomes scenario-mixing variance rather
  than the continuous probabilistic spread we get with RFF-SP. How does
  the variance partition look under each framing?

This is largely a pipeline-swap exercise — almost everything in
SLR-RFF-BRICK is reusable. The methodological work is in the comparison
framing, not the climate modeling.

## 2. Key methodological choices to flag upfront

A fresh session should *not* silently resolve any of these — get explicit
direction from Marcus before committing to one:

### 2.1 Which van Vuuren scenarios?

Marcus said "the new van Vuuren scenarios" without specifying. Likely
candidates as of 2026:

- A new scenario set published by van Vuuren and collaborators in
  2024-2026 (specific paper TBD — ask Marcus or check IIASA scenario
  database).
- The post-SSP scenarios under development for AR7 — van Vuuren has been
  a co-author / scenario-architect on those.
- An update to the SSP/RCP framework specifically for sea-level rise
  applications.

Get the exact paper / dataset reference from Marcus on Turn 1.

### 2.2 Probabilistic interpretation

- **RFF-SPs** are probabilistic — 10,000 trajectories with intrinsic
  weights summing to 1. Quoting "median RFF-SP at 2100" is well-defined.
- **van Vuuren scenarios** are likely *storyline-based*, with no
  intrinsic probability weights. They span the future plausibly but
  don't sample it probabilistically.

Implications for comparison:
- Per-scenario percentiles from FaIR+BRICK uncertainty (climate +
  ice-sheet) are well-defined for either input set.
- Cross-scenario percentiles for RFF-SP have intrinsic meaning;
  cross-scenario percentiles for van Vuuren require an explicit
  weighting choice (equal-scenario, expert-elicited, or none).

The substack handoff `notes/handoff_2026-05-19_claude_chat_substack.md`
§5.5 already flags this RFF-vs-SSP distinction; the same lens applies
here.

### 2.3 Hawkins-Sutton with discrete scenarios

For RFF-SP, the H-S "emissions" variance is the variance of climate
outcomes *across* the probabilistic emissions distribution. For
van Vuuren:

- If scenarios are treated as equal-weighted, the "emissions" variance
  is the among-scenario variance of the FaIR-ensemble median.
- If scenarios are treated as named (deterministic), the H-S frame
  doesn't really apply — you'd report per-scenario GMST distributions
  separately rather than blending them.

Either is defensible; the choice frames the conclusion.

### 2.4 BRICK side

Likely unchanged. The same LHS-10k or ANOVA factorial design works.
Just need to swap the FaIR cube being fed to BRICK from
`rff_baseline_stoch_to2300.npz` to a van-Vuuren-driven cube. Confirm
with Marcus, but the BRICK posterior + Wong weighting should still apply
unchanged.

## 3. What's reusable from SLR-RFF-BRICK

Almost everything. Path references assume the repo at
`/Users/MarcusMarcus/Documents/2026/CodeProjects/SLR-RFF-BRICK/`.

| Existing component | Reuse |
|---|---|
| `python/lhs_climate_pilot{,_ext}.py` | FaIR cube generator. Modify to read van Vuuren emissions instead of RFF-SP. |
| `python/run_fair_rff.py` | Single-scenario FaIR runner. Probably the right place to start (one van Vuuren scenario at a time before going to factorial). |
| `julia/run_mimibrick_paired_explicit.jl` | BRICK driver. Unchanged. |
| `python/scripts/build_lhs10k_metadata.py` | LHS metadata builder. Modify to use scenario-index instead of rff_idx, OR add a scenario-index dimension if running multiple scenarios. |
| `python/apply_wong_weights.py` | Wong importance weighting. Unchanged (operates on BRICK output trajectories, independent of upstream emissions source). |
| `python/scripts/run_4way_slr_decomp.py`, `run_pulse_*` | H-S decomposition. May need a different decomposition structure (see §2.3). |
| `outputs/brick_lhs10k_baseline_to2300_weighted.csv` | The RFF-SP baseline — reuse as the comparison reference. |
| FaIR-calibrate v1.4.1 (Smith et al. 2024, 841 configs) | Unchanged calibration. The same 841-config posterior applies. |

The "comparison" half of the project is new code:

- A script that aligns van Vuuren scenarios with the RFF-SP distribution
  (matching percentiles, scenario-to-RFF mapping, or overlay plots).
- A figure script for the side-by-side projection bands.
- A H-S figure that shows the van Vuuren framing alongside (or replacing)
  the RFF-SP variance decomposition.

## 4. Suggested first steps (in order)

1. **Get the exact scenario set from Marcus.** Citation, format, gas
   coverage (CO2 only? all GHGs? aerosols?), time horizon (to 2100? to
   2300?). Without this, any pipeline work risks rebuilding for the
   wrong input.
2. **Format-conversion sanity check.** Load one van Vuuren scenario,
   verify it has the same gas-by-gas structure FaIR expects (CO2 fossil,
   CO2 AFOLU, CH4, N2O, BC, OC, SO2, NH3, NMVOC, NOx, CO, HFCs, etc.).
   The most common pitfall is gas-coverage gaps — fall back to AR6
   harmonized defaults for missing species.
3. **Run one scenario through FaIR via `run_fair_rff.py` analog.**
   Compare 2100 GMST to published van-Vuuren-paper values as a sanity
   check.
4. **Sanity tests** (per universal CLAUDE.md): zero-emissions scenario
   should give bit-identical GMST. Doubling all emissions in one
   scenario should give roughly 2× the warming response.
5. **Full ensemble: scenarios × 841 FaIR configs**. Then BRICK as before.
   This produces a van Vuuren GMST cube directly analogous to
   `outputs/rff_baseline_stoch_to2300.npz`.
6. **Comparison figure.** Side-by-side projection bands at 2050 / 2100 /
   2150 for RFF-SP vs van Vuuren. Probably the headline output.
7. **Decide on H-S framing** per §2.3 and produce the variance
   decomposition figure(s).
8. **Repo decision.** Likely a new repo `SLR-vanVuuren-FaIR-BRICK` (or
   similar), with this repo's pipeline as the methodological dependency.
   Confirm with Marcus.

## 5. External references to track down

- **van Vuuren D.P. et al.** (specific paper TBD — the user said "new"
  so probably 2024 or later). Likely venues: *Nature*,
  *Nature Climate Change*, *Earth System Science Data*, *Environmental
  Research Letters*, IIASA-published scenarios database.
- **van Vuuren D.P. et al. 2017.** SSPs original framework paper.
  *Global Environmental Change*. Useful background for understanding
  van Vuuren's scenario design philosophy.
- **O'Neill B.C. et al. 2014, 2017.** SSP narrative + quantification
  papers. Foundational.
- **Rennert K. et al. 2022** (RFF-SP, *Nature*) — the comparison
  reference, already cited in this project.
- **Smith C. et al. 2024.** FaIR-calibrate v1.4.1. The same calibration
  applies; no change.

## 6. Open questions a fresh session should ask Marcus on Turn 1

- "Which van Vuuren scenarios specifically? Citation, dataset URL, file
  format?"
- "Probabilistic interpretation: equal-weighted scenarios, expert-elicited
  weights, or treat each scenario as deterministic?"
- "H-S framing: do we decompose across scenarios as 'emissions' variance,
  or report per-scenario decomposition?"
- "Comparison framing: side-by-side RFF-SP vs van Vuuren projection
  bands, or pair each van Vuuren scenario to its closest RFF-SP
  percentile?"
- "New repo, or extend SLR-RFF-BRICK on a branch?"
- "Time horizon: does van Vuuren scenario data extend to 2300, or
  truncated at 2100/2150?"
