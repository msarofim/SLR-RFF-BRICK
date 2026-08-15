## ============================================================================
## diag_r19_modern_rate.jl — measure the R19 block's 2000-2024 modern melt rate
## on a posterior, and score it against the GlaMBIE observation.
##
## WHY THIS EXISTS. The L11 change set was built to fix L10's R19 sitting 3x
## above GlaMBIE. A 200k single-chain diagnostic (D2chk3) said it OVERCORRECTED:
## the point estimate went from ~3x too high to ~9x too LOW, with the 5-95%
## reaching 0.0000, while IMPROVING in sigma terms (+0.88 -> -0.38). That
## measurement was made ad hoc and never committed, so the re-measurement its own
## caveat demanded ("single common-start 200k diagnostic chain, not converged,
## and R19 is weakly identified -- indicative, not definitive") had nothing to
## run. This is that script.
##
## THE QUANTITY is the calibrator's own, not a re-derivation: the likelihood
## scores `1000*(gsic_r19[2024] - gsic_r19[2000])/24` in mm/yr against
## N(R19_RATE_MU, R19_RATE_SD) (calibrate_mcmc_ext.jl, the R19_RATE_ON block).
## Two things differ here and BOTH are unit/coordinate traps:
##   * `ladrillo_series` returns CENTIMETRES (metres x100, ladrillo_rebase),
##     while the calibrator reads the raw metres. The factor is therefore 10,
##     NOT the calibrator's 1000. A copied 1000 gives a 100x wrong answer that
##     still looks like a plausible melt rate to a reader who is not checking.
##   * The rate is a DIFFERENCE, so `ladrillo_rebase`'s subtraction of the
##     1995-2014 mean cancels exactly. Re-referencing does not enter.
##
## COORDINATES. An L11+ posterior carries the Greenland slow channel as
## (gis_slow_ell, gis_slow_w); the projection kernel wants the native
## (gis_alpha_s, gis_beta_s). We map back through the calibrator's own transform
## (alpha_s = w*exp(ell)/Tbar, beta_s = (1-w)*exp(ell)). R19 does not depend on
## Greenland, so this does not change the answer -- it is done so the draw
## applied to the model is a COMPLETE, valid draw rather than one with a
## silently unset Greenland slot.
##
## VALIDATION. Run on the L10 canonical posterior it must reproduce L10's
## recorded modern rate of ~0.15 mm/yr (0.1513, handoff 2026-08-15 section 5;
## 0.1490 [0.0544, 0.2300] as measured in design_2026-08-14_r19_replacement_term
## section 4). `--check-l10` asserts this and is the guard against exactly the
## unit and coordinate traps above.
##
##   julia --project=julia_v2 julia/diag_r19_modern_rate.jl --check-l10
##   julia --project=julia_v2 julia/diag_r19_modern_rate.jl --posterior=PATH [n]
##   julia --project=julia_v2 julia/diag_r19_modern_rate.jl --chain-glob=L11 [n]
## Writes outputs/diag_r19_modern_rate.csv (one row per source).
## ============================================================================

using CSV, DataFrames, Mimi, Printf, Statistics
include(joinpath(@__DIR__, "ladrillo_projection.jl"))

## ---- the constraint, mirrored from calibrate_mcmc_ext.jl ------------------
const RATE_Y0, RATE_Y1 = 2000, 2024          # GLAMBIE_I0 / GLAMBIE_I1
const RATE_SPAN        = RATE_Y1 - RATE_Y0   # GLAMBIE_SPAN = 24
const R19_RATE_MU      = 0.049251            # GlaMBIE R19, mm SLE/yr over 2000-2024
const R19_RATE_SD      = 0.11615             # serially-correlated sigma; SUPERSEDES
                                             # GLAMBIE_ERR_INFLATE, does not compound
const CM_TO_MM         = 10.0                # ladrillo_series is cm; see header
const L10_ANCHOR       = 0.1513              # recorded L10 modern rate, mm/yr
const L10_ANCHOR_TOL   = 0.030               # generous: the anchor itself was quoted
                                             # at 0.1513 and 0.1490 from two draw sets
const NDRAW_DEFAULT    = 400
const SSP              = "ssp245"            # the calibration driver is ssp245harm;
                                             # 2000-2024 is observed, so scenario is inert
const OUT = joinpath(LADRILLO_REPO, "outputs/diag_r19_modern_rate.csv")

_argval(pfx) = (i = findfirst(a -> startswith(a, pfx), ARGS);
                i === nothing ? nothing : ARGS[i][length(pfx)+1:end])
const NDRAW = let p = filter(a -> !startswith(a, "--"), ARGS)
    isempty(p) ? NDRAW_DEFAULT : parse(Int, p[1])
end

## The (ell, w) -> native (alpha_s, beta_s) map lives in ladrillo_projection.jl
## as `ladrillo_native_greenland!`, with `LADRILLO_GIS_TBAR` recomputed from the
## driver under the calibrator's own 1.963 K assertion. It is deliberately NOT
## duplicated here: two implementations of one transform is how they drift apart.

"""Thin to `n` rows over the POST-BURN half. Chains are stored in sample order,
so taking the 2nd half first is what makes this a posterior rather than a
transient; a subsample CSV is already post-burn and is thinned whole."""
function load_draws(path::AbstractString; n::Int=NDRAW, burn::Bool)
    df = CSV.read(path, DataFrame)
    burn && (df = df[(nrow(df) ÷ 2 + 1):end, :])
    step = max(1, nrow(df) ÷ n)
    df = df[1:step:end, :][1:min(n, length(1:step:nrow(df))), :]
    return ladrillo_native_greenland!(df)
end

"""The 2000-2024 mean R19 rate, mm/yr, one value per draw."""
function r19_rates(df::DataFrame)
    bf = ladrillo_setup(ssp=SSP, y0=1850, y1=2300, gis_ab=true)
    i0 = ladrillo_yi(bf, RATE_Y0); i1 = ladrillo_yi(bf, RATE_Y1)
    (i0 === nothing || i1 === nothing) && error("years $RATE_Y0/$RATE_Y1 not in the run window")
    out = Float64[]
    for r in eachrow(df)
        ladrillo_run_draw!(bf, r)
        s = ladrillo_series(bf, :gsic_r19)
        push!(out, CM_TO_MM * (s[i1] - s[i0]) / RATE_SPAN)
    end
    return out
end

function report(label::AbstractString, path::AbstractString; burn::Bool)
    df = load_draws(path; burn=burn)
    v  = r19_rates(df)
    p50, lo, hi = median(v), quantile(v, 0.05), quantile(v, 0.95)
    nsig = (p50 - R19_RATE_MU) / R19_RATE_SD
    @printf("%-22s n=%4d  rate %.4f [%.4f, %.4f] mm/yr   vs GlaMBIE %.4f: %+.2f sigma  (%.2fx)\n",
            label, length(v), p50, lo, hi, R19_RATE_MU, nsig, p50 / R19_RATE_MU)
    return (source=label, path=basename(path), ndraw=length(v), p05=lo, p50=p50, p95=hi,
            glambie_mu=R19_RATE_MU, glambie_sd=R19_RATE_SD, n_sigma=nsig,
            ratio_to_glambie=p50 / R19_RATE_MU)
end

rows = NamedTuple[]

@printf("R19 modern rate %d-%d | GlaMBIE %.4f +/- %.4f mm/yr | Tbar %.4f K\n",
        RATE_Y0, RATE_Y1, R19_RATE_MU, R19_RATE_SD, LADRILLO_GIS_TBAR)

if "--check-l10" in ARGS
    ## The unit/coordinate guard. L10 is the NATIVE-Greenland posterior, so this
    ## also exercises the branch where ladrillo_native_greenland! is a no-op.
    r = report("L10 (anchor)", LADRILLO_POSTERIOR_CSV; burn=false)
    push!(rows, r)
    if abs(r.p50 - L10_ANCHOR) > L10_ANCHOR_TOL
        error("ANCHOR FAILED: L10 gives $(round(r.p50, digits=4)) mm/yr, expected " *
              "$L10_ANCHOR +/- $L10_ANCHOR_TOL. Suspect the cm-vs-m factor " *
              "($CM_TO_MM) or the draw wiring BEFORE trusting any other row.")
    end
    println("  anchor OK (|Δ| = $(round(abs(r.p50 - L10_ANCHOR), digits=4)) <= $L10_ANCHOR_TOL)")
end

let p = _argval("--posterior=")
    p !== nothing && push!(rows, report("posterior", p; burn=false))
end

let g = _argval("--chain-glob=")
    if g !== nothing
        cs = sort(filter(f -> occursin(Regex("chain_$(g)_seed\\d+_n\\d+\\.csv\$"), f),
                         readdir(joinpath(LADRILLO_REPO, "outputs/mcmc"), join=true)))
        isempty(cs) && error("no chains matched chain_$(g)_seed*_n*.csv")
        ## Per chain AND pooled: a pooled median hides a between-chain split, and
        ## R19 is weakly identified — exactly the case where chains can disagree
        ## about where on a ridge they sit. Report both or report nothing.
        all = Float64[]
        for c in cs
            df = load_draws(c; burn=true)
            v = r19_rates(df); append!(all, v)
            p50 = median(v)
            @printf("%-22s n=%4d  rate %.4f [%.4f, %.4f] mm/yr   vs GlaMBIE: %+.2f sigma\n",
                    "  " * replace(basename(c), r"chain_|_n\d+\.csv" => ""), length(v), p50,
                    quantile(v, 0.05), quantile(v, 0.95), (p50 - R19_RATE_MU) / R19_RATE_SD)
            push!(rows, (source="chain:" * basename(c), path=basename(c), ndraw=length(v),
                         p05=quantile(v, 0.05), p50=p50, p95=quantile(v, 0.95),
                         glambie_mu=R19_RATE_MU, glambie_sd=R19_RATE_SD,
                         n_sigma=(p50 - R19_RATE_MU) / R19_RATE_SD,
                         ratio_to_glambie=p50 / R19_RATE_MU))
        end
        p50 = median(all)
        @printf("%-22s n=%4d  rate %.4f [%.4f, %.4f] mm/yr   vs GlaMBIE %.4f: %+.2f sigma  (%.2fx)\n",
                "$g POOLED", length(all), p50, quantile(all, 0.05), quantile(all, 0.95),
                R19_RATE_MU, (p50 - R19_RATE_MU) / R19_RATE_SD, p50 / R19_RATE_MU)
        push!(rows, (source="$g POOLED", path="pooled", ndraw=length(all),
                     p05=quantile(all, 0.05), p50=p50, p95=quantile(all, 0.95),
                     glambie_mu=R19_RATE_MU, glambie_sd=R19_RATE_SD,
                     n_sigma=(p50 - R19_RATE_MU) / R19_RATE_SD,
                     ratio_to_glambie=p50 / R19_RATE_MU))
    end
end

isempty(rows) && error("nothing to do: pass --check-l10, --posterior=PATH or --chain-glob=TAG")
CSV.write(OUT, DataFrame(rows))
println("Wrote $(relpath(OUT, LADRILLO_REPO))")
