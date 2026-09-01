## scope_amp_likelihood_tilt.jl — WHY DID THE OLD GLACIER LAW MOVE amp's CENTRE BUT NOT ITS WIDTH?
##
## §7 item 4 of handoff_2026-09-01. The champion's promotion reasoning (champions.json, all six
## modules) rests on a 2x2 showing the glacier law moves `ais_gmst_amp` by 1.43 prior sd. The
## MECHANISM is unexplained, and there is an apparent tension with §3: amplification is reported
## PRIOR-DOMINATED (posterior sd / prior sd = 0.97-0.99) yet the likelihood moved its centre.
##
## THE HYPOTHESIS UNDER TEST (Claude 2026-09-01, not from the literature): if the log-likelihood
## is locally LINEAR in amp over the prior's support -- a TILT, not a curvature -- then
## exp(linear) x Gaussian is Gaussian with the SAME sd and a shifted mean. Shift without
## sharpening is exactly that signature. Laplace, with ll ~ ll0 + s*(a-mu) + c/2*(a-mu)^2:
##
##     posterior precision = 1/sigma^2 - c        sd_post/sd_prior = 1/sqrt(1 - c*sigma^2)
##     posterior mean      = mu + s*sigma^2/(1 - c*sigma^2)
##
## So the measured L21 shift (-0.1431 at sigma=0.10) and width ratio (~0.98) PREDICT
## s ~ -15 per unit amp and c ~ -4 under the OLD law, and s ~ 0 under the NEW law (L23 sits on
## the prior). Both are falsifiable here.
##
## ⚠ THIS IS A CONDITIONAL PROFILE AT FIXED PARAMETERS, NOT A MARGINAL -- same caveat as
## scope_ais_anchor_identification.jl. Every other parameter is held at the draw's value, so the
## curvature is an UPPER bound on identification and the absolute magnitudes are not the
## marginal ones. The OLD-vs-NEW comparison of the SLOPE, at identical theta, is the robust part.
##
## THE LAW IS SWITCHED BY ENV VARS injected into the glacier components in this INSTRUMENTED
## WORKTREE ONLY (nothing tracked in the main repo is edited):
##     AMPPROF_R=1.0|Inf      regrowth cap; Inf = no regrowth = the melt-only ratchet
##     AMPPROF_FLOOR=1|0      S_eq = max(.,0) on or off
## OLD LAW (a0155bf^) == R=Inf AND FLOOR=0, verified algebraically: old `exc = max(T-T_eq,0)`
## zeroes the step on cooling exactly as `mult /= Inf` does, and old S_eq was unfloored.
##
##   AMPPROF_R=Inf AMPPROF_FLOOR=0 julia --project=julia_v2 julia/scope_amp_likelihood_tilt.jl
## Writes outputs/scope_amp_likelihood_tilt_<arm>.csv
empty!(ARGS); append!(ARGS, ["2000", "2026", "--tag=AMPPROF", "--gis-ordered", "--gis-basins2"])
include(joinpath(@__DIR__, "calibrate_mcmc_ext.jl"))
using Printf, Statistics, CSV, DataFrames, Distributions

const ARM   = "$(get(ENV,"AMPPROF_VINT","L23"))_R$(get(ENV,"AMPPROF_R","1.0"))_F$(get(ENV,"AMPPROF_FLOOR","1"))"
const VINT   = get(ENV, "AMPPROF_VINT", "L23")
const SUBCSV = joinpath(REPO, "data/MimiBRICK/parameters_subsample_brick_mengel_$(VINT).csv")
const NDRAW  = parse(Int, get(ENV, "AMPPROF_NDRAW", "9"))
const NGRID  = parse(Int, get(ENV, "AMPPROF_NGRID", "41"))

sub = CSV.read(SUBCSV, DataFrame)
## ⚠ MATCH BY NAME, NEVER BY POSITION, and ASSERT absence rather than intersect() it away.
## A silently-narrowed column set here would seed one parameter with another's value -- the
## exact failure the calibrator's own adapted_cov header comment records (L13's ais_c).
miss = setdiff(pn0, names(sub))
isempty(miss) || error("subsample is missing $(length(miss)) sampled parameters: $(miss)")
@printf("ARM %s   subsample %d draws x %d params (all %d sampled names present)\n",
        ARM, nrow(sub), ncol(sub), length(pn0))

## base thetas: the column-wise MEDIAN draw, then NDRAW-1 spread draws at fixed stride
nextra = max(NDRAW - 1, 0)
extra  = nextra == 0 ? Int[] :
         nextra == 1 ? [nrow(sub) ÷ 2] :
         unique(round.(Int, range(1, nrow(sub), length=nextra)))
rows = vcat(0, extra)
amps = collect(range(AMP_LO + 1e-6, AMP_HI - 1e-6, length=NGRID))
out  = DataFrame(draw=Int[], amp=Float64[], ll=Float64[], logpost=Float64[])

for (di, r) in enumerate(rows)
    θ = r == 0 ? [median(sub[!, nm]) for nm in pn0] : [Float64(sub[r, nm]) for nm in pn0]
    base = logposterior(copy(θ))
    isfinite(base) || (@printf("  draw %d: logposterior not finite at its own value — SKIPPED\n", di); continue)
    for a in amps
        θ[AMP_IDX] = a
        lp = logposterior(copy(θ))
        ## strip the amp prior analytically; every OTHER prior term is constant in amp, so it
        ## shifts the profile without changing slope or curvature.
        ll = lp - logpdf(Normal(AMP_MU, AMP_SIGMA), a)
        push!(out, (di, a, ll, lp))
    end
    @printf("  draw %-2d done (%d grid points)\n", di, NGRID)
end

## ---- POWER CHECK (no_power_null): the law's effect is only meaningful against the ll
## response to a perturbation the likelihood DEMONSTRABLY sees. Perturb each glacier
## parameter by 1% and report |dll| -- if these are also ~1e-5 the glacier block is not
## wired into this likelihood and the whole measurement is void.
θp = [median(sub[!, nm]) for nm in pn0]
ll0 = logposterior(copy(θp))
println("\nPOWER CHECK — |dll| for a 1% perturbation of each glacier parameter:")
for (k, nm) in enumerate(pn0)
    startswith(nm, "gic_") || continue
    θq = copy(θp); θq[k] *= 1.01
    d = abs(logposterior(θq) - ll0)
    @printf("  %-22s |dll| = %.3e\n", nm, d)
end
@printf("  %-22s |dll| = %.3e\n", "ais_gmst_amp +1%", abs(logposterior((q=copy(θp); q[AMP_IDX]*=1.01; q)) - ll0))

CSV.write(joinpath(REPO, "outputs", "scope_amp_likelihood_tilt_$(ARM).csv"), out)
@printf("\nwrote outputs/scope_amp_likelihood_tilt_%s.csv  (%d rows)\n", ARM, nrow(out))
