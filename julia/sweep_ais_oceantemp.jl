## ============================================================================
## sweep_ais_oceantemp.jl
##
## Confirming parameter sweep on BRICK's Antarctic Ice Sheet reference/
## equilibrium ocean temperature `ais_ocean_temperature₀`.
##
## GOAL: show whether raising ais_ocean_temperature₀ (default 0.72 °C, set
## inside MimiBRICK.get_model via update_param!) removes the historical AIS
## overshoot — i.e. whether median AIS@1900 (rel 2000) moves from the FaIR-mean
## obs-driven ~−3.97 cm toward the Frederikse 2020 target of −0.64 cm — and
## whether doing so preserves or degrades the modern IMBIE ΔAIS(1992-2017) fit.
##
## This is a NON-DESTRUCTIVE diagnostic. It reuses the exact obs-driven
## machinery of run_mimibrick_obs_driven.jl (same posterior, same FaIR-mean
## GMST + OHC forcing, same brick_param_updates.jl per-member parameterisation)
## and ONLY additionally overrides ais_ocean_temperature₀ to each sweep value,
## for every posterior member, AFTER update_brick_params!.
##
## Invocation (matches the obs-driven driver's env — julia/Manifest.toml pins
## MimiBRICK v1.0.1, the "bpCAF" env):
##
##   julia --project=julia julia/sweep_ais_oceantemp.jl \
##       --posterior data/MimiBRICK/parameters_subsample_brick.csv \
##       --gmst-csv  data/observations/fair_mean_gmst.csv \
##       --ohc-csv   data/observations/fair_mean_ohc.csv \
##       --max-post  2000
##
## Writes outputs/ais_oceantemp_sweep.csv and outputs/ais_oceantemp_sweep_summary.md.
## ============================================================================

using ArgParse
using CSV
using DataFrames
using Mimi
using MimiBRICK
using Random
using Statistics
using Printf

include(joinpath(@__DIR__, "brick_param_updates.jl"))

# --- sweep grid + validation targets ----------------------------------------
const SWEEP_VALUES = [0.72, 1.0, 1.25, 1.5, 1.75, 2.0, 2.5]
const DEFAULT_OCEANTEMP = 0.72   # MimiBRICK.get_model default for this param

# Frederikse 2020 AIS@1900 (rel 2000) and IMBIE ΔAIS(1992-2017) targets.
const FRED_AIS1900_MU  = -0.64
const FRED_AIS1900_SIG =  0.39
const IMBIE_DAIS_MU    =  0.72
const IMBIE_DAIS_SIG   =  0.156

# Sanity-check anchor: at default 0.72, median AIS@1900 must reproduce the
# existing fair_fair obs-driven run (~−3.97 cm) and median ΔAIS ~ +0.91 cm.
const SANITY_AIS1900 = -3.97
const SANITY_DAIS    =  0.91
const SANITY_TOL     =  0.10   # cm; subsample must be within this of full run

function parse_cli()
    s = ArgParseSettings()
    @add_arg_table! s begin
        "--posterior"; required = true
        "--gmst-csv";  required = true
        "--ohc-csv";   required = true
        "--output";        default = "outputs/ais_oceantemp_sweep.csv"
        "--summary";       default = "outputs/ais_oceantemp_sweep_summary.md"
        "--gmst-time-col";  default = "year"
        "--gmst-value-col"; default = "gmst_C"
        "--ohc-time-col";   default = "year"
        "--ohc-value-col";  default = "ohc_1e22J"
        "--seed";        arg_type = Int; default = 2026
        "--start-year";  arg_type = Int; default = 1850
        "--end-year";    arg_type = Int; default = 2024
        "--rcp";         default = "RCP45"     # v1.0.1 get_model scenario arg
        "--ssp";         default = "ssp245"    # v2.0.0 get_model scenario arg (ssprcp_scenario)
        "--strict-sanity"; action = :store_true  # error (not warn) if 0.72 baseline drifts from ref
        "--max-post";    arg_type = Int; default = 2000   # 0 = all 10k
    end
    return parse_args(s)
end

# Loader copied verbatim in behaviour from run_mimibrick_obs_driven.jl.
function load_trajectory(path::String, time_col::String, value_col::String,
                         years::AbstractVector{Int})
    df = CSV.read(path, DataFrame; comment="#")
    @assert time_col in names(df)  "$path missing time column '$time_col'; have $(names(df))"
    @assert value_col in names(df) "$path missing value column '$value_col'; have $(names(df))"
    src_years = floor.(Int, Float64.(df[!, time_col]))
    src_vals  = Float64.(df[!, value_col])
    by_year = Dict(src_years[i] => src_vals[i] for i in eachindex(src_years))
    out = Vector{Float64}(undef, length(years))
    n_missing = 0
    for (i, y) in enumerate(years)
        if haskey(by_year, y)
            out[i] = by_year[y]
        else
            out[i] = NaN; n_missing += 1
        end
    end
    return out, n_missing
end

function main()
    args = parse_cli()
    Random.seed!(args["seed"])

    yr_start = args["start-year"]; yr_end = args["end-year"]
    years_int = collect(yr_start:yr_end)
    n_yr = length(years_int)
    println("Year window: $yr_start-$yr_end ($n_yr yrs)")

    gmst, nmg = load_trajectory(args["gmst-csv"], args["gmst-time-col"], args["gmst-value-col"], years_int)
    ohc,  nmo = load_trajectory(args["ohc-csv"],  args["ohc-time-col"],  args["ohc-value-col"],  years_int)
    (nmg > 0 || nmo > 0) && error("Trajectory CSVs do not fully cover $yr_start-$yr_end.")
    println("Loaded GMST $(args["gmst-csv"]) / OHC $(args["ohc-csv"])")

    # Index helpers for the analysis years.
    idx(y) = (i = findfirst(==(y), years_int); isnothing(i) && error("year $y not in window"); i)
    i_2000 = idx(2000); i_1900 = idx(1900); i_1992 = idx(1992); i_2017 = idx(2017)

    println("Loading posterior $(args["posterior"]) ...")
    posterior = DataFrame(CSV.File(args["posterior"]))
    n_post = nrow(posterior)
    cap = args["max-post"] > 0 ? min(args["max-post"], n_post) : n_post
    println("  posterior: $n_post members, processing $cap")

    Random.seed!(args["seed"])
    # Version-aware get_model: v2.0.0 renamed the scenario kwarg rcp_scenario->ssprcp_scenario
    # (default RCP45->ssp245). Try the v2.0.0 signature first, fall back to v1.0.1.
    local m
    local precip_log   # v2.0.0 AIS precip is log-parameterized; v1.0.1 linear (see brick_param_updates.jl)
    try
        m = MimiBRICK.get_model(ssprcp_scenario = args["ssp"], start_year = yr_start, end_year = yr_end)
        precip_log = true
        println("Built MimiBRICK model via v2.0.0 API (ssprcp_scenario=$(args["ssp"])) — precip_log=true")
    catch err
        isa(err, MethodError) || rethrow()
        m = MimiBRICK.get_model(rcp_scenario = args["rcp"], start_year = yr_start, end_year = yr_end)
        precip_log = false
        println("Built MimiBRICK model via v1.0.1 API (rcp_scenario=$(args["rcp"])) — precip_log=false")
    end
    # The obs-driven forcing overrides are constant across members; set once.
    update_param!(m, :model_global_surface_temperature, gmst)
    update_param!(m, :thermal_expansion, :ocean_heat_interior, ohc)

    results = DataFrame(
        ais_ocean_temp0 = Float64[], n_members = Int[],
        median_ais_1900 = Float64[], median_dAIS_9217 = Float64[],
        hist_pass_frac = Float64[], modern_pass_frac = Float64[],
        joint_pass_frac = Float64[],
    )

    for sweepval in SWEEP_VALUES
        ais1900 = Vector{Float64}(undef, cap)
        dais    = Vector{Float64}(undef, cap)
        t0 = time()
        for i in 1:cap
            prow = posterior[i, :]
            update_brick_params!(m, prow; precip_log = precip_log)
            # Re-apply forcing overrides every member, exactly as run_mimibrick_obs_driven.jl does.
            update_param!(m, :model_global_surface_temperature, gmst)
            update_param!(m, :thermal_expansion, :ocean_heat_interior, ohc)
            # Override AFTER per-member params, for every member.
            update_param!(m, :antarctic_icesheet, :ais_ocean_temperature₀, sweepval)
            run(m)
            ais = m[:antarctic_icesheet, :ais_sea_level]
            base = ais[i_2000]
            ais1900[i] = 100 * (ais[i_1900] - base)
            dais[i]    = 100 * (ais[i_2017] - ais[i_1992])
        end
        med1900 = median(ais1900); medd = median(dais)
        histpass  = mean(abs.(ais1900 .- FRED_AIS1900_MU) .<= 2 * FRED_AIS1900_SIG)
        modpass   = mean(abs.(dais   .- IMBIE_DAIS_MU)    .<= 2 * IMBIE_DAIS_SIG)
        jointpass = mean((abs.(ais1900 .- FRED_AIS1900_MU) .<= 2 * FRED_AIS1900_SIG) .&
                         (abs.(dais   .- IMBIE_DAIS_MU)    .<= 2 * IMBIE_DAIS_SIG))
        el = round(time() - t0, digits=1)
        @printf("  oceantemp0=%.2f  med_AIS1900=%.3f  med_dAIS=%.3f  hist=%.3f mod=%.3f joint=%.3f  (%ss)\n",
                sweepval, med1900, medd, histpass, modpass, jointpass, el)
        push!(results, (sweepval, cap, med1900, medd, histpass, modpass, jointpass))

        # Sanity / cross-version anchor at default ocean temp. On v1.0.1 this must reproduce
        # the -3.97 obs-driven baseline; on v2.0.0 a deviation is INFORMATIVE (model/#98 effect),
        # so warn (don't error) unless --strict-sanity is set.
        if isapprox(sweepval, DEFAULT_OCEANTEMP; atol=1e-9)
            off = abs(med1900 - SANITY_AIS1900)
            msg = "median AIS@1900 at 0.72 = $(round(med1900,digits=3)) cm (ref $SANITY_AIS1900, " *
                  "Δ=$(round(med1900-SANITY_AIS1900,digits=3))); ΔAIS=$(round(medd,digits=3)) (ref $SANITY_DAIS)"
            if off > SANITY_TOL
                args["strict-sanity"] ? error("SANITY FAIL: $msg") : @warn "Baseline drift vs v1.0.1 ref: $msg"
            else
                println("  [sanity OK] $msg")
            end
        end
    end

    mkpath(dirname(args["output"]))
    CSV.write(args["output"], results)
    println("\nWrote $(args["output"])")

    # --- markdown summary ----------------------------------------------------
    open(args["summary"], "w") do io
        println(io, "# AIS `ais_ocean_temperature₀` confirming sweep")
        println(io)
        ver_label = precip_log ? "MimiBRICK v2.0.0 (precip_log=true)" : "MimiBRICK v1.0.1 (precip_log=false)"
        scen_label = precip_log ? "ssprcp=$(args["ssp"])" : "rcp=$(args["rcp"])"
        println(io, "Driver: `julia/sweep_ais_oceantemp.jl` (reuses `run_mimibrick_obs_driven.jl` machinery, $ver_label).")
        println(io, "Forcing: FaIR-mean GMST (`$(basename(args["gmst-csv"]))`) + FaIR-mean OHC (`$(basename(args["ohc-csv"]))`), the `fair_fair` combo.")
        println(io, "Posterior: `$(basename(args["posterior"]))`, first **$cap** of $n_post members. Window $yr_start-$yr_end, $scen_label. All AIS values cm rel 2000.")
        println(io)
        println(io, "Targets: Frederikse 2020 AIS@1900 = **$(FRED_AIS1900_MU) ± $(FRED_AIS1900_SIG)** cm; IMBIE ΔAIS(1992-2017) = **$(IMBIE_DAIS_MU) ± $(IMBIE_DAIS_SIG)** cm. Pass = within ±2σ. `ais_ocean_temperature₀` default = $(DEFAULT_OCEANTEMP) °C.")
        println(io)
        println(io, "| ocean_temp₀ (°C) | n | median AIS@1900 (cm) | median ΔAIS 1992-2017 (cm) | hist pass | modern pass | joint pass |")
        println(io, "|---:|---:|---:|---:|---:|---:|---:|")
        for r in eachrow(results)
            @printf(io, "| %.2f | %d | %.3f | %.3f | %.3f | %.3f | %.3f |\n",
                    r.ais_ocean_temp0, r.n_members, r.median_ais_1900, r.median_dAIS_9217,
                    r.hist_pass_frac, r.modern_pass_frac, r.joint_pass_frac)
        end
        println(io)
        # crossing point for AIS@1900 reaching the Frederikse central -0.64
        println(io, "Frederikse AIS@1900 central target = $(FRED_AIS1900_MU) cm (horizontal reference in the PNG).")
    end
    println("Wrote $(args["summary"])")
    return results
end

main()
