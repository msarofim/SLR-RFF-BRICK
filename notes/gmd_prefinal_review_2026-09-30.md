# GMD draft: pre-share review (before sending to Tony Wong), 2026-09-30

Reviewed file: Marcus's 16:40 save of `deliverables/GMD.Ladrillo.v1_review-2026-09-30b_L27.docx`
(all changes accepted, one comment left). Read-only. There were two passes: a numbers pass, which
re-traced the claims against L27 / calib 1.6.0 / LWS-observed outputs, and a clarity/GMD pass (full list
in `gmd_prefinal_clarity_2026-09-30.md`, line numbers refer to a pandoc plain-text dump). Checked
mechanically:
- all six figures embedded = the current `figures/paper` renders;
- no leftover media;
- metadata shows only Marcus.

**No wrong numbers found.** The numbers pass checked all 25 cells of Table 4, Table 5, the High/Low/regrowth
paragraphs, the Introduction's sensitivity ratios, runtime, Table 2, and the Greenland and Antarctic
paragraphs.

## Must fix before sharing
1. **1.10 × 1.10 = 1.21 ≠ "1.24–1.29×"** (TE paragraphs). This was introduced on 09-30 when the 1.22 was
   corrected to the 1993–2026 window; the decomposition is for 1993–2024 (1.215). State the window.
2. **Antarctic widths "314 and 405 cm at SSP5-8.5"** sit in the vvH paragraph. At vvH they are 274 and
   332 cm.
3. **"MAGICC-SLR is the narrow outlier throughout"** is false for glaciers and Greenland at vvVL. It holds
   for Antarctica, TE and the total.
4. **Hindcast inputs not disclosed:**
   - the observed total after 2021 is NOAA STAR altimetry (Dangendorf ends in 2021);
   - GRACE also extends the AIS/GIS targets 2019–2026;
   - the NOAA 0–2000 m thermosteric series (2005–2025) is not in Table 3.
5. **"regrowth … in the short-timescale regional block"** (Conclusions) and "SLOWG dominates … the
   projections" have no per-block output behind them.
6. **FACTS FittedISMIP 47 / 112 cm**: still no output file.
7. **GMD sections**: Author contributions (mandatory) is missing; Financial support; corresponding-author
   email; the Code-availability placeholders (DOI, repository URL); the MimiBRICK citation is a GitHub URL
   and needs an archive DOI.
8. **Typo**: "the Greenland peripher not included".
9. **Undefined internal terms**: vvVL/vvLN/vvML; "joint arm"/"fixed arm"; "L27"; "SLOWG = SLOWP … in the
   code"; "ledger"; "deliverable-level criterion"; parameter code names in running text.
10. **SSP1-2.6/2-4.5/5-8.5 results** appear, but only van Vuuren runs are described.
11. **FIG 2/3/4/6 are never cited in the body; FIG 5 is cited before FIG 1.**
12. **fair-calibrate 1.6.0** is cited to Smith et al. 2024 (the v1.4.1 paper); add Smith 2026.

## Should
- **BRICK naming** (BRICK / BRICK 2.0 / MimiBRICK v2.0.0 / BRICK v0.2) and the "rather than coupled to
  SNEASY" framing against Table 1's "runs on FaIR: yes". Tony will read this first.
- **Projection baseline** (1995–2014) should be stated once; hindcasts use 1995–2005.
- **IGCC +8.21** is closer to BRICK's 8.34 than to Ladrillo's 7.88; "BRICK runs slightly high" holds only
  against the target.
- **"thermal expansion ties by construction"** vs Table 4's TE ratios.
- **Table A2** loadings are on ln P₀, not the sampled u.
- Undefined acronyms; heading format; Appendix placement; mixed "FIG"/"Figure".
