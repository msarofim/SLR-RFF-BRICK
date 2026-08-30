## ============================================================================
## project_ssps_components_oldbrick.jl — BRICK 2.0 PROJECTIONS, ALL COMPONENTS,
##                                       ALL SSPs, to 2300.
##
## WHY THIS EXISTS. `ladrillo_model_comparison.py` could only ever put ONE BRICK 2.0
## arm on the projection table — glaciers, from `project_ssps_gsic_2300.jl` — because
## that was the only BRICK 2.0 projection ever produced. Every AIS / Greenland / TE /
## total cell of the comparison therefore had a BLANK where the reference model should
## be, and `handoff_2026-08-25b_module_assessment.md` §3 has to warn "do not report a
## blank as a zero". The durable benchmark (`python/bench_ladrillo.py`) needs BRICK 2.0
## on the PROJECTION side as well as the hindcast side, so it is produced here.
##
## WHAT "BRICK 2.0" MEANS. Stock MimiBRICK v2.0.0 (`MimiBRICK.get_model`, no `replace!`)
## on its OWN published posterior `data/MimiBRICK/parameters_subsample_brick.csv`
## (post-PR#93). NOT recalibrated on our extended targets. Identical convention to
## `posterior_predictive_oldbrick.jl` (the hindcast arm) and to
## `project_ssps_gsic_2300.jl` (the glacier arm) — same posterior file, same
## `update_brick_params!(...; precip_log=true)` shim, same seed before `get_model`.
##
## LIKE-FOR-LIKE WITH LADRILLO. Same FaIR 2.2.4 (calib 1.6.0 + CMIP7 since 2026-08-30;
## was 1.4.5 and this line said so) ENSEMBLE-MEAN GMST + OHC
## per SSP (`data/observations/fair_mean_{gmst,ohc}_<ssp>.csv`), same 1995-2014 AR6
## re-reference window, same horizons, same output schema as
## `outputs/ssps_components_2300_<TAG>.csv`. Both arms are therefore MEAN-FORCING:
## their bands are POSTERIOR-PARAMETER spread only and are NOT comparable to the
## FACTS/MAGICC bands, which carry climate uncertainty. (The Ladrillo JOINT band is
## the one that is; see `scope_slr_fairunc_draws_*`.)
##
## CROSS-CHECK BUILT IN: the glacier column here must reproduce
## `outputs/ssps_gsic_2300.csv` to within the get_model non-determinism, since it is
## the same model, posterior, forcing and window. [GSIC-MATCH] reports it.
##
##   julia --project=julia_v2 julia/project_ssps_components_oldbrick.jl [n_draws]
## Writes outputs/ssps_components_2300_oldbrick.csv
## ============================================================================
using CSV, DataFrames, Mimi, MimiBRICK, Statistics, Printf, Random
include(joinpath(@__DIR__, "brick_mengel.jl"))      # set_forcing! + update_brick_params!

const REPO = abspath(joinpath(@__DIR__, ".."))
const OBS  = joinpath(REPO, "data/observations")
const POST = joinpath(REPO, "data/MimiBRICK/parameters_subsample_brick.csv")
const Y0, Y1 = 1850, 2300
const BASE0, BASE1 = 1995, 2014                     # AR6 SLR reference window
const SEED = 2026                                   # get_model is non-deterministic (~1e-5 m)
const OUT  = joinpath(REPO, "outputs/ssps_components_2300_oldbrick.csv")
const GSIC_REF = joinpath(REPO, "outputs/ssps_gsic_2300.csv")
## The three SSPs every comparison source (FACTS, MAGICC-SLR, Ladrillo) shares, plus
## the three Ladrillo also runs, so the file is a superset of what the benchmark needs.
const SSPS = [("ssp119","SSP1-1.9"), ("ssp126","SSP1-2.6"), ("ssp245","SSP2-4.5"),
              ("ssp460","SSP4-6.0"), ("ssp370","SSP3-7.0"), ("ssp585","SSP5-8.5")]
const YEARS_OUT = collect(1990:10:2300)
const NTHIN = 1000

years = collect(Y0:Y1)
ib  = [findfirst(==(y), years) for y in BASE0:BASE1]
idx(y) = findfirst(==(y), years)
reref(v) = 100 .* (v .- sum(v[ib])/length(ib))      # m -> cm, rel 1995-2014

NDRAW = length(ARGS) >= 1 ? parse(Int, ARGS[1]) : NTHIN

lc(p, c) = (d = CSV.read(p, DataFrame);
            by = Dict(Int(d[i, "year"]) => Float64(d[i, c]) for i in 1:nrow(d));
            [by[y] for y in years])

post = CSV.read(POST, DataFrame)
stepp = max(1, nrow(post) ÷ NDRAW)
rows = collect(1:stepp:nrow(post))
@printf("BRICK 2.0 all-component projections: %d draws (thinned from %d), %d-%d, reref %d-%d\n",
        length(rows), nrow(post), Y0, Y1, BASE0, BASE1)

oi = [idx(y) for y in YEARS_OUT]
COMPS = ["glaciers", "gis", "ais", "te", "lws", "total"]
out = DataFrame(year=Int[], ssp=String[], component=String[], gmst=Float64[],
                med=Float64[], p05=Float64[], p17=Float64[], p83=Float64[],
                p95=Float64[], n_finite=Int[])

for (ssp, label) in SSPS
    gmst = lc(joinpath(OBS, "fair_mean_gmst_$ssp.csv"), "gmst_C")
    ohc  = lc(joinpath(OBS, "fair_mean_ohc_$ssp.csv"), "ohc_1e22J")
    Random.seed!(SEED)
    m = MimiBRICK.get_model(ssprcp_scenario="ssp245", start_year=Y0, end_year=Y1)
    set_forcing!(m, gmst, ohc)
    store = Dict(c => Array{Float64}(undef, length(rows), length(YEARS_OUT)) for c in COMPS)
    @time for (k, i) in enumerate(rows)
        update_brick_params!(m, post[i, :]; precip_log=true)
        run(m)
        ais  = reref(m[:antarctic_icesheet,     :ais_sea_level])[oi]
        gsic = reref(m[:glaciers_small_icecaps, :gsic_sea_level])[oi]
        gis  = reref(m[:greenland_icesheet,     :greenland_sea_level])[oi]
        te   = reref(m[:thermal_expansion,      :te_sea_level])[oi]
        lws  = reref(m[:landwater_storage,      :lws_sea_level])[oi]
        store["ais"][k,:]=ais;  store["glaciers"][k,:]=gsic; store["gis"][k,:]=gis
        store["te"][k,:]=te;    store["lws"][k,:]=lws
        store["total"][k,:] = ais .+ gsic .+ gis .+ te .+ lws
    end
    for (j, y) in enumerate(YEARS_OUT), c in COMPS
        v = filter(isfinite, store[c][:, j])
        push!(out, (y, label, c, gmst[idx(y)],
                    quantile(v,0.50), quantile(v,0.05), quantile(v,0.17),
                    quantile(v,0.83), quantile(v,0.95), length(v)))
    end
    @printf("  %s done: total@2100 med %.2f cm, @2300 med %.2f cm\n", label,
            quantile(filter(isfinite, store["total"][:, findfirst(==(2100), YEARS_OUT)]), 0.5),
            quantile(filter(isfinite, store["total"][:, findfirst(==(2300), YEARS_OUT)]), 0.5))
end

CSV.write(OUT, out)
println("Wrote ", OUT)

## [GSIC-MATCH] — the glacier column must reproduce the standalone glacier driver.
## A mismatch above the get_model non-determinism means the forcing or the posterior
## thinning differs between the two arms, and the whole file is then not like-for-like.
## ⚠ THIS GATE WAS VACUOUS UNTIL 2026-08-30 AND HAD NEVER ONCE FIRED. Two independent
## defects, either of which alone forced "0.0000 cm":
##   1. LABEL MISMATCH. It mapped r.ssp ("SSP5-8.5") to a SHORT form ("ssp585") and then
##      matched that against ssps_gsic_2300.csv -- which uses the LONG labels. `nrow(h) == 1`
##      was therefore false on every row and every row hit `continue`. ZERO rows were ever
##      compared, for either calibration vintage.
##   2. SOFT-SCOPE ASSIGNMENT. `worst = max(worst, ...)` inside a top-level `for` binds a NEW
##      LOCAL each iteration, so the outer `worst` stayed 0.0 even if a row had matched.
##      Julia WARNED about this on every run ("Assignment to `worst` in soft scope is
##      ambiguous") and the warning was never acted on.
## `n_matched` is now printed BESIDE the number: a gate that compares nothing must not be
## able to report a pass (`no_power_null`, `mutation_test_gates`).
if isfile(GSIC_REF)
    ref = CSV.read(GSIC_REF, DataFrame)
    global worst = 0.0
    global n_matched = 0
    for r in eachrow(filter(x -> x.component == "glaciers", out))
        h = filter(x -> x.ssp == r.ssp && x.year == r.year, ref)   # BOTH use long labels
        nrow(h) == 1 || continue
        global n_matched += 1
        global worst = max(worst, abs(r.med - h[1, :gsic_med]))
    end
    @printf("[GSIC-MATCH] worst |median difference| vs ssps_gsic_2300.csv: %.4f cm  (%d rows compared)\n",
            worst, n_matched)
    n_matched == 0 && error("[GSIC-MATCH] compared ZERO rows -- the gate is vacuous, not passing.")
    worst > 0.05 && @warn "GSIC arms disagree by more than the get_model non-determinism"
end
