## diag_ais_leverage.jl — per-draw ssp245 AIS/GIS/total SLR at 2100/2300 for a posterior tag, joined to the draws, so a
## parameter's PROJECTION leverage (Spearman with AIS@2300) can be set against its identification (post/prior sd).
##   julia --project=julia_v2 julia/diag_ais_leverage.jl L26     -> outputs/diag_ais_leverage_draws_<tag>.csv

using CSV, DataFrames, Mimi, MimiBRICK, Statistics, Printf
include(joinpath("/Users/MarcusMarcus/Documents/2026/CodeProjects/SLR-RFF-BRICK/julia", "ladrillo_projection.jl"))
TAG = length(ARGS) >= 1 ? ARGS[1] : "L26"
path = joinpath(LADRILLO_REPO, "data/MimiBRICK/parameters_subsample_brick_mengel_$TAG.csv")
post = ladrillo_posterior(path=path, cols=:all, nthin=2000)
out = DataFrame(draw=Int[], ais2100=Float64[], ais2300=Float64[], gis2300=Float64[], tot2300=Float64[])
for ssp in ("ssp245",)
    bf = ladrillo_setup(ssp=ssp, y0=1850, y1=2300, gis_variant=ladrillo_posterior_variant(path)); ladrillo_set_tap!(bf)
    yrs = collect(1850:2300); yi(y) = findfirst(==(y), yrs)
    for (i, r) in enumerate(eachrow(post))
        ladrillo_run_draw!(bf, r)
        a = ladrillo_series(bf, :ais); g = ladrillo_series(bf, :gis); t = ladrillo_series(bf, :total)
        push!(out, (i, a[yi(2100)], a[yi(2300)], g[yi(2300)], t[yi(2300)]))
    end
end
CSV.write(joinpath(LADRILLO_REPO, "outputs/diag_ais_leverage_draws_$TAG.csv"), hcat(out, post[:, :]))
println("wrote outputs/diag_ais_leverage_draws_$TAG.csv  n=$(nrow(out))")
