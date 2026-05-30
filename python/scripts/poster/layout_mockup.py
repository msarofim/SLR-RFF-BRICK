"""
layout_mockup.py
================

Builds half-scale wireframe mockups of the AGU Chapman SLR poster, composing
the real panel PNGs into the planned grid so the layout can be reviewed as a
whole. The mockup is a review aid; IEc produces the final print-ready poster.

Two sizes are emitted:
  outputs/poster/layout_mockup.{png,pdf}        — 46" wide × 46" high (square)
  outputs/poster/layout_mockup_42in.{png,pdf}   — 46" wide × 42" high
      (height cap for some print-on-demand sites; shorter title band, panel
       block reflowed proportionally to fit.)

Panel D carries a small inset showing the TOTAL pulse-SLR response trajectory
(cm per GtCO₂, median + 5–95% band, x starting at the 2030 pulse year), built
by pulse_slr_response_inset.py, overlaid on the pulse-SLR H-S decomposition.

Panels with no image yet fall back to a labeled placeholder box.
"""
from pathlib import Path
import textwrap
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch
import matplotlib.image as mpimg

# Embed fonts as TrueType (type 42) in PDF/PS output so a print service can't
# substitute glyphs — required for a press-ready PDF.
matplotlib.rcParams["pdf.fonttype"] = 42
matplotlib.rcParams["ps.fonttype"] = 42

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "outputs" / "poster"
OUT.mkdir(parents=True, exist_ok=True)

# Panel inventory — image path (or None for text-box placeholder).
PANELS = {
    "pipeline":              ROOT / "outputs/poster/pipeline_stages.png",
    "slr_band":              ROOT / "outputs/poster/slr_band.png",
    # Group-Sobol H-S decomposition (normalized; emissions/climate/BRICK/
    # interactions/tipping/internal), the canonical Panels C & D (replaced the
    # old TreeSHAP-era hawkins_sutton_slr_4way composites).
    "hs_decomp":             ROOT / "outputs/poster/C_total_slr_hawkins_sutton.png",
    "pulse_response":        ROOT / "outputs/poster/D_pulse_slr_hawkins_sutton.png",
    # Total pulse-SLR response trajectory (cm/GtCO₂), overlaid as a Panel-D inset.
    "pulse_inset":           ROOT / "outputs/poster/E_pulse_slr_response_inset.png",
    "sweet_scenarios":       ROOT / "outputs/poster/sweet_scenarios.png",
    "lorie_panel":           ROOT / "outputs/poster/lorie_panel.png",
    "coastal_map":           ROOT / "outputs/plots/fredi_state_damages_2100.png",
    "sheahan_table":         ROOT / "outputs/poster/sheahan_table.png",
    "htf_table":             ROOT / "outputs/poster/htf_transport_table.png",
}

EDGE = "#1F4E79"

# Native (46"-tall) vertical layout anchors. The 42" build reflows the panel
# block through Y()/Hs() below; x-coordinates and widths are identical in both.
NATIVE_H = 46.0
TOP_MARGIN = 0.5          # gap between header band and top border
GAP_BELOW_HEADER = 0.5    # gap between header band and the top panel row
PANEL_BOT = 0.5           # bottom of the lowest panel row
NATIVE_TITLE_H = 5.0
# Native panel block spans [PANEL_BOT, NATIVE_PANEL_TOP].
NATIVE_PANEL_TOP = NATIVE_H - TOP_MARGIN - NATIVE_TITLE_H - GAP_BELOW_HEADER  # = 40.0
NATIVE_SPAN = NATIVE_PANEL_TOP - PANEL_BOT                                    # = 39.5


def draw_panel(ax, x, y, w, h, label, image_path=None, placeholder_text=None,
               caption=None, label_font=8, caption_font=7,
               caption_wrap=None):
    """Render a labeled panel with image thumbnail or placeholder text.

    Coordinates: natural orientation. (x, y) is the BOTTOM-LEFT corner of
    the panel; w extends right, h extends up. Optional `caption_wrap` (int)
    wraps the caption text to that column width (chars).  If `caption_wrap`
    is omitted, the caption auto-fills the panel width using an approximate
    char-width-per-inch heuristic.

    Returns (img_x, img_y, img_w, img_h): the image sub-rectangle, so callers
    can overlay an inset.
    """
    rect = Rectangle((x, y), w, h, linewidth=1.5,
                     edgecolor=EDGE, facecolor="#F8F8F8", zorder=1)
    ax.add_patch(rect)

    # Panel label (top)
    ax.text(x + 0.3, y + h - 0.3, label, fontsize=label_font, fontweight="bold",
            color=EDGE, va="top", ha="left", zorder=5)

    # Caption (bottom) — wrap to fill the panel width at the caption font.
    cap_room = 0.0
    if caption is not None:
        if caption_wrap is None:
            caption_wrap = max(20, int((w - 0.3) * 7.5))
        paras = caption.split("\n") if "\n" in caption else [caption]
        cap_txt = "\n".join(textwrap.fill(p, width=caption_wrap) for p in paras)
        n_lines = cap_txt.count("\n") + 1
        cap_room = 0.45 + 0.16 * n_lines
        ax.text(x + w / 2, y + 0.18, cap_txt,
                ha="center", va="bottom", fontsize=caption_font,
                color="#444", style="italic", zorder=5)

    label_room = 0.7

    img_x = x + 0.3
    img_w = w - 0.6
    img_y = y + cap_room
    img_h = h - cap_room - label_room

    # Image
    if image_path is not None and image_path.exists():
        try:
            img = mpimg.imread(image_path)
            ax.imshow(img, extent=[img_x, img_x + img_w, img_y, img_y + img_h],
                      aspect="auto", zorder=3, origin="upper")
        except Exception as e:
            ax.text(x + w / 2, y + h / 2, f"[image: {image_path.name}]\n{e}",
                    ha="center", va="center", fontsize=7, color="#888")

    # Placeholder text instead of image
    if placeholder_text is not None:
        bg = FancyBboxPatch((x + 0.4, y + max(cap_room, 0.2)),
                            w - 0.8, h - max(cap_room, 0.2) - label_room,
                            boxstyle="round,pad=0.05,rounding_size=0.05",
                            facecolor="#FFFEF0", edgecolor="#CCCCCC",
                            linewidth=0.6, zorder=3)
        ax.add_patch(bg)
        ax.text(x + w / 2,
                y + (h - cap_room - label_room) / 2 + cap_room,
                placeholder_text,
                ha="center", va="center", fontsize=9, color="#444",
                style="italic", zorder=4, wrap=True)

    return img_x, img_y, img_w, img_h


def overlay_inset(ax, image_path, panel_img_rect, frac_w=0.42, frac_h=0.48,
                  pad=0.25, scale_y=1.0):
    """Overlay an inset image in the TOP-RIGHT of a panel's image rectangle.

    panel_img_rect = (img_x, img_y, img_w, img_h) as returned by draw_panel.
    A white backing box is drawn first so the inset reads cleanly over the
    underlying stacked-area chart.
    """
    if not image_path.exists():
        return
    ix, iy, iw, ih = panel_img_rect
    in_w = iw * frac_w
    in_h = ih * frac_h
    x1 = ix + iw - pad
    y1 = iy + ih - pad
    x0 = x1 - in_w
    y0 = y1 - in_h
    ax.add_patch(Rectangle((x0 - 0.12, y0 - 0.12), in_w + 0.24, in_h + 0.24,
                           facecolor="white", edgecolor="#999999",
                           linewidth=0.8, zorder=6))
    img = mpimg.imread(image_path)
    ax.imshow(img, extent=[x0, x1, y0, y1], aspect="auto", zorder=7,
              origin="upper")


def build(total_h, title_h, out_stem, wireframe_label, compact_header=False,
          print_mode=False):
    """Render one poster mockup at the given height. Width is always 46".

    print_mode=True produces a press-ready master rather than a review
    wireframe: the figure is rendered at TRUE full size (46 × total_h inches)
    so the exported PDF measures exactly that on paper; the axes fill the whole
    canvas (no surrounding whitespace, no bbox_inches="tight" which would change
    the trim size); the "WIREFRAME … draft" banner is suppressed; PNG is 300 DPI.
    """
    # Vertical reflow: map native panel-block y -> this build's y.
    panel_top = total_h - TOP_MARGIN - title_h - GAP_BELOW_HEADER
    scale_y = (panel_top - PANEL_BOT) / NATIVE_SPAN

    def Y(y):
        return PANEL_BOT + (y - PANEL_BOT) * scale_y

    def Hs(h):
        return h * scale_y

    if print_mode:
        # Full physical size; axes span the entire figure so output trim = 46×H".
        fig = plt.figure(figsize=(46.0, total_h))
        ax = fig.add_axes([0, 0, 1, 1])
    else:
        fig, ax = plt.subplots(figsize=(23, total_h / 2.0))  # half-scale review
    ax.set_xlim(0, 46)
    ax.set_ylim(0, total_h)
    ax.set_aspect("equal")
    ax.axis("off")

    ax.add_patch(Rectangle((0, 0), 46, total_h, fill=False, edgecolor=EDGE,
                           linewidth=2.0))

    # ============================================================== HEADER
    tx, tw = 0.5, 45
    ty = total_h - TOP_MARGIN - title_h
    th = title_h
    ax.add_patch(Rectangle((tx, ty), tw, th, linewidth=1.5,
                           edgecolor=EDGE, facecolor="#F8F8F8", zorder=1))
    if compact_header:
        # Shorter band: title + subtitle on tighter lines, authors+affil merged,
        # smaller fonts. Designed to fit ~2.8" while staying legible at print.
        fs_title, fs_sub, fs_auth, fs_fine = 17, 12, 9.5, 7.5
        ax.text(tx + tw / 2, ty + th - 0.55, "Some Assembly Required:",
                ha="center", va="top", fontsize=fs_title, fontweight="bold",
                color=EDGE, zorder=5)
        ax.text(tx + tw / 2, ty + th - 1.45,
                "Simplified Damage Functions for Probabilistic Coastal Impact Estimation Using FrEDI",
                ha="center", va="top", fontsize=fs_sub, fontweight="bold",
                color=EDGE, zorder=5)
        ax.text(tx + tw / 2, ty + th - 2.25,
                "Marcus C. Sarofim¹  •  James E. Neumann²  •  Megan B. Sheahan²    "
                "(¹NYU Marron Institute  •  ²Industrial Economics, Inc.)",
                ha="center", va="top", fontsize=fs_auth, color="#333", zorder=5)
        ax.text(tx + 0.4, ty + 0.22, "Funding: Wellcome Trust 227149/Z/23/Z",
                ha="left", va="bottom", fontsize=fs_fine, color="#666", zorder=5)
        ax.text(tx + tw - 0.4, ty + 0.62,
                "Code: github.com/msarofim/SLR-RFF-BRICK  ·  Data: doi.org/10.5281/zenodo.20451296",
                ha="right", va="bottom", fontsize=fs_fine, color="#666", zorder=5)
        ax.text(tx + tw - 0.4, ty + 0.22,
                "Read more:  thesaraphreport.substack.com",
                ha="right", va="bottom", fontsize=fs_fine, color="#666", zorder=5)
    else:
        ax.text(tx + tw / 2, ty + th - 0.75, "Some Assembly Required:",
                ha="center", va="top", fontsize=19, fontweight="bold",
                color=EDGE, zorder=5)
        ax.text(tx + tw / 2, ty + th - 1.9,
                "Simplified Damage Functions for Probabilistic Coastal Impact Estimation Using FrEDI",
                ha="center", va="top", fontsize=15, fontweight="bold",
                color=EDGE, zorder=5)
        ax.text(tx + tw / 2, ty + th - 3.1,
                "Marcus C. Sarofim¹    •    James E. Neumann²    •    Megan B. Sheahan²",
                ha="center", va="top", fontsize=11, color="#333", zorder=5)
        ax.text(tx + tw / 2, ty + th - 3.95,
                "¹NYU Marron Institute of Urban Management    •    ²Industrial Economics, Inc.",
                ha="center", va="top", fontsize=9.5, style="italic", color="#555", zorder=5)
        ax.text(tx + 0.4, ty + 0.28, "Funding: Wellcome Trust 227149/Z/23/Z",
                ha="left", va="bottom", fontsize=8, color="#666", zorder=5)
        ax.text(tx + tw - 0.4, ty + 0.85,
                "Code: github.com/msarofim/SLR-RFF-BRICK  ·  Data: doi.org/10.5281/zenodo.20451296",
                ha="right", va="bottom", fontsize=8, color="#666", zorder=5)
        ax.text(tx + tw - 0.4, ty + 0.28,
                "Read more:  thesaraphreport.substack.com",
                ha="right", va="bottom", fontsize=8, color="#666", zorder=5)

    # ============================================================== UPPER ROW
    # A. Pipeline — tall left column. NO caption: the pipeline graphic
    # itself carries the methods description band along its bottom.
    draw_panel(ax, 0.5, Y(24), 13, Hs(16),
               label="A. PIPELINE",
               image_path=PANELS["pipeline"])

    # B. SLR band — upper middle.
    draw_panel(ax, 14, Y(32.5), 16, Hs(7.5),
               label="B. PROBABILISTIC SLR",
               image_path=PANELS["slr_band"],
               caption="RFF-SP baseline ensemble (N=10,000 LHS), importance-weighted percentiles, 2020–2150.\n"
                       "For reference, IPCC AR6 SSP2-4.5 and SSP3-7.0 median GMSL at 2100 (Table 9.9, rebaselined to NOAA STAR rel 2000) are shown as diamond markers.  RFF-SP median emissions lie somewhere between SSP2-4.5 and SSP3-7.0.")

    # C. Total-SLR decomposition — upper right.
    draw_panel(ax, 30.5, Y(32.5), 15, Hs(7.5),
               label="C. TOTAL SLR — sources of uncertainty",
               image_path=PANELS["hs_decomp"],
               caption="Hawkins-Sutton 4-way decomposition of total-SLR variance, importance-weighted factorial design over 400 RFF-SP emissions paths, 15 climate calibrations per path, 3 FaIR stochastic seeds, and 3 BRICK posterior samples (N=54,000).  Stacked variance fractions over 2020–2150.\n"
                       "Conceptual companion to Darnell et al. 2025 (Nat Clim Change), who decompose total-SLR uncertainty across emissions vs geophysical sources at the multi-century horizon.")

    # D. Pulse SLR — side-by-side: total-response trajectory (left) + H-S
    # decomposition (right). Side-by-side (not an inset) so the H-S legend is
    # never occluded. The two sub-panels split the 15-wide D slot.
    draw_panel(ax, 30.5, Y(24), 7.2, Hs(8),
               label="D. PULSE SLR RESPONSE",
               image_path=PANELS["pulse_inset"],
               caption="Total pulse-marginal SLR — median + 5–95% band, ΔSLR per GtCO₂, from the 0.01-GtC small-pulse arm (SC-GHG-relevant linear regime, pulse-size invariant). No ensemble mean (corrupted by a few AIS-tipped draws).")
    draw_panel(ax, 38.3, Y(24), 7.2, Hs(8),
               label="D′. PULSE SLR — sources of uncertainty",
               image_path=PANELS["pulse_response"],
               caption="Paired BRICK runs on the same factorial design as Panel C (1 GtCO₂ pulse at 2030); stacked variance fractions of the pulse-marginal ΔSLR.")

    # Discussion — central position. Marcus draft (May 17 2026).
    discussion_paras = [
        ("There is high value in probabilistic damage assessment for both "
         "mitigation-benefit estimates and adaptation-response planning.  Here we "
         "demonstrate one methodology that leverages emissions uncertainty from "
         "RFF, climate uncertainty from FaIR, sea-level-response uncertainty from "
         "BRICK, global-to-local mapping from Sweet et al., and damage functions "
         "from FrEDI to produce probabilistic damage estimates by US state for "
         "three SLR-sensitive impact sectors: coastal property damage, "
         "high-tide-flooding transportation interruptions, and high-tide-flooding "
         "elder mortality.  This pipeline allows fast estimation of damages for "
         "any future scenario."),
        ("Louisiana is the state most at threat for SLR-related impacts, "
         "particularly on a per-capita basis; Florida, Massachusetts, Virginia, "
         "and New Jersey are distant 2nd–5th in per-capita impacts (Panel I).  "
         "Among FrEDI sectors, HTF elder mortality has the largest monetized "
         "impact (Panel J), with HTF transportation 2nd and coastal properties "
         "3rd (Panel H).  Climate-response uncertainty is the largest "
         "contributor to total-SLR variance (~33%) and marginal pulse response "
         "variance (~44%) in 2100, with BRICK ice-sheet uncertainty (posterior + "
         "AIS tipping) second (~28% / ~41%); emissions uncertainty matters for "
         "total SLR (~19%) but is nearly irrelevant for the per-tonne marginal "
         "response (~1%), which is essentially scenario-independent (Panels C, D)."),
        ("Key considerations we identify for this kind of work: dependence "
         "between FrEDI and BRICK parameter uncertainty (Wong et al. 2026); "
         "look-ahead-based adaptation estimates that account for observed "
         "non-optimal adaptive behavior and smoothing of capital expenditures "
         "(Panel G); and the importance of a wide range of anchor scenarios "
         "for damage-function calibration (Panel F).  The most important "
         "limitation we identify is the limited set of impact methodologies "
         "currently in FrEDI.  We call on the community to produce more impact "
         "estimates that can be transformed into damage functions to inform "
         "this kind of analysis."),
    ]
    dx, dw = 14, 16
    dy, dh = Y(24), Hs(8)
    ax.add_patch(Rectangle((dx, dy), dw, dh, linewidth=1.8,
                           edgecolor=EDGE, facecolor="#FFFEF0", zorder=1))
    ax.text(dx + 0.3, dy + dh - 0.3, "DISCUSSION",
            fontsize=10, fontweight="bold", color=EDGE, va="top", ha="left",
            zorder=5)
    discussion_body = "\n\n".join(textwrap.fill(p, width=112)
                                  for p in discussion_paras)
    ax.text(dx + 0.35, dy + dh - 0.85, discussion_body,
            ha="left", va="top", fontsize=8.5, color="#222",
            linespacing=1.30, zorder=4)

    # ============================================================== MIDDLE — damage-function methodology
    draw_panel(ax, 0.5, Y(13.5), 22.5, Hs(10),
               label="F. DAMAGE-FUNCTION METHODOLOGY — Sweet 6 SLR nodes + FrEDI damage curve",
               image_path=PANELS["sweet_scenarios"],
               caption="Left: 6 NCA5 scenarios + 2 FrEDI extensions, monotone-cubic spline through every Sweet anchor year.\n"
                       "Right: empirical FrEDI damage function at 2100 from 1000 SIR-resampled RFF-SP draws (v1.4.5 LHS-10k baseline); colored dots mark the Sweet calibration nodes that FrEDI interpolates between.")
    draw_panel(ax, 23, Y(13.5), 22.5, Hs(10),
               label="G. ADAPTATION (Lorie 2020) — NCPM decision logic + 11-yr smoothing",
               image_path=PANELS["lorie_panel"],
               caption="Left: NCPM decision logic with sub-optimal S=4 case representing observed under-adaptation (capital invested only when benefits exceed costs by ≥ 4×).\n"
                       "Middle: Lorie Table-1 cost stacks for Tampa & Virginia Beach.  Right: 11-year rolling-average smoothing of lumpy NCPM capital investments.\n"
                       "This smoothing is not only necessary because FrEDI's damage functions abstract away time — it is also consistent with how adaptation capital is amortized and financially smoothed in the real world.")

    # ============================================================== LOWER ROW — impact case studies
    # Reading order H → I → J: per-sector table (H), state map (I), elder mortality (J).
    draw_panel(ax, 0.5, Y(5), 15, Hs(8),
               label="H. COASTAL PROPERTIES AND HTF TRANSPORTATION DAMAGES",
               image_path=PANELS["htf_table"],
               caption="RFF-SP baseline ensemble (1,000 SIR-resampled draws from v1.4.5 LHS-10k baseline; equal-weighted after SIR), quantiles for Coastal Properties and HTF Transportation at 2100 and 2150.\n"
                       "Top inset bars: median ± 5–95% whiskers.")
    draw_panel(ax, 16, Y(5), 14, Hs(8),
               label="I. COASTAL PROPERTIES AND HTF TRANSPORTATION DAMAGES BY STATE",
               image_path=PANELS["coastal_map"],
               caption="Importance-weighted median annual damages (Coastal Properties + HTF Transportation) by state, 2100.  Absolute USD (left) and per-capita (right).\n"
                       "Louisiana is most impacted on a per-capita basis; FL/MA/VA/NJ are distant 2nd–5th.")
    draw_panel(ax, 30.5, Y(5), 15, Hs(8),
               label="J. HTF ELDER MORTALITY (Sheahan 2025)",
               image_path=PANELS["sheahan_table"],
               caption="Sheahan et al. 2025 Tables 2 & 3.  Additional 65+ deaths / yr from high-tide flooding under the Rennert et al. (2022) RFF–FaIR–BRICK distribution.  VSL = $7.9M (1990$) inflated to 2023$.\n"
                       "Bottom row: % reduction from stylized adaptation at the 5th, 50th, and 95th percentiles.")

    # ============================================================== BOTTOM — caveats (bulleted) + references
    caveat_bullets = [
        ("RFF-SP emissions vintage",
         "Scenarios were developed about 5 years ago; given rapid renewable / "
         "battery advances, present-day analogs might differ."),
        ("FaIR known limitations",
         "State-of-the-art probabilistic implementation, but missing "
         "permafrost feedbacks, possible Amazon dieback, and ozone / "
         "carbon-cycle interactions."),
        ("BRICK upper bias",
         "Runs slightly higher than the AR6 best estimates."),
        ("Sweet et al. as a single realization",
         "One realization of local SLR given global SLR; different "
         "partitioning between AIS, Greenland, thermal expansion, and "
         "local wind / current effects would yield different results."),
        ("FrEDI sector coverage",
         "Accounts for a limited number of SLR-derived damage categories; "
         "does not yet include probabilistic damages."),
    ]
    cx, cw = 0.5, 23
    cy, ch = Y(0.5), Hs(4.0)
    ax.add_patch(Rectangle((cx, cy), cw, ch, linewidth=1.0,
                           edgecolor="#999999", facecolor="#FAFAFA", zorder=1))
    ax.text(cx + 0.3, cy + ch - 0.3, "K. CAVEATS",
            fontsize=10, fontweight="bold", color="#666", va="top", ha="left",
            zorder=5)
    y_cur = cy + ch - 0.85
    for head, body in caveat_bullets:
        line = "•  " + head + ":  " + body
        wrapped = textwrap.fill(line, width=180, subsequent_indent="    ")
        n_lines = wrapped.count("\n") + 1
        ax.text(cx + 0.4, y_cur, wrapped,
                ha="left", va="top", fontsize=8.5, color="#444",
                linespacing=1.28, zorder=4, family="DejaVu Sans")
        y_cur -= (0.12 + 0.22 * n_lines) * scale_y

    refs = [
        ("Darnell et al. 2025.  Nat Clim Change.",
         "The interplay of future emissions and geophysical uncertainties for projections of sea-level rise.",
         "doi.org/10.1038/s41558-025-02457-0"),
        ("EPA. 2024.  EPA 430-R-24-001.",
         "Technical Documentation for the Framework for Evaluating Damages and Impacts (FrEDI).  U.S. Environmental Protection Agency.",
         ""),
        ("Fant et al. 2021.  J Infrastructure Sys.",
         "Mere Nuisance or Growing Threat? The Physical and Economic Impact of High Tide Flooding on US Road Networks.",
         "doi.org/10.1061/(ASCE)IS.1943-555X.000065"),
        ("Lorie et al. 2020.  Clim Risk Mgmt.",
         "Modeling Coastal Flood Risk and Adaptation Response under Future Climate Conditions.",
         "doi.org/10.1016/j.crm.2020.100233"),
        ("Neumann et al. 2021.  Climatic Change.",
         "Climate effects on US infrastructure: the economics of adaptation for rail, roads, and coastal development.",
         "doi.org/10.1007/s10584-021-03179-w"),
        ("Rennert et al. 2022.  Nature.",
         "Comprehensive evidence implies a higher social cost of CO₂.",
         "doi.org/10.1038/s41586-022-05224-9"),
        ("Sheahan et al. 2025.  Lancet Planet Health.",
         "Projections of future mortality risk in older adults from high-tide flooding in coastal areas of the USA: an economic modelling study.",
         "doi.org/10.1016/j.lanplh.2025.101382"),
        ("Smith et al. 2024.  Geosci Model Dev.",
         "fair-calibrate v1.4.1: calibration, constraining, and validation of the FaIR simple climate model for reliable future climate projections.",
         "doi.org/10.5194/gmd-17-8569-2024"),
        ("Sweet et al. 2022.  NOAA Tech Rep NOS 01.",
         "Global and Regional Sea Level Rise Scenarios for the United States.",
         "earth.gov/sealevel/us/resources/2022-sea-level-rise-technical-report/"),
        ("Wong 2026.  arXiv preprint.",
         "Modeling the Sea-Level Change from U.S. Vehicle Emissions.",
         "doi.org/10.48550/arXiv.2604.13446"),
    ]
    rx, rw = 24, 21.5
    ry, rh = Y(0.5), Hs(4.0)
    ax.add_patch(Rectangle((rx, ry), rw, rh, linewidth=1.0,
                           edgecolor="#999999", facecolor="#FAFAFA", zorder=1))
    ax.text(rx + 0.3, ry + rh - 0.3, "L. REFERENCES",
            fontsize=10, fontweight="bold", color="#777", va="top", ha="left",
            zorder=5)
    ref_paras = []
    for preamble, title, doi in refs:
        text = f"{preamble}  {title}  {doi}"
        ref_paras.append(textwrap.fill(text, width=200, subsequent_indent="     "))
    refs_text = "\n".join(ref_paras)
    ax.text(rx + 0.4, ry + rh - 0.85, refs_text,
            ha="left", va="top", fontsize=7.0, color="#222",
            family="DejaVu Sans", linespacing=1.30, zorder=4)

    if print_mode:
        # No wireframe banner, no tight_layout/bbox trim — keep the exact
        # 46 × total_h trim size. 300-DPI PNG; vector PDF with embedded fonts.
        fig.savefig(OUT / f"{out_stem}.png", dpi=300)
        fig.savefig(OUT / f"{out_stem}.pdf")
        plt.close(fig)
        print(f"wrote PRINT MASTER {OUT / out_stem}.{{png,pdf}}  "
              f"(46 × {total_h:g} in; PNG 300 DPI = {int(46*300)}×{int(total_h*300)} px)")
    else:
        fig.suptitle(wireframe_label, fontsize=14, fontweight="bold",
                     color=EDGE, y=0.99)
        fig.tight_layout()
        fig.savefig(OUT / f"{out_stem}.png", dpi=200, bbox_inches="tight")
        fig.savefig(OUT / f"{out_stem}.pdf", bbox_inches="tight")
        plt.close(fig)
        print(f"wrote {OUT / out_stem}.{{png,pdf}}")


def main():
    # 46" × 46" square (canonical).
    build(total_h=46.0, title_h=5.0, out_stem="layout_mockup",
          wireframe_label='46" × 46" POSTER LAYOUT WIREFRAME  —  AGU Chapman SLR conference, draft',
          compact_header=False)
    # 46" wide × 42" high (height cap for some print-on-demand sites).
    build(total_h=42.0, title_h=2.8, out_stem="layout_mockup_42in",
          wireframe_label='46" wide × 42" high POSTER LAYOUT WIREFRAME  —  AGU Chapman SLR conference, draft',
          compact_header=True)
    # PRINT MASTER — 46 wide × 42 high only (42 in is the hard height cap).
    # Full physical size, 300 DPI, no wireframe banner, fonts embedded.
    build(total_h=42.0, title_h=2.8, out_stem="poster_print_46x42",
          wireframe_label="", compact_header=True, print_mode=True)


if __name__ == "__main__":
    main()
