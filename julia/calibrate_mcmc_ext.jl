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
const GEO_FILE  = joinpath(REPO, "outputs/paleo_geo_prior.csv")
const GEO_NAMES = ["ais_mu","ais_bedheight0","ais_slope","ais_iceflow0","ais_precip0_LOG","ais_runoff_h0","ais_c"]
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

const NP = length(FREE)
const SERIES = [:ais,:gsic,:gis,:steric,:dang]
const NN = 2*length(SERIES); const NK = NP + NN
println("MCMC: $NP physical (incl $(length(GEO_IDX)) DAIS-geometry under a joint paleo prior) " *
        "+ $NN AR(1)-noise = $NK free params  (point terms DROPPED)")

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
    # priors: independent Gaussian on physical (EXCEPT the geometry block, which gets the
    # joint paleo prior below), weak half-normal on AR(1) σ
    lp = 0.0
    @inbounds for k in 1:NP
        k in GEO_IDX && continue
        lp += logpdf(Normal(FREE[k].μ, FREE[k].σ), θ[k])
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
    "ais_precip0_LOG" => "antarctic_precip0",   "ais_c"          => "antarctic_c",
    "ais_runoff_h0"   => "antarctic_runoff_height0")
θ0 = Float64[]
for k in 1:NP
    nm = FREE[k].name
    if k in GEO_IDX
        v = Float64(medoid[GEO_MEDOID_COL[nm]])          # medoid stores precip₀ LINEAR
        push!(θ0, nm == "ais_precip0_LOG" ? log(v) : v)  # ...but θ/model are log-space
    else
        j = findfirst(==(nm), mapp.param)
        push!(θ0, isnothing(j) ? FREE[k].μ : mapp.MAP[j])
    end
end
append!(θ0, repeat([1.0, 0.5], length(SERIES)))
prop = vcat([0.1*Float64(k.σ) for k in FREE], repeat([0.3, 0.1], length(SERIES)))
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
const ADCOV = let e = joinpath(REPO,"outputs/mcmc/adapted_cov_ext.csv"),
                  b = joinpath(REPO,"outputs/mcmc/adapted_cov.csv")
    isfile(e) ? e : b
end
cov0 = Matrix(Diagonal(prop.^2))
if isfile(ADCOV)
    old = Matrix(CSV.read(ADCOV, DataFrame))
    # Pre-v-next covariances are (NK - 7)x(NK - 7): they predate the geometry block.
    # The geometry rows were APPENDED to the end of the physical block, so the remaining
    # params keep their relative order and the old matrix maps onto OLDIDX exactly.
    OLDIDX = [k for k in 1:NK if !(k in GEO_IDX)]
    if size(old,1) == NK
        cov0 = old
        println("(seeding proposal from adapted covariance $(basename(ADCOV)))")
    elseif size(old,1) == length(OLDIDX)
        cov0[OLDIDX, OLDIDX] = old      # tuned shape for the old params, diagonal for geometry
        println("(seeding proposal: embedded $(size(old,1))x$(size(old,1)) $(basename(ADCOV)) " *
                "+ diagonal for the $(length(GEO_IDX)) newly freed geometry params)")
    else
        println("(WARNING: $(basename(ADCOV)) is $(size(old,1))x$(size(old,1)), incompatible " *
                "with NK=$NK -- falling back to the diagonal proposal)")
    end
end
isposdef(cov0) || error("seed proposal covariance is not positive definite")
println("logpost(θ0) = ", round(logposterior(θ0), digits=2), "  (start = MAP)")

Random.seed!(SEED)
@time chain, accept, covout, lp = RAM_sample(logposterior, θ0, cov0, N_ITER; opt_α=0.234, output_log_probability_x=true)
mkpath(joinpath(REPO,"outputs/mcmc"))
CSV.write(joinpath(REPO,"outputs/mcmc/adapted_cov_$(TAG)_seed$(SEED).csv"), DataFrame(covout, :auto))
println("RAM run: $N_ITER iter, acceptance = ", round(accept, digits=3))
pn = vcat([k.name for k in FREE], vcat([["sd_$s","rho_$s"] for s in SERIES]...))
burn = chain[(N_ITER÷2+1):end, :]
println("\nposterior (2nd-half) median ± sd for key params:")
for nm in ["ais_ocean_temperature₀","anto_alpha","thermal_alpha","gic_T_lia","gic_f","gic_tau_fast","gic_tau_slow","gic_a",
           "ais_mu","ais_precip0_LOG","ais_iceflow0","ais_c"]
    c = burn[:, findfirst(==(nm),pn)]
    @printf("  %-24s %.3g ± %.2g\n", nm, median(c), std(c))
end
df = DataFrame(chain, pn); df.log_post = lp; df.accept_rate = fill(accept, nrow(df))
CSV.write(joinpath(REPO,"outputs/mcmc/chain_$(TAG)_seed$(SEED)_n$(N_ITER).csv"), df)
println("\nWrote outputs/mcmc/chain_$(TAG)_seed$(SEED)_n$(N_ITER).csv  (accept $(round(accept,digits=3)))")
println("Production = large N_ITER × ≥4 seeds, then postprocess_mcmc.jl with the chain_$(TAG)_* glob.")
