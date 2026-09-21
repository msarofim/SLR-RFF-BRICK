# Handoff — the GMD draft is on L27 (one-round tracked swap done); NEXT = Marcus's review + the L27r question (09-20 19:50 → 21:15)

**Start here.** Continues `handoff_2026-09-20b_L27_shipped.md` (its §3 open question, §4 files and §5 traps all still
stand; its §1 NEXT items 1–2 are DONE here). CHANGELOG **09-20f** is the primary record (commit `bd23cc2` on
`ladrillo-dev`, pushed). Memory written: `gmd_draft_swapped_to_l27`; `INDEX_slr.md` live state updated (17.7 KB —
over its 14 KB soft target, under the 18 KB ceiling; the next addition should split or trim).

**STATE AT HANDOFF (2026-09-20 ~21:15):**
- **`deliverables/GMD.Ladrillo.v1_review-2026-09-20b_L27.docx`** = the draft on L27, every change tracked (author
  Claude, date 2026-09-20) over Marcus's 09-20 copy. `validate.py --original --author Claude` PASS; pandoc reject-all
  view byte-identical to the base's. **Untracked in git like every docx in the lineage** — the file on disk is the
  artefact. Marcus reviews in Word (accept/reject); the r4 LWS and r5 Table A2 changes from earlier rounds are
  still pending in it too.
- **L27 is the paper's posterior; L26 stays champion** (`benchmark/champions.json` untouched). Say both.
- The 19:40 background job LANDED (14 vv MAGICC-climate arms OK, memo figures + climate swap exit 0); its outputs
  and the L27 cells/gates/paths of every arm are committed (19e317d had not included them).
- No job is running. Three tracked L24 files differ from HEAD in provenance timestamps only (as before; left).
  Six `outputs/profile_L26_*.csv` are untracked strays from the earlier session (not mine; not committed).

---

## 1. ⭐ NEXT (in order)

1. **Marcus reviews the docx.** Things to look at first: the NEW paragraph "The fast-dynamics parameters are
   propagated, not sampled" (Antarctic section, after the runoff-line paragraph); the rewritten AIC/BIC paragraph
   (BIC now positive at every ρ bound — the "level on BIC" hedge is gone); the six comments marking numbers that
   were NOT re-run on L27 (§3); Table A2's generated caption reads "1 retain" (grammar from `ladrillo_table_a2.py`).
2. **Decide the L27r question** (09-20b handoff §3, unchanged): the stated precision of the AIS projection medians
   between refits. ~4 h; Torch-eligible — ask first.
3. The 09-16 list, unchanged: venue (GMD recommended), package extraction for Tony's team, the `facts` remote, the
   FACTS/MAGICC-scope call, the "must STATE" items, the pulse analysis.

## 2. WHAT THE SWAP CHANGED (receipts: CHANGELOG 09-20f; every number below is in the accepted view)

FIGs 1–6 → `figures/paper/*_L27*.png` (paper renders; FIG 1 alt text says L27). Table 4 = L27 RMSE ratios (AIS
0.026/0.062/0.099/1.077/0.059 … Total 1.986/0.563/0.215/0.677/0.546). Table 5 = 42/27 & 50/35, +2521/+2458,
+84/+21, +141/+78, +208/+145. Text: 50 params (14+9+16+11); α flat [0.05, 0.30], 0.167 [0.148, 0.186], within 4 % of
obs-implied; only TE carries δ; convergence 42/50, 8 AIS fails (T_on 1.31, c 1.08), SLR R̂ 1.001/1.002, ESS ~1240;
hindcast cumulative +20.41 (obs +21.00), 2022–24 +7.88 (+0.07), rate 0.363; TE 1.23× obs, excess 0.7 cm; compensating
error 1900–19 +1.23 of 1.37 (the "same pattern in 1920–49" sentence retired — Ladrillo now beats BRICK on the total
there); "except glaciers 1950–1992 **and Antarctica 1993–2026**"; responsiveness 1.3×/3×; High 71/82/62, 422/414/570,
AIS 244/248/382, MAGICC-climate −15/−22 → 406/392; λ paragraph rewritten (propagated, ensemble 0.0104 ± 0.0036,
widths 314 vs 405); Low 59/46/81, widths 67/137/182; regrowth 0.11/0.10 on FaIR, 1.95 on MAGICC's climate, MAGICC
8.58, climate term 1.84 (share 78 % ⇒ "about ¾" holds); Table A1 152 cells + 8 rows deleted, `ais_precip_u`; Table A2
the 3 L27 rows + 14-parameter caption; the ledger-set-asides + `u_unch` (33 mm, upper half of Parkes & Marzeion)
methods sentence (owed since L26) is in the parameter-count paragraph.

## 3. NUMBERS STILL ON THE L24 BASIS (each has a Claude comment in the docx)

Greenland amplification-held 1–9 cm; the tap's 35.1 cm; Antarctic-amp leverage 58/24 cm and 17/42 cm; RGI 19's
80–3200 yr; runtime 6.2 vs 5.0 ms; **Conclusions' "up to 60 cm by 2300"** — its provenance was NOT found in the
current outputs (joint-arm AIS medians differ from BRICK 2.0 by −31 cm ssp245 / −27 cm vvHL at 2300, fixed-arm not
checked); Marcus should say which arm it came from. Also still not in the paper: the runoff-onset-LOCATION-follows-L
statement (1991/2027/2049/2063; no clean sentence-ready number in hand).

## 4. FILES (new or changed this arc)

`deliverables/redline/apply_edits_r6_l27.py` (the swap; reads every number from its L27 output and asserts the L24
value it replaces), `deliverables/redline/run_r6.sh` (re-runnable pipeline), `deliverables/redline/redline.py`
(+ `edit_table`, `replace_image`, `revert_pending`/`remove_pending_para` (unused in the end), `` `mono` `` runs,
`start_ids_above`). `python/diag_component_error_cancellation.py` (tag-aware; output `_<TAG>.csv`),
`python/plot_vv_gsic_wr_vs_ladrillo.py` (tagged filename + `--paper` caption sidecar). Renamed:
`figures/{,paper/}vv_gsic_ladrillo_L24_2300.png`, `figures/vv_gsic_wr_vs_ladrillo_L24_2300.png`,
`outputs/diag_component_error_cancellation_L24.csv`. New outputs: `scope_ladrillo_vs_brick20_scorecard_L27.csv`,
`diag_component_error_cancellation_L27.csv`, `diag_te_rate_attribution_L27.csv`,
`verify_magicc_regrowth_attribution_L27.csv`, `vv_climate_swap_L27.csv`, `figures/vv_climate_swap_L27_*.png`,
`figures/ladrillo_L27_fig1-3`, `figures/{,paper/}vv_gsic_ladrillo_L27_2300.png` (+ caption). Scratch (not in git):
`deliverables/redline/unpacked/` (the last run's tree), `deliverables/redline/tbl/` absent (pandoc route not used).

## 5. ⚠ NON-OBVIOUS STATE / TRAPS (adds to 09-20b §5)

- **`validate.py` identifies an EXISTING tracked change by author + DATE + text.** A new round must set
  `redline.DATE` to its own date, or a new insertion that repeats a pending one's text is mistaken for it (Table A2's
  "14" did exactly that). Rejecting one's own pending insertion must be a `<w:del>` NESTED in the `<w:ins>` — that
  is what Word writes and what the validator checks; silently removing it reads as an untracked deletion.
- **Word's `<w:lastRenderedPageBreak/>` splits a run's `<w:t>`** — `replace_text`'s single-run matching then misses
  text that the accepted view shows contiguous. The r6 script strips the hints and merges the split `<w:t>` at load.
- **Bold-lead-in paragraphs are two runs** ("High scenarios." + body): anchor `replace_para_text` on the BODY run.
- **A `--tag` that is not honoured reports the old vintage silently** — twice today (`diag_component_error_
  cancellation.py` literal `TAG = "L24"`; the untagged gsic filename). Before quoting a re-run number, read its
  provenance stamp; identical-to-the-old-vintage is a bug signal.
- The docx's Table 4 had been the 09-10 scorecard (AIS 0.676 / 0.019) while `postpred_L24` now gives 0.679 / 0.018
  — the L24 table was two digits stale before the swap retired it. Not a live issue; recorded in 09-20f.
- `python-docx` reports 0 inline shapes on the r6 docx — its XPath ignores drawings wrapped in `w:ins`/`w:del`.
  Not a defect; the XSD validation passed and the media/rels are verified by md5 in the CHANGELOG-era check.
- The memo deliverable `LadrilloUpdateDescription_FILLED.md` / its docx is an L24 document and stays so; only its
  gsic figure REFERENCE was renamed to the tagged L24 filename.
