## ============================================================================
## calibrate_mcmc_joint_cont.jl — CONTINUOUS joint FaIR/BRICK calibration
##
## ‼ STATUS 2026-08-01: DIAGNOSTIC / REJECTED FOR PRODUCTION — see
## notes/negresult_2026-08-01_joint_forcing_calibration.md. The joint free-forcing approach was tested
## and rejected: the SLR likelihood RE-INFERS the forcing (bends GMST ~0.28°C cool @2100 via fpc1, the
## ECS/atmosphere mode) — SLR must not do that — and the te_α↔OHC coupling it recovers is immaterial to
## the total-SLR bands (shuffle test −0.55 cm @2100). Canonical BRICK-AM = mean-forcing calibrate_mcmc_ext.jl
## + forward-propagated FaIR uncertainty. Kept only as the diagnostic that established this.
##
## Supersedes the discrete-index calibrate_mcmc_joint.jl (whose single-site MH z-step mixed
## poorly — the θ↔z coupling made the SLR likelihood too peaked in z at fixed θ). Here the FaIR
## forcing dimension is CONTINUOUS: NPC=3 principal-component scores over the 841-member ensemble
## (outputs/forcing_pca_basis.csv + forcing_pca_meta.csv, from python/precompute_forcing_pca).
## GMST(t) = gmean(t) + gs·Σ_k a_k·Gload[k,t];  OHC(t) = omean(t) + os·Σ_k a_k·Oload[k,t].
## The scores a_k are sampled JOINTLY with θ_BRICK in ONE RAM, so RAM adapts the joint covariance
## and proposes ALONG the te_α↔OHC ridge — which single-site MH on z could not. a=0 => ensemble-mean
## forcing (≈ fair_mean). PC2/PC3 carry the historical-OHC coupling (constrained by the fit); PC1 is
## future/ECS-dominated (barely touched by 1850-2026 data → samples its prior → projection spread).
## See notes/design_2026-07-24_index_augmented_joint_calibration_torch.md §3.
##
## The BRICK setup (priors/FREE/θ0/cov0/--overdisperse/--amp-*) is IDENTICAL to calibrate_mcmc_ext.jl.
## Modes:
##   --recover   dim NK, forcing=fair_mean (a excluded) → BIT-IDENTICAL to calibrate_mcmc_ext.jl.
##   (default)   dim NK+NPC, forcing reconstructed from a; single RAM over (θ_BRICK, a).
##
## Usage:
##   julia --project=julia_v2 julia/calibrate_mcmc_joint_cont.jl 5000 2026 --recover           # sanity
##   julia --project=julia_v2 julia/calibrate_mcmc_joint_cont.jl 5000 2026 --amp-mu=1.08 --amp-sigma=0.15
## ============================================================================
using CSV, DataFrames, Mimi, MimiBRICK, Statistics, LinearAlgebra, Distributions, Random, Printf
using RobustAdaptiveMetropolisSampler
include(joinpath(@__DIR__, "brick_mengel.jl"))

const REPO = abspath(joinpath(@__DIR__, ".."))
const OBS  = joinpath(REPO, "data/observations")
const Y0, Y1, B0, B1 = 1850, 2026, 1995, 2005
const TARGETS = joinpath(REPO, "outputs/recalib_targets_ext.csv")
const AMP_EQ = "--amp-equilibrium" in ARGS
_argval(pfx) = (i = findfirst(a -> startswith(a, pfx), ARGS); i === nothing ? nothing : ARGS[i][length(pfx)+1:end])
const AMP_MU_OVR=_argval("--amp-mu="); const AMP_SIGMA_OVR=_argval("--amp-sigma="); const TAG_OVR=_argval("--tag=")
const RECOVER = "--recover" in ARGS
const TAG = TAG_OVR !== nothing ? TAG_OVR : (RECOVER ? "jcontrec" : (AMP_EQ ? "jcontA6eq" : "jcont"))
years = collect(Y0:Y1); ib = [findfirst(==(y),years) for y in B0:B1]; idx(y)=findfirst(==(y),years)
N_ITER = length(ARGS)>=1 && !startswith(ARGS[1],"--") ? parse(Int,ARGS[1]) : 2000
SEED   = length(ARGS)>=2 && !startswith(ARGS[2],"--") ? parse(Int,ARGS[2]) : 2026

function hetero_logl_ar1(res::Vector{Float64}, σ::Float64, ρ::Float64, ϵ::Vector{Float64})
    n=length(res); σp=σ^2/(1-ρ^2); H=abs.(collect(1:n)' .- collect(1:n)); Σ=σp.*ρ.^H .+ Diagonal(ϵ.^2)
    return logpdf(MvNormal(Symmetric(Σ)), res)
end
lc(p,c)=(d=CSV.read(p,DataFrame); Dict(Int(d[i,"year"])=>Float64(d[i,c]) for i in 1:nrow(d)))
const FORCING_TAG = "ssp245harm"
gmst=[lc(joinpath(OBS,"fair_mean_gmst_$(FORCING_TAG).csv"),"gmst_C")[y] for y in years]
ohc =[lc(joinpath(OBS,"fair_mean_ohc_$(FORCING_TAG).csv"),"ohc_1e22J")[y] for y in years]

# ---- CONTINUOUS forcing basis: NPC PC scores reconstruct GMST/OHC over the fit window ----
const PCB = CSV.read(joinpath(REPO,"outputs/forcing_pca_basis.csv"), DataFrame)
const PCM = CSV.read(joinpath(REPO,"outputs/forcing_pca_meta.csv"),  DataFrame)
const NPC = nrow(PCM)
_pk = [findfirst(==(y), PCB.year) for y in years]
const GMEAN = Float64.(PCB.gmean[_pk]); const OMEAN = Float64.(PCB.omean[_pk])
const GLOAD = [Float64.(PCB[_pk, Symbol("Gload$k")]) for k in 1:NPC]
const OLOAD = [Float64.(PCB[_pk, Symbol("Oload$k")]) for k in 1:NPC]
const GS = PCM.gs[1]; const OS = PCM.os[1]
const ASTD = Float64.(PCM.sstd); const ALO = Float64.(PCM.amin); const AHI = Float64.(PCM.amax)
reconstruct(a) = (g = copy(GMEAN); o = copy(OMEAN);
    @inbounds for k in 1:NPC; g .+= (GS*a[k]).*GLOAD[k]; o .+= (OS*a[k]).*OLOAD[k]; end; (g, o))
if !RECOVER
    let (g0,o0)=reconstruct(zeros(NPC))
        @printf("forcing: %d-PC continuous. a=0 vs fair_mean: max|ΔGMST| %.3g C, max|ΔOHC| %.3g (10^22J)\n",
                NPC, maximum(abs.(g0.-gmst)), maximum(abs.(o0.-ohc)))
    end
else
    println("forcing: fair_mean (RECOVERY, a excluded → bit-identical to calibrate_mcmc_ext.jl)")
end

tg = CSV.read(TARGETS, DataFrame); ϵband(lo,hi)=max.((hi.-lo)./(2*1.645), 0.05)
function series_years(col); ys=Int[]; for i in 1:nrow(tg); v=tg[i,col];
    (tg.year[i]>=1900 && !ismissing(v) && !isnan(Float64(v))) && push!(ys,Int(tg.year[i])); end; sort(ys); end
rowof(y)=findfirst(==(y),tg.year)
function make_series(col,lo,hi;isdang=false)
    fy=series_years(col); @assert fy==collect(fy[1]:fy[end]); ri=[rowof(y) for y in fy]; ob=Float64.(tg[ri,col])
    ev=isdang ? sqrt.(Float64.(tg.dang_sig[ri]).^2 .+ ϵband(Float64.(tg.lws_lo[ri]),Float64.(tg.lws_hi[ri])).^2) : ϵband(Float64.(tg[ri,lo]),Float64.(tg[ri,hi]))
    (years=fy,myi=[idx(y) for y in fy],obs=ob,ϵ=ev)
end
S=(ais=make_series(:ais,:ais_lo,:ais_hi),gsic=make_series(:gsic,:gsic_lo,:gsic_hi),gis=make_series(:gis,:gis_lo,:gis_hi),
   steric=make_series(:steric,:steric_lo,:steric_hi),dang=make_series(:dang,:dang_lo,:dang_hi;isdang=true))
lws_dang=Float64.(tg.lws[[rowof(y) for y in S.dang.years]])

pri=CSV.read(joinpath(REPO,"outputs/param_priors.csv"),DataFrame); prow(n)=pri[findfirst(==(n),pri.param),:]
P(n,c,s;islog=false)=(r=prow(n); (name=n,comp=c,sym=s,μ=r.mean,σ=r.std,lo=r.lo,hi=r.hi,islog=islog))
FREE=NamedTuple[]
push!(FREE,(name="ais_ocean_temperature₀",comp=:antarctic_icesheet,sym=:ais_ocean_temperature₀,μ=0.72,σ=0.50,lo=0.50,hi=2.00,islog=false))
push!(FREE,P("antarctic_alpha",:antarctic_icesheet,:ais_α)); push!(FREE,P("antarctic_nu",:antarctic_icesheet,:ais_ν))
push!(FREE,P("antarctic_temp_threshold",:antarctic_icesheet,:temperature_threshold))
push!(FREE,P("anto_alpha",:antarctic_ocean,:anto_α)); push!(FREE,P("anto_beta",:antarctic_ocean,:anto_β))
push!(FREE,P("greenland_a",:greenland_icesheet,:greenland_a)); push!(FREE,P("greenland_b",:greenland_icesheet,:greenland_b))
push!(FREE,P("greenland_alpha",:greenland_icesheet,:greenland_α)); push!(FREE,P("greenland_beta",:greenland_icesheet,:greenland_β))
push!(FREE,P("greenland_v0",:greenland_icesheet,:greenland_v₀)); push!(FREE,P("thermal_alpha",:thermal_expansion,:te_α))
G=:glaciers_small_icecaps
push!(FREE,(name="gic_a",comp=G,sym=:gic_a,μ=0.45,σ=0.08,lo=0.32,hi=0.55,islog=false))
push!(FREE,(name="gic_b",comp=G,sym=:gic_b,μ=0.52,σ=0.25,lo=0.25,hi=1.00,islog=false))
push!(FREE,(name="gic_T_lia",comp=G,sym=:gic_T_lia,μ=-0.45,σ=0.30,lo=-1.00,hi=-0.10,islog=false))
push!(FREE,(name="gic_f",comp=G,sym=:gic_f,μ=0.50,σ=0.30,lo=0.02,hi=0.98,islog=false))
push!(FREE,(name="gic_tau_fast",comp=G,sym=:gic_tau_fast,μ=40.,σ=30.,lo=5.,hi=80.,islog=false))
push!(FREE,(name="gic_tau_slow",comp=G,sym=:gic_tau_slow,μ=300.,σ=200.,lo=80.,hi=800.,islog=false))
push!(FREE,P("antarctic_lambda",:antarctic_icesheet,:λ)); push!(FREE,P("antarctic_gamma",:antarctic_icesheet,:ais_γ)); push!(FREE,P("antarctic_kappa",:antarctic_icesheet,:ais_κ))
const AMP_MU    = AMP_MU_OVR!==nothing ? parse(Float64,AMP_MU_OVR) : (AMP_EQ ? 1.0/0.8365 : 0.95)
const AMP_SIGMA = AMP_SIGMA_OVR!==nothing ? parse(Float64,AMP_SIGMA_OVR) : (AMP_EQ ? 0.002 : 0.10)
const AMP_LO=AMP_MU_OVR===nothing ? 0.70 : AMP_MU-3*AMP_SIGMA; const AMP_HI=AMP_MU_OVR===nothing ? 1.25 : AMP_MU+3*AMP_SIGMA
const AIS_TANT0=-15.42/0.8365
push!(FREE,(name="ais_gmst_amp",comp=:antarctic_icesheet,sym=:ais_temperature_coefficient,μ=AMP_MU,σ=AMP_SIGMA,lo=AMP_LO,hi=AMP_HI,islog=false))
const AMP_IDX=length(FREE)
const GEO_FILE=joinpath(REPO,"outputs/paleo_geo_prior_ton.csv")
const GEO_NAMES=["ais_mu","ais_bedheight0","ais_slope","ais_iceflow0","ais_precip0_LOG","ais_runoff_Ton","ais_c"]
const GEO_SYMS=[:ais_μ,:ais_bedheight₀,:ais_slope,:ais_iceflow₀,:ais_precipitation₀,:ais_runoffline_snowheight₀,:ais_c]
_gl=[split(strip(l),',') for l in readlines(GEO_FILE) if !startswith(l,"#") && !isempty(strip(l))]
_grow(t)=[parse(Float64,x) for x in first(l for l in _gl if l[1]==t)[2:end]]
const GEO_MU=_grow("mean"); const GEO_SD=_grow("sd")
const GEO_C=Symmetric(permutedims(reduce(hcat,[[parse(Float64,x) for x in l[2:end]] for l in _gl if l[1]=="corr"])))
let glo=_grow("lo"),ghi=_grow("hi"); for i in eachindex(GEO_SYMS)
    push!(FREE,(name=GEO_NAMES[i],comp=:antarctic_icesheet,sym=GEO_SYMS[i],μ=GEO_MU[i],σ=GEO_SD[i],lo=glo[i],hi=ghi[i],islog=false)); end; end
const GEO_IDX=(length(FREE)-length(GEO_SYMS)+1):length(FREE)
const GEO_PRIOR=MvNormal(zeros(length(GEO_SYMS)),Matrix(GEO_C))
const TON_IDX=GEO_IDX[findfirst(==("ais_runoff_Ton"),GEO_NAMES)]; const C_IDX=GEO_IDX[findfirst(==("ais_c"),GEO_NAMES)]
const SMB_Y0,SMB_Y1=1979,2008; const SMB_IDX=[idx(y) for y in SMB_Y0:SMB_Y1]
const SMB_TARGET_GT=2098.0*(10.92/12.295); const SMB_SIGMA_GT=133.0*(10.92/12.295); const M3ICE_TO_GT=917.0/1e12
const NP=length(FREE); const SERIES=[:ais,:gsic,:gis,:steric,:dang]; const NN=2*length(SERIES); const NK=NP+NN
const USE_FPC = !RECOVER
const NFULL = USE_FPC ? NK+NPC : NK
const FPC_IDX = NK+1:NK+NPC
const pn0 = vcat([k.name for k in FREE], vcat([["sd_$s","rho_$s"] for s in SERIES]...), USE_FPC ? ["fpc$k" for k in 1:NPC] : String[])
@printf("A6 prior: amp ~ N(%.3f, %.3f)  TAG=%s | dim %d = %d BRICK%s\n", AMP_MU,AMP_SIGMA,TAG,NFULL,NK, USE_FPC ? " + $NPC forcing PCs" : "")

medoid=CSV.read(joinpath(REPO,"outputs/recalib_central_row.csv"),DataFrame)[1,:]
m=build_brick_mengel(ssp="ssp245",y0=Y0,y1=Y1)
update_brick_mengel!(m,medoid,(a=0.45,b=0.52,T_lia=-0.45,f=0.5,tau_fast=40.0,tau_slow=250.0,sl0=0.0);precip_log=true)
set_forcing!(m,gmst,ohc)
setp!(k,v)=update_param!(m,k.comp,k.sym,k.islog ? log(v) : v); reref(v)=100 .*(v .- sum(v[ib])/length(ib))

function logposterior(θ)
    @inbounds for k in 1:NP; (θ[k]<FREE[k].lo || θ[k]>FREE[k].hi) && return -Inf; end
    σn=θ[NP+1:2:NK]; ρn=θ[NP+2:2:NK]
    (any(σn.<=0)||any(ρn.<0)||any(ρn.>=0.99)) && return -Inf
    if USE_FPC
        a=@view θ[FPC_IDX]
        @inbounds for k in 1:NPC; (a[k]<ALO[k]||a[k]>AHI[k]) && return -Inf; end
        g,o = reconstruct(a); set_forcing!(m,g,o)
    end
    @inbounds for k in 1:NP; (k==AMP_IDX||k==TON_IDX) && continue; setp!(FREE[k],θ[k]); end
    update_param!(m,:antarctic_icesheet,:ais_runoffline_snowheight₀,-θ[TON_IDX]*θ[C_IDX])
    update_param!(m,:antarctic_icesheet,:ais_temperature_coefficient,1.0/θ[AMP_IDX])
    update_param!(m,:antarctic_icesheet,:ais_temperature_intercept,-AIS_TANT0/θ[AMP_IDX])
    run(m)
    ais=reref(m[:antarctic_icesheet,:ais_sea_level]); gsic=reref(m[:glaciers_small_icecaps,:gsic_sea_level])
    gis=reref(m[:greenland_icesheet,:greenland_sea_level]); te=reref(m[:thermal_expansion,:te_sea_level])
    tot_full=ais.+gsic.+gis.+te; ll=0.0
    for (i,(s,full)) in enumerate(zip([S.ais,S.gsic,S.gis,S.steric],[ais,gsic,gis,te])); ll+=hetero_logl_ar1(full[s.myi].-s.obs,σn[i],ρn[i],s.ϵ); end
    ll+=hetero_logl_ar1(tot_full[S.dang.myi].+lws_dang.-S.dang.obs,σn[5],ρn[5],S.dang.ϵ)
    smb_gt=mean(m[:antarctic_icesheet,:β_total][SMB_IDX])*M3ICE_TO_GT; ll+=logpdf(Normal(SMB_TARGET_GT,SMB_SIGMA_GT),smb_gt)
    lp=0.0
    @inbounds for k in 1:NP; k in GEO_IDX && continue; lp+=logpdf(Normal(FREE[k].μ,FREE[k].σ),θ[k]); end
    lp+=logpdf(GEO_PRIOR,(θ[GEO_IDX].-GEO_MU)./GEO_SD)
    for i in 1:length(SERIES); lp+=logpdf(truncated(Normal(0,5),0,Inf),σn[i]); end
    USE_FPC && (@inbounds for k in 1:NPC; lp+=logpdf(Normal(0.0,ASTD[k]),θ[FPC_IDX[k]]); end)   # forcing-score prior = ensemble
    return ll+lp
end

# ---- θ0 + cov0 (BRICK block IDENTICAL to ext; forcing scores appended) ----
mapp=CSV.read(joinpath(REPO,"outputs/calib_full_joint_params.csv"),DataFrame)
const GEO_MEDOID_COL=Dict("ais_mu"=>"antarctic_mu","ais_bedheight0"=>"antarctic_bed_height0","ais_slope"=>"antarctic_slope","ais_iceflow0"=>"antarctic_flow0","ais_precip0_LOG"=>"antarctic_precip0","ais_c"=>"antarctic_c")
const FD_MEDOID=("antarctic_lambda","antarctic_gamma","antarctic_kappa")
θ0=Float64[]
for k in 1:NP
    nm=FREE[k].name
    if k in GEO_IDX
        nm=="ais_runoff_Ton" ? push!(θ0,-Float64(medoid["antarctic_runoff_height0"])/Float64(medoid["antarctic_c"])) :
            (v=Float64(medoid[GEO_MEDOID_COL[nm]]); push!(θ0, nm=="ais_precip0_LOG" ? log(v) : v))
    elseif nm in FD_MEDOID; push!(θ0,Float64(medoid[nm]))
    elseif nm=="ais_gmst_amp"; push!(θ0,1.0/0.8365)
    else j=findfirst(==(nm),mapp.param); push!(θ0,isnothing(j) ? FREE[k].μ : mapp.MAP[j]); end
end
append!(θ0,repeat([1.0,0.5],length(SERIES)))
USE_FPC && append!(θ0, zeros(NPC))                                   # forcing scores start at ensemble mean
prop=vcat([0.1*Float64(k.σ) for k in FREE],repeat([0.3,0.1],length(SERIES)))
const GEO_PROP_SCALE=0.02; for k in GEO_IDX; prop[k]=GEO_PROP_SCALE*Float64(FREE[k].σ); end
USE_FPC && append!(prop, 0.1.*ASTD)                                  # forcing-score proposal: 0.1×prior sd
const ADCOV=let e=joinpath(REPO,"outputs/mcmc/adapted_cov_ext.csv"),b=joinpath(REPO,"outputs/mcmc/adapted_cov.csv"); isfile(e) ? e : b end
cov0=Matrix(Diagonal(prop.^2))
const OLD35_NAMES=vcat(["ais_ocean_temperature₀","antarctic_alpha","antarctic_nu","antarctic_temp_threshold","anto_alpha","anto_beta","greenland_a","greenland_b","greenland_alpha","greenland_beta","greenland_v0","thermal_alpha","gic_a","gic_b","gic_T_lia","gic_f","gic_tau_fast","gic_tau_slow","ais_mu","ais_bedheight0","ais_slope","ais_iceflow0","ais_precip0_LOG","ais_runoff_h0","ais_c"],vcat([["sd_$s","rho_$s"] for s in SERIES]...))
if isfile(ADCOV)
    old=Matrix(CSV.read(ADCOV,DataFrame))
    if size(old,1)==NK; cov0[1:NK,1:NK]=old; println("(seeding BRICK block from $(basename(ADCOV)))")
    elseif size(old,1)==length(OLD35_NAMES)
        oi=Int[];ni=Int[]; for (i,nm) in enumerate(OLD35_NAMES); j=findfirst(==(nm),pn0); isnothing(j)&&continue; push!(oi,i);push!(ni,j); end
        cov0[ni,ni]=old[oi,oi]; println("(seeding proposal: name-mapped $(length(oi)) rows of $(basename(ADCOV)))")
    end
end
isposdef(cov0)||error("seed proposal covariance is not positive definite")

const OVERDISPERSE="--overdisperse" in ARGS
if OVERDISPERSE
    SF=joinpath(REPO,"outputs/mcmc/overdispersed_starts.csv"); isfile(SF)||error("--overdisperse needs $SF")
    st=CSV.read(SF,DataFrame); si=findfirst(==(SEED),[2026,2027,2028,2029]); (isnothing(si)||nrow(st)<si)&&error("no start row for seed $SEED")
    missing_cols=[nm for nm in pn0[1:NK] if !hasproperty(st,Symbol(nm))]; isempty(missing_cols)||error("--overdisperse: $SF missing BRICK columns")
    for (k,nm) in enumerate(pn0[1:NK]); θ0[k]=Float64(st[si,Symbol(nm)]); end
    AMP_EQ && (θ0[AMP_IDX]=AMP_MU)
    isfinite(logposterior(θ0))||error("--overdisperse: start has non-finite logposterior")
end

# Guard the sampling+output so this file can be `include`d for its setup (FREE list, param-apply
# logic, forcing basis) by downstream scripts — e.g. project_slr_joint_cont.jl — WITHOUT running the
# 4M-iter chain. Behaviour when run directly as a script is unchanged (PROGRAM_FILE == this file).
if abspath(PROGRAM_FILE) == @__FILE__
Random.seed!(SEED); mkpath(joinpath(REPO,"outputs/mcmc"))
@time chain, accept, covout, lp = RAM_sample(logposterior, θ0, cov0, N_ITER; opt_α=0.234, output_log_probability_x=true)
CSV.write(joinpath(REPO,"outputs/mcmc/adapted_cov_$(TAG)_seed$(SEED).csv"), DataFrame(covout, :auto))
df=DataFrame(chain,pn0); df.log_post=lp; df.accept_rate=fill(accept,nrow(df))
CSV.write(joinpath(REPO,"outputs/mcmc/chain_$(TAG)_seed$(SEED)_n$(N_ITER).csv"), df)
@printf("%s: %d iter, acceptance = %.3f\n", RECOVER ? "RECOVERY" : "JCONT", N_ITER, accept)
if USE_FPC
    burn=chain[(N_ITER÷2+1):end,:]
    for k in 1:NPC; c=burn[:,NK+k]; @printf("  fpc%d posterior: %.2f ± %.2f  (prior sd %.2f)\n",k,median(c),std(c),ASTD[k]); end
    te=burn[:,findfirst(==("thermal_alpha"),pn0)]
    @printf("  corr(te_α, fpc2) = %+.2f, corr(te_α, fpc3) = %+.2f  (expect <0: te_α↔OHC coupling)\n",
            cor(te,burn[:,NK+2]), cor(te,burn[:,NK+3]))
end
println("Wrote outputs/mcmc/chain_$(TAG)_seed$(SEED)_n$(N_ITER).csv")
end
