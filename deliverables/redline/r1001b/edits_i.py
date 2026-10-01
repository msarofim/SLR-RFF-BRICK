"""10-01b edit set I: Marcus's 10-01 instructions, text edits only (tracked, w:date 2026-10-01T20:00:00Z).
Receipts: outputs/diag_te_rate_attribution_L27.csv (matched-span rates, 1993-2025), scorecard / IC relabel
(values unchanged), outputs/diag_ais_flux_split_vs_imbie_draws_L27.csv (SMB reweighting), Fretwell et al.
2013 Table 7 (12.295e6 km2 = Bedmap2 grounded area), Rignot et al. 2019 Table 1 (12,353 incl. islands)."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from trackedit import Doc
import extra  # noqa: F401  (adds methods)
d = Doc(sys.argv[1] + "/word/document.xml")

# ---- observation windows end in 2025 (Marcus 10-01) -------------------------------------------------
d.replace("over the 1900–2026 record", "over the 1900–2025 record", "obs end 2025")
d.replace("the 1900–2026 record therefore constrains", "the 1900–2025 record therefore constrains", "obs end 2025")
d.replace("held constant through 2026 in the hindcast", "held constant through 2025 in the hindcast", "obs end 2025")
d.replace("the 2023 value is held constant through 2026)", "the 2023 value is held constant through 2025)", "obs end 2025")
d.replace("fit window runs to 2026, so its last three years", "fit window runs to 2025, so its last two years",
          "splice at 2023.5: scored years 2024-2025 are scenario-driven")
d.replace("Component hindcasts against the observations, 1900–2026", "Component hindcasts against the observations, 1900–2025",
          "FIG 1 re-rendered to 2025")
d.replace_after("RMSE of the Ladrillo median against the observations", "1993–2026", "1993–2025",
                "Table 4 header; scorecard re-run, values identical")
d.replace("Antarctica over 1993–2026", "Antarctica over 1993–2025", "obs end 2025")
d.replace("N = 502 observation-years, 1900–2026", "N = 502 observation-years, 1900–2025", "IC re-run, N unchanged")
d.replace("the 1993–2026 overshoot discussed under Results", "the 1993–2025 overshoot discussed in Sect. 4.1",
          "obs end 2025; section number")
d.replace("overestimate the 1993–2026 thermal-expansion rate (Ladrillo 1.23×, BRICK 2.0 1.17×)",
          "overestimate the 1993–2025 thermal-expansion rate (Ladrillo 1.22×, BRICK 2.0 1.16×)",
          "diag_te_rate_attribution_L27.csv, matched spans (was model to 2026 vs obs to 2025)")
d.replace("over that period is 1.24–1.29× the observed 0–2000 m products the target is built from.",
          "over that period is 1.21–1.27× the observed 0–2000 m products the target is built from (IGCC's record ends in 2024).",
          "FaIR/IGCC 1.215 (1993-2024), FaIR/Cheng 1.274 (1993-2025)")
d.revise_own_ins("when FaIR's uptake is 1.22× IGCC's", "1.22×", "1.21×", "1.2148 rounds to 1.21 (= 1.10 x 1.10); inside the 10-01 insertion")

# ---- deletions Marcus asked for ---------------------------------------------------------------------
d.replace(" and BRICK 2.0 runs slightly high:", ":", "Marcus 10-01: delete")
d.replace("(the mean over 2022-2024 relative", "(the mean over 2022–2024 relative", "en dash")
d.delete("; thermal expansion ties by construction (same module, same ocean-heat driver)", "Marcus 10-01: delete")

# ---- profiled noise (body accurate, caption was not) and the 1,600-draw diagnostic -------------------
d.replace("with noise scale and autocorrelation profiled per series for both models",
          "with the noise scale σ and autocorrelation ρ re-fitted (profiled) to each posterior draw's residuals, "
          "separately for each of the four series and identically for both models",
          "ic_ladrillo_vs_brick20.py:35-36, 206-248, 323-325")
d.replace("plus each posterior's four (σ, ρ) noise pairs under AR(1) (50 / 35)",
          "plus, under AR(1), four (σ, ρ) noise pairs, one per series, re-fitted (profiled) to each draw's residuals "
          "rather than taken from the posterior (50 / 35)", "the caption said the posterior's own pairs were used")
d.replace("with an effective sample size of about 1240 on the 1,600 thinned draws used for the diagnostic).",
          "with effective sample sizes of about 1,240 and 1,250). That diagnostic uses its own subsample of 400 draws "
          "from each chain (every 2,500th post-burn-in iteration, 1,600 in total), each run through the SSP2-4.5 "
          "projection; the parameter-level R̂ and effective sample sizes above are computed on all 4,000,000 "
          "post-burn-in iterations.",
          "diag_slr_convergence_by_chain_ladrillo.jl :42-43, :119-121; log ESS 1238.5 / 1249.4; postprocess_mcmc_ext.jl:83")
d.replace("couples to any reduced-complexity climate model that produces both GMST and ocean heat content",
          "is designed to run off any model that produces annual time series of both GMST and ocean heat content",
          "Marcus 10-01 wording")

# ---- leftovers --------------------------------------------------------------------------------------
d.replace("with the same cubes, splice pivot, and pair seed;",
          "with identical forcing and the same pairing of posterior draws to configurations;", "internal wording")
d.replace("can't", "cannot", "contraction")
d.replace("(1.3x larger difference", "(1.3× larger difference", "×")
d.replace("and Greenland (3x)", "and Greenland (3×)", "×")
d.replace("within about 8 % in every", "within about 8% in every", "unit spacing")
d.replace("warming below 2000m", "warming below 2000 m", "unit spacing")
d.replace("BRICK is one of the premier sea level rise emulators.", "BRICK is a widely used sea level rise emulator.",
          "value word")
d.replace("holds four times fewer draws under the joint prior than under independent ones",
          "holds a quarter as many draws under the joint prior as under independent ones", "phrasing")
d.replace("for the initial projections years", "for the initial projection years", "typo")
d.replace("N(−1.98, 0.743) on [−1000000000, 1000000000]", "N(−1.98, 0.743), unbounded", "Table A1 bounds")

# ---- Rignot area scaling: say where 12.295 comes from (Marcus 10-01 question) -------------------------
d.replace("the ratio of the DAIS model's idealised ice-sheet area to the grounded area of the published estimate, "
          "giving 1863 ± 118 Gt/yr.",
          "the ratio of the DAIS model's idealised ice-sheet area (π R₀² = 10.92 × 10⁶ km²) to the Bedmap2 grounded-ice "
          "area (12.295 × 10⁶ km²; Fretwell et al., 2013), giving 1863 ± 118 Gt/yr. Rignot et al.'s own basin total "
          "(12.353 × 10⁶ km², which includes the peripheral islands) would give 0.884; reweighting the posterior to that "
          "target moves its 1979–2008 SMB by −9 Gt/yr (0.07 posterior standard deviations).",
          "Fretwell 2013 Table 7; Rignot 2019 Table 1; importance reweighting, ESS 994/1000")

# ---- section cross-references and equation numbers --------------------------------------------------
d.replace("(see Calibration)", "(see Sect. 3.2)", "section number")
d.replace("(see Forcing)", "(see Sect. 3.2)", "section number")
d.replace("see the peak-and-decline discussion below", "see Sect. 4.3", "section number")
d.insert_after("are listed in Appendix A, Table A1", "; fixed values are in Table A3", "new Table A3")
d.insert_after("in the layout of Wong et al. (2017b), Appendix A.",
               " Table A3 lists the values that are fixed rather than sampled.", "new Table A3")
d.insert_after("S_eq = max( a·(1 − exp(−b·(T − T_off))), 0 )        ", " " * 20 + "(1)", "GMD numbers equations")
d.insert_after("dS   = min( κ·|T − T_eq|^ν, 1 ) · (S_eq − S)        ", " " * 20 + "(2)", "GMD numbers equations")

d.save()
for o, n, w in d.log:
    print(f"- {o[:60]!r} -> {n[:70]!r}")
print(len(d.log), "edits")
