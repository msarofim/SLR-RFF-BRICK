# Poster handoff to IEc graphics — checklist

When sending the near-final poster to IEc graphics for visual polish
ahead of the AGU Chapman SLR conference, package three things:

## 1. The near-final composite poster PDF

The current wireframe / layout reference:

```
outputs/poster/layout_mockup.pdf
outputs/poster/layout_mockup.png   (PNG version for quick preview)
```

IEc graphics should use this as the *layout reference* — panel
positions, panel labels (A–L), the discussion-box position, the
reference block at the bottom, the row of caveat bullets.

## 2. Individual panel PDFs (so IEc can re-typeset / re-tile)

All under `outputs/poster/`:

| Panel | File |
|---|---|
| Pipeline schematic (top-left) | `pipeline_linear.pdf`, `pipeline_stages.pdf` |
| B. Probabilistic SLR band | `slr_band.pdf` |
| C. Total SLR Hawkins-Sutton | `../plots/hawkins_sutton_slr_4way.pdf` |
| D. Pulse SLR Hawkins-Sutton + small-pulse inset | `../plots/hawkins_sutton_slr_4way_pulse.pdf` |
| F. Sweet damage-function methodology | `sweet_scenarios.pdf` |
| G. Lorie adaptation panel | `lorie_panel.pdf` |
| H. Per-sector damages table | (TBD — fredi state damages) |
| I. Sheahan HTF mortality table | `sheahan_table.pdf` |
| J. HTF transportation table | `htf_transport_table.pdf` |

## 3. A plain-text file with all non-graphic text

Send a single `.txt` (or `.docx`) with these copy blocks, clearly labeled:

```
[TITLE]
[AUTHORS — Marcus Sarofim, James E. Neumann, Megan Sheahan]
[AFFILIATIONS]
[ACKNOWLEDGEMENTS — see acknowledgements block in poster_text_to_iec.txt
                    if a separate file ships with this handoff]

[PANEL A LABEL + CAPTION]
[PANEL B LABEL + CAPTION]
... etc for every panel A–L

[CAVEAT BULLETS — currently 4 caveats]
[REFERENCES BLOCK — currently 12 entries; alphabetical by first author]
[DISCUSSION PARAGRAPHS — currently 5 paragraphs]
[VERSION STAMP — small-print bottom corner]
```

The current values for all of these come straight out of
`python/scripts/poster/layout_mockup.py` — search for `caption=`,
`caveat_bullets`, `refs`, `discussion_paras`, etc.

## 4. After IEc returns the polished PDF

1. Save the deliverable as `outputs/poster/poster_final.pdf`.
2. Save the source files IEc used (typically Illustrator `.ai`,
   InDesign `.indd`, or Figma export) under `outputs/poster/iec_source/`
   if IEc shares them. Gitignore that subdirectory — they're large.
3. Update the version stamp embedded in the poster's bottom corner:
   `v1.0-poster-agu-chapman · 2026-06-01 · github.com/msarofim/SLR-RFF-BRICK`
4. Verify the QR code on the poster resolves to:
   `https://github.com/msarofim/SLR-RFF-BRICK/tree/v1.0-poster-agu-chapman`
5. Tag and push:
   ```bash
   git add outputs/poster/poster_final.pdf
   git commit -m "Add IEc-polished final poster for AGU Chapman SLR"
   git tag -a v1.0-poster-agu-chapman -m "Poster delivered to AGU Chapman SLR conference"
   git push origin main v1.0-poster-agu-chapman
   ```
6. (Optional) Deposit `poster_final.pdf` to ESS Open Archive for a
   poster-specific DOI; see `SETUP_ZENODO.md` § 7.
