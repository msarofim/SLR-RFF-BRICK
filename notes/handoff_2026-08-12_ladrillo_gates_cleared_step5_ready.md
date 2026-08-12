# Handoff 2026-08-12 — Ladrillo: both gates cleared, rename landed, step 5 still has two prerequisites

**Self-contained pickup:** this note + `CHANGELOG.md` entries for 2026-08-11/12 +
`notes/note_2026-08-11_gate31_target_conflict_verdict.md` +
`notes/note_2026-08-11_gate32_mengel_to_brickf_attribution.md`. The prior handoff
`notes/handoff_2026-08-11_greenland_pass1_complete.md` is still the reference for
Greenland pass 1 steps 1–4, but **its §3 is now answered** and **two of its numbers
were corrected** — see §2 before reusing it.

Repo `SLR-RFF-BRICK`, branch **`brick-mengel-vnext`**, tip `3f7f2aa`. Five commits
this session (`4bf7493`, `0df767a`, `b38e165`, `245197b`, `3f7f2aa`).

**Run `./run_ladrillo_tests.sh` first** — note the new name. Four suites, all pass.

---

## 0. THE NAME CHANGED — read this before grepping anything

**`BRICK-F*` is now `Ladrillo`** (Marcus, 2026-08-12; Spanish for *brick*). Code
identity moved too: `brickf_` → `ladrillo_`, `BRICKF_` → `LADRILLO_`, Julia struct
`BrickF` → `Ladrillo`. `run_brickf_tests.sh` → **`run_ladrillo_tests.sh`**.

**Ladrillo 1.0 is DEFINED as the version carrying the Greenland update as well as
the GSIC and Antarctic updates** — i.e. the posterior from step 5, which has **not
been run**. Everything on the branch today is **pre-1.0** (`extC` = GSIC +
Antarctic, no Greenland). **Do not label current outputs 1.0.**

**THE TRAP:** `brickf` is a substring of `brickfm`, and **BRICK-FM is a different
model** (MimiBRICK-FM / Mengel line) with ~130 references in this same repo. Never
`sed s/brickf/ladrillo/g`. If another sweep is ever needed, use the five anchored
patterns in `notes/scoping_2026-08-11_ladrillo_rename.md` §2 and assert the
BRICK-FM count is unchanged per file.

**Dated `notes/` are frozen** — filenames and contents. They still say BRICK-F\*
and reference `brickf_*` paths on purpose. `CHANGELOG.md` (2026-08-12) has the
old→new **path mapping table**. Three note files deliberately keep `brickf` in
their names. Don't "fix" them.

`extC` and the component tags (`greenland_ab`, `glaciers_nu3`) were **not** renamed —
orthogonal axes. "Ladrillo, extC posterior" is the correct way to speak.

---

## 1. Where the work stands

| step | state |
|---|---|
| Greenland pass 1, steps 1–4 | DONE (prior handoff) |
| **Gate 3.1** — target conflict | **CLEARED** — §2 |
| **Gate 3.2** — 28 cm attribution | **CLEARED** — §3 |
| Rename to Ladrillo | DONE, byte-identity verified |
| **4.1 decide `g`** | **OPEN — prerequisite for step 5** |
| **4.2 fix or justify β_f** | **OPEN — prerequisite for step 5** |
| **step 5** joint recalibration | **NOT started; blocked on 4.1 + 4.2** |

**Step 5 is not ready to launch.** The prior handoff §4 is explicit that items
4.1 and 4.2 are prerequisites *alongside* the gates, not after them. The gates are
done; these two are not. Do them first or the recalibration carries a parameter the
data cannot see plus an unanchored initial condition.

---

## 2. Gate 3.1 — answered, and it moved the diagnosis

Scripts `python/diag_target_conflict.py`, `python/diag_gis_likelihood_leverage.py`.
Full argument in `notes/note_2026-08-11_gate31_target_conflict_verdict.md`.

**The +0.74 cm conflict is Frederikse 2020's own mid-century budget non-closure.**
It decomposes exactly: `+0.738 = +1.109 (budget closure) − 0.371 (reconstruction)`.
Not a splice (earliest modern-product year is 2019, cannot reach 1950–80). Not
Dangendorf-vs-Frederikse — that term has the **opposite sign**. Our closure matches
Frederikse's own 5000-member ensemble median at **z = +0.006**; ≈1.4σ of their joint
spread. **No data-side surgery is required.**

**The under-melt was never the conflict.** The total channel's own σ there is
1.538 cm. The mechanism is the **sampled per-series AR(1)**: **ρ_gis = 0.985**
(τ 67.5 yr), ρ_steric = 0.973, vs 0.45–0.62 elsewhere. That removes **14–16×** of
the leverage on a mid-century GIS offset. But not enough — driven by the *actual*
extC residuals, the Greenland correction still nets **+12.43 logl** (+16.49 on gis,
−4.06 on the total). **The sampler should take the deal.**

**Two corrections to the record.** The GIS mid-century miss is **+0.822 cm**, not
the 0.5–0.7 cm the sharing memo carries. And the direction is that the target wants
more melt in the **first half** of the century (1920s–40s southern-Greenland
anomaly) — which is what driver option A delivers.

**n_eff caveat:** n(1−ρ)/(1+ρ) gives 0.93 for gis but describes the AR(1) term alone
and **understates** the grip (strip the band term and the penalty goes −27.7 →
−141.7). Never quote n_eff bare.

### Pre-registration for step 5, updated — read the posterior against this
- **Outcome 1 expected**: Greenland improves, total degrades — but "degrades" means
  the total's mid-century residual flipping −0.32 → +0.50 cm, **0.32σ** of its own σ.
- **Outcome 3 (suppression) is less likely than the red team feared.** If the
  posterior *does* come back ≈ extC, the cause is **not** the target conflict —
  look at **sd_gis / rho_gis inflation** next.
- Outcome 2: if glaciers/TE absorb it, check the GlacierMIP3 rungs and the GlaMBIE
  modern rate didn't break.

### OPEN DECISION for Marcus (methodological — do not let the sampler resolve it)
Component and total targets cannot both be met to nominal σ mid-century.
**(a) do nothing and document** — *recommended*: the conflict is inside both σ's and
this keeps the only Frederikse-independent constraint at full strength. **(b)** add
the 0.792 cm ensemble closure sd in quadrature to the total σ in that window.
**Marcus has not ruled.** Ask before launching step 5.

---

## 3. Gate 3.2 — answered, and the headline number must be retired

Script `python/diag_mengel_to_ladrillo_attribution.py`. Note
`notes/note_2026-08-11_gate32_mengel_to_brickf_attribution.md` (frozen name).

The proposed AIS-block swap was **ill-posed** and was not run: Mengel sampled 6 AIS
params, extC samples those 6 **plus 11 more**, and those 11 *are* the
re-parameterisation. Glacier structures differ too. Did a component decomposition
instead, after verifying both vintages share forcing files, FaIR **mean** climate,
and the 1995–2014 baseline.

SSP2-4.5 medians @2100: Antarctic **43.05 → 11.74 (−31.32)**, glaciers +4.29,
TE −1.18, **Greenland −0.15**, total 78.02 → 49.48 (−28.54). **The Antarctic is
110% of the shift.** Robust to vintage (post-2018-ext: 113%).

**But it is NOT a level shift. Do not write "Ladrillo is 28 cm lower than
BRICK-Mengel".** The Antarctic distribution is bimodal (tipped vs not tipped by
2100) and the big movement sits at a different quantile per scenario — SSP1-2.6
p95 −40.16, SSP2-4.5 p50 −31.32 but p05 only −2.59, SSP5-8.5 p05 −32.16 but p95
only −6.05. **What changed is the probability of Antarctic tipping by 2100**, not
the amount conditional on tipping. Quote a distribution.

**And it is substantially prior-driven** — the red team records the 8 non-converged
AIS marginals as the block that sets the tail, and SSP2-4.5 p83 = 41.0 cm as prior-
not data-driven. The tipping fraction *is* that quantity.

---

## 4. Immediate next steps, in order

1. **Get Marcus's ruling on the §2 open decision** (target σ treatment).
2. **4.1 — decide `g`.** The fraction of the 1850 commitment realised at 1850 fits
   at 0.711 with no observational anchor before 1900; stock SIMPLE has g = 0 by
   construction. It was introduced for the ladder cells that were then rejected.
   **Recommendation on record: fix at 0 unless it earns its place in a
   likelihood-ratio sense.** This is the weakest thing in the new module.
3. **4.2 — fix or justify β_f.** The fast rate is unidentified: 100% of its local
   range within Δ<2.3 at corr −0.03 (`outputs/gis_offline_cell_ridge.csv`). Fixing
   it at a literature SMB response time costs nothing measurable and removes a free
   parameter before the MCMC.
4. **4.7 — fix the `python/ladrillo_data.py` RNG call-order dependence** (was
   `brickf_data.py`). The file's own header says to fix it at the next
   recalibration. That is now. It is byte-tested by `python/test_ladrillo_data.py`,
   so the fix is gated.
5. **Launch step 5.** It mints **Ladrillo 1.0** and regenerates every
   posterior-derived output — which is why the rename was done first, so the new
   files carry correct names and correct internal provenance labels on the first pass.

---

## 5. Owed work, not blocking step 5

- **Quarantine sweep** for deliverables built on the 78.02 / 77.7 cm vintage:
  `outputs/quarantine/YYYYMMDD_<tag>/` + README naming the vintage, the files, and
  the canonical replacement. **It is a vintage difference, not a bug** — say so in
  the README. Needs a list of affected deliverables first.
- `data/MimiBRICK/parameters_subsample_brick_mengel_extC.csv` says "brick_mengel"
  although extC has no Mengel glaciers. Wrong *before* the rename; kept separate.
- **4.3** re-check TE against a modern OHC target. Note ρ_steric = 0.973 makes TE
  the *other* near-random-walk channel — §2's finding and 4.3 are plausibly the
  same story, worth doing together.
- **4.4** report a ν sensitivity once. **4.5** refit with the four glacier
  set-asides fixed at prior centres. **4.6** state the structural-uncertainty
  caveat wherever bands are compared to FACTS.
- **Etymology / rationale sentence** for the sharing memo and any paper —
  **Marcus drafts prose**; placeholder is in `CHANGELOG.md`.
- Branch is still `brick-mengel-vnext`; renaming it is optional and was deferred.

---

## 6. Non-obvious state

- **Two tracked files are dirty and are incidental**, unchanged by this session's
  work: `figures/diag_gis_regional_driver.png`, `outputs/mcmc/overdispersed_starts.csv`.
  They were dirty at the start of the previous session too. Leave them or commit
  them deliberately — don't sweep them into an unrelated commit (I kept them out).
- ~53 untracked files, all pre-existing MCMC scratch and raw netCDFs.
- **Verification pattern worth reusing:** a rename is semantically null, so the gate
  is **byte-identity, not "tests pass"** — snapshot the suite output, change, re-run,
  diff with renamed identifiers normalised, and check no tracked output changed
  content. Both passed here.
- The suite is **idempotent on tracked files** — re-running it leaves `git status`
  unchanged. That is what makes the byte-identity gate work; if that ever stops
  being true, something started writing nondeterministic output.
- Python env: `source ~/climate-env/bin/activate`. Julia: `--project=julia_v2`.
- The Bochow-2026 emulator retraction still stands;
  `outputs/scope_greenland_bochow2026*.csv` must not be used. It still contains the
  string `BRICK-F*` — deliberately left alone as a retracted artefact.
- **The external interface is still GMST + OHC only**, deliberately. Regional drivers
  are built *inside* the model as `amp × GMST + offset` with an anchor-preserving
  splice (`ladrillo_driver` in `julia/ladrillo_projection.jl`). Do not break this —
  it is the drop-in property that distinguishes Ladrillo from MAGICC-SLR.
- A+B's 6.30 cm 2100 spread is **on** the evaluation band floor (6.3–7.3), not inside
  it. The joint calibration can only push it down.
- Greenland option C failed and is out of pass 1; the same criticism (proportional
  relaxation cannot serve both a small historical loss and a huge post-threshold
  commitment) applies to A+B at high warming, where it is invisible rather than
  absent. **Flag it wherever 2300 or high-warming Greenland is reported.**
