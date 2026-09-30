# GMD next tracked pass — verified edit list (prep, 2026-09-29 evening)

Read-only checks against a snapshot of **Marcus's 17:29 save** of
`deliverables/GMD.Ladrillo.v1_review-2026-09-29_L27.docx` (md5 `efe6b3a3…`). ⛔ Marcus is editing that
file now. **Apply nothing until he uploads.** Then apply only the items he approves, as tracked changes by
"Claude" on **the newest file** (`ls -t deliverables/GMD*.docx | head -1`). Re-quote every sentence
against his new text before editing it, because he may already have changed it. Paragraph numbers
(¶) refer to the snapshot and will move.

## A. The nine "found, not acted on" items (handoff 09-29b §4)

| # | Where (snapshot) | Verdict | Receipt | Minimal edit (⚖ = judgment call) |
|---|---|---|---|---|
| 1 | Calibration Data Updates ¶58, "each by about two of IMBIE's standard deviations" | IMPRECISE | `outputs/diag_imbie2026_vs_targets_windows_L27.csv` (HEAD Frederikse target). Target−IMBIE ÷ IMBIE σ alone gives AIS 1979–2023 **−2.92**, GIS 1972–2023 **+1.84**. ÷ combined σ gives −1.79 / +1.10. ¶57's 2.6σ uses IMBIE σ alone, so the same basis applies here | ⚖ "by about three and two, respectively, of IMBIE's standard deviations" **or** "by 2.9 and 1.8 of IMBIE's standard deviations, respectively" |
| 2 | ¶57, "within 8 % in every window from 2003 onward" | IMPRECISE | same file. GIS Ladrillo vs IMBIE: 2003–10 **−8.1 %**, 2011–17 −0.8 %, 2018–23 −7.4 % | "within 8 %" → "within about 8 %" (or "within 9 %") |
| 3 | Antarctic ¶44, "posterior width equals their prior width in every calibration that sampled them" | **CORRECT** | Measured against the *truncated* prior, the ratios are L26 γ/λ/T_crit 0.998/1.013/1.001 and L24 0.992/0.997/1.002 (`ladrillo_prior_posterior_L2{4,6}.csv`). The "0.86" was sd over the untruncated σ = the truncation factor (CHANGELOG ~l.2479) | ⚖ optional: "prior width" → "truncated prior width" |
| 4 | Comparisons to Observations ¶82, FaIR OHC "1.22–1.29×" | IMPRECISE (mixes windows) | `outputs/diag_te_rate_attribution_L27.csv`: on 1993–2026 the ratios are 1.236 (Zanna+IGCC) and 1.285 (Zanna+Cheng). The 1.215 is 1993–2024 FaIR/IGCC 0–2000 m | "1.22–1.29×" → "1.24–1.29×" |
| 5 | Table 5 ¶80 / ¶81 | ✅ **RE-RUN 09-30 with equal draws (10,000 each)**, on L27's own target (`63e4a88`) | Control: the old 2k/10k pipeline reproduced the 09-20 files byte-for-byte first | **Update the table's numbers** (Marcus asked for the re-run): ρ≤0.99 Ladrillo AR(1) ln L 238.0→**240.4**, AIC −376.0→**−380.8**, BIC →**−169.9**; ΔAIC 84.1→**88.9**, ΔBIC 20.8→**25.7**. ρ≤0.95: ln L →**235.8**, ΔBIC →**81.9**. ρ≤0.90: ln L →**227.0**, ΔBIC →**146.9**. BRICK rows and the obs_iid row are unchanged. Full rows are in `outputs/ic_ladrillo_vs_brick20_L27{,_rho0.95,_rho0.9}.md`. ⚖ Optionally note "(10,000 posterior draws per model)" in the caption |
| 6 | Conclusions ¶112, "open-source (MIT) licence" | IMPRECISE | `LICENSE` = MIT; `LICENSE-CONTENT` = CC-BY-4.0 for non-code content; README.md:192–196. `CITATION.cff:32` lists MIT only | → "the MIT licence (code) and CC-BY-4.0 (non-code content)". ⚖ optionally repeat in Code and data availability ¶116. Separately, `CITATION.cff` should name both licences |
| 7 | FIG 4 caption ¶95 | manuscript **CORRECT** (gives no count); the sidecar was wrong | **FIXED in code `5b3b4e3`**: the sidecar now reads n_draws from the cells files (2000 / 1000). PNG byte-identical | none in the manuscript |
| 8 | Future Projections ¶88, glacier differences "in reservoir count, driver, and posterior" | IMPRECISE (omission) | Ladrillo S_eq = max(a(1−e^{−b(T−T_off)}), 0) per block (`glaciers_nu3_component.jl:92`); MAGICC tabulates S_eq(T) on 0–10.3 K with 15 CMIP5 tunes (CHANGELOG ~l.4983). Only the transient law is shared | → "differences in equilibrium curve, reservoir count, driver, and posterior" |
| 9 | Model code ¶62, "the Parkes and Marzeion range" | MISSING REFERENCE | Crossref + local PDF `ClaudeDocs/Papers/Parkes.Marzeion.s41586-018-0687-9.pdf`: 16.7–48.0 mm (1901–2015) brackets the 33 mm posterior | cite "(Parkes and Marzeion, 2018)" + entry: Parkes, D. and Marzeion, B.: Twentieth-century contribution to sea-level rise from uncharted glaciers, Nature, 563, 551–554, https://doi.org/10.1038/s41586-018-0687-9, 2018. |

## B. Reference audit (all 36 list entries' DOIs resolve and match Crossref/DataCite; 0 year mismatches)

**Cited but not listed:**
- **Parkes and Marzeion, 2018** (A9).
- **CSIRO "2015 update of Church and White"**: needs a dataset citation with version and access date, or drop "2015 update".
- **Gelman–Rubin**: Gelman and Rubin, 1992, Stat. Sci. 7, doi:10.1214/ss/1177011136 (verified).
- **DAIS**: Shaffer, 2014, GMD 7, 1803–1818, doi:10.5194/gmd-7-1803-2014 (verified).

**Inputs with no citation at all:**
- **HadCRUT5**: Morice et al., 2021, JGR 126, e2019JD032361, doi:10.1029/2019JD032361, plus the version used. It is not in Table 3.
- **CMIP7 historical emissions** and **MESSAGE-GLOBIOM SSP2-4.5**: need a release or version.
- **"observed 0–2000 m products"** (the TE target): the products are never named.
- **SLEIP preprint**: Table 1 caption; should be (Nauels et al., 2026).
- **DAIS paleo ensemble file**: probably Wong, Bakker and Keller, 2017, Clim. Change 144, 347–364, doi:10.1007/s10584-017-2039-4. ⚠ Confirm this paper produced the file before citing it.
- **Named-only models and modules**: FACTS modules, GlacierMIP2, PISM, ISMIP6, SICOPOLIS, RGI 6.0, Mimi.jl, MAGICC v7.5.3. ⚖ Cite the primaries, or route through Kopp 2023 / Nauels 2026.

**Listed but never cited:**
- Eyring 2016 and Leach 2021. The placeholder at the end of the list claims Eyring is cited in Table 3 fn 19; it is not.
- Goelzer 2020 and Greve & Chambers 2022. Natural homes: the Introduction, and the ISMIP6/SICOPOLIS above-threshold ¶.

**Named but never formally cited at first mention:** IMBIE Team 2018, GlaMBIE Team 2025, Mengel 2016, Nauels 2017. Smith 2026 and Smith 2024 appear only in Code and data availability, not at FaIR's first mention.

**Dataset DOIs given inline only (Copernicus wants them as "[data set]" list entries):** GlaMBIE 10.5904/wgms-glambie-2024-07; GRACE RL06.3Mv04 10.5067/TEMSC-3JC634; Dangendorf 10.5281/zenodo.10621070; IGCC 10.5281/zenodo.20499280; GlacierMIP3 10.5281/zenodo.15046588; GTN-G 10.5904/gtng-glacreg-2023-07. All resolve.

**Copernicus style:**
- Missing "et al." (3+ authors): Nauels 2017, Dangendorf 2024 ×3, Hock 2023, Millan 2022, Mouginot 2019, Rignot 2019 ×2, Farinotti 2019 ×3.
- Punctuation: "(Akaike, 1974; Schwarz, 1978)", "Wong et al., 2017, 2022", "(Zekollari et al., 2025)".
- List order: National Academies before Nauels; single-author Smith 2026 before Smith et al.; van Vuuren placed consistently.
- Remove the "[Reference list complete … as of 2026-09-18 …]" placeholder, which is untrue.

**Still placeholders:**
- Code and data availability: Zenodo DOI, repo URL, and no DOI or version for MimiBRICK v2.0.0, the FaIR 2.2.4 code, FACTS (no remote), or MAGICC runs.
- Acknowledgments.

## C. Repo changes made this evening (no manuscript edits)
- `a62e555` FIG 1: the obs band is hatched (it was the same grey as BRICK 2.0's band) and has its own legend entry; sidecar caption +1 sentence. **The manuscript's FIG 1 caption does not describe the obs band.** ⚖ Adding "observations black, ±1.645σ hatched" is his call. The new PNG needs swapping into the docx.
- `f2569d6` Stale docs moved to L27 (LADRILLO.md, calibrate header, LWS note, run_mcmc_L27.sh, README).
- `5b3b4e3` FIG 4 sidecar draw counts.

## D. Decisions for Marcus
1. The A-table ⚖ choices, especially #1 wording and #5 (disclose, or re-run BRICK at 2,000 draws).
2. ✅ DONE 09-30: L27 is the default everywhere (Marcus).
3. ✅ DONE 09-30: poster pointers removed from the README (Marcus: the poster is done).
4. The DAIS paleo-file source (Wong 2017?) needs confirming before it is cited.
