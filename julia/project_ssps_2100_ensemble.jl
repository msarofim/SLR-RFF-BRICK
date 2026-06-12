## ============================================================================
## project_ssps_2100_ensemble.jl  —  ENSEMBLE SSP projections to 2100
##
## Ensemble version of project_ssps_2100.jl: instead of the medoid only, loop over
## N posterior draws so we get a 5-50-95 band and SMOOTH the DAIS-MICI step (the
## antarctic_temp_threshold varies across draws). Two calibrations:
##   v2.0.0 : each posterior draw as-is.
##   new    : each posterior draw + the 10 recalibrated knob overrides (the
##            recalibration only produced central knob VALUES, so they are applied
##            ensemble-wide; the non-recalibrated params — incl. the MICI threshold —
##            keep their per-draw posterior values, so both bands smooth the step).
## FaIR v1.4.5-forced per SSP; SLR rel AR6 1995-2014.
##
##   julia --project=julia_v2 julia/project_ssps_2100_ensemble.jl [N_DRAWS]
## ============================================================================

using CSV, DataFrames, Mimi, MimiBRICK, Statistics, Printf

include(joinpath(@__DIR__, "brick_param_updates.jl"))

const REPO = abspath(joinpath(@__DIR__, ".."))
const OBSDIR = joinpath(REPO, "data/observations")
const Y0, Y1 = 1850, 2100
const BASE0, BASE1 = 1995, 2014
years = collect(Y0:Y1)
const IB = [findfirst(==(y), years) for y in BASE0:BASE1]
const i2100 = findfirst(==(2100), years)
const TS_YEARS = 2000:10:2100               # band reported each decade (keeps CSV small)

SSPS = [("ssp119","SSP1-1.9"), ("ssp126","SSP1-2.6"), ("ssp245","SSP2-4.5"),
        ("ssp460","SSP4-6.0"), ("ssp370","SSP3-7.0"), ("ssp585","SSP5-8.5")]

N_DRAWS = length(ARGS) >= 1 ? parse(Int, ARGS[1]) : 2000
post  = CSV.read(joinpath(REPO, "data/MimiBRICK/parameters_subsample_brick.csv"), DataFrame)
knobs = CSV.read(joinpath(REPO, "outputs/recalib_knobs.csv"), DataFrame)
ncap = min(N_DRAWS, nrow(post))
println("Ensemble: $ncap draws x $(length(SSPS)) SSPs x 2 calibrations, FaIR-forced")

function load_traj(path, vcol)
    df = CSV.read(path, DataFrame)
    by = Dict(Int(df[i,"year"]) => Float64(df[i,vcol]) for i in 1:nrow(df))
    [by[y] for y in years]
end
rerefval(v, idx) = 100 * (v[idx] - sum(v[IB])/length(IB))   # cm rel 1995-2014 at idx
pcts(v) = (quantile(v,0.05), quantile(v,0.50), quantile(v,0.95))

summ = DataFrame(ssp=String[], ssp_label=String[], calib=String[],
                 p05=Float64[], p50=Float64[], p95=Float64[],
                 ais=Float64[], gsic=Float64[], gis=Float64[], te=Float64[], lws=Float64[])
tser = DataFrame(year=Int[], ssp_label=String[], calib=String[], p05=Float64[], p50=Float64[], p95=Float64[])

t_start = time()
for (ssp, label) in SSPS
    gmst = load_traj(joinpath(OBSDIR,"fair_mean_gmst_$ssp.csv"), "gmst_C")
    ohc  = load_traj(joinpath(OBSDIR,"fair_mean_ohc_$ssp.csv"),  "ohc_1e22J")
    m = MimiBRICK.get_model(ssprcp_scenario="ssp245", start_year=Y0, end_year=Y1)
    setf!() = (update_param!(m,:model_global_surface_temperature,gmst);
               update_param!(m,:thermal_expansion,:ocean_heat_interior,ohc))

    for (cal, apply_knobs) in [("v2.0.0", false), ("new", true)]
        tot_ts = Array{Float64}(undef, ncap, length(years))   # total trajectory per draw
        comp2100 = (ais=zeros(ncap), gsic=zeros(ncap), gis=zeros(ncap), te=zeros(ncap), lws=zeros(ncap))
        for i in 1:ncap
            update_brick_params!(m, post[i,:]; precip_log=true)
            if apply_knobs
                for r in eachrow(knobs); update_param!(m, Symbol(r.component), Symbol(r.symbol), r.after); end
            end
            setf!(); run(m)
            gmsl = m[:global_sea_level, :sea_level_rise]
            base = sum(gmsl[IB])/length(IB)
            @inbounds for t in eachindex(years); tot_ts[i,t] = 100*(gmsl[t]-base); end
            comp2100.ais[i]  = rerefval(m[:antarctic_icesheet,:ais_sea_level], i2100)
            comp2100.gsic[i] = rerefval(m[:glaciers_small_icecaps,:gsic_sea_level], i2100)
            comp2100.gis[i]  = rerefval(m[:greenland_icesheet,:greenland_sea_level], i2100)
            comp2100.te[i]   = rerefval(m[:thermal_expansion,:te_sea_level], i2100)
            comp2100.lws[i]  = rerefval(m[:landwater_storage,:lws_sea_level], i2100)
        end
        p05,p50,p95 = pcts(tot_ts[:,i2100])
        push!(summ, (ssp, label, cal, p05, p50, p95,
                     median(comp2100.ais), median(comp2100.gsic), median(comp2100.gis),
                     median(comp2100.te), median(comp2100.lws)))
        for y in TS_YEARS
            t = findfirst(==(y), years); a,b,c = pcts(tot_ts[:,t])
            push!(tser, (y, label, cal, a, b, c))
        end
    end
    @printf("%-9s done  (%.0fs elapsed)\n", label, time()-t_start)
end

CSV.write(joinpath(REPO,"outputs/proj_ssps_ensemble_summary.csv"), summ)
CSV.write(joinpath(REPO,"outputs/proj_ssps_ensemble_timeseries.csv"), tser)
println("\nWrote outputs/proj_ssps_ensemble_{summary,timeseries}.csv  ($(round(time()-t_start))s total)")

println("\n=== GMSL @2100 (cm, rel 1995-2014), $ncap-draw ensemble, FaIR v1.4.5 ===")
println(rpad("scenario",10), rpad("calib",8), "  p05   p50   p95   |  AIS  GSIC  GIS   TE  LWS  (medians)")
for r in eachrow(summ)
    @printf("%-10s%-8s %5.1f %5.1f %5.1f  | %5.1f %5.1f %5.1f %5.1f %5.1f\n",
            r.ssp_label, r.calib, r.p05, r.p50, r.p95, r.ais, r.gsic, r.gis, r.te, r.lws)
end
