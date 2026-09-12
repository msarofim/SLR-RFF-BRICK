## ============================================================================
## diag_brick_gsic_melt_1850_2000.jl — BRICK 2.0's OWN glacier melt from its 1850 start to
## 2000 and 2020, so its 42 cm initial volume can be put on Farinotti's ~2000 basis
## (Marcus, 2026-09-12: the attribute table's inventories carry different epochs).
##
## Same posterior, forcing, seed and model construction as posterior_predictive_oldbrick.jl
## (which SAVES from 1900 because the observed-LWS splice needs obs coverage); this reads the
## glacier component alone from 1850 and reports increments, never a re-referenced level.
##   julia --project=julia_v2 julia/diag_brick_gsic_melt_1850_2000.jl [n_draws]
## ============================================================================
using CSV, DataFrames, Mimi, MimiBRICK, Statistics, Printf, Random
include(joinpath(@__DIR__, "brick_mengel.jl"))

const REPO = abspath(joinpath(@__DIR__, ".."))
const OBS  = joinpath(REPO, "data/observations")
const Y0, Y1 = 1850, 2026
const FORCING = "ssp245harm"                       # as posterior_predictive_oldbrick.jl
const SEED = 2026                                  # same convention, same placement
NDRAW = length(ARGS) >= 1 ? parse(Int, ARGS[1]) : typemax(Int)
years = collect(Y0:Y1); idx(y)=findfirst(==(y),years)
lc(p,c)=(d=CSV.read(p,DataFrame); Dict(Int(d[i,"year"])=>Float64(d[i,c]) for i in 1:nrow(d)))
gmst=[lc(joinpath(OBS,"fair_mean_gmst_$(FORCING).csv"),"gmst_C")[y] for y in years]
ohc =[lc(joinpath(OBS,"fair_mean_ohc_$(FORCING).csv"),"ohc_1e22J")[y] for y in years]

Random.seed!(SEED)
m = MimiBRICK.get_model(ssprcp_scenario="ssp245", start_year=Y0, end_year=Y1)
set_forcing!(m, gmst, ohc)
post = CSV.read(joinpath(REPO,"data/MimiBRICK/parameters_subsample_brick.csv"), DataFrame)
ND = min(NDRAW, nrow(post))
EPOCHS = (1900, 2000, 2020)
inc = Dict(y => Vector{Float64}(undef, ND) for y in EPOCHS)
v0  = Vector{Float64}(undef, ND)
@time for i in 1:ND
    update_brick_params!(m, post[i,:]; precip_log=true)
    run(m)
    g = 100 .* m[:glaciers_small_icecaps, :gsic_sea_level]      # m -> cm, level from 1850
    for y in EPOCHS; inc[y][i] = g[idx(y)] - g[idx(Y0)]; end
    v0[i] = 100 * Float64(post[i, "glaciers_v0"])                # initial volume, cm SLE
end
q(v) = (quantile(v,0.05), quantile(v,0.50), quantile(v,0.95))
rows = DataFrame(quantity=String[], p05=Float64[], p50=Float64[], p95=Float64[])
for y in EPOCHS
    a,b,c = q(inc[y]); push!(rows, ("gsic_melt_1850_to_$(y)_cm", a,b,c))
end
a,b,c = q(v0);            push!(rows, ("glaciers_v0_cm", a,b,c))
a,b,c = q(v0 .- inc[2000]); push!(rows, ("remaining_at_2000_cm", a,b,c))
a,b,c = q(v0 .- inc[2020]); push!(rows, ("remaining_at_2020_cm", a,b,c))
rows[!, "provenance"] = fill("diag_brick_gsic_melt_1850_2000.jl | stock MimiBRICK get_model(ssp245) | " *
    "Random.seed!($SEED) immediately before get_model | posterior parameters_subsample_brick.csv ND=$ND | " *
    "forcing fair_mean_{gmst,ohc}_$(FORCING).csv | run $Y0-$Y1 | increments from the 1850 level, cm SLE", nrow(rows))
CSV.write(joinpath(REPO,"outputs/diag_brick_gsic_melt_1850_2000.csv"), rows)
println("BRICK 2.0 glaciers, ND=$ND draws (cm SLE, p05 / p50 / p95):")
for r in eachrow(rows); @printf("  %-28s %6.1f %6.1f %6.1f\n", r.quantity, r.p05, r.p50, r.p95); end
