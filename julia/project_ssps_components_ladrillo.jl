## ============================================================================
## project_ssps_components_ladrillo.jl — Ladrillo per-component SSP projections
##
## Component-resolved sea-level bands for SSP1-2.6 / SSP2-4.5 / SSP5-8.5 from
## the accepted Ladrillo (extC) posterior, 1990-2300, cm relative to 1995-2014.
## This is the projection deliverable the sharing memo's SSP section and every
## comparison arm (FACTS, MAGICC, pre-Mengel BRICK 2.0) read.
##
## Basis
##   posterior : data/MimiBRICK/parameters_subsample_brick_mengel_<TAG>.csv,
##               --tag=, default L10 (Ladrillo 1.0, 4 x 2M chains, seeds
##               2026-2029; accepted on the deliverable 2026-08-13). L11 is the
##               D1+D2 change set, accepted 2026-08-15, and stores the Greenland
##               slow channel as (ell, w) — the loader derives the native pair.
##               The Greenland variant is read off the file, not assumed. CAVEAT
##               carried from both acceptances: the 2150 and 2300 columns rest on
##               the AIS tipping tail, the slowest-mixing feature (chain-median
##               spread at 2150 is 13x the 2100 value relative to within-chain
##               scatter, and R-hat is mean-based so it reads 1.000 there anyway).
##   model     : Ladrillo = MimiBRICK v2.0.0 + 3-reservoir glacier emulator +
##               Greenland A+B with the amp(GMST) law, applied through
##               julia/ladrillo_projection.jl (tested by
##               julia/test_ladrillo_projection.jl)
##   forcing   : FaIR mean GMST + OHC per SSP (fair_mean_{gmst,ohc}_<ssp>.csv,
##               RCMIP-native run_fair_ssps.py) — mean forcing, so the reported
##               spread is POSTERIOR-PARAMETER spread, not climate spread
##   baseline  : 1995-2014 (AR6; ~ FACTS baseyear 2005)
##   LWS       : seeded realization (build_brick_nu3 default, LWS_SEED)
##   F_unch    : excluded — hindcast-target construct (see ladrillo_projection.jl)
##
## Bands are 5-95% and 17-83% (AR6 "likely") over FINITE draws; the AIS
## fast-dynamics tail can go non-finite, so the finite count is reported per
## scenario and carried in the output.
##
##   julia --project=julia_v2 julia/project_ssps_components_ladrillo.jl [n_draws] [--tag=L11]
##
## --tag selects the posterior AND the output filename together (default L10).
## ============================================================================

using CSV, DataFrames, Mimi, Printf, Statistics
include(joinpath(@__DIR__, "ladrillo_projection.jl"))

const Y0, Y1   = 1850, 2300
const REPORT0  = 1990                      # first year written out
const NTHIN    = let p = filter(a -> !startswith(a, "--"), ARGS)
    isempty(p) ? 2000 : parse(Int, p[1])
end
## POSTERIOR TAG drives BOTH the input posterior and the output filename, so a
## run on one vintage cannot write a file labelled with another. The default
## tracks the CANONICAL posterior (L11 since 2026-08-17; L10 before that), so it
## is derived from LADRILLO_POSTERIOR_CSV rather than written out again — the
## two cannot drift. Passing --tag=X asserts the file exists rather than
## silently falling back, and older vintages stay reachable that way.
const DEFAULT_TAG = let b = basename(LADRILLO_POSTERIOR_CSV)
    replace(replace(b, "parameters_subsample_brick_mengel_" => ""), ".csv" => "")
end
const POST_TAG = let i = findfirst(a -> startswith(a, "--tag="), ARGS)
    i === nothing ? DEFAULT_TAG : ARGS[i][7:end]
end
const TAP_ON = "--tap" in ARGS
## THE TAP STATE IS IN THE FILENAME. A tapped and an untapped 2300 projection differ
## by ~180 cm on ssp585 and are otherwise identical in shape, units and header — the
## one thing that must never be ambiguous about a file on disk is which arm it is.
const TAG = TAP_ON ? "$(POST_TAG)_tap$(replace(string(GIS_TAP_CELL.onset_K), "." => "p"))K_V$(replace(string(GIS_TAP_CELL.V_m), "." => "p"))m_tau$(Int(GIS_TAP_CELL.tau_yr))" : POST_TAG
const POSTERIOR = joinpath(LADRILLO_REPO,
    "data/MimiBRICK/parameters_subsample_brick_mengel_$(POST_TAG).csv")
isfile(POSTERIOR) || error("no posterior for --tag=$POST_TAG at $POSTERIOR")
POST_TAG != DEFAULT_TAG || POSTERIOR == LADRILLO_POSTERIOR_CSV ||
    error("the default tag '$DEFAULT_TAG' resolved to $POSTERIOR, which is not " *
          "LADRILLO_POSTERIOR_CSV ($LADRILLO_POSTERIOR_CSV)")
const OUT      = joinpath(LADRILLO_REPO, "outputs/ssps_components_2300_$(TAG).csv")
const SSPS     = [("ssp126", "SSP1-2.6"), ("ssp245", "SSP2-4.5"), ("ssp585", "SSP5-8.5")]
const HORIZONS = (2100, 2150, 2300)
const COMPONENTS = [:glaciers, :gis, :ais, :te, :lws, :total]

const VARIANT = ladrillo_posterior_variant(POSTERIOR)
post = ladrillo_posterior(path=POSTERIOR, nthin=NTHIN)
@printf("Ladrillo SSP components | posterior %s (%d draws) | Greenland :%s | base %d-%d | horizon %d\n",
        basename(POSTERIOR), nrow(post), VARIANT,
        LADRILLO_REF[1], LADRILLO_REF[2], Y1)
VARIANT === :ab && @printf("  amp law ON: S anchored at dT_eff = %.3f K, %d-yr window\n",
                           LADRILLO_GIS_SHAPE_ANCHOR_DT, LADRILLO_GIS_SHAPE_WIN)

out = DataFrame(year=Int[], ssp=String[], component=String[], gmst=Float64[],
                med=Float64[], p05=Float64[], p17=Float64[], p83=Float64[], p95=Float64[],
                n_finite=Int[])

for (ssp, label) in SSPS
    bf = ladrillo_setup(ssp=ssp, y0=Y0, y1=Y1, gis_variant = VARIANT)
    ## --tap switches the high-basin volume tap ON at GIS_TAP_CELL. PRIOR-PROPAGATED,
    ## not sampled: the calibration tops out at 1.385 K against a 6.5 K onset, so the
    ## tap is exactly likelihood-inert and the same posterior serves both arms.
    ## Gated by julia/test_gis_tap_wiring.jl — 2100 and 2150 move by 0.000e+00 and
    ## cooler scenarios deviate EXACTLY 0.0, so a --tap run is directly comparable
    ## to an untapped one at every horizon the model is validated at.
    TAP_ON && ladrillo_set_tap!(bf)
    ny = length(bf.years)
    series = Dict(c => Array{Float64}(undef, ny, nrow(post)) for c in COMPONENTS)
    t0 = time()
    for (j, r) in enumerate(eachrow(post))
        ladrillo_run_draw!(bf, r)
        for c in COMPONENTS
            series[c][:, j] = ladrillo_series(bf, c)
        end
        j % 250 == 0 && (print("."); flush(stdout))
    end
    @printf("\n%-9s %d draws in %.0fs\n", label, nrow(post), time() - t0)

    for c in COMPONENTS, (i, y) in enumerate(bf.years)
        y >= REPORT0 || continue
        v = filter(isfinite, @view series[c][i, :])
        push!(out, (y, label, string(c), bf.gmst[i], median(v), quantile(v, 0.05),
                    quantile(v, 0.17), quantile(v, 0.83), quantile(v, 0.95), length(v)))
    end
    for y in HORIZONS
        row(c) = out[(out.year .== y) .& (out.ssp .== label) .& (out.component .== string(c)), :]
        @printf("  @%d GMST %+0.2f | glac %5.1f  gis %5.1f  ais %6.1f  te %5.1f  lws %4.1f | TOTAL %6.1f [%5.1f, %6.1f] cm  (finite %d/%d)\n",
                y, bf.gmst[ladrillo_yi(bf, y)], row(:glaciers).med[1], row(:gis).med[1],
                row(:ais).med[1], row(:te).med[1], row(:lws).med[1], row(:total).med[1],
                row(:total).p17[1], row(:total).p83[1], row(:total).n_finite[1], nrow(post))
    end
end

CSV.write(OUT, out)
println("\nwrote ", relpath(OUT, LADRILLO_REPO))
