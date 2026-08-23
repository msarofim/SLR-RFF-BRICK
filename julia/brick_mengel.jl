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
include(joinpath(@__DIR__, "glaciers_nu_component.jl"))
include(joinpath(@__DIR__, "glaciers_nu3_component.jl"))
include(joinpath(@__DIR__, "greenland_ab_component.jl"))
include(joinpath(@__DIR__, "greenland_3basin_component.jl"))
include(joinpath(@__DIR__, "brick_param_updates.jl"))

const _MENGEL_GLAC_SLOT = :glaciers_small_icecaps   # name kept by Mimi replace!
const _GIS_SLOT = :greenland_icesheet               # name kept by Mimi replace!

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

# ============================================================================
# extB3 (2026-08-07): glaciers_nu variant — Mengel S_eq + Nauels-ν transient,
# driven by GLACIER-AREA temperature (Option D). The old build_brick_mengel /
# update_brick_mengel! paths above are kept untouched for provenance
# (extA108/extB1/extB2 reproduction). See glaciers_nu_component.jl header for
# the frame contract; the driver is set by set_glacier_forcing!, never by
# set_forcing! (deliberately different parameter name).
# ============================================================================

"""
    build_brick_nu(; ssp, y0, y1, lws=:seeded, lws_seed=LWS_SEED)

`build_brick_mengel` with the glaciers_nu component in the glacier slot. The new
`glacier_surface_temperature` driver is UNBOUND after the build — call
`set_glacier_forcing!` before `run(m)`.
"""
function build_brick_nu(; ssp::String="ssp245", y0::Int=1850, y1::Int=2026,
                        lws::Symbol=:seeded, lws_seed::Int=LWS_SEED)
    m = MimiBRICK.get_model(ssprcp_scenario=ssp, start_year=y0, end_year=y1)
    replace!(m, _MENGEL_GLAC_SLOT => glaciers_nu)
    n = y1 - y0 + 1
    if lws === :seeded
        update_param!(m, :landwater_storage, :lws_random_sample,
                      LWS_MEAN .+ LWS_SD .* randn(MersenneTwister(lws_seed), n))
    elseif lws === :central
        update_param!(m, :landwater_storage, :lws_random_sample, fill(LWS_MEAN, n))
    elseif lws === :zero
        update_param!(m, :landwater_storage, :lws_random_sample, zeros(n))
    elseif lws !== :random
        error("build_brick_nu: lws must be :seeded, :central, :zero, or :random (got :$lws)")
    end
    return m
end

"""
    update_brick_nu!(m, prow, gic; precip_log=true)

Non-glacier params from posterior row `prow`; glacier params from `gic`
(NamedTuple with fields a, b, T_off, kappa, nu, sl0 — GLACIER-FRAME values).
"""
function update_brick_nu!(m, prow, gic; precip_log::Bool=true)
    update_brick_params!(m, prow; precip_log=precip_log, skip_glaciers=true)
    update_param!(m, _MENGEL_GLAC_SLOT, :gic_a,     gic.a)
    update_param!(m, _MENGEL_GLAC_SLOT, :gic_b,     gic.b)
    update_param!(m, _MENGEL_GLAC_SLOT, :gic_T_off, gic.T_off)
    update_param!(m, _MENGEL_GLAC_SLOT, :gic_kappa, gic.kappa)
    update_param!(m, _MENGEL_GLAC_SLOT, :gic_nu,    gic.nu)
    update_param!(m, _MENGEL_GLAC_SLOT, :gic_sl0,   gic.sl0)
    return m
end

"""Set the glacier-frame driver (T_glac historically, amp_g x GMST spliced forward)."""
function set_glacier_forcing!(m, tglac::Vector{<:Real})
    update_param!(m, _MENGEL_GLAC_SLOT, :glacier_surface_temperature, tglac)
    return m
end

# ============================================================================
# extC (2026-08-09): 3-reservoir glaciers_nu3 (R19 / SLOWP / FAST)
# Structure + constants provenance: python/d1d_fourrung_seam.py C_both,
# python/build_extc_inputs.py -> outputs/extc_block_constants.csv.
# ============================================================================

const NU3_BLOCKS = ("R19", "SLOWP", "FAST")

"""
    build_brick_nu3(; ssp, y0, y1, lws=:seeded, lws_seed=LWS_SEED)

`build_brick_nu` with the 3-reservoir glaciers_nu3 component in the glacier
slot. All three per-block drivers are UNBOUND after the build — call
`set_glacier_forcing3!` before `run(m)`.
"""
function build_brick_nu3(; ssp::String="ssp245", y0::Int=1850, y1::Int=2026,
                         lws::Symbol=:seeded, lws_seed::Int=LWS_SEED)
    m = MimiBRICK.get_model(ssprcp_scenario=ssp, start_year=y0, end_year=y1)
    replace!(m, _MENGEL_GLAC_SLOT => glaciers_nu3)
    n = y1 - y0 + 1
    if lws === :seeded
        update_param!(m, :landwater_storage, :lws_random_sample,
                      LWS_MEAN .+ LWS_SD .* randn(MersenneTwister(lws_seed), n))
    elseif lws === :central
        update_param!(m, :landwater_storage, :lws_random_sample, fill(LWS_MEAN, n))
    elseif lws === :zero
        update_param!(m, :landwater_storage, :lws_random_sample, zeros(n))
    elseif lws !== :random
        error("build_brick_nu3: lws must be :seeded, :central, :zero, or :random (got :$lws)")
    end
    return m
end

"""
    update_brick_nu3!(m, prow, gic3; precip_log=true)

Non-glacier params from posterior row `prow`; glacier params from `gic3`, a
NamedTuple of per-block NamedTuples keyed R19/SLOWP/FAST, each with fields
a, b, T_off, kappa, nu (GLACIER-FRAME values). sl0 is always 0.
"""
function update_brick_nu3!(m, prow, gic3; precip_log::Bool=true,
                           skip_greenland::Bool=false)
    update_brick_params!(m, prow; precip_log=precip_log, skip_glaciers=true,
                         skip_greenland=skip_greenland)
    for blk in NU3_BLOCKS
        g = getproperty(gic3, Symbol(blk))
        update_param!(m, _MENGEL_GLAC_SLOT, Symbol("gic_a_$blk"),     g.a)
        update_param!(m, _MENGEL_GLAC_SLOT, Symbol("gic_b_$blk"),     g.b)
        update_param!(m, _MENGEL_GLAC_SLOT, Symbol("gic_T_off_$blk"), g.T_off)
        update_param!(m, _MENGEL_GLAC_SLOT, Symbol("gic_kappa_$blk"), g.kappa)
        update_param!(m, _MENGEL_GLAC_SLOT, Symbol("gic_nu_$blk"),    g.nu)
    end
    update_param!(m, _MENGEL_GLAC_SLOT, :gic_sl0, 0.0)
    return m
end

"""Set the three per-block glacier-frame drivers (NamedTuple R19/SLOWP/FAST)."""
function set_glacier_forcing3!(m, tg3)
    for blk in NU3_BLOCKS
        update_param!(m, _MENGEL_GLAC_SLOT,
                      Symbol("glacier_surface_temperature_$blk"),
                      getproperty(tg3, Symbol(blk)))
    end
    return m
end

# ============================================================================
# Greenland pass 1 (2026-08-10): cell A+B in the Greenland slot.
# Structure + fitted theta provenance: python/gis_offline_cell.py cell "A+B";
# port ground truth: python/emit_gis_port_reference.py.
# Option C (the PISM ladder as V_eq) FAILED offline and is deliberately absent.
# ============================================================================

"""
    build_brick_nu3_gis(; ssp, y0, y1, lws=:seeded, lws_seed=LWS_SEED)

`build_brick_nu3` with `greenland_ab` in the Greenland slot as well. BOTH the
glacier block drivers and the Greenland regional driver are UNBOUND after the
build — call `set_glacier_forcing3!` and `set_gis_forcing!` before `run(m)`.
"""
function build_brick_nu3_gis(; ssp::String="ssp245", y0::Int=1850, y1::Int=2026,
                             lws::Symbol=:seeded, lws_seed::Int=LWS_SEED)
    m = build_brick_nu3(; ssp=ssp, y0=y0, y1=y1, lws=lws, lws_seed=lws_seed)
    replace!(m, _GIS_SLOT => greenland_ab)
    return m
end

"""
    update_gis_ab!(m, gis)

Greenland A+B parameters from a NamedTuple with fields c1, c0, v0, f, alpha_f,
beta_f, alpha_s, beta_s, g — all in COMPONENT units (metres, not the offline
cell's centimetres; see python/emit_gis_port_reference.py).
"""
function update_gis_ab!(m, gis)
    for f in (:c1, :c0, :v0, :f, :alpha_f, :beta_f, :alpha_s, :beta_s, :g)
        update_param!(m, _GIS_SLOT, Symbol("gis_$f"), Float64(getproperty(gis, f)))
    end
    return m
end

"""
    build_brick_nu3_gis3(; ssp, y0, y1, lws=:seeded, lws_seed=LWS_SEED)

`build_brick_nu3` with the 3-BASIN Greenland (`greenland_3basin`) in the Greenland
slot — Mouginot sectors south{SW,CW,CE,SE} / mid{NW} / high{NO,NE} on ONE shared
regional driver. Same unbound-driver contract as `build_brick_nu3_gis`: call
`set_glacier_forcing3!` and `set_gis_forcing!` before `run(m)`.
"""
function build_brick_nu3_gis3(; ssp::String="ssp245", y0::Int=1850, y1::Int=2026,
                              lws::Symbol=:seeded, lws_seed::Int=LWS_SEED)
    m = build_brick_nu3(; ssp=ssp, y0=y0, y1=y1, lws=lws, lws_seed=lws_seed)
    replace!(m, _GIS_SLOT => greenland_3basin)
    # TAP OFF BY DEFAULT (gis_tap_v = 0), so every existing consumer of this builder
    # is bit-identical until it opts in. The other three carry the chosen cell so a
    # caller that switches only V on gets the specified tap rather than a zero tau.
    update_param!(m, _GIS_SLOT, :gis_tap_v,      GIS_TAP_OFF)
    update_param!(m, _GIS_SLOT, :gis_tap_onset,  GIS_TAP_CELL.onset_K)
    update_param!(m, _GIS_SLOT, :gis_tap_tau,    GIS_TAP_CELL.tau_yr)
    update_param!(m, _GIS_SLOT, :gis_tap_ramp_w, GIS_TAP_CELL.ramp_w_K)
    # Both additive capabilities default to the pre-existing behaviour: ONE stage
    # (first-order) and the HIGH-BASIN home with its k_high*v0 clamp.
    update_param!(m, _GIS_SLOT, :gis_tap_stages,     GIS_TAP_STAGES_DEFAULT)
    update_param!(m, _GIS_SLOT, :gis_tap_wholesheet, GIS_TAP_WHOLESHEET_OFF)
    update_param!(m, _GIS_SLOT, :gis_tap_gmt,    zeros(length(y0:y1)))
    return m
end

"""
    update_gis3_tap!(m, gmt; v=GIS_TAP_CELL.V_m, onset=..., tau=..., ramp_w=...,
                     stages=..., wholesheet=...)

Switch the high-basin volume tap ON with the GLOBAL temperature series `gmt`
(K rel 1850-1900, one value per model year).

`gmt` IS GLOBAL, NOT the regional Greenland driver. The onset is quoted in GMT —
4.69 K is our own fair_mean ssp585's 2100 GMT — so passing the amplified regional
series would fire the tap about `gis_amp` (~1.92x) too early. Nothing downstream can
detect that, which is why it is asserted here.

`stages` and `wholesheet` default to `GIS_TAP_CELL`'s values (2-stage cascade,
whole-sheet home), so switching the tap on with no keywords gives the SHIPPED cell.
The build-time parameter defaults remain first-order / high-basin — see the
COMPONENT-LEVEL DEFAULTS note in greenland_3basin_component.jl.
"""
function update_gis3_tap!(m, gmt; v::Real = GIS_TAP_CELL.V_m,
                          onset::Real = GIS_TAP_CELL.onset_K,
                          tau::Real = GIS_TAP_CELL.tau_yr,
                          ramp_w::Real = GIS_TAP_CELL.ramp_w_K,
                          stages::Real = GIS_TAP_CELL.stages,
                          wholesheet::Bool = GIS_TAP_CELL.wholesheet)
    g = Float64.(collect(gmt))
    # A tap with V > 0 and an all-zero (or never-reaching-onset) driver is SILENTLY
    # INERT: it returns exactly the untapped model and looks like "the tap does
    # nothing", which is the wrong conclusion drawn from a wiring mistake. The
    # builder's default IS all-zeros, so this is a live trap, not a hypothetical.
    if v > 0
        # THE GUARD IS ON A DEGENERATE DRIVER, NOT A COOL ONE. The first version of
        # this errored whenever max(gmt) <= onset — which rejected ssp126 and ssp245,
        # where a tap that never fires is the CORRECT and expected behaviour and is
        # exactly what gate G2b asserts. Caught by that gate on the first run.
        # What must be refused is a driver that carries no scenario at all: the
        # builder binds all-zeros by default, so a caller who forgets the series gets
        # silence rather than a result.
        (maximum(g) > minimum(g)) || error("update_gis3_tap!: v = $v but the GLOBAL " *
            "driver is CONSTANT at $(round(first(g), digits=3)) K — almost certainly " *
            "the builder's all-zero default rather than a scenario. The tap would be " *
            "silently inert. Pass the GMT series (NOT the regional Greenland driver).")
        tau > 0 || error("update_gis3_tap!: tau must be > 0, got $tau")
        ramp_w > 0 || error("update_gis3_tap!: ramp_w must be > 0, got $ramp_w")
        # A real scenario that never reaches the onset is legitimate — say so, do not
        # fail. Cool scenarios deviating EXACTLY 0.0 is a designed property of the
        # onset choice, not an error.
        maximum(g) > onset ||
            @info("update_gis3_tap!: this driver peaks at " *
                  "$(round(maximum(g), digits=3)) K, below the onset $onset K — the " *
                  "tap will not fire on this scenario. Expected for cool scenarios.")
    end
    update_param!(m, _GIS_SLOT, :gis_tap_v,      Float64(v))
    update_param!(m, _GIS_SLOT, :gis_tap_onset,  Float64(onset))
    update_param!(m, _GIS_SLOT, :gis_tap_tau,    Float64(tau))
    update_param!(m, _GIS_SLOT, :gis_tap_ramp_w, Float64(ramp_w))
    # `tau` is the TOTAL mean delay at every stage count, so stages = 1 reproduces
    # the pre-existing recursion exactly and a cascade at the same tau is slower to
    # start rather than simply smaller.
    update_param!(m, _GIS_SLOT, :gis_tap_stages, Float64(stages))
    update_param!(m, _GIS_SLOT, :gis_tap_wholesheet,
                  wholesheet ? GIS_TAP_WHOLESHEET_ON : GIS_TAP_WHOLESHEET_OFF)
    update_param!(m, _GIS_SLOT, :gis_tap_gmt,    g)
    return m
end

"""
    update_gis3_shares!(m; k=GIS3_VSHARE, s=(south=1.0, mid=1.0, high=1.0))

Set the 3-basin volume shares (FIXED geometry) and rate scales (the sampled knobs).
Defaults put every basin at its Mouginot volume share and unit rate scale.
`k=(south=1.0, mid=0.0, high=0.0)` with unit rate scales is the NESTING point at
which this component must reproduce `greenland_ab` exactly.
"""
function update_gis3_shares!(m; k=GIS3_VSHARE, s=(south=1.0, mid=1.0, high=1.0))
    for b in GIS3_BASINS
        update_param!(m, _GIS_SLOT, Symbol("gis_k_$b"), Float64(getproperty(k, b)))
        update_param!(m, _GIS_SLOT, Symbol("gis_s_$b"), Float64(getproperty(s, b)))
    end
    return m
end

"""Set the Greenland REGIONAL driver (K rel 1850-1900, amp-spliced forward)."""
function set_gis_forcing!(m, tgis)
    update_param!(m, _GIS_SLOT, :greenland_surface_temperature, Float64.(tgis))
    return m
end
