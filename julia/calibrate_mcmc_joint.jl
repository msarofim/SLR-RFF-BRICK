## ============================================================================
## calibrate_mcmc_joint.jl — index-augmented JOINT FaIR/BRICK calibration
##
## Extends calibrate_mcmc_ext.jl: instead of conditioning BRICK on the single FaIR-MEAN
## forcing, sample a FaIR member index z ∈ {1..M} over the pre-run FaIR ensemble jointly
## with the 39 BRICK params. This restores the θ_BRICK↔z coupling (esp. te_α↔historical OHC,
## which the ensemble spreads 19% sd) that the calibrate-on-mean + independent-pairing
## approximation drops. FaIR is pre-run, so the cost is only ~2× BRICK. See
## notes/design_2026-07-24_index_augmented_joint_calibration_torch.md.
##
## The BRICK setup (priors, FREE, targets, θ0, cov0, --overdisperse, --amp-*) is IDENTICAL to
## calibrate_mcmc_ext.jl — this file changes exactly three things:
##   (1) forcing is an M-column ensemble (GMST_ens, OHC_ens); default M=1 = fair_mean.
##   (2) logposterior(θ, z) re-sets the forcing to member z, then the SAME ext body, + logLclim[z].
##   (3) the sampler adds an MH step on z (Metropolis-within-Gibbs); z frozen in --recover.
##
## Modes:
##   --recover           M=1 (fair_mean), z frozen at 1, delegate to RAM_sample EXACTLY like ext.
##                       => must reproduce chain_ext_seed<seed> bit-for-bit. RECOVERY TEST target.
##   --fair-ensemble=DIR full joint: load fair_{gmst,ohc}_base_wide.csv (841 members) from DIR;
##                       blocked RAM (--block) with an MH z-step between blocks.
##
## Usage:
##   # recovery test (Mac): must match ext
##   julia --project=julia_v2 julia/calibrate_mcmc_joint.jl 3000 2026 --recover
##   # full joint (Torch): see the design note + slurm/joint_calib.sbatch
##   julia --project=julia_v2 julia/calibrate_mcmc_joint.jl 2000000 2026 --fair-ensemble=data/fair_ensemble \
##         --tag=jointA108 --amp-mu=1.08 --amp-sigma=0.15 --overdisperse --block=2000 --zsteps=3 --zwindow=30
## ============================================================================

using CSV, DataFrames, Mimi, MimiBRICK, Statistics, LinearAlgebra, Distributions, Random, Printf
using RobustAdaptiveMetropolisSampler
include(joinpath(@__DIR__, "brick_mengel.jl"))

const REPO = abspath(joinpath(@__DIR__, ".."))
const OBS  = joinpath(REPO, "data/observations")
const Y0, Y1, B0, B1 = 1850, 2026, 1995, 2005
const TARGETS = joinpath(REPO, "outputs/recalib_targets_ext.csv")
const AMP_EQ = "--amp-equilibrium" in ARGS
_argval(pfx) = (i = findfirst(a -> startswith(a, pfx), ARGS);
                i === nothing ? nothing : ARGS[i][length(pfx)+1:end])
const AMP_MU_OVR    = _argval("--amp-mu=")
const AMP_SIGMA_OVR = _argval("--amp-sigma=")
const TAG_OVR       = _argval("--tag=")
# ---- JOINT-specific CLI ----
const RECOVER     = "--recover" in ARGS
const FAIR_ENS    = _argval("--fair-ensemble=")            # dir with fair_{gmst,ohc}_base_wide.csv
const ZSTEPS      = (v=_argval("--zsteps=");  v===nothing ? 3  : parse(Int,v))
const ZWINDOW     = (v=_argval("--zwindow="); v===nothing ? 30 : parse(Int,v))
const BLOCK       = (v=_argval("--block=");   v===nothing ? 2000 : parse(Int,v))
const TAG = TAG_OVR !== nothing ? TAG_OVR : (RECOVER ? "jointrec" : (AMP_EQ ? "jointA6eq" : "joint"))
years = collect(Y0:Y1); ib = [findfirst(==(y),years) for y in B0:B1]; idx(y)=findfirst(==(y),years)
N_ITER = length(ARGS)>=1 && !startswith(ARGS[1],"--") ? parse(Int,ARGS[1]) : 2000
SEED   = length(ARGS)>=2 && !startswith(ARGS[2],"--") ? parse(Int,ARGS[2]) : 2026

function hetero_logl_ar1(res::Vector{Float64}, σ::Float64, ρ::Float64, ϵ::Vector{Float64})
    n = length(res); σp = σ^2/(1-ρ^2)
    H = abs.(collect(1:n)' .- collect(1:n)); Σ = σp .* ρ.^H .+ Diagonal(ϵ.^2)
    return logpdf(MvNormal(Symmetric(Σ)), res)
end

lc(p,c)=(d=CSV.read(p,DataFrame); Dict(Int(d[i,"year"])=>Float64(d[i,c]) for i in 1:nrow(d)))
const FORCING_TAG = "ssp245harm"
gmst=[lc(joinpath(OBS,"fair_mean_gmst_$(FORCING_TAG).csv"),"gmst_C")[y] for y in years]
ohc =[lc(joinpath(OBS,"fair_mean_ohc_$(FORCING_TAG).csv"),"ohc_1e22J")[y] for y in years]

# ---- FaIR forcing ENSEMBLE (GMST_ens, OHC_ens are T×M) ----------------------------------
# Recovery / default: M=1 = the fair_mean used by calibrate_mcmc_ext.jl.
# --fair-ensemble=DIR: load fair_{gmst,ohc}_base_wide.csv (year, m0000..; ZJ OHC ×0.1 -> 1e22 J),
# trimmed to Y0:Y1. Lclim[z] is the per-member climate-obs weight (uniform for now; the ensemble
# is already AR6+historical constrained — a GMST/OHC-vs-obs term is a modular add, see design §2).
const OHCS = 0.1
function load_ensemble(dir)
    ldw(fn;s=1.0)=(d=CSV.read(joinpath(dir,fn),DataFrame); keep=[y in years for y in d.year];
                   permutedims(Matrix(d[keep,2:end]).*s))   # -> (member, year); we want year×member
    Gt = permutedims(ldw("fair_gmst_base_wide.csv"))         # year × member
    Ot = permutedims(ldw("fair_ohc_base_wide.csv"; s=OHCS))
    @assert size(Gt,1)==length(years) "ensemble year axis != $(length(years))"
    return Gt, Ot
end
GMST_ens, OHC_ens, MEMBERS = if FAIR_ENS !== nothing && !RECOVER
    G,O = load_ensemble(FAIR_ENS); (G, O, size(G,2))
else
    (reshape(copy(gmst), :, 1), reshape(copy(ohc), :, 1), 1)  # M=1
end
const M = MEMBERS
# member order for the local z-proposal: sort by historical OHC@2018 (smooth axis for L_SLR).
const ZORDER = M==1 ? [1] : sortperm([OHC_ens[idx(2018),z]-OHC_ens[idx(1850),z] for z in 1:M])
const ZRANK  = invperm(ZORDER)                               # member -> position in sorted order
const LCLIM  = zeros(M)                                       # TODO: GMST/OHC-vs-obs term (design §2)
println("forcing: $(M==1 ? "fair_mean (M=1, recovery)" : "FaIR ensemble M=$M from $FAIR_ENS")")

tg = CSV.read(TARGETS, DataFrame)
ϵband(lo,hi)=max.((hi.-lo)./(2*1.645), 0.05)
function series_years(col)
    ys = Int[]
    for i in 1:nrow(tg)
        v = tg[i,col]; (tg.year[i] >= 1900 && !ismissing(v) && !isnan(Float64(v))) && push!(ys, Int(tg.year[i]))
    end; return sort(ys)
end
rowof(y) = findfirst(==(y), tg.year)
function make_series(col, lo, hi; isdang=false)
    fy = series_years(col); @assert fy == collect(fy[1]:fy[end]) "series $col has a year gap"
    ri = [rowof(y) for y in fy]; ob = Float64.(tg[ri, col])
    ev = isdang ? sqrt.(Float64.(tg.dang_sig[ri]).^2 .+ ϵband(Float64.(tg.lws_lo[ri]),Float64.(tg.lws_hi[ri])).^2) :
                  ϵband(Float64.(tg[ri,lo]), Float64.(tg[ri,hi]))
    return (years=fy, myi=[idx(y) for y in fy], obs=ob, ϵ=ev)
end
S = (ais=make_series(:ais,:ais_lo,:ais_hi), gsic=make_series(:gsic,:gsic_lo,:gsic_hi),
     gis=make_series(:gis,:gis_lo,:gis_hi), steric=make_series(:steric,:steric_lo,:steric_hi),
     dang=make_series(:dang,:dang_lo,:dang_hi; isdang=true))
lws_dang = Float64.(tg.lws[[rowof(y) for y in S.dang.years]])

# ---- FREE params (IDENTICAL to calibrate_mcmc_ext.jl) ----
pri = CSV.read(joinpath(REPO,"outputs/param_priors.csv"), DataFrame)
prow(n)=pri[findfirst(==(n),pri.param),:]
P(n,c,s;islog=false)=(r=prow(n); (name=n,comp=c,sym=s,μ=r.mean,σ=r.std,lo=r.lo,hi=r.hi,islog=islog))
FREE = NamedTuple[]
push!(FREE, (name="ais_ocean_temperature₀",comp=:antarctic_icesheet,sym=:ais_ocean_temperature₀,μ=0.72,σ=0.50,lo=0.50,hi=2.00,islog=false))
push!(FREE, P("antarctic_alpha",:antarctic_icesheet,:ais_α)); push!(FREE, P("antarctic_nu",:antarctic_icesheet,:ais_ν))
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
push!(FREE, P("antarctic_lambda",:antarctic_icesheet,:λ)); push!(FREE, P("antarctic_gamma",:antarctic_icesheet,:ais_γ))
push!(FREE, P("antarctic_kappa",:antarctic_icesheet,:ais_κ))
const AMP_MU    = AMP_MU_OVR    !== nothing ? parse(Float64, AMP_MU_OVR)    : (AMP_EQ ? 1.0/0.8365 : 0.95)
const AMP_SIGMA = AMP_SIGMA_OVR !== nothing ? parse(Float64, AMP_SIGMA_OVR) : (AMP_EQ ? 0.002 : 0.10)
const AMP_LO = AMP_MU_OVR === nothing ? 0.70 : AMP_MU - 3*AMP_SIGMA
const AMP_HI = AMP_MU_OVR === nothing ? 1.25 : AMP_MU + 3*AMP_SIGMA
const AIS_TANT0 = -15.42 / 0.8365
push!(FREE, (name="ais_gmst_amp",comp=:antarctic_icesheet,sym=:ais_temperature_coefficient,μ=AMP_MU,σ=AMP_SIGMA,lo=AMP_LO,hi=AMP_HI,islog=false))
@printf("A6 prior: amp ~ N(%.3f, %.3f) on [%.3f, %.3f]   TAG=%s\n", AMP_MU, AMP_SIGMA, AMP_LO, AMP_HI, TAG)
const AMP_IDX = length(FREE)
const GEO_FILE  = joinpath(REPO, "outputs/paleo_geo_prior_ton.csv")
const GEO_NAMES = ["ais_mu","ais_bedheight0","ais_slope","ais_iceflow0","ais_precip0_LOG","ais_runoff_Ton","ais_c"]
const GEO_SYMS  = [:ais_μ, :ais_bedheight₀, :ais_slope, :ais_iceflow₀, :ais_precipitation₀, :ais_runoffline_snowheight₀, :ais_c]
_gl = [split(strip(l), ',') for l in readlines(GEO_FILE) if !startswith(l,"#") && !isempty(strip(l))]
_grow(tag) = [parse(Float64, x) for x in first(l for l in _gl if l[1] == tag)[2:end]]
const GEO_MU = _grow("mean"); const GEO_SD = _grow("sd")
const GEO_C  = Symmetric(permutedims(reduce(hcat, [[parse(Float64,x) for x in l[2:end]] for l in _gl if l[1] == "corr"])))
let glo = _grow("lo"), ghi = _grow("hi")
    for i in eachindex(GEO_SYMS)
        push!(FREE, (name=GEO_NAMES[i], comp=:antarctic_icesheet, sym=GEO_SYMS[i], μ=GEO_MU[i], σ=GEO_SD[i], lo=glo[i], hi=ghi[i], islog=false))
    end
end
const GEO_IDX   = (length(FREE)-length(GEO_SYMS)+1):length(FREE)
const GEO_PRIOR = MvNormal(zeros(length(GEO_SYMS)), Matrix(GEO_C))
const TON_IDX   = GEO_IDX[findfirst(==("ais_runoff_Ton"), GEO_NAMES)]
const C_IDX     = GEO_IDX[findfirst(==("ais_c"), GEO_NAMES)]
const SMB_Y0, SMB_Y1 = 1979, 2008
const SMB_IDX       = [idx(y) for y in SMB_Y0:SMB_Y1]
const SMB_TARGET_GT = 2098.0 * (10.92 / 12.295)
const SMB_SIGMA_GT  = 133.0 * (10.92 / 12.295)
const M3ICE_TO_GT   = 917.0 / 1e12
const NP = length(FREE)
const SERIES = [:ais,:gsic,:gis,:steric,:dang]
const NN = 2*length(SERIES); const NK = NP + NN
const pn0 = vcat([k.name for k in FREE], vcat([["sd_$s","rho_$s"] for s in SERIES]...))
println("JOINT MCMC: $NP physical + $NN AR(1) = $NK BRICK params + z over $M FaIR member(s)")

medoid = CSV.read(joinpath(REPO,"outputs/recalib_central_row.csv"), DataFrame)[1,:]
m = build_brick_mengel(ssp="ssp245", y0=Y0, y1=Y1)
update_brick_mengel!(m, medoid, (a=0.45,b=0.52,T_lia=-0.45,f=0.5,tau_fast=40.0,tau_slow=250.0,sl0=0.0); precip_log=true)
set_forcing!(m, GMST_ens[:,1], OHC_ens[:,1])                 # member 1 (= fair_mean when M=1)
setp!(k,v)=update_param!(m,k.comp,k.sym, k.islog ? log(v) : v)
reref(v)=100 .* (v .- sum(v[ib])/length(ib))

# ---- JOINT logposterior: forcing = member z, then the EXACT ext body, + log Lclim[z] ----
function logposterior(θ, z::Int)
    @inbounds for k in 1:NP; (θ[k]<FREE[k].lo || θ[k]>FREE[k].hi) && return -Inf; end
    σn = θ[NP+1:2:NK]; ρn = θ[NP+2:2:NK]
    (any(σn .<= 0) || any(ρn .< 0) || any(ρn .>= 0.99)) && return -Inf
    set_forcing!(m, GMST_ens[:,z], OHC_ens[:,z])             # <-- THE joint change (idempotent at z=1)
    @inbounds for k in 1:NP
        (k == AMP_IDX || k == TON_IDX) && continue
        setp!(FREE[k], θ[k])
    end
    update_param!(m, :antarctic_icesheet, :ais_runoffline_snowheight₀, -θ[TON_IDX] * θ[C_IDX])
    update_param!(m, :antarctic_icesheet, :ais_temperature_coefficient, 1.0 / θ[AMP_IDX])
    update_param!(m, :antarctic_icesheet, :ais_temperature_intercept, -AIS_TANT0 / θ[AMP_IDX])
    run(m)
    ais=reref(m[:antarctic_icesheet,:ais_sea_level]); gsic=reref(m[:glaciers_small_icecaps,:gsic_sea_level])
    gis=reref(m[:greenland_icesheet,:greenland_sea_level]); te=reref(m[:thermal_expansion,:te_sea_level])
    tot_full = ais .+ gsic .+ gis .+ te
    ll = 0.0
    for (i,(s,full)) in enumerate(zip([S.ais,S.gsic,S.gis,S.steric], [ais,gsic,gis,te]))
        ll += hetero_logl_ar1(full[s.myi] .- s.obs, σn[i], ρn[i], s.ϵ)
    end
    ll += hetero_logl_ar1(tot_full[S.dang.myi] .+ lws_dang .- S.dang.obs, σn[5], ρn[5], S.dang.ϵ)
    smb_gt = mean(m[:antarctic_icesheet, :β_total][SMB_IDX]) * M3ICE_TO_GT
    ll += logpdf(Normal(SMB_TARGET_GT, SMB_SIGMA_GT), smb_gt)
    lp = 0.0
    @inbounds for k in 1:NP
        k in GEO_IDX && continue
        lp += logpdf(Normal(FREE[k].μ, FREE[k].σ), θ[k])
    end
    lp += logpdf(GEO_PRIOR, (θ[GEO_IDX] .- GEO_MU) ./ GEO_SD)
    for i in 1:length(SERIES); lp += logpdf(truncated(Normal(0,5),0,Inf), σn[i]); end
    return ll + lp + LCLIM[z]
end

# ---- start point θ0 + proposal cov0 (IDENTICAL to calibrate_mcmc_ext.jl) ----
mapp = CSV.read(joinpath(REPO,"outputs/calib_full_joint_params.csv"), DataFrame)
const GEO_MEDOID_COL = Dict("ais_mu"=>"antarctic_mu","ais_bedheight0"=>"antarctic_bed_height0","ais_slope"=>"antarctic_slope",
    "ais_iceflow0"=>"antarctic_flow0","ais_precip0_LOG"=>"antarctic_precip0","ais_c"=>"antarctic_c")
const FD_MEDOID = ("antarctic_lambda", "antarctic_gamma", "antarctic_kappa")
θ0 = Float64[]
for k in 1:NP
    nm = FREE[k].name
    if k in GEO_IDX
        if nm == "ais_runoff_Ton"
            push!(θ0, -Float64(medoid["antarctic_runoff_height0"]) / Float64(medoid["antarctic_c"]))
        else
            v = Float64(medoid[GEO_MEDOID_COL[nm]]); push!(θ0, nm == "ais_precip0_LOG" ? log(v) : v)
        end
    elseif nm in FD_MEDOID; push!(θ0, Float64(medoid[nm]))
    elseif nm == "ais_gmst_amp"; push!(θ0, 1.0 / 0.8365)
    else j = findfirst(==(nm), mapp.param); push!(θ0, isnothing(j) ? FREE[k].μ : mapp.MAP[j])
    end
end
append!(θ0, repeat([1.0, 0.5], length(SERIES)))
prop = vcat([0.1*Float64(k.σ) for k in FREE], repeat([0.3, 0.1], length(SERIES)))
const GEO_PROP_SCALE = 0.02
for k in GEO_IDX; prop[k] = GEO_PROP_SCALE * Float64(FREE[k].σ); end
const ADCOV = let e = joinpath(REPO,"outputs/mcmc/adapted_cov_ext.csv"), b = joinpath(REPO,"outputs/mcmc/adapted_cov.csv")
    isfile(e) ? e : b end
cov0 = Matrix(Diagonal(prop.^2))
const OLD35_NAMES = vcat(
    ["ais_ocean_temperature₀","antarctic_alpha","antarctic_nu","antarctic_temp_threshold","anto_alpha","anto_beta",
     "greenland_a","greenland_b","greenland_alpha","greenland_beta","greenland_v0","thermal_alpha","gic_a","gic_b",
     "gic_T_lia","gic_f","gic_tau_fast","gic_tau_slow","ais_mu","ais_bedheight0","ais_slope","ais_iceflow0",
     "ais_precip0_LOG","ais_runoff_h0","ais_c"], vcat([["sd_$s","rho_$s"] for s in SERIES]...))
if isfile(ADCOV)
    old = Matrix(CSV.read(ADCOV, DataFrame))
    if size(old,1) == NK; cov0 = old; println("(seeding proposal from $(basename(ADCOV)))")
    elseif size(old,1) == length(OLD35_NAMES)
        oi=Int[]; ni=Int[]
        for (i,nm) in enumerate(OLD35_NAMES); j=findfirst(==(nm),pn0); isnothing(j) && continue; push!(oi,i); push!(ni,j); end
        cov0[ni,ni] = old[oi,oi]; println("(seeding proposal: name-mapped $(length(oi)) rows of $(basename(ADCOV)))")
    end
end
isposdef(cov0) || error("seed proposal covariance is not positive definite")

const OVERDISPERSE = "--overdisperse" in ARGS
if OVERDISPERSE
    SF = joinpath(REPO, "outputs/mcmc/overdispersed_starts.csv")
    isfile(SF) || error("--overdisperse needs $SF")
    st = CSV.read(SF, DataFrame); si = findfirst(==(SEED), [2026,2027,2028,2029])
    (isnothing(si) || nrow(st) < si) && error("--overdisperse: no start row for seed $SEED")
    missing_cols = [nm for nm in pn0 if !hasproperty(st, Symbol(nm))]
    isempty(missing_cols) || error("--overdisperse: $SF missing $(length(missing_cols)) columns (predates current param set)")
    for (k,nm) in enumerate(pn0); θ0[k] = Float64(st[si, Symbol(nm)]); end
    AMP_EQ && (θ0[AMP_IDX] = AMP_MU)
    isfinite(logposterior(θ0, 1)) || error("--overdisperse: start has non-finite logposterior")
end

# ---- z-step: MH on the FaIR member index (Metropolis-within-Gibbs) --------------------------
# Propose z' in an OHC-sorted local window (80%) or independent-uniform (20%); accept by the
# joint-target ratio (which includes L_SLR at forcing_z' and log Lclim[z']). Cheap: 1 BRICK run.
function z_step(θ, z, lpz)
    M == 1 && return z, lpz, false
    if rand() < 0.8
        r = clamp(ZRANK[z] + rand(-ZWINDOW:ZWINDOW), 1, M); zp = ZORDER[r]        # local in sorted order
    else
        zp = rand(1:M)                                                            # global independence
    end
    zp == z && return z, lpz, false
    lpp = logposterior(θ, zp)
    if log(rand()) < lpp - lpz; return zp, lpp, true; else return z, lpz, false; end
end

Random.seed!(SEED)
mkpath(joinpath(REPO,"outputs/mcmc"))
if RECOVER || M == 1
    # RECOVERY: z frozen at 1 = fair_mean. Delegate to RAM_sample exactly like calibrate_mcmc_ext.jl.
    println("RECOVERY mode: z frozen at member 1 (fair_mean); must reproduce chain_ext_seed$SEED.")
    @time chain, accept, covout, lp = RAM_sample(θ -> logposterior(θ, 1), θ0, cov0, N_ITER; opt_α=0.234, output_log_probability_x=true)
    CSV.write(joinpath(REPO,"outputs/mcmc/adapted_cov_$(TAG)_seed$(SEED).csv"), DataFrame(covout, :auto))
    df = DataFrame(chain, pn0); df.log_post = lp; df.z = fill(1, nrow(df)); df.accept_rate = fill(accept, nrow(df))
    CSV.write(joinpath(REPO,"outputs/mcmc/chain_$(TAG)_seed$(SEED)_n$(N_ITER).csv"), df)
    @printf("RECOVERY: %d iter, acceptance = %.3f\n", N_ITER, accept)
else
    # FULL JOINT: blocked RAM (carry covariance + position) with an MH z-step between blocks.
    # (A per-iteration manual-RAM variant is the production upgrade — see design §3; blocked is
    #  correct block-Gibbs but restarts the RAM adaptation schedule each block, so keep BLOCK large.)
    # Wrapped in a function so the loop shares FUNCTION-local scope (top-level for-loops can't
    # reassign outer vars — Julia soft-scope).
    function run_full_joint(θ0, cov0)
        nblocks = cld(N_ITER, BLOCK)
        z = OVERDISPERSE ? ZORDER[clamp(round(Int, (findfirst(==(SEED),[2026,2027,2028,2029])-0.5)/4*M),1,M)] : (M÷2+1)
        lpz = logposterior(θ0, z)
        θcur = copy(θ0); covc = copy(cov0)
        chainbuf = Matrix{Float64}(undef, 0, NK); lpbuf = Float64[]; zbuf = Int[]; zacc = 0; ztot = 0
        accs = Float64[]
        for b in 1:nblocks
            k = min(BLOCK, N_ITER - (b-1)*BLOCK)
            ch, ac, covc, lpb = RAM_sample(θ -> logposterior(θ, z), θcur, covc, k; opt_α=0.234, output_log_probability_x=true)
            θcur = vec(ch[end, :]); push!(accs, ac)
            chainbuf = vcat(chainbuf, ch); append!(lpbuf, lpb); append!(zbuf, fill(z, k))
            lpz = logposterior(θcur, z)                                          # re-eval at block end
            for _ in 1:ZSTEPS; ztot += 1; z, lpz, moved = z_step(θcur, z, lpz); zacc += moved; end
            b % max(1, nblocks÷20) == 0 && (@printf("  block %d/%d: θ-acc %.3f  z=%d (rank %d/%d)  z-acc %.2f\n",
                                                    b,nblocks,ac,z,ZRANK[z],M,zacc/max(ztot,1)); flush(stdout))
        end
        return chainbuf, lpbuf, zbuf, covc, mean(accs), zacc/max(ztot,1)
    end
    chainbuf, lpbuf, zbuf, covc, θacc, zaccrate = run_full_joint(θ0, cov0)
    CSV.write(joinpath(REPO,"outputs/mcmc/adapted_cov_$(TAG)_seed$(SEED).csv"), DataFrame(covc, :auto))
    df = DataFrame(chainbuf, pn0); df.log_post = lpbuf; df.z = zbuf; df.accept_rate = fill(θacc, nrow(df))
    CSV.write(joinpath(REPO,"outputs/mcmc/chain_$(TAG)_seed$(SEED)_n$(N_ITER).csv"), df)
    @printf("JOINT: %d iter, mean θ-acc %.3f, z-acc %.2f, distinct z visited %d\n",
            N_ITER, θacc, zaccrate, length(unique(zbuf)))
end
println("Wrote outputs/mcmc/chain_$(TAG)_seed$(SEED)_n$(N_ITER).csv")
