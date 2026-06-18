## ============================================================================
## project_magicc_hybrid_ssp245_mengel.jl — TRACK C, MAGICC->BRICK-Mengel hybrid
##
## The off-diagonal 2x2 cell of the climate x SLR-emulator comparison:
##   climate forcing = MAGICC (GSAT + OHC, per ensemble member)
##   SLR emulator    = BRICK-Mengel (same emulator as Track B)
## Isolates climate-forcing differences from SLR-emulator-structure differences.
##
## Companion to project_matched_ssp245_mengel.jl (FaIR->BRICK-Mengel matched).
## SAME pairing scheme: for draw i in 1..N_draws, climate member = sampled with
## replacement from the 600 MAGICC members (MAGICC & BRICK posteriors are
## independent calibrations -> random pairing valid). Same fixed seed so the
## BRICK-parameter draws line up with the matched run; only the climate forcing
## source differs. SSP2-4.5 only.
##
## Forcing inputs: MAGICC per-member wide CSVs (year + m0000..m0599) built by
## FaIRtoFrEDI/magicc_comparison/magicc_to_wide.py:
##   GMST: Surface Air Temperature Change, K rel 1750 -> rebaselined 1850-1900
##   OHC : Heat Content|Ocean, ZJ stock since 1750 -> rebaselined 1850-1900
##         (matches the Track-B matched run's FaIR-OHC convention; the TE module
##          re-references SLR to 1995-2014 so a constant OHC offset cancels --
##          VERIFIED via --ohc rel1750 vs rel1850 giving identical SLR).
##
##   julia --project=julia_v2 julia/project_magicc_hybrid_ssp245_mengel.jl [N_DRAWS] [rel1850|rel1750]
## ============================================================================
using CSV, DataFrames, Mimi, MimiBRICK, Statistics, Printf, Random
include(joinpath(@__DIR__, "brick_mengel.jl"))

const REPO = abspath(joinpath(@__DIR__, ".."))
const MAGDIR = joinpath(homedir(), "Documents/2026/CodeProjects/FaIRtoFrEDI/magicc_comparison/processed")
const Y0, Y1 = 1850, 2100
const BASE0, BASE1 = 1995, 2014
years = collect(Y0:Y1)
const IB = [findfirst(==(y), years) for y in BASE0:BASE1]
const i2100 = findfirst(==(2100), years)
const TS_YEARS = 2000:10:2100
const SEED = 20260616
# MAGICC "Heat Content|Ocean" is in ZJ (1e21 J); BRICK's set_forcing! expects the
# ohc_1e22J convention (1e22 J), same as the FaIR OHC files the matched run used.
# 1 ZJ = 0.1 x 1e22 J. (The slr-refresh memory note "1e22 J = ZJ" was WRONG.)
const ZJ_TO_1E22J = 0.1

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

# --- load per-member MAGICC ensemble forcing (wide: year, m0000..m0599) -------
function load_member_matrix(path)
    df = CSV.read(path, DataFrame)
    yr = Int.(df.year)
    keep = [findfirst(==(y), yr) for y in years]      # slice 1850..2100, in order
    cols = [c for c in names(df) if startswith(c, "m") && c != "year"]
    M = Matrix{Float64}(undef, length(years), length(cols))
    for (j, c) in enumerate(cols); M[:, j] = Float64.(df[keep, c]); end
    return M                                          # (nyear, nmember)
end

OHC_CONV = length(ARGS) >= 2 ? ARGS[2] : "rel1850"
@assert OHC_CONV in ("rel1850", "rel1750") "OHC arg must be rel1850 or rel1750"
ohc_file = OHC_CONV == "rel1850" ? "magicc_ohc_ssp245_wide_rel1850.csv" : "magicc_ohc_ssp245_wide_rel1750.csv"

gmst_mat = load_member_matrix(joinpath(MAGDIR, "magicc_gmst_ssp245_wide.csv"))
ohc_mat  = load_member_matrix(joinpath(MAGDIR, ohc_file)) .* ZJ_TO_1E22J   # ZJ -> 1e22 J
n_mag = size(gmst_mat, 2)
@assert size(ohc_mat, 2) == n_mag "GMST/OHC member counts differ"
@printf("MAGICC forcing: %d members, GMST median@2100=%.3f C, OHC(%s) median@2100=%.1f (1e22 J)\n",
        n_mag, median(gmst_mat[i2100, :]), OHC_CONV, median(ohc_mat[i2100, :]))

# convention sanity vs FaIR OHC the matched run used (same 1e22 J unit, similar magnitude)
fairmean = CSV.read(joinpath(REPO, "data/observations/fair_mean_ohc_ssp245.csv"), DataFrame)
fm = Dict(Int(fairmean[i,"year"]) => Float64(fairmean[i,"ohc_1e22J"]) for i in 1:nrow(fairmean))
@printf("CONVENTION CHECK OHC@2100: MAGICC per-member median=%.1f  FaIR-mean file=%.1f (1e22 J)\n",
        median(ohc_mat[i2100, :]), fm[2100])

N_DRAWS = length(ARGS) >= 1 ? parse(Int, ARGS[1]) : typemax(Int)
post   = CSV.read(joinpath(REPO, "data/MimiBRICK/parameters_subsample_brick_mengel.csv"), DataFrame)
medoid = CSV.read(joinpath(REPO, "outputs/recalib_central_row.csv"), DataFrame)[1,:]
ncap = min(N_DRAWS, nrow(post))

Random.seed!(SEED)
mag_assign = rand(1:n_mag, ncap)                      # MAGICC member per BRICK draw (w/ replacement)
@printf("MAGICC->BRICK-Mengel HYBRID SSP2-4.5: %d BRICK draws × paired MAGICC members (of %d), seed=%d, OHC=%s\n",
        ncap, n_mag, SEED, OHC_CONV)

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
    mi = mag_assign[i]
    set_forcing!(m, gmst_mat[:, mi], ohc_mat[:, mi]); run(m)
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
# Write the MAGICC-derived result to the PRIVATE FaIRtoFrEDI repo (MAGDIR), NOT this public
# repo's outputs/ — keeps MAGICC results out of the public SLR-RFF-BRICK. See PUBLISHING.md there.
outname = OHC_CONV == "rel1850" ? "proj_magicc_hybrid_ssp245_mengel_timeseries.csv" :
                                  "proj_magicc_hybrid_ssp245_mengel_timeseries_rel1750.csv"
CSV.write(joinpath(MAGDIR, outname), tser)
@printf("\nWrote (private) %s  (%.0fs)\n", joinpath(MAGDIR, outname), time()-t_start)

a = pcts(tot_ts[:,i2100])
@printf("\n=== SSP2-4.5 @2100 total GMSL (cm, rel 1995-2014), HYBRID MAGICC->BRICK-Mengel %d draws, OHC=%s ===\n", ncap, OHC_CONV)
@printf("p05=%.1f p17=%.1f p50=%.1f p83=%.1f p95=%.1f\n", a...)
