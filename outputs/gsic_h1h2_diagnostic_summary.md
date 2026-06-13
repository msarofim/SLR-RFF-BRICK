# GSIC H1/H2 recalibration diagnostic

Frederikse Glaciers @1900 = -7.27 cm rel 2000 (band -8.86..-5.56); Dyurgerov & Meier ΔGSIC 1961-2003 = +2.127 ± 0.148 cm (1σ quadrature; fully-correlated upper bound σ = 0.953 cm).

### FaIR-forced (primary)  (n=10000)

**Historical GSIC @ 1900 (cm rel 2000):**
- BRICK draws: median -3.25  (5-95%: -3.80 .. -2.81)
- Frederikse target: -7.27 ± 1.00 (1σ)
- bias of median vs Frederikse: +4.02 cm (+4.0 σ)

**Modern ΔGSIC 1961->2003 (cm):**
- BRICK draws: median +2.035  (5-95%: +1.768 .. +2.373)
- Dyurgerov calibration target: +2.127 ± 0.148 (1σ, quadrature)

**Joint-pass fractions** (within k·σ of BOTH targets):

| k·σ | hist-pass | modern-pass | JOINT | among modern-passers: median hist GSIC |
|----:|----------:|------------:|------:|---------------------------------------:|
| 1.65 |   0.0% |  76.8% | ** 0.00%** | -3.29 cm |
| 2 |   0.0% |  86.2% | ** 0.00%** | -3.28 cm |
| 3 |   0.4% |  97.7% | ** 0.00%** | -3.25 cm |

corr(hist, modern) all draws = -0.998;  among modern-passers = -0.997
(NB: hist is signed −melt and modern is signed +melt, both scaling with overall
 glacier-melt magnitude, so a strong negative corr is LARGELY MECHANICAL — one
 latent factor — not an informative free-parameter trade-off. The substantive
 diagnostic is the melt-RATIO below.)

**Melt distribution (historical 1900->2000 : modern 1961-2003):**
- BRICK median: 3.25 : 2.03 cm  => ratio **1.60**
- Observed (Frederikse hist / Dyurgerov modern): 7.27 : 2.13 cm  => ratio **3.42**
- BRICK under-weights pre-1960 glacier loss by ~2.1x relative to obs.

### IGCC-obs-forced (sensitivity)  (n=10000)

**Historical GSIC @ 1900 (cm rel 2000):**
- BRICK draws: median -3.33  (5-95%: -3.89 .. -2.88)
- Frederikse target: -7.27 ± 1.00 (1σ)
- bias of median vs Frederikse: +3.94 cm (+3.9 σ)

**Modern ΔGSIC 1961->2003 (cm):**
- BRICK draws: median +2.169  (5-95%: +1.885 .. +2.529)
- Dyurgerov calibration target: +2.127 ± 0.148 (1σ, quadrature)

**Joint-pass fractions** (within k·σ of BOTH targets):

| k·σ | hist-pass | modern-pass | JOINT | among modern-passers: median hist GSIC |
|----:|----------:|------------:|------:|---------------------------------------:|
| 1.65 |   0.0% |  78.5% | ** 0.00%** | -3.28 cm |
| 2 |   0.0% |  86.1% | ** 0.00%** | -3.29 cm |
| 3 |   0.8% |  96.5% | ** 0.00%** | -3.32 cm |

corr(hist, modern) all draws = -0.998;  among modern-passers = -0.997
(NB: hist is signed −melt and modern is signed +melt, both scaling with overall
 glacier-melt magnitude, so a strong negative corr is LARGELY MECHANICAL — one
 latent factor — not an informative free-parameter trade-off. The substantive
 diagnostic is the melt-RATIO below.)

**Melt distribution (historical 1900->2000 : modern 1961-2003):**
- BRICK median: 3.33 : 2.17 cm  => ratio **1.53**
- Observed (Frederikse hist / Dyurgerov modern): 7.27 : 2.13 cm  => ratio **3.42**
- BRICK under-weights pre-1960 glacier loss by ~2.2x relative to obs.


## Parameter attribution of joint-passers (±3σ, n=0, FaIR-forced)

Percentile rank of joint-passer median within the full posterior (50% = interior/uninformative; >85% or <15% = pushed to a tail):

| GSIC parameter | full median | JP median | JP %ile | corr(histGSIC, param) |
|---|---:|---:|---:|---:|
| glaciers_beta0 | 0.0009421 | nan | nan% | -0.75 |
| glaciers_v0 | 0.417 | nan | nan% | +0.04 |
| glaciers_s0 | 0.0192 | nan | nan% | -0.02 |
| glaciers_n | 0.7838 | nan | nan% | -0.04 |

## Verdict
**H2-leaning — structural, NOT clean data-starvation (and harder than AIS).**

- GSIC@1900 is a **+4σ historical UNDERshoot** (BRICK median ~-3.25 cm vs Frederikse -7.27): BRICK produces too LITTLE early-20th-century glacier loss — the opposite sign to the AIS overshoot, and consistent with the known per-component bias picture.
- The modern calibration window (Dyurgerov 1961-2003) is well fit (~86% within ±2σ), as expected since the posterior was calibrated on it.
- Joint ±2σ pass = **0.00%** (n_JP@±3σ = 0): NO draw fits both, and the WHOLE 10k-draw distribution tops out near -3.8 cm at 1900 (±3σ hist-pass only ~0.4%) — the historical loss has a structural ceiling, not a tail that a re-weighting reaches.
- The mechanism is a **fixed historical:modern melt RATIO**: BRICK splits melt ~1.6:1 (1900-2000 : 1961-2003) but observations imply ~3.4:1 — BRICK under-weights pre-1960 loss by ~2x. corr(hist,modern)≈-0.998 is mostly the mechanical one-latent-factor artifact (signed quantities both scaling with melt magnitude), so scaling glaciers_beta0 just slides draws ALONG that fixed-ratio line — it cannot move them toward the off-line observation point (hist=-7.27, modern=+2.13).

**Implication for the recalibration plan:** unlike AIS (where a ~10% anto_alpha-tail subset already fits both, so a pre-1992 target + possibly wider bounds suffices), the GSIC arm has NO joint-fitting subset in the current support — adding a Frederikse 1900 target alone would trade modern fit for historical fit along the fixed ratio. Breaking it likely needs a STRUCTURAL lever: re-examine the glaciers_v0 (total reservoir) and glaciers_beta0/n priors that set the melt-vs-volume-depletion SHAPE (not just amplitude), and/or accept that the single-reservoir Wong-Bakker GSIC form cannot match both ends. This is the single most important GSIC question for Tony, and is HARDER than the AIS fix.