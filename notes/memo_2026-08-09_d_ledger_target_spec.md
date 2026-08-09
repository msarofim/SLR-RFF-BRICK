# Spec 2026-08-09 — Option D: the model-side ledger for the historical target (Marcus-approved), with P&M 2018 primary receipts

Marcus's ruling (2026-08-09, after the T1 options + two-issue framing): **go ahead with
D** — "make the best defensible historical data target with appropriate set-asides,
uncertainties, and so forth, and then work on getting the model to fit that data
target." Datum edits are out; the vanished/out-of-scope ice is held **separately on the
model side** wherever it appears. P&M 2018 is now on disk
(`~/Documents/2026/ClaudeDocs/Papers/Parkes.Marzeion.s41586-018-0687-9.pdf`) and was
read in full (9 pp incl. Methods + ED Figs 1–2 + ED Table 1); receipts below are
page-referenced. Implementation: `python/d1e_dside_ledger.py` (cell D1e).

## 1. New primary receipts from P&M 2018 (things the repo did not have)

1. **Headline decomposition (Table 1, p. 553):** uncharted 1901–2015 = missing
   (upper 42.7 ± 6.5 / lower 12.3 ± 1.6) + disappeared (5.3 ± 2.4 / 4.4 ± 1.4)
   = 48.0 ± 8.9 / 16.7 ± 3.0 mm SLE. NB the canonical [16.7, 48.0] flat range spans
   the two bound *centrals*; each bound has its own ±. (Not propagated into the
   F_unch prior for now — flagged §5.)
2. **The 1901 uncharted stock is derivable (Table 1):** missing 2015 remainder is
   2.4 ± 0.4 (upper) / 2.1 ± 0.3 (lower); disappeared have zero 2015 mass by
   definition. So stock@1901 = loss + remainder: **upper ≈ 50.4, lower ≈ 18.8 mm
   SLE.** This grounds the pre-1900 set-aside (§3).
3. **Why 1901:** the glacier model is forced by CRU climate observations (Methods
   p. 555, ref 19 CRU TS) — the start year is a data-availability boundary, **not** a
   statement that uncharted melt began in 1901.
4. **Time profile (p. 553 + Fig. 2):** the uncharted contribution "is largest early in
   the twentieth century… decreases gradually to the point where it is negligible by
   2015"; the disappeared-glacier series is explicitly a **constructed linear decline**
   from a 1901 maximum ("we instead show a linear decrease from a maximum in 1901") —
   profile shape is partly convention, which further supports choosing our F_unch
   profile empirically (taper won in D1c) rather than from P&M's plotted shape.
5. **r19 is INSIDE the headline, and removing it RAISES the uncharted estimate**
   (Methods "Impact of Antarctic peripheral glaciers", p. 556): excluding r19, RGIv5
   loss drops 89.1→75.8 mm but missing/disappeared **rise** to 49.1 ± 5.2 / 6.3 ± 2.5
   (power-law exponents steepen). Naive share-subtraction of r19 from U has the wrong
   sign; the effect is small either way.
6. **The upscaling is global-only; P&M explicitly decline to regionalize** (Methods
   p. 555: the regression coefficient "is only generated once, globally"; regional
   masses "not necessarily the same as the sum… for individual regions"). **ED Table 1:
   43.1% of global small-glacier (<10^0.3 km²) area is in r5** (Central Asia 19.3%,
   r19 4.7%); the caption says they cannot tell whether that is real distribution or
   data quality. → Frederikse's regionalization of U by *large*-glacier melt shares
   (r5 ≈ 13%) is Frederikse's own invention and plausibly under-assigns r5.
   **Consequence for us:** F_unch keeps the ×0.87 factor because it must match what
   Frederikse *inserted into the target* (their rule), not physical truth — but this
   is now a documented caveat on the target's uncharted content, and it argues the
   flat U prior should not be narrowed.
7. **ED Fig. 1a:** mean specific mass balance 1901–2015 is nearly flat across size
   classes (~−250 to −350 mm w.e./yr) — small-glacier SLE contribution scales ~with
   area. **ED Fig. 1b:** the smallest surviving glaciers lost almost ALL of their 1901
   mass over 1901–2015.

## 2. The ledger (what compares to what)

The 20th-century flow target is already D-compliant (set-asides on the model side:
F_unch for the inserted uncharted content; obs_adj for the r19 seam; r5 removed at the
splice). D1e extends the same principle to the one remaining datum:

**Leclercq comparison (A2b + gate), datum untouched at N(20, 9) mm** (receipts-family
envelope; basis of its primary member: 1850–1900, excl r19, incl r5):

```
S_ledger(1900) = S_inv(1900)        # SLOWP+FAST melt 1850→1900 (excl r5, excl r19 — model, no new dof)
               + S_r5               # set-aside: charted r5 melt 1850–1900   (prior, fitted)
               + U_pre              # set-aside: pre-1901 melt of ice not in the present
                                    # inventory (P&M uncharted stock + pre-1901-vanished
                                    # glaciers)                              (prior, fitted)
ll_lec = Normal(20, 9).logpdf(S_ledger)     ;  gate g_lec = |z| <= 2
```

R19 is excluded from S_inv here because the datum's primary basis excludes r19 (the
model's R19 1850–1900 melt is ~1–2 mm; the r19 share of U_pre is ~5% of small-glacier
area — both ≪ σ = 9 and both documented rather than parameterized).

## 3. Set-aside priors (the "appropriate uncertainties")

**U_pre ~ flat [0, 25] mm.** Construction from receipts:
- stock@1901 ≈ 18.8–50.4 mm (receipt 2) — the stock existed and was large;
- early-20th-c uncharted rate: avg 1901–1990 is 0.17–0.53 mm/yr, "largest early"
  (receipt 4) → early rate up to ~0.6 mm/yr;
- pre-1900/early-20th rate ratio m ∈ [0.25, 1.0] (weaker forcing, late regional LIA
  maxima at the low end; fast small-glacier response at the high end; m ≫ 1 excluded
  by self-consistency — the stock had to survive to 1901 with a century of melt ahead);
- 50 yr × m × rate → ~[2, 30]; capped at 25 (pre-1901 shed ≳ half the 1850 stock would
  contradict "largest contribution early in the twentieth century").
- **The 0 edge is load-bearing, not padding:** under the charted-scope reading of
  Leclercq (T1 memo §1), the datum contains no uncharted melt and U_pre = 0 is the
  correct value. The prior is flat (mirroring Frederikse's uniform U convention);
  a half-normal |N(0, 12)| alternative (mass at the reading-(ii) end) is noted for
  extC if Marcus prefers.
- No ×0.87: the datum includes r5, and r5 holds 43.1% of small-glacier area
  (receipt 6) — scoping U_pre to the datum means keeping it global-minus-r19,
  and the r19 share (4.7% of small-glacier area) is noise against σ = 9.

**S_r5 ~ N(2.5, 2.0) mm, bounds [0, 8].** Charted r5 melt 1850–1900: 13% (RGI
large-glacier melt share, the Frederikse rule — appropriate here because the *charted*
r5 stock is large-glacier-dominated) × the ~20 mm family value ≈ 2.6 mm; σ = 2 spans
0–6.5 (Arctic amplification / share drift). The 43.1% figure does NOT apply here — it
is the small-glacier (uncharted-class) share, which lives in U_pre.

**Both set-asides are identified only by this one datum + their priors** — they are
prior-dominated bookkeeping parameters, reported as such (the check is "interior vs
railed", exactly as U-vs-Frederikse-central).

## 4. Cell D1e — implementation contract

- Exec-inherits the full d1d machinery (structures, 4-rung fits, anchors, caches,
  obs_adj) by splitting `d1d_fourrung_seam.py` at its run marker; output paths rebound
  after the exec (rebind trap). Structures built in d1d's exact order (A, B, C) so the
  seeded rng stream reproduces the d1d block parameters bit-comparably.
- Configs: **C_both only** (the 2-block A_4rung ablation cannot separate r19 from
  SLOW, so the ledger is undefined there) × {unc_t5d (primary), unc_sx2} × {ANCH, MID,
  FREE}. Free params gain (U_pre, S_r5) in every arm AND in the pathological
  comparator (matched-freedom rule).
- Gates: `g_lec` (|z| ≤ 2 on the ledger) REPLACES `g_s1900` in npass/feasible;
  the legacy quantity (S_all incl R19) and the legacy 10–30 box verdict are still
  computed and reported per the original-metric rule.
- Deficit reported twice: vs the re-fitted matched-freedom pathological (canonical)
  and vs the stored d1d pathological reference (comparability).
- New emitters (the T2 cheap items): per-era model flow rates (mm/yr, hind and
  hind+F_unch) alongside obs/obs_adj/δ-corrected obs era rates; per-reservoir modern
  rates (2000–23, 2015–23) vs their GlaMBIE values; the modern-rate comparator printed
  against the **adjusted** obs (the 0.766 correction from the T2 memo, computed from
  OBS_ADJ, not hardcoded).
- Sanity battery (all evaluation-based, no optimizer in the loop):
  1. inherited: obs_adj pre-2019 identity + net r19 removal;
  2. structures reproduce `d1d_blocks.csv` (a, b, T_off, κ, ν per reservoir, ≤1e-4);
  3. **legacy-mode evaluation identity:** the stored d1d C_both/ANCH θ (from
     `d1d_fourrung_seam.csv`) evaluated under the inherited d1d `loglik` reproduces
     the stored flow_win / S1900 / logJ columns;
  4. ledger arithmetic identity (z recomputed from components).
- **Pre-registered predictions:** P1 — ANCH deficit unchanged (8.21 ± 0.05): the
  ledger params are separable from (σ, ρ, U, δ) in ANCH. P2 — ledger fits interior
  (U_pre ≈ 6–11, S_r5 within prior, z_lec ≈ 0) → ANCH/MID npass 4/4. P3 — FREE
  decouples from the Leclercq pull (envelope theorem via U_pre): FREE legacy-S1900
  drops from ~27–28 toward the ANCH range; spread still fails (FREE conclusions
  unchanged). Watch item (not a prediction): C_both/MID/unc_sx2 deficit 5.07 vs
  tol 5 under the reshaped MID objective.
- **Pre-registered bars:** minimal = ANCH C_both deficit ≤ 8.4, |δ| ≤ 1σ, 4/4 gates
  (now reachable via g_lec); strong = feasible (4/4 AND ≤ 5) — **not expected to be
  met** (deficit ~8.2 is untouched by D; D1e's purpose is the honest target ledger,
  not deficit improvement).

## 5. Companion changes and flags

- **Julia pairing (change-together trap):** `julia/calibrate_mcmc_ext.jl` A2b gets the
  D-ledger spec as a documented comment block + explicit TODO for the extC surgery
  (implementing it now in the extB3-era single-reservoir calibrator would be dead code
  — the glacier block is being replaced wholesale in the extC surgery anyway). The
  marginalized equivalent for a sampler that prefers fewer params: convolving the
  set-aside priors gives ≈ Normal(20 − 12.5 − 2.5 = 5.0, √(9² + 25²/12 + 2²) ≈ 11.7)
  on S_inv(1900) — but the explicit 2-param ledger is preferred for reporting.
- **Flat-U prior width (F_unch):** the P&M per-bound errors (±8.9 / ±3.0) and the
  Frederikse-regionalization caveat (receipt 6) both argue the [14.5, 41.8] flat range
  is if anything too narrow. Not changed in D1e (it matches the Frederikse insertion
  convention); flagged for the extC prior review.
- The obs-amp sensitivity arm remains outstanding (unchanged by this cell).
