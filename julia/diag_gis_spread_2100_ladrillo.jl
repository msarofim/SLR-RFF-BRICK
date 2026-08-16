## ============================================================================
## diag_gis_spread_2100_ladrillo.jl — the G4 scenario spread ON THE POSTERIOR
##
## G4 (the pre-registered Greenland evaluation gate) is the 2100 SSP1-2.6 ->
## SSP5-8.5 spread of the Greenland component, in cm relative to 1995-2014.
## Until now it has only ever been evaluated at a POINT: the offline cell's
## converged optimum (python/gis_offline_cell.py, `spread = proj["SSP5-8.5"] -
## proj["SSP1-2.6"]`), which reports A+B at 10.44 cm against the 6.3-7.3 cm
## evaluation band. Handoff 2026-08-13 section 4 item 1 asks for the same number
## on the accepted L10 posterior, because the interpolated ~8.7 cm estimate of
## what the amp(GMST) law would do to it is the weakest number in that note.
##
## WHAT THIS COMPUTES
##   For each posterior draw and each of the three SSPs, the Greenland sea-level
##   contribution at 2100 (cm rel. LADRILLO_REF), and the PER-DRAW spread
##   ssp585 - ssp126. Per-draw is the right pairing: spread is a difference of
##   two runs of the SAME parameter vector, so differencing the marginal
##   quantiles would mix draws and inflate the interval.
##   It also regresses the per-draw spread on that draw's `gis_amp`, which
##   REPLACES the stage-1 "~6.7 cm of spread per unit amp" table the 8.7 cm
##   figure was interpolated off.
##
## HORIZON
##   Runs to 2100, not 2300. Greenland is a forward integration whose only
##   inputs are the regional driver and the gis_* parameters, so the horizon
##   cannot reach back into it; the truncation is GATED here (--check-horizon)
##   by re-running the first draw to 2300 and demanding the 2100 value be
##   bit-identical. Nothing else in this file reads a non-Greenland component.
##
##   julia --project=julia_v2 julia/diag_gis_spread_2100_ladrillo.jl \
##         [n_draws] [--post=<csv>] [--check-horizon] [--no-shape]
## ============================================================================
using CSV, DataFrames, Statistics, Printf

include(joinpath(@__DIR__, "ladrillo_projection.jl"))

const POSTERIOR_CSV = let i = findfirst(a -> startswith(a, "--post="), ARGS)
    i === nothing ?
        joinpath(LADRILLO_REPO, "data/MimiBRICK/parameters_subsample_brick_mengel_L10.csv") :
        ARGS[i][8:end]
end
const NTHIN = let p = findfirst(a -> !startswith(a, "--"), ARGS)
    p === nothing ? 1000 : parse(Int, ARGS[p])
end
const CHECK_HORIZON = "--check-horizon" in ARGS
## --no-shape reverts to the CONSTANT-amp splice, i.e. the model as calibrated,
## which is what the 10.44 cm offline point estimate was computed on. Run both to
## read off what the amp(GMST) law actually buys.
const GIS_SHAPE = !("--no-shape" in ARGS)
const Y0, Y1     = 1850, 2100
const PROJ_YEAR  = 2100
## G4 band, verbatim from gis_offline_cell.GATE_SPREAD_RANGE_CM. The comparison
## arms behind it: MAGICC-SLR 7.09, FACTS FittedISMIP 6.34, emuGrIS 7.26,
## bamber19 7.23 (outputs/ladrillo_model_comparison_L10_spread.csv).
const GATE_SPREAD_RANGE_CM = (6.3, 7.3)
## The two scenarios the gate is defined on, plus the reported middle.
const SSP_LO, SSP_HI = "ssp126", "ssp585"
const SSPS = [(SSP_LO, "SSP1-2.6"), ("ssp245", "SSP2-4.5"), (SSP_HI, "SSP5-8.5")]
## The arm is IN THE FILENAME: constant-amp, the default shape, and any
## sensitivity shape selected with LADRILLO_GIS_SHAPE all write different files,
## so a sensitivity arm cannot silently overwrite the deliverable's numbers.
const ARM = !GIS_SHAPE ? "_constamp" :
    LADRILLO_GIS_SHAPE_STEM == "gis_amp_shape" ? "" :
    "_" * replace(LADRILLO_GIS_SHAPE_STEM, "gis_amp_shape_" => "")
const OUT = joinpath(LADRILLO_REPO, "outputs/diag_gis_spread_2100_ladrillo$(ARM).csv")

## ---- variant first, THEN the model (see diag_slr_convergence_by_chain_ladrillo) --
isfile(POSTERIOR_CSV) || error("missing posterior $POSTERIOR_CSV")
const HDR = String.(propertynames(CSV.read(POSTERIOR_CSV, DataFrame; limit = 0)))
const VARIANT = ladrillo_gis_variant(HDR)
post = ladrillo_posterior(path = POSTERIOR_CSV, nthin = NTHIN)

@printf("Ladrillo G4 scenario spread on the posterior\n")
@printf("  posterior %s (%d draws) | Greenland :%s | %d-%d | base %d-%d\n",
        basename(POSTERIOR_CSV), nrow(post), VARIANT, Y0, Y1,
        LADRILLO_REF[1], LADRILLO_REF[2])
@printf("  amp law %s%s\n", GIS_SHAPE ? "ON" : "OFF (constant-amp splice, the model as calibrated)",
        GIS_SHAPE ? @sprintf(": S anchored at dT_eff = %.3f K, %d-yr warming-level window",
                             LADRILLO_GIS_SHAPE_ANCHOR_DT, LADRILLO_GIS_SHAPE_WIN) : "")
@printf("  G4 band %.1f-%.1f cm (evaluation only, never in the objective)\n\n",
        GATE_SPREAD_RANGE_CM...)

gis = Dict(ssp => Vector{Float64}(undef, nrow(post)) for (ssp, _) in SSPS)
for (ssp, label) in SSPS
    bf = ladrillo_setup(ssp = ssp, y0 = Y0, y1 = Y1, gis_ab = VARIANT === :ab,
                        gis_shape = GIS_SHAPE)
    iy = ladrillo_yi(bf, PROJ_YEAR)
    t0 = time()
    for (j, r) in enumerate(eachrow(post))
        ladrillo_run_draw!(bf, r)
        gis[ssp][j] = ladrillo_series(bf, :gis)[iy]
        j % 250 == 0 && (print("."); flush(stdout))
    end
    @printf("\n%-9s %d draws in %.0fs | GIS@%d med %.2f cm\n",
            label, nrow(post), time() - t0, PROJ_YEAR, median(gis[ssp]))

    if CHECK_HORIZON && ssp == SSP_HI
        bf3 = ladrillo_setup(ssp = ssp, y0 = Y0, y1 = 2300, gis_ab = VARIANT === :ab,
                             gis_shape = GIS_SHAPE)
        ladrillo_run_draw!(bf3, first(eachrow(post)))
        v3 = ladrillo_series(bf3, :gis)[ladrillo_yi(bf3, PROJ_YEAR)]
        bf1 = ladrillo_setup(ssp = ssp, y0 = Y0, y1 = Y1, gis_ab = VARIANT === :ab,
                             gis_shape = GIS_SHAPE)
        ladrillo_run_draw!(bf1, first(eachrow(post)))
        v1 = ladrillo_series(bf1, :gis)[ladrillo_yi(bf1, PROJ_YEAR)]
        @printf("  [horizon gate] draw 1 GIS@%d: y1=2100 %.12f vs y1=2300 %.12f  %s\n",
                PROJ_YEAR, v1, v3, v1 == v3 ? "IDENTICAL PASS" : "DIFFER FAIL")
        v1 == v3 || error("horizon truncation changes GIS@$PROJ_YEAR")
    end
end

spread = gis[SSP_HI] .- gis[SSP_LO]
q(v, p) = quantile(v, p)

df = DataFrame(draw = 1:nrow(post), gis_amp = Float64.(post.gis_amp),
               gis126 = gis[SSP_LO], gis245 = gis["ssp245"], gis585 = gis[SSP_HI],
               spread = spread)
CSV.write(OUT, df)

@printf("\n%-10s %8s %8s %8s %8s\n", "quantity", "q05", "q50", "q95", "mean")
for (ssp, label) in SSPS
    v = gis[ssp]
    @printf("%-10s %8.2f %8.2f %8.2f %8.2f\n", label, q(v, .05), q(v, .5), q(v, .95), mean(v))
end
@printf("%-10s %8.2f %8.2f %8.2f %8.2f  <- G4\n",
        "spread", q(spread, .05), q(spread, .5), q(spread, .95), mean(spread))

inband = count(s -> GATE_SPREAD_RANGE_CM[1] <= s <= GATE_SPREAD_RANGE_CM[2], spread)
@printf("\nG4: median spread %.2f cm vs band %.1f-%.1f  ->  %s\n",
        median(spread), GATE_SPREAD_RANGE_CM...,
        GATE_SPREAD_RANGE_CM[1] <= median(spread) <= GATE_SPREAD_RANGE_CM[2] ?
            "IN BAND" : median(spread) > GATE_SPREAD_RANGE_CM[2] ? "ABOVE BAND" : "BELOW BAND")
@printf("    %d/%d draws (%.1f%%) fall inside the band\n",
        inband, nrow(post), 100 * inband / nrow(post))

## ---- spread vs the draw's own amplification --------------------------------
## The stage-1 "~6.7 cm per unit amp" table was an amp SCAN at a single
## parameter vector. This is the posterior's own slope: what a draw's gis_amp
## buys in spread with every other parameter varying with it.
a = Float64.(post.gis_amp)
sl = cov(a, spread) / var(a)
ic = mean(spread) - sl * mean(a)
r = cor(a, spread)
@printf("\nspread = %.3f + %.3f * gis_amp   (r = %.3f, amp p05/p50/p95 %.3f/%.3f/%.3f)\n",
        ic, sl, r, q(a, .05), q(a, .5), q(a, .95))
@printf("  -> a shift of amp from %.3f to X moves the median spread by %.3f cm per unit\n",
        median(a), sl)
@printf("\nwrote %s\n", OUT)
