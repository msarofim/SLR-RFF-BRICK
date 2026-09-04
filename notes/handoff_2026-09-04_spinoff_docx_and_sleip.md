# Spinoff brief — the L24 Word doc + the SLEIP Phase 1 draft

**Written 2026-09-04 (evening) from a FaIRtoFrEDI session, for a SPINOFF session that Marcus will
bring questions to.** This is a **priming brief, not a task list**: read the two documents, hold
the facts below with their provenance attached, and wait for the questions. Do not start editing
the deliverable, and do not re-derive anything marked SETTLED.

⚠ It lives in `SLR-RFF-BRICK/notes/` because both documents are Ladrillo deliverables, per the
cross-repo rule in `FaIRtoFrEDI/CLAUDE.md`. **Launch the session from `FaIRtoFrEDI/` anyway** —
the memory keyspace follows the launch cwd and all of it lives under the FaIRtoFrEDI key.

---

## 1. THE TWO DOCUMENTS

### 1a. The Word doc — `SLR-RFF-BRICK/deliverables/LadrilloUpdateDescription_L24.docx`

**That path is the one to read. It is 2.84 MB, last modified 2026-09-04 15:41, and is UNCOMMITTED
in the SLR repo** (`git status` shows it modified). 114 paragraphs, 11 headings:

```
H1  Ladrillo Sea Level Rise Emulator
H2   Ladrillo Structural Updates        H3 GSIC | H3 Greenland
H2   Ladrillo Calibration Data Updates
H2   Ladrillo Calibration Approach Updates
H2   Ladrillo Observational Comparison
H2   Ladrillo Projection Comparison     H3 Secondary: the SSPs
                                        H3 Ladrillo compared to MAGICC on MAGICC's own climate
                                        H3 Physical intuition — how Ladrillo behaves by scenario class
```

⛔⛔ **THE `.docx` IS THE SOURCE. `FILLED.md` IS DISPOSABLE, GENERATED OUTPUT.** Marcus edits the
Word file directly; rebuilding it from a hand-maintained `FILLED.md` has silently reverted his own
condensing edits **twice**. Memory: `l24_deliverable_docx_canonical`. Before ANY text edit:

```bash
python3 deliverables/sync_filled_from_docx.py --verify
```

That pulls `FILLED.md` up to whatever is CURRENTLY in the `.docx` and round-trips it back through
the same pandoc invocation the build script uses. ⚠ **The 15:41 mtime is later than every commit
in the repo, so `FILLED.md` is behind right now** — sync before reading `FILLED.md` for anything,
and never read it as a proxy for the doc.

⚠ **`deliverables/~$drilloUpdateDescription_L24.docx` exists** — a Word lock file, so the document
may be OPEN in Word. Reading the `.docx` is safe; writing it while Word holds it is not.

⚠ **Two untracked strays at the repo ROOT are NOT the current doc**: `LadrilloUpdateDescription_L24.docx`
(2.91 MB, Sep 2 14:02, different md5) and `LadrilloUpdateDescription.docx` (15 KB, Sep 2). Do not
read or edit either; if the questions turn on doc history, ask Marcus whether the root copies
should be deleted rather than deciding it.

### 1b. The SLEIP Phase 1 draft — ⛔ **NOT ON THIS MACHINE. ASK MARCUS FOR IT FIRST.**

**SLEIP Phase 1**, egusphere-**2026-3874** (Nauels, Wong, Mengel, Nicholls, Smith, Kopp, Slangen
et al.) — the formal sea-level emulator intercomparison. 13 datasets, 7 emulators (BRICK, FACTS,
FRISIA, MAGICC, MP25, ProFSea, SURFER), to 2300, run on native **and** common-MAGICC forcing.
**The author list is essentially everyone Ladrillo is built on.**

I searched for it before writing this: `~/Documents`, `~/Downloads`, `~/Desktop`, the
`~/Documents/2026/ClaudeDocs/Papers/` folder (memory `claudedocs_papers_folder`), and Spotlight for
"SLEIP" / "Nauels" / "egusphere-2026-3874". **Nothing.** The nearest hit,
`Papers/Impacts_of_emissions_and_Earth_system_uncertainties_on_sea_level_rise_outcomes.pdf`, is
**Darnell/Rennels/Errickson/Wong/Srikrishnan** — a different paper (memory `darnell2025`), zero
occurrences of "SLEIP".

⇒ **Every SLEIP number below reached the repo through notes, not through a PDF this machine can
open.** Treat them as RELAYED until the draft is in hand and the number is read off it. That is the
single highest-value thing the first ten minutes of the spinoff session can fix.

---

## 2. WHAT THE REPO ALREADY HOLDS ABOUT SLEIP — with provenance attached

Sources: `LADRILLO.md` §4 and §7, `SLR-RFF-BRICK/CHANGELOG.md` 2026-09-02e,
`notes/handoff_2026-09-02_fable_review_brief.md` §2.6 and §4.

**RELAYED from SLEIP (verify against the draft):**
- 2300 p-box SSP2-4.5: **2.08 m (0.97–11.00)**. Ladrillo L24 gives **2.49 m** — inside, ~20 % above
  their central. Not an outlier.
- Overshoot penalty **0.1–0.3 m at 2300** across seven emulators.
- Their finding: **structural differences dominate over climate forcing; AIS is the largest
  uncertainty.**

**MEASURED here (ours, and safe to quote):**
- Matched-dT overshoot penalty @2300, paired median, cm: Bamber SEJ **1.65**, **Ladrillo L24 2.21**,
  BRICK 2.0 **2.58**, IPCC-AR5 **3.39**, DeConto/Kopp **4.97**, LARMIP-2 **5.39**. Ladrillo is
  **mid-pack**. (`python/diag_matched_dt_penalty.py`; FACTS was run to 2300 on 09-02 so the
  comparison reaches SLEIP's own headline year.)
- **The models split 3–3 on whether the penalty decays.** 2300/2100 ratio: Ladrillo 0.55, Bamber
  0.61, BRICK 0.71 vs AR5 1.07, LARMIP 1.28, DeConto/Kopp 1.34. Ladrillo decays fastest, but an
  independent SEJ workflow sits beside it ⇒ a decaying penalty is **not a Ladrillo peculiarity**.
- **The medians agree and the tails do not.** @2300 medians span 1.65–5.39 cm (**3.3×**); p95 spans
  7.1–858.4 cm (**121×**). Ladrillo p95 **43.3**, BRICK **51.3**; DeConto/Kopp — the only workflow
  that can express MICI — carries a **mean of 107 cm**. The MICI gap lives **entirely in the tail**.
- **Antarctica carries the penalty**, and **the AIS never regrows** on any pathway (memory
  `ais_never_regrows`); the earlier "native regrowth" row was a **dT-bias artifact**.

**⚠⚠ THE TENSION, AND THE RETRACTED VERSION OF IT.** The 09-02 brief recorded a **native-pair**
penalty of **1.1 cm = 0.01 m** against SLEIP's 0.1–0.3 m and called it "an order of magnitude low".
**That framing is superseded**: our SSP5-3.4-OS ended **0.082 K COOLER** than our SSP1-2.6 at 2300,
so the native number was measuring a driver residual. On the **matched-dT** pair it is **+2.21 cm**,
and **BRICK 2.0 agrees at +2.57** (memory `matched_dt_overshoot_pair`). ⛔ **Do not repeat the
0.01 m figure.** The remaining gap is ~**2 cm vs 10–30 cm**, and the leading explanation is a
**statistic mismatch**, not physics:

> ⭐ **`LADRILLO.md` §7 open item 4 — "Which statistic is SLEIP's 0.1–0.3 m?" — is named there as
> the highest-value open item in the whole file.** 0.1–0.3 m is above EVERY model's *median* in our
> table (largest 5.39 cm) but sits in the **mean/tail** region — Ladrillo's own mean is **8.94 cm**.
> ⇒ **If it is a mean or a p-box, our penalty may not disagree with theirs at all.**
> **This is the one fact to extract from the draft first.**

⭐ **Second question for the draft, `LADRILLO.md` §7 item 5: how deep is the real SSP5-3.4-OS
overshoot?** Ours peaks at only **+0.311 K** over SSP1-2.6. If the published pair is nearer
**0.5–0.6 K**, much of any residual gap is **scenario depth, not model physics**.

⭐ **Third: on which forcing?** SLEIP runs native AND common-MAGICC. Our matched-dT pair is the
like-for-like construct; **which of their two columns it should be compared against decides the
comparison** (`like_for_like_forcing` — this class of error has inverted a reading three times on
one dataset).

---

## 3. WHAT ELSE THE SESSION SHOULD HAVE LOADED

- `INDEX_slr.md` and `INDEX_cmp.md` — **not auto-loaded, Read them explicitly.** `INDEX_cmp.md`
  holds the non-pulse cross-model facts including SLEIP and the FACTS matched pair.
- `INDEX_gis.md` and `INDEX_ais.md` if the questions reach Greenland or Antarctica.
- ⚠ Do NOT answer from the `MEMORY.md` one-liners; they are pointers, and answering from them is
  the gist-recall failure `~/.claude/CLAUDE.md` warns about. The directional claims here
  (who is above whom, mean vs median) are exactly where that goes wrong.

---

## 4. STATE AT THE TIME OF WRITING

- `SLR-RFF-BRICK` is on branch **`ladrillo-dev`**; the deliverable `.docx` is **modified and
  uncommitted**, plus two untracked root strays (§1a).
- `FaIRtoFrEDI` is on **`heat-ed-morbidity`**, nothing pushed. Today's work there was the van
  Vuuren pulse comparison, not the deliverable; the only overlap is that both cite the same
  cross-model penalty table.
- **L24 is the champion vintage** since 2026-09-02.

## 5. THE TRAPS MOST LIKELY TO BITE THIS PARTICULAR SESSION

1. ⛔ Rebuilding the `.docx` from `FILLED.md` without syncing first. **Two prior incidents.**
2. ⛔ Quoting the **0.01 m** native penalty, or the **1.1 cm** figure, as a model finding.
3. ⚠ Quoting SLEIP's 0.1–0.3 m against our **median** without first establishing which statistic
   theirs is — the comparison is currently mean-vs-median-shaped and may be no disagreement at all.
4. ⚠ Editing the root-level `.docx` strays instead of `deliverables/`.
5. ⚠ Treating any SLEIP number in §2 as read off the paper. **None of them are** (§1b).
