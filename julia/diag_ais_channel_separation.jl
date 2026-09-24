## ============================================================================
## diag_ais_channel_separation.jl — WOULD A DYNAMICS CONSTRAINT IDENTIFY WHAT THE LEVEL
## CHANNEL CANNOT? (Marcus 09-22: "could adding a dynamics constraint help make a good model?")
##
## ⚠ THIS ASKS A DIFFERENT QUESTION FROM diag_ais_dynamics_channel_profile.jl, AND THE
## DIFFERENCE IS THE POINT. That script priced option D1 against the RAMP direction and found
## <=3 log-units, because sigma_dyn (76 Gt/yr, 150 over 2020-23) swamps a small perturbation.
## It answered "does a dynamics channel RESCUE the ramp?" -- no.
##
## The question here is IDENTIFICATION, not fit: does a dynamics channel SEPARATE two arms that
## the level channel cannot tell apart? That matters because the separation is not hypothetical.
## `diag_ais_objective_shape_sensitivity_L30.csv` measures the level channel as NUMERICALLY
## INDIFFERENT between a constant discharge offset and a late divergence of the same terminal
## size -- q 2.5343 vs 2.5308, ratio 1.001 -- AT THE POSTERIOR'S OWN rho of 0.966. At rho 0.90
## the ratio is 1.74 and at 0.60 it is 2.03, so the blindness is a FUNCTION OF rho, and rho_ais
## is SAMPLED: it went 0.893 (L27) -> 0.966 (L28/L30) when the target became the IMBIE level.
##
## The arms are therefore a natural experiment along the degeneracy direction:
##   L27  rho 0.893   the shipped posterior, fitted to the Frederikse-era AIS target
##   L28  rho 0.966   the SAME objective refitted to the IMBIE level, rho FREE
##   L29  rho 0.885   the same refit with rho CAPPED at 0.90   -- the alternative fix, already run
##   L30  rho 0.967   L28 plus the additional discharge response (--ais-ramp)
## L27 and L28 differ by ~33 Gt/yr in BASELINE discharge and ~48 Gt/yr in the 2018-23 ANOMALY,
## i.e. L28 bought the cumulative with a level shift and paid for it in TREND
## ([[ais_net_dynamics_tradeoff_identity]]). That is a far larger perturbation than the ramp.
##
## WHAT IS MEASURED. Every arm's own draws are scored on TWO COMMON channels:
##   LEVEL     hetero_logl_ar1(model - obs, sigma, rho, eps, L=100) on recalib_targets_ext.csv
##             `ais`, 1900-2025 -- the calibrator's own Antarctic term, re-implemented (12 lines)
##             because calibrate_mcmc_ext.jl parses ARGS at top level.
##   DYNAMICS  the model's discharge anomaly against IMBIE 2026's dynamics anomaly, 1979-2023,
##             on a COMMON anomaly reference applied to model AND obs (like-for-like).
##
## ⚠ THE LEVEL CHANNEL IS EVALUATED AT A COMMON (sigma, rho), NOT AT EACH ARM'S OWN.
## A log-likelihood level is not comparable across arms that sampled different sigma -- a smaller
## sigma inflates every penalty. Each arm's own (sigma, rho) is used as a COMMON SETTING in turn,
## and the arm-to-arm DIFFERENCE is reported under each. A conclusion that survives both settings
## is a conclusion about the arms; one that flips is a conclusion about the noise model.
##
## ⚠ THE LEVEL TARGET IS THE IMBIE ONE FOR EVERY ARM, INCLUDING L27. recalib_targets_ext.csv has
## carried AIS_SOURCE = "imbie2026" since L28 and the Frederikse-era file L27 was actually fitted
## to is gone. That is correct FOR THIS TEST -- a common channel is exactly what is wanted -- but
## it means L27's level score is out-of-sample and must never be read as "L27 fits worse".
##
## ⚠ THE NOISE MODEL FOR THE DYNAMICS CHANNEL IS A METHODOLOGICAL CHOICE AND IS NOT RESOLVED
## HERE (Marcus's, per ~/.claude/CLAUDE.md). The same three as the D1 script are reported side
## by side: IND (published per-year sigma_dyn), AR1 (rho 0.8 on the same sigma), WIN (the five
## IMBIE window means, sigma/sqrt(n)). None is adopted.
##
## NOTHING IS REFITTED. Every draw runs at its own posterior parameters.
##
##   julia --project=julia_v2 julia/diag_ais_channel_separation.jl [--arms=L27,L28,L29,L30] [ndraw]
##
## ⚠ THE OUTPUT PATHS CARRY THE ARM LIST, AND THE UNTAGGED PATH IS RETIRED. Writes
## outputs/diag_ais_channel_separation_<ARMS>.csv (per draw) and _<ARMS>_summary.csv (per arm),
## where <ARMS> is the joined --arms list -- so a run over L27,L34 CANNOT overwrite a run over
## L27,L28,L32,L33. Both names derive from OUT_STEM below, per the repo convention that labels
## and filenames come from named constants.
##
## ⚠ outputs/diag_ais_channel_separation{,_summary}.csv -- NO TAG -- are FROZEN PROVENANCE for the
## 2026-09-23 L27/L28/L32/L33 run whose dynamics anomalies (-133.1 L32, -126.2 L33) CHANGELOG cites
## as the floor-insensitivity record. Byte-identical copies sit at
## ..._20260923_L27L28L32L33.csv. This script asserts it will never write those names again: a
## 2026-09-24 L27,L34 run had already overwritten them in place before the tag existed, and that
## content was recovered to ..._L27L34.csv.
## ============================================================================
using CSV, DataFrames, Mimi, MimiBRICK, Statistics, Printf, Dates, LinearAlgebra, Distributions

include(joinpath(@__DIR__, "ladrillo_projection.jl"))
include(joinpath(@__DIR__, "antarctic_icesheet_magdep_component.jl"))

const SCRIPT = "diag_ais_channel_separation.jl"
const ARMS   = (i = findfirst(a -> startswith(a, "--arms="), ARGS);
                i === nothing ? ["L27", "L28", "L29", "L30"] : String.(split(ARGS[i][8:end], ",")))
const NDRAW  = (p = filter(a -> !startswith(a, "--"), ARGS); length(p) >= 1 ? parse(Int, p[1]) : 100)

## ---- the output paths, tagged with the arm list ----------------------------------------------
## EVERY reference to these files -- the CSV.write calls and the closing read-out -- derives from
## OUT_STEM, so the tag cannot drift out of step with the arms actually run.
const ARM_TAG      = join(ARMS)                                    # L27,L34 -> "L27L34"
const OUT_STEM     = "diag_ais_channel_separation_$ARM_TAG"
const OUT_DRAWS    = joinpath(LADRILLO_REPO, "outputs", "$OUT_STEM.csv")
const OUT_SUMMARY  = joinpath(LADRILLO_REPO, "outputs", "$(OUT_STEM)_summary.csv")
const UNTAGGED_STEM = "diag_ais_channel_separation"                 # retired; frozen provenance
@assert(!isempty(ARMS) && all(a -> !isempty(strip(a)), ARMS),
        "--arms is empty or has an empty entry ($(repr(ARMS))): refusing to run, because an " *
        "empty tag would land on the retired untagged path")
## ⚠ MUTATION-TESTED, and the OBVIOUS form of this gate has NO POWER: with an empty tag the stem
## is "..._" -- NOT equal to UNTAGGED_STEM -- so `OUT_STEM != UNTAGGED_STEM` can never fire. The
## gate that bites is that the stem must NAME EVERY ARM; forcing ARM_TAG = "" trips it.
@assert(OUT_STEM != UNTAGGED_STEM && all(a -> occursin(a, OUT_STEM), ARMS),
        "output stem $OUT_STEM does not carry every arm in $(join(ARMS, ",")): refusing to run, " *
        "because an untagged or partly-tagged name can silently overwrite another arm set " *
        "(the retired $UNTAGGED_STEM{,_summary}.csv are frozen 2026-09-23 provenance)")

## The calibration's own frame, copied from calibrate_mcmc_ext.jl.
const Y0, Y1, B0, B1 = 1850, 2026, 1995, 2005
const FORCING      = "ssp245harm"
const TARGETS      = joinpath(LADRILLO_REPO, "outputs/recalib_targets_ext.csv")
const IMBIE        = joinpath(LADRILLO_REPO, "data/observations/raw/imbie2026/imbie3_antarctica_Gt_partitioned.csv")
const OBS_CORR_LEN = 100.0                 # --obs-corr-len=100, the L27+ setting
const LEVEL_Y0     = 1900                  # the AIS level term's span (upper end = the target's last year)
const M3ICE_TO_GT  = 917.0 / 1e12
const REF_Y0, REF_Y1 = 1979, 2008          # COMMON anomaly reference, applied to model AND obs
const FIT_Y0, FIT_Y1 = 1979, 2023          # IMBIE Antarctica's own span
const WINS      = [(1979, 1991), (1992, 2002), (2003, 2010), (2011, 2017), (2018, 2023)]
const AR1_RHO   = 0.8                      # the AR1 variant's correlation; a CHOICE, reported not adopted
const TREND_WIN = (2018, 2023)             # the window the flat-vs-accelerating contrast lives in
const BASE_WIN  = (REF_Y0, REF_Y1)

ϵband(lo, hi) = max.((hi .- lo) ./ (2 * 1.645), 0.05)
function hetero_logl_ar1(res, σ, ρ, ϵ, L = OBS_CORR_LEN)
    n = length(res); σp = σ^2 / (1 - ρ^2)
    H = abs.(collect(1:n)' .- collect(1:n))
    Σ = L > 0 ? σp .* ρ .^ H .+ (ϵ * ϵ') .* exp.(-H ./ L) : σp .* ρ .^ H .+ Diagonal(ϵ .^ 2)
    return logpdf(MvNormal(Symmetric(Σ)), res)
end

## ---- the LEVEL channel's target ------------------------------------------------------------
tg = CSV.read(TARGETS, DataFrame)
ly = [Int(tg.year[i]) for i in 1:nrow(tg)
      if tg.year[i] >= LEVEL_Y0 && !ismissing(tg.ais[i]) && !isnan(Float64(tg.ais[i]))]
sort!(ly); @assert ly == collect(ly[1]:ly[end]) "AIS level target has a year gap"
ti      = [findfirst(==(y), tg.year) for y in ly]
lev_obs = Float64.(tg.ais[ti])
lev_eps = ϵband(Float64.(tg.ais_lo[ti]), Float64.(tg.ais_hi[ti]))

## ---- the DYNAMICS channel's target ---------------------------------------------------------
raw = CSV.read(IMBIE, DataFrame; comment = "#")
yr  = [parse(Int, first(string(d), 4)) for d in raw[!, "Date"]]
dyncol, sigcol = "Dynamics mass balance anomaly (Gt/yr)", "Dynamics mass balance anomaly uncertainty (Gt/yr)"
ann = combine(groupby(DataFrame(year = yr, dyn = raw[!, dyncol], sig = raw[!, sigcol]), :year),
              :dyn => mean => :dyn, :sig => mean => :sig)
sort!(ann, :year)
ann  = ann[(ann.year .>= FIT_Y0) .& (ann.year .<= FIT_Y1), :]
oref = mean(ann[(ann.year .>= REF_Y0) .& (ann.year .<= REF_Y1), :dyn])
ann.anom = ann.dyn .- oref
dy = ann.year; nY = length(dy)

Σ_ind = Diagonal(ann.sig .^ 2)
Hd    = abs.(collect(1:nY)' .- collect(1:nY))
Σ_ar1 = (ann.sig * ann.sig') .* (AR1_RHO .^ Hd)
ll(res, Σ) = logpdf(MvNormal(Symmetric(Matrix(Σ))), res)

@printf("%s | arms %s | %d draw(s)/arm\n", SCRIPT, join(ARMS, ","), NDRAW)
@printf("  WRITES   : %s\n             %s\n",
        relpath(OUT_DRAWS, LADRILLO_REPO), relpath(OUT_SUMMARY, LADRILLO_REPO))
@printf("  LEVEL    : %s `ais` %d-%d (%d yr), eps mean %.4f cm, L=%.0f\n",
        basename(TARGETS), ly[1], ly[end], length(ly), mean(lev_eps), OBS_CORR_LEN)
@printf("  DYNAMICS : IMBIE 2026 dynamics anomaly %d-%d (%d yr), common ref %d-%d (obs ref mean %.1f Gt/yr)\n",
        dy[1], dy[end], nY, REF_Y0, REF_Y1, oref)
@printf("             IMBIE %d-%d dynamics anomaly = %.1f Gt/yr | published sigma_dyn median %.1f\n",
        TREND_WIN[1], TREND_WIN[2], mean(ann[(ann.year .>= TREND_WIN[1]) .& (ann.year .<= TREND_WIN[2]), :anom]),
        median(ann.sig))

## ---- the COMMON (sigma, rho) settings the level channel is evaluated at ---------------------
## Each arm's own posterior median pair becomes a common setting applied to EVERY arm.
setting = Tuple{String,Float64,Float64}[]
for arm in ARMS
    pp = CSV.read(joinpath(LADRILLO_REPO, "outputs/ladrillo_prior_posterior_$arm.csv"), DataFrame)
    g(n) = Float64(pp[findfirst(==(n), pp.name), :p50])
    push!(setting, (arm, g("sd_ais"), g("rho_ais")))
end
println("\n  level-channel settings (each arm's posterior median, applied to ALL arms):")
for (a, s, r) in setting; @printf("    from %-4s  sd_ais %.4f  rho_ais %.4f\n", a, s, r); end

## ---- run ------------------------------------------------------------------------------------
rows = DataFrame()
for arm in ARMS
    path = joinpath(LADRILLO_REPO, "data/MimiBRICK/parameters_subsample_brick_mengel_$arm.csv")
    post = ladrillo_posterior(path = path, cols = :all, nthin = NDRAW)
    ladrillo_attach_propagated!(post)
    has_ramp = ladrillo_has_ramp(String.(names(post)))
    bf = ladrillo_setup(ssp = "ssp245", y0 = Y0, y1 = Y1, forcing_tag = FORCING, ref = (B0, B1),
                        lws = :central, gis_variant = ladrillo_posterior_variant(path), ais_ramp = has_ramp)
    lmi = [ladrillo_yi(bf, y) for y in ly]
    dmi = [ladrillo_yi(bf, y) for y in dy]
    rmi = [ladrillo_yi(bf, y) for y in REF_Y0:REF_Y1]
    @printf("\n[%s] %d draws, ramp column present: %s\n", arm, nrow(post), has_ramp); flush(stdout)

    for (di, r) in enumerate(eachrow(post))
        ladrillo_run_draw!(bf, r)
        ## ⚠ MODEL DYNAMICS = ice_flux + disintegration_rate. The fast-dynamics term carries the
        ## ramp, so `ice_flux` alone makes an L30 response nearly invisible -- the false negative
        ## diag_ais_dynamics_channel_profile.jl documents at its line ~98. For the non-ramp arms
        ## disintegration_rate is identically 0 over the hindcast (no draw tips before 2024), so
        ## the two readings agree there; this form is correct for BOTH.
        gv(sym) = [ismissing(e) ? NaN : Float64(e) for e in bf.m[:antarctic_icesheet, sym]] .* M3ICE_TO_GT
        dis  = gv(:ice_flux) .+ gv(:disintegration_rate)
        anom = dis[dmi] .- mean(dis[rmi])        # SAME reference construction as the obs
        dres = anom .- ann.anom

        ser  = ladrillo_series(bf, :ais)
        lres = ser[lmi] .- lev_obs

        row = DataFrame(arm = arm, draw = di,
                        ll_dyn_ind = ll(dres, Σ_ind), ll_dyn_ar1 = ll(dres, Σ_ar1),
                        cum_1979_2023 = ser[ladrillo_yi(bf, 2023)] - ser[ladrillo_yi(bf, 1978)],
                        dis_base = mean(dis[[ladrillo_yi(bf, y) for y in BASE_WIN[1]:BASE_WIN[2]]]),
                        dis_trend_anom = mean(anom[findall(y -> TREND_WIN[1] <= y <= TREND_WIN[2], dy)]))
        for (a, s, ρ) in setting
            row[!, "ll_lev_from$a"] = [hetero_logl_ar1(lres, s, ρ, lev_eps)]
        end
        zs = 0.0
        for (a, b) in WINS
            k  = findall(y -> a <= y <= b, dy)
            sw = mean(ann.sig[k]) / sqrt(length(k))
            zs += ((mean(anom[k]) - mean(ann.anom[k])) / sw)^2
            row[!, "win_$(a)_$(b)"] = [mean(anom[k]) - mean(ann.anom[k])]
        end
        row.ll_dyn_win = [-0.5 * zs]
        append!(rows, row)
        di % 20 == 0 && (@printf("  %d/%d\n", di, nrow(post)); flush(stdout))
    end
end

rows.provenance .= "$SCRIPT | arms $(join(ARMS, ",")) | $NDRAW draw(s)/arm, DETERMINISTIC even thinning " *
    "(_ladrillo_thin, no RNG) | paleo fast-dynamics rows assigned by FIXED seed $LADRILLO_PALEO_SEED | " *
    "LEVEL = hetero_logl_ar1(model-obs, sd, rho, eps, L=$OBS_CORR_LEN) on $(ly[1])-$(ly[end]) of " *
    "$(basename(TARGETS)) (AIS_SOURCE imbie2026 for EVERY arm incl. L27, whose own target is superseded) | " *
    "DYNAMICS = model (ice_flux + disintegration_rate) anomaly vs IMBIE 2026 dynamics anomaly " *
    "$(dy[1])-$(dy[end]), common ref $REF_Y0-$REF_Y1 | IND = published per-year sigma_dyn; AR1 = rho $AR1_RHO; " *
    "WIN = $(length(WINS)) window means, sigma/sqrt(n) | noise model NOT adopted | forcing $FORCING | " *
    "no refit, every draw at its own posterior parameters | $(now())"
CSV.write(OUT_DRAWS, rows)

## ---- report -----------------------------------------------------------------------------------
se(v) = std(v) / sqrt(length(v))
summ = DataFrame()
for arm in ARMS
    g = rows[rows.arm .== arm, :]
    d = Dict{String,Any}("arm" => arm, "n" => nrow(g))
    for c in ["ll_dyn_ind", "ll_dyn_ar1", "ll_dyn_win", "cum_1979_2023", "dis_base", "dis_trend_anom"]
        d[c] = mean(g[!, c]); d[c * "_se"] = se(g[!, c])
    end
    for (a, _, _) in setting
        d["ll_lev_from$a"] = mean(g[!, "ll_lev_from$a"]); d["ll_lev_from$(a)_se"] = se(g[!, "ll_lev_from$a"])
    end
    append!(summ, DataFrame(d))
end
summ.provenance .= rows.provenance[1]
CSV.write(OUT_SUMMARY, summ)

println("\n" * "="^100)
@printf("DISCHARGE, by arm (Gt/yr, ice-mass sign; anomaly vs %d-%d). IMBIE %d-%d anomaly = %.1f\n",
        REF_Y0, REF_Y1, TREND_WIN[1], TREND_WIN[2],
        mean(ann[(ann.year .>= TREND_WIN[1]) .& (ann.year .<= TREND_WIN[2]), :anom]))
@printf("  %-5s %14s %18s %18s\n", "arm", "cum79-23 cm", "baseline dis", "$(TREND_WIN[1])-$(TREND_WIN[2]) anom")
for arm in ARMS
    s = summ[summ.arm .== arm, :][1, :]
    @printf("  %-5s %8.3f±%-5.3f %11.1f±%-5.1f %11.1f±%-5.1f\n", arm,
            s.cum_1979_2023, s.cum_1979_2023_se, s.dis_base, s.dis_base_se,
            s.dis_trend_anom, s.dis_trend_anom_se)
end

println("\n" * "="^100)
println("CHANNEL SEPARATION. Each channel's log-likelihood, mean ± SE over draws.")
println("A channel that IDENTIFIES the arms separates them by many units; one that is BLIND does not.")
hdr = ["ll_dyn_ind" => "DYN ind", "ll_dyn_ar1" => "DYN ar1", "ll_dyn_win" => "DYN win"]
append!(hdr, ["ll_lev_from$a" => "LEV @$a" for (a, _, _) in setting])
@printf("\n  %-5s", "arm"); for (_, h) in hdr; @printf("%20s", h); end; println()
for arm in ARMS
    s = summ[summ.arm .== arm, :][1, :]
    @printf("  %-5s", arm)
    for (c, _) in hdr; @printf("%13.1f±%-6.1f", s[c], s[c * "_se"]); end
    println()
end

if length(ARMS) >= 2
    println("\n  PAIRWISE SEPARATION (row - col arm), per channel. |diff| >> its SE = the channel SEES the difference.")
    for (c, h) in hdr
        @printf("\n    %s\n", h)
        @printf("      %-5s", "")
        for a in ARMS; @printf("%14s", a); end; println()
        for a in ARMS
            @printf("      %-5s", a)
            for b in ARMS
                ga = rows[rows.arm .== a, c]; gb = rows[rows.arm .== b, c]
                d = mean(ga) - mean(gb); sd_ = sqrt(se(ga)^2 + se(gb)^2)
                a == b ? @printf("%14s", "-") : @printf("%9.1f±%-4.1f", d, sd_)
            end
            println()
        end
    end
end
@printf("\nwrote %s\n      %s\n", relpath(OUT_DRAWS, LADRILLO_REPO), relpath(OUT_SUMMARY, LADRILLO_REPO))
