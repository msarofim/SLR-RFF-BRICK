## ============================================================================
## project_matched_ssp245_mengel.jl — MATCHED-UNCERTAINTY BRICK-Mengel, SSP2-4.5
##
## Companion to project_ssps_2100_mengel.jl. That driver forces every BRICK draw
## with the FaIR *mean* climate -> its SLR spread is BRICK-parameter uncertainty
## ONLY. This driver pairs each BRICK posterior draw with a randomly-assigned
## FaIR *ensemble member* (per-member GMST + OHC), so the resulting SLR spread
## carries climate + SLR-parameter uncertainty JOINTLY -> directly comparable to
## the MAGICC-native 600-member band (which also varies climate + SLR).
##
## Pairing (Marcus 2026-06-16): for draw i in 1..N_draws, FaIR member =
## sampled with replacement from the 841 configs (FaIR & BRICK posteriors are
## independent calibrations -> random pairing is valid). Fixed seed.
## SSP2-4.5 only (the only SSP with per-member FaIR forcing on disk).
##
##   julia --project=julia_v2 julia/project_matched_ssp245_mengel.jl [N_DRAWS]
## ============================================================================
using CSV, DataFrames, Mimi, MimiBRICK, Statistics, Printf, Random
include(joinpath(@__DIR__, "brick_mengel.jl"))

const REPO = abspath(joinpath(@__DIR__, ".."))
const FAIRDIR = joinpath(homedir(), "Documents/2026/CodeProjects/FaIRtoFrEDI/fair_outputs")
const Y0, Y1 = 1850, 2100
const BASE0, BASE1 = 1995, 2014
years = collect(Y0:Y1)
const IB = [findfirst(==(y), years) for y in BASE0:BASE1]
const i2100 = findfirst(==(2100), years)
const TS_YEARS = 2000:10:2100
const SEED = 20260616

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

# --- load per-member FaIR ensemble forcing (wide: year, cfg_0000..cfg_0840) ---
function load_member_matrix(path)
    df = CSV.read(path, DataFrame)
    yr = Int.(df.year)
    keep = [findfirst(==(y), yr) for y in years]      # slice 1850..2100, in order
    cols = [c for c in names(df) if startswith(c, "cfg_")]
    M = Matrix{Float64}(undef, length(years), length(cols))
    for (j, c) in enumerate(cols); M[:, j] = Float64.(df[keep, c]); end
    return M                                          # (nyear, nmember)
end

gmst_mat = load_member_matrix(joinpath(FAIRDIR, "fair_baseline_gmst_v145_ssp245_harmonized.csv"))
ohc_mat  = load_member_matrix(joinpath(FAIRDIR, "fair_baseline_ohc_v145_ssp245_harmonized.csv"))
n_fair = size(gmst_mat, 2)
@assert size(ohc_mat, 2) == n_fair "GMST/OHC member counts differ"

# sanity: per-member mean ≈ the fair_mean file the param-only driver used (same convention)
meanchk = CSV.read(joinpath(REPO, "data/observations/fair_mean_ohc_ssp245.csv"), DataFrame)
mc = Dict(Int(meanchk[i,"year"]) => Float64(meanchk[i,"ohc_1e22J"]) for i in 1:nrow(meanchk))
ohc_permember_mean_2100 = mean(ohc_mat[i2100, :])
@printf("CONVENTION CHECK OHC@2100: per-member mean=%.3f  fair_mean file=%.3f (1e22 J)\n",
        ohc_permember_mean_2100, mc[2100])

N_DRAWS = length(ARGS) >= 1 ? parse(Int, ARGS[1]) : typemax(Int)
post   = CSV.read(joinpath(REPO, "data/MimiBRICK/parameters_subsample_brick_mengel.csv"), DataFrame)
medoid = CSV.read(joinpath(REPO, "outputs/recalib_central_row.csv"), DataFrame)[1,:]
ncap = min(N_DRAWS, nrow(post))

Random.seed!(SEED)
fair_assign = rand(1:n_fair, ncap)                    # FaIR member per BRICK draw (w/ replacement)
@printf("MATCHED-UNC BRICK-Mengel SSP2-4.5: %d BRICK draws × paired FaIR members (of %d), seed=%d\n",
        ncap, n_fair, SEED)

rerefseries(v) = 100 .* (v .- sum(v[IB])/length(IB))
pcts(v) = (quantile(v,0.05), quantile(v,0.17), quantile(v,0.50), quantile(v,0.83), quantile(v,0.95))

m = build_brick_mengel(ssp="ssp245", y0=Y0, y1=Y1)
update_brick_mengel!(m, medoid, (a=0.45,b=0.52,T_lia=-0.45,f=0.5,tau_fast=40.0,tau_slow=250.0,sl0=0.0); precip_log=true)

tot_ts = Array{Float64}(undef, ncap, length(years))
comp_ts = Dict(c => Array{Float64}(undef, ncap, length(years)) for c in ("ais","gsic","gis","te","lws"))
t_start = time()
for i in 1:ncap
    @inbounds for k in 1:length(PHYS)
        update_param!(m, PHYS[k][1], PHYS[k][2], Float64(post[i, PHYS_NAMES[k]]))
    end
    fi = fair_assign[i]
    set_forcing!(m, gmst_mat[:, fi], ohc_mat[:, fi]); run(m)
    tot_ts[i, :]      = rerefseries(m[:global_sea_level, :sea_level_rise])
    comp_ts["ais"][i,:]  = rerefseries(m[:antarctic_icesheet,:ais_sea_level])
    comp_ts["gsic"][i,:] = rerefseries(m[:glaciers_small_icecaps,:gsic_sea_level])
    comp_ts["gis"][i,:]  = rerefseries(m[:greenland_icesheet,:greenland_sea_level])
    comp_ts["te"][i,:]   = rerefseries(m[:thermal_expansion,:te_sea_level])
    comp_ts["lws"][i,:]  = rerefseries(m[:landwater_storage,:lws_sea_level])
    if i % 2000 == 0; @printf("  %d/%d  (%.0fs)\n", i, ncap, time()-t_start); end
end

# tidy band output: total + components, p05/p17/p50/p83/p95, decadal
tser = DataFrame(year=Int[], variable=String[], p05=Float64[], p17=Float64[], p50=Float64[], p83=Float64[], p95=Float64[])
for y in TS_YEARS
    t = findfirst(==(y), years)
    a = pcts(tot_ts[:,t]); push!(tser, (y, "SLR_total", a...))
    for cn in ("ais","gsic","gis","te","lws")
        a = pcts(comp_ts[cn][:,t]); push!(tser, (y, cn, a...))
    end
end
CSV.write(joinpath(REPO,"outputs/proj_matched_ssp245_mengel_timeseries.csv"), tser)
@printf("\nWrote outputs/proj_matched_ssp245_mengel_timeseries.csv  (%.0fs)\n", time()-t_start)

a = pcts(tot_ts[:,i2100])
@printf("\n=== SSP2-4.5 @2100 total GMSL (cm, rel 1995-2014), MATCHED-UNC %d draws ===\n", ncap)
@printf("p05=%.1f p17=%.1f p50=%.1f p83=%.1f p95=%.1f\n", a...)
