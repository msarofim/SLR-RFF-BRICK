# Handoff — a FRESH-EYES BRIEF for a spinoff session (Fable 5.1): what are we missing?

**Purpose.** This is not a continuation handoff. It is a **review brief**. A different model is
being pointed at the Ladrillo sea-level work specifically to find what the incumbent session has
been blind to. Read it adversarially. The most valuable output is a defect or an improvement we
have not seen — not a confirmation.

**Repo** `SLR-RFF-BRICK`, branch `ladrillo-dev`, all pushed. Companion documents:
`notes/note_2026-09-01_vintage_comparison_L21_L23_L24_L25.md` (vintages),
`notes/scoping_2026-09-02_te_rate_vs_observations.md` (the thermal-expansion arc, 3 addenda),
`LADRILLO.md` (the standing definition), `deliverables/LadrilloUpdateDescription_L24.docx`.

⚠ **Read `~/.claude/CLAUDE.md` and the project `CLAUDE.md` first.** In particular: memory lives in
a TIERED index (`MEMORY.md` is a pointer file; the sub-indexes are NOT auto-loaded and must be read
explicitly — `INDEX_slr.md`, `INDEX_ais.md`, `INDEX_cmp.md`, `INDEX_diag.md` are the relevant ones
here). Answering from the root index one-liners is the documented failure mode.

---

## 0. WHAT THE MODEL IS, IN ONE PARAGRAPH

Ladrillo is a BRICK 2.0 derivative: a calibrated, global-only sea-level emulator driven by FaIR
2.2.4 (fair-calibrate 1.6.0 + CMIP7). 58 sampled parameters — 17 Antarctic, 9 Greenland, 19
glacier, 13 other. Champion posterior is **L24** (promoted 2026-09-02), 4 chains x 2M, accepted on
the deliverable criterion. Components: glaciers (3 regional reservoirs, Mengel equilibrium +
Nauels-nu transient), Greenland (2 basins x fast/slow channels), Antarctica (DAIS with 7 freed
geometry parameters), thermal expansion (`alpha x OHC`), land-water storage.

---

## 1. ⛔ RULED OUT WITH POWER — DO NOT RE-DERIVE THESE

Each of these cost real time and each is measured, not argued. Re-running them is waste; the
useful move is to attack the *measurement*, if you think it is wrong.

| claim | status | the measurement |
|---|---|---|
| The glacier law moved Antarctica by +66 cm | **REFUTED** | It was a dropped `--amp-mu=0.95`. Prior mean moved +0.1400, posterior followed +0.1386, ratio 0.990, on a parameter measured prior-dominated. |
| The glacier law is visible in the likelihood | **NULL WITH POWER** | <=7.3e-05 log-units, against 1.86 for a 1 % glacier-parameter wiggle and 11.4 for 1 % of amp. 4-5 orders of headroom. |
| The proposal covariance moved the posterior | **REFUTED** | L25 (L23 config + L21/L22 covariance) lands 0.7 se from L23. Its effect is INSIDE the RNG-only noise floor (median shift 0.029 sd vs 0.046 sd from seed alone). |
| An OHC depth split would fix thermal expansion | **REFUTED TWICE** | Empirically 2026-08-29 (FaIR and IGCC agree on the vertical partition); and on physics 2026-09-02 — 5 of 6 box splits need a NEGATIVE coefficient, and for ANY re-mapping the high-alpha epoch is deeper-weighted than the low-alpha one, so any monotone alpha(depth) has the wrong SIGN. |
| Thermal expansion's coefficient is wrong | **REFUTED** | Against OBSERVED OHC a single constant alpha ~0.11 fits all three epochs to 3 %; the fit's 0.11252 is inside that range. The defect is FaIR's OHC (~22 % fast in the altimetry era), shared with BRICK 2.0. |
| The steric noise model explains the TE residual | **REFUTED** | L22 capped the AR(1) marginal by 64 %; the residual did not collapse. |

---

## 2. ⭐ WHERE I THINK WE ARE MOST LIKELY WRONG — attack these first

Ordered by how much I distrust them. These are my own suspicions about my own work.

**2.1 The Antarctic band is a PRIOR, and nobody has audited that prior.**
`antarctic_lambda` carries **78 %** of the ssp585/2300 AIS width, and `ais_gmst_amp` is
prior-dominated at every width tried (posterior sd / prior sd = 0.95-0.99) while carrying **386 cm
per unit** at 2300. So the headline uncertainty at 2300 is a *stated* uncertainty, not an inferred
one. **We have never seriously interrogated whether those priors are right** — only whether the
data constrain them (measured: they do not). ⚠ A fresh reading of the paleo/`lambda` literature is
probably the single highest-value thing in this list.

**2.2 The amp prior is GAUSSIAN on a demonstrably right-skewed quantity, and we know it and shipped
it anyway.** CMIP6 empirical p17 0.934 / median 1.095 / p83 1.348 — upper half-width 0.253 against
lower 0.161, a **1.57x asymmetry**. N(1.09, 0.180) reproduces p17 (0.923) and **understates p83
(1.267, short by 0.081 ~ 31 cm at 2300)**. The AIS response is CONVEX in amp, so the tail is where
the risk is, and Marcus's own standing rule prefers empirical percentiles to `mean +/- sigma` on
skewed quantities. ⚠ Counter-evidence, recorded honestly: at n=34 the asymmetry is NOT resolved
(bootstrap 68 % CI on the p83/p17 ratio [1.06, 2.14]; P(ratio >= 1.56 | Gaussian) = 0.123). **Both
things are true.** Is shipping a Gaussian defensible, or is that a 31 cm understatement hiding
behind an underpowered test?

**2.3 We accept a posterior with 19 unconverged parameter marginals.** The "accepted on
deliverable" criterion says projected SLR converges (R-hat 1.008/1.011, ESS ~1050) even though the
AIS-geometry ridge does not. That has been the standing practice since 2026-07-19. ⚠ **Is it
sound?** A ridge that never mixes means the reported band is conditioned on where the chains
happened to sit. We have argued this is fine because the deliverable converges. A fresh look at
whether that argument actually holds — and what it would take to break it — would be valuable.

**2.4 The Greenland tap is likelihood-inert and is a stated structural choice.**
V = 5.64 m, tau = 800 yr, onset 4.69 K. It acts entirely after the observational record, so no data
can inform it, and it is ON in the shipped deliverable. ⚠ It changes ssp585/2300 Greenland by
**41.3 cm** (measured tap effect). That is a large number resting on a judgement.

**2.5 The D2 discrepancy absorbs 0.663 cm of steric at 2025.** The fit is allowed to run thermal
expansion high and buy the residual off in a discrepancy term whose prior carries 0.45 % of the
posterior precision. We have argued this is legitimate (the term is orthogonal to S(t) by
construction). ⚠ Is it? Or is a structural misfit being laundered?

**2.6 ⚠⚠ A LIVE RESULT I DO NOT TRUST, computed today.** Ladrillo's **overshoot penalty**
(SSP5-3.4-OS minus SSP1-2.6, total GMSL at 2300) is **1.1 cm = 0.01 m**, against SLEIP Phase 1's
**0.1-0.3 m** across seven emulators — an order of magnitude low. The tempting story is that
Ladrillo's new floored-equilibrium glacier law lets it regrow and recover where melt-only models
cannot. **I do not believe that is the whole explanation.** Our own driver may be doing it:

    yr    OS GMST   126 GMST      dT     SLR penalty
    2100    2.043      1.900   +0.142        5.2 cm
    2150    1.715      1.779   -0.063        4.0 cm
    2300    1.733      1.815   -0.082        1.1 cm

**Our SSP5-3.4-OS ends 0.082 K COOLER than our SSP1-2.6**, and the penalty tracks that residual dT
almost exactly. So the small penalty is not cleanly a statement about committed sea level. ⚠ **Do
not repeat the 0.01 m figure as a model finding until this is separated.** The decisive test is to
compare against SLEIP's own scenario pair on a matched dT, or to re-run the penalty at a horizon
where the two drivers actually agree in temperature.

---

## 3. PROCESS DEFECTS THAT KEEP RECURRING — a fifth instance is likely present and unfound

This project's dominant failure mode is **not** bad physics. It is a configuration or label that is
silently wrong while everything reports success. Four instances in the last three days:

1. `--gis-ordered --gis-basins2` dropped (quarantined `20260831_l23_missing_gis_flags`).
2. `--adcov` dropped — L23 onward inherited an older tuning covariance.
3. `--amp-mu` dropped — **this one produced a headline result that had to be retracted.**
4. `--tap` omitted from a deliverable-arms script I wrote 2026-09-02; caught after one marker by
   listing what the predecessor vintage actually had.

Plus a documentation instance the same day: a rebuild shipped **1 figure instead of 6** with every
step exiting 0, caught only by an archive check.

⚠ **The common shape: an absent flag does not error — it selects a default, and the default is not
the predecessor's value.** L23 and L24 have the SAME original command line and DIFFERENT priors,
because `AMP_SIGMA`'s default moved between their run times.

**A genuinely useful contribution would be to find the fifth.** Suggested attack: for every
`_argval(` / `--flag` in `julia/calibrate_mcmc_ext.jl`, ask what its default is, whether that
default has ever changed, and whether any shipped vintage relied on it implicitly. Mitigations now
in place: every vintage has a pinned `run_mcmc_<TAG>.sh` with an arm-verification block, and the
calibrator prints whether the proposal covariance was CHOSEN or INHERITED.

---

## 4. THE EXTERNAL BENCHMARK WE JUST ACQUIRED

**SLEIP Phase 1**, egusphere-2026-3874 (Nauels, Wong, Mengel, Nicholls, Smith, Kopp, Slangen et al.)
— the formal sea-level emulator intercomparison. 13 datasets, 7 emulators (BRICK, FACTS, FRISIA,
MAGICC, MP25, ProFSea, SURFER), to 2300, run on native AND common-MAGICC forcing. **The author list
is essentially everyone Ladrillo is built on.**

* 2300 p-box SSP2-4.5: **2.08 m (0.97-11.00)**. Ladrillo L24 gives **2.49 m** — inside, ~20 % above
  their central. Not an outlier.
* Their finding "structural differences dominate over climate forcing, AIS the largest uncertainty"
  **converges with ours independently**, and ours is the mechanistic version (which parameters, and
  that they are priors).
* Their caveat "the consistency of thermal expansion and glacier contributions reflects **shared
  parametrizations**, not independent agreement" is something we can **quantify**: Ladrillo's
  glacier transient IS MAGICC's law (Nauels 2017 Eq. 3), and Ladrillo and BRICK 2.0 miss the same
  TE cell on the same FaIR driver with independent posteriors.
* ⭐ Their **0.1-0.3 m overshoot penalty** is §2.6 above. **This is the sharpest open question in
  the project right now.**

---

## 5. HOW TO RUN THINGS

    source ~/climate-env/bin/activate            # python
    julia --project=julia_v2 ...                 # julia

    python python/bench_ladrillo.py --tag=L24                 # the standing benchmark
    python python/diag_amp_by_vintage.py                      # amp by vintage, cached, ~1 s
    python python/diag_te_rate_attribution.py --tag=L24       # the TE decomposition
    bash run_mcmc_L24.sh                                      # reproduce the champion (pinned)
    bash run_l24_deliverable_arms.sh                          # the 16 projection arms (tapped)
    bash build_l24_deliverable_doc.sh                         # figures + docx, gated on figure count

⚠ **Chains are ~2.2 GB each and a refit is ~3 h for 4 x 2M.** Check `uptime` and what is already
running before launching; an ETA in days is contention, not a slow run. Pin BLAS threads.

⚠ **Read `benchmark/champions.json` before trusting any "champion" statement** — it carries `why`,
`correction_2026-09-01`, `resolution_2026-09-01b` and `prior_promotion_2026-09-01`, because the
previous promotion's reasoning was retracted and that history is deliberately preserved.

---

## 6. WHAT WOULD MAKE THIS REVIEW A SUCCESS

In descending order of value:

1. A defect in §2 that we have argued ourselves out of — especially §2.1 (the unaudited AIS priors)
   or §2.6 (the overshoot penalty).
2. The fifth dropped-flag / silent-default instance (§3).
3. A structural improvement to the model we have not considered. ⚠ Check §1 first: several obvious
   candidates are already dead, and the reasons are measured.
4. A reason the "accepted on deliverable" convention (§2.3) is not sound.

⚠ **Please do not** produce a summary of what is already here, or re-derive anything in §1. The
incumbent session's blind spots are the target, and by construction they are not in this list —
this list is what it CAN see.
