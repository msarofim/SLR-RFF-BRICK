"""Round 8 (2026-09-21): projections carry the OBSERVED land-water series (Marcus: "If we have LWS observations we
should use them"). Base = the r7 review docx. Edits: the land-water paragraph (a pending r4 insertion -> nested
deletion + new insertion), the design-overview clause, footnote 15, the High / Low scenario paragraphs (their
totals move by the observed-minus-constant offset), and the three paper figures whose content changed
(FIGs 2, 3, 4) -- their media files are REPLACED IN PLACE inside the r6 tracked insertion (same rId, same
picture name), since the r6 insertion is still pending and a picture cannot carry a nested deletion.
Every number is read from the regenerated outputs; the L24/L27-central values it replaces are asserted."""
import hashlib, re, shutil
import pandas as pd
from redline import *
import redline

redline.DATE = "2026-09-21T12:00:00Z"        # distinct from r7's 00:00 stamp (validate keys on author+date+text)
REPO = HERE.parent.parent; OUT = REPO / "outputs"; FIG = REPO / "figures/paper"; UNP = HERE / "unpacked"
x = load()
x = x.replace("<w:lastRenderedPageBreak/>", "").replace("<w:t>", '<w:t xml:space="preserve">')
x = re.sub(r'</w:t><w:t xml:space="preserve">', "", x)
start_ids_above(x)
_esc0 = redline.esc
def _esc_minus(sx): return _esc0(re.sub(r"(?<![\w])-(?=\d)", "−", sx))
redline.esc = _esc_minus; esc = _esc_minus
def chk(c, m):
    if not c: raise SystemExit("[r8 ABORT] " + m)

# ---- numbers ---------------------------------------------------------------------------------------
S = pd.read_csv(OUT / "ssps_components_2300_L27_tap4p69K_V5p64m_tau800_n2_ws.csv")
lws2300 = float(S[(S.ssp == "SSP2-4.5") & (S.component == "lws") & (S.year == 2300)].med.iloc[0])
lws_all = S[(S.component == "lws") & (S.year == 2300)].med
chk(lws_all.max() - lws_all.min() < 1e-6, "lws@2300 identical across scenarios")
V = pd.read_csv(OUT / "vv_model_comparison_L27.csv"); SW = pd.read_csv(OUT / "vv_climate_swap_L27.csv")
def v(src, scen, comp, yr, col="med"): return float(V[(V.source == src) & (V.scenario == scen) & (V.component == comp) & (V.year == yr)][col].iloc[0])
def sw(src, mk, comp, yr, col): return float(SW[(SW.source == src) & (SW.marker == mk) & (SW.component == comp) & (SW.year == yr)][col].iloc[0])
prov = pd.read_csv(OUT / "scope_slr_fairunc_cells_vvH_spliced_L27_tap4p69K_V5p64m_tau800.csv").provenance.iloc[0]
chk("lws observed" in prov, "the vvH arm is on the observed LWS: %s" % prov[:120])
prov_b = pd.read_csv(OUT / "scope_slr_fairunc_cells_vvH_spliced_oldbrick.csv").provenance.iloc[0]
chk("observed" in prov_b, "the BRICK vvH arm is on the observed LWS: %s" % prov_b[:160])

# ---- 1. design overview clause -----------------------------------------------------------------------
x = smart_replace(x, "(the last taken from observations in the hindcast and a constant 0.30 mm yr⁻¹ in projections; see below)",
                 "(the last taken from observations through 2023 and continued at a constant 0.30 mm yr⁻¹ thereafter; see below)")

# ---- 2. the land-water paragraph ----------------------------------------------------------------------
chk(esc("so land water contributes 8.5 cm by 2300") in x, "LWS paragraph is the constant-rate version")
x = replace_para_text(x, "Land-water storage is not explicitly modeled in either Ladrillo or BRICK",
    "Land-water storage is not explicitly modeled in either Ladrillo or BRICK; both take it from observations. The observed "
    "series (Frederikse et al. (2020) through 2018, then GRACE/GRACE-FO JPL mascons for 2019–2023, land mass with the ice "
    "sheets masked, less the GlaMBIE glacier mass) enters the hindcast total (FIG 1, Table 4; the 2023 value is held "
    "constant through 2026, the end of the calibration window) and the projections alike: from 2024 both Ladrillo and the "
    "BRICK 2.0 comparison arm continue it at a constant 0.30 mm yr⁻¹ (the mean of the N(0.30, 0.18) mm yr⁻¹ annual rate that "
    "BRICK 2.0 draws stochastically), so land water contributes %.1f cm by 2300 relative to 1995–2014, identically in every "
    "scenario and in both models. BRICK 2.0 as published sets land water to zero before 2019; the comparison arm here is "
    "given the observed series so that the two models' totals stay on one basis." % lws2300)

# ---- 3. footnote 15 --------------------------------------------------------------------------------
x = smart_replace(x, "in projections LWS is a constant 0.30 mm yr⁻¹ from 2019",
                 "in projections the observed series is continued at a constant 0.30 mm yr⁻¹ from 2024")

# ---- 4. High / Low paragraphs ------------------------------------------------------------------------
H = dict(l21=v("Ladrillo", "vvH", "total", 2100), b21=v("BRICK 2.0", "vvH", "total", 2100), m21=v("MAGICC-SLR", "vvH", "total", 2100),
         l23=v("Ladrillo", "vvH", "total", 2300), b23=v("BRICK 2.0", "vvH", "total", 2300), m23=v("MAGICC-SLR", "vvH", "total", 2300),
         la=v("Ladrillo", "vvH", "ais", 2300), ba=v("BRICK 2.0", "vvH", "ais", 2300), ma=v("MAGICC-SLR", "vvH", "ais", 2300),
         lsw=sw("Ladrillo", "vvH", "total", 2300, "med_magiccclim"), bsw=sw("BRICK 2.0", "vvH", "total", 2300, "med_magiccclim"))
dl, db = H["l23"] - H["lsw"], H["b23"] - H["bsw"]
x = replace_para_text(x, "For the High scenario, the three models are fairly similar at 2100",
    "**High scenarios.** For the High scenario, the three models are fairly similar at 2100 (Ladrillo %.0f cm, BRICK 2.0 %.0f, "
    "MAGICC-SLR %.0f). By 2300 Ladrillo and BRICK 2.0 sit together (%.0f and %.0f cm, median) well below MAGICC-SLR (%.0f cm), "
    "and the gap is due to Antarctica: %.0f and %.0f cm against MAGICC's %.0f. Driving both on MAGICC's own climate actually "
    "decreases their totals by %.0f–%.0f cm mainly due to thermal expansion (to %.0f and %.0f), so the difference is the "
    "ice-sheet modules, not the climate."
    % (H["l21"], H["b21"], H["m21"], H["l23"], H["b23"], H["m23"], H["la"], H["ba"], H["ma"], min(dl, db), max(dl, db), H["lsw"], H["bsw"]))
VL = {s: v(s, "vvVL", "total", 2300) for s in ("Ladrillo", "MAGICC-SLR", "BRICK 2.0")}
VLw = {s: v(s, "vvVL", "total", 2300, "p95") - v(s, "vvVL", "total", 2300, "p05") for s in VL}
for comp in ("ais", "gis", "glaciers", "te"):
    chk(v("Ladrillo", "vvVL", comp, 2300, "p95") - v("Ladrillo", "vvVL", comp, 2300, "p05") <
        v("BRICK 2.0", "vvVL", comp, 2300, "p95") - v("BRICK 2.0", "vvVL", comp, 2300, "p05"), "narrower than BRICK on %s" % comp)
x = replace_para_text(x, "Ladrillo sits at the low end of the comparison set on level",
    "**Low scenarios.** Ladrillo sits at the low end of the comparison set on level — at vvVL its 2300 total median is %.0f cm, "
    "above only MAGICC-SLR's %.0f cm and below BRICK 2.0's %.0f. On spread it is narrower than BRICK 2.0 on every component "
    "and narrower than the FACTS glacier and thermal-expansion modules (the only FACTS modules drawn at 2300); MAGICC-SLR is "
    "the narrow outlier throughout (2300 total 5–95%% width %.0f cm against Ladrillo's %.0f and BRICK 2.0's %.0f)."
    % (VL["Ladrillo"], VL["MAGICC-SLR"], VL["BRICK 2.0"], VLw["MAGICC-SLR"], VLw["Ladrillo"], VLw["BRICK 2.0"]))

# ---- 5. figures whose content changed: replace the media inside the pending r6 insertion ---------------
rels = (UNP / "word/_rels/document.xml.rels").read_text()
def media_for(png_name):
    m = re.search(r'<pic:cNvPr id="\d+" name="[^"]*" descr="%s"' % re.escape("figures/paper/" + png_name), x)
    chk(m, "drawing for %s" % png_name)
    rid = re.search(r'r:embed="(rId\d+)"', x[m.end():m.end() + 800]).group(1)
    tgt = re.search(r'Id="%s"[^>]*Target="([^"]+)"' % rid, rels).group(1)
    return UNP / "word" / tgt
swapped = []
for png in ("model_comparison_components_vv_L27_2100.png", "model_comparison_components_vv_L27_2300.png", "future_components_vv_L27_joint.png"):
    dst = media_for(png); src = FIG / png
    if hashlib.md5(dst.read_bytes()).hexdigest() != hashlib.md5(src.read_bytes()).hexdigest():
        shutil.copy(src, dst); swapped.append(png)
for png in ("hindcast_components_L27.png", "vv_gsic_ladrillo_L27_2300.png", "vv_responsiveness_L27.png"):
    chk(hashlib.md5(media_for(png).read_bytes()).hexdigest() == hashlib.md5((FIG / png).read_bytes()).hexdigest(), "%s unchanged" % png)
save(x)
print("r8 applied: lws@2300 %.2f; High %.0f/%.0f/%.0f, %.0f/%.0f/%.0f; Low %.0f/%.0f/%.0f; media replaced: %s" %
      (lws2300, H["l21"], H["b21"], H["m21"], H["l23"], H["b23"], H["m23"], VL["Ladrillo"], VL["MAGICC-SLR"], VL["BRICK 2.0"], swapped))
