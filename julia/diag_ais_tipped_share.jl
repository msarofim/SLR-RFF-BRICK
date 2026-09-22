## diag_ais_tipped_share.jl — how many posterior draws cross DAIS's fast-dynamics threshold under a scenario, per tag.
## WHY (2026-09-22, L29): the fixed-climate SSP1-2.6 AIS p95 fell 30.3 -> 17.0 cm (2100) and 50.4 -> 30.5 (2300) between
## L28 and L29 while every Antarctic marginal moved < 0.1 sd. On a BIMODAL tail a p95 is a step function of the tipped
## SHARE — it sits in the upper mode while the share exceeds 5 % and drops into the lower mode's edge the moment it does not —
## so the p95 change must be read as a share, not as a magnitude (memory: ais_amp_leverage_is_a_threshold). This writes the
## per-draw AIS at the horizons and the share above a gap threshold, for each tag given.
##   julia --project=julia_v2 julia/diag_ais_tipped_share.jl --tags=L28,L29 [--ssps=ssp126,ssp245] [--gap=15]
##   -> outputs/diag_ais_tipped_share_<tags>.csv (summary) and outputs/diag_ais_tipped_share_draws_<tags>.csv (per draw)
using CSV, DataFrames, Mimi, MimiBRICK, Statistics, Printf, Dates
include(joinpath(@__DIR__, "ladrillo_projection.jl"))
const SCRIPT   = "diag_ais_tipped_share.jl"
argv(p, d) = (i = findfirst(a -> startswith(a, p), ARGS); i === nothing ? d : ARGS[i][length(p)+1:end])
const TAGS     = String.(split(argv("--tags=", "L28,L29"), ","))
const SSPS     = Tuple(String.(split(argv("--ssps=", "ssp126,ssp245"), ",")))
const GAP_CM   = parse(Float64, argv("--gap=", "15"))   # AIS@2100 above this = the tipped mode (the SSP1-2.6 gap sits ~8-25 cm)
const NTHIN    = 2000
const HORIZONS = (2100, 2300)
const Y0, Y1   = 1850, 2300
const TAGSTR   = join(TAGS, "_")

summ  = DataFrame(tag=String[], ssp=String[], horizon=Int[], n=Int[], med=Float64[], p83=Float64[], p90=Float64[], p95=Float64[],
                  gap_cm=Float64[], share_above_gap_pct=Float64[], provenance=String[])
draws = DataFrame(tag=String[], ssp=String[], draw=Int[], ais_gmst_amp=Float64[], ais2100=Float64[], ais2300=Float64[])
for tag in TAGS
    path = joinpath(LADRILLO_REPO, "data/MimiBRICK/parameters_subsample_brick_mengel_$tag.csv")
    post = ladrillo_posterior(path=path, cols=:all, nthin=NTHIN)
    prov = "$SCRIPT | tag $tag ($(basename(path)), $(nrow(post)) evenly thinned draws) | fixed-driver arm (fair_mean_gmst, " *
           "$Y0-$Y1, LWS $(LWS_MODE)) | gap = AIS@2100 > $GAP_CM cm | cm relative to $(LADRILLO_REF) | $(now())"
    for ssp in SSPS
        bf = ladrillo_setup(ssp=ssp, y0=Y0, y1=Y1, gis_variant=ladrillo_posterior_variant(path)); ladrillo_set_tap!(bf)
        yrs = collect(Y0:Y1); yi = Dict(h => findfirst(==(h), yrs) for h in HORIZONS)
        a21 = Float64[]; a23 = Float64[]
        for (i, r) in enumerate(eachrow(post))
            ladrillo_run_draw!(bf, r); a = ladrillo_series(bf, :ais)
            push!(a21, a[yi[2100]]); push!(a23, a[yi[2300]])
            push!(draws, (tag, ssp, i, Float64(r.ais_gmst_amp), a[yi[2100]], a[yi[2300]]))
        end
        share = 100 * count(a21 .> GAP_CM) / length(a21)
        for (h, v) in ((2100, a21), (2300, a23))
            push!(summ, (tag, ssp, h, length(v), median(v), quantile(v, 0.83), quantile(v, 0.90), quantile(v, 0.95), GAP_CM, share, prov))
            @printf("%s %s @%d: n %d  med %.1f  p83 %.1f  p90 %.1f  p95 %.1f | share with AIS@2100 > %.0f cm: %.2f %%\n",
                    tag, ssp, h, length(v), median(v), quantile(v, 0.83), quantile(v, 0.90), quantile(v, 0.95), GAP_CM, share)
        end
    end
end
CSV.write(joinpath(LADRILLO_REPO, "outputs/diag_ais_tipped_share_$TAGSTR.csv"), summ)
CSV.write(joinpath(LADRILLO_REPO, "outputs/diag_ais_tipped_share_draws_$TAGSTR.csv"), draws)
println("wrote outputs/diag_ais_tipped_share_$TAGSTR.csv and _draws_")
