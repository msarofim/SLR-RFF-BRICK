## ============================================================================
## calibrate_mcmc_ext.jl  —  BRICK-Mengel MCMC on the EXTENDED (post-2018) targets
##
## ★ CANONICAL BRICK-AM calibration (mean forcing). Forcing is a FIXED prior — NOT a free parameter;
## propagate FaIR forcing uncertainty FORWARD (LHS-10k pairing), never re-calibrate it against SLR.
## The joint free-forcing alternative (calibrate_mcmc_joint*.jl) was tested and REJECTED 2026-08-01
## (SLR must not re-infer the forcing; the coupling is immaterial to total SLR). See
## notes/negresult_2026-08-01_joint_forcing_calibration.md.
##
## Variant of calibrate_mcmc.jl that re-fits the SAME 28-param posterior against
## recalibration targets EXTENDED past Frederikse 2020's 2018 end with modern
## reconciled products (GRACE-FO AIS/GIS ->2025, GlaMBIE GSIC ->2023, NOAA NCEI
## steric ->2025, NOAA STAR total ->2024). Purpose (Marcus 2026-06-13): quantify
## how post-2018 obs -- especially the post-2020 Antarctic GRACE-FO pause -- shift
## ais_ocean_temperature0 and the SSP-2100 projections.
##
## Differences vs calibrate_mcmc.jl (the 2018-only baseline; kept untouched for A/B):
##   1. Reads outputs/recalib_targets_ext.csv (1900-2026, NaN where a component has
##      no data) instead of recalib_targets.csv.
##   0. v-next (2026-07-18): the 7 DAIS geometry params -- previously FIXED at the prior
##      medoid -- are FREED under a joint MvNormal paleo-covariance prior (Strategy B),
##      taking the param count 28 -> 35. See the GEO block below.
##   2. Model run window extended Y1 1850->2026 (forcing fair_mean_*.csv already
##      reaches 2301, so the SAME forcing is used -- only the window changes).
##   3. PER-SERIES fit windows: each component fit to its own valid (non-missing)
##      year range -> the AR(1) likelihood gets a different-length residual vector
##      per series. (All series are contiguous 1900..end, asserted below.)
##   4. DROPS the IMBIE dAIS(92-17) + Dyurgerov dGSIC(61-03) Gaussian point terms:
##      the extended AIS/GSIC time-series now constrain the modern rate directly
##      (Marcus 2026-06-13 -- avoids double-weighting; see prep README).
##
## PHASE-2 (2026-07-20, Marcus-approved scope; see notes/handoff_2026-07-19_*):
##   A2. λ / ais_γ / ais_κ FREED under their existing paleo marginals (were fixed at
##       the medoid; λ dominates the 100/150-yr pulse with zero reported uncertainty).
##   A4. Runoff line reparameterized to its identified direction: sample
##       (T_on = -h0/c, c) under the transformed joint paleo prior
##       (paleo_geo_prior_ton.csv); h0 = -T_on*c is reconstructed per draw.
##       Posterior r(h0,c) was 0.9997 and the fitted onset (+0.62 C GMST) unphysical.
##   A5. One SMB likelihood term: model β_total (1979-2008 mean, Gt/yr) vs
##       area-scaled Rignot 2019. Breaks the SMB-discharge input-output degeneracy
##       (posterior pinned the difference 34:1 tighter than either flux).
##   A6. GMST->Antarctic temperature map sampled as transient amplification `amp`
##       (anchor preserved), prior centered on CMIP6 PAI1 (Xie et al. 2022).
##   Param count 35 -> 39 (25 -> 29 physical).
##
## extB3 (2026-08-07, post-D0-shootout; memo_2026-08-05 §3e + §5-D0):
##   * Glacier component REPLACED: glaciers_mengel (2-τ) -> glaciers_nu (Mengel S_eq +
##     Nauels-2017 single-reservoir ν transient; ν=0 nests Mengel; melt-only clamp).
##   * Glacier DRIVER: glacier-area-weighted observed T (t_glac_hadcrut5.csv) + 1.8×GMST
##     tail splice — Option D. All gic_* params/priors are GLACIER-FRAME quantities.
##   * gic block: (a, b, T_off, log10κ, ν); b prior re-centered 0.52->0.29 (frame);
##     ν N(1.0,0.5)[0,2.5] = projection-informed prior (hindcast cannot identify ν).
##   * Param count 39 -> 38 (29 -> 28 physical). extB1/extB2 tags are burned (falsified);
##     run with --tag=extB3. Port validation: julia/validate_glaciers_nu.jl (4/4 PASS).
##
## Usage:  julia --project=julia_v2 julia/calibrate_mcmc_ext.jl [n_iter] [seed] [--overdisperse] [--amp-equilibrium]
##   --overdisperse     start each chain from a real over-dispersed posterior draw (production)
##   --amp-equilibrium  A6 SENSITIVITY: pin the amplification at the old equilibrium 1.196
##                      (prior N(1.19546,0.002)); output infix -> "extA6eq". Isolates A6.
##
## PARALLEL LAUNCH -- PIN BLAS TO ONE THREAD (measured 2026-08-12, 4x2M on an Apple M4):
##   for s in 2026 2027 2028 2029; do
##     OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
##       julia --project=julia_v2 --threads=1 julia/calibrate_mcmc_ext.jl 2000000 $s \
##       --tag=L10 --overdisperse &
##   done; wait
## Julia defaults to BLAS.get_num_threads() == 4, so a NAKED 4-chain launch spawns 16 BLAS
## threads onto an M4's FOUR performance cores (hw.perflevel0.physicalcpu = 4; the other 6
## are efficiency cores). Measured cost of getting this wrong: ETA 11h vs 2h17m, a 4.8x
## slowdown, with each process burning ~200% CPU of which about half is OpenBLAS spin-wait.
## Pinning to 1 thread puts each chain on its own P-core and recovers the full single-chain
## rate (stage-1 solo chain was 2h25m; four pinned chains finish in ~2h20m TOTAL).
## The RAM sampler's per-iteration work is a 55x55 Cholesky update -- far below the size
## where threaded BLAS pays for itself, so the threads were never buying anything here.
## ============================================================================

using CSV, DataFrames, Mimi, MimiBRICK, Statistics, LinearAlgebra, Distributions, Random, Printf
using RobustAdaptiveMetropolisSampler
include(joinpath(@__DIR__, "brick_mengel.jl"))

const REPO = abspath(joinpath(@__DIR__, ".."))
const OBS  = joinpath(REPO, "data/observations")
const Y0, Y1, B0, B1 = 1850, 2026, 1995, 2005          # Y1 1850->2026 (was 2018)
const TARGETS = joinpath(REPO, "outputs/recalib_targets_ext.csv")
# --amp-equilibrium: A6 SENSITIVITY run. Pins the GMST->AIS amplification at the OLD
# equilibrium value (1/0.8365 = 1.19546) instead of the CMIP6-transient N(0.95,0.10) prior,
# so the ONLY difference from the production run is A6. Everything else (A2/A4/A5, the
# Dangendorf/STAR targets) is identical -> isolates A6's effect on the SLR headline. Output
# infix becomes "extA6eq" so its chains do NOT match the production "chain_ext_seed*" glob.
const AMP_EQ = "--amp-equilibrium" in ARGS
# 2026-07-22 (CMIP6 secant update): optional A6-prior overrides, so a new amplification
# prior can be run WITHOUT touching the phase-2 defaults. --amp-mu=/--amp-sigma= set the
# prior; --tag= renames the output infix so new chains do NOT match the phase-2
# chain_ext_seed* glob. With no overrides, behaviour is bit-for-bit the phase-2 setup.
_argval(pfx) = (i = findfirst(a -> startswith(a, pfx), ARGS);
                i === nothing ? nothing : ARGS[i][length(pfx)+1:end])
const AMP_MU_OVR    = _argval("--amp-mu=")
const AMP_SIGMA_OVR = _argval("--amp-sigma=")
const TAG_OVR       = _argval("--tag=")
# --drop-total: SPEC D1 (Marcus 2026-08-14, spec_2026-08-14_next_calibration.md §2).
# Removes the independent-total ("dang") likelihood term AND its sd_dang/rho_dang
# noise pair, 55 -> 53 sampled parameters. OPT-IN, so the shipped L10
# configuration stays bit-for-bit reproducible; flip the default only when D1 is
# promoted to production. The tie it removes is EXACT per draw:
# total_model - sum(component_models) = gsic_tot - gsic_flow = the R19 seam. Note
# this is a deliberate DISCARD of an independent observational constraint, not the
# removal of a double-count (spec §8.1) -- the Wong weights are already off for
# this arm, so total GMSL enters exactly once, here.
# APPROVED CHANGE SET, Marcus 2026-08-14: drop the total, add the GlaMBIE R19
# rate, tighten the rung — together, because they interact. The total was the
# only thing constraining R19 and it was pinning it at 97-99% committed at EVERY
# warming level (no scenario response), 3x GlaMBIE's observed modern rate, and
# 1.0-1.8 sigma above the GlacierMIP3 rungs; R19 is the one component with no
# target of its own, so it absorbs the Frederikse-vs-Dangendorf budget
# non-closure. Dropping the total removes the cause; the other two supply R19
# with constraints of its own. Each has a restore flag, and all three together
# reproduce the L10 configuration bit-identically.
const DROP_TOTAL    = !("--keep-total" in ARGS)
const R19_RATE_ON   = !("--no-r19-rate" in ARGS)
const RUNG_SIG_LEGACY = "--rung-sig-legacy" in ARGS
const D2_ON = !("--no-d2" in ARGS)
const GIS_REPARAM = !("--gis-native" in ARGS)
const TAG = TAG_OVR !== nothing ? TAG_OVR :
            (AMP_EQ ? "extA6eq" : (DROP_TOTAL ? "D1" : "ext"))   # output infix
years = collect(Y0:Y1); ib = [findfirst(==(y),years) for y in B0:B1]; idx(y)=findfirst(==(y),years)
N_ITER = length(ARGS)>=1 ? parse(Int,ARGS[1]) : 2000
SEED   = length(ARGS)>=2 ? parse(Int,ARGS[2]) : 2026

# ---- AR(1) heteroscedastic log-likelihood (Ruckert et al. 2017; MimiBRICK form) ----
function hetero_logl_ar1(res::Vector{Float64}, σ::Float64, ρ::Float64, ϵ::Vector{Float64})
    n = length(res)
    σp = σ^2/(1-ρ^2)
    H  = abs.(collect(1:n)' .- collect(1:n))
    Σ  = σp .* ρ.^H .+ Diagonal(ϵ.^2)
    return logpdf(MvNormal(Symmetric(Σ)), res)
end

# ---- forcing (UNCHANGED series, just read through Y1) + extended targets ----
lc(p,c)=(d=CSV.read(p,DataFrame); Dict(Int(d[i,"year"])=>Float64(d[i,c]) for i in 1:nrow(d)))
# v-next (2026-07-18): forcing switched from the RFF-SP-central splice to the SSP2-4.5
# HARMONIZED splice, so the calibration sits on the SAME forcing as the pulse projections
# (fairtable7_v145_pulse.py uses emissions_v145_ssp245_harmonized.csv) and matches this
# script's build_brick_mengel(ssp="ssp245"). Both splices share the Smith historical, so
# 1850-2020 is unchanged; they differ only over ~2020-2026 of the fit window (mean
# |dGMST| 0.03 C) and in the post-fit tail. NOT the same as fair_mean_*_ssp245.csv, which
# is RCMIP-native (run_fair_ssps.py) rather than harmonized.
const FORCING_TAG = "ssp245harm"
gmst=[lc(joinpath(OBS,"fair_mean_gmst_$(FORCING_TAG).csv"),"gmst_C")[y] for y in years]
ohc =[lc(joinpath(OBS,"fair_mean_ohc_$(FORCING_TAG).csv"),"ohc_1e22J")[y] for y in years]
println("forcing: fair_mean_{gmst,ohc}_$(FORCING_TAG).csv")
tg = CSV.read(TARGETS, DataFrame)

# ---- extC (2026-08-09): PER-BLOCK glacier drivers — 3-reservoir surgery ------------------
# Blocks R19 {19} / SLOWP {03,09,07,06} / FAST {13 regions} (d1d C_both, Marcus green-light).
# Observed block drivers from data/observations/t_glac_blocks.csv (GlaMBIE-area-weighted
# HadCRUT5, K rel 1850-1900; machine-generated by python/build_extc_inputs.py), spliced
# forward with amp_b × GMST (anchor-preserving, 11-yr window ending at the obs last year —
# the offline extend_obs convention). GMST is explicitly rebased to 1850-1900 so the frame
# contract is not resting on the ssp245harm ~0.0000 coincidence.
# amp basis selectable: --amp-basis=regchar|obsfit (D1f sensitivity arm 2026-08-09:
# MID-arm deficit invariant to the basis; projections differ ~1.5 cm at SSP2-4.5).
const AMP_G = 1.8            # aggregate convention (d0 gates/patho frame; kept for reference)
# amp handling (Marcus 2026-08-09 FINAL: SAMPLED, dataset-informed priors).
# Cross-dataset evidence (diag_amp_dataset_comparison, commit c52bd42): HadCRUT5 is
# mid-range on SLOWP (BE 1.82 / Had 2.48 / GISTEMP 3.46); R19 weakly constrained in
# every product; regchar sits below the obs range. Priors = center near HadCRUT5 with
# σ from the dataset spread; hard bounds = the cross-dataset ranges.
# Fixed-basis modes (regchar/obsfit) retained for A/B arms.
const AMP_BASIS = something(_argval("--amp-basis="), "sampled")
AMP_BASIS in ("sampled", "regchar", "obsfit") || error("--amp-basis must be sampled|regchar|obsfit")
const SAMPLED_AMP = AMP_BASIS == "sampled"
const BLOCKS = ["R19", "SLOWP", "FAST"]
const HIND_BLOCKS = ["SLOWP", "FAST"]   # r19 seam: excluded from the flow/ledger scope
bcdf = CSV.read(joinpath(REPO, "outputs/extc_block_constants.csv"), DataFrame)
bcrow(b) = bcdf[findfirst(==(b), bcdf.block), :]
const AMP_PRIOR = Dict("R19"   => (0.72, 0.15, 0.58, 0.88),
                       "SLOWP" => (2.50, 0.45, 1.80, 3.50),
                       "FAST"  => (1.45, 0.15, 1.33, 1.82))   # (μ, σ, lo, hi)
# NB sampled amp touches the LIKELIHOOD only via the rung frame-conversion and the
# κ-prior center: the drivers' amp-dependent part is the 2025-2026 splice tail, which
# no likelihood term reads (gsic obs end 2023; GlaMBIE rate ends at melt[2024] ←
# T[2023] = obs). Drivers are therefore built ONCE at the amp-prior centers.
const AMP_B = SAMPLED_AMP ?
    Dict(b => AMP_PRIOR[b][1] for b in BLOCKS) :
    Dict(b => Float64(bcrow(b)["amp_$(AMP_BASIS)"]) for b in BLOCKS)
# κ-anchor center as a function of amp: log-linear interpolation between the two
# precomputed τ50 anchor solves (regchar-amp and obsfit-amp points, per block) — keeps
# the τ50-as-prior centered consistently when amp moves.
const K10_PTS = Dict(b => ((Float64(bcrow(b).amp_regchar),
                            log10(Float64(bcrow(b).kappa_anch_regchar))),
                           (Float64(bcrow(b).amp_obsfit),
                            log10(Float64(bcrow(b).kappa_anch_obsfit)))) for b in BLOCKS)
function k10c(b, amp)
    (a1, k1), (a2, k2) = K10_PTS[b]
    return k1 + (k2 - k1) * (amp - a1) / (a2 - a1)
end
const K10_SIG = 0.114        # ±30% at 1σ — the ANCH-vs-MID freedom (offline evidence)
const FIT_BASIS = SAMPLED_AMP ? "obsfit" : AMP_BASIS   # θ0 (b, T_off) start frame
const KAP_ANCH = SAMPLED_AMP ?
    Dict(b => 10.0^k10c(b, AMP_B[b]) for b in BLOCKS) :
    Dict(b => Float64(bcrow(b)["kappa_anch_$(AMP_BASIS)"]) for b in BLOCKS)
const NU_ANCH  = Dict(b => Float64(bcrow(b)["nu_anch_$(FIT_BASIS)"]) for b in BLOCKS)
const S2020_D  = Dict(b => Float64(bcrow(b).S2020_data)              for b in BLOCKS)
const GLAMBIE_RATE = Dict(b => Float64(bcrow(b).glambie_rate)    for b in BLOCKS)
const GLAMBIE_SD   = Dict(b => Float64(bcrow(b).glambie_rate_sd) for b in BLOCKS)
tgb = CSV.read(joinpath(REPO, "data/observations/t_glac_blocks.csv"), DataFrame)
const TGB_LAST = Int(maximum(tgb.year))
const IB5900 = findall(y -> 1850 <= y <= 1900, years)
gmst_rb = gmst .- mean(gmst[IB5900])
tg3 = let gmd = Dict(zip(years, gmst_rb)), anchor = (TGB_LAST-10):TGB_LAST
    d = Dict{String,Vector{Float64}}()
    for b in BLOCKS
        obsd = Dict(Int(tgb[i, :year]) => Float64(tgb[i, b]) for i in 1:nrow(tgb))
        off = mean(obsd[y] for y in anchor) - AMP_B[b] * mean(gmd[y] for y in anchor)
        d[b] = [y <= TGB_LAST ? obsd[y] : AMP_B[b]*gmd[y] + off for y in years]
    end
    (R19=d["R19"], SLOWP=d["SLOWP"], FAST=d["FAST"])
end
@printf("glacier drivers: t_glac_blocks.csv 1850-%d + amp_b x GMST splice | basis=%s | amp R19 %.2f / SLOWP %.2f / FAST %.2f\n",
        TGB_LAST, AMP_BASIS, AMP_B["R19"], AMP_B["SLOWP"], AMP_B["FAST"])

# ============================================================================
# GREENLAND A+B — the Ladrillo 1.0 module (Greenland pass-1 step 5)
# ============================================================================
# Replaces stock SIMPLE greenland_icesheet with julia/greenland_ab_component.jl:
# a REGIONAL rate driver plus a two-channel SMB/dynamic split. Structure chosen
# offline in python/gis_offline_cell.py (cell "A+B"); the Mimi port is validated
# against that cell at 1e-9 by julia/validate_greenland_ab.jl.
# --stock-gis reverts to stock SIMPLE (the extC parameter set) for A/B work.
#
# THE EXTERNAL INTERFACE IS STILL GMST + OHC ONLY. The regional driver is built
# HERE, inside the model's own inputs, exactly as the glacier block drivers are.
# Do not promote it to a required input -- that drop-in property is what
# distinguishes Ladrillo from MAGICC-SLR.
const GIS_AB = !("--stock-gis" in ARGS)
# --gis-zone=<south|all|central|north>. A FLAG, not a source edit, for the same
# reason --adcov is: the arm becomes runnable, reviewable in the run script, and
# recorded in the log, instead of living as an uncommitted one-character diff.
# Default "south" = the shipped L11/L12/L13 line (Marcus 2026-08-10).
const GIS_ZONE = something(_argval("--gis-zone="), "south")
GIS_ZONE in ("south","all","central","north") ||
    error("--gis-zone=$GIS_ZONE is not a column of t_gis_zones.csv " *
          "(south, all, central, north)")
const GIS_AMP_WINDOW = "full"     # gis_amp_prior.csv row selector; "early"/"modern" are arms
#
# THE AMP PRIOR IS READ FROM ITS SOURCE, keyed on (GIS_ZONE, GIS_AMP_WINDOW).
# Until 2026-08-20 all four numbers — mean, sd, lo, hi — were hand-transcribed
# literals and only the MEAN carried a name; the sd/lo/hi sat inline in the FREE
# push! a few hundred lines below, with no reference to GIS_ZONE at all. So
# flipping GIS_ZONE to "all" would have moved GIS_AMP 1.92 -> 2.347 while silently
# LEAVING the prior at south's N(., 0.32) on [1.51, 2.28] — a prior whose upper
# bound (2.28) sits BELOW the new mean (2.347), i.e. the sampler would have been
# pinned against a bound it could never leave, with no error. That is the
# `~/.claude/CLAUDE.md` "labels derive from named constants" rule and it is the
# same failure shape as the L11_NAMES mis-map: a hand-maintained copy of data that
# lives somewhere else, silently wrong when the key changes.
const GIS_AMP_PRIOR = let f = joinpath(REPO, "outputs/gis_amp_prior.csv")
    isfile(f) || error("missing $f — regenerate with python/diag_gis_amp_cmip6.py")
    df = CSV.read(f, DataFrame)
    i = findfirst(r -> r.zone == GIS_ZONE && r.window == GIS_AMP_WINDOW, eachrow(df))
    isnothing(i) && error("gis_amp_prior.csv has no row for zone=$GIS_ZONE " *
                          "window=$GIS_AMP_WINDOW; rows present: " *
                          join(["$(r.zone)/$(r.window)" for r in eachrow(df)], ", "))
    r = df[i, :]
    (mean=Float64(r.mean), sd=Float64(r.sd), lo=Float64(r.lo), hi=Float64(r.hi))
end
const GIS_AMP = GIS_AMP_PRIOR.mean
# PROVENANCE: the shipped L11/L12/L13 line ran with GIS_AMP hardcoded to the
# ROUNDED 1.92, not the CSV's 1.9221976. Deriving moves the prior mean by +0.0022
# (0.007 sd) and the built driver's post-2024 splice with it, so an L12 re-run from
# this file is no longer bit-identical to the shipped L12 — it is 0.007 sd away.
# Bounded and stated rather than silently absorbed; reproduce the exact shipped L12
# from commit ab069bd or earlier.
GIS_ZONE != "south" || abs(GIS_AMP - 1.92) < 5e-3 ||
    error("south/full amp is $GIS_AMP, not within 5e-3 of the shipped 1.92 — " *
          "gis_amp_prior.csv has changed under the calibration; re-check before running")
const GIS_V0_M = 7.42             # Greenland volume, m SLE — STRUCTURAL, not sampled
# ---- 3-basin (Mouginot sector) Greenland + the per-sector SHARES term ---------
# Handoff notes/handoff_2026-08-19_calibrator_sector_shares.md. The shipped A+B is
# calibrated to the TOTAL Greenland loss on a single regional driver, so its rate
# constants absorb mass that came from basins it does not represent — NW alone is
# 17.3% of the volume and 31.7% of the 1972-2018 loss. --gis-basins puts the three
# Mouginot sector groups in the slot (julia/greenland_3basin_component.jl, gated by
# julia/test_greenland_3basin_nesting.jl) and adds ONE rate scale per basin. The
# geometry — the volume shares k_b — is FIXED, never sampled.
const GIS_BASINS2 = "--gis-basins2" in ARGS
const GIS_BASINS = ("--gis-basins" in ARGS) || GIS_BASINS2
GIS_BASINS && !GIS_AB && error("--gis-basins requires the A+B Greenland module (drop --stock-gis)")
# ---- --gis-basins2: the TWO-basin configuration (Marcus 2026-08-20) -----------
# NO NEW COMPONENT. `greenland_3basin` at k_mid = 0 IS a two-basin model, and it is
# so BY CONSTRUCTION rather than by test: eq_b == k_b * eq_whole identically (see
# the clamp algebra in greenland_3basin_component.jl), so a zero share contributes
# a zero series to every sum. Measured anyway at max|gis_sl_mid| = 0.0 and
# active/high/total differing by 0.000e+00, and gated by
# julia/test_greenland_3basin_nesting.jl [4].
#
#   active = SW + CW + CE + SE + NW   (the merged basin, carried in the `south` slot)
#   high   = NO + NE                  (unchanged)
#
# WHY. A full refit of every structure in the offline harness returns s_mid = 1.024;
# pinning it to 1 costs Delta nlp 0.0023, and the PROFILE IS WELL CURVED (+6.3 at
# s_mid 0.25, +7.3 at 3.98), so s_mid is IDENTIFIED-and-equal-to-1 rather than merely
# unconstrained. Two basins also fit the Mouginot windows BETTER — worst |z| 0.69 vs
# 1.01 — with one fewer parameter, because a single NW scale cannot span the
# two-window tension 0.207 -> 0.262. Evidence: 03df3d2,
# outputs/scope_gis_basin_structure{,_profile}.csv; handoff_2026-08-20b/c.
#
# THE `south` SLOT IS NOT RENAMED. It carries the merged `active` basin. The output
# contract (gis_fast / gis_slow / greenland_sea_level as basin sums, plus
# gis_sl_{south,mid,high}) is what every downstream consumer reads; renaming buys
# nothing and would silently break diag_l13_basin_shares.jl and ladrillo_projection.
#
# STANDING CAVEAT on all of the above: the evidence is the Greenland-ONLY offline
# cell — no BRICK coupling, no AR(1) noise, none of the other likelihood terms. It
# has NOT been shown to transfer. That transfer is what the L14 run tests.
GIS_BASINS2 && !GIS_BASINS && error("--gis-basins2 implies the basin component")
# The term itself is separable from the state, so step 2 of the handoff's order of
# work (basins in, term OFF, confirm the total is unchanged) is reachable as a run.
const GISB_TERM = GIS_BASINS && !("--no-gis-shares" in ARGS)
# THE VOLUME SHARES ACTUALLY USED. Both tables are DERIVED from GIS3_VOL_M in
# greenland_3basin_component.jl, never typed as literals here: the two-basin k is
# (south + mid, 0, high) = (0.628571, 0, 0.371429), and a literal would silently stop
# tracking the Mouginot inventory if it is ever revised. Everything downstream — the
# setup banner, --gis-check's s = 1 null, the component wiring — reads GISB_K, so
# there is exactly one place the geometry lives.
const GISB_K = GIS_BASINS2 ? GIS2_VSHARE : GIS3_VSHARE
abs(sum(GISB_K) - 1) < 1e-12 ||
    error("basin volume shares must sum to 1, got $(sum(GISB_K)) for k = $GISB_K")
# The basins with a NON-ZERO share. A zero-share basin has no state, so a rate scale
# on it multiplies nothing: it would be a DEAD SAMPLED PARAMETER — a random walk that
# inflates the proposal and hides defects. Dropping gis_s_mid here is what takes NK
# from 59 to 58, which is why the L13 covariance must be embedded BY NAME.
const GISB_LIVE = Tuple(b for b in GIS3_BASINS if getproperty(GISB_K, b) > 0)
# Every banner, target line and diagnostic label derives from HERE, so a flag change
# cannot leave a run log claiming a structure it did not run.
const GISB_MODE_LABEL = GIS_BASINS2 ?
    "2 basins, active{SW+CW+CE+SE+NW} / high{NO+NE} (--gis-basins2, k_mid = 0)" :
    "3 Mouginot sectors, south{SW+CW+CE+SE} / mid{NW} / high{NO+NE}"

# TARGET — the MODERN RATE shares, NOT the cumulative 1972-2018 split. Greenland was
# near balance before the mid-1990s (the south basin was GAINING mass in 1972-1990,
# whole-sheet +15.9 Gt/yr in 1972-1981), so an early-window share is a ratio with a
# vanishing denominator: the 1972-1981 "shares" come out 2.272 / -0.911 / -0.361.
# Post-2002 the split is stable to about ±0.03. Two well-separated modern windows,
# so the term is TIME-RESOLVED (Marcus 2026-08-19) and the drift between them is
# itself information about whether the model reproduces the EVOLUTION of the
# partition, not merely its level.
# Provenance: python/diag_gis_basin_lit_check.py block 1c ->
# outputs/diag_gis_basin_lit_check.csv, parsed from Mouginot 2019 Dataset S2.
const GISB_WINS = ((2002, 2011), (2012, 2018))
# ONLY south and mid are scored. The three shares sum to 1, so a third term adds no
# information and makes the block rank-deficient by one — it would just re-weight
# the same constraint by ~1.5x. high follows, and --gis-check prints it.
# `high` is the DEPENDENT share — the one that follows by sum-to-one and is
# therefore never scored. Named, so the "score all but one" rule below is a
# derivation rather than a hand-maintained pair of lists that can drift apart.
const GISB_DEPENDENT = :high
const GISB_SCORED = Tuple(b for b in GISB_LIVE if b != GISB_DEPENDENT)
# The Mouginot 3-way table. NEVER read directly by the likelihood — GISB_SHARE below
# is what is scored, and under --gis-basins2 it is the MERGED table.
const GISB_SHARE3 = ((south = 0.592, mid = 0.207, high = 0.201),   # 2002-2011, -245.6 Gt/yr
                     (south = 0.554, mid = 0.262, high = 0.183))   # 2012-2018, -264.3 Gt/yr
# TWO-BASIN TARGETS ARE THE MERGE, not a separate measurement: active = south + mid,
# giving 0.799 / 0.201 and 0.816 / 0.183. Derived rather than typed for the same
# reason GISB_K is — one revision of Mouginot, one place to change. Only ONE share is
# independent now, so GISB_SCORED collapses to (:south,); scoring both would
# double-count the single observation.
const GISB_SHARE = GIS_BASINS2 ?
    Tuple((south = sh.south + sh.mid, mid = 0.0, high = sh.high) for sh in GISB_SHARE3) :
    GISB_SHARE3
# sigma on a SHARE, matching MOUG_SHARE_SD and comfortably covering the ±0.03
# window-to-window spread. Deliberately NOT Mouginot's published per-region mass
# errors (30-91 Gt): those are far too tight to accommodate the 1.227x total
# disagreement between Mouginot's sector sum and the calibration target.
const GISB_SHARE_SD = 0.05
# A vanishing total rate makes every share undefined. The guard is load-bearing here
# in a way it is not for MOUG_SHARE: with sectors the denominator genuinely passes
# through zero in the early record, so dividing without it produces garbage rather
# than a mild bias. The windows above are chosen to sit far from it — this catches
# a PROPOSAL that wanders there, not the target.
const GISB_TOT_FLOOR = 1e-12
# REFERENCE BASIN — pinned at s = 1, NOT sampled. Measured 2026-08-19, and it is a
# property of the reduced form rather than a tuning choice: the basin rate is
# clip(s_b * (alpha*T + beta)), so scaling EVERY s_b by c while scaling the shared
# shape rates (alpha_f, beta_f, and r_s through ell) by 1/c leaves the model
# EXACTLY invariant — verified at 0.0 max|diff| over c in [0.25, 10], with 1.1e-16
# at c = 10 as pure roundoff. The common mode of the three log s_b is therefore a
# perfectly flat likelihood direction, broken only by the priors, and sampling it
# collapsed acceptance from 0.268 to 0.012-0.014 (measured with the shares term
# both ON and OFF, so it is the DIMENSION and not the term).
# Only the RATIOS carry information, which is exactly what the shares term can
# identify: two independent shares per window. Pinning south makes mid and high
# read as "rate relative to the south basin" and leaves the overall level where it
# already lived — in the shipped shape parameters.
const GISB_REF = :south
# LIVE basins only: a zero-share basin gets no sampled scale (see GISB_LIVE).
const GISB_FREE_BASINS = Tuple(b for b in GISB_LIVE if b != GISB_REF)
# gis_g is FIXED AT 0 (item 4.1, 2026-08-12): profiled over [0, 0.8] the offline
# objective moves 4e-4 nlp and the 2100 projections do not move at all, and it is
# confounded with gis_c0. 0 is also stock SIMPLE's own initial condition.
const GIS_G = 0.0

# Mouginot 2019 SMB/discharge partition: the extra loss rate of 2000-2018 over
# 1972-1990 is 73.5% surface. This is what makes the two-channel split
# identifiable -- without it f and the timescales trade off freely, which is why
# the offline cell carried it and why it is ported into the joint likelihood
# below rather than left as a prior on f.
const MOUG_SHARE, MOUG_SHARE_SD = 0.735, 0.05
const MOUG_REF_WIN, MOUG_LATE_WIN = (1972, 1990), (2000, 2018)
tgz = CSV.read(joinpath(REPO, "data/observations/t_gis_zones.csv"), DataFrame)
const TGZ_LAST = Int(maximum(tgz.year))
# ---- item 1.2: Greenland slow channel sampled as (level, tilt) ----------------
# rate_s(T) = alpha_s*T + beta_s is reparameterised as
#     ell = log r_s(Tbar)                 the LEVEL of the slow rate at Tbar
#     w   = alpha_s*Tbar / r_s(Tbar)      the share of that level carried by T
# inverse alpha_s = w*e^ell/Tbar, beta_s = (1-w)*e^ell, which keeps both
# non-negative for w in [0,1]. Measured gain (python/diag_gis_slow_reparam.py):
# mean WITHIN-CHAIN |corr| over the four L10 chains falls 0.578 -> 0.139, and a
# Tbar scan bottoms at 0.135 near 1.90 K, so the anchor is essentially optimal.
# It does NOT un-rail anything -- alpha_s=0 maps to w=0 and beta_s=0 to w=1, so
# both bounds move into the tilt. The gain is that the LEVEL, which is the
# direction the chains do not mix along, gets its own unbounded coordinate.
#
# Tbar is the 2015-2024 anchor of the regional driver, COMPUTED from the driver
# rather than hardcoded so it cannot drift from t_gis_zones.csv.
const GIS_TBAR_WIN = (2015, 2024)
const GIS_TBAR = mean(Float64(tgz[i, GIS_ZONE]) for i in 1:nrow(tgz)
                      if GIS_TBAR_WIN[1] <= Int(tgz[i, :year]) <= GIS_TBAR_WIN[2])
# THE ASSERTION IS ZONE-AWARE. It used to compare against a bare 1.963 for every
# zone, which is SOUTH's anchor: switching GIS_ZONE to "all" (Tbar 2.6543) tripped an
# error whose text blamed t_gis_zones.csv drift. That failed safe — loudly, and it is
# why this is a cheap fix rather than a postmortem — but the message pointed at the
# wrong cause and the real constraint went unstated. The real constraint is that the
# (ell, w) SLOW-CHANNEL REPARAMETERISATION was chosen at south's Tbar = 1.963
# (notes/spec_2026-08-14 §4): ell = log r_s and w are defined RELATIVE to the anchor,
# so moving the anchor moves what the (ell, w) priors mean. Switching zones is
# therefore NOT a one-line change — it re-anchors the reparameterisation, and the
# priors must be re-derived at the new Tbar before the run is meaningful.
const GIS_TBAR_REPARAM_ANCHOR = 1.963      # spec_2026-08-14 §4, GIS_ZONE = "south"
if GIS_ZONE == "south"
    abs(GIS_TBAR - GIS_TBAR_REPARAM_ANCHOR) < 5e-3 ||
        error("GIS_TBAR = $GIS_TBAR from $(GIS_TBAR_WIN) disagrees with the " *
              "$GIS_TBAR_REPARAM_ANCHOR K on which the reparameterisation was chosen " *
              "(notes/spec_2026-08-14 section 4) — t_gis_zones.csv has drifted")
else
    error("GIS_ZONE = \"$GIS_ZONE\" gives Tbar = $(round(GIS_TBAR, digits=4)) K against " *
          "south's $GIS_TBAR_REPARAM_ANCHOR K.\n" *
          "  The (ell, w) priors themselves are FINE — GIS_ELL_MU/GIS_W_MU already derive " *
          "from GIS_TBAR, so they re-anchor automatically (south ell -4.2074 w 0.9328 -> " *
          "all ell -3.9234 w 0.9494).\n" *
          "  WHAT DOES NOT MOVE is the offline A+B fit those centres are built on: " *
          "GIS_NATIVE_MU (the native alpha_s/beta_s centres, defined below) " *
          "and the gis_c1/gis_c0/gis_f/gis_alpha_f/gis_beta_f prior centres, plus the " *
          "GIS_OFFLINE_G0 reference --gis-check scores against. Those are PHYSICAL rate " *
          "constants fitted against the SOUTH temperature series; the same alpha_s on a " *
          "driver $(round(GIS_TBAR/GIS_TBAR_REPARAM_ANCHOR, digits=3))x hotter at the anchor " *
          "produces correspondingly more melt, so the priors would be centred on the wrong " *
          "physics.\n" *
          "  PREREQUISITE: re-run the offline A+B Greenland fit on the \"$GIS_ZONE\" driver, " *
          "update GIS_NATIVE_MU + the five gis_* centres + GIS_OFFLINE_G0, regenerate the " *
          "--gis-check reference (do NOT widen its tolerance), then relax this branch.")
end
# PRIORS ARE SPECIFIED DIRECTLY IN (ell, w), NOT inherited through the transform.
# Only 33.2% of draws from the (alpha_s, beta_s) priors fall inside the native
# bounds, so what those priors actually encode is a pair of heavily truncated
# half-normals, not the N(mu, sigma) the code appears to state; and the induced
# (ell, w) prior correlates 0.315 at the anchor, against 0.0 for independent ones.
# ell, w CENTRES: chosen so theta0 maps EXACTLY onto the native prior centres
#   (alpha_s 0.0070727, beta_s 0.0010), NOT onto the offline optimum. The
#   calibrator centres beta_s at 1e-3 DELIBERATELY, off its 1e-6 rail, and
#   centring ell on the optimum instead silently moved theta0 to
#   (alpha_s 0.00354, beta_s 0.00695) -- which the GIS wiring test caught as a
#   Mouginot surface share of 0.7716 against the offline 0.7351. Mapping the
#   centres through the transform preserves both the deliberate off-rail choice
#   and the wiring test. sd = 1.0 (MARCUS,
#   2026-08-14): tau_s 23-172 yr at 1 sigma and to 469 yr at 2 sigma, which covers
#   L10's posterior (29-136 yr) with room above it while NOT admitting the
#   millennial arm. Widening to reach the commitment ridge's ~1300 yr was offered
#   and declined: without an external Leq(T) constraint that admits the ridge
#   rather than resolving it, and makes the 2300 projection prior-dominated along
#   a direction the hindcast cannot see. The reparam stays a CONDITIONING fix.
# w: FLAT on [0, 1] (sigma = 1e3, the gic_u_unch pattern). It is a share, the L10
#   posterior spans 0.08-0.95, and a flat prior makes ell and w independent by
#   construction.
const GIS_NATIVE_MU = (alpha_s = 0.0070727, beta_s = 0.0010)   # the native centres
const GIS_ELL_MU = log(GIS_NATIVE_MU.alpha_s * GIS_TBAR + GIS_NATIVE_MU.beta_s)
const GIS_W_MU   = GIS_NATIVE_MU.alpha_s * GIS_TBAR /
                   (GIS_NATIVE_MU.alpha_s * GIS_TBAR + GIS_NATIVE_MU.beta_s)
const GIS_ELL_SD = 1.0
# The transform must be a pure change of COORDINATES, not of model. Assert the
# round trip at load: (alpha_s, beta_s) -> (ell, w) -> (alpha_s, beta_s).
let a0 = 0.0070727, b0 = 0.0010, r0 = 0.0070727 * GIS_TBAR + 0.0010
    ell0 = log(r0); w0 = a0 * GIS_TBAR / r0
    a1 = w0 * exp(ell0) / GIS_TBAR; b1 = (1 - w0) * exp(ell0)
    (abs(a1 - a0) < 1e-12 && abs(b1 - b0) < 1e-12) ||
        error("(ell, w) round trip is not exact: alpha_s $a0 -> $a1, beta_s $b0 -> $b1")
    (abs(exp(ell0) - (a0 * GIS_TBAR + b0)) < 1e-12) ||
        error("exp(ell) must equal r_s(Tbar) = alpha_s*Tbar + beta_s")
    # theta0 EQUIVALENCE: the reparameterised centres must reproduce the native
    # ones, or the sampler silently starts somewhere else and the GIS wiring test
    # fails downstream instead of here.
    aM = GIS_W_MU * exp(GIS_ELL_MU) / GIS_TBAR
    bM = (1 - GIS_W_MU) * exp(GIS_ELL_MU)
    (abs(aM - GIS_NATIVE_MU.alpha_s) < 1e-12 && abs(bM - GIS_NATIVE_MU.beta_s) < 1e-12) ||
        error("(ell, w) prior centres map to (alpha_s $aM, beta_s $bM), not the " *
              "native ($(GIS_NATIVE_MU.alpha_s), $(GIS_NATIVE_MU.beta_s))")
end
# The zone column is ALREADY an anomaly on the 1850-1900 frame (verified: mean
# over that window is -0.0), so it is used as-is, matching gis_offline_cell.py.
tgis = let obsd = Dict(Int(tgz[i, :year]) => Float64(tgz[i, GIS_ZONE]) for i in 1:nrow(tgz)),
           gmd = Dict(zip(years, gmst_rb)), anchor = (TGZ_LAST-10):TGZ_LAST
    off = mean(obsd[y] for y in anchor) - GIS_AMP * mean(gmd[y] for y in anchor)
    [y <= TGZ_LAST ? obsd[y] : GIS_AMP * gmd[y] + off for y in years]
end
if GIS_AB
    @printf("greenland driver: t_gis_zones.csv[%s] 1850-%d + amp %.2f x GMST splice | gis_g FIXED %.1f | Mouginot share %.3f+/-%.3f\n",
            GIS_ZONE, TGZ_LAST, GIS_AMP, GIS_G, MOUG_SHARE, MOUG_SHARE_SD)
    if GIS_BASINS
        @printf("greenland basins: %s on the SHARED %s driver | k FIXED %s | rate scales sampled for %s (%s PINNED at 1: the common mode is exactly degenerate with the shape rates) | sector shares term %s\n",
                GISB_MODE_LABEL, GIS_ZONE,
                join((@sprintf("%s %.6f", b, getproperty(GISB_K, b)) for b in GIS3_BASINS), " / "),
                join(GISB_FREE_BASINS, "+"), GISB_REF,
                GISB_TERM ? "ON" : "OFF (--no-gis-shares)")
        GISB_TERM && for (w, sh) in zip(GISB_WINS, GISB_SHARE)
            @printf("    %d-%d target: %s scored at %s +/- %.3f (%s %.3f follows by sum-to-one)\n",
                    w[1], w[2], join(GISB_SCORED, "+"),
                    join((@sprintf("%.3f", getproperty(sh, b)) for b in GISB_SCORED), "/"),
                    GISB_SHARE_SD, GISB_DEPENDENT, getproperty(sh, GISB_DEPENDENT))
        end
    end
else
    println("greenland: STOCK SIMPLE (--stock-gis) — the extC parameter set")
end

ϵband(lo,hi)=max.((hi.-lo)./(2*1.645), 0.05)           # per-year obs σ (floor 0.05cm)

# Budget-closure inflation of the TOTAL target's σ (Marcus ruling, 2026-08-12, gate 3.1).
# The five component targets (Frederikse) sum +0.74cm above the independent total
# (Dangendorf + NOAA STAR) over 1950-1980; that is Frederikse's OWN budget non-closure, so
# it is carried as uncertainty on the total rather than resolved by the sampler. Shape and
# magnitude come from Frederikse's own 5000-member ensemble, per year, over the WHOLE span
# -- no window edge and no decay function is chosen. Column built by
# python/prep_recalib_targets_ext.py (CLOSURE_SIG_COL); see the constant block there for
# the flagged AR(1) double-counting caveat. --no-closure-sigma reverts to the old σ.
const CLOSURE_SIGMA_OFF = "--no-closure-sigma" in ARGS
const CLOSURE_SIG_COL = :dang_closure_sig
closure_sigma(ri) = (CLOSURE_SIGMA_OFF || !hasproperty(tg, CLOSURE_SIG_COL)) ?
    zeros(length(ri)) : coalesce.(Float64.(tg[ri, CLOSURE_SIG_COL]), 0.0)

# per-series valid years: target value present (non-missing, non-NaN) AND >=1900
function series_years(col)
    ys = Int[]
    for i in 1:nrow(tg)
        v = tg[i,col]
        (tg.year[i] >= 1900 && !ismissing(v) && !isnan(Float64(v))) && push!(ys, Int(tg.year[i]))
    end
    return sort(ys)
end
rowof(y) = findfirst(==(y), tg.year)
# build a series record: fit years, model-output indices, obs vector, obs-σ vector
function make_series(col, lo, hi; isdang=false)
    fy = series_years(col)
    @assert fy == collect(fy[1]:fy[end]) "series $col has a year gap (AR(1) assumes unit spacing)"
    ri = [rowof(y) for y in fy]
    ob = Float64.(tg[ri, col])
    if isdang   # total obs error = altimetry/Dangendorf σ ⊕ LWS-budget σ ⊕ budget-closure σ
        ev = sqrt.(Float64.(tg.dang_sig[ri]).^2 .+
                   ϵband(Float64.(tg.lws_lo[ri]), Float64.(tg.lws_hi[ri])).^2 .+
                   closure_sigma(ri).^2)
    else
        ev = ϵband(Float64.(tg[ri,lo]), Float64.(tg[ri,hi]))
    end
    return (years=fy, myi=[idx(y) for y in fy], obs=ob, ϵ=ev)
end
S = (ais    = make_series(:ais,:ais_lo,:ais_hi),
     gsic   = make_series(:gsic,:gsic_lo,:gsic_hi),
     gis    = make_series(:gis,:gis_lo,:gis_hi),
     steric = make_series(:steric,:steric_lo,:steric_hi),
     dang   = make_series(:dang,:dang_lo,:dang_hi; isdang=true))
# LWS to add into the modeled total, aligned to the dang fit years
lws_dang = Float64.(tg.lws[[rowof(y) for y in S.dang.years]])
println("Extended fit windows: ais 1900-$(S.ais.years[end]), gis 1900-$(S.gis.years[end]), ",
        "gsic 1900-$(S.gsic.years[end]), steric 1900-$(S.steric.years[end]), total 1900-$(S.dang.years[end])")
let ri = [rowof(y) for y in S.dang.years], cs = closure_sigma(ri)
    base = sqrt.(S.dang.ϵ.^2 .- cs.^2)
    @printf("total-target σ: budget-closure inflation %s | 1900 %.3f→%.3f (%.2fx), 1950 %.3f→%.3f (%.2fx), 2000 %.3f→%.3f (%.2fx), %d %.3f→%.3f (%.2fx)\n",
            CLOSURE_SIGMA_OFF ? "OFF (--no-closure-sigma)" : "ON (Frederikse ensemble, per year)",
            (vcat([[base[i], S.dang.ϵ[i], S.dang.ϵ[i]/base[i]]
                   for i in [findfirst(==(y), S.dang.years) for y in (1900, 1950, 2000)]]...))...,
            S.dang.years[end], base[end], S.dang.ϵ[end], S.dang.ϵ[end]/base[end])
end

# ---- extB3b fallback: REMOVED 2026-08-14, obsolete (spec_2026-08-14 §8.2) -----------------
# `--gsic-early-sigma-x2` inflated the GSIC flow σ before 1940 by ×2. It was the documented
# remedy for the extB3 wiggle-tracking mode (σ_gsic → 0.032 cm with ρ 0.96, gic_nu piled at 0,
# S(1900) median 45 mm, 0/4 evaluation gates). That mode's cause was a FREE ν; ν is now fixed
# at the anchored value and is not sampled at all, and L10 sits at σ_gsic 0.0156 / ρ 0.649 —
# nowhere near the signature. The flag was never passed to any shipped run (L10 launched as
# `--tag=L10 --overdisperse`), so this was dead code guarding a condition that can no longer
# arise. Recoverable from git history if the ν-free configuration is ever revisited.

# ---- extC: r19-seam-adjusted gsic target (obs_adj) + δ ramp ------------------------------
# The Frederikse gsic segment assumes zero r19 melt; the GlaMBIE splice (2019+) includes it.
# obs_adj removes the observed GlaMBIE r19 cumulative from 2019+ so the whole target is
# scope-without-r19, matching the model's hindcast scope (gsic_hind = SLOWP+FAST).
# Machine-generated by python/build_extc_inputs.py (asserted vs the raw column there).
gadj = CSV.read(joinpath(REPO, "outputs/recalib_targets_ext_gsicadj.csv"), DataFrame)
@assert Int.(gadj.year) == S.gsic.years "gsicadj year grid mismatch vs gsic target"
let pre = S.gsic.years .< 2019
    @assert maximum(abs.(Float64.(gadj.gsic_adj)[pre] .- S.gsic.obs[pre])) < 1e-6 "obs_adj pre-2019 identity violated"
end
net_rm_mm = 10 * (S.gsic.obs[end] - Float64(gadj.gsic_adj[end]))
@assert net_rm_mm > 0 "net r19 removal must be positive at series end"
S.gsic.obs .= Float64.(gadj.gsic_adj)
@printf("gsic target: r19-seam adjusted (net removal at %d: %.3f mm)\n",
        S.gsic.years[end], net_rm_mm)
# δ (M15 early-segment bias, offline T5d): obs-side rate correction on 1900-1959,
# obs_corr[y] = obs[y] + δ·(1960−y)/10 cm (δ in mm/yr; prior N(0, 0.30) via the FREE entry)
const DELTA_RAMP = [y < 1960 ? (1960.0 - y)/10.0 : 0.0 for y in S.gsic.years]

# ---- D2: model-discrepancy term delta(t) on gsic and steric (spec section 3) ----
# SCOPE. Only these two streams have residuals approaching their own observation
# bands (resid sd / mean band sigma on L10: ais 0.17, gsic 1.06, gis 0.33,
# steric 0.95). Greenland's old pathology was the MODULE, fixed by A+B, so it is
# not here.
#
# FORM. A low-order polynomial basis, NOT a GP: the degrees of freedom are
# countable, the priors are interpretable in cm, and — the reason it is chosen —
# the basis can be made ORTHOGONAL to the things delta(t) must not steal.
#
# WHAT IT IS ORTHOGONALISED AGAINST, and why this is the whole design:
#   * THE CONSTANT, on both streams, so delta(t) cannot absorb a pure level shift.
#   * THE STERIC SHAPE S(t) ITSELF, on steric. CORRECTED 2026-08-14 after the
#     L11tune2 diagnostic: orthogonalising against the constant alone was NOT
#     enough and the first version FAILED here, with corr(d2_steric_1,
#     thermal_alpha) = -0.724. The reasoning behind that version was wrong.
#     te_sea_level = te_s0 + te_alpha * S(t), so thermal_alpha rescales the
#     SHAPE, not the level -- and a mean-zero polynomial closely resembles that
#     shape, so it traded off against alpha directly. The protection has to be
#     against S(t). Conveniently S(t) is exactly the OHC forcing up to an
#     additive constant (te_sea_level accumulates Delta_oceanheat, so the sum
#     telescopes to OHC(t) - OHC(1)), and the constant is removed by the
#     ones-projection anyway. delta(t) can then only describe structure that a
#     rescaling of the driver cannot -- which is what a discrepancy term is for.
#   * DELTA_RAMP, on gsic only. gsic ALREADY carries a one-parameter obs-side
#     early-century discrepancy (gic_delta, the M15/Roe-2021 ramp over 1900-1959).
#     Orthogonalising against it means the new term can only describe structure
#     that ramp does not already explain, instead of fighting it.
#
# Basis vectors are normalised to unit RMS over the fit window, so a coefficient
# is an RMS discrepancy in cm and the prior sd is directly interpretable.
const D2_BASIS_N  = 2        # polynomial dof per stream AFTER orthogonalisation
const D2_BASIS_SD = 0.5      # cm, prior sd on each coefficient (residuals are 0.3-0.6)
# --d2-streams=steric (or =gsic) runs ONE stream's discrepancy term. Default is
# both = the shipped L11 configuration, unchanged. This exists for the 2026-08-16
# attribution question: L10 -> L11 moved thermal_alpha +1.31 L10 sd (mix ratio
# 19.7) and no chain in the repo separates a steric-basis coupling from a gsic
# one, because D2chk/D2chk2/D2chk3 all carry both. Restricting the list drops the
# other stream's coefficients from FREE and from D2_IDX, and `d2()` is already
# keyed on haskey(D2_IDX, st), so the other stream reverts to no-discrepancy
# exactly.
const D2_STREAMS  = let a = _argval("--d2-streams=")
    a === nothing ? ["gsic", "steric"] : split(a, ",")
end
issubset(D2_STREAMS, ["gsic", "steric"]) ||
    error("--d2-streams= takes gsic and/or steric, got $(D2_STREAMS)")

"""Orthonormal (unit-RMS) discrepancy basis for one stream: shifted Legendre-like
powers of scaled time, Gram-Schmidt'd against `protect` and against each other,
then RMS-normalised. Returns an (nyear x D2_BASIS_N) matrix."""
function d2_basis(years, protect::Vector{Vector{Float64}}, wt::Vector{Float64})
    n = length(years)
    # PLAIN inner product, and that is a MEASURED choice, not an oversight.
    # Weighting by the likelihood's own 1/eps^2 was tried and is WORSE overall:
    # measured on 100k post-burn draws it moved corr(d2_steric_1, thermal_alpha)
    # from +0.349 to -0.297 (no real gain) while pushing
    # corr(d2_gsic_1, gic_delta) from +0.161 to +0.787 (much worse). The reason is
    # that the posterior metric is neither the plain nor the diagonal one — it is
    # the full AR(1)-correlated heteroskedastic precision plus prior curvature —
    # so chasing posterior correlation by changing the design metric is whack-a-
    # mole. The basis is instead orthogonalised on PHYSICAL grounds: against the
    # driver shape it must not duplicate. `wt` is accepted and ignored so the call
    # sites document which weights were tested.
    ip = (u, v) -> dot(u, v)
    x = 2 .* (Float64.(years) .- minimum(years)) ./ (maximum(years) - minimum(years)) .- 1
    cols = Vector{Vector{Float64}}()
    # ORTHOGONALISE THE PROTECT SET AGAINST ITSELF FIRST. Projecting out `ones`
    # and then a non-orthogonal DELTA_RAMP re-introduces a constant component —
    # the load-time assertion below caught exactly that (mean 0.605 on gsic col 1).
    base = Vector{Vector{Float64}}()
    for u0 in protect
        u = copy(u0)
        for w in base
            d = ip(w, w); d > 1e-12 && (u = u .- (ip(u, w) / d) .* w)
        end
        norm(u) > 1e-10 && push!(base, u)
    end
    for k in 1:(D2_BASIS_N + length(protect) + 2)
        length(cols) == D2_BASIS_N && break
        v = x .^ k
        for u in base                                   # Gram-Schmidt, weighted
            d = ip(u, u)
            d > 1e-12 && (v = v .- (ip(v, u) / d) .* u)
        end
        rms = sqrt(sum(v .^ 2) / n)
        rms < 1e-8 && continue                          # numerically dependent, skip
        v = v ./ rms
        push!(cols, v); push!(base, v)
    end
    length(cols) == D2_BASIS_N ||
        error("d2_basis: only $(length(cols)) of $D2_BASIS_N independent columns")
    return hcat(cols...)
end

# S(t) at the steric fit years, up to an additive constant: te_sea_level
# accumulates Delta_oceanheat, so the cumulative sum telescopes to OHC(t)-OHC(1).
const TE_SHAPE = Float64.(ohc)[S.steric.myi]
const D2_BASIS = Dict(
    "gsic"   => d2_basis(S.gsic.years, [ones(length(S.gsic.years)), copy(DELTA_RAMP)],
                         1.0 ./ S.gsic.ϵ .^ 2),
    "steric" => d2_basis(S.steric.years, [ones(length(S.steric.years)), copy(TE_SHAPE)],
                         1.0 ./ S.steric.ϵ .^ 2))
# The 1/eps^2 weights, kept only so the d2_basis call sites document which metric
# was tested and rejected (see the ip comment in d2_basis).
const D2_WT = Dict("gsic" => 1.0 ./ S.gsic.ϵ .^ 2, "steric" => 1.0 ./ S.steric.ϵ .^ 2)

# The orthogonality IS the design — a basis that quietly acquired a constant
# component would silently re-open the thermal_alpha degeneracy and nothing
# downstream would show it. Assert at load, like the amp-law S(anchor)=1 identity.
let tol = 1e-9
    for (st, B) in D2_BASIS, k in 1:D2_BASIS_N
        v = B[:, k]
        abs(sum(v) / length(v)) < tol ||
            error("D2 basis $st col $k has mean $(sum(v)/length(v)) — not mean-zero, " *
                  "so delta(t) could absorb a LEVEL offset and unidentify thermal_alpha")
        abs(sqrt(sum(v .^ 2) / length(v)) - 1) < 1e-8 ||
            error("D2 basis $st col $k is not unit-RMS; the prior sd would not be in cm")
    end
    for k in 1:D2_BASIS_N
        r = dot(D2_BASIS["gsic"][:, k], DELTA_RAMP)
        abs(r) / (norm(D2_BASIS["gsic"][:, k]) * norm(DELTA_RAMP)) < 1e-8 ||
            error("D2 gsic col $k is not orthogonal to DELTA_RAMP (cos = $r) — it " *
                  "would fight gic_delta rather than complement it")
        # The one that actually matters: a steric column with a component along
        # S(t) trades off against thermal_alpha. The first version of this basis
        # failed exactly here (corr -0.724), so it is asserted, not assumed.
        rs = dot(D2_BASIS["steric"][:, k], TE_SHAPE)
        abs(rs) / (norm(D2_BASIS["steric"][:, k]) * norm(TE_SHAPE)) < 1e-8 ||
            error("D2 steric col $k is not orthogonal to the steric shape S(t) " *
                  "(cos = $rs) — it would be degenerate with thermal_alpha")
    end
    if D2_BASIS_N >= 2
        b1 = D2_BASIS["steric"][:, 1]; b2 = D2_BASIS["steric"][:, 2]
        abs(dot(b1, b2)) / (norm(b1) * norm(b2)) < 1e-8 ||
            error("D2 steric columns are not orthogonal")
    end
end

# ---- free physical params (name, comp, sym, prior μ, σ, lo, hi, islog) -- UNCHANGED
pri = CSV.read(joinpath(REPO,"outputs/param_priors.csv"), DataFrame)
prow(n)=pri[findfirst(==(n),pri.param),:]
P(n,c,s;islog=false)=(r=prow(n); (name=n,comp=c,sym=s,μ=r.mean,σ=r.std,lo=r.lo,hi=r.hi,islog=islog))
FREE = NamedTuple[]
push!(FREE, (name="ais_ocean_temperature₀",comp=:antarctic_icesheet,sym=:ais_ocean_temperature₀,μ=0.72,σ=0.50,lo=0.50,hi=2.00,islog=false))
push!(FREE, P("antarctic_alpha",:antarctic_icesheet,:ais_α))
push!(FREE, P("antarctic_nu",:antarctic_icesheet,:ais_ν))
push!(FREE, P("antarctic_temp_threshold",:antarctic_icesheet,:temperature_threshold))
push!(FREE, P("anto_alpha",:antarctic_ocean,:anto_α)); push!(FREE, P("anto_beta",:antarctic_ocean,:anto_β))
if GIS_AB
    # ---- Greenland A+B: 7 sampled params (gis_g fixed at 0, gis_v0 structural) ----
    # UNITS: the component works in m SLE; the offline cell in cm. Centres are the
    # CONVERGED offline A+B fit AT g = 0 (outputs/gis_g_betaf_variants.csv row
    # "g=0"), converted /100 for the two level parameters. Taking them from the
    # g = 0.917 fit instead would be wrong: (c0, g) is a flat manifold and c0
    # moves from 4.04 cm to 61.99 cm along it at identical nlp.
    # BOUNDS are the offline PBOUNDS, converted. PRIORS are deliberately WEAK
    # (sigma several times the centre) so the joint likelihood, not the offline
    # fit, decides — in particular beta_f is left free across its whole range per
    # Marcus's 4.2 ruling, rather than re-bounded to the offline data support.
    #
    # SIGNED OFF by Marcus 2026-08-12, with the caveat ON RECORD: the offline fit
    # was made against the SAME gis target the joint likelihood scores, so these
    # centres re-use data the likelihood already uses. The sigmas are wide enough
    # that the prior contributes little — the 4000-iteration smoke moved alpha_s
    # from 0.0071 to 0.039 and f from 0.78 to 0.89 — so the centres function as a
    # starting point rather than as information. Flat priors (sigma = 1e3, the
    # gic_u_unch pattern) and a 10x-wider variant were both offered and declined.
    # ANY METHODS SECTION MUST SAY SO: "priors centred on an offline fit to the
    # same target, with sigmas wide enough to be effectively uninformative".
    GISC = :greenland_icesheet
    push!(FREE, (name="gis_c1", comp=GISC, sym=:gis_c1,
                 μ=0.032766, σ=0.050, lo=0.0, hi=4.0, islog=false))
    push!(FREE, (name="gis_c0", comp=GISC, sym=:gis_c0,
                 μ=0.040429, σ=0.100, lo=0.0, hi=4.0, islog=false))
    # NB the centre is the offline FITTED f, not MOUG_SHARE. The Mouginot
    # information enters through the likelihood term below; centring the prior on
    # it as well would count the same observation twice. (--gis-check caught this:
    # at mu = 0.735 the model's modern surface share comes out 0.682, not 0.735,
    # because f is the share of the COMMITMENT, not of the modern rate.)
    push!(FREE, (name="gis_f", comp=GISC, sym=:gis_f,
                 μ=0.782569, σ=0.30, lo=0.02, hi=0.98, islog=false))
    push!(FREE, (name="gis_alpha_f", comp=GISC, sym=:gis_alpha_f,
                 μ=0.0028487, σ=0.020, lo=0.0, hi=0.5, islog=false))
    push!(FREE, (name="gis_beta_f", comp=GISC, sym=:gis_beta_f,
                 μ=0.0073684, σ=0.050, lo=1e-6, hi=0.5, islog=false))
    if GIS_REPARAM
        push!(FREE, (name="gis_slow_ell", comp=:likelihood_only, sym=:none,
                     μ=GIS_ELL_MU, σ=GIS_ELL_SD,
                     lo=GIS_ELL_MU - 4*GIS_ELL_SD, hi=GIS_ELL_MU + 4*GIS_ELL_SD,
                     islog=false))
        push!(FREE, (name="gis_slow_w", comp=:likelihood_only, sym=:none,
                     μ=GIS_W_MU, σ=1e3, lo=0.0, hi=1.0, islog=false))
    else
        push!(FREE, (name="gis_alpha_s", comp=GISC, sym=:gis_alpha_s,
                     μ=0.0070727, σ=0.020, lo=0.0, hi=0.2, islog=false))
        push!(FREE, (name="gis_beta_s", comp=GISC, sym=:gis_beta_s,
                     μ=0.0010000, σ=0.020, lo=1e-6, hi=0.2, islog=false))
    end
    # The regional amplification, SAMPLED (Marcus 2026-08-12), not pinned at the
    # prior centre. Same treatment as the glacier blocks' gic_amp_b and the same
    # reasoning as the 4.2 beta_f ruling: the likelihood cannot see it, but it is
    # the DOMINANT control on the 2100 projection -- across its own prior the
    # 2100 scenario spread runs 7.4 (amp 1.51) to 12.6 cm (amp 2.28), which
    # brackets the 6.3-7.3 evaluation band. Pinning it at 1.92 would hide that
    # entire range inside a point value.
    # Likelihood-inert in the same sense the glacier amps are: the driver is
    # built ONCE at GIS_AMP, and the amp-dependent part is the post-2024 splice
    # tail. NB unlike the glaciers this is not exactly zero -- the gis target
    # runs to 2025, so ONE of its 126 years falls in the spliced region. The
    # effect is negligible and it is not modelled; gis_amp is therefore
    # prior-propagated into the projections, not estimated.
    # sd/lo/hi FROM THE PRIOR FILE, keyed on GIS_ZONE — never inline literals.
    push!(FREE, (name="gis_amp", comp=:likelihood_only, sym=:none,
                 μ=GIS_AMP, σ=GIS_AMP_PRIOR.sd,
                 lo=GIS_AMP_PRIOR.lo, hi=GIS_AMP_PRIOR.hi, islog=false))
    if GIS_BASINS
        # The ONE free knob per basin: a multiplicative scale on BOTH of that
        # basin's channel rates. Sampled as log10, the gic_log10_kappa pattern, and
        # for the same reason — it is a positive SCALE spanning a decade (the
        # offline prototype's exactly-identified fit returned 0.562 / 2.513 / 0.216),
        # so a linear proposal would step badly at the small end.
        #
        # PRIOR CENTRED AT s = 1, NOT at the prototype's fitted values, on the same
        # principle as the gis_f comment above: the prototype was fitted to the SAME
        # Mouginot partition the new likelihood term scores, so centring on it would
        # count that observation twice. It was also fitted on the `all` driver while
        # this run is still on `south`. s = 1 is the honest null — "no basin
        # re-scaling", the exact nesting point at which this model IS greenland_ab —
        # and sigma 0.5 in log10 puts the prototype's whole range inside 1 sd.
        for b in GISB_FREE_BASINS
            push!(FREE, (name="gis_s_$b", comp=GISC, sym=Symbol("gis_s_$b"),
                         μ=0.0, σ=0.5, lo=-2.0, hi=2.0, islog=false))
        end
    end
else
    push!(FREE, P("greenland_a",:greenland_icesheet,:greenland_a)); push!(FREE, P("greenland_b",:greenland_icesheet,:greenland_b))
    push!(FREE, P("greenland_alpha",:greenland_icesheet,:greenland_α)); push!(FREE, P("greenland_beta",:greenland_icesheet,:greenland_β))
    push!(FREE, P("greenland_v0",:greenland_icesheet,:greenland_v₀))
end
push!(FREE, P("thermal_alpha",:thermal_expansion,:te_α))
G=:glaciers_small_icecaps
# ---- 2026-08-06 glacier-stock fix (Marcus-approved; memo_2026-08-05 §3) --------------------
# A0 showed the old box closed the flow-unidentified STOCK direction at the wrong point
# (T_lia floor -1.00 binding -> a→0.35, b→0.89, S_eq saturated by ~1.3°C = the spread
# collapse). Changes: (1) bounds widened so no gic bound binds — the new inventory
# LIKELIHOOD (below) closes the stock direction with data instead; (2) gic_T_lia is
# REINTERPRETED as the EFFECTIVE glacier-equilibrium temperature offset, NOT an LIA
# reconstruction (PAGES 2k global LIA is only -0.03..-0.14°C — the LIA label is falsified;
# Mengel 2016 had no such temperature, they subtracted Marzeion-2014 natural melt from the
# data instead, contested by Roe 2021; GlacierMIP3's 39%-committed-at-present is the physics
# this offset encodes). Prior N(-1.0, 0.5) on [-2.0, -0.1] is deliberately weak: the flow
# constraints + inventory term identify it (self-consistent solution ≈ -1.11).
# ---- extB3 (2026-08-07): glaciers_nu — Mengel S_eq + Nauels-ν transient on T_glac ----
# D0 shootout (memo §3e): the GMST driver bought missing regional (ETCW) warming with a
# deep equilibrium offset (committed@1850 = 0.20 m — the pre-1900 leak + spread collapse);
# under the T_glac driver the self-consistent solution is a .383 / b .286 glacier-K /
# T_off −0.96 glacier-K (= −0.60 global-K, inside amplified PAGES-2k LIA minima;
# committed@1850 = 0.092 m). FRAME: all gic_* priors are GLACIER-FRAME. gic_b prior
# re-centered 0.52 → 0.29 = Mengel's published global-frame 0.52 ÷ amp_g 1.8 (leaving
# 0.52 would pull b toward re-saturation). T_off prior N(−1.0, 0.5) already sits at the
# glacier-frame value — unchanged (label renamed from the falsified "T_lia"). The 2-τ
# split (f, τ_fast, τ_slow) is REPLACED by the single-reservoir Nauels transient (κ, ν);
# ν = 0 nests single-τ Mengel exactly (validate_glaciers_nu.jl, 4/4 PASS 2026-08-07).
# κ is sampled as log10(κ) (spans decades; derived-param pattern like amp/T_on).
# ν prior N(1.0, 0.5) on [0, 2.5] is INFORMATIVE BY DESIGN: the hindcast cannot identify
# ν (D0: rails to 0 under the flow likelihood); the value is projection-physics —
# scenario spread sits in the AR6/FACTS family for ν 0.5-2 and dies at ν = 0. Labeled
# as a projection-informed prior per the A3-line discussion (Marcus 2026-08-07).
# ---- extC glacier block (2026-08-09): 3 reservoirs × (a, b, T_off, log10κ) + scope/ledger ----
# a_b: Farinotti priors (build_extc_inputs.py; R19 direct SLE, SLOWP/FAST = Gt-share split).
# b/T_off: bounds-only (σ=10 ≈ flat — the per-block RUNG likelihood constrains them; a
#   Gaussian prior here would double-count the rungs). μ carries the offline 4-rung fit so
#   θ0 starts on the D1d/D1f solution. T_off bounds widened to +1.0 (fitted R19/SLOWP sit
#   at +0.27/+0.23, outside the old (−2.00, −0.10) — the silent -Inf trap).
# log10κ: τ50-as-prior, centered on the anchored solve, σ=0.114 (±30% at 1σ — the
#   ANCH-vs-MID freedom the offline cells measured). ν_b: FIXED at the anchored value
#   (MID design; the hindcast cannot identify ν — D1/D1c FREE arms rail it to ~0).
# Scope/ledger params are gic_*-named so θ0 uses the prior-mean branch; they are
#   comp=:likelihood_only (never setp!'d — they exist only in likelihood terms):
#   gic_u_unch — F_unch U (mm scope, flat[14.5,41.8] via σ=1e3); gic_delta — M15 bias
#   (mm/yr, N(0,0.30), 1900-1960); gic_u_pre + gic_s_r5 — the Option-D ledger
#   (memo_2026-08-09_d_ledger_target_spec.md).
for b in BLOCKS
    r = bcrow(b)
    a_lo = max(1.5*Float64(r.S2020_data), Float64(r.a0) - 3.5*Float64(r.a0_sig), 0.01)
    push!(FREE, (name="gic_a_$b", comp=G, sym=Symbol("gic_a_$b"),
                 μ=Float64(r.a0), σ=Float64(r.a0_sig), lo=a_lo,
                 hi=Float64(r.a0) + 4.0*Float64(r.a0_sig), islog=false))
    push!(FREE, (name="gic_b_$b", comp=G, sym=Symbol("gic_b_$b"),
                 μ=Float64(r["b_fit_$(FIT_BASIS)"]), σ=10.0, lo=0.05, hi=3.0, islog=false))
    push!(FREE, (name="gic_T_off_$b", comp=G, sym=Symbol("gic_T_off_$b"),
                 μ=Float64(r["T_off_fit_$(FIT_BASIS)"]), σ=10.0, lo=-3.0, hi=1.0, islog=false))
    # κ bounds: sampled mode spans the anchor-center range over the amp prior bounds ±1
    klo, khi = if SAMPLED_AMP
        c1 = k10c(b, AMP_PRIOR[b][3]); c2 = k10c(b, AMP_PRIOR[b][4])
        (min(c1, c2) - 1.0, max(c1, c2) + 1.0)
    else
        (log10(KAP_ANCH[b]) - 1.0, log10(KAP_ANCH[b]) + 1.0)
    end
    push!(FREE, (name="gic_log10_kappa_$b", comp=G, sym=Symbol("gic_kappa_$b"),
                 μ=log10(KAP_ANCH[b]), σ=K10_SIG, lo=klo, hi=khi, islog=false))
end
if SAMPLED_AMP
    for b in BLOCKS
        μa, σa, loa, hia = AMP_PRIOR[b]
        push!(FREE, (name="gic_amp_$b", comp=:likelihood_only, sym=:none,
                     μ=μa, σ=σa, lo=loa, hi=hia, islog=false))
    end
end
push!(FREE, (name="gic_u_unch", comp=:likelihood_only, sym=:none,
             μ=28.15, σ=1.0e3, lo=14.5, hi=41.8, islog=false))
push!(FREE, (name="gic_delta", comp=:likelihood_only, sym=:none,
             μ=0.0, σ=0.30, lo=-1.2, hi=1.2, islog=false))
push!(FREE, (name="gic_u_pre", comp=:likelihood_only, sym=:none,
             μ=12.5, σ=1.0e3, lo=0.0, hi=25.0, islog=false))
push!(FREE, (name="gic_s_r5", comp=:likelihood_only, sym=:none,
             μ=2.5, σ=2.0, lo=0.0, hi=8.0, islog=false))
# name-based derived/likelihood-only index sets (the positional KAPPA_IDX trap is gone)
const KAPPA_IDX3 = Dict(b => findfirst(k -> k.name == "gic_log10_kappa_$b", FREE) for b in BLOCKS)
const A_IDX3     = Dict(b => findfirst(k -> k.name == "gic_a_$b", FREE) for b in BLOCKS)
const B_IDX3     = Dict(b => findfirst(k -> k.name == "gic_b_$b", FREE) for b in BLOCKS)
const TOFF_IDX3  = Dict(b => findfirst(k -> k.name == "gic_T_off_$b", FREE) for b in BLOCKS)
const UUNCH_IDX  = findfirst(k -> k.name == "gic_u_unch", FREE)
if D2_ON
    for st in D2_STREAMS, k in 1:D2_BASIS_N
        push!(FREE, (name="d2_$(st)_$(k)", comp=:likelihood_only, sym=:none,
                     μ=0.0, σ=D2_BASIS_SD, lo=-5*D2_BASIS_SD, hi=5*D2_BASIS_SD,
                     islog=false))
    end
end
const D2_IDX = D2_ON ?
    Dict(st => [findfirst(k -> k.name == "d2_$(st)_$(i)", FREE) for i in 1:D2_BASIS_N]
         for st in D2_STREAMS) : Dict{String,Vector{Int}}()
const GIS_ELL_IDX = GIS_REPARAM ? findfirst(k -> k.name == "gis_slow_ell", FREE) : nothing
const GIS_W_IDX   = GIS_REPARAM ? findfirst(k -> k.name == "gis_slow_w", FREE) : nothing
const GIS_ALPHA_F_IDX = findfirst(k -> k.name == "gis_alpha_f", FREE)
const GIS_BETA_F_IDX  = findfirst(k -> k.name == "gis_beta_f", FREE)
## ---------------------------------------------------------------------------
## CHANNEL ORDERING (--gis-ordered), Marcus 2026-08-17.
##
## The A+B channels are NAMED fast (surface mass balance) and slow (dynamic
## discharge), but nothing in the 126-yr hindcast assigns those labels: the two
## enter L_total symmetrically, so swapping them leaves the residual
## BIT-IDENTICAL (diag_gis_channel_inversion.py, T1). The labels are carried
## entirely by the Mouginot prior, which pins the SMB share of the modern loss
## RATE at 0.735 -- and a share cannot pin a sensitivity (T2). The result is
## that in ~32% of L11 draws the channel Mouginot names SMB is also the one
## with the LONGER timescale, which contradicts what SMB is: it tracks
## temperature near-instantaneously while discharge carries the century memory.
##
## Relabelling cannot fix that, because swapping the channels also swaps the
## share and so breaks Mouginot (T1 measured the swap at 44.20 nlp, all of it
## the Mouginot term). The two constraints pick out DIFFERENT channels, so the
## ordering has to be imposed here, jointly, where the sampler can find the
## region in which both hold.
##
## In the SAMPLED (ell, w) coordinates the constraint is a WEDGE, not a box:
##     alpha_s = w*exp(ell)/TBAR <= alpha_f   AND   beta_s = (1-w)*exp(ell) <= beta_f
## Both bounds are joint in (ell, w) AND coupled to alpha_f/beta_f, so this
## CANNOT be expressed by moving any parameter's lo/hi -- it needs the -Inf
## region below. Priced offline at +0.067 nlp with the hindcast RMSE IMPROVING
## 0.0617 -> 0.0604 (handoff 2026-08-16 thread-5 section 5, T3); measured on the
## L11 posterior to move total SLR by <=0.85 cm @2100 and <=3.44 cm @2300
## (diag_gis_ordering_projection_cost.py).
##
## OFF by default: L11 and every earlier vintage must stay bit-reproducible.
const GIS_ORDERED = "--gis-ordered" in ARGS
if GIS_ORDERED && !GIS_REPARAM
    error("--gis-ordered needs the (ell, w) reparameterisation; the " *
          "native-coordinate branch would need its own wedge.")
end
const DELTA_IDX  = findfirst(k -> k.name == "gic_delta", FREE)
const UPRE_IDX   = findfirst(k -> k.name == "gic_u_pre", FREE)
const SR5_IDX    = findfirst(k -> k.name == "gic_s_r5", FREE)
const AMPB_IDX3  = SAMPLED_AMP ?
    Dict(b => findfirst(k -> k.name == "gic_amp_$b", FREE) for b in BLOCKS) :
    Dict{String,Int}()
const GISAMP_IDX = findfirst(k -> k.name == "gis_amp", FREE)   # nothing when --stock-gis
# the three basin rate scales, sampled as log10 -- the component gets 10^θ, so they
# are DERIVED in the same sense gic_kappa is and must be skipped by the setp! loop.
const GISB_IDX3 = GIS_BASINS ?
    Dict(b => findfirst(k -> k.name == "gis_s_$b", FREE) for b in GISB_FREE_BASINS) :
    Dict{Symbol,Int}()
const SETP_SKIP  = Set(vcat(collect(values(KAPPA_IDX3)),
                            [UUNCH_IDX, DELTA_IDX, UPRE_IDX, SR5_IDX],
                            collect(values(AMPB_IDX3)),
                            # D2's delta(t) coefficients are likelihood_only: they
                            # correct the MODEL SERIES, not a Mimi parameter, so
                            # setp! must skip them or update_param! sees :none.
                            reduce(vcat, values(D2_IDX); init=Int[]),
                            # (ell, w) are DERIVED: they set gis_alpha_s/gis_beta_s
                            # in logposterior, they are not Mimi parameters.
                            GIS_REPARAM ? [GIS_ELL_IDX, GIS_W_IDX] : Int[],
                            GISAMP_IDX === nothing ? Int[] : [GISAMP_IDX],
                            collect(values(GISB_IDX3))))
# sampled mode: the κ prior is amp-dependent (center k10c(amp)) — exclude κ from the
# generic Normal(μ,σ) prior loop and add the explicit term in logposterior
const PRIOR_SKIP = SAMPLED_AMP ? Set(values(KAPPA_IDX3)) : Set{Int}()
# per-block rung likelihood data (data-basis committed %, band σ, cross-rung corr 0.6)
const GMIP_LEVELS = [1.2, 1.5, 2.0, 3.0]
const RUNG_CORR = 0.6
# Rung sigma. The stored sig* columns are HALF THE FULL INTER-MODEL RANGE of the
# 8 GlacierMIP3 models, treated as 1 sigma (d1d_fourrung_seam.py:
# rung_sig = (hi - lo)/2). For n normal draws the expected range is d2(n) sigma,
# and d2(8) = 2.847 — the standard order-statistic constant — so half-range
# OVERSTATES sigma by 2.847/2 = 1.42x. Dividing the range by d2 instead of by 2
# is the tightening: principled from order statistics, not chosen to get a
# result. --rung-sig-legacy restores the half-range convention.
const RUNG_D2_N8 = 2.847
const RUNG_SIG_SCALE = RUNG_SIG_LEGACY ? 1.0 : 2.0 / RUNG_D2_N8
const RUNG_Y  = Dict(b => [Float64(bcrow(b)["com$(replace(string(L), "." => "p"))"])
                           for L in GMIP_LEVELS] for b in BLOCKS)
const RUNG_CI = Dict(b => begin
        sig = RUNG_SIG_SCALE .*
              [Float64(bcrow(b)["sig$(replace(string(L), "." => "p"))"]) for L in GMIP_LEVELS]
        C = (sig * sig') .* (RUNG_CORR .+ (1 - RUNG_CORR) .* Matrix(1.0I, 4, 4))
        inv(C)
    end for b in BLOCKS)
# F_unch taper profile per mm of U (offline unch_cum, d1d: const 1901-1970, linear→0 by 2005)
const FUNCH_UNIT = let flat = 1970 - 1901, ramp = 2005 - 1970
    r = (1.0/1000.0) / (flat + ramp/2)
    [y <= 1901 ? 0.0 :
     y <= 1970 ? r*(y - 1901) :
     y <= 2005 ? r*flat + r*(y - 1970)*(1 - (y - 1970)/(2.0*ramp)) :
                 r*(flat + ramp/2.0) for y in years]
end
const GLAMBIE_I0, GLAMBIE_I1 = idx(2000), idx(2024)   # per-block modern-rate window
const GLAMBIE_SPAN = 2024 - 2000

# ---- GlaMBIE as a PARTITION constraint (2026-08-14, spec_2026-08-14 §8.3) ------------------
# WAS: two independent Normal terms on the ABSOLUTE 2000-2024 rate of gsic_slowp and
# gsic_fast. That constrained the modern AGGREGATE rate a second time — the gsic component
# channel already scores their sum annually over 1900-2023, with grip σ 0.0587 mm/yr against
# GlaMBIE's implied 0.0476 — while the information only GlaMBIE has is the SLOWP/FAST SPLIT,
# which the aggregate channel is blind to.
#
# AND the absolute-rate σ could not be trusted at that tightness. `glambie_block_stats` in
# python/ladrillo_data.py sums the per-region-per-year `combined_gt_errors` in QUADRATURE,
# i.e. assumes GlaMBIE's annual errors are serially independent. They share methodology and
# are not: allowing full within-region serial correlation inflates σ_SLOWP ×4.72 and σ_FAST
# ×4.80, against √24 = 4.90 — the whole ratio is the quadrature assumption.
# GLAMBIE_ERR_INFLATE = 1.5 covers about a third of it. (This also RETIRES the apparent
# 2.59σ GlaMBIE-vs-Frederikse conflict: it is 0.54σ once the errors are allowed to correlate,
# so there is no target conflict to resolve — only a σ that was too tight.)
#
# The SHARE is the right quantity for both reasons at once: it is what the aggregate channel
# cannot see, and it is the combination in which the correlated common-mode error CANCELS, so
# it does not inherit the σ that could not be trusted. Same construction as the Mouginot
# surface-share term below, including the vanishing-denominator guard.
const R19_RATE_MU = GLAMBIE_RATE["R19"]      # 0.049251 mm SLE/yr over 2000-2024
const R19_RATE_SD = 0.11615                  # serially-correlated sigma; see the term
const GLAMBIE_FAST_SHARE = GLAMBIE_RATE["FAST"] /
                           (GLAMBIE_RATE["SLOWP"] + GLAMBIE_RATE["FAST"])
# σ on the share, propagated from the per-block σ. BRACKET (see the spec): 0.0296 with the
# as-coded independent σ and ρ_block = 0; 0.0493 with serially-correlated σ and ρ_block = 0.9.
# Those are the two INTERNALLY CONSISTENT corners — errors correlated in time are correlated
# in space too — and 0.05 is the conservative end of that pair. The (correlated-in-time,
# ρ_block = 0) corner gives 0.14 but is not self-consistent, so it is not used.
# ‼ METHODOLOGICAL CHOICE — flagged for Marcus, not settled.
const GLAMBIE_SHARE_SD  = 0.05
const GLAMBIE_TOT_FLOOR = 1e-9        # a vanishing modern rate makes the share undefined
# Restores the pre-2026-08-14 two-absolute-term form, so the shipped L10 likelihood stays
# exactly reproducible (same purpose as --no-closure-sigma).
const GLAMBIE_ABS = "--glambie-absolute" in ARGS
@printf("GlaMBIE term: %s | FAST share of (SLOWP+FAST) %.4f ± %.4f | blocks %s, %d-%d\n",
        GLAMBIE_ABS ? "ABSOLUTE rates (pre-2026-08-14, --glambie-absolute)" : "PARTITION (default)",
        GLAMBIE_FAST_SHARE, GLAMBIE_SHARE_SD, join(HIND_BLOCKS, "+"), 2000, 2024)

# ---- phase-2 A2: free the DAIS fast-dynamics params under their EXISTING paleo marginals
# (outputs/param_priors.csv rows, from the DAISfastdyn ensemble). Previously FIXED at the
# medoid, which is biased in the pulse-amplifying direction (λ 0.0137 vs paleo mean 0.0104)
# and hides that λ -- the dominant lever on the 100/150-yr pulse -- carried ZERO reported
# uncertainty. They are observationally unidentified over the historical window (T_ant never
# crosses temperature_threshold), so their marginals will simply sample the prior. That is
# the point: propagate real fast-dynamics uncertainty. temperature_threshold was ALREADY free.
push!(FREE, P("antarctic_lambda",:antarctic_icesheet,:λ))
push!(FREE, P("antarctic_gamma",:antarctic_icesheet,:ais_γ))
push!(FREE, P("antarctic_kappa",:antarctic_icesheet,:ais_κ))

# ---- phase-2 A6: GMST->Antarctic temperature map as a sampled amplification ----
# The component computes T_ant = (GMST - intercept)/coef, i.e. amp = 1/coef with anchor
# T_ant(GMST=0) = -intercept/coef = -18.435 on the DAIS paleo scale. The hard-coded map
# (coef 0.8365, intercept 15.42 -> amp 1.196) is the inverted paleo/equilibrium regression.
# `amp` is sampled with the ANCHOR PRESERVED (coef = 1/amp, intercept = -T_ant0/amp), so only
# the anomaly scaling changes; threshold-crossing GMST = (threshold - T_ant0)/amp.
#
# ⚠⚠ RE-CENTRED 0.95 -> 1.09 ON 2026-08-25 (Marcus). THE OLD CENTRE CAME FROM THE WRONG
# STATISTIC. It was Xie et al. 2022's PAI1, a sliding-window TREND ratio. BRICK's `amp`
# multiplies a LEVEL anomaly, so the BRICK-relevant quantity is the SECANT ratio
# [T_AIS(t) - T_AIS,PI] / [T_glob(t) - T_glob,PI]. `diag_pai_cmip6_time.py` was switched to
# the secant on 2026-08-24 (`a79d532`) in the same pass that repaired seven corrupt reduction
# files (`9de38bf`: an xarray `.weighted()` inner join on float-noise latitudes had silently
# cut MPI-ESM1-2-LR to 56 of 96 latitudes, and the AIS numerator inherited it). The two
# statistics behave OPPOSITELY with warming, so this is a sign-level correction, not a tweak.
#
# THE CORRECTED MEASUREMENT (`python/scope_ais_amp_law_form.py`, dT >= 1.0 K, land-frame):
#   34-model SSP secant, model-median  1.095  (between-model sd 0.180)
#   41-model DECK 1pctCO2 secant       1.097  (range 1.087-1.153)  <- INDEPENDENT ensemble
# Two ensembles, different experiments, agreeing on ~1.09. Adopted: 1.09.
#
# ⚠ AND amp IS A CONSTANT, NOT amp(dT) -- MEASURED, after a proposal to make it
# state-dependent. Per-model slopes of the secant on dT: ssp245 -0.0065/K (z=-0.59),
# ssp585 +0.0091/K (z=+1.43). NEITHER RESOLVES, THEY DISAGREE IN SIGN, and each is worth
# 0.02-0.03 in amp over the 1-4 K projection range against a between-model sd of 0.180 --
# 6-9x smaller than the spread. A state-dependent law would encode a trend the data do not
# have. Do not rebuild it without re-running that test.
#
# σ SIGN-OFF ITEM (Marcus), RE-AFFIRMED 2026-08-25 AT 0.10. The corrected data now DOES give
# an inter-model sd (0.180), and it was deliberately NOT adopted: the centre is the one
# moving part of this recalibration, so the delta stays attributable, and between-model
# spread is the term the standing constraint puts out of scope. 0.10 still spans 0.79-1.39
# at +-2σ, covering both ensembles' p17-p83 (0.934-1.348).
# Production: N(1.09, 0.10). --amp-equilibrium: pin at 1.19546 (the old hard-coded map).
const AMP_MU    = AMP_MU_OVR    !== nothing ? parse(Float64, AMP_MU_OVR)    : (AMP_EQ ? 1.0/0.8365 : 1.09)
const AMP_SIGMA = AMP_SIGMA_OVR !== nothing ? parse(Float64, AMP_SIGMA_OVR) : (AMP_EQ ? 0.002 : 0.10)
# Bounds are μ±3σ so the prior is NEVER truncated. ⚠ THIS REPLACES THE HARD-CODED (0.70,
# 1.25), which was built around μ = 0.95 and would clip the new prior at +1.6σ -- a
# mechanical consequence of moving the centre, not a separate choice. The override branch
# already used μ±3σ for exactly this reason; the default now shares it.
const AMP_LO = AMP_MU - 3*AMP_SIGMA
const AMP_HI = AMP_MU + 3*AMP_SIGMA
const AIS_TANT0 = -15.42 / 0.8365              # = -18.435, the preserved anchor
push!(FREE, (name="ais_gmst_amp",comp=:antarctic_icesheet,sym=:ais_temperature_coefficient,
             μ=AMP_MU,σ=AMP_SIGMA,lo=AMP_LO,hi=AMP_HI,islog=false))
@printf("A6 prior: amp ~ N(%.3f, %.3f) on [%.3f, %.3f]   TAG=%s\n",
        AMP_MU, AMP_SIGMA, AMP_LO, AMP_HI, TAG)
const AMP_IDX = length(FREE)                   # DERIVED param: sym above is never set directly

# ---- v-next Strategy B: FREE the 7 DAIS geometry params under a JOINT paleo prior ----
# These were previously FIXED at the prior medoid, which discards both their spread and
# the paleo correlation structure among them. Freed here with a joint prior built from the
# DAISfastdyn paleo ensemble (MimiBRICK.jl/calibration/compute_paleo_geo_prior.jl).
# STANDARDIZED form: prior = MvNormal(0, C) on z = (θ - μ)/sd. The correlation C is well
# conditioned (cond 2.75) where the raw covariance is not (cond 5.2e13 -- scales span
# 1e-4..1e3), so this keeps the paleo correlation without the ill-conditioning.
# Bounds = paleo ensemble min/max.
# ais_precipitation₀ is sampled in LOG space: MimiBRICK v2.0.0's AIS component computes
# exp(ais_precipitation₀) (package default log(0.37)), so islog=false passes the log-space
# θ straight through -- do NOT set islog=true here, that would log it twice.
# phase-2 A4: the runoff line is sampled in its IDENTIFIED direction. h0 and c enter the
# model ONLY as hR = h0 + c*T_ant, so the posterior pins T_on = -h0/c (runoff onset, deg C
# on the DAIS Antarctic-surface scale) while (h0,c) individually ride a r=0.9997 ridge.
# The joint paleo prior is REBUILT in (T_on, c) coordinates from the same DAISfastdyn
# ensemble (MimiBRICK.jl/calibration/compute_paleo_geo_prior_ton.jl): T_on paleo marginal
# -15.64 ± 5.54 [-43.3, -5.2] == runoff onset at GMST ~+2.3 C under the default map,
# consistent with Shaffer's DAIS (+2.5 C); r(T_on,c) in the prior is +0.64, not 0.9997.
# h0 = -T_on*c is reconstructed per draw in logposterior (the T_on row's sym is a
# placeholder, never set directly).
const GEO_FILE  = joinpath(REPO, "outputs/paleo_geo_prior_ton.csv")
const GEO_NAMES = ["ais_mu","ais_bedheight0","ais_slope","ais_iceflow0","ais_precip0_LOG","ais_runoff_Ton","ais_c"]
const GEO_SYMS  = [:ais_μ, :ais_bedheight₀, :ais_slope, :ais_iceflow₀,
                   :ais_precipitation₀, :ais_runoffline_snowheight₀, :ais_c]
_gl = [split(strip(l), ',') for l in readlines(GEO_FILE) if !startswith(l,"#") && !isempty(strip(l))]
_grow(tag) = [parse(Float64, x) for x in first(l for l in _gl if l[1] == tag)[2:end]]
const GEO_MU = _grow("mean")
const GEO_SD = _grow("sd")
const GEO_C  = Symmetric(permutedims(reduce(hcat,
    [[parse(Float64,x) for x in l[2:end]] for l in _gl if l[1] == "corr"])))
let glo = _grow("lo"), ghi = _grow("hi")
    for i in eachindex(GEO_SYMS)
        push!(FREE, (name=GEO_NAMES[i], comp=:antarctic_icesheet, sym=GEO_SYMS[i],
                     μ=GEO_MU[i], σ=GEO_SD[i], lo=glo[i], hi=ghi[i], islog=false))
    end
end
const GEO_IDX   = (length(FREE)-length(GEO_SYMS)+1):length(FREE)
const GEO_PRIOR = MvNormal(zeros(length(GEO_SYMS)), Matrix(GEO_C))
const TON_IDX   = GEO_IDX[findfirst(==("ais_runoff_Ton"), GEO_NAMES)]   # derived: h0 = -T_on*c
const C_IDX     = GEO_IDX[findfirst(==("ais_c"), GEO_NAMES)]

# ---- phase-2 A5: SMB likelihood term on the model's own β_total vs Rignot 2019 ----------
# The posterior pinned SMB - discharge to -145±15 Gt/yr (34:1 tighter than either flux)
# while SMB and discharge were individually ±505/±509 -- the textbook input-output
# degeneracy, exactly where ais_iceflow0 (worst mixer, true ESS ~24) lives. One Gaussian
# term anchors the absolute flux scale. AREA CONVENTION (handled explicitly, else ±15%
# bias into ais_precip0 and the pulse): Rignot 2019 grounded-AIS SMB 2098±133 Gt/yr is for
# 12.295e6 km2; DAIS is an idealized pi*R0^2 = 10.92e6 km2 disc -> x(10.92/12.295)=0.888.
# σ SIGN-OFF ITEM (Marcus): 118 = Rignot's ±133 area-scaled (inter-model spread, not
# measurement error); Mottram 2021 (TC 15:3751) 5-RCM ensemble = 2329±94 Gt/yr INCLUDING
# shelves (~2000 grounded, consistent with Rignot). β_total is m3 ice/yr -> Gt/yr via
# ρ_ice; window 1979-2008 matches the Rignot climatology.
const SMB_Y0, SMB_Y1 = 1979, 2008
const SMB_IDX       = [idx(y) for y in SMB_Y0:SMB_Y1]
const SMB_TARGET_GT = 2098.0 * (10.92 / 12.295)          # = 1863.4 Gt/yr
const SMB_SIGMA_GT  = 133.0 * (10.92 / 12.295)           # = 118.1 Gt/yr
const M3ICE_TO_GT   = 917.0 / 1e12                       # ais_ρ_ice = 917 kg/m3

# ---- 2026-08-06 A2: glacier INVENTORY likelihood -- gic_a − S_raw(2000) ~ N(V, σ) ----------
# The flow target fixes only slope@0 and committed melt; total meltable stock gic_a is
# invisible to flow data (unmelted ice leaves no trace). This term closes that direction with
# the present-day inventory. SCOPE (matches the GSIC target, prep_recalib_targets_ext.py):
# RGI regions 1-18 minus 5 (r5 lives in the GIS target) PLUS 19 (deliberate zero everywhere
# else in the chain): V = 0.221±0.057 (Farinotti 2019 excl 5+19, Hock 2023 tables)
# + 0.069±0.018 (r19) = 0.290, σ = 0.060 (quadrature). S_raw = un-rereferenced cumulative
# melt since 1850 (valid because gic_sl0 = 0). Self-consistency predicts the posterior lands
# near (a 0.452, b 0.529, T_lia -1.106) = Mengel's published 0.47/0.52 — the A5 success check.
const INV_V_M      = 0.290
const INV_SIGMA_M  = 0.060
# Checkpoint at the MEASUREMENT epoch: Farinotti's volume refers to RGI ~2000 outlines
# (2026-08-06 fix; was 2020, a ~0.014 m / 0.2σ epoch error). Millan 2022 (~2018, matched
# scope 0.223±0.073) agrees to 1% — cross-check only, NOT a second term (same RGI basis).
const INV_YEAR_IDX = idx(2000)
# extC: the stock is the SUM of the three reservoir a_b (A_IDX3); melt is the all-block sum
@printf("A2 inventory: sum(a_b) - S_all(2000) ~ N(%.3f, %.3f) m SLE  (scope: RGI 1-18 minus 5, plus 19)\n",
        INV_V_M, INV_SIGMA_M)

# ---- 2026-08-06 A2b: 19th-CENTURY flow constraint -- S(1900) − S(1850) ~ N(µ, σ) ----------
# The extB1 tuning run FALSIFIED A2-alone: the re-referenced flow target starts in 1900, so
# pre-1900 melt is unobserved, and the sampler drained 13.1 cm of stock over 1850-1900
# (2.6 mm/yr GMSL — absurd vs any 19th-c budget) to buy a sharper 1900+ fit while violating
# the inventory (memo_2026-08-05 §3b; Marcus approved remedy 1, 2026-08-06). This term closes
# that third soft direction with length-based 19th-c reconstruction data (Leclercq-type).
# VALUES (receipts 2026-08-06): Leclercq/Oerlemans/Cogley 2011 (SurvGeophys 32:519, DOI
# 10.1007/s10712-011-9121-7) series gives 1850-1900 = 18.5 mm SLE (excl r19, incl r5; from
# the Marzeion-2015 supplement data); their 2015 update = 28.0 mm; published scope (×1.18
# ANT upscale) ≈ 21.8; Oerlemans 2007 (differenced) ≈ 10 mm. STRUCTURAL spread (10-28 mm,
# calibration-dataset-driven) >> any formal σ (~3-5 mm), and the scope deltas vs our
# convention (drop r5, add r19) are a few mm with offsetting signs. µ=20, σ=9 mm spans all
# four within ~1.2σ. Kills the extB1 fiction decisively: 131 mm → z≈12 (~-76 logL).
#
# ---- 2026-08-09 OPTION-D LEDGER (Marcus-approved) — TODO(extC surgery): wire this in ----
# The offline cells (d1e_dside_ledger.py) replaced the bare comparison with a MODEL-SIDE
# ledger; the datum stays N(20, 9) mm (basis: excl r19, incl r5). extC must implement:
#   S_ledger(1900) = S_nonr19(1900)            (SLOWP+FAST melt 1850->1900; NOT the R19 res.)
#                  + S_r5   ~ N(2.5, 2.0) mm, bounds [0, 8]   (charted r5 set-aside, +1 param)
#                  + U_pre  ~ flat [0, 25] mm                 (pre-1901 uncharted set-aside,
#                                                              +1 param; 0-edge = charted-
#                                                              scope reading of Leclercq)
#   ll += logpdf(Normal(0.020, 0.009), S_ledger in m) + logpdf(Normal(2.5, 2.0), S_r5)
# Spec + P&M 2018 primary receipts: notes/memo_2026-08-09_d_ledger_target_spec.md.
# Marginalized 1-term equivalent if params are unwanted: Normal(0.0050, 0.0117) m on
# S_nonr19(1900) — but the explicit 2-param ledger is preferred for reporting.
# IMPLEMENTED (extC surgery, 2026-08-09): the ledger term in logposterior evaluates
# Normal(M19_MU_M, M19_SIGMA_M) on gsic_hind(1900) + (gic_u_pre + gic_s_r5)/1000.
const M19_MU_M    = 0.020
const M19_SIGMA_M = 0.009
const M19_I1850, M19_I1900 = idx(1850), idx(1900)
@printf("A2b 19th-c flow: S(1900) - S(1850) ~ N(%.3f, %.3f) m SLE (Leclercq-family span)\n",
        M19_MU_M, M19_SIGMA_M)

const NP = length(FREE)
# ALL_SERIES is the FIXED five-stream layout every historical chain/covariance was
# written in; the OLD*_NAMES tables below describe those layouts and must NOT
# follow the live SERIES, or --drop-total would silently shorten them and break
# the by-name proposal embedding.
const ALL_SERIES = [:ais,:gsic,:gis,:steric,:dang]
const SERIES = DROP_TOTAL ? [:ais,:gsic,:gis,:steric] : ALL_SERIES
const NN = 2*length(SERIES); const NK = NP + NN
# parameter names in θ order (physical, then AR(1) noise). Defined here because
# --overdisperse needs it before sampling; the post-run summary reuses it.
const pn0 = vcat([k.name for k in FREE], vcat([["sd_$s","rho_$s"] for s in SERIES]...))
println("MCMC: $NP physical (incl $(length(GEO_IDX)) DAIS-geometry under a joint paleo prior) " *
        "+ $NN AR(1)-noise = $NK free params  (point terms DROPPED)")
@printf("R19 change set: total %s | GlaMBIE R19 rate %s (%.4f +/- %.4f mm/yr) | rung sigma x%.3f\n",
        DROP_TOTAL ? "DROPPED" : "kept (--keep-total)",
        R19_RATE_ON ? "ON" : "OFF (--no-r19-rate)",
        R19_RATE_MU, R19_RATE_SD, RUNG_SIG_SCALE)
GIS_REPARAM && println("Greenland slow channel: (log r_s, w) at Tbar = " *
        "$(round(GIS_TBAR, digits=4)) K | ell ~ N($(round(GIS_ELL_MU, digits=4)), " *
        "$GIS_ELL_SD) | w flat on [0,1], centred $(round(GIS_W_MU, digits=4))")
println("Greenland channel ordering: " * (GIS_ORDERED ?
        "IMPOSED (--gis-ordered) -- alpha_s <= alpha_f AND beta_s <= beta_f, a " *
        "WEDGE in (ell, w); the labels are otherwise carried only by Mouginot" :
        "FREE (default) -- channels are exchangeable in the likelihood, so the " *
        "fast/slow labels rest entirely on the Mouginot share prior"))
println("D2 discrepancy: " * (D2_ON ? "ON" : "OFF (--no-d2)") *
        " | $D2_BASIS_N dof per stream on " * join(D2_STREAMS, "+") *
        " | prior sd $D2_BASIS_SD cm | orthogonal to the constant" *
        (D2_ON ? ", to DELTA_RAMP on gsic, and to S(t) on steric" : ""))

# ---- model base (medoid + glacier init), forcing once -- extC 3-reservoir build ----
medoid = CSV.read(joinpath(REPO,"outputs/recalib_central_row.csv"), DataFrame)[1,:]
m = GIS_BASINS ? build_brick_nu3_gis3(ssp="ssp245", y0=Y0, y1=Y1) :
    GIS_AB     ? build_brick_nu3_gis(ssp="ssp245", y0=Y0, y1=Y1) :
                 build_brick_nu3(ssp="ssp245", y0=Y0, y1=Y1)
gic3_init = (; (Symbol(b) => (a=Float64(bcrow(b).a0),
                              b=Float64(bcrow(b)["b_fit_$(FIT_BASIS)"]),
                              T_off=Float64(bcrow(b)["T_off_fit_$(FIT_BASIS)"]),
                              kappa=KAP_ANCH[b], nu=NU_ANCH[b]) for b in BLOCKS)...)
update_brick_nu3!(m, medoid, gic3_init; precip_log=true,   # ν_b FIXED here (anchored; not sampled)
                  skip_greenland=GIS_AB)                   # greenland_ab has no stock-SIMPLE params
set_forcing!(m, gmst, ohc)
set_glacier_forcing3!(m, tg3)         # per-block T_glac; glacier slot never sees raw GMST
if GIS_AB
    set_gis_forcing!(m, tgis)         # REGIONAL driver; the GIS slot never sees raw GMST
    # structural, never sampled: the commitment cap and the 1850 initial condition
    update_param!(m, _GIS_SLOT, :gis_v0, GIS_V0_M)
    # the basin volume shares are FIXED Mouginot geometry, set once and never
    # sampled; the rate scales are overwritten every logposterior call below
    # k = GISB_K, NOT the component's default: under --gis-basins2 that default
    # would silently load the mid basin the flag exists to switch off, and the run
    # would be a 3-basin run wearing a 2-basin label.
    GIS_BASINS && update_gis3_shares!(m; k=GISB_K)
    update_param!(m, _GIS_SLOT, :gis_g, GIS_G)
end
# Indices for the Mouginot partition term. Defined unconditionally so the name is
# always bound; only the GIS_AB branch of the likelihood reads it.
# Per-basin share windows, mirroring MOUG_I. Bound unconditionally so the name
# always exists; only the GISB_TERM branch reads it.
const GISB_I = [(i0=idx(w[1]), i1=idx(w[2]), n=w[2]-w[1]) for w in GISB_WINS]
const MOUG_I = (r0=idx(MOUG_REF_WIN[1]),  r1=idx(MOUG_REF_WIN[2]),
                l0=idx(MOUG_LATE_WIN[1]), l1=idx(MOUG_LATE_WIN[2]))
# --gis-check ONLY. The ordering wedge is a hard rejection evaluated BEFORE run(m),
# which is right for a sampled proposal and WRONG for a fixed reference vector: the
# offline A+B fit that --gis-check compares against predates the ordering convention
# and legitimately has alpha_s (0.00707) > alpha_f (0.00285), so the wedge rejected
# it, run(m) never happened, and the diagnostic read whatever state the PREVIOUS
# logposterior call left in `m` — reporting theta0's numbers as if they were the
# reference vector's. That is how it came to report a Mouginot share of 0.8699
# (theta0's) against the offline 0.7351 and call it a wiring failure. Found
# 2026-08-19; --gis-check has been inert this way for the whole L12 line, since
# --gis-ordered is the canonical configuration. Never set outside the diagnostic.
const WEDGE_OFF = Ref(false)
setp!(k,v)=update_param!(m,k.comp,k.sym, k.islog ? log(v) : v)
reref(v)=100 .* (v .- sum(v[ib])/length(ib))

function logposterior(θ)
    @inbounds for k in 1:NP; (θ[k]<FREE[k].lo || θ[k]>FREE[k].hi) && return -Inf; end
    σn = θ[NP+1:2:NK]; ρn = θ[NP+2:2:NK]
    (any(σn .<= 0) || any(ρn .< 0) || any(ρn .>= 0.99)) && return -Inf
    # the channel-ordering wedge (see GIS_ORDERED above). Evaluated HERE, with
    # the other hard rejections and BEFORE run(m), so a rejected proposal costs
    # no model evaluation.
    if GIS_ORDERED && !WEDGE_OFF[]
        r_s = exp(θ[GIS_ELL_IDX]); w_s = θ[GIS_W_IDX]
        (w_s * r_s / GIS_TBAR > θ[GIS_ALPHA_F_IDX]) && return -Inf   # alpha_s <= alpha_f
        ((1 - w_s) * r_s > θ[GIS_BETA_F_IDX])       && return -Inf   # beta_s  <= beta_f
    end
    @inbounds for k in 1:NP
        (k == AMP_IDX || k == TON_IDX || k in SETP_SKIP) && continue   # derived/likelihood-only
        setp!(FREE[k], θ[k])
    end
    # extC: per-block κ sampled as log10 -- the component gets the linear value
    for b in BLOCKS
        update_param!(m, G, Symbol("gic_kappa_$b"), 10.0^θ[KAPPA_IDX3[b]])
    end
    # basin rate scales: sampled as log10, the component takes the linear value
    if GIS_BASINS
        # the reference basin stays pinned at 1 (set once at build); only the
        # information-carrying ratios are sampled
        for b in GISB_FREE_BASINS
            update_param!(m, _GIS_SLOT, Symbol("gis_s_$b"), 10.0^θ[GISB_IDX3[b]])
        end
    end
    # A4: runoff line -- reconstruct h0 from the identified direction
    update_param!(m, :antarctic_icesheet, :ais_runoffline_snowheight₀, -θ[TON_IDX] * θ[C_IDX])
    if GIS_REPARAM                     # (ell, w) -> the component's native rate pair
        r_s = exp(θ[GIS_ELL_IDX]); w_s = θ[GIS_W_IDX]
        update_param!(m, _GIS_SLOT, :gis_alpha_s, w_s * r_s / GIS_TBAR)
        update_param!(m, _GIS_SLOT, :gis_beta_s, (1 - w_s) * r_s)
    end
    # A6: temperature map -- amp with the T_ant(GMST=0) anchor preserved
    update_param!(m, :antarctic_icesheet, :ais_temperature_coefficient, 1.0 / θ[AMP_IDX])
    update_param!(m, :antarctic_icesheet, :ais_temperature_intercept, -AIS_TANT0 / θ[AMP_IDX])
    run(m)
    # F_unch: the target's uncharted content, held on the model side of every comparison
    # (never in the Mimi graph — the AIS sea-level feedback sees only real reservoir melt)
    Funch = θ[UUNCH_IDX] .* FUNCH_UNIT
    gsic_all_raw  = m[G, :gsic_sea_level]
    gsic_hind_raw = m[G, :gsic_hind]
    ais=reref(m[:antarctic_icesheet,:ais_sea_level])
    gsic_flow = reref(gsic_hind_raw .+ Funch)            # hindcast scope: SLOWP+FAST+F_unch
    gsic_tot  = reref(gsic_all_raw .+ Funch)             # total scope: + R19 (real melt)
    gis=reref(m[:greenland_icesheet,:greenland_sea_level]); te=reref(m[:thermal_expansion,:te_sea_level])
    tot_full = ais .+ gsic_tot .+ gis .+ te              # +LWS added per dang-year below
    ll = 0.0
    # individual components on their own (possibly extended) windows; the gsic obs get the
    # δ ramp (M15 early-segment bias, obs-side, 1900-1959 — offline obs_corrected)
    # D2: delta(t) is added to the MODEL (it is a model-discrepancy term), so the
    # per-year band sigma and the AR(1) noise are untouched — spec section 3
    # sub-choice 2 requires delta to be added to, not to replace, diag(eps^2).
    d2 = (st, v) -> (!D2_ON || !haskey(D2_IDX, st)) ? v :
                    v .+ D2_BASIS[st] * [θ[j] for j in D2_IDX[st]]
    for (i,(s,full)) in enumerate(zip([S.ais,S.gsic,S.gis,S.steric], [ais,gsic_flow,gis,te]))
        if i == 2
            ll += hetero_logl_ar1(d2("gsic", full[s.myi]) .-
                                  (s.obs .+ θ[DELTA_IDX] .* DELTA_RAMP),
                                  σn[i], ρn[i], s.ϵ)
        elseif i == 4
            ll += hetero_logl_ar1(d2("steric", full[s.myi]) .- s.obs,
                                  σn[i], ρn[i], s.ϵ)
        else
            ll += hetero_logl_ar1(full[s.myi] .- s.obs, σn[i], ρn[i], s.ϵ)
        end
    end
    # total: modeled ice+steric at "dang" years + observed LWS. NB the "dang"-labeled
    # target is the FREDERIKSE 2020 total (label fix 2026-07-20) spliced with NOAA STAR
    # altimetry -- rename pending the M3 total-term rework.
    # D1: with --drop-total this term and its noise pair are gone; σn/ρn then have
    # only 4 entries, so the guard is load-bearing, not cosmetic.
    DROP_TOTAL ||
        (ll += hetero_logl_ar1(tot_full[S.dang.myi] .+ lws_dang .- S.dang.obs,
                               σn[5], ρn[5], S.dang.ϵ))
    # A5: SMB anchor -- model β_total (1979-2008 mean, Gt/yr) vs area-scaled Rignot 2019
    smb_gt = mean(m[:antarctic_icesheet, :β_total][SMB_IDX]) * M3ICE_TO_GT
    ll += logpdf(Normal(SMB_TARGET_GT, SMB_SIGMA_GT), smb_gt)
    # A2 glacier inventory: remaining stock = sum(a_b) - all-block cumulative melt since 1850
    ll += logpdf(Normal(INV_V_M, INV_SIGMA_M),
                 sum(θ[A_IDX3[b]] for b in BLOCKS) - Float64(gsic_all_raw[INV_YEAR_IDX]))
    # Option-D ledger (replaces the pre-D A2b): datum N(20,9)mm untouched; model side =
    # S_hind(1900) + U_pre + S_r5 (memo_2026-08-09_d_ledger_target_spec.md)
    S_ledger_m = (Float64(gsic_hind_raw[M19_I1900]) - Float64(gsic_hind_raw[M19_I1850])) +
                 (θ[UPRE_IDX] + θ[SR5_IDX]) / 1000.0
    ll += logpdf(Normal(M19_MU_M, M19_SIGMA_M), S_ledger_m)
    # per-block GlacierMIP3 rung likelihood (data-basis committed %, corr 0.6, band σ);
    # sampled mode: the frame conversion uses the SAMPLED amp
    for b in BLOCKS
        a = θ[A_IDX3[b]]; bb = θ[B_IDX3[b]]; T0 = θ[TOFF_IDX3[b]]
        s20 = S2020_D[b]
        amp = SAMPLED_AMP ? θ[AMPB_IDX3[b]] : AMP_B[b]
        r4 = [100.0*(a*(1 - exp(-bb*(amp*L - T0))) - s20)/max(a - s20, 1e-9) - RUNG_Y[b][i]
              for (i, L) in enumerate(GMIP_LEVELS)]
        ll += -0.5 * (r4' * (RUNG_CI[b] * r4))
    end
    # GlaMBIE (hindcast blocks only, 2000-2024 mean rate). Default: ONE term on the
    # SLOWP/FAST PARTITION, leaving the aggregate modern rate to the gsic component channel
    # that already scores it. --glambie-absolute restores the two absolute-rate terms.
    # See the constant block above for why the share, and not the levels.
    let rs = 1000.0*(Float64(m[G, :gsic_slowp][GLAMBIE_I1]) -
                     Float64(m[G, :gsic_slowp][GLAMBIE_I0])) / GLAMBIE_SPAN,
        rf = 1000.0*(Float64(m[G, :gsic_fast][GLAMBIE_I1]) -
                     Float64(m[G, :gsic_fast][GLAMBIE_I0])) / GLAMBIE_SPAN
        if GLAMBIE_ABS
            ll += logpdf(Normal(GLAMBIE_RATE["SLOWP"], GLAMBIE_SD["SLOWP"]), rs)
            ll += logpdf(Normal(GLAMBIE_RATE["FAST"],  GLAMBIE_SD["FAST"]),  rf)
        else
            tot = rs + rf
            # A vanishing modern rate makes the share undefined; skip the term there rather
            # than dividing through, exactly as the Mouginot share term does.
            if abs(tot) > GLAMBIE_TOT_FLOOR
                ll += logpdf(Normal(GLAMBIE_FAST_SHARE, GLAMBIE_SHARE_SD), rf / tot)
            end
        end
    end
    # GlaMBIE R19 modern rate. R19 is excluded from HIND_BLOCKS (no gsic component
    # term) and from the GlaMBIE SHARE term (which is SLOWP/FAST only), so with the
    # total dropped this is its ONLY sea-level observation. It is weak by
    # construction — region 19 contributes 8 GlaMBIE input datasets with ZERO
    # gravimetry (GRACE cannot separate the Antarctic periphery from the ice
    # sheet) and one DEM-differencing estimate — but it is the only DIRECT
    # measurement of the block, and L10 sits 3x above it.
    # SIGMA: the fully serially-correlated value, NOT the as-coded quadrature.
    # GLAMBIE_SD["R19"] = 0.0361 is quadrature-over-24-years x GLAMBIE_ERR_INFLATE;
    # the restructure established that serial independence understates by ~4.7x,
    # and the 1.5x inflate was a partial compensation for exactly that. Summing
    # the per-year errors instead gives 0.11615, which SUPERSEDES the inflate
    # rather than compounding with it (python/ladrillo_data.py glambie_block_stats).
    if R19_RATE_ON
        r19rate = 1000.0*(Float64(m[G, :gsic_r19][GLAMBIE_I1]) -
                          Float64(m[G, :gsic_r19][GLAMBIE_I0])) / GLAMBIE_SPAN
        ll += logpdf(Normal(R19_RATE_MU, R19_RATE_SD), r19rate)
    end
    # Mouginot 2019 SMB/discharge partition — the constraint that makes the A+B
    # two-channel split identifiable. Ported verbatim from model_surface_share()
    # in python/gis_offline_cell.py: the FAST channel's share of the EXTRA loss
    # RATE of MOUG_LATE_WIN over MOUG_REF_WIN, matched to how the observed 73.5%
    # was computed. Scale-free, so the m-vs-cm unit difference does not enter.
    if GIS_AB
        tot = m[_GIS_SLOT, :greenland_sea_level]; fst = m[_GIS_SLOT, :gis_fast]
        rate(x, i0, i1, n) = (Float64(x[i1]) - Float64(x[i0])) / n
        nref, nlate = MOUG_REF_WIN[2]-MOUG_REF_WIN[1], MOUG_LATE_WIN[2]-MOUG_LATE_WIN[1]
        d_tot  = rate(tot, MOUG_I.l0, MOUG_I.l1, nlate) - rate(tot, MOUG_I.r0, MOUG_I.r1, nref)
        d_fast = rate(fst, MOUG_I.l0, MOUG_I.l1, nlate) - rate(fst, MOUG_I.r0, MOUG_I.r1, nref)
        # A vanishing extra rate makes the share undefined; the offline cell skips
        # the term there rather than dividing through, and so does this.
        if abs(d_tot) > 1e-12
            ll += logpdf(Normal(MOUG_SHARE, MOUG_SHARE_SD), d_fast / d_tot)
        end
    end
    # Mouginot 2019 per-SECTOR partition — the constraint that stops one basin
    # absorbing all of Greenland's loss. Built as a direct analogue of the term
    # above: a SHARES-ONLY, scale-free ratio, so it is orthogonal to the total
    # term (which already spans 1900-2025 and would otherwise be double-counted)
    # and immune to the 1.227x disagreement between Mouginot's sector sum and the
    # calibration target over 1972-2018.
    #
    # LEVEL shares of the MEAN LOSS RATE in two modern windows — NOT the extra
    # rate over a 1972-1990 reference, and NOT the cumulative 1972-2018 split.
    # Both of those divide by a denominator that passes through zero: Greenland
    # was near balance until the mid-1990s. See the constant block for the
    # window scan that establishes it.
    #
    # Only GISB_SCORED is scored; GISB_DEPENDENT (high) follows by sum-to-one.
    # Adding it would make the block rank-deficient by one, not add an observation.
    # Under --gis-basins2 that is ONE term per window, not two — the merged `active`
    # share is the single independent number the two-basin partition has.
    # The sum over GIS3_BASINS below is still right in that mode: k_mid = 0 makes
    # gis_sl_mid identically zero, so it contributes exactly 0.0 to dtot.
    if GISB_TERM
        bsl = (south = m[_GIS_SLOT, :gis_sl_south],
               mid   = m[_GIS_SLOT, :gis_sl_mid],
               high  = m[_GIS_SLOT, :gis_sl_high])
        for (wi, tgt) in zip(GISB_I, GISB_SHARE)
            d = map(b -> (Float64(getproperty(bsl, b)[wi.i1]) -
                          Float64(getproperty(bsl, b)[wi.i0])) / wi.n, GIS3_BASINS)
            dtot = sum(d)
            # A vanishing total rate makes every share undefined; skip rather than
            # divide through, exactly as the two share terms above do.
            if abs(dtot) > GISB_TOT_FLOOR
                for b in GISB_SCORED
                    j = findfirst(==(b), GIS3_BASINS)
                    ll += logpdf(Normal(getproperty(tgt, b), GISB_SHARE_SD), d[j] / dtot)
                end
            end
        end
    end
    # priors: independent Gaussian on physical (EXCEPT the geometry block, which gets the
    # joint paleo prior below), weak half-normal on AR(1) σ
    lp = 0.0
    @inbounds for k in 1:NP
        (k in GEO_IDX || k in PRIOR_SKIP) && continue
        lp += logpdf(Normal(FREE[k].μ, FREE[k].σ), θ[k])
    end
    # sampled mode: τ50-as-prior with the center moving consistently with the sampled amp
    if SAMPLED_AMP
        for b in BLOCKS
            lp += logpdf(Normal(k10c(b, θ[AMPB_IDX3[b]]), K10_SIG), θ[KAPPA_IDX3[b]])
        end
    end
    lp += logpdf(GEO_PRIOR, (θ[GEO_IDX] .- GEO_MU) ./ GEO_SD)
    for i in 1:length(SERIES); lp += logpdf(truncated(Normal(0,5),0,Inf), σn[i]); end
    return ll + lp
end

# ---- start point: MAP physical + noise inits -- UNCHANGED ----
mapp = CSV.read(joinpath(REPO,"outputs/calib_full_joint_params.csv"), DataFrame)
# The geometry params are NOT in calib_full_joint_params.csv (they were fixed, not fitted),
# so they must start at the MEDOID -- the values the rest of the MAP was conditioned on --
# NOT at the paleo prior mean. The medoid precip₀ is 0.94 m/yr vs the paleo mean 0.40 (2.3x)
# and iceflow₀ is -1.4sd off, so starting at the prior mean puts θ0 ~4900 log-units below the
# mode and collapses RAM acceptance to 0.02 (vs 0.19 for the 28-param baseline). This changes
# only the START POINT; the joint paleo prior is unchanged.
const GEO_MEDOID_COL = Dict(
    "ais_mu"          => "antarctic_mu",        "ais_bedheight0" => "antarctic_bed_height0",
    "ais_slope"       => "antarctic_slope",     "ais_iceflow0"   => "antarctic_flow0",
    "ais_precip0_LOG" => "antarctic_precip0",   "ais_c"          => "antarctic_c")
# phase-2 params likewise start at the values the MAP was CONDITIONED on (the medoid /
# the old fixed map), not at their prior means -- same lesson as the geometry start.
const FD_MEDOID = ("antarctic_lambda", "antarctic_gamma", "antarctic_kappa")
θ0 = Float64[]
for k in 1:NP
    nm = FREE[k].name
    if k in GEO_IDX
        if nm == "ais_runoff_Ton"                        # medoid T_on = -h0/c
            push!(θ0, -Float64(medoid["antarctic_runoff_height0"]) / Float64(medoid["antarctic_c"]))
        else
            v = Float64(medoid[GEO_MEDOID_COL[nm]])      # medoid stores precip₀ LINEAR
            push!(θ0, nm == "ais_precip0_LOG" ? log(v) : v)  # ...but θ/model are log-space
        end
    elseif nm in FD_MEDOID
        push!(θ0, Float64(medoid[nm]))
    elseif startswith(nm, "gic_")
        push!(θ0, Float64(FREE[k].μ))    # extB3: fresh glacier structure/frame — the old MAP's
                                         # gic_a/gic_b are OLD-FRAME values (gic_b can even sit
                                         # outside the new bounds); start at the prior center,
                                         # which D0 puts near the self-consistent solution
    elseif nm == "ais_gmst_amp"
        # ⚠ START AT THE PRIOR CENTRE, not at 1/0.8365. The old start was "the fixed map the
        # MAP ran under" (1.196), which is now +1.06σ off-centre and outside nothing but is a
        # needlessly displaced start for four chains that must mix across the prior.
        push!(θ0, AMP_MU)
    else
        j = findfirst(==(nm), mapp.param)
        push!(θ0, isnothing(j) ? FREE[k].μ : mapp.MAP[j])
    end
end
append!(θ0, repeat([1.0, 0.5], length(SERIES)))
## --gis-ordered: the DEFAULT START VIOLATES THE WEDGE, so it must be repaired.
##
## GIS_NATIVE_MU is (alpha_s = 0.0070727, beta_s = 0.0010) while gis_alpha_f is
## centred at 0.0028487 — i.e. the prior centre is itself INVERTED, which is the
## defect the constraint exists to remove. Starting there gives
## logposterior(θ0) = -Inf, and then every MH ratio is (-Inf) - (-Inf) = NaN,
## which compares false: acceptance collapses to EXACTLY 0.0 and the chain never
## moves. Measured (3k smoke, seed 2026): 0.0 with --gis-ordered against 0.257
## without it, which is what identified this.
##
## Repaired to L11's ORD-half medians (`split_l11_by_gis_ordering.py`):
## alpha_s 0.00147, beta_s 0.00237 against alpha_f 0.00415, beta_f 0.00754.
## Chosen over §5's T3 ordered optimum because that optimum binds at EQUALITY
## (alpha_f = alpha_s = 0.0036625) and rails beta_s at 1e-6 — starting on a
## constraint boundary and a rail would reject half the local proposals. These
## values are strictly INTERIOR and carry real posterior mass behind them.
##
## Only the START moves. The PRIORS are left exactly as they are, so the
## constraint is the clean operation "the same prior, TRUNCATED to the ordered
## region" rather than a different prior — recentring would change the model,
## not just enforce the labelling.
if GIS_ORDERED
    local a_s0, b_s0 = 0.00147, 0.00237          # L11 ORD-half medians
    local r_s0 = a_s0 * GIS_TBAR + b_s0
    θ0[GIS_ELL_IDX] = log(r_s0)
    θ0[GIS_W_IDX]   = a_s0 * GIS_TBAR / r_s0
    θ0[GIS_ALPHA_F_IDX] = max(θ0[GIS_ALPHA_F_IDX], 0.00415)
    θ0[GIS_BETA_F_IDX]  = max(θ0[GIS_BETA_F_IDX],  0.00754)
end
# extC: cap the proposal scale at (hi-lo)/4 — the flat-prior params (σ=10 / 1e3) would
# otherwise get absurd initial proposal widths; RAM adapts from a sane start instead
prop = vcat([0.1*Float64(min(k.σ, (k.hi - k.lo)/4)) for k in FREE],
            repeat([0.3, 0.1], length(SERIES)))
# Geometry proposals get their OWN scale: FREE[k].σ here is the PALEO prior sd, which is far
# broader than what the modern obs permit (paleo sd for ais_μ is 1.8; the chain's spread is
# ~0.004), so 0.1*prior-sd would be a very wide start. RAM adapts from here.
# NB this was NOT the cause of the low-acceptance problem seen while building this -- tested:
# it moved acceptance only 0.022 -> 0.029. That was the θ0 start point (see GEO_MEDOID_COL).
const GEO_PROP_SCALE = 0.02
for k in GEO_IDX; prop[k] = GEO_PROP_SCALE * Float64(FREE[k].σ); end
# proposal seed: PREFER the ext-tuned covariance (adapted_cov_ext.csv, written by
# postprocess_mcmc_ext.jl from a prior ext run) -- it matches the extended posterior
# shape, which the 2018-baseline adapted_cov.csv does NOT (point terms dropped +
# extended targets move the AIS block). Fall back to baseline cov, then diagonal.
# L11 = the 2026-08-14 change set (total dropped, GlaMBIE R19 rate, tightened
# rung, D2, Greenland (ell, w)). l11c is the FINAL-config tuning covariance and
# must be preferred: it is the only one tuned on the SHIPPED D2 basis
# (construction 2, steric col ⊥ S(t), cb21def). l11b was tuned on construction 1
# (⊥ the constant alone) and l11a on construction 1 AND native-coordinate
# Greenland. All three share the 57-name layout, so l11b/l11c are positionally
# valid; l11a is not (see the name-mapping guard below). Even a stale-basis L11
# covariance beats the 55-param L10 one, which knows nothing about the four
# d2_* columns either.
const ADCOV = let l11c = joinpath(REPO,"outputs/mcmc/adapted_cov_L11tune3_seed2026.csv"),
                  l11b = joinpath(REPO,"outputs/mcmc/adapted_cov_L11tune2_seed2026.csv"),
                  l11a = joinpath(REPO,"outputs/mcmc/adapted_cov_L11tune_seed2026.csv"),
                  l10b = joinpath(REPO,"outputs/mcmc/adapted_cov_L10tune2_seed2026.csv"),
                  l10 = joinpath(REPO,"outputs/mcmc/adapted_cov_L10tune_seed2026.csv"),
                  c1s = joinpath(REPO,"outputs/mcmc/adapted_cov_extC1_seed2026.csv"),
                  c1 = joinpath(REPO,"outputs/mcmc/adapted_cov_extC1.csv"),
                  b3c = joinpath(REPO,"outputs/mcmc/adapted_cov_extB3c_seed2026.csv"),
                  b2 = joinpath(REPO,"outputs/mcmc/adapted_cov_extB2_seed2026.csv"),
                  e = joinpath(REPO,"outputs/mcmc/adapted_cov_ext.csv"),
                  b = joinpath(REPO,"outputs/mcmc/adapted_cov.csv")
    # PRODUCTION: prefer the extC1-tuned full-rank cov (52x52, used as-is when NK
    # matches). Falls back to extB3c (38-param, name-mapped, fresh glacier diagonal)
    # for the first tuning run itself; a dimension mismatch is caught by the
    # dispatch below (visible WARNING -> diagonal), never silently misused.
    # L10tune2 is the 55-param (gis_amp sampled) tuning run and matches NK exactly,
    # so it is used AS-IS. L10tune is the 54-param first tuning run, name-mapped via
    # OLD54_NAMES. Both beat the extC covariance for a Ladrillo 1.0 run.
    # Preference order, most-preferred first. The Ladrillo-only covariances are
    # offered only when the A+B Greenland module is on; the rest are the pre-Ladrillo
    # fallbacks. Falls through to the 2018-baseline `b` if none exist.
    cands = String[]
    GIS_AB && append!(cands, [l11c, l11b, l11a, l10b, l10])
    append!(cands, [c1s, c1, b3c, b2, e])
    # --adcov=<name-or-path> overrides the preference list entirely. Added for the
    # L13 reseed: the list is ordered for the L11/L12 line and would keep handing an
    # L13-layout run the L11tune3 covariance, when the covariance actually wanted is
    # the CANONICAL L12 production one. An explicit flag also puts the choice in the
    # run script, where it is reviewable, instead of in a preference ordering.
    ov = _argval("--adcov=")
    if !isnothing(ov)
        # Accept an absolute path, a path relative to the repo root (what the
        # run_*.sh scripts define, e.g. outputs/mcmc/adapted_cov_L13tune_seed2026.csv),
        # a path relative to the cwd, or a bare filename in outputs/mcmc/.
        a = ov
        cands_ov = [a, joinpath(REPO, a), joinpath(REPO, "outputs/mcmc", a)]
        k = findfirst(isfile, cands_ov)
        isnothing(k) && error("--adcov=$a: no such file (tried " *
                              join(cands_ov, ", ") * ")")
        cands_ov[k]
    else
        i = findfirst(isfile, cands)
        isnothing(i) ? b : cands[i]
    end
end
cov0 = Matrix(Diagonal(prop.^2))
# Column order of the 35-param v-next chains/covs (18 physical + 7 geometry with the OLD
# ais_runoff_h0 coordinate + 10 AR(1) noise). Embedding is BY NAME: carried-over params
# keep the ridge-tuned proposal shape; the four new params (λ, γ, κ, amp) and the
# reparameterized T_on get the diagonal (h0's old row is deliberately NOT mapped -- its
# scale/meaning is wrong for T_on).
const OLD35_NAMES = vcat(
    ["ais_ocean_temperature₀","antarctic_alpha","antarctic_nu","antarctic_temp_threshold",
     "anto_alpha","anto_beta","greenland_a","greenland_b","greenland_alpha","greenland_beta",
     "greenland_v0","thermal_alpha","gic_a","gic_b","gic_T_lia","gic_f","gic_tau_fast","gic_tau_slow",
     "ais_mu","ais_bedheight0","ais_slope","ais_iceflow0","ais_precip0_LOG","ais_runoff_h0","ais_c"],
    vcat([["sd_$s","rho_$s"] for s in ALL_SERIES]...))
# extB2-vintage 39-param chain/cov order (29 physical + 10 noise), for name-mapping the
# tuned proposal shape into the extB3 parameter set. The gic_* rows are deliberately NOT
# mapped: the extB3 glacier block is a different structure AND frame, so the old glacier
# proposal scales/correlations are meaningless — those rows keep the fresh diagonal.
const OLD39_NAMES = vcat(
    ["ais_ocean_temperature₀","antarctic_alpha","antarctic_nu","antarctic_temp_threshold",
     "anto_alpha","anto_beta","greenland_a","greenland_b","greenland_alpha","greenland_beta",
     "greenland_v0","thermal_alpha","gic_a","gic_b","gic_T_lia","gic_f","gic_tau_fast","gic_tau_slow",
     "antarctic_lambda","antarctic_gamma","antarctic_kappa","ais_gmst_amp",
     "ais_mu","ais_bedheight0","ais_slope","ais_iceflow0","ais_precip0_LOG","ais_runoff_Ton","ais_c"],
    vcat([["sd_$s","rho_$s"] for s in ALL_SERIES]...))
# extB3-vintage 38-param chain/cov order (28 physical + 10 noise) — the verified header of
# chain_extB3*_seed2026_n500000.csv. Used to name-map the extB3c tuned proposal shape into
# the extC set; the single-reservoir gic_* rows are skipped (different structure).
const OLD38_NAMES = vcat(
    ["ais_ocean_temperature₀","antarctic_alpha","antarctic_nu","antarctic_temp_threshold",
     "anto_alpha","anto_beta","greenland_a","greenland_b","greenland_alpha","greenland_beta",
     "greenland_v0","thermal_alpha","gic_a","gic_b","gic_T_off","gic_log10_kappa","gic_nu",
     "antarctic_lambda","antarctic_gamma","antarctic_kappa","ais_gmst_amp",
     "ais_mu","ais_bedheight0","ais_slope","ais_iceflow0","ais_precip0_LOG","ais_runoff_Ton","ais_c"],
    vcat([["sd_$s","rho_$s"] for s in ALL_SERIES]...))
# extC-vintage 52-param chain/cov order (42 physical + 10 noise) — the verified
# header of chain_extC_seed2026_n2000000.csv. Used to name-map the extC1 tuned
# proposal shape into the Ladrillo 1.0 set, where the five stock-SIMPLE Greenland
# rows disappear and seven gis_* rows arrive on a fresh diagonal. The glacier rows
# ARE mapped here (unlike the older vintages): extC and Ladrillo 1.0 share the same
# three-reservoir glacier structure and frame, so those proposal scales still mean
# what they meant.
const OLD52_NAMES = vcat(
    ["ais_ocean_temperature₀","antarctic_alpha","antarctic_nu","antarctic_temp_threshold",
     "anto_alpha","anto_beta","greenland_a","greenland_b","greenland_alpha","greenland_beta",
     "greenland_v0","thermal_alpha",
     "gic_a_R19","gic_b_R19","gic_T_off_R19","gic_log10_kappa_R19",
     "gic_a_SLOWP","gic_b_SLOWP","gic_T_off_SLOWP","gic_log10_kappa_SLOWP",
     "gic_a_FAST","gic_b_FAST","gic_T_off_FAST","gic_log10_kappa_FAST",
     "gic_amp_R19","gic_amp_SLOWP","gic_amp_FAST",
     "gic_u_unch","gic_delta","gic_u_pre","gic_s_r5",
     "antarctic_lambda","antarctic_gamma","antarctic_kappa","ais_gmst_amp",
     "ais_mu","ais_bedheight0","ais_slope","ais_iceflow0","ais_precip0_LOG",
     "ais_runoff_Ton","ais_c"],
    vcat([["sd_$s","rho_$s"] for s in ALL_SERIES]...))

# L10tune-vintage 54-param order (44 physical + 10 noise) — the header of
# chain_L10tune_seed2026_n2000000.csv, the first Ladrillo 1.0 tuning run. It is
# the 55-param production set minus gis_amp, so 54 of 55 rows map and only the
# new amp row takes a fresh diagonal. This is a much better seed than the extC
# covariance: every Greenland row is already Ladrillo-shaped.
const OLD54_NAMES = vcat(
    ["ais_ocean_temperature₀","antarctic_alpha","antarctic_nu","antarctic_temp_threshold",
     "anto_alpha","anto_beta",
     "gis_c1","gis_c0","gis_f","gis_alpha_f","gis_beta_f","gis_alpha_s","gis_beta_s",
     "thermal_alpha",
     "gic_a_R19","gic_b_R19","gic_T_off_R19","gic_log10_kappa_R19",
     "gic_a_SLOWP","gic_b_SLOWP","gic_T_off_SLOWP","gic_log10_kappa_SLOWP",
     "gic_a_FAST","gic_b_FAST","gic_T_off_FAST","gic_log10_kappa_FAST",
     "gic_amp_R19","gic_amp_SLOWP","gic_amp_FAST",
     "gic_u_unch","gic_delta","gic_u_pre","gic_s_r5",
     "antarctic_lambda","antarctic_gamma","antarctic_kappa","ais_gmst_amp",
     "ais_mu","ais_bedheight0","ais_slope","ais_iceflow0","ais_precip0_LOG",
     "ais_runoff_Ton","ais_c"],
    vcat([["sd_$s","rho_$s"] for s in ALL_SERIES]...))

# The SHIPPED Ladrillo 1.0 layout: whatever FREE currently is, plus the full
# five-stream noise block. Built from FREE rather than typed out so it cannot
# drift, and it is what `pn0` equals when --drop-total is OFF. With --drop-total
# ON, NK=53 no longer matches the 55x55 L10-tuned covariance, and this table is
# what lets the by-name embedding carry the tuned shape across: sd_dang/rho_dang
# simply find no target in pn0 and are skipped.
# The L11tune layout: the current FREE set with the Greenland pair in its NATIVE
# coordinates, i.e. what the first tuning run sampled. Lets that covariance be
# name-mapped once the reparameterisation is on.
# THE SAME TRAP AS ALL_SERIES ABOVE, one layer out. These tables describe the
# layout of FILES ON DISK, so they must NOT follow the live FREE either: with
# --gis-basins the three gis_s_* rows do not exist in ANY pre-existing covariance,
# and letting them lengthen L11_NAMES from 57 to 60 makes the `size(old,1) ==
# length(L11_NAMES)` dispatch below MISS the L12 covariance entirely. That fails
# safe (visible warning -> fresh diagonal) rather than catastrophically, but it
# throws away the tuned proposal shape and would be read as "the covariance is
# incompatible" when in fact 57 of its 60 rows map perfectly. Filter them out.
const GISB_PNAMES = ["gis_s_$b" for b in GIS3_BASINS]   # all three; only some are sampled
prelayout(fr) = [k for k in fr if !(k.name in GISB_PNAMES)]

const L11A_NAMES = vcat(
    [k.name == "gis_slow_ell" ? "gis_alpha_s" :
     k.name == "gis_slow_w"   ? "gis_beta_s"  : k.name for k in prelayout(FREE)],
    vcat([["sd_$s","rho_$s"] for s in SERIES]...))

const L10_NAMES = vcat([k.name for k in prelayout(FREE)],
                       vcat([["sd_$s","rho_$s"] for s in ALL_SERIES]...))

# The L11 PRODUCTION layout: both D2 streams, D1 noise block. Built independently
# of the live D2_STREAMS so a one-stream run can still name-map the L11 covariance.
#
# SIZE COLLISION, and it is why this exists. L10_NAMES and the L11 layout are BOTH
# 57 long — L10 = 53 physical + 2 gis-native + 10 five-stream noise; L11 = 53
# physical + 2 gis-reparam + 4 D2 + 8 four-stream noise. So `size(old,1) ==
# length(L10_NAMES)` MATCHES AN L11 COVARIANCE, and a --d2-streams= run (NK=55)
# silently mapped adapted_cov_L11tune3 through L10's names: d2 coefficients landed
# on noise parameters, the Greenland pair on the wrong coordinates, and the chain
# accepted EXACTLY 0 of 2000 proposals. Caught 2026-08-16 by the acceptance being
# 0.0 rather than merely low. The shipped L11 production run is NOT affected — at
# NK=57 the `size(old,1) == NK` branch fires first and uses the matrix as-is,
# which is correct — so this is a latent trap the new flag exposed, not a defect
# in any published result. Dispatch on the file's VINTAGE, never on its size.
#
# IT MUST BE THE FILE'S PHYSICAL ROW ORDER, AND FOR A YEAR IT WAS NOT. The first
# version of this constant was built as `[non-d2 physical...] ++ [d2...] ++ noise`
# -- i.e. it PULLED the d2 block out of its FREE position and re-appended it after
# the AIS geometry block. The d2 params are pushed into FREE right after gic_s_r5
# and BEFORE antarctic_lambda, so on disk they are rows 35-38 while that literal
# put them at 45-48. The name SET still matched, so `embed_cov!` mapped 57 of 57
# rows and logged "dropped <nothing>" -- while shifting every row from 35 to 49 by
# four. Live `ais_c` was handed `ais_slope`'s variance, 8.005e-07 instead of 0.6065,
# which is a proposal that cannot move a parameter whose posterior spans ~95 units.
# That is the whole of the L13 "frozen ais_c": it was never an adaptation collapse,
# it was born dead at the seed (measured 2026-08-19d; see notes/handoff_2026-08-19c).
# RAM's update is multiplicative and rank-one along L*u, so a coordinate whose row
# of L is ~0 contributes ~0 to every proposal and can never be re-inflated -- the
# seed is the only chance the coordinate gets.
#
# So this is now a FROZEN LITERAL transcribed from the header of
# chain_L11tune3_seed2026_n1000000.csv (which is written in pn0 order, i.e. exactly
# the order RAM wrote the covariance in). It deliberately does NOT derive from the
# live FREE/SERIES: the file is a historical artefact and its layout cannot change,
# whereas FREE moves with every flag. Derived-from-live is what broke it.
const L11_NAMES = [
    "ais_ocean_temperature₀", "antarctic_alpha", "antarctic_nu", "antarctic_temp_threshold",
    "anto_alpha", "anto_beta", "gis_c1", "gis_c0",
    "gis_f", "gis_alpha_f", "gis_beta_f", "gis_slow_ell",
    "gis_slow_w", "gis_amp", "thermal_alpha", "gic_a_R19",
    "gic_b_R19", "gic_T_off_R19", "gic_log10_kappa_R19", "gic_a_SLOWP",
    "gic_b_SLOWP", "gic_T_off_SLOWP", "gic_log10_kappa_SLOWP", "gic_a_FAST",
    "gic_b_FAST", "gic_T_off_FAST", "gic_log10_kappa_FAST", "gic_amp_R19",
    "gic_amp_SLOWP", "gic_amp_FAST", "gic_u_unch", "gic_delta",
    "gic_u_pre", "gic_s_r5", "d2_gsic_1", "d2_gsic_2",
    "d2_steric_1", "d2_steric_2", "antarctic_lambda", "antarctic_gamma",
    "antarctic_kappa", "ais_gmst_amp", "ais_mu", "ais_bedheight0",
    "ais_slope", "ais_iceflow0", "ais_precip0_LOG", "ais_runoff_Ton",
    "ais_c", "sd_ais", "rho_ais", "sd_gsic",
    "rho_gsic", "sd_gis", "rho_gis", "sd_steric",
    "rho_steric"]
# The literal is checked against the live derivation as a SET (order is the whole
# point of the literal, so it is the one thing that must not be re-derived). A live
# config that cannot reproduce the L11 name set has no business reading an L11 file.
let live = Set(vcat([k.name for k in prelayout(FREE)],
                    ["d2_$(st)_$(k)" for st in ["gsic","steric"] for k in 1:D2_BASIS_N],
                    vcat([["sd_$s","rho_$s"] for s in SERIES]...)))
    Set(L11_NAMES) ⊆ live || @warn "L11_NAMES has names absent from the live layout; " *
        "the L11-vintage branch will leave those rows on the fresh diagonal: " *
        join(setdiff(Set(L11_NAMES), live), ", ")
end
"""Covariance files whose rows are in the L11 production ordering."""
# The L12 line adds NO parameters (--gis-ordered is a log-prior wedge), so every L12
# covariance is byte-for-byte in this same 57-row order -- verified 2026-08-19 by
# comparing the chain headers, which are written in pn0 order: all six L11/L12 chains
# compare equal to chain_L11tune3's. Listing them lets an L13-layout run reseed from
# the CANONICAL posterior's proposal instead of the two-vintages-older L11tune3.
const L11_VINTAGE_ADCOV = ["adapted_cov_L11tune2_seed2026.csv",
                           "adapted_cov_L11tune3_seed2026.csv",
                           "adapted_cov_L11_seed2026.csv",
                           "adapted_cov_L12tune_seed2026.csv",
                           "adapted_cov_L12_seed2026.csv",
                           "adapted_cov_L12_seed2027.csv",
                           "adapted_cov_L12_seed2028.csv",
                           "adapted_cov_L12_seed2029.csv"]

function embed_cov!(cov0, old, old_names; skip_gic::Bool=false)
    oi = Int[]; ni = Int[]
    for (i, nm) in enumerate(old_names)
        skip_gic && startswith(nm, "gic_") && continue
        j = findfirst(==(nm), pn0)
        isnothing(j) && continue                          # dropped/renamed params
        push!(oi, i); push!(ni, j)
    end
    cov0[ni, ni] = old[oi, oi]
    return length(oi)
end
# The seeding message is CAPTURED, not just printed: the run log is overwritten by
# ProgressMeter within seconds, and "which name list did this run map through" is the
# single most important fact about a seeded proposal. It is written to seed_diag_*.txt
# alongside the geometry gate below.
adcov_msg = "(no adapted covariance found; diagonal proposal)"
if isfile(ADCOV)
    adf = CSV.read(ADCOV, DataFrame)
    old = Matrix(adf)
    # SELF-DESCRIBING FILES FIRST. Files written before 2026-08-19 used
    # DataFrame(covout, :auto) and carry the placeholder header x1..xN, so their
    # row order is recoverable only from a vintage table (the ladder below, and
    # the source of the L11_NAMES order bug). Files written from now on carry pn0
    # as the header, so they name their own rows and need no vintage entry ever.
    adcov_named = !all(nm -> occursin(r"^x\d+$", nm), names(adf))
    # SIZE IS NOT IDENTITY. adapted_cov_L11tune is 57x57 and NK is 57, but its
    # Greenland rows are (alpha_s, beta_s) while ours are (ell, w) — taking it
    # as-is would apply an alpha_s proposal scale of ~0.005 to an ell of ~-4.2.
    # That is the positional-index trap; match on NAMES whenever they can differ.
    if adcov_named
        nmap = embed_cov!(cov0, old, names(adf))
        dropped = setdiff(names(adf), pn0)
        adcov_msg = ("(seeding proposal: name-mapped $nmap of $(size(old,1)) rows of " *
                "$(basename(ADCOV)) using the FILE'S OWN header" *
                (isempty(dropped) ? "" : "; dropped " * join(dropped, ", ")) * ")")
    elseif size(old,1) == NK &&
       !(GIS_REPARAM && basename(ADCOV) == "adapted_cov_L11tune_seed2026.csv")
        cov0 = old
        adcov_msg = ("(seeding proposal from adapted covariance $(basename(ADCOV)))")
    elseif basename(ADCOV) == "adapted_cov_L11tune_seed2026.csv" &&
           size(old,1) == length(L11A_NAMES)
        # native-coordinate Greenland rows are deliberately NOT mapped onto
        # (ell, w): the scales and meanings differ, so they keep a fresh diagonal.
        nmap = embed_cov!(cov0, old, L11A_NAMES)
        adcov_msg = ("(seeding proposal: name-mapped $nmap of $(size(old,1)) rows of " *
                "$(basename(ADCOV)); fresh diagonal for gis_slow_ell, gis_slow_w)")
    elseif basename(ADCOV) in L11_VINTAGE_ADCOV && size(old,1) == length(L11_NAMES)
        # MUST precede the L10 branch: the two layouts are the same length (see
        # the L11_NAMES comment), so size alone cannot tell them apart.
        nmap = embed_cov!(cov0, old, L11_NAMES)
        adcov_msg = ("(seeding proposal: name-mapped $nmap of $(size(old,1)) rows of " *
                "$(basename(ADCOV)) as L11 layout; dropped " *
                join(setdiff(L11_NAMES, pn0), ", ") * ")")
    elseif size(old,1) == length(L10_NAMES)
        basename(ADCOV) in L11_VINTAGE_ADCOV &&
            error("$(basename(ADCOV)) is an L11-vintage covariance but did not match " *
                  "L11_NAMES ($(size(old,1)) vs $(length(L11_NAMES))); refusing to " *
                  "read it under L10 names — that is the size collision, and it " *
                  "produces a zero-acceptance chain rather than an obvious failure")
        nmap = embed_cov!(cov0, old, L10_NAMES)
        adcov_msg = ("(seeding proposal: name-mapped $nmap of $(size(old,1)) rows of " *
                "$(basename(ADCOV)); dropped " *
                join(setdiff(L10_NAMES, pn0), ", ") * ")")
    elseif size(old,1) == length(OLD54_NAMES)
        nmap = embed_cov!(cov0, old, OLD54_NAMES)
        adcov_msg = ("(seeding proposal: name-mapped $nmap of $(size(old,1)) rows of " *
                "$(basename(ADCOV)); fresh diagonal for " *
                join(setdiff(pn0[1:NP], OLD54_NAMES), ", ") * ")")
    elseif size(old,1) == length(OLD52_NAMES)
        nmap = embed_cov!(cov0, old, OLD52_NAMES)
        adcov_msg = ("(seeding proposal: name-mapped $nmap of $(size(old,1)) rows of " *
                "$(basename(ADCOV)); fresh diagonal for " *
                join(setdiff(pn0[1:NP], OLD52_NAMES), ", ") * ")")
    elseif size(old,1) == length(OLD38_NAMES)
        nmap = embed_cov!(cov0, old, OLD38_NAMES; skip_gic=true)
        adcov_msg = ("(seeding proposal: name-mapped $nmap of $(size(old,1)) rows of " *
                "$(basename(ADCOV)); fresh diagonal for the extC glacier/ledger block " *
                join([nm for nm in pn0[1:NP] if startswith(nm,"gic_")], ", ") * ")")
    elseif size(old,1) == length(OLD39_NAMES)
        nmap = embed_cov!(cov0, old, OLD39_NAMES; skip_gic=true)
        adcov_msg = ("(seeding proposal: name-mapped $nmap of $(size(old,1)) rows of " *
                "$(basename(ADCOV)); fresh diagonal for the extB3 glacier block " *
                join([nm for nm in pn0[1:NP] if startswith(nm,"gic_")], ", ") * ")")
    elseif size(old,1) == length(OLD35_NAMES)
        nmap = embed_cov!(cov0, old, OLD35_NAMES; skip_gic=true)
        adcov_msg = ("(seeding proposal: name-mapped $nmap of $(size(old,1)) rows of " *
                "$(basename(ADCOV)); diagonal for " *
                join(setdiff(pn0[1:NP], OLD35_NAMES), ", ") * ")")
    else
        adcov_msg = ("(WARNING: $(basename(ADCOV)) is $(size(old,1))x$(size(old,1)), incompatible " *
                "with NK=$NK -- falling back to the diagonal proposal)")
    end
end
println(adcov_msg)
isposdef(cov0) || error("seed proposal covariance is not positive definite")

# ---- GEOMETRY SEED GATE (Marcus 2026-08-19; handoff_2026-08-19c §1.1) -------------
# A mis-ordered vintage table hands a live parameter another parameter's variance.
# It is positive definite, it is a valid permutation of a valid matrix, and nothing
# downstream complains: the chain runs at a healthy 0.246 global acceptance while one
# coordinate never moves. L13 spent 4x2M iterations and ~4h25m learning nothing about
# ais_c that way. RAM's rank-one multiplicative update means the seed is the ONLY
# chance a coordinate gets, so the seed is where the check belongs.
#
# Floors are the AIS paleo-geometry block's L12-production proposal sds divided by
# ~30 -- loose enough that a legitimately better-tuned proposal passes, tight enough
# that receiving a NEIGHBOURING parameter's scale fails. (ais_slope, the row L13
# actually got, is 8e-07 against ais_c's floor of 0.05: five orders of margin.)
const GEO_SEED_FLOOR = Dict("ais_c" => 0.05, "ais_mu" => 3e-3, "ais_bedheight0" => 0.03,
                            "ais_slope" => 1e-8, "ais_iceflow0" => 3e-4,
                            "ais_precip0_LOG" => 1e-3, "ais_runoff_Ton" => 5e-4,
                            # THE BASIN SCALES GET THE SAME GATE, and --gis-basins2 is
                            # exactly when they need it: dropping gis_s_mid takes NK
                            # 59 -> 58, so no covariance on disk matches by size and
                            # every seed goes through embed_cov! BY NAME. That is the
                            # third layout change in this arc and both previous ones
                            # bit (the ADCOV size collision -> acceptance 0.0; the
                            # L11_NAMES mis-order -> ais_c frozen for 4x2M). Floor is
                            # L13's own production proposal sd / ~30, the GEO_SEED_FLOOR
                            # convention: gis_s_high tuned to 0.0234 in L13, and the
                            # smallest sd anywhere in that layout is ais_slope's 8e-07,
                            # three orders below this floor.
                            "gis_s_south" => 1e-3, "gis_s_mid" => 1e-3,
                            "gis_s_high" => 1e-3)
# The gate runs over the AIS geometry block PLUS whichever basin scales are actually
# sampled. Derived from GISB_FREE_BASINS so it cannot list a parameter the run does
# not have (nor miss one it does).
const SEED_GATE_NAMES = vcat(GEO_NAMES, ["gis_s_$b" for b in GISB_FREE_BASINS])
# The table also goes to its OWN file. ProgressMeter writes cursor-up escapes to the
# same stream the setup output went to, so in a redirected run log the seeding line and
# this table are overwritten within seconds and the run's provenance is unrecoverable —
# which is half of why the mis-map went unnoticed for a whole L13 line. A plain file
# cannot be scribbled over.
let sd = sqrt.(diag(cov0)), bad = String[], rep = IOBuffer()
    println(rep, "proposal seed for tag=$TAG seed=$SEED")
    println(rep, "  ADCOV = $ADCOV")
    println(rep, "  NK = $NK")
    println(rep, "  $adcov_msg")
    println(rep, "AIS geometry block + sampled basin scales (sqrt of the covariance diagonal):")
    println("proposal seed, AIS geometry block + sampled basin scales (sqrt of the covariance diagonal):")
    for nm in SEED_GATE_NAMES
        j = findfirst(==(nm), pn0); isnothing(j) && continue
        flr = GEO_SEED_FLOOR[nm]
        ok = sd[j] >= flr
        ok || push!(bad, "$nm = $(sd[j]) < $flr")
        @printf("  %-18s %-12.4g floor %-10.4g %s\n", nm, sd[j], flr, ok ? "ok" : "TOO SMALL")
        @printf(rep, "  %-18s %-12.4g floor %-10.4g %s\n", nm, sd[j], flr, ok ? "ok" : "TOO SMALL")
    end
    mkpath(joinpath(REPO,"outputs/mcmc"))
    write(joinpath(REPO,"outputs/mcmc/seed_diag_$(TAG)_seed$(SEED).txt"), take!(rep))
    isempty(bad) || error("proposal seed is degenerate in the gated block: " *
        join(bad, "; ") * ". These parameters would be FROZEN for the whole run while " *
        "global acceptance looks healthy. Check that the vintage name list used to read " *
        "$(basename(ADCOV)) is in the FILE'S row order, not a re-derived one.")
end

# ---- over-dispersed starts (--overdisperse) ----------------------------------------
# R̂ is only a valid convergence diagnostic when chains start OVER-DISPERSED relative to
# the target. Every run through 2026-07-19 started all 4 chains at the SAME θ0 (θ0 is built
# deterministically from the MAP/medoid CSVs above, and Random.seed! was not called until
# after), so the chains differed only in RNG stream -- maximal UNDER-dispersion, the exact
# opposite of the Gelman-Rubin requirement. That makes R̂ anti-conservative: between-chain
# variance cannot reflect posterior mass no chain ever reached. With measured τ > 1e5 for
# the AIS block, 4 common-start chains cannot forget θ0 in a feasible run.
# Dispersion: geometry block drawn from its (bounded) paleo prior; everything else jittered
# by ±2 posterior sd taken from the seed covariance diagonal. Expect R̂ to LOOK WORSE than
# the common-start runs -- that is the diagnostic working, not a regression.
const OVERDISPERSE = "--overdisperse" in ARGS
if OVERDISPERSE
    # Starts are REAL posterior draws, not random jitter. Jittering the MAP (geometry from
    # the full paleo prior + 2 posterior sd on the rest) was tried and FAILED: 200/200 draws
    # gave a non-finite logposterior, because a jointly-perturbed geometry vector leaves the
    # feasible region even when every marginal is inside its bounds. Real draws are feasible
    # by construction AND dispersed along the direction that actually fails to mix.
    # Built by picking pooled run-3 draws at ais_iceflow0 quantiles 0.02/0.35/0.65/0.98.
    # --starts=PATH (2026-08-27, default-off): use a DIFFERENT starts file without touching
    # the canonical one. outputs/mcmc/overdispersed_starts.csv is L14's and is load-bearing —
    # L14 AND L18 both ran on it, and reusing it unrebuilt is what makes their comparison
    # exactly controlled. Swapping that file in place is how a later run silently inherits
    # another arm's starts (the repo already carries 4 .pre_*_bak files from doing exactly
    # that). Omitting the flag reproduces the previous behaviour byte for byte.
    SF = something(_argval("--starts="), joinpath(REPO, "outputs/mcmc/overdispersed_starts.csv"))
    isfile(SF) || error("--overdisperse needs $SF (4 rows x NK params). See notes/handoff_2026-07-18_brick_mengel_vnext.md")
    println("over-dispersed starts file: $SF")
    st = CSV.read(SF, DataFrame)
    si = findfirst(==(SEED), [2026,2027,2028,2029])
    isnothing(si) && error("--overdisperse: no start row defined for seed $SEED")
    nrow(st) >= si || error("--overdisperse: $SF has $(nrow(st)) rows, need >= $si")
    # The starts file must cover the CURRENT parameter set. The v-next (35-param)
    # starts predate phase-2's λ/γ/κ/amp and the T_on reparam, so this is a two-stage
    # launch (handoff §9): (1) a common-start tuning run to produce a phase-2 posterior;
    # (2) build overdispersed_starts.csv from it (draws at ais_iceflow0 quantiles
    # 0.02/0.35/0.65/0.98 -- NOT random jitter, which gives non-finite logpost) and
    # adapted_cov_ext.csv; (3) this production run.
    missing_cols = [nm for nm in pn0 if !hasproperty(st, Symbol(nm))]
    isempty(missing_cols) || error("--overdisperse: $SF is missing $(length(missing_cols)) " *
        "column(s): $(join(missing_cols, ", ")). It predates the current parameter set — " *
        "rebuild it from a phase-2 tuning run (two-stage launch; see calibrate header + handoff §9).")
    θmap = copy(θ0)
    for (k, nm) in enumerate(pn0)
        θ0[k] = Float64(st[si, Symbol(nm)])
    end
    # A6 sensitivity: the starts file holds phase-2 amp draws (~0.94); pin the start at the
    # equilibrium value so the chain begins on the pinned prior, not +100σ off it.
    AMP_EQ && (θ0[AMP_IDX] = AMP_MU)
    lp0 = logposterior(θ0)
    isfinite(lp0) || error("--overdisperse: start row $si for seed $SEED has non-finite logposterior")
    @printf("over-dispersed start (seed %d, row %d): logpost(θ0) = %.2f  [MAP start = %.2f]\n",
            SEED, si, lp0, logposterior(θmap))
else
    println("logpost(θ0) = ", round(logposterior(θ0), digits=2), "  (start = MAP; common across seeds -> R̂ is ANTI-CONSERVATIVE)")
end
## STRUCTURAL GUARD. --overdisperse already asserts this for its own start rows;
## the default path only PRINTED it, which is how a -Inf start reached a smoke
## run as "accept 0.0" rather than as an error. A non-finite start does not
## degrade sampling, it disables it: every MH ratio becomes NaN and the chain
## freezes at θ0 with sd ~ 1e-15 on every parameter. Fail loudly instead.
let lp0 = logposterior(θ0)
    isfinite(lp0) || error("logposterior(θ0) = $lp0 — the start point is in a " *
        "rejected region, so every MH ratio would be NaN and acceptance would " *
        "be exactly 0.0 with the chain frozen. " *
        (GIS_ORDERED ? "With --gis-ordered, check the channel-ordering wedge: " *
                       "alpha_s <= alpha_f AND beta_s <= beta_f must hold AT θ0." :
                       "Check the parameter bounds and the noise-term limits."))
end

# ---- --gis-check: acceptance gate for the Ladrillo 1.0 Greenland wiring -------------
# The Mimi component is validated against the offline cell by
# julia/validate_greenland_ab.jl, but that says nothing about whether the CALIBRATOR
# wires it up correctly -- the driver, the fixed g and v0, the re-reference frame and
# the Mouginot windows all live here, not in the component. This runs the model at
# theta0 (whose gis_* entries ARE the offline g=0 fit) and checks the four numbers the
# offline cell reports for that same parameter vector. A wiring error shows up as a
# gross miss, not a rounding difference, so the tolerances are deliberately loose.
if "--gis-check" in ARGS
    GIS_AB || error("--gis-check requires the A+B module (drop --stock-gis)")
    # Run at the EXACT offline g=0 vector, not at theta0. Two of the seven prior
    # centres are deliberately not the offline optimum (gis_beta_s is centred at
    # 1e-3 rather than on its 1e-6 rail, and gis_f carries a weak prior), so a
    # theta0 comparison would be testing the prior table rather than the wiring.
    # This gate is about the wiring: driver, fixed g and v0, re-reference frame,
    # Mouginot windows.
    const GIS_OFFLINE_G0 = Dict(          # m SLE / per-yr; cm centres /100
        "gis_c1" => 0.032766, "gis_c0" => 0.0404293, "gis_f" => 0.782569,
        "gis_alpha_f" => 0.00284865, "gis_beta_f" => 0.00736838,
        "gis_alpha_s" => 0.00707271, "gis_beta_s" => 1e-6)
    θchk = copy(θ0)
    applied = String[]
    for (k, fr) in enumerate(FREE)
        haskey(GIS_OFFLINE_G0, fr.name) &&
            (θchk[k] = GIS_OFFLINE_G0[fr.name]; push!(applied, fr.name))
    end
    # THE SLOW CHANNEL NEEDS THE (ell, w) MAP, and this is the second half of the
    # 2026-08-19 --gis-check repair. GIS_OFFLINE_G0 is keyed on the NATIVE names
    # gis_alpha_s / gis_beta_s, which do not exist in FREE under GIS_REPARAM — so
    # both overrides were silently skipped and θchk kept whatever slow channel θ0
    # carried. Under --gis-ordered θ0's slow channel is deliberately overwritten
    # with the L11 ORD-half medians (see the GIS_ORDERED block above), giving
    # r_s = 0.00526 against the offline cell's 0.01389, a factor 2.6 — which is
    # the whole of the four-gate failure. WITHOUT --gis-ordered it passed only
    # because θ0's MAP happened to sit near the offline slow channel, so the
    # defect was masked in exactly the configuration nobody ships.
    if GIS_REPARAM
        a_s, b_s = GIS_OFFLINE_G0["gis_alpha_s"], GIS_OFFLINE_G0["gis_beta_s"]
        r_s = a_s * GIS_TBAR + b_s
        θchk[GIS_ELL_IDX] = log(r_s)
        θchk[GIS_W_IDX]   = a_s * GIS_TBAR / r_s
        append!(applied, ["gis_slow_ell", "gis_slow_w"])
    end
    # PIN THE BASIN SCALES AT s = 1 IN THE REFERENCE VECTOR. --gis-check compares
    # against the A+B offline cell, and the 3-basin model equals A+B exactly only at
    # s = 1 (partition invariance, gated at 4.4e-16 by the nesting test). Today theta0
    # carries s = 1 anyway, because the basin params are absent from the MAP/medoid
    # CSVs and fall back to their prior centre of 0 in log10 — but the moment theta0
    # is rebuilt from an L13 posterior with s_b != 1, this gate would start failing
    # for a reason that has nothing to do with the wiring it tests. Pin it, so the
    # diagnostic keeps measuring the wiring rather than the posterior.
    if GIS_BASINS
        for b in GISB_FREE_BASINS; θchk[GISB_IDX3[b]] = 0.0; end   # log10(1) = 0
    end
    # NO SILENT SKIPS. Every offline key must reach a parameter, or the diagnostic
    # is comparing a vector that is not the reference vector — which is precisely
    # how this went unnoticed. Under GIS_REPARAM the native slow pair is consumed
    # by the map above rather than matched by name.
    let want = Set(keys(GIS_OFFLINE_G0)),
        got = Set(GIS_REPARAM ? vcat(applied, ["gis_alpha_s", "gis_beta_s"]) : applied)
        missed = setdiff(want, got)
        isempty(missed) || error("--gis-check: $(length(missed)) offline reference " *
            "value(s) matched no free parameter and were SILENTLY DROPPED: " *
            join(sort(collect(missed)), ", ") * ". θchk is then not the reference " *
            "vector and every gate below is meaningless.")
    end
    # Bypass the ordering wedge for the reference vector (see WEDGE_OFF), and ASSERT
    # the evaluation was real. A non-finite logposterior means run(m) never happened,
    # so every number below would be stale state from the previous call rather than a
    # measurement — the failure mode this guard exists to make impossible.
    lp_chk = WEDGE_OFF[] = true
    lp_chk = logposterior(θchk)                   # sets params and runs the model
    WEDGE_OFF[] = false
    isfinite(lp_chk) || error("--gis-check: logposterior(θchk) = $lp_chk, so run(m) " *
        "never executed and every diagnostic below would be STALE STATE from the " *
        "previous evaluation, not a measurement. Check the bounds on the offline " *
        "reference vector — the ordering wedge is already bypassed here.")
    gser = reref(m[_GIS_SLOT, :greenland_sea_level])       # cm, calibrator frame
    r = gser[S.gis.myi] .- S.gis.obs
    rmse = sqrt(sum(abs2, r) / length(r))
    mw = [i for (i, y) in enumerate(S.gis.years) if 1942 <= y <= 1982]
    bias = mean(r[mw])                             # MODEL - obs, matching evaluate_gates()
                                                   # in python/gis_offline_cell.py
    i03, i18 = idx(2003), idx(2018)
    rate = 10.0 * (gser[i18] - gser[i03]) / (2018 - 2003)   # cm -> mm/yr
    tot = m[_GIS_SLOT, :greenland_sea_level]; fst = m[_GIS_SLOT, :gis_fast]
    rt(x, i0, i1, n) = (Float64(x[i1]) - Float64(x[i0])) / n
    nref, nlate = MOUG_REF_WIN[2]-MOUG_REF_WIN[1], MOUG_LATE_WIN[2]-MOUG_LATE_WIN[1]
    share = (rt(fst, MOUG_I.l0, MOUG_I.l1, nlate) - rt(fst, MOUG_I.r0, MOUG_I.r1, nref)) /
            (rt(tot, MOUG_I.l0, MOUG_I.l1, nlate) - rt(tot, MOUG_I.r0, MOUG_I.r1, nref))
    # offline A+B at g=0 (outputs/gis_offline_cell_fits.csv + gis_g_betaf_variants.csv)
    REF = (rmse=0.0617, bias=0.0146, rate=0.7749, share=0.7351)
    TOL = (rmse=0.005,  bias=0.010,  rate=0.020,  share=0.010)
    # Per-basin modern shares at this same theta. Printed BEFORE any verdict on the
    # shares term, because a diagnostic that can already measure the thing is how
    # you tell a wiring bug from a physics result (handoff 2026-08-19 step 1).
    # NB with the basin rate scales at their prior centre (s = 1) these MUST come
    # out at the VOLUME shares GISB_K (3-basin 0.456/0.173/0.371; --gis-basins2
    # 0.629/0.000/0.371) — the model is linear in the commitment split and the
    # channel rates do not depend on k, so anything else is a wiring bug, not a
    # result. julia/test_greenland_3basin_nesting.jl [3] and [4] gate exactly that.
    if GIS_BASINS
        bsl = (south = m[_GIS_SLOT, :gis_sl_south],
               mid   = m[_GIS_SLOT, :gis_sl_mid],
               high  = m[_GIS_SLOT, :gis_sl_high])
        println("\n--gis-check | per-basin shares of the mean loss RATE, this theta")
        @printf("  %-12s %8s %8s %8s   %s\n", "window", "south", "mid", "high", "total cm/yr")
        for (wi, w, tgt) in zip(GISB_I, GISB_WINS, GISB_SHARE)
            d = map(b -> (Float64(getproperty(bsl, b)[wi.i1]) -
                          Float64(getproperty(bsl, b)[wi.i0])) / wi.n, GIS3_BASINS)
            dtot = sum(d)
            if abs(dtot) > GISB_TOT_FLOOR
                @printf("  %-12s %8.3f %8.3f %8.3f   %11.4f\n",
                        "$(w[1])-$(w[2])", (d ./ dtot)..., 100 * dtot)
            else
                @printf("  %-12s %s\n", "$(w[1])-$(w[2])",
                        "total rate below floor — shares undefined, term SKIPPED")
            end
            @printf("  %-12s %8.3f %8.3f %8.3f   (Mouginot target; %s scored, sd %.2f)\n",
                    "  target", tgt.south, tgt.mid, tgt.high,
                    join(GISB_SCORED, "+"), GISB_SHARE_SD)
        end
        @printf("  volume shares (the s = 1 null): %.3f %.3f %.3f   [%s]\n",
                GISB_K.south, GISB_K.mid, GISB_K.high, GISB_MODE_LABEL)
    end

    println("\n--gis-check | calibrator wiring vs the offline A+B cell at the SAME parameter vector")
    checks = [("RMSE cm", rmse, REF.rmse, TOL.rmse),
              ("1942-1982 bias cm", bias, REF.bias, TOL.bias),
              ("2003-2018 rate mm/yr", rate, REF.rate, TOL.rate),
              ("Mouginot surface share", share, REF.share, TOL.share)]
    passes = [abs(g - w) <= t for (_, g, w, t) in checks]
    for ((k, g, w, t), p) in zip(checks, passes)
        @printf("  %-24s got %8.4f   offline %8.4f   |diff| %7.4f  tol %.2f  %s\n",
                k, g, w, abs(g - w), t, p ? "PASS" : "FAIL")
    end
    println(all(passes) ? "GIS WIRING OK" : "GIS WIRING FAILED")
    exit(all(passes) ? 0 : 1)
end

# Guard the sampling+output so this canonical calibrator can be `include`d for its setup (FREE list,
# θ→BRICK apply logic, the dang-channel AR(1) likelihood, mean forcing) by forward-propagation tooling
# (e.g. weight_brick_conditional_fair.jl) WITHOUT running the chain. Run-as-script behaviour unchanged.
if abspath(PROGRAM_FILE) == @__FILE__
Random.seed!(SEED)
@time chain, accept, covout, lp = RAM_sample(logposterior, θ0, cov0, N_ITER; opt_α=0.234, output_log_probability_x=true)
mkpath(joinpath(REPO,"outputs/mcmc"))
# Header = pn0, NOT :auto. A nameless covariance can only be re-read through a
# hardcoded vintage table, and getting one of those orderings wrong is silent (it
# is a valid permutation of a valid matrix) -- that is how L13's ais_c was seeded
# with ais_slope's variance. A named file re-seeds correctly under ANY future layout.
CSV.write(joinpath(REPO,"outputs/mcmc/adapted_cov_$(TAG)_seed$(SEED).csv"), DataFrame(covout, pn0))
println("RAM run: $N_ITER iter, acceptance = ", round(accept, digits=3))
pn = pn0
burn = chain[(N_ITER÷2+1):end, :]
println("\nposterior (2nd-half) median ± sd for key params:")
for nm in vcat(["ais_ocean_temperature₀","anto_alpha","thermal_alpha"],
               [nm for nm in pn if startswith(nm, "gic_")],
               ["ais_mu","ais_precip0_LOG","ais_iceflow0","ais_c",
                "antarctic_lambda","antarctic_gamma","antarctic_kappa","ais_gmst_amp","ais_runoff_Ton"])
    j = findfirst(==(nm), pn)
    isnothing(j) && continue          # robust to glacier-block renames (extC surgery)
    c = burn[:, j]
    @printf("  %-24s %.3g ± %.2g\n", nm, median(c), std(c))
end
df = DataFrame(chain, pn); df.log_post = lp; df.accept_rate = fill(accept, nrow(df))
CSV.write(joinpath(REPO,"outputs/mcmc/chain_$(TAG)_seed$(SEED)_n$(N_ITER).csv"), df)
println("\nWrote outputs/mcmc/chain_$(TAG)_seed$(SEED)_n$(N_ITER).csv  (accept $(round(accept,digits=3)))")
println("Production = large N_ITER × ≥4 seeds, then postprocess_mcmc.jl with the chain_$(TAG)_* glob.")
end  # PROGRAM_FILE guard
