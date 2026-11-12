"""Round r1113: Claude's tracked edits on Marcus's 08:26 save of r1112 (2026-11-12). Run by build.sh on a fresh copy.

Marcus 11-12: "Fix Table A3." (Also two placeholder reference entries completed, found in the pre-share check; see
below.) His 08:26 save puts the as-run calibration values in Sect. 2.2.3 ("holds them fixed
during calibration (λ = 0.0137 m yr⁻¹, T_crit = −15.1 °C, γ = 2.04). For projections, γ is set to its DAIS
paleo-ensemble median (2.83) ..."). Table A3 still gave the paleo medians as the calibration values.
Source of the as-run values: SLR-RFF-BRICK `outputs/recalib_central_row.csv` (row 5808 of the BRICK posterior subsample
`data/MimiBRICK/parameters_subsample_brick.csv`), loaded over the paleo medians by `calibrate_mcmc_ext.jl:1627`;
memory `l27_held_gamma_is_central_row`. Values there: λ 0.0136513, T_crit −15.1396, γ 2.03819.
"""
import os, re, sys
from xml.sax.saxutils import escape

HERE = os.path.dirname(os.path.abspath(__file__))
W = sys.argv[1]
sys.path.insert(0, HERE)
import edlib  # noqa: E402

d = edlib.open_doc(W + "/word/document.xml")

## Table A3, λ/T_crit row: (context, old, new). verify_r1113.py reads EDITS, GAMMA, NEW_VALUES and ABSENT.
## The T_crit edit goes first: it splits the run, and the λ edit then finds its context in the run's first part.
EDITS = [("Calibration: 0.00991 m yr⁻¹, −15.67 °C; projection: joint draws", "−15.67", "−15.14"),
         ("Calibration: 0.00991 m yr⁻¹, ", "0.00991", "0.01365")]
## Table A3, γ row: the value cell after "DAIS ice-flow exponent" reads "2.83"; the calibration value goes in front.
GAMMA = dict(label="DAIS ice-flow exponent", cell="2.83", prefix="Calibration: 2.04; projection: ")
## References: Marcus's two 11-05 placeholder entries completed (Crossref 10.5194/tc-19-6887-2025; DataCite
## 10.11582/2025.lf9m2wd0 and 10.7265/4m1f-gd79, looked up 11-12). The Goelzer placeholder named both the paper and the
## PROTECT-Greenland data set it describes; the 5.7 ratio in Sect. 2.2.2 is computed from that data set
## (python/build_gis_matched_targets.py), so the data set gets its own entry and an in-text citation.
GOELZER_OLD = "Goelzer et al. (2025), The Cryosphere 19, 6887 (data doi:10.11582/2025"
GOELZER_NEW = ("Goelzer, H., Berends, C. J., Boberg, F., Durand, G., Edwards, T. L., Fettweis, X., Gillet-Chaulet, F., "
               "Glaude, Q., Huybrechts, P., Le clec'h, S., Mottram, R., Noël, B., Olesen, M., Rahlves, C., Rohmer, J., "
               "van den Broeke, M., and van de Wal, R. S. W.: Extending the range and reach of physically-based Greenland "
               "ice sheet sea-level projections, The Cryosphere, 19, 6887–6906, https://doi.org/10.5194/tc-19-6887-2025, "
               "2025.")
PROTECT_DATA = ("Goelzer, H.: Greenland ice sheet projections for EU-project PROTECT, Version 1, NIRD Research Data "
                "Archive [data set], https://doi.org/10.11582/2025.lf9m2wd0, 2025.")
PROTECT_BEFORE = "Goelzer, H., Nowicki, S., Payne"            # Copernicus order: the single-author entry comes first
RGI_ENTRY = ("RGI Consortium: Randolph Glacier Inventory – A Dataset of Global Glacier Outlines, Version 6, NSIDC "
             "[data set], https://doi.org/10.7265/4m1f-gd79, 2017.")
NEW_VALUES = ["Calibration: 0.01365 m yr⁻¹, −15.14 °C; projection: joint draws", "Calibration: 2.04; projection: 2.83",
              GOELZER_NEW, PROTECT_DATA, RGI_ENTRY, "(RGI, RGI Consortium, 2017)",
              "matched forcing (Goelzer et al., 2025; Goelzer, 2025)."]
ABSENT = ["0.00991", "−15.67", "(data doi:", "RGI Consortium 2017"]


def gamma_cell():
    i = d.x.index(escape(GAMMA["label"]))
    assert d.x.count(escape(GAMMA["label"])) == 1
    j = d.x.index("</w:tc>", i)                                   # end of the description cell
    k = d.x.index("</w:tc>", j + 7)                               # end of the value cell
    cell = d.x[j:k]
    m = re.search(r'<w:r>(<w:rPr>(?:(?!</w:rPr>).)*</w:rPr>)?<w:t(?: xml:space="preserve")?>' + re.escape(GAMMA["cell"])
                  + r'</w:t></w:r>', cell, re.S)
    assert m and len(re.findall(r"<w:t[ >]", cell)) == 1, "the γ value cell is not one plain run reading 2.83"
    rpr = m.group(1) or ""
    s = j + m.start()
    d.x = d.x[:s] + d._ins(rpr, escape(GAMMA["prefix"])) + d.x[s:]
    d.log.append((GAMMA["label"] + " [value cell]", f"+ {GAMMA['prefix']!r}", "Table A3: γ as run in calibration"))


def goelzer_data_cite():
    """'; Goelzer, 2025' before the ')' of Marcus's split insertion ' (Goelzer et al.' + ', ' + '2025)'."""
    a = d.x.index(" (Goelzer et al.</w:t>")
    assert d.x.count(" (Goelzer et al.</w:t>") == 1
    m = re.compile(r'<w:ins (w:id="\d+") (w:author="Marcus Sarofim" [^>]*)><w:r><w:t>2025\)</w:t></w:r></w:ins>').search(d.x, a)
    assert m and m.start() - a < 800, "the closing '2025)' insertion was not found"
    attrs = m.group(2)
    out = (f'<w:ins {m.group(1)} {attrs}><w:r><w:t>2025</w:t></w:r></w:ins>' + d._ins(None, "; Goelzer, 2025")
           + f'<w:ins w:id="{d._id()}" {attrs}><w:r><w:t>)</w:t></w:r></w:ins>')
    d.x = d.x[:m.start()] + out + d.x[m.end():]
    d.log.append(("matched forcing (Goelzer et al., 2025)", "+ '; Goelzer, 2025'", "data citation for PROTECT-Greenland"))


if __name__ == "__main__":
    for ctx, old, new in EDITS:
        edlib.edit(ctx, old, new, "Table A3: λ, T_crit as run in calibration")
    gamma_cell()
    ## references; the in-text RGI comma first, so the entry's context is then unique
    edlib.ins(", RGI Consortium 2017", ", RGI Consortium", ",", "Copernicus in-text form")
    edlib.edit("RGI Consortium 2017", "RGI Consortium 2017", RGI_ENTRY, "placeholder entry completed (DataCite)")
    edlib.edit(GOELZER_OLD, GOELZER_OLD, GOELZER_NEW, "placeholder entry completed (Crossref)")
    d.insert_para(PROTECT_BEFORE, PROTECT_DATA, before=True, why="data set behind the 5.7 ratio (DataCite)")
    goelzer_data_cite()
    d.save()
    open(os.path.join(W, "..", os.path.basename(W) + "_log.txt"), "w", encoding="utf8").write(
        "\n".join(f"{a} | {b} | {c}" for a, b, c in d.log) + "\n")
    print(f"edits_r1113: {len(EDITS) + 1} tracked edits in Table A3, 5 in references and citations")
