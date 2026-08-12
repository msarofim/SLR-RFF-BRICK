# Scoping: renaming BRICK-F\* → Ladrillo

2026-08-11. Inventory and execution plan for the rename Marcus proposed. **Nothing
has been renamed** — this note is the scope, the hazards, and the decisions needed.

**Bottom line.** The rename is mechanically small (426 occurrences, 25 files, one
repo) and carries **no public-surface or DOI consequences** — `README.md` and
`CITATION.cff` never name the model, so repo identity and model identity are
already decoupled. There is exactly one real hazard (§3) and one strong timing
argument (§6): do it **before** step 5, because step 5 regenerates every
posterior-derived output anyway, so the regeneration is paid once instead of twice.

---

## 1. Three separable axes — decide each independently

| axis | example | in scope? |
|---|---|---|
| **A. Display name** | `"BRICK-F*"` in prose, figure legends, CSV `source` column | yes — this is the ask |
| **B. Code identity** | `brickf_projection.jl`, `BRICKF_REF`, `struct BrickF` | recommend yes — see D1 |
| **C. Vintage / component tags** | `extC`, `greenland_ab`, `glaciers_nu3` | **no** — orthogonal axes |

Axis C is worth stating explicitly because it is tempting to sweep it in. `extC`
labels a *calibration vintage*, not a model; `greenland_ab` and `glaciers_nu3`
label *components*. Renaming them would destroy the ability to say "Ladrillo,
extC posterior" and would break every cross-reference in the dated notes.

---

## 2. Inventory (verified by `git grep`, 2026-08-11)

**426 occurrences across five distinct patterns.** They need five distinct
patterns because no single one covers the set safely:

| # | pattern | count | what it is |
|---|---|---|---|
| 1 | `BRICK-F\*` | 112 | display name (prose, labels, CSV cell values) |
| 2 | `brickf_` | 192 | lowercase prefix — filenames and functions |
| 3 | `BRICKF_` | 88 | Julia/Python module constants |
| 4 | `BrickF` | 8 | the Julia struct |
| 5 | `_brickf` (suffix) | 26 | trailing form: `posterior_predictive_brickf.jl`, `project_ssps_components_brickf.jl` |

**25 files carry it in the filename**: 4 `julia/`, 7 `python/`, 6 `outputs/`,
4 `figures/`, 3 `notes/`, plus `run_brickf_tests.sh`.

**By destination:**

| destination | occurrences | treatment |
|---|---|---|
| live code (`.py` / `.jl` / `.sh`) | 249 | rename (§5 tier B) |
| dated `notes/` | 38 | **freeze** — see D4 |
| CSV cell values | 44 | regenerate, don't sed — see D5 |
| `CHANGELOG.md` | 18 | freeze history, add a rename entry |

**Public surface is clean.** `README.md` and `CITATION.cff` contain zero
occurrences of the model name. The repo `msarofim/SLR-RFF-BRICK` and its concept
DOI (zenodo.20312324) describe the *repository*, not the model.

**Cross-repo: zero true hits.** `MimiBRICK-FM` has none. The 30 apparent hits in
`FaIRtoFrEDI` are all `brickfm` / BRICK-FM — a different model (see §3).

---

## 3. THE HAZARD — `brickf` is a substring of `brickfm`

**A naive `sed s/brickf/ladrillo/g` would silently corrupt 130 references to
BRICK-FM**, which is a *different model* (the MimiBRICK-FM / Mengel line). In this
repo alone: 128 `BRICK-FM` + 2 `brickfm`, spread across 17 files including
`julia/brick_mengel.jl`, `julia/diag_decomposition.jl`, and eleven dated notes.

Mitigations, all required:

- Use the **five anchored patterns in §2**, never a bare `brickf`. Verified:
  `\bbrickf\b` matches **0** times, so every lowercase occurrence is part of a
  longer token and the anchored set is exhaustive.
- Patterns 1 and 4 are already safe by construction — `BRICK-F\*` requires the
  literal asterisk, and `BrickF` is case-sensitive so it cannot match `BRICK-FM`.
- **Dry-run and eyeball the full diff before committing.** 426 changes is small
  enough to read.
- Post-rename assertion: `git grep -ciE 'brick-fm|brickfm'` must return the
  **same 130** it does today.

Incidental benefit of the new name: `BRICK-F*` contains a literal `*`, which is
hostile to grep, filenames, and regex. `Ladrillo` removes that permanently.

---

## 4. Naming convention to settle before touching anything

Proposed mapping, so the five patterns have unambiguous targets:

| from | to |
|---|---|
| `BRICK-F*` | `Ladrillo` |
| `brickf_` | `ladrillo_` |
| `BRICKF_` | `LADRILLO_` |
| `BrickF` (struct) | `Ladrillo` |
| `_brickf.jl` (suffix) | `_ladrillo.jl` |

`ladrillo` is 8 characters against `brickf`'s 6 — some long filenames grow
(`julia/project_ssps_components_ladrillo.jl`, 41 chars). Acceptable. A shorter
code prefix (`ldr_`) is possible but I would not: the whole point is legibility,
and a cryptic prefix reintroduces the problem the rename solves.

---

## 5. Risk tiers and treatment

**Tier A — free.** Forward-looking prose: `CHANGELOG.md` going forward, the
sharing memo's header, any new note. Just write the new name.

**Tier B — mechanical, strongly gated.** Code identifiers and script filenames
(249 occurrences, 12 code files). The safety net is unusually good here:
`run_brickf_tests.sh` drives **four** suites, one of which validates the Greenland
port at 1e-9 against a Python reference. **The rename is semantically null, so the
gate is byte-identity**, not "tests pass":

1. Run the suite, capture every output CSV to a scratch snapshot.
2. Rename (`git mv` for files; anchored `sed` for contents).
3. Re-run and `diff` every output against the snapshot. **Any non-identical byte
   is a bug in the rename.**

**Tier C — regenerate, do not edit.** The 44 CSV cell values (`source` column in
`outputs/brickf_model_comparison{,_spread}.csv`, plus
`outputs/scope_greenland_bochow2026.csv`). Per the standing convention that labels
derive from named constants, these should change because the constant changed, not
because someone edited a data file. `python/brickf_model_comparison.py` is cheap
to re-run. Note `scope_greenland_bochow2026.csv` is already under the Bochow-2026
retraction and must not be used regardless.

**Tier D — do not do now.** Repo name, branch names, Zenodo DOI. See D2/D3.

---

## 6. Timing — before step 5, and the reason is cost

Step 5 (joint recalibration) regenerates the posterior and therefore every
posterior-derived output and figure. If the rename lands **after** step 5, every
one of those artefacts gets renamed a second time and the provenance strings
written *inside* them (per the output-provenance convention) will say `BRICK-F*`
until yet another regeneration.

Landing it **before** step 5 means: rename code now (cheap, byte-identity gated),
and step 5's own regeneration emits correctly named files with correct internal
provenance labels, at no extra compute.

The stale outputs under the old names then get the standing quarantine treatment
alongside the vintage quarantine already owed from gate 3.2 — one sweep, not two.

---

## 7. Decisions needed

| # | decision | recommendation |
|---|---|---|
| **D1** | Display name only, or display + code identity? | **Both.** A half-rename rots — you end up with `Ladrillo` in figures and `brickf_` in the code that made them, and every new reader has to learn both. |
| **D2** | Rename the repo `SLR-RFF-BRICK`? | **No, not now.** Public repo + concept DOI zenodo.20312324. README/CITATION don't name the model, so the two identities are already cleanly separated. Revisit at paper submission, as a deliberate release act. |
| **D3** | Rename branch `brick-mengel-vnext`? | **Optional, low cost** (delete + re-push). If yes, do it in the same commit window so the CHANGELOG entry can name both. |
| **D4** | Rewrite dated notes/handoffs? | **No — freeze them.** They are records of what was known when written; rewriting falsifies provenance, the same principle as quarantining rather than deleting outputs. Add one dated pointer line at the top of `memo_2026-08-10_brickf_sharing.md` and a CHANGELOG rename entry. |
| **D5** | CSV `source` values: sed or regenerate? | **Regenerate.** Labels derive from named constants. |
| **D6** | Before or after step 5? | **Before** — §6. |
| **D7** | Start version numbering? | Worth it. A rename is the natural moment: **Ladrillo 1.0 = the post-step-5 posterior**. Avoids "BRICK-F\* but the newer one" forever. |
| **D8** | Do `extC` / component tags change? | **No** — §1 axis C. |
| **D9** | Fix the stale posterior filenames? | `data/MimiBRICK/parameters_subsample_brick_mengel_extC.csv` says "brick_mengel" but extC no longer has Mengel glaciers — already wrong today. Could ride along, but it is a **separate** correctness fix; keep it in its own commit so the rename diff stays byte-identity-checkable. |
| **D10** | Etymology sentence | Needed for the sharing memo and any paper — one line on why the name and what it descends from. **Marcus drafts**; I'll leave a placeholder. |

---

## 8. Effort

Tier B is the only real work: ~12 code files, 25 filename changes, 314 identifier
occurrences, gated by byte-identity on the four suites. The dominant cost is
reading the diff and running the suite twice, not the editing. Tier C is one
script re-run. Tiers A and D are minutes.

The one thing that would make this expensive is discovering the rename is *not*
semantically null — i.e. some output differs after renaming. That would mean a
path or a label was load-bearing in a way nobody intended, which is worth knowing
regardless.
