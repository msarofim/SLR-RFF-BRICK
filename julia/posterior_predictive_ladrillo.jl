## ============================================================================
## posterior_predictive_ladrillo.jl — Ladrillo hindcast vs observations
##
## Forward-runs the accepted Ladrillo 1.0 (L10) posterior over the calibration
## window and compares component bands to the observational targets they were
## fit to. This is the observation-comparison deliverable for the sharing memo.
##
## Conventions are the CALIBRATOR's, so the bias numbers mean what the fit
## meant (calibrate_mcmc_ext.jl):
##   window     1850-2026, forcing fair_mean_{gmst,ohc}_ssp245harm.csv
##   baseline   1995-2005 (the calibration re-reference; NOT the 1995-2014
##              projection baseline)
##   glaciers   model scope is gsic_hind = SLOWP + FAST plus the per-draw
##              F_unch uncharted-ice term; the target is the r19-seam-adjusted
##              gsic series (outputs/recalib_targets_ext_gsicadj.csv) with the
##              per-draw delta ramp applied on the OBS side over 1900-1959
##   total      modelled ice + steric at the total-target years plus the
##              observed land-water-storage budget, vs the Frederikse/NOAA-STAR
##              spliced total
##
## The bands are POSTERIOR-PARAMETER bands: the AR(1) observation-noise
## parameters the calibration also sampled are not added back, so coverage
## below 90% at 90% nominal is expected where the obs noise is material.
##
## Targets (all fit series start 1900):
##   ais / gis / steric  Frederikse 2020 + GRACE-FO / NOAA extensions
##   gsic                Frederikse 2020 (Marzeion-2015 early segment) spliced
##                       to GlaMBIE 2019+, r19 removed
##   total               Frederikse 2020 spliced to NOAA STAR altimetry
##
##   julia --project=julia_v2 julia/posterior_predictive_ladrillo.jl [n_draws] [--tag=L11]
##
## --tag selects the posterior AND every output filename together (default L10),
## so a run on one posterior cannot write files labelled with another.
## ============================================================================

using CSV, DataFrames, Mimi, Printf, Random, Statistics
include(joinpath(@__DIR__, "ladrillo_projection.jl"))

const Y0, Y1     = 1850, 2026
const FIT_REF    = (1995, 2005)            # calibration re-reference window
const FORCING    = "ssp245harm"
const FIT_START  = 1900                    # all target series start here
const NTHIN      = let p = filter(a -> !startswith(a, "--"), ARGS)
    isempty(p) ? 2000 : parse(Int, p[1])
end
## POSTERIOR TAG drives BOTH the input posterior and every output filename, so a
## run on one vintage cannot write files labelled with another. The default
## tracks the CANONICAL posterior (L11 since 2026-08-17; L10 before that), so it
## is derived from LADRILLO_POSTERIOR_CSV rather than written out again — the
## two cannot drift. Passing --tag=X asserts the file exists rather than
## silently falling back, and older vintages stay reachable that way.
const DEFAULT_TAG = let b = basename(LADRILLO_POSTERIOR_CSV)
    replace(replace(b, "parameters_subsample_brick_mengel_" => ""), ".csv" => "")
end
const POST_TAG = let i = findfirst(a -> startswith(a, "--tag="), ARGS)
    i === nothing ? DEFAULT_TAG : ARGS[i][7:end]
end
const POSTERIOR = joinpath(LADRILLO_REPO,
    "data/MimiBRICK/parameters_subsample_brick_mengel_$(POST_TAG).csv")
isfile(POSTERIOR) || error("no posterior for --tag=$POST_TAG at $POSTERIOR")
POST_TAG != DEFAULT_TAG || POSTERIOR == LADRILLO_POSTERIOR_CSV ||
    error("the default tag '$DEFAULT_TAG' resolved to $POSTERIOR, which is not " *
          "LADRILLO_POSTERIOR_CSV ($LADRILLO_POSTERIOR_CSV)")
const OUT_BANDS  = joinpath(LADRILLO_REPO, "outputs/postpred_$(POST_TAG)_components_timeseries.csv")
const OUT_BIAS   = joinpath(LADRILLO_REPO, "outputs/postpred_$(POST_TAG)_bias.csv")
const OUT_COVER  = joinpath(LADRILLO_REPO, "outputs/postpred_$(POST_TAG)_coverage.csv")
const DELTA_END  = 1960                    # delta ramp is zero from this year on

## (kernel component, target column in recalib_targets_ext.csv, AR(1) noise-parameter
## suffix in the posterior). The glacier target is served from the r19-seam-adjusted
## file, keyed :gsic.
const SERIES = [(:ais,      :ais,    "ais"),
                (:glaciers, :gsic,   "gsic"),
                (:gis,      :gis,    "gis"),
                (:te,       :steric, "steric"),
                (:total,    :dang,   "dang")]
const NOISE_SEED = 2026


## ---------------------------------------------------------------------------
## targets
## ---------------------------------------------------------------------------
tg   = CSV.read(joinpath(LADRILLO_REPO, "outputs/recalib_targets_ext.csv"), DataFrame)
gadj = CSV.read(joinpath(LADRILLO_REPO, "outputs/recalib_targets_ext_gsicadj.csv"), DataFrame)
tgi(y) = findfirst(==(y), tg.year)
haveobs(col, y) = (r = tgi(y); r !== nothing && !ismissing(tg[r, col]) && !isnan(Float64(tg[r, col])))

FY  = collect(FIT_START:Y1)                       # comparison year grid
gsic_target = let d = Dict(Int(gadj[i, :year]) => Float64(gadj[i, :gsic_adj]) for i in 1:nrow(gadj))
    Dict(y => get(d, y, NaN) for y in FY)
end
obs_of(key, y) = key === :gsic ? gsic_target[y] : (haveobs(key, y) ? Float64(tg[tgi(y), key]) : NaN)
lws_obs = [haveobs(:lws, y) ? Float64(tg[tgi(y), :lws]) : NaN for y in FY]
delta_ramp = [y < DELTA_END ? (DELTA_END - y) / 10.0 : 0.0 for y in FY]

## Per-year observational sigma, exactly as the likelihood builds it: half the
## reported band over 1.645, floored at 0.05 cm; the total additionally carries
## the land-water-storage budget error.
band_sigma(lo, hi) = max((Float64(hi) - Float64(lo)) / (2 * 1.645), 0.05)
function obs_sigma(tcol, y)
    r = tgi(y)
    (r === nothing || isnan(obs_of(tcol, y))) && return NaN
    tcol === :dang && return sqrt(Float64(tg[r, :dang_sig])^2 +
                                 band_sigma(tg[r, :lws_lo], tg[r, :lws_hi])^2)
    return band_sigma(tg[r, Symbol("$(tcol)_lo")], tg[r, Symbol("$(tcol)_hi")])
end
const OBS_SIGMA = Dict(tcol => [obs_sigma(tcol, y) for y in FY] for (_, tcol, _) in SERIES)

## ---------------------------------------------------------------------------
## run the posterior
## ---------------------------------------------------------------------------
post = ladrillo_posterior(path=POSTERIOR, cols=:all, nthin=NTHIN)  # :all — the ledger columns are needed here
const VARIANT = ladrillo_posterior_variant(POSTERIOR)
## WHICH SERIES THE POSTERIOR WAS ACTUALLY FIT TO, read off the posterior itself
## rather than assumed. L11's D1 change DROPPED the total stream, so an L11
## posterior has no sd_dang/rho_dang and there is no calibrated error model for
## the total.
##
## That does NOT make the total uninteresting — it makes it OUT-OF-SAMPLE, which
## is the direct evidence on whether D1 cost anything. So the total is still run
## and still compared to obs, but:
##   * its `pred` (predictive) band is NaN, because inventing a noise model for
##     an unfitted stream would fabricate the very thing being tested; and
##   * its coverage is reported for the PARAMETER band only, and is NOT
##     comparable to a fitted series' coverage_pred, nor to L10's total, which
##     WAS in-sample.
## `in_sample` in the bias/coverage outputs carries this distinction downstream
## so a reader cannot mistake an out-of-sample total for a fitted one.
const FITTED = Set(k for (k, _, sfx) in SERIES
                   if ("sd_$sfx" in names(post)) && ("rho_$sfx" in names(post)))
const UNFITTED = [k for (k, _, _) in SERIES if !(k in FITTED)]
isempty(UNFITTED) ||
    println("NOTE: no calibrated error model for $(join(UNFITTED, ", ")) — reported " *
            "OUT-OF-SAMPLE, parameter band only, predictive band NaN")
bf   = ladrillo_setup(ssp="ssp245", y0=Y0, y1=Y1, forcing_tag=FORCING, ref=FIT_REF,
                      gis_variant = VARIANT)
imy  = [ladrillo_yi(bf, y) for y in FY]
ny   = length(FY)

@printf("Ladrillo posterior predictive | %s | %d draws | %d-%d | base %d-%d | forcing %s\n",
        basename(POSTERIOR), nrow(post), FIT_START, Y1,
        FIT_REF[1], FIT_REF[2], FORCING)

model = Dict(k => Array{Float64}(undef, nrow(post), ny) for (k, _, _) in SERIES)
# Predictive = model + a draw from the CALIBRATED error model, i.e. the residual
# distribution the likelihood assumes: stationary AR(1) with marginal variance
# sd^2/(1-rho^2) plus independent per-year observational error (hetero_logl_ar1
# in calibrate_mcmc_ext.jl). Coverage of THIS band is the honest goodness-of-fit
# statement; the model-only band above is parameter spread alone.
pred = Dict(k => Array{Float64}(undef, nrow(post), ny) for (k, _, _) in SERIES)
obs_corrected = Array{Float64}(undef, nrow(post), ny)      # gsic obs + per-draw delta ramp
rng = MersenneTwister(NOISE_SEED)
function ar1_plus_obs_error!(rng, out, sd, rho, sigma_y)
    out[1] = sd / sqrt(1 - rho^2) * randn(rng)
    @inbounds for t in 2:length(out)
        out[t] = rho * out[t-1] + sd * randn(rng)
    end
    @inbounds for t in eachindex(out)
        out[t] += isnan(sigma_y[t]) ? 0.0 : sigma_y[t] * randn(rng)
    end
    return out
end
noise = Vector{Float64}(undef, ny)
t0 = time()
for (i, r) in enumerate(eachrow(post))
    ladrillo_run_draw!(bf, r)
    u = Float64(r["gic_u_unch"])
    ais  = ladrillo_series(bf, :ais)[imy]
    gsic = ladrillo_series(bf, :gsic_hind; funch=u)[imy]     # hindcast scope: SLOWP+FAST+F_unch
    gis  = ladrillo_series(bf, :gis)[imy]
    te   = ladrillo_series(bf, :te)[imy]
    # total scope adds the R19 seam (real melt) and the observed LWS budget
    tot  = ladrillo_series(bf, :glaciers; funch=u)[imy] .+ ais .+ gis .+ te .+ lws_obs
    model[:ais][i, :] = ais; model[:glaciers][i, :] = gsic
    model[:gis][i, :] = gis; model[:te][i, :] = te; model[:total][i, :] = tot
    obs_corrected[i, :] = [obs_of(:gsic, y) for y in FY] .+ Float64(r["gic_delta"]) .* delta_ramp
    for (key, tcol, sfx) in SERIES
        if key in FITTED
            ar1_plus_obs_error!(rng, noise, Float64(r["sd_$sfx"]), Float64(r["rho_$sfx"]), OBS_SIGMA[tcol])
            pred[key][i, :] = model[key][i, :] .+ noise
        else
            pred[key][i, :] .= NaN     # no calibrated error model — see FITTED
        end
    end
    i % 250 == 0 && (print("."); flush(stdout))
end
@printf("\n  %d draws in %.0fs\n", nrow(post), time() - t0)

## ---------------------------------------------------------------------------
## bands + obs overlay
## ---------------------------------------------------------------------------
qv(x, p) = (v = filter(isfinite, x); isempty(v) ? NaN : quantile(v, p))
bands = DataFrame(year=FY)
for (key, tcol, _) in SERIES
    bands[!, "$(key)_p05"] = [qv(model[key][:, j], 0.05) for j in 1:ny]
    bands[!, "$(key)_p50"] = [qv(model[key][:, j], 0.50) for j in 1:ny]
    bands[!, "$(key)_p95"] = [qv(model[key][:, j], 0.95) for j in 1:ny]
    bands[!, "$(key)_pred_p05"] = [qv(pred[key][:, j], 0.05) for j in 1:ny]
    bands[!, "$(key)_pred_p95"] = [qv(pred[key][:, j], 0.95) for j in 1:ny]
    o = [obs_of(tcol, y) for y in FY]
    bands[!, "$(key)_obs"] = [isnan(v) ? missing : v for v in o]
end
# the glacier target the model is actually compared against is delta-corrected per draw;
# report its posterior median so the overlay is self-consistent
bands[!, "glaciers_obs_delta_corrected"] =
    [(v = qv(obs_corrected[:, j], 0.50); isnan(v) ? missing : v) for j in 1:ny]
CSV.write(OUT_BANDS, bands)

## ---------------------------------------------------------------------------
## bias + coverage
## ---------------------------------------------------------------------------
## in_sample: FALSE marks a series this posterior was NOT fit to (L11's total,
## post-D1). Its bias is an out-of-sample check, not a fit residual.
bias = DataFrame(component=String[], year=Int[], obs=Float64[], p50=Float64[],
                 bias=Float64[], in90=Bool[], in_sample=Bool[])
function report(key, tcol, y)
    j = findfirst(==(y), FY); j === nothing && return
    o = key === :glaciers ? qv(obs_corrected[:, j], 0.50) : obs_of(tcol, y)
    isnan(o) && return
    p05, p50, p95 = qv(model[key][:, j], 0.05), qv(model[key][:, j], 0.50), qv(model[key][:, j], 0.95)
    inb = p05 <= o <= p95
    @printf("  %-9s %d  obs %7.2f  p50 %7.2f  bias %+6.2f  %s%s\n",
            key, y, o, p50, p50 - o, inb ? "in 90%" : "OUT",
            key in FITTED ? "" : "  [OUT-OF-SAMPLE]")
    push!(bias, (string(key), y, o, p50, p50 - o, inb, key in FITTED))
end

println("\nComponent bias (model p50 - obs, cm; glaciers vs the delta-corrected target)")
for y in (1900, 1950, 2000, 2018)
    println(" @$y:"); for (k, t, _) in SERIES; report(k, t, y); end
end
println(" @series end:")
for (k, t, _) in SERIES
    ys = [y for y in FY if isfinite(k === :glaciers ? obs_of(:gsic, y) : obs_of(t, y))]
    isempty(ys) || report(k, t, maximum(ys))
end
println(" AIS plateau (does the fit track the GRACE-FO pause?):")
for y in (2019, 2020, 2022, 2024, 2025); report(:ais, :ais, y); end
CSV.write(OUT_BIAS, bias)

println("\n90% coverage over the fit window (share of obs years inside the band)")
println("  parameter = posterior parameter spread only; predictive = + the calibrated AR(1)+obs error model")
cov = DataFrame(component=String[], n_years=Int[], coverage_param=Float64[],
                coverage_pred=Float64[], mean_bias=Float64[], in_sample=Bool[])
for (key, tcol, _) in SERIES
    ins, insp, bs = Bool[], Bool[], Float64[]
    for (j, y) in enumerate(FY)
        o = key === :glaciers ? qv(obs_corrected[:, j], 0.50) : obs_of(tcol, y)
        isnan(o) && continue
        push!(ins,  qv(model[key][:, j], 0.05) <= o <= qv(model[key][:, j], 0.95))
        push!(insp, key in FITTED &&
                    qv(pred[key][:, j], 0.05) <= o <= qv(pred[key][:, j], 0.95))
        push!(bs, qv(model[key][:, j], 0.50) - o)
    end
    isempty(ins) && continue
    cp = key in FITTED ? 100 * mean(insp) : NaN
    @printf("  %-9s %3d years   parameter %5.1f%%   predictive %5.1f%%   mean bias %+.2f cm%s\n",
            key, length(ins), 100 * mean(ins), cp, mean(bs),
            key in FITTED ? "" : "   [OUT-OF-SAMPLE: no fitted error model]")
    push!(cov, (string(key), length(ins), mean(ins),
                key in FITTED ? mean(insp) : NaN, mean(bs), key in FITTED))
end
CSV.write(OUT_COVER, cov)

println("\nwrote ", relpath(OUT_BANDS, LADRILLO_REPO), ", ", relpath(OUT_BIAS, LADRILLO_REPO),
        ", ", relpath(OUT_COVER, LADRILLO_REPO))
