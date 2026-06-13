## ============================================================================
## calibrate_mcmc.jl  —  Bayesian MCMC calibration of BRICK-Mengel (RAM + AR(1))
##
## Promotes the MAP point estimate (calibrate_full_joint.jl) to a full posterior.
## Reuses MimiBRICK's calibration approach: Robust Adaptive Metropolis (RAM_sample)
## + heteroscedastic AR(1) per-component likelihood (Ruckert et al. 2017, reproduced
## from MimiBRICK's hetero_logl_ar1). FaIR-forced BRICK with the 2-timescale Mengel
## glacier. ~28 free params: 18 physical (key DAIS incl. ais_ocean_temperature₀ +
## MICI, anto, GIS, te_α, glacier 2-τ) — the weakly-constrained DAIS shape params are
## FIXED at Tony's posterior median — plus (σ,ρ) AR(1) noise for the 5 fitted series.
##
## Targets (re-ref 1995-2005): Frederikse AIS/GSIC/GIS/Steric 1900-2018 (AR(1)),
## Dangendorf total (+ Frederikse-TWS LWS budget, with LWS uncertainty in the obs
## error), IMBIE ΔAIS(92-17) + Dyurgerov ΔGSIC(61-03) (Gaussian point terms).
##
## Usage (smoke test ~2000 iter local; production = many iter × chains on Torch cs):
##   julia --project=julia_v2 julia/calibrate_mcmc.jl [n_iter] [seed]
## ============================================================================

using CSV, DataFrames, Mimi, MimiBRICK, Statistics, LinearAlgebra, Distributions, Random, Printf
using RobustAdaptiveMetropolisSampler
include(joinpath(@__DIR__, "brick_mengel.jl"))

const REPO = abspath(joinpath(@__DIR__, ".."))
const OBS  = joinpath(REPO, "data/observations")
const Y0, Y1, B0, B1 = 1850, 2018, 1995, 2005
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

# ---- forcing + targets ----
lc(p,c)=(d=CSV.read(p,DataFrame); Dict(Int(d[i,"year"])=>Float64(d[i,c]) for i in 1:nrow(d)))
gmst=[lc(joinpath(OBS,"fair_mean_gmst.csv"),"gmst_C")[y] for y in years]
ohc =[lc(joinpath(OBS,"fair_mean_ohc.csv"),"ohc_1e22J")[y] for y in years]
tg = CSV.read(joinpath(REPO,"outputs/recalib_targets.csv"), DataFrame); tgi(y)=findfirst(==(y),tg.year)
FY = collect(1900:2018); fyi=[tgi(y) for y in FY]; myi=[idx(y) for y in FY]
ϵband(lo,hi)=max.((hi.-lo)./(2*1.645), 0.05)         # per-year obs σ (floor 0.05cm)
obs = (ais=Float64.(tg.ais[fyi]), gsic=Float64.(tg.gsic[fyi]), gis=Float64.(tg.gis[fyi]), steric=Float64.(tg.steric[fyi]),
       dang=Float64.(tg.dang[fyi]), lws=Float64.(tg.lws[fyi]))
ϵ = (ais=ϵband(tg.ais_lo[fyi],tg.ais_hi[fyi]), gsic=ϵband(tg.gsic_lo[fyi],tg.gsic_hi[fyi]),
     gis=ϵband(tg.gis_lo[fyi],tg.gis_hi[fyi]), steric=ϵband(tg.steric_lo[fyi],tg.steric_hi[fyi]),
     # total obs error = Dangendorf σ ⊕ LWS-budget σ (LWS uncertainty)
     dang=sqrt.(Float64.(tg.dang_sig[fyi]).^2 .+ ϵband(tg.lws_lo[fyi],tg.lws_hi[fyi]).^2))
const IMBIE_MU,IMBIE_SIG,DYU_MU,DYU_SIG = 0.72,0.156,2.127,0.148

# ---- free physical params (name, comp, sym, prior μ, σ, lo, hi, islog) ----
pri = CSV.read(joinpath(REPO,"outputs/param_priors.csv"), DataFrame)
prow(n)=pri[findfirst(==(n),pri.param),:]
P(n,c,s;islog=false)=(r=prow(n); (name=n,comp=c,sym=s,μ=r.mean,σ=r.std,lo=r.lo,hi=r.hi,islog=islog))
FREE = NamedTuple[]
# DAIS (key only; weak shape params fixed at medoid): oceanT0 kept, ais_α, MICI, nu
push!(FREE, (name="ais_ocean_temperature₀",comp=:antarctic_icesheet,sym=:ais_ocean_temperature₀,μ=0.72,σ=0.50,lo=0.50,hi=2.00,islog=false))
push!(FREE, P("antarctic_alpha",:antarctic_icesheet,:ais_α))
push!(FREE, P("antarctic_nu",:antarctic_icesheet,:ais_ν))
push!(FREE, P("antarctic_temp_threshold",:antarctic_icesheet,:temperature_threshold))
push!(FREE, P("anto_alpha",:antarctic_ocean,:anto_α)); push!(FREE, P("anto_beta",:antarctic_ocean,:anto_β))
push!(FREE, P("greenland_a",:greenland_icesheet,:greenland_a)); push!(FREE, P("greenland_b",:greenland_icesheet,:greenland_b))
push!(FREE, P("greenland_alpha",:greenland_icesheet,:greenland_α)); push!(FREE, P("greenland_beta",:greenland_icesheet,:greenland_β))
push!(FREE, P("greenland_v0",:greenland_icesheet,:greenland_v₀)); push!(FREE, P("thermal_alpha",:thermal_expansion,:te_α))
# Mengel 2-τ glacier (physical priors)
G=:glaciers_small_icecaps
push!(FREE, (name="gic_a",comp=G,sym=:gic_a,μ=0.45,σ=0.08,lo=0.32,hi=0.55,islog=false))
push!(FREE, (name="gic_b",comp=G,sym=:gic_b,μ=0.52,σ=0.25,lo=0.25,hi=1.00,islog=false))
push!(FREE, (name="gic_T_lia",comp=G,sym=:gic_T_lia,μ=-0.45,σ=0.30,lo=-1.00,hi=-0.10,islog=false))
push!(FREE, (name="gic_f",comp=G,sym=:gic_f,μ=0.50,σ=0.30,lo=0.02,hi=0.98,islog=false))
push!(FREE, (name="gic_tau_fast",comp=G,sym=:gic_tau_fast,μ=40.,σ=30.,lo=5.,hi=80.,islog=false))
push!(FREE, (name="gic_tau_slow",comp=G,sym=:gic_tau_slow,μ=300.,σ=200.,lo=80.,hi=800.,islog=false))
const NP = length(FREE)
# AR(1) noise (σ,ρ) per fitted series; weak priors (σ>0 half-normal-ish, ρ∈[0,0.99])
const SERIES = [:ais,:gsic,:gis,:steric,:dang]
const NN = 2*length(SERIES)
const NK = NP + NN
println("MCMC: $NP physical + $NN AR(1)-noise = $NK free params")

# ---- model base (medoid + glacier init), forcing once ----
medoid = CSV.read(joinpath(REPO,"outputs/recalib_central_row.csv"), DataFrame)[1,:]
m = build_brick_mengel(ssp="ssp245", y0=Y0, y1=Y1)
update_brick_mengel!(m, medoid, (a=0.45,b=0.52,T_lia=-0.45,f=0.5,tau_fast=40.0,tau_slow=250.0,sl0=0.0); precip_log=true)
set_forcing!(m, gmst, ohc)
setp!(k,v)=update_param!(m,k.comp,k.sym, k.islog ? log(v) : v)
reref(v)=100 .* (v .- sum(v[ib])/length(ib))

function logposterior(θ)
    # bounds
    @inbounds for k in 1:NP; (θ[k]<FREE[k].lo || θ[k]>FREE[k].hi) && return -Inf; end
    σn = θ[NP+1:2:NK]; ρn = θ[NP+2:2:NK]
    (any(σn .<= 0) || any(ρn .< 0) || any(ρn .>= 0.99)) && return -Inf
    @inbounds for k in 1:NP; setp!(FREE[k], θ[k]); end
    run(m)
    ais=reref(m[:antarctic_icesheet,:ais_sea_level])[myi]; gsic=reref(m[:glaciers_small_icecaps,:gsic_sea_level])[myi]
    gis=reref(m[:greenland_icesheet,:greenland_sea_level])[myi]; te=reref(m[:thermal_expansion,:te_sea_level])[myi]
    tot = ais .+ gsic .+ gis .+ te .+ obs.lws
    ll = 0.0
    for (i,(mod,ob,ev)) in enumerate([(ais,obs.ais,ϵ.ais),(gsic,obs.gsic,ϵ.gsic),(gis,obs.gis,ϵ.gis),
                                      (te,obs.steric,ϵ.steric),(tot,obs.dang,ϵ.dang)])
        ll += hetero_logl_ar1(mod .- ob, σn[i], ρn[i], ev)
    end
    # modern-rate point terms
    full_ais=reref(m[:antarctic_icesheet,:ais_sea_level]); full_g=reref(m[:glaciers_small_icecaps,:gsic_sea_level])
    ll += logpdf(Normal(IMBIE_MU,IMBIE_SIG), full_ais[idx(2017)]-full_ais[idx(1992)])
    ll += logpdf(Normal(DYU_MU,DYU_SIG),     full_g[idx(2003)]-full_g[idx(1961)])
    # priors: Gaussian on physical, weak on AR(1) noise
    lp = 0.0
    @inbounds for k in 1:NP; lp += logpdf(Normal(FREE[k].μ, FREE[k].σ), θ[k]); end
    for i in 1:length(SERIES); lp += logpdf(truncated(Normal(0,5),0,Inf), σn[i]); end   # σ>0 weak
    return ll + lp
end

# ---- start point: MAP physical + noise inits; smoke-test RAM ----
mapp = CSV.read(joinpath(REPO,"outputs/calib_full_joint_params.csv"), DataFrame)
θ0 = Float64[]
for k in 1:NP
    j = findfirst(==(FREE[k].name), mapp.param)
    push!(θ0, isnothing(j) ? FREE[k].μ : mapp.MAP[j])
end
append!(θ0, repeat([1.0, 0.5], length(SERIES)))         # σ=1cm, ρ=0.5 inits
# initial proposal scaled to each param's prior σ (physical) / fixed steps (noise);
# RAM then adapts the full covariance toward opt_α=0.234.
prop = vcat([0.1*Float64(k.σ) for k in FREE], repeat([0.3, 0.1], length(SERIES)))
cov0 = Diagonal(prop.^2)
println("logpost(θ0) = ", round(logposterior(θ0), digits=2), "  (start = MAP)")

Random.seed!(SEED)
@time chain, accept, covout, lp = RAM_sample(logposterior, θ0, Matrix(cov0), N_ITER; opt_α=0.234, output_log_probability_x=true)
println("RAM smoke test: $N_ITER iter, acceptance = ", round(accept, digits=3))
pn = vcat([k.name for k in FREE], vcat([["sd_$s","rho_$s"] for s in SERIES]...))
burn = chain[(N_ITER÷2+1):end, :]
println("\nposterior (2nd-half) median ± sd for key params:")
for nm in ["ais_ocean_temperature₀","anto_alpha","gic_T_lia","gic_f","gic_tau_fast","gic_tau_slow","gic_a"]
    c = burn[:, findfirst(==(nm),pn)]
    @printf("  %-24s %.3g ± %.2g\n", nm, median(c), std(c))
end
# per-chain output (production: one file per seed; combine + diagnose in postprocess)
mkpath(joinpath(REPO,"outputs/mcmc"))
df = DataFrame(chain, pn); df.log_post = lp; df.accept_rate = fill(accept, nrow(df))
CSV.write(joinpath(REPO,"outputs/mcmc/chain_seed$(SEED)_n$(N_ITER).csv"), df)
println("\nWrote outputs/mcmc/chain_seed$(SEED)_n$(N_ITER).csv  (accept $(round(accept,digits=3)))")
println("OK if acceptance ~0.1-0.4 and key params sane. Production = large N_ITER × ≥4 seeds on Torch cs,")
println("then postprocess_mcmc.jl (R̂/ESS, combine, subsample -> parameters_subsample_brick_mengel.csv).")
