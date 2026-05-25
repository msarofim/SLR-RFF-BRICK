## ============================================================================
## compute_lB_per_post.jl
##
## Compute per-posterior-member baseline log-likelihoods l_B(theta_i) for the
## Wong (2025) importance-weighting scheme. For every BRICK posterior member
## i in 1..N_post, we:
##
##   1. Build a MimiBRICK model in its DEFAULT non-FaIR configuration
##      (RCP4.5 forcing, BRICK's own GMST/OHC backbone — i.e. NO
##      :model_global_surface_temperature override, NO :ocean_heat_interior
##      override). This is "BRICK as calibrated".
##   2. Apply that posterior member's full physical parameter vector
##      (anto_alpha/beta, ais_*, gsic_*, greenland_*, te_*) via the same
##      update_brick_params! routine used by the paired driver.
##   3. Run the model, extract the modeled gmsl[year] trajectory (in meters).
##   4. Re-reference modeled and observed series to year 2000 (so this is
##      consistent with the paired CSV's 2000-baseline convention; the Python
##      script must use the same convention -- it does).
##   5. Compute the heteroscedastic AR(1) log-likelihood vs the observed GMSL
##      series, using BRICK's own `hetero_logl_ar1` form:
##
##         cov = sigma_gmsl^2 / (1 - rho_gmsl^2) * rho_gmsl^|t_i - t_j|
##                 + Diagonal(eps_t^2)
##         log L = logpdf(MvNormal(cov), residuals)
##
##      with sigma_gmsl = posterior `sd_gmsl`, rho_gmsl = posterior `rho_gmsl`,
##      and eps_t = the per-year observed 1-sigma uncertainty inflated to
##      account for re-baselining (sqrt(sigma_t^2 + sigma_2000^2)).
##      Default obs source: Dangendorf et al. 2024 (ESSD 16, 3471).  Use
##      --obs csiro for the legacy CSIRO Recons series.
##   6. Write `outputs/brick_lB_per_post.csv` with columns:
##      post_idx (1-based), l_B_gmsl.
##
## IMPORTANT: keep this script's --obs argument in sync with the
## apply_wong_weights.py --obs argument.  l_FB (from Python) and l_B (from
## here) MUST be computed against the same observed series, or the weight
## ratio (l_FB - l_B) is meaningless.
##
## Why "default RCP4.5 mode": Wong's vehicle paper uses the BRICK posterior's
## native climate forcing as the "baseline" against which the alternative
## (here FaIR-derived) forcing is judged. BRICK's default backbone is SNEASY
## driven by an RCP scenario; the posterior was calibrated under that backbone,
## so its sd_gmsl/rho_gmsl values are the right scales for residuals from
## that same setup.
##
## CLI
## ---
##   --posterior   PATH   BRICK posterior CSV (default
##                        data/MimiBRICK/parameters_subsample_brick.csv)
##   --obs         STR    Observed GMSL source: "dangendorf" (default) or "csiro"
##   --obs-path    PATH   Override the obs CSV path.  Defaults:
##                          dangendorf -> data/observations/dangendorf_2024_gmsl.csv
##                          csiro      -> data/calibration/CSIRO_Recons_gmsl_yr_2015.csv
##   --output      PATH   output CSV (default outputs/brick_lB_per_post.csv)
##   --start-year  INT    default 1850
##   --end-year    INT    default 2100
##   --rcp         STR    default "RCP45"
##   --max-post    INT    cap on number of posterior members (0 = all)
## ============================================================================

using ArgParse
using CSV
using DataFrames
using Distributions
using LinearAlgebra
using Mimi
using MimiBRICK

# Shared BRICK-posterior-row updater (extracted 2026-05-25).
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
        "--output";     default = "outputs/brick_lB_per_post.csv"
        "--start-year"; arg_type = Int; default = 1850
        "--end-year";   arg_type = Int; default = 2100
        "--rcp";        default = "RCP45"
        "--max-post";   arg_type = Int; default = 0   # 0 means "use all"
    end
    return parse_args(s)
end

# ---------------------------------------------------------------------------
# Heteroscedastic AR(1) log-likelihood (mirror of MimiBRICK's
# `hetero_logl_ar1`, but written here so we don't depend on internals.)
#
#   cov_matrix = sigma^2 / (1 - rho^2) * rho^|t_i - t_j| + Diagonal(obs_sigma^2)
#   log L = logpdf(MvNormal(cov_matrix), residuals)
# ---------------------------------------------------------------------------
function hetero_logl_ar1(residuals::Vector{Float64},
                         sigma::Float64,
                         rho::Float64,
                         obs_sigma::Vector{Float64})
    n = length(residuals)
    n == 0 && return 0.0
    # Stationary AR(1) process variance.
    process_var = sigma^2 / (1 - rho^2)
    # Lag matrix |i - j|.
    H = abs.((1:n)' .- (1:n))
    cov_matrix = process_var .* (rho .^ H) .+ Diagonal(obs_sigma .^ 2)
    return try
        logpdf(MvNormal(cov_matrix), residuals)
    catch err
        # Numerical issues -> return -Inf so the weight is effectively 0.
        @warn "MvNormal logpdf failed: $err — returning -Inf"
        -Inf
    end
end

# ---------------------------------------------------------------------------
# Load CSIRO Recons GMSL, return (years::Vector{Int}, gmsl_m, sigma_m) all in meters.
# Skip the first 9 lines (header comments starting with '#'), then the next
# row is the column header "Time, GMSL (mm), GMSL 1-sigma uncertainty (mm)".
# Time stamps are half-years (e.g. 1880.5) — floor to int per BRICK convention.
# ---------------------------------------------------------------------------
function load_csiro(path::String)
    raw = CSV.read(path, DataFrame; header = 10)
    # Column names may include a trailing space; strip via lookup.
    time_col  = first(filter(c -> startswith(strip(string(c)), "Time"), names(raw)))
    gmsl_col  = first(filter(c -> occursin("GMSL (mm)", string(c)), names(raw)))
    sigma_col = first(filter(c -> occursin("sigma", lowercase(string(c))), names(raw)))
    years = floor.(Int, raw[!, time_col])
    gmsl_m  = Float64.(raw[!, gmsl_col])  ./ 1000.0
    sigma_m = Float64.(raw[!, sigma_col]) ./ 1000.0
    return years, gmsl_m, sigma_m
end

# ---------------------------------------------------------------------------
# Load Dangendorf et al. 2024 GMSL reconstruction (ESSD 16, 3471).  Expected
# schema (from python/download_obs.py output): year (int), value (mm),
# sigma (mm), value_lower, value_upper.  sigma is approximated from the
# 90% interval as (upper - lower) / 3.29.
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
    println("  will process post_idx 1..$cap")

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

    # Year-2000 anchor — required for the 2000-baseline normalisation that
    # matches the paired CSV / Python script.
    i2000_obs = findfirst(==(2000), obs_years)
    i2000_obs === nothing && error("obs source '$obs_source' missing year 2000; cannot re-baseline.")
    obs_gmsl_m_2000  = obs_gmsl_m[i2000_obs]
    obs_sigma_m_2000 = obs_sigma_m[i2000_obs]

    # -----------------------------------------------------------------------
    # 3. Build the BRICK model ONCE in default RCP4.5 mode (no FaIR overrides).
    #    BRICK will then use its SNEASY-derived GMST and OHC for the run.
    # -----------------------------------------------------------------------
    yr_start = args["start-year"]
    yr_end   = args["end-year"]
    println("Building MimiBRICK model (rcp=$(args["rcp"]), $yr_start-$yr_end) ...")
    m = MimiBRICK.get_model(
        rcp_scenario = args["rcp"],
        start_year   = yr_start,
        end_year     = yr_end,
    )

    model_years = collect(yr_start:yr_end)
    i2000_mod   = findfirst(==(2000), model_years)
    i2000_mod === nothing && error("Model year window does not include 2000.")

    # Years where the observed series and the model grid intersect.
    overlap_years   = sort(intersect(obs_years, model_years))
    n_overlap       = length(overlap_years)
    @assert n_overlap > 0 "No overlap between CSIRO years and model years."

    # Build mapped indices for the overlap.
    obs_idx_by_year = Dict(y => i for (i, y) in enumerate(obs_years))
    mod_idx_by_year = Dict(y => i for (i, y) in enumerate(model_years))
    overlap_obs_idx = [obs_idx_by_year[y] for y in overlap_years]
    overlap_mod_idx = [mod_idx_by_year[y] for y in overlap_years]

    # Pre-compute observation delta-from-2000 and inflated sigmas, ONCE.
    obs_delta_m = obs_gmsl_m[overlap_obs_idx] .- obs_gmsl_m_2000
    obs_sigma_eff_m = sqrt.(obs_sigma_m[overlap_obs_idx] .^ 2 .+ obs_sigma_m_2000 ^ 2)
    println("  overlap years: $(overlap_years[1])-$(overlap_years[end])  ($n_overlap)")

    # -----------------------------------------------------------------------
    # 4. Loop over posterior members; compute l_B for each.
    # -----------------------------------------------------------------------
    println("Running BRICK with default RCP forcing for each posterior member ...")
    l_B   = Vector{Float64}(undef, cap)
    pidx  = collect(1:cap)
    t0 = time()
    n_failed = 0
    for i in 1:cap
        prow = posterior[i, :]
        sigma = Float64(prow.sd_gmsl)
        rho   = Float64(prow.rho_gmsl)
        try
            update_brick_params!(m, prow)
            run(m)
            gmsl = m[:global_sea_level, :sea_level_rise]   # METERS
            mod_delta_m = Float64.(gmsl[overlap_mod_idx]) .- Float64(gmsl[i2000_mod])
            residuals   = obs_delta_m .- mod_delta_m
            l_B[i] = hetero_logl_ar1(residuals, sigma, rho, obs_sigma_eff_m)
        catch err
            # If a posterior member yields a non-physical run, log it and use -Inf.
            n_failed += 1
            @warn "post_idx=$i failed to run/score: $err"
            l_B[i] = -Inf
        end

        if i % 500 == 0 || i == cap
            el = time() - t0
            println("  $i / $cap  ($(round(el, digits=1))s, $(round(i/el, digits=2)) runs/s)")
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

    # Quick diagnostics so the Python script's auto-c tuner has context.
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
