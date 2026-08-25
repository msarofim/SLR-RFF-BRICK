## ============================================================================
## diag_ais_tipping_under_forcing.jl — WHY DOES THE ssp245 MEDIAN FALL 26-40%
##                                     WHEN THE FORCING SPREAD GOES IN?
##
## THE OBSERVATION. `scope_slr_fair_uncertainty.jl` moves the ssp245 medians a lot
## (ais@2300 131.35 -> 79.23 = -39.7%; total@2300 219.07 -> 162.84 = -25.7%) while
## the ssp585 medians barely move (-1.3%). A median that moves that far under a
## width-preserving change of forcing sample is a THRESHOLD signature, not a level
## shift, and the candidate mechanism is stated in `ais_lambda_rests_on_lig`:
## DAIS tips when T_ant clears `antarctic_temp_threshold`, and at ssp245 the mean
## driver tips ~62.5% of draws -- i.e. the MEDIAN draw is tipped, and contributes a
## fast-dynamics term (110 cm at 2300) that a cooler config would not.
##
## THE TEST. Compute the tipped fraction two ways at each horizon: under the shipped
## MEAN driver, and under each draw's OWN assigned FaIR config (same seeded pairing
## as the projection). If the mechanism is right, the ssp245 tipped fraction must
## cross 50% between the two -- the median draw stops being a tipped draw -- while
## ssp585 stays pinned near 100% in both. No model run: T_ant = amp*GMST + TANT0 is
## closed form, and the threshold is a sampled column.
##
## ⚠ This is a DIAGNOSTIC of the projection's own arithmetic, not an independent
## check of the projection. It shares the pairing seed deliberately, so the fraction
## it reports is the one the band actually saw.
##
##   julia --project=julia_v2 julia/diag_ais_tipping_under_forcing.jl [--tag=L14]
## Writes outputs/diag_ais_tipping_under_forcing_<tag>.csv
## ============================================================================
using CSV, DataFrames, Statistics, Printf, Random

include(joinpath(@__DIR__, "ladrillo_projection.jl"))

const REPO  = LADRILLO_REPO
const SEEDS = [2026, 2027, 2028, 2029]
const NITER, NBURN = 2000000, 1000000
const TAG = let i = findfirst(a -> startswith(a, "--tag="), ARGS)
    i === nothing ? "L14" : ARGS[i][7:end]
end
const N_TARGET = 500
const SSPS = ["ssp126", "ssp245", "ssp585"]
const HORIZONS = [2100, 2150, 2300]
const Y0, Y1 = 1850, 2300
const SPLICE_YEAR = 2014
const PAIR_SEED = 2026                # MUST match scope_slr_fair_uncertainty.jl
const TANT0 = LADRILLO_AIS_TANT0
const YEARS = collect(Y0:Y1)
const IREF = findall(y -> LADRILLO_REF[1] <= y <= LADRILLO_REF[2], YEARS)

chain_path(sd) = joinpath(REPO, "outputs/mcmc", "chain_$(TAG)_seed$(sd)_n$(NITER).csv")
function read_two(sd)
    df = CSV.read(chain_path(sd), DataFrame; select = ["ais_gmst_amp", "antarctic_temp_threshold"])
    step = max(1, (nrow(df) - NBURN) ÷ N_TARGET)
    df[collect((NBURN + 1):step:nrow(df))[1:N_TARGET], :]
end
const D = vcat([read_two(sd) for sd in SEEDS]...)
const NDRAW = nrow(D)
const AMP = Float64.(D.ais_gmst_amp)
const THR = Float64.(D.antarctic_temp_threshold)
@printf("AIS TIPPING UNDER FORCING | tag %s | %d draws | pairing seed %d\n", TAG, NDRAW, PAIR_SEED)

rows = DataFrame(ssp = String[], horizon = Int[], driver = String[],
                 tipped_frac = Float64[], median_is_tipped = Bool[], med_excess_degC = Float64[])
for ssp in SSPS
    G = CSV.read(joinpath(LADRILLO_OBS, "fair_cube_gmst_$(ssp)_raw.csv"), DataFrame)
    cfg = [c for c in String.(propertynames(G)) if startswith(c, "cfg_")]
    mean_g = [_yearmap(joinpath(LADRILLO_OBS, "fair_mean_gmst_$(ssp).csv"), "gmst_C")[y] for y in YEARS]
    mref = mean(mean_g[IREF])
    ## the SAME seeded pairing the projection used
    assign = let rng = MersenneTwister(PAIR_SEED); a = Int[]
        while length(a) < NDRAW; append!(a, randperm(rng, length(cfg))); end; a[1:NDRAW]
    end
    spliced = Dict(c => (raw = Float64.(G[!, c]);
                         cref = mean(raw[IREF]);
                         [y <= SPLICE_YEAR ? mean_g[i] : mref + (raw[i] - cref)
                          for (i, y) in enumerate(YEARS)]) for c in cfg)
    @printf("\n%s\n%s -- tipped fraction of %d draws\n%s\n", repeat("=", 78), ssp, NDRAW, repeat("=", 78))
    @printf("  %-6s %-18s %12s %10s %14s\n", "horiz", "driver", "tipped", "med tipped", "med excess degC")
    for H in HORIZONS
        i = findfirst(==(H), YEARS)
        for (lab, tant) in (("shipped MEAN", [AMP[k] * mean_g[i] + TANT0 for k in 1:NDRAW]),
                            ("per-draw config", [AMP[k] * spliced[cfg[assign[k]]][i] + TANT0 for k in 1:NDRAW]))
            ex = tant .- THR
            f = count(>(0), ex) / NDRAW
            push!(rows, (ssp, H, lab, f, f > 0.5, median(ex)))
            @printf("  %-6d %-18s %11.1f%% %10s %14.3f\n", H, lab, 100f,
                    f > 0.5 ? "YES" : "no", median(ex))
        end
    end
end
CSV.write(joinpath(REPO, "outputs", "diag_ais_tipping_under_forcing_$(TAG).csv"), rows)

@printf("\n%s\nVERDICT\n%s\n", repeat("=", 78), repeat("=", 78))
for ssp in SSPS, H in HORIZONS
    a = rows[(rows.ssp .== ssp) .& (rows.horizon .== H) .& (rows.driver .== "shipped MEAN"), :]
    b = rows[(rows.ssp .== ssp) .& (rows.horizon .== H) .& (rows.driver .== "per-draw config"), :]
    if a.median_is_tipped[1] != b.median_is_tipped[1]
        @printf("  %s @%d: THE MEDIAN DRAW CHANGES TIPPING STATE (%.1f%% -> %.1f%%)\n",
                ssp, H, 100a.tipped_frac[1], 100b.tipped_frac[1])
    end
end
@printf("\ndone.\n")
