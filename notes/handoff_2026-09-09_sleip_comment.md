# Handoff — material for Marcus's COMMENT on the SLEIP Phase 1 preprint

**Written 2026-09-09 from a FaIRtoFrEDI-launched session (`ladrillo-dev`), for a NEW session whose
job is to SUPPORT Marcus writing an EGUsphere comment on SLEIP Phase 1.**

⛔ **MARCUS DRAFTS THE COMMENT.** `~/.claude/CLAUDE.md`: "I produce the first drafts of the main
text of my own writing." The new session's role is **numbers, tables, citations, structural
outline, and verification** — not narrative prose. Do not open by drafting the comment.

⚠ It lives in `SLR-RFF-BRICK/notes/` per the cross-repo rule in `FaIRtoFrEDI/CLAUDE.md`, because
it documents BRICK/SLR work. **Launch the session from `FaIRtoFrEDI/` anyway** — the memory
keyspace follows the launch cwd.

⚠ **The parent session is being KEPT for a different purpose** — using SLEIP to improve the
Ladrillo documentation (`deliverables/LadrilloUpdateDescription_L24.docx`). Do not edit the
deliverable from the comment session; that work is live elsewhere.

---

## 0. THE PAPER, AND HOW TO REACH IT

**SLEIP Phase 1**, `https://doi.org/10.5194/egusphere-2026-3874`, discussion started **2 Sep 2026**.
Nauels, Möller, Couplet, Kopp, Kumar, Mengel, Munday, Nicholls, Ramme, Slangen, Smith, Weeks, Wong.

⭐ **THE PDF IS ON THIS MACHINE**: `~/Documents/2026/ClaudeDocs/Papers/SLEIP.egusphere-2026-3874`
(a PDF, **no file extension** — `pdftotext -layout` works). Data `10.5281/zenodo.21027187`;
figure code `zenodo.org/records/21166356`. **Neither Zenodo archive has been downloaded.**

⚠ **FIRST ACTION: find the discussion deadline.** EGUsphere comment periods are finite and the
preprint posted 2 Sep. Nothing in this note establishes how long is left. Check before anything else.

⚠ **AUTHOR RELATIONS ARE NOT NEUTRAL HERE.** The author list is essentially everyone Ladrillo is
built on — **Wong** (BRICK; Ladrillo is a BRICK 2.0 derivative), **Nauels** (Nauels 2017 Eq. 3 IS
Ladrillo's glacier transient), **Mengel** (Ladrillo's glacier equilibrium form), **Nicholls/Smith**
(FaIR), **Kopp** (FACTS). A public comment lands in front of all of them. ⭐ **A decision for
Marcus, not the session: whether some of this is better sent as a note to Nauels/Wong, or offered
as a Phase 2 contribution, rather than filed as a formal comment.** Ask; do not assume.

---

## 1. ⭐ THE STRATEGIC POINT, DECIDE IT FIRST

**The strongest version of this comment does not mention Ladrillo at all.**

Every substantive claim below can be made with **BRICK 2.0 and FACTS — both of which SLEIP itself
includes — plus SLEIP's own published numbers.** Ladrillo is unpublished, is not in SLEIP, and
introducing it invites "your unpublished model disagrees" as a dismissal. Using their own two
models instead makes the argument very hard to wave off.

Ladrillo can still appear as a *third* line ("a further BRICK derivative behaves the same way"),
but it should not be load-bearing. **Put this choice to Marcus early — it changes the whole shape.**

---

## 2. THE FINDINGS, RANKED, WITH PROVENANCE

All numbers below are READ from committed files, not recalled. Reproduce with
`python3 python/diag_sleip_metric_penalty.py` (no args) in `SLR-RFF-BRICK`.

### ⭐⭐ A. The overshoot penalty's DRIVER-SENSITIVITY is unmeasured, and it is large

**What SLEIP says.** Abstract: "an overshoot sea level rise penalty of roughly **0.1 to 0.3 m**
persists by 2300". §4.4: "8 cm (FACTS_1f) to 29 cm (FACTS_3f) … an additional 6 % (FACTS_1f) to
34 % (BRICK)". Fig. 8H caption defines it as "**the median total SLR difference** between
SSP5-3.4-OS and SSP1-2.6"; Fig. 8B draws it as the gap between MEDIAN lines. **Fig. 8 is
MAGICC-forced ONLY — there is no native-forced penalty anywhere in the paper.**

**What we measured.** MAGICC's own ssp534-over − ssp126 overshoot peaks at **+0.659 K**; FaIR's,
on the *identical scenario pair*, at **+0.308 K** — **2.14×**, both peaking in **2059**
(`python/diag_magicc_overshoot_depth.py`). Driving unchanged modules on each climate:

| model | climate | penalty @2300, diff-of-medians | paired median | % of ssp126 2300 total |
|---|---|---|---|---|
| MAGICC-SLR | MAGICC | 14.28 cm | 12.75 | 21.5 % |
| BRICK 2.0 | MAGICC | **19.36 cm** | 11.72 | 23.9 % |
| BRICK 2.0 | FaIR | **5.66 cm** | 2.57 | 6.1 % |
| Ladrillo L24 | MAGICC | 9.58 cm | 5.65 | 16.5 % |
| Ladrillo L24 | FaIR | 3.43 cm | 2.21 | 4.8 % |

⇒ **The climate swap alone moves BRICK 2.0 4.6× (paired median) and 3.4× (diff-of-medians).**
On MAGICC's climate BRICK lands on MAGICC-SLR within 9 % and inside SLEIP's 8–29 cm band; on
FaIR's it falls below it.

### ⭐⭐ B. THEIR OWN FACTS NUMBERS CONFIRM IT — this is the cleanest evidence

SLEIP's **FACTS_1f (8 cm)** and **FACTS_3f (29 cm)** *are* FACTS-on-MAGICC-climate, and their
workflow definitions are ours exactly (1f = `ipccar5/AIS`, 3f = `deconto21`). Same model, same
workflows, only the climate differs:

| FACTS workflow | ours, FaIR climate | SLEIP, MAGICC climate | ratio |
|---|---|---|---|
| wf1f IPCC-AR5 | 3.11 cm | 8 cm | **2.57×** |
| wf3f DeConto/Kopp | 10.51 cm | 29 cm | **2.76×** |
| *overshoot depth* | *+0.308 K* | *+0.659 K* | ***2.14×*** |

Two workflows with completely different Antarctic methods agree on the ratio to within 0.2 and
both bracket the depth ratio; the **1f-lowest / 3f-highest ordering is preserved**. ⇒ The effect
is demonstrable **on SLEIP's own model with SLEIP's own published numbers**, needing nothing of ours
but a differently-forced run of the same code.

⚠ Their FACTS is **v1.1 with their module versions and sample size**; ours is **n = 200**. Like-for-like
on workflow *definition*, not on build. State that.

### ⭐ C. §4.2's "climate forcing hardly matters" has NO POWER over the penalty

§4.2: "the choice of climate forcing hardly matters for most models and components: MAGICC-forced
and native projections are often closely together." That is a statement about projection **levels**,
displayed on axes where 2300 medians span ~**0.35 m to 10 m**. A 5–10 cm shift in a *difference
between two scenarios* is invisible at that resolution. A reader will carry the reassurance from
§4.2 to Fig. 8, where it does not hold. (`no_power_null`: a test whose null is structurally
guaranteed reports "no effect" identically to one that looked.)

**Constructive ask:** scope the §4.2 claim to levels, or report the native-forced penalty.

### ⭐ D. Table 2 gives BRICK a DASH for land water storage — but §3.1 describes BRICK's LWS

Table 2's caption: "Dash indicates components not included in an emulator." §3.1: "The land water
storage component of BRICK is based on mass balance trends between 2003-2013 from Dieng et al.
(2015)." Compare SURFER, which genuinely has none. **Straightforward erratum**, cheap to raise,
and the kind of thing authors are glad to catch pre-publication.

### ⭐ E. Table 2's type scheme is blind to REVERSIBILITY — the property Fig. 8 turns on

A glacier module can be rewritten completely — Wigley-Raper → an equilibrium-volume form with a
relaxation transient, regionalised, **able to regrow ice** — and classify identically (type 2) to
the one it replaced. Yet whether a component can regrow is exactly what the overshoot experiment
measures. SLEIP notes glaciers show "a slow partial recovery … after the GSAT convergence in 2150",
so the property is doing visible work in their own Fig. 8 while being invisible in their taxonomy.

**Constructive ask:** a reversibility column, or a stated limitation.
⚠ This is where Ladrillo makes the point concrete — so it is the one place introducing it may be
worth the cost. Marcus's call.

### F. Depth and structure INTERACT — the reported spread is itself driver-conditional

Ladrillo-vs-BRICK gap @2300: **0.36 cm** on FaIR's shallow pair (2.21 vs 2.57), **6.07 cm** on
MAGICC's (5.65 vs 11.72) — a **16.9×** widening on the paired median, **4.4×** on
difference-of-medians. Two DAIS-lineage models nearly identical at shallow overshoot separate 2×
at MAGICC's depth, because a threshold model only expresses its structure once the threshold is
approached.

⇒ §4.3's framing — spread at a given cumulative GSAT "reflects structural differences … without
any contribution from climate forcing differences" — is true **as constructed** but incomplete:
the *magnitude* of that structural spread is conditional on the driver's overshoot depth.

⚠⚠ **THE MOST INTERESTING AND THE MOST CONTESTABLE POINT.** Measured on two DAIS-lineage models
plus MAGICC-SLR. Non-threshold emulators (ProFSea, MP25, thermal expansion generally) should
amplify far less. **Do not claim the whole 8–29 cm range would collapse.**

### G. (weaker — CHECK BEFORE USING) The penalty is reported as a median, and it is heavily skewed

On our matched pair the penalty distribution has **skew ≈ +3**; FACTS wf3f DeConto/Kopp @2300 has
**median 4.97 cm against a mean of 107 cm**. A median is the one statistic that hides the MICI
tail — the tail §6 calls a central challenge.
⛔ **Verify first whether Fig. 8 panels C–G already display spread.** If they do, this point is
much weaker and should probably be dropped. Nobody has looked.

---

## 3. ⛔ GUARDRAILS — what the comment MUST NOT claim

1. ⛔⛔ **The depth result is for the LEVEL OVERSHOOT PENALTY ONLY.** Memory
   `climate_swap_share_is_per_quantity`: the same BRICK 2.0 climate swap moves the **pulse H/VL
   ratio only 16 %** — module-dominated, the opposite verdict. **A climate-swap share is a property
   of the QUANTITY, never of the model.** Do not write "climate forcing dominates" unqualified.
2. ⛔ **Never assert MAGICC's depth is wrong.** Which of MAGICC/FaIR is right on this overshoot is
   **UNRESOLVED**; `magicc_colder_than_fair_2300` records MAGICC running 0.38–0.93 K colder at 2300
   on declining pathways with that behaviour explicitly **unchecked and load-bearing**. The comment
   says the result is *conditional on* the driver, not that the driver is *wrong*.
3. ⛔ **Our FaIR pair is the IDEALISED `ssp534overMATCH`** — `ERF_126 + max(ERF_534 − ERF_126, 0)`,
   built in forcing space because FaIR's *native* pair INVERTS after 2150. **NEVER quote it as
   SSP5-3.4-OS.** Post-convergence residuals are close to MAGICC's (+0.035 vs +0.044 K @2150), so
   the pairs are comparable, but they are **not identically constructed** — say so.
4. ⛔ **Do not repeat the retired 0.01 m / 1.1 cm native penalty**, or the retracted reading that
   SLEIP's figure "is probably not a median". It **is** a median (Fig. 8H).
5. ⚠ **FACTS on MAGICC's climate is RUNNABLE, NOT RUN by us.** The
   `global.coupling.ssp245.magicc{base,pulse,p10gt}` experiments prove FACTS accepts a MAGICC
   climate step, but no overshoot-pair arm exists. The SLEIP column in §2B is **their** run.
6. ⚠ **Ladrillo at 9.58 cm is inside the precise 8–29 cm range but rounds to 0.10 m** — describe it
   as "at the bottom of their range", not "inside it".

---

## 4. STATE, FILES, AND WHAT IS ALREADY VERIFIED

**Repo `SLR-RFF-BRICK`, branch `ladrillo-dev`.** Relevant commits, newest first:

| commit | what |
|---|---|
| `767ece0` | every arm in SLEIP's metric; the FACTS confirmation (§2B) |
| `acc48cc` | deliverable ¶3 now states the BRICK-philosophy position |
| `867641f` | the decisive arm: modules on MAGICC's climate; also fixed a `[CONTROL]` gate bug |
| `a159169` | SLEIP's penalty is a MEDIAN; MAGICC's overshoot 2.1× deeper |
| `cffb33d` (FaIRtoFrEDI) | the `ssp534over` MAGICC wide cubes + `[GATE-REPRO]` |

**Reproduce everything:** `python3 python/diag_sleip_metric_penalty.py`. Underlying:
`outputs/diag_{sleip_metric_penalty,magiccclim_overshoot_penalty,magicc_overshoot_depth,matched_dt_penalty}.csv`
and `outputs/diag_matched_pair_facts_penalty.txt`.

**Memory to read before answering anything quantitative:** `INDEX_cmp.md`, `INDEX_slr.md`, and the
files `magiccclim_overshoot_penalty`, `matched_dt_overshoot_pair`,
`sleip2026_emulator_intercomparison`, `climate_swap_share_is_per_quantity`,
`magicc_colder_than_fair_2300`. ⛔ Do NOT answer from `MEMORY.md` one-liners.

**Uncommitted / not ours:** two untracked `.docx` strays at the repo ROOT
(`LadrilloUpdateDescription.docx`, `LadrilloUpdateDescription_L24.docx`) — **not** the deliverable,
do not touch. Ask Marcus before deleting.

---

## 5. WHAT HAS NOT BEEN DONE (openings, honestly labelled)

1. **The Zenodo data has never been downloaded.** `10.5281/zenodo.21027187` holds their per-emulator
   output. It would let us (a) read the exact per-emulator penalties instead of the 8/29 endpoints,
   (b) check whether a native-forced penalty is computable from what they released, (c) settle
   point G without guessing. **Cheapest high-value next step by a wide margin.**
2. **FACTS on MAGICC's climate for the overshoot pair — RUNNABLE, not run** (§3.5). Would convert
   §2B from "their number vs ours" into a controlled one-model experiment.
3. **Fig. 8 panels C–G have not been examined** for whether spread is displayed (blocks point G).
4. **Whether MAGICC or FaIR is right about the overshoot depth is untested** and is the scientific
   question underneath the whole comment.
5. **No one has checked FRISIA's native FaIR** (2.1.1, calib 1.1.0) or FACTS's native FaIR (v1.6.4,
   AR6-calibrated) against MAGICC on this pair. If their native FaIR versions give a *deeper*
   overshoot than our 2.2.4/calib 1.6.0, that materially weakens §2A — **and it is checkable from
   the Zenodo release.** ⭐ This is the most likely way the argument is wrong; look before filing.

---

## 6. SUGGESTED FIRST FIVE MINUTES

1. Find the EGUsphere discussion deadline.
2. Put §1 (Ladrillo in or out) to Marcus.
3. Ask whether this is a formal comment or a note to Nauels/Wong.
4. Offer to pull the Zenodo data (§5.1) — it is the one action that could both strengthen and
   falsify the central point.
5. **Then** wait for Marcus to draft. Supply tables, not paragraphs.
