## ============================================================================
## run_mimibrick_flatcube.jl
##
## BRICK driver for the FaIRtoFrEDI v1.4.5 *flat-cube* schema. Each FaIR cube
## is stored as a flat (n_cells, n_year) layout with a cells_meta lookup
## table — replacing the older rectangular (n_rff, n_cfg, n_seed, n_year)
## layout that exploded compute by ~270×.
##
## Cube .npz contents (keys, dtypes, shapes):
##   cells_meta  Int64   (n_cells, 3)    cols = (rff_idx, fair_cfg_idx, seed_idx)
##   years       Int64   (n_year,)       e.g. 1850..2300
##   gmst_traj   Float32 (n_cells, n_year)
##   ohc_traj    Float32 (n_cells, n_year)
##   erf_2100    Float32 (n_cells,)      (informational; not used here)
##
## Metadata CSV columns (REQUIRED): rff_idx, fair_cfg_idx, seed_idx, post_idx
## Optional: axis (string), sample, draw_id — passed through to output.
##
## Trajectory selection: build a Dict (rff,cfg,seed) → row index in the cube
## once at startup. For each metadata row, look up the cell row, slice its
## (gmst, ohc) trajectories, and run BRICK with posterior[post_idx + 1]
## (BRICK posterior is 1-based in Julia; metadata post_idx is 0-based to
## match the rest of the pipeline). Output schema mirrors the explicit
## (rectangular-cube) driver so downstream Wong-weighting / H-S plotting
## code does NOT need to branch on cube layout.
##
## Output CSV: one row per metadata row, with summary cols
## (slr_2050_cm, slr_2100_cm, slr_2150_cm, slr_2300_cm, ais/gsic/gis/te_2100_cm)
## and optional per-year per-component trajectories (te_<y>, ais_<y>, gis_<y>,
## gsic_<y>, lws_<y>) plus total slr_<y> = sum check.
## ============================================================================

using ArgParse
using CSV
using DataFrames
using Mimi
using MimiBRICK
using NPZ
using Random

# Shared 27-parameter BRICK-posterior-row updater. Single source of truth
# across all four BRICK drivers — see julia/brick_param_updates.jl.
include(joinpath(@__DIR__, "brick_param_updates.jl"))

function parse_cli()
    s = ArgParseSettings()
    @add_arg_table! s begin
        "--cube";       required = true; help = ".npz with cells_meta, years, gmst_traj, ohc_traj"
        "--metadata";   required = true; help = "metadata CSV (rff_idx, fair_cfg_idx, seed_idx, post_idx)"
        "--posterior";  required = true; help = "MimiBRICK posterior CSV (parameters_subsample_brick.csv)"
        "--output";     required = true; help = "Output CSV"
        "--seed";       arg_type = Int;  default = 2026
        "--start-year"; arg_type = Int;  default = 1850
        "--end-year";   arg_type = Int;  default = 2300
        "--rcp";        default = "RCP45"
        "--save-trajs";           arg_type = Bool; default = false
        "--save-component-trajs"; arg_type = Bool; default = true
        "--max-rows";   arg_type = Int;  default = 0   # 0 = all
    end
    return parse_args(s)
end

function main()
    args = parse_cli()
    Random.seed!(args["seed"])

    # ---- load cube ----
    println("Loading flat cube from ", args["cube"])
    cube = NPZ.npzread(args["cube"])
    cells_meta = Int.(cube["cells_meta"])
    years_cube = Int.(cube["years"])
    gmst       = Float64.(cube["gmst_traj"])
    ohc        = Float64.(cube["ohc_traj"])
    n_cells, n_yr_cube = size(gmst)
    @assert size(cells_meta) == (n_cells, 3) "cells_meta must be (n_cells, 3); got $(size(cells_meta))"
    @assert size(ohc) == (n_cells, n_yr_cube)
    @assert length(years_cube) == n_yr_cube
    println("  cells: $n_cells, years $(years_cube[1])-$(years_cube[end])")

    # cell lookup: (rff, cfg, seed) -> row index (1-based)
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
    n_rows_meta = nrow(meta)
    if args["max-rows"] > 0
        cap = min(args["max-rows"], n_rows_meta)
        meta = meta[1:cap, :]
    end
    n_rows = nrow(meta)
    println("  metadata rows: $n_rows")
    has_axis = "axis" in names(meta)

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
    isnothing(i_2000) && error("Year window $yr_start-$yr_end must include 2000 (re-baselining anchor).")
    i_2050 = findfirst(==(2050), yr_window)
    i_2100 = findfirst(==(2100), yr_window)
    i_2150 = findfirst(==(2150), yr_window)
    i_2300 = findfirst(==(2300), yr_window)
    println("  year window: $yr_start-$yr_end ($n_yr yrs)")

    # ---- build BRICK model once ----
    # Seed Julia's RNG immediately before get_model() to make different script
    # invocations deterministic (see mimibrick-quirks skill: get_model has
    # internal non-determinism). Critical for paired baseline/pulse arms.
    Random.seed!(args["seed"])
    println("Building MimiBRICK model (rcp=$(args["rcp"]), $yr_start-$yr_end) ...")
    m = MimiBRICK.get_model(
        rcp_scenario = args["rcp"],
        start_year   = yr_start,
        end_year     = yr_end,
    )

    save_trajs      = args["save-trajs"]
    save_comp_trajs = args["save-component-trajs"]

    # ---- output frame ----
    out = DataFrame(
        axis          = String[],
        rff_idx       = Int[],
        fair_cfg_idx  = Int[],
        seed_idx      = Int[],
        post_idx      = Int[],
        slr_2050_cm   = Float64[],
        slr_2100_cm   = Float64[],
        slr_2150_cm   = Float64[],
        slr_2300_cm   = Float64[],
        ais_2100_cm   = Float64[],
        gsic_2100_cm  = Float64[],
        gis_2100_cm   = Float64[],
        te_2100_cm    = Float64[],
        lws_2100_cm   = Float64[],
    )

    slr_cols  = Symbol[]
    te_cols   = Symbol[]
    ais_cols  = Symbol[]
    gis_cols  = Symbol[]
    gsic_cols = Symbol[]
    lws_cols  = Symbol[]
    if save_trajs
        slr_cols = [Symbol("slr_$(y)") for y in yr_window]
        for c in slr_cols; out[!, c] = Float64[]; end
    end
    if save_comp_trajs
        te_cols   = [Symbol("te_$(y)")   for y in yr_window]
        ais_cols  = [Symbol("ais_$(y)")  for y in yr_window]
        gis_cols  = [Symbol("gis_$(y)")  for y in yr_window]
        gsic_cols = [Symbol("gsic_$(y)") for y in yr_window]
        lws_cols  = [Symbol("lws_$(y)")  for y in yr_window]
        for c in vcat(te_cols, ais_cols, gis_cols, gsic_cols, lws_cols)
            out[!, c] = Float64[]
        end
    end

    # ---- main loop ----
    println("\nRunning BRICK over $n_rows metadata rows ...")
    t0 = time()
    n_missing_cell = 0
    for k in 1:n_rows
        rff_i  = Int(meta.rff_idx[k])
        cfg_i  = Int(meta.fair_cfg_idx[k])
        seed_i = Int(meta.seed_idx[k])
        post_i = Int(meta.post_idx[k])          # 0-based in metadata

        cell_row = get(cell_idx, (rff_i, cfg_i, seed_i), 0)
        if cell_row == 0
            n_missing_cell += 1
            if n_missing_cell <= 5
                println("  WARN: row $k missing cube cell (rff=$rff_i, cfg=$cfg_i, seed=$seed_i)")
            end
            continue
        end
        post_idx_1b = post_i + 1                # 1-based for Julia / posterior CSV
        @assert post_idx_1b ≥ 1 && post_idx_1b ≤ n_post  "post_idx=$post_i out of [0, $(n_post-1)]"

        # mmap-friendly views into the cube; gmst/ohc are already Float64.
        @inbounds gmst_traj = gmst[cell_row, yr_idx_window]
        @inbounds ohc_traj  = ohc[cell_row,  yr_idx_window]

        prow = posterior[post_idx_1b, :]
        update_brick_params!(m, prow)
        update_param!(m, :model_global_surface_temperature, gmst_traj)
        update_param!(m, :thermal_expansion, :ocean_heat_interior, ohc_traj)
        run(m)

        ais  = m[:antarctic_icesheet,     :ais_sea_level]
        gsic = m[:glaciers_small_icecaps, :gsic_sea_level]
        gis  = m[:greenland_icesheet,     :greenland_sea_level]
        te   = m[:thermal_expansion,      :te_sea_level]
        lws  = m[:landwater_storage,      :lws_sea_level]
        gmsl = m[:global_sea_level,       :sea_level_rise]

        row = (
            axis          = has_axis ? String(meta.axis[k]) : "",
            rff_idx       = rff_i,
            fair_cfg_idx  = cfg_i,
            seed_idx      = seed_i,
            post_idx      = post_i,
            slr_2050_cm   = isnothing(i_2050) ? NaN : 100 * (gmsl[i_2050] - gmsl[i_2000]),
            slr_2100_cm   = isnothing(i_2100) ? NaN : 100 * (gmsl[i_2100] - gmsl[i_2000]),
            slr_2150_cm   = isnothing(i_2150) ? NaN : 100 * (gmsl[i_2150] - gmsl[i_2000]),
            slr_2300_cm   = isnothing(i_2300) ? NaN : 100 * (gmsl[i_2300] - gmsl[i_2000]),
            ais_2100_cm   = isnothing(i_2100) ? NaN : 100 * (ais[i_2100]  - ais[i_2000]),
            gsic_2100_cm  = isnothing(i_2100) ? NaN : 100 * (gsic[i_2100] - gsic[i_2000]),
            gis_2100_cm   = isnothing(i_2100) ? NaN : 100 * (gis[i_2100]  - gis[i_2000]),
            te_2100_cm    = isnothing(i_2100) ? NaN : 100 * (te[i_2100]   - te[i_2000]),
            lws_2100_cm   = isnothing(i_2100) ? NaN : 100 * (lws[i_2100]  - lws[i_2000]),
        )
        push!(out, row; cols=:subset, promote=true)

        if save_trajs
            base = gmsl[i_2000]
            for (t, c) in enumerate(slr_cols)
                out[end, c] = 100 * (gmsl[t] - base)
            end
        end
        if save_comp_trajs
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
            # Closure check on the FIRST run only (anchor at last year of
            # window so it always fires). BRICK :global_sea_level sums five
            # contributors; residual >1e-10 m means BRICK internals changed
            # or LWS was dropped — fail loudly before writing a misleading CSV.
            if k == 1
                i_check = n_yr
                y_check = yr_window[i_check]
                comp_sum = (ais[i_check] - ais_base) + (gsic[i_check] - gsic_base) +
                           (gis[i_check] - gis_base) + (te[i_check] - te_base) +
                           (lws[i_check] - lws_base)
                total    = gmsl[i_check] - gmsl[i_2000]
                resid    = total - comp_sum
                println("  closure check (k=1, year=$y_check): " *
                        "total=$(round(total, digits=8)) m  " *
                        "Σcomp=$(round(comp_sum, digits=8)) m  " *
                        "residual=$(round(resid, sigdigits=3)) m")
                @assert abs(resid) < 1e-10 "Σ components ≠ total SLR (residual=$resid m). "
            end
        end

        if k % 500 == 0 || k == n_rows
            el = time() - t0
            println("  $k / $n_rows  ($(round(el, digits=1)) s, $(round(k/el, digits=1)) runs/s)")
        end
    end

    if n_missing_cell > 0
        println("\n!! $n_missing_cell metadata rows had no matching cube cell — those were skipped.")
    end

    mkpath(dirname(args["output"]))
    CSV.write(args["output"], out)
    println("\nWrote $(args["output"])  ($(nrow(out)) rows)")

    # Quick stats so a Slurm tail-of-log shows what landed.
    if !isnothing(i_2100)
        println("\n=== Quick stats (year 2100, re-referenced to 2000) ===")
        for col in [:slr_2100_cm, :ais_2100_cm, :te_2100_cm, :gis_2100_cm, :gsic_2100_cm, :lws_2100_cm]
            v = sort(out[!, col])
            n = length(v)
            n == 0 && continue
            p5  = v[max(1, round(Int, 0.05 * n))]
            p50 = v[max(1, round(Int, 0.50 * n))]
            p95 = v[max(1, round(Int, 0.95 * n))]
            println("  $col:  median=$(round(p50, digits=2))  5th=$(round(p5, digits=2))  95th=$(round(p95, digits=2))")
        end
    end
end

main()
