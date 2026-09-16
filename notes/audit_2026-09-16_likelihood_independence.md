# Audit — what constrains Ladrillo L24, and where two terms share a source (2026-09-16)

Prompted by Tony Wong's reply (09-15): "nip in the bud any potential criticisms about possible
double-counting of information or potential correlation between datasets used to constrain the
model." Every term below is read from `julia/calibrate_mcmc_ext.jl` (line numbers at HEAD
`a249e9f`+) and `python/prep_recalib_targets_ext.py`. Nothing here is a new result; it is the
ledger a reviewer would build.

## 0. Framework

Ladrillo is still a **Mimi** model: the Julia components are `@defcomp`s dropped into MimiBRICK's
slots (`brick_mengel.jl` `replace!(m, :glaciers_small_icecaps => glaciers_nu3)`;
`greenland_3basin_component.jl`, `antarctic_icesheet_magdep_component.jl`), built with
`MimiBRICK.get_model` and run with `Mimi.run`. What changed is the CLIMATE: SNEASY is not in the
loop; FaIR GMST/OHC are prescribed inputs (`set_forcing!`), calibration on the ensemble mean,
projection on the 841-config cube. Code lives in the private `MimiBRICK-FM` repo + this one.

## 1. The likelihood, term by term

| # | term (code) | data | quantity scored | shares a source with | mitigation already in place |
|---|---|---|---|---|---|
| 1 | AIS series, AR(1) (`:1473`) | Frederikse 2020 AIS 1900–2018 → JPL GRACE-FO mascon 2019–2026 | annual level, 1995–2005 ref | Frederikse's own ice-sheet inputs (IMBIE lineage); GRACE underlies IMBIE too | **IMBIE dropped** from the likelihood for exactly this reason; GRACE used only AFTER Frederikse ends (offset-matched over the overlap, not double-scored) |
| 2 | GIS series, AR(1) (`:1473`) | Frederikse GrIS (= Kjeldsen 2015 + **Mouginot 2019** + RGI 05) 1900–2018 → GRACE-FO 2019–2026 | annual level | **terms 12–13 (Mouginot shares)** | shares are ratios of RATE DIFFERENCES (late − reference window), so the level that term 2 scores cancels; the information is the partition, which term 2 cannot see |
| 3 | GSIC series, AR(1) + δ(t) (`:1466`) | Frederikse glaciers 1900–2018 → **GlaMBIE** 2019–2023 (global − RGI 05) | annual level, SLOWG+FASTG scope | **terms 9–10 (GlaMBIE share, R19 rate)** | the share cancels GlaMBIE's common-mode error; R19 is outside term 3's model scope (`HIND_BLOCKS`); σ on the rate terms is the serially-correlated value (×4.7 vs quadrature) |
| 4 | steric series, AR(1) + δ(t) (`:1470`) | NOAA NCEI 0–2000 m thermosteric 2005–2025 spliced to Frederikse steric | annual level | the FaIR DRIVER (calib 1.6.0 was constrained on observed OHC) — see §2 (iii) | none in the likelihood; stated as a driver–target dependence |
| 5 | SMB anchor (`:1486`) | Rignot 2019, area-scaled | 1979–2008 mean SMB flux | none in the fit (a flux, not a mass series) | — |
| 6 | glacier inventory (`:1488`) | Farinotti 2019 (Hock 2023 reconciliation) | remaining volume at 2000 | GlacierMIP3 models carry their own volumes | rungs (term 8) are FRACTIONS of 2020 mass, so the inventory does not enter them |
| 7 | 19th-c ledger (`:1494`) | Leclercq/Oerlemans/Cogley 2011 | S(1900)−S(1850) | Frederikse's glacier series starts 1900 — disjoint in time | — |
| 8 | GlacierMIP3 rungs (`:1503`) | Zekollari 2025 equilibrium runs, 8 models | committed-loss % at 1.2/1.5/2.0/3.0 K, per block | **κ prior (term 15)** — same ensemble, different quantity | within-block rung correlation 0.6 modelled; NO cross-block correlation modelled (same 8 models in every block) |
| 9 | GlaMBIE SLOWG/FASTG share (`:1521`) | GlaMBIE 2000–2024 regional | FASTG share of the modern rate | term 3 | ratio (common-mode cancels); the absolute-rate form was retired 08-14 for this reason |
| 10 | GlaMBIE R19 rate (`:1541`) | GlaMBIE region 19 | 2000–2024 mean rate | term 3's TARGET keeps r19 melt 2019+ (scope mismatch, ~0.03 cm) | model side excludes R19 from term 3, so R19 is scored once |
| 11 | total series | Dangendorf 2024 + NOAA STAR | — | Frederikse components (budget non-closure +0.74 cm 1950–80) | **DROPPED** (D1, 08-14): it was double-scoring the components and loading the non-closure onto RGI 19 |
| 12 | Mouginot SMB/discharge share (`:1557`) | Mouginot 2019 | fast-channel share of the extra loss, late vs reference window | term 2 (Frederikse GrIS contains Mouginot) | ratio of rate differences; see §2 (i) |
| 13 | Mouginot sector shares (`:1592`) | Mouginot 2019 Dataset S2 | per-basin share of the loss rate | term 2, term 12 | same construction; basins scored are the two independent shares |
| 14 | DAIS geometry prior (`:1610`) | Wong/Bakker DAIS paleo ensemble | joint prior on 7 geometry params | none of the data terms (paleo) | — |
| 15 | κ prior (`:1607`) | GlacierMIP3 τ80@1.5 K / τ50@3 K | log10 κ centre per block | term 8 | different observable (timescale vs commitment); σ 0.114 dex |
| 16 | AIS amp prior N(1.09, 0.18); GIS amp warming-dependence + width | CMIP6 (34–41 models) | priors | each other (same panel) | priors on two different regions; Greenland LEVEL is observed (1.92), CMIP6 sets only its slope and width |
| 17 | glacier amp priors 0.72 / 2.50 / 1.45 | observed regional temperature vs GMST (HadCRUT-based fit) | prior centres | the FaIR driver (calib 1.6.0 constrained on observed GSAT); the drivers themselves are built from the same temperature products | stated dependence, §2 (iii); product spread BE 1.82 / Had 2.48 / GISTEMP 3.46 for SLOWG (CHANGELOG 09-13f) |
| 18 | AR(1) noise pairs σ, ρ per series | — | fitted | — | independent ACROSS series by construction — §2 (iv) |

## 2. Residual exposures, honestly stated (the four a reviewer will find)

**(i) Mouginot 2019 enters twice — as part of the Greenland LEVEL target (inside Frederikse's GrIS
reconstruction) and as the SMB/discharge and sector SHARE terms.** The shares are ratios of rate
differences, so the level information is projected out and what remains is the partition, which
the level term is blind to. But the ERRORS are not independent: if Mouginot's discharge estimate is
biased, both the Frederikse GrIS post-1972 level and the share move together. Not double-counting
of the same statistic; a shared error source. Fix for the paper: state it, and quote the share
term's precision contribution (the `d2_prior_is_not_binding` method — count the places, compute the
precision share) so the reader can see how much the partition constraint is doing.

**(ii) GlaMBIE enters three times — the 2019+ tail of the glacier series, the SLOWG/FASTG share,
and the R19 rate.** Same defence as (i): the share is the one combination the aggregate series
cannot see and cancels the common-mode error; R19 is outside the series' model scope; the
absolute-rate terms that WOULD have double-scored the modern rate were retired 08-14 for exactly this
reason (calibrator comment at the GlaMBIE block). The σ on the two rate/share terms is the fully
serially-correlated value, which is the conservative end.

**(iii) Driver–target dependence — the one that is NOT a likelihood-construction question.** FaIR
2.2.4 calib 1.6.0 was constrained on observed GSAT and OHC; Ladrillo then fits its thermal expansion
to an observed steric series and its regional drivers are built from observed temperature products.
No datum is scored twice, but the driver is not independent of the targets. This is inherent to
every emulator that runs on a calibrated climate (BRICK/SNEASY has the same structure); say so.

**(iv) Cross-series error correlation is not modelled.** The four AR(1) noise models are
independent across components, yet three of the four series come from ONE reconstruction
(Frederikse 2020) whose components were built to close a budget — their errors are correlated by
construction. Dropping the total removed the worst of this (the total is the sum of the components),
but the component-level correlation remains unmodelled. Cheap fix: estimate the cross-component
residual correlation from Frederikse's 5000-member ensemble (already on disk, `FRED_ENS_NC`) and
report it; a full multivariate AR(1) is a refit.

**(v) GlacierMIP3 twice (rungs + τ anchors) and CMIP6 twice (two amp priors).** Same ensemble,
different observables; the rungs carry a within-block correlation but the same eight models sit in
every block and no cross-block correlation is modelled. Minor, but a reviewer who counts sources
will list it.

## 3. What was already removed for this reason (worth saying to Tony)

IMBIE (double-weights the ice-sheet mass balance already inside Frederikse/GRACE) and the total
series (double-scores the components and pushes the budget non-closure into RGI 19). Both removals
are in the document ("Deliberately removed").

## 4. Cheapest next steps if he wants receipts before the paper

1. Precision-share table: for each point/share term, the fraction of the posterior precision it
   supplies to the parameters it touches (closed-form where linear, as for `d2_steric`). Hours.
2. Frederikse cross-component residual correlation from the ensemble. An hour.
3. Leave-one-source-out refits are 3 h each (4 × 2 M) — only if 1–2 show a term that dominates.
