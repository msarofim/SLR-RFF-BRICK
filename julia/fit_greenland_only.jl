## ============================================================================
## fit_greenland_only.jl  —  CANDIDATE-1 structural test for the SIMPLE/Bakker
## Greenland module (handoff_2026-06-13 §4.1).
##
## Question: can the existing 5-parameter SIMPLE Greenland component
##   eq_volume(t) = a·T(t) + b                       (equilibrium LINEAR in T)
##   τ_inv(t)     = (α·T(t) + β)·(V/V₀)               (single-timescale rate)
##   dV/dt        = τ_inv·(eq_volume − V)             (one-pole relaxation)
## reproduce the OBSERVED Greenland increase→pause→increase melt shape, whose
## resumption begins ~2000 — i.e. ~30 yr AFTER the ~1970 GMST warming resumption?
##
## Test design: fit GIS ALONE (no competition from AIS/GSIC/TE/total) to the
## extended GIS target (Frederikse 1900-2018 + GRACE-FO ->2025), forced by the
## same FaIR-mean GMST as the production calibration. To give SIMPLE its BEST
## possible shot we WIDEN the 5 param bounds well past the production priors
## (stronger T-sensitivity, far faster/slower relaxation). If even the
## best-fit-on-GIS-alone resumes melt ~1970 (or must flatten the early-century
## melt to delay the resumption), the limit is STRUCTURAL, not a tuning failure.
##
## Outputs:
##   outputs/greenland_only_fit_ext.csv     (year, obs+band, best-fit model, GMST)
##   outputs/greenland_only_fit_params.csv  (best-fit params + fit diagnostics)
##
## Usage:  julia --project=julia_v2 julia/fit_greenland_only.jl
## ============================================================================

using CSV, DataFrames, Mimi, MimiBRICK, Statistics, LinearAlgebra, Random, Printf
include(joinpath(@__DIR__, "brick_mengel.jl"))

const REPO = abspath(joinpath(@__DIR__, ".."))
const OBS  = joinpath(REPO, "data/observations")
const Y0, Y1, B0, B1 = 1850, 2026, 1995, 2005          # same window + display baseline as ext calib
const TARGETS = joinpath(REPO, "outputs/recalib_targets_ext.csv")
years = collect(Y0:Y1); ib = [findfirst(==(y),years) for y in B0:B1]; idx(y)=findfirst(==(y),years)

# ---- forcing (same FaIR-mean GMST + OHC as production calibration) ----
lc(p,c)=(d=CSV.read(p,DataFrame); Dict(Int(d[i,"year"])=>Float64(d[i,c]) for i in 1:nrow(d)))
gmst=[lc(joinpath(OBS,"fair_mean_gmst.csv"),"gmst_C")[y] for y in years]
ohc =[lc(joinpath(OBS,"fair_mean_ohc.csv"),"ohc_1e22J")[y] for y in years]

# ---- extended GIS target (cm SLE), exactly as calibrate_mcmc_ext.jl builds it ----
tg = CSV.read(TARGETS, DataFrame)
ϵband(lo,hi)=max.((hi.-lo)./(2*1.645), 0.05)
function series_years(col)
    ys = Int[]
    for i in 1:nrow(tg)
        v = tg[i,col]
        (tg.year[i] >= 1900 && !ismissing(v) && !isnan(Float64(v))) && push!(ys, Int(tg.year[i]))
    end
    return sort(ys)
end
rowof(y) = findfirst(==(y), tg.year)
gy  = series_years(:gis)
gri = [rowof(y) for y in gy]
gobs = Float64.(tg[gri, :gis])
gϵ   = ϵband(Float64.(tg[gri,:gis_lo]), Float64.(tg[gri,:gis_hi]))
gmyi = [idx(y) for y in gy]
glo  = Float64.(tg[gri,:gis_lo]); ghi = Float64.(tg[gri,:gis_hi])
println("GIS fit window: $(gy[1])-$(gy[end])  ($(length(gy)) yrs)")

# ---- model: full BRICK-Mengel (Greenland runs inside it), forcing set once ----
medoid = CSV.read(joinpath(REPO,"outputs/recalib_central_row.csv"), DataFrame)[1,:]
m = build_brick_mengel(ssp="ssp245", y0=Y0, y1=Y1)
update_brick_mengel!(m, medoid, (a=0.45,b=0.52,T_lia=-0.45,f=0.5,tau_fast=40.0,tau_slow=250.0,sl0=0.0); precip_log=true)
set_forcing!(m, gmst, ohc)
reref(v)=100 .* (v .- sum(v[ib])/length(ib))           # cm, de-meaned to 1995-2005 (same as calib)

# ---- WIDENED bounds (well past the production priors) to give SIMPLE its best shot ----
# production priors (for reference): a[-0.761,-0.003] b[5.91,7.04] α[1.4e-6,6.4e-4] β[2.8e-4,9.9e-4] v₀[7.16,7.56]
const PNAME = (:greenland_a, :greenland_b, :greenland_α, :greenland_β, :greenland_v₀)
const LO = [ -3.0, 3.0, 1e-6, 1e-6, 5.0 ]
const HI = [ -0.001, 9.0, 1e-2, 1e-2, 12.0 ]
const LOGP = [false, false, true, true, false]          # sample α,β in log-space

function set_gis!(θ)
    for (i,nm) in enumerate(PNAME); update_param!(m, :greenland_icesheet, nm, θ[i]); end
end
function model_gis()                                    # de-meaned model GIS on fit years (cm)
    run(m)
    reref(m[:greenland_icesheet,:greenland_sea_level])[gmyi]
end
# weighted SSE on cumulative de-meaned GIS (same quantity the production calib fits)
wsse(θ) = (set_gis!(θ); g=model_gis(); sum(((g .- gobs)./gϵ).^2))

# ---- bounded search: log/linear-uniform random scan + local Gaussian refinement ----
Random.seed!(2026)
draw() = [ LOGP[i] ? exp(log(LO[i]) + rand()*(log(HI[i])-log(LO[i]))) :
                     LO[i] + rand()*(HI[i]-LO[i]) for i in 1:5 ]
clampθ(θ) = [ clamp(θ[i], LO[i], HI[i]) for i in 1:5 ]

function run_search()
    best = draw(); bestf = wsse(best)
    for _ in 1:40_000                                   # global scan
        θ = draw(); f = wsse(θ)
        if f < bestf; bestf = f; best = θ; end
    end
    for round in 1:10                                   # local refinement (shrinking)
        scale = 0.5^(round-1)
        for _ in 1:5_000
            θ = clampθ([ LOGP[i] ? best[i]*exp(0.6*scale*randn()) : best[i]+0.3*scale*(HI[i]-LO[i])*randn() for i in 1:5 ])
            f = wsse(θ)
            if f < bestf; bestf = f; best = θ; end
        end
        @printf("  refine round %2d  wSSE=%.1f\n", round, bestf)
    end
    return best, bestf
end
best, bestf = run_search()

# ---- best-fit diagnostics ----
set_gis!(best); gfit = model_gis()
rmse = sqrt(mean((gfit .- gobs).^2))
# decadal melt RATE (cm/decade), centered 11-yr smooth then 10-yr difference proxy
function rate(v, yrs)                                    # cm/yr, simple central diff on a 5-yr smooth
    n=length(v); sm=copy(v)
    for i in 1:n; w=max(1,i-2):min(n,i+2); sm[i]=mean(v[w]); end
    r=fill(NaN,n); for i in 6:n-5; r[i]=(sm[i+5]-sm[i-5])/10; end; r
end
obs_rate = rate(gobs, gy); fit_rate = rate(gfit, gy)
# resumption check: melt rate at the obs ~2000 resumption vs the ~1970 warming resumption
yr(y)=findfirst(==(y), gy)
println("\n=== CANDIDATE-1 GIS-only best fit (WIDENED bounds) ===")
for (i,nm) in enumerate(PNAME); @printf("  %-14s = %.6g\n", nm, best[i]); end
@printf("  wSSE=%.1f  RMSE=%.3f cm over %d-%d\n", bestf, rmse, gy[1], gy[end])
@printf("  model melt rate (cm/decade):  1965=%.3f  1975=%.3f  1995=%.3f  2010=%.3f\n",
        10fit_rate[yr(1965)], 10fit_rate[yr(1975)], 10fit_rate[yr(1995)], 10fit_rate[yr(2010)])
@printf("  obs   melt rate (cm/decade):  1965=%.3f  1975=%.3f  1995=%.3f  2010=%.3f\n",
        10obs_rate[yr(1965)], 10obs_rate[yr(1975)], 10obs_rate[yr(1995)], 10obs_rate[yr(2010)])

# ---- write outputs ----
out = DataFrame(year=gy, gis_obs=gobs, gis_lo=glo, gis_hi=ghi, gis_model=gfit,
                gmst=[gmst[idx(y)] for y in gy],
                obs_rate_cm_dec=10 .* obs_rate, model_rate_cm_dec=10 .* fit_rate)
CSV.write(joinpath(REPO,"outputs/greenland_only_fit_ext.csv"), out)
parm = DataFrame(param=collect(string.(PNAME)), value=best,
                 prior_lo=[-0.761,5.908,1.415e-6,2.776e-4,7.164],
                 prior_hi=[-0.003,7.042,6.381e-4,9.915e-4,7.556],
                 search_lo=LO, search_hi=HI)
CSV.write(joinpath(REPO,"outputs/greenland_only_fit_params.csv"), parm)
@printf("\nwrote outputs/greenland_only_fit_ext.csv  (+_params.csv)\n")
