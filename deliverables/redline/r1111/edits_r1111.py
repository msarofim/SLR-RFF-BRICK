"""Round 11-11: Claude's next pass on Marcus's 15:07 save of the TW2 review file.

Scope: the "Claude's next pass" table of notes/ladrillo_guidance_2026-11-11.md (figures, equations, Table A1, notation,
dashes/signs/units, citation forms, references, runtime, version), plus handoff 11-11b §4 (the IGCC 2025 numbers of
Decision 2) and comments for the facts of handoffs 11-11c §4 and 11-11d §5 (code availability, seeds, gamma). The HAND
items of the guidance are Marcus's and are not touched. Every change is a tracked change by Claude dated this round;
everyone's pending tracked changes and all comments are left as they are.

    python edits_r1111.py <unpacked workdir>      (run by build.sh)

An entry whose `old` span cannot be placed in exactly one run or one paragraph is REPORTED and skipped, never guessed.
The placement helpers (para_text ... span_edit) are r1015's, read verbatim from _placement_from_r1015.py.
"""
import math, os, re, shutil, sys
from xml.sax.saxutils import escape, unescape
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import edlib
from trackedit import RUN_RE, _in_tracked, _para_bounds, AUTHOR, DATE

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
W = sys.argv[1]
d = edlib.open_doc(W + "/word/document.xml")
exec(open(os.path.join(HERE, "_placement_from_r1015.py"), encoding="utf8").read())

E = lambda id, section, old, new, anchor, source: dict(id=id, section=section, category="wording", old=old, new=new,
                                                        anchor=anchor, source=source)
ENTRIES = [
    # ---- version (Decision 1, Marcus 11-11: v1.0; Ladrillo.jl Project.toml 1.0.0, tag v1.0.0 at release) -------------
    E("V1", "5", "Ladrillo v1.3", "Ladrillo v1.0", "We present Ladrillo v1.3", "Decision 1"),
    E("V2", "Code availability", "v1.3 (Ladrillo.jl", "v1.0 (Ladrillo.jl", "is archived at Zenodo", "Decision 1"),
    E("V3", "Code availability", "git tag v1.3.0)", "git tag v1.0.0)", "is archived at Zenodo", "Decision 1"),
    # ---- IGCC 2025 indicators (Decision 2; SLR outputs/diag_*_igcc2025.csv, commit 41ec7f4) ---------------------------
    # ---- notation ------------------------------------------------------------------------------------------------
    E("T1", "2.2.2", "with onset T_on = 4.69 K", "with onset T_thr = 4.69 K", "with onset T_on",
      "guidance: Eq. (8) writes T_thr; T_on is the Antarctic runoff onset"),
    E("T5", "3.2", "(ais_iceflow₀)", "(ais_iceflow0)", "ice-flow constant", "Table A1 spelling"),
    E("T6", "3.2", "against Eq(4)", "against Eq. (4)", "against Eq(4)", "guidance"),
    E("T7", "2.2.2", "A_G·φ (Ḡ₃₀", "A_G·φ(Ḡ₃₀", "A_G·φ (", "guidance"),
    E("T8", "3.2", "a two coefficient discrepancy", "a two-coefficient discrepancy", "two coefficient", "guidance"),
    E("T9", "4.2", "LARMIP's 200 year response", "LARMIP's 200-year response", "LARMIP's 200 year", "guidance"),
    E("T10", "4.2", "FACTS’ Greenland module", "FACTS's Greenland module", "FACTS’ Greenland", "one spelling (3 x FACTS's)"),
    # ---- dashes, signs, units, spaces -------------------------------------------------------------------------------
    E("D1", "Abstract", "9-14 cm (27-56%)", "9–14 cm (27–56%)", "less glacier melt than BRICK 2.0", "en dashes"),
    E("D2", "2.2.1", "range of 60-3200 years", "range of 60–3200 years", "least constrained", "en dash"),
    E("D3", "3.2", "ESS below 400 (20-244)", "ESS below 400 (20–244)", "ESS below 400", "en dash"),
    E("D4", "4.3", "by 17-20 cm", "by 17–20 cm", "17-20 cm", "en dash"),
    E("D5", "4.1", "+20.41 (-0.6)", "+20.41 (−0.6)", "+20.41 (-0.6)", "minus sign"),
    E("D6", "3.2", "5-95% -0.05 to", "5–95% −0.05 to", "The quadratic coefficient spans zero",
      "en dash and minus sign in Marcus's 17:00 insertion"),
    E("U1", "Table 3", "133 Gt/yr over 1979–2008", "133 Gt yr⁻¹ over 1979–2008", "133 Gt/yr", "units"),
    E("U2", "Table 3 note", "1863 ± 118 Gt/yr", "1863 ± 118 Gt yr⁻¹", "1863 ± 118", "units"),
    E("U3", "Table 3 note", "SMB by −9 Gt/yr", "SMB by −9 Gt yr⁻¹", "SMB by −9", "units"),
    E("U4", "3.2", "about ±505 Gt/yr each", "about ±505 Gt yr⁻¹ each", "±505", "units"),
    E("U5", "2.2.1", "0.116 mm/yr)", "0.116 mm yr⁻¹)", "0.049 ± 0.116", "units"),
    E("S1", "2.2.2", "temperature.  The tilt", "temperature. The tilt", "The tilt, w", "double space"),
    E("S2", "2.2.4", "so  δ and α", "so δ and α", "cannot trade off", "double space"),
    E("S3", "4.3", "307 cm  at 2300", "307 cm at 2300", "307 cm", "double space"),
    E("S4", "5", "individual components.  ", "individual components.", "replace individual components", "trailing spaces"),
    E("S5", "Table 3 note 18", "outline ( World", "outline (World", "( World", "space"),
    # ---- citation forms ---------------------------------------------------------------------------------------------
    E("C1", "2.2.1", "(Frederikse et al. 2020) assumes", "(Frederikse et al., 2020) assumes", "assumes no Antarctic-periphery melt", "comma"),
    E("C2", "2.2.3", "1900 (Frederikse et al. 2020)", "1900 (Frederikse et al., 2020)", "starts in 1900", "comma"),
    E("C3", "2.2.3", "(Fox-Kemper et al. 2021)", "(Fox-Kemper et al., 2021)", "dearth of contemporary", "comma"),
    E("C4", "2.2.1", "Millan et al., 2022 estimate", "Millan et al. (2022) estimate", "Millan et al., 2022", "form"),
    E("C5", "1", "Mouginot et al. 2019 data", "Mouginot et al. (2019)", "Mouginot et al. 2019", "form"),
    E("C6", "1", "(CMIP6) (Eyring et al., 2016)", "(CMIP6; Eyring et al., 2016)", "(CMIP6) (Eyring", "form"),
    E("C7", "2.2.3", "(Wong et al., 2017b; Shaffer 2014)", "(Shaffer, 2014; Wong et al., 2017b)", "Shaffer 2014",
      "alphabetical, comma"),
    # ---- Table A1 text (p. 5) and Table A3 ---------------------------------------------------------------------------
    E("A0", "2.2.1", "log₁₀ κ are sampled", "ln κ are sampled", "are sampled for each block", "Table A1 shows ln"),
    E("A3T", "Table A3", "T_on, V", "T_thr, V", "T_on, V", "T1 notation"),
    # ---- references (verified 11-11 against Crossref / publisher / Zenodo; scratchpad refs report) -------------------
    E("R1", "References", "10.1022/2017GL074954", "10.1002/2017GL074954", "2017GL074954", "Crossref: 10.1002/2017GL074954"),
    E("R2", "References", "De La Guardia, F. H.", "Hoces de la Guardia, F.", "De La Guardia",
      "Zenodo creator Fernando Hoces de la Guardia; Crossref family 'Hoces de la Guardia'"),
    E("R3", "References", "and Catawbasam:", "and catawbasam:", "Catawbasam", "Zenodo creator list (a GitHub handle)"),
    # ---- Fig. 5: the joint-arm image replaces the fixed-arm one (FIGS below), so the caption's last words go ----------
    E("F5", "Fig. 5", " Fixed arm.", "", "Regrowth of about 0.08 cm", "joint-arm image swapped in; caption says Joint arm"),
]

## Minimal edits (only `old` becomes a tracked change, found inside a unique `context`): the likelihood symbols L_i and
## L_m become script L (guidance: L stays the e-folding length of Eq. 13).
## The IGCC 2025 numbers (Decision 2; SLR outputs/diag_*_igcc2025.csv, commit 41ec7f4) are minimal edits as well.
MINIMAL = [
    ("T2a", "ln L_i   = ln N", "L_i", "𝓛_i"), ("T2b", "Σ_i ln L_i + Σ_m", "L_i", "𝓛_i"),
    ("T2c", "Σ_m ln L_m + ln π", "L_m", "𝓛_m"), ("T2d", "The L_m are Gaussian", "L_m", "𝓛_m"),
    # 2.2.4: alpha matched to total Earth heat, 1993-2020: diag_te_alpha_matched_scope_L27_igcc2025.csv alpha_obs_param 0.13921
    ("N1", "0.141, below the posterior", "0.141", "0.139"),
    # 4.1: era shape 1900-1949 of observed 0-2000 m heat: diag_te_driver_timing_igcc2025.csv 0.2028
    ("N2", "0.21 for observed", "0.21", "0.20"),
    # 4.1: FaIR over 0-2000 m: Zanna+IGCC 1.192 (1993-2024), Zanna+Cheng 1.274 (diag_te_rate_attribution_L27_igcc2025.csv B)
    ("N3", "by a factor of 1.21–1.27", "1.21", "1.19"),
    # 4.1: 1993-2020 decomposition: diag_fair_ohc_vs_earth_heat_igcc2025.csv fair_over_0_2000 1.2185 = 1.1058 x 1.0954 x 1.0060
    ("N4", "the factor is 1.24, the product", "1.24", "1.22"),
    ("N5", "three terms: 1.11 because", "1.11", "1.106"),
    ("N6", "1.10 because FaIR counts", "1.10", "1.095"),
    ("N7", "and 1.02, the remaining", "1.02", "1.006"),
    ("N8", "(1.11 × 1.10 × 1.02 ≈ 1.24)", "1.11 × 1.10 × 1.02 ≈ 1.24", "1.106 × 1.095 × 1.006 ≈ 1.22"),
]

## Citations added where a source is used but not cited (context, text before the insertion point, inserted text).
CITES = [
    ("CI1", "(RCMIP; v5.1.0) SSP emissions", "(RCMIP; v5.1.0", "; Nicholls et al., 2020; Nicholls and Lewis, 2021"),
    ("CI2", "historical emissions 1750–2023 spliced", "historical emissions 1750–2023", " (Smith, 2026)"),
    ("CI3", "NOAA STAR altimetry over 2022–2024).", "NOAA STAR altimetry over 2022–2024",
     "; NOAA Laboratory for Satellite Altimetry, 2026"),
]
## New reference entries: (anchor of the entry they follow, text). Same anchor = inserted in reverse order.
NEW_REFS = [
    ("Levitus, S., Antonov", "Lin, Y., Zhang, X., Golledge, N. R., Kopp, R. E., Church, J. A., Jin, Y., Zhao, C., and Stokes, "
     "C. R.: Committed Antarctic Ice Sheet mass loss by the end of the twenty-first century, Nat. Geosci., 19, 1315–1324, "
     "https://doi.org/10.1038/s41561-026-02102-1, 2026."),
    ("Perrette, M. and Mengel", "Poinelli, M., Rignot, E., Seroussi, H., Cuzzone, J., Pelle, T., and Larour, E.: Sea-level "
     "contribution from Thwaites Glacier doubles in an observation-constrained ice-sheet model, Nat. Commun., 17, 10364, "
     "https://doi.org/10.1038/s41467-026-77976-1, 2026."),
    ("Nauels, A., Möller", "NOAA Laboratory for Satellite Altimetry: Global mean sea level time series, TOPEX/Poseidon, "
     "Jason-1, -2, -3 and Sentinel-6MF, seasonal signals removed (slr_sla_gbl_free_ref_90), NOAA/NESDIS/STAR [data set], "
     "https://www.star.nesdis.noaa.gov/socd/lsa/SeaLevelRise/LSA_SLR_timeseries.php, last access: 18 May 2026, 2026."),
    ("Nauels, A., Möller", "Nicholls, Z. R. J., Meinshausen, M., Lewis, J., Gieseke, R., Dommenget, D., Dorheim, K., Fan, "
     "C.-S., Fuglestvedt, J. S., Gasser, T., Golüke, U., Goodwin, P., Hartin, C., Hope, A. P., Kriegler, E., Leach, N. J., "
     "Marchegiani, D., McBride, L. A., Quilcaille, Y., Rogelj, J., Salawitch, R. J., Samset, B. H., Sandstad, M., "
     "Shiklomanov, A. N., Skeie, R. B., Smith, C. J., Smith, S., Tanaka, K., Tsutsui, J., and Xie, Z.: Reduced Complexity "
     "Model Intercomparison Project Phase 1: introduction and evaluation of global-mean temperature response, Geosci. "
     "Model Dev., 13, 5175–5190, https://doi.org/10.5194/gmd-13-5175-2020, 2020."),
    ("Nauels, A., Möller", "Nicholls, Z. and Lewis, J.: Reduced Complexity Model Intercomparison Project (RCMIP) protocol, "
     "v5.1.0, Zenodo [data set], https://doi.org/10.5281/zenodo.4589756, 2021."),
]


def add_after(id_, ctx, prefix, new):
    try:
        edlib.ins(ctx, prefix, new, id_)
        return "ok"
    except SystemExit:
        return span_edit(dict(id=id_, category="wording", anchor=ctx, old=prefix, new=prefix + new))


## ---- Table A1: the four log10 rows shown in ln, as the research table does since b8d7fdf (Marcus "Option 1", 11-10) ---
## Values from Ladrillo.jl test/reference/research_ladrillo_prior_posterior_L27.md (the 11-10 research build).
LN10 = math.log(10)
A1 = {  # row label -> {column: new text}
    "gic_log10_kappa_R19": {"Description": "ln of the response-rate constant κ, RGI 19", "Units": "ln(yr⁻¹ K⁻ν)ᶜ",
                            "Prior": "N(κ̂(amp), 0.262) on [−9, −3.81]ᵃ", "Median": "−6.4", "5%": "−6.9", "95%": "−5.9"},
    "gic_log10_kappa_SLOWG": {"Description": "ln of the response-rate constant κ, SLOWG", "Units": "ln(yr⁻¹ K⁻ν)ᶜ",
                              "Prior": "N(κ̂(amp), 0.262) on [−10.9, −4.99]ᵃ", "Median": "−8.01", "5%": "−8.5", "95%": "−7.5"},
    "gic_log10_kappa_FASTG": {"Description": "ln of the response-rate constant κ, FASTG", "Units": "ln(yr⁻¹ K⁻ν)ᶜ",
                              "Prior": "N(κ̂(amp), 0.262) on [−8.69, −3.5]ᵃ", "Median": "−6.01", "5%": "−6.36", "95%": "−5.65"},
    "gis_s_high": {"Description": "ln rate scale of the high basin (North and Northeast) relative to the active basin",
                   "Units": "ln(–)ᶜ", "Prior": "N(0, 1.15) on [−4.61, 4.61]", "Median": "−1.29", "5%": "−1.81", "95%": "−0.83"},
    "ais_c": {"Description": "Rise of the runoff line per °C, c_R"},
}
A1_FOOTNOTE = (" ᶜ Sampled as log₁₀ in the code and the posterior file; shown here as ln = ln 10 × log₁₀ "
               "(ln 10 = 2.303).")


def cell_text(e):
    cs = cell_bounds(e)
    assert len(cs) == 1, (e, len(cs))
    return para_text(*cs[0]).strip()


def num(s):
    return float(s.replace("−", "-"))


def table_a1():
    out = {}
    for row, cols in A1.items():
        for col, new in cols.items():
            e = dict(id=f"A1:{row}:{col}", category="table", docx_table_index=5, row_label=row, column=col, new=new)
            e["old"] = cell_text(e)
            if col in ("Median", "5%", "95%"):     # the ln value is ln 10 x the log10 value it replaces, to rounding
                assert abs(num(new) - LN10 * num(e["old"])) <= 0.006 * abs(num(new)) + 0.006, (e["id"], e["old"], new)
            out[e["id"]] = "same" if e["old"] == new else span_edit(e)
    edlib.ins("replaces h₀ (h₀ = −T_on·c).", "replaces h₀ (h₀ = −T_on·c).", A1_FOOTNOTE, "Table A1 footnote c")
    return out


## ---- equations: each on its own line (they are, one run per line) with the number at the right margin -------------
EQ_PARAS = [("S_eq = max(", 2), ("E_b(T)   = min(", 5), ("u(t)  = min(", 4), ("   = ln N( r_i", 3)]
EQ_RUN = re.compile(r"^(.*\S)( {2,})(\(\d+\))$")


def text_width_twips():
    s = d.x[d.x.rindex("<w:sectPr"):]
    w = int(re.search(r'<w:pgSz w:w="(\d+)"', s).group(1))
    left = int(re.search(r'<w:pgMar [^>]*w:left="(\d+)"', s).group(1))
    right = int(re.search(r'<w:pgMar [^>]*w:right="(\d+)"', s).group(1))
    return w - left - right


def equation_tabs():
    pos = text_width_twips()
    n_total = 0
    for anchor, n_expected in EQ_PARAS:
        a = escape(anchor)
        hits = [m.start() for m in RUN_RE.finditer(d.x) if a in m.group(2) and not _in_tracked(d.x, m.start())]
        assert len(hits) == 1, (anchor, len(hits))
        ps, pe = _para_bounds(d.x, hits[0])
        p = d.x[ps:pe]
        runs = [m for m in RUN_RE.finditer(p) if EQ_RUN.match(unescape(m.group(2))) and not _in_tracked(d.x, ps + m.start())]
        assert len(runs) == n_expected, (anchor, len(runs), n_expected)
        for m in reversed(runs):
            rpr, t = m.group(1), unescape(m.group(2))
            pre, sp, numtxt = EQ_RUN.match(t).groups()
            tab = (f'<w:ins w:id="{d._id()}" w:author="{AUTHOR}" w:date="{DATE}"><w:r>{rpr or ""}<w:tab/></w:r></w:ins>')
            new = d._run(rpr, escape(pre)) + d._del(rpr, sp) + tab + d._run(rpr, escape(numtxt))
            p = p[:m.start()] + new + p[m.end():]
        ppr = re.search(r"<w:pPr>(.*?)</w:pPr>", p, re.S)
        inner = ppr.group(1)
        assert "<w:tabs>" not in inner and "<w:pPrChange" not in inner, anchor
        style = re.search(r'<w:pStyle w:val="[^"]*"/>', inner).group(0)
        old_props = re.sub(r"<w:rPr>.*?</w:rPr>", "", inner, flags=re.S)        # pPrChange holds the old pPr, no rPr
        tabs = f'<w:tabs><w:tab w:val="right" w:pos="{pos}"/></w:tabs>'
        new_inner = inner.replace(style, style + tabs, 1) + (
            f'<w:pPrChange w:id="{d._id()}" w:author="{AUTHOR}" w:date="{DATE}"><w:pPr>{old_props}</w:pPr></w:pPrChange>')
        p = p.replace(f"<w:pPr>{inner}</w:pPr>", f"<w:pPr>{new_inner}</w:pPr>", 1)
        d.x = d.x[:ps] + p + d.x[pe:]
        d.log.append((anchor, f"{len(runs)} equation numbers on a right tab at {pos} twips", "guidance: Equations"))
        n_total += len(runs)
    return n_total


## ---- figures: the 11-05 lettered renders and the joint-arm Fig. 5 replace the images round 10-15 inserted ---------
## Each 10-15 image is still a pending insertion (Claude, 10-15); its run is deleted inside that insertion and the new
## image inserted after it, so both rounds stay visible.
FIGS = [("rId11", "hindcast_components_L27.png", "Fig. 1: lettered render (11-05)"),
        ("rId13", "model_comparison_components_vv_L27_2100.png", "Fig. 2: lettered render (11-05)"),
        ("rId15", "model_comparison_components_vv_L27_2300.png", "Fig. 3: lettered render (11-05)"),
        ("rId17", "future_components_vv_L27_joint.png", "Fig. 4: lettered render (11-05)"),
        ("rId19", "vv_gsic_ladrillo_L27_2300_joint.png", "Fig. 5: joint arm (11-05), as the caption says"),
        ("rId21", "vv_responsiveness_L27.png", "Fig. 6: lettered render (11-05)")]


def reswap(rid, new_rid, new_cy, descr):
    key = f'r:embed="{rid}"'
    assert d.x.count(key) == 1, rid
    i = d.x.index(key)
    s = max(d.x.rfind("<w:r>", 0, i), d.x.rfind("<w:r ", 0, i))
    e = d.x.index("</w:r>", i) + len("</w:r>")
    o = d.x.rfind("<w:ins ", 0, s)
    assert o > d.x.rfind("</w:ins>", 0, s) and 'w:author="Claude"' in d.x[o:o + 200], f"{rid} is not in a pending insertion"
    c = d.x.index("</w:ins>", e) + len("</w:ins>")
    assert d.x[e:c] == "</w:ins>", f"{rid}: its insertion holds more than the image"
    run = d.x[s:e]
    new = run.replace(key, f'r:embed="{new_rid}"')
    new = re.sub(r'(<wp:extent cx="\d+" cy=")\d+(")', rf"\g<1>{new_cy}\2", new)
    new = re.sub(r'(<a:ext cx="\d+" cy=")\d+(")', rf"\g<1>{new_cy}\2", new)
    dpr = max(int(v) for v in re.findall(r'<wp:docPr id="(\d+)"', d.x)) + 1
    new = re.sub(r'<wp:docPr id="\d+"', f'<wp:docPr id="{dpr}"', new)
    new = re.sub(r'( descr=")[^"]*(")', rf"\g<1>{descr}\2", new)
    out = (f'<w:del w:id="{d._id()}" w:author="{AUTHOR}" w:date="{DATE}">{run}</w:del></w:ins>'
           f'<w:ins w:id="{d._id()}" w:author="{AUTHOR}" w:date="{DATE}">{new}</w:ins>')
    d.x = d.x[:s] + out + d.x[c:]
    d.log.append((f"[image {rid}]", f"[image {new_rid}: {descr}]", "guidance: Figures"))


def swap_figures():
    from PIL import Image
    rels_p = W + "/word/_rels/document.xml.rels"
    rels = open(rels_p, encoding="utf8").read()
    nid = max(int(i) for i in re.findall(r'Id="rId(\d+)"', rels)) + 1
    for rid, png, why in FIGS:
        src = os.path.join(REPO, "figures", "paper", png)
        tgt = f"media/fig1111_{png}"
        shutil.copyfile(src, os.path.join(W, "word", tgt))
        new = f"rId{nid}"; nid += 1
        rels = rels.replace("</Relationships>", f'<Relationship Id="{new}" Type="http://schemas.openxmlformats.org/'
                            f'officeDocument/2006/relationships/image" Target="{tgt}"/></Relationships>')
        cx = int(re.findall(r'<wp:extent cx="(\d+)"', d.x[:d.x.index(f'r:embed="{rid}"')])[-1])
        w_px, h_px = Image.open(src).size
        reswap(rid, new, round(cx * h_px / w_px), "figures/paper/" + png)
    open(rels_p, "w", encoding="utf8").write(rels)
    return len(FIGS)


## ---- this round's insertions out of pending moves --------------------------------------------------------------
## An insertion that lands inside someone's pending <w:moveTo> (the equation blocks, moved by Marcus 11-01) is not part
## of that move. As Word does when one types inside moved text, close the move before it and reopen it after, with a
## new id and the move's own attributes, inside the same move range. (Pandoc's reader drops an <w:ins> nested in a
## <w:moveTo>, so verify_r1111.py check 3 could not see these.)
def split_moves():
    own = re.compile(r'<w:ins w:id="\d+" w:author="%s" w:date="%s">.*?</w:ins>' % (AUTHOR, DATE), re.S)
    n = 0
    for m in reversed(list(own.finditer(d.x))):
        pre = d.x[:m.start()]
        o = max((k.start() for k in re.finditer(r"<w:moveTo w:id=\"\d+\"[^>]*?(?<!/)>", pre[-20000:])), default=-1)
        if o < 0:
            continue
        o += len(pre) - len(pre[-20000:])
        if pre.rfind("</w:moveTo>") > o:
            continue
        attrs = re.match(r'<w:moveTo w:id="\d+" ([^>]*)>', d.x[o:]).group(1)
        d.x = d.x[:m.start()] + "</w:moveTo>" + m.group(0) + f'<w:moveTo w:id="{d._id()}" {attrs}>' + d.x[m.end():]
        n += 1
    d.x = re.sub(r'<w:moveTo w:id="\d+" [^>]*?(?<!/)></w:moveTo>', "", d.x)   # empty halves at a move's edge
    return n


## ---- comments for Marcus: facts behind sentences that are his to write ------------------------------------------
COMMENTS = [
    ("paleo-ensemble medians during calibration",
     "Claude 11-11: the L27 chains did not hold the paleo medians. The research calibrator sets them and then loads the "
     "central row over them, so the chains ran at lambda = 0.01365 m/yr, T_crit = -15.14 °C and gamma = 2.038 (found "
     "porting the calibrator to Ladrillo.jl; the port reproduces the production chain only with these values). Products "
     "use the paleo median gamma 2.834 and joint (lambda, T_crit) draws. Lambda and T_crit have no effect on the "
     "1900-2025 hindcast (bitwise); gamma moves it by at most 0.015 cm. Importance weights from gamma 2.038 to 2.834 "
     "over the 10,000 draws: ESS 99.7%, projected quantiles move at most 0.54 cm, so the products match a calibration at "
     "2.834 to about 0.5 cm. Your call (11-11): keep the products and state this. Table A3's lambda, T_crit and gamma "
     "rows give the same calibration values. The sentence is yours."),
    ("the remaining difference between FaIR and IGCC",
     "Claude 11-11: IGCC 2025 numbers (Decision 2). Three decimals because the two-decimal factors 1.11 × 1.10 × 1.01 "
     "multiply to 1.23, not 1.22. Rewording to avoid the product is your call."),
    ("the calibration targets with the scripts that build them from the sources in Table 3",
     "Claude 11-11, state of Ladrillo.jl: it now has the scripts for Figs. 1-6 and Tables 4, 5, A1 and A2, the "
     "calibration sampler (reproduces the production L27 chain bit for bit for 20,000 iterations) and the post-processing "
     "(the four production chains give the shipped 10,000-draw posterior byte for byte). Not yet: the scripts that build "
     "the calibration targets and drivers from the Table 3 sources. That port needs your decisions on the non-public "
     "Dangendorf v2 file, GRACE redistribution and dataset licences."),
    ("mimiframework/Mimi.jl, all versions",
     "Claude 11-11: the Manifest pins Mimi 1.6.0 (GitHub tag v1.6.0, commit b01ae95, 2026-04-03), but Zenodo never archived "
     "1.6: the concept DOI 4321855 resolves to v1.5.1 (10.5281/zenodo.7370071, 2022). Option 1: cite the GitHub tag "
     "v1.6.0 (no DOI), year 2026, so 'Rennels et al., 2026' in Sect. 3.2. Option 2: keep this entry (2022, concept "
     "DOI). I fixed only the two creator names to match Zenodo."),
    ("last access: 18 May 2026",
     "Claude 11-11: the repository bounds the download to 18-20 May 2026 (URLs confirmed 05-18 in download_obs.py; the "
     "file was committed 05-20); I used 18 May. NOAA's data policy asks for the acknowledgment 'Altimetry data are "
     "provided by the NOAA Laboratory for Satellite Altimetry.'; the Acknowledgements say 'are sourced from'."),
    ("that each figure reads",
     "Claude 11-11: true of Ladrillo.jl since 11-11: every file a figure reads there records the seeds behind it, and its "
     "figures are byte-identical to the paper's. Still false of the research repository's files. The wording is yours."),
    ("Regrowth of about 0.08 cm occurs on Low-to-Negative",
     "Claude 11-11: the joint-arm image is in; I deleted the caption's closing 'Fixed arm.' to match it. The guidance's "
     "move of this figure to after the peak-and-decline paragraph is NOT done: a scripted move would turn this caption's "
     "pending edits into one Claude insertion. Cut and paste the figure and caption in Word with Track Changes on if you "
     "want it. Figs. 5 and 6 are first cited together (Sect. 4.2), so the move does not change their numbering."),
]


if __name__ == "__main__":
    report = {}
    for e in ENTRIES:
        r = apply(e)
        if r.startswith("SKIP (0 runs") and e.get("anchor"):
            r = span_edit(e)
        report[e["id"]] = r
    for id_, ctx, o, n in MINIMAL:
        try:
            edlib.edit(ctx, o, n, id_)
            report[id_] = "ok"
        except SystemExit:      # context not in one run (e.g. inside a multi-run pending insertion): span edit of ctx
            report[id_] = span_edit(dict(id=id_, category="wording", anchor=ctx, old=ctx, new=ctx.replace(o, n, 1)))
    for id_, ctx, prefix, new in CITES:
        report[id_] = add_after(id_, ctx, prefix, new)
    for k, (anchor, text) in enumerate(NEW_REFS):
        d.insert_para(anchor, text, why=f"new reference {k}")
        report[f"REF{k}"] = "ok"
    report.update(table_a1())
    neq = equation_tabs()
    nfig = swap_figures()
    nmv = split_moves()
    print(f"{nmv} of this round's insertions moved out of pending moves")
    d.save()
    skipped = {k: v for k, v in report.items() if not (v.startswith("ok") or v == "same")}
    print(f"applied {sum(v.startswith('ok') for v in report.values())} of {len(report)} text/table edits "
          f"({sum('span' in v for v in report.values())} span runs); {neq} equation numbers tabbed; {nfig} figures")
    for k, v in skipped.items():
        print(f"  SKIPPED {k}: {v}")
    import comments_lib as cl
    for phrase, text in COMMENTS:
        cl.comment(phrase, text)
    open(os.path.join(W, "..", os.path.basename(W) + "_log.txt"), "w", encoding="utf8").write(
        "\n".join(f"{a} | {b} | {c}" for a, b, c in d.log) + "\n")
    print(f"edits_r1111: {len(report) - len(skipped)} applied, {len(skipped)} skipped, {len(COMMENTS)} comments")
    sys.exit(1 if skipped else 0)
