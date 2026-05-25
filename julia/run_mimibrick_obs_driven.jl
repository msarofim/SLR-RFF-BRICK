## ============================================================================
## run_mimibrick_obs_driven.jl
##
## Drive BRICK with externally-supplied GMST + OHC trajectories (typically
## observations) instead of a FaIR cube. Loops over BRICK posterior members
## and writes year-by-year per-component SLR. The output schema matches the
## --save-component-trajs branch of run_mimibrick_paired_explicit.jl so that
## the obs-driven and FaIR-driven runs can be overlaid trivially in the
## downstream Python plotting code.
##
## Use it for any (GMST source, OHC source) combination — pass the relevant
## CSVs:
##
##   (obs GMST, obs OHC)    [headline]   : both --gmst-csv and --ohc-csv obs
##   (obs GMST, FaIR OHC)   [diagnostic] : --gmst-csv obs, --ohc-csv fair_mean
##   (FaIR GMST, obs OHC)   [diagnostic] : --gmst-csv fair_mean, --ohc-csv obs
##   (FaIR GMST, FaIR OHC)  [reference]  : both fair_mean (sanity-check only;
##                                         the existing FaIR-cube driver does
##                                         this more rigorously per cell)
##
## The hybrid combos use FaIR ensemble-mean CSVs produced by
## python/build_fair_mean_trajectories.py.
##
## Input CSVs:
##   --gmst-csv:  CSV with columns `year` and `gmst_C` (°C, anomaly relative
##                to BRICK/FaIR's pre-industrial baseline). IGCC obs CSV at
##                data/observations/igcc2024_gmst_4dataset_mean.csv has a
##                differently-named column; pass the canonical schema or use
##                fair_mean_gmst.csv (year,gmst_C). For raw IGCC, see
##                obs schema notes below.
##   --ohc-csv:   CSV with columns `year` and `ohc_1e22J` (cumulative since
##                1750, units 10^22 J). Matches the schema of
##                data/observations/ohc_spliced_zanna_cheng.csv (which
##                already has those exact columns) and the FaIR-mean OHC.
##
## IGCC schema note: igcc2024_gmst_4dataset_mean.csv has columns
## `time,timebound_lower,timebound_upper,GMST,Land,Ocean`. Use --gmst-time-col
## time --gmst-value-col GMST to consume it directly.
##
## Output: long-by-cell-only, wide-by-year CSV. One row per posterior member;
## columns: post_idx, slr_<y>, te_<y>, ais_<y>, gis_<y>, gsic_<y>, lws_<y>
## for every year in the run window. All values in cm, re-referenced to year
## 2000 (matches the convention used by run_mimibrick_paired_explicit.jl).
## NOTE: BRICK's total SLR sums five contributors (AIS, GSIC, GIS, TE, LWS).
## LWS (landwater storage) is stochastic but small (<5 mm by 2100). Including
## it makes Σ components ≡ total SLR to ~1e-15; omitting leaves a ~3 mm
## residual by 2024 that the closure check would catch.
## ============================================================================

using ArgParse
using CSV
using DataFrames
using Mimi
using MimiBRICK
using Random

# Shared BRICK-posterior-row updater (extracted 2026-05-25).
include(joinpath(@__DIR__, "brick_param_updates.jl"))

function parse_cli()
    s = ArgParseSettings()
    @add_arg_table! s begin
        "--posterior"; required = true; help = "BRICK posterior CSV (parameters_subsample_brick.csv)"
        "--gmst-csv";  required = true; help = "Trajectory CSV with year + GMST (°C)"
        "--ohc-csv";   required = true; help = "Trajectory CSV with year + OHC (10^22 J)"
        "--output";    required = true; help = "Output CSV path"
        "--gmst-time-col";  default = "year"
        "--gmst-value-col"; default = "gmst_C"
        "--ohc-time-col";   default = "year"
        "--ohc-value-col";  default = "ohc_1e22J"
        "--seed";        arg_type = Int; default = 2026
        "--start-year";  arg_type = Int; default = 1850
        "--end-year";    arg_type = Int; default = 2100
        "--rcp";         default = "RCP45"
        "--max-post";    arg_type = Int; default = 0   # 0 = all
        # Phase A symmetric: drop the bare-year "total" columns to keep the
        # CSV narrow. The default writes per-component + total in the same
        # prefixed schema; flip if you only need the total.
        "--save-total-trajs";     arg_type = Bool; default = true
        "--save-component-trajs"; arg_type = Bool; default = true
    end
    return parse_args(s)
end

# CSV loader that tolerates BRICK obs files with header comments (lines
# starting with '#'), and lets the caller pick column names (e.g. IGCC's
# `time`/`GMST` vs the canonical `year`/`gmst_C`). Returns the values on the
# requested year grid, interpolating NaN-fill outside the file's coverage so
# the caller can detect missing years instead of silently extrapolating.
function load_trajectory(path::String, time_col::String, value_col::String,
                         years::AbstractVector{Int})
    df = CSV.read(path, DataFrame; comment="#")
    @assert time_col in names(df)  "$path missing time column '$time_col'; have $(names(df))"
    @assert value_col in names(df) "$path missing value column '$value_col'; have $(names(df))"
    # IGCC stamps mid-year (1850.5); floor to int for matching.
    src_years = floor.(Int, Float64.(df[!, time_col]))
    src_vals  = Float64.(df[!, value_col])
    by_year = Dict(src_years[i] => src_vals[i] for i in eachindex(src_years))
    n_missing = 0
    out = Vector{Float64}(undef, length(years))
    for (i, y) in enumerate(years)
        if haskey(by_year, y)
            out[i] = by_year[y]
        else
            out[i] = NaN
            n_missing += 1
        end
    end
    return out, n_missing
end

function main()
    args = parse_cli()
    Random.seed!(args["seed"])

    yr_start = args["start-year"]
    yr_end   = args["end-year"]
    yr_window = yr_start:yr_end
    years_int = collect(yr_window)
    n_yr = length(years_int)
    println("Year window: $yr_start-$yr_end ($n_yr yrs)")

    gmst, n_missing_gmst = load_trajectory(args["gmst-csv"], args["gmst-time-col"],
                                           args["gmst-value-col"], years_int)
    ohc,  n_missing_ohc  = load_trajectory(args["ohc-csv"],  args["ohc-time-col"],
                                           args["ohc-value-col"], years_int)
    println("Loaded GMST from $(args["gmst-csv"])  ($n_missing_gmst missing yrs out of $n_yr)")
    println("Loaded OHC  from $(args["ohc-csv"])   ($n_missing_ohc missing yrs out of $n_yr)")
    if n_missing_gmst > 0 || n_missing_ohc > 0
        # Hard-fail rather than silently extrapolating — caller should
        # explicitly clip the year window or extend the obs CSVs.
        error("Trajectory CSVs do not fully cover $yr_start-$yr_end. " *
              "Clip --start-year/--end-year or extend the source CSVs.")
    end

    i_2000 = findfirst(==(2000), years_int)
    isnothing(i_2000) && error("Year window must include 2000 (re-baselining anchor).")

    println("Loading posterior from $(args["posterior"]) ...")
    posterior = DataFrame(CSV.File(args["posterior"]))
    n_post = nrow(posterior)
    cap = args["max-post"] > 0 ? min(args["max-post"], n_post) : n_post
    println("  posterior: $n_post members, processing $cap")

    Random.seed!(args["seed"])
    println("Building MimiBRICK model (rcp=$(args["rcp"]))...")
    m = MimiBRICK.get_model(
        rcp_scenario = args["rcp"],
        start_year   = yr_start,
        end_year     = yr_end,
    )

    save_total = args["save-total-trajs"]
    save_comp  = args["save-component-trajs"]

    out = DataFrame(
        post_idx     = Int[],
        slr_2050_cm  = Float64[],
        slr_2100_cm  = Float64[],
        ais_2100_cm  = Float64[],
        gsic_2100_cm = Float64[],
        gis_2100_cm  = Float64[],
        te_2100_cm   = Float64[],
        lws_2100_cm  = Float64[],
    )
    slr_cols  = Symbol[]
    te_cols   = Symbol[]
    ais_cols  = Symbol[]
    gis_cols  = Symbol[]
    gsic_cols = Symbol[]
    lws_cols  = Symbol[]
    if save_total
        slr_cols = [Symbol("slr_$(y)") for y in years_int]
        for c in slr_cols; out[!, c] = Float64[]; end
    end
    if save_comp
        te_cols   = [Symbol("te_$(y)")   for y in years_int]
        ais_cols  = [Symbol("ais_$(y)")  for y in years_int]
        gis_cols  = [Symbol("gis_$(y)")  for y in years_int]
        gsic_cols = [Symbol("gsic_$(y)") for y in years_int]
        lws_cols  = [Symbol("lws_$(y)")  for y in years_int]
        for c in vcat(te_cols, ais_cols, gis_cols, gsic_cols, lws_cols)
            out[!, c] = Float64[]
        end
    end

    i_2050 = findfirst(==(2050), years_int)
    i_2100 = findfirst(==(2100), years_int)

    println("Running BRICK over $cap posterior members (forced by GMST + OHC) ...")
    t0 = time()
    for i in 1:cap
        prow = posterior[i, :]
        update_brick_params!(m, prow)
        update_param!(m, :model_global_surface_temperature, gmst)
        update_param!(m, :thermal_expansion, :ocean_heat_interior, ohc)
        run(m)

        ais  = m[:antarctic_icesheet,     :ais_sea_level]
        gsic = m[:glaciers_small_icecaps, :gsic_sea_level]
        gis  = m[:greenland_icesheet,     :greenland_sea_level]
        te   = m[:thermal_expansion,      :te_sea_level]
        lws  = m[:landwater_storage,      :lws_sea_level]
        gmsl = m[:global_sea_level,       :sea_level_rise]

        row = (
            post_idx     = i,
            slr_2050_cm  = isnothing(i_2050) ? NaN : 100 * (gmsl[i_2050] - gmsl[i_2000]),
            slr_2100_cm  = isnothing(i_2100) ? NaN : 100 * (gmsl[i_2100] - gmsl[i_2000]),
            ais_2100_cm  = isnothing(i_2100) ? NaN : 100 * (ais[i_2100]  - ais[i_2000]),
            gsic_2100_cm = isnothing(i_2100) ? NaN : 100 * (gsic[i_2100] - gsic[i_2000]),
            gis_2100_cm  = isnothing(i_2100) ? NaN : 100 * (gis[i_2100]  - gis[i_2000]),
            te_2100_cm   = isnothing(i_2100) ? NaN : 100 * (te[i_2100]   - te[i_2000]),
            lws_2100_cm  = isnothing(i_2100) ? NaN : 100 * (lws[i_2100]  - lws[i_2000]),
        )
        push!(out, row; cols=:subset, promote=true)

        if save_total
            for (t, c) in enumerate(slr_cols)
                out[end, c] = 100 * (gmsl[t] - gmsl[i_2000])
            end
        end
        if save_comp
            te_base   = te[i_2000]
            ais_base  = ais[i_2000]
            gis_base  = gis[i_2000]
            gsic_base = gsic[i_2000]
            lws_base  = lws[i_2000]
            for t in 1:n_yr
                out[end, te_cols[t]]   = 100 * (te[t]   - te_base)
                out[end, ais_cols[t]]  = 100 * (ais[t]  - ais_base)
                out[end, gis_cols[t]]  = 100 * (gis[t]  - gis_base)
                out[end, gsic_cols[t]] = 100 * (gsic[t] - gsic_base)
                out[end, lws_cols[t]]  = 100 * (lws[t]  - lws_base)
            end
            # Closure check on the first posterior draw: anchor on the last
            # year in the window so it fires regardless of the run horizon.
            if i == 1
                i_check = n_yr
                y_check = years_int[i_check]
                comp_sum = (ais[i_check] - ais_base) + (gsic[i_check] - gsic_base) +
                           (gis[i_check] - gis_base) + (te[i_check] - te_base) +
                           (lws[i_check] - lws_base)
                total    = gmsl[i_check] - gmsl[i_2000]
                resid    = total - comp_sum
                println("  closure check (post_idx=1, year=$y_check): total=$(round(total, digits=8)) m, " *
                        "Σcomp=$(round(comp_sum, digits=8)) m, residual=$(round(resid, sigdigits=3)) m")
                @assert abs(resid) < 1e-10 "Σ components ≠ total SLR (residual=$resid m)."
            end
        end

        if i % 500 == 0 || i == cap
            el = time() - t0
            println("  $i / $cap  ($(round(el, digits=1)) s, $(round(i/el, digits=1)) runs/s)")
        end
    end

    mkpath(dirname(args["output"]))
    CSV.write(args["output"], out)
    println("\nWrote $(args["output"])  ($(nrow(out)) rows)")

    if !isnothing(i_2100)
        println("\n=== Quick stats (year 2100, re-referenced to 2000) ===")
        for col in [:slr_2100_cm, :ais_2100_cm, :te_2100_cm, :gis_2100_cm, :gsic_2100_cm]
            v = sort(out[!, col])
            n = length(v)
            p5  = v[max(1, round(Int, 0.05 * n))]
            p50 = v[max(1, round(Int, 0.50 * n))]
            p95 = v[max(1, round(Int, 0.95 * n))]
            println("  $col:  median=$(round(p50, digits=2))  5th=$(round(p5, digits=2))  95th=$(round(p95, digits=2))")
        end
    end
end

main()
