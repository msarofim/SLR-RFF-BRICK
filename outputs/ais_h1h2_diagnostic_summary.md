# AIS H1/H2 recalibration diagnostic

Frederikse AIS @1900 = -0.64 cm rel 2000 (band -1.30..-0.02); IMBIE ΔAIS 1992-2017 = +0.720 ± 0.156 cm

### FaIR-forced (primary)  (n=10000)

**Historical AIS @ 1900 (cm rel 2000):**
- BRICK draws: median -3.97  (5-95%: -5.09 .. -2.58)
- Frederikse target: -0.64 ± 0.39 (1σ)
- overshoot of median vs Frederikse: -3.34 cm (-8.5 σ)

**Modern ΔAIS 1992->2017 (cm):**
- BRICK draws: median +0.906  (5-95%: +0.692 .. +1.161)
- IMBIE target: +0.720 ± 0.156 (1σ)

**Joint-pass fractions** (within k·σ of BOTH targets):

| k·σ | hist-pass | modern-pass | JOINT | among modern-passers: median hist AIS |
|----:|----------:|------------:|------:|---------------------------------------:|
| 1.65 |   0.6% |  69.2% | ** 0.45%** | -3.94 cm |
| 2 |   0.8% |  81.2% | ** 0.73%** | -3.95 cm |
| 3 |   1.4% |  96.3% | ** 1.30%** | -3.96 cm |

corr(hist, modern) all draws = -0.067;  among modern-passers = -0.035

### IGCC-obs-forced (sensitivity)  (n=10000)

**Historical AIS @ 1900 (cm rel 2000):**
- BRICK draws: median -3.95  (5-95%: -5.05 .. -2.59)
- Frederikse target: -0.64 ± 0.39 (1σ)
- overshoot of median vs Frederikse: -3.31 cm (-8.5 σ)

**Modern ΔAIS 1992->2017 (cm):**
- BRICK draws: median +0.909  (5-95%: +0.678 .. +1.179)
- IMBIE target: +0.720 ± 0.156 (1σ)

**Joint-pass fractions** (within k·σ of BOTH targets):

| k·σ | hist-pass | modern-pass | JOINT | among modern-passers: median hist AIS |
|----:|----------:|------------:|------:|---------------------------------------:|
| 1.65 |   0.6% |  66.8% | ** 0.37%** | -3.94 cm |
| 2 |   0.8% |  78.9% | ** 0.60%** | -3.94 cm |
| 3 |   1.3% |  95.6% | ** 1.19%** | -3.95 cm |

corr(hist, modern) all draws = -0.016;  among modern-passers = -0.000


## Parameter attribution of joint-passers (±3σ, n=130, FaIR-forced)

Percentile rank of joint-passer median within the full posterior (50% = interior/uninformative; >85% or <15% = pushed to a tail):

| AIS parameter | full median | JP median | JP %ile | corr(histAIS, param) |
|---|---:|---:|---:|---:|
| antarctic_s0 | 0.004052 | -0.006625 | 39% | -0.00 |
| anto_alpha | 0.1307 | 0.4684 | 90% | +0.17 |
| anto_beta | 0.8589 | 1.194 | 67% | +0.02 |
| antarctic_gamma | 2.865 | 2.778 | 47% | -0.03 |
| antarctic_alpha | 0.1556 | 0.27 | 70% | +0.16 |
| antarctic_mu | 10.84 | 11.57 | 63% | +0.03 |
| antarctic_nu | 0.009269 | 0.01015 | 59% | +0.15 |
| antarctic_precip0 | 0.7978 | 0.7431 | 44% | -0.13 |
| antarctic_kappa | 0.06794 | 0.06274 | 37% | -0.16 |
| antarctic_flow0 | 1.222 | 1.078 | 38% | -0.17 |
| antarctic_runoff_height0 | 1594 | 1667 | 56% | +0.06 |
| antarctic_c | 92.91 | 94.57 | 52% | +0.01 |
| antarctic_bed_height0 | 779.1 | 781.2 | 52% | -0.00 |
| antarctic_slope | 0.0006478 | 0.0006352 | 40% | +0.04 |
| antarctic_lambda | 0.009965 | 0.00966 | 46% | -0.01 |
| antarctic_temp_threshold | -15.66 | -15.65 | 51% | -0.00 |

## Verdict
**Mixed — recalibration is viable but not a clean data-starvation fix.**

- Only 0.73% of post-#93 draws fit BOTH targets at ±2σ (1.3% at ±3σ); the historical AIS@1900 median (~-4 cm) is ~8σ from Frederikse and is **near-uniform** across the posterior — conditioning on a good modern (IMBIE) fit barely moves it (corr(hist,modern)≈-0.07).
- So the overshoot is NOT a trade-off forced by the modern constraint; it is the default DAIS response to historical forcing under the current priors.
- BUT draws that fit both DO exist in the current support: they sit in the **upper tail of `anto_alpha`** (Antarctic ocean-temperature sensitivity; JP median ~90th pct) with weak, multi-parameter gradients (no single |corr|>0.17). `antarctic_s0` is interior, so this is a dynamic-response issue, not an initial-condition offset.

**Implication for the recalibration plan:** adding a pre-1992 Frederikse AIS target WILL pull the posterior toward higher `anto_alpha`/`antarctic_alpha` — the region that fits both exists, so it is not structurally blocked. However, because that region is a disfavored ~10% tail (with some draws railing at the sampled edge), expect (a) a substantial posterior shift, not a minor tweak, and (b) a need to CHECK whether the `anto_alpha`/`antarctic_alpha` prior bounds are binding — if so, widen them. This is more involved than the GIS fix in #93 and is the single most important open question for Tony.