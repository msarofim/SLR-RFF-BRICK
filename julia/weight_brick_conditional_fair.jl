## ============================================================================
## weight_brick_conditional_fair.jl — CONDITIONAL Wong-style weighting of BRICK-AM draws per FaIR config
##
## Endorsed forward-propagation consistency (see notes/negresult_2026-08-01_joint_forcing_calibration.md):
## the joint free-forcing calibration was rejected because it let SLR RE-INFER the forcing. This instead
## keeps the forcing FIXED and only fixes the PAIRING — for each FaIR config k it reweights the BRICK-AM
## posterior draws by historical-SLR consistency, NORMALIZED WITHIN each config so p(config) stays uniform
## (every FaIR parameter set equally likely — SLR never touches the forcing marginal). This recovers the
## te_α↔OHC coupling in PROPAGATION, not calibration.
##
## Weight (Wong Eqs 1-3, conditional variant):  w_{i|k} ∝ exp[ c·(ℓ^FB_{ik} − ℓ^B_i) ],  Σ_i w_{i|k}=1 per k
##   ℓ^FB_{ik} = historical total-SLR (Frederikse "dang" channel, draw i's own AR(1) sd_dang/rho_dang)
##               with BRICK-AM driven by FaIR config k's GMST+OHC.
##   ℓ^B_i     = same at the MEAN forcing (the calibration climate) ⇒ the ratio isolates the pairing and
##               cancels each draw's intrinsic (calibrated) fit, mitigating the Mengel double-count.
## c is tuned to a GENTLE mean conditional ESS/N (default 0.6) — a consistency nudge, not a re-calibration.
##
## Reuses calibrate_mcmc_ext.jl (CANONICAL) via guarded include: FREE, θ→BRICK apply, dang AR(1) lik,
## mean forcing, model m (1850–2026, historical is all the weighting needs).
##
## Usage: julia --project=julia_v2 julia/weight_brick_conditional_fair.jl --amp-mu=1.08 --amp-sigma=0.15 \
##            [--draws N] [--configs N|all] [--ess-target 0.6]
## ============================================================================
include(joinpath(@__DIR__, "calibrate_mcmc_ext.jl"))     # guarded: gives FREE, NP, AMP_IDX, TON_IDX,
                                                         # C_IDX, AIS_TANT0, m, set_forcing!, setp!, reref,
                                                         # S, lws_dang, hetero_logl_ar1, gmst, ohc, years
using Statistics, Printf, CSV, DataFrames

_arg(p,d)=(i=findfirst(a->startswith(a,p),ARGS); i===nothing ? d : ARGS[i][length(p)+1:end])
const NDRAWS  = parse(Int, _arg("--draws=", "1000"))
const CFGARG  = _arg("--configs=", "all")
const ESSTGT  = parse(Float64, _arg("--ess-target=", "0.6"))
const FRC = joinpath(REPO, "..", "FaIRtoFrEDI", "magicc_comparison", "processed", "curv_wide")
const OHCS = 0.1                                          # wide OHC (1e21 J) → 1e22 J (matches ext mean)
yy(y) = findfirst(==(y), years)

# ---- FaIR ensemble forcing over the HISTORICAL window (1850:2026), aligned to ext's `years` ----
loadw(p; s=1.0) = (d=CSV.read(p,DataFrame); keep=[y in years for y in d.year]; Matrix(d[keep,2:end]).*s)
const GW = loadw(joinpath(FRC,"fair_gmst_base_wide.csv"))          # (nyear × NCFG)
const OW = loadw(joinpath(FRC,"fair_ohc_base_wide.csv"); s=OHCS)
const NCFG_ALL = size(GW,2)
@printf("FaIR ensemble: %d configs × %d yr; ext mean vs ensemble-mean GMST@2018 max|Δ| %.2e\n",
        NCFG_ALL, length(years), maximum(abs.(vec(mean(GW,dims=2)) .- gmst)))

# ---- BRICK-AM draws (extA108 subsample), thinned ----
sub = CSV.read(joinpath(REPO,"data/MimiBRICK/parameters_subsample_brick_mengel_extA108.csv"), DataFrame)
step = max(1, nrow(sub) ÷ NDRAWS); ridx = collect(1:step:nrow(sub))[1:min(NDRAWS,length(1:step:nrow(sub)))]
const ND = length(ridx)
θmat = [Float64[Float64(sub[r, Symbol(FREE[k].name)]) for k in 1:NP] for r in ridx]
sd_d = Float64[Float64(sub[r,:sd_dang])  for r in ridx]
rh_d = Float64[Float64(sub[r,:rho_dang]) for r in ridx]
te_i = Float64[Float64(sub[r,:thermal_alpha]) for r in ridx]
@printf("BRICK-AM draws: %d (thinned from %d)\n", ND, nrow(sub))

# ---- dang-channel historical log-likelihood of draw θ under a given (gmst,ohc) forcing ----
function dang_ll(θ, g, o, sd, rho)
    (sd<=0 || rho<0 || rho>=0.99) && return -Inf
    set_forcing!(m, g, o)
    @inbounds for k in 1:NP; (k==AMP_IDX||k==TON_IDX) && continue; setp!(FREE[k], θ[k]); end
    update_param!(m,:antarctic_icesheet,:ais_runoffline_snowheight₀, -θ[TON_IDX]*θ[C_IDX])
    update_param!(m,:antarctic_icesheet,:ais_temperature_coefficient, 1.0/θ[AMP_IDX])
    update_param!(m,:antarctic_icesheet,:ais_temperature_intercept, -AIS_TANT0/θ[AMP_IDX])
    run(m)
    tot = reref(m[:antarctic_icesheet,:ais_sea_level]) .+ reref(m[:glaciers_small_icecaps,:gsic_sea_level]) .+
          reref(m[:greenland_icesheet,:greenland_sea_level]) .+ reref(m[:thermal_expansion,:te_sea_level])
    hetero_logl_ar1(tot[S.dang.myi] .+ lws_dang .- S.dang.obs, sd, rho, S.dang.ϵ)
end

# ---- ℓ^B (mean forcing) per draw ----
println("computing ℓ^B (mean forcing) for $ND draws ...")
lB = Float64[dang_ll(θmat[i], gmst, ohc, sd_d[i], rh_d[i]) for i in 1:ND]

# ---- pick configs (validation: subset spanning OHC@2018; full: all) ----
ohc2018 = Float64[OW[yy(2018),k]-OW[yy(1850),k] for k in 1:NCFG_ALL]
cfgs = CFGARG=="all" ? collect(1:NCFG_ALL) :
       (n=parse(Int,CFGARG); sortperm(ohc2018)[round.(Int, range(1, NCFG_ALL, length=n))])
const NCFG = length(cfgs)
@printf("configs: %d (%s); OHC@2018 range [%.1f, %.1f] ×1e22J\n", NCFG, CFGARG, minimum(ohc2018[cfgs]), maximum(ohc2018[cfgs]))

# ---- ℓ^FB per (config, draw) ----
println("computing ℓ^FB for $NCFG configs × $ND draws = $(NCFG*ND) runs ...")
lFB = Array{Float64}(undef, ND, NCFG)
for (j,k) in enumerate(cfgs)
    g=GW[:,k]; o=OW[:,k]
    for i in 1:ND; lFB[i,j]=dang_ll(θmat[i], g, o, sd_d[i], rh_d[i]); end
    j % 20 == 0 && (print("."); flush(stdout))
end
println()

# ---- conditional weights w_{i|k} ∝ exp(c·(ℓ^FB−ℓ^B)), normalized per config; tune c for mean ESS/N ----
Δ = lFB .- lB                                              # (ND × NCFG)
function condw(c)
    W = similar(Δ)
    for j in 1:NCFG
        x = c .* @view Δ[:,j]; m_=maximum(x); w = exp.(x .- m_); s=sum(w)
        W[:,j] = s>0 ? w./s : fill(1/ND, ND)
    end
    W
end
essfrac(W) = mean(1.0 ./ (ND .* vec(sum(W.^2, dims=1))))   # mean over configs of ESS_k/ND
# bisect c on monotone-decreasing ESS(c) to hit ESSTGT (wrapped to avoid top-level soft-scope)
function tune_c(target)
    clo, chi = 0.0, 5.0
    while essfrac(condw(chi)) > target; chi *= 2; chi > 1e4 && break; end
    for _ in 1:40; cm=(clo+chi)/2; essfrac(condw(cm)) > target ? (clo=cm) : (chi=cm); end
    (clo+chi)/2
end
const C = tune_c(ESSTGT)
W = condw(C)
@printf("\nc = %.4g  →  mean conditional ESS/N = %.3f  (target %.2f)\n", C, essfrac(W), ESSTGT)

# ---- SANITY 1: mean-forcing pseudo-config must give UNIFORM weights (ℓ^FB=ℓ^B ⇒ Δ=0) ----
lFBmean = Float64[dang_ll(θmat[i], gmst, ohc, sd_d[i], rh_d[i]) for i in 1:ND]
xm = C .* (lFBmean .- lB); wm = exp.(xm .- maximum(xm)); wm ./= sum(wm)
@printf("SANITY mean-forcing: max|ℓ^FB−ℓ^B| = %.2e, weight ESS/N = %.4f  (expect ≈ 0 and ≈ 1.0)\n",
        maximum(abs.(lFBmean .- lB)), 1.0/(ND*sum(wm.^2)))

# ---- SANITY 2: coupling signature — hot-OHC configs down-weight high-te_α draws ----
corr_te = Float64[cor(W[:,j], te_i) for j in 1:NCFG]
oc = ohc2018[cfgs]
@printf("SANITY coupling: corr(weight, te_α) vs config OHC@2018: slope %.4f, corr %.2f\n",
        (cov(oc,corr_te)/var(oc)), cor(oc,corr_te))
@printf("   hottest-OHC configs mean corr(w,te_α) = %+.3f ; coldest = %+.3f  (expect hot<0<cold)\n",
        mean(corr_te[sortperm(oc)[end-max(1,NCFG÷5)+1:end]]), mean(corr_te[sortperm(oc)[1:max(1,NCFG÷5)]]))

# ---- output ----
outw = DataFrame(config=repeat(cfgs, inner=ND), draw=repeat(ridx, outer=NCFG),
                 w=vec(W), lFB=vec(lFB), lB=repeat(lB, outer=NCFG))
CSV.write(joinpath(REPO,"outputs/mcmc/wong_conditional_weights.csv"), outw)
@printf("wrote outputs/mcmc/wong_conditional_weights.csv  (%d rows, c=%.4g, ESS/N=%.3f)\n", nrow(outw), C, essfrac(W))
