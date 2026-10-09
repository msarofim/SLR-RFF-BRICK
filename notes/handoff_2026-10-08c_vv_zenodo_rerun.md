# Handoff 2026-10-08c: van Vuuren on the PUBLISHED emissions + record conditioning

> ✅ **DONE 2026-10-08 18:40.** Every step of §3 ran and every gate passed; the results are in CHANGELOG 2026-10-08k.
> SLR e567ea7 and Ladrillo 2a1a34b are pushed. FaIRtoFrEDI 202eb74/f22572a and facts d52b9ed4 are local: FaIRtoFrEDI's
> branch also carries another session's unpushed pulse commits, and facts' origin is the public FACTS org.
> **Open for Marcus:**
>
> 1. the climate-swap [ARM-MATCH] (the figure is not regenerated; ≤ 0.1 cm);
> 2. the version label;
> 3. the pulse arc's downstream;
> 4. the docx pass, now three vv rounds.
>
> **UPDATE 2026-10-08 evening** (CHANGELOG 10-08l and 10-08m; Ladrillo 10-08l):
> - item 1: the swap is on the COMMON draw set (Marcus).
>   - ⛔ The swap committed in e567ea7 was NOT "not regenerated". A partial retry wrote it from MIXED VINTAGES; it is
>     quarantined and replaced.
> - item 2: the paper reports **Ladrillo v1.2**, tag `v1.2.0` (Marcus).
> - The stale MAGICC history-gap reader is fixed.
> - Items 3 and 4 remain open.
> - FaIRtoFrEDI is held unpushed (Marcus).

Follows `handoff_2026-10-08b_ladrillo_github.md` (done: private repo `msarofim/Ladrillo.jl`, fresh-clone fix).

## 1. Why

- **The bug** (CHANGELOG 10-08j). The live vv arms used the `harmonized` emissions: the IIASA prerelease to 2100, then
  the published Zenodo v1.1.1 extension ADDED to the prerelease 2100 CO₂ level.
  - Medium-to-Low was revised before publication, so its tail sat 10.5 GtCO₂/yr low for 200 years: −2,098 GtCO₂, and
    0.73 K too cold at 2300.
  - L −167 Gt; LN −112 Gt; the rest within 27 Gt.
- **Marcus 10-08, "go with b and any pending fixes that can be done simultaneously".** His rulings:
  1. **Variant b:** the CMIP7 1.6.0 history verbatim, plus the published 2024–2300 future, scaled per species at
     2023.5.
     - The a-vs-b test put the history choice at ≤ 0.009 K.
  2. **Conditioning, "own-config, drop".** In Ladrillo's FaIR joint arms (SSP + vv), drop each draw whose fast
     dynamics fire by 2025 on its own paired config.
     - This is the 10-08f likelihood weighting exactly.
     - BRICK 2.0 and the MAGICC-climate arms are NOT conditioned.
     - Ladrillo.jl gets the same rule, so its identity gate stays exact.
  3. **MAGICC-SLR's own vv run is re-run** on the new emissions.
  4. **Pulse arc:** rebuild the 112 FaIR pulse cubes now; the pulse arc's downstream comes later, in its own session.

## 2. Done so far

| repo | commit | what |
|---|---|---|
| FaIRtoFrEDI (`heat-ed-morbidity`) | 202eb74 | `DEFAULT_VARIANT="zenodo"`; measured gate exceptions (CCl4 ×1.257, CFC-115 ×0.181, Halon-2402 ×0); `.variant` sidecar; cube provenance from it; the 7 old emissions files in `outputs/quarantine/20261008_vv_harmonized_tail_offset/` |
| SLR-RFF-BRICK (`ladrillo-dev`) | 238c944 | the a-vs-b diagnostic `python/diag_vv_zenodo_ab/` + CHANGELOG 10-08j |
| SLR-RFF-BRICK | 10b06ec | record conditioning in `scope_slr_fair_uncertainty.jl` ([TRIGGER-PORT]: model onset == ported formula on every draw; `--no-record-conditioning` → `_uncond`); `run_vv_zenodo_rerun_20261008.sh`; `gate_vv_zenodo_basis.py`; `gate_conditioned_predicted.py` |
| Ladrillo | **UNCOMMITTED** | `tools/forcing/build_emissions_v160_cmip7harm_vv.py` + `build_fair_cube_vv_v160.py` ported (parity-checked against the research copies) |

Checks already passed:
- the production builder rebuilds ML byte-identical to arm b;
- `spliced_ext_zenodo` == the raw Zenodo file (≤ 2.2e-16) on all 7 markers.

## 3. Plan (in order)

1. `./run_vv_zenodo_rerun_20261008.sh regress`: the driver with conditioning OFF must reproduce shipped ssp585.
2. `… cubes`: quarantine the 28 base + 112 pulse cubes in `outputs/quarantine/20261008_vv_harmonized_tail_cubes/`;
   rebuild; [VV-ZENODO-BASIS] + [VV-BASIS].
3. **In parallel:**
   - **FACTS:** `facts/run_vv_zenodo_rerun_20261008.sh` (to write, after `facts/run_vv_cmip7_rerun_20261007.sh`): 14
     experiments, ~95 min. ⚠ Include the stale `global.shared.vvHL2300.n200.crate0`, then re-run
     `python/diag_facts_gis_extrap_receipt.py`: the paper's FACTS "112 cm" receipt.
   - **MAGICC-SLR vv:**
     - point `MAGICC/slr-refresh/build_vv_scenarios.py:44-45` at `spliced_ext_zenodo`;
     - run `notebooks/302_run-magicc-vv.py` (jupytext, ~15 min);
     - run `python/extract_magicc_vv_components.py` (SOURCE is hard-coded to the 08-31 run) and
       `extract_magicc_vv_gmst.py --force`;
     - rebuild `vv_wide_20260831/` with `FaIRtoFrEDI/magicc_comparison/build_magicc_wide_vv.py`. That script is ONLY on
       FaIRtoFrEDI branch `magicc-comparison` (f81b71f); take it with `git show`, don't switch branches.
     - Quarantine the old wide files first, then `touch outputs/vvz_regression_20261008/.magicc_vv_done`.
4. `… arms`: snapshot; three streams; gsic; [CONDITIONED-PREDICTED].
5. `… downstream`; then the paper-number diff (template `python/v11_paper_number_diff.py`; add MAGICC-SLR-own and
   FACTS rows).
6. **Ladrillo.jl:**
   - `tools/forcing`: build the zenodo splice from a committed skeleton (names, units and order only), so the vv files
     need NO IIASA input; drop IIASA from `inputs.sha256`; `build_forcing.py VV_TAIL_VARIANT="zenodo"`; make the input
     verification stage-aware.
   - Re-import the 28 vv forcing files (`tools/import_l27_data.py --only`).
   - Add conditioning to `scripts/project_joint.jl` (own config, drop).
   - Re-certify: gate 2 on 3 SSP + 7 vv × 2 models; `check_forcing_identity`; `runtests`.
   - CHANGELOG.
7. Quarantine READMEs, both CHANGELOGs, memory.

## 4. Open for Marcus

- **Version label.** The paper says "Ladrillo v1.1". With conditioning on, the package default changes. Is this v1.2?
- The docx pass now carries a third set of vv numbers (CMIP7, v1.1, and this one).

## 5. Non-obvious state

- **Another session's CCX R MCMC** (4 chains + diag) was running at 16:47 (load ~8). Check `uptime` before each phase.
- `outputs/vvz_regression_20261008/arm_b_cubes/` (7 MB) is a TRACKED path but must stay UNcommitted. It is reproducible
  from `python/diag_vv_zenodo_ab/`.
- `gate_vv_cmip7_basis.py` is BLIND to this change (pre-2014 only); `gate_vv_zenodo_basis.py` is its complement.
- 10-08e's predicted dropped sets: SSP draws 229, 610, 1260; vv draws 187, 610. The vv set is on the OLD cubes, so
  expect it to recur but check.
