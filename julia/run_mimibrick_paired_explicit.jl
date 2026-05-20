## ============================================================================
## run_mimibrick_paired_explicit.jl
##
## Explicit-tuple variant of run_mimibrick_paired_seeded.jl. Each metadata
## row specifies ONE BRICK draw via the full (rff_idx, fair_cfg_idx,
## seed_idx, post_idx) tuple. No seed multiplication, no random post pairing.
##
## Use cases:
##   - OFAT sensitivity (vary one axis at a time across the 4D parameter space)
##   - ANOVA-style 4-way variance decomposition (factorial design over the
##     same 4 axes, with replication in each so within-cell variance is
##     estimable per axis)
##
## Output: long-format CSV with one row per metadata row.
##
## Inputs:
##   --cube / --npy-stem:  FaIR cube — same as run_mimibrick_paired_seeded.jl
##   --metadata:    CSV with REQUIRED columns:
##                    rff_idx, fair_cfg_idx, seed_idx, post_idx
##                  Optional columns retained in output: sample, draw_id, axis
##   --posterior:   MimiBRICK posterior_subsample_brick.csv
##   --output:      Output CSV path
##   --seed:        RNG seed for MimiBRICK.get_model() determinism only
##   --start-year:  default 1850
##   --end-year:    default 2100
##   --rcp:         default RCP45
##   --save-trajs:  if true, write full year-by-year SLR
## ============================================================================

using ArgParse
using CSV
using DataFrames
using Distributions
using Mimi
using MimiBRICK
using NPZ
using Random
using Mmap

# Lightweight .npy reader that returns an Mmap-backed Array view. Avoids
# loading the entire file into RAM — only pages we touch are paged in.
function mmap_npy(path::String, T::DataType, shape::Tuple)
    io = open(path, "r")
    magic = read(io, 6)
    @assert magic == UInt8[0x93,0x4E,0x55,0x4D,0x50,0x59] "not a .npy file: $path"
    v_major = read(io, UInt8); read(io, UInt8)  # major.minor
    header_len = v_major == 1 ? Int(read(io, UInt16)) : Int(read(io, UInt32))
    skip(io, header_len)
    return Mmap.mmap(io, Array{T, length(shape)}, shape)
end

function parse_cli()
    s = ArgParseSettings()
    @add_arg_table! s begin
        "--cube";        required = true; help = "FaIR .npz cube (legacy); use --npy-stem instead"
        "--npy-stem";    default = "";    help = "Stem of pre-extracted .npy files "*
                                                  "(<stem>_gmst.npy, _ohc.npy, _years.npy, _rffs.npy). "*
                                                  "If set, --cube is ignored and we mmap these instead — "*
                                                  "peak memory drops from ~100 GB to ~2 GB."
        "--metadata";    required = true; help = "LHS metadata CSV"
        "--posterior";   required = true; help = "MimiBRICK posterior CSV"
        "--output";      required = true; help = "Output CSV"
        "--seed";        arg_type = Int; default = 2026
        "--start-year";  arg_type = Int; default = 1850
        "--end-year";    arg_type = Int; default = 2100
        "--rcp";         default = "RCP45"
        "--n-seeds";     arg_type = Int; default = 0   # 0 means use all from cube
        "--save-trajs";  arg_type = Bool; default = false
    end
    return parse_args(s)
end

function update_brick_params!(m, prow)
    update_param!(m, :antarctic_ocean, :anto_α, prow.anto_alpha)
    update_param!(m, :antarctic_ocean, :anto_β, prow.anto_beta)
    update_param!(m, :antarctic_icesheet, :ais_sea_level₀,             prow.antarctic_s0)
    update_param!(m, :antarctic_icesheet, :ais_bedheight₀,             prow.antarctic_bed_height0)
    update_param!(m, :antarctic_icesheet, :ais_slope,                  prow.antarctic_slope)
    update_param!(m, :antarctic_icesheet, :ais_μ,                      prow.antarctic_mu)
    update_param!(m, :antarctic_icesheet, :ais_runoffline_snowheight₀, prow.antarctic_runoff_height0)
    update_param!(m, :antarctic_icesheet, :ais_c,                      prow.antarctic_c)
    update_param!(m, :antarctic_icesheet, :ais_precipitation₀,         prow.antarctic_precip0)
    update_param!(m, :antarctic_icesheet, :ais_κ,                      prow.antarctic_kappa)
    update_param!(m, :antarctic_icesheet, :ais_ν,                      prow.antarctic_nu)
    update_param!(m, :antarctic_icesheet, :ais_iceflow₀,               prow.antarctic_flow0)
    update_param!(m, :antarctic_icesheet, :ais_γ,                      prow.antarctic_gamma)
    update_param!(m, :antarctic_icesheet, :ais_α,                      prow.antarctic_alpha)
    update_param!(m, :antarctic_icesheet, :temperature_threshold,      prow.antarctic_temp_threshold)
    update_param!(m, :antarctic_icesheet, :λ,                          prow.antarctic_lambda)
    update_param!(m, :glaciers_small_icecaps, :gsic_β₀, prow.glaciers_beta0)
    update_param!(m, :glaciers_small_icecaps, :gsic_v₀, prow.glaciers_v0)
    update_param!(m, :glaciers_small_icecaps, :gsic_s₀, prow.glaciers_s0)
    update_param!(m, :glaciers_small_icecaps, :gsic_n,  prow.glaciers_n)
    update_param!(m, :greenland_icesheet, :greenland_a, prow.greenland_a)
    update_param!(m, :greenland_icesheet, :greenland_b, prow.greenland_b)
    update_param!(m, :greenland_icesheet, :greenland_α, prow.greenland_alpha)
    update_param!(m, :greenland_icesheet, :greenland_β, prow.greenland_beta)
    update_param!(m, :greenland_icesheet, :greenland_v₀, prow.greenland_v0)
    update_param!(m, :thermal_expansion, :te_α,  prow.thermal_alpha)
    update_param!(m, :thermal_expansion, :te_s₀, prow.thermal_s0)
end

function main()
    args = parse_cli()
    rng = MersenneTwister(args["seed"])

    if !isempty(args["npy-stem"])
        stem = args["npy-stem"]
        println("mmap'ing pre-extracted .npy files from stem '$stem' ...")
        # Read metadata (small) then mmap the big ones
        years_cube = Int.(NPZ.npzread(stem * "_years.npy"))
        rffs_cube  = Int.(NPZ.npzread(stem * "_rffs.npy"))
        # mmap needs shape — derive from the metadata + known FaIR config count.
        # Cube is (n_rff, n_cfg, n_seed, n_year). We know n_rff from rffs file.
        # n_cfg = 841 (FaIR v1.4.1 posterior), n_seed = 10, n_year = len(years).
        # Use file size to verify so we don't silently mmap wrong shape.
        n_rff_cube  = length(rffs_cube)
        n_yr_cube   = length(years_cube)
        gmst_path   = stem * "_gmst.npy"
        # Probe expected n_cfg × n_seed from file size:
        floats_per_rff = (filesize(gmst_path) - 128) ÷ (n_rff_cube * 4)
        # floats_per_rff = n_cfg * n_seed * n_year (FaIR v1.4.1 has n_cfg = 841)
        n_seed_guess = if floats_per_rff % (841 * n_yr_cube) == 0
            floats_per_rff ÷ (841 * n_yr_cube)
        else
            1
        end
        n_cfg_cube  = 841
        n_seed_cube = n_seed_guess
        cube_shape = (n_rff_cube, n_cfg_cube, n_seed_cube, n_yr_cube)
        println("  inferred cube shape: $cube_shape")
        # NumPy .npy files are C-order; Julia default is Fortran-order.
        # Mmap with reversed shape, then PermutedDimsArray gives a zero-copy
        # view with the original (rff, cfg, seed, year) indexing semantics.
        gmst_raw = mmap_npy(gmst_path, Float32, reverse(cube_shape))
        ohc_raw  = mmap_npy(stem * "_ohc.npy", Float32, reverse(cube_shape))
        gmst_cube = PermutedDimsArray(gmst_raw, (4, 3, 2, 1))
        ohc_cube  = PermutedDimsArray(ohc_raw,  (4, 3, 2, 1))
        println("  mmap'd gmst + ohc (with C-order permutation)")
    else
        println("Loading FaIR cube from ", args["cube"], " (full decompress) ...")
        cube       = NPZ.npzread(args["cube"])
        years_cube = Int.(cube["years"])
        rffs_cube  = Int.(cube["unique_rffs"])
        gmst_cube  = cube["gmst_traj_rff"]
        ohc_cube   = cube["ohc_traj_rff"]
        n_rff_cube, n_cfg_cube, n_seed_cube, n_yr_cube = size(gmst_cube)
    end
    @assert ndims(gmst_cube) == 4 "Expected 4D cube (rff,cfg,seed,year); got $(ndims(gmst_cube))D"
    println("  cube: gmst $(size(gmst_cube)), years $(years_cube[1])-$(years_cube[end])")

    n_seeds_use = args["n-seeds"] > 0 ? min(args["n-seeds"], n_seed_cube) : n_seed_cube

    println("Loading metadata from ", args["metadata"], " ...")
    meta = DataFrame(CSV.File(args["metadata"]))
    n_rows = nrow(meta)
    println("  metadata: $n_rows explicit-tuple rows")
    @assert "rff_idx"      in names(meta)
    @assert "fair_cfg_idx" in names(meta)
    @assert "seed_idx"     in names(meta)  "metadata must have seed_idx column"
    @assert "post_idx"     in names(meta)  "metadata must have post_idx column"

    println("Loading MimiBRICK posterior from ", args["posterior"], " ...")
    posterior = DataFrame(CSV.File(args["posterior"]))
    n_post = nrow(posterior)
    println("  posterior: $n_post members")

    # Build cube-row lookup: rff_idx -> position in cube
    rff_to_cube_row = Dict{Int,Int}()
    for (i, r) in enumerate(rffs_cube)
        rff_to_cube_row[r] = i
    end

    # Year window: clip to cube's available range, then intersect with [start,end] args
    yr_window = max(args["start-year"], years_cube[1]):min(args["end-year"], years_cube[end])
    yr_idx_window = [findfirst(==(y), years_cube) for y in yr_window]
    i_2000 = findfirst(==(2000), collect(yr_window))
    i_2050 = findfirst(==(2050), collect(yr_window))
    i_2100 = findfirst(==(2100), collect(yr_window))
    # Phase C: may also report 2150 and 2300. nothing if year is outside window.
    i_2150 = findfirst(==(2150), collect(yr_window))
    i_2300 = findfirst(==(2300), collect(yr_window))
    println("  year window: $(yr_window[1])-$(yr_window[end])  ($(length(yr_window)) yrs)")

    # Build base BRICK model once; parameter updates replace fields between runs.
    # CRITICAL: MimiBRICK.get_model() has internal non-determinism (some derived
    # variable seeded from the global RNG). To make baseline / pulse / vehicle
    # runs across separate script invocations have IDENTICAL initial model state,
    # we seed Julia's global RNG deterministically right before the build call.
    # Without this, different invocations produce ~1e-5 m offsets in AIS_2100
    # that swamp the marginal pulse signal we care about for SCC analysis.
    Random.seed!(args["seed"])
    println("Building MimiBRICK model (rcp=$(args["rcp"]))...")
    m = MimiBRICK.get_model(
        rcp_scenario = args["rcp"],
        start_year   = yr_window[1],
        end_year     = yr_window[end],
    )

    # One BRICK call per metadata row (explicit tuple).
    n_total = n_rows
    println("\nWill run $n_total BRICK draws (explicit tuples)")

    has_axis = "axis" in names(meta)

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
    )

    save_trajs = args["save-trajs"]
    traj_cols = Symbol[]
    if save_trajs
        traj_cols = [Symbol(string(y)) for y in yr_window]
        for c in traj_cols
            out[!, c] = Float64[]
        end
    end

    println("Running BRICK over $n_total explicit tuples...")
    t0 = time()
    for k in 1:n_total
        rff_idx = Int(meta.rff_idx[k])
        cfg_idx = Int(meta.fair_cfg_idx[k])     # 0-based (Python convention)
        seed_idx = Int(meta.seed_idx[k])        # 0-based
        post_idx = Int(meta.post_idx[k])        # 1-based (Julia / posterior CSV convention)

        cube_row = rff_to_cube_row[rff_idx]
        cube_cfg = cfg_idx + 1                  # 1-based for the Julia cube
        cube_seed = seed_idx + 1                # 1-based for the Julia cube
        @assert cube_cfg ≥ 1 && cube_cfg ≤ n_cfg_cube
        @assert cube_seed ≥ 1 && cube_seed ≤ n_seed_cube  "seed_idx $seed_idx out of [0, $(n_seed_cube-1)]"
        @assert post_idx ≥ 1 && post_idx ≤ n_post         "post_idx $post_idx out of [1, $n_post]"

        gmst_traj = Float64.(gmst_cube[cube_row, cube_cfg, cube_seed, yr_idx_window])
        ohc_traj  = Float64.(ohc_cube[cube_row,  cube_cfg, cube_seed, yr_idx_window])

        prow = posterior[post_idx, :]
        update_brick_params!(m, prow)
        update_param!(m, :model_global_surface_temperature, gmst_traj)
        update_param!(m, :thermal_expansion, :ocean_heat_interior, ohc_traj)

        run(m)

        ais  = m[:antarctic_icesheet,     :ais_sea_level]
        gsic = m[:glaciers_small_icecaps, :gsic_sea_level]
        gis  = m[:greenland_icesheet,     :greenland_sea_level]
        te   = m[:thermal_expansion,      :te_sea_level]
        gmsl = m[:global_sea_level,       :sea_level_rise]

        row = (
            axis          = has_axis ? String(meta.axis[k]) : "",
            rff_idx       = rff_idx,
            fair_cfg_idx  = cfg_idx,
            seed_idx      = seed_idx,
            post_idx      = post_idx,
            slr_2050_cm   = 100 * (gmsl[i_2050] - gmsl[i_2000]),
            slr_2100_cm   = 100 * (gmsl[i_2100] - gmsl[i_2000]),
            slr_2150_cm   = isnothing(i_2150) ? NaN : 100 * (gmsl[i_2150] - gmsl[i_2000]),
            slr_2300_cm   = isnothing(i_2300) ? NaN : 100 * (gmsl[i_2300] - gmsl[i_2000]),
            ais_2100_cm   = 100 * (ais[i_2100]  - ais[i_2000]),
            gsic_2100_cm  = 100 * (gsic[i_2100] - gsic[i_2000]),
            gis_2100_cm   = 100 * (gis[i_2100]  - gis[i_2000]),
            te_2100_cm    = 100 * (te[i_2100]   - te[i_2000]),
        )
        push!(out, row; cols=:subset, promote=true)
        if save_trajs
            for (t, c) in enumerate(traj_cols)
                out[end, c] = 100 * (gmsl[t] - gmsl[i_2000])
            end
        end

        if k % 500 == 0 || k == n_total
            el = time() - t0
            println("  $k / $n_total  ($(round(el, digits=1)) s, $(round(k/el, digits=1)) runs/s)")
        end
    end

    CSV.write(args["output"], out)
    println("\nWrote ", args["output"], " ($n_total rows)")

    println("\n=== Quick stats by axis ===")
    for ax in unique(out.axis)
        sub = out[out.axis .== ax, :]
        nrow(sub) == 0 && continue
        println("\n[axis=$ax] n=", nrow(sub))
        for col in [:slr_2100_cm, :ais_2100_cm, :te_2100_cm]
            v = sort(sub[!, col])
            n = length(v)
            p5  = v[max(1, round(Int, 0.05 * n))]
            p50 = v[max(1, round(Int, 0.50 * n))]
            p95 = v[max(1, round(Int, 0.95 * n))]
            println("  $col:  median=$(round(p50, digits=2))  5th=$(round(p5, digits=2))  95th=$(round(p95, digits=2))")
        end
    end
end

main()
