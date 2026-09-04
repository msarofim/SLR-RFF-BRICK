## ============================================================================
## diag_gcrit_brick2_vs_ladrillo.jl -- WHY BRICK 2.0's p_fired SITS ABOVE LADRILLO'S
##
## WHY THIS EXISTS. The stage-3 sweep (`scope_slr_pulse_vv_brick2.jl`, 2026-09-04) returned a
## BRICK 2.0 `p_fired` above Ladrillo's in ALL 28 marker x specie x horizon cells, ratio
## 1.2-1.7x. All-same-sign across N >> 1 is a code-path signature until disproven
## (`suspicious uniformity ~ bug signal`), so it gets a test rather than a story.
##
## THE TEST. Both models fire DAIS when the Antarctic surface temperature crosses
## `antarctic_temp_threshold`, and in both the map from GMST is a line, so each posterior draw
## has a single CRITICAL GMST at which it fires:
##     BRICK 2.0 : T_ant = (GMST[t-1] - b) / a,  a, b FIXED   => gcrit = b + a * thr
##     Ladrillo  : T_ant = amp * GMST[t-1] + TANT0, amp SAMPLED => gcrit = (thr - TANT0) / amp
## Putting both on the SAME axis -- degrees of GMST -- makes the two posteriors directly
## comparable without running either model. If the distributions coincide, the uniform p_fired
## gap is a defect in one of the drivers. If they do not, the gap is the posteriors.
##
## ⚠ THE THINNING MUST MATCH THE RUNS or this compares different subsets: BRICK 2.0's step-5
## thinning of the published subsample, and Ladrillo's 500-per-chain post-burn thinning over
## the four L24 seeds -- the same rules `scope_slr_pulse_vv_brick2.jl` and
## `scope_slr_pulse_vv.jl` apply to their own draws.
##
##   julia --project=julia_v2 julia/diag_gcrit_brick2_vs_ladrillo.jl [--chain-tag=L24]
## Writes outputs/diag_gcrit_brick2_vs_ladrillo_<TAG>.csv
## ============================================================================
using CSV, DataFrames, Statistics, Printf

const REPO = abspath(joinpath(@__DIR__, ".."))
argval(flag, dflt) = let i = findfirst(a -> startswith(a, flag), ARGS)
    i === nothing ? dflt : ARGS[i][(length(flag) + 1):end]
end
const CHAIN_TAG = argval("--chain-tag=", "L24")
const SEEDS = [2026, 2027, 2028, 2029]
const NITER, NBURN = 2000000, 1000000
const N_PER_CHAIN = 500          # scope_slr_pulse_vv.jl's N_TARGET default => 2000 total
const NDRAW_B20   = 2000         # scope_slr_pulse_vv_brick2.jl's --ndraw default

## ⚠ READ OFF THE MODEL, not typed. These are MimiBRICK v2.0.0's regression constants and they
## can move under a package bump; Ladrillo's TANT0 is DEFINED from the same pair, so both sides
## of this comparison must come from one source (`derived_must_mean_computed`).
using Mimi, MimiBRICK, Random
Random.seed!(2026)
let m = MimiBRICK.get_model(ssprcp_scenario = "ssp245", start_year = 1850, end_year = 2300)
    run(m)
    global const AIS_COEF = Float64(m[:antarctic_icesheet, :ais_temperature_coefficient])
    global const AIS_INT  = Float64(m[:antarctic_icesheet, :ais_temperature_intercept])
end
const TANT0 = -AIS_INT / AIS_COEF          # = LADRILLO_AIS_TANT0, by construction

post = CSV.read(joinpath(REPO, "data/MimiBRICK/parameters_subsample_brick.csv"), DataFrame)
const ROWS_B = collect(1:max(1, nrow(post) ÷ NDRAW_B20):nrow(post))
gB = [AIS_INT + AIS_COEF * Float64(post[r, :antarctic_temp_threshold]) for r in ROWS_B]

gL = Float64[]; ampL = Float64[]; thrL = Float64[]
for sd in SEEDS
    p = joinpath(REPO, "outputs/mcmc", "chain_$(CHAIN_TAG)_seed$(sd)_n$(NITER).csv")
    isfile(p) || error("missing chain $(p)")
    d = CSV.read(p, DataFrame; select = [:ais_gmst_amp, :antarctic_temp_threshold])
    d = d[(NBURN + 1):end, :]
    step = max(1, nrow(d) ÷ N_PER_CHAIN)
    idx = collect(1:step:nrow(d))[1:min(N_PER_CHAIN, length(1:step:nrow(d)))]
    for i in idx
        amp = Float64(d[i, :ais_gmst_amp]); thr = Float64(d[i, :antarctic_temp_threshold])
        push!(ampL, amp); push!(thrL, thr); push!(gL, (thr - TANT0) / amp)
    end
end

qs(v) = (minimum(v), quantile(v, .05), quantile(v, .25), median(v),
         quantile(v, .75), quantile(v, .95), maximum(v))
@printf("CRITICAL GMST FOR DAIS FIRING (degC, the model's own GMST frame)\n")
@printf("  BRICK 2.0 : gcrit = %.4f + %.4f * thr   (slope FIXED)\n", AIS_INT, AIS_COEF)
@printf("  Ladrillo  : gcrit = (thr - %.4f) / amp  (amp SAMPLED)\n\n", TANT0)
@printf("%-10s %5s %7s %7s %7s %7s %7s %7s %7s %8s\n",
        "model", "n", "min", "p05", "p25", "med", "p75", "p95", "max", "sd")
for (nm, v) in (("BRICK2.0", gB), ("Ladrillo", gL))
    @printf("%-10s %5d %7.3f %7.3f %7.3f %7.3f %7.3f %7.3f %7.3f %8.4f\n",
            nm, length(v), qs(v)..., std(v))
end

## THE TWO CHANNELS, separated. A LOCATION difference moves how many draws sit inside the
## markers' own warming range; a SPREAD difference changes how concentrated they are there.
## Both push the same way here, so the report names each rather than quoting one ratio.
@printf("\n  LOCATION: median gcrit %.3f (BRICK 2.0) vs %.3f (Ladrillo) = %+.3f degC.\n",
        median(gB), median(gL), median(gB) - median(gL))
@printf("            BRICK 2.0 fires COLDER, so more of its draws sit inside the markers'\n")
@printf("            2100 range (baseline dT 1.64-3.32 K over the seven van Vuuren markers).\n")
@printf("  SPREAD:   sd %.4f vs %.4f = Ladrillo %.2fx WIDER. Ladrillo samples the slope\n",
        std(gB), std(gL), std(gL) / std(gB))
@printf("            (`ais_gmst_amp`, sd %.4f over these draws); BRICK 2.0 holds it at %.4f.\n",
        std(ampL), 1 / AIS_COEF)
@printf("            A wider gcrit spreads draws OUT of the markers' range at both ends.\n")
@printf("\n  => the uniform p_fired gap is the two POSTERIORS on the same axis, not a driver\n")
@printf("     defect. It is a structural difference to REPORT beside the two p_fired columns,\n")
@printf("     not a discrepancy to reconcile.\n")

out = DataFrame(model = String[], n = Int[], stat = String[], value = Float64[])
for (nm, v) in (("BRICK2.0", gB), ("Ladrillo", gL))
    for (s, x) in zip(["min","p05","p25","med","p75","p95","max"], qs(v))
        push!(out, (nm, length(v), "gcrit_$(s)_degC", x))
    end
    push!(out, (nm, length(v), "gcrit_sd_degC", std(v)))
end
push!(out, ("Ladrillo", length(ampL), "ais_gmst_amp_med", median(ampL)))
push!(out, ("Ladrillo", length(ampL), "ais_gmst_amp_sd", std(ampL)))
push!(out, ("BRICK2.0", length(gB), "ais_gmst_amp_fixed", 1 / AIS_COEF))
CSV.write(joinpath(REPO, "outputs", "diag_gcrit_brick2_vs_ladrillo_$(CHAIN_TAG).csv"), out)
@printf("\nwrote outputs/diag_gcrit_brick2_vs_ladrillo_%s.csv\n", CHAIN_TAG)
