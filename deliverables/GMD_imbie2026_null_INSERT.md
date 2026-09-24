# IMBIE 2026 out-of-sample test — insert material for the GMD draft

**Basis:** Ladrillo v1.0, posterior **L27** (the shipped posterior); structural test arms L28/L29/L30.
FaIR 2.2.4 (calib 1.6.0). Antarctic fluxes in Gt yr⁻¹, ice-mass sign (negative = loss); sea level in
cm SLE relative to 1995–2005. Every model number is a mean over **100 posterior draws**; ± is the
standard error over draws. Commit: see CHANGELOG 09-22h.

⚠ **Marcus drafts the main text.** Below are the pieces that are mine per our standing split — the
figure, its technical caption, the table, the methods paragraphs, and the verifiable numbers.
**Framing, emphasis and how much weight this carries are marked `[MCS]` and left for you.**

---

## 1. Where this goes

The natural home is the paragraph that currently begins *"Deliberately removed: IMBIE, and the
total"* (§ Calibration Data Updates). That paragraph already establishes IMBIE is **not** in the
Antarctic likelihood, which makes IMBIE 2026 an out-of-sample check by construction — the same
status the draft already gives Dangendorf 2024 for the total. Suggested structure:

1. Existing sentence: IMBIE dropped to avoid double-weighting. *(unchanged)*
2. **NEW** — one sentence introducing IMBIE 2026 as a newly published out-of-sample comparison. `[MCS]`
3. **NEW** — the methods paragraph in §3 below (what was tested and how).
4. **NEW** — the result paragraph in §4 below (what was found).
5. **NEW** — Figure X + caption (§2), and Table X (§5), both appendix-suitable.

---

## 2. Figure and caption

**File:** `figures/diag_imbie2026_dynamics_null_L30.png` (script
`python/plot_imbie2026_dynamics_null.py`).

> **Figure X.** Antarctic mass balance against the IMBIE 2026 reconciled record (Otosaka et al.,
> *Sci. Data* 13:1301), as means over the record's own assessment windows; ice-mass sign, so negative
> is loss. **(A)** The record's own decomposition. The total mass balance slows between 2011–17 and
> 2018–23 (−200 to −104 Gt yr⁻¹) while the dynamics anomaly continues to accelerate (−179 to
> −249 Gt yr⁻¹); the difference is a +144 Gt yr⁻¹ surface-mass-balance anomaly. Error bars are IMBIE's
> published window uncertainties; thin lines are annual values. **(B)** Ladrillo's dynamics anomaly
> misfit against the same record, referenced over 1979–2008 for model and observations alike. The
> shipped posterior (solid grey) tracks the record to within 48 Gt yr⁻¹ in 2018–23, against IMBIE's own
> window uncertainty of 130 Gt yr⁻¹ for that window. Refitting the model to the IMBIE *level* series
> (dashed grey) moves it further from the dynamics record, not closer. Coloured lines add an
> additional discharge response of the stated slope above the stated global-warming onset; the inset
> gives the change in log-likelihood on each channel. Model curves are means over 100 posterior draws.

*Accessibility note (not for the caption):* this figure uses only `#2166ac` / `#b2182b` / `#7f7f7f`.
The paper's other figures pair `#1b7837` green with `#b2182b` red, which is OKLab ΔE **2.7** under
deuteranopia — effectively one colour. Worth a pass over the existing figure set. `[MCS]`

---

## 3. Methods paragraph (draft — mine to write, yours to cut)

> **The IMBIE 2026 reconciled record as an out-of-sample test.** Because IMBIE is not a likelihood
> term (above), the 2026 reconciled record provides an independent check on the Antarctic module, and
> in particular on whether its discharge response is structurally adequate. We compare on the record's
> own assessment windows and on its SMB/dynamics partition, noting that the partition is an identity
> (SMB + dynamics = total to within 4 × 10⁻⁸ Gt yr⁻¹), so the total and one partition channel exhaust
> the information the record carries. We also tested a structural extension: an additional discharge
> response linear in Antarctic surface temperature above a sampled onset, coexisting with DAIS's
> existing fast-dynamics term, with both its slope and its onset free and refitted by the full MCMC.
> Model dynamics is the sum of the grounding-line ice flux and the fast-dynamics term, anomalised over
> 1979–2008 exactly as the observations are.

> **Power.** A null result is only informative if the objective could have detected the effect. We
> measured this directly by generating synthetic Antarctic records from the model *with* a known
> discharge response, adding noise drawn from the fitted Antarctic error covariance, and asking whether
> the objective recovers the response. At the posterior's own AR(1) coefficient it recovers a
> 6 × 10⁻⁴ m SLE yr⁻¹ K⁻¹ response above 0.75 K in 95.7 % of realisations, at the correct slope and
> onset; a 3 × 10⁻⁴ response above 0.60 K is recovered in 84.5 %.

---

## 4. Result paragraph (draft — numbers are mine, the verdict sentence is `[MCS]`)

> **Result.** The shipped posterior reproduces the reconciled record's dynamics anomaly within its
> published uncertainty in every window (Figure X(B)); its largest departure, +48 Gt yr⁻¹ over 2018–23,
> is 0.4 of IMBIE's own uncertainty for that window. It nonetheless underpredicts the cumulative
> Antarctic *level* over 1979–2023 by 2.6σ of IMBIE's bar. Refitting to that level closes the level gap
> to 0.8σ and moves the dynamics misfit from +48 to +86 Gt yr⁻¹.
>
> **These two are not independent, and the trade between them is an identity.** Over 2018–23, relative
> to a 1979–2008 reference, the record's dynamics anomaly is −167 Gt yr⁻¹ and its surface-mass-balance
> anomaly is +141, leaving a net of only −26. Because the net is the sum of the two by construction, a
> model's dynamics error equals its net error minus its surface-mass-balance error. The module's surface
> mass balance responds to temperature on multidecadal timescales but produces window anomalies between
> −20 and +27 Gt yr⁻¹ across these posteriors, against the record's +141, so its surface-mass-balance
> error cannot be brought near zero. Its dynamics error is therefore bounded below by its net error plus
> about 114 Gt yr⁻¹: a calibration that matched the net exactly would necessarily understate the
> dynamics anomaly by that amount, and one that matched the dynamics would have to lose 114 Gt yr⁻¹ more
> than observed in the net. The two posteriors sit at different points on that constraint rather than
> one being better calibrated than the other, and the refit reaches its point by adding discharge early
> and removing it late (−31 Gt yr⁻¹ over 1979–2008, +8 over 2018–23), flattening the discharge trend to
> reproduce a net that flattens.
>
> The additional discharge response is not taken by the likelihood: its slope is pushed to the lower
> edge of its prior and its onset is unidentified across the prior range, and the projections are
> unchanged (Antarctic contribution at 2300 under SSP2-4.5, 165.8 cm against 165.7 cm without the
> response). Adding a dynamics channel to the likelihood does not change this: the channel does favour a
> response, by +2.8 ± 0.4 log-likelihood units at 3 × 10⁻⁴, but the level channel penalises the same
> response by −3.5 ± 0.6 and the larger response by −10.6 ± 0.7.
>
> `[MCS — the interpretive sentence goes here. Note that the identity above makes this a statement`
> `about the SIX-YEAR SNOWFALL EXCURSION being outside the module's representable behaviour, not about`
> `DAIS's discharge law being wrong; those are different claims and only the first is demonstrated.]`

## 5. Table X — the verifiable numbers

**Table X.** Ladrillo against the IMBIE 2026 Antarctic record. Model values are means over 100
posterior draws. *Level* rows are cumulative sea-level contribution in cm SLE with z against IMBIE's
published window uncertainty; *dynamics* rows are the mass-balance anomaly misfit in Gt yr⁻¹,
referenced 1979–2008 for model and observations alike.

| Quantity | Window | IMBIE 2026 | **Ladrillo v1.0 (L27, shipped)** | refitted to IMBIE level (L30) |
|---|---|---|---|---|
| Level, cumulative (cm SLE) | 1979–2023 | 1.328 ± 0.143 | 0.951 (z −2.64) | 1.216 (z −0.77) |
| Level, cumulative (cm SLE) | 2011–2017 | 0.389 ± 0.051 | 0.215 (z −3.27) | 0.267 (z −2.14) |
| Level, cumulative (cm SLE) | 2018–2023 | 0.174 ± 0.091 | 0.218 (z +0.48) | 0.262 (z +0.94) |
| Dynamics misfit (Gt yr⁻¹) | 2003–2010 | 0 by construction (σ 79) | +21.8 | +38.7 |
| Dynamics misfit (Gt yr⁻¹) | 2011–2017 | 0 by construction (σ 80) | **+13.4** | +39.8 |
| Dynamics misfit (Gt yr⁻¹) | 2018–2023 | 0 by construction (σ 130) | **+48.1** | +85.8 |
| SMB interannual spread (Gt yr⁻¹) | 1979–2025 | 122.9 | 4.8 | 4.8 |
| SMB anomaly (Gt yr⁻¹) | 2018–2023 | **+141.0** | +26.7 | −0.7 |
| Dynamics anomaly (Gt yr⁻¹) | 2018–2023 | −167.2 | −116.6 | −77.8 |

⚠ The last three rows are the constraint: net = SMB + dynamics identically, so with the model's SMB
anomaly unable to reach +141 the dynamics error is bounded below by the net error plus ~114 Gt yr⁻¹.

**Δ log-likelihood from the additional discharge response** (mean ± SE over 100 draws; positive =
the channel prefers the response):

| Response | dynamics channel | level channel |
|---|---|---|
| 1 × 10⁻⁴ above 0.45 K | +1.73 ± 0.19 | +0.12 ± 0.30 |
| 3 × 10⁻⁴ above 0.60 K | +2.83 ± 0.44 | −3.52 ± 0.60 |
| 6 × 10⁻⁴ above 0.75 K | +1.83 ± 0.58 | −10.62 ± 0.73 |

Dynamics-channel values use IMBIE's published per-year σ with independent errors, the most
information that channel can carry; under an AR(1) error model with ρ = 0.8 they fall to +0.32,
+0.71 and +0.62 respectively. ⚠ **The dynamics-channel error model is an open methodological choice**
and is reported, not adopted — the verdict does not depend on it.

---

## 6. Reference to add

Otosaka, I. N., Shepherd, A., Amory, C., Horwath, M., Ivins, E. R., King, M. D., Nowicki, S.,
Payne, A. J., Rignot, E., Sørensen, L. S., Schlegel, N. J., Simon, K. M., Smith, B. E., Sutterley, T. C.,
van den Broeke, M. R., Velicogna, I., A, G., Agosta, C., Ditmar, P., Döhne, T., Engdahl, M. E.,
Fettweis, X., Forsberg, R., Gardner, A. S., Gilbert, L., Goelzer, H., Gourmelen, N., Groh, A.,
Hansen, N., Harig, C., Helm, V., Khan, S. A., Kittel, C., Langen, P. L., Larsen, M., Loomis, B. D.,
McMillan, M., Medley, B., Melini, D., Mottram, R. H., Muir, A., Nilsson, J., Noël, B., Pattle, M. E.,
Roca i Aparici, M., Sasgen, I., Save, H. V., Scheuchl, B., Schrama, E. J. O., Schröder, L., Seo, K. W.,
Simonsen, S. B., Slater, T., Spada, G., Vishwakarma, B. D., Wever, N., Wiese, D. N., and Wouters, B.:
Mass balance of the Greenland and Antarctic ice sheets from the 1970s to 2023, Sci. Data, 13, 1301,
https://doi.org/10.1038/s41597-026-08088-0, 2026.

Data citation: NERC EDS UK Polar Data Centre, https://doi.org/10.5285/128c5e33-5224-4197-82f0-19dcc95b80a0,
Open Government Licence v3.0.

⭐ **Verified against Crossref 2026-09-24** (58 authors, published 2026-09-16); the full list is given
because Copernicus house style lists all authors. ⚠ **House-style choice, Marcus's:** if the target
bibliography abbreviates at N authors, this collapses to "Otosaka, I. N., et al.". The existing
bibliography already carries IMBIE Team (2018), Nature 558, 219–222, which stays.
