## ============================================================================
## ladrillo_projection.jl — the Ladrillo projection kernel (extC posterior)
##
## ONE place that knows how to push a draw of the Ladrillo posterior through
## MimiBRICK. Every extC-era driver (SSP projections, posterior-predictive,
## comparison arms, pulse experiments) includes this file instead of
## re-deriving the parameter map, the per-block glacier drivers, and the
## rebaselining convention. Before extraction that block was copy-pasted into
## each driver and had already drifted (2-tau names, missing sampled-amp
## drivers, wrong nu basis).
##
## WHAT "Ladrillo" IS
##   MimiBRICK v2.0.0 with the single-reservoir Wigley-Raper-Bakker glacier
##   component replaced by a THREE-RESERVOIR Mengel-type emulator
##   (julia/glaciers_nu3_component.jl): reservoirs R19 (Antarctic periphery,
##   RGI region 19), SLOWP (slow-responding: RGI 03/09/07/06) and FAST (the
##   remaining 13 regions). Each reservoir integrates
##       S_eq,b = a_b (1 - exp(-b_b (T_b - T_off,b)))
##       dS_b   = min(kappa_b * exc^nu_b, 1) (S_eq,b - S_b)
##   on its OWN area-weighted surface-temperature driver T_b.
##
## POSTERIOR
##   data/MimiBRICK/parameters_subsample_brick_mengel_extC.csv — 10 000 draws
##   from 4 x 2M chains (seeds 2026-2029, acceptance 0.236-0.237), accepted on
##   the deliverable (SLR@2100 R-hat 1.000, @2150 1.002). 52 columns:
##     21 non-glacier physical params applied directly       (PHYSICAL_PARAMS)
##      2 derived AIS params (runoff line, GMST->T_ant amp)  (see apply_draw!)
##     12 per-block glacier params (a, b, T_off, log10 kappa)
##      3 per-block glacier temperature amplifications
##      4 likelihood-only glacier ledger params — NOT model inputs
##        (gic_u_unch, gic_delta, gic_u_pre, gic_s_r5; see F_UNCH below)
##     10 AR(1) observation-noise params — NOT model inputs
##
## WHAT IS **NOT** SAMPLED
##   nu_b is FIXED at the anchored value in outputs/extc_block_constants.csv
##   (column nu_anch_obsfit — the calibrator's FIT_BASIS in sampled-amp mode).
##   The hindcast cannot identify nu; freeing it only adds an unconstrained
##   direction. Every consumer must use the SAME basis, hence NU_FIXED here.
##
## THE PER-BLOCK DRIVERS
##   Historical: data/observations/t_glac_blocks.csv — GlaMBIE-area-weighted
##   HadCRUT5 surface temperature per block, K rel. 1850-1900, through 2024.
##   Future: amp_b x GMST(rel 1850-1900), offset so the model driver matches
##   the observed driver over the last 11 observed years (anchor-preserving
##   splice). amp_b is SAMPLED per draw (gic_amp_*), so the splice tail is
##   rebuilt per draw — cheap, it is linear in amp.
##   This reproduces the calibrator's `tg3` construction exactly; the identity
##   is asserted by julia/test_ladrillo_projection.jl.
##
## F_UNCH — A HINDCAST-TARGET CONSTRUCT, NOT A RESERVOIR
##   gic_u_unch prices the uncharted-ice content of the Frederikse glacier
##   target (glaciers absent from the RGI inventory but present in the
##   observational budget). It is held on the MODEL side of the hindcast
##   comparison and never enters the Mimi graph, so the AIS sea-level feedback
##   sees only real reservoir melt. Its taper is exhausted by 2005 (FUNCH_UNIT
##   below), so in a projection re-referenced to 1995-2014 it contributes only
##   a ~1 mm baseline sliver. CONVENTION: include it in hindcast overlays
##   (`funch=true`), exclude it from future-only deltas (the default).
##
## USAGE
##   include(joinpath(@__DIR__, "ladrillo_projection.jl"))
##   bf = ladrillo_setup(ssp="ssp245", y0=1850, y1=2300)     # forcing + drivers
##   post = ladrillo_posterior()                             # 10 000 x 52
##   for r in eachrow(post)
##       ladrillo_run_draw!(bf, r)                           # apply + run(m)
##       total = ladrillo_series(bf, :total)                 # cm, rel. baseline
##   end
## ============================================================================

using CSV, DataFrames, Mimi, MimiBRICK, Statistics
include(joinpath(@__DIR__, "brick_mengel.jl"))

const LADRILLO_REPO = abspath(joinpath(@__DIR__, ".."))
const LADRILLO_OBS  = joinpath(LADRILLO_REPO, "data/observations")

"""Canonical Ladrillo posterior subsample (extC, accepted 2026-08-10, commit 205ccbf)."""
const LADRILLO_POSTERIOR_CSV =
    joinpath(LADRILLO_REPO, "data/MimiBRICK/parameters_subsample_brick_mengel_extC.csv")
const LADRILLO_BLOCK_CONSTANTS_CSV = joinpath(LADRILLO_REPO, "outputs/extc_block_constants.csv")
const LADRILLO_BLOCK_DRIVERS_CSV   = joinpath(LADRILLO_OBS, "t_glac_blocks.csv")
"""Medoid row supplying the params the extC posterior does NOT sample (e.g. ais_sea_level₀)."""
const LADRILLO_MEDOID_CSV = joinpath(LADRILLO_REPO, "outputs/recalib_central_row.csv")

const LADRILLO_BLOCKS = ("R19", "SLOWP", "FAST")
"""nu basis: sampled-amp calibration fits (b, T_off) in the obsfit frame — keep consumers aligned."""
const LADRILLO_NU_BASIS = "obsfit"
"""Baseline period for reported sea level (AR6 / FACTS-comparable)."""
const LADRILLO_REF = (1995, 2014)
"""Rebaseline window for the glacier temperature drivers (the frame contract)."""
const LADRILLO_DRIVER_BASE = (1850, 1900)
"""Preserved T_ant(GMST=0) anchor of the DAIS temperature map (calibrate_mcmc_ext.jl A6)."""
const LADRILLO_AIS_TANT0 = -15.42 / 0.8365

const _GLAC = :glaciers_small_icecaps      # Mimi slot name (kept by replace!)
const _AIS  = :antarctic_icesheet

## ---------------------------------------------------------------------------
## Posterior column -> Mimi parameter map
## ---------------------------------------------------------------------------

"""
21 posterior columns applied straight to a model parameter, as
`(posterior column, component, Mimi parameter)`. `ais_precip0_LOG` is already
log-space (v2.0.0 convention) and is assigned directly.
"""
const LADRILLO_PHYSICAL_PARAMS = [
    ("ais_ocean_temperature₀",   _AIS, :ais_ocean_temperature₀),
    ("antarctic_alpha",          _AIS, :ais_α),
    ("antarctic_nu",             _AIS, :ais_ν),
    ("antarctic_temp_threshold", _AIS, :temperature_threshold),
    ("antarctic_lambda",         _AIS, :λ),
    ("antarctic_gamma",          _AIS, :ais_γ),
    ("antarctic_kappa",          _AIS, :ais_κ),
    ("ais_mu",                   _AIS, :ais_μ),
    ("ais_bedheight0",           _AIS, :ais_bedheight₀),
    ("ais_slope",                _AIS, :ais_slope),
    ("ais_iceflow0",             _AIS, :ais_iceflow₀),
    ("ais_precip0_LOG",          _AIS, :ais_precipitation₀),
    ("ais_c",                    _AIS, :ais_c),
    ("anto_alpha",     :antarctic_ocean,    :anto_α),
    ("anto_beta",      :antarctic_ocean,    :anto_β),
    ("greenland_a",     :greenland_icesheet, :greenland_a),
    ("greenland_b",     :greenland_icesheet, :greenland_b),
    ("greenland_alpha", :greenland_icesheet, :greenland_α),
    ("greenland_beta",  :greenland_icesheet, :greenland_β),
    ("greenland_v0",    :greenland_icesheet, :greenland_v₀),
    ("thermal_alpha",   :thermal_expansion,  :te_α),
]
const LADRILLO_PHYSICAL_COLS = [p[1] for p in LADRILLO_PHYSICAL_PARAMS]
"""Per-block glacier columns applied straight through (kappa is log10 — see apply)."""
const LADRILLO_GLACIER_COLS =
    vcat([["gic_a_$b", "gic_b_$b", "gic_T_off_$b"] for b in LADRILLO_BLOCKS]...)
"""Posterior columns consumed by `ladrillo_run_draw!` but not assigned 1:1 to a parameter."""
const LADRILLO_DERIVED_COLS = vcat(
    ["ais_runoff_Ton",          # with ais_c -> ais_runoffline_snowheight₀
     "ais_gmst_amp"],           # -> the anchor-preserving DAIS temperature map
    ["gic_log10_kappa_$b" for b in LADRILLO_BLOCKS],   # -> gic_kappa_b = 10^theta
    ["gic_amp_$b" for b in LADRILLO_BLOCKS])           # -> per-block driver splice
"""Every posterior column this kernel reads."""
const LADRILLO_USED_COLS =
    vcat(LADRILLO_PHYSICAL_COLS, LADRILLO_GLACIER_COLS, LADRILLO_DERIVED_COLS)

const _GLACIER_SYMS = Dict(nm => Symbol(nm) for nm in LADRILLO_GLACIER_COLS)

"""
    ladrillo_posterior(; path=LADRILLO_POSTERIOR_CSV, cols=:used, nthin=nothing)

Read the Ladrillo posterior subsample. `cols=:used` reads only the columns the
kernel needs (the default — the ledger and AR(1)-noise columns are not model
inputs); `cols=:all` reads the file as-is. `nthin` evenly thins to at most that
many draws.
"""
function ladrillo_posterior(; path::AbstractString=LADRILLO_POSTERIOR_CSV,
                          cols::Symbol=:used, nthin::Union{Nothing,Int}=nothing)
    df = cols === :all ? CSV.read(path, DataFrame) :
                         CSV.read(path, DataFrame; select=LADRILLO_USED_COLS)
    if nthin !== nothing && nrow(df) > nthin
        step = cld(nrow(df), nthin)
        df = df[1:step:nrow(df), :][1:min(nthin, length(1:step:nrow(df))), :]
    end
    return df
end

## ---------------------------------------------------------------------------
## Model + driver setup
## ---------------------------------------------------------------------------

"""
Everything a driver needs to run draws: the built model, the year grid, the
baseline indices, and the pieces of the per-block driver splice that do not
depend on the draw.
"""
struct Ladrillo
    m                                        # Mimi model (glaciers_nu3 in the slot)
    ssp::String
    years::Vector{Int}
    iref::Vector{Int}                        # indices of the reporting baseline
    gmst::Vector{Float64}                    # forcing as fed (rel. 1850-1900 for the SSP files)
    gmst_rb::Vector{Float64}                 # GMST rebased to LADRILLO_DRIVER_BASE
    obs_driver::Dict{String,Vector{Float64}} # observed per-block T, padded to `years`
    obs_anchor::Dict{String,Float64}         # mean observed T over the splice anchor window
    gmst_anchor::Float64                     # mean gmst_rb over the same window
    obs_mask::BitVector                      # years <= last observed driver year
    nu::Dict{String,Float64}                 # FIXED per-block nu
    funch_unit::Vector{Float64}              # F_unch profile per mm of gic_u_unch (m SLE)
end

"""Per-year F_unch profile per mm of uncharted-ice stock U: zero before 1901,
linear to 1970, tapering to zero rate by 2005, flat after. Returns m SLE per mm."""
function _funch_unit(years)
    flat, ramp = 1970 - 1901, 2005 - 1970
    r = (1.0 / 1000.0) / (flat + ramp / 2)
    return [y <= 1901 ? 0.0 :
            y <= 1970 ? r * (y - 1901) :
            y <= 2005 ? r * flat + r * (y - 1970) * (1 - (y - 1970) / (2.0 * ramp)) :
                        r * (flat + ramp / 2.0) for y in years]
end

_yearmap(path, col) = (d = CSV.read(path, DataFrame);
                       Dict(Int(d[i, "year"]) => Float64(d[i, col]) for i in 1:nrow(d)))

"""
    ladrillo_setup(; ssp="ssp245", y0=1850, y1=2300, forcing_tag=ssp, ref=LADRILLO_REF,
                   gmst=nothing, ohc=nothing, lws=:seeded)

Build the Ladrillo model on a scenario, attach forcing, and precompute the
draw-independent parts of the per-block glacier drivers.

`forcing_tag` selects `data/observations/fair_mean_{gmst,ohc}_<tag>.csv`; it
defaults to `ssp`. Pass `gmst`/`ohc` vectors (length `y1-y0+1`) to override the
files entirely — that is how the MAGICC-hybrid and per-member arms inject their
own climate. `ssp` still selects the MimiBRICK scenario used for anything the
forcing override does not cover.
"""
function ladrillo_setup(; ssp::String="ssp245", y0::Int=1850, y1::Int=2300,
                      forcing_tag::String=ssp, ref::Tuple{Int,Int}=LADRILLO_REF,
                      gmst::Union{Nothing,Vector{<:Real}}=nothing,
                      ohc::Union{Nothing,Vector{<:Real}}=nothing,
                      lws::Symbol=:seeded)
    years = collect(y0:y1)
    yi(y) = findfirst(==(y), years)

    if gmst === nothing
        gmst = [_yearmap(joinpath(LADRILLO_OBS, "fair_mean_gmst_$(forcing_tag).csv"), "gmst_C")[y]
                for y in years]
    end
    if ohc === nothing
        ohc = [_yearmap(joinpath(LADRILLO_OBS, "fair_mean_ohc_$(forcing_tag).csv"), "ohc_1e22J")[y]
               for y in years]
    end
    length(gmst) == length(years) || error("ladrillo_setup: gmst has $(length(gmst)) values, need $(length(years))")
    length(ohc)  == length(years) || error("ladrillo_setup: ohc has $(length(ohc)) values, need $(length(years))")

    # Glacier frame: GMST is EXPLICITLY rebased to 1850-1900 so the frame contract
    # does not rest on the forcing file happening to be near zero there.
    ibase = findall(y -> LADRILLO_DRIVER_BASE[1] <= y <= LADRILLO_DRIVER_BASE[2], years)
    gmst_rb = Float64.(gmst) .- mean(Float64.(gmst)[ibase])

    tgb = CSV.read(LADRILLO_BLOCK_DRIVERS_CSV, DataFrame)
    last_obs = Int(maximum(tgb.year))
    last_obs <= y1 || error("ladrillo_setup: observed drivers end $last_obs, past the horizon $y1")
    anchor = (last_obs - 10):last_obs      # 11-yr anchor-preserving splice window
    obs_driver, obs_anchor = Dict{String,Vector{Float64}}(), Dict{String,Float64}()
    for b in LADRILLO_BLOCKS
        d = Dict(Int(tgb[i, :year]) => Float64(tgb[i, b]) for i in 1:nrow(tgb))
        obs_driver[b] = [get(d, y, 0.0) for y in years]     # values past last_obs are masked out
        obs_anchor[b] = mean(d[y] for y in anchor)
    end

    bc = CSV.read(LADRILLO_BLOCK_CONSTANTS_CSV, DataFrame)
    bcrow(b) = bc[findfirst(==(b), bc.block), :]
    nu = Dict(b => Float64(bcrow(b)["nu_anch_$(LADRILLO_NU_BASIS)"]) for b in LADRILLO_BLOCKS)

    m = build_brick_nu3(ssp=ssp, y0=y0, y1=y1, lws=lws)
    medoid = CSV.read(LADRILLO_MEDOID_CSV, DataFrame)[1, :]
    # Initialise from the medoid + the anchored glacier solve. Everything the
    # posterior samples is overwritten per draw; this only fixes the params the
    # extC posterior does NOT carry (e.g. ais_sea_level₀).
    gic3_init = (; (Symbol(b) => (a     = Float64(bcrow(b).a0),
                                  b     = Float64(bcrow(b)["b_fit_$(LADRILLO_NU_BASIS)"]),
                                  T_off = Float64(bcrow(b)["T_off_fit_$(LADRILLO_NU_BASIS)"]),
                                  kappa = Float64(bcrow(b)["kappa_anch_$(LADRILLO_NU_BASIS)"]),
                                  nu    = nu[b]) for b in LADRILLO_BLOCKS)...)
    update_brick_nu3!(m, medoid, gic3_init; precip_log=true)
    set_forcing!(m, gmst, ohc)

    return Ladrillo(m, ssp, years, [yi(y) for y in ref[1]:ref[2]],
                  Float64.(gmst), gmst_rb, obs_driver, obs_anchor,
                  mean(gmst_rb[[yi(y) for y in anchor]]),
                  years .<= last_obs, nu, _funch_unit(years))
end

"""
    ladrillo_driver(bf, block, amp)

The per-block glacier-frame temperature driver: observations where they exist,
`amp * GMST` spliced on afterwards with the offset that preserves the observed
mean over the last 11 observed years.
"""
ladrillo_driver(bf::Ladrillo, block::AbstractString, amp::Real) =
    ifelse.(bf.obs_mask, bf.obs_driver[block],
            amp .* bf.gmst_rb .+ (bf.obs_anchor[block] - amp * bf.gmst_anchor))

## ---------------------------------------------------------------------------
## Applying a draw
## ---------------------------------------------------------------------------

"""
    ladrillo_apply_draw!(bf, row)

Apply one posterior row to the model WITHOUT running it. Sets the 21 direct
physical parameters, the 9 direct glacier parameters, the three per-block
kappas (10^log10kappa), the three per-block drivers (rebuilt at this draw's
amp), and the two derived AIS quantities:

  * `ais_runoffline_snowheight₀ = -ais_runoff_Ton * ais_c` — the runoff line is
    sampled along its identified direction (T_on) rather than as h0 directly;
  * the DAIS temperature map with the T_ant(GMST=0) anchor preserved:
    `coefficient = 1/amp`, `intercept = -T_ant0/amp`, so only the anomaly
    scaling moves.
"""
function ladrillo_apply_draw!(bf::Ladrillo, row)
    m = bf.m
    @inbounds for (col, comp, sym) in LADRILLO_PHYSICAL_PARAMS
        update_param!(m, comp, sym, Float64(row[col]))
    end
    @inbounds for col in LADRILLO_GLACIER_COLS
        update_param!(m, _GLAC, _GLACIER_SYMS[col], Float64(row[col]))
    end
    for b in LADRILLO_BLOCKS
        update_param!(m, _GLAC, Symbol("gic_kappa_$b"), 10.0^Float64(row["gic_log10_kappa_$b"]))
        update_param!(m, _GLAC, Symbol("glacier_surface_temperature_$b"),
                      ladrillo_driver(bf, b, Float64(row["gic_amp_$b"])))
    end
    update_param!(m, _AIS, :ais_runoffline_snowheight₀,
                  -Float64(row["ais_runoff_Ton"]) * Float64(row["ais_c"]))
    amp = Float64(row["ais_gmst_amp"])
    update_param!(m, _AIS, :ais_temperature_coefficient, 1.0 / amp)
    update_param!(m, _AIS, :ais_temperature_intercept, -LADRILLO_AIS_TANT0 / amp)
    return bf
end

"""`ladrillo_apply_draw!` followed by `run`."""
ladrillo_run_draw!(bf::Ladrillo, row) = (ladrillo_apply_draw!(bf, row); run(bf.m); bf)

## ---------------------------------------------------------------------------
## Reading results
## ---------------------------------------------------------------------------

"""Components readable with `ladrillo_series`. `gsic_hind` = SLOWP+FAST (the
hindcast/ledger scope, excluding the R19 seam); `total` is BRICK's summed
`global_sea_level` (glaciers + GIS + AIS + TE + LWS)."""
const LADRILLO_COMPONENTS = Dict{Symbol,Tuple{Symbol,Symbol}}(
    :glaciers   => (_GLAC, :gsic_sea_level),
    :gsic_r19   => (_GLAC, :gsic_r19),
    :gsic_slowp => (_GLAC, :gsic_slowp),
    :gsic_fast  => (_GLAC, :gsic_fast),
    :gsic_hind  => (_GLAC, :gsic_hind),
    :gis        => (:greenland_icesheet, :greenland_sea_level),
    :ais        => (_AIS,  :ais_sea_level),
    :te         => (:thermal_expansion,  :te_sea_level),
    :lws        => (:landwater_storage,  :lws_sea_level),
    :total      => (:global_sea_level,   :sea_level_rise),
)

"""Metres SLE -> cm, re-referenced to the reporting baseline."""
ladrillo_rebase(bf::Ladrillo, v) =
    (x = [ismissing(e) ? NaN : 100.0 * Float64(e) for e in v]; x .- mean(x[bf.iref]))

"""
    ladrillo_series(bf, component; funch=nothing)

One component of the last run, in cm relative to the reporting baseline.

`funch` adds the F_unch uncharted-ice term (mm of stock, i.e. the draw's
`gic_u_unch`) to a glacier series BEFORE re-referencing. Use it for hindcast
overlays against the observational glacier target; leave it off for
projections (see the F_UNCH note in the file header).
"""
function ladrillo_series(bf::Ladrillo, component::Symbol; funch::Union{Nothing,Real}=nothing)
    haskey(LADRILLO_COMPONENTS, component) ||
        error("ladrillo_series: unknown component :$component (have $(sort(collect(keys(LADRILLO_COMPONENTS)))))")
    comp, var = LADRILLO_COMPONENTS[component]
    raw = bf.m[comp, var]
    if funch !== nothing
        component in (:glaciers, :gsic_hind, :total) ||
            error("ladrillo_series: F_unch applies to :glaciers, :gsic_hind or :total, not :$component")
        raw = Float64.(raw) .+ Float64(funch) .* bf.funch_unit
    end
    return ladrillo_rebase(bf, raw)
end

"""Index of year `y` in `bf.years`."""
ladrillo_yi(bf::Ladrillo, y::Int) = findfirst(==(y), bf.years)
