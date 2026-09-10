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

using CSV, DataFrames, Mimi, MimiBRICK, Statistics, Printf, Random
include(joinpath(@__DIR__, "brick_mengel.jl"))      # set_forcing! + (transitively) update_brick_params!

const REPO = abspath(joinpath(@__DIR__, ".."))
const OBS  = joinpath(REPO, "data/observations")
const Y0, Y1, B0, B1 = 1850, 2026, 1995, 2005
years = collect(Y0:Y1); ib = [findfirst(==(y),years) for y in B0:B1]; idx(y)=findfirst(==(y),years)
NDRAW = length(ARGS) >= 1 ? parse(Int, ARGS[1]) : typemax(Int)
## OUTPUT SPAN. The MODEL runs Y0-Y1 (1850-2026); this only says which years are SAVED.
## Was 1920, which was neither a model property nor a scientific choice -- but it silently set
## the evaluation window of the whole Ladrillo-vs-BRICK scorecard, because that script scores on
## `Ladrillo.index INTERSECT BRICK.index`. That discarded 1900-1919 from every RMSE ratio and
## from the cumulative-rise number, i.e. exactly the early era where the gain is claimed.
## Now matched to the Ladrillo driver's own FY0 (posterior_predictive_ext.jl:33 = 1900), which is
## also the panel's x-axis start and the first year of the total target.
## ⚠ reref() is computed on the FULL 1850-based vector BEFORE this subset, so lowering FY0 CANNOT
## move an existing value -- the 1920+ rows must come back BIT-IDENTICAL. That is asserted after
## the run, against a pre-change copy, and it is the regression test for this change.
const FY0, FY1 = 1900, Y1
FY = collect(FY0:FY1); myi=[idx(y) for y in FY]

lc(p,c)=(d=CSV.read(p,DataFrame); Dict(Int(d[i,"year"])=>Float64(d[i,c]) for i in 1:nrow(d)))
gmst=[lc(joinpath(OBS,"fair_mean_gmst.csv"),"gmst_C")[y] for y in years]
ohc =[lc(joinpath(OBS,"fair_mean_ohc.csv"),"ohc_1e22J")[y] for y in years]

## ⭐ SEED, ADDED 2026-09-10 -- THIS DRIVER WAS THE ONLY UNSEEDED ONE.
## `MimiBRICK.get_model()` draws from the UNSEEDED global RNG (the mimibrick-quirks item 1
## non-determinism, and the LWS realization with it), so two runs of this script produced
## DIFFERENT numbers: measured 5.05e-02 cm on the total and 3.3e-04 on AIS, with gsic/gis/te
## exactly zero. Every BRICK 2.0 figure in the L24 deliverable therefore carried ~0.05 cm of
## run-to-run jitter and could not be reproduced.
## SEED VALUE IS NOT NEW: `Random.seed!(2026)` immediately before `get_model` is the convention
## already used by diag_component_hindcast.jl, diag_brick20_crossmodel.jl, diag_annual_step_pulse.jl,
## diag_brick_level_distribution.jl, diag_decomposition{,_pulse}.jl and diag_nonoise_pulse_median.jl,
## and it matches `brick_mengel.jl`'s LWS_SEED = 2026. It is the BRICK-2.0/`main` form of the
## project's LWS lock ("seed before get_model"), so this driver now agrees with its siblings.
## ⚠ The seed MUST be set immediately before get_model: it is get_model that consumes the stream.
## ⚠ The seed is RECORDED IN THE OUTPUT (provenance column below), not only here, so the file
## can be re-run from the file itself.
const SEED = 2026
Random.seed!(SEED)
# stock BRICK (single-reservoir glacier), old posterior, FaIR-forced
m = MimiBRICK.get_model(ssprcp_scenario="ssp245", start_year=Y0, end_year=Y1)
set_forcing!(m, gmst, ohc)
reref(v)=100 .* (v .- sum(v[ib])/length(ib))
post = CSV.read(joinpath(REPO,"data/MimiBRICK/parameters_subsample_brick.csv"), DataFrame)
ND = min(NDRAW, nrow(post))
println("OLD-BRICK posterior-predictive: $ND draws × stock BRICK forward ($Y0-$Y1), saving $FY0-$FY1...")

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
## PROVENANCE IN THE FILE ITSELF. A seed recorded only in the script is lost the moment the
## CSV is read somewhere else; this column makes the run re-creatable from the artifact.
band[!, "provenance"] = fill(
    "posterior_predictive_oldbrick.jl | stock MimiBRICK get_model(ssp245) | " *
    "Random.seed!($SEED) immediately before get_model | posterior " *
    "data/MimiBRICK/parameters_subsample_brick.csv ND=$ND | forcing fair_mean_{gmst,ohc}.csv | " *
    "run $Y0-$Y1, saved $FY0-$FY1, re-referenced $B0-$B1 | cm", ny)
CSV.write(joinpath(REPO,"outputs/postpred_oldbrick_components_timeseries.csv"), band)
println("Wrote outputs/postpred_oldbrick_components_timeseries.csv (seed $SEED, ND=$ND)")
