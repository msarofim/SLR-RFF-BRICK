## ============================================================================
## compute_lB_per_post_brick2.jl
##
## BRICK-v2.0.0 ("brick2") variant of compute_lB_per_post_v121.jl: per-posterior-
## member baseline log-likelihood l_B(theta_i) vs Dangendorf, for the Wong (2025)
## importance-weighting of the BRICK2 arm in the CO2/CH4 pulse->SLR study (Step 5).
##
## Identical in every respect to compute_lB_per_post_v121.jl EXCEPT:
##   1. The MimiBRICK model is built under the v2.0.0 get_model API (run this
##      script in the `julia_v2` project env, NOT julia_v121). The get_model
##      *signature* is the same (ssprcp_scenario="ssp245") in both versions.
##   2. `--precip-log` defaults to TRUE here: v2.0.0's AIS component takes
##      ais_precipitation₀ in LOG space, but the post-#93 35-col posterior stores
##      antarctic_precip0 in LINEAR units, so update_brick_params! must log-shim it
##      (exp(log(p)) = p reproduces v1.0.1 behaviour). See brick_param_updates.jl
##      and the run_mimibrick_pulse_versioned.jl Step-4 driver (precip_log = true
##      for brick2/mengel, false for pre93). Mirrors the brick2 backbone build
##      exactly so the Wong baseline l_B is consistent with the paired runs.
##   3. Defaults point at the post-#93 35-col posterior
##      (data/MimiBRICK/parameters_subsample_brick.csv) and output
##      outputs/brick_lB_per_post_brick2.csv.
##
## IMPORTANT: keep --obs in sync with apply_wong_weights.py (l_FB and l_B MUST be
## scored against the same observed series, or the weight ratio is meaningless).
## ============================================================================

using ArgParse
using CSV
using DataFrames
using Distributions
using LinearAlgebra
using Mimi
using MimiBRICK

# Shared BRICK-posterior-row updater (single source of truth; precip_log shim lives here).
include(joinpath(@__DIR__, "brick_param_updates.jl"))

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
function parse_cli()
    s = ArgParseSettings()
    @add_arg_table! s begin
        "--posterior";  default = "data/MimiBRICK/parameters_subsample_brick.csv"
        "--obs";        default = "dangendorf";  range_tester = x -> x in ("dangendorf", "csiro")
        "--obs-path";   default = ""             # empty => default per --obs
        "--output";     default = "outputs/brick_lB_per_post_brick2.csv"
        "--start-year"; arg_type = Int; default = 1850
        "--end-year";   arg_type = Int; default = 2100
        "--ssp";        default = "ssp245"  # v2.0.0 ssprcp_scenario (default backbone forcing)
        "--precip-log"; arg_type = Bool; default = true  # v2.0.0 AIS precip log-shim (see header)
        "--max-post";   arg_type = Int; default = 0   # 0 means "use all"
        "--post-idx-file"; default = ""     # CSV with a post_idx column; restrict l_B to these members
    end
    return parse_args(s)
end

# ---------------------------------------------------------------------------
# Heteroscedastic AR(1) log-likelihood (mirror of MimiBRICK's `hetero_logl_ar1`).
#   cov_matrix = sigma^2 / (1 - rho^2) * rho^|t_i - t_j| + Diagonal(obs_sigma^2)
#   log L = logpdf(MvNormal(cov_matrix), residuals)
# ---------------------------------------------------------------------------
function hetero_logl_ar1(residuals::Vector{Float64},
                         sigma::Float64,
                         rho::Float64,
                         obs_sigma::Vector{Float64})
    n = length(residuals)
    n == 0 && return 0.0
    process_var = sigma^2 / (1 - rho^2)
    H = abs.((1:n)' .- (1:n))
    cov_matrix = process_var .* (rho .^ H) .+ Diagonal(obs_sigma .^ 2)
    return try
        logpdf(MvNormal(cov_matrix), residuals)
    catch err
        @warn "MvNormal logpdf failed: $err — returning -Inf"
        -Inf
    end
end

# ---------------------------------------------------------------------------
# Load CSIRO Recons GMSL (years::Vector{Int}, gmsl_m, sigma_m) all in meters.
# ---------------------------------------------------------------------------
function load_csiro(path::String)
    raw = CSV.read(path, DataFrame; header = 10)
    time_col  = first(filter(c -> startswith(strip(string(c)), "Time"), names(raw)))
    gmsl_col  = first(filter(c -> occursin("GMSL (mm)", string(c)), names(raw)))
    sigma_col = first(filter(c -> occursin("sigma", lowercase(string(c))), names(raw)))
    years = floor.(Int, raw[!, time_col])
    gmsl_m  = Float64.(raw[!, gmsl_col])  ./ 1000.0
    sigma_m = Float64.(raw[!, sigma_col]) ./ 1000.0
    return years, gmsl_m, sigma_m
end

# ---------------------------------------------------------------------------
# Load Dangendorf et al. 2024 GMSL reconstruction (ESSD 16, 3471).
# ---------------------------------------------------------------------------
function load_dangendorf(path::String)
    raw = CSV.read(path, DataFrame)
    years   = Int.(raw[!, "year"])
    gmsl_m  = Float64.(raw[!, "value"]) ./ 1000.0
    sigma_m = Float64.(raw[!, "sigma"]) ./ 1000.0
    return years, gmsl_m, sigma_m
end

# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
function main()
    args = parse_cli()

    # -----------------------------------------------------------------------
    # 1. Load posterior parameters.
    # -----------------------------------------------------------------------
    println("Loading posterior from $(args["posterior"]) ...")
    posterior = DataFrame(CSV.File(args["posterior"]))
    n_post = nrow(posterior)
    println("  posterior: $n_post members")
    @assert "sd_gmsl"  in names(posterior)
    @assert "rho_gmsl" in names(posterior)

    cap = args["max-post"] > 0 ? min(args["max-post"], n_post) : n_post
    target_idx = if args["post-idx-file"] != ""
        want = sort(unique(Int.(DataFrame(CSV.File(args["post-idx-file"])).post_idx)))
        @assert minimum(want) >= 1 && maximum(want) <= n_post "post-idx-file has out-of-range members"
        println("  restricting to $(length(want)) post_idx from $(args["post-idx-file"]) (min $(minimum(want)), max $(maximum(want)))")
        want
    else
        collect(1:cap)
    end

    # -----------------------------------------------------------------------
    # 2. Load observed GMSL series.
    # -----------------------------------------------------------------------
    obs_source = args["obs"]
    obs_path   = if args["obs-path"] == ""
        obs_source == "dangendorf" ?
            "data/observations/dangendorf_2024_gmsl.csv" :
            "data/calibration/CSIRO_Recons_gmsl_yr_2015.csv"
    else
        args["obs-path"]
    end
    println("Loading obs ($obs_source) from $obs_path ...")
    obs_years, obs_gmsl_m, obs_sigma_m = if obs_source == "dangendorf"
        load_dangendorf(obs_path)
    else
        load_csiro(obs_path)
    end
    println("  obs years $(minimum(obs_years))-$(maximum(obs_years))  ($(length(obs_years)) rows)")

    i2000_obs = findfirst(==(2000), obs_years)
    i2000_obs === nothing && error("obs source '$obs_source' missing year 2000; cannot re-baseline.")
    obs_gmsl_m_2000  = obs_gmsl_m[i2000_obs]
    obs_sigma_m_2000 = obs_sigma_m[i2000_obs]

    # -----------------------------------------------------------------------
    # 3. Build the BRICK v2.0.0 model ONCE in default ssp245 mode (no FaIR
    #    overrides). Same get_model signature as v1.2.1; the package version is
    #    selected by the active project env (run under --project=julia_v2).
    # -----------------------------------------------------------------------
    yr_start = args["start-year"]
    yr_end   = args["end-year"]
    precip_log = args["precip-log"]
    println("Building MimiBRICK v2.0.0 model (ssprcp=$(args["ssp"]), precip_log=$precip_log, $yr_start-$yr_end) ...")
    m = MimiBRICK.get_model(
        ssprcp_scenario = args["ssp"],
        start_year      = yr_start,
        end_year        = yr_end,
    )

    model_years = collect(yr_start:yr_end)
    i2000_mod   = findfirst(==(2000), model_years)
    i2000_mod === nothing && error("Model year window does not include 2000.")

    overlap_years   = sort(intersect(obs_years, model_years))
    n_overlap       = length(overlap_years)
    @assert n_overlap > 0 "No overlap between obs years and model years."

    obs_idx_by_year = Dict(y => i for (i, y) in enumerate(obs_years))
    mod_idx_by_year = Dict(y => i for (i, y) in enumerate(model_years))
    overlap_obs_idx = [obs_idx_by_year[y] for y in overlap_years]
    overlap_mod_idx = [mod_idx_by_year[y] for y in overlap_years]

    obs_delta_m = obs_gmsl_m[overlap_obs_idx] .- obs_gmsl_m_2000
    obs_sigma_eff_m = sqrt.(obs_sigma_m[overlap_obs_idx] .^ 2 .+ obs_sigma_m_2000 ^ 2)
    println("  overlap years: $(overlap_years[1])-$(overlap_years[end])  ($n_overlap)")

    # -----------------------------------------------------------------------
    # 4. Loop over posterior members; compute l_B for each (precip_log shim on).
    # -----------------------------------------------------------------------
    println("Running BRICK v2.0.0 (default $(args["ssp"]) forcing) for each posterior member ...")
    ncompute = length(target_idx)
    l_B   = Vector{Float64}(undef, ncompute)
    pidx  = copy(target_idx)
    t0 = time()
    n_failed = 0
    for (k, i) in enumerate(target_idx)
        prow = posterior[i, :]
        sigma = Float64(prow.sd_gmsl)
        rho   = Float64(prow.rho_gmsl)
        try
            update_brick_params!(m, prow; precip_log = precip_log)
            run(m)
            gmsl = m[:global_sea_level, :sea_level_rise]   # METERS
            mod_delta_m = Float64.(gmsl[overlap_mod_idx]) .- Float64(gmsl[i2000_mod])
            residuals   = obs_delta_m .- mod_delta_m
            l_B[k] = hetero_logl_ar1(residuals, sigma, rho, obs_sigma_eff_m)
        catch err
            n_failed += 1
            @warn "post_idx=$i failed to run/score: $err"
            l_B[k] = -Inf
        end

        if k % 200 == 0 || k == ncompute
            el = time() - t0
            println("  $k / $ncompute  ($(round(el, digits=1))s, $(round(k/el, digits=2)) runs/s)")
        end
    end

    if n_failed > 0
        println("Note: $n_failed posterior member(s) failed; their l_B is -Inf.")
    end

    # -----------------------------------------------------------------------
    # 5. Write output CSV.
    # -----------------------------------------------------------------------
    out_df = DataFrame(post_idx = pidx, l_B_gmsl = l_B)
    outpath = args["output"]
    mkpath(dirname(outpath))
    CSV.write(outpath, out_df)
    println("\nWrote $outpath  ($(nrow(out_df)) rows)")

    finite = filter(isfinite, l_B)
    if !isempty(finite)
        sorted_l = sort(finite)
        n = length(sorted_l)
        p5  = sorted_l[max(1, round(Int, 0.05 * n))]
        p50 = sorted_l[max(1, round(Int, 0.50 * n))]
        p95 = sorted_l[max(1, round(Int, 0.95 * n))]
        println("l_B summary (finite values, n=$n):")
        println("  median=$(round(p50, digits=3))  p5=$(round(p5, digits=3))  p95=$(round(p95, digits=3))")
    end
end

main()
