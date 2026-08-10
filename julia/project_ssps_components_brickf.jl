## ============================================================================
## project_ssps_components_brickf.jl — BRICK-F* per-component SSP projections
##
## Component-resolved sea-level bands for SSP1-2.6 / SSP2-4.5 / SSP5-8.5 from
## the accepted BRICK-F* (extC) posterior, 1990-2300, cm relative to 1995-2014.
## This is the projection deliverable the sharing memo's SSP section and every
## comparison arm (FACTS, MAGICC, pre-Mengel BRICK 2.0) read.
##
## Basis
##   posterior : data/MimiBRICK/parameters_subsample_brick_mengel_extC.csv
##               (4 x 2M chains, seeds 2026-2029; accepted on the deliverable)
##   model     : BRICK-F* = MimiBRICK v2.0.0 + 3-reservoir glacier emulator,
##               applied through julia/brickf_projection.jl (tested by
##               julia/test_brickf_projection.jl)
##   forcing   : FaIR mean GMST + OHC per SSP (fair_mean_{gmst,ohc}_<ssp>.csv,
##               RCMIP-native run_fair_ssps.py) — mean forcing, so the reported
##               spread is POSTERIOR-PARAMETER spread, not climate spread
##   baseline  : 1995-2014 (AR6; ~ FACTS baseyear 2005)
##   LWS       : seeded realization (build_brick_nu3 default, LWS_SEED)
##   F_unch    : excluded — hindcast-target construct (see brickf_projection.jl)
##
## Bands are 5-95% and 17-83% (AR6 "likely") over FINITE draws; the AIS
## fast-dynamics tail can go non-finite, so the finite count is reported per
## scenario and carried in the output.
##
##   julia --project=julia_v2 julia/project_ssps_components_brickf.jl [n_draws]
## ============================================================================

using CSV, DataFrames, Mimi, Printf, Statistics
include(joinpath(@__DIR__, "brickf_projection.jl"))

const OUT      = joinpath(BRICKF_REPO, "outputs/ssps_components_2300_extC.csv")
const Y0, Y1   = 1850, 2300
const REPORT0  = 1990                      # first year written out
const NTHIN    = length(ARGS) >= 1 ? parse(Int, ARGS[1]) : 2000
const SSPS     = [("ssp126", "SSP1-2.6"), ("ssp245", "SSP2-4.5"), ("ssp585", "SSP5-8.5")]
const HORIZONS = (2100, 2150, 2300)
const COMPONENTS = [:glaciers, :gis, :ais, :te, :lws, :total]

post = brickf_posterior(nthin=NTHIN)
@printf("BRICK-F* SSP components | posterior %s (%d draws) | base %d-%d | horizon %d\n",
        basename(BRICKF_POSTERIOR_CSV), nrow(post), BRICKF_REF[1], BRICKF_REF[2], Y1)

out = DataFrame(year=Int[], ssp=String[], component=String[], gmst=Float64[],
                med=Float64[], p05=Float64[], p17=Float64[], p83=Float64[], p95=Float64[],
                n_finite=Int[])

for (ssp, label) in SSPS
    bf = brickf_setup(ssp=ssp, y0=Y0, y1=Y1)
    ny = length(bf.years)
    series = Dict(c => Array{Float64}(undef, ny, nrow(post)) for c in COMPONENTS)
    t0 = time()
    for (j, r) in enumerate(eachrow(post))
        brickf_run_draw!(bf, r)
        for c in COMPONENTS
            series[c][:, j] = brickf_series(bf, c)
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
                y, bf.gmst[brickf_yi(bf, y)], row(:glaciers).med[1], row(:gis).med[1],
                row(:ais).med[1], row(:te).med[1], row(:lws).med[1], row(:total).med[1],
                row(:total).p17[1], row(:total).p83[1], row(:total).n_finite[1], nrow(post))
    end
end

CSV.write(OUT, out)
println("\nwrote ", relpath(OUT, BRICKF_REPO))
