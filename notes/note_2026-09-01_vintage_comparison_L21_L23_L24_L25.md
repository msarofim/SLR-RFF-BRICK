# The vintage comparison — L21, L23, L24, L25, and which axis each one actually moved

**Written 2026-09-01**, after L25 landed and resolved the `--amp-mu` question. Companion to
`handoff_2026-09-01c_readers_gates_and_the_amp_error_bar.md`. Every number here is measured from
chains on disk; nothing is carried over from a prior document.

---

## 1. WHAT EACH VINTAGE IS

| | **L21** | **L22** | **L23** (champion) | **L23b** | **L24** | **L25** |
|---|---|---|---|---|---|---|
| glacier law | ratchet | ratchet | floored | floored | floored | floored |
| amp prior | N(0.95, 0.10) | N(0.95, 0.10) | N(1.09, 0.10) | N(1.09, 0.10) | **N(1.09, 0.180)** | N(1.09, 0.10) |
| steric cap | pre | post | post | post | post | post |
| proposal cov | L14tune *(chosen)* | L14tune *(chosen)* | L11tune3 *(inherited)* | L11tune3 | L11tune3 | L14tune *(chosen)* |
| RNG | — | — | — | seeds 3026-9 | — | — |
| amp posterior | 0.9438 ± 0.0018 | 0.9465 ± 0.0021 | 1.0824 ± 0.0037 | 1.0896 ± 0.0029 | 1.0723 ± 0.0091 | 1.0791 ± 0.0030 |
| run script | **yes** | **yes** | none | none | **added 09-01** | none |
| benchmarked | yes | yes | yes | no | **running 09-01** | no |

⚠ **The shipped prior is N(1.09, 0.180)** (`165a860`). Only **L24** uses it. L21/L22 carry a
superseded centre *and* width; L23/L23b/L25 have the right centre and a width 1.8× too narrow.

⚠ **L24 has no run log.** Its arm is verified from data instead: amp is prior-dominated, so its
posterior sd reveals the prior sigma. L24 implies **0.1782**; every other vintage implies ~0.10.

## 2. WHICH COMPARISONS ARE CONTROLLED

| pair | axes that differ | verdict |
|---|---|---|
| L21 → L22 | steric cap | **+0.0026 ± 0.0027** — no difference, no sign |
| L23 → L23b | RNG only | the NOISE FLOOR |
| L23 → L25 | proposal covariance | inside the noise floor (§3) |
| L23 → L24 | amp sigma 0.10 → 0.180 | **the only controlled test of the prior width** |
| L21 → L23 | glacier law **+ amp centre + covariance** | ⛔ **NOT controlled — three axes** |
| L22 → L25 | glacier law **+ amp centre** | ⛔ **NOT controlled — two axes** |

⛔ **NO RUN ISOLATES THE GLACIER LAW.** Every pair that changes it also changes the amp prior.
The law is justified on physical grounds (`glacier_floor_bounded_regrowth`) and is inert in the
likelihood, but it has never been tested on fit alone.

## 3. THE COVARIANCE IS INSIDE THE NOISE FLOOR — MEASURED

L23-vs-L25 changes only the proposal covariance. L23-vs-L23b changes only the seed. Thinned 1/500,
post-burn, 8000 draws per arm, all 59 sampled parameters:

| | L23 vs **L25** *(covariance)* | L23 vs **L23b** *(RNG only)* |
|---|---|---|
| median \|shift\| | 0.029 sd | **0.046 sd** |
| max \|shift\| | 0.84 sd | **0.79 sd** |
| `antarctic_alpha` | −0.60 sd | **+0.71 sd** |
| sd_ratio range | [0.60, 1.88] | [0.58, 1.36] |
| R-hat > 1.05 | 7 → **13** | 7 → 9 |

⇒ **The covariance moves this posterior less than the random seed does.** The one signal outside
the noise band points the wrong way: L25, on the *deliberately chosen* L14tune, converges WORSE
than both L11tune3 arms. L14tune was tuned for L14's configuration; being chosen does not make it
better for this one.

**Two consequences.** (a) Re-running any arm purely to give it a chosen covariance would land
inside sampler noise — not worth the chains. (b) ⭐ **The 4.93 cm between-refit reproducibility
figure is REHABILITATED.** It was dismissed as blind because L23b shares L23's covariance; now
that the covariance is measured not to matter, L23b is a valid replicate and 4.93 cm stands.

## 4. THE BENCHMARK, AND WHY L21'S LEAD IS CONFOUNDED

`bench_ladrillo.py`, candidate arm, 304 scored cells:

| | PASS | WARN | FAIL |
|---|---|---|---|
| **L21** | **87** | 63 | **4** |
| **L23** | 86 | 64 | **6** |

Eight cells change verdict L21→L23: **two improve, six degrade.** All six degradations are AIS or
AIS-dominated totals:

    ais   ssp126 2100  spread_vs_lit   N/A(bimodal) -> FAIL    0.75 -> 2.19
    ais   ssp126 2150  spread_vs_lit   N/A(bimodal) -> WARN    0.70 -> 1.56
    ais   ssp245 2150  median_vs_lit           PASS -> WARN    0.40 -> 1.72
    total ssp126 2300  spread_vs_lit           PASS -> WARN    1.56 -> 2.23
    total ssp245 2150  spread_vs_lit           PASS -> WARN    1.18 -> 1.38
    ais          —     projection              WARN -> FAIL
    ais   ssp585 2300  median_vs_lit           WARN -> PASS    0.98 -> 1.08   (better)
    total ssp245 2100  median_vs_lit           WARN -> PASS    0.86 -> 0.96   (better)

⚠ **L21 is not a better MODEL; it has a lower, narrower AIS prior.** Moving the amp centre
+0.14 on a parameter carrying 386 cm/unit at 2300 is exactly what widens AIS past the literature
at the cool scenarios. Reading this table as "the old glacier law fits better" repeats the error
this whole arc was built on.

Totals, median joint band (cm): ssp245/2300 **158.9 → 263.8**, ssp585/2300 **491.6 → 519.2**,
ssp126/2300 **70.9 → 72.9**.

## 4b. L24 HAS LANDED — AND THE PRIOR WIDTH IS NOT A LEVER (2026-09-02)

`run_l24_postprocess.sh` completed in 66 min, every step OK. **ACCEPTED ON DELIVERABLE**:
SLR@2100 R-hat **1.008** ESS 1049, SLR@2150 R-hat **1.011** ESS 1061; 19 parameter marginals
unconverged (L21: 18) — the documented AIS-geometry ridge, same as every vintage.

| | PASS | WARN | FAIL |
|---|---|---|---|
| L21 *(superseded prior)* | **87** | 63 | 4 |
| L23 *(champion)* | 86 | 64 | 6 |
| **L24 — SHIPPED PRIOR** | **85** | 65 | 6 |
| L22 | 77 | 72 | 7 |

⭐ **L23 → L24 changes only 3 of 304 cells** (2 worse, 1 better), and two of the three merely
cross a threshold (`gis ssp585/2150 spread` 0.55→0.47; `total ssp126/2150 spread` 1.49→1.66;
`total ssp245/2150 median` 1.15→1.07, better). **A 1.8× wider prior is worth three cells.** That
matches the earlier finding that it widened the AIS band only 1.07×: amplification dominates the
between-VINTAGE SHIFT, not the BAND.

Totals, median joint (cm) — L24 sits slightly BELOW L23 at the warm end, tracking its lower amp
median (1.0723 vs 1.0824):

    scenario    yr        L21       L23       L24
    ssp126    2300      70.85     72.85     72.58
    ssp245    2300     158.93    263.80    249.20
    ssp585    2300     491.55    519.20    481.57

⚠ **The one thing the CORRECT prior makes worse is AIS spread against the literature at the cool
scenario**: `ais ssp126/2100 spread_vs_lit` **2.19 → 2.55× lit** (both FAIL). The measured CMIP6
prior width produces an AIS band 2.5× the literature's there. Not automatically a defect — 78 % of
ssp585/2300 AIS width is `antarctic_lambda`, a PRIOR, and narrowness is never scored as a win —
but it is the sharpest remaining tension and it is not fixed by anything in this comparison.

⇒ **On fit, L23 and L24 are indistinguishable.** The tiebreaker is provenance: L24 is the only
vintage on the shipped prior N(1.09, 0.180). L21's higher score rests on an amp centre (0.95) that
was superseded on measured grounds — 34 CMIP6 models put it at 1.09 — so it is not a reason to
keep L21.

## 5. WHAT IS ACTUALLY OPEN

1. ✅ **L24 is benchmarked** (§4b). It scores within 3 cells of L23 and is the only vintage on the
   shipped prior. **Recommended champion on provenance, not on fit.**
2. **The champion decision.** L23's promotion reasoning is void and L23-vs-L21 is not
   like-for-like. Re-promotion on a corrected basis is Marcus's call and wants L24's score first.
3. **The glacier law has never been tested on fit alone** (§2). One 3 h run — L25's config with
   the old ratchet — would do it. Only worth spending if the physical case needs a fit defence.
4. **Three vintages still have no run script** (L23, L23b, L25). Three dropped flags on this refit
   all trace to that. L24 now has one.
