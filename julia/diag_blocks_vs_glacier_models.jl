## ============================================================================
## diag_blocks_vs_glacier_models.jl — Ladrillo's three glacier reservoirs against
## the Zekollari et al. 2024 model archives, on the archives' own metric.
##
## Companion to python/scope_glacier_model_constraints.py, which aggregates
## GloGEM (zenodo.10908278) and OGGM (zenodo.8286065) to the same three blocks.
## Metric: % of 2015 block mass lost by the horizon, so the RGI/Farinotti vs
## OGGM/GloGEM inventory difference divides out.
##
## READ THE HISTORICAL CHECK IN THAT SCRIPT FIRST. Over 2000-2020 against GlaMBIE,
## OGGM is 1.01x on SLOWP and 0.97x on FAST but 3.11x on R19 -- so its SLOWP/FAST
## projections are historically validated and its R19 projections are not.
##
##   julia --project=julia_v2 julia/diag_blocks_vs_glacier_models.jl [n_draws]
## Writes outputs/diag_blocks_vs_glacier_models.csv
## ============================================================================

using CSV, DataFrames, Mimi, Printf, Statistics
include(joinpath(@__DIR__, "ladrillo_projection.jl"))

const OUT   = joinpath(LADRILLO_REPO, "outputs/diag_blocks_vs_glacier_models.csv")
const NDRAW = length(ARGS) >= 1 ? parse(Int, ARGS[1]) : 300
const REF   = 2015
const SSPS  = ["ssp126", "ssp245", "ssp585"]
const SLOTS = Dict("R19" => :gsic_r19, "SLOWP" => :gsic_slowp, "FAST" => :gsic_fast)
const ACOL  = Dict("R19" => "gic_a_R19", "SLOWP" => "gic_a_SLOWP", "FAST" => "gic_a_FAST")

post = ladrillo_posterior(nthin=NDRAW)
rows = DataFrame(block=String[], ssp=String[], year=Int[], med=Float64[],
                 p05=Float64[], p95=Float64[])
@printf("Ladrillo blocks vs glacier models | %d draws | %% of %d mass lost\n",
        nrow(post), REF)
for ssp in SSPS
    bf = ladrillo_setup(ssp=ssp, y0=1850, y1=2300,
                        gis_ab = ladrillo_posterior_variant() === :ab)
    yi(y) = findfirst(==(y), bf.years)
    acc = Dict(b => Dict(y => Float64[] for y in (2100, 2300)) for b in keys(SLOTS))
    for r in eachrow(post)
        ladrillo_run_draw!(bf, r)
        for (b, slot) in SLOTS
            s = Float64.(bf.m[:glaciers_small_icecaps, slot])
            m15 = Float64(r[ACOL[b]]) - s[yi(REF)]
            for y in (2100, 2300)
                push!(acc[b][y], 100 * (s[yi(y)] - s[yi(REF)]) / m15)
            end
        end
    end
    for b in ["R19", "SLOWP", "FAST"], y in (2100, 2300)
        v = filter(isfinite, acc[b][y])
        push!(rows, (block=b, ssp=ssp, year=y, med=median(v),
                     p05=quantile(v, 0.05), p95=quantile(v, 0.95)))
    end
end
CSV.write(OUT, rows)
@printf("\n  %-7s %-8s %5s %10s %18s\n", "block", "ssp", "year", "median", "5-95%")
for r in eachrow(sort(rows, [:block, :ssp, :year]))
    @printf("  %-7s %-8s %5d %10.2f  [%6.2f,%6.2f]\n", r.block, r.ssp, r.year,
            r.med, r.p05, r.p95)
end
println("\nwrote $(relpath(OUT, LADRILLO_REPO))")
