## ============================================================================
## ic_hindcast_residuals.jl — PER-DRAW hindcast residuals of Ladrillo (L24) and
## BRICK 2.0 against ONE common target set, for the information-criterion
## comparison in python/ic_ladrillo_vs_brick20.py.
##
## WHY A NEW DRIVER. The existing scorecard (scope_ladrillo_vs_brick20_scorecard.py)
## scores the posterior MEDIAN series, which has no likelihood attached and no
## parameter vector behind it. AIC/BIC need the likelihood at a PARAMETER VECTOR
## (the maximiser), and DIC needs it at every draw. Neither postpred driver keeps
## its per-draw series (posterior_predictive_ladrillo.jl holds them in memory only;
## posterior_predictive_oldbrick.jl writes bands). This driver forward-runs BOTH
## posteriors under the SAME conventions those two drivers use and writes the
## per-draw residual (model - obs, cm) per series and year, so every likelihood
## arm downstream is computed from one file per model.
##
## CONVENTIONS — matched to the two postpred drivers and the scorecard, so the
## residuals here ARE the residuals behind Table 4 of the L24 deliverable:
##   window     1850-2026 run, scored 1900-2026 where the target exists
##   forcing    fair_mean_{gmst,ohc}_ssp245harm.csv (both arms)
##   baseline   1995-2005 (the calibration re-reference)
##   targets    outputs/recalib_targets_ext.csv (ais, gis, steric, dang) and the
##              r19-seam-adjusted glacier target recalib_targets_ext_gsicadj.csv —
##              the SAME target both arms are scored against in the scorecard.
##              NO per-draw delta ramp and NO d2 discrepancy on either arm: those are
##              Ladrillo-only likelihood devices and would not be like-for-like.
##   glaciers   Ladrillo: gsic_hind scope (SLOWP + FAST + per-draw F_unch), as the
##              postpred; BRICK 2.0: gsic_sea_level.
##   total      ice + steric + OBSERVED LWS on both arms (the 2026-09-10 LWS ruling),
##              vs the Dangendorf/Frederikse-NOAA total. Out-of-sample for BOTH:
##              Ladrillo never scores it (DROP_TOTAL), BRICK 2.0 was fit to CW11.
##   draws      NDRAW evenly thinned from each 10,000-row posterior, SAME count on
##              both arms; the posterior row index is recorded per draw so the
##              maximising draw's parameters can be looked up.
##   BRICK 2.0  Random.seed!(2026) immediately before get_model (the LWS lock);
##              BRICK's own LWS is not used (0 before 2019 by calibration design).
##
##   julia --project=julia_v2 julia/ic_hindcast_residuals.jl [ndraw_ladrillo=2000] [ndraw_brick=all] [--tag=L24]
## Writes:
##   outputs/ic_hindcast_residuals_ladrillo_<TAG>.csv   draw, sd_*/rho_*, <series>_<year>
##   outputs/ic_hindcast_residuals_brick20.csv          same layout (BRICK's own noise cols)
##   outputs/ic_hindcast_obs_sigma.csv                  year, <series>_obs, <series>_sigma
## ============================================================================

using CSV, DataFrames, Mimi, MimiBRICK, Printf, Random, Statistics
include(joinpath(@__DIR__, "ladrillo_projection.jl"))   # brings brick_mengel.jl: set_forcing!, update_brick_params!

const Y0, Y1     = 1850, 2026
const FIT_REF    = (1995, 2005)
const FORCING    = "ssp245harm"
const FIT_START  = 1900
## DRAW COUNTS. Ladrillo defaults to 2000 = the postpred's NTHIN, thinned the same way, so
## its residual medians reproduce postpred_<TAG>_components_timeseries.csv EXACTLY (gated
## below). BRICK 2.0 defaults to ALL 10,000 because ITS postpred ran all 10,000, and only the
## same draw set reproduces its p50 exactly. The counts therefore differ (2000 vs 10,000):
## a max-over-draws log-likelihood is a lower bound that rises with draws, so the asymmetry
## favours BRICK 2.0 -- the conservative direction for the comparison this feeds.
const NDRAW_L, NDRAW_B = let p = filter(a -> !startswith(a, "--"), ARGS)
    (length(p) >= 1 ? parse(Int, p[1]) : 2000, length(p) >= 2 ? parse(Int, p[2]) : typemax(Int))
end
const DEFAULT_TAG = replace(replace(basename(LADRILLO_POSTERIOR_CSV),
                                    "parameters_subsample_brick_mengel_" => ""), ".csv" => "")
const POST_TAG = let i = findfirst(a -> startswith(a, "--tag="), ARGS)
    i === nothing ? DEFAULT_TAG : ARGS[i][7:end]
end
const POSTERIOR = joinpath(LADRILLO_REPO, "data/MimiBRICK/parameters_subsample_brick_mengel_$(POST_TAG).csv")
isfile(POSTERIOR) || error("no posterior for --tag=$POST_TAG at $POSTERIOR")
const BRICK_POSTERIOR = joinpath(LADRILLO_REPO, "data/MimiBRICK/parameters_subsample_brick.csv")
const BRICK_SEED = 2026
const OUT_L = joinpath(LADRILLO_REPO, "outputs/ic_hindcast_residuals_ladrillo_$(POST_TAG).csv")
const OUT_B = joinpath(LADRILLO_REPO, "outputs/ic_hindcast_residuals_brick20.csv")
const OUT_S = joinpath(LADRILLO_REPO, "outputs/ic_hindcast_obs_sigma.csv")

## series key => target column (the total's target is :dang)
const SERIES = [(:ais, :ais), (:gsic, :gsic), (:gis, :gis), (:steric, :steric), (:total, :dang)]

## ---------------------------------------------------------------------------
## targets + per-year observational sigma, exactly as posterior_predictive_ladrillo.jl
## ---------------------------------------------------------------------------
tg   = CSV.read(joinpath(LADRILLO_REPO, "outputs/recalib_targets_ext.csv"), DataFrame)
gadj = CSV.read(joinpath(LADRILLO_REPO, "outputs/recalib_targets_ext_gsicadj.csv"), DataFrame)
tgi(y) = findfirst(==(y), tg.year)
haveobs(col, y) = (r = tgi(y); r !== nothing && !ismissing(tg[r, col]) && !isnan(Float64(tg[r, col])))
FY = collect(FIT_START:Y1); ny = length(FY)
gsic_target = let d = Dict(Int(gadj[i, :year]) => Float64(gadj[i, :gsic_adj]) for i in 1:nrow(gadj))
    Dict(y => get(d, y, NaN) for y in FY)
end
obs_of(key, y) = key === :gsic ? gsic_target[y] : (haveobs(key, y) ? Float64(tg[tgi(y), key]) : NaN)
lws_obs = [haveobs(:lws, y) ? Float64(tg[tgi(y), :lws]) : NaN for y in FY]
all(isfinite, lws_obs) || error("observed lws does not cover $(FIT_START)-$(Y1)")
band_sigma(lo, hi) = max((Float64(hi) - Float64(lo)) / (2 * 1.645), 0.05)
function obs_sigma(tcol, y)
    r = tgi(y)
    (r === nothing || isnan(obs_of(tcol, y))) && return NaN
    tcol === :dang && return sqrt(Float64(tg[r, :dang_sig])^2 +
                                 band_sigma(tg[r, :lws_lo], tg[r, :lws_hi])^2)
    return band_sigma(tg[r, Symbol("$(tcol)_lo")], tg[r, Symbol("$(tcol)_hi")])
end
OBS   = Dict(k => [obs_of(t, y) for y in FY] for (k, t) in SERIES)
SIGMA = Dict(k => [obs_sigma(t, y) for y in FY] for (k, t) in SERIES)

sig = DataFrame(year=FY)
for (k, _) in SERIES
    sig[!, "$(k)_obs"] = OBS[k]; sig[!, "$(k)_sigma"] = SIGMA[k]
end
sig[!, "provenance"] = fill("ic_hindcast_residuals.jl | targets recalib_targets_ext.csv + " *
    "recalib_targets_ext_gsicadj.csv (gsic) | sigma = max((hi-lo)/(2*1.645), 0.05) cm, total adds " *
    "dang_sig (+) lws band in quadrature | re-referenced $(FIT_REF[1])-$(FIT_REF[2]) | cm", ny)
CSV.write(OUT_S, sig)

## ---------------------------------------------------------------------------
## residual table writer
## ---------------------------------------------------------------------------
function write_residuals(path, draws, noise, resid, prov)
    df = DataFrame(draw = draws)
    for (c, v) in noise; df[!, c] = v; end
    for (k, _) in SERIES, (j, y) in enumerate(FY)
        df[!, "$(k)_$(y)"] = resid[k][:, j]
    end
    df[!, "provenance"] = fill(prov, nrow(df))
    CSV.write(path, df)
end

## ---------------------------------------------------------------------------
## Ladrillo
## ---------------------------------------------------------------------------
post = ladrillo_posterior(path=POSTERIOR, cols=:all, nthin=NDRAW_L)
const VARIANT = ladrillo_posterior_variant(POSTERIOR)
nfull = nrow(CSV.read(POSTERIOR, DataFrame; select=[1]))
ldraws = collect(1:cld(nfull, NDRAW_L):nfull)[1:nrow(post)]      # the rows _ladrillo_thin keeps
## lws=:central PINNED (2026-09-21): the objective was calibrated with land water zero before 2018 (:central since 09-18); projections default to :observed (brick_mengel.jl LWS_MODE) and must not move the hindcast side.
bf  = ladrillo_setup(ssp="ssp245", y0=Y0, y1=Y1, forcing_tag=FORCING, ref=FIT_REF, gis_variant=VARIANT, lws=:central)
imy = [ladrillo_yi(bf, y) for y in FY]
@printf("Ladrillo %s | %d of %d draws | %d-%d scored, base %d-%d | forcing %s\n",
        POST_TAG, nrow(post), nfull, FIT_START, Y1, FIT_REF[1], FIT_REF[2], FORCING)
resL = Dict(k => Array{Float64}(undef, nrow(post), ny) for (k, _) in SERIES)
t0 = time()
for (i, r) in enumerate(eachrow(post))
    ladrillo_run_draw!(bf, r)
    u = Float64(r["gic_u_unch"])
    ais  = ladrillo_series(bf, :ais)[imy]
    gsic = ladrillo_series(bf, :gsic_hind; funch=u)[imy]
    gis  = ladrillo_series(bf, :gis)[imy]
    te   = ladrillo_series(bf, :te)[imy]
    tot  = ladrillo_series(bf, :glaciers; funch=u)[imy] .+ ais .+ gis .+ te .+ lws_obs
    resL[:ais][i, :] = ais .- OBS[:ais];  resL[:gsic][i, :] = gsic .- OBS[:gsic]
    resL[:gis][i, :] = gis .- OBS[:gis];  resL[:steric][i, :] = te .- OBS[:steric]
    resL[:total][i, :] = tot .- OBS[:total]
    i % 250 == 0 && (print("."); flush(stdout))
end
@printf("\n  Ladrillo: %d draws in %.0fs\n", nrow(post), time() - t0)
lnoise = [(c, Float64.(post[!, c])) for c in ("sd_ais", "rho_ais", "sd_gsic", "rho_gsic",
                                              "sd_gis", "rho_gis", "sd_steric", "rho_steric")]
write_residuals(OUT_L, ldraws, lnoise, resL,
    "ic_hindcast_residuals.jl | Ladrillo tag $POST_TAG | posterior $(basename(POSTERIOR)) " *
    "NDRAW=$(nrow(post)) evenly thinned of $nfull | forcing $FORCING | run $Y0-$Y1 scored $FIT_START-$Y1 " *
    "reref $(FIT_REF[1])-$(FIT_REF[2]) | gsic = gsic_hind + F_unch vs gsic_adj target, no delta ramp, no d2 | " *
    "total = glaciers+ais+gis+te+OBSERVED lws vs dang | residual = model - obs, cm")
println("wrote $(relpath(OUT_L, LADRILLO_REPO))")

## ---------------------------------------------------------------------------
## BRICK 2.0 (stock MimiBRICK v2.0.0, Wong's posterior)
## ---------------------------------------------------------------------------
lc(p, c) = (d = CSV.read(p, DataFrame); Dict(Int(d[i, "year"]) => Float64(d[i, c]) for i in 1:nrow(d)))
years = collect(Y0:Y1)
gmst = [lc(joinpath(LADRILLO_OBS, "fair_mean_gmst_$(FORCING).csv"), "gmst_C")[y] for y in years]
ohc  = [lc(joinpath(LADRILLO_OBS, "fair_mean_ohc_$(FORCING).csv"), "ohc_1e22J")[y] for y in years]
ib   = [findfirst(==(y), years) for y in FIT_REF[1]:FIT_REF[2]]
myi  = [findfirst(==(y), years) for y in FY]
Random.seed!(BRICK_SEED)                       # immediately before get_model: it consumes the stream
m = MimiBRICK.get_model(ssprcp_scenario="ssp245", start_year=Y0, end_year=Y1)
set_forcing!(m, gmst, ohc)
reref(v) = 100 .* (v .- sum(v[ib]) / length(ib))
bpost_full = CSV.read(BRICK_POSTERIOR, DataFrame)
bdraws = let n = nrow(bpost_full), s = cld(n, min(NDRAW_B, n)), v = collect(1:s:n); v[1:min(NDRAW_B, length(v))] end
bpost = bpost_full[bdraws, :]
@printf("BRICK 2.0 | %d of %d draws | seed %d before get_model\n", nrow(bpost), nrow(bpost_full), BRICK_SEED)
resB = Dict(k => Array{Float64}(undef, nrow(bpost), ny) for (k, _) in SERIES)
t0 = time()
for i in 1:nrow(bpost)
    update_brick_params!(m, bpost[i, :]; precip_log=true)
    run(m)
    ais  = reref(m[:antarctic_icesheet, :ais_sea_level])[myi]
    gsic = reref(m[:glaciers_small_icecaps, :gsic_sea_level])[myi]
    gis  = reref(m[:greenland_icesheet, :greenland_sea_level])[myi]
    te   = reref(m[:thermal_expansion, :te_sea_level])[myi]
    tot  = ais .+ gsic .+ gis .+ te .+ lws_obs
    resB[:ais][i, :] = ais .- OBS[:ais];  resB[:gsic][i, :] = gsic .- OBS[:gsic]
    resB[:gis][i, :] = gis .- OBS[:gis];  resB[:steric][i, :] = te .- OBS[:steric]
    resB[:total][i, :] = tot .- OBS[:total]
    i % 250 == 0 && (print("."); flush(stdout))
end
@printf("\n  BRICK 2.0: %d draws in %.0fs\n", nrow(bpost), time() - t0)
bnoise = [(c, Float64.(bpost[!, c])) for c in ("sd_glaciers", "rho_glaciers", "sd_greenland", "rho_greenland",
                                               "sd_antarctic", "rho_antarctic", "sd_gmsl", "rho_gmsl")]
write_residuals(OUT_B, bdraws, bnoise, resB,
    "ic_hindcast_residuals.jl | BRICK 2.0 stock MimiBRICK get_model(ssp245), Random.seed!($BRICK_SEED) " *
    "immediately before get_model | posterior $(basename(BRICK_POSTERIOR)) NDRAW=$(nrow(bpost)) evenly thinned " *
    "of $(nrow(bpost_full)) | forcing $FORCING | run $Y0-$Y1 scored $FIT_START-$Y1 reref $(FIT_REF[1])-$(FIT_REF[2]) | " *
    "gsic = gsic_sea_level vs gsic_adj target | total = ais+gsic+gis+te+OBSERVED lws vs dang | residual = model - obs, cm")
println("wrote $(relpath(OUT_B, LADRILLO_REPO))")

## ---------------------------------------------------------------------------
## GATE: the per-draw medians must reproduce the two postpred files' p50 series EXACTLY,
## or these residuals are not the residuals behind Table 4. Exactness holds only on the
## postpred's own draw set (Ladrillo NTHIN=2000 thinned identically; BRICK 2.0 all 10,000
## under the same seed); a different draw count on either arm makes its p50 a different
## subset's median and the gate then bounds it at a quarter of the smallest obs sigma
## (a 2000-of-10,000 BRICK subset was measured at 0.039 cm on AIS, above that bound).
## ---------------------------------------------------------------------------
ppL = CSV.read(joinpath(LADRILLO_REPO, "outputs/postpred_$(POST_TAG)_components_timeseries.csv"), DataFrame)
ppB = CSV.read(joinpath(LADRILLO_REPO, "outputs/postpred_oldbrick_components_timeseries.csv"), DataFrame)
medL = Dict(k => [median(resL[k][:, j]) + OBS[k][j] for j in 1:ny] for (k, _) in SERIES)
medB = Dict(k => [median(resB[k][:, j]) + OBS[k][j] for j in 1:ny] for (k, _) in SERIES)
lmap = Dict(:ais => "ais", :gsic => "glaciers", :gis => "gis", :steric => "te", :total => "total")
bmap = Dict(:ais => "ais", :gsic => "gsic", :gis => "gis", :steric => "te", :total => "total")
ok = true
for (k, _) in SERIES
    fin = findall(j -> isfinite(OBS[k][j]), 1:ny)
    dL = maximum(abs.(medL[k][fin] .- Float64.(ppL[fin, "$(lmap[k])_p50"])))
    dB = maximum(abs.(medB[k][fin] .- Float64.(ppB[fin, "$(bmap[k])_p50"])))
    tolL = nrow(post) == 2000 ? 1e-9 : 0.25 * minimum(filter(isfinite, SIGMA[k]))
    tolB = nrow(bpost) == nrow(bpost_full) ? 1e-9 : 0.25 * minimum(filter(isfinite, SIGMA[k]))
    passL = dL < tolL; passB = dB < tolB
    @printf("  [gate] %-6s median vs postpred p50: Ladrillo max|Δ| %.2e vs tol %.0e (%s)  BRICK 2.0 %.2e vs tol %.0e (%s)\n",
            k, dL, tolL, passL ? "PASS" : "FAIL", dB, tolB, passB ? "PASS" : "FAIL")
    global ok &= passL && passB
end
ok || error("residual medians do not reproduce the postpred p50 series — these are NOT the Table 4 residuals")
println("GATE PASS — per-draw residual medians reproduce the postpred p50 series")
