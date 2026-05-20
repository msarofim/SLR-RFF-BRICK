# IEc graphics handoff package — SLR-RFF-FaIR-BRICK poster

**Conference:** AGU Chapman SLR conference
**Poster dimensions:** 46″ × 46″
**Date:** 2026-05-20 (current snapshot)
**Authors:** Marcus C. Sarofim, James E. Neumann, Megan B. Sheahan

This folder is everything you need to assemble the final printable poster
from the underlying scientific deliverables.

## Contents

```
iec_graphics_handoff/
├── README.md                          ← you are here
├── 00_full_layout_mockup.pdf          ← the current Marcus-side wireframe
│                                        showing positions, sizes, panel
│                                        labels, and intended text content
│                                        of every block
├── poster_text.txt                    ← every text block, verbatim, keyed
│                                        to its panel label
└── panels/
    ├── A_pipeline.pdf
    ├── B_probabilistic_slr.pdf
    ├── C_total_slr_hawkins_sutton.pdf
    ├── D_pulse_slr.pdf
    ├── F_damage_function_methodology.pdf
    ├── G_adaptation_lorie.pdf
    ├── H_coastal_property_and_htf_damages.pdf
    ├── I_state_damages_map.pdf
    └── J_htf_elder_mortality.pdf
```

## How to use it

1. Open `00_full_layout_mockup.pdf` — this is the canonical layout
   reference. It shows where every panel goes on the 46″ × 46″ canvas, at
   half-scale render. Panel positions, sizes, and labels are
   authoritative for the poster; everything *inside* a panel comes from
   the corresponding PDF in `panels/`.

2. Each file in `panels/` is the print-ready vector PDF for that panel.
   File names are keyed to the panel labels used in the layout
   (`A_pipeline.pdf` for Panel A, etc.). Note: there is no Panel E or K
   on this poster (E is the central discussion text block; K is reserved
   for caveats, which appears in the text file only).

3. All non-graphic text — titles, authors, captions for each panel,
   discussion paragraphs, caveats, references, version stamp — is in
   `poster_text.txt`. Every block is keyed to its panel label so it can
   be dropped into the corresponding position without ambiguity. Text
   is exact and should be used verbatim (only typographic adjustments
   like hyphenation, kerning, and line-breaks are at the designer's
   discretion).

## Notes on figure quality

All panel PDFs are vector-format (matplotlib's default), so they should
scale cleanly to any print size. Internal text inside each panel
(legend labels, axis labels, tick labels) is part of the figure and is
already laid out in the source script — please don't re-typeset that
text. The poster-level captions, panel labels, and surrounding prose
in `poster_text.txt` are what you'll typeset.

## On color and typography

Panels were rendered with a project-standard palette:

- Deep blue `#1F4E79` for emphasis (panel borders, primary trend lines)
- Warm red `#A6361C` for comparison / observed series
- Greys for neutral references

You're welcome to harmonize with IEc's house style — the panel content
will read clearly regardless. The science-side palette inside each
panel (orange / purple / green / pink for Hawkins-Sutton stacked
variance components in Panels C and D) is meaningful and should be
preserved.

## On poster fonts

Source figures use matplotlib's default sans-serif. Replace with the
IEc house font (or a print-ready Helvetica / Inter / Source Sans Pro)
as preferred. The fonts inside each panel PDF *will* render
substitution-friendly because they're embedded as outlines, not as
named fonts.

## Suggested poster fine-print

A small line near the bottom corner of the final poster is recommended
to make the work re-traceable:

> v1.0-poster-agu-chapman · 2026-06-01 · github.com/msarofim/SLR-RFF-BRICK

The QR code (typically next to the fine print) should resolve to:

  https://github.com/msarofim/SLR-RFF-BRICK/tree/v1.0-poster-agu-chapman

(That tagged release is created when the print-ready poster lands; a
bare `github.com/msarofim/SLR-RFF-BRICK` URL also works as a fallback
QR target if needed before the tag exists.)

## Questions

For science questions / panel content tweaks: Marcus Sarofim
(<msarofim@gmail.com>). For dataset / archive questions, the underlying
intermediate ensembles are at [doi.org/10.5281/zenodo.20312325](https://doi.org/10.5281/zenodo.20312325) and the code is at
[github.com/msarofim/SLR-RFF-BRICK](https://github.com/msarofim/SLR-RFF-BRICK).
