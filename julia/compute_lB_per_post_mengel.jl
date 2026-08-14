## ============================================================================
## compute_lB_per_post_mengel.jl
##
## ‼ STATUS 2026-08-14: RETIRED — the Mengel/FM arm is EQUAL-WEIGHTED, not Wong-weighted.
## Its posterior is already MCMC-calibrated against the total-GMSL target (the `dang` channel
## in calibrate_mcmc_ext.jl), so applying Wong importance weights on top would double-count
## that constraint. Tony Wong excluded the Mengel arm from global Wong-weighting for exactly
## this reason; research_plan_2026-07-09_ch4co2_slr_paper.md records the decision.
## NOTE the sibling `compute_lB_per_post.jl` is STILL LIVE -- the pre-#93 and BRICK-2.0 arms
## ARE Wong-weighted (their posteriors carry no total-GMSL likelihood term). Only this
## Mengel variant is retired. See notes/spec_2026-08-14_next_calibration.md section 8.1.
##
## BRICK-Mengel variant of compute_lB_per_post.jl: per-posterior-member baseline
## log-likelihood l_B(theta_i) vs Dangendorf, for the Wong importance-weighting
## of the MENGEL arm in the CO2/CH4 pulse->SLR study (Step 5).
##
## Differs from the 35-col stock script in three ways:
##   1. Model = build_brick_mengel (v2.0.0 + Mengel glacier swap), built ONCE;
##      fixed params from the medoid central row, then the 18 FREE physical
##      params per posterior member (same application as run_mimibrick_pulse_
##      versioned.jl / project_ssps_2100_mengel.jl).
##   2. Posterior = the 28-col mengel-ext CSV, which has NO sd_gmsl/rho_gmsl.
##      The total-GMSL-vs-Dangendorf AR(1) nuisance params are sd_dang/rho_dang
##      -> those are used as (sigma, rho) in the heteroscedastic AR(1) logl.
##   3. "Default backbone" = the v2.0.0 ssp245 SNEASY GMST/OHC (no FaIR override),
##      i.e. ssprcp_scenario="ssp245" (vs the stock script's rcp_scenario="RCP45").
##
## ⚠ DECISION (Marcus 2026-06-15): the PRIMARY BRICK-Mengel result is EQUAL-WEIGHTED.
##   The Mengel posterior was MCMC-calibrated DIRECTLY to Dangendorf (obs-driven),
##   so its equal-weight draws are already the data-conditioned distribution; Wong
##   importance-weighting would DOUBLE-COUNT Dangendorf (cf project_ssps_2100_mengel.jl).
##   => Step 6 reports the mengel marginals as PLAIN (uniform-weight) quantiles.
##   pre93 and brick2 remain Wong-weighted via the stock compute_lB_per_post.jl.
##   This script is therefore NOT on the primary path; it exists only for an
##   OPTIONAL Wong-weighted mengel SENSITIVITY. Caveat if used: a v2.0.0 ssp245-
##   SNEASY "default backbone" is an imperfect analogue of the stock RCP45 baseline,
##   since the mengel posterior was never calibrated under a SNEASY ssp backbone.
##
## CLI mirrors compute_lB_per_post.jl (--obs in sync with apply_wong_weights.py).
## ============================================================================

using ArgParse
using CSV
using DataFrames
using Distributions
using LinearAlgebra
using Mimi
using MimiBRICK

include(joinpath(@__DIR__, "brick_mengel.jl"))   # build_brick_mengel / update_brick_mengel!

# the 18 free physical params (== run_mimibrick_pulse_versioned.jl / project_ssps_2100_mengel.jl)
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
const MENGEL_MEDOID_GIC = (a=0.45, b=0.52, T_lia=-0.45, f=0.5, tau_fast=40.0, tau_slow=250.0, sl0=0.0)

function parse_cli()
    s = ArgParseSettings()
    @add_arg_table! s begin
        "--posterior";   default = "data/MimiBRICK/parameters_subsample_brick_mengel_ext.csv"
        "--central-row"; default = "outputs/recalib_central_row.csv"
        "--obs";         default = "dangendorf"; range_tester = x -> x in ("dangendorf", "csiro")
        "--obs-path";    default = "data/observations/dangendorf_2024_gmsl.csv"
        "--output";      default = "outputs/brick_lB_per_post_mengel.csv"
        "--ssp";         default = "ssp245"
        "--start-year";  arg_type = Int; default = 1850
        "--end-year";    arg_type = Int; default = 2100
        "--max-post";    arg_type = Int; default = 0
    end
    return parse_args(s)
end

function hetero_logl_ar1(residuals::Vector{Float64}, sigma::Float64, rho::Float64, obs_sigma::Vector{Float64})
    n = length(residuals); n == 0 && return 0.0
    process_var = sigma^2 / (1 - rho^2)
    H = abs.((1:n)' .- (1:n))
    cov_matrix = process_var .* (rho .^ H) .+ Diagonal(obs_sigma .^ 2)
    return try
        logpdf(MvNormal(cov_matrix), residuals)
    catch err
        @warn "MvNormal logpdf failed: $err — returning -Inf"; -Inf
    end
end

function load_dangendorf(path::String)
    raw = CSV.read(path, DataFrame)
    Int.(raw[!, "year"]), Float64.(raw[!, "value"]) ./ 1000.0, Float64.(raw[!, "sigma"]) ./ 1000.0
end

function main()
    args = parse_cli()
    println("Loading mengel posterior from $(args["posterior"]) ...")
    posterior = DataFrame(CSV.File(args["posterior"]))
    n_post = nrow(posterior)
    @assert "sd_dang"  in names(posterior) "mengel posterior missing sd_dang (total-vs-Dangendorf AR1 sigma)"
    @assert "rho_dang" in names(posterior) "mengel posterior missing rho_dang"
    for nm in MENGEL_PHYS_NAMES
        @assert nm in names(posterior) "mengel posterior missing free-param column '$nm'"
    end
    cap = args["max-post"] > 0 ? min(args["max-post"], n_post) : n_post
    println("  posterior: $n_post members; processing 1..$cap")

    println("Loading obs (dangendorf) from $(args["obs-path"]) ...")
    obs_years, obs_gmsl_m, obs_sigma_m = load_dangendorf(args["obs-path"])
    i2000_obs = findfirst(==(2000), obs_years)
    i2000_obs === nothing && error("obs missing year 2000.")
    obs_gmsl_m_2000 = obs_gmsl_m[i2000_obs]; obs_sigma_m_2000 = obs_sigma_m[i2000_obs]

    yr_start, yr_end = args["start-year"], args["end-year"]
    println("Building BRICK-Mengel (ssp=$(args["ssp"]), $yr_start-$yr_end, DEFAULT backbone, no FaIR override) ...")
    m = build_brick_mengel(ssp = args["ssp"], y0 = yr_start, y1 = yr_end)
    medoid = DataFrame(CSV.File(args["central-row"]))[1, :]
    update_brick_mengel!(m, medoid, MENGEL_MEDOID_GIC; precip_log = true)

    model_years = collect(yr_start:yr_end)
    i2000_mod = findfirst(==(2000), model_years)
    overlap_years = sort(intersect(obs_years, model_years))
    obs_idx = Dict(y => i for (i, y) in enumerate(obs_years))
    mod_idx = Dict(y => i for (i, y) in enumerate(model_years))
    ov_obs = [obs_idx[y] for y in overlap_years]; ov_mod = [mod_idx[y] for y in overlap_years]
    obs_delta_m = obs_gmsl_m[ov_obs] .- obs_gmsl_m_2000
    obs_sigma_eff = sqrt.(obs_sigma_m[ov_obs] .^ 2 .+ obs_sigma_m_2000 ^ 2)
    println("  overlap years: $(overlap_years[1])-$(overlap_years[end]) ($(length(overlap_years)))")

    l_B = Vector{Float64}(undef, cap); t0 = time(); n_failed = 0
    for i in 1:cap
        prow = posterior[i, :]
        sigma = Float64(prow.sd_dang); rho = Float64(prow.rho_dang)
        try
            @inbounds for j in 1:length(MENGEL_PHYS)
                update_param!(m, MENGEL_PHYS[j][1], MENGEL_PHYS[j][2], Float64(prow[MENGEL_PHYS_NAMES[j]]))
            end
            run(m)
            gmsl = m[:global_sea_level, :sea_level_rise]
            mod_delta = Float64.(gmsl[ov_mod]) .- Float64(gmsl[i2000_mod])
            l_B[i] = hetero_logl_ar1(obs_delta_m .- mod_delta, sigma, rho, obs_sigma_eff)
        catch err
            n_failed += 1; @warn "post_idx=$i failed: $err"; l_B[i] = -Inf
        end
        if i % 500 == 0 || i == cap
            println("  $i / $cap  ($(round(time()-t0,digits=1))s)")
        end
    end
    n_failed > 0 && println("Note: $n_failed members failed (l_B=-Inf).")

    out = DataFrame(post_idx = collect(1:cap), l_B_gmsl = l_B)
    mkpath(dirname(args["output"])); CSV.write(args["output"], out)
    println("\nWrote $(args["output"])  ($(nrow(out)) rows)")
    println("⚠ Mengel Wong-weighting applicability is an OPEN Step-5 decision (see header).")
end

main()
