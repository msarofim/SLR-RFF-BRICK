## ============================================================================
## calibrate_full_joint.jl  —  full joint MAP calibration of BRICK-Mengel
##
## Maximum-a-posteriori (regularized) joint calibration of ALL key parameters of
## BRICK v2.0.0 with the Mengel glacier emulator, driven by FaIR-mean historical
## GMST+OHC (obs-driven). Minimizes the negative log-posterior:
##
##   J(θ) = Σ_targets ((model − obs)/σ_obs)²   [data misfit]
##        + Σ_params  ((θ − μ_prior)/σ_prior)² [prior penalty / regularization]
##
## Priors: post-#93 BRICK posterior mean±std for the 22 AIS/anto/GIS/TE params;
## physical for the Mengel glacier (a,b,τ,T_lia) and the freed ais_ocean_temperature₀.
## The prior keeps the many weakly-constrained DAIS shape params from overfitting,
## while the data pulls the well-constrained ones (oceanT0, anto_α, MICI, te_α, glacier).
##
## Targets (re-ref 1995-2005): Frederikse AIS/GSIC/GIS/Steric 1900-2018 (subsampled),
## IMBIE ΔAIS(1992-2017), Dyurgerov ΔGSIC(1961-2003), Dangendorf total (+ Frederikse-TWS
## LWS budget). Optimizer: coordinate descent. This MAP is also the MCMC start point.
##
##   julia --project=julia_v2 julia/calibrate_full_joint.jl
## ============================================================================

using CSV, DataFrames, Mimi, MimiBRICK, Statistics, Printf
include(joinpath(@__DIR__, "brick_mengel.jl"))

const REPO = abspath(joinpath(@__DIR__, ".."))
const OBS = joinpath(REPO, "data/observations")
const Y0, Y1 = 1850, 2018
const B0, B1 = 1995, 2005
years = collect(Y0:Y1)
ib = [findfirst(==(y), years) for y in B0:B1]
idx(y) = findfirst(==(y), years)

# ---- forcing + targets ----
loadcol(p, c) = (df=CSV.read(p, DataFrame); Dict(Int(df[i,"year"])=>Float64(df[i,c]) for i in 1:nrow(df)))
gmst_d = loadcol(joinpath(OBS,"fair_mean_gmst.csv"),"gmst_C"); gmst = [gmst_d[y] for y in years]
ohc_d  = loadcol(joinpath(OBS,"fair_mean_ohc.csv"),"ohc_1e22J"); ohc = [ohc_d[y] for y in years]
tg  = CSV.read(joinpath(REPO,"outputs/recalib_targets.csv"), DataFrame)   # cm rel 1995-2005, 1900-2018
sg  = CSV.read(joinpath(REPO,"outputs/recalib_target_sigmas.csv"), DataFrame)
tgi(y) = findfirst(==(y), tg.year)
const FITYRS = [1900, 1940, 1970, 2000, 2018]                # subsampled (reduce autocorrelation)
σ = (ais=sg.ais[1], gsic=sg.gsic[1], gis=(tg.gis_hi[tgi(1900)]-tg.gis_lo[tgi(1900)])/(2*1.645),
     steric=sg.steric[1], dang=sg.dang[1])
const IMBIE_MU, IMBIE_SIG = 0.72, 0.156
const DYU_MU,  DYU_SIG    = 2.127, 0.148

# ---- free-parameter table (name, model comp, model sym, prior μ, σ, lo, hi, islog) ----
# posterior column -> (component, symbol, is-log-precip)
PMAP = Dict(
  "thermal_alpha"=>(:thermal_expansion,:te_α,false),
  "greenland_a"=>(:greenland_icesheet,:greenland_a,false), "greenland_b"=>(:greenland_icesheet,:greenland_b,false),
  "greenland_alpha"=>(:greenland_icesheet,:greenland_α,false), "greenland_beta"=>(:greenland_icesheet,:greenland_β,false),
  "greenland_v0"=>(:greenland_icesheet,:greenland_v₀,false),
  "anto_alpha"=>(:antarctic_ocean,:anto_α,false), "anto_beta"=>(:antarctic_ocean,:anto_β,false),
  "antarctic_s0"=>(:antarctic_icesheet,:ais_sea_level₀,false), "antarctic_alpha"=>(:antarctic_icesheet,:ais_α,false),
  "antarctic_gamma"=>(:antarctic_icesheet,:ais_γ,false), "antarctic_mu"=>(:antarctic_icesheet,:ais_μ,false),
  "antarctic_nu"=>(:antarctic_icesheet,:ais_ν,false), "antarctic_kappa"=>(:antarctic_icesheet,:ais_κ,false),
  "antarctic_precip0"=>(:antarctic_icesheet,:ais_precipitation₀,true),   # LINEAR prior -> log() when set (v2.0.0)
  "antarctic_flow0"=>(:antarctic_icesheet,:ais_iceflow₀,false),
  "antarctic_runoff_height0"=>(:antarctic_icesheet,:ais_runoffline_snowheight₀,false),
  "antarctic_c"=>(:antarctic_icesheet,:ais_c,false), "antarctic_bed_height0"=>(:antarctic_icesheet,:ais_bedheight₀,false),
  "antarctic_slope"=>(:antarctic_icesheet,:ais_slope,false), "antarctic_lambda"=>(:antarctic_icesheet,:λ,false),
  "antarctic_temp_threshold"=>(:antarctic_icesheet,:temperature_threshold,false),
)
pri = CSV.read(joinpath(REPO,"outputs/param_priors.csv"), DataFrame)
KN = NamedTuple[]
for r in eachrow(pri)
    c,s,islog = PMAP[r.param]
    push!(KN, (name=r.param, comp=c, sym=s, μ=r.mean, σ=r.std, lo=r.lo, hi=r.hi, islog=islog))
end
# Mengel glacier (physical priors) + freed ais_ocean_temperature₀ (weak prior)
push!(KN, (name="gic_a",     comp=:glaciers_small_icecaps, sym=:gic_a,     μ=0.45, σ=0.08, lo=0.32, hi=0.55, islog=false))
push!(KN, (name="gic_b",     comp=:glaciers_small_icecaps, sym=:gic_b,     μ=0.52, σ=0.25, lo=0.25, hi=1.00, islog=false))
push!(KN, (name="gic_tau",   comp=:glaciers_small_icecaps, sym=:gic_tau,   μ=150., σ=100., lo=20.,  hi=500., islog=false))
push!(KN, (name="gic_T_lia", comp=:glaciers_small_icecaps, sym=:gic_T_lia, μ=-0.35,σ=0.20, lo=-0.80,hi=-0.10,islog=false))
push!(KN, (name="ais_ocean_temperature₀", comp=:antarctic_icesheet, sym=:ais_ocean_temperature₀, μ=0.72, σ=0.50, lo=0.50, hi=2.00, islog=false))
const NK = length(KN)
println("Full joint MAP calibration: $NK free parameters")

# ---- build model + set the base (medoid + Mengel init), forcing once ----
medoid = CSV.read(joinpath(REPO,"outputs/recalib_central_row.csv"), DataFrame)[1,:]
m = build_brick_mengel(ssp="ssp245", y0=Y0, y1=Y1)
update_brick_mengel!(m, medoid, (a=0.45,b=0.52,tau=150.0,T_lia=-0.35,sl0=0.0); precip_log=true)
set_forcing!(m, gmst, ohc)
setknob!(k, v) = update_param!(m, k.comp, k.sym, k.islog ? log(v) : v)

reref(v) = 100 .* (v .- sum(v[ib])/length(ib))   # m -> cm rel 1995-2005

function run_components(θ)
    @inbounds for k in 1:NK; setknob!(KN[k], θ[k]); end
    run(m)
    (ais=reref(m[:antarctic_icesheet,:ais_sea_level]), gsic=reref(m[:glaciers_small_icecaps,:gsic_sea_level]),
     gis=reref(m[:greenland_icesheet,:greenland_sea_level]), te=reref(m[:thermal_expansion,:te_sea_level]))
end

function objective(θ)
    c = run_components(θ)
    fl = [tgi(y) for y in FITYRS]; ml = [idx(y) for y in FITYRS]
    J = 0.0
    for (mod, obs, s) in [(c.ais,tg.ais,σ.ais),(c.gsic,tg.gsic,σ.gsic),(c.gis,tg.gis,σ.gis),(c.te,tg.steric,σ.steric)]
        for (mi,fi) in zip(ml,fl); J += ((mod[mi]-obs[fi])/s)^2; end
    end
    # total vs Dangendorf (+ Frederikse-TWS LWS budget)
    for (mi,fi) in zip(ml,fl)
        tot = c.ais[mi]+c.gsic[mi]+c.gis[mi]+c.te[mi]+tg.lws[fi]
        J += ((tot - tg.dang[fi])/σ.dang)^2
    end
    # modern rates
    J += ((c.ais[idx(2017)]-c.ais[idx(1992)] - IMBIE_MU)/IMBIE_SIG)^2
    J += ((c.gsic[idx(2003)]-c.gsic[idx(1961)] - DYU_MU)/DYU_SIG)^2
    # prior penalty
    @inbounds for k in 1:NK; J += ((θ[k]-KN[k].μ)/KN[k].σ)^2; end
    return J
end

# ---- coordinate descent (start at prior means) ----
θ = [Float64(k.μ) for k in KN]
println("Start J (prior means) = ", round(objective(θ), digits=1))
NGRID, NPASS = 15, 12
for pass in 1:NPASS
    improved = false
    for k in 1:NK
        grid = range(KN[k].lo, KN[k].hi, length=NGRID)
        bestv, bestj = θ[k], objective(θ)
        for v in grid
            θ[k]=v; j=objective(θ); if j<bestj; bestj=j; bestv=v; improved=true; end
        end
        θ[k]=bestv
    end
    pass % 3 == 0 && println("  pass $pass: J = ", round(objective(θ), digits=1))
    improved || break
end
Jfin = objective(θ)
println("Final J = ", round(Jfin, digits=1))

# ---- report + save ----
c = run_components(θ)
fl=[tgi(y) for y in FITYRS]; ml=[idx(y) for y in FITYRS]
rmse(mod,obs) = sqrt(mean([(mod[idx(y)]-obs[tgi(y)])^2 for y in 1900:2018]))
println("\n=== Fit (cm rel 1995-2005) ===")
println("comp        @1900(mod/obs)   RMSE 1900-2018")
for (nm,mod,obs) in [("AIS",c.ais,tg.ais),("GSIC",c.gsic,tg.gsic),("GIS",c.gis,tg.gis),("Steric",c.te,tg.steric)]
    @printf("%-8s   %+6.2f / %+6.2f      %.2f\n", nm, mod[idx(1900)], obs[tgi(1900)], rmse(mod,obs))
end
totobs = [tg.dang[tgi(y)] for y in 1900:2018]
totmod = [c.ais[idx(y)]+c.gsic[idx(y)]+c.gis[idx(y)]+c.te[idx(y)]+tg.lws[tgi(y)] for y in 1900:2018]
@printf("%-8s   %+6.2f / %+6.2f      %.2f\n", "TOTAL", totmod[1], totobs[1], sqrt(mean((totmod.-totobs).^2)))
@printf("ΔAIS(92-17)=%.2f (IMBIE %.2f)   ΔGSIC(61-03)=%.2f (Dyu %.2f)\n",
        c.ais[idx(2017)]-c.ais[idx(1992)], IMBIE_MU, c.gsic[idx(2003)]-c.gsic[idx(1961)], DYU_MU)

# save MAP component trajectories (1900-2018) for the validation figure
traj = DataFrame(year=collect(1900:2018))
for (nm,mod) in [("ais",c.ais),("gsic",c.gsic),("gis",c.gis),("te",c.te)]
    traj[!, nm] = [mod[idx(y)] for y in 1900:2018]
end
traj[!, "total"] = totmod
traj[!, "lws_budget"] = [tg.lws[tgi(y)] for y in 1900:2018]
CSV.write(joinpath(REPO,"outputs/calib_full_joint_trajectories.csv"), traj)

out = DataFrame(param=String[], prior_mean=Float64[], MAP=Float64[], prior_sigma=Float64[], moved_sigmas=Float64[])
for k in 1:NK
    push!(out, (KN[k].name, KN[k].μ, θ[k], KN[k].σ, (θ[k]-KN[k].μ)/KN[k].σ))
end
CSV.write(joinpath(REPO,"outputs/calib_full_joint_params.csv"), out)
println("\nParameters that moved >1σ from prior (data-constrained):")
for r in eachrow(out); abs(r.moved_sigmas)>1 && @printf("  %-26s %8.4g -> %8.4g  (%+.1fσ)\n", r.param, r.prior_mean, r.MAP, r.moved_sigmas); end
println("\nWrote outputs/calib_full_joint_params.csv  (MAP J=$(round(Jfin,digits=1)), $NK params)")
