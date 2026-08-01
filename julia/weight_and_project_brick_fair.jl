## ============================================================================
## weight_and_project_brick_fair.jl — FULL conditional-Wong forward propagation + coupled SLR bands.
##
## Combines weight_brick_conditional_fair.jl (conditional weighting) with a projection to 2300, so a
## SINGLE BRICK run per (config, draw) yields BOTH the historical fit ℓ^FB (for the weight) AND the
## future SLR (for the bands). Produces COUPLED bands (each FaIR config equally likely, BRICK draws
## conditionally weighted) vs INDEPENDENT bands (equal weight) — the deliverable comparison.
##
## Method: for each FaIR config k, w_{i|k} ∝ exp[c·(ℓ^FB_ik − ℓ^B_i)] normalized WITHIN config k, so
## p(config)=1/NCFG stays uniform (SLR never touches the forcing marginal). ℓ^B at the mean (calibration)
## forcing. c tuned to a gentle mean conditional ESS/N (default 0.6). See
## notes/negresult_2026-08-01_joint_forcing_calibration.md + weight_brick_conditional_fair.jl (validated).
##
## Usage (smoke): julia --project=julia_v2 julia/weight_and_project_brick_fair.jl 2000 2026 \
##                    --amp-mu=1.08 --amp-sigma=0.15 --draws=200 --configs=5
##        (full): ... --draws=2000 --configs=all     (≈1.68M runs to 2300, ~1–2.5 h single-core)
## ============================================================================
include(joinpath(@__DIR__, "calibrate_mcmc_ext.jl"))     # guarded: FREE, NP, AMP_IDX, TON_IDX, C_IDX,
                                                         # AIS_TANT0, setp!(unused), S, lws_dang,
                                                         # hetero_logl_ar1, build_brick_mengel, update_brick_mengel!
using Statistics, Printf, CSV, DataFrames

_arg(p,d)=(i=findfirst(a->startswith(a,p),ARGS); i===nothing ? d : ARGS[i][length(p)+1:end])
const NDRAWS = parse(Int, _arg("--draws=", "2000"))
const CFGARG = _arg("--configs=", "all")
const ESSTGT = parse(Float64, _arg("--ess-target=", "0.6"))
const FRC = joinpath(REPO, "..", "FaIRtoFrEDI", "magicc_comparison", "processed", "curv_wide")
const OHCS = 0.1
const YP0, YP1 = 1850, 2300
const YRS2 = collect(YP0:YP1); ty(y)=findfirst(==(y),YRS2)
const IB2 = [ty(y) for y in 1995:2005]
const HORIZONS = [2050, 2100, 2150, 2300]
const LABELS = ["total@2050","total@2100","total@2150","total@2300","ais@2100","gsic@2100","gis@2100","te@2100"]
const DANG_IDX2 = [ty(y) for y in S.dang.years]          # dang fit years mapped into the 1850–2300 array

# ---- FaIR ensemble forcing to 2300 ----
loadw(p; s=1.0)=(d=CSV.read(p,DataFrame); keep=[y in YRS2 for y in d.year]; Matrix(d[keep,2:end]).*s)
const GW2 = loadw(joinpath(FRC,"fair_gmst_base_wide.csv"))
const OW2 = loadw(joinpath(FRC,"fair_ohc_base_wide.csv"); s=OHCS)
const NCFG_ALL = size(GW2,2)
const GMEAN2 = vec(mean(GW2,dims=2)); const OMEAN2 = vec(mean(OW2,dims=2))   # ensemble mean = calibration forcing
@printf("FaIR ensemble to 2300: %d configs × %d yr\n", NCFG_ALL, length(YRS2))

# ---- BRICK-AM draws (extA108 subsample), thinned ----
sub = CSV.read(joinpath(REPO,"data/MimiBRICK/parameters_subsample_brick_mengel_extA108.csv"), DataFrame)
step = max(1, nrow(sub) ÷ NDRAWS); ridx = collect(1:step:nrow(sub))[1:min(NDRAWS,length(1:step:nrow(sub)))]
const ND = length(ridx)
θmat = [Float64[Float64(sub[r, Symbol(FREE[k].name)]) for k in 1:NP] for r in ridx]
sd_d = Float64[Float64(sub[r,:sd_dang])  for r in ridx]
rh_d = Float64[Float64(sub[r,:rho_dang]) for r in ridx]
te_i = Float64[Float64(sub[r,:thermal_alpha]) for r in ridx]
@printf("BRICK-AM draws: %d (thinned from %d)\n", ND, nrow(sub))

# ---- projection model (1850–2300) ----
medoid = CSV.read(joinpath(REPO,"outputs/recalib_central_row.csv"), DataFrame)[1,:]
const m2 = build_brick_mengel(ssp="ssp245", y0=YP0, y1=YP1)
update_brick_mengel!(m2, medoid, (a=0.45,b=0.52,T_lia=-0.45,f=0.5,tau_fast=40.0,tau_slow=250.0,sl0=0.0); precip_log=true)
setp2!(k,v)=update_param!(m2,k.comp,k.sym, k.islog ? log(v) : v)
reref2(v)=100 .* (v .- mean(v[IB2]))

# run once to 2300 → (historical ice+steric total at dang years, future global total@horizons, comps@2100)
function run2300(θ, g, o)
    set_forcing!(m2, g, o)
    @inbounds for k in 1:NP; (k==AMP_IDX||k==TON_IDX) && continue; setp2!(FREE[k], θ[k]); end
    update_param!(m2,:antarctic_icesheet,:ais_runoffline_snowheight₀, -θ[TON_IDX]*θ[C_IDX])
    update_param!(m2,:antarctic_icesheet,:ais_temperature_coefficient, 1.0/θ[AMP_IDX])
    update_param!(m2,:antarctic_icesheet,:ais_temperature_intercept, -AIS_TANT0/θ[AMP_IDX])
    run(m2)
    ais=reref2(m2[:antarctic_icesheet,:ais_sea_level]); gsic=reref2(m2[:glaciers_small_icecaps,:gsic_sea_level])
    gis=reref2(m2[:greenland_icesheet,:greenland_sea_level]); te=reref2(m2[:thermal_expansion,:te_sea_level])
    icesteric = ais .+ gsic .+ gis .+ te
    gtot = reref2(m2[:global_sea_level,:sea_level_rise])           # projected total incl model LWS
    i100 = ty(2100)
    (icesteric[DANG_IDX2], gtot[[ty(y) for y in HORIZONS]], (ais[i100],gsic[i100],gis[i100],te[i100]))
end
dll(dang_tot, sd, rho) = hetero_logl_ar1(dang_tot .+ lws_dang .- S.dang.obs, sd, rho, S.dang.ϵ)

# ---- ℓ^B (mean forcing) per draw ----
println("ℓ^B (mean forcing) for $ND draws ...")
lB = Vector{Float64}(undef, ND)
for i in 1:ND; d,_,_ = run2300(θmat[i], GMEAN2, OMEAN2); lB[i]=dll(d, sd_d[i], rh_d[i]); end
@printf("  ℓ^B done; mean-forcing sanity: ensemble-mean GMST@2018 vs ext-mean not checked here (see weight_* driver)\n")

# ---- configs ----
ohc2018 = Float64[OW2[ty(2018),k]-OW2[ty(1850),k] for k in 1:NCFG_ALL]
cfgs = CFGARG=="all" ? collect(1:NCFG_ALL) :
       (n=parse(Int,CFGARG); sortperm(ohc2018)[round.(Int, range(1, NCFG_ALL, length=n))])
const NCFG = length(cfgs)
@printf("configs: %d (%s)\n", NCFG, CFGARG)

# ---- ℓ^FB + future SLR per (config, draw) ----
println("ℓ^FB + projection: $NCFG configs × $ND draws = $(NCFG*ND) runs to 2300 ...")
lFB = Array{Float64}(undef, ND, NCFG)
FUT = [Array{Float64}(undef, ND, NCFG) for _ in 1:length(LABELS)]   # 8 metrics
for (j,k) in enumerate(cfgs)
    g=GW2[:,k]; o=OW2[:,k]
    for i in 1:ND
        dang, fut, comp = run2300(θmat[i], g, o)
        lFB[i,j] = dll(dang, sd_d[i], rh_d[i])
        for h in 1:4; FUT[h][i,j]=fut[h]; end
        FUT[5][i,j]=comp[1]; FUT[6][i,j]=comp[2]; FUT[7][i,j]=comp[3]; FUT[8][i,j]=comp[4]
    end
    j % 20 == 0 && (print("."); flush(stdout))
end
println()

# ---- conditional weights (per config), c tuned for gentle mean ESS ----
Δ = lFB .- lB
function condw(c)
    W=similar(Δ); for j in 1:NCFG; x=c.*@view Δ[:,j]; w=exp.(x.-maximum(x)); s=sum(w); W[:,j]= s>0 ? w./s : fill(1/ND,ND); end; W
end
essfrac(W)=mean(1.0 ./ (ND .* vec(sum(W.^2,dims=1))))
function tune_c(t); clo,chi=0.0,5.0; while essfrac(condw(chi))>t; chi*=2; chi>1e4&&break; end
    for _ in 1:40; cm=(clo+chi)/2; essfrac(condw(cm))>t ? (clo=cm) : (chi=cm); end; (clo+chi)/2; end
const C = tune_c(ESSTGT); W = condw(C)
@printf("c = %.4g → mean conditional ESS/N = %.3f (target %.2f)\n", C, essfrac(W), ESSTGT)

# ---- bands: COUPLED (w_{i|k}/NCFG) vs INDEPENDENT (equal) ----
function wq(v, w)                              # weighted quantiles 5/50/95
    p=sortperm(v); vs=v[p]; ws=cumsum(w[p])./sum(w); q=Float64[]
    for t in (0.05,0.5,0.95); push!(q, vs[searchsortedfirst(ws,t)]); end; q
end
wc = vec(W) ./ NCFG                            # coupled pair weights (config equal, draws conditional)
wi = fill(1.0/(ND*NCFG), ND*NCFG)              # independent (equal) pair weights
println("\n=== SLR bands  COUPLED vs INDEPENDENT  (median [5,95] cm, rel 1995-2005) ===")
summ = NamedTuple[]
for (h,lab) in enumerate(LABELS)
    v=vec(FUT[h]); qc=wq(v,wc); qi=wq(v,wi)
    @printf("  %-11s COUPLED %7.2f [%7.2f,%8.2f] | INDEP %7.2f [%7.2f,%8.2f] | Δmed %+6.2f Δw95-5 %+6.2f\n",
            lab, qc[2],qc[1],qc[3], qi[2],qi[1],qi[3], qc[2]-qi[2], (qc[3]-qc[1])-(qi[3]-qi[1]))
    push!(summ, (metric=lab, cpl_med=qc[2],cpl_lo=qc[1],cpl_hi=qc[3], ind_med=qi[2],ind_lo=qi[1],ind_hi=qi[3]))
end

# ---- outputs ----
CSV.write(joinpath(REPO,"outputs/mcmc/wong_cond_slr_bands.csv"), DataFrame(summ))
CSV.write(joinpath(REPO,"outputs/mcmc/wong_cond_weights_full.csv"),
          DataFrame(config=repeat(cfgs,inner=ND), draw=repeat(ridx,outer=NCFG), w=vec(W), lFB=vec(lFB), lB=repeat(lB,outer=NCFG)))
@printf("\nwrote outputs/mcmc/wong_cond_slr_bands.csv + wong_cond_weights_full.csv  (c=%.4g, ESS/N=%.3f, %d configs × %d draws)\n",
        C, essfrac(W), NCFG, ND)
