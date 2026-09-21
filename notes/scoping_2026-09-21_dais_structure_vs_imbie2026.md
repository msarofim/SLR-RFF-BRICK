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
