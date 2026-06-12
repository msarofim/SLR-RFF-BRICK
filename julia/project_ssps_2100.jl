## ============================================================================
## project_ssps_2100.jl  —  SSP projections to 2100, v2.0.0 vs preliminary recal
##
## For Tony: forward GMSL projection to 2100 under 6 SSPs, comparing the v2.0.0
## (published post-#93) calibration against the preliminary central recalibration.
## BOTH calibrations are driven by the SAME FaIR v1.4.5 ensemble-mean GMST + OHC
## per SSP (run_fair_ssps.py; obs-driven override, NOT SNEASY) — FaIR is the more
## trusted climate model and matches the forcing the recalibration was built on.
## The only difference between the two columns is the recalibrated parameters.
## Central = the MEDOID posterior draw for both. SLR re-referenced to AR6 1995-2014.
##
##   julia --project=julia_v2 julia/project_ssps_2100.jl
## ============================================================================

using CSV, DataFrames, Mimi, MimiBRICK, Printf

include(joinpath(@__DIR__, "brick_param_updates.jl"))

const REPO = abspath(joinpath(@__DIR__, ".."))
const CENTRAL_ROW = joinpath(REPO, "outputs/recalib_central_row.csv")
const KNOBS = joinpath(REPO, "outputs/recalib_knobs.csv")
const OBSDIR = joinpath(REPO, "data/observations")
const Y0, Y1 = 1850, 2100
const BASE0, BASE1 = 1995, 2014        # AR6 SLR baseline
years = collect(Y0:Y1)
const IB = [findfirst(==(y), years) for y in BASE0:BASE1]
i2100 = findfirst(==(2100), years)

# SSP -> RCMIP forcing-file tag, display label (ordered by radiative forcing)
SSPS = [("ssp119","SSP1-1.9"), ("ssp126","SSP1-2.6"), ("ssp245","SSP2-4.5"),
        ("ssp460","SSP4-6.0"), ("ssp370","SSP3-7.0"), ("ssp585","SSP5-8.5")]

medrow = CSV.read(CENTRAL_ROW, DataFrame)[1, :]
knobs  = CSV.read(KNOBS, DataFrame)
println("Central = medoid post_idx=$(medrow.medoid_post_idx); $(nrow(knobs)) recalibrated knobs; FaIR-forced")

# load a FaIR trajectory CSV on the BRICK window
function load_traj(path, vcol)
    df = CSV.read(path, DataFrame)
    by = Dict(Int(df[i, "year"]) => Float64(df[i, vcol]) for i in 1:nrow(df))
    [by[y] for y in years]
end

reref(v) = 100 .* (v .- sum(v[IB])/length(IB))   # m -> cm, rel 1995-2014

function components(m)
    (ais  = reref(m[:antarctic_icesheet,     :ais_sea_level]),
     gsic = reref(m[:glaciers_small_icecaps, :gsic_sea_level]),
     gis  = reref(m[:greenland_icesheet,     :greenland_sea_level]),
     te   = reref(m[:thermal_expansion,      :te_sea_level]),
     lws  = reref(m[:landwater_storage,      :lws_sea_level]),
     tot  = reref(m[:global_sea_level,       :sea_level_rise]))
end

summary = DataFrame(ssp=String[], ssp_label=String[], calib=String[], gmst2100=Float64[],
                    total=Float64[], ais=Float64[], gsic=Float64[], gis=Float64[], te=Float64[], lws=Float64[])
tseries = DataFrame(year=Int[], ssp_label=String[], calib=String[], total=Float64[])

for (ssp, label) in SSPS
    gmst = load_traj(joinpath(OBSDIR, "fair_mean_gmst_$ssp.csv"), "gmst_C")
    ohc  = load_traj(joinpath(OBSDIR, "fair_mean_ohc_$ssp.csv"),  "ohc_1e22J")
    g2100 = gmst[i2100]

    # build once; get_model scenario is irrelevant (forcing is overridden)
    m = MimiBRICK.get_model(ssprcp_scenario="ssp245", start_year=Y0, end_year=Y1)

    function set_forcing!(mm)
        update_param!(mm, :model_global_surface_temperature, gmst)
        update_param!(mm, :thermal_expansion, :ocean_heat_interior, ohc)
    end

    # --- v2.0.0 calibration: medoid posterior as-is ---
    update_brick_params!(m, medrow; precip_log=true); set_forcing!(m)
    run(m); c0 = components(m)

    # --- new calibration: medoid + recalibrated knob overrides ---
    update_brick_params!(m, medrow; precip_log=true)
    for r in eachrow(knobs)
        update_param!(m, Symbol(r.component), Symbol(r.symbol), r.after)
    end
    set_forcing!(m)
    run(m); c1 = components(m)

    for (cal, c) in [("v2.0.0", c0), ("new", c1)]
        push!(summary, (ssp, label, cal, g2100, c.tot[i2100], c.ais[i2100], c.gsic[i2100],
                        c.gis[i2100], c.te[i2100], c.lws[i2100]))
        for (i, y) in enumerate(years)
            y >= 2000 && push!(tseries, (y, label, cal, c.tot[i]))
        end
    end
    @printf("%-9s  GMST@2100 %+.2f°C   v2.0.0 SLR@2100 = %5.1f cm   new = %5.1f cm   (Δ %+.1f)\n",
            label, g2100, c0.tot[i2100], c1.tot[i2100], c1.tot[i2100]-c0.tot[i2100])
end

CSV.write(joinpath(REPO, "outputs/proj_ssps_2100_summary.csv"), summary)
CSV.write(joinpath(REPO, "outputs/proj_ssps_2100_timeseries.csv"), tseries)
println("\nWrote outputs/proj_ssps_2100_{summary,timeseries}.csv")

println("\n=== GMSL @2100 (cm, rel 1995-2014), FaIR v1.4.5-forced ===")
println(rpad("scenario",10), rpad("calib",8), " GMST  total   AIS   GSIC   GIS    TE   LWS")
for r in eachrow(summary)
    @printf("%-10s%-8s %4.1f %6.1f %5.1f %5.1f %5.1f %5.1f %5.1f\n",
            r.ssp_label, r.calib, r.gmst2100, r.total, r.ais, r.gsic, r.gis, r.te, r.lws)
end
