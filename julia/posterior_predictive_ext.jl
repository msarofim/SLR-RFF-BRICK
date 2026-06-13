## ============================================================================
## posterior_predictive_ext.jl  —  obs/historical check of the EXTENDED BRICK-Mengel
##
## Variant of posterior_predictive.jl for the post-2018-extended re-fit. Forward-runs
## the extended posterior (parameters_subsample_brick_mengel_ext.csv) over 1900-2026
## and compares 5/50/95 component bands to the EXTENDED targets (recalib_targets_ext.csv:
## Frederikse + GRACE-FO/GlaMBIE/NOAA splices). Per-series obs end at different years
## (AIS/GIS 2025, GSIC 2023, TE 2025, total 2024); bands are reported over the full
## 1900-2026 model window, obs attached where present.
##
## Reports component bias (median - obs) at BOTH 2018 (compare to the 2018-baseline:
## AIS -0.04, GSIC +0.15, GIS -0.23, TE +0.61, total -0.41) AND at the extension end,
## plus the AIS plateau years 2020/2022/2024 -- does the new fit track the GRACE-FO pause?
## No importance weighting (posterior calibrated directly to the data). Same sanity tests.
##
##   julia --project=julia_v2 julia/posterior_predictive_ext.jl [n_draws]
## ============================================================================

using CSV, DataFrames, Mimi, MimiBRICK, Statistics, Printf
include(joinpath(@__DIR__, "brick_mengel.jl"))

const REPO = abspath(joinpath(@__DIR__, ".."))
const OBS  = joinpath(REPO, "data/observations")
const Y0, Y1, B0, B1 = 1850, 2026, 1995, 2005
const TAG = "ext"
years = collect(Y0:Y1); ib = [findfirst(==(y),years) for y in B0:B1]; idx(y)=findfirst(==(y),years)
NDRAW = length(ARGS) >= 1 ? parse(Int, ARGS[1]) : typemax(Int)

lc(p,c)=(d=CSV.read(p,DataFrame); Dict(Int(d[i,"year"])=>Float64(d[i,c]) for i in 1:nrow(d)))
gmst=[lc(joinpath(OBS,"fair_mean_gmst.csv"),"gmst_C")[y] for y in years]
ohc =[lc(joinpath(OBS,"fair_mean_ohc.csv"),"ohc_1e22J")[y] for y in years]
tg = CSV.read(joinpath(REPO,"outputs/recalib_targets_ext.csv"), DataFrame); tgi(y)=findfirst(==(y),tg.year)
FY = collect(1900:2026); fyi=[tgi(y) for y in FY]; myi=[idx(y) for y in FY]
present(col,y) = (r=tgi(y); !ismissing(tg[r,col]) && !isnan(Float64(tg[r,col])))

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

medoid = CSV.read(joinpath(REPO,"outputs/recalib_central_row.csv"), DataFrame)[1,:]
m = build_brick_mengel(ssp="ssp245", y0=Y0, y1=Y1)
update_brick_mengel!(m, medoid, (a=0.45,b=0.52,T_lia=-0.45,f=0.5,tau_fast=40.0,tau_slow=250.0,sl0=0.0); precip_log=true)
set_forcing!(m, gmst, ohc)
reref(v)=100 .* (v .- sum(v[ib])/length(ib))
lws_fy = Float64.(tg.lws[fyi])     # LWS budget (held const post-2018 in the ext targets)

function run_draw!(row)
    @inbounds for k in 1:length(PHYS)
        update_param!(m, PHYS[k][1], PHYS[k][2], Float64(row[PHYS_NAMES[k]]))
    end
    run(m)
    ais  = reref(m[:antarctic_icesheet, :ais_sea_level])[myi]
    gsic = reref(m[:glaciers_small_icecaps, :gsic_sea_level])[myi]
    gis  = reref(m[:greenland_icesheet, :greenland_sea_level])[myi]
    te   = reref(m[:thermal_expansion, :te_sea_level])[myi]
    tot  = ais .+ gsic .+ gis .+ te .+ lws_fy
    return (ais=ais, gsic=gsic, gis=gis, te=te, total=tot)
end

post = CSV.read(joinpath(REPO,"data/MimiBRICK/parameters_subsample_brick_mengel_$(TAG).csv"), DataFrame)
ND = min(NDRAW, nrow(post))
println("Posterior-predictive [EXTENDED]: $ND draws × BRICK-Mengel forward (1900-2026)...")
comps = (:ais, :gsic, :gis, :te, :total); ny = length(FY)
store = Dict(c => Array{Float64}(undef, ND, ny) for c in comps)
@time for i in 1:ND
    r = run_draw!(post[i, :])
    for c in comps; store[c][i, :] = getfield(r, c); end
end

band = DataFrame(year=FY)
for c in comps
    band[!, "$(c)_p5"]  = [quantile(store[c][:,j], 0.05) for j in 1:ny]
    band[!, "$(c)_p50"] = [quantile(store[c][:,j], 0.50) for j in 1:ny]
    band[!, "$(c)_p95"] = [quantile(store[c][:,j], 0.95) for j in 1:ny]
end
for (c, ocol) in [(:ais,:ais),(:gsic,:gsic),(:gis,:gis),(:te,:steric),(:total,:dang)]
    band[!, "$(c)_obs"] = [present(ocol,y) ? Float64(tg[tgi(y),ocol]) : missing for y in FY]
end
CSV.write(joinpath(REPO,"outputs/postpred_$(TAG)_components_timeseries.csv"), band)
println("Wrote outputs/postpred_$(TAG)_components_timeseries.csv")

# ---- component bias (median - obs) at key years: 2018 (vs baseline), end-year, AIS plateau ----
obscol = Dict(:ais=>:ais,:gsic=>:gsic,:gis=>:gis,:te=>:steric,:total=>:dang)
endyr  = Dict(c => maximum(y for y in FY if present(obscol[c],y)) for c in comps)
println("\nComponent bias (model p50 - obs, cm).  Baseline@2018 for reference: AIS -0.04 GSIC +0.15 GIS -0.23 TE +0.61 tot -0.41")
biasrows = DataFrame(component=String[], year=Int[], obs=Float64[], p50=Float64[], bias=Float64[], in90=Bool[])
function report(c, y)
    present(obscol[c], y) || return
    j = findfirst(==(y), FY); o = Float64(tg[tgi(y), obscol[c]])
    p50 = band[j,"$(c)_p50"]; p5 = band[j,"$(c)_p5"]; p95 = band[j,"$(c)_p95"]
    inb = (o >= p5) && (o <= p95)
    @printf("  %-7s %d  obs=%6.2f  p50=%6.2f  bias=%+.2f  %s\n", c, y, o, p50, p50-o, inb ? "(in 90%)" : "(OUT)")
    push!(biasrows, (string(c), y, o, p50, p50-o, inb))
end
println(" @2018:");        for c in comps; report(c, 2018); end
println(" @extension end:"); for c in comps; report(c, endyr[c]); end
println(" AIS plateau:");  for y in [2019,2020,2022,2024,2025]; report(:ais, y); end
CSV.write(joinpath(REPO,"outputs/postpred_$(TAG)_bias.csv"), biasrows)

# ---- determinism sanity ----
println("\n[sanity] determinism: re-run draw 1 twice...")
a1 = run_draw!(post[1, :]); a2 = run_draw!(post[1, :])
maxdiff = maximum(maximum(abs.(getfield(a1,c) .- getfield(a2,c))) for c in comps)
@printf("  max |Δ| = %.2e  ->  %s\n", maxdiff, maxdiff < 1e-12 ? "PASS" : "FAIL")
println("\nposterior_predictive_ext.jl DONE -> outputs/postpred_$(TAG)_{components_timeseries,bias}.csv")
