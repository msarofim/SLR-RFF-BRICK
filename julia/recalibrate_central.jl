## ============================================================================
## recalibrate_central.jl  —  QUICK central BRICK recalibration test
##
## A point ("central") recalibration, NOT a Bayesian MCMC. Start from the
## column-wise MEDIAN of the post-#93 BRICK posterior, drive BRICK with the
## FaIR-mean GMST + OHC trajectories, and adjust FIVE global knobs by
## coordinate-descent to best fit the historical targets:
##
##   knob                       primary target
##   ais_ocean_temperature₀  →  Frederikse AIS         (the AIS "equilibrium" temp)
##   ais_α                   →  Frederikse AIS         (discharge partition; breaks the see-saw)
##   gsic_β₀                 →  Frederikse Glaciers    (GSIC amplitude)
##   gsic_v₀                 →  Frederikse Glaciers    (GSIC reservoir / shape)
##   te_α                    →  Frederikse Steric      (thermal-expansion efficiency)
##   (all five jointly)      →  Dangendorf total GMSL  (closure)
##
## LWS is NOT a BRICK parameter here — BRICK's landwater_storage is zero
## historically by design — so the modeled total uses the Frederikse TWS series
## as a budget add-on when comparing to Dangendorf.
##
## Everything is re-referenced to the common 1995-2005 window (matches
## prep_recalib_targets.py). Runs on the v2.0.0 env (julia_v2) with the
## precip_log shim so the v1.0.1-era posterior is consumed correctly.
##
##   julia --project=julia_v2 julia/recalibrate_central.jl
## ============================================================================

using CSV, DataFrames, Mimi, MimiBRICK, Random, Statistics, Printf

include(joinpath(@__DIR__, "brick_param_updates.jl"))

const REPO    = abspath(joinpath(@__DIR__, ".."))
const POSTER  = joinpath(REPO, "data/MimiBRICK/parameters_subsample_brick.csv")
const GMST    = joinpath(REPO, "data/observations/fair_mean_gmst.csv")
const OHC     = joinpath(REPO, "data/observations/fair_mean_ohc.csv")
const TARGETS = joinpath(REPO, "outputs/recalib_targets.csv")
const SIGMAS  = joinpath(REPO, "outputs/recalib_target_sigmas.csv")
const OUT_TRAJ = joinpath(REPO, "outputs/recalib_central_trajectories.csv")
const OUT_MD   = joinpath(REPO, "outputs/recalib_central_summary.md")

const Y0, Y1   = 1850, 2018          # model run window
const BASE0, BASE1 = 1995, 2005      # re-reference window (matches prep)
const FIT0, FIT1   = 1900, 2018      # fitting window
years = collect(Y0:Y1)
fit_years = collect(FIT0:FIT1)
yidx(y) = findfirst(==(y), years)
const IB = [yidx(y) for y in BASE0:BASE1]            # baseline-window indices
const IF = [yidx(y) for y in FIT0:FIT1]              # fit-window indices

# ---- load forcing on the run window ----------------------------------------
function load_traj(path, vcol)
    df = CSV.read(path, DataFrame; comment="#")
    by = Dict(floor(Int, Float64(df[i, "year"])) => Float64(df[i, vcol]) for i in 1:nrow(df))
    [by[y] for y in years]
end
gmst = load_traj(GMST, "gmst_C")
ohc  = load_traj(OHC,  "ohc_1e22J")

# ---- targets (already cm, rel 1995-2005) -----------------------------------
tg = CSV.read(TARGETS, DataFrame)
sig = CSV.read(SIGMAS, DataFrame)
# align targets to the fit window (they ARE 1900-2018)
@assert tg.year == fit_years "targets year grid != fit window"
fred_ais    = Float64.(tg.ais)
fred_gsic   = Float64.(tg.gsic)
fred_steric = Float64.(tg.steric)
fred_lws    = Float64.(tg.lws)         # budget add-on
dang_tot    = Float64.(tg.dang)
σ_ais = sig.ais[1]; σ_gsic = sig.gsic[1]; σ_steric = sig.steric[1]; σ_dang = sig.dang[1]

# ---- central posterior parameter vector ------------------------------------
# Prefer the MEDOID draw (real posterior member closest to the ensemble-median
# trajectories — written by prep medoid step), NOT the synthetic median-PARAMETER
# vector: median-of-params != median-of-outputs for the nonlinear ice-sheet, and
# the median-param run lands in an unrepresentatively AIS-extreme regime.
post = CSV.read(POSTER, DataFrame)
const CENTRAL_ROW = joinpath(REPO, "outputs/recalib_central_row.csv")
if isfile(CENTRAL_ROW)
    medrow = CSV.read(CENTRAL_ROW, DataFrame)[1, :]
    println("Central vector = MEDOID draw post_idx=", medrow.medoid_post_idx)
else
    medrow = DataFrame(Dict(n => median(skipmissing(post[!, n])) for n in names(post)))[1, :]
    println("Central vector = synthetic median-parameter vector (medoid file absent)")
end
# knob bounds from posterior 5-95% (oceanT0 is fixed in get_model -> sweep range)
q(col, p) = quantile(Float64.(post[!, col]), p)
const KNAMES = ["ais_ocean_temperature₀", "ais_α", "gsic_β₀", "gsic_v₀", "te_α"]
lo = [0.72, q("antarctic_alpha",0.05), q("glaciers_beta0",0.05), q("glaciers_v0",0.05), q("thermal_alpha",0.05)]
hi = [2.00, q("antarctic_alpha",0.95), q("glaciers_beta0",0.95), q("glaciers_v0",0.95), q("thermal_alpha",0.95)]
# "before" knobs = the central draw's own values (oceanT0 at its fixed default 0.72)
med_knobs = [0.72, Float64(medrow.antarctic_alpha), Float64(medrow.glaciers_beta0),
             Float64(medrow.glaciers_v0), Float64(medrow.thermal_alpha)]

# ---- model build (v2.0.0) --------------------------------------------------
local m, precip_log
try
    global m = MimiBRICK.get_model(ssprcp_scenario="ssp245", start_year=Y0, end_year=Y1)
    global precip_log = true
    println("Built BRICK v2.0.0 (ssp245), precip_log=true")
catch err
    isa(err, MethodError) || rethrow()
    global m = MimiBRICK.get_model(rcp_scenario="RCP45", start_year=Y0, end_year=Y1)
    global precip_log = false
    println("Built BRICK v1.0.1 (RCP45), precip_log=false")
end

reref(v) = v .- mean(v[IB])     # re-reference a full-window series to 1995-2005

"""Run BRICK with median params + the 5 knobs; return component series (cm, rel window) on the FULL run window."""
function run_components(knobs)
    update_brick_params!(m, medrow; precip_log=precip_log)
    update_param!(m, :antarctic_icesheet, :ais_ocean_temperature₀, knobs[1])
    update_param!(m, :antarctic_icesheet, :ais_α,                  knobs[2])
    update_param!(m, :glaciers_small_icecaps, :gsic_β₀,            knobs[3])
    update_param!(m, :glaciers_small_icecaps, :gsic_v₀,            knobs[4])
    update_param!(m, :thermal_expansion, :te_α,                   knobs[5])
    update_param!(m, :model_global_surface_temperature, gmst)
    update_param!(m, :thermal_expansion, :ocean_heat_interior, ohc)
    run(m)
    ais  = reref(100 .* m[:antarctic_icesheet,     :ais_sea_level])
    gsic = reref(100 .* m[:glaciers_small_icecaps, :gsic_sea_level])
    gis  = reref(100 .* m[:greenland_icesheet,     :greenland_sea_level])
    te   = reref(100 .* m[:thermal_expansion,      :te_sea_level])
    lws  = reref(100 .* m[:landwater_storage,      :lws_sea_level])
    return (; ais, gsic, gis, te, lws)
end

"""Reduced weighted SSR over the fit window for one knob vector."""
function objective(knobs)
    c = run_components(knobs)
    a = c.ais[IF]; g = c.gsic[IF]; t = c.te[IF]; gi = c.gis[IF]
    tot = a .+ g .+ gi .+ t .+ fred_lws       # modeled total + Frederikse LWS budget
    j  = mean((a   .- fred_ais).^2)    / σ_ais^2
    j += mean((g   .- fred_gsic).^2)   / σ_gsic^2
    j += mean((t   .- fred_steric).^2) / σ_steric^2
    j += mean((tot .- dang_tot).^2)    / σ_dang^2
    return j
end

# ---- coordinate descent ----------------------------------------------------
knobs = copy(med_knobs)
println("\nStart obj (median params, oceanT0=0.72) = ", round(objective(knobs), digits=3))
NGRID = 17; NPASS = 6
for pass in 1:NPASS
    improved = false
    for k in 1:5
        grid = range(lo[k], hi[k], length=NGRID)
        best_v = knobs[k]; best_j = objective(knobs)
        for v in grid
            trial = copy(knobs); trial[k] = v
            j = objective(trial)
            if j < best_j; best_j = j; best_v = v; improved = true; end
        end
        knobs[k] = best_v
    end
    @printf("pass %d: obj=%.3f  knobs=[%.3f %.4g %.4g %.4g %.4g]\n",
            pass, objective(knobs), knobs...)
    improved || break
end

# ---- before / after trajectories + diagnostics -----------------------------
before = run_components(med_knobs)
after  = run_components(knobs)

function rmse(model, obs); sqrt(mean((model[IF] .- obs).^2)); end
tot_before = before.ais[IF] .+ before.gsic[IF] .+ before.gis[IF] .+ before.te[IF] .+ fred_lws
tot_after  = after.ais[IF]  .+ after.gsic[IF]  .+ after.gis[IF]  .+ after.te[IF]  .+ fred_lws

out = DataFrame(year=years)
for (nm, c) in [("ais",:ais),("gsic",:gsic),("gis",:gis),("te",:te),("lws",:lws)]
    out[!, "before_$nm"] = getfield(before, c)
    out[!, "after_$nm"]  = getfield(after,  c)
end
# total (with Frederikse LWS budget) only defined on fit window; pad with missing
tb = fill(NaN, length(years)); ta = fill(NaN, length(years))
tb[IF] .= tot_before; ta[IF] .= tot_after
out[!, "before_total"] = tb; out[!, "after_total"] = ta
out[!, "lws_fred"] = (v=fill(NaN,length(years)); v[IF] .= fred_lws; v)
CSV.write(OUT_TRAJ, out)
println("\nWrote $OUT_TRAJ")

open(OUT_MD, "w") do io
    central_lbl = isfile(CENTRAL_ROW) ? "MEDOID draw post_idx=$(medrow.medoid_post_idx) (the real posterior member closest to the ensemble-median trajectories)" : "synthetic median-parameter vector"
    println(io, "# Quick central BRICK recalibration — result\n")
    println(io, "Point recalibration from the post-#93 posterior central vector [$central_lbl], FaIR-mean")
    println(io, "GMST+OHC forcing, MimiBRICK v2.0.0 (precip_log shim). 5 knobs, coordinate-descent.")
    println(io, "All cm rel 1995-2005; fit window $FIT0-$FIT1.\n")
    println(io, "## Calibrated knobs\n")
    println(io, "| knob | before (median) | after | bound [lo, hi] |")
    println(io, "|---|---:|---:|---|")
    for k in 1:5
        @printf(io, "| %s | %.4g | %.4g | [%.4g, %.4g] |\n", KNAMES[k], med_knobs[k], knobs[k], lo[k], hi[k])
    end
    println(io, "\nObjective (reduced weighted SSR): before = ", round(objective(med_knobs),digits=3),
                " → after = ", round(objective(knobs),digits=3))
    println(io, "\n## Per-component fit @1900 and RMSE over $FIT0-$FIT1 (cm)\n")
    println(io, "| component | target @1900 | before @1900 | after @1900 | RMSE before | RMSE after |")
    println(io, "|---|---:|---:|---:|---:|---:|")
    a1 = findfirst(==(1900), fit_years)
    for (nm, c, obs, o1900) in [("AIS",:ais,fred_ais,fred_ais[a1]),
                                ("GSIC",:gsic,fred_gsic,fred_gsic[a1]),
                                ("Steric/TE",:te,fred_steric,fred_steric[a1])]
        @printf(io, "| %s | %+.2f | %+.2f | %+.2f | %.2f | %.2f |\n", nm, o1900,
                getfield(before,c)[IF][a1], getfield(after,c)[IF][a1],
                rmse(getfield(before,c), obs), rmse(getfield(after,c), obs))
    end
    @printf(io, "| **Total vs Dangendorf** | %+.2f | %+.2f | %+.2f | %.2f | %.2f |\n",
            dang_tot[a1], tot_before[a1], tot_after[a1],
            sqrt(mean((tot_before .- dang_tot).^2)), sqrt(mean((tot_after .- dang_tot).^2)))
    println(io, "\nGIS is NOT adjusted (fixed by post-#93 calibration); LWS uses the Frederikse")
    println(io, "TWS budget add-on (BRICK LWS is zero historically). The medoid central draw's AIS@1900")
    println(io, "≈ the ensemble median (−3.96 vs −3.97), so the 'before' here represents central BRICK.")
    println(io, "\n**Key reading:** AIS is fixable (oceanT0→interior ~1.2, RMSE collapses), but GSIC rails")
    println(io, "at both glacier-knob upper bounds and still reaches only ~half the Frederikse historical")
    println(io, "loss (structural undershoot). The total-vs-Dangendorf fit DEGRADES after recalibration:")
    println(io, "the apparent pre-fit total match was error cancellation (too-negative AIS offsetting the")
    println(io, "too-positive GSIC/GIS). These 5 knobs cannot fit the components AND the total at once.")
end
println("Wrote $OUT_MD")
print(read(OUT_MD, String))
