# IMBIE 2026 out-of-sample test — insert material for the GMD draft

**Basis:** Ladrillo v1.0, posterior **L27** — the shipped posterior, and (Marcus, 2026-09-24) the paper's
posterior, decided after the IMBIE-2026 arc closed. Structural/noise test arms L28/L29/L30/L32/L34.
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

## 2. Figures and captions

### Figure X — the shipped posterior against the new record

**File:** `figures/diag_imbie2026_vs_targets_L27.png` (script `python/diag_imbie2026_vs_targets.py`,
regenerated 2026-09-24 via `regen_imbie_fig_L27.sh`). ⚠ That runner exists because the script reads the
SHARED `outputs/recalib_targets_ext.csv` and hardcodes a "Frederikse 2020 ≤ 2018, GRACE-FO after" label
in its own provenance string; it swaps in L27's own training target under an md5 gate and restores the
IMBIE build by exit trap, so the label and the file cannot disagree.

> **Figure X.** The IMBIE 2026 reconciled record (Otosaka et al., *Sci. Data* 13:1301) against Ladrillo's
> ice-sheet calibration targets and the shipped posterior. Sea-level sign throughout (positive = rise),
> levels in cm SLE relative to 1995–2005. **Top:** cumulative Antarctic (left) and Greenland (right)
> contributions — IMBIE 2026 with its ±1σ band, the calibration target actually used (Frederikse 2020
> through 2018, GRACE-FO mascons after), the posterior median with its 5–95 % band, and BRICK 2.0 for
> reference. IMBIE is not an Antarctic likelihood term, so this comparison is out-of-sample by
> construction. **Bottom:** annual rates, with IMBIE's own surface-mass-balance and dynamics anomalies
> stacked. The dotted vertical marks the 2018 end of the Frederikse record.

### Figure Y — the structural extension is not taken

**File:** `figures/diag_imbie2026_dynamics_null_L30.png` (script `python/plot_imbie2026_dynamics_null.py`).
⚠ This figure is the **ramp** test specifically and is correct as it stands; its channel-profile input
exists only for L27 and L30, and the later arms are not ramp arms, so it is neither re-tagged nor rebuilt.

*Accessibility note (not for the caption).* Checked with the repo's own `python/validate_palette.py`
(Viénot–Brettel–Mollon dichromat simulation, OKLab ΔE×100; normal floor 15, CVD target 8):

- **Figure X passes on every pair.** Its four marks `#1b7837` / `#762a83` / `#5aae61` / `#9970ab` give a
  worst-case **deutan ΔE 15.8**, roughly twice the target. ⚠ One WARN, easily met: the SMB green
  `#5aae61` is **2.74:1** on white, under the 3:1 mark floor — it is a *labelled* legend entry, which is
  the mitigation the tool asks for, so no change is needed unless the bars are ever shown unlabelled.
- ⛔ **The paper's existing `#1b7837` green with `#b2182b` red still FAILS at deutan ΔE 2.7** — effectively
  one colour for a deuteranope. That pair is used elsewhere in the figure set and is **unaddressed**. A
  pass over the existing figures is still owed. `[MCS]`

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

---

## 4b. The Antarctic innovation variance — what the record says about our error model `[NEW 09-24]`

*This is the one place the new record changes something about the shipped posterior rather than merely
checking it. Numbers and structure are mine; the framing sentence is yours.*

> **The record's interannual variability and the model's error term.** The reconciled record's
> surface-mass-balance anomaly varies from year to year with a standard deviation of first differences
> of 118 Gt yr⁻¹ over 1979–2019, and that variability is old and broadly distributed — every decade
> since the 1980s shows 107–132 Gt yr⁻¹, and global mean surface temperature explains 4 % of its
> variance, so it is weather rather than a forced signal the module could be made to reproduce.
> Expressed as a sea-level innovation this implies a lower bound of 0.033 cm yr⁻¹ on the Antarctic
> AR(1) innovation standard deviation. The shipped posterior fits **0.0216 cm** (5–95 %:
> 0.0188–0.0249), a factor **1.5 below that bound and outside its own 95th percentile** — the
> likelihood chose an Antarctic error term smaller than the observed record permits.
>
> **What imposing the bound does, and does not, do.** Refitting with the innovation standard deviation
> floored at the implied value, and nothing else changed, leaves the shipped configuration essentially
> where it was: the floored variant sits at 0.73 σ against 0.70 σ on the full-record Antarctic scorer
> and 1.32 σ against 1.27 σ over the altimetry era, i.e. marginally worse on both. The same floor
> applied on top of a refit to the IMBIE level series is worth a factor of three on the
> pre-satellite hindcast. **The correction therefore matters for a posterior calibrated to the
> reconciled record and not for the one calibrated to the reconstruction**, which is why the shipped
> posterior is reported without it.
>
> `[MCS — the framing sentence goes here. Two things are demonstrated and a third is not:`
> `(i) the fitted innovation term is smaller than the record allows, and (ii) correcting it does not`
> `improve the shipped posterior on our own target. What is NOT demonstrated is that the error term`
> `is harmless — a misspecified innovation variance biases the posterior mean, it does not only`
> `under-disperse it, which we observed directly on the IMBIE-target arms. Whether that is worth a`
> `caveat sentence or a limitations bullet is a judgement.]`

**Table Y — the innovation term against the record.**

| | implied by the record | shipped (L27) | floored, our target (L34) | floored, IMBIE target (L32) |
|---|---|---|---|---|
| `sd_ais` (cm) | **0.03259** | **0.02160** (p05 0.0188, p95 0.0249) | 0.03305 (on the floor) | 0.03294 (on the floor) |
| ratio to the implied bound | 1.00 | **0.66** | 1.01 | 1.01 |
| full-record AIS (σ) | — | **0.70** | 0.73 | 0.88 |
| altimetry-era AIS (σ) | — | **1.27** | 1.32 | 1.01 |

⚠ The implied bound is derived from IMBIE's SMB anomaly first differences over 1979–2019 (n = 41,
118.0 Gt yr⁻¹, 3620 Gt per cm SLE). **The total → SMB transfer is an assumption**, stated here rather
than buried: it was re-derived against the 2021 IMBIE vintage as a sensitivity and the conclusion did
not move. `[MCS — whether the sensitivity is worth reporting is yours.]`

⛔ **Not claimed, and the draft should not imply it:** that the module's surface mass balance *should*
reproduce 118 Gt yr⁻¹ of interannual variability. It cannot — the module's own SMB window anomalies
span roughly ±25 Gt yr⁻¹ — and the identity in §4 is why that is a statement about representable
behaviour, not about the discharge law.

## 5. Table X — the verifiable numbers

**Table X.** Ladrillo against the IMBIE 2026 Antarctic record. Model values are means over 100
posterior draws. *Level* rows are cumulative sea-level contribution in cm SLE; z combines the model's own spread with
IMBIE's published window uncertainty in quadrature (`diag_imbie2026_vs_targets.py`). ⚠ The L27 column
was **regenerated 2026-09-24** and reproduced its 09-22 values exactly; the L30 column is the 09-22 run
and was not re-run, because L30's postpred has not changed. *Dynamics* rows are the mass-balance anomaly in Gt yr⁻¹,
referenced 1979–2008 for model and observations alike (`diag_ais_channel_separation.jl`, 100 draws).
⚠ **The comparison column is L30, the arm Figure Y shows** — the refit to the IMBIE *level* series.
The table and that figure must describe the same arm, so it is deliberately NOT one of the later
noise-model arms; those appear only in §4b, where they answer a different question and are labelled
as such. `[MCS — one consequence you should know about: a refit that ALSO floors the innovation term
(L32) moves the 2018–23 dynamics anomaly to −133.1 ± 4.9, i.e. CLOSER to the record's −167.2, not
further. That would complicate the "refitting the level moves the dynamics away" sentence in §4. It
sits outside the scope you set for this material, so it is flagged here and not built in.]`

| Quantity | Window | IMBIE 2026 | **Ladrillo v1.0 (L27, the paper's posterior)** | refitted to the IMBIE level (L30) |
|---|---|---|---|---|
| Level, cumulative (cm SLE) | 1979–2023 | 1.328 ± 0.143 | 0.951 (z −2.64) | 1.216 (z −0.77) |
| Level, cumulative (cm SLE) | 2011–2017 | 0.389 ± 0.051 | 0.215 (z −3.27) | 0.267 (z −2.14) |
| Level, cumulative (cm SLE) | 2018–2023 | 0.174 ± 0.091 | 0.218 (z +0.48) | 0.262 (z +0.94) |
| **SMB anomaly** (Gt yr⁻¹) | 2018–2023 | **+141.0** | +26.7 | −0.7 |
| **Dynamics anomaly** (Gt yr⁻¹) | 2018–2023 | **−167.2** | −119.1 ± 4.6 | −77.8 |
| SMB interannual sd (Gt yr⁻¹) | 1979–2019 | 118.0 | ~5 | ~5 |

⚠ **The two bold rows are the constraint**, and they are named rather than referred to by position:
net ≡ SMB + dynamics identically, so with the module's SMB anomaly unable to reach +141 Gt yr⁻¹ its
dynamics error is bounded below by its net error plus ≈114 Gt yr⁻¹. The cumulative-level rows use the
`diag_imbie2026_vs_targets.py` route (z includes the model's own spread); the anomaly rows use
`diag_ais_channel_separation.jl` (100 draws, ± SE). The same 1979–2023 cumulative on the second route
is 0.948 ± 0.008 for L27, against 0.951 on the first — the two routes agree to 0.003 cm, inside the
draw SE, which is the check that they measure the same thing. **The fitted `sd_ais` values are in Table Y, not repeated here.**

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
