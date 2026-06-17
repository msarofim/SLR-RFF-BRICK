## ============================================================================
## brick_mengel.jl  —  BRICK v2.0.0 with the Mengel-2016 glacier emulator
##
## Build helper + parameter updater for a BRICK model whose single-reservoir
## Wigley-Raper-Bakker glacier component has been replaced (via Mimi `replace!`,
## which keeps the slot name :glaciers_small_icecaps and all I/O wiring) by the
## temperature-dependent-equilibrium Mengel component (glaciers_mengel_component.jl).
##
## The committed/disequilibrium early-20th-c melt is SIMULATED directly via the
## LIA-disequilibrium offset gic_T_lia (the glacier equilibrium temperature ≈ the
## colder Little-Ice-Age climate) — driven by total temperature, no anthropogenic/
## natural forcing split, no external budget. See python/calibrate_mengel_glacier.py.
##
## Usage:
##   include("julia/brick_mengel.jl")
##   m = build_brick_mengel(ssp="ssp245", y0=1850, y1=2100)
##   update_brick_mengel!(m, posterior_row, (a=…, b=…, tau=…, sl0=…); precip_log=true)
##   set_forcing!(m, gmst, ohc); run(m)
## ============================================================================

using Mimi, MimiBRICK, Random

include(joinpath(@__DIR__, "glaciers_mengel_component.jl"))
include(joinpath(@__DIR__, "brick_param_updates.jl"))

const _MENGEL_GLAC_SLOT = :glaciers_small_icecaps   # name kept by Mimi replace!

# Land-water-storage (LWS) annual rate. MimiBRICK's get_model draws this fresh and UNSEEDED on every
# call — rand(Normal(0.0003, 0.00018), n) m/yr — which makes total SLR irreproducible build-to-build
# (the ~0.4 cm LWS drift seen between SSP-projection re-runs, 2026-06-17). We LOCK it. Treatments:
#   :seeded  (default) — the same Normal draw but from a FIXED-seed local RNG -> reproducible random
#                        realization (the "locked seed" the BRICK versions use).
#   :central           — smooth deterministic 0.3 mm/yr mean (matches the MimiBRICK-FM shareable repo).
#   :zero              — no LWS.
#   :random            — MimiBRICK's legacy unseeded draw (irreproducible — not recommended).
# LWS is a small, climate-independent term (~0.16 cm spread by 2100) relative to the AIS/posterior
# spread. A LOCAL RNG is used so the global stream (e.g. FaIR-member pairing seeds) is untouched.
const LWS_MEAN  = 0.0003    # m/yr  (mean of MimiBRICK's N(0.0003, 0.00018) LWS rate)
const LWS_SD    = 0.00018   # m/yr  (sd  of that distribution)
const LWS_SEED  = 2026      # locks the :seeded realization (matches the obs-driven driver default)

"""
    build_brick_mengel(; ssp, y0, y1, lws=:seeded, lws_seed=LWS_SEED)

Build a v2.0.0 BRICK with the Mengel glacier emulator swapped in (wiring preserved). `lws` selects the
land-water-storage treatment: `:seeded` (default) = fixed-seed random realization (reproducible);
`:central` = smooth 0.3 mm/yr mean; `:zero` = no LWS; `:random` = legacy unseeded draw (irreproducible).
"""
function build_brick_mengel(; ssp::String="ssp245", y0::Int=1850, y1::Int=2100,
                            lws::Symbol=:seeded, lws_seed::Int=LWS_SEED)
    m = MimiBRICK.get_model(ssprcp_scenario=ssp, start_year=y0, end_year=y1)
    replace!(m, _MENGEL_GLAC_SLOT => glaciers_mengel)
    n = y1 - y0 + 1
    if lws === :seeded
        update_param!(m, :landwater_storage, :lws_random_sample,
                      LWS_MEAN .+ LWS_SD .* randn(MersenneTwister(lws_seed), n))
    elseif lws === :central
        update_param!(m, :landwater_storage, :lws_random_sample, fill(LWS_MEAN, n))
    elseif lws === :zero
        update_param!(m, :landwater_storage, :lws_random_sample, zeros(n))
    elseif lws !== :random   # :random keeps get_model's unseeded draw (legacy)
        error("build_brick_mengel: lws must be :seeded, :central, :zero, or :random (got :$lws)")
    end
    return m
end

"""
    update_brick_mengel!(m, prow, gic; precip_log=true)

Set the non-glacier params from a BRICK posterior row `prow` (AIS, anto, GIS, TE —
via update_brick_params! with skip_glaciers=true) and the Mengel glacier params from
`gic` (a NamedTuple/struct with fields a, b, tau, sl0).
"""
function update_brick_mengel!(m, prow, gic; precip_log::Bool=true)
    update_brick_params!(m, prow; precip_log=precip_log, skip_glaciers=true)
    update_param!(m, _MENGEL_GLAC_SLOT, :gic_a,        gic.a)
    update_param!(m, _MENGEL_GLAC_SLOT, :gic_b,        gic.b)
    update_param!(m, _MENGEL_GLAC_SLOT, :gic_T_lia,    gic.T_lia)
    update_param!(m, _MENGEL_GLAC_SLOT, :gic_f,        gic.f)
    update_param!(m, _MENGEL_GLAC_SLOT, :gic_tau_fast, gic.tau_fast)
    update_param!(m, _MENGEL_GLAC_SLOT, :gic_tau_slow, gic.tau_slow)
    update_param!(m, _MENGEL_GLAC_SLOT, :gic_sl0,      gic.sl0)
    return m
end

"""Obs-driven forcing override (FaIR GMST + OHC), as in run_mimibrick_obs_driven.jl."""
function set_forcing!(m, gmst::Vector{<:Real}, ohc::Vector{<:Real})
    update_param!(m, :model_global_surface_temperature, gmst)
    update_param!(m, :thermal_expansion, :ocean_heat_interior, ohc)
    return m
end
