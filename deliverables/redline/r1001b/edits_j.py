"""10-01b edit set J: structure (Marcus 10-01). Greenland equations, the likelihood, a Verification subsection,
Table A3 (fixed values), numbered sentence-case headings, the back matter moved after the Appendix
(Copernicus order: Conclusions, Appendices, Code availability, ..., Financial support, References), and the
two new references. Equations are transcribed from the code (julia/greenland_3basin_component.jl:300-411,
julia/calibrate_mcmc_ext.jl:176-185, 1664-1880, run_mcmc_L27.sh flags) and spot-checked line by line."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from trackedit import Doc
import extra  # noqa: F401
d = Doc(sys.argv[1] + "/word/document.xml")


def eqlines(rows, col=72):
    """Monospace equation lines with the number right-aligned at a common column (SourceCode style)."""
    out = []
    for i, (lhs, num) in enumerate(rows):
        if i:
            out.append(("", "br"))
        out.append((lhs + " " * max(2, col - len(lhs)) + num, "code"))
    return out


# ---- Greenland equations (Sect. 2.2.2) -----------------------------------------------------------------
d.insert_paras_after_prefix("Above-threshold discharge channel.", [
    ("BodyText", [("Greenland equations.", "b"),
                  (" Each basin b carries a surface-mass-balance (SMB) state F_b and a discharge state D_b (m SLE), "
                   "updated annually from the regional temperature of the previous year, T_t−1 (K relative to 1850–1900):", "")]),
    ("SourceCode", eqlines([
        ("E_b(T)   = min( max( k_b·(c₁·T + c₀), 0 ), k_b·V₀ )", "(3)"),
        ("r_j,b(T) = min( max( s_b·(α_j·T + β_j), 10⁻⁹ ), 1 ),   j ∈ {f, s}", "(4)"),
        ("F_b(t)   = F_b(t−1) + [ f·E_b(T_t−1) − F_b(t−1) ] · r_f,b(T_t−1)", "(5)"),
        ("D_b(t)   = D_b(t−1) + [ (1 − f)·E_b(T_t−1) − D_b(t−1) ] · r_s,b(T_t−1)", "(6)"),
        ("GIS(t)   = Σ_b [ F_b(t) + D_b(t) ] + P(t)", "(7)"),
    ], col=72)),
    ("BodyText", [(
        "E_b is the basin's committed loss: linear in temperature, with sensitivity c₁ and intercept c₀, and capped at "
        "the basin's share k_b of the sheet's volume V₀ = 7.42 m SLE (Morlighem et al., 2017). f is the SMB share of "
        "the committed loss. The basin shares (0.629 active, 0.371 high) are the sector volumes of Mouginot et al. "
        "(2019). The rate scale s_b is 1 for the active basin, the reference, and is sampled as log₁₀ s_b for the "
        "high basin. The discharge rates are sampled as a level and a tilt at the reference temperature T̄ = 1.963 K "
        "(the 2015–2024 mean of the regional driver): ℓ = ln r_s(T̄) and w = α_s·T̄ / r_s(T̄), so that "
        "α_s = w·e^ℓ / T̄ and β_s = (1 − w)·e^ℓ; the discharge channel is required to be the slower of the two "
        "(α_s ≤ α_f and β_s ≤ β_f). Both states are zero in 1850. Through 2024 the regional temperature T is the "
        "observed series; after 2024 it is a·S(Ḡ₃₀(t))·G(t) plus the constant that matches the 2014–2024 mean of the "
        "observations, where G is GMST, a the sampled amplification and S the CMIP6 decline of the amplification "
        "with warming, normalised to 1 at the anchor warming (0.94 K) and evaluated on the 30-year running mean of "
        "GMST, Ḡ₃₀. In calibration this splice is built once with the prior-centre amplification (1.92), so the "
        "sampled a does not enter the calibration likelihood: its posterior is its prior, propagated into the "
        "projections.", "")]),
    ("BodyText", [("The above-threshold channel P is switched on in projections only:", "")]),
    ("SourceCode", eqlines([
        ("u(t)  = min( max( (G(t−1) − T_on) / w_r, 0 ), 1 )", "(8)"),
        ("q₁(t) = q₁(t−1) + [ u(t) − q₁(t−1) ] · n/τ", "(9)"),
        ("q₂(t) = q₂(t−1) + [ q₁(t−1) − q₂(t−1) ] · n/τ", "(10)"),
        ("P(t)  = min( V·q₂(t), max( V₀ − Σ_b [ F_b(t) + D_b(t) ], 0 ) )", "(11)"),
    ], col=72)),
    ("BodyText", [(
        "with onset T_on = 4.69 K of GMST relative to 1850–1900, ramp width w_r = 1 K, n = 2 stages, total delay "
        "τ = 800 yr and volume V = 5.64 m SLE; q₁ = q₂ = 0 in 1850. The clamp in Eq. (11) keeps total Greenland loss "
        "within the sheet's volume.", "")]),
], why="GMD: model must be re-implementable from the text (Marcus 10-01)")

# ---- the likelihood (Sect. 3.2) -------------------------------------------------------------------------
d.insert_paras_after_prefix("Discrepancy terms.", [
    ("BodyText", [("Likelihood.", "b"),
                  (" Each of the four scored series i (Antarctica, Greenland, glaciers and thermal expansion; total sea "
                   "level is not scored) contributes one multivariate-normal term on its residual vector r_i, model minus "
                   "observation in cm, both relative to 1995–2005, over the years with observations (1900–2025; "
                   "glaciers to 2023):", "")]),
    ("SourceCode", eqlines([
        ("ln L_i   = ln N( r_i ; 0, Σ_i )", "(12)"),
        ("(Σ_i)_jk = σ_i²·ρ_i^|j−k| / (1 − ρ_i²) + ε_j·ε_k·exp( −|j − k| / L )", "(13)"),
        ("ln p(θ)  = Σ_i ln L_i + Σ_m ln L_m + ln π(θ)", "(14)"),
    ])),
    ("BodyText", [(
        "The first part of Σ_i is a stationary AR(1) process with innovation standard deviation σ_i and lag-1 "
        "autocorrelation ρ_i, which represents the residual structure the model cannot; the second is the "
        "observational error, ε_t being the published 90% range divided by 2 × 1.645 (at least 0.05 cm), correlated "
        "with an e-folding length of L = 100 yr. σ_i has a half-normal N⁺(0, 5 cm) prior and ρ_i is uniform on "
        "[0, 0.99). For thermal expansion r_i includes the discrepancy term above. The L_m are Gaussian constraints on "
        "single quantities: the Antarctic SMB anchor (Table 3, note 17), the remaining glacier ice at 2000, the "
        "Leclercq 1850–1900 glacier loss, the GlacierMIP3 committed-loss fractions (correlated across warming "
        "levels), the two GlaMBIE constraints, and the Mouginot SMB share and sector shares. π(θ) is the product of "
        "the priors in Table A1.", "")]),
], why="GMD: model must be re-implementable from the text (Marcus 10-01)")

# ---- Verification (Sect. 3.3), before Results ---------------------------------------------------------
d.insert_paras("Results:", [
    ("Heading2", [("3.3 Verification", "")]),
    ("BodyText", [(
        "Verification here means checking that the code computes what Eqs. (1)–(14) specify; agreement with the "
        "observations is evaluated separately in Sect. 4. The Antarctic ice-sheet and thermal-expansion components are "
        "MimiBRICK v2.0.0's own code, run unmodified with Ladrillo's parameter values. The new glacier and Greenland "
        "components are covered by a ten-step test suite, which passes on the code version described here. It checks "
        "that (i) the calibration inputs rebuilt from the raw data equal the committed input files; (ii) the glacier "
        "component, as called by both the calibration code and the projection code, and the Greenland component "
        "reproduce independent Python implementations of Eqs. (1)–(6) to within 10⁻⁹, and the Greenland projection "
        "agrees with the Python implementation to within 0.1 cm at 2100; (iii) the components nest: the two-basin "
        "Greenland component reduces to the one-basin form when both basins share the same rates, the basins sum to "
        "the whole sheet, and with V = 0 the above-threshold channel leaves every projection unchanged; and (iv) re-running a posterior draw reproduces it bit for bit. Each identity test is paired with "
        "a deliberate error that it must detect, so that a test which cannot fail is caught. The level-and-tilt form "
        "of the discharge rates is checked against the native form, to 10⁻¹², each time the calibrator starts. The "
        "calibrator itself is verified by re-running the first 300 iterations of the production chain from the same "
        "seed and requiring every sampled value and log-posterior value to equal the production chain exactly. The "
        "suite does not run the complete model with the new components reverted against BRICK 2.0.", "")]),
], before=True, why="GMD separates verification from evaluation (Marcus 10-01)")
d.insert_paras("Calibration Data Updates", [("Heading1", [("3 Calibration and verification", "")])], before=True,
               why="new parent section")

# ---- Table A3 (fixed values) at the end of Appendix A ---------------------------------------------------
d.insert_paras("References", [
    ("FirstParagraph", [("Table A3.", "b"),
                        (" Fixed (non-sampled) values. Greenland symbols as in Eqs. (3)–(11), likelihood symbols as in "
                         "Eqs. (12)–(13).", "")]),
], before=True, why="GMD: tabulate the fixed values (Marcus 10-01)")
d.insert_table_after_prefix("Table A3.", [
    ["symbol", "fixed quantity", "value", "source"],
    ["V₀", "Greenland ice volume, the cap on committed loss", "7.42 m SLE", "Morlighem et al. (2017)"],
    ["k_b", "Basin shares of V₀ (active, high)", "0.629, 0.371", "Mouginot et al. (2019) sector volumes"],
    ["s_b", "Rate scale of the active (reference) basin", "1", "Only the ratio to the high basin is identified"],
    ["T̄", "Reference temperature of the discharge-rate level and tilt", "1.963 K", "2015–2024 mean of the regional driver"],
    ["F_b, D_b (1850)", "Greenland states at the start", "0", "Not identified separately from c₀"],
    ["–", "Bounds on the Greenland rates r", "10⁻⁹ to 1 yr⁻¹", "Numerical"],
    ["T_on, V", "Above-threshold onset (GMST) and volume", "4.69 K, 5.64 m SLE", "ISMIP6 and SICOPOLIS (Sect. 2.2.2)"],
    ["τ, n, w_r", "Above-threshold delay, stages, ramp width", "800 yr, 2, 1 K", "ISMIP6 and SICOPOLIS (Sect. 2.2.2)"],
    ["–", "Anchor warming of the Greenland amplification shape S", "0.94 K (30-yr mean GMST)", "CMIP6 (Sect. 2.2.2)"],
    ["ν", "Glacier response exponent (SLOWG, FASTG, RGI 19)", "1.622, 1.567, 1.545",
     "Reproduces each block's GlacierMIP3 half-response time at +1.5 and +3.0 K"],
    ["λ, T_crit", "DAIS fast-dynamics rate and threshold",
     "Calibration: 0.00991 m yr⁻¹, −15.67 °C; projection: joint draws", "Paleo ensemble (Wong et al., 2017a)"],
    ["γ", "DAIS ice-flow exponent", "2.83", "Paleo median (Wong et al., 2017a)"],
    ["T_ant,0", "Antarctic temperature at zero GMST anomaly", "−18.44 °C", "BRICK 2.0 (−15.42/0.8365)"],
    ["ρ_ice, ρ_sw, ρ_rock", "DAIS densities", "917, 1030, 4000 kg m⁻³", "BRICK 2.0 (Shaffer, 2014)"],
    ["R₀", "DAIS reference radius", "1.864 × 10⁶ m", "BRICK 2.0 (Shaffer, 2014)"],
    ["–", "Area scaling of the Rignot SMB anchor", "10.92/12.295 = 0.888", "Table 3, note 17"],
    ["A, C, ρ", "Ocean area, heat capacity and density (thermal expansion)",
     "3.619 × 10¹⁴ m², 3991.87 J kg⁻¹ K⁻¹, 1027 kg m⁻³", "BRICK 2.0"],
    ["L", "Correlation length of the observational error", "100 yr", "Eq. (13)"],
    ["–", "Upper bound on ρ_i; floor on ε_t", "0.99; 0.05 cm", "Eq. (13)"],
    ["–", "Reference periods: hindcast and likelihood; projections", "1995–2005; 1995–2014", ""],
    ["–", "Land-water storage in projections", "Observed series to 2023, then 0.30 mm yr⁻¹", "Sect. 2.2.5"],
], widths=[1500, 3360, 2400, 2100], why="new Table A3")

# ---- references --------------------------------------------------------------------------------------
d.insert_paras_after_prefix("Frederikse, T., Landerer", [(None, [(
    "Fretwell, P., Pritchard, H. D., Vaughan, D. G., Bamber, J. L., Barrand, N. E., Bell, R., Bianchi, C., Bingham, "
    "R. G., Blankenship, D. D., Casassa, G., Catania, G., Callens, D., Conway, H., Cook, A. J., Corr, H. F. J., "
    "Damaske, D., Damm, V., Ferraccioli, F., Forsberg, R., Fujita, S., Gim, Y., Gogineni, P., Griggs, J. A., "
    "Hindmarsh, R. C. A., Holmlund, P., Holt, J. W., Jacobel, R. W., Jenkins, A., Jokat, W., Jordan, T., King, E. C., "
    "Kohler, J., Krabill, W., Riger-Kusk, M., Langley, K. A., Leitchenkov, G., Leuschen, C., Luyendyk, B. P., "
    "Matsuoka, K., Mouginot, J., Nitsche, F. O., Nogi, Y., Nost, O. A., Popov, S. V., Rignot, E., Rippin, D. M., "
    "Rivera, A., Roberts, J., Ross, N., Siegert, M. J., Smith, A. M., Steinhage, D., Studinger, M., Sun, B., "
    "Tinto, B. K., Welch, B. C., Wilson, D., Young, D. A., Xiangbin, C., and Zirizzotti, A.: Bedmap2: improved ice "
    "bed, surface and thickness datasets for Antarctica, The Cryosphere, 7, 375–393, "
    "https://doi.org/10.5194/tc-7-375-2013, 2013.", "")])], why="Crossref-verified 10-01")
d.insert_paras_after_prefix("Morice, C. P.", [(None, [(
    "Morlighem, M., Williams, C. N., Rignot, E., An, L., Arndt, J. E., Bamber, J. L., Catania, G., Chauché, N., "
    "Dowdeswell, J. A., Dorschel, B., Fenty, I., Hogan, K., Howat, I., Hubbard, A., Jakobsson, M., Jordan, T. M., "
    "Kjeldsen, K. K., Millan, R., Mayer, L., Mouginot, J., Noël, B. P. Y., O'Cofaigh, C., Palmer, S., Rysgaard, S., "
    "Seroussi, H., Siegert, M. J., Slabon, P., Straneo, F., van den Broeke, M. R., Weinrebe, W., Wood, M., and "
    "Zinglersen, K. B.: BedMachine v3: Complete bed topography and ocean bathymetry mapping of Greenland from multibeam "
    "echo sounding combined with mass conservation, Geophys. Res. Lett., 44, 11051–11061, "
    "https://doi.org/10.1002/2017GL074954, 2017.", "")])], why="Crossref + OpenAlex verified 10-01")

# ---- the 10-01 cross-reference inside Claude's own earlier insertion -------------------------------------
d.revise_own_ins("see Future Projections", "Future Projections", "Sect. 4.2", "section number")

# ---- headings: numbered, sentence case, Heading styles (GMD: 3 levels, sentence case) --------------------
for old, new, lvl in [
    ("Introduction", "1 Introduction", 1),
    ("Framework Design", "2 Framework design", 1),
    ("Overall structure", "2.1 Overall structure", 2),
    ("Five component modules", "2.2 Five component modules", 2),
    ("Glaciers", "2.2.1 Glaciers", 3),
    ("Greenland Ice Sheet", "2.2.2 Greenland ice sheet", 3),
    ("Antarctic Ice Sheet", "2.2.3 Antarctic ice sheet", 3),
    ("Thermal Expansion", "2.2.4 Thermal expansion", 3),
    ("Land water storage", "2.2.5 Land water storage", 3),
    ("Calibration Data Updates", "3.1 Calibration data updates", 2),
    ("Model code and calibration", "3.2 Model code and calibration", 2),
    ("Results:", "4 Results", 1),
    ("Comparisons to Observations", "4.1 Comparisons to observations", 2),
    ("Future Projections", "4.2 Future projections", 2),
    ("Comparisons for high, low, and peak-and-decline scenarios",
     "4.3 Comparisons for high, low, and peak-and-decline scenarios", 2),
    ("Conclusions:", "5 Conclusions", 1),
    ("Appendix A: prior and posterior parameter distributions",
     "Appendix A: Prior and posterior parameter distributions, and fixed values", 1),
    ("References", "References", 1),
]:
    d.heading(old, new, lvl, "GMD sectioning")

# ---- back matter after the Appendix (Copernicus order) ----------------------------------------------------
d.move_block("Code and data availability", "Appendix A: Prior and posterior parameter distributions, and fixed values",
             "References",
             retitle={"Author contributions. ": "Author contributions", "Competing interests. ": "Competing interests",
                      "Acknowledgments. ": "Acknowledgements", "Financial support. ": "Financial support"},
             restyle={"Code and data availability": "Heading1", "Author contributions. ": "Heading1",
                      "Competing interests. ": "Heading1", "Acknowledgments. ": "Heading1",
                      "Financial support. ": "Heading1"},
             why="GMD: Appendices precede Code availability ... Financial support, References")
d.edit_own_ins("Tessa Moeller", "Tessa Möller", "Marcus 10-01 (inside the moved copy)")
d.edit_own_ins("regional-temperature drivers are included in the archive.",
               "regional-temperature drivers are included in the archive. A user manual (installation, running the "
               "calibration and projections, input formats) is in preparation and will be included in the archive.",
               "Marcus 10-01: pointer to the manual (inside the moved copy)")

d.save()
for o, n, w in d.log:
    print(f"- {o[:60]!r} -> {n[:70]!r}")
print(len(d.log), "edits")
