## ============================================================================
## run_mimibrick_pulse_versioned.jl
##
## Version-aware BRICK flat-cube driver for the CO2/CH4 pulse->SLR study. ONE
## driver, ONE output schema for all THREE BRICK versions (so the downstream
## per-component marginal extractor never has to branch on version / drift):
##   --brick-version pre93   : MimiBRICK v1.2.1 (run in the julia_v121 env),
##                             single-reservoir glacier, pre-#93 35-col posterior,
##                             precip_log=FALSE (v1.2.1 uses linear precip0).
##   --brick-version brick2  : MimiBRICK v2.0.0 (julia_v2), single-reservoir
##                             glacier, post-#93 35-col posterior, precip_log=true.
##   --brick-version mengel  : v2.0.0 (julia_v2) + Mengel-2016 glacier swap
##                             (build_brick_mengel), 28-col mengel-ext posterior
##                             applied as 18 FREE params over a medoid central
##                             row (mirrors project_ssps_2100_mengel.jl).
##
## ENV: pre93 -> `julia --project=julia_v121`; brick2/mengel -> `--project=julia_v2`.
## The Mengel build code (v2.0.0 API) is include()d ONLY for --brick-version mengel,
## so the v1.2.1 env never touches it. Supersedes the schema-limited
## run_mimibrick_flatcube_v121.jl (which emitted components at 2100 only).
##
## This driver runs ONE cube (baseline OR a pulse arm) and writes per-cell SLR.
## The pulse MARGINAL is formed downstream (python/scripts/extract_pulse_marginals.py)
## by differencing the pulse-arm CSV against the baseline-arm CSV, per cell, /pulse-size.
## PAIRED DETERMINISM: run the baseline and pulse arms with the SAME --seed so the
## (non-deterministic) get_model()/build is bit-identical -> BRICK internal noise
## (~1e-5 m AIS) cancels in the difference, leaving the pure pulse signal.
## See ~/.claude/skills/mimibrick-quirks and the project handoff.
##
## Cube .npz schema (== flatcube.jl):
##   cells_meta Int64 (n,3) = (rff_idx, fair_cfg_idx, seed_idx)
##   years      Int64 (n_year,) ; gmst_traj/ohc_traj Float32 (n, n_year)
## Metadata CSV (REQUIRED cols): rff_idx, fair_cfg_idx, seed_idx, post_idx [+ axis]
##
## Output CSV: one row per metadata row; per-component + total SLR (cm, rel 2000)
## at 2100/2150/2300, plus optional GMSL history trajectory (--save-trajs) needed
## for the per-version Wong baseline fit.
## ============================================================================

using ArgParse
using CSV
using DataFrames
using Mimi
using MimiBRICK
using NPZ
using Random

include(joinpath(@__DIR__, "brick_param_updates.jl"))
# brick_mengel.jl defines the Mengel glacier Mimi @defcomp; it MUST be loaded at
# module scope (not lazily inside a function) or Mimi's run(m) hits a world-age
# MethodError on run_timestep_glaciers_mengel. Defining the component is harmless
# for pre93/brick2 (it is only *instantiated* via build_brick_mengel for mengel),
# and it loads cleanly under both v1.2.1 (julia_v121) and v2.0.0 (julia_v2).
include(joinpath(@__DIR__, "brick_mengel.jl"))   # build_brick_mengel / update_brick_mengel!

const CLOSURE_TOL_M = 1e-10

# Mengel: the 18 FREE physical params, in posterior-CSV column order
# (== project_ssps_2100_mengel.jl / calibrate_mcmc.jl FREE). The rest of the
# physical params are held at the medoid central row.
const MENGEL_PHYS = [
    (:antarctic_icesheet, :ais_ocean_temperature₀), (:antarctic_icesheet, :ais_α),
    (:antarctic_icesheet, :ais_ν), (:antarctic_icesheet, :temperature_threshold),
    (:antarctic_ocean, :anto_α), (:antarctic_ocean, :anto_β),
    (:greenland_icesheet, :greenland_a), (:greenland_icesheet, :greenland_b),
    (:greenland_icesheet, :greenland_α), (:greenland_icesheet, :greenland_β),
    (:greenland_icesheet, :greenland_v₀), (:thermal_expansion, :te_α),
    (:glaciers_small_icecaps, :gic_a), (:glaciers_small_icecaps, :gic_b),
    (:glaciers_small_icecaps, :gic_T_lia), (:glaciers_small_icecaps, :gic_f),
    (:glaciers_small_icecaps, :gic_tau_fast), (:glaciers_small_icecaps, :gic_tau_slow),
]
const MENGEL_PHYS_NAMES = ["ais_ocean_temperature₀","antarctic_alpha","antarctic_nu",
    "antarctic_temp_threshold","anto_alpha","anto_beta","greenland_a","greenland_b",
    "greenland_alpha","greenland_beta","greenland_v0","thermal_alpha","gic_a","gic_b",
    "gic_T_lia","gic_f","gic_tau_fast","gic_tau_slow"]
# default gic tuple for the medoid fixed-param pass (overwritten per draw; gic_sl0
# stays fixed at 0.0 -- it is NOT a free param).
const MENGEL_MEDOID_GIC = (a=0.45, b=0.52, T_lia=-0.45, f=0.5, tau_fast=40.0, tau_slow=250.0, sl0=0.0)

function parse_cli()
    s = ArgParseSettings()
    @add_arg_table! s begin
        "--cube";          required = true; help = ".npz with cells_meta, years, gmst_traj, ohc_traj"
        "--metadata";      required = true; help = "metadata CSV (rff_idx, fair_cfg_idx, seed_idx, post_idx)"
        "--posterior";     required = true; help = "MimiBRICK posterior CSV (brick2=35col, mengel=28col mengel-ext)"
        "--output";        required = true; help = "Output CSV"
        "--brick-version"; required = true; help = "brick2 | mengel"
        "--central-row";   default = joinpath(@__DIR__, "..", "outputs", "recalib_central_row.csv");
                           help = "mengel medoid central row (full-column) for fixed params"
        "--ssp";           default = "ssp245"; help = "v2.0.0 ssprcp_scenario (forcing is overridden by cube)"
        "--seed";          arg_type = Int; default = 2026
        "--start-year";    arg_type = Int; default = 1850
        "--end-year";      arg_type = Int; default = 2300
        "--save-trajs";           arg_type = Bool; default = false  # GMSL history (for Wong)
        "--save-component-trajs"; arg_type = Bool; default = false
        "--max-rows";      arg_type = Int; default = 0   # 0 = all
    end
    return parse_args(s)
end

function main()
    args = parse_cli()
    version = args["brick-version"]
    version in ("pre93", "brick2", "mengel") || error("--brick-version must be pre93 | brick2 | mengel (got '$version')")
    # AIS precip reparam: v1.2.1 (pre93) stores/uses LINEAR precip0 -> precip_log=false;
    # v2.0.0 (brick2/mengel) needs the log shim -> precip_log=true. See brick_param_updates.jl.
    precip_log = version != "pre93"
    Random.seed!(args["seed"])

    # ---- load cube ----
    println("Loading flat cube from ", args["cube"])
    cube = NPZ.npzread(args["cube"])
    cells_meta = Int.(cube["cells_meta"])
    years_cube = Int.(cube["years"])
    gmst       = Float64.(cube["gmst_traj"])
    ohc        = Float64.(cube["ohc_traj"])
    n_cells, n_yr_cube = size(gmst)
    @assert size(cells_meta) == (n_cells, 3) "cells_meta must be (n_cells,3); got $(size(cells_meta))"
    @assert size(ohc) == (n_cells, n_yr_cube)
    @assert length(years_cube) == n_yr_cube
    println("  cells: $n_cells, years $(years_cube[1])-$(years_cube[end])")

    cell_idx = Dict{Tuple{Int,Int,Int}, Int}()
    sizehint!(cell_idx, n_cells)
    for i in 1:n_cells
        cell_idx[(cells_meta[i,1], cells_meta[i,2], cells_meta[i,3])] = i
    end

    # ---- load metadata ----
    println("Loading metadata from ", args["metadata"])
    meta = DataFrame(CSV.File(args["metadata"]))
    for col in ("rff_idx", "fair_cfg_idx", "seed_idx", "post_idx")
        @assert col in names(meta) "metadata missing required column '$col'"
    end
    if args["max-rows"] > 0
        meta = meta[1:min(args["max-rows"], nrow(meta)), :]
    end
    n_rows = nrow(meta)
    has_axis = "axis" in names(meta)
    println("  metadata rows: $n_rows")

    # ---- load posterior ----
    println("Loading posterior from ", args["posterior"])
    posterior = DataFrame(CSV.File(args["posterior"]))
    n_post = nrow(posterior)
    println("  posterior members: $n_post")

    # ---- year window ----
    yr_start = max(args["start-year"], years_cube[1])
    yr_end   = min(args["end-year"],   years_cube[end])
    yr_window = collect(yr_start:yr_end)
    n_yr = length(yr_window)
    yr_to_cube_col = Dict(years_cube[i] => i for i in 1:n_yr_cube)
    yr_idx_window  = [yr_to_cube_col[y] for y in yr_window]
    i_2000 = findfirst(==(2000), yr_window)
    isnothing(i_2000) && error("Year window must include 2000 (re-baselining anchor).")
    i_2100 = findfirst(==(2100), yr_window)
    i_2150 = findfirst(==(2150), yr_window)
    i_2300 = findfirst(==(2300), yr_window)
    println("  year window: $yr_start-$yr_end ($n_yr yrs)")

    # ---- build BRICK model once (seed RNG immediately before for paired determinism) ----
    Random.seed!(args["seed"])
    if version == "mengel"
        println("Building BRICK-Mengel (v2.0.0 + glacier swap, ssprcp=$(args["ssp"]), $yr_start-$yr_end) ...")
        m = build_brick_mengel(ssp = args["ssp"], y0 = yr_start, y1 = yr_end)
        # fixed (non-free) params from the medoid central row, applied ONCE
        medoid = DataFrame(CSV.File(args["central-row"]))[1, :]
        update_brick_mengel!(m, medoid, MENGEL_MEDOID_GIC; precip_log = true)
        # validate the 18 free-param columns exist in the posterior
        for nm in MENGEL_PHYS_NAMES
            @assert nm in names(posterior) "mengel posterior missing free-param column '$nm'"
        end
    else  # pre93 (v1.2.1 env) or brick2 (v2.0.0 env): stock single-reservoir glacier
        label = version == "pre93" ? "MimiBRICK v1.2.1 (pre93)" : "MimiBRICK v2.0.0 (brick2)"
        println("Building $label, ssprcp=$(args["ssp"]), precip_log=$precip_log, $yr_start-$yr_end ...")
        m = MimiBRICK.get_model(ssprcp_scenario = args["ssp"], start_year = yr_start, end_year = yr_end)
    end

    save_trajs      = args["save-trajs"]
    save_comp_trajs = args["save-component-trajs"]

    # ---- output frame ----
    out = DataFrame(
        axis=String[], rff_idx=Int[], fair_cfg_idx=Int[], seed_idx=Int[], post_idx=Int[],
        slr_2100_cm=Float64[], slr_2150_cm=Float64[], slr_2300_cm=Float64[],
        ais_2100_cm=Float64[], gsic_2100_cm=Float64[], gis_2100_cm=Float64[],
        te_2100_cm=Float64[], lws_2100_cm=Float64[],
        ais_2150_cm=Float64[], gsic_2150_cm=Float64[], gis_2150_cm=Float64[],
        te_2150_cm=Float64[], lws_2150_cm=Float64[],
        ais_2300_cm=Float64[], gsic_2300_cm=Float64[], gis_2300_cm=Float64[],
        te_2300_cm=Float64[], lws_2300_cm=Float64[],
    )
    slr_cols = Symbol[]
    if save_trajs
        slr_cols = [Symbol("slr_$(y)") for y in yr_window]
        for c in slr_cols; out[!, c] = Float64[]; end
    end
    te_cols = ais_cols = gis_cols = gsic_cols = lws_cols = Symbol[]
    if save_comp_trajs
        te_cols   = [Symbol("te_$(y)")   for y in yr_window]
        ais_cols  = [Symbol("ais_$(y)")  for y in yr_window]
        gis_cols  = [Symbol("gis_$(y)")  for y in yr_window]
        gsic_cols = [Symbol("gsic_$(y)") for y in yr_window]
        lws_cols  = [Symbol("lws_$(y)")  for y in yr_window]
        for c in vcat(te_cols, ais_cols, gis_cols, gsic_cols, lws_cols); out[!, c] = Float64[]; end
    end

    rr(v, i, b) = isnothing(i) ? NaN : 100 * (v[i] - v[b])   # cm rel year-2000 index b

    # ---- main loop ----
    println("\nRunning BRICK-$version over $n_rows metadata rows ...")
    t0 = time(); n_missing_cell = 0
    for k in 1:n_rows
        rff_i  = Int(meta.rff_idx[k]); cfg_i = Int(meta.fair_cfg_idx[k])
        seed_i = Int(meta.seed_idx[k]); post_i = Int(meta.post_idx[k])   # 0-based
        cell_row = get(cell_idx, (rff_i, cfg_i, seed_i), 0)
        if cell_row == 0
            n_missing_cell += 1
            n_missing_cell <= 5 && println("  WARN: row $k missing cube cell (rff=$rff_i,cfg=$cfg_i,seed=$seed_i)")
            continue
        end
        post_idx_1b = post_i + 1
        @assert 1 ≤ post_idx_1b ≤ n_post "post_idx=$post_i out of [0,$(n_post-1)]"

        @inbounds gmst_traj = gmst[cell_row, yr_idx_window]
        @inbounds ohc_traj  = ohc[cell_row,  yr_idx_window]
        prow = posterior[post_idx_1b, :]

        if version == "mengel"   # update the 18 free params by name
            @inbounds for j in 1:length(MENGEL_PHYS)
                update_param!(m, MENGEL_PHYS[j][1], MENGEL_PHYS[j][2], Float64(prow[MENGEL_PHYS_NAMES[j]]))
            end
        else  # pre93 / brick2: full 35-col posterior row
            update_brick_params!(m, prow; precip_log = precip_log)
        end
        update_param!(m, :model_global_surface_temperature, gmst_traj)
        update_param!(m, :thermal_expansion, :ocean_heat_interior, ohc_traj)
        run(m)

        ais  = m[:antarctic_icesheet,     :ais_sea_level]
        gsic = m[:glaciers_small_icecaps, :gsic_sea_level]
        gis  = m[:greenland_icesheet,     :greenland_sea_level]
        te   = m[:thermal_expansion,      :te_sea_level]
        lws  = m[:landwater_storage,      :lws_sea_level]
        gmsl = m[:global_sea_level,       :sea_level_rise]

        push!(out, (
            axis = has_axis ? String(meta.axis[k]) : "",
            rff_idx=rff_i, fair_cfg_idx=cfg_i, seed_idx=seed_i, post_idx=post_i,
            slr_2100_cm=rr(gmsl,i_2100,i_2000), slr_2150_cm=rr(gmsl,i_2150,i_2000), slr_2300_cm=rr(gmsl,i_2300,i_2000),
            ais_2100_cm=rr(ais,i_2100,i_2000), gsic_2100_cm=rr(gsic,i_2100,i_2000), gis_2100_cm=rr(gis,i_2100,i_2000),
            te_2100_cm=rr(te,i_2100,i_2000), lws_2100_cm=rr(lws,i_2100,i_2000),
            ais_2150_cm=rr(ais,i_2150,i_2000), gsic_2150_cm=rr(gsic,i_2150,i_2000), gis_2150_cm=rr(gis,i_2150,i_2000),
            te_2150_cm=rr(te,i_2150,i_2000), lws_2150_cm=rr(lws,i_2150,i_2000),
            ais_2300_cm=rr(ais,i_2300,i_2000), gsic_2300_cm=rr(gsic,i_2300,i_2000), gis_2300_cm=rr(gis,i_2300,i_2000),
            te_2300_cm=rr(te,i_2300,i_2000), lws_2300_cm=rr(lws,i_2300,i_2000),
        ); cols=:subset, promote=true)

        if save_trajs
            base = gmsl[i_2000]
            for (t, c) in enumerate(slr_cols); out[end, c] = 100 * (gmsl[t] - base); end
        end
        if save_comp_trajs
            teb=te[i_2000]; aib=ais[i_2000]; gib=gis[i_2000]; gsb=gsic[i_2000]; lwb=lws[i_2000]
            for t in 1:n_yr
                out[end, te_cols[t]]=100*(te[t]-teb); out[end, ais_cols[t]]=100*(ais[t]-aib)
                out[end, gis_cols[t]]=100*(gis[t]-gib); out[end, gsic_cols[t]]=100*(gsic[t]-gsb)
                out[end, lws_cols[t]]=100*(lws[t]-lwb)
            end
        end

        # closure check on first successful run (anchor at last window year)
        if nrow(out) == 1
            ic = n_yr
            comp = (ais[ic]-ais[i_2000])+(gsic[ic]-gsic[i_2000])+(gis[ic]-gis[i_2000])+(te[ic]-te[i_2000])+(lws[ic]-lws[i_2000])
            tot  = gmsl[ic]-gmsl[i_2000]; resid = tot - comp
            println("  closure (year=$(yr_window[ic])): total=$(round(tot,digits=8)) Σcomp=$(round(comp,digits=8)) resid=$(round(resid,sigdigits=3)) m")
            @assert abs(resid) < CLOSURE_TOL_M "Σcomponents ≠ total SLR (resid=$resid m > tol=$CLOSURE_TOL_M)"
        end

        if k % 500 == 0 || k == n_rows
            el = time() - t0
            println("  $k / $n_rows  ($(round(el,digits=1)) s, $(round(k/el,digits=1)) runs/s)")
        end
    end

    n_missing_cell > 0 && println("\n!! $n_missing_cell metadata rows had no matching cube cell -- skipped.")
    mkpath(dirname(args["output"]))
    CSV.write(args["output"], out)
    println("\nWrote $(args["output"])  ($(nrow(out)) rows)  [version=$version]")

    if !isnothing(i_2100) && nrow(out) > 0
        println("\n=== Quick stats (2100, rel 2000) ===")
        for col in [:slr_2100_cm, :ais_2100_cm, :te_2100_cm, :gis_2100_cm, :gsic_2100_cm, :lws_2100_cm]
            v = sort(out[!, col]); n = length(v); n == 0 && continue
            p5=v[max(1,round(Int,0.05n))]; p50=v[max(1,round(Int,0.50n))]; p95=v[max(1,round(Int,0.95n))]
            println("  $col:  median=$(round(p50,digits=3))  5th=$(round(p5,digits=3))  95th=$(round(p95,digits=3))")
        end
    end
end

main()
