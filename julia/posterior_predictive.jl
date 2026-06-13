## ============================================================================
## posterior_predictive.jl  —  Posterior-predictive check of BRICK-Mengel
##
## Step 2 of the recalibration arc (handoff_2026-06-12). Runs the FaIR-forced
## BRICK-Mengel forward over the 1900-2018 historical window for every posterior
## draw in data/MimiBRICK/parameters_subsample_brick_mengel.csv, builds 5/50/95
## component bands (AIS / GSIC / GIS / TE / total), and compares to the
## Frederikse component obs + Dangendorf total (outputs/recalib_targets.csv).
##
## The posterior was calibrated DIRECTLY to Dangendorf (the AR(1) total term in
## calibrate_mcmc.jl), so the draws ARE the data-conditioned distribution — the
## bands are raw percentiles over draws, NO importance weighting (unlike the old
## v2.0.0-default ensemble that needed Dangendorf reweighting).
##
## Also runs two sanity tests on the posterior (climate-modeling skill):
##   (4) determinism / bit-identical re-run of one draw
##   glacier stabilization — Mengel remnant property S_eq(T*) < a holds across
##       the WHOLE posterior (no commit-to-total-melt), integrating the exact
##       component update equations (glaciers_mengel_component.jl:56-59).
## The other 3 paired tests (zero-pert, sign-flip, ×2) are PULSE-experiment tests;
## they belong to the later SC-GHG pulse stage, not this posterior-predictive run.
##
## Usage:
##   julia --project=julia_v2 julia/posterior_predictive.jl [n_draws]
##   (n_draws default = all 10k; forward run ~4 ms each, ~40 s for 10k)
## ============================================================================

using CSV, DataFrames, Mimi, MimiBRICK, Statistics, Random, Printf
include(joinpath(@__DIR__, "brick_mengel.jl"))

const REPO = abspath(joinpath(@__DIR__, ".."))
const OBS  = joinpath(REPO, "data/observations")
const Y0, Y1, B0, B1 = 1850, 2018, 1995, 2005          # same window + baseline as calibration
years = collect(Y0:Y1); ib = [findfirst(==(y),years) for y in B0:B1]; idx(y)=findfirst(==(y),years)
NDRAW = length(ARGS) >= 1 ? parse(Int, ARGS[1]) : typemax(Int)

# ---- forcing + targets (identical to calibrate_mcmc.jl) ----
lc(p,c)=(d=CSV.read(p,DataFrame); Dict(Int(d[i,"year"])=>Float64(d[i,c]) for i in 1:nrow(d)))
gmst=[lc(joinpath(OBS,"fair_mean_gmst.csv"),"gmst_C")[y] for y in years]
ohc =[lc(joinpath(OBS,"fair_mean_ohc.csv"),"ohc_1e22J")[y] for y in years]
tg = CSV.read(joinpath(REPO,"outputs/recalib_targets.csv"), DataFrame); tgi(y)=findfirst(==(y),tg.year)
FY = collect(1900:2018); fyi=[tgi(y) for y in FY]; myi=[idx(y) for y in FY]

# ---- the 18 free PHYSICAL params, in posterior-CSV column order (= pn[1:18]) ----
# (comp, sym) mapping mirrors calibrate_mcmc.jl FREE; all islog=false there.
const PHYS = [
    (:antarctic_icesheet, :ais_ocean_temperature₀), (:antarctic_icesheet, :ais_α),
    (:antarctic_icesheet, :ais_ν), (:antarctic_icesheet, :temperature_threshold),
    (:antarctic_ocean, :anto_α), (:antarctic_ocean, :anto_β),
    (:greenland_icesheet, :greenland_a), (:greenland_icesheet, :greenland_b),
    (:greenland_icesheet, :greenland_α), (:greenland_icesheet, :greenland_β),
    (:greenland_icesheet, :greenland_v₀), (:thermal_expansion, :te_α),
    (:glaciers_small_icecaps, :gic_a), (:glaciers_small_icecaps, :gic_b),
    (:glaciers_small_icecaps, :gic_T_lia), (:glaciers_small_icecaps, :gic_f),
    (:glaciers_small_icecaps, :gic_tau_fast), (:glaciers_small_icecaps, :gic_tau_slow),
]
const PHYS_NAMES = ["ais_ocean_temperature₀","antarctic_alpha","antarctic_nu","antarctic_temp_threshold",
    "anto_alpha","anto_beta","greenland_a","greenland_b","greenland_alpha","greenland_beta",
    "greenland_v0","thermal_alpha","gic_a","gic_b","gic_T_lia","gic_f","gic_tau_fast","gic_tau_slow"]

# ---- model base (medoid fixed params + glacier init), forcing once ----
medoid = CSV.read(joinpath(REPO,"outputs/recalib_central_row.csv"), DataFrame)[1,:]
m = build_brick_mengel(ssp="ssp245", y0=Y0, y1=Y1)
update_brick_mengel!(m, medoid, (a=0.45,b=0.52,T_lia=-0.45,f=0.5,tau_fast=40.0,tau_slow=250.0,sl0=0.0); precip_log=true)
set_forcing!(m, gmst, ohc)
reref(v)=100 .* (v .- sum(v[ib])/length(ib))

# set the 18 physical params from a posterior row, run, return reref'd components at FY
function run_draw!(row)
    @inbounds for k in 1:length(PHYS)
        update_param!(m, PHYS[k][1], PHYS[k][2], Float64(row[PHYS_NAMES[k]]))
    end
    run(m)
    ais  = reref(m[:antarctic_icesheet, :ais_sea_level])[myi]
    gsic = reref(m[:glaciers_small_icecaps, :gsic_sea_level])[myi]
    gis  = reref(m[:greenland_icesheet, :greenland_sea_level])[myi]
    te   = reref(m[:thermal_expansion, :te_sea_level])[myi]
    tot  = ais .+ gsic .+ gis .+ te .+ Float64.(tg.lws[fyi])   # + Frederikse LWS budget (as in calib)
    return (ais=ais, gsic=gsic, gis=gis, te=te, total=tot)
end

# ---- DIAGNOSTIC: reproduce the MAP fit, compare components@2018 to obs ----
# Verifies this script's forward run matches the calibration (calibrate_full_joint).
# The MAP CSV has rows (param, MAP); build a 1-row frame keyed by PHYS_NAMES.
mapp = CSV.read(joinpath(REPO,"outputs/calib_full_joint_params.csv"), DataFrame)
maprow = Dict(string(mapp.param[i]) => Float64(mapp.MAP[i]) for i in 1:nrow(mapp))
if all(haskey(maprow, n) for n in PHYS_NAMES)
    rmap = run_draw!(maprow)
    println("[diag] MAP forward run — component vs Frederikse/Dangendorf obs @2018 (cm):")
    for (c, ocol) in [(:ais,:ais),(:gsic,:gsic),(:gis,:gis),(:te,:steric),(:total,:dang)]
        @printf("   %-7s MAP=%6.2f  obs=%6.2f  (Δ=%+.2f)\n",
                c, getfield(rmap,c)[end], Float64(tg[fyi[end], ocol]),
                getfield(rmap,c)[end]-Float64(tg[fyi[end], ocol]))
    end
else
    println("[diag] MAP param names don't all match PHYS_NAMES; skipping MAP reproduction check.")
end

# ============================================================================
# 1. POSTERIOR-PREDICTIVE BANDS
# ============================================================================
post = CSV.read(joinpath(REPO,"data/MimiBRICK/parameters_subsample_brick_mengel.csv"), DataFrame)
ND = min(NDRAW, nrow(post))
println("Posterior-predictive: $ND draws × BRICK-Mengel forward (1900-2018)...")

comps = (:ais, :gsic, :gis, :te, :total)
ny = length(FY)
store = Dict(c => Array{Float64}(undef, ND, ny) for c in comps)
@time for i in 1:ND
    r = run_draw!(post[i, :])
    for c in comps; store[c][i, :] = getfield(r, c); end
end

# 5/50/95 percentiles per year per component
band = DataFrame(year=FY)
for c in comps
    band[!, "$(c)_p5"]  = [quantile(store[c][:,j], 0.05) for j in 1:ny]
    band[!, "$(c)_p50"] = [quantile(store[c][:,j], 0.50) for j in 1:ny]
    band[!, "$(c)_p95"] = [quantile(store[c][:,j], 0.95) for j in 1:ny]
end
# attach obs (Frederikse components + Dangendorf total) for the plot
for (c, ocol) in [(:ais,:ais),(:gsic,:gsic),(:gis,:gis),(:te,:steric),(:total,:dang)]
    band[!, "$(c)_obs"] = Float64.(tg[fyi, ocol])
end
for (c, lo, hi) in [(:ais,:ais_lo,:ais_hi),(:gsic,:gsic_lo,:gsic_hi),(:gis,:gis_lo,:gis_hi),(:te,:steric_lo,:steric_hi)]
    band[!, "$(c)_obs_lo"] = Float64.(tg[fyi, lo]); band[!, "$(c)_obs_hi"] = Float64.(tg[fyi, hi])
end
# Dangendorf total obs band = ±1.645σ (matches the calibration's ϵ definition direction)
band[!, "total_obs_lo"] = Float64.(tg.dang[fyi]) .- 1.645 .* Float64.(tg.dang_sig[fyi])
band[!, "total_obs_hi"] = Float64.(tg.dang[fyi]) .+ 1.645 .* Float64.(tg.dang_sig[fyi])
CSV.write(joinpath(REPO,"outputs/postpred_components_timeseries.csv"), band)
println("Wrote outputs/postpred_components_timeseries.csv")

# coverage: the model's 90% parametric band is NARROW (it carries parameter
# uncertainty only, not the AR(1) obs-noise term). The calibration-adequacy
# question is whether the model band OVERLAPS the obs uncertainty band each year.
# Report both: band-overlap (primary) and obs-mean-in-model-band (secondary, strict).
println("\nBand coverage vs Frederikse/Dangendorf obs (overlap = model 90% band ∩ obs unc. band):")
covsum = DataFrame(component=String[], overlap_pct=Float64[], meaninband_pct=Float64[],
                   obs2018=Float64[], p50_2018=Float64[], p5_2018=Float64[], p95_2018=Float64[])
for c in comps
    o   = band[!, "$(c)_obs"]
    olo = band[!, "$(c)_obs_lo"]; ohi = band[!, "$(c)_obs_hi"]
    mlo = band[!, "$(c)_p5"];     mhi = band[!, "$(c)_p95"]
    overlap   = (mhi .>= olo) .& (mlo .<= ohi)            # band intersection non-empty
    meaninband= (o .>= mlo) .& (o .<= mhi)
    ov = 100*sum(overlap)/ny; mi = 100*sum(meaninband)/ny
    @printf("  %-7s overlap %5.1f%%  mean-in-band %5.1f%%   2018: obs=%6.2f  p50=%6.2f  [%6.2f, %6.2f] cm\n",
            c, ov, mi, o[end], band[end,"$(c)_p50"], band[end,"$(c)_p5"], band[end,"$(c)_p95"])
    push!(covsum, (string(c), ov, mi, o[end], band[end,"$(c)_p50"], band[end,"$(c)_p5"], band[end,"$(c)_p95"]))
end
CSV.write(joinpath(REPO,"outputs/postpred_coverage.csv"), covsum)

# ============================================================================
# 2. SANITY TEST — DETERMINISM (climate-modeling test 4: bit-identical re-run)
# ============================================================================
println("\n[sanity] determinism: re-run draw 1 twice, expect bit-identical components...")
a1 = run_draw!(post[1, :]); a2 = run_draw!(post[1, :])
maxdiff = maximum(maximum(abs.(getfield(a1,c) .- getfield(a2,c))) for c in comps)
@printf("  max |Δ| across all components = %.2e  ->  %s\n", maxdiff, maxdiff < 1e-12 ? "PASS" : "FAIL")

# ============================================================================
# 3. SANITY TEST — GLACIER STABILIZATION ACROSS THE POSTERIOR
#    Integrate the EXACT Mengel 2-τ update equations (glaciers_mengel_component.jl
#    :56-59) under a sustained T* for every draw; confirm gsic -> S_eq(T*) < a
#    (a temperature-appropriate remnant survives; NO commit-to-total-melt).
# ============================================================================
function stabilize(a, b, Tlia, f, tf, ts, Tstar; nyr=2000)
    Seq = a * (1 - exp(-b*(Tstar - Tlia)))          # equilibrium SLE (m) under held T*
    fast = f*Seq; slow = (1-f)*Seq                  # seed at equilibrium-ish; relax anyway
    fast = 0.0; slow = 0.0                           # start from 0 to test convergence
    for _ in 1:nyr
        fast += (f*Seq - fast)/tf
        slow += ((1-f)*Seq - slow)/ts
    end
    return (fast+slow), Seq                          # (modeled gsic@equil, analytic S_eq)
end
println("\n[sanity] glacier stabilization across $(nrow(post)) posterior draws (hold T*=1.5 °C to equilibrium):")
function stab_scan(post)
    worst_gap = 0.0; n_collapse = 0; n_overshoot = 0
    for r in eachrow(post)
        a,b,Tlia,f,tf,ts = r.gic_a, r.gic_b, r.gic_T_lia, r.gic_f, r.gic_tau_fast, r.gic_tau_slow
        g, Seq = stabilize(a,b,Tlia,f,tf,ts, 1.5)
        worst_gap = max(worst_gap, abs(g - Seq))
        (g >= a) && (n_overshoot += 1)               # must stay below asymptote a (no overshoot)
        (Seq >= a - 1e-9) && (n_collapse += 1)       # S_eq must be < a (remnant, not total melt)
    end
    return worst_gap, n_collapse, n_overshoot
end
worst_gap, n_collapse, n_overshoot = stab_scan(post)
amin = minimum(post.gic_a); amax = maximum(post.gic_a)
@printf("  worst |gsic_equil - S_eq| = %.2e m  (relaxation converges)\n", worst_gap)
@printf("  draws with S_eq >= a (total-melt commitment): %d / %d  ->  %s\n",
        n_collapse, nrow(post), n_collapse==0 ? "PASS (remnant always survives)" : "FAIL")
@printf("  draws with gsic_equil >= a (asymptote overshoot): %d / %d  ->  %s\n",
        n_overshoot, nrow(post), n_overshoot==0 ? "PASS" : "FAIL")
@printf("  posterior gic_a (asymptotic max SLE) range: [%.3f, %.3f] m\n", amin, amax)
println("\nposterior_predictive.jl DONE.")
