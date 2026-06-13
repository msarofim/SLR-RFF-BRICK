## ============================================================================
## posterior_predictive_oldbrick.jl  —  hindcast of the OLD (stock) BRICK
##
## Companion to posterior_predictive_ext.jl: forward-runs the STOCK single-reservoir
## BRICK (no Mengel swap) with the OLD posterior (parameters_subsample_brick.csv) over
## 1850-2026 under the SAME FaIR forcing + 1995-2005 reref, and writes 5/50/95 component
## bands. Used only to overlay "old BRICK" on the historical-comparison figure so the
## effect of (Mengel glacier + recalibration + extension) on the hindcast is visible.
##
##   julia --project=julia_v2 julia/posterior_predictive_oldbrick.jl [n_draws]
## ============================================================================

using CSV, DataFrames, Mimi, MimiBRICK, Statistics, Printf
include(joinpath(@__DIR__, "brick_mengel.jl"))      # set_forcing! + (transitively) update_brick_params!

const REPO = abspath(joinpath(@__DIR__, ".."))
const OBS  = joinpath(REPO, "data/observations")
const Y0, Y1, B0, B1 = 1850, 2026, 1995, 2005
years = collect(Y0:Y1); ib = [findfirst(==(y),years) for y in B0:B1]; idx(y)=findfirst(==(y),years)
NDRAW = length(ARGS) >= 1 ? parse(Int, ARGS[1]) : typemax(Int)
FY = collect(1920:2026); myi=[idx(y) for y in FY]      # plot starts 1920

lc(p,c)=(d=CSV.read(p,DataFrame); Dict(Int(d[i,"year"])=>Float64(d[i,c]) for i in 1:nrow(d)))
gmst=[lc(joinpath(OBS,"fair_mean_gmst.csv"),"gmst_C")[y] for y in years]
ohc =[lc(joinpath(OBS,"fair_mean_ohc.csv"),"ohc_1e22J")[y] for y in years]

# stock BRICK (single-reservoir glacier), old posterior, FaIR-forced
m = MimiBRICK.get_model(ssprcp_scenario="ssp245", start_year=Y0, end_year=Y1)
set_forcing!(m, gmst, ohc)
reref(v)=100 .* (v .- sum(v[ib])/length(ib))
post = CSV.read(joinpath(REPO,"data/MimiBRICK/parameters_subsample_brick.csv"), DataFrame)
ND = min(NDRAW, nrow(post))
println("OLD-BRICK posterior-predictive: $ND draws × stock BRICK forward (1850-2026)...")

comps = (:ais, :gsic, :gis, :te, :total); ny = length(FY)
store = Dict(c => Array{Float64}(undef, ND, ny) for c in comps)
@time for i in 1:ND
    update_brick_params!(m, post[i,:]; precip_log=true)
    run(m)
    ais  = reref(m[:antarctic_icesheet, :ais_sea_level])[myi]
    gsic = reref(m[:glaciers_small_icecaps, :gsic_sea_level])[myi]
    gis  = reref(m[:greenland_icesheet, :greenland_sea_level])[myi]
    te   = reref(m[:thermal_expansion, :te_sea_level])[myi]
    lws  = reref(m[:landwater_storage, :lws_sea_level])[myi]
    store[:ais][i,:]=ais; store[:gsic][i,:]=gsic; store[:gis][i,:]=gis; store[:te][i,:]=te
    store[:total][i,:]=ais.+gsic.+gis.+te.+lws
end
band = DataFrame(year=FY)
for c in comps
    band[!, "$(c)_p5"]  = [quantile(store[c][:,j], 0.05) for j in 1:ny]
    band[!, "$(c)_p50"] = [quantile(store[c][:,j], 0.50) for j in 1:ny]
    band[!, "$(c)_p95"] = [quantile(store[c][:,j], 0.95) for j in 1:ny]
end
CSV.write(joinpath(REPO,"outputs/postpred_oldbrick_components_timeseries.csv"), band)
println("Wrote outputs/postpred_oldbrick_components_timeseries.csv")
