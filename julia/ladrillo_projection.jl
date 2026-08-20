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
##   data/MimiBRICK/parameters_subsample_brick_mengel_L12.csv — 10 000 draws
##   from 4 x 2M chains (seeds 2026-2029, acceptance 0.237), accepted on the
##   deliverable 2026-08-18 (SLR@2100 R-hat 1.002), with the Greenland channel
##   ordering imposed. 57 columns = the 52
##   below with the five stock-SIMPLE Greenland columns replaced by the eight
##   Ladrillo ones (7 sampled gis_* + gis_amp), PLUS the four d2_* basis columns
##   and MINUS sd_dang/rho_dang (dropped by D1). Its predecessor
##   parameters_subsample_brick_mengel_extC.csv (stock SIMPLE, 52 columns) is
##   LADRILLO_POSTERIOR_EXTC_CSV. The column layout of the 52:
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

"""Canonical Ladrillo posterior subsample: tag L12, 4 x 2M chains (seeds
2026-2029, acceptance 0.237 on all four), ACCEPTED ON THE DELIVERABLE
2026-08-18 — projected SLR converges at R-hat 1.002 @2100 / 1.004 @2150 (ESS
1445 / 1401) while 16 parameter marginals are NOT converged (`ais_iceflow0`
R-hat 1.755, improved from L11's 2.449 and L10's 2.359). Consequence, carried
here because this file is what every driver reads: the posterior MAY be used for
projected SLR and anything derived from it, and MAY NOT be used for
parameter-level inference (the pooled AIS-geometry marginals are a mixture of
four chains that never merged, not posteriors). Pooled SLR, cm rel. 1995-2014:
2100 = 45.53 [41.64, 78.55]; 2150 = 70.84 [63.01, 156.74].

L12 = L11's change set PLUS the Greenland CHANNEL-ORDERING constraint
(`--gis-ordered`): every draw satisfies `alpha_s <= alpha_f AND beta_s <=
beta_f`, verified 100.00 % on all 10,000. Timescales are correctly ordered at
every temperature the projections visit (tau_fast 61.7 / tau_slow 194.1 yr at
Tbar), and the long-lived reservoir the earlier vintages lacked is present:
39.96 % of draws exceed 221 yr against L11's 13.61 %. Total SLR is essentially
unchanged from L11 (+0.04 to +0.24 cm @2100), so the constraint bought
interpretability, not different numbers.

57 columns; Greenland is the A+B variant, so consumers must build the model with
`ladrillo_setup(gis_ab=true)` — `ladrillo_posterior_variant()` reads that off the
file. Like L11 and UNLIKE L10 it carries the slow channel in the REPARAMETERISED
`(gis_slow_ell, gis_slow_w)` coordinates, not native `(gis_alpha_s,
gis_beta_s)`, so anything doing parameter-level work on the Greenland channels
must go through `ladrillo_native_greenland!` first. Also carries the four `d2_*`
basis columns and drops `sd_dang`/`rho_dang` (D1)."""
const LADRILLO_POSTERIOR_CSV =
    joinpath(LADRILLO_REPO, "data/MimiBRICK/parameters_subsample_brick_mengel_L12.csv")
"""The L11 posterior (accepted 2026-08-15), which L12 supersedes.

Kept as a named constant on the `LADRILLO_POSTERIOR_L10_CSV` precedent: it is
the provenance of every L11-vintage deliverable, and it is the last
UNCONSTRAINED-Greenland posterior, so it is the fixture for any test that needs
a vintage where the channel ordering does NOT hold — 37.53 % of its draws
satisfy the wedge. `diag_gis_ordering_in_l11_posterior.py` defaults to it
deliberately: its unsuffixed output IS the L11 measurement that the decision to
build L12 rested on, so do not repoint that default at the canonical constant."""
const LADRILLO_POSTERIOR_L11_CSV =
    joinpath(LADRILLO_REPO, "data/MimiBRICK/parameters_subsample_brick_mengel_L11.csv")
"""The L10 posterior (accepted 2026-08-13, commit 6d73349), which L11 supersedes.

Kept as a named constant for the same reason `LADRILLO_POSTERIOR_EXTC_CSV` is:
it is the provenance of every L10-vintage deliverable, AND it is the last
NATIVE-Greenland posterior, so it is the only fixture that exercises the branch
where `ladrillo_native_greenland!` is a no-op. `diag_r19_modern_rate.jl
--check-l10` anchors on it deliberately — do NOT repoint that at the canonical
constant, or the anchor silently starts measuring L11 under an L10 label."""
const LADRILLO_POSTERIOR_L10_CSV =
    joinpath(LADRILLO_REPO, "data/MimiBRICK/parameters_subsample_brick_mengel_L10.csv")
"""The extC posterior (accepted 2026-08-10, commit 205ccbf), which Ladrillo 1.0
supersedes. Kept as a named constant because it is the stock-SIMPLE Greenland
vintage the variant-detection tests exercise, and the provenance of every
pre-L10 deliverable."""
const LADRILLO_POSTERIOR_EXTC_CSV =
    joinpath(LADRILLO_REPO, "data/MimiBRICK/parameters_subsample_brick_mengel_extC.csv")
const LADRILLO_BLOCK_CONSTANTS_CSV = joinpath(LADRILLO_REPO, "outputs/extc_block_constants.csv")
const LADRILLO_BLOCK_DRIVERS_CSV   = joinpath(LADRILLO_OBS, "t_glac_blocks.csv")
# Ladrillo 1.0 Greenland: the regional driver and the two structural constants.
# These MUST match calibrate_mcmc_ext.jl (GIS_ZONE/GIS_AMP/GIS_V0_M/GIS_G) or the
# projections are run on a different model than the one that was calibrated.
const LADRILLO_GIS_DRIVER_CSV = joinpath(LADRILLO_OBS, "t_gis_zones.csv")
const LADRILLO_GIS_ZONE  = "south"
const LADRILLO_GIS_AMP   = 1.92
const LADRILLO_GIS_V0_M  = 7.42
const LADRILLO_GIS_G     = 0.0

## ---------------------------------------------------------------------------
## The Greenland amplification law amp(GMST) — Marcus 2026-08-13
## ---------------------------------------------------------------------------
## Ladrillo 1.0 as calibrated applies a CONSTANT regional amplification to the
## post-2024 splice. CMIP6 says the amplification FALLS with warming level
## (40 models, secant slope -0.050/K [95% -0.079, -0.012], balanced 40-model
## panel monotone 1.498 -> 1.284 over 0.75-2.75 K). The decision was: keep the
## OBSERVED LEVEL (1.922 is only +0.52 sd above the CMIP6 full-window ensemble
## mean, high side but not an outlier) and take only the CMIP6 SHAPE:
##
##     amp(dT) = amp_draw * S(dT),   S = R_secant(dT) / R_secant(dT_eff)
##
## S is tabulated on a fine grid by python/diag_gis_amp_cmip6.py and read here;
## the anchor dT_eff = sum(x^3)/sum(x^2) is the x^2-weighted effective warming
## level of the observed through-origin fit (python/diag_gis_amp_anchor.py), so
## S(dT_eff) = 1 exactly and the law meets the calibration at the point the
## calibration was made. That identity is asserted at load and again in
## validate_gis_projection_ab.jl -- it is what stops this file and the
## calibrator drifting onto different Greenlands now that the projector's amp is
## a function and the calibrator's is a scalar.
##
## PROJECTION-SIDE ONLY. calibrate_mcmc_ext.jl runs 1850-2026, so exactly two of
## its years fall past the splice seam and gis_amp is likelihood-inert there
## (its own comment at the gis_amp prior says so). Nothing here changes any
## calibrated quantity.
##
## LEVEL FORM. S multiplies the amplification, not the temperature: the driver
## is amp*S(dT_t)*GMST_t, because the CMIP6 estimator behind S is a SECANT
## (a level ratio), not a marginal/trend ratio. Integrating a trend ratio is the
## error recorded in memory project_pai_cmip6_time_diagnostic.
## LADRILLO_GIS_SHAPE env var swaps in an alternative shape table, for the
## pre-registered sensitivity arms ONLY (e.g. gis_amp_shape_fullcurve, which
## drops the flat-hold above 2.75 K). It names a stem under outputs/, so the
## table and its meta row cannot be mismatched. Deliverables use the default.
const LADRILLO_GIS_SHAPE_STEM = get(ENV, "LADRILLO_GIS_SHAPE", "gis_amp_shape")
const LADRILLO_GIS_SHAPE_CSV      =
    joinpath(LADRILLO_REPO, "outputs/$(LADRILLO_GIS_SHAPE_STEM).csv")
const LADRILLO_GIS_SHAPE_META_CSV =
    joinpath(LADRILLO_REPO, "outputs/$(LADRILLO_GIS_SHAPE_STEM)_meta.csv")
"""Warming-level averaging window for the shape argument, years. CMIP6 measured
S on 30-yr running windows, so the level fed to S is the same 30-yr running mean
of GMST (centred, shrinking at the ends) rather than the single year — with a
mean-GMST forcing the two differ by little, but the window is what was measured.
Set to 1 for the raw annual level."""
const LADRILLO_GIS_SHAPE_WIN = 30
const _GIS_SHAPE_TBL = CSV.read(LADRILLO_GIS_SHAPE_CSV, DataFrame)
const _GIS_SHAPE_META = CSV.read(LADRILLO_GIS_SHAPE_META_CSV, DataFrame)[1, :]
"""Warming level at which S == 1: the calibration point of the amp law."""
const LADRILLO_GIS_SHAPE_ANCHOR_DT = Float64(_GIS_SHAPE_META.anchor_dt)

"""S(dT), linear interpolation of the emitted grid. The grid is already held FLAT
outside the fitted support (0.75-2.75 K), so clamping at its ends is the same
flat-hold rather than an extrapolation."""
function ladrillo_gis_shape(dt::Real)
    x, y = _GIS_SHAPE_TBL.dt, _GIS_SHAPE_TBL.S
    d = clamp(Float64(dt), first(x), last(x))
    i = searchsortedlast(x, d)
    i >= length(x) && return Float64(y[end])
    w = (d - x[i]) / (x[i+1] - x[i])
    return Float64(y[i]) * (1 - w) + Float64(y[i+1]) * w
end

# The identity the whole construction rests on. If the emitted grid is ever
# re-anchored without re-emitting, this fires at load instead of silently
# rescaling every Greenland projection.
abs(ladrillo_gis_shape(LADRILLO_GIS_SHAPE_ANCHOR_DT) - 1.0) < 1e-9 ||
    error("ladrillo_projection: S(anchor dT = $LADRILLO_GIS_SHAPE_ANCHOR_DT) = " *
          "$(ladrillo_gis_shape(LADRILLO_GIS_SHAPE_ANCHOR_DT)) != 1; " *
          "$(basename(LADRILLO_GIS_SHAPE_CSV)) and " *
          "$(basename(LADRILLO_GIS_SHAPE_META_CSV)) disagree on the anchor")
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

"""Ladrillo 1.0 Greenland (greenland_ab) replaces the five stock-SIMPLE columns
above with these seven. gis_g is FIXED at 0 and gis_v0 is structural, so neither
is a posterior column -- both are set once in `ladrillo_setup`."""
const LADRILLO_GIS_AB_PARAMS = [
    ("gis_c1",      :greenland_icesheet, :gis_c1),
    ("gis_c0",      :greenland_icesheet, :gis_c0),
    ("gis_f",       :greenland_icesheet, :gis_f),
    ("gis_alpha_f", :greenland_icesheet, :gis_alpha_f),
    ("gis_beta_f",  :greenland_icesheet, :gis_beta_f),
    ("gis_alpha_s", :greenland_icesheet, :gis_alpha_s),
    ("gis_beta_s",  :greenland_icesheet, :gis_beta_s),
]
"""The stock-SIMPLE Greenland columns, split out so the two variants can be
swapped as a block."""
const LADRILLO_GIS_STOCK_COLS =
    ["greenland_a", "greenland_b", "greenland_alpha", "greenland_beta", "greenland_v0"]
const LADRILLO_GIS_AB_COLS = vcat([p[1] for p in LADRILLO_GIS_AB_PARAMS], "gis_amp")
"""The A+B Greenland columns as an L11+ posterior CARRIES them: the slow channel
in the sampled `(log r_s, w)` coordinates instead of the native `(alpha_s,
beta_s)` rate pair.

L11 reparameterised the slow channel for CONDITIONING (the native pair is
strongly correlated and `beta_s` sits near a rail), so the chain, the covariance
and the canonical subsample all carry `gis_slow_ell`/`gis_slow_w`. The Mimi
component still takes the native pair. `ladrillo_native_greenland!` maps back;
`ladrillo_posterior` calls it for you."""
const LADRILLO_GIS_SLOW_REPARAM_COLS = ["gis_slow_ell", "gis_slow_w"]
const LADRILLO_GIS_SLOW_NATIVE_COLS  = ["gis_alpha_s", "gis_beta_s"]
const LADRILLO_GIS_AB_REPARAM_COLS =
    vcat(setdiff(LADRILLO_GIS_AB_COLS, LADRILLO_GIS_SLOW_NATIVE_COLS),
         LADRILLO_GIS_SLOW_REPARAM_COLS)
"""The two SAMPLED 3-basin rate scales, as an L13+ posterior carries them: LOG10
scales, matching the calibrator's `10.0^theta[GISB_IDX3[b]]`. `gis_s_south` is the
pinned reference (s = 1) and is never sampled, so it is not here.

A chain that carries these was fitted with `greenland_3basin` in the Greenland
slot. Projecting it through `greenland_ab` silently evaluates it at s = 1 — the
partition-invariance null — which is a model that was never calibrated."""
const LADRILLO_GIS_BASIN_COLS = ["gis_s_mid", "gis_s_high"]
const LADRILLO_GIS_BASIN3_COLS = LADRILLO_GIS_BASIN_COLS
"""The ONE sampled rate scale a `--gis-basins2` (L14+) posterior carries. `gis_s_mid`
is DROPPED from that layout — at `k_mid = 0` it multiplies a zero-commitment basin —
so a 2-basin posterior is identified by `gis_s_high` PRESENT and `gis_s_mid` ABSENT.

THE ABSENCE IS LOAD-BEARING, not a convenience. Testing only for presence made
`all(c in cols for LADRILLO_GIS_BASIN_COLS)` false for an L14 chain, which fell
through to `:ab` and would have projected the whole sheet at s = 1 — the exact
failure this variant exists to close, and the one that cost -1.7 cm on the 2100
median when an L13 chain fell through the same hole before 2026-08-19."""
const LADRILLO_GIS_BASIN2_COLS = ["gis_s_high"]
"""The FIXED volume shares each basin variant projects under. One place, so the
projector cannot use the 3-basin geometry on a 2-basin posterior — which would be
silent: both are valid `k` vectors summing to 1."""
ladrillo_basin_k(variant::Symbol) =
    variant === :basins  ? GIS3_VSHARE :
    variant === :basins2 ? GIS2_VSHARE :
    error("ladrillo_basin_k: :$variant is not a basin variant")

const LADRILLO_PHYSICAL_PARAMS_NOGIS =
    [p for p in LADRILLO_PHYSICAL_PARAMS if !(p[1] in LADRILLO_GIS_STOCK_COLS)]

"""Which Greenland structure a posterior file belongs to, decided by its columns.

There is no default and no fallback: a posterior that carries neither column set
(or both) is a file we do not understand, and guessing would silently project
Greenland at whatever the model was initialised with."""
function ladrillo_gis_variant(cols)
    hasab = all(c -> c in cols, LADRILLO_GIS_AB_COLS)
    hasrp = all(c -> c in cols, LADRILLO_GIS_AB_REPARAM_COLS)
    hasst = all(c -> c in cols, LADRILLO_GIS_STOCK_COLS)
    (hasab || hasrp) && hasst &&
        error("ladrillo_gis_variant: posterior carries BOTH the stock-SIMPLE " *
              "and the A+B Greenland columns; cannot tell which model made it")
    # Both A+B coordinate sets is not an error: an L11 posterior that has already
    # been through ladrillo_native_greenland! legitimately carries both, and the
    # transform is idempotent. Native wins because it is what the model takes.
    hasb3 = all(c -> c in cols, LADRILLO_GIS_BASIN3_COLS)
    # 2-basin is presence of gis_s_high AND ABSENCE of gis_s_mid. Checking presence
    # alone would make an L14 chain indistinguishable from a 3-basin one; checking
    # nothing at all is what made it read as :ab. See LADRILLO_GIS_BASIN2_COLS.
    hasb2 = all(c -> c in cols, LADRILLO_GIS_BASIN2_COLS) &&
            !("gis_s_mid" in cols)
    (hasab || hasrp) && hasb3 && return :basins
    (hasab || hasrp) && hasb2 && return :basins2
    # A+B columns plus a PARTIAL basin set is not :ab — it is a file we do not
    # understand, and :ab is the answer that silently projects a never-calibrated
    # model. Refuse instead.
    if (hasab || hasrp) && ("gis_s_mid" in cols) && !("gis_s_high" in cols)
        error("ladrillo_gis_variant: posterior carries gis_s_mid but NOT gis_s_high. " *
              "No calibrated layout looks like that (3-basin has both, 2-basin has " *
              "only gis_s_high); falling back to :ab would project a model that was " *
              "never calibrated.")
    end
    (hasab || hasrp) && return :ab
    hasst && return :stock
    error("ladrillo_gis_variant: posterior carries NEITHER Greenland column set. " *
          "Expected $(join(LADRILLO_GIS_STOCK_COLS, ", ")) (stock SIMPLE), " *
          "$(join(LADRILLO_GIS_AB_COLS, ", ")) (Ladrillo 1.0), " *
          "or $(join(LADRILLO_GIS_AB_REPARAM_COLS, ", ")) (L11+ reparameterised).")
end

"""True if `cols` carries the slow channel ONLY in the sampled (ell, w)
coordinates, i.e. it needs `ladrillo_native_greenland!` before the draws can be
applied. Consumers that read a chain or subsample themselves (rather than
through `ladrillo_posterior`) must check this."""
ladrillo_gis_needs_native(cols) =
    all(c -> c in cols, LADRILLO_GIS_SLOW_REPARAM_COLS) &&
    !all(c -> c in cols, LADRILLO_GIS_SLOW_NATIVE_COLS)

"""Greenland slow-channel driver temperature, the calibrator's `GIS_TBAR`.

Recomputed from the driver with the calibrator's own 1.963 K assertion rather
than hardcoded, so the two cannot drift apart silently — the transform below is
wrong by exactly the ratio if they do."""
const LADRILLO_GIS_TBAR_WIN = (2015, 2024)
const LADRILLO_GIS_TBAR = let tgz = CSV.read(LADRILLO_GIS_DRIVER_CSV, DataFrame)
    mean(Float64(tgz[i, LADRILLO_GIS_ZONE]) for i in 1:nrow(tgz)
         if LADRILLO_GIS_TBAR_WIN[1] <= Int(tgz[i, :year]) <= LADRILLO_GIS_TBAR_WIN[2])
end
abs(LADRILLO_GIS_TBAR - 1.963) < 5e-3 ||
    error("LADRILLO_GIS_TBAR = $LADRILLO_GIS_TBAR from $LADRILLO_GIS_TBAR_WIN disagrees " *
          "with the calibrator's asserted 1.963 K")

"""
    ladrillo_native_greenland!(df)

Add the native slow-channel pair to an L11+ posterior, in place, from the
sampled `(gis_slow_ell, gis_slow_w)`:

    r_s = exp(ell);  alpha_s = w*r_s/Tbar;  beta_s = (1-w)*r_s

This is the INVERSE of the calibrator's forward map (`calibrate_mcmc_ext.jl`,
the `GIS_REPARAM` branch), and it is the only place the projection stack knows
it. No-op on a posterior that already carries the native pair, so it is safe to
call unconditionally and safe to call twice."""
function ladrillo_native_greenland!(df)
    ladrillo_gis_needs_native(String.(names(df))) || return df
    r_s = exp.(Float64.(df.gis_slow_ell)); w_s = Float64.(df.gis_slow_w)
    df.gis_alpha_s = w_s .* r_s ./ LADRILLO_GIS_TBAR
    df.gis_beta_s  = (1 .- w_s) .* r_s
    return df
end
"""Which Greenland variant a posterior FILE carries, from its header alone.

Drivers must call this BEFORE `ladrillo_setup`, because `gis_ab=` decides which
Greenland slot the model is built with; setting up wrong and then applying draws
fails at apply time, after the setup cost, rather than projecting the wrong
Greenland — but only because `ladrillo_apply_draw!` checks. Do not guess."""
ladrillo_posterior_variant(path::AbstractString=LADRILLO_POSTERIOR_CSV) =
    ladrillo_gis_variant(String.(propertynames(CSV.read(path, DataFrame; limit=0))))

"""Per-block glacier columns applied straight through (kappa is log10 — see apply)."""
const LADRILLO_GLACIER_COLS =
    vcat([["gic_a_$b", "gic_b_$b", "gic_T_off_$b"] for b in LADRILLO_BLOCKS]...)
"""Posterior columns consumed by `ladrillo_run_draw!` but not assigned 1:1 to a parameter."""
const LADRILLO_DERIVED_COLS = vcat(
    ["ais_runoff_Ton",          # with ais_c -> ais_runoffline_snowheight₀
     "ais_gmst_amp"],           # -> the anchor-preserving DAIS temperature map
    ["gic_log10_kappa_$b" for b in LADRILLO_BLOCKS],   # -> gic_kappa_b = 10^theta
    ["gic_amp_$b" for b in LADRILLO_BLOCKS])           # -> per-block driver splice
"""Every posterior column this kernel reads, for a given Greenland variant."""
ladrillo_used_cols(variant::Symbol) = vcat(
    [p[1] for p in LADRILLO_PHYSICAL_PARAMS_NOGIS],
    variant === :stock ? LADRILLO_GIS_STOCK_COLS : LADRILLO_GIS_AB_COLS,
    variant === :basins  ? LADRILLO_GIS_BASIN3_COLS :
    variant === :basins2 ? LADRILLO_GIS_BASIN2_COLS : String[],
    LADRILLO_GLACIER_COLS, LADRILLO_DERIVED_COLS)
## No variant-free column list: it would silently mean ":stock" and every
## consumer of it would check the wrong contract on a Ladrillo 1.0 posterior
## (exactly how test_ladrillo_projection.jl failed when the canonical posterior
## moved to L10). Ask for the variant you have: ladrillo_used_cols(VARIANT).

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
    if cols === :all
        df = CSV.read(path, DataFrame)
        return ladrillo_native_greenland!(nthin === nothing ? df : _ladrillo_thin(df, nthin))
    else
        # CSV.jl's `select=` silently returns only the columns it FINDS, so a
        # posterior missing a required column used to load fine and fail later
        # (or, worse, project at whatever the model was initialised with). Read
        # the header, decide the Greenland variant from it, then demand the full
        # set for that variant.
        hdr = String.(propertynames(CSV.read(path, DataFrame; limit=0)))
        want = ladrillo_used_cols(ladrillo_gis_variant(hdr))
        # An L11+ posterior stores the slow channel as (ell, w); ask the file for
        # what it HAS, then derive the native pair the kernel needs after reading.
        # Demanding alpha_s/beta_s here would reject every post-L11 posterior.
        ladrillo_gis_needs_native(hdr) &&
            (want = vcat(setdiff(want, LADRILLO_GIS_SLOW_NATIVE_COLS),
                         LADRILLO_GIS_SLOW_REPARAM_COLS))
        missing_cols = [c for c in want if !(c in hdr)]
        isempty(missing_cols) || error("ladrillo_posterior: $path is missing " *
            "$(length(missing_cols)) required column(s): $(join(missing_cols, ", "))")
        df = CSV.read(path, DataFrame; select=want)
    end
    nthin === nothing || (df = _ladrillo_thin(df, nthin))
    return ladrillo_native_greenland!(df)
end

"""Evenly thin to at most `n` rows."""
function _ladrillo_thin(df, n::Int)
    nrow(df) > n || return df
    step = cld(nrow(df), n)
    return df[1:step:nrow(df), :][1:min(n, length(1:step:nrow(df))), :]
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
    gis_variant::Symbol                      # :ab (Ladrillo 1.0), :basins (L13 3-basin), :basins2 (L14 2-basin), :stock (SIMPLE)
    gis_obs::Vector{Float64}                 # observed regional Greenland T, padded to `years`
    gis_anchor::Float64                      # mean observed regional T over the splice anchor
    gis_mask::BitVector                      # years <= last observed Greenland driver year
    gis_shape::Vector{Float64}               # S(warming level) per year; ALL ONES when the law is off
    gis_shape_anchor::Float64                # mean(S_t * gmst_rb_t) over the splice anchor window
    gis_shape_on::Bool                       # whether amp(GMST) is applied at all
end

"""Centred running mean of `v` over `w` years, shrinking at the ends. `w = 1`
returns `v`. Matches the CMIP6 window that measured S (30 yr, centre = window
midpoint)."""
function _running_mean(v::AbstractVector{<:Real}, w::Int)
    w <= 1 && return Float64.(v)
    n, lo, hi = length(v), (w - 1) ÷ 2, w ÷ 2
    return [mean(@view v[max(1, i - lo):min(n, i + hi)]) for i in 1:n]
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
                      lws::Symbol=:seeded, gis_ab::Bool=false,
                      gis_variant::Union{Nothing,Symbol}=nothing,
                      gis_shape::Bool=true)
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

    # Greenland variant. The regional driver is built HERE, from the same file and
    # with the same anchor-preserving splice the calibrator uses, so the projection
    # and the calibration see the same construction. GIS_AMP is not sampled (the
    # calibrator fixes it too), so the driver is fixed and computed once.
    # `gis_variant=` is the full three-way selector; `gis_ab=` is the older boolean
    # and stays exact for :ab / :stock. Passing both must AGREE -- silently
    # preferring one would let a caller ask for the 3-basin model and get A+B,
    # which is the very failure this variant exists to close.
    gis_variant === nothing && (gis_variant = gis_ab ? :ab : :stock)
    gis_variant in (:ab, :basins, :basins2, :stock) ||
        error("ladrillo_setup: unknown gis_variant :$gis_variant")
    (gis_ab && gis_variant === :stock) &&
        error("ladrillo_setup: gis_ab=true contradicts gis_variant=:stock")
    gis_ab = gis_variant !== :stock          # the A+B-shaped Greenland driver path
    gis_obs, gis_anchor, gis_mask = Float64[], 0.0, falses(length(years))
    gis_shape_v, gis_shape_anchor = Float64[], 0.0
    if gis_ab
        tgz = CSV.read(LADRILLO_GIS_DRIVER_CSV, DataFrame)
        gd = Dict(Int(tgz[i, :year]) => Float64(tgz[i, LADRILLO_GIS_ZONE]) for i in 1:nrow(tgz))
        gis_last = Int(maximum(tgz.year))
        gis_last <= y1 || error("ladrillo_setup: Greenland driver ends $gis_last, past $y1")
        ganch = (gis_last - 10):gis_last
        gis_obs = [get(gd, y, 0.0) for y in years]      # values past gis_last are masked out
        gis_anchor = mean(gd[y] for y in ganch)
        gis_mask = years .<= gis_last
        # The amp law. S is evaluated on the running-mean warming level; the
        # anchor scalar is mean(S_t * GMST_t) over the SAME 11-yr splice window
        # the constant-amp version anchors on, so the splice still reproduces the
        # observed mean there exactly whether or not the law is on.
        gis_shape_v = gis_shape ?
            ladrillo_gis_shape.(_running_mean(gmst_rb, LADRILLO_GIS_SHAPE_WIN)) :
            ones(length(years))
        ianch = [yi(y) for y in ganch]
        gis_shape_anchor = mean(gis_shape_v[ianch] .* gmst_rb[ianch])
    end
    # :basins2 builds the SAME component as :basins — greenland_3basin at k_mid = 0
    # IS the two-basin model. Only the k vector differs, and it is bound below.
    m = gis_variant in (:basins, :basins2) ?
                                  build_brick_nu3_gis3(ssp=ssp, y0=y0, y1=y1, lws=lws) :
        gis_variant === :ab     ? build_brick_nu3_gis(ssp=ssp, y0=y0, y1=y1, lws=lws) :
                                  build_brick_nu3(ssp=ssp, y0=y0, y1=y1, lws=lws)
    medoid = CSV.read(LADRILLO_MEDOID_CSV, DataFrame)[1, :]
    # Initialise from the medoid + the anchored glacier solve. Everything the
    # posterior samples is overwritten per draw; this only fixes the params the
    # extC posterior does NOT carry (e.g. ais_sea_level₀).
    gic3_init = (; (Symbol(b) => (a     = Float64(bcrow(b).a0),
                                  b     = Float64(bcrow(b)["b_fit_$(LADRILLO_NU_BASIS)"]),
                                  T_off = Float64(bcrow(b)["T_off_fit_$(LADRILLO_NU_BASIS)"]),
                                  kappa = Float64(bcrow(b)["kappa_anch_$(LADRILLO_NU_BASIS)"]),
                                  nu    = nu[b]) for b in LADRILLO_BLOCKS)...)
    update_brick_nu3!(m, medoid, gic3_init; precip_log=true, skip_greenland=gis_ab)
    set_forcing!(m, gmst, ohc)
    if gis_ab
        # the driver itself is rebuilt PER DRAW from that draw's gis_amp; this is
        # only a valid placeholder so the model builds
        set_gis_forcing!(m, gis_obs)
        update_param!(m, :greenland_icesheet, :gis_v0, LADRILLO_GIS_V0_M)   # structural
        update_param!(m, :greenland_icesheet, :gis_g,  LADRILLO_GIS_G)      # item 4.1: fixed 0
    end
    # Mouginot volume shares + unit rate scales, matching calibrate_mcmc_ext.jl's
    # `GIS_BASINS && update_gis3_shares!(m)`. The three `gis_s_b` are unbound
    # Parameters after `build_brick_nu3_gis3`, so this is required, not cosmetic;
    # the two SAMPLED scales are overwritten per draw in `ladrillo_apply_draw!`
    # and `gis_s_south` stays pinned at the reference value 1.
    gis_variant in (:basins, :basins2) &&
        update_gis3_shares!(m; k = ladrillo_basin_k(gis_variant))

    return Ladrillo(m, ssp, years, [yi(y) for y in ref[1]:ref[2]],
                  Float64.(gmst), gmst_rb, obs_driver, obs_anchor,
                  mean(gmst_rb[[yi(y) for y in anchor]]),
                  years .<= last_obs, nu, _funch_unit(years),
                  gis_variant, gis_obs, gis_anchor, gis_mask,
                  gis_shape_v, gis_shape_anchor, gis_shape)
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

"""Regional Greenland driver at this draw's `amp`, same anchor-preserving splice.

gis_amp is SAMPLED (it is the dominant control on the 2100 projection -- across
its prior the scenario spread runs 7.4 to 12.6 cm), so the driver is rebuilt per
draw here exactly as the glacier block drivers are.

With the amp law on (`ladrillo_setup(gis_shape=true)`, the default) the
amplification is `amp * S(warming level)` rather than the constant `amp`; the
offset still preserves the observed mean over the 11-yr anchor window, because
`gis_shape_anchor` is that window's mean of `S_t * GMST_t`. With the law off
`gis_shape` is all ones and `gis_shape_anchor` reduces to `gmst_anchor`, i.e.
the expression below is identically the constant-amp splice."""
ladrillo_gis_driver(bf::Ladrillo, amp::Real) =
    ifelse.(bf.gis_mask, bf.gis_obs,
            amp .* bf.gis_shape .* bf.gmst_rb .+ (bf.gis_anchor - amp * bf.gis_shape_anchor))

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
    # The row and the model must agree on which Greenland structure they are.
    # Without this the kernel would apply whatever it could and leave the slot at
    # its initialised values -- projections that are neither variant, silently.
    gis_params = bf.gis_variant === :stock ?
        [p for p in LADRILLO_PHYSICAL_PARAMS if p[1] in LADRILLO_GIS_STOCK_COLS] :
        LADRILLO_GIS_AB_PARAMS
    @inbounds for (col, comp, sym) in Iterators.flatten((LADRILLO_PHYSICAL_PARAMS_NOGIS,
                                                         gis_params))
        update_param!(m, comp, sym, Float64(row[col]))
    end
    bf.gis_variant !== :stock &&
        set_gis_forcing!(m, ladrillo_gis_driver(bf, Float64(row["gis_amp"])))
    # The two sampled basin rate scales, LOG10 as the chain carries them --
    # identical to calibrate_mcmc_ext.jl's `10.0^theta[GISB_IDX3[b]]`. south is
    # the pinned reference and keeps the s = 1 bound at setup.
    # k FOLLOWS THE VARIANT. Using GIS3_VSHARE on a 2-basin draw would be silent —
    # both are valid k vectors summing to 1 — and would load a basin the calibration
    # held empty. s_mid is 1.0 under :basins2: the column does not exist, and at
    # k_mid = 0 the value is inert anyway.
    bf.gis_variant in (:basins, :basins2) &&
        update_gis3_shares!(m; k = ladrillo_basin_k(bf.gis_variant),
                            s = (south = 1.0,
                                 mid   = bf.gis_variant === :basins2 ? 1.0 :
                                         10.0^Float64(row["gis_s_mid"]),
                                 high  = 10.0^Float64(row["gis_s_high"])))
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
