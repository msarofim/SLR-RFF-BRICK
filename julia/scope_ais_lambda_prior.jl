## ============================================================================
## scope_ais_lambda_prior.jl — what does the ssp585 AIS 2300 band do under a
##                             DEFENSIBLE ALTERNATIVE fast-dynamics prior?
##
## THE QUESTION. `diag_ais_block_propagation.jl` established that the ssp585 AIS
## 2300 spread (252 cm, 55% of the whole total) is 78% ONE parameter,
## `antarctic_lambda`, and that its posterior sits 0.027 prior sd from its prior
## mean -- i.e. the band is a PRIOR, not an inference. Handoff 2026-08-24b makes
## that prior priority 1. This file asks the propagation half of it.
##
## WHAT THE CURRENT PRIOR ACTUALLY IS. `outputs/param_priors.csv` rows
## `antarctic_lambda` / `antarctic_temp_threshold` are an INDEPENDENT-GAUSSIAN
## fit to the DAISfastdyn paleo ensemble
## (MimiBRICK .../DAISfastdyn_calibratedParameters_gamma_29Jan2017.nc, 800,000
## members), hard-truncated to a [lo, hi] box (calibrate_mcmc_ext.jl:1313
## returns -Inf outside). Verified against the ensemble: the lambda row
## reproduces the paleo marginal mean to 0.018 sd and sd to 2%. So the PROVENANCE
## is sound -- but the FIT is not the evidence, and it differs from it three ways:
##
##   (1) SHAPE. The paleo lambda marginal is right-skewed (skew +0.711); the
##       Gaussian is not. Median biased HIGH 6.2%, upper tail biased LOW:
##       p99 1.099x, p99.9 1.242x.
##   (2) TRUNCATION. The lambda box top sits at paleo pctile 99.10, deleting 7,167
##       of 800,000 members whose mean lambda is 2.18x the prior mean. Tcrit's box
##       cuts at pctile 0.96 / 98.96.
##   (3) CORRELATION. The paleo ensemble has corr(lambda, Tcrit) = +0.445; the
##       prior is independent. NB the SIGN on the deliverable: higher lambda means
##       faster once tipped (contrast +0.56 at ssp245) but higher Tcrit means
##       HARDER to tip (contrast -0.68), so a POSITIVE parameter correlation is a
##       NEGATIVE response correlation -- reinstating it should NARROW the band,
##       not widen it. Do not reason about this from the parameter sign alone.
##
## These do NOT all point the same way, which is exactly why this has to be
## MEASURED rather than argued: (1) and (2) raise the lambda tail, the Tcrit fit
## sits ABOVE the paleo marginal at 77 of 99 percentiles (median -15.591 vs
## -15.667, 0.18 prior sd) so the fitted prior is systematically HARDER to tip
## than the evidence, and (3) works against both.
## MimiBRICK's own stock calibrator offers a truncated-KDE alternative for these
## rows precisely because "many of the marginal paleo pdfs are not normally
## distributed" (create_log_posterior_brick.jl:20). Using the empirical marginal
## is not a new prior; it is the SAME evidence without the parametric detour --
## the `use real data when you have it` discipline in ~/.claude/CLAUDE.md.
##
## WHY THIS NEEDS NO REFIT. lambda and Tcrit are observationally unidentified
## over the historical window (calibrate_mcmc_ext.jl:1093: T_ant never crosses
## temperature_threshold), so their marginals sample the prior and a prior
## revision is propagatable at PROJECTION time -- the same status as `gis_amp`
## and the Greenland tap onset. Gate [INERT] below MEASURES that rather than
## assuming it.
##
## THE SWAP IS A MONOTONE TRANSPORT, NOT A RESAMPLE. Draw i's lambda is replaced
## by Q_paleo(F_truncGauss(lambda_i)). This is deterministic, adds ZERO Monte
## Carlo noise, and preserves each draw's rank -- so every other parameter stays
## paired with the draw it belongs to and the arm-to-arm difference is the prior
## change alone. A resample would confound it with sampling noise on 2000 draws.
## For the joint arm, Tcrit is transported by its paleo distribution CONDITIONAL
## on the new lambda (nearest-neighbour window in lambda), which reinstates the
## +0.445 paleo dependence without disturbing the marginal.
##
##   julia --project=julia_v2 julia/scope_ais_lambda_prior.jl [n_per_chain] [--tag=L14] [--maxrows=N]
## Writes outputs/scope_ais_lambda_prior_<tag>.csv
## ============================================================================
using CSV, DataFrames, Statistics, Printf, Distributions

include(joinpath(@__DIR__, "ladrillo_projection.jl"))

const REPO   = LADRILLO_REPO
const SEEDS  = [2026, 2027, 2028, 2029]
const NITER  = 2000000
const NBURN  = 1000000
const TAG    = let i = findfirst(a -> startswith(a, "--tag="), ARGS)
    i === nothing ? "L14" : ARGS[i][7:end]
end
const MAXROWS = let i = findfirst(a -> startswith(a, "--maxrows="), ARGS)
    i === nothing ? nothing : parse(Int, ARGS[i][11:end])
end
const SMOKE  = MAXROWS !== nothing
const N_TARGET = let p = findfirst(a -> !startswith(a, "--"), ARGS)
    p === nothing ? 500 : parse(Int, ARGS[p])
end
const SSPS      = ["ssp245", "ssp585"]
const Y0, Y1    = 1850, 2300
const HORIZONS  = [2100, 2150, 2300]
const COMPONENT = :ais
const LAM  = "antarctic_lambda"
const TCR  = "antarctic_temp_threshold"
const PALEO_CSV = joinpath(REPO, "data/dais_paleo/daisfastdyn_lambda_tcrit.csv")
const PRIORS_CSV = joinpath(REPO, "outputs/param_priors.csv")
## Width of the lambda neighbourhood used for the CONDITIONAL Tcrit transport, as a
## fraction of the paleo ensemble. 2% of 800,000 = 16,000 neighbours -- wide enough
## that the conditional quantile is not noise, narrow enough that corr(lambda,Tcrit)
## is resolved. Gate [COND] below checks the realised correlation against the paleo
## target rather than trusting the choice.
const COND_FRAC = 0.02
## Identity gate: the control arm must reproduce the shipped spread. Scaled to the
## band's own size rather than an absolute cm (tolerance_scaled_to_spread) -- but this
## IS an identity, so the tolerance is float-noise, not plausibility.
const IDENT_TOL_FRAC = 1e-10
const OUT = joinpath(REPO, "outputs",
                     "scope_ais_lambda_prior_$(TAG)$(SMOKE ? "_SMOKE" : "").csv")

## ---- the five arms -------------------------------------------------------
## `chain`     the shipped prior, untouched -- the identity control.
## `lam_box`   lambda -> paleo marginal RESTRICTED to the shipped [lo,hi] box.
##             Isolates the SHAPE error from the truncation.
## `lam_full`  lambda -> full paleo marginal. Shape + the deleted 0.90% tail.
## `tcr_full`  Tcrit  -> full paleo marginal, lambda untouched. Separates Tcrit's
##             own contribution, which the ranking says is rank 1 at ssp245.
## `joint`     both, with Tcrit conditional on the new lambda: the full paleo
##             evidence including corr = +0.445.
## `lam_pmin` / `lam_boxmax` / `lam_pmax` are DETERMINISTIC ENVELOPE arms: every draw
##             gets the same lambda -- the paleo ensemble minimum, the shipped prior
##             box top, and the paleo ensemble maximum. They do not represent any
##             candidate prior. They answer the question a candidate prior cannot:
##             what is the MOST and LEAST any lambda revision can do while staying
##             inside the DAISfastdyn paleo support? Reporting the envelope rather
##             than one alternative is the `report the RANKING of knobs` discipline
##             from memory `npv_retires_tau` applied to a prior instead of a cell.
const ARMS = ["chain", "lam_box", "lam_full", "tcr_full", "joint",
              "lam_pmin", "lam_boxmax", "lam_pmax"]
## The three envelope levels, named so the labels below derive from them.
const LAM_PMIN_SRC   = "paleo ensemble minimum"
const LAM_BOXMAX_SRC = "shipped prior box top (param_priors.csv hi)"
const LAM_PMAX_SRC   = "paleo ensemble maximum"

chain_path(sd) = joinpath(REPO, "outputs/mcmc", "chain_$(TAG)_seed$(sd)_n$(NITER).csv")
hdr(sd) = String.(propertynames(CSV.read(chain_path(sd), DataFrame; limit = 0)))
for sd in SEEDS; isfile(chain_path(sd)) || error("missing chain $(chain_path(sd))"); end
const VARIANT = ladrillo_gis_variant(hdr(SEEDS[1]))

@printf("AIS fast-dynamics PRIOR propagation | tag %s%s | %d draws/chain x %d chains\n",
        TAG, SMOKE ? "  ** SMOKE (--maxrows=$(MAXROWS)) **" : "", N_TARGET, length(SEEDS))
@printf("  arms: %s\n", join(ARMS, ", "))
flush(stdout)

## ---- the shipped prior, read from the file the calibrator reads -----------
const PRI = CSV.read(PRIORS_CSV, DataFrame)
prow(n) = PRI[findfirst(==(n), PRI.param), :]
gauss(n) = (r = prow(n); truncated(Normal(r.mean, r.std), r.lo, r.hi))
const G_LAM = gauss(LAM)
const G_TCR = gauss(TCR)

## ---- the paleo evidence --------------------------------------------------
const PALEO = CSV.read(PALEO_CSV, DataFrame)
const P_LAM = Float64.(PALEO.lambda)
const P_TCR = Float64.(PALEO.Tcrit)
const NP_ALL = length(P_LAM)
const LAM_LO, LAM_HI = prow(LAM).lo, prow(LAM).hi
const BOXMASK = (P_LAM .>= LAM_LO) .& (P_LAM .<= LAM_HI)
const P_LAM_BOX = sort(P_LAM[BOXMASK])
const P_LAM_SORTED = sort(P_LAM)
const P_TCR_SORTED = sort(P_TCR)
## lambda-ordered view, for the conditional Tcrit transport
const LORD = sortperm(P_LAM)
const P_LAM_ORD = P_LAM[LORD]
const P_TCR_ORD = P_TCR[LORD]

@printf("  paleo ensemble n=%d | corr(lambda,Tcrit) = %+.4f | lambda box keeps %.3f%%\n",
        NP_ALL, cor(P_LAM, P_TCR), 100 * count(BOXMASK) / NP_ALL)
@printf("  lambda envelope: %s %.6f | %s %.6f | %s %.6f\n",
        LAM_PMIN_SRC, minimum(P_LAM), LAM_BOXMAX_SRC, LAM_HI, LAM_PMAX_SRC, maximum(P_LAM))

"""Empirical quantile of a PRE-SORTED vector at u in (0,1), linear interpolation."""
function eq(sorted::Vector{Float64}, u::Float64)
    n = length(sorted)
    h = clamp(u, 0.0, 1.0) * (n - 1) + 1
    lo = floor(Int, h); hi = min(lo + 1, n)
    sorted[lo] + (h - lo) * (sorted[hi] - sorted[lo])
end

"""Tcrit's paleo quantile at level u, CONDITIONAL on lambda = l: the empirical
quantile within the nearest `COND_FRAC` of the ensemble in lambda. searchsorted on
the lambda-ordered copy makes this O(log n + window)."""
function eq_tcr_given_lam(l::Float64, u::Float64)
    w = max(200, round(Int, COND_FRAC * NP_ALL))
    i = searchsortedfirst(P_LAM_ORD, l)
    a = clamp(i - w ÷ 2, 1, NP_ALL - w + 1)
    win = sort(P_TCR_ORD[a:(a + w - 1)])
    eq(win, u)
end

"""Read N_TARGET post-burn draws from one chain, in the coordinates the kernel wants."""
function read_draws(sd)
    need = vcat(ladrillo_used_cols(VARIANT), [LAM, TCR]) |> unique
    h = hdr(sd)
    rd = ladrillo_gis_needs_native(h) ?
        vcat(setdiff(need, LADRILLO_GIS_SLOW_NATIVE_COLS),
             LADRILLO_GIS_SLOW_REPARAM_COLS) |> unique : need
    miss = setdiff(rd, h)
    isempty(miss) || error("chain_$(TAG)_seed$(sd) is missing: " * join(miss, ", "))
    df = SMOKE ? CSV.read(chain_path(sd), DataFrame; select = rd, limit = MAXROWS) :
                 CSV.read(chain_path(sd), DataFrame; select = rd)
    nb = SMOKE ? 0 : NBURN
    step = max(1, (nrow(df) - nb) ÷ N_TARGET)
    idx = collect((nb + 1):step:nrow(df))
    length(idx) >= N_TARGET || error("only $(length(idx)) draws available; lower n_per_chain")
    draws = ladrillo_native_greenland!(df[idx[1:N_TARGET], :])
    df = nothing; GC.gc()
    return draws
end

const DRAWS = [(@printf("  reading chain seed%d ...\n", sd); flush(stdout); read_draws(sd))
               for sd in SEEDS]

## ---- build the transported columns ---------------------------------------
"""Return (lambda, Tcrit) vectors for one arm, transported from the chain's own."""
function arm_cols(arm::String, lam::Vector{Float64}, tcr::Vector{Float64})
    arm == "chain" && return (copy(lam), copy(tcr))
    u_l = cdf.(G_LAM, lam)
    u_t = cdf.(G_TCR, tcr)
    if arm == "lam_box"
        return ([eq(P_LAM_BOX, u) for u in u_l], copy(tcr))
    elseif arm == "lam_full"
        return ([eq(P_LAM_SORTED, u) for u in u_l], copy(tcr))
    elseif arm == "tcr_full"
        return (copy(lam), [eq(P_TCR_SORTED, u) for u in u_t])
    elseif arm == "joint"
        nl = [eq(P_LAM_SORTED, u) for u in u_l]
        return (nl, [eq_tcr_given_lam(nl[i], u_t[i]) for i in eachindex(nl)])
    elseif arm == "lam_pmin"
        return (fill(minimum(P_LAM), length(lam)), copy(tcr))
    elseif arm == "lam_boxmax"
        return (fill(LAM_HI, length(lam)), copy(tcr))
    elseif arm == "lam_pmax"
        return (fill(maximum(P_LAM), length(lam)), copy(tcr))
    end
    error("unknown arm $arm")
end

## ---- GATES ---------------------------------------------------------------
const ALL_LAM = vcat([Float64.(d[!, LAM]) for d in DRAWS]...)
const ALL_TCR = vcat([Float64.(d[!, TCR]) for d in DRAWS]...)

@printf("\n%s\nGATES\n%s\n", repeat("=", 78), repeat("=", 78))

## [INERT] If lambda/Tcrit are truly likelihood-inert, the POSTERIOR marginal must
## be the PRIOR. Measured, not assumed: the max |CDF| gap over a 99-point grid
## (a Kolmogorov-Smirnov statistic against the analytic truncated Gaussian).
function ks_vs(g, x::Vector{Float64})
    xs = sort(x); n = length(xs)
    maximum(abs(cdf(g, xs[i]) - i / n) for i in 1:n)
end
ks_l = ks_vs(G_LAM, ALL_LAM); ks_t = ks_vs(G_TCR, ALL_TCR)
crit = 1.36 / sqrt(length(ALL_LAM))   # KS 5% critical value, n draws
@printf("[INERT] posterior-vs-prior KS: lambda %.4f | Tcrit %.4f | 5%% crit %.4f (n=%d)\n",
        ks_l, ks_t, crit, length(ALL_LAM))
@printf("        %s\n", (ks_l < crit && ks_t < crit) ?
        "both INDISTINGUISHABLE from the prior => inert, prior-propagatable" :
        "** at least one differs from its prior -- the swap is NOT a pure prior move **")

## [INDEP] The transport replaces lambda draw-by-draw. That is only valid if lambda
## carries no posterior dependence on the parameters left alone.
## ⚠ `intersect` OMITS rather than raises, so a chain missing a used column silently
## SHRINKS this scan and the max below is then a max over fewer parameters -- a
## looked-at-less null reported as a looked-and-found-nothing (`no_power_null`,
## `intersect_is_a_silent_default`). The coverage is therefore printed, and a missing
## column is named rather than dropped.
const OTHERS = intersect(names(DRAWS[1]), ladrillo_used_cols(VARIANT))
let miss = setdiff(ladrillo_used_cols(VARIANT), names(DRAWS[1]))
    @printf("[INDEP] scanning %d of %d used parameters%s\n", length(OTHERS),
            length(ladrillo_used_cols(VARIANT)),
            isempty(miss) ? "" : "  ⚠ ABSENT FROM THE CHAIN: " * join(miss, ", "))
end
let maxr = 0.0, maxn = ""
    for c in OTHERS
        c in (LAM, TCR) && continue
        v = Float64.(vcat([d[!, c] for d in DRAWS]...))
        (std(v) == 0 || !all(isfinite, v)) && continue
        r = abs(cor(ALL_LAM, v))
        if r > maxr; maxr = r; maxn = c; end
    end
    @printf("[INDEP] max |corr(lambda, any other used param)| = %.4f  (%s)\n", maxr, maxn)
end

## [COND] The conditional transport must reinstate the paleo correlation.
let (nl, nt) = arm_cols("joint", ALL_LAM, ALL_TCR)
    @printf("[COND]  joint arm corr(lambda,Tcrit) = %+.4f  vs paleo %+.4f  (chain %+.4f)\n",
            cor(nl, nt), cor(P_LAM, P_TCR), cor(ALL_LAM, ALL_TCR))
end
flush(stdout)

## ---- run -----------------------------------------------------------------
out = DataFrame(scenario = String[], horizon = Int[], arm = String[], n = Int[],
                median_cm = Float64[], p05_cm = Float64[], p95_cm = Float64[],
                p99_cm = Float64[], spread_p05_p95_cm = Float64[],
                lam_median = Float64[], lam_p95 = Float64[], lam_max = Float64[],
                tcr_median = Float64[], tcr_p95 = Float64[])

for ssp in SSPS
    bf = ladrillo_setup(ssp = ssp, y0 = Y0, y1 = Y1, gis_variant = VARIANT)
    for arm in ARMS
        proj = Dict(y => Float64[] for y in HORIZONS)
        lamv = Float64[]; tcrv = Float64[]
        t0 = time()
        for d in DRAWS
            dd = copy(d)
            nl, nt = arm_cols(arm, Float64.(dd[!, LAM]), Float64.(dd[!, TCR]))
            dd[!, LAM] = nl; dd[!, TCR] = nt
            append!(lamv, nl); append!(tcrv, nt)
            for r in eachrow(dd)
                ladrillo_run_draw!(bf, r)
                s = ladrillo_series(bf, COMPONENT)
                for y in HORIZONS; push!(proj[y], s[ladrillo_yi(bf, y)]); end
            end
        end
        for y in HORIZONS
            v = proj[y]
            push!(out, (ssp, y, arm, length(v), median(v),
                        quantile(v, 0.05), quantile(v, 0.95), quantile(v, 0.99),
                        quantile(v, 0.95) - quantile(v, 0.05),
                        median(lamv), quantile(lamv, 0.95), maximum(lamv),
                        median(tcrv), quantile(tcrv, 0.95)))
        end
        @printf("  %s / %-9s : %d draws in %5.0fs | 2300 median %7.2f  p05-p95 %7.2f cm\n",
                ssp, arm, length(proj[2300]), time() - t0,
                median(proj[2300]), quantile(proj[2300], 0.95) - quantile(proj[2300], 0.05))
        flush(stdout)
    end
end

CSV.write(OUT, out)
@printf("\nwrote %s\n", relpath(OUT, REPO))

## ---- [IDENT] the control arm must reproduce the shipped propagation -------
const SHIPPED = joinpath(REPO, "outputs", "diag_ais_block_propagation_$(TAG).csv")
if isfile(SHIPPED) && !SMOKE
    sh = CSV.read(SHIPPED, DataFrame)
    @printf("\n[IDENT] control arm vs %s\n", basename(SHIPPED))
    for ssp in SSPS, y in HORIZONS
        a = out[(out.scenario .== ssp) .& (out.horizon .== y) .& (out.arm .== "chain"), :]
        b = sh[(sh.scenario .== ssp) .& (sh.horizon .== y), :]
        isempty(b) && continue
        d = abs(a.spread_p05_p95_cm[1] - b.spread_p05_p95_cm[1]) / b.spread_p05_p95_cm[1]
        @printf("        %s @%d  %8.3f vs %8.3f cm  rel %.2e  %s\n", ssp, y,
                a.spread_p05_p95_cm[1], b.spread_p05_p95_cm[1], d,
                d < IDENT_TOL_FRAC ? "IDENTICAL" :
                "** DIFFERS -- expected if n_per_chain differs from that run **")
    end
end

## ---- the headline --------------------------------------------------------
@printf("\n%s\nWHAT THE PRIOR IS WORTH (AIS component, cm)\n%s\n",
        repeat("=", 78), repeat("=", 78))
for ssp in SSPS, y in HORIZONS
    base = out[(out.scenario .== ssp) .& (out.horizon .== y) .& (out.arm .== "chain"), :]
    @printf("\n%s @%d   control: median %.2f  p05-p95 %.2f  p95 %.2f  p99 %.2f\n",
            ssp, y, base.median_cm[1], base.spread_p05_p95_cm[1], base.p95_cm[1], base.p99_cm[1])
    for arm in ARMS[2:end]
        a = out[(out.scenario .== ssp) .& (out.horizon .== y) .& (out.arm .== arm), :]
        @printf("  %-9s median %7.2f (%+6.2f)  spread %7.2f (x%.3f)  p95 %7.2f (x%.3f)  p99 %7.2f (x%.3f)\n",
                arm, a.median_cm[1], a.median_cm[1] - base.median_cm[1],
                a.spread_p05_p95_cm[1], a.spread_p05_p95_cm[1] / base.spread_p05_p95_cm[1],
                a.p95_cm[1], a.p95_cm[1] / base.p95_cm[1],
                a.p99_cm[1], a.p99_cm[1] / base.p99_cm[1])
    end
end
