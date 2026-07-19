## ============================================================================
## diag_pulse_size_robustness.jl   (Claude, 2026-07-19)
##
## Pulse-size robustness of the BRICK-Mengel marginal SLR, per Marcus's question:
##   "For any given year, some number of runs will be pushed from non-melt to melt
##    by a pulse. Test by doing multiple pulse sizes and normalizing to a 1-ton
##    pulse: if they do not vary much, we are okay; if they vary, we must handle it."
##
## WHY this matters: DAIS fast-dynamics disintegration is a HARD ANNUAL STEP
## (antarctic_icesheet_component.jl:180 — disintegration_rate turns on for the whole
## year once antartic_surface_temperature > temperature_threshold). A pulse advances
## the threshold-crossing by a fraction of a year, so for most ensemble members the
## INTEGER crossing year is unchanged and the AIS fast-dynamics channel contributes
## EXACTLY ZERO to the marginal; only members whose crossing year flips carry signal.
## => the AIS pulse marginal is annual-QUANTIZED.
##
## Small pulses suffer QUANTIZATION (few members flip);   large pulses would suffer
## genuine physical NONLINEARITY (disintegration compounds as the ice radius shrinks).
## A wide size ladder separates the two.
##
## METHOD.  Climate trajectories for every ladder size are built by SCALING a unit
## IRF taken from the REAL FaIR 10-GtCO2 base+pulse pair:
##     GMST_pulse(P) = GMST_base + (P/P0) * (GMST_pulse(P0) - GMST_base)
##     OHC_pulse(P)  = OHC_base  + (P/P0) * (OHC_pulse(P0)  - OHC_base)
## FaIR climate is verified linear to ~1e-5 over 0.01..20 GtCO2 (see linearity check),
## so any per-GtCO2 drift ACROSS the ladder is BRICK/DAIS-side, not climate-side.
##
## PAIRED DISCIPLINE (mandatory): baseline and every pulse size use the SAME per-member
## climate draw AND the SAME posterior parameter draw. post_assign is seeded with the
## SAME SEED as project_pulse_hybrid_mengel*.jl (20260616), so (a) the ladder is
## comparable member-by-member, and (b) the P=10 rung reproduces the existing
## fair_ssp245_10gt driver output bit-for-bit (an internal consistency check).
## Baseline is run ONCE per member and reused across all sizes.
##
## LINEARITY CHECK (mandatory): the scaled-IRF pulse is compared THROUGH BRICK against
## the REAL FaIR pulse trajectory at 20 GtCO2 and 0.01 GtCO2. If they disagree by more
## than a few %, the IRF scaling is invalid and real trajectories must be used instead.
##
## Reads the current canonical posterior parameters_subsample_brick_mengel.csv (the
## pre-v-next posterior — quantization is a property of the INTEGRATOR, so the posterior
## choice barely affects THIS question; see caveats in the console output).
##
##   julia --project=julia_v2 julia/diag_pulse_size_robustness.jl [NMEM_MAX]
## ============================================================================
using CSV, DataFrames, Mimi, MimiBRICK, Statistics, Printf, Random
include(joinpath(@__DIR__, "brick_mengel.jl"))

const REPO = abspath(joinpath(@__DIR__, ".."))
const Y0, Y1 = 1850, 2300
const SEED = 20260616                 # identical to project_pulse_hybrid_mengel*.jl
const OHC_ZJ_TO_1E22 = 0.1            # wide OHC is in ZJ (1e21 J); BRICK wants 1e22 J
years = collect(Y0:Y1)

const PULSE_YEAR = 2030               # FaIR CO2 pulse year (marginal turns on 2031)
const P0_GTCO2   = 10.0               # size of the REAL FaIR base+pulse pair used as the IRF
const LADDER     = [0.03, 0.1, 0.3, 1.0, 3.0, 10.0, 30.0]   # GtCO2
const HORIZONS   = [2100, 2130, 2150, 2180]                 # 2130 = pulse+100yr, 2180 = pulse+150yr
const CARRIER_EPS = 1e-6              # cm/GtCO2 — "non-negligible" AIS marginal (task spec)
const TIP_THRESH  = 0.02             # cm/GtCO2 — empirical fast-dynamics "flipper" cutoff
                                      #   (smooth-channel AIS bulk ~1e-3..1e-2; tipped tail ~1e-1)

# ---- climate-trajectory sources (wide CSVs: col "year" + m0000..; verified) --------------
const CW = "/Users/MarcusMarcus/Documents/2026/CodeProjects/FaIRtoFrEDI/magicc_comparison/processed/curv_wide"
const SP = "/private/tmp/claude-501/-Users-MarcusMarcus-Documents-2026-CodeProjects-FaIRtoFrEDI/15a4cf7c-7727-4add-a678-df257cbe20ae/scratchpad"
const BASE_GMST = joinpath(CW, "fair_gmst_base_wide.csv")     # = FaIR ssp245-harmonized base
const BASE_OHC  = joinpath(CW, "fair_ohc_base_wide.csv")
const P0_GMST   = joinpath(CW, "fair_gmst_pulse_wide.csv")    # = FaIR 10-GtCO2 pulse
const P0_OHC    = joinpath(CW, "fair_ohc_pulse_wide.csv")
const R20_GMST  = joinpath(SP, "real_gmst_pulse_20gt.csv")    # REAL FaIR 20-GtCO2 pulse
const R20_OHC   = joinpath(SP, "real_ohc_pulse_20gt.csv")
const R001_GMST = joinpath(SP, "real_gmst_pulse_0p01gt.csv")  # REAL FaIR 0.01-GtCO2 pulse
const R001_OHC  = joinpath(SP, "real_ohc_pulse_0p01gt.csv")
const OUTCSV    = joinpath(REPO, "outputs/diag_pulse_size_robustness.csv")

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

function load_wide(path; scale=1.0)
    df = CSV.read(path, DataFrame)
    yr = Int.(df.year)
    keep = [findfirst(==(y), yr) for y in years]
    cols = [c for c in names(df) if startswith(c, "m")]
    M = Matrix{Float64}(undef, length(years), length(cols))
    for (j, c) in enumerate(cols); M[:, j] = Float64.(df[keep, c]) .* scale; end
    return M
end

# ---- load climate ------------------------------------------------------------------------
gmst_b = load_wide(BASE_GMST); ohc_b = load_wide(BASE_OHC; scale=OHC_ZJ_TO_1E22)
gmst_p0 = load_wide(P0_GMST);  ohc_p0 = load_wide(P0_OHC; scale=OHC_ZJ_TO_1E22)
gmst_r20 = load_wide(R20_GMST);  ohc_r20 = load_wide(R20_OHC; scale=OHC_ZJ_TO_1E22)
gmst_r001 = load_wide(R001_GMST); ohc_r001 = load_wide(R001_OHC; scale=OHC_ZJ_TO_1E22)

nmem_all = size(gmst_b, 2)
nmem = length(ARGS) >= 1 ? min(parse(Int, ARGS[1]), nmem_all) : nmem_all
@printf("[diag_pulse_size] %d/%d members | ladder=%s GtCO2 | pulse yr %d | IRF from real %g GtCO2\n",
        nmem, nmem_all, string(LADDER), PULSE_YEAR, P0_GTCO2)

# unit IRF (per GtCO2). OHC arrays already ×0.1 -> BRICK 1e22-J units; scaling is unit-consistent.
dgmst = (gmst_p0 .- gmst_b) ./ P0_GTCO2
dohc  = (ohc_p0  .- ohc_b ) ./ P0_GTCO2

# ---- posterior + medoid geometry (paired assignment, driver-identical seed) ---------------
post = CSV.read(joinpath(REPO, "data/MimiBRICK/parameters_subsample_brick_mengel.csv"), DataFrame)
medoid = CSV.read(joinpath(REPO, "outputs/recalib_central_row.csv"), DataFrame)[1, :]
Random.seed!(SEED); post_assign = rand(1:nrow(post), nmem_all)   # draw over FULL member set...
post_assign = post_assign[1:nmem]                                # ...then take first nmem (subset-stable)

m = build_brick_mengel(ssp="ssp245", y0=Y0, y1=Y1)
update_brick_mengel!(m, medoid, (a=0.45,b=0.52,T_lia=-0.45,f=0.5,tau_fast=40.0,tau_slow=250.0,sl0=0.0); precip_log=true)

# ---- storage: per (arm) -> member × horizon, in MARGINAL cm (not yet per-GtCO2) -----------
hz_idx = [findfirst(==(y), years) for y in HORIZONS]
nH = length(HORIZONS)
# arms: LADDER sizes (scaled) + "real20" + "real001"
sizes = LADDER
tot = [fill(NaN, nmem, nH) for _ in 1:length(sizes)]   # scaled-ladder TOTAL marginal cm
ais = [fill(NaN, nmem, nH) for _ in 1:length(sizes)]   # scaled-ladder AIS marginal cm
r20_tot = fill(NaN, nmem, nH); r20_ais = fill(NaN, nmem, nH)     # real 20gt
r01_tot = fill(NaN, nmem, nH); r01_ais = fill(NaN, nmem, nH)     # real 0.01gt

t0 = time()
for i in 1:nmem
    p = post_assign[i]
    @inbounds for k in 1:length(PHYS)
        update_param!(m, PHYS[k][1], PHYS[k][2], Float64(post[p, PHYS_NAMES[k]]))
    end
    # baseline ONCE
    set_forcing!(m, gmst_b[:, i], ohc_b[:, i]); run(m)
    bt = m[:global_sea_level, :sea_level_rise][hz_idx]
    ba = m[:antarctic_icesheet, :ais_sea_level][hz_idx]
    # scaled ladder
    for (s, P) in enumerate(sizes)
        gp = gmst_b[:, i] .+ P .* dgmst[:, i]
        op = ohc_b[:, i]  .+ P .* dohc[:, i]
        set_forcing!(m, gp, op); run(m)
        tot[s][i, :] = 100 .* (m[:global_sea_level, :sea_level_rise][hz_idx] .- bt)
        ais[s][i, :] = 100 .* (m[:antarctic_icesheet, :ais_sea_level][hz_idx] .- ba)
    end
    # real 20gt
    set_forcing!(m, gmst_r20[:, i], ohc_r20[:, i]); run(m)
    r20_tot[i, :] = 100 .* (m[:global_sea_level, :sea_level_rise][hz_idx] .- bt)
    r20_ais[i, :] = 100 .* (m[:antarctic_icesheet, :ais_sea_level][hz_idx] .- ba)
    # real 0.01gt
    set_forcing!(m, gmst_r001[:, i], ohc_r001[:, i]); run(m)
    r01_tot[i, :] = 100 .* (m[:global_sea_level, :sea_level_rise][hz_idx] .- bt)
    r01_ais[i, :] = 100 .* (m[:antarctic_icesheet, :ais_sea_level][hz_idx] .- ba)
    if i % 100 == 0; @printf("  %d/%d (%.0fs)\n", i, nmem, time()-t0); end
end
@printf("ran %d members in %.0fs\n", nmem, time()-t0)

# ---- assemble ladder table (per GtCO2) ----------------------------------------------------
rows = DataFrame(component=String[], pulse_gtco2=Float64[], year=Int[], horizon_after=Int[],
                 median=Float64[], mean=Float64[], q05=Float64[], q95=Float64[],
                 n_carrier_1e6=Int[], frac_carrier_1e6=Float64[],
                 n_tip=Int[], frac_tip=Float64[], n=Int[])
for (s, P) in enumerate(sizes)
    for (h, y) in enumerate(HORIZONS)
        for (comp, M) in (("ais", ais[s]), ("total", tot[s]))
            v = M[:, h] ./ P                       # cm/GtCO2
            nc = count(x -> abs(x) > CARRIER_EPS, v)
            nt = count(x -> x > TIP_THRESH, v)
            push!(rows, (comp, P, y, y - PULSE_YEAR,
                         quantile(v,0.50), mean(v), quantile(v,0.05), quantile(v,0.95),
                         nc, nc/nmem, nt, nt/nmem, nmem))
        end
    end
end
mkpath(dirname(OUTCSV)); CSV.write(OUTCSV, rows)

# ---- console table ------------------------------------------------------------------------
println("\n================= PULSE-SIZE ROBUSTNESS LADDER (per GtCO2) =================")
for (comp) in ("ais", "total")
    for hy in (2130, 2180)
        println("\n--- $(uppercase(comp))  @ $(hy)  ( pulse + $(hy-PULSE_YEAR) yr ) ---")
        @printf("%8s | %11s %11s %11s %11s | %10s %8s\n",
                "GtCO2","median","mean","q05","q95","carrier1e6","tip>$(TIP_THRESH)")
        for (s, P) in enumerate(sizes)
            r = rows[(rows.component.==comp).&(rows.pulse_gtco2.==P).&(rows.year.==hy), :][1, :]
            @printf("%8.3g | %11.5f %11.5f %11.5f %11.5f | %5d/%d %5d/%d\n",
                    P, r.median, r.mean, r.q05, r.q95, r.n_carrier_1e6, nmem, r.n_tip, nmem)
        end
    end
end

# robustness spread of the MEDIAN and MEAN across the ladder (per component/horizon)
println("\n================= PER-TON STABILITY (spread across ladder) =================")
@printf("%6s %5s | %-9s %-9s %-8s | %-9s %-9s %-8s\n",
        "comp","hz","med_min","med_max","med_%spr","mean_min","mean_max","mean_%spr")
for comp in ("ais","total"), hy in (2130,2180)
    sub = rows[(rows.component.==comp).&(rows.year.==hy), :]
    meds = sub.median; mns = sub.mean
    mspr = 100*(maximum(meds)-minimum(meds))/abs(median(meds))
    nspr = 100*(maximum(mns)-minimum(mns))/abs(median(mns))
    @printf("%6s %5d | %9.5f %9.5f %7.1f%% | %9.5f %9.5f %7.1f%%\n",
            comp, hy, minimum(meds), maximum(meds), mspr, minimum(mns), maximum(mns), nspr)
end

# ---- linearity validation: scaled-IRF vs REAL FaIR pulse THROUGH BRICK --------------------
println("\n================= LINEARITY CHECK (scaled-IRF vs REAL FaIR, through BRICK) =========")
println("per-GtCO2 marginal; scaled = ladder rung built from 10gt IRF; real = actual FaIR cube")
function cmp_arm(scaled_M, real_M, P, comp)
    for (h, y) in enumerate(HORIZONS)
        y in (2130,2180) || continue
        vs = scaled_M[:, h] ./ P
        vr = real_M[:, h]  ./ P
        med_s, med_r = quantile(vs,0.50), quantile(vr,0.50)
        mn_s,  mn_r  = mean(vs), mean(vr)
        dmed = 100*(med_s-med_r)/abs(med_r)
        dmn  = 100*(mn_s -mn_r )/abs(mn_r)
        @printf("  %5s @%d: median scaled=%.6f real=%.6f (Δ%+.3f%%) | mean scaled=%.6f real=%.6f (Δ%+.3f%%)\n",
                comp, y, med_s, med_r, dmed, mn_s, mn_r, dmn)
    end
end
# scaled counterparts: ladder rung P=20 is NOT in the ladder, so build it on the fly? Use P index.
# We compare the REAL 20gt/0.01gt to the SCALED value at the SAME size.
scaled20_tot = fill(NaN, nmem, nH); scaled20_ais = fill(NaN, nmem, nH)
scaled01_tot = fill(NaN, nmem, nH); scaled01_ais = fill(NaN, nmem, nH)
# recompute scaled 20 & 0.01 through BRICK (cheap: nmem runs each) using the SAME paired base
let
    for i in 1:nmem
        p = post_assign[i]
        @inbounds for k in 1:length(PHYS)
            update_param!(m, PHYS[k][1], PHYS[k][2], Float64(post[p, PHYS_NAMES[k]]))
        end
        set_forcing!(m, gmst_b[:, i], ohc_b[:, i]); run(m)
        bt = m[:global_sea_level, :sea_level_rise][hz_idx]; ba = m[:antarctic_icesheet, :ais_sea_level][hz_idx]
        for (P, Mt, Ma) in ((20.0, scaled20_tot, scaled20_ais), (0.01, scaled01_tot, scaled01_ais))
            gp = gmst_b[:, i] .+ P .* dgmst[:, i]; op = ohc_b[:, i] .+ P .* dohc[:, i]
            set_forcing!(m, gp, op); run(m)
            Mt[i, :] = 100 .* (m[:global_sea_level, :sea_level_rise][hz_idx] .- bt)
            Ma[i, :] = 100 .* (m[:antarctic_icesheet, :ais_sea_level][hz_idx] .- ba)
        end
    end
end
println("[20 GtCO2]")
cmp_arm(scaled20_ais, r20_ais, 20.0, "ais");  cmp_arm(scaled20_tot, r20_tot, 20.0, "total")
println("[0.01 GtCO2]")
cmp_arm(scaled01_ais, r01_ais, 0.01, "ais");  cmp_arm(scaled01_tot, r01_tot, 0.01, "total")

# ---- P=10 reproduction cross-check vs existing driver output ------------------------------
i10 = findfirst(==(10.0), sizes); i2100h = findfirst(==(2100), HORIZONS)
@printf("\n[repro] scaled P=10 @2100  AIS median=%.7f (driver 0.0012622)  TOTAL median=%.7f (driver 0.0053455)\n",
        quantile(ais[i10][:,i2100h]./10.0, 0.50), quantile(tot[i10][:,i2100h]./10.0, 0.50))
@printf("wrote %s\n", OUTCSV)
