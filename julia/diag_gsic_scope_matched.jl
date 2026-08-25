## ============================================================================
## diag_gsic_scope_matched.jl — THE CHEAP DECISIVE TEST FOR THE GLACIER LEVEL
##   DEFICIT: our glaciers, projected, with the R19 SLOT SPLIT OUT, so the
##   region-scope correction can be computed AT EACH HORIZON from the model
##   instead of assumed from observed-era shares.
##
## THE CLAIM UNDER TEST (handoff -25c addendum 3 §C). Our glacier projections
## run 0.755-0.93x the literature at every scenario and horizon. Most of that
## was shown to be REGIONAL SCOPE: ours owns RGI 1-18 minus r5 plus r19, while
## FACTS's AR5 module has glac5 and has neither glac18 nor glac19. Over GlaMBIE
## 2000-2023 r5 = 13.00% and r19 = 6.54% of global loss, so scope alone predicts
## 0.931 against an observed 0.843 -- leaving a ~9% residual model deficit.
##
## ⚠ AND THAT CORRECTION WAS FLAGGED AS AN UNDER-ESTIMATE, for a stated reason:
## the shares are OBSERVED-ERA while **r19 depletes last**, so its share of the
## total should GROW with horizon and the correction at 2150/2300 should be
## larger than 6.54%. That is a model-testable statement and this driver tests
## it: `glaciers_nu3` carries r19 in its OWN `:gsic_r19` slot (three reservoirs:
## R19 / SLOWP / FAST), so no differencing of aggregates is involved and no
## re-calibration is needed. Same posterior, same forcing, same horizons as the
## deliverable driver.
##
## ⚠ WHAT THIS CANNOT DO. The other half of the scope difference is r5, which our
## glaciers do NOT model at all -- it lives in the GIS target (Marcus 2026-08-06),
## and our GIS is a two-stage sheet cascade with no separable periphery term. So
## r19 is measured here and r5 must still be assumed. The python side states
## which half is which; do not let the two be quoted as one number.
##
##     julia --project=julia_v2 julia/diag_gsic_scope_matched.jl [NTHIN] [--tag=L14]
## Writes outputs/diag_gsic_scope_matched_<TAG>.csv
## ============================================================================
using CSV, DataFrames, Mimi, Printf, Statistics
include(joinpath(@__DIR__, "ladrillo_projection.jl"))

const Y0, Y1 = 1850, 2300
const NTHIN = let p = filter(a -> !startswith(a, "--"), ARGS)
    isempty(p) ? 2000 : parse(Int, p[1])
end
const DEFAULT_TAG = let b = basename(LADRILLO_POSTERIOR_CSV)
    replace(replace(b, "parameters_subsample_brick_mengel_" => ""), ".csv" => "")
end
const POST_TAG = let i = findfirst(a -> startswith(a, "--tag="), ARGS)
    i === nothing ? DEFAULT_TAG : ARGS[i][7:end]
end
const POSTERIOR = joinpath(LADRILLO_REPO,
    "data/MimiBRICK/parameters_subsample_brick_mengel_$(POST_TAG).csv")
isfile(POSTERIOR) || error("no posterior for --tag=$POST_TAG at $POSTERIOR")
const OUT = joinpath(LADRILLO_REPO, "outputs/diag_gsic_scope_matched_$(POST_TAG).csv")
const SSPS = [("ssp126", "SSP1-2.6"), ("ssp245", "SSP2-4.5"), ("ssp585", "SSP5-8.5")]
const HORIZONS = (2100, 2150, 2300)
## :glaciers is the reported component; :gsic_r19 is the R19 reservoir alone.
## The scope-matched arm is the DIFFERENCE, taken PER DRAW so the band is the
## band of the difference and not a difference of bands.
const SLOTS = [:glaciers, :gsic_r19]

post = ladrillo_posterior(path=POSTERIOR, nthin=NTHIN)
@printf("GSIC scope-matched | posterior %s (%d draws) | horizons %s\n",
        basename(POSTERIOR), nrow(post), join(HORIZONS, ", "))

out = DataFrame(year=Int[], ssp=String[], slot=String[], med=Float64[], p05=Float64[],
                p95=Float64[], n_finite=Int[])

for (ssp, label) in SSPS
    bf = ladrillo_setup(ssp=ssp, y0=Y0, y1=Y1, gis_variant=ladrillo_posterior_variant(POSTERIOR))
    ny = length(bf.years)
    series = Dict(s => Array{Float64}(undef, ny, nrow(post)) for s in SLOTS)
    t0 = time()
    for (j, r) in enumerate(eachrow(post))
        ladrillo_run_draw!(bf, r)
        for s in SLOTS
            series[s][:, j] = ladrillo_series(bf, s)
        end
        j % 250 == 0 && (print("."); flush(stdout))
    end
    @printf("\n%-9s %d draws in %.0fs\n", label, nrow(post), time() - t0)

    ## PER-DRAW difference: glaciers minus its own R19 reservoir.
    exr19 = series[:glaciers] .- series[:gsic_r19]
    for (nm, arr) in (("glaciers", series[:glaciers]), ("gsic_r19", series[:gsic_r19]),
                      ("glaciers_ex_r19", exr19))
        for (i, y) in enumerate(bf.years)
            y in HORIZONS || continue
            v = filter(isfinite, @view arr[i, :])
            push!(out, (y, label, nm, median(v), quantile(v, 0.05), quantile(v, 0.95),
                        length(v)))
        end
    end
    for y in HORIZONS
        g = out[(out.year .== y) .& (out.ssp .== label) .& (out.slot .== "glaciers"), :].med[1]
        r = out[(out.year .== y) .& (out.ssp .== label) .& (out.slot .== "gsic_r19"), :].med[1]
        @printf("  @%d  glaciers %6.2f  r19 %5.2f  ex-r19 %6.2f cm | r19 share %5.1f%%\n",
                y, g, r, g - r, 100r / g)
    end
end

CSV.write(OUT, out)
println("\nwrote ", relpath(OUT, LADRILLO_REPO))
