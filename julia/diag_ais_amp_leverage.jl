## diag_ais_amp_leverage.jl — the PROJECTION leverage of the Antarctic amplification (ais_gmst_amp) on a posterior tag:
## "a one-sigma change in the amplification moves Antarctic sea level at 2300 by X cm" (the GMD draft's calibration
## section). Two definitions, both written, because they answer different questions:
##   (a) REGRESSION across the posterior draws: OLS slope of AIS@2300 on ais_gmst_amp, times sigma. Draws vary jointly
##       with the other AIS parameters, so this is the MARGINAL association the posterior exhibits.
##   (b) PERTURBATION: every draw re-run with ais_gmst_amp + sigma (and - sigma), all other parameters held; median (and
##       mean) of the per-draw change. This is the partial derivative the "revert to 1.196" arm also measures. The per-draw
##       changes are written too (diag_ais_amp_leverage_draws_<tag>.csv): on SSP2-4.5 they are BIMODAL — a subset of draws
##       is pushed across the DAIS thresholds — so the mean, the median and the regression slope answer different questions.
## sigma = the PRIOR sd (0.180, N(1.09, 0.180)); the posterior sd is also written (prior-dominated, ~0.95x).
## Fixed-driver arm (FaIR ensemble-mean forcing), 1850-2300, the tagged thinned subsample; medians of the scenario's
## AIS and total at 2300 for the "share of the scenario's total" phrasing.
##   julia --project=julia_v2 julia/diag_ais_amp_leverage.jl --tag=L27   -> outputs/diag_ais_amp_leverage_<tag>.csv

using CSV, DataFrames, Mimi, MimiBRICK, Statistics, Printf, Dates
include(joinpath(@__DIR__, "ladrillo_projection.jl"))

const SCRIPT   = "diag_ais_amp_leverage.jl"
const TAG      = (i = findfirst(a -> startswith(a, "--tag="), ARGS); i === nothing ? "L27" : ARGS[i][7:end])
const NTHIN    = 2000
const SIGMA    = 0.180                       # the prior sd of ais_gmst_amp, N(1.09, 0.180)
const SSPS     = ("ssp245", "ssp585")
const HORIZONS = (2100, 2300)
const Y0, Y1   = 1850, 2300
const PATH     = joinpath(LADRILLO_REPO, "data/MimiBRICK/parameters_subsample_brick_mengel_$TAG.csv")
const OUTCSV   = joinpath(LADRILLO_REPO, "outputs/diag_ais_amp_leverage_$TAG.csv")
const OUTDRAWS = joinpath(LADRILLO_REPO, "outputs/diag_ais_amp_leverage_draws_$TAG.csv")

post = ladrillo_posterior(path=PATH, cols=:all, nthin=NTHIN)
amp  = Float64.(post.ais_gmst_amp)
prov = "$SCRIPT | tag $TAG ($(basename(PATH)), $(nrow(post)) evenly thinned draws) | fixed-driver arm (fair_mean_gmst, " *
       "$Y0-$Y1, LWS $(LWS_MODE)) | sigma = prior sd $SIGMA; posterior sd $(round(std(amp), digits=4)) | (a) OLS slope of " *
       "AIS@h on ais_gmst_amp across draws x sigma; (b) each draw re-run with amp + sigma, others held, median/mean of the " *
       "per-draw change | cm relative to $(LADRILLO_REF) | $(now())"

rows = DataFrame(tag=String[], ssp=String[], horizon=Int[], definition=String[], sigma_kind=String[], sigma=Float64[],
                 leverage_cm=Float64[], leverage_mean_cm=Float64[], ais_med_cm=Float64[], total_med_cm=Float64[],
                 share_of_total_pct=Float64[], slope_cm_per_unit=Float64[], n=Int[], provenance=String[])
draws = DataFrame(tag=String[], ssp=String[], draw=Int[], ais_gmst_amp=Float64[], ais2100=Float64[], ais2300=Float64[], total2300=Float64[],
                  d_plus_2100=Float64[], d_plus_2300=Float64[], d_minus_2100=Float64[], d_minus_2300=Float64[])
for ssp in SSPS
    bf = ladrillo_setup(ssp=ssp, y0=Y0, y1=Y1, gis_variant=ladrillo_posterior_variant(PATH)); ladrillo_set_tap!(bf)
    yrs = collect(Y0:Y1); yi = Dict(h => findfirst(==(h), yrs) for h in HORIZONS)
    base = Dict(h => Float64[] for h in HORIZONS); pert = Dict(h => Float64[] for h in HORIZONS)
    tot  = Dict(h => Float64[] for h in HORIZONS)
    for (i, r) in enumerate(eachrow(post))
        ladrillo_run_draw!(bf, r)
        a = ladrillo_series(bf, :ais); t = ladrillo_series(bf, :total)
        for h in HORIZONS; push!(base[h], a[yi[h]]); push!(tot[h], t[yi[h]]); end
        r2 = DataFrame(r); r2.ais_gmst_amp .+= SIGMA
        ladrillo_run_draw!(bf, r2[1, :])
        a2 = ladrillo_series(bf, :ais)
        for h in HORIZONS; push!(pert[h], a2[yi[h]]); end
        r3 = DataFrame(r); r3.ais_gmst_amp .-= SIGMA
        ladrillo_run_draw!(bf, r3[1, :])
        a3 = ladrillo_series(bf, :ais)
        push!(draws, (TAG, ssp, i, Float64(r.ais_gmst_amp), a[yi[2100]], a[yi[2300]], t[yi[2300]],
                      a2[yi[2100]] - a[yi[2100]], a2[yi[2300]] - a[yi[2300]], a3[yi[2100]] - a[yi[2100]], a3[yi[2300]] - a[yi[2300]]))
    end
    for h in HORIZONS
        slope = (X = hcat(ones(length(amp)), amp); (X \ base[h])[2])
        d = pert[h] .- base[h]
        am, tm = median(base[h]), median(tot[h])
        for (kind, s) in (("prior", SIGMA), ("posterior", std(amp)))
            push!(rows, (TAG, ssp, h, "regression", kind, s, slope * s, slope * s, am, tm, 100 * slope * s / tm, slope, length(amp), prov))
        end
        push!(rows, (TAG, ssp, h, "perturbation", "prior", SIGMA, median(d), mean(d), am, tm, 100 * median(d) / tm, NaN, length(d), prov))
        @printf("%s %s @%d: AIS med %.1f, total med %.1f | (a) regression %.1f cm/unit -> %.1f cm per prior sd, %.1f per post sd | (b) perturbation +%.3f: median %.1f cm (mean %.1f), %.1f%% of the total\n",
                TAG, ssp, h, am, tm, slope, slope * SIGMA, slope * std(amp), SIGMA, median(d), mean(d), 100 * median(d) / tm)
    end
end
draws.provenance .= prov
CSV.write(OUTCSV, rows); CSV.write(OUTDRAWS, draws)
println("wrote ", relpath(OUTCSV, LADRILLO_REPO), " and ", relpath(OUTDRAWS, LADRILLO_REPO))
