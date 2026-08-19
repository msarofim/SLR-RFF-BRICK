## ============================================================================
## diag_iceflow0_propagation.jl — does the unmixed axis REACH the deliverable?
##
## THE QUESTION (Marcus, thread 3, after diag_block_ridge + the identifiability
## tests). `ais_iceflow0` is weakly identified and the four chains sit in
## different places at indistinguishable log-posteriors: R-hat 2.359, pooled
## marginal 0.65 of the prior, within-chain sd 0.49 of the pooled. That is a fact
## about the PARAMETER. Before spending anything on the sampler, the question
## that decides what to do is whether it is also a fact about the PROJECTION.
##
##   * SLR@2100 is certified converged (R-hat 1.000, between/within 0.009), so
##     2100 is not at risk whatever the parameter does.
##   * SLR@2150's chain-median spread is 15x that, relative to within-chain
##     scatter, and R-hat is MEAN-based so it reads 1.000 and does not see it.
##   * 2300 has never been checked across chains at all.
##
## If the axis does not propagate, `ais_iceflow0`'s R-hat is a REPORTING CAVEAT
## and the next calibration should spend its effort on the noise model instead.
## If it does, the sampler work is load-bearing.
##
## WHAT IS MEASURED
##   Per chain, 400 post-burn draws projected to 2300 on ssp245. Then, at each
##   horizon and for both the AIS component and the total:
##     1. the between-chain spread of the chain MEDIANS against the mean
##        within-chain sd -- the same ratio the acceptance certificate uses;
##     2. the same ratio at **p95**, because the AIS distribution is bimodal in
##        tipped/not-tipped and a median can agree while the tail does not. This
##        is the statistic R-hat cannot see, and it is where the risk lives;
##     3. the correlation and R^2 of the projection on that draw's `ais_iceflow0`
##        -- how much of the projection the axis actually explains.
##
## No tipping THRESHOLD is used anywhere: a threshold would have to be invented,
## and the quantile ladder answers the same question without one.
##
##   julia --project=julia_v2 julia/diag_iceflow0_propagation.jl [n_per_chain]
## ============================================================================
using CSV, DataFrames, Statistics, Printf

include(joinpath(@__DIR__, "ladrillo_projection.jl"))

const REPO     = LADRILLO_REPO
const SEEDS    = [2026, 2027, 2028, 2029]
const NITER    = 2000000
const NBURN    = 1000000
const TAG      = "L10"
const N_TARGET = length(ARGS) >= 1 ? parse(Int, ARGS[1]) : 400
const SSP      = "ssp245"
const Y0, Y1   = 1850, 2300
const HORIZONS = [2100, 2150, 2300]
const PARAM    = "ais_iceflow0"
## CONTROLS. r ~ 0 for a grounding-line flux coefficient is a surprising result,
## and a surprising result is presumptively an implementation problem: if the
## draw vector and the projection vector were misaligned, EVERY correlation would
## be ~0 and the headline would look exactly like this. These are parameters the
## AIS projection must depend on — the tipping threshold, the GMST->T_ant map,
## the fast-dynamics switch. If they also come back ~0, the pipeline is broken,
## not the physics.
const CONTROLS = ["antarctic_temp_threshold", "ais_gmst_amp", "antarctic_alpha",
                  "antarctic_gamma", "ais_mu"]
const COMPONENTS = [:ais, :total]
const OUT      = joinpath(REPO, "outputs/diag_iceflow0_propagation.csv")

chain_path(sd) = joinpath(REPO, "outputs/mcmc", "chain_$(TAG)_seed$(sd)_n$(NITER).csv")
hdr(sd) = String.(propertynames(CSV.read(chain_path(sd), DataFrame; limit = 0)))
for sd in SEEDS; isfile(chain_path(sd)) || error("missing chain $(chain_path(sd))"); end
const VARIANT = ladrillo_gis_variant(hdr(SEEDS[1]))

bf = ladrillo_setup(ssp = SSP, y0 = Y0, y1 = Y1, gis_variant = VARIANT)
@printf("Does %s reach the deliverable? | tag %s | %s | %d-%d | %d draws/chain\n",
        PARAM, TAG, SSP, Y0, Y1, N_TARGET)
@printf("  amp law ON (the shipped model) | rebaseline %d-%d\n\n",
        LADRILLO_REF[1], LADRILLO_REF[2])

## ---- project, per chain -------------------------------------------------
vals = Dict((c, y) => Vector{Float64}[] for c in COMPONENTS, y in HORIZONS)
par  = Vector{Float64}[]
ctl  = Dict{String,Vector{Float64}}[]
for sd in SEEDS
    need = vcat(ladrillo_used_cols(VARIANT), [PARAM]) |> unique
    df = CSV.read(chain_path(sd), DataFrame; select = need)
    step = max(1, (nrow(df) - NBURN) ÷ N_TARGET)
    draws = df[collect((NBURN + 1):step:nrow(df))[1:N_TARGET], :]
    df = nothing; GC.gc()

    v = Dict((c, y) => Float64[] for c in COMPONENTS, y in HORIZONS)
    t0 = time()
    for r in eachrow(draws)
        ladrillo_run_draw!(bf, r)
        for c in COMPONENTS
            s = ladrillo_series(bf, c)
            for y in HORIZONS
                push!(v[(c, y)], s[ladrillo_yi(bf, y)])
            end
        end
    end
    for k in keys(v); push!(vals[k], v[k]); end
    push!(par, Float64.(draws[!, PARAM]))
    push!(ctl, Dict(c => Float64.(draws[!, c]) for c in CONTROLS))
    @printf("  seed%d: %d draws in %.0fs  (%s p50 %.3f)\n",
            sd, N_TARGET, time() - t0, PARAM, median(par[end]))
end

## ---- the two ratios, and the regression ---------------------------------
q(v, p) = quantile(filter(isfinite, v), p)
out = DataFrame(component = String[], horizon = Int[],
                ratio_p50 = Float64[], ratio_p95 = Float64[],
                r_param = Float64[], r2_param = Float64[],
                med_lo = Float64[], med_hi = Float64[], mean_sd_wc = Float64[])

allpar = vcat(par...)
for c in COMPONENTS, y in HORIZONS
    ch = vals[(c, y)]
    meds  = [q(v, 0.50) for v in ch]
    p95s  = [q(v, 0.95) for v in ch]
    sd_wc = mean([std(filter(isfinite, v)) for v in ch])
    # p95 sampling noise is larger than the median's, so the p95 ratio is only
    # meaningful against the same within-chain scale -- reported, not tested.
    pooled = vcat(ch...)
    ok = isfinite.(pooled)
    r = cor(allpar[ok], pooled[ok])
    push!(out, (string(c), y, std(meds) / sd_wc, std(p95s) / sd_wc,
                r, r^2, minimum(meds), maximum(meds), sd_wc))
end
CSV.write(OUT, out)

@printf("\n%-8s %6s | %11s %11s | %8s %8s | %s\n",
        "comp", "year", "ratio@p50", "ratio@p95", "r", "R^2", "chain medians lo..hi (cm)")
for r in eachrow(out)
    @printf("%-8s %6d | %11.3f %11.3f | %+8.3f %8.3f | %.2f .. %.2f  (sd_wc %.2f)\n",
            r.component, r.horizon, r.ratio_p50, r.ratio_p95, r.r_param, r.r2_param,
            r.med_lo, r.med_hi, r.mean_sd_wc)
end

## ---- verdict -------------------------------------------------------------
tot = out[out.component .== "total", :]
worst_p50 = maximum(tot.ratio_p50)
worst_p95 = maximum(tot.ratio_p95)
worst_r2  = maximum(out[out.component .== "ais", :r2_param])
@printf("\n%s\n", "="^78)
@printf("Worst TOTAL between/within ratio: %.3f at the median, %.3f at p95\n",
        worst_p50, worst_p95)
@printf("Largest share of the AIS projection explained by %s: R^2 = %.3f\n",
        PARAM, worst_r2)
if worst_p95 < 0.5 && worst_r2 < 0.10
    println("VERDICT: the axis does NOT reach the deliverable. Its R-hat is a " *
            "REPORTING CAVEAT, not a defect to engineer away — spend the next " *
            "calibration's effort elsewhere.")
elseif worst_p95 >= 0.5
    println("VERDICT: the chains DISAGREE in the tail ($(round(worst_p95, digits=2)) " *
            "at p95). The axis reaches the deliverable where R-hat cannot see it; " *
            "the sampler work is load-bearing for 2150/2300.")
else
    println("VERDICT: medians and tails agree across chains, but $PARAM explains " *
            "R^2 = $(round(worst_r2, digits=3)) of the AIS projection — read the " *
            "table rather than a label.")
end
## ---- controls: does ANY parameter correlate, or is the pipeline broken? ----
@printf("\n%s\nCONTROLS — correlation with the AIS projection (alignment check)\n%s\n",
        "="^78, "="^78)
@printf("%-28s %9s %9s %9s\n", "parameter", "r@2100", "r@2150", "r@2300")
ctlmax = 0.0
for c in vcat([PARAM], CONTROLS)
    v = c == PARAM ? allpar : vcat([d[c] for d in ctl]...)
    rs = Float64[]
    for y in HORIZONS
        pooled = vcat(vals[(:ais, y)]...)
        ok = isfinite.(pooled)
        push!(rs, cor(v[ok], pooled[ok]))
    end
    global ctlmax
    c != PARAM && (ctlmax = max(ctlmax, maximum(abs.(rs))))
    @printf("%-28s %+9.3f %+9.3f %+9.3f%s\n", c, rs..., c == PARAM ? "   <- the axis" : "")
end
@printf("\nLargest |r| among controls: %.3f — %s\n", ctlmax,
        ctlmax > 0.20 ?
        "the pipeline DOES resolve parameter->projection dependence, so $PARAM's ~0 is real" :
        "NO parameter correlates; suspect a draw/projection ALIGNMENT BUG, not physics")

@printf("\nwrote %s\n", OUT)
