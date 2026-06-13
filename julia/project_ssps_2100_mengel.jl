## ============================================================================
## project_ssps_2100_mengel.jl  —  ENSEMBLE SSP projections to 2100,
##                                  MCMC-calibrated BRICK-Mengel posterior
##
## Successor to project_ssps_2100_ensemble.jl (which projected the OLD
## parameters_subsample_brick.csv on stock single-reservoir BRICK, with a
## v2.0.0-vs-knob split + Dangendorf importance weighting). This driver projects
## the Bayesian MCMC posterior of BRICK-Mengel (parameters_subsample_brick_mengel.csv):
##
##   * Model = build_brick_mengel (2-τ temperature-dependent glacier swapped in),
##     fixed (non-free) params from the medoid central row, the 18 free physical
##     params set PER DRAW (same setup as the calibration / posterior_predictive.jl).
##   * ONE calibration (the MCMC posterior IS the calibration — no v2.0.0/knob split).
##   * UNWEIGHTED bands: the posterior was calibrated DIRECTLY to Dangendorf, so the
##     equal-weight draws already are the data-conditioned distribution. Re-applying
##     Dangendorf importance weights here would DOUBLE-COUNT the same obs → dropped.
##   * FaIR v1.4.5-forced per SSP (GMST + OHC). SLR rel AR6 1995-2014.
##
##   julia --project=julia_v2 julia/project_ssps_2100_mengel.jl [N_DRAWS] [TAG]
##     TAG (optional): "" (default) projects the 2018-baseline posterior; "ext"
##     projects the post-2018-extended posterior (parameters_subsample_brick_mengel_ext.csv)
##     and writes proj_ssps_mengel_ext_{summary,timeseries}.csv. Baseline behavior
##     is byte-identical when TAG is omitted.
## ============================================================================

using CSV, DataFrames, Mimi, MimiBRICK, Statistics, Printf
include(joinpath(@__DIR__, "brick_mengel.jl"))

const REPO = abspath(joinpath(@__DIR__, ".."))
const OBSDIR = joinpath(REPO, "data/observations")
const Y0, Y1 = 1850, 2100
const BASE0, BASE1 = 1995, 2014            # AR6 projection baseline
years = collect(Y0:Y1)
const IB = [findfirst(==(y), years) for y in BASE0:BASE1]
const i2100 = findfirst(==(2100), years)
const TS_YEARS = 2000:10:2100              # band reported each decade (keeps CSV small)

SSPS = [("ssp119","SSP1-1.9"), ("ssp126","SSP1-2.6"), ("ssp245","SSP2-4.5"),
        ("ssp460","SSP4-6.0"), ("ssp370","SSP3-7.0"), ("ssp585","SSP5-8.5")]

# the 18 free PHYSICAL params, in posterior-CSV column order (= calibrate_mcmc.jl FREE)
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

N_DRAWS = length(ARGS) >= 1 ? parse(Int, ARGS[1]) : typemax(Int)
const TAG = length(ARGS) >= 2 ? String(ARGS[2]) : ""        # "" = 2018-baseline; "ext" = extended posterior
const SUF = isempty(TAG) ? "" : "_$(TAG)"
post   = CSV.read(joinpath(REPO, "data/MimiBRICK/parameters_subsample_brick_mengel$(SUF).csv"), DataFrame)
medoid = CSV.read(joinpath(REPO, "outputs/recalib_central_row.csv"), DataFrame)[1,:]
ncap = min(N_DRAWS, nrow(post))
println("BRICK-Mengel ensemble [$(isempty(TAG) ? "2018-baseline" : TAG) posterior]: $ncap draws × $(length(SSPS)) SSPs, FaIR v1.4.5-forced, UNWEIGHTED")

function load_traj(path, vcol)
    df = CSV.read(path, DataFrame)
    by = Dict(Int(df[i,"year"]) => Float64(df[i,vcol]) for i in 1:nrow(df))
    [by[y] for y in years]
end
rerefval(v, idx) = 100 * (v[idx] - sum(v[IB])/length(IB))   # cm rel 1995-2014 at idx
pcts(v) = (quantile(v,0.05), quantile(v,0.50), quantile(v,0.95))

summ = DataFrame(ssp=String[], ssp_label=String[],
                 p05=Float64[], p50=Float64[], p95=Float64[],
                 ais=Float64[], gsic=Float64[], gis=Float64[], te=Float64[], lws=Float64[])
tser = DataFrame(year=Int[], ssp_label=String[], p05=Float64[], p50=Float64[], p95=Float64[])

t_start = time()
for (ssp, label) in SSPS
    gmst = load_traj(joinpath(OBSDIR,"fair_mean_gmst_$ssp.csv"), "gmst_C")
    ohc  = load_traj(joinpath(OBSDIR,"fair_mean_ohc_$ssp.csv"),  "ohc_1e22J")
    # build the Mengel model + medoid fixed params once; forcing + free params per draw
    m = build_brick_mengel(ssp="ssp245", y0=Y0, y1=Y1)
    update_brick_mengel!(m, medoid, (a=0.45,b=0.52,T_lia=-0.45,f=0.5,tau_fast=40.0,tau_slow=250.0,sl0=0.0); precip_log=true)

    tot_ts = Array{Float64}(undef, ncap, length(years))
    comp2100 = (ais=zeros(ncap), gsic=zeros(ncap), gis=zeros(ncap), te=zeros(ncap), lws=zeros(ncap))
    for i in 1:ncap
        @inbounds for k in 1:length(PHYS)
            update_param!(m, PHYS[k][1], PHYS[k][2], Float64(post[i, PHYS_NAMES[k]]))
        end
        set_forcing!(m, gmst, ohc); run(m)
        gmsl = m[:global_sea_level, :sea_level_rise]
        base = sum(gmsl[IB])/length(IB)
        @inbounds for t in eachindex(years); tot_ts[i,t] = 100*(gmsl[t]-base); end
        comp2100.ais[i]  = rerefval(m[:antarctic_icesheet,:ais_sea_level], i2100)
        comp2100.gsic[i] = rerefval(m[:glaciers_small_icecaps,:gsic_sea_level], i2100)
        comp2100.gis[i]  = rerefval(m[:greenland_icesheet,:greenland_sea_level], i2100)
        comp2100.te[i]   = rerefval(m[:thermal_expansion,:te_sea_level], i2100)
        comp2100.lws[i]  = rerefval(m[:landwater_storage,:lws_sea_level], i2100)
    end
    a,b,c = pcts(tot_ts[:,i2100])
    push!(summ, (ssp, label, a, b, c, median(comp2100.ais), median(comp2100.gsic),
                 median(comp2100.gis), median(comp2100.te), median(comp2100.lws)))
    for y in TS_YEARS
        t = findfirst(==(y), years); a,b,c = pcts(tot_ts[:,t])
        push!(tser, (y, label, a, b, c))
    end
    @printf("%-9s done  (%.0fs elapsed)\n", label, time()-t_start)
end

CSV.write(joinpath(REPO,"outputs/proj_ssps_mengel$(SUF)_summary.csv"), summ)
CSV.write(joinpath(REPO,"outputs/proj_ssps_mengel$(SUF)_timeseries.csv"), tser)
println("\nWrote outputs/proj_ssps_mengel$(SUF)_{summary,timeseries}.csv  ($(round(time()-t_start))s)")

println("\n=== GMSL @2100 (cm, rel 1995-2014), $ncap-draw BRICK-Mengel posterior, FaIR v1.4.5 ===")
println(rpad("scenario",11), "  p05   p50   p95   |  AIS  GSIC   GIS    TE   LWS  (median, cm)")
for r in eachrow(summ)
    @printf("%-11s %5.1f %5.1f %5.1f   | %5.1f %5.1f %5.1f %5.1f %5.1f\n",
            r.ssp_label, r.p05, r.p50, r.p95, r.ais, r.gsic, r.gis, r.te, r.lws)
end
