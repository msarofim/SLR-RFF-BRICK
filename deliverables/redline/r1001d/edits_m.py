"""10-01d edit set M (Marcus 10-01: "fix FIG, the undefined acronym, make UK spelling consistent if that is
what GMD expects").

GMD's submission guidelines (geoscientific-model-development.net/submission.html, read 10-01):
  - "Fig." in running text, "Figure" at the start of a sentence; "Table" is never abbreviated.
    Captions follow the Copernicus "Figure N." form.
  - Abbreviations are defined in the abstract and again at the first instance in the rest of the text,
    except ones better known than their written-out form (NASA, GPS, ...).
  - "All standard varieties of English are accepted ... the variety should be consistent", and for an
    international readership "Oxford spelling using -z- variants ... is often utilized". GMD does not
    require British spelling; this round applies OXFORD spelling (British, with -ize), which is the
    British variety GMD names. The draft was mixed (-ise 10 / -ize 8; centre 3 / center 1; modelling 2 /
    modeling 1). Reference titles are never changed.

Acronym expansions were checked against a source, not recalled:
  BRICK (MimiBRICK.jl source), SNEASY (MimiBRICK docs), FaIR (fair package), DAIS = "DCESS (Danish Center
  for Earth System Science) Antarctic Ice Sheet" (Shaffer 2014, GMD 7:1803), SICOPOLIS (its GitHub README),
  FrEDI (the FrEDI package DESCRIPTION), SLEIP / GlaMBIE / FACTS (titles in this paper's reference list),
  IMBIE (Ice Sheet Mass Balance Inter-comparison Exercise, in local IMBIE papers). The rest are generic
  terms or standard CMIP-family project names. LARMIP and PISM were left alone (footnote labels with a
  citation each, and the LARMIP expansion could not be checked).
Rule used: define at the first use in running text or a caption; table cells are covered by a
definition list in their table's caption (Table 2 already had one, "n.d. = ...").
"""
import os, re, sys
from xml.sax.saxutils import escape
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from trackedit import Doc, DATE

d = Doc(sys.argv[1] + "/word/document.xml")
INS_PAT = re.compile(r'<w:ins (w:id="\d+") (w:author="Claude" w:date="[^"]*")>'
                     r'<w:r>((?:<w:rPr>(?:(?!</w:rPr>).)*</w:rPr>)?)<w:t(?: xml:space="preserve")?>([^<]*)</w:t></w:r></w:ins>', re.S)


def _plain_hits(c):
    from trackedit import RUN_RE, _in_tracked
    return [m for m in RUN_RE.finditer(d.x) if c in m.group(2) and not _in_tracked(d.x, m.start())]


def _earlier_ins(c):
    hits = [m for m in INS_PAT.finditer(d.x) if c in m.group(4)]
    for m in hits:
        assert DATE not in m.group(2), "that insertion is this round's own"
    return hits


def edit(context, old, new, why=""):
    """Tracked replacement of `old` by `new` at the first occurrence of `old` inside `context`.
    `context` must occur once: in an untracked run, or else in one of Claude's EARLIER pending insertions
    (which is split around the change rather than nested)."""
    c = escape(context)
    ph, eh = _plain_hits(c), _earlier_ins(c)
    if len(ph) + len(eh) != 1:   # (raw counts would include deleted text, which is not a second target)
        raise SystemExit(f"*** context must occur exactly once (plain {len(ph)}, earlier-ins {len(eh)}): {context[:80]!r}")
    o, n = escape(old), escape(new)
    if ph:
        m = ph[0]; rpr, t = m.group(1), m.group(2)
        i = t.index(c) + c.index(o)
        out = d._run(rpr, t[:i]) + d._del(rpr, o) + d._ins(rpr, n) + d._run(rpr, t[i + len(o):])
    else:
        m = eh[0]; attrs, rpr, t = m.group(2), m.group(3), m.group(4)
        i = t.index(c) + c.index(o)
        half = lambda s: f'<w:ins w:id="{d._id()}" {attrs}><w:r>{rpr}{d._t(s)}</w:r></w:ins>' if s else ""
        nested = (f'<w:ins w:id="{d._id()}" {attrs}>' + d._del(rpr, o) + '</w:ins>') if o else ""
        out = half(t[:i]) + nested + d._ins(rpr, n) + half(t[i + len(o):])
    d.x = d.x[:m.start()] + out + d.x[m.end():]
    d.log.append((context, f"{old!r} -> {new!r}", why))


def ins(context, prefix, new, why=""):
    """Tracked insertion of `new` right after `prefix` (a leading part of `context`)."""
    assert context.startswith(prefix)
    c = escape(context)
    ph, eh = _plain_hits(c), _earlier_ins(c)
    if len(ph) + len(eh) != 1:
        raise SystemExit(f"*** context must occur exactly once (plain {len(ph)}, earlier-ins {len(eh)}): {context[:80]!r}")
    n = escape(new)
    if ph:
        m = ph[0]; rpr, t = m.group(1), m.group(2)
        j = t.index(c) + len(escape(prefix))
        out = d._run(rpr, t[:j]) + d._ins(rpr, n) + d._run(rpr, t[j:])
    else:
        m = eh[0]; attrs, rpr, t = m.group(2), m.group(3), m.group(4)
        j = t.index(c) + len(escape(prefix))
        half = lambda s: f'<w:ins w:id="{d._id()}" {attrs}><w:r>{rpr}{d._t(s)}</w:r></w:ins>' if s else ""
        out = half(t[:j]) + d._ins(rpr, n) + half(t[j:])
    d.x = d.x[:m.start()] + out + d.x[m.end():]
    d.log.append((context, f"+ {new!r}", why))


# ---- 1. Figure calls ---------------------------------------------------------------------------
FIG = "Fig. in running text, Figure at sentence start and in captions (GMD guidelines)"
edit("(see Figure 1 and Table 4)", "Figure", "Fig.", FIG)
edit("(FIG 1, Table 4;", "FIG", "Fig.", FIG)
edit("The total in FIG 1 and Table 4, through 2021", "FIG", "Fig.", FIG)
edit("The total in FIG 1 and Table 4 over 2022", "FIG", "Fig.", FIG)
edit("hindcast in FIG 1 and Table 4", "FIG", "Fig.", FIG)
edit("FIG 1 and Table 4 show the bare module", "FIG", "Figure", FIG)
edit("FIG 2 and FIG 3 compare", "FIG 2 and FIG 3", "Figures 2 and 3", FIG)
edit("FIG 4 shows the Ladrillo", "FIG", "Fig.", FIG)
edit("FIG 5 Ladrillo's glacier response", "FIG", "Fig.", FIG)
edit("FIG 6 each model", "FIG", "Fig.", FIG)
for cap in ("FIG 1.", "FIG 2.", "FIG 3.", "FIG 4.", "FIG 5.", "FIG 6."):   # each caption label is its own run
    edit(cap, "FIG", "Figure", "caption form")

# ---- 2. Acronyms: abstract ---------------------------------------------------------------------
AB = "defined in the abstract (GMD)"
ins("BRICK is a widely used sea level rise emulator", "BRICK", " (Building blocks for Relevant Ice and Climate Knowledge)", AB)
edit("Rather than being coupled to SNEASY,", "SNEASY", "the Simple Nonlinear Earth System model (SNEASY)", AB)
edit("input from the FaIR model", "FaIR model", "Finite-amplitude Impulse Response (FaIR) model", AB)
edit("assessed by the SLEIP project", "SLEIP project", "Sea Level Emulator Intercomparison Project (SLEIP)", AB)

# ---- 3. Acronyms: first use in the body ----------------------------------------------------------
B = "defined at first use in the body (GMD)"
ins("or earlier: BRICK 2.0, SURFER", "or earlier: BRICK 2.0", " (Building blocks for Relevant Ice and Climate Knowledge)", B)
edit("informed by ISMIP6 and SICOPOLIS", "ISMIP6 and SICOPOLIS",
     "the Ice Sheet Model Intercomparison Project for CMIP6 (ISMIP6) and the SImulation COde for POLythermal Ice Sheets (SICOPOLIS)", B)
edit("use of GlacierMIP3 experiments", "GlacierMIP3", "the Glacier Model Intercomparison Project phase 3 (GlacierMIP3)", B)
edit("rather than IMBIE's 1992–2017", "IMBIE's 1992–2017", "the 1992–2017 Ice Sheet Mass Balance Inter-comparison Exercise (IMBIE) record", B)
edit("additions of GlaMBIE, GRACE and Mouginot", "GlaMBIE, GRACE",
     "Glacier Mass Balance Intercomparison Exercise (GlaMBIE), Gravity Recovery and Climate Experiment (GRACE)", B)
edit("to a CMIP6 based one", "CMIP6 based", "Coupled Model Intercomparison Project Phase 6 (CMIP6) based", B)
ins("a current version of FaIR 2.2.4", "a current version of ", "the Finite-amplitude Impulse Response model, ", B)
edit("rather than being coupled to SNEASY.", "SNEASY", "the Simple Nonlinear Earth System model (SNEASY)", B)
ins("FACTS (Kopp et al., 2023), FRISIA", "FACTS (", "Framework for Assessing Changes To Sea-level; ", B)
ins("MAGICC-SLR (Nauels et al., 2017, 2025), MP25", "MAGICC-SLR (",
    "sea-level module of the Model for the Assessment of Greenhouse Gas Induced Climate Change; ", B)
ins("read from its code. n.d. = not documented in SLEIP.", "read from its code. n.d. = not documented in SLEIP.",
    " GMST = global mean surface temperature.", "Table 1 cells")
edit("TE, glaciers only", "TE", "Thermal expansion", "single use; spelled out")
edit("Observations plus AR6 projections", "AR6", "IPCC Sixth Assessment Report (AR6)", B)
ins("regions. n.d. = not documented in SLEIP.", "regions. n.d. = not documented in SLEIP.",
    " OHC = ocean heat content; GSAT = global surface air temperature; SMB = surface mass balance; DAIS = Danish"
    " Center for Earth System Science Antarctic Ice Sheet model (Shaffer, 2014); ODE = ordinary differential equation.",
    "Table 2 cells")
edit("8.4 cm SLE for all RGI regions", "SLE for all RGI regions",
     "sea-level equivalent (SLE) for all Randolph Glacier Inventory (RGI) regions", B)
edit("Cumulative-melt cap from AR5 Table 4.2", "AR5", "IPCC Fifth Assessment Report (AR5)", B)
edit("forced with external GMST and OHC", "GMST and OHC",
     "global mean surface temperature (GMST) and ocean heat content (OHC)", B)
edit("Two channels (SMB / dynamic discharge)", "SMB / dynamic discharge", "surface mass balance, SMB, and dynamic discharge", B)
ins("an additional 0.7 cm (SSP1-2.6, 2300)", "an additional 0.7 cm (", "Shared Socioeconomic Pathway ", B)
ins("same DAIS structure (Shaffer, 2014)", "same DAIS structure (", "Danish Center for Earth System Science Antarctic Ice Sheet model; ", B)
edit("GRACE/GRACE-FO JPL mascons", "GRACE/GRACE-FO JPL", "GRACE/GRACE Follow-On (GRACE-FO) Jet Propulsion Laboratory (JPL)", B)
edit("Dangendorf et al. (2024) GMSL", "GMSL", "global mean sea level (GMSL)", B)
edit("no GIA correction", "GIA", "glacial isostatic adjustment", "single use; spelled out")
ins("IGCC 2025-indicators GMSL", "IGCC", " (Indicators of Global Climate Change)", B)
edit("so the AIS changes", "AIS", "Antarctic", "single use; spelled out")
ins("four AR(1) noise pairs", "four AR(1)", " (first-order autoregressive)", B)
edit("driven by CMIP7 historical", "CMIP7", "Coupled Model Intercomparison Project Phase 7 (CMIP7)", B)
edit("to the RCMIP (v5.1.0)", "RCMIP (v5.1.0)", "Reduced Complexity Model Intercomparison Project (RCMIP; v5.1.0)", B)
edit(" RMSE of the Ladrillo median", "RMSE", "Root-mean-square error (RMSE)", B)
ins(". AIC = 2k − 2 ln L; BIC = k ln N − 2 ln L; lower is better", ". AIC", " (Akaike information criterion)", B)
ins("; BIC = k ln N − 2 ln L; lower is better", "; BIC", " (Bayesian information criterion)", B)
ins("seven ScenarioMIP-CMIP7 marker", "seven ScenarioMIP-CMIP7", " (Scenario Model Intercomparison Project for CMIP7)", B)
ins("(e.g., FrEDI;", "(e.g., ", "the Framework for Evaluating Damages and Impacts, ", B)

# ---- 4. Oxford spelling (body only; reference titles untouched) --------------------------------
OX = "Oxford spelling, consistent (GMD)"
for ctx, old, new in [
    ("its realised volume", "realised", "realized"),
    ("Measured on realised regrowth", "realised", "realized"),
    ("is centered on its observed", "centered", "centred"),
    ("coefficient is centered near zero", "centered", "centred"),
    ("normalised to 1 at the anchor", "normalised", "normalized"),
    ("rank-normalised split", "normalised", "normalized"),
    ("that is orthogonalised", "orthogonalised", "orthogonalized"),
    ("The basis is orthogonalised", "orthogonalised", "orthogonalized"),
    ("not explicitly modeled", "modeled", "modelled"),
    ("model's idealised ice-sheet", "idealised", "idealized"),
    ("used in a standardised correlation", "standardised", "standardized"),
    ("during the run toward a", "toward", "towards"),
    ("a modeling framework", "modeling", "modelling"),
    ("complex future behavior", "behavior", "behaviour"),
    ("prior-standardised coordinates", "standardised", "standardized"),
    ("parameter standardised by its prior", "standardised", "standardized"),
]:
    edit(ctx, old, new, OX)

d.save()
for c, ch, w in d.log:
    print(f"- {c[:50]!r}: {ch[:90]}  [{w}]")
print(f"{len(d.log)} edits")
