## ============================================================================
## diag_ais_spread_decomposition.jl — WHAT drives Ladrillo's AIS 2100 scenario
## spread, and is it by design or an artefact?
##
## THE QUESTION (Marcus, 2026-08-14). L10's AIS SSP1-2.6→SSP5-8.5 spread at 2100
## is 32.95 cm, against every FACTS module (ar5AIS −2.32, emuAIS −0.22, larmip
## 2.53, bamber19 8.92, deconto21 19.66) and matching only MAGICC-SLR (35.45).
## Two readings, and the scorecard could not separate them:
##   (a) BY DESIGN — Ladrillo freed λ/γ/κ and the 7 Strategy-B geometry params
##       that BRICK 2.0 fixed at the DAISfastdyn medoid, and re-mapped GMST→T_ant
##       from the paleo/equilibrium amp 1.196 to a sampled transient N(0.95,0.10)
##       (A6). A scenario-responsive AIS is what those changes are FOR.
##   (b) ARTEFACT — the spread is carried by `ais_iceflow0`, whose marginal R̂ is
##       2.359 (thread 3's non-mixing direction).
## Reading (b) would make the spread a reporting defect. Reading (a) would make
## it a criterion-4 PASS and the near-zero-spread FACTS modules the odd ones.
##
## METHOD — REVERT one parameter group to its BRICK 2.0 value across all draws
## and re-read the scenario spread. NOT freeze-at-posterior-median: the spread
## here is `med(ssp585) − med(ssp126)`, a scenario response OF the median, so
## freezing a group at its own median barely moves it (measured: every group
## retained 95-120% of the base spread — the freeze arm answers a different
## question and was discarded). Reverting to BRICK 2.0 answers the question
## actually asked: did OUR changes produce the wide response?
##
## BRICK 2.0 reference values:
##   A6         amp = 1/0.8365 = 1.19546 (the paleo/equilibrium map)
##   fast_dyn   lambda/gamma/kappa/threshold at the DAISfastdyn MEDOID
##   geometry   the 7 Strategy-B params at the same medoid
## all from outputs/recalib_central_row.csv, which is the medoid row BRICK 2.0
## fixed these at (its antarctic_lambda 0.013651 is the "λ 0.0137" the calibrator
## comment cites as biased pulse-amplifying).
##
## Also reported: the share of draws whose T_ant crosses
## `antarctic_temp_threshold`, per scenario — if the response is the fast-dynamics
## tail switching on under SSP5-8.5 and not SSP1-2.6, that is where it lives.
##
##   julia --project=julia_v2 julia/diag_ais_spread_decomposition.jl [n_draws]
## Writes outputs/diag_ais_spread_decomposition.csv
## ============================================================================

using CSV, DataFrames, Mimi, Printf, Statistics
include(joinpath(@__DIR__, "ladrillo_projection.jl"))

const OUT    = joinpath(LADRILLO_REPO, "outputs/diag_ais_spread_decomposition.csv")
const Y0, Y1 = 1850, 2100
const NDRAW  = length(ARGS) >= 1 ? parse(Int, ARGS[1]) : 500
const YEAR   = 2100
## The two ends define the spread; ssp245 is carried so the response is not read
## off two points alone.
const SSPS   = [("ssp126", "SSP1-2.6"), ("ssp245", "SSP2-4.5"), ("ssp585", "SSP5-8.5")]

## The BRICK 2.0 reference values, as (posterior column => value). Read from the
## DAISfastdyn medoid row rather than hardcoded, EXCEPT where the posterior
## samples a reparameterised coordinate — those two conversions are done here and
## are the only place this file can silently disagree with the calibrator:
##   ais_precip0_LOG = log(antarctic_precip0)   (MimiBRICK v2.0.0 exponentiates)
##   ais_runoff_Ton  = -antarctic_runoff_height0 / antarctic_c
const MEDOID = CSV.read(LADRILLO_MEDOID_CSV, DataFrame)[1, :]
const B20_AMP = 1.0 / 0.8365          # the paleo/equilibrium map BRICK 2.0 hardcodes

const GROUPS = [
    ("A6_tempmap", Dict("ais_gmst_amp" => B20_AMP)),
    ("fast_dyn",   Dict("antarctic_lambda"         => Float64(MEDOID.antarctic_lambda),
                        "antarctic_gamma"          => Float64(MEDOID.antarctic_gamma),
                        "antarctic_kappa"          => Float64(MEDOID.antarctic_kappa),
                        "antarctic_temp_threshold" => Float64(MEDOID.antarctic_temp_threshold))),
    ("geometry_B", Dict("ais_mu"          => Float64(MEDOID.antarctic_mu),
                        "ais_bedheight0"  => Float64(MEDOID.antarctic_bed_height0),
                        "ais_slope"       => Float64(MEDOID.antarctic_slope),
                        "ais_iceflow0"    => Float64(MEDOID.antarctic_flow0),
                        "ais_precip0_LOG" => log(Float64(MEDOID.antarctic_precip0)),
                        "ais_c"           => Float64(MEDOID.antarctic_c),
                        "ais_runoff_Ton"  => -Float64(MEDOID.antarctic_runoff_height0) /
                                              Float64(MEDOID.antarctic_c))),
    # the non-mixing suspect, ISOLATED — if the response is an artefact it is here
    ("iceflow0",   Dict("ais_iceflow0" => Float64(MEDOID.antarctic_flow0))),
]
## The all-at-once arm: every AIS change reverted together, i.e. "BRICK 2.0's AIS
## inside Ladrillo". Built from the groups so it cannot drift from them.
const ALL_KEY = "ALL_ais_to_BRICK20"

post0 = ladrillo_posterior(nthin=NDRAW)
@printf("AIS %d scenario-response decomposition | %s | %d draws | revert-to-BRICK-2.0\n",
        YEAR, basename(LADRILLO_POSTERIOR_CSV), nrow(post0))
for (g, d) in GROUPS
    miss = [c for c in keys(d) if !(c in names(post0))]
    isempty(miss) || error("group $g names columns not in the posterior: " * join(miss, ", "))
end

"""Median :ais at YEAR, the finite share, and the share of draws whose Antarctic
surface temperature ever reaches `antarctic_temp_threshold` — one pass."""
function run_arm(post, ssp)
    bf = ladrillo_setup(ssp=ssp, y0=Y0, y1=Y1, gis_variant = ladrillo_posterior_variant())
    iy = findfirst(==(YEAR), bf.years)
    vals, crossed = Float64[], 0
    for r in eachrow(post)
        ladrillo_run_draw!(bf, r)
        push!(vals, ladrillo_series(bf, :ais)[iy])
        # NB MimiBRICK spells it `antartic_...` (missing c), and Mimi leaves the
        # first timestep `missing` on a lagged variable — skipmissing, don't index.
        tant = collect(skipmissing(bf.m[:antarctic_icesheet, :antartic_surface_temperature]))
        !isempty(tant) && maximum(tant) >= r["antarctic_temp_threshold"] && (crossed += 1)
    end
    finite = filter(isfinite, vals)
    return median(finite), length(finite) / length(vals), crossed / nrow(post)
end

rows = DataFrame(arm=String[], ssp=String[], med_cm=Float64[], finite_share=Float64[],
                 crossed_share=Float64[], spread_126_585=Float64[], retained=Float64[])

function do_arm(name, post)
    med = Dict{String,Float64}()
    for (ssp, label) in SSPS
        m, fin, cr = run_arm(post, ssp)
        med[ssp] = m
        push!(rows, (arm=name, ssp=label, med_cm=m, finite_share=fin, crossed_share=cr,
                     spread_126_585=NaN, retained=NaN))
    end
    sp = med["ssp585"] - med["ssp126"]
    rows[end-length(SSPS)+1:end, :spread_126_585] .= sp
    return sp
end

revert(post, d) = (p = copy(post); for (c, v) in d; p[!, c] .= v; end; p)

t0 = time()
base = do_arm("BASE_L10", post0)
@printf("  BASE (L10 as shipped) spread = %6.2f cm   (%.0f s)\n", base, time() - t0)
rows[1:length(SSPS), :retained] .= 1.0

for (g, d) in GROUPS
    sp = do_arm("revert_$g", revert(post0, d))
    rows[end-length(SSPS)+1:end, :retained] .= sp / base
    @printf("  revert %-12s -> BRICK 2.0   spread = %6.2f cm   %5.1f%% of base\n",
            g, sp, 100 * sp / base)
end

allrev = Dict{String,Float64}()
for (_, d) in GROUPS; merge!(allrev, d); end
sp_all = do_arm(ALL_KEY, revert(post0, allrev))
rows[end-length(SSPS)+1:end, :retained] .= sp_all / base
@printf("  %-26s spread = %6.2f cm   %5.1f%% of base\n",
        ALL_KEY, sp_all, 100 * sp_all / base)

CSV.write(OUT, rows)
println("\nBASE arm — where the response lives")
for r in eachrow(rows[1:length(SSPS), :])
    @printf("  %-9s AIS median %7.2f cm | %5.1f%% of draws cross the threshold | finite %5.1f%%\n",
            r.ssp, r.med_cm, 100 * r.crossed_share, 100 * r.finite_share)
end
@printf("\nwrote %s  (%.0f s total)\n", relpath(OUT, LADRILLO_REPO), time() - t0)
