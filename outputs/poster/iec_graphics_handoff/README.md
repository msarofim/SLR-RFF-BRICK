# IEc graphics handoff package — SLR-RFF-FaIR-BRICK poster

**Conference:** AGU Chapman SLR conference
**Poster dimensions:** 46″ × 46″
**Date:** 2026-05-25 (current snapshot)
**Authors:** Marcus C. Sarofim, James E. Neumann, Megan B. Sheahan

This folder is everything you need to assemble the final printable poster
from the underlying scientific deliverables.

## What changed in this snapshot (vs. 2026-05-20)

Panels B, C, D, and the full-layout mockup have been refreshed to the
v1.4.5 FaIR-calibration + post-PR#93 BRICK posterior ensemble. The
ensemble design changed too — Panel B is now built on the 10,000-draw
LHS baseline (was 500 paired draws), and the Panel C / D Hawkins-Sutton
factorial uses the ANOVA-18k design (400 RFFs × 15 climate calibrations
× 3 FaIR stochastic seeds × 3 BRICK posterior samples = N=54,000; was
100 RFFs × N=13,500). Captions in `poster_text.txt` have been updated
to match the new sample sizes.

A `METHODS NOTE` block has been added to `poster_text.txt` summarizing
the climate model, calibration release, SLR model, emissions inventory,
and importance-weighting target — placement recommended next to the
references list or above the version stamp.

Panels F and H have also been refreshed to v1.4.5. The FrEDI rerun
used 1,000 SIR-resampled draws from the v1.4.5 LHS-10k baseline
ensemble (vs. 500 paired draws in v1.4.1). Per-draw FrEDI runtime
was ~44.8 minutes wall-clock with 8 parallel R workers; the importance
weights were absorbed into the SIR resample so downstream weighting
is uniform.

Panel B has been refined: the x-axis now starts at 2020 (consistent
with the other panels), the NOAA STAR observed-anchor plot annotation
was dropped (the bias-correction math still uses NOAA STAR
underneath), and AR6 Table 9.9 diamond markers for SSP2-4.5 and
SSP3-7.0 median GMSL at 2100 have been added — rebaselined from
AR6's 1995-2014 reference to our NOAA-STAR-rel-2000 reference via
the +1.34 cm satellite-derived offset. RFF-SP median emissions sit
between SSP2-4.5 and SSP3-7.0, so the band brackets the projection.
AR6 doesn't publish SSP4-6.0 through the FACTS pipeline; bracketing
with SSP2-4.5 / SSP3-7.0 is the cleanest authoritative comparison.

Panel D had a unit bug repaired (pulse inset was dividing per-GtCO₂
v1.4.5 values by GtC→GtCO₂ = 44/12, leaving the inset 3.67× too
small) and the inset was shifted right (left edge 0.06 → 0.12) so
its y-axis label no longer overlaps the main axes. Caption was
also corrected: the previous "AIS-tipping-regime split" description
was stale, the current inset shows median + 5–95% band of per-unit
pulse-marginal SLR from the 0.01-GtC small-pulse arm.

Panel H dropped its "N" (effective-draws) column — with v1.4.5
all 1,000 draws clear FrEDI's lowest-calibrated-scenario floor at
every reported year, so that column was redundant. The Sweet "Low"
floor caveat was also dropped from the caveats list (no longer
applies under v1.4.5).

Panels A, G, I, J are unchanged from 2026-05-20.

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
