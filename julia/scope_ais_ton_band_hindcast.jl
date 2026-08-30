## ============================================================================
## scope_ais_ton_band_hindcast.jl — IS THE L15 HINDCAST DAMAGE A FUNCTION OF
##                                  WHERE THE POSTERIOR SITS IN T_on?
##
## THE QUESTION. L16 (amp σ 0.10 → 0.180) repaired L15's AIS hindcast: mean RMSE
## ratio vs the L14 champion 4.884 → 1.272, 1950-1992 coverage 7% → 98%. But the amp
## MEDIAN only moved 1.090 → 1.060, and 0.03 in amp is ~0.012 K of T_ant over the
## calibration window — far too small to move RMSE by 2×. So the repair is NOT the
## amp median. Something else in the posterior moved.
##
## WHAT ACTUALLY MOVED. The A4 runoff-line coordinate `ais_runoff_Ton`. KDE modes of
## the accepted subsamples:
##   L15   peaks −19.27 (1.00), −16.20 (0.12), −13.93 (0.18);  deep valley at −17.51
##   L16   peak  −17.76 (1.00), minor bumps −18.93 / −18.56
## ⚠⚠ L16's MAIN MODE SITS IN L15's VALLEY. This is NOT "L16 dropped L15's second
## mode" — an earlier reading of the chain summary statistics that this script was
## written to test and which is WRONG. The two posteriors are nearly DISJOINT here:
## only 1.28% of L15's draws lie in L16's main-mode range, and only 7.45% of L16's
## lie in L15's. Both arms fail R-hat on this parameter (L15 1.908, L16 1.184).
##
## THE DESIGN — 2 arms × 3 COMMON absolute bands, so the comparison is like-for-like
## rather than each arm being split at its own modes:
##   LOW   T_on ≤ −18.5   L15's main mode
##   MID   −18.5 < T_on ≤ −17.4   L16's main mode, L15's valley
##   HIGH  T_on > −17.4   L15's upper modes
## Band edges are the KDE valley floors, not round numbers: −18.5 and −17.4 bracket
## L15's minimum-density point (−17.51) and L16's peak (−17.76).
##
## WHAT EACH OUTCOME MEANS:
##   * quality tracks the BAND (same band → same score in BOTH arms) ⇒ T_on location
##     is the proximate cause, and the σ widening acted by RELOCATING the posterior.
##   * quality tracks the ARM (L16 better in every band) ⇒ T_on is a passenger and
##     the repair is something else; the σ story needs a different mechanism.
##
## ⚠ THIS IS CONDITIONAL AND CORRELATIONAL. Draws in different T_on bands differ in
## OTHER parameters too — they are posterior draws, not a controlled perturbation. A
## band that scores well may do so because of what it is correlated with. This
## localises the damage; it does not prove T_on causes it.
##
## Scoring is bench_ladrillo.py's block [H], copied by value the same way
## scope_ais_anchor_offline.jl copies it, and the POOLED row is printed so it can be
## checked against the committed benchmark rather than trusted.
##
##   julia --project=julia_v2 julia/scope_ais_ton_band_hindcast.jl [n_draws] [--tags=L15,L16]
## Writes outputs/scope_ais_ton_band_hindcast_<TAGS>.csv, e.g. ..._L14-L21.csv.
## ⚠ TAG-SUFFIXED SINCE 2026-08-29, and that is load-bearing. It used to write ONE
## untagged path while every other output in these drivers was tag-suffixed, so the
## L22 postprocess silently OVERWROTE the L21/L14 measurement a decision rested on.
## Same bug class the repo already fixed for --gis-check. Do not revert to a fixed name.
## ============================================================================
using CSV, DataFrames, Mimi, Printf, Statistics

include(joinpath(@__DIR__, "ladrillo_projection.jl"))

const REPO = LADRILLO_REPO
_argval(p) = (i = findfirst(a -> startswith(a, p), ARGS); i === nothing ? nothing : ARGS[i][length(p)+1:end])
const NTHIN = let p = filter(a -> !startswith(a, "--"), ARGS); isempty(p) ? 10000 : parse(Int, p[1]) end
const TAGS  = split(something(_argval("--tags="), "L15,L16"), ",")
const OUT   = joinpath(REPO, "outputs",
                       "scope_ais_ton_band_hindcast_$(join(TAGS, "-")).csv")

## Band edges: the KDE valley floors between the arms' modes (see header). Named so
## the table's labels cannot drift from the cut that produced them.
const TON_EDGE_LOW  = -18.5
const TON_EDGE_HIGH = -17.4
const BANDS = [("LOW",  (-Inf, TON_EDGE_LOW)),
               ("MID",  (TON_EDGE_LOW, TON_EDGE_HIGH)),
               ("HIGH", (TON_EDGE_HIGH, Inf)),
               ("POOLED", (-Inf, Inf))]

const HIND_Y0, HIND_Y1 = 1850, 2026
const FIT_START, FIT_REF, FORCING = 1900, (1995, 2005), "ssp245harm"
const WINDOWS = [("full", nothing), ("1950-1992", (1950, 1992))]

const TG = CSV.read(joinpath(REPO, "outputs/recalib_targets_ext.csv"), DataFrame)
const FY = collect(FIT_START:HIND_Y1)
function _obs(y)
    r = findfirst(==(y), TG.year); r === nothing && return NaN
    v = TG[r, :ais]; (ismissing(v) || isnan(Float64(v))) ? NaN : Float64(v)
end
const OBS = [_obs(y) for y in FY]
const SIGMA_AIS = let w = [(ismissing(TG[i,:ais_hi]) || ismissing(TG[i,:ais_lo])) ? NaN :
                           (Float64(TG[i,:ais_hi]) - Float64(TG[i,:ais_lo]))/(2*1.645) for i in 1:nrow(TG)]
    mean(filter(isfinite, w))
end

qv(x, p) = (v = filter(isfinite, x); isempty(v) ? NaN : quantile(v, p))
function score_window(p50, p05, p95, win)
    m = [isfinite(OBS[j]) && isfinite(p50[j]) &&
         (win === nothing || (FY[j] >= win[1] && FY[j] <= win[2])) for j in eachindex(FY)]
    any(m) || return nothing
    r = p50[m] .- OBS[m]
    return (n=count(m), bias=mean(r), rmse=sqrt(mean(r.^2)),
            cov90=mean((OBS[m] .>= p05[m]) .& (OBS[m] .<= p95[m])),
            band=mean(p95[m] .- p05[m]))
end

rows = DataFrame(tag=String[], band=String[], n_draws=Int[], ton_med=Float64[],
                 amp_med=Float64[], window=String[], bias_sigma=Float64[],
                 rmse_cm=Float64[], band_cm=Float64[], cov90=Float64[])

@printf("T_on BAND × ARM HINDCAST | %d draws requested | AIS target sigma %.4f cm\n",
        NTHIN, SIGMA_AIS)
@printf("  bands: LOW ≤ %.1f  |  MID (%.1f, %.1f]  |  HIGH > %.1f   (KDE valley floors)\n",
        TON_EDGE_LOW, TON_EDGE_LOW, TON_EDGE_HIGH, TON_EDGE_HIGH)
println("  ⚠ CONDITIONAL AND CORRELATIONAL — bands differ in other parameters too.\n")

for tag in TAGS
    path = joinpath(REPO, "data/MimiBRICK", "parameters_subsample_brick_mengel_$(tag).csv")
    isfile(path) || error("no posterior for tag=$tag at $path")
    variant = ladrillo_posterior_variant(path)
    post = ladrillo_posterior(path=path, nthin=NTHIN)
    bf = ladrillo_setup(ssp="ssp245", y0=HIND_Y0, y1=HIND_Y1, forcing_tag=FORCING,
                        ref=FIT_REF, gis_variant=variant)
    imy = [ladrillo_yi(bf, y) for y in FY]
    ## Run EVERY draw once, then band the rows. Re-running per band would triple the
    ## cost and let the two paths drift.
    ais = Array{Float64}(undef, nrow(post), length(FY))
    t0 = time()
    for (i, r) in enumerate(eachrow(post))
        ladrillo_run_draw!(bf, r)
        ais[i, :] = ladrillo_series(bf, :ais)[imy]
    end
    ton = [Float64(r["ais_runoff_Ton"]) for r in eachrow(post)]
    amp = [Float64(r["ais_gmst_amp"])   for r in eachrow(post)]
    @printf("%s: %d draws in %.0fs\n", tag, nrow(post), time() - t0)
    for (bname, (lo, hi)) in BANDS
        sel = findall(t -> t > lo && t <= hi, ton)
        ## A band with too few draws cannot carry a 90% coverage number: with n < 40
        ## the p05/p95 ARE nearly the extremes and coverage is not estimable.
        length(sel) >= 40 || (@printf("  %-6s SKIPPED — only %d draws\n", bname, length(sel)); continue)
        sub = view(ais, sel, :)
        p05 = [qv(view(sub, :, j), 0.05) for j in eachindex(FY)]
        p50 = [qv(view(sub, :, j), 0.50) for j in eachindex(FY)]
        p95 = [qv(view(sub, :, j), 0.95) for j in eachindex(FY)]
        for (wname, win) in WINDOWS
            s = score_window(p50, p05, p95, win); s === nothing && continue
            push!(rows, (tag, bname, length(sel), median(ton[sel]), median(amp[sel]),
                         wname, s.bias/SIGMA_AIS, s.rmse, s.band, s.cov90))
        end
    end
end

CSV.write(OUT, rows)
println("\n", "="^108)
println("AIS HINDCAST BY T_on BAND — does the damage track the BAND or the ARM?")
println("="^108)
@printf("%-5s %-7s %7s %8s %8s | %9s %8s %8s %7s | %9s %8s %8s %7s\n",
        "arm","band","n","T_on","amp","bias/sd","rmse","bandw","cov90","bias/sd","rmse","bandw","cov90")
@printf("%-5s %-7s %7s %8s %8s | %9s %8s %8s %7s | %9s %8s %8s %7s\n",
        "","","","med","med","[full]","[full]","[full]","[full]","[50-92]","[50-92]","[50-92]","[50-92]")
for tag in TAGS, (bname, _) in BANDS
    f = rows[(rows.tag .== tag) .& (rows.band .== bname) .& (rows.window .== "full"), :]
    g = rows[(rows.tag .== tag) .& (rows.band .== bname) .& (rows.window .== "1950-1992"), :]
    nrow(f) == 1 || continue
    @printf("%-5s %-7s %7d %8.2f %8.3f | %9.3f %8.4f %8.4f %6.0f%% | %9.3f %8.4f %8.4f %6.0f%%\n",
            tag, bname, f.n_draws[1], f.ton_med[1], f.amp_med[1],
            f.bias_sigma[1], f.rmse_cm[1], f.band_cm[1], 100*f.cov90[1],
            g.bias_sigma[1], g.rmse_cm[1], g.band_cm[1], 100*g.cov90[1])
end
println("\n  REPRODUCTION CHECK — the POOLED rows must match the committed benchmark:")
println("    L15 1950-1992 bias −0.340 sd, cov90 7% | L16 bias −0.02 sd, cov90 98%")
println("\nwrote ", relpath(OUT, REPO))
