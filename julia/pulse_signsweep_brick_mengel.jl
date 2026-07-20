## ============================================================================
## pulse_signsweep_brick_mengel.jl — push the FaIR signed CO2-pulse sweep through
## BRICK-Mengel to test whether the ICE-SHEET emulator adds sign-flip asymmetry /
## hysteresis beyond its (near-symmetric, -1.000) FaIR GMST input.
##
## Reads fair_signsweep_v145_ssp245.npz (arms: baseline + signed pulses, paired
## seeds, GMST+OHC 1850-2300). For each FaIR cfg run baseline + each pulse arm
## through the SAME paired posterior draw, difference -> SLR marginal (total, AIS).
## Reports per-GtCO2 sensitivity + sign-flip (neg/pos) per magnitude, @2100/@2300.
##
##   julia --project=julia_v2 julia/pulse_signsweep_brick_mengel.jl [N_CFGS]
## ============================================================================
using NPZ, CSV, DataFrames, Mimi, MimiBRICK, Statistics, Printf, Random
include(joinpath(@__DIR__, "brick_mengel.jl"))

const REPO = abspath(joinpath(@__DIR__, ".."))
const NPZF = joinpath(homedir(), "Documents/2026/CodeProjects/FaIRtoFrEDI/fair_outputs/fair_signsweep_v145_ssp245_numeric.npz")
const OUTCSV = joinpath(homedir(), "Documents/2026/CodeProjects/FaIRtoFrEDI/magicc_comparison/processed/pulse_signsweep_brickfm_ssp245.csv")
const Y0, Y1 = 1850, 2300
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

d = npzread(NPZF)
years = Int.(d["years"]); sizes = Float64.(d["sizes"])
gmst = d["gmst"]; ohc = d["ohc"]                  # (arm, year, cfg)
narm, nyear, ncfg = size(gmst)
i_base = findfirst(==(0.0), sizes)
i2100 = findfirst(==(2100), years); i2300 = findfirst(==(2300), years)
@printf("loaded sweep: %d arms, %d cfgs, sizes=%s\n", narm, ncfg, string(sizes))

N = length(ARGS) >= 1 ? parse(Int, ARGS[1]) : ncfg
ncap = min(N, ncfg)
post = CSV.read(joinpath(REPO, "data/MimiBRICK/parameters_subsample_brick_mengel.csv"), DataFrame)
medoid = CSV.read(joinpath(REPO, "outputs/recalib_central_row.csv"), DataFrame)[1, :]
Random.seed!(SEED); post_assign = rand(1:nrow(post), ncap)

# Skip absurd arms that break the DAIS emulator domain (|size|>=100 blows AIS up
# to ~1e50 and corrupts model state). The hysteresis probe is covered by |size|<=10.
const ARM_MAX_ABS = 10.0
const GIC = (a=0.45, b=0.52, T_lia=-0.45, f=0.5, tau_fast=40.0, tau_slow=250.0, sl0=0.0)
function fresh_model()
    mm = build_brick_mengel(ssp="ssp245", y0=Y0, y1=Y1)
    update_brick_mengel!(mm, medoid, GIC; precip_log=true)
    return mm
end
apply_phys!(mm, p) = (@inbounds for k in 1:length(PHYS)
    update_param!(mm, PHYS[k][1], PHYS[k][2], Float64(post[p, PHYS_NAMES[k]])); end)

m = fresh_model()

# marginal[arm] = SLR(arm) - SLR(base), cm, per cfg, for total & ais, @2100 & @2300
mtot100 = fill(NaN, narm, ncap); mtot300 = fill(NaN, narm, ncap)
mais100 = fill(NaN, narm, ncap); mais300 = fill(NaN, narm, ncap)
nfail = zeros(Int, narm)
nanmed(v) = (w = filter(!isnan, v); isempty(w) ? NaN : median(w))
# run with rebuild-on-failure (a failed mid-timestep run can corrupt model state)
const _ERRSEEN = Ref(false)
function safe_run!(mm, p, gv, ov)
    set_forcing!(mm, gv, ov)
    try; run(mm); return (mm, true)
    catch e
        if !_ERRSEEN[]; _ERRSEEN[]=true; @warn "first run failure" err=sprint(showerror, e); end
        mm = fresh_model(); apply_phys!(mm, p); return (mm, false)
    end
end
t0 = time()
for i in 1:ncap
    global m
    p = post_assign[i]
    apply_phys!(m, p)
    m, okb = safe_run!(m, p, gmst[i_base, :, i], ohc[i_base, :, i])
    if !okb; nfail[i_base] += 1; continue; end   # baseline should never fail
    bt = m[:global_sea_level, :sea_level_rise]; ba = m[:antarctic_icesheet, :ais_sea_level]
    bt100, bt300 = bt[i2100], bt[i2300]; ba100, ba300 = ba[i2100], ba[i2300]
    for a in 1:narm
        (a == i_base || abs(sizes[a]) > ARM_MAX_ABS) && continue
        m, ok = safe_run!(m, p, gmst[a, :, i], ohc[a, :, i])
        if !ok; nfail[a] += 1; continue; end
        qt = m[:global_sea_level, :sea_level_rise]; qa = m[:antarctic_icesheet, :ais_sea_level]
        mtot100[a, i] = 100*(qt[i2100]-bt100); mtot300[a, i] = 100*(qt[i2300]-bt300)
        mais100[a, i] = 100*(qa[i2100]-ba100); mais300[a, i] = 100*(qa[i2300]-ba300)
    end
    if i % 200 == 0; @printf("  %d/%d (%.0fs)\n", i, ncap, time()-t0); end
end

# pair magnitudes for sign-flip
mags = sort(unique(abs.(sizes[(sizes .!= 0.0) .& (abs.(sizes) .<= ARM_MAX_ABS)])))
rows = DataFrame(mag=Float64[], horizon=Int[], variable=String[],
                 pos_cm_per_gt=Float64[], neg_cm_per_gt=Float64[], signflip=Float64[])
function ai(sz); findfirst(==(sz), sizes); end
@printf("\n=== BRICK-Mengel SLR: per-GtCO2 sensitivity & sign-flip (median over cfgs) ===\n")
for (lbl, M100, M300) in (("total", mtot100, mtot300), ("ais", mais100, mais300))
    @printf("-- %s --\n", uppercase(lbl))
    @printf("  %7s  %5s  %16s  %16s  %14s\n", "|size|","horiz","+cm/GtCO2","-cm/GtCO2","signflip n/p")
    for mag in mags
        ip = ai(mag); ineg = ai(-mag)
        for (hz, M) in ((2100, M100), (2300, M300))
            pos = M[ip, :] ./ mag; neg = M[ineg, :] ./ mag
            sf  = M[ineg, :] ./ M[ip, :]
            push!(rows, (mag, hz, lbl, nanmed(pos), nanmed(neg), nanmed(sf)))
            @printf("  %7g  %5d  %16.4e  %16.4e  %14.5f\n", mag, hz, nanmed(pos), nanmed(neg), nanmed(sf))
        end
    end
end
@printf("\nAIS-emulator run failures per arm (size GtCO2 => n cfgs failed of %d):\n", ncap)
for a in 1:narm
    nfail[a] > 0 && @printf("  size %+g: %d failed\n", sizes[a], nfail[a])
end
mkpath(dirname(OUTCSV)); CSV.write(OUTCSV, rows)
@printf("\nwrote %s\n", OUTCSV)
