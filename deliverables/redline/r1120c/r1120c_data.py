"""Round r1120c edits (2026-11-20) on Marcus's 10:02 save of GMD.Ladrillo.v1.2026-11-20b.clean.docx (frozen here as
base_marcus_2026-11-20_1002.docx, md5 a93fb35c; all comments deleted; three tracked marks of his own, kept as they are).
Marcus 11-20 (his notes + AskUserQuestion): draw count, symbols, text-vs-table names, Table 2's BRICK 2.0 inventory on
the s0-inclusive basis, Table 4 caption, Table 1 n.d., SICOPOLIS 3000, RGI 19 wording.

EDITS:   (context occurring once in one plain run, old text inside it, new text, why)       author "Claude"
INSERTS: (context, prefix of the context, text inserted after the prefix, why)               author "Claude"
NOTATION (symbol renames) is in notation_r1120c.py, author "Claude (notation)".
TEXT_NOTATION: the same renames as string edits on the pandoc text (sub/superscripts written _(x) / ^(x)), for G3.
"""

# BRICK 2.0's glacier inventory at 2000 counted as its melt law counts it: v0 - s0 - melt(1850-2000), all 10,000 draws.
# SLR-RFF-BRICK julia/diag_brick_gsic_melt_1850_2000.jl (2026-11-20 rows): remaining_at_2000_s0incl_cm 35.74
# (23.68-48.52); glaciers_v0_cm 41.52 (32.00-51.81); glaciers_s0_cm 1.92 (-4.56 to 7.36); melt 4.05.
EDITS = [
    ("the 10,000-member posterior used for projection", " used for projection",
     "; projections use every fifth draw (2,000)", "draw count (Marcus 11-20)"),
    ("RGI 19, the one glacier block with no target of its own, would", "the one glacier block with no target of its own",
     "constrained only by a weak GlaMBIE rate", "RGI 19 wording (Marcus 11-20, AskUserQuestion)"),
    ("read from its code. n.d. = not documented in SLEIP. GMST", " n.d. = not documented in SLEIP.", "",
     "Table 1 uses no n.d. (Table 2 defines it)"),
    ("SICOPOLIS at 2300 and 3001", "3001", "3000", "match Greve and Chambers's title (Marcus 11-20)"),
    ("37.4 (28–48)", "37.4 (28–48)", "35.7 (24–49)", "BRICK 2.0 inventory, s0-inclusive (Marcus 11-20)"),
    ("Calibrated initial volume 42 cm (5–95 % 32–52) at the 1850 start, reduced by 4.0 cm of melt by 2000.",
     "Calibrated initial volume 42 cm (5–95 % 32–52) at the 1850 start, reduced by 4.0 cm of melt by 2000.",
     "Calibrated volume 41.5 cm (5–95 % 32.0–51.8), less the 1850 starting value of BRICK 2.0’s glacier term (median "
     "1.9 cm, 5–95 % −4.6 to 7.4), which its melt equation counts against that volume, and 4.0 cm of modelled melt over "
     "1850–2000.", "note a on the s0-inclusive basis"),
]

INSERTS = [
    ("against Dangendorf et al. (2024), all in cm", "against Dangendorf et al. (2024)",
     ", extended with NOAA STAR altimetry over 2022–2024", "Table 4 caption: the total's 2022-2024 values"),
]

# For G3: the notation pass as edits on the pandoc text. (context, old, new, expected count of context)
TEXT_NOTATION = [
    ("κ_(DAIS)", "κ_(DAIS)", "κ_(P)", 2),
    ("·T̄ (T̄ = −17.99", "·T̄ (T̄ = −17.99", "·T̄_(A) (T̄_(A) = −17.99", 1),
    ("T̄ Reference temperature of the discharge-rate level and tilt", "T̄ ", "T_(ref) ", 1),
    ("amplification shape S 0.94 K", "shape S", "shape φ", 1),
    ("τ, n, w_(r)", "w_(r)", "ΔT_(r)", 1),
]
BLOCK_PARA = ("Each block b is driven by its own regional temperature", "stays close to its prior (Table A1).")
N_BLOCK_SUB = 10
