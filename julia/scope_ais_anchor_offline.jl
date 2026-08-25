## ============================================================================
## scope_ais_anchor_offline.jl — PRICE THE DAIS ANCHOR SHIFT BEFORE REFITTING IT
##
## THE QUESTION (handoff 2026-08-25d §4). L15 re-centred the GMST->T_ant
## amplification 0.945 -> 1.09 on two CMIP6 secant ensembles. The projections moved
## where the mechanism says they should and the AIS HINDCAST BROKE: RMSE 1.5-9.2x
## worse by window, 1950-1992 coverage 98% -> 7%, bias +0.02 -> -0.34 target sd.
##
## The proposed repair is to stop PINNING the paleo anchor. DAIS uses
##     T_ant(t) = amp * GMST(t) + T_ant0,     T_ant0 = -15.42/0.8365 = -18.434 degC
## and the A6 reparameterization samples `amp` while holding T_ant0 fixed -- i.e. it
## moves the SLOPE of a jointly-fitted paleo regression while nailing its INTERCEPT.
## Because calibration-era GMST (~0.41 K) is far below projection-era GMST (2.7-4.7 K),
## a small negative shift in T_ant0 can restore the historical T_ant while leaving most
## of the projection shift in place. §4b's first-order arithmetic puts that shift at
## about -0.077 K and predicts ~83% of the projection effect survives.
##
## ⚠ THAT ARITHMETIC IS FIRST-ORDER ONLY. T_ant enters precipitation as exp(kappa*T_ant)
## and the runoff line as h0 + c*T_ant, so equal T_ant does NOT guarantee equal mass
## balance. THIS SCRIPT MEASURES THE REAL THING instead of assuming it: it runs the
## actual model over the actual posterior at a grid of anchor shifts and scores the
## hindcast with the BENCHMARK'S OWN metric (bench_ladrillo.py block [H]: bias in
## target sd over the same four windows, 90% coverage of the parameter band).
##
## ⚠⚠ THIS IS NOT A REFIT, AND IT IS A LOWER BOUND ON WHAT ONE WOULD DO. The posterior
## is HELD at L15 and only the anchor moves, so every other parameter stays tuned for
## T_ant0 = -18.434. A refit would let `ais_runoff_Ton` and friends re-compensate
## (amp correlates r = 0.608 with ais_runoff_Ton in the posterior -- see
## scope_ais_amp_price.py). The same caveat that script carries applies here:
##   * if a shift RESTORES the hindcast at fixed parameters, a refit can only do better
##     -> freeing the anchor is worth the 4-hour chain, and §4c's degeneracy question
##        (T_ant0 vs antarctic_temp_threshold) has to be answered before it runs;
##   * if NO shift restores it, the leading term is not the problem, and handoff §4e's
##     alternative -- that DAIS's paleo pair and the CMIP6 secant are not the same
##     object -- is the conclusion, at zero chain cost.
##
## The L14 champion is run through the SAME code path at shift 0 as the reference row,
## so the comparison is like-for-like rather than against a number copied from a report.
##
##   julia --project=julia_v2 julia/scope_ais_anchor_offline.jl [n_draws] \
##         [--tag=L15] [--ref-tag=L14] [--shifts=0,-0.04,-0.077,-0.12,-0.16,-0.20]
##
## Writes outputs/scope_ais_anchor_offline_<TAG>.csv
## ============================================================================
using CSV, DataFrames, Mimi, Printf, Statistics

include(joinpath(@__DIR__, "ladrillo_projection.jl"))

const REPO = LADRILLO_REPO
_argval(p) = (i = findfirst(a -> startswith(a, p), ARGS); i === nothing ? nothing : ARGS[i][length(p)+1:end])

const NTHIN = let p = filter(a -> !startswith(a, "--"), ARGS)
    isempty(p) ? 2000 : parse(Int, p[1])
end
const TAG     = something(_argval("--tag="), "L15")
const REF_TAG = something(_argval("--ref-tag="), "L14")
## The §4b prediction is IN the default grid, bracketed on both sides, so the run
## reports the trade-off CURVE rather than one point that could only confirm.
const SHIFTS = let s = _argval("--shifts=")
    s === nothing ? [0.0, -0.04, -0.077, -0.12, -0.16, -0.20] :
                    [parse(Float64, x) for x in split(s, ",")]
end
const OUT = joinpath(REPO, "outputs", "scope_ais_anchor_offline_$(TAG).csv")

## Hindcast conventions are posterior_predictive_ladrillo.jl's, which are the
## calibrator's; the scoring windows and the sigma normalisation are
## bench_ladrillo.py's. Both are copied by VALUE here and asserted where possible,
## because a metric that silently differs from the benchmark's is worse than none.
const HIND_Y0, HIND_Y1 = 1850, 2026
const FIT_START  = 1900
const FIT_REF    = (1995, 2005)
const FORCING    = "ssp245harm"
const WINDOWS    = [("full", nothing), ("1920-1949", (1920, 1949)),
                    ("1950-1992", (1950, 1992)), ("1993-2026", (1993, 2026))]
const PROJ_Y0, PROJ_Y1 = 1850, 2300
const SSPS     = ["ssp126", "ssp245", "ssp585"]
const HORIZONS = [2100, 2150, 2300]

## ---------------------------------------------------------------------------
## targets: the AIS series and the benchmark's sigma normalisation
## ---------------------------------------------------------------------------
const TG = CSV.read(joinpath(REPO, "outputs/recalib_targets_ext.csv"), DataFrame)
const FY = collect(FIT_START:HIND_Y1)
_tgi(y) = findfirst(==(y), TG.year)
function _obs_ais(y)
    r = _tgi(y); r === nothing && return NaN
    v = TG[r, :ais]
    (ismissing(v) || isnan(Float64(v))) ? NaN : Float64(v)
end
const OBS = [_obs_ais(y) for y in FY]
## bench_ladrillo.py:1122 -- sigma[key] = mean over the target of (hi-lo)/(2*1.645).
const SIGMA_AIS = let w = [(ismissing(TG[i, :ais_hi]) || ismissing(TG[i, :ais_lo])) ? NaN :
                           (Float64(TG[i, :ais_hi]) - Float64(TG[i, :ais_lo])) / (2 * 1.645)
                           for i in 1:nrow(TG)]
    mean(filter(isfinite, w))
end
## The benchmark refuses to score arms that do not share a baseline; assert the same.
let base = mean(filter(isfinite, [_obs_ais(y) for y in FIT_REF[1]:FIT_REF[2]]))
    abs(base) < 1e-3 || error("recalib_targets_ext.csv AIS is not zeroed on " *
        "$(FIT_REF): mean = $base cm. The handoff warns this file MOVED -- re-run " *
        "python/prep_recalib_targets_ext.py rather than scoring against a stale one.")
end

## ---------------------------------------------------------------------------
## one (posterior, shift) cell
## ---------------------------------------------------------------------------
"""Apply the draw, then OVERRIDE the anchor. `ladrillo_apply_draw!` sets the
intercept from the pinned `LADRILLO_AIS_TANT0`; this re-sets it from the shifted
anchor, preserving `amp` exactly. The shift is applied in T_ant DEGREES, so the
divide by amp is the same reparameterization the calibrator uses."""
function run_draw_shifted!(bf, r, shift)
    ladrillo_apply_draw!(bf, r)
    amp = Float64(r["ais_gmst_amp"])
    update_param!(bf.m, :antarctic_icesheet, :ais_temperature_intercept,
                  -(LADRILLO_AIS_TANT0 + shift) / amp)
    run(bf.m)
    return bf
end

qv(x, p) = (v = filter(isfinite, x); isempty(v) ? NaN : quantile(v, p))

"""bench_ladrillo.py:score_window, on the parameter band (p05/p50/p95)."""
function score_window(p50, p05, p95, obs, win)
    m = [isfinite(obs[j]) && isfinite(p50[j]) &&
         (win === nothing || (FY[j] >= win[1] && FY[j] <= win[2])) for j in eachindex(FY)]
    any(m) || return nothing
    res = p50[m] .- obs[m]
    return (n = count(m), bias = mean(res), rmse = sqrt(mean(res .^ 2)),
            cov90 = mean((obs[m] .>= p05[m]) .& (obs[m] .<= p95[m])),
            band  = mean(p95[m] .- p05[m]))
end

rows = DataFrame(tag=String[], shift=Float64[], block=String[], scenario=String[],
                 window=String[], horizon=Int[], metric=String[], value=Float64[])
push_row!(t, s, b, sc, w, h, m, v) = push!(rows, (t, s, b, sc, w, h, m, Float64(v)))

function cell!(tag, posterior, shift)
    variant = ladrillo_posterior_variant(posterior)
    post = ladrillo_posterior(path=posterior, nthin=NTHIN)

    ## ---- hindcast --------------------------------------------------------
    bf = ladrillo_setup(ssp="ssp245", y0=HIND_Y0, y1=HIND_Y1, forcing_tag=FORCING,
                        ref=FIT_REF, gis_variant=variant)
    imy = [ladrillo_yi(bf, y) for y in FY]
    ais = Array{Float64}(undef, nrow(post), length(FY))
    t0 = time()
    for (i, r) in enumerate(eachrow(post))
        run_draw_shifted!(bf, r, shift)
        ais[i, :] = ladrillo_series(bf, :ais)[imy]
    end
    p05 = [qv(view(ais, :, j), 0.05) for j in eachindex(FY)]
    p50 = [qv(view(ais, :, j), 0.50) for j in eachindex(FY)]
    p95 = [qv(view(ais, :, j), 0.95) for j in eachindex(FY)]
    for (wname, win) in WINDOWS
        s = score_window(p50, p05, p95, OBS, win)
        s === nothing && continue
        push_row!(tag, shift, "H", "", wname, 0, "bias_cm",    s.bias)
        push_row!(tag, shift, "H", "", wname, 0, "bias_sigma", s.bias / SIGMA_AIS)
        push_row!(tag, shift, "H", "", wname, 0, "rmse_cm",    s.rmse)
        push_row!(tag, shift, "H", "", wname, 0, "cov90",      s.cov90)
        ## ⚠ THE BAND WIDTH IS REPORTED BESIDE THE COVERAGE, ALWAYS. Coverage is a
        ## ratio and a widening band forgives it (`rhat_denominator_forgives`): a shift
        ## that moves the median AWAY from the observations can still raise coverage by
        ## inflating the parameter spread. Without this column that reads as a repair.
        push_row!(tag, shift, "H", "", wname, 0, "band_cm",    s.band)
    end
    @printf("  hindcast %.0fs", time() - t0); flush(stdout)

    ## ---- projections -----------------------------------------------------
    ## AIS only, and UNTAPPED: the Greenland volume tap is a Greenland-component
    ## object and does not enter :ais, so an untapped run is the cheaper arm of an
    ## identical AIS. The tipped fraction is closed form on the same mean driver
    ## the medians use -- T_ant = amp*GMST + anchor, tested INSTANTANEOUSLY at the
    ## horizon, because DAIS re-tests every year and does not latch
    ## (diag_ais_tipping_under_forcing.jl).
    for ssp in SSPS
        bfp = ladrillo_setup(ssp=ssp, y0=PROJ_Y0, y1=PROJ_Y1, gis_variant=variant)
        ih = [ladrillo_yi(bfp, y) for y in HORIZONS]
        acc = Array{Float64}(undef, nrow(post), length(HORIZONS))
        t1 = time()
        for (i, r) in enumerate(eachrow(post))
            run_draw_shifted!(bfp, r, shift)
            acc[i, :] = ladrillo_series(bfp, :ais)[ih]
        end
        for (k, y) in enumerate(HORIZONS)
            push_row!(tag, shift, "P", ssp, "", y, "ais_med", qv(view(acc, :, k), 0.50))
            push_row!(tag, shift, "P", ssp, "", y, "ais_p05", qv(view(acc, :, k), 0.05))
            push_row!(tag, shift, "P", ssp, "", y, "ais_p95", qv(view(acc, :, k), 0.95))
            tf = mean([Float64(r["ais_gmst_amp"]) * bfp.gmst[ih[k]] + LADRILLO_AIS_TANT0 + shift >
                       Float64(r["antarctic_temp_threshold"]) for r in eachrow(post)])
            push_row!(tag, shift, "P", ssp, "", y, "tipped_frac", tf)
        end
        @printf(" | %s %.0fs", ssp, time() - t1); flush(stdout)
    end
    println()
end

@printf("AIS ANCHOR OFFLINE SCOPE | candidate %s | reference %s | %d draws | anchor %.4f degC\n",
        TAG, REF_TAG, NTHIN, LADRILLO_AIS_TANT0)
@printf("  AIS target sigma = %.4f cm (bench normalisation) | shifts: %s\n",
        SIGMA_AIS, join(SHIFTS, ", "))
println("  ⚠ FIXED POSTERIOR — only the anchor moves. This is a LOWER BOUND on a refit.\n")

const POST_PATH = Dict(t => joinpath(REPO, "data/MimiBRICK",
                                     "parameters_subsample_brick_mengel_$(t).csv")
                       for t in (TAG, REF_TAG))
for (t, p) in POST_PATH
    isfile(p) || error("no posterior for tag=$t at $p")
end

println("$REF_TAG (champion reference, shift 0):")
cell!(REF_TAG, POST_PATH[REF_TAG], 0.0)
for s in SHIFTS
    @printf("%s shift %+.3f K:\n", TAG, s)
    cell!(TAG, POST_PATH[TAG], s)
end

CSV.write(OUT, rows)

## ---------------------------------------------------------------------------
## the trade-off table: what the shift buys on the projection, what it costs on
## the hindcast. Both columns are the ones the benchmark actually scored.
## ---------------------------------------------------------------------------
val(t, s, b, sc, w, h, m) = let r = rows[(rows.tag .== t) .& (rows.shift .≈ s) .&
                                         (rows.block .== b) .& (rows.scenario .== sc) .&
                                         (rows.window .== w) .& (rows.horizon .== h) .&
                                         (rows.metric .== m), :]
    nrow(r) == 1 ? r.value[1] : NaN
end
println("\n", "="^104)
println("HINDCAST (AIS, bias in target sigma; PASS <=1.0, WARN <=3.0 — bench_ladrillo.py) ",
        "and 1950-1992 coverage")
println("="^104)
@printf("%-18s %9s %9s %9s %9s %9s %9s %9s %9s\n", "arm", "bias/sd", "rmse", "band",
        "cov90", "bias/sd", "rmse", "band", "cov90")
@printf("%-18s %9s %9s %9s %9s %9s %9s %9s %9s\n", "", "[full]", "[full]", "[full]",
        "[full]", "[50-92]", "[50-92]", "[50-92]", "[50-92]")
function hrow(label, t, s)
    @printf("%-18s %9.3f %9.3f %9.3f %8.0f%% %9.3f %9.3f %9.3f %8.0f%%\n", label,
            val(t, s, "H", "", "full", 0, "bias_sigma"), val(t, s, "H", "", "full", 0, "rmse_cm"),
            val(t, s, "H", "", "full", 0, "band_cm"),
            100 * val(t, s, "H", "", "full", 0, "cov90"),
            val(t, s, "H", "", "1950-1992", 0, "bias_sigma"),
            val(t, s, "H", "", "1950-1992", 0, "rmse_cm"),
            val(t, s, "H", "", "1950-1992", 0, "band_cm"),
            100 * val(t, s, "H", "", "1950-1992", 0, "cov90"))
end
hrow("$REF_TAG (champion)", REF_TAG, 0.0)
for s in SHIFTS; hrow(@sprintf("%s %+.3f", TAG, s), TAG, s); end

println("\n", "="^104)
println("PROJECTION (AIS median, cm) and the fraction of the L15 pinned-anchor gain retained")
println("="^104)
@printf("%-18s %26s %26s %26s\n", "arm", "ssp126 2100/2150/2300",
        "ssp245 2100/2150/2300", "ssp585 2100/2150/2300")
function prow(label, t, s)
    f(ssp) = join([@sprintf("%.1f", val(t, s, "P", ssp, "", y, "ais_med")) for y in HORIZONS], "/")
    @printf("%-18s %26s %26s %26s\n", label, f("ssp126"), f("ssp245"), f("ssp585"))
end
prow("$REF_TAG (champion)", REF_TAG, 0.0)
for s in SHIFTS; prow(@sprintf("%s %+.3f", TAG, s), TAG, s); end

## RETENTION: (shifted - L14) / (L15 pinned - L14), per cell. 1.0 = the whole L15
## move survives the shift; 0.0 = the shift undoes it. Reported ONLY where the L15
## move is large enough to divide by -- a ratio on a near-zero denominator is noise
## (`endpoint_division_is_not_a_ratio_band` is the band case of the same trap).
const RETAIN_FLOOR = 1.0        # cm; below this the L15-vs-L14 move is not a signal
println("\nRETAINED FRACTION OF THE L15 PINNED-ANCHOR PROJECTION MOVE")
println("  (shifted - $REF_TAG) / ($TAG@0 - $REF_TAG); blank where |$TAG@0 - $REF_TAG| < $(RETAIN_FLOOR) cm")
@printf("%-18s", "arm")
for ssp in SSPS, y in HORIZONS; @printf(" %10s", "$(ssp[4:end])@$(y)"); end
println()
for s in SHIFTS
    @printf("%-18s", @sprintf("%s %+.3f", TAG, s))
    for ssp in SSPS, y in HORIZONS
        base = val(REF_TAG, 0.0, "P", ssp, "", y, "ais_med")
        pin  = val(TAG, 0.0, "P", ssp, "", y, "ais_med")
        cur  = val(TAG, s,   "P", ssp, "", y, "ais_med")
        @printf(" %10s", abs(pin - base) < RETAIN_FLOOR ? "-" :
                         @sprintf("%.2f", (cur - base) / (pin - base)))
    end
    println()
end
println("\nwrote ", relpath(OUT, REPO))
