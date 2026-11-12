"""Round r1115 data, shared by edits_r1115.py (tracked, on r1114), clean_r1115.py (plain, on Marcus's 09:21 clean
copy) and verify_r1115.py.

Marcus 11-12: "Fill in the Code and data availability sentence facts, and update the clean version too."
Facts: Ladrillo.jl `tools/targets/` rebuilds every calibration target and driver from `data/sources/`; only the two
Frederikse et al. (2020) files are fetched, from Zenodo 10621070 (cited in the paper as Dangendorf, 2024); the NOAA
STAR, NOAA NCEI, Berkeley Earth and GISTEMP series ship as used because the publishers overwrite them; the Berkeley
Earth file is CC BY-NC 4.0 (Ladrillo.jl 1168c9b, data/sources/README.md, README sources table).
"""
## Code and data availability: a new passage after "... regional-temperature drivers are included in the archive."
AVAIL_ANCHOR = "temperature drivers are included in the archive."
AVAIL_NEW = (" The archive also includes the source files needed to rebuild the calibration targets, except the two "
             "Frederikse et al. (2020) files, which are retrieved from the Zenodo record of Dangendorf (2024). The NOAA "
             "STAR, NOAA NCEI, Berkeley Earth and GISTEMP series are archived as used, because their publishers update "
             "these files in place. The licence of each source is listed in the archive; the Berkeley Earth series is "
             "distributed under CC BY-NC 4.0.")
## Sect. 2.2.1 typo: "( committed-loss" (a space Marcus's 11-09 deletion of "the" left behind)
TYPO_CTX, TYPO_OLD, TYPO_NEW = " committed-loss fractions at 1.2", " committed", "committed"
## Two of Claude's comments that the text has overtaken: marked resolved (the Code availability status note, which said
## the target builders were not yet in Ladrillo.jl; the NOAA note, whose open point Marcus settled with "provided by").
STALE_COMMENTS = ["state of Ladrillo.jl", "access date 20 May"]
## Clean copy only: the space lost when Marcus joined the regrowth paragraph, and the trailing spaces after his new
## Introduction sentence. In the tracked file the regrowth paragraph is still split inside his moved equation block,
## where a scripted join could corrupt the moves, so it is left there.
CLEAN_ONLY = [("Ladrillo’s glaciers can regrow up to each block’s", "1850 ice extent. In the two larger blocks"),
              ("better classified as an intermediate complexity model.   ", "better classified as an intermediate complexity model.")]
