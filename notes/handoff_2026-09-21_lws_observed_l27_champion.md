# Handoff — L27 champion; refit precision measured; projections on the OBSERVED land-water series; draft at r8 (09-21 06:20 → 10:05)

**Start here.** Continues `handoff_2026-09-20c_docx_on_L27.md` (its §5 traps stand). CHANGELOG **09-21a–d** are the primary
record (commits `d371a08`, `3bf1618`, `b94888c`, `31ace68`, `9ad9f0a` on `ladrillo-dev`, all pushed). Memory written today:
`lws_observed_projections`, `stale_parquet_twin_shadowed_the_csv`, `calibrator_identity_gate_red_since_0918`; updated
`l27_paper_posterior` (precision CLOSED), `lws_central_default` (SUPERSEDED), `INDEX_slr.md` (⚠ **18,154 B of its 18,432 B
ceiling — split before the next addition**), `INDEX_diag.md`.

**STATE AT HANDOFF (2026-09-21 ~10:05):**
- **L27 is CHAMPION on all six modules AND the paper's posterior** (`champions.json`, since 09-21; frozen snapshot
  `benchmark/reference/L27/`).
- **Between-refit precision measured** (L27r, L27b overnight): every AIS projection median reproduces to ≤ 1.3 cm at 2300,
  the hindcast to 0.005 cm; the L26→L27 ocean-parameter shift was L26's own unfinished relaxation (eight-segment drift
  test), not the fast-dynamics cut (conditioning L26's draws on γ/λ/T_crit moves ≤ 0.05 sd) and not the ledger. Sentence
  in the draft (r7). L27r/L27b subsamples exist under `data/MimiBRICK/` (gitignored; test arms, not force-added).
- **Projections carry the OBSERVED land-water series** on both arms since this morning (`LWS_MODE = :observed`);
  hindcast-side drivers pin `:central`. Every paper arm re-run and verified (+0.35 cm on every total from 2024; nothing
  else moves beyond AIS 0.0125 cm). Draft r8 = **`deliverables/GMD.Ladrillo.v1_review-2026-09-21b_L27.docx`** — built on
  Marcus's 07:49 copy of the 09-21 file, which he edited with **tracking OFF** (abstract, two intro paragraphs, "almost"
  in the tap sentence, the fast-dynamics paragraph's last clause, parentheses in the LWS paragraph — all kept).
- Nothing is running. Disk: the L27r/L27b chains (16 GB) are on disk, not in git.

## 1. ⭐ NEXT (in order)
1. Marcus reviews r8 (the LWS paragraph is the substantive text change; the High/Low numbers moved by ≤ 1 unit; FIG 4's
   land-water panel now shows the observed series). ⚠ Tell him: edits made with tracking off are silently absorbed into
   the next round's base — fine, but the redline then shows his wording as the "deleted" side of my replacements.
2. **Split `INDEX_slr.md`** (18,154 B). Natural cut: the L26/L27/refit arc + LWS conventions into an `INDEX_slr_l27.md`.
3. Pool L27 + L27r (8 chains) only if a reviewer asks for better-mixed ridge marginals — not recommended otherwise.
4. The 09-16 list: venue (GMD), package extraction for Tony's team, `facts` remote, FACTS/MAGICC scope, pulse analysis.

## 2. WHAT LANDED TODAY (receipts by CHANGELOG entry)
- **09-21a** overnight result; **09-21b** L27 promoted + `plot_hindcast_components --compare=`; **09-21c** the low-hanging
  list — the calibrator identity gate had been RED since 09-18 (LWS ruling, 1e-4 via the AIS feedback), proven the only
  change, re-frozen with the 09-16 reference archived; `--dump-priors` no longer clobbers the production seed_diag;
  runtime L27 1.26×; four more tag literals retired; `run_postprocess.sh` by tag; paper-arms template writes the table
  sources; **09-21d** observed LWS + the stale-Parquet trap (`draws_io` preferred a twin by NAME; every BRICK 2.0
  comparison number 09-01→09-21 was the 09-01 :seeded run, ≤ 0.44 cm) + draft r8.

## 3. ⚠ NON-OBVIOUS STATE / TRAPS (adds to 09-20b §5 and 09-20c §5)
- **LWS vintages in outputs**: pre-09-18 `:seeded`; 09-18 → 09-21 morning `:central`; after `:observed`. The cells
  `provenance` column says which ("lws observed / central / seeded"). The four `ssp534over*`/`nomarker` BRICK arms were
  NOT re-run (still :central). L27r/L27b ssps components are :central.
- **Parquet twins**: `draws_io.draws_path` now ignores a twin OLDER than its CSV (stderr warning). After any arm re-run,
  run `python/refresh_draws_parquet.py` (or read the warning). Ten twins refreshed today.
- **Identity gate**: run `scripts/gate_calibrator_identity.sh` after every edit to `calibrate_mcmc_ext.jl` OR
  `brick_mengel.jl`. Reference = LWS :central objective; the :seeded 09-16 reference is archived beside it.
- **Editing inside a pending insertion** (`redline.edit_ins_text` / `smart_replace`): the outer `<w:ins>` must be SPLIT
  around the edit with the original author+date kept on the pieces, or validate.py reports the text missing.
- **Two driver instances ran concurrently for ~1 h this morning** (a launch command that errored after starting the
  script). Killed by PID; every output verified against HEAD (52 cells gated, 90 paths/gates/ssps shape-checked). Launch
  with a single `(nohup … &)` line and confirm ONE instance with `ps` before doing anything else.
- **Marcus's tracking-off edits** (07:49) are in the r7/r8 base untracked; the reject-all view of r8 equals the 09-21 file
  as on disk, not the 09-20 base.
