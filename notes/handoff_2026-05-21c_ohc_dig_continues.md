# Handoff — 2026-05-21 — OHC calibration diagnostic continues (pre-Tony-email)

This is a **forward-looking** handoff — the OHC diagnostic is *not* closed.
A fresh Claude session should be able to pick up cold and continue the dig
by reading this note plus `~/.claude/CLAUDE.md`, the project `CLAUDE.md`,
and the auto-memory at
`~/.claude/projects/-Users-MarcusMarcus-Documents-2026-CodeProjects-FaIRtoFrEDI/memory/`.

Companion handoffs (read in order):
1. `notes/handoff_2026-05-20_tony_wong_followup.md` — original Tony scope.
2. `notes/handoff_2026-05-21_julia_per_component_done.md` — Julia per-component + obs-driven driver landed.
3. `notes/handoff_2026-05-21b_brick_calibration_diagnostic.md` — full diagnostic session writeup (mid-day 2026-05-21).
4. **This handoff** — IGCC addition + continued-dig framing (afternoon 2026-05-21).

## 1. Why the email to Tony is on hold

The 6-product OHC comparison built this afternoon
(`outputs/substack/gouretski_vs_cheng_ohc.png`) revealed two things that
make the original "BRICK calibration mismatch" framing less crisp than
we thought yesterday:

1. **FaIR's own ensemble-mean OHC trajectory lands within 7% of SNEASY MAP**
   over 1971-2018 (38.0 vs 40.7 × 10²² J). The "BRICK is calibrated for
   something we can't reproduce" framing is wrong — **BRICK's calibration
   target IS approximately what FaIR produces**.

2. **FaIR, Gouretski, and IGCC all agree reasonably well over post-1960.**
   Specifically:
   - IGCC 2024 ΔOHC 1971-2018: +36.94
   - FaIR mean ΔOHC 1971-2018: +38.01
   - SNEASY MAP ΔOHC 1971-2018: +40.65
   - Cheng IAPv4.2 ΔOHC 1971-2018: +31.04 (the LOW outlier)
   - Zanna 2019 ΔOHC 1971-2018: +27.40 (also LOW, ~25% below IGCC)
   - Gouretski overlaps to 1996 only; 1971-1996 trend close to IGCC.

So before drafting the email, Marcus wants more digging to confirm this
recharacterization and figure out where the residual undershoot in our
pipeline actually comes from.

## 2. Status of artifacts

### Code (committable but currently uncommitted)

| file | role | status |
|---|---|---|
| `julia/test_sneasy_default.jl` | default-mode BRICK (no posterior, SNEASY internal) | tested ✓ |
| `julia/test_sneasy_posterior.jl` | Tony-mode (posterior + SNEASY internal) | tested ✓ |
| `julia/run_mimibrick_obs_driven.jl` | obs-driven driver (existed yesterday) | tested ✓ |
| `python/build_ohc_spliced.py` | Zanna+Cheng splice builder (existing) | OK |
| `python/build_ohc_spliced_igcc.py` | Zanna+IGCC splice builder (new today) | tested ✓ |
| `python/scripts/substack/gouretski_vs_cheng_ohc.py` | 6-product OHC comparison figure | latest |
| `python/scripts/substack/component_overlay_obsdriven.py` | 2×3 component diagnostic | latest |
| `python/scripts/substack/component_overlay_tony_style.py` | Tony-recipe replication | latest |

### Outputs

- `outputs/substack/gouretski_vs_cheng_ohc.{png,pdf}` — 6-product OHC, 1870-2024, 1971-zero baseline.
- `outputs/substack/component_overlay_obsdriven.{png,pdf}` — per-component diagnostic with Gouretski caveat.
- `outputs/substack/component_overlay_tony_style.{png,pdf}` — direct Tony-recipe reproduction.
- `outputs/brick_sneasy_posterior_diagnostic.csv` — Tony-mode (100 members) at landmark years.
- `data/observations/ohc_spliced_zanna_cheng.csv` — original splice.
- `data/observations/ohc_spliced_zanna_igcc.csv` — new IGCC splice (1850-2024).

### Memory entries (in priority order)

- `project_brick_calibration_input_mismatch.md` (with Tony-mode verification)
- `project_brick_gouretski_calibration_target.md`
- `project_igcc_ohc_finding.md` (latest, including 6-product comparison + FaIR≈SNEASY finding)
- `project_brick_component_biases_vs_frederikse.md`
- `project_brick_lws_calibration_convention.md`
- `project_brick_five_components.md`
- `project_ohc_splice_provenance.md`
- `project_tony_obs_vs_fair_attribution.md`

## 3. Immediate next experiments (in priority order)

### 3.1 Smooth SNEASY MAP for visual comparability — START HERE

The current SNEASY MAP line in `gouretski_vs_cheng_ohc.py` is extremely
noisy at annual resolution (±20 ZJ year-to-year, much larger than any
other product). This visual noise obscures the trend agreement with FaIR
and IGCC that's actually present.

**Action:** add an 11-year centered running mean of SNEASY MAP alongside
(or replacing) the raw trace. The smoothed SNEASY should track FaIR mean
within ~5% over 1971-2018.

Implementation hint:
```python
sneasy_smooth = sneasy.rolling(window=11, center=True, min_periods=6).mean()
```

Worth keeping the raw trace at low alpha to show the noise honestly, with
the smoothed line on top.

### 3.2 Quantify post-1960 agreement across FaIR/Gouretski/IGCC

Marcus's observation: "FaIR, Gouretski, and IGCC all agree reasonably
well over the post-1960 period." Verify with explicit numbers:

- ΔOHC 1960-1996 for FaIR / Gouretski / IGCC / Cheng / Zanna
- Linear trends over 1960-1996
- Compute pairwise RMS difference (after baselining to 1971-zero)
- Aim for a table that shows which products are mutually consistent and
  which are outliers.

This goes into the email body as a soft-landing for the calibration
conversation: "the modern OHC products agree to within X% in trend; the
disagreement is in the early-record (pre-1960) period."

### 3.3 Re-run obs-driven BRICK with Zanna+IGCC splice

Replace `data/observations/ohc_spliced_zanna_cheng.csv` input with
`data/observations/ohc_spliced_zanna_igcc.csv` in the obs-driven driver,
re-run for the `obs_obs` combo (IGCC GMST + IGCC OHC), and see if TE
moves closer to Frederikse Steric.

Predicted (from the 16% IGCC > Cheng increase over 1971-2023, scaled to
~1.16× TE):
- Previous obs_obs TE at 2018: +0.67 cm
- New prediction with IGCC OHC: ~+0.78 cm (still 3× under Frederikse 2.3)

Predicted (from the steeper 1971-1996 IGCC > Cheng ratio of 1.57×):
- TE response in the calibration window scales 1.57× → modest movement
  but probably not enough to close the gap.

Run is fast — modify the obs-driven SLURM submission to point at the new
CSV, ~3 min on Torch.

### 3.4 The bigger experiment: posterior + FaIR-mean OHC (not SNEASY)

If FaIR mean ≈ SNEASY MAP within 7%, then feeding BRICK FaIR-mean OHC
should produce TE close to Tony-mode TE. Our existing obs_fair combo
(obs GMST + FaIR-mean OHC) already does this in spirit. Compare:
- `outputs/brick_obsdriven_obs_fair_to2024.csv` TE at 2018
- `outputs/brick_obsdriven_fair_fair_to2024.csv` TE at 2018
- Tony-mode predicted TE at 2018 (2.71 cm verified)

If obs_fair and fair_fair TE are also ~2.7 cm at 2018, then **the original
FaIR cube already produces a Tony-equivalent BRICK response — the
calibration mismatch only appears when we feed obs OHC**. That would be a
clean story to land with Tony.

Look at the existing CSV — no new BRICK runs needed.

### 3.5 Why is Zanna 2019 ~25% below IGCC modern?

Zanna 2019 is a Green's function reconstruction tuned to early-period
data; IGCC 2024 includes multiple modern reanalyses (IAP/Cheng, NCEI,
Met Office). The 25% gap over 1971-2018 is large for two products both
claiming "ocean heat content reconstruction." Worth understanding:

- Is Zanna's depth integration different from IGCC's 0-2000m? (Zanna has
  multiple depth options: OHC_300m, OHC_700m, OHC_2000m, OHC_below_2000m,
  OHC_full_depth. We used OHC_2000m.)
- Does Zanna underrepresent post-2000 acceleration because its method
  weights early-period data?

Could check Zanna OHC_full_depth vs IGCC ocean_full-depth to remove
depth-integration as a confound.

### 3.6 The principled fix: FaIR-coupled BRICK via Tony's MAGICC pattern

The raddleverse master branch of MimiBRICK has a public `magicc_sampling`
hook in `run_projections.jl` that overrides `:model_global_surface_temperature`
with MAGICC-derived inputs. Tony offered the FaIR equivalent (from his
EDF work) but it's in his personal branch.

**Two ways to proceed:**

(a) Wait for Tony to share the FaIR hook (one of the email's "asks").

(b) Mirror the MAGICC pattern ourselves — write a `fair_sampling=true`
    branch in our local `run_projections.jl` copy, ~1-2 days of Julia
    work. Lets us feed FaIR-derived inputs through BRICK's *internal*
    plumbing (proper handling of `:ocean_heat_mixed` + interior, all
    posterior parameters applied correctly). This is the principled fix.

Given the FaIR ≈ SNEASY finding from § 1, (b) is likely to work well —
FaIR's OHC magnitude is in BRICK's calibrated range.

## 4. Open questions / unverified hypotheses

- Does ANY BRICK setup (default + IGCC inputs, posterior + IGCC inputs,
  posterior + FaIR inputs) reproduce Frederikse Steric +5.68 cm at 2018?
  Or is the ~2× TE undershoot vs Frederikse a deeper feature?
- Is BRICK's Steric posterior actually narrow enough to call it "low"?
  Check the posterior te_α distribution — what fraction of posterior
  members would, with IGCC OHC, give TE ≥ Frederikse?
- For the AIS historical overshoot (BRICK ~−4 cm vs Frederikse −0.6 cm at
  1900) — is that a Wong-calibration-vintage issue, or persistent across
  newer BRICK calibrations? The raddleverse master may have a more recent
  posterior; worth checking version history.

## 5. Reproducible commands

```bash
# Re-render the 6-product OHC comparison
cd ~/Documents/2026/CodeProjects/SLR-RFF-BRICK
source ~/climate-env/bin/activate
python3 python/scripts/substack/gouretski_vs_cheng_ohc.py
```

```bash
# Rebuild Zanna+IGCC splice
python3 python/build_ohc_spliced_igcc.py
```

```bash
# Tony-mode BRICK (posterior + SNEASY internal)
cd julia
julia --project=. test_sneasy_posterior.jl
```

```bash
# Default-mode BRICK (no posterior, SNEASY internal)
julia --project=. test_sneasy_default.jl
```

## 6. The pending Tony email

Outline lives in this session's transcript. Key changes from the original
draft (yesterday) to the new draft (after IGCC addition):

- **Old headline:** "BRICK calibrated against Gouretski OHC which is 2× modern Cheng — calibration mismatch causes our TE undershoot."
- **New headline:** "Our pipeline's TE undershoot was traceable to feeding BRICK Cheng IAPv4.2 alone, which is the low-side outlier among modern OHC products. IGCC, FaIR, SNEASY, and Gouretski all cluster in the +37-41 ZJ range over 1971-2018; Cheng sits at +31 and Zanna at +27."
- **New ask of Tony:** "Does the BRICK community see Cheng IAPv4.2 as a reliable single-product or always use the IGCC compilation?"

**Don't send the email until § 3.1-3.4 experiments are run and the
post-1960 agreement is quantified.** That's a hardening pass that makes
the email much more credible.

## 7. Things a fresh session should NOT do

- Don't characterize "BRICK was calibrated against an outlier" as the
  headline. The 6-product comparison reframes that — see § 1.
- Don't relitigate the verified findings in `project_brick_*` memory
  entries. The Gouretski/Cheng/IGCC numbers are pinned.
- Don't re-run Tony-mode BRICK without `MAX_POST=10000` if you want
  better-than-100-member posterior coverage. Default is 100 (fast); for
  publication-quality, override the env var.
- Don't believe agent-reported claims about BRICK source without
  verifying against `~/.julia/packages/MimiBRICK/bpCAF/`. This project
  has caught two agent-reported "bugs" that were actually correct code.

## 8. Where this work fits

If 3.1-3.4 line up to confirm "the pipeline issue was the OHC product
choice, not a fundamental incompatibility between BRICK and FaIR," then
the natural sequence is:

1. Email Tony with the refined story (and request his FaIR hook).
2. Implement the FaIR-coupled BRICK (option § 3.6, either Tony's hook or
   our own MAGICC-pattern mirror).
3. Re-run the LHS-10k canonical bands with FaIR-coupled BRICK, generate
   updated SLR percentile bands.
4. Pulse experiments (the 9-cube design from
   `notes/handoff_2026-05-20_tony_wong_followup.md` § 2.2) all flow
   through the FaIR-coupled pipeline.

The ensemble redesign (D vs E from
`notes/ensemble_design_proscons_2026-05-20.md`) is independent of this
and can run in parallel.

The AGU Chapman poster deadline ~2026-06-01 (memory
`project_agu_chapman_poster.md`) becomes relevant once the
FaIR-coupled BRICK lands — the per-component panels can then show
honest obs-vs-model agreement instead of caveat-heavy ones.
