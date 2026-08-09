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
const TAG = TAG_OVR !== nothing ? TAG_OVR : (AMP_EQ ? "extA6eq" : "ext")   # output infix
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

ϵband(lo,hi)=max.((hi.-lo)./(2*1.645), 0.05)           # per-year obs σ (floor 0.05cm)

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
    if isdang   # total obs error = altimetry/Dangendorf σ ⊕ LWS-budget σ
        ev = sqrt.(Float64.(tg.dang_sig[ri]).^2 .+ ϵband(Float64.(tg.lws_lo[ri]), Float64.(tg.lws_hi[ri])).^2)
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

# ---- extB3b fallback (2026-08-07, handoff §2 item 7): pre-1940 GSIC flow σ ×2 -------------
# The extB3 tuning run (chain_extB3_seed2026_n500000) camped on the wiggle-tracking mode:
# all three pre-registered co-indicators fired (σ_gsic → 0.032 cm with ρ 0.96, gic_nu piled
# at 0 [P(ν<0.05)=0.24], S(1900) median 45 mm) and 0/4 evaluation gates passed
# (outputs/eval_gates_extB3_seed2026.csv). The documented fallback inflates the GSIC flow σ
# before GSIC_EARLY_YEAR: the residual 1900-1920 target melt sits on the Marzeion-2015-derived
# segment Roe 2021 calls an initialization artifact and precedes the HadCRUT5 ETCW ramp
# (~1918). Flag-gated so the extB3 no-inflation behaviour stays exactly reproducible.
const GSIC_EARLY_X2   = "--gsic-early-sigma-x2" in ARGS
const GSIC_EARLY_YEAR = 1940
const GSIC_EARLY_FAC  = 2.0
if GSIC_EARLY_X2
    early = S.gsic.years .< GSIC_EARLY_YEAR
    S.gsic.ϵ[early] .*= GSIC_EARLY_FAC
    @printf("GSIC early-σ fallback ON: flow σ ×%.1f for %d years < %d\n",
            GSIC_EARLY_FAC, count(early), GSIC_EARLY_YEAR)
end

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
push!(FREE, P("greenland_a",:greenland_icesheet,:greenland_a)); push!(FREE, P("greenland_b",:greenland_icesheet,:greenland_b))
push!(FREE, P("greenland_alpha",:greenland_icesheet,:greenland_α)); push!(FREE, P("greenland_beta",:greenland_icesheet,:greenland_β))
push!(FREE, P("greenland_v0",:greenland_icesheet,:greenland_v₀)); push!(FREE, P("thermal_alpha",:thermal_expansion,:te_α))
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
const DELTA_IDX  = findfirst(k -> k.name == "gic_delta", FREE)
const UPRE_IDX   = findfirst(k -> k.name == "gic_u_pre", FREE)
const SR5_IDX    = findfirst(k -> k.name == "gic_s_r5", FREE)
const AMPB_IDX3  = SAMPLED_AMP ?
    Dict(b => findfirst(k -> k.name == "gic_amp_$b", FREE) for b in BLOCKS) :
    Dict{String,Int}()
const SETP_SKIP  = Set(vcat(collect(values(KAPPA_IDX3)),
                            [UUNCH_IDX, DELTA_IDX, UPRE_IDX, SR5_IDX],
                            collect(values(AMPB_IDX3))))
# sampled mode: the κ prior is amp-dependent (center k10c(amp)) — exclude κ from the
# generic Normal(μ,σ) prior loop and add the explicit term in logposterior
const PRIOR_SKIP = SAMPLED_AMP ? Set(values(KAPPA_IDX3)) : Set{Int}()
# per-block rung likelihood data (data-basis committed %, band σ, cross-rung corr 0.6)
const GMIP_LEVELS = [1.2, 1.5, 2.0, 3.0]
const RUNG_CORR = 0.6
const RUNG_Y  = Dict(b => [Float64(bcrow(b)["com$(replace(string(L), "." => "p"))"])
                           for L in GMIP_LEVELS] for b in BLOCKS)
const RUNG_CI = Dict(b => begin
        sig = [Float64(bcrow(b)["sig$(replace(string(L), "." => "p"))"]) for L in GMIP_LEVELS]
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

# ---- phase-2 A6: GMST->Antarctic temperature map as a sampled TRANSIENT amplification ----
# The component computes T_ant = (GMST - intercept)/coef, i.e. amp = 1/coef with anchor
# T_ant(GMST=0) = -intercept/coef = -18.435 on the DAIS paleo scale. The hard-coded map
# (coef 0.8365, intercept 15.42 -> amp 1.196) is the inverted paleo/equilibrium regression;
# CMIP6 TRANSIENT AIS amplification is ~0.95 under SSP2-4.5 (Xie et al. 2022, Sci Rep
# 12:16548, PAI1 over the AIS: 0.88/0.95/0.97/1.03 for SSP1-2.6/2-4.5/3-7.0/5-8.5).
# `amp` is sampled with the ANCHOR PRESERVED (coef = 1/amp, intercept = -T_ant0/amp), so only
# the anomaly scaling changes; threshold-crossing GMST = (threshold - T_ant0)/amp.
# σ SIGN-OFF ITEM (Marcus): Xie publishes NO inter-model sd. 0.06 ~= the scenario spread;
# the default 0.10 spans the scenario range + structural uncertainty without re-admitting
# the equilibrium 1.196 (+2.5σ). Bounds cover SSP1-2.6 .. just above equilibrium.
# Production: N(0.95, 0.10) transient prior. --amp-equilibrium: pin at 1.19546 (old map).
const AMP_MU    = AMP_MU_OVR    !== nothing ? parse(Float64, AMP_MU_OVR)    : (AMP_EQ ? 1.0/0.8365 : 0.95)
const AMP_SIGMA = AMP_SIGMA_OVR !== nothing ? parse(Float64, AMP_SIGMA_OVR) : (AMP_EQ ? 0.002 : 0.10)
# Bounds: phase-2 defaults (0.70, 1.25). An explicit prior override widens them to μ±3σ so
# the new prior is NOT truncated — N(1.08, 0.15) would otherwise be clipped at +1.1σ.
const AMP_LO = AMP_MU_OVR === nothing ? 0.70 : AMP_MU - 3*AMP_SIGMA
const AMP_HI = AMP_MU_OVR === nothing ? 1.25 : AMP_MU + 3*AMP_SIGMA
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
const SERIES = [:ais,:gsic,:gis,:steric,:dang]
const NN = 2*length(SERIES); const NK = NP + NN
# parameter names in θ order (physical, then AR(1) noise). Defined here because
# --overdisperse needs it before sampling; the post-run summary reuses it.
const pn0 = vcat([k.name for k in FREE], vcat([["sd_$s","rho_$s"] for s in SERIES]...))
println("MCMC: $NP physical (incl $(length(GEO_IDX)) DAIS-geometry under a joint paleo prior) " *
        "+ $NN AR(1)-noise = $NK free params  (point terms DROPPED)")

# ---- model base (medoid + glacier init), forcing once -- extC 3-reservoir build ----
medoid = CSV.read(joinpath(REPO,"outputs/recalib_central_row.csv"), DataFrame)[1,:]
m = build_brick_nu3(ssp="ssp245", y0=Y0, y1=Y1)
gic3_init = (; (Symbol(b) => (a=Float64(bcrow(b).a0),
                              b=Float64(bcrow(b)["b_fit_$(FIT_BASIS)"]),
                              T_off=Float64(bcrow(b)["T_off_fit_$(FIT_BASIS)"]),
                              kappa=KAP_ANCH[b], nu=NU_ANCH[b]) for b in BLOCKS)...)
update_brick_nu3!(m, medoid, gic3_init; precip_log=true)   # ν_b FIXED here (anchored; not sampled)
set_forcing!(m, gmst, ohc)
set_glacier_forcing3!(m, tg3)         # per-block T_glac; glacier slot never sees raw GMST
setp!(k,v)=update_param!(m,k.comp,k.sym, k.islog ? log(v) : v)
reref(v)=100 .* (v .- sum(v[ib])/length(ib))

function logposterior(θ)
    @inbounds for k in 1:NP; (θ[k]<FREE[k].lo || θ[k]>FREE[k].hi) && return -Inf; end
    σn = θ[NP+1:2:NK]; ρn = θ[NP+2:2:NK]
    (any(σn .<= 0) || any(ρn .< 0) || any(ρn .>= 0.99)) && return -Inf
    @inbounds for k in 1:NP
        (k == AMP_IDX || k == TON_IDX || k in SETP_SKIP) && continue   # derived/likelihood-only
        setp!(FREE[k], θ[k])
    end
    # extC: per-block κ sampled as log10 -- the component gets the linear value
    for b in BLOCKS
        update_param!(m, G, Symbol("gic_kappa_$b"), 10.0^θ[KAPPA_IDX3[b]])
    end
    # A4: runoff line -- reconstruct h0 from the identified direction
    update_param!(m, :antarctic_icesheet, :ais_runoffline_snowheight₀, -θ[TON_IDX] * θ[C_IDX])
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
    for (i,(s,full)) in enumerate(zip([S.ais,S.gsic,S.gis,S.steric], [ais,gsic_flow,gis,te]))
        if i == 2
            ll += hetero_logl_ar1(full[s.myi] .- (s.obs .+ θ[DELTA_IDX] .* DELTA_RAMP),
                                  σn[i], ρn[i], s.ϵ)
        else
            ll += hetero_logl_ar1(full[s.myi] .- s.obs, σn[i], ρn[i], s.ϵ)
        end
    end
    # total: modeled ice+steric at "dang" years + observed LWS. NB the "dang"-labeled
    # target is the FREDERIKSE 2020 total (label fix 2026-07-20) spliced with NOAA STAR
    # altimetry -- rename pending the M3 total-term rework.
    ll += hetero_logl_ar1(tot_full[S.dang.myi] .+ lws_dang .- S.dang.obs, σn[5], ρn[5], S.dang.ϵ)
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
    # per-block GlaMBIE modern-rate terms (hindcast blocks only; 2000-2024 mean, err ×1.5)
    for b in HIND_BLOCKS
        ser = b == "SLOWP" ? m[G, :gsic_slowp] : m[G, :gsic_fast]
        mrate = 1000.0*(Float64(ser[GLAMBIE_I1]) - Float64(ser[GLAMBIE_I0])) / (2024 - 2000)
        ll += logpdf(Normal(GLAMBIE_RATE[b], GLAMBIE_SD[b]), mrate)
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
        push!(θ0, 1.0 / 0.8365)                          # the fixed map the MAP ran under
    else
        j = findfirst(==(nm), mapp.param)
        push!(θ0, isnothing(j) ? FREE[k].μ : mapp.MAP[j])
    end
end
append!(θ0, repeat([1.0, 0.5], length(SERIES)))
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
const ADCOV = let c1s = joinpath(REPO,"outputs/mcmc/adapted_cov_extC1_seed2026.csv"),
                  c1 = joinpath(REPO,"outputs/mcmc/adapted_cov_extC1.csv"),
                  b3c = joinpath(REPO,"outputs/mcmc/adapted_cov_extB3c_seed2026.csv"),
                  b2 = joinpath(REPO,"outputs/mcmc/adapted_cov_extB2_seed2026.csv"),
                  e = joinpath(REPO,"outputs/mcmc/adapted_cov_ext.csv"),
                  b = joinpath(REPO,"outputs/mcmc/adapted_cov.csv")
    # PRODUCTION: prefer the extC1-tuned full-rank cov (52x52, used as-is when NK
    # matches). Falls back to extB3c (38-param, name-mapped, fresh glacier diagonal)
    # for the first tuning run itself; a dimension mismatch is caught by the
    # dispatch below (visible WARNING -> diagonal), never silently misused.
    isfile(c1s) ? c1s : (isfile(c1) ? c1 :
        (isfile(b3c) ? b3c : (isfile(b2) ? b2 : (isfile(e) ? e : b))))
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
    vcat([["sd_$s","rho_$s"] for s in SERIES]...))
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
    vcat([["sd_$s","rho_$s"] for s in SERIES]...))
# extB3-vintage 38-param chain/cov order (28 physical + 10 noise) — the verified header of
# chain_extB3*_seed2026_n500000.csv. Used to name-map the extB3c tuned proposal shape into
# the extC set; the single-reservoir gic_* rows are skipped (different structure).
const OLD38_NAMES = vcat(
    ["ais_ocean_temperature₀","antarctic_alpha","antarctic_nu","antarctic_temp_threshold",
     "anto_alpha","anto_beta","greenland_a","greenland_b","greenland_alpha","greenland_beta",
     "greenland_v0","thermal_alpha","gic_a","gic_b","gic_T_off","gic_log10_kappa","gic_nu",
     "antarctic_lambda","antarctic_gamma","antarctic_kappa","ais_gmst_amp",
     "ais_mu","ais_bedheight0","ais_slope","ais_iceflow0","ais_precip0_LOG","ais_runoff_Ton","ais_c"],
    vcat([["sd_$s","rho_$s"] for s in SERIES]...))
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
if isfile(ADCOV)
    old = Matrix(CSV.read(ADCOV, DataFrame))
    if size(old,1) == NK
        cov0 = old
        println("(seeding proposal from adapted covariance $(basename(ADCOV)))")
    elseif size(old,1) == length(OLD38_NAMES)
        nmap = embed_cov!(cov0, old, OLD38_NAMES; skip_gic=true)
        println("(seeding proposal: name-mapped $nmap of $(size(old,1)) rows of " *
                "$(basename(ADCOV)); fresh diagonal for the extC glacier/ledger block " *
                join([nm for nm in pn0[1:NP] if startswith(nm,"gic_")], ", ") * ")")
    elseif size(old,1) == length(OLD39_NAMES)
        nmap = embed_cov!(cov0, old, OLD39_NAMES; skip_gic=true)
        println("(seeding proposal: name-mapped $nmap of $(size(old,1)) rows of " *
                "$(basename(ADCOV)); fresh diagonal for the extB3 glacier block " *
                join([nm for nm in pn0[1:NP] if startswith(nm,"gic_")], ", ") * ")")
    elseif size(old,1) == length(OLD35_NAMES)
        nmap = embed_cov!(cov0, old, OLD35_NAMES; skip_gic=true)
        println("(seeding proposal: name-mapped $nmap of $(size(old,1)) rows of " *
                "$(basename(ADCOV)); diagonal for " *
                join(setdiff(pn0[1:NP], OLD35_NAMES), ", ") * ")")
    else
        println("(WARNING: $(basename(ADCOV)) is $(size(old,1))x$(size(old,1)), incompatible " *
                "with NK=$NK -- falling back to the diagonal proposal)")
    end
end
isposdef(cov0) || error("seed proposal covariance is not positive definite")

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
    SF = joinpath(REPO, "outputs/mcmc/overdispersed_starts.csv")
    isfile(SF) || error("--overdisperse needs $SF (4 rows x NK params). See notes/handoff_2026-07-18_brick_mengel_vnext.md")
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

# Guard the sampling+output so this canonical calibrator can be `include`d for its setup (FREE list,
# θ→BRICK apply logic, the dang-channel AR(1) likelihood, mean forcing) by forward-propagation tooling
# (e.g. weight_brick_conditional_fair.jl) WITHOUT running the chain. Run-as-script behaviour unchanged.
if abspath(PROGRAM_FILE) == @__FILE__
Random.seed!(SEED)
@time chain, accept, covout, lp = RAM_sample(logposterior, θ0, cov0, N_ITER; opt_α=0.234, output_log_probability_x=true)
mkpath(joinpath(REPO,"outputs/mcmc"))
CSV.write(joinpath(REPO,"outputs/mcmc/adapted_cov_$(TAG)_seed$(SEED).csv"), DataFrame(covout, :auto))
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
