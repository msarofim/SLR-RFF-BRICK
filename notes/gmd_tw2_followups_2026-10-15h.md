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
- The Lin et al. 2026 comparison at 2100 needs the paper. It is not in `ClaudeDocs/Papers`.

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
