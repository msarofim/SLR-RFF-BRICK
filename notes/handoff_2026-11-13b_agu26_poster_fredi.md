# Handoff 2026-11-13b: AGU26 pulse poster, first pass done; next is the FrEDI pulse-damage build

Successor to `handoff_2026-11-13_agu26_pulse_poster.md` (read its §4 "where the pulse arc lives" and §6 "what not
to touch"; both still hold). Written by the poster session at the end of its first pass. Read this, then
`FaIRtoFrEDI/magicc_comparison/poster_agu26/claims_and_layout.md`, which is the live working document.

## 1. The poster

- AGU26 GC092 "Slow Seas, Fast Gas: Coastal Damages from CO2 and CH4". **Wednesday 9 December 2026, 14:15-17:45
  PST.** Maximum size **44 in wide x 44 in high**; AGU encourages printing through CCI. Allow print lead time.
- Authors MC Sarofim, T Wong, V Srikrishnan, F Errickson, L Rennels. On the poster: "Marcus C. Sarofim (NYU Marron
  Institute)".
- Marcus writes all poster text. Claude supplies figures, headline numbers and layout, with text placeholders.
- The submitted abstract text has not been supplied; the 08-03 draft (`~/Documents/2026/AGUFallMeeting/AGU26
  Abstract Drafts.docx`, second entry) is the working text. Ask again if it matters.

## 2. Rulings (Marcus, 2026-11-13; also in memory `agu26_pulse_poster_rulings`)

Round 1:
1. Backbone: the six van Vuuren markers (`pulse_stats.VV_MARKERS`). RFF-SP named as the next step. Reason on the
   table: all RFF-SP products are calib 1.4.5, BRICK-lineage only, and the shipped 0.01 Tg CH4 pulse is
   float32-corrupted after ~2060.
2. FrEDI coastal damages are in scope, on the IEc 1.0.0 build.
3. SLR models: all four (Ladrillo L27, BRICK 2.0, MAGICC-SLR, FACTS wf1f + wf2f). FACTS totals to 2100 only.

Round 2 (FrEDI design):
4. Pairing: FrEDI on each model's **central baseline SLR path** plus its **mean pulse difference**, with the
   shortcut's **bias measured at 2100 and 2300** from the existing per-draw horizon files.
5. Socioeconomics: **SSP2 for all six markers** (damage differences then come from the SLR physics only).
6. Coastal Properties: **NoAdapt, Reactive and Proactive shown as a range.**
7. Horizon: **2100 headline, plus a 2300 sensitivity labelled as FrEDI's extrapolation.** FACTS stays at 2100.

## 3. What exists now (FaIRtoFrEDI branch `heat-ed-morbidity`, commits 8352679, 9e200be, 1f10325; not pushed)

- `magicc_comparison/poster_agu26/claims_and_layout.md`: claims vs evidence (11 rows), RFF-SP inventory (§1b),
  headline numbers, decisions, layout (four columns), FrEDI scoping (§4), status table.
- `magicc_comparison/poster_agu26/make_panels_agu26.py`: panels B (pulse GMST), C (pulse SLR, five series),
  E (t50 of the 2030-2300 integral), F (component shares). It imports `pulse_duration_vv.load_path` and
  `diag_igmst_ordering_vv.load_dgmst`; labels come from constants at the top; each panel carries a two-line
  provenance stamp. Outputs: `panels/*.{pdf,png}`, `panel_numbers_agu26.csv` (every plotted headline value),
  `panel_manifest_agu26.csv` (every input with its sha256). Two renders were byte-identical.
- Panel conventions to keep for new panels:
  - Model colours: Ladrillo `#2a78d6`, BRICK 2.0 `#eda100`, MAGICC-SLR `#e87ba4`, FACTS `#008300` (wf2f dashed).
    They pass the dataviz validator on all pairs (CVD dE 13.0). The Python validator is `validate_palette.py` in the
    dataviz skill's `scripts/` dir; there is no node on this machine.
  - Component colours: Antarctica `#6250d6`, TE `#e34948`, glaciers `#1baf7a`, Greenland `#eb6834`.
  - Every series is direct-labelled with a leader line, because yellow and magenta are below 3:1 contrast.
  - Panel size about 10 in wide (one column of the 44 in poster); fonts 13-21 pt; manual margins (`ADJ`), not
    `tight_layout`.
  - Commit the script before the final render so the stamp carries a clean hash.
- CHANGELOG entry: FaIRtoFrEDI `CHANGELOG.md` 2026-11-13 (a).

## 4. Next job: the FrEDI pulse-damage build (panel I)

**Torch-or-laptop verdict: laptop.** About 90 coastal-only FrEDI calls on central paths. No MAGICC binary or Docker
is involved, and a one-off does not repay a port. Re-check the verdict if the bias check grows into per-draw FrEDI
runs.

Facts from the read-only scoping (details in `claims_and_layout.md` §4):
- **Build:** `~/Rlibs/fredi_iec100_oct6` (packaged 2026-10-06; the HTF fix is in its data). Use the `_slim`
  variant if needed, never `_rv`, which cannot compute Proactive. Load via `FREDI_LIB`, and set
  `FREDI_EXPECT_BUILD=iec100_oct6` so `gates/check_fredi_build.R` checks the build.
- **SLR sectors in the headline set** (all 2015$, no mortality endpoint): Coastal Properties (Reactive; NoAdapt and
  Proactive also exist), HTF (Reasonable), Marsh Migration Primary (Medium).
- **Driver template:** `vehicle_fredi_v145_fredi5.R`. It has SSP2 GDP and state population for 2010-2300 (:441-453)
  and `prep_slr` (:826-838: years 2000-2300, clip [0, 1000] cm, copy the last year to 2301). It asserts
  `driverValue` equals its input (:620-628) and passes temperature alongside SLR (GMST minus each draw's 1986-2005
  mean, `temptype="global"`). **Copy it under a new name; do not edit it** (other sessions use it).
- **FrEDI's SLR mechanics:**
  - Damage in a year is linearly interpolated in that year's SLR between NCPM level runs.
  - After 2100 the level runs are held at 2100, and coastal damages are rescaled by socioeconomics.
  - FrEDI needs SLR through `maxYear`, so FACTS runs with `maxYear = 2100`.
  - Inputs must be referenced to 2000. The pulse paths are referenced to 1995-2014; the pulse difference is zero
    before 2026, so re-referencing moves only the baseline level.
- **Linearity:** the only coastal scaling test (CHANGELOG 09-16j, September build, policy-size changes) found a 4x
  change gave 5.0x / 6.7x / 252x (Coastal / HTF / Marsh). Nothing has been measured at pulse size (1 GtCO2 is
  0.012-0.019 cm at 2100).

Steps:
1. **Assemble central baseline annual SLR paths** per model x marker. This is the unknown.
   - The pulse path files (`pulse_*_paths_*`) hold differences only.
   - Ladrillo and BRICK 2.0: look for annual baseline paths from the level vv arm
     (`SLR-RFF-BRICK/outputs/scope_slr_fairunc_*_vv*_spliced_L27*`; the pulse runner's baseline IS that arm,
     certified by `[LEVEL-MATCH]` in `julia/scope_slr_pulse_vv.jl`).
   - MAGICC-SLR: per-member SLR was never saved; look for a baseline mean or median path in the stage-4 outputs
     or `~/CodeProjects/MAGICC/` (members-only; nothing from it leaves the machine).
   - FACTS: the facts experiments `global.shared.*.step1.n200` hold per-sample levels.
   - If a model has no annual baseline, stop and tell Marcus what would need re-running.
2. **Ask Marcus: mean or median for the central baseline path.** It is not ruled. The mean matches the
   paired-mean pulse difference; the median is what the level figures usually show.
3. **Write the driver**, e.g. `magicc_comparison/poster_agu26/fredi_pulse_coastal_agu26.R`, with constants at the
   top and provenance plus build hash stamped into every output. SLR sectors only, three Coastal Properties
   variants, SSP2. Arms are baseline, baseline + CO2 pulse difference and baseline + CH4 pulse difference.
   `maxYear` is 2300 (2100 headline taken from the same run), or 2100 for FACTS. Temperature input is the
   matching climate's central GMST (FaIR for Ladrillo/BRICK/FACTS, MAGICC for MAGICC-SLR).
4. **Sanity tests before any number** (`climate-modeling` skill):
   - a zero pulse must be bit-identical to the baseline;
   - a sign flip;
   - a doubling, to check linearity at pulse size;
   - that the SLR damages do not change with the temperature input.
5. **Bias check (ruling 4):** at 2100 and 2300 compare mean_i[D(b_i + d_i) - D(b_i)] with D(b + d) - D(b), using
   `SLR-RFF-BRICK/outputs/pulse_{ladrillo,brick2}_draws_vv*_{CO2,CH4}_*_2030_spliced_*.csv` (columns `base_cm`,
   `pulse_cm`, `diff_cm` at horizons 2100/2150/2300). Only Ladrillo and BRICK 2.0 can be checked this way. Say so
   in the caption.
6. **Outputs:**
   - annual marginal damages per model x marker x gas x variant, per GtCO2e (GWP100 29.8);
   - NPV discounted to 2030 at 2 % and 3 %, through 2100 (headline) and 2300 (labelled sensitivity). 3 % is the
     rate relevant to current federal regulatory comparisons; 2 % is for comparability with the SC-GHG
     literature.
   - Then panel I in `make_panels_agu26.py` style.
7. FrEDI pulse damages have never been computed on any basis, so there is no benchmark. Run the quantitative
   pre-check (CLAUDE.md) against the RFF-SP level damages (Coastal Properties $34.9B / HTF $183B per year at 2100,
   calib 1.4.5, FrEDI 4.1.0; `SLR-RFF-BRICK/outputs/fredi_slr_phaseC_rff_baseline_v145_lhs10ks_quantiles.csv`)
   times a local slope.

## 5. Other open items (Marcus's calls; listed in `claims_and_layout.md` status table)

- Panel D: a test definition for "SLR damages may scale with cumulative CH4 emissions". One option is the ratio
  of the 2300 to the 2150 response with paired-bootstrap intervals; a pulse-year or pulse-size ladder would be new
  runs.
- Panel J: the parametric-vs-structural method. Options: a two-way split (draws vs model means), intervals and
  spreads side by side, or the climate-swap shares already computed (CO2 only).
- Panel H: an interval for MAGICC-SLR's CH4:CO2e rate. No per-member SLR, so there is nothing to bootstrap.
- HTF elder mortality: FrEDI has no sector. Drop it, or show Sheahan 2025 as context, as the Chapman poster's
  panel J did (`SLR-RFF-BRICK/python/scripts/poster/sheahan_table.py`).
- Dollar year: FrEDI's 2015$ or 2020$.
- Panels A (schematic) and G (agreement map) are unblocked but not started.

## 6. Hygiene

- FaIRtoFrEDI `heat-ed-morbidity` and SLR-RFF-BRICK `ladrillo-dev` are shared with other sessions. Stage files by
  name, never `git add -A`, and ask before pushing.
- The GMD session owns `SLR-RFF-BRICK/deliverables/GMD*`, `deliverables/redline/`, `figures/paper/`,
  `python/ladrillo_figs.py`, `python/plot_vv_*` and the Ladrillo.jl repo. Do not edit them.
- Log work, including what was tried and dropped, in FaIRtoFrEDI `CHANGELOG.md`.
- Memory: `agu26_pulse_poster_rulings` (pointer in `INDEX_cmp_pulse.md`). Read `INDEX_fredi_vehicle.md`,
  `INDEX_fredi_power.md` and the `fredi-quirks` skill before the FrEDI run. ⚠ The skill's item 3 (two SLR sectors)
  and item 7 (socioeconomics-independent coastal damages) describe 4.x and are wrong for this build.
