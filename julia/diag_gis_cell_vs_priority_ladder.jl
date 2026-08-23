## ============================================================================
## diag_gis_cell_vs_priority_ladder.jl — the SHIPPED cell, the RATE-CLEARING cell,
## the untapped base, and ORIGINAL BRICK's Greenland, scored on Marcus's own
## priority ladder in ONE table.
##
## THE LADDER (memory `greenland_fit_priority`, Marcus 2026-08-22):
##   1  known physical constraints (total ice volume) + HISTORICAL OBSERVATIONS,
##      within uncertainties
##   2  physical ice models for LONG-TERM COMMITMENT, within uncertainties
##   3  understood constraints on melt RATE
##   4  TRANSIENT ice models
## with the stringency rule: a test is only as stringent as the number of models
## behind it; few models ⇒ guidance, not a fit objective.
##
## WHY IN JULIA AND NOT IN THE OFFLINE PYTHON. Priority 1 is a statement about the
## HINDCAST, and the question "is the reservoir really inert over the observed
## record" must be answered by the SHIPPED model, not by an emulator of it — the
## emulator is where the inertness claim came from in the first place, so using it
## to check the claim is circular. And ORIGINAL BRICK's Greenland (the stock SIMPLE
## module, `gis_variant = :stock`) has no offline emulator at all.
##
## LIKE-FOR-LIKE (memory `like_for_like_forcing`). Every arm runs through the SAME
## `ladrillo_setup`, the SAME fair_mean forcing per SSP, the SAME baseline window and
## the SAME observational target file. The ONLY thing that differs between the BRICK
## arm and the Ladrillo arms is the Greenland module and the posterior it needs.
## That is the comparison "is it better than original BRICK" actually asks for; a
## published-BRICK number computed under different forcing would not be.
##
## READ-ONLY. Writes one CSV.
##   julia --project=julia_v2 julia/diag_gis_cell_vs_priority_ladder.jl [--draws=N]
## ============================================================================
using CSV, DataFrames, Printf, Statistics
include(joinpath(@__DIR__, "ladrillo_projection.jl"))

const REPO   = LADRILLO_REPO
const Y0, Y1 = 1850, 2300
const NTHIN  = let i = findfirst(a -> startswith(a, "--draws="), ARGS)
    i === nothing ? 400 : parse(Int, ARGS[i][9:end])
end
const OBS_CSV = joinpath(REPO, "outputs/recalib_targets_ext.csv")
const OUT     = joinpath(REPO, "outputs/diag_gis_cell_vs_priority_ladder.csv")

## --- THE ARMS ---------------------------------------------------------------
## `extC` is the posterior that carries BRICK's STOCK Greenland (greenland_a/b/
## alpha/beta/v0 — the SIMPLE module of Bakker et al.) calibrated inside THIS
## pipeline. That, not a published BRICK table, is the like-for-like "original
## BRICK" arm: same forcing, same obs, same everything but the module.
const ARMS = [
    ("original BRICK (:stock SIMPLE)", "brick_mengel_extC", nothing),
    ("Ladrillo L14, untapped",         "brick_mengel_L14",  nothing),
    ("Ladrillo L14 + V=5.66 cascade",  "brick_mengel_L14",  5.66),
    ("Ladrillo L14 + V=6.00 cascade",  "brick_mengel_L14",  GIS_TAP_CELL.V_m),
]
## PRIORITY 1. The windows the hindcast bisection does NOT control, so they are the
## evidence; the calibration-window total is fitted and is reported as such.
const CALIB_WIN  = (1900, 2025)
const FREE_WINS  = [(1900, 1950), (1950, 1990), (1993, 2010), (2010, 2024)]
const OBS_RATE_WIN = (1995, 2024)          # the priority-1 rate
const ACCEL_WIN    = (1993, 2024)
## PRIORITY 2 / 4. The horizons with independent ice-model evidence.
const HORIZONS = (2100, 2150, 2300)
const SSPS = [("ssp126", "SSP1-2.6"), ("ssp245", "SSP2-4.5"), ("ssp585", "SSP5-8.5")]
## PRIORITY 2 target for our own ssp585 (gis_targets.MATCHED_2300_{M,P50_M}).
## ⚠ NOT the r2300 arm's own band median (72.3 cm) — that is a DIFFERENT predictor
## and quoting it moves any verdict here by 1.36x. See memory
## `gis_matched_band_predictor`.
const MATCHED_2300 = (lo = 42.9, p50 = 98.5, hi = 145.0)
## PRIORITY 1, the volume constraint: CLIMBER-X's total Greenland ice volume.
const VOLUME_BAND_M = (7.30, 7.68)
## PRIORITY 3. The 2250-2300 rate window and the PROTECT r2300 run-level band, from
## python/diag_gis_cascade_rate_crit.py (35 runs / 5 GCM clusters, p05-p95).
const RATE_WIN = (2250, 2300)
const R2300_RATE_BAND = (9.7, 41.5)

mmyr(v, yrs, w) = let i0 = findfirst(==(w[1]), yrs), i1 = findfirst(==(w[2]), yrs)
    10.0 * (v[i1] - v[i0]) / (w[2] - w[1])            # cm -> mm/yr
end
"""Quadratic coefficient x2 = the acceleration, mm/yr^2, same estimator as
diag_gis_obs_scorecard.py section C so the two tables are comparable."""
function accel(v, yrs, w)
    m = (yrs .>= w[1]) .& (yrs .<= w[2])
    x = Float64.(yrs[m]) .- mean(Float64.(yrs[m]))
    y = 10.0 .* Float64.(v[m])
    X = hcat(ones(length(x)), x, x .^ 2)
    return 2.0 * (X \ y)[3]
end

## The target file runs one year past the last Greenland observation, so the tail is
## `missing`. Dropped explicitly — a silent coercion here would either error late or,
## worse, propagate a NaN into a rate and print it as a number.
obs = dropmissing(CSV.read(OBS_CSV, DataFrame)[:, [:year, :gis, :gis_lo, :gis_hi]], :gis)
const OY = Int.(obs.year)
const OV = Float64.(obs.gis)
const OLO = Float64.(obs.gis_lo)
const OHI = Float64.(obs.gis_hi)
## BASELINE IS A MULTI-YEAR MEAN, never a single year (standing rule). Model and obs
## live on different baselines, so both are rebased to their own mean over this
## window before any LEVEL comparison; single-year rebasing on a series this noisy
## manufactures an offset that is pure artefact.
const REBASE_WIN = (1900, 1910)
oi(y) = findfirst(==(y), OY)

@printf("Greenland vs Marcus's PRIORITY LADDER | %d draws/arm | obs %s ('gis', %d-%d)\n\n",
        NTHIN, relpath(OBS_CSV, REPO), minimum(OY), maximum(OY))

out = DataFrame(arm=String[], priority=Int[], quantity=String[], ssp=String[],
                value=Float64[], target=Float64[], ratio=Float64[])
proj = Dict{Tuple{String,String},Any}()
v0s  = Dict{String,Float64}()
v0src = Dict{String,String}()

for (nm, tag, vcell) in ARMS
    postpath = joinpath(REPO, "data/MimiBRICK/parameters_subsample_$(tag).csv")
    isfile(postpath) || error("no posterior at $postpath")
    variant = ladrillo_posterior_variant(postpath)
    post = ladrillo_posterior(path = postpath, nthin = NTHIN)
    ## v0 is the WHOLE-SHEET inventory the module carries — priority 1's "known
    ## physical constraint". Its column name differs between the modules, which is
    ## itself the tell that these are two different objects.
    ## v0 is SAMPLED in the stock module (`greenland_v0`) and STRUCTURAL in Ladrillo
    ## (`LADRILLO_GIS_V0_M`, the Mouginot sector sum). Reporting them side by side is
    ## honest only if that difference is stated: one arm's volume is a fitted
    ## parameter with posterior spread, the other's is an inventory constant.
    v0col = variant === :stock ? "greenland_v0" : "gis_v0"
    v0s[nm] = v0col in names(post) ? median(Float64.(post[!, v0col])) : LADRILLO_GIS_V0_M
    v0src[nm] = v0col in names(post) ? "sampled ($v0col)" : "structural (Mouginot sum)"
    @printf("%-32s %-22s :%-8s %4d draws  v0 %.2f m%s\n", nm, tag, variant, nrow(post),
            v0s[nm], vcell === nothing ? "" : @sprintf("   tap V=%.2f m", vcell))
    for (ssp, lab) in SSPS
        bf = ladrillo_setup(ssp = ssp, y0 = Y0, y1 = Y1, gis_variant = variant)
        ## The tap is REFUSED on :stock / :ab by design (no basin to tap), so the
        ## BRICK arm never asks for it. That refusal IS the arm, not a limitation.
        vcell === nothing || ladrillo_set_tap!(bf; v = vcell)
        ny = length(bf.years)
        g = Array{Float64}(undef, ny, nrow(post))
        for (j, r) in enumerate(eachrow(post))
            ladrillo_run_draw!(bf, r)
            g[:, j] = ladrillo_series(bf, :gis)
        end
        proj[(nm, lab)] = (years = collect(bf.years),
                           med = [median(filter(isfinite, @view g[i, :])) for i in 1:ny])
    end
end
println()

## ---- PRIORITY 1 -------------------------------------------------------------
## Rebased to the FIRST calibration year so model and obs are compared as CHANGE,
## which is what the observational product is: our series starts at 1850 and the
## target at 1900, and an un-rebased level comparison would be an offset, not a fit.
println("=== PRIORITY 1 — known physical constraints + HISTORICAL OBSERVATIONS ===\n")
@printf("  A. TOTAL over the calibration window %d-%d, cm.  FITTED, not evidence.\n",
        CALIB_WIN[1], CALIB_WIN[2])
obs_tot = OV[oi(CALIB_WIN[2])] - OV[oi(CALIB_WIN[1])]
@printf("     %-32s %8s %9s %9s\n", "arm", "ours", "observed", "ratio")
hs = Dict{String,Any}()
for (nm, _, _) in ARMS
    p = proj[(nm, "SSP5-8.5")]
    yi(y) = findfirst(==(y), p.years)
    hs[nm] = (p = p, yi = yi)
    v = p.med[yi(CALIB_WIN[2])] - p.med[yi(CALIB_WIN[1])]
    @printf("     %-32s %8.3f %9.3f %8.3fx\n", nm, v, obs_tot, v / obs_tot)
    push!(out, (nm, 1, "calib_total_cm", "-", v, obs_tot, v / obs_tot))
end

println("\n  B. THE FREE PART — rates the calibration does not control, mm/yr")
@printf("     %-32s", "arm")
for w in vcat(FREE_WINS, [OBS_RATE_WIN]); @printf("%12s", "$(w[1])-$(w[2])"); end
println("   <- last col = the priority-1 rate")
@printf("     %-32s", "OBSERVED")
for w in vcat(FREE_WINS, [OBS_RATE_WIN]); @printf("%12.3f", mmyr(OV, OY, w)); end
println()
for (nm, _, _) in ARMS
    p, yi = hs[nm].p, hs[nm].yi
    @printf("     %-32s", nm)
    for w in vcat(FREE_WINS, [OBS_RATE_WIN])
        r = mmyr(p.med, p.years, w); o = mmyr(OV, OY, w)
        @printf("%9.3f %2.2fx", r, r / o)
        push!(out, (nm, 1, "rate_$(w[1])_$(w[2])_mmyr", "-", r, o, r / o))
    end
    println()
end

## --- the LEVEL, against the observational uncertainty envelope ---------------
## "within their uncertainties" is a LEVEL statement and the rates above do not make
## it: a model can match every rate and still sit outside the band if its baseline is
## off. Reported as the fraction of observed years the median line falls inside
## [gis_lo, gis_hi], plus the worst excursion in units of the band's own half-width,
## so a near-miss and a gross one are distinguishable.
println("\n  B2. THE LEVEL vs the observational uncertainty band [gis_lo, gis_hi],")
println("      both rebased to their $(REBASE_WIN[1])-$(REBASE_WIN[2]) mean")
let om = (OY .>= REBASE_WIN[1]) .& (OY .<= REBASE_WIN[2]), ob = mean(OV[om])
    ol, oh, oc = OLO .- ob, OHI .- ob, OV .- ob
    ## THE BAND'S OWN HALF-WIDTH COLLAPSES 67x ACROSS THE RECORD -- 1.068 cm at 1900,
    ## 0.016 cm (0.16 mm) at 2020 -- so an excursion measured in half-widths is
    ## dominated entirely by the satellite era and says almost nothing about the
    ## first century. The ABSOLUTE miss in cm is printed beside it for exactly that
    ## reason: 4.7 half-widths at 2020 is 0.08 cm on a 5.8 cm accumulated signal.
    ## Neither column alone is the answer; quoting only the first would overstate the
    ## defect and only the second would hide where it sits.
    @printf("     %-32s %11s %13s %13s %11s\n", "arm", "yrs in band",
            "worst |excurs|", "worst |miss|", "worst year")
    for (nm, _, _) in ARMS
        p = hs[nm].p
        mm = (p.years .>= REBASE_WIN[1]) .& (p.years .<= REBASE_WIN[2])
        mb = mean(p.med[mm])
        inb, worst, wy, wcm = 0, 0.0, 0, 0.0
        for (k, y) in enumerate(OY)
            j = findfirst(==(y), p.years); j === nothing && continue
            v = p.med[j] - mb
            half = 0.5 * (oh[k] - ol[k])
            (ol[k] <= v <= oh[k]) && (inb += 1)
            e = max(ol[k] - v, v - oh[k]) / max(half, 1e-9)
            e > worst && (worst = e; wy = y; wcm = max(ol[k] - v, v - oh[k]))
        end
        @printf("     %-32s %7d/%-4d %11.2f %11.3f cm %10s\n", nm, inb, length(OY),
                max(worst, 0.0), max(wcm, 0.0), worst > 0 ? string(wy) : "-")
        push!(out, (nm, 1, "obs_band_frac_in", "-", inb / length(OY), 1.0,
                    inb / length(OY)))
        push!(out, (nm, 1, "obs_band_worst_excursion", "-", max(worst, 0.0), 1.0, NaN))
        push!(out, (nm, 1, "obs_band_worst_miss_cm", "-", max(wcm, 0.0), 0.0, NaN))
    end
    @printf("     band half-width: %.3f cm at %d -> %.3f cm at %d (%.0fx narrower)\n",
            0.5 * (oh[1] - ol[1]), OY[1], 0.5 * (oh[end] - ol[end]), OY[end],
            (oh[1] - ol[1]) / (oh[end] - ol[end]))
end

println("\n  C. ACCELERATION over $(ACCEL_WIN[1])-$(ACCEL_WIN[2]), mm/yr^2 (quadratic coeff x2)")
oa = accel(OV, OY, ACCEL_WIN)
@printf("     %-32s %+9.4f\n", "OBSERVED", oa)
for (nm, _, _) in ARMS
    p, _ = hs[nm].p, hs[nm].yi
    a = accel(p.med, p.years, ACCEL_WIN)
    @printf("     %-32s %+9.4f  %5.2fx\n", nm, a, a / oa)
    push!(out, (nm, 1, "accel_mmyr2", "-", a, oa, a / oa))
end

println("\n  D. TOTAL ICE VOLUME, m SLE — CLIMBER-X $(VOLUME_BAND_M[1])-$(VOLUME_BAND_M[2]) m")
for (nm, _, _) in ARMS
    v = v0s[nm]
    ok = VOLUME_BAND_M[1] <= v <= VOLUME_BAND_M[2]
    @printf("     %-32s %8.2f   %-4s  %s\n", nm, v, ok ? "IN" : "OUT", v0src[nm])
    push!(out, (nm, 1, "v0_m", "-", v, 0.5 * sum(VOLUME_BAND_M), v / (0.5 * sum(VOLUME_BAND_M))))
end

## ---- PRIORITY 2 / 4 ---------------------------------------------------------
println("\n=== PRIORITY 2 — LONG-TERM COMMITMENT (2300), and PRIORITY 4 — TRANSIENT (2100) ===\n")
println("  Greenland median, cm, per scenario")
@printf("  %-32s", "arm")
for (_, lab) in SSPS, y in HORIZONS; @printf("%9s", "$(lab[end-2:end])@$(y)"); end
println()
for (nm, _, _) in ARMS
    @printf("  %-32s", nm)
    for (_, lab) in SSPS
        p = proj[(nm, lab)]; yi(y) = findfirst(==(y), p.years)
        for y in HORIZONS
            @printf("%9.1f", p.med[yi(y)])
            push!(out, (nm, y == 2300 ? 2 : 4, "gis_$(y)_cm", lab, p.med[yi(y)], NaN, NaN))
        end
    end
    println()
end

println("\n  PRIORITY 2, our own ssp585 @2300 vs the MATCHED band " *
        "[$(MATCHED_2300.lo), $(MATCHED_2300.hi)] cm, p50 $(MATCHED_2300.p50)")
for (nm, _, _) in ARMS
    p = proj[(nm, "SSP5-8.5")]; yi(y) = findfirst(==(y), p.years)
    v = p.med[yi(2300)]
    ok = MATCHED_2300.lo <= v <= MATCHED_2300.hi
    @printf("     %-32s %8.1f cm   %6.3fx the p50   %s\n", nm, v, v / MATCHED_2300.p50,
            ok ? "IN band" : "OUT of band")
    push!(out, (nm, 2, "gis_2300_vs_matched_p50", "SSP5-8.5", v, MATCHED_2300.p50,
                v / MATCHED_2300.p50))
end

println("\n  SCENARIO SEPARATION at 2300 — the quantity the reservoir exists to buy")
for (nm, _, _) in ARMS
    g(lab) = (p = proj[(nm, lab)]; p.med[findfirst(==(2300), p.years)])
    r = g("SSP5-8.5") / g("SSP2-4.5")
    @printf("     %-32s ssp585/ssp245 = %6.2fx\n", nm, r)
    push!(out, (nm, 2, "sep_585_over_245_2300", "-", r, NaN, NaN))
end

## ---- PRIORITY 3 — THE MELT-RATE CRITERION ------------------------------------
## The 2250-2300 rate is defined on the PROTECT r2300 arm (late-century forcing HELD
## from 2101), NOT on our own SSP paths, so it needs its own run with that GMST
## injected. Doing it here rather than quoting the offline number is what makes the
## ORIGINAL BRICK arm comparable at all: there is no offline emulator of the stock
## SIMPLE module, so the only like-for-like route is the model itself.
println("\n=== PRIORITY 3 — MELT RATE, $(RATE_WIN[1])-$(RATE_WIN[2]) on the PROTECT r2300 arm ===\n")
println("  band $(R2300_RATE_BAND) cm/century, run-level p05-p95 over 35 runs / 5 GCM clusters.")
println("  Marcus's stringency rule applies: 5 clusters ⇒ GUIDANCE, not a fit objective.")
rf = CSV.read(joinpath(REPO, "outputs/protect_r2300_forcing_gmst.csv"), DataFrame)
rmap = Dict(Int(rf[i, "year"]) => Float64(rf[i, "gmst_spliced"]) for i in 1:nrow(rf))
@printf("\n     %-32s %14s %10s   %s\n", "arm", "cm/century", "band", "verdict")
for (nm, tag, vcell) in ARMS
    postpath = joinpath(REPO, "data/MimiBRICK/parameters_subsample_$(tag).csv")
    variant = ladrillo_posterior_variant(postpath)
    post = ladrillo_posterior(path = postpath, nthin = NTHIN)
    yrs = collect(Y0:Y1)
    gm = [get(rmap, y, NaN) for y in yrs]
    any(isnan, gm) && error("r2300 forcing does not cover $Y0-$Y1")
    bf = ladrillo_setup(ssp = "ssp585", y0 = Y0, y1 = Y1, gis_variant = variant, gmst = gm)
    vcell === nothing || ladrillo_set_tap!(bf; v = vcell)
    g = Array{Float64}(undef, length(bf.years), nrow(post))
    for (j, r) in enumerate(eachrow(post))
        ladrillo_run_draw!(bf, r); g[:, j] = ladrillo_series(bf, :gis)
    end
    med = [median(filter(isfinite, @view g[i, :])) for i in 1:length(bf.years)]
    yi(y) = findfirst(==(y), bf.years)
    rate = (med[yi(RATE_WIN[2])] - med[yi(RATE_WIN[1])]) / (RATE_WIN[2] - RATE_WIN[1]) * 100
    ok = R2300_RATE_BAND[1] <= rate <= R2300_RATE_BAND[2]
    @printf("     %-32s %14.1f %10s   %s\n", nm, rate,
            "[$(R2300_RATE_BAND[1]), $(R2300_RATE_BAND[2])]",
            ok ? "IN" : (rate < R2300_RATE_BAND[1] ? "OUT (too SLOW)" : "OUT (too FAST)"))
    push!(out, (nm, 3, "rate_2250_2300_r2300_cm_per_century", "r2300", rate,
                R2300_RATE_BAND[2], rate / R2300_RATE_BAND[2]))
end

## ---- THE RATE-CLEARING V, SOLVED IN THE WIRED MODEL --------------------------
## The 5.66 m figure came from a bisection on the OFFLINE emulator
## (python/diag_gis_cascade_rate_crit.py). Emulator and model are two different
## objects until that is measured -- the standing port-test discipline -- and here it
## MATTERS, because the cell was chosen to sit exactly ON the band top: a 0.5% port
## difference is the difference between IN and OUT. So the same bisection is run
## again, in the model, and the two answers are printed together.
println("\n=== THE RATE-CLEARING V, SOLVED HERE IN THE WIRED MODEL ===")
let tag = "brick_mengel_L14"
    postpath = joinpath(REPO, "data/MimiBRICK/parameters_subsample_$(tag).csv")
    variant = ladrillo_posterior_variant(postpath)
    post = ladrillo_posterior(path = postpath, nthin = NTHIN)
    yrs = collect(Y0:Y1)
    gm = [get(rmap, y, NaN) for y in yrs]
    function rate_at(V)
        bf = ladrillo_setup(ssp = "ssp585", y0 = Y0, y1 = Y1, gis_variant = variant, gmst = gm)
        V > 0 && ladrillo_set_tap!(bf; v = V)
        g = Array{Float64}(undef, length(bf.years), nrow(post))
        for (j, r) in enumerate(eachrow(post))
            ladrillo_run_draw!(bf, r); g[:, j] = ladrillo_series(bf, :gis)
        end
        med = [median(filter(isfinite, @view g[i, :])) for i in 1:length(bf.years)]
        yi(y) = findfirst(==(y), bf.years)
        (med[yi(RATE_WIN[2])] - med[yi(RATE_WIN[1])]) / (RATE_WIN[2] - RATE_WIN[1]) * 100
    end
    ## The reservoir is a pure additive scaling in V, so two evaluations pin the line
    ## exactly -- no bisection loop, and no ambiguity about convergence.
    r0, r1 = rate_at(0.0), rate_at(GIS_TAP_CELL.V_m)
    Vstar = GIS_TAP_CELL.V_m * (R2300_RATE_BAND[2] - r0) / (r1 - r0)
    @printf("     base rate %.2f, at V=%.2f m rate %.2f  ⇒  rate is linear in V at %.3f per m\n",
            r0, GIS_TAP_CELL.V_m, r1, (r1 - r0) / GIS_TAP_CELL.V_m)
    @printf("     V clearing the band top (%.1f) IN THE WIRED MODEL : %.2f m\n",
            R2300_RATE_BAND[2], Vstar)
    @printf("     the OFFLINE emulator's answer                      : 5.66 m  (%.1f%% apart)\n",
            100 * (5.66 / Vstar - 1))
    push!(out, ("wired bisection", 3, "V_clearing_rate_band_m", "r2300", Vstar, 5.66,
                Vstar / 5.66))
    ## And what that V costs at 2300 on OUR ssp585 -- the trade the decision is about.
    bf = ladrillo_setup(ssp = "ssp585", y0 = Y0, y1 = Y1, gis_variant = variant)
    ladrillo_set_tap!(bf; v = Vstar)
    g = Array{Float64}(undef, length(bf.years), nrow(post))
    for (j, r) in enumerate(eachrow(post))
        ladrillo_run_draw!(bf, r); g[:, j] = ladrillo_series(bf, :gis)
    end
    med = [median(filter(isfinite, @view g[i, :])) for i in 1:length(bf.years)]
    v23 = med[findfirst(==(2300), bf.years)]
    @printf("     it gives our ssp585 Greenland@2300 = %.1f cm = %.3fx the matched p50 %.1f\n",
            v23, v23 / MATCHED_2300.p50, MATCHED_2300.p50)
    push!(out, ("wired bisection", 2, "gis_2300_at_rate_clearing_V", "SSP5-8.5", v23,
                MATCHED_2300.p50, v23 / MATCHED_2300.p50))
end

## ---- THE INERTNESS CLAIM, MEASURED NOT ASSERTED ------------------------------
println("\n=== IS THE RESERVOIR REALLY INERT OVER THE OBSERVED RECORD? ===")
println("  The whole priority-1 argument rests on it, so it is measured on the SHIPPED")
println("  model rather than inherited from the emulator that produced the claim.")
base = proj[("Ladrillo L14, untapped", "SSP5-8.5")]
for (nm, _, vcell) in ARMS
    vcell === nothing && continue
    p = proj[(nm, "SSP5-8.5")]
    m = p.years .<= CALIB_WIN[2]
    d = maximum(abs.(p.med[m] .- base.med[m]))
    @printf("     %-32s max|tapped - untapped| over %d-%d = %.3e cm\n",
            nm, minimum(p.years), CALIB_WIN[2], d)
    push!(out, (nm, 1, "hindcast_deviation_cm", "-", d, 0.0, NaN))
end

CSV.write(OUT, out)
println("\nwrote ", relpath(OUT, REPO))
