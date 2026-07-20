## ============================================================================
## project_pulse_ssp245_mengel.jl — FaIR→BRICK-Mengel CO2-PULSE marginal, SSP2-4.5
##
## Reference arm of the MAGICC-pulse-vs-BRICK-FM study (Phase 1). Computes the
## marginal SLR response to a 0.01 GtCO2 pulse @2030 (cm per GtCO2, by horizon),
## the FaIR→BRICK-Mengel counterpart of the MAGICC-native pulse marginal.
##
## Pairing / marginal: each FaIR config i is run through BRICK-Mengel with BOTH
##   - baseline forcing  (fair_baseline_{gmst,ohc}_..._pulse001_2030.csv)
##   - pulse forcing     (fair_policy_{gmst,ohc}_...  = baseline + 0.01 GtCO2@2030)
## using the SAME posterior draw (assigned per config, fixed seed). The marginal
## per config = (SLR_pulse - SLR_base); BRICK params identical across the pair, so
## the marginal is clean. Reref to 1995-2014 is unnecessary (pulse is 2030, so the
## pre-pulse reference mean is identical for both arms and cancels) — we difference
## the raw component series directly. Marginal normalised by PULSE_GTCO2 (0.01).
##
## Mirrors project_matched_ssp245_mengel.jl: glacier (Mengel) params fixed at the
## medoid; the 18 free BRICK phys params vary per posterior draw. Horizons to 2300.
##
##   julia --project=julia_v2 julia/project_pulse_ssp245_mengel.jl [N_PAIRS]
## ============================================================================
using CSV, DataFrames, Mimi, MimiBRICK, Statistics, Printf, Random
include(joinpath(@__DIR__, "brick_mengel.jl"))

const REPO = abspath(joinpath(@__DIR__, ".."))
const FAIRDIR = joinpath(homedir(), "Documents/2026/CodeProjects/FaIRtoFrEDI/fair_outputs")
const PROCDIR = joinpath(homedir(),
    "Documents/2026/CodeProjects/FaIRtoFrEDI/magicc_comparison/processed")
# Gas-parameterised via ENV (defaults reproduce the CO2 reference arm bit-for-bit).
# PULSE_SIZE normalises the marginal; PULSE_UNIT is its reporting label. For CH4
# the per-tonne-CO2e (GWP) conversion is applied DOWNSTREAM in the Python
# comparison builder, so this driver stays in transparent per-(Tg CH4) units.
const TAG    = get(ENV, "PULSE_TAG", "ssp245_pulse001_2030")
const OUTCSV = get(ENV, "PULSE_OUTCSV",
    joinpath(PROCDIR, "fairbrickfm_pulse_co2_ssp245_marginal.csv"))
const PULSE_SIZE = parse(Float64, get(ENV, "PULSE_SIZE", "0.01"))
const PULSE_UNIT = get(ENV, "PULSE_UNIT", "cm/GtCO2")
const Y0, Y1 = 1850, 2300
const SEED = 20260616
years = collect(Y0:Y1)
const HORIZONS = [2030, 2040, 2050, 2060, 2070, 2080, 2090, 2100, 2150, 2200, 2300]
const COMPS = ("te", "gsic", "gis", "ais", "lws")

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

function load_member_matrix(path)
    df = CSV.read(path, DataFrame)
    yr = Int.(df.year)
    keep = [findfirst(==(y), yr) for y in years]
    cols = [c for c in names(df) if startswith(c, "cfg_")]
    M = Matrix{Float64}(undef, length(years), length(cols))
    for (j, c) in enumerate(cols); M[:, j] = Float64.(df[keep, c]); end
    return M
end

gmst_base = load_member_matrix(joinpath(FAIRDIR, "fair_baseline_gmst_v145_$(TAG).csv"))
ohc_base  = load_member_matrix(joinpath(FAIRDIR, "fair_baseline_ohc_v145_$(TAG).csv"))
gmst_pul  = load_member_matrix(joinpath(FAIRDIR, "fair_policy_gmst_v145_$(TAG).csv"))
ohc_pul   = load_member_matrix(joinpath(FAIRDIR, "fair_policy_ohc_v145_$(TAG).csv"))
n_fair = size(gmst_base, 2)
@printf("Loaded FaIR base+pulse forcing: %d configs, %d years (%d-%d)\n", n_fair, length(years), Y0, Y1)

N_PAIRS = length(ARGS) >= 1 ? parse(Int, ARGS[1]) : n_fair
ncap = min(N_PAIRS, n_fair)
post   = CSV.read(joinpath(REPO, "data/MimiBRICK/parameters_subsample_brick_mengel.csv"), DataFrame)
medoid = CSV.read(joinpath(REPO, "outputs/recalib_central_row.csv"), DataFrame)[1, :]

Random.seed!(SEED)
post_assign = rand(1:nrow(post), ncap)             # posterior draw per FaIR config
@printf("FaIR→BRICK-Mengel PULSE SSP2-4.5: %d configs × paired posterior draws, seed=%d\n", ncap, SEED)

m = build_brick_mengel(ssp="ssp245", y0=Y0, y1=Y1)
update_brick_mengel!(m, medoid, (a=0.45,b=0.52,T_lia=-0.45,f=0.5,tau_fast=40.0,tau_slow=250.0,sl0=0.0); precip_log=true)

# marginal series per pair (cm), total + 5 components
marg = Dict(c => Array{Float64}(undef, ncap, length(years)) for c in ("total", COMPS...))
function comp_series(model)
    (total = model[:global_sea_level, :sea_level_rise],
     ais   = model[:antarctic_icesheet, :ais_sea_level],
     gsic  = model[:glaciers_small_icecaps, :gsic_sea_level],
     gis   = model[:greenland_icesheet, :greenland_sea_level],
     te    = model[:thermal_expansion, :te_sea_level],
     lws   = model[:landwater_storage, :lws_sea_level])
end

t_start = time()
for i in 1:ncap
    p = post_assign[i]
    @inbounds for k in 1:length(PHYS)
        update_param!(m, PHYS[k][1], PHYS[k][2], Float64(post[p, PHYS_NAMES[k]]))
    end
    set_forcing!(m, gmst_base[:, i], ohc_base[:, i]); run(m); b = comp_series(m)
    set_forcing!(m, gmst_pul[:, i],  ohc_pul[:, i]);  run(m); q = comp_series(m)
    marg["total"][i, :] = 100 .* (q.total .- b.total)         # m -> cm
    marg["ais"][i, :]   = 100 .* (q.ais  .- b.ais)
    marg["gsic"][i, :]  = 100 .* (q.gsic .- b.gsic)
    marg["gis"][i, :]   = 100 .* (q.gis  .- b.gis)
    marg["te"][i, :]    = 100 .* (q.te   .- b.te)
    marg["lws"][i, :]   = 100 .* (q.lws  .- b.lws)
    if i % 200 == 0; @printf("  %d/%d  (%.0fs)\n", i, ncap, time()-t_start); end
end

# --- sanity: pre-pulse marginal must be ~0 (forcing identical pre-2030) -------
ipre = findfirst(==(2029), years)
premax = maximum(abs.(marg["total"][:, 1:ipre]))
@printf("\nSANITY pre-pulse max|marginal total| (yrs<=2029): %.3e cm  %s\n",
        premax, premax < 1e-9 ? "PASS" : "CHECK")
# closure: components sum to total
clo = maximum(abs.((marg["te"] .+ marg["gsic"] .+ marg["gis"] .+ marg["ais"] .+ marg["lws"])
                   .- marg["total"]))
@printf("SANITY component closure max|Σcomp-total|: %.3e cm\n", clo)

# --- tidy marginal output (cm/GtCO2), matching the MAGICC marginal schema ----
qs(v) = (quantile(v,0.05), quantile(v,0.50), quantile(v,0.95), mean(v))
rows = DataFrame(variable=String[], component=String[], year=Int[], unit=String[],
                 q05=Float64[], q50=Float64[], q95=Float64[], mean=Float64[], n=Int[])
for comp in ("total", COMPS...)
    for y in HORIZONS
        t = findfirst(==(y), years)
        t === nothing && continue
        v = marg[comp][:, t] ./ PULSE_SIZE
        a = qs(v)
        push!(rows, ("slr", comp, y, PULSE_UNIT, a[1], a[2], a[3], a[4], ncap))
    end
end
mkpath(dirname(OUTCSV))
CSV.write(OUTCSV, rows)
@printf("\nwrote %s (%d rows)\n", OUTCSV, nrow(rows))

@printf("\n=== HEADLINE FaIR→BRICK-Mengel pulse marginal (%s) ===\n", PULSE_UNIT)
for y in (2050, 2100, 2300)
    r = rows[(rows.component .== "total") .& (rows.year .== y), :]
    @printf("  SLR total @%d: q50=%.4e  [%.4e, %.4e]\n", y, r.q50[1], r.q05[1], r.q95[1])
end
@printf("  components @2100 (median %s):\n", PULSE_UNIT)
for c in COMPS
    r = rows[(rows.component .== c) .& (rows.year .== 2100), :]
    @printf("    %-5s: %.4e\n", c, r.q50[1])
end
