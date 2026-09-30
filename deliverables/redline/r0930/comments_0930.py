"""09-30 replies to Marcus's comment responses + one new comment. Run AFTER all tracked edits."""
import sys
sys.path.insert(0, "/private/tmp/claude-501/-Users-MarcusMarcus-Documents-2026-CodeProjects-FaIRtoFrEDI/e88c7db1-5ed3-4ee0-bbf2-08bb6c77ecb6/scratchpad/v0930")
from comments_lib import reply, comment
JOINT = open(sys.argv[2], encoding="utf8").read().strip()

reply(0, "Checked against the driver actually used (data/observations/t_gis_zones.csv, column 'south'), on 11-yr "
         "and 5-yr centred means. Warming from about 1920 (5-yr minimum 1920; the 11-yr mean is flat over 1915–18) "
         "to a peak in 1930–31; a plateau to about 1960; cooling through the 1960s to a low lasting until about 1990 "
         "(11-yr minimum 1988, 5-yr 1991). By 1998 the 11-yr mean is back at plateau level, so 'through 1998' was too "
         "late, and the series has a plateau and then a cooling rather than one or the other. Rewritten as a tracked change.")
reply(2, JOINT)
reply(4, "Done. Re-derived on the current calib 1.6.0 forcing, the matched ratio is 5.7 (86.9 / 15.3 cm: the PROTECT "
         "NORCE-CISM runs interpolated to our own 2015–2300 GSAT integral), not the 6.4 I quoted on 09-29, which rests "
         "on calib 1.4.5 forcing (the canonical outputs/gis_matched_targets_2300.csv, which other gates read, is left as is; the 5.7 is "
         "outputs/gis_matched_targets_2300_calib160.csv, the same two scripts re-run on today's forcing). The 2.4 is unchanged (2.36 fixed arm, 2.35 joint). Caveat: every anchor past "
         "2100 is one ice-sheet model, so 5.7 carries climate spread only, not structural spread.")
reply(5, "No. The 23 cm was the regression slope times σ, not a mean, and the 21% belonged to that regression figure "
         "(57.5 cm) too. All per-draw means now: SSP2-4.5 45.8 cm (17% of the 270.4 cm median total), SSP5-8.5 19.9 cm "
         "(4% of 509.9 cm). Source: outputs/diag_ais_amp_leverage_draws_L27.csv (2,000 draws, +0.18). Two things you may "
         "want to say or change: the median per-draw change at SSP2-4.5 is only 17.9 cm, so the 46 cm mean is carried by "
         "the minority of draws that cross the threshold; and this paragraph is on the fixed-driver arm, while the "
         "Greenland paragraphs are now joint.")
reply(7, "Rewritten in plain terms. What L27 does (--no-ledger): the published 1850–1900 melt, N(2.0, 0.9) cm (an "
         "envelope over four estimates of 1.0–2.8 cm; Leclercq alone is 1.85), less the prior-mean contributions of "
         "uncharted ice (1.25 cm) and the Greenland periphery (0.25 cm), with their spreads added in quadrature. The "
         "model's own 1850–1900 glacier melt is scored against N(0.5, 1.17) cm (calibrate_mcmc_ext.jl:1458–59, "
         "1761–64, 866–68).")
reply(9, "Nearly. The published value is multiplied by 0.888 before use, but 'published values are area-corrected' reads "
         "as if Rignot did the correcting. The factor is DAIS's idealised disc area (10.92 × 10⁶ km²) over the grounded "
         "area (12.295 × 10⁶ km² in the code), giving 1863 ± 118 Gt/yr (calibrate_mcmc_ext.jl:1400–09). I checked "
         "2098 ± 133 Gt/yr (grounded ice, 1979–2008) against Rignot et al.'s Table 1: correct. One loose end: the paper "
         "tabulates 12,353 thousand km², and I cannot find the source of the code's 12.295. With 12.353 the target "
         "would be 1854.6 ± 117.6 Gt/yr, a 0.07σ change.")
reply(11, "Yes. Ladrillo (0.363) and BRICK 2.0 (0.389) were fitted over 2006–2025 (20 years), the observational target "
          "over 2006–2024 (19; it ends in 2024), and IGCC over 2006–2025. All four are least-squares slopes, whereas "
          "SLEIP's Table 6 is an average annual rate. On a common 2006–2024 window they are 0.363 / 0.388 / 0.392 / "
          "0.403. Deleted as you suggested.")
reply(13, "Done. All six figures were re-rendered from the current code and compared byte-for-byte with the committed "
          "renders; FIG 2, 3 and 6 were already current. Swapped as tracked changes: FIG 1 (the observation band is "
          "now hatched, so it is no longer the same grey as BRICK 2.0's band; the caption gains one sentence), and FIG 4 "
          "and FIG 5 (the 09-22 direct labels). FIG 4's caption now says what the shading is.")
reply(15, "Still open on 09-30: the Zenodo DOI and the slr-comparison-arm remote. Acknowledgments are also still a placeholder.")
reply(17, "Done as tracked changes. Added Parkes and Marzeion (2018), Gelman and Rubin (1992), Shaffer (2014) for DAIS "
          "and Morice et al. (2021) for HadCRUT5, each checked against Crossref (Gelman–Rubin's pages come from citing "
          "records, not the publisher). The four listed-but-uncited references (Eyring, Leach, Goelzer, Greve and "
          "Chambers) are now cited where they belong; IMBIE Team, GlaMBIE Team, Mengel and Nauels 2017 get formal "
          "citations; 'et al.' and Copernicus punctuation are fixed; National Academies, Smith 2026 and van Vuuren moved "
          "to GMD order; the placeholder note is deleted. Not done, your call: (1) the DAIS paleo file in Table 3 is "
          "almost certainly from Wong, Bakker and Keller (2017), Clim. Change 144, 347–364 (the BRICK fastdy branch "
          "writes that filename; 4 × 200,000 = 800,000 members), but citing it forces 2017a/2017b on every Wong et al. "
          "2017; (2) Copernicus wants the six Table 3 dataset DOIs as '[data set]' reference entries; (3) the FACTS "
          "modules, GlacierMIP2, PISM, Mimi and the other SLEIP emulators are still named without references; (4) 'the "
          "2015 update of Church and White' has no entry; (5) HadCRUT5 is not in Table 3.")
comment("Information criteria for the Ladrillo and BRICK 2.0 hindcasts",
        "Re-run 09-30 with 10,000 draws of each posterior; it was 2,000 Ladrillo against 10,000 BRICK 2.0, which "
        "favoured BRICK 2.0. The old configuration was first reproduced byte-for-byte as a control. Every AR(1) row "
        "moves toward Ladrillo (ΔBIC 21 → 26 at ρ ≤ 0.99, 78 → 82, 145 → 147); the independent-errors row is unchanged "
        "(its best Ladrillo draw was already in the 2,000). The paragraph below is updated to match; the per-series "
        "order flips (glaciers +26, Greenland +30).")
