# Scoping — does IMBIE 2026 warrant a STRUCTURAL change to DAIS? (2026-09-21, while L28 runs)

**Question (Marcus):** with the reconciled ice-sheet record (Otosaka et al. 2026, Sci Data 13:1301; AIS 1979–2023 with an
SMB / dynamics split, WAIS / EAIS / AP), is the Antarctic hindcast deficit a parameter problem (the refit fixes it) or a
structure problem (DAIS cannot produce what is observed)?

**Receipts:** `python/diag_imbie2026_vs_targets.py --tag=L27` (CHANGELOG 09-21f), `julia/diag_ais_flux_split_vs_imbie.jl
--tag=L27 1000` (DAIS's own β_total / ice_flux per draw on the calibration span; outputs
`diag_ais_flux_split_vs_imbie{,_draws}_L27.csv`), the IMBIE Gt files, `fair_mean_gmst_ssp245harm.csv`.

## 1. What the observed record is made of (IMBIE 2026, Gt/yr, ice-mass sign)

| window | AIS net | SMB anom. | dynamics anom. | WAIS dyn | EAIS dyn | AP dyn | GMST (K) |
|---|---|---|---|---|---|---|---|
| 1979–1991 | −47 | +14 | −62 | −34 | −24 | −5 | 0.456 |
| 1992–2002 | −79 | −7 | −73 | −56 | −7 | −11 | 0.580 |
| 2003–2010 | −158 | −1 | −157 | −118 | +2 | −45 | 0.862 |
| 2011–2017 | −200 | −21 | −179 | −159 | +5 | −28 | 1.033 |
| 2018–2023 | −104 | **+144** | −249 | −192 | −8 | −21 | 1.206 |

- The loss is **dynamics** (84 % of 1979–2023) and it is **WAIS** (−34 → −192); EAIS is in balance; the Peninsula is small.
- The dynamics anomaly is **near-linear in GMST**: on 11-yr means, −232 Gt/yr per K with residual sd 22 Gt/yr and no
  window residual above 14; a quadratic term buys 2 Gt/yr of residual. **No lag is visible** (the fit needs none).
- The 2018–2023 slowdown is **entirely SMB** (+144 Gt/yr; the record EAIS snowfall) — dynamics kept accelerating.
- SMB interannual sd is 123 Gt/yr (0.034 cm/yr); a 7-yr window mean carries an se of ~45 Gt/yr.

## 2. What DAIS does on the same span (L27 posterior, 1000 draws, medians; Gt/yr)

| window | SMB | discharge | net | dyn anomaly vs 1979–2008 | level rate (cm/yr) | IMBIE rate |
|---|---|---|---|---|---|---|
| 1979–1991 | 1845 | −1889 | −46 | +23 | 0.011 | 0.013 |
| 1992–2002 | 1847 | −1909 | −64 | +1 | 0.015 | 0.022 |
| 2003–2010 | 1854 | −1960 | −107 | −54 | 0.026 | 0.044 |
| 2011–2017 | 1864 | −1991 | −128 | −85 | 0.031 [0.026, 0.034] | 0.056 |
| 2018–2023 | 1874 | −2026 | −151 | −121 | 0.036 | 0.029 |

- **The partition matches**: DAIS puts the loss in the discharge, and its discharge anomaly tracks GMST like IMBIE's
  (change 1979–91 → 2011–17: model −108 Gt/yr, IMBIE −117 — **92 %**; ratio of modern to early net loss 2.8 vs
  IMBIE's dynamics ratio 2.9).
- **The gap in the acceleration window is more SMB than discharge.** 1992–2002 → 2011–2017: IMBIE net −121 (dyn −106,
  SMB −14); L27 net −64 (dyn −82, **SMB +17**). Discharge reaches 77 % of the observed change; DAIS's precipitation
  rises with warming (κ) while the RCM-based SMB anomaly fell 35 Gt/yr — a difference of ~31 Gt/yr that is **inside the
  SMB anomaly's own noise** (se ~45 for a window mean; the trend is not significant in the RCMs either).
- **The old posterior cannot reach the observed acceleration**: 2011–17 minus 1992–2002 rate is 0.015 cm/yr (max over
  1000 draws 0.033) against IMBIE's 0.034; the 2011–17 rate spans 0.026–0.034 across the posterior, IMBIE 0.056 ± 0.007.
  And **no single parameter controls it** (|Spearman| ≤ 0.16 for every AIS parameter) — the posterior sits on the
  compensating ridge the earlier work documented (Table A2). The sensitivity parameters are only partly identified
  (posterior / prior sd: anto_α 0.64, antarctic_α 0.71, T_oc,0 0.66), so the priors leave room for ~2× the sensitivity.
  Whether the likelihood takes it is what **L28 measures**.

## 3. Verdict on structure

**Not warranted by this information.** Every structural feature the reconciled record exhibits is one DAIS already has:
dynamics-dominated loss, discharge responding to (a linear map of) GMST with no visible lag, SMB as a noisy near-zero
anomaly. The deficit is a **magnitude** (77–92 % of the observed discharge response) and a **noise-scale SMB sign**, both
of which the refit can address with existing parameters. Structural candidates, ranked by what the data say:

1. **An ocean lag or basal-melt state variable** — not asked for: the dynamics anomaly is linear in contemporaneous GMST
   (residual sd 22 Gt/yr, no window structure). Adding one would add an unidentified timescale.
2. **A WAIS / EAIS split** — the loss is WAIS-only, but a single disc reproduces the global total's structure; a split would
   be motivated by PROJECTIONS (marine-based WAIS vs EAIS thresholds), which is the existing open Antarctic question, not
   something IMBIE changes. Cost: a Greenland-basins-scale build (weeks), new priors, no historical constraint on the
   EAIS half.
3. **Weaker precipitation–temperature coupling (κ) or an SMB trend term** — the observed 1979–2017 SMB decline is inside
   its own noise; the 2018–23 event is a 6-yr anomaly the AR(1) term absorbs (target σ 0.09–0.12 cm in those years).
   A parameter (κ's prior), not a structure.
4. **Stronger convexity in discharge (T_oc exponent, depth exponent γ)** — DAIS already has T_oc² × depth^γ; IMBIE's
   window pairs hint at convexity (−89 then −234 Gt/yr per K) but the smoothed regression does not (linear suffices).
   Revisit only if L28 lands with the early record fitted and the modern rate still short.

**The one test that would change this verdict:** if L28 — free to use the discharge-sensitivity parameters — still leaves
the 2011–2017 rate > 2σ below IMBIE (i.e. < ~0.042 cm/yr) while fitting the pre-1979 record, then something binds the
sensitivity from above: the near-flat 1900–1978 Frederikse AIS (a GMST-proportional discharge that is large in 2010
loses too much in 1940) or the paleo geometry prior. The discriminating pair of runs is then (a) L28 with the 1900–1978
AIS σ inflated ×3, (b) L28 with the geometry prior widened — which one moves the modern rate names the binding term.
Not launched; decide on L28's postpred.

## 4. L28 landed (17:17) — the pre-registered test, answered

**The threshold was not met.** L28's 2011–2017 AIS rate is **0.039 cm/yr** (p05–p95 0.032–0.045) against IMBIE's 0.056 —
−2.1σ with both bars — below the 0.042 that §3 set as the line. Cumulative 1979–2023 is fitted (1.22 vs 1.33 ± 0.14,
−0.8σ), the 1979–2002 windows are fitted (±0.2σ), and the model overshoots the 2018–23 SMB pause (+0.9σ, as it should).

**How the likelihood took the new target — not with the physics.** Every Antarctic parameter moved ≤ 0.8 L27-sd and the
sensitivity ones moved DOWN (anto_α 0.38 → 0.29, ice-flow₀ 1.20 → 1.06, antarctic_α 0.34 → 0.30; T_oc,0 up 0.94 → 1.03,
anto_β down 1.01 → 0.84). The move is in the noise model: `sd_ais` 0.0216 → 0.0139 (−4 sd), **`rho_ais` 0.89 → 0.97 with its
spread down to 0.35×, against the 0.99 bound** — the AR(1) term absorbs the acceleration as persistent noise (the same
"ρ bound absorbs a smooth bias" mechanism the IC test found in BRICK 2.0's hindcast, CHANGELOG 09-16d).

**What the fit did instead — a level, not a response** (per-draw split, `diag_ais_flux_split_vs_imbie_L28`): the
discharge anomaly over the acceleration window (1992–2002 → 2011–17) is **−50 Gt/yr, DOWN from L27's −82** (IMBIE −106);
SMB now falls (−24; L27 +17; IMBIE −14); the baseline net loss is larger everywhere (1979–2008 −87 vs L27 −64, IMBIE −78).
The cumulative was bought by losing more ice throughout the century: **1900–1978 loss −43 Gt/yr against the target's −20
(L27 −19)**, the 1935 level 0.31 cm below the target (1.4σ of the target's 0.22; benchmark 1920–49 bias −1.86 sd, cov90 0 %).
Projections follow: **SSP2-4.5 AIS 2100 12.6 → 8.1 cm, 2300 178 → 166; SSP5-8.5 38 → 36, 281 → 272; SSP1-2.6 unchanged;
p95s narrower** — fitting the reconciled record made DAIS LESS sensitive to warming, because the record's higher mean loss
was absorbed as a larger standing imbalance rather than a stronger response.

**Why a linear model cannot do it — the number.** Loss per unit GMST on the new target: 1900–78 **−113 Gt/yr K⁻¹**
(GMST 0.17 K), 1978–91 −98 (0.45 K), 1991–2002 −137, 2002–10 −186, 2010–17 **−198** (1.02 K). The ratio doubles across
0.45 → 1.0 K: local exponents 0.85 before 1978, 1.3–2.3 after. DAIS's discharge speed is (1−α) + α·r², r = (anto_α·GMST +
anto_β − T_f)/(T_oc,0 − T_f); at the fitted values r² = 0.87 + 0.19·GMST + 0.01·GMST² — **linear to 1 %**. A linear
response with the modern slope loses 2× too much in 1900–78; with the early slope it is 2× short in 2010–17. L28 split
the difference and let ρ carry the rest. (§1's "linear in GMST" reading was made on 1984–2018 only; the early century is
what breaks it.)

**Revised verdict.** The reconciled record asks for a discharge response that steepens above ~0.5 K of global warming —
convex or threshold-like — and DAIS's is linear over the historical range. That IS a structural gap, and L28 measures its
cost: −2σ on the modern rate, −1.9σ on the early century, ρ pinned, and projections that move the wrong way. The
candidates, now ordered by what the data say:
1. **A reachable steepening in the discharge** — either a free exponent on the ocean-temperature ratio (nests DAIS at 2; one
   parameter; the smallest change) or an onset temperature for the fast-dynamics term within the observed range (λ above
   T_crit already exists; its paleo prior puts T_crit far above present). ⚠ The second reads as "a marine instability
   already under way" and has large projection consequences; the first is a curvature, not a claim.
2. ~~Ocean lag~~ — makes the response smoother, the opposite of what is needed.
3. ~~WAIS/EAIS split~~ — unchanged: a projection motivation.

**The decisive test before any build (Marcus's call, ~4 h each):** L28 with `rho_ais` capped at 0.90 (a `--rho-max` flag; the
bound is the literal 0.99 at `calibrate_mcmc_ext.jl:1490`). If the physics can carry the shape, the sensitivity parameters
move up and the early-century misfit grows; if they cannot, the fit degrades everywhere — either way it names the binding
term. The 1900–78 σ ×3 and geometry-prior arms are second-order now: the early record is a 1.4σ constraint, not the cap.
