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

`precip_log` — AIS precipitation reparameterization shim for MimiBRICK ≥ v2.0.0.
v1.0.1's AIS component computes accumulation as `ais_precipitation₀ * exp(κ·T)`
(precipitation₀ in LINEAR m/yr; get_model default 0.37). v2.0.0 changed this to
`exp(ais_precipitation₀) * exp(κ·T)` (precipitation₀ in LOG space; get_model
default log(0.37)). The post-#93 posterior we use (delivered 2026-05-22, BEFORE
v2.0.0's 2026-06-08 release) stores `antarctic_precip0` in LINEAR units (median
0.80 m/yr). Feeding those linear values into v2.0.0's exp() overloads Antarctic
snowfall by exp(p)/p ≈ 2.2–4.5× and blows up the highly nonlinear ice-sheet
dynamics — this is the +100 cm AIS@1900 "v2.0.0 obs-driven blocker" (NOT the
OHC reference/units originally suspected; OHC injection and the byte-identical
thermal_expansion component are version-invariant).

Set `precip_log=true` when the model was built via the v2.0.0 get_model API so
the linear posterior value is log-transformed (`exp(log(p)) = p` reproduces
v1.0.1 behavior bit-for-bit). Leave false (default) for v1.0.1 models — all
existing callers are unaffected.

NB: do NOT detect the version via `pkgversion(MimiBRICK)` — the v2.0.0 git tag
ships a Project.toml that still reads `1.2.0-dev`, so version introspection
lies. The caller knows which get_model signature it built with; pass the flag
from there.
"""
function update_brick_params!(m, prow; precip_log::Bool=false, skip_glaciers::Bool=false,
                              skip_greenland::Bool=false)
    # `skip_glaciers=true` for a model whose single-reservoir glacier component has
    # been swapped for the Mengel emulator (`glaciers_mengel`, see brick_mengel.jl):
    # the old gsic_β₀/gsic_v₀/gsic_s₀/gsic_n params do not exist there, so skip them
    # and set the Mengel params (gic_a/b/τ/sl0) separately.
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
    update_param!(m, :antarctic_icesheet, :ais_precipitation₀,
                  precip_log ? log(prow.antarctic_precip0) : prow.antarctic_precip0)
    update_param!(m, :antarctic_icesheet, :ais_κ,                      prow.antarctic_kappa)
    update_param!(m, :antarctic_icesheet, :ais_ν,                      prow.antarctic_nu)
    update_param!(m, :antarctic_icesheet, :ais_iceflow₀,               prow.antarctic_flow0)
    update_param!(m, :antarctic_icesheet, :ais_γ,                      prow.antarctic_gamma)
    update_param!(m, :antarctic_icesheet, :ais_α,                      prow.antarctic_alpha)
    update_param!(m, :antarctic_icesheet, :temperature_threshold,      prow.antarctic_temp_threshold)
    update_param!(m, :antarctic_icesheet, :λ,                          prow.antarctic_lambda)

    # Glaciers + small ice caps module (single-reservoir Wigley-Raper-Bakker;
    # skipped when the Mengel emulator is swapped in)
    if !skip_glaciers
        update_param!(m, :glaciers_small_icecaps, :gsic_β₀, prow.glaciers_beta0)
        update_param!(m, :glaciers_small_icecaps, :gsic_v₀, prow.glaciers_v0)
        update_param!(m, :glaciers_small_icecaps, :gsic_s₀, prow.glaciers_s0)
        update_param!(m, :glaciers_small_icecaps, :gsic_n,  prow.glaciers_n)
    end

    # Greenland Ice Sheet module (post-PR#93 calibration)
    # `skip_greenland=true` for a model whose Greenland slot holds greenland_ab
    # (Ladrillo 1.0) rather than stock SIMPLE: none of these five parameters
    # exists there, and Mimi throws KeyError rather than ignoring them.
    if !skip_greenland
        update_param!(m, :greenland_icesheet, :greenland_a,  prow.greenland_a)
        update_param!(m, :greenland_icesheet, :greenland_b,  prow.greenland_b)
        update_param!(m, :greenland_icesheet, :greenland_α,  prow.greenland_alpha)
        update_param!(m, :greenland_icesheet, :greenland_β,  prow.greenland_beta)
        update_param!(m, :greenland_icesheet, :greenland_v₀, prow.greenland_v0)
    end

    # Thermal expansion module
    update_param!(m, :thermal_expansion, :te_α,  prow.thermal_alpha)
    update_param!(m, :thermal_expansion, :te_s₀, prow.thermal_s0)
end

## ============================================================================
## The BRICK 2.0 arm's posterior and its `antarctic_precip0` convention, kept together.
##
## Marcus 2026-10-15: the arm moves to the joint SNEASY-BRICK posterior subsample published with MimiBRICK v2.0.0
## (Zenodo 10.5281/zenodo.20592337, parameters_subsample_sneasybrick.csv, sha256 d74577f6...; CHANGELOG 2026-10-15c/d).
## The arm reads its 35 BRICK columns; the 16 SNEASY columns are unused (the arm is driven by FaIR or MAGICC climate).
## That file stores antarctic_precip0 in LOG space, as v2.0.0 expects, so the `precip_log` shim is OFF for it. Through
## 2026-10-15 the arm used Tony's May-22 subsample (parameters_subsample_brick.csv, sha256 78247db8..., LINEAR units,
## shim ON).
##
## BRICK20_POSTERIOR (a path relative to the repo) and BRICK20_PRECIP_LOG (true|false) override both, for a
## regression run of the old file only (run_brick20_zenodo_swap_20261015.sh). They are functions, not consts, because
## some drivers reach this file through two include chains.
## ============================================================================
brick20_posterior_rel() = get(ENV, "BRICK20_POSTERIOR",
                              joinpath("data", "MimiBRICK", "parameters_subsample_sneasybrick_zenodo20592337.csv"))
brick20_precip_log() = get(ENV, "BRICK20_PRECIP_LOG", "false") == "true"
brick20_posterior_path(repo) = joinpath(repo, brick20_posterior_rel())
brick20_label() = "BRICK 2.0 posterior $(basename(brick20_posterior_rel())) (precip_log=$(brick20_precip_log()))"

"""
    load_brick20_posterior(path) -> DataFrame

Read the BRICK 2.0 posterior and refuse a units mismatch: a file whose `antarctic_precip0` is positive in every row
is in LINEAR units and needs the shim; one with negative values is in LOG space and must not get it.
"""
function load_brick20_posterior(path)
    df = CSV.read(path, DataFrame)
    linear = all(>(0), df.antarctic_precip0)
    linear == brick20_precip_log() || error("$path: antarctic_precip0 looks $(linear ? "LINEAR" : "LOG-space") but " *
        "brick20_precip_log() = $(brick20_precip_log()); the file and the shim disagree (see brick_param_updates.jl)")
    return df
end
