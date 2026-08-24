## ============================================================================
## scope_ais_three_tests.jl — the three tests Marcus called for, 2026-08-24
##
## ONE chain read serves all three; the read dominates the runtime (~12 min for
## 4 x 2e6-row chains) and splitting these into three files would triple it.
##
## TEST 1 — WHICH OF RUCKERT'S FOUR CONSTRAINTS ACTUALLY TOUCHES lambda?
##   The DAIS paleo calibration (Ruckert et al. 2017, PLoS ONE 12:e0170052) uses
##   FOUR LEVEL constraints: LIG (~120 kyr BP), LGM (~20 kyr BP), mid-Holocene
##   (~6 kyr BP), instrumental (1992-2011). Fast dynamics only fires above
##   `temperature_threshold`, so a window whose T_ant never crosses Tcrit carries
##   ZERO information about lambda. If only one window fires, the "paleo prior on
##   lambda" rests on ONE data point, not four.
##   The map is exact and its anchor is PRESERVED under the A6 amp resampling
##   (`calibrate_mcmc_ext.jl:1106`): T_ant = T_ANT0 + amp * dGMST, so
##   dGMST_crossing = (Tcrit - T_ANT0)/amp is computable per draw. Both halves are
##   reported: the paleo windows in ABSOLUTE T_ant (which is what Ruckert forced
##   DAIS with), and our own drivers in dGMST.
##
## TEST 2 — THE AIS OBSERVED-DATA-FIRST SCORECARD, SCORING ACCELERATION
##   `diag_gis_obs_scorecard.py` established for Greenland that the hindcast
##   matches LEVEL and RATE but under-runs ACCELERATION (0.65x observed). That
##   gate has never been run on Antarctica. ⚠ The AIS series is a FITTED
##   likelihood stream (`calibrate_mcmc_ext.jl:1242`), so the level over the
##   target window is fitted BY CONSTRUCTION and is not evidence; the SHAPE and
##   especially the CURVATURE are the parts the AR(1)-on-levels likelihood
##   constrains weakly. Report which is which, as the Greenland file does.
##
## TEST 3 — A lambda LADDER, so any rate band maps to the deliverable with no re-run
##   `scope_ais_lambda_prior.jl` measured three lambda points and found the AIS
##   2300 response linear to 0.6 cm. A LADDER over the whole paleo support (a) tests
##   that linearity properly rather than on three points, and (b) makes every future
##   lambda band -- MWP-1A, a kinematic bound, anything -- a POST-PROCESSING step
##   instead of another 12-minute chain read. Deliberately NOT hard-coding one
##   MWP-1A number: the Antarctic share of MWP-1A is contested across the
##   literature, and baking one estimate into a driver would hide that.
##
##   julia --project=julia_v2 julia/scope_ais_three_tests.jl [n_per_chain] [--tag=L14] [--maxrows=N]
##   Writes outputs/scope_ais_three_tests_{crossing,scorecard,ladder}_<tag>.csv
## ============================================================================
using CSV, DataFrames, Statistics, Printf, Distributions

include(joinpath(@__DIR__, "ladrillo_projection.jl"))

const REPO  = LADRILLO_REPO
const SEEDS = [2026, 2027, 2028, 2029]
const NITER = 2000000
const NBURN = 1000000
const TAG = let i = findfirst(a -> startswith(a, "--tag="), ARGS)
    i === nothing ? "L14" : ARGS[i][7:end]
end
const MAXROWS = let i = findfirst(a -> startswith(a, "--maxrows="), ARGS)
    i === nothing ? nothing : parse(Int, ARGS[i][11:end])
end
const SMOKE = MAXROWS !== nothing
const N_TARGET = let p = findfirst(a -> !startswith(a, "--"), ARGS)
    p === nothing ? 500 : parse(Int, ARGS[p])
end
const SFX = SMOKE ? "_SMOKE" : ""
const LAM, TCR, AMP = "antarctic_lambda", "antarctic_temp_threshold", "ais_gmst_amp"

## ---- TEST 1 constants ----------------------------------------------------
## The DAIS map's preserved anchor: T_ant(dGMST = 0) on the paleo scale.
const T_ANT0 = LADRILLO_AIS_TANT0                       # = -18.4340 degC
## Ruckert et al. 2017's four constraint windows, as ANTARCTIC temperature
## anomalies relative to pre-industrial. DAIS is forced with Antarctic temperature
## directly, so this -- not dGMST -- is the like-for-like axis for the paleo half.
## Ranges are deliberately GENEROUS (they bracket the spread across reconstructions)
## so a "does not fire" verdict is conservative: a window is only declared inert if
## even its WARM end fails to cross.
const PALEO_WINDOWS = [
    ("LIG  ~120 kyr BP", 3.0,  6.0),
    ("LGM  ~20 kyr BP", -10.0, -7.0),
    ("MH   ~6 kyr BP",   0.0,  1.5),
    ("instrumental 1992-2011", 0.3, 1.2),
]
const HIND_WIN = (1850, 2024)

## ---- TEST 2 constants ----------------------------------------------------
const TARGETS_CSV = joinpath(REPO, "outputs/recalib_targets_ext.csv")
## Same window set as the Greenland scorecard so the two read side by side.
const SHAPE_WINS   = [(1900, 1950), (1950, 1990), (1993, 2010), (2010, 2024)]
const OBS_RATE_WIN = (1995, 2024)
const ACCEL_WIN    = (1993, 2024)   # the Greenland file's curvature window

## ---- TEST 3 constants ----------------------------------------------------
const LADDER_N  = 15
const SSPS      = ["ssp245", "ssp585"]
const HORIZONS  = [2100, 2150, 2300]
const Y0, Y1    = 1850, 2300
const COMPONENT = :ais

const PRI = CSV.read(joinpath(REPO, "outputs/param_priors.csv"), DataFrame)
prow(n) = PRI[findfirst(==(n), PRI.param), :]
const PALEO = CSV.read(joinpath(REPO, "data/dais_paleo/daisfastdyn_lambda_tcrit.csv"), DataFrame)
const P_LAM = Float64.(PALEO.lambda)
const LAM_LADDER = collect(range(minimum(P_LAM), maximum(P_LAM); length = LADDER_N))

chain_path(sd) = joinpath(REPO, "outputs/mcmc", "chain_$(TAG)_seed$(sd)_n$(NITER).csv")
hdr(sd) = String.(propertynames(CSV.read(chain_path(sd), DataFrame; limit = 0)))
for sd in SEEDS; isfile(chain_path(sd)) || error("missing chain $(chain_path(sd))"); end
const VARIANT = ladrillo_gis_variant(hdr(SEEDS[1]))

@printf("AIS three tests | tag %s%s | %d draws/chain x %d chains\n",
        TAG, SMOKE ? "  ** SMOKE **" : "", N_TARGET, length(SEEDS))
@printf("  T_ant anchor %.4f degC | lambda ladder %d points over [%.6f, %.6f]\n",
        T_ANT0, LADDER_N, first(LAM_LADDER), last(LAM_LADDER))
flush(stdout)

function read_draws(sd)
    need = vcat(ladrillo_used_cols(VARIANT), [LAM, TCR, AMP]) |> unique
    h = hdr(sd)
    rd = ladrillo_gis_needs_native(h) ?
        vcat(setdiff(need, LADRILLO_GIS_SLOW_NATIVE_COLS),
             LADRILLO_GIS_SLOW_REPARAM_COLS) |> unique : need
    miss = setdiff(rd, h); isempty(miss) || error("missing: " * join(miss, ", "))
    df = SMOKE ? CSV.read(chain_path(sd), DataFrame; select = rd, limit = MAXROWS) :
                 CSV.read(chain_path(sd), DataFrame; select = rd)
    nb = SMOKE ? 0 : NBURN
    step = max(1, (nrow(df) - nb) ÷ N_TARGET)
    idx = collect((nb + 1):step:nrow(df))
    d = ladrillo_native_greenland!(df[idx[1:N_TARGET], :]); df = nothing; GC.gc(); d
end

const DRAWS = [(@printf("  reading chain seed%d ...\n", sd); flush(stdout); read_draws(sd))
               for sd in SEEDS]
const ALL_TCR = vcat([Float64.(d[!, TCR]) for d in DRAWS]...)
const ALL_AMP = vcat([Float64.(d[!, AMP]) for d in DRAWS]...)
const ALL_LAM = vcat([Float64.(d[!, LAM]) for d in DRAWS]...)
const NDRAW = length(ALL_TCR)

## ===========================================================================
## TEST 1 — which constraint windows fire?
## ===========================================================================
@printf("\n%s\nTEST 1 — WHICH OF RUCKERT'S FOUR CONSTRAINTS TOUCHES lambda?\n%s\n",
        repeat("=", 78), repeat("=", 78))
@printf("Fast dynamics fires only where T_ant > Tcrit (antarctic_icesheet_component.jl:180).\n")
@printf("Posterior Tcrit: median %.3f, p05 %.3f, p95 %.3f degC (absolute, DAIS paleo scale)\n",
        median(ALL_TCR), quantile(ALL_TCR, 0.05), quantile(ALL_TCR, 0.95))
@printf("Anchor T_ant(dGMST=0) = %.4f  =>  Antarctic warming needed to fire:\n", T_ANT0)
const DT_FIRE = ALL_TCR .- T_ANT0
@printf("   median %.3f degC  [p05 %.3f, p95 %.3f]\n",
        median(DT_FIRE), quantile(DT_FIRE, 0.05), quantile(DT_FIRE, 0.95))

t1 = DataFrame(window = String[], dT_ant_lo = Float64[], dT_ant_hi = Float64[],
               frac_fire_at_lo = Float64[], frac_fire_at_hi = Float64[], verdict = String[])
@printf("\n%-26s %11s %11s %10s %10s   %s\n",
        "constraint window", "dT_ant lo", "dT_ant hi", "fire@lo", "fire@hi", "verdict")
for (nm, lo, hi) in PALEO_WINDOWS
    flo = mean(DT_FIRE .< lo); fhi = mean(DT_FIRE .< hi)
    v = fhi < 0.01 ? "INERT — carries no lambda information" :
        flo > 0.99 ? "FIRES for ~all draws" : "PARTIAL"
    @printf("%-26s %11.2f %11.2f %9.1f%% %9.1f%%   %s\n", nm, lo, hi, 100flo, 100fhi, v)
    push!(t1, (nm, lo, hi, flo, fhi, v))
end
CSV.write(joinpath(REPO, "outputs", "scope_ais_three_tests_crossing_$(TAG)$(SFX).csv"), t1)

## Our own drivers: dGMST needed, and the in-model crossing year.
@printf("\nOur drivers (transient amp, N(0.95,0.10)): dGMST needed to fire =\n")
const DGMST_FIRE = DT_FIRE ./ ALL_AMP
@printf("   median %.3f degC  [p05 %.3f, p95 %.3f]   (amp median %.3f)\n",
        median(DGMST_FIRE), quantile(DGMST_FIRE, 0.05), quantile(DGMST_FIRE, 0.95),
        median(ALL_AMP))

## ===========================================================================
## TEST 2 + 3 — one setup per scenario, reused
## ===========================================================================
## dropmissing + explicit Float64: the targets file is a PER-SERIES layout (each
## component fit over its own valid window), so sibling columns carry `missing` and
## the AIS columns come back Union{Missing,Float64} even where they are complete.
const TGT = let t = CSV.read(TARGETS_CSV, DataFrame; select = [:year, :ais, :ais_lo, :ais_hi])
    t = dropmissing(t)
    DataFrame(year = Int.(t.year), ais = Float64.(t.ais),
              ais_lo = Float64.(t.ais_lo), ais_hi = Float64.(t.ais_hi))
end
rate_mm_yr(v, yrs, w) = let i0 = findfirst(==(w[1]), yrs), i1 = findfirst(==(w[2]), yrs)
    (i0 === nothing || i1 === nothing) ? NaN : (v[i1] - v[i0]) / (w[2] - w[1])
end
"""Quadratic-fit acceleration (mm/yr^2) of a cumulative series over a window."""
function accel_mm_yr2(v, yrs, w)
    i0 = findfirst(==(w[1]), yrs); i1 = findfirst(==(w[2]), yrs)
    (i0 === nothing || i1 === nothing) && return NaN
    x = Float64.(yrs[i0:i1] .- yrs[i0]); y = Float64.(v[i0:i1])
    X = hcat(ones(length(x)), x, x .^ 2)
    2 * (X \ y)[3]
end

sc = DataFrame(quantity = String[], window = String[], ours = Float64[],
               obs = Float64[], ratio = Float64[], obs_lo = Float64[], obs_hi = Float64[],
               in_band = Bool[], status = String[])
ladder = DataFrame(scenario = String[], horizon = Int[], lambda = Float64[],
                   median_cm = Float64[], p05_cm = Float64[], p95_cm = Float64[])
cross = DataFrame(scenario = String[], frac_ever_cross = Float64[],
                  cross_yr_p05 = Float64[], cross_yr_med = Float64[], cross_yr_p95 = Float64[])

for ssp in SSPS
    bf = ladrillo_setup(ssp = ssp, y0 = Y0, y1 = Y1, gis_variant = VARIANT)
    yrs = bf.years

    ## ---- crossing years, and (once) the AIS hindcast scorecard -----------
    cy = Float64[]; nev = 0
    ais_hist = Vector{Vector{Float64}}()
    for d in DRAWS, r in eachrow(d)
        ladrillo_run_draw!(bf, r)
        ## Mimi returns Union{Missing,Float64}: the AIS component steps from t-1, so
        ## t = 1 is `missing`. coalesce to -Inf (never above threshold) rather than
        ## dropping, so the year index still lines up with `yrs`.
        tant = coalesce.(bf.m[:antarctic_icesheet, :antartic_surface_temperature], -Inf)
        thr  = Float64(r[TCR])
        k = findfirst(>(thr), tant)
        if k === nothing; nev += 1 else push!(cy, Float64(yrs[k])) end
        ssp == SSPS[1] && push!(ais_hist, coalesce.(ladrillo_series(bf, COMPONENT), NaN))
    end
    fr = 1 - nev / NDRAW
    push!(cross, (ssp, fr, isempty(cy) ? NaN : quantile(cy, 0.05),
                  isempty(cy) ? NaN : median(cy), isempty(cy) ? NaN : quantile(cy, 0.95)))
    @printf("\n%s: %.1f%% of draws EVER cross Tcrit by %d; crossing year median %.0f [%.0f, %.0f]\n",
            ssp, 100fr, Y1, isempty(cy) ? NaN : median(cy),
            isempty(cy) ? NaN : quantile(cy, 0.05), isempty(cy) ? NaN : quantile(cy, 0.95))
    ## how many cross within the HINDCAST -- the "observationally unidentified" claim
    if !isempty(cy)
        @printf("   within the hindcast %d-%d: %.2f%% of ALL draws\n",
                HIND_WIN[1], HIND_WIN[2], 100 * count(<=(HIND_WIN[2]), cy) / NDRAW)
    end
    flush(stdout)

    ## ---- TEST 2 (once, on the first scenario: the hindcast is shared) -----
    if ssp == SSPS[1]
        @printf("\n%s\nTEST 2 — AIS OBSERVED-DATA-FIRST SCORECARD\n%s\n",
                repeat("=", 78), repeat("=", 78))
        med = [median(getindex.(ais_hist, i)) for i in eachindex(yrs)]
        oy  = TGT.year
        ## rebase both to the first target year so levels are comparable
        i0m = findfirst(==(oy[1]), yrs)
        mr  = med .- med[i0m]
        ov  = TGT.ais .- TGT.ais[1]
        olo = TGT.ais_lo .- TGT.ais_lo[1]
        ohi = TGT.ais_hi .- TGT.ais_hi[1]
        @printf("%-12s %-12s %9s %9s %8s %18s  %s\n",
                "quantity", "window", "ours", "obs", "ratio", "obs band", "status")
        for w in vcat(SHAPE_WINS, [OBS_RATE_WIN])
            ro = rate_mm_yr(ov, oy, w); rm = rate_mm_yr(mr, yrs, w)
            rlo = rate_mm_yr(olo, oy, w); rhi = rate_mm_yr(ohi, oy, w)
            (isnan(ro) || isnan(rm)) && continue
            b = min(rlo, rhi) <= rm <= max(rlo, rhi)
            st = w == OBS_RATE_WIN ? "FREE — the priority-1 obs rate" : "shape (partly fitted)"
            @printf("%-12s %-12s %9.4f %9.4f %8.3f  [%7.4f,%7.4f] %s %s\n",
                    "rate mm/yr", "$(w[1])-$(w[2])", rm, ro, rm / ro,
                    min(rlo, rhi), max(rlo, rhi), b ? "IN " : "OUT", st)
            push!(sc, ("rate_mm_yr", "$(w[1])-$(w[2])", rm, ro, rm / ro,
                       min(rlo, rhi), max(rlo, rhi), b, st))
        end
        ## ⚠ The band below is the curvature of the LEVEL envelopes (ais_lo / ais_hi), which
    ## is NOT an uncertainty band on the acceleration -- same family as
    ## `endpoint_division_is_not_a_ratio_band`. It is an OUTER bound: always too wide, so
    ## an "IN" verdict cannot reject anything. THE POINT-ESTIMATE RATIO IS THE FINDING;
    ## the band is reported only so the reader can see how loose it is. A proper band
    ## needs the IMBIE error structure, which is strongly autocorrelated in a CUMULATIVE
    ## series -- an independent-error GLS would be far too tight and is not offered here.
    ao = accel_mm_yr2(ov, oy, ACCEL_WIN); am = accel_mm_yr2(mr, yrs, ACCEL_WIN)
        alo = accel_mm_yr2(olo, oy, ACCEL_WIN); ahi = accel_mm_yr2(ohi, oy, ACCEL_WIN)
        b = min(alo, ahi) <= am <= max(alo, ahi)
        @printf("%-12s %-12s %9.5f %9.5f %8.3f  [%7.5f,%7.5f] %s %s\n",
                "accel mm/yr2", "$(ACCEL_WIN[1])-$(ACCEL_WIN[2])", am, ao, am / ao,
                min(alo, ahi), max(alo, ahi), b ? "IN " : "OUT",
                "FREE — vs GIS 0.65x, same 1993-2024 window; band is an OUTER bound")
        push!(sc, ("accel_mm_yr2", "$(ACCEL_WIN[1])-$(ACCEL_WIN[2])", am, ao, am / ao,
                   min(alo, ahi), max(alo, ahi), b, "FREE — curvature; band is an OUTER bound, cannot reject"))
        CSV.write(joinpath(REPO, "outputs", "scope_ais_three_tests_scorecard_$(TAG)$(SFX).csv"), sc)
        ais_hist = Vector{Vector{Float64}}()  # release
        GC.gc()
    end

    ## ---- TEST 3: the lambda ladder --------------------------------------
    for lv in LAM_LADDER
        proj = Dict(y => Float64[] for y in HORIZONS)
        for d in DRAWS
            dd = copy(d); dd[!, LAM] = fill(lv, nrow(dd))
            for r in eachrow(dd)
                ladrillo_run_draw!(bf, r)
                s = ladrillo_series(bf, COMPONENT)
                for y in HORIZONS; push!(proj[y], s[ladrillo_yi(bf, y)]); end
            end
        end
        for y in HORIZONS
            v = proj[y]
            push!(ladder, (ssp, y, lv, median(v), quantile(v, 0.05), quantile(v, 0.95)))
        end
    end
    @printf("  %s ladder done (%d lambda x %d horizons)\n", ssp, LADDER_N, length(HORIZONS))
    flush(stdout)
end
CSV.write(joinpath(REPO, "outputs", "scope_ais_three_tests_ladder_$(TAG)$(SFX).csv"), ladder)
CSV.write(joinpath(REPO, "outputs", "scope_ais_three_tests_crossyear_$(TAG)$(SFX).csv"), cross)

## ---- TEST 3 headline: linearity over the FULL ladder ---------------------
@printf("\n%s\nTEST 3 — lambda LADDER, and how linear the response really is\n%s\n",
        repeat("=", 78), repeat("=", 78))
for ssp in SSPS, y in HORIZONS
    sub = ladder[(ladder.scenario .== ssp) .& (ladder.horizon .== y), :]
    x = sub.lambda; v = sub.median_cm
    X = hcat(ones(length(x)), x); c = X \ v
    resid = maximum(abs.(X * c .- v))
    @printf("%s @%d : median = %8.2f + %9.0f * lambda   max resid %6.3f cm (%.2f%% of range)\n",
            ssp, y, c[1], c[2], resid, 100 * resid / (maximum(v) - minimum(v)))
end
@printf("\nLadder written — any lambda band now maps to the deliverable with NO chain re-read.\n")
