# Scoping — what the Zekollari 2024 archives can constrain, per glacier block

Marcus, 2026-08-14: "Fetch the zenodo data and scope how it can help with all
three blocks. Remember that we want to prioritize matching historical data and
matching known physics."

Sources, fetched and openly licensed:
Zekollari et al. (2024), *The Cryosphere* 18, 5045-5066, doi
10.5194/tc-18-5045-2024 — **GloGEM** `zenodo.10908278` (CC BY 4.0; volume/area per
RGI region, 2015-2100, 12 CMIP6 GCMs) and **OGGM** `zenodo.8286065`
(oggm-standard-projections v1.0; volume per RGI region, **2000**-2100 on 19 GCMs
and **2000-2300** on a 6-GCM subset, ssp126/ssp534-over/ssp585 only).
Aggregation: `python/scope_glacier_model_constraints.py`; Ladrillo side:
`julia/diag_blocks_vs_glacier_models.jl`. Archives are NOT committed (584 kB +
47 MB); the derived per-block CSV is, with the fetch commands in the script header.

**Validation of the aggregation:** my region-19 GloGEM numbers (13.2 / 32.1% at
ssp126 / ssp585) reproduce the paper's stated 14 ± 13 / 33 ± 24, so the block
summation is reading the archives correctly.

---

## 1. HISTORICAL FIRST — and it decides everything downstream

Both archives predate the projection era, so the same files say whether these
models reproduce the observed record. Matched window 2000-2020, % of 2000 mass
lost, against GlaMBIE:

| block | GlaMBIE observed | OGGM | ratio |
|---|---|---|---|
| **R19** | **0.51 %** | **1.59 %** | **3.11×** |
| SLOWP | 2.57 % | 2.59 % | **1.01×** |
| FAST | 8.12 % | 7.85 % | **0.97×** |

**OGGM reproduces SLOWP and FAST to within 1-3 % and overestimates R19 by 3.1×.**
That is the single most useful thing in the archives, and it sets what each block
can be used for. (GloGEM's archive starts at 2015, so it **cannot** be
historically validated from these files — a real gap, since GloGEM is the model
that treats frontal ablation.)

Note the coincidence that matters: **Ladrillo L10's R19 is also ~3× GlaMBIE**
(modern rate 0.1513 vs 0.04925 mm/yr). So "L10's R19 agrees with OGGM" would be
false comfort — they are both 3× the observation, in the same direction.

## 2. Ladrillo vs the models at 2100 — % of 2015 block mass lost

| block | ssp | **Ladrillo L10** | GloGEM | OGGM |
|---|---|---|---|---|
| R19 | 126 | **32.4** | 13.2 | 21.5 |
| R19 | 245 | **37.5** | 16.3 | 27.3 |
| R19 | 585 | **48.2** | 32.1 | 55.1 |
| SLOWP | 126 | **22.7** | 17.4 | 19.9 |
| SLOWP | 245 | **29.2** | 23.0 | 24.9 |
| SLOWP | 585 | **43.5** | 36.8 | 49.6 |
| FAST | 126 | **38.5** | 47.1 | 51.6 |
| FAST | 245 | **47.9** | 57.9 | 59.3 |
| FAST | 585 | **66.6** | 72.7 | 77.2 |

Inter-model spread (OGGM − GloGEM), the thing any term must span: R19 **+8.3 to
+23.0 pp**; SLOWP +1.9 to +12.8; FAST +1.3 to +4.5. Region 19 is the largest
disagreement globally, exactly as the paper says, from frontal ablation (GloGEM
simplified, this OGGM setup not explicitly represented; the authors call it
"difficult to judge" which is right).

## 3. At 2300 — the only external comparator that exists

FACTS stops at 2150 and MAGICC-SLR at 2100. OGGM's 6-GCM branch is the first
2300 glacier comparator available to this project.

| block | ssp126: Ladrillo / OGGM | ssp585: Ladrillo / OGGM |
|---|---|---|
| R19 | 64.6 / **59.8** | 97.7 / **99.6** |
| SLOWP | **42.2** / 58.6 | 94.8 / 100.0 |
| FAST | **52.7** / 67.4 | 96.9 / 99.7 |

Under SSP5-8.5 both agree that essentially all glacier ice is gone by 2300.
Under SSP1-2.6 **Ladrillo is 15-16 pp LOW on SLOWP and FAST** and close on R19.

---

## 4. What this supports, block by block

**FAST — the strongest case, and a new finding.** The two glacier models agree
with each other to 1.3-4.5 pp, OGGM matches the observed historical loss to
0.97×, and **Ladrillo sits 8.6-11.4 pp BELOW both at 2100** (38.5 vs 47.1/51.6 at
ssp126) and 14.8 pp below at 2300/ssp126. This is a historically-validated,
model-agreed, sizeable discrepancy in the block that carries most of the glacier
signal. A transient-loss term here is well founded, and worth having whatever
happens to D1.

**SLOWP — usable, second priority.** Models agree to ~2 pp except ssp585 (12.8),
OGGM matches history to 1.01×, and Ladrillo runs 3.7-6.7 pp high at 2100 but
16.4 pp LOW at 2300/ssp126. The 2100 and 2300 discrepancies have opposite signs,
which is a timescale signature rather than a level one — precisely what a
realised-loss constraint (as opposed to GlacierMIP3's committed loss) is able to
see, and a reason to include 2300 in any term.

**R19 — do NOT build a projection term from these archives.** OGGM is 3.11× the
observed historical loss there, so its R19 projections inherit a known bias in
the same direction as Ladrillo's own; GloGEM cannot be historically validated
from its archive at all; and the two disagree by up to 23 pp. Using them would
import an unverifiable projection constraint into the one block whose problem is
already that it is unconstrained by observation. **R19 should be anchored on
GlaMBIE observations plus a tightened GlacierMIP3 rung**, exactly as the revised
R19 design note recommends, and the archives used only as a cross-check.

Worth recording as a cross-check result: the D1 R19 block lands on GloGEM
(14.8 vs 13.2 at ssp126, 30.9 vs 32.1 at ssp585) while L10's lands well above
both — a fourth independent line agreeing that L10's R19 melts too much.

## 5. Proposed term, if one is written

Realised loss as a fraction of 2015 block mass, at 2100 **and** 2300, on
**SLOWP and FAST only**:

```julia
# Zekollari et al. 2024 (TC 18:5045) transient-loss constraint, per block.
# mu = the GloGEM/OGGM pooled median; sigma spans the INTER-MODEL spread as well
# as the GCM spread, because region-level model disagreement is the dominant term
# and picking a model is not defensible (the paper says so for R19; the same
# logic applies wherever they part).
ll += logpdf(Normal(ZEK_MU[b, ssp, yr], ZEK_SD[b, ssp, yr]), loss_frac(b, ssp, yr))
```

Three properties to check before it is trusted, none of them done yet:
1. **Mutation-test it** — perturb the block's `kappa`/`nu` and require `ll` to
   move (spec §7.4; a dead term looks exactly like a working one).
2. **Does it duplicate the GlacierMIP3 rungs?** Committed-at-warming-level and
   realised-by-date are different quantities, but they are not independent.
   Measure the posterior correlation before adding both.
3. **Scenario handling.** Our runs use FaIR *mean* GMST, so they are
   scenario-matched but not GCM-matched to the archives; our bands are
   parameter spread only while theirs include GCM spread. **Compare medians,
   never bands**, and do not let the term inherit a σ that assumes GCM-matching.

## 6. Caveats, all binding

- These are **model** constraints, not observations — the same category as the
  GlacierMIP3 rungs already in the likelihood, so not unprecedented, but they add
  process information, not data.
- Adding a 2100/2300 term makes the calibration partly a projection-matching
  exercise. That is a methodological choice for Marcus, not a technical one.
- The GloGEM archive has **no historical period**, so half the model pair cannot
  be validated the way OGGM was in §1.
- Inventory bases differ (Farinotti a0 vs RGI6 volume); the "% of own 2015 mass"
  metric divides that out, but the block *membership* is matched exactly and the
  absolute SLE is not compared anywhere here.
