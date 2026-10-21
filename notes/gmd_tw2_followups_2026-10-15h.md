# GMD TW2 pass: follow-ups computed after the build (2026-10-15h)

Continues `handoff_2026-10-15b_brick20_swap_tw2_pass.md`. The built docx
(`deliverables/GMD.Ladrillo.v1_review-2026-10-15_L27_TW2.docx`) is unchanged. Everything below is numbers and receipts
for the items the inventory (`deliverables/redline/r1015/tw2_edit_inventory.md`) left for Marcus.

## Item 4 (N01): the α comparison on matched scopes

Receipt: `python/diag_te_alpha_matched_scope.py` → `outputs/diag_te_alpha_matched_scope_L27.csv` (9baec70).

α multiplies FaIR's OHC, which is Earth's total heat uptake, so the matched observation-implied α divides the steric
target's rate by IGCC's total heat rate. Ladrillo L27 α ÷ observation-implied α (OLS rates, common window):

| window | per 0–2000 m ocean (draft's basis) | per full-depth ocean | per total Earth heat (matched) |
|---|---|---|---|
| 1993–2020 | 0.974 | 1.079 | 1.183 |
| 2006–2020 | 1.010 | 1.113 | 1.225 |
| 1971–2020 | 0.990 | 1.082 | 1.184 |

- In parameter units the posterior median is 0.167 (5–95 % 0.148–0.186). The matched observation-implied value is 0.141
  (1993–2020), below the posterior's 5 % bound.
- BRICK 2.0 (Zenodo posterior) on the matched scope: 1.095 (1993–2020).
- There is no formal error bar. IGCC publishes level errors only, and its non-ocean terms end in 2020.
- Sentences affected: Sect. 2.2.4 ("within 4% of the value the 0–2000 m observations imply") and Sect. 4.1
  ("Despite Ladrillo's expansion coefficient being within 4% of the value implied by the observations").

## Item 7 (N02): the post-2002 Antarctic rate, per draw

Receipt: `python/diag_ais_rate_2002_per_draw.py` → `outputs/diag_ais_rate_2002_per_draw_L27.csv` (4108e55).

The item came from Claude's 10-02 reading of Lin et al. 2026, whose emulator is calibrated over 2002–2021. Rates are OLS
in mm/yr over all 10,000 posterior rows on the calibration driver. Observation standard errors are AR(1)-inflated scatter.

| window | L27 p05 / p50 / p95 | BRICK 2.0 p05 / p50 / p95 | target (Frederikse + GRACE) | IMBIE 2026 |
|---|---|---|---|---|
| 2002–2021 | 0.248 / 0.294 / 0.331 | 0.230 / 0.333 / 0.527 | 0.423 ± 0.029 | 0.524 ± 0.048 |
| 2002–2023 | 0.255 / 0.302 / 0.339 | 0.224 / 0.331 / 0.533 | 0.393 ± 0.038 | 0.498 ± 0.062 |
| 2002–2025 | 0.262 / 0.310 / 0.348 | 0.217 / 0.329 / 0.541 | 0.372 ± 0.049 | record ends 2023 |

- Every L27 draw is below the target through 2021 and 2023, and 99.5 % through 2025. For BRICK 2.0 the shares are
  82 / 75 / 68 %.
- The gap shrinks with the end year because the target's rate from 2002 falls (0.42 → 0.37).

## Item 7 (N02), added 10-17: the 2100 Antarctic comparison with Lin et al. 2026

Receipt: `julia/diag_ais_2100_vs_lin2026.jl` → `outputs/diag_ais_2100_vs_lin2026_L27.csv`, run against Ladrillo.jl
v1.3.0. **Comparator ruled (Marcus 10-17): Lin's drift-corrected row.** The raw-simulation rows are not used. Source: Lin et al. (2026), Nat. Geosci., doi:10.1038/s41561-026-02102-1, Table 1 and Methods
(`ClaudeDocs/Papers/s41561-026-02102-1.pdf`).

**Basis.** Lin's 2100 values are the change since 2015 (ISMIP6 projections start in 2015). Ladrillo and BRICK 2.0 are put on
that basis per draw: AIS(2100) − AIS(2015) in each draw of the paper's joint arm, built exactly as Ladrillo.jl's
`project_joint.jl` and `brick20_joint.jl` build it. Each draw is run a second time with `antarctic_lambda = 0`, which switches
off DAIS's fast-dynamics flux and nothing else (a draw whose fast dynamics never fire by 2100 is bit-identical).

2100 Antarctic contribution, cm SLE since 2015, median (16–84) [5–95]:

| | SSP2-4.5 | SSP5-8.5 |
|---|---|---|
| Lin, posterior, drift-corrected | 5.2 (2.8–7.8) [1.2–9.7] | 7.7 (3.8–12.2) [1.9–16.2] |
| Lin, posterior high-end, drift-corrected | 7.9 (4.8–10.7) [2.9–11.1] | 14.9 (10.6–21.2) [7.7–25.2] |
| Ladrillo L27 | 10.0 (4.5–40.6) [3.8–57.2] | 36.3 (19.2–56.0) [6.9–69.3] |
| Ladrillo L27, λ = 0 | 5.4 (4.2–7.3) [3.6–8.8] | 7.5 (5.6–10.4) [4.6–12.9] |
| BRICK 2.0 | 22.0 (2.2–46.8) [0.8–66.6] | 37.6 (22.1–59.0) [13.7–78.4] |
| BRICK 2.0, λ = 0 | 2.1 (0.4–4.6) [−0.8–7.3] | 1.8 (−0.4–5.7) [−2.1–10.2] |

| | SSP2-4.5 | SSP5-8.5 |
|---|---|---|
| Ladrillo draws whose fast dynamics fire by 2100 | 56 % | 95 % |
| fast dynamics' share of Ladrillo's median change | 46 % | 80 % |
| BRICK 2.0 draws firing by 2100 | 72 % | 99.5 % |
| fast dynamics' share of BRICK 2.0's median change | 91 % | 95 % |
| Ladrillo draws above Lin's posterior 95th percentile | 51 % | 88 % |
| Ladrillo draws above Lin's high-end 95th percentile (11.1 / 25.2 cm) | 49 % | 74 % |
| BRICK 2.0 draws above Lin's posterior 95th percentile | 64 % | 93 % |
| BRICK 2.0 draws above Lin's high-end 95th percentile | 63 % | 77 % |

- With λ = 0, Ladrillo's medians and 5–95 % ranges fall inside Lin's posterior (5.4 vs 5.2 cm; 7.5 vs 7.7 cm). The
  difference from Lin at 2100 is the fast-dynamics channel.
- BRICK 2.0's 2100 Antarctic change is almost entirely fast dynamics; without it, its medians are below Lin's.
- Lin's high end (14.9 cm, SSP5-8.5) comes from ISMIP6 processes (ocean warming, melt parameterization, sliding law,
  ice-shelf collapse). Lin's Methods say no ISMIP6 experiment includes MICI. DAIS's fast dynamics is a constant flux λ
  above an Antarctic temperature threshold, with (λ, T_crit) from the paleo prior (`ais_spread_is_lambda_prior`).
- Record conditioning: Ladrillo's joint arm drops draws that fire by 2025 (1,997 kept). No BRICK 2.0 draw fires by 2025,
  so BRICK 2.0's unconditioned arm is like-for-like on that point.

**Lin's calibration quantity.** Lin scores the emulated 2015–2021 rate against 0.44 ± 0.04 mm/yr (King et al. 2023,
2002–2021, decadal variability removed). Ladrillo's 2015–2021 rate in the same runs is 0.341 (5–95 % 0.276–0.427) mm/yr;
BRICK 2.0's is 0.317 (0.182–0.612). The three SSPs give identical rates because the CMIP7-basis forcing shares its history
through 2024 (checked: max |ΔGMST| between SSPs is 0 through 2024).

**Warming, like for like.** Lin's GMST is 500 FaIR v1.x projections "similar to those used in IPCC AR6". Ladrillo's paired
FaIR 2.2.4 (calib 1.6.0) configs, 2081–2100 relative to 1850–1900, median (5–95): SSP2-4.5 2.52 (1.87–3.67) K, SSP5-8.5 3.75
(2.84–5.28) K, against AR6 WG1 Table SPM.1's 2.7 (2.1–3.5) and 4.4 (3.3–5.7) K. Ladrillo's climate is cooler, so the warming
difference does not account for Ladrillo's higher Antarctic contribution.

**Scenarios:** SSP2-4.5 and SSP5-8.5 only. SSP1-2.6 is dropped (Marcus 10-17), because Lin runs SSP1-1.9 and Ladrillo's
calib 1.6.0 forcing has no SSP1-1.9.

**Choice left to Marcus:** whether the comparison goes in Sect. 4.3, and its framing.

The 10-02 transcript numbers (SSP2-4.5 10.3, SSP5-8.5 36.4 cm; BRICK 2.0 "higher still") predate the record conditioning
and the BRICK 2.0 posterior swap. Use the table above.

## Item 7 (N02), added 10-21: Poinelli et al. 2026 and the committed loss under held climate

Receipt: `julia/diag_ais_constant_climate_vs_poinelli2026.jl` → `outputs/diag_ais_constant_climate_vs_poinelli2026_L27.csv`
(8dc5dc0), run against Ladrillo.jl v1.3.0. Source: Poinelli et al. (2026), Nat. Commun. 17, 10364,
doi:10.1038/s41467-026-77976-1 (open access; code and the spun-up model at doi:10.5281/zenodo.16551126).

**The paper.** ISSM over Thwaites and Haynes, Thwaites reported. Melt is applied inside a grounding zone of length L
upstream of the flotation line. (melt rate, L) are calibrated on 1996–2023 grounding-line retreat, discharge, thinning and
speed-up. Projections to 2100 hold surface mass balance and ocean melt at their 1996–2023 averages, with a fixed ice
front. Thwaites' 2100 sea-level equivalent at 110 m/yr: 0.83 cm (no grounding zone), 1.43 (1 km), 1.94 (3 km, the
posterior maximum), 3.01 (5 km, the 2020s observed extent). The ISMIP6 constant-forcing Thwaites mean it quotes is
1.52 ± 2.18 cm. The ± values are the spread at a fixed melt rate with L ± 1 km, not a posterior predictive interval. The
origin is not stated; the Fig. 4b curves start at about 2021.

**Bearing on the Lin comparison.** Lin's drift-corrected row replaces each control run with a linear 0.33 ± 0.16 mm/yr
background trend, so its constant-climate loss is linear: 2.6 ± 1.3 cm over 2021–2100 and 2.8 ± 1.4 over 2015–2100 at the
prior value. Lin does not report that term's posterior. Poinelli's mechanism needs no further warming. DAIS's fast
dynamics need Antarctic warming above T_crit, so they cannot represent it; only the slow channel can.

**Ladrillo and BRICK 2.0 under held climate.** GMST and OHC held at each config's mean over the window, from the first
held year; the draw set is the paper's joint arm (conditioning on the unheld climate). The hold is not ruled.

| AIS, cm, median [5–95] | 2021 → 2100 | 2015 → 2100 | rate ratio 2091–2100 / 2021–2030 |
|---|---|---|---|
| Ladrillo, hold 1996–2023 (from 2024) | 2.15 [1.78–2.48] | 2.36 [1.95–2.72] | 0.95 |
| Ladrillo, hold 2015–2024 (from 2025) | 2.69 [2.15–3.44] | 2.89 [2.31–3.70] | 0.95 |
| BRICK 2.0, hold 1996–2023 | 2.54 [1.69–4.52] | 2.74 [1.81–4.87] | 1.07 |
| BRICK 2.0, hold 2015–2024 | 2.37 [1.25–4.74] | 2.57 [1.37–5.11] | 1.02 |
| Ladrillo, SSP2-4.5, λ = 0 | 5.19 [3.39–8.59] | 5.4 [3.6–8.8] | |
| Poinelli, Thwaites alone, 3 km / 5 km | 1.94 / 3.01 | | convex (Fig. 4b) |
| Lin, background term (prior) | 2.6 ± 1.3 | 2.8 ± 1.4 | 1 by construction |

Share of draws whose whole-sheet loss (2021 → 2100) is below Poinelli's Thwaites-alone central value:

| | 3 km (1.94 cm) | 5 km (3.01 cm) |
|---|---|---|
| Ladrillo, hold 1996–2023 | 16.5 % | 100 % |
| Ladrillo, hold 2015–2024 | 1.4 % | 78 % |
| BRICK 2.0, hold 1996–2023 | 12 % | 73 % |
| BRICK 2.0, hold 2015–2024 | 26 % | 73 % |

- No draw fires under either hold (gate), so the held numbers are the slow channel alone.
- Ladrillo's committed loss for the whole sheet is about the size of Poinelli's committed loss for Thwaites alone, and its
  committed rate falls slightly where Poinelli's rises. The ordering holds unless the rest of the sheet gains mass under
  constant climate.
- About half of Ladrillo's SSP2-4.5 λ = 0 change from 2015 is the committed part (2.89 of 5.4 cm under the 2015–2024
  hold), close to the share of Lin's background term in Lin's SSP2-4.5 median (2.8 of 5.2 cm at the prior value).
- The slow channels respond to warming with opposite sign: per draw, between the two holds, Ladrillo loses more under the
  warmer hold in 99.6 % of draws (median +2.4 cm/K) and BRICK 2.0 loses less in 82 % (median −1.0 cm/K).
- Ties to item 7's rate: Ladrillo's held rate in 2021–2030 is 0.28 / 0.35 mm/yr, against the 2002–2021 target of 0.423.

**Ruled (Marcus 10-21):** "Maybe just cite Poinelli as a Thwaites analysis, but that without the broader context it is
difficult to make comparisons to Ladrillo given that Ladrillo models AIS as a single sheet." No Poinelli number is compared
with Ladrillo in the paper, so the hold choice is moot. The receipt above stays as provenance. Reference entry, in the
draft's style:

> Poinelli, M., Rignot, E., Seroussi, H., Cuzzone, J., Pelle, T., and Larour, E.: Sea-level contribution from Thwaites
> Glacier doubles in an observation-constrained ice-sheet model, Nat. Commun., 17, 10364,
> https://doi.org/10.1038/s41467-026-77976-1, 2026.

## Uncertain items from the inventory

- **U02 (Fig. 5's 0.05 cm), resolved.** `python/verify_magicc_regrowth_attribution.py --arm=fixed` →
  `outputs/verify_magicc_regrowth_attribution_L27_fixed.csv` (5c5cdff): Low-to-Negative 0.0526 cm (peak 2230), 0 on every
  other scenario. The fixed arm has no MAGICC-climate counterpart (it is the FaIR-mean control in both climate files), so
  that receipt reports no climate split.
- **U03 (BRICK 2.0's calibration data).** The Zenodo record (version v4, 2026-06-08) describes itself as output
  "supporting the model calibration and analysis codes included in MimiBRICK v2.0.0". It does not name the datasets, so
  the question to Tony about Wang et al. 2024 stands. Reference E091 may want "v4".
- **U10 (Sect. 4.2 "the same pairing").** Draw by draw, all 998 BRICK 2.0 joint-arm draws with a Ladrillo partner use the
  same FaIR configuration (checked on SSP2-4.5, SSP5-8.5, Very Low, Low-to-Negative and High). Two BRICK 2.0 draws have no
  partner because Ladrillo's record conditioning drops them and BRICK 2.0 is not conditioned: 229 and 610 in the SSPs,
  187 and 610 in the van Vuuren scenarios. Joint-arm counts: BRICK 2.0 1,000; Ladrillo 1,997 (SSPs) and 1,998 (van Vuuren).
- **Repo item (Table 5 reading).** The "tie by construction" sentence and the "every BRICK 2.0 series at the ρ bound"
  sentence are now computed (ba82407; Ladrillo 6674807). Table 5 was re-run at all three ρ bounds in both repos to
  regenerate the .md. See CHANGELOG 2026-10-15h for the byte-identity result.

## Not affected

The paper cites nothing from the products still on the May-22 BRICK 2.0 file (the overshoot / matched-ΔT arms and
`diag_gcrit`).
