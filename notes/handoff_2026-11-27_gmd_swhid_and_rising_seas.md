# Handoff 2026-11-27: GMD after submission (Mimi.jl SWHID) and the "Rising Seas" Substack post

Session 6596ba3b (launched from FaIRtoFrEDI, working mostly in SLR-RFF-BRICK, Ladrillo, and `~/Documents/2026/Substacks/RisingSeas/`).
Read with `~/.claude/CLAUDE.md`, this repo's CHANGELOG (2026-11-25, 2026-11-27) and memory `gmd_1111_decisions` (its
11-24 and 11-25 blocks).

## 1. What was worked on

**GMD Ladrillo paper, after submission (11-24).**
- Ladrillo.jl went public. The GitHub release v1.0.0 was published (Claude) and Zenodo 10.5281/zenodo.24445689 was
  published (Marcus). Marcus submitted to GMD on 11-24 and emailed the acknowledged authors.
- Advice for that email: mention the glacier module as the clear improvement, Greenland as "may also be an
  improvement", Antarctica as the least certain. The evidence is in this session's transcript, not repeated here.
- **11-25 GMD technical check:** reference 56 (Mimi.jl v1.6.0) was flagged "No DOI/URL". No DOI exists: Mimi's
  Zenodo archiving stops at v1.5.1, and the concept DOI resolves to v1.5.1. Marcus: "use the Software Heritage ID".
  - Round **r1125** (`deliverables/redline/r1125/`, CHANGELOG 2026-11-25) puts
    `swh:1:rel:0410476503074d090a8e9aa2221ff23922601af8` and its resolver URL in the entry.
  - That ID equals GitHub's v1.6.0 tag object, and its tree `0148d585` is the Manifest's pin.
  - Outputs: `deliverables/GMD.Ladrillo.v1.2026-11-25.{clean,submission}.docx` and `.submission.pdf` (44 pp, lines 1-1138).
  - `word_render.applescript` is now kept in r1125. The copy into Word's sandbox folder stalls about 10 minutes on a
    macOS permission prompt.

**Substack post "Rising Seas" (11-27).** Marcus's draft, with Claude's figures, captions, review edits, HTML and cover.
All files are in `~/Documents/2026/Substacks/RisingSeas/`; its `README.md` records every round.
- Figures:
  - `risingseas_1_glacier_map.png` and `_2_glacier_temperature.png`, from `python/substack_glacier_blocks.py` here
    (outputs `outputs/substack/glacier_blocks_20261127/`, whose README lists every methodological choice);
  - poster panels B and C, cropped;
  - panel D's left half redrawn by `FaIRtoFrEDI/magicc_comparison/poster_agu26/substack_risingseas_panel_d_left.py`;
  - cover `risingseas_cover.png`, from `.../substack_risingseas_cover.py`.
- Text: `RisingSeas.captions.docx` carries six rounds of tracked edits by "Claude" (captions; review fixes; Marcus's
  pulse conclusion and Next Steps; SLEIP spelled out; the approved corrections; map caption colours). There are no
  comments.
- HTML: `RisingSeas_substack.html`, built by `make_substack_html.py` from the **accept-all** view. The paste steps are
  in `RisingSeas_paste_README.txt`.

## 2. Decisions and rationale

- **Glacier map.**
  - Uses GTN-G (2023) region outlines, which have 20 regions: RGI 6's 19 is split into 19 (islands and coastal ring,
    Ladrillo's R19) and 20 (Antarctic mainland = the ice sheet).
  - 05 (Greenland periphery) and 20 are in no glacier cluster and are hatched. 05 is teal, matching the southern
    Greenland line (Marcus); 20 is gray. Region 20 is labelled "20", not "RGI 20", because RGI 6 has 19 regions.
- **Temperature chart, 1900-2050.**
  - Observations: HadCRUT5 cluster series, southern Greenland and the global mean, from Ladrillo v1.0.0 files checked
    against the tag. 11-year centered means use only years after 1897, so none of the region-years filled from the
    global series are plotted.
  - 2025-2050: `src/model.jl`'s glacier_driver/greenland_driver, re-implemented in Python. It is gated against
    `julia/substack_glacier_blocks_check.jl` (4e-15 K); three mutations each fail the gate.
  - Projection basis: the fixed-climate arm (FaIR 2.2.4 calib 1.6.0 vvM ensemble mean) at posterior-median
    amplifications. The joint-arm median is 0.02-0.08 K lower at 2050. FaIR is 0.06 K below HadCRUT5 over 2014-2024,
    so the global line steps down slightly at 2025.
- **House style (memory `saraph_figure_house_style`).**
  - Georgia; coral = slow Arctic, dark blue = faster, purple = Antarctic, teal = southern Greenland, gray = global;
    direct labels, no legend box.
  - The first versions used the dataviz default palette and Arial. They were redone because the house style had not
    been read first.
- **Pulse conclusion numbers.**
  - At 100 years: CH4 gives 1.1-1.8x CO2's sea level rise per tonne CO2e and 0.3-0.6x its warming.
  - Source: `FaIRtoFrEDI/magicc_comparison/poster_agu26/substack_risingseas_numbers.py` (daily step) →
    `answers/substack_2026-11-27/ch4_co2_ratios_100_200yr.csv`.
  - Its 200-year rows reproduce the poster's Conclusion 1 (0.7-1.2, 0.2-0.3). Marcus chose "a century".
- **Review fixes Marcus approved.**
  - Sandy's $8.1B is attributed to human-caused SLR (about 4 in at New York), not the full 8 in.
  - MAGICC-SLR is more responsive in M and H only.
  - "Persist through 2300", not "permanent".
  - The CH4 heat-uptake gap (1.8x at 2100) is not explained by the 10% full-system versus ocean difference.
  - Terms are defined at first mention, and BRICK 2.0 is used in the pulse section.
- **Claims Marcus verified himself.** Miami "four of the top eight" (the Yale article's Figure 1) and the Thanksgiving
  "worse than anything since Hurricane Sandy" (Guardian). Neither page could be read here: the Guardian and Smithsonian
  refuse fetchers, and reading in Chrome was blocked by the permission classifier.

## 3. Files

- **Committed and pushed:**
  - SLR-RFF-BRICK `ladrillo-dev` through 4979a8c, plus the commit holding this handoff;
  - FaIRtoFrEDI `heat-ed-morbidity` through 9e34cbe;
  - Ladrillo.jl `main` is unchanged since the v1.0.0 tag.
- **Not in git** (the Substacks folder is not a repo): everything in `Substacks/RisingSeas/`.
  - `RisingSeas.docx` is Marcus's original draft, unchanged.
  - `RisingSeas.captions.1206.docx` is his 12:06 save, kept because it holds his direct edits.
  - `RisingSeas.captions.r1.docx` is the caption-only copy. Marcus also edited it at 12:08 ("since Sandy"); it is
    stale, so do not build from it.
- **Uncommitted, deliberately:** `outputs/substack/glacier_blocks_20261127/world_land_rmaps.gpkg`, a cache exported
  from R's `maps` package and rebuilt by the script if missing.

## 4. Open items and next steps

1. **Marcus:** accept the tracked changes in `RisingSeas.captions.docx` (or not), paste the HTML into Substack
   following the paste guide, set the cover, publish. If he edits the docx again, rerun
   `python3 -I make_substack_html.py RisingSeas.captions.docx RisingSeas_substack.html`; its gate checks the visible
   text.
2. **Marcus:** upload the r1125 files or reply to GMD's technical check, if not already done (not confirmed here).
3. **When the GMD Discussions preprint DOI arrives:** Marcus adds it to Zenodo as "is supplement to"; Claude adds it
   to `CITATION.cff` on Ladrillo.jl `main`. Do not move the v1.0.0 tag.
4. **Done 11-27 (Marcus: "add the pointer"):** the `substack-formatting` skill now has a "Figures and cover images:
   read the house style first" section, and its description mentions figures. Backup of the previous version:
   session scratchpad only, since `~/.claude/skills` is not under git.
5. The AGU26 GC092 poster runs in its own session (`agu26-pulse-poster`); its handoffs are
   `notes/handoff_2026-11-24*_agu26_*.md`.

## 5. Non-obvious state

- **Poster-derived Substack scripts need `AGU26_AIS_STEP=daily`** (asserted), as the poster panels do.
  `text_numbers_agu26.py` does `os.chdir(REPO)` on import, so pass absolute output paths.
- **The docx edit tooling** is `SLR-RFF-BRICK/deliverables/redline/r1125/{trackedit,edlib,normalise}.py` plus the docx
  skill's `merge_runs.py`, `comment.py` and `office/validate.py`.
  - `trackedit.Doc` assumes the document has some `w:id`; the Substack scripts patch `__init__` for a draft with none.
  - Each round script guards its base by md5. Rebuild from the installed file, never from a stale copy.
- **Word re-saves add `sz` to comment-reference runs**, so removal patterns must allow any run properties.
- **No `node` on this Mac.** The dataviz palette validator runs as `scripts/validate_palette.py`.
- **The `~$singSeas.docx` lock file** in `Substacks/` (not in `RisingSeas/`) dates from 11-26 and is stale.
