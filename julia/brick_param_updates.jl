## ============================================================================
## brick_param_updates.jl
##
## Shared BRICK posterior-row → model-parameter update function. Single source
## of truth for the 27 `update_param!` calls that map a row of
## parameters_subsample_brick.csv onto a MimiBRICK model instance.
##
## The four Julia drivers that need this — `run_mimibrick_flatcube.jl`,
## `run_mimibrick_paired_explicit.jl`, `run_mimibrick_obs_driven.jl`, and
## `compute_lB_per_post.jl` — each `include("brick_param_updates.jl")` and
## call `update_brick_params!(m, prow)`. Before extraction the same 27-line
## block lived inline in each driver, drifting was a real concern: any new
## BRICK posterior column (e.g. a future PR adding an AIS coefficient) only
## had to be added here.
##
## Greek-letter parameter names (anto_α, ais_μ, te_α, etc.) match MimiBRICK's
## native parameter naming, which uses Unicode for the physics symbols. The
## posterior CSV columns use the ASCII transliteration (anto_alpha, antarctic_mu,
## thermal_alpha, etc.) — see the mapping below. This is a MimiBRICK
## quirk; see ~/.claude/skills/mimibrick-quirks for context.
## ============================================================================

"""
    update_brick_params!(m::Mimi.Model, prow)

Apply one row of the BRICK posterior CSV (as e.g. `posterior[i, :]`)
to a built MimiBRICK model `m`. Mutates `m` in place.
"""
function update_brick_params!(m, prow)
    # Antarctic Ocean module
    update_param!(m, :antarctic_ocean, :anto_α, prow.anto_alpha)
    update_param!(m, :antarctic_ocean, :anto_β, prow.anto_beta)

    # Antarctic Ice Sheet module (15 parameters)
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

    # Glaciers + small ice caps module
    update_param!(m, :glaciers_small_icecaps, :gsic_β₀, prow.glaciers_beta0)
    update_param!(m, :glaciers_small_icecaps, :gsic_v₀, prow.glaciers_v0)
    update_param!(m, :glaciers_small_icecaps, :gsic_s₀, prow.glaciers_s0)
    update_param!(m, :glaciers_small_icecaps, :gsic_n,  prow.glaciers_n)

    # Greenland Ice Sheet module (post-PR#93 calibration)
    update_param!(m, :greenland_icesheet, :greenland_a,  prow.greenland_a)
    update_param!(m, :greenland_icesheet, :greenland_b,  prow.greenland_b)
    update_param!(m, :greenland_icesheet, :greenland_α,  prow.greenland_alpha)
    update_param!(m, :greenland_icesheet, :greenland_β,  prow.greenland_beta)
    update_param!(m, :greenland_icesheet, :greenland_v₀, prow.greenland_v0)

    # Thermal expansion module
    update_param!(m, :thermal_expansion, :te_α,  prow.thermal_alpha)
    update_param!(m, :thermal_expansion, :te_s₀, prow.thermal_s0)
end
