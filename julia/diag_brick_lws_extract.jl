## Read-only: extract BRICK 2.0's OWN landwater_storage over the hindcast, to test whether it is
## identically zero before first_projection_year (mimibrick-quirks item 6) rather than infer it
## from a quantile-of-sum subtraction.
using CSV, DataFrames, Mimi, MimiBRICK, Statistics, Printf, Random
include(joinpath(@__DIR__, "brick_mengel.jl"))
const REPO = abspath(joinpath(@__DIR__, "..")); const OBS = joinpath(REPO,"data/observations")
const Y0,Y1,B0,B1 = 1850,2026,1995,2005
years=collect(Y0:Y1); ib=[findfirst(==(y),years) for y in B0:B1]; idx(y)=findfirst(==(y),years)
lc(p,c)=(d=CSV.read(p,DataFrame); Dict(Int(d[i,"year"])=>Float64(d[i,c]) for i in 1:nrow(d)))
gmst=[lc(joinpath(OBS,"fair_mean_gmst.csv"),"gmst_C")[y] for y in years]
ohc =[lc(joinpath(OBS,"fair_mean_ohc.csv"),"ohc_1e22J")[y] for y in years]
Random.seed!(2026)
m = MimiBRICK.get_model(ssprcp_scenario="ssp245", start_year=Y0, end_year=Y1)
set_forcing!(m, gmst, ohc)
post = CSV.read(joinpath(REPO,"data/MimiBRICK/parameters_subsample_brick.csv"), DataFrame)
reref(v)=100 .* (v .- sum(v[ib])/length(ib))
mat = zeros(20, length(years))
for i in 1:20
    update_brick_params!(m, post[i,:]; precip_log=true); run(m)
    mat[i,:] = reref(m[:landwater_storage, :lws_sea_level])
end
@printf("BRICK 2.0 landwater_storage, cm rel %d-%d, across 20 posterior draws\n", B0, B1)
@printf("%6s %10s %10s %10s\n","year","min","median","max")
for y in (1900,1950,2000,2015,2018,2019,2020,2024,2026)
    c=mat[:,idx(y)]; @printf("%6d %10.4f %10.4f %10.4f\n", y, minimum(c), median(c), maximum(c))
end
nz = [y for y in years if any(abs.(mat[:,idx(y)]) .> 1e-9)]
@printf("\nfirst year ANY draw is nonzero: %s\n", isempty(nz) ? "never" : string(minimum(nz)))
