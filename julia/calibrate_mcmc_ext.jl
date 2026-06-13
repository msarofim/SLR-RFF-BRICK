## ============================================================================
## calibrate_mcmc_ext.jl  —  BRICK-Mengel MCMC on the EXTENDED (post-2018) targets
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
##   2. Model run window extended Y1 1850->2026 (forcing fair_mean_*.csv already
##      reaches 2301, so the SAME forcing is used -- only the window changes).
##   3. PER-SERIES fit windows: each component fit to its own valid (non-missing)
##      year range -> the AR(1) likelihood gets a different-length residual vector
##      per series. (All series are contiguous 1900..end, asserted below.)
##   4. DROPS the IMBIE dAIS(92-17) + Dyurgerov dGSIC(61-03) Gaussian point terms:
##      the extended AIS/GSIC time-series now constrain the modern rate directly
##      (Marcus 2026-06-13 -- avoids double-weighting; see prep README).
##
## Forcing, params, priors, medoid, AR(1) likelihood, proposal-cov seed: IDENTICAL.
##
## Usage:  julia --project=julia_v2 julia/calibrate_mcmc_ext.jl [n_iter] [seed]
## ============================================================================

using CSV, DataFrames, Mimi, MimiBRICK, Statistics, LinearAlgebra, Distributions, Random, Printf
using RobustAdaptiveMetropolisSampler
include(joinpath(@__DIR__, "brick_mengel.jl"))

const REPO = abspath(joinpath(@__DIR__, ".."))
const OBS  = joinpath(REPO, "data/observations")
const Y0, Y1, B0, B1 = 1850, 2026, 1995, 2005          # Y1 1850->2026 (was 2018)
const TARGETS = joinpath(REPO, "outputs/recalib_targets_ext.csv")
const TAG = "ext"                                      # output infix
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
gmst=[lc(joinpath(OBS,"fair_mean_gmst.csv"),"gmst_C")[y] for y in years]
ohc =[lc(joinpath(OBS,"fair_mean_ohc.csv"),"ohc_1e22J")[y] for y in years]
tg = CSV.read(TARGETS, DataFrame)
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
push!(FREE, (name="gic_a",comp=G,sym=:gic_a,μ=0.45,σ=0.08,lo=0.32,hi=0.55,islog=false))
push!(FREE, (name="gic_b",comp=G,sym=:gic_b,μ=0.52,σ=0.25,lo=0.25,hi=1.00,islog=false))
push!(FREE, (name="gic_T_lia",comp=G,sym=:gic_T_lia,μ=-0.45,σ=0.30,lo=-1.00,hi=-0.10,islog=false))
push!(FREE, (name="gic_f",comp=G,sym=:gic_f,μ=0.50,σ=0.30,lo=0.02,hi=0.98,islog=false))
push!(FREE, (name="gic_tau_fast",comp=G,sym=:gic_tau_fast,μ=40.,σ=30.,lo=5.,hi=80.,islog=false))
push!(FREE, (name="gic_tau_slow",comp=G,sym=:gic_tau_slow,μ=300.,σ=200.,lo=80.,hi=800.,islog=false))
const NP = length(FREE)
const SERIES = [:ais,:gsic,:gis,:steric,:dang]
const NN = 2*length(SERIES); const NK = NP + NN
println("MCMC: $NP physical + $NN AR(1)-noise = $NK free params  (point terms DROPPED)")

# ---- model base (medoid + glacier init), forcing once -- UNCHANGED build/medoid ----
medoid = CSV.read(joinpath(REPO,"outputs/recalib_central_row.csv"), DataFrame)[1,:]
m = build_brick_mengel(ssp="ssp245", y0=Y0, y1=Y1)
update_brick_mengel!(m, medoid, (a=0.45,b=0.52,T_lia=-0.45,f=0.5,tau_fast=40.0,tau_slow=250.0,sl0=0.0); precip_log=true)
set_forcing!(m, gmst, ohc)
setp!(k,v)=update_param!(m,k.comp,k.sym, k.islog ? log(v) : v)
reref(v)=100 .* (v .- sum(v[ib])/length(ib))

function logposterior(θ)
    @inbounds for k in 1:NP; (θ[k]<FREE[k].lo || θ[k]>FREE[k].hi) && return -Inf; end
    σn = θ[NP+1:2:NK]; ρn = θ[NP+2:2:NK]
    (any(σn .<= 0) || any(ρn .< 0) || any(ρn .>= 0.99)) && return -Inf
    @inbounds for k in 1:NP; setp!(FREE[k], θ[k]); end
    run(m)
    ais=reref(m[:antarctic_icesheet,:ais_sea_level]); gsic=reref(m[:glaciers_small_icecaps,:gsic_sea_level])
    gis=reref(m[:greenland_icesheet,:greenland_sea_level]); te=reref(m[:thermal_expansion,:te_sea_level])
    tot_full = ais .+ gsic .+ gis .+ te                  # +LWS added per dang-year below
    ll = 0.0
    # individual components on their own (possibly extended) windows
    for (i,(s,full)) in enumerate(zip([S.ais,S.gsic,S.gis,S.steric], [ais,gsic,gis,te]))
        ll += hetero_logl_ar1(full[s.myi] .- s.obs, σn[i], ρn[i], s.ϵ)
    end
    # total (Dangendorf+altimetry): modeled ice+steric at dang years + observed LWS
    ll += hetero_logl_ar1(tot_full[S.dang.myi] .+ lws_dang .- S.dang.obs, σn[5], ρn[5], S.dang.ϵ)
    # priors: Gaussian on physical, weak half-normal on AR(1) σ
    lp = 0.0
    @inbounds for k in 1:NP; lp += logpdf(Normal(FREE[k].μ, FREE[k].σ), θ[k]); end
    for i in 1:length(SERIES); lp += logpdf(truncated(Normal(0,5),0,Inf), σn[i]); end
    return ll + lp
end

# ---- start point: MAP physical + noise inits -- UNCHANGED ----
mapp = CSV.read(joinpath(REPO,"outputs/calib_full_joint_params.csv"), DataFrame)
θ0 = Float64[]
for k in 1:NP
    j = findfirst(==(FREE[k].name), mapp.param)
    push!(θ0, isnothing(j) ? FREE[k].μ : mapp.MAP[j])
end
append!(θ0, repeat([1.0, 0.5], length(SERIES)))
prop = vcat([0.1*Float64(k.σ) for k in FREE], repeat([0.3, 0.1], length(SERIES)))
# proposal seed: PREFER the ext-tuned covariance (adapted_cov_ext.csv, written by
# postprocess_mcmc_ext.jl from a prior ext run) -- it matches the extended posterior
# shape, which the 2018-baseline adapted_cov.csv does NOT (point terms dropped +
# extended targets move the AIS block). Fall back to baseline cov, then diagonal.
const ADCOV = let e = joinpath(REPO,"outputs/mcmc/adapted_cov_ext.csv"),
                  b = joinpath(REPO,"outputs/mcmc/adapted_cov.csv")
    isfile(e) ? e : b
end
cov0 = isfile(ADCOV) ? Matrix(CSV.read(ADCOV, DataFrame)) : Matrix(Diagonal(prop.^2))
isfile(ADCOV) && println("(seeding proposal from adapted covariance $(basename(ADCOV)))")
println("logpost(θ0) = ", round(logposterior(θ0), digits=2), "  (start = MAP)")

Random.seed!(SEED)
@time chain, accept, covout, lp = RAM_sample(logposterior, θ0, cov0, N_ITER; opt_α=0.234, output_log_probability_x=true)
mkpath(joinpath(REPO,"outputs/mcmc"))
CSV.write(joinpath(REPO,"outputs/mcmc/adapted_cov_$(TAG)_seed$(SEED).csv"), DataFrame(covout, :auto))
println("RAM run: $N_ITER iter, acceptance = ", round(accept, digits=3))
pn = vcat([k.name for k in FREE], vcat([["sd_$s","rho_$s"] for s in SERIES]...))
burn = chain[(N_ITER÷2+1):end, :]
println("\nposterior (2nd-half) median ± sd for key params:")
for nm in ["ais_ocean_temperature₀","anto_alpha","thermal_alpha","gic_T_lia","gic_f","gic_tau_fast","gic_tau_slow","gic_a"]
    c = burn[:, findfirst(==(nm),pn)]
    @printf("  %-24s %.3g ± %.2g\n", nm, median(c), std(c))
end
df = DataFrame(chain, pn); df.log_post = lp; df.accept_rate = fill(accept, nrow(df))
CSV.write(joinpath(REPO,"outputs/mcmc/chain_$(TAG)_seed$(SEED)_n$(N_ITER).csv"), df)
println("\nWrote outputs/mcmc/chain_$(TAG)_seed$(SEED)_n$(N_ITER).csv  (accept $(round(accept,digits=3)))")
println("Production = large N_ITER × ≥4 seeds, then postprocess_mcmc.jl with the chain_$(TAG)_* glob.")
