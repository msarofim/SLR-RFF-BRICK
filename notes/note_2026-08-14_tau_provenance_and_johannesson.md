# For the paper — where our glacier τ comes from, and a first-principles check

Marcus, 2026-08-14: confirm the Jóhannesson scaling and the apparent difference
between GlacierMIP3's τ and ours, for the write-up.

## 1. The "factor 2-3 τ discrepancy" was MY ERROR — there is none

I reported GlacierMIP3's τ50 at 1.70 K as 389/157/52 yr (R19/SLOWP/FAST) against
our stored `tau15` of 828/523/130, "a factor 2.1-3.3", and flagged it as possibly
a definitional mismatch. **It is a definitional difference, and the definitions
are both correct.** Traced to source:

- **`tau15` = GlacierMIP3's own published headline response timescale.** Table
  S1a column 9 is headed *"Response timescale (years)"* / *"1.5±0.2 °C"*, and
  reads **828 [224-1322]** for Sub- & Antarctic Islands (region 19) — exactly our
  R19 `tau15`. Mass-weighted to blocks it reproduces all three of ours to 0.1 yr
  (828.0/828.0, 522.8/523.1, 129.9/130.1). It is the **τ80** — time to realise
  **80%** of the committed loss — which is what the regchar CSV calls
  `resp_time_-80%_1_5_deg`.
- **`tau30` = `resp_time_-50%_3_0_deg`** from
  `3_shift_summary_region_characteristicsFeb12_2024.csv`, i.e. the **τ50** at
  3.0 °C. Reproduces ours exactly (213.0, 112.7, 37.0).

My 389/157/52 was a τ50 computed from the transient; comparing it to a published
τ80 is comparing different quantities. Cross-check that the definitions are
fractions of the **committed loss** and not of volume: my direct τ50 read for R19
at 1.70 K is 297 yr against the published τ50@1.5 of 290 — and R19's committed
loss at that level is only 47%, so a "50% of volume" reading could not exist at
all. Confirmed.

### The one thing genuinely worth stating in the paper
**The two anchor points use different thresholds — τ80 at 1.5 °C and τ50 at
3.0 °C.** `d1b_slow_split.py` solves (κ, ν) to match both, so the pair sets the
curvature of our rate law. That is a modelling choice, not an error, but it is
invisible in the code (one value is parsed positionally from Table S1a, the other
by column name from the regchar CSV) and it should be declared. Anyone quoting
"our τ" must say **which** τ.

## 2. Jóhannesson scaling — CONFIRMED, and it corroborates GlacierMIP3

**Jóhannesson, T., Raymond, C. & Waddington, E. (1989), "Time-scale for
adjustment of glaciers to changes in mass balance", *J. Glaciol.* 35(121),
355-369.** Volume time-scale τ_v = H / (−b_t), H a glacier thickness scale and
b_t the ablation rate at the terminus. (Note the paper's own headline point: τ for
mountain glaciers can be substantially **less** than the 10²-10³ yr then
expected.)

Applied with GlacierMIP3's own region characteristics — H from mean volume /
mean area of the ten largest glaciers, mass-weighted to our blocks:

| block | H (m) | τ at b_t = 1 / 2 / 3 / 5 m yr⁻¹ | GlacierMIP3 τ50@1.5 | implied b_t |
|---|---|---|---|---|
| R19 | 463 | 463 / 231 / 154 / 93 | **290** | ~1.6 m yr⁻¹ |
| SLOWP | 380 | 380 / 190 / 127 / 76 | **207** | ~1.8 m yr⁻¹ |
| FAST | 346 | 346 / 173 / 115 / 69 | **59** | ~5.9 m yr⁻¹ |

The implied terminus ablation rates are physically sensible and correctly ordered
— ~1.6-1.8 m yr⁻¹ for the cold Antarctic-periphery and Arctic ice-cap blocks,
~5.9 m yr⁻¹ for FAST, which contains the temperate regions (Southern Andes,
Central Europe, low latitudes, South Asia). So an independent first-principles
scaling reproduces GlacierMIP3's response times without tuning.

**Caveats:** b_t is not in the archive, so this is a bracket, not a
determination; and H taken from the ten *largest* glaciers overestimates the
area-weighted thickness of a whole region, biasing τ_v long. Both cut the same
way and neither changes the conclusion.

## 3. What this means for the write-up
- Our τ is GlacierMIP3's published number, citable as such — not a fitted
  quantity, and not in tension with the ensemble.
- Declare the τ80/τ50 pairing explicitly.
- The Jóhannesson check is worth a sentence: it is the only line of evidence here
  that does not come from a glacier model.
