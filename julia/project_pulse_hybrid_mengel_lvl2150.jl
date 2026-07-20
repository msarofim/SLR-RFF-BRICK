## ============================================================================
## project_pulse_hybrid_mengel_lvl2150.jl  (Claude, 2026-07-15)
## Copy of project_pulse_hybrid_mengel.jl with two additive changes:
##   (1) HORIZONS includes 2150;
##   (2) also emits absolute baseline SLR LEVEL (variable "level_base", cm,
##       rebaselined to 1995-2014) in addition to the pulse marginal.
## Same OHC×0.1 convention (input OHC in ZJ=1e21 J -> BRICK 1e22 J). For the FaIR
## arm, export the NPZ to wide CSVs with OHC in ZJ (raw J / 1e21) so this ×0.1 lands
## at 1e22 J, identical to the MAGICC path.
##   julia --project=julia_v2 julia/project_pulse_hybrid_mengel_lvl2150.jl \
##       GMST_BASE OHC_BASE GMST_PULSE OHC_PULSE PULSE_GTCO2 LABEL OUTCSV
## ============================================================================
using CSV, DataFrames, Mimi, MimiBRICK, Statistics, Printf, Random
include(joinpath(@__DIR__, "brick_mengel.jl"))

const REPO = abspath(joinpath(@__DIR__, ".."))
const Y0, Y1 = 1850, 2300
const SEED = 20260616
const OHC_ZJ_TO_1E22 = 0.1
years = collect(Y0:Y1)
const i2100 = findfirst(==(2100), years)
const HORIZONS = [2050, 2100, 2150, 2200, 2300]

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

gb, ob, gp, op, pulse, label, outcsv = ARGS[1], ARGS[2], ARGS[3], ARGS[4], parse(Float64, ARGS[5]), ARGS[6], ARGS[7]

function load_wide(path; scale=1.0)
    df = CSV.read(path, DataFrame)
    yr = Int.(df.year)
    keep = [findfirst(==(y), yr) for y in years]
    cols = [c for c in names(df) if startswith(c, "m")]
    M = Matrix{Float64}(undef, length(years), length(cols))
    for (j, c) in enumerate(cols); M[:, j] = Float64.(df[keep, c]) .* scale; end
    return M
end

gmst_b = load_wide(gb); ohc_b = load_wide(ob; scale=OHC_ZJ_TO_1E22)
gmst_p = load_wide(gp); ohc_p = load_wide(op; scale=OHC_ZJ_TO_1E22)
nmem = size(gmst_b, 2)
@printf("[%s] →BRICK-Mengel pulse+level: %d members, %g GtCO2, OHC×%.1f\n", label, nmem, pulse, OHC_ZJ_TO_1E22)

post = CSV.read(joinpath(REPO, "data/MimiBRICK/parameters_subsample_brick_mengel.csv"), DataFrame)
medoid = CSV.read(joinpath(REPO, "outputs/recalib_central_row.csv"), DataFrame)[1, :]
Random.seed!(SEED); post_assign = rand(1:nrow(post), nmem)

m = build_brick_mengel(ssp="ssp245", y0=Y0, y1=Y1)
update_brick_mengel!(m, medoid, (a=0.45,b=0.52,T_lia=-0.45,f=0.5,tau_fast=40.0,tau_slow=250.0,sl0=0.0); precip_log=true)

mtot = fill(NaN, nmem, length(years)); mais = fill(NaN, nmem, length(years))
mbase = fill(NaN, nmem, length(years))          # baseline TOTAL SLR level (cm)
t0 = time()
for i in 1:nmem
    p = post_assign[i]
    @inbounds for k in 1:length(PHYS)
        update_param!(m, PHYS[k][1], PHYS[k][2], Float64(post[p, PHYS_NAMES[k]]))
    end
    set_forcing!(m, gmst_b[:, i], ohc_b[:, i]); run(m)
    bt = m[:global_sea_level, :sea_level_rise]; ba = m[:antarctic_icesheet, :ais_sea_level]
    set_forcing!(m, gmst_p[:, i], ohc_p[:, i]); run(m)
    qt = m[:global_sea_level, :sea_level_rise]; qa = m[:antarctic_icesheet, :ais_sea_level]
    mtot[i, :] = 100 .* (qt .- bt); mais[i, :] = 100 .* (qa .- ba); mbase[i, :] = 100 .* bt
    if i % 200 == 0; @printf("  %d/%d (%.0fs)\n", i, nmem, time()-t0); end
end

rows = DataFrame(label=String[], variable=String[], year=Int[], unit=String[],
                 q05=Float64[], q50=Float64[], q95=Float64[], mean=Float64[], n=Int[])
qf(v) = (quantile(v,0.05), quantile(v,0.50), quantile(v,0.95), mean(v))
# pulse marginal (cm/GtCO2)
for (lbl, M) in (("total", mtot), ("ais", mais))
    for y in HORIZONS
        t = findfirst(==(y), years); t === nothing && continue
        v = M[:, t] ./ pulse
        a = qf(v); push!(rows, (label, lbl, y, "cm/GtCO2", a..., nmem))
    end
end
# absolute baseline SLR LEVEL (cm), rebaselined to 1995-2014
let iref = [findfirst(==(y), years) for y in 1995:2014]
    levref = vec(mean(mbase[:, iref], dims=2))
    for y in HORIZONS
        t = findfirst(==(y), years); t === nothing && continue
        v = mbase[:, t] .- levref
        a = qf(v); push!(rows, (label, "level_base", y, "cm", a..., nmem))
    end
end
mkpath(dirname(outcsv)); CSV.write(outcsv, rows)
lvl(y) = rows[(rows.variable.=="level_base").&(rows.year.==y), :q50]
tot(y) = rows[(rows.variable.=="total").&(rows.year.==y), :q50]
@printf("LEVEL med @2100=%.1f @2150=%.1f cm | PULSE tot med @2100=%.4e @2150=%.4e cm/GtCO2\n",
        lvl(2100)[1], lvl(2150)[1], tot(2100)[1], tot(2150)[1])
@printf("wrote %s\n", outcsv)
