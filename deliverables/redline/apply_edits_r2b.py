"""Round 2b: complete the references (author lists, Nauels 2025, fair-calibrate 1.6.0 Zenodo, IMBIE, CMIP6)."""
from redline import *
import html as _h

def edit_ins_text(x, old, new):
    """Edit text inside one of Claude's own PENDING <w:ins> runs in place (stays a tracked insertion)."""
    o, n = esc(old), esc(new)
    hits = [m for m in re.finditer(r"<w:ins [^>/]*>(?:(?!</w:ins>).)*</w:ins>", x, re.S) if o in m.group(0)]
    assert len(hits) == 1, (old[:40], len(hits))
    m = hits[0]
    ins = m.group(0)
    head = re.match(r"<w:ins [^>/]*>", ins).group(0)
    run = re.search(r"<w:r>.*?</w:r>|<w:r [^>]*>.*?</w:r>", ins, re.S).group(0)
    rpr, text = run_parts(run)
    i = text.index(o); before, after = text[:i], text[i+len(o):]
    out = ""
    if before: out += head + mk_run(before, rpr) + "</w:ins>"
    out += head + mk_del(o, rpr) + "</w:ins>"          # deletion nested inside the insertion
    out += mk_ins(n, rpr)
    if after: out += head + mk_run(after, rpr) + "</w:ins>"
    return x[:m.start()] + out + x[m.end():]

x = load()
# full author lists (verified from publisher pages 2026-09-18)
x = edit_ins_text(x, "Forster, P. M., Walsh, T., Smith, C., Lamb, W. F., Lamboll, R., Cassou, C., Hauser, M., Hausfather, Z., Lee, J.-Y., Palmer, M. D., von Schuckmann, K., Slangen, A. B. A., et al.: Indicators",
    "Forster, P. M., Walsh, T., Smith, C., Lamb, W. F., Lamboll, R., Cassou, C., Hauser, M., Hausfather, Z., Lee, J.-Y., Palmer, M. D., von Schuckmann, K., Slangen, A. B. A., Szopa, S., Trewin, B., Yun, J., Gillett, N. P., Jenkins, S., Matthews, H. D., Raghavan, K., Ribes, A., Rogelj, J., Rosen, D., Zhang, X., Allen, M., Andrew, R. M., Atkinson, C., Betts, R. A., Bombelli, A., Burgess, S. N., Cheng, L., Claxton, H. E., Friedlingstein, P., Frölicher, T. L., Domingues, C. M., Gasser, T., Gregory, C. H., Hoesly, R. M., Huppmann, D., Ishii, M., Kadow, C., Karwat, A., Kennedy, J., Killick, R. E., Kovilakam, M. V. M., Krummel, P. B., Lan, X., Lamarque, J.-F., Liné, A., Martín-Míguez, B., Monselesan, D. P., Morice, C., Mühle, J., Mussak, P., Peters, G. P., Pirani, A., Pongratz, J., Rigby, M., Rohde, R., Savita, A., Seneviratne, S. I., Smith, S. J., Taha, G., Tassone, C., Thorne, P., Wells, C., Western, L. M., van der Werf, G. R., Wijffels, S. E., Zecchetto, M., Zhong, J., Zhang, X.-Y., Masson-Delmotte, V., and Zhai, P.: Indicators")
x = edit_ins_text(x, ", 2026. [67 authors — complete the list]", ", 2026.")
x = edit_ins_text(x, "Goelzer, H., Nowicki, S., Payne, A., Larour, E., Seroussi, H., Lipscomb, W. H., et al.: The future",
    "Goelzer, H., Nowicki, S., Payne, A., Larour, E., Seroussi, H., Lipscomb, W. H., Gregory, J., Abe-Ouchi, A., Shepherd, A., Simon, E., Agosta, C., Alexander, P., Aschwanden, A., Barthel, A., Calov, R., Chambers, C., Choi, Y., Cuzzone, J., Dumas, C., Edwards, T., Felikson, D., Fettweis, X., Golledge, N. R., Greve, R., Humbert, A., Huybrechts, P., Le clec'h, S., Lee, V., Leguy, G., Little, C., Lowry, D. P., Morlighem, M., Nias, I., Quiquet, A., Rückamp, M., Schlegel, N.-J., Slater, D. A., Smith, R. S., Straneo, F., Tarasov, L., van de Wal, R., and van den Broeke, M.: The future")
x = edit_ins_text(x, ", 2020. [complete the author list]", ", 2020.")
x = replace_text(x, "Zekollari, H., et al.: Glacier preservation doubled by limiting warming to 1.5 °C versus 2.7 °C, Science, https://doi.org/10.1126/science.adu4675, 2025. [confirm title/authors]",
    "Zekollari, H., Schuster, L., Maussion, F., Hock, R., Marzeion, B., Rounce, D. R., Compagno, L., Fujita, K., Huss, M., James, M., Kraaijenbrink, P. D. A., Lipscomb, W. H., Minallah, S., Oberrauch, M., Van Tricht, L., Champollion, N., Edwards, T., Farinotti, D., Immerzeel, W., Leguy, G., and Sakai, A.: Glacier preservation doubled by limiting warming to 1.5 °C versus 2.7 °C, Science, 388, 979–983, https://doi.org/10.1126/science.adu4675, 2025.")
x = edit_ins_text(x, "van Vuuren, D. P., O'Neill, B. C., Tebaldi, C., Sanderson, B. M., Chini, L. P., Friedlingstein, P., Hasegawa, T., Riahi, K., et al.: The Scenario",
    "van Vuuren, D. P., O'Neill, B. C., Tebaldi, C., Sanderson, B. M., Chini, L. P., Friedlingstein, P., Hasegawa, T., Riahi, K., Govindasamy, B., Bauer, N., Eyring, V., Fall, C. M. N., Frieler, K., Gidden, M. J., Gohar, L. K., Högner, A., Jones, A. D., Kikstra, J., King, A., Knutti, R., Kriegler, E., Lawrence, P., Lennard, C., Lowe, J., Mathison, C., Mehmood, S., Nicholls, Z., Prado, L. F., Zhang, Q., Rose, S. K., Ruane, A. C., Sandstad, M., Schleussner, C.-F., Seferian, R., Sillmann, J., Smith, C., Sörensson, A. A., Panickal, S., Tachiiri, K., Vaughan, N., Vishwanathan, S. S., Yokohata, T., Zecchetto, M., and Ziehn, T.: The Scenario")
x = edit_ins_text(x, ", 2026. [45 authors — complete the list]", ", 2026.")

# new entries
x = insert_after(x, "Nauels, A., Meinshausen, M.", [
    "Nauels, A., Nicholls, Z., Möller, T., Hermans, T. H. J., Mengel, M., Kloenne, U., Smith, C., Slangen, A. B. A., and Palmer, M. D.: Multi-century global and regional sea-level rise commitments from cumulative greenhouse gas emissions in the coming decades, Nat. Clim. Change, 15, 1198–1204, https://doi.org/10.1038/s41558-025-02452-5, 2025."])
x = insert_after(x, "Smith, C., Cummins", [
    "Smith, C.: fair calibration data, v1.6.0 (fastmip v1 calibration of fair v2.2.4), Zenodo [data set], https://doi.org/10.5281/zenodo.18828694, 2026."])
x = insert_after(x, "Hock, R., Maussion", [
    "IMBIE Team: Mass balance of the Antarctic Ice Sheet from 1992 to 2017, Nature, 558, 219–222, https://doi.org/10.1038/s41586-018-0179-y, 2018."])
x = insert_after(x, "Dangendorf, S., Sun", [
    "Eyring, V., Bony, S., Meehl, G. A., Senior, C. A., Stevens, B., Stouffer, R. J., and Taylor, K. E.: Overview of the Coupled Model Intercomparison Project Phase 6 (CMIP6) experimental design and organization, Geosci. Model Dev., 9, 1937–1958, https://doi.org/10.5194/gmd-9-1937-2016, 2016."])
# the to-do line: nothing left
x = edit_ins_text(x, "[Still to add: the MAGICC-SLR 'Nauels 2025' source cited in the FIG 1 caption; a SICOPOLIS Antarctic/3001 source if one is cited beyond Greve and Chambers (2022); ISMIP6 Antarctica if cited; the CMIP6 catalogue (Pangeo/Google Cloud); the fair-calibrate 1.6.0 release (Zenodo DOI); IMBIE if named as a source. Zekollari (2025), Goelzer (2020), Forster (2026) and van Vuuren (2026) still need their full author lists.]",
    "[Reference list complete for everything the text cites as of 2026-09-18; the CMIP6 catalogue itself (Pangeo / Google Cloud) is cited as Eyring et al. 2016 plus the fetch dates in the Table 3 footnote.]")
# in-text
x = replace_text(x, "v7.5.3 + Nauels 2025", "v7.5.3, sea-level parameters of Nauels et al., 2025")
x = replace_text(x, "[Smith et al., DOI]", "(Smith, 2026; Smith et al., 2024)")
x = add_reply(x, 15, "Round 2b: the three open items closed by lookup — the FIG 1 'Nauels 2025' is Nauels et al., Nat. Clim. Change 15, 1198–1204, 2025 (the MAGICC v7.5.3 sea-level drawnset on Zenodo cites it as its source); fair-calibrate 1.6.0 = Smith, Zenodo 10.5281/zenodo.18828694; full author lists for Forster (73), Goelzer (42), Zekollari (21) and van Vuuren (45) from the publisher pages. Also added IMBIE Team 2018 (named in the text) and Eyring 2016 for CMIP6.")
save(x); print("r3 applied")
