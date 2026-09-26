## ============================================================================
## diag_ais_block_propagation.jl — PRICE every AIS parameter against the deliverable
##
## THE QUESTION. Handoff 2026-08-24 makes Antarctica the priority: 54.8% of the
## ssp585 2300 total, 9.4x Greenland's spread, the only component still on stock
## MimiBRICK, and the block that fails to converge. Before any of that can be
## acted on, the same question that retired tau for Greenland has to be asked of
## the whole AIS block: WHICH knobs actually move the deliverable, and are those
## the ones that mix badly? Memory `npv_retires_tau` is explicit that the useful
## output is a RANKING of knobs, not one knob's sensitivity.
##
## `diag_iceflow0_propagation.jl` asked this for ONE parameter and answered it --
## `ais_iceflow0` explains R^2 = 0.004 of the AIS projection, so its R-hat is a
## reporting caveat. But its CONTROLS list was five parameters chosen to check
## that the pipeline resolves any dependence at all, not to rank the block. Eleven
## of the seventeen sampled AIS parameters have never been measured against the
## projection. This file measures all of them.
##
## TWO EFFECT SIZES, BECAUSE ONE OF THEM IS KNOWN TO BE MISLEADING HERE.
##   * Pearson r / R^2, comparable with the earlier file's numbers.
##   * DECILE CONTRAST: median(projection | param in its top decile) minus
##     median(projection | bottom decile), reported as a FRACTION OF THE
##     PROJECTION'S OWN p05-p95. The AIS 2100 distribution is bimodal in
##     tipped/not-tipped (handoff sec 4), and a linear correlation across a
##     bimodal response understates a parameter that moves the MIXTURE WEIGHT
##     rather than the level. The contrast is rank-based on the parameter and
##     quantile-based on the response, so it survives that; and expressing it
##     against the sampled spread is the tolerance-scaling discipline from memory
##     `tolerance_scaled_to_spread` -- a raw cm move means nothing without the
##     spread it is being compared to.
##   * Spearman rho as well, so a monotone-but-curved dependence is not read as
##     absence through Pearson alone.
## Where the two disagree, THAT IS THE RESULT: it localises a parameter acting on
## the tipping probability rather than on the trajectory.
##
## BOTH SCENARIOS. ssp245 is what diag_iceflow0_propagation.jl used; ssp585 is
## where AIS is 55% of the total, and the AIS reservoir/threshold parameters are
## exactly the kind that can be inert in one scenario and dominant in the other
## (the Greenland onset behaved that way). Reporting one alone would be a
## scenario-specific claim dressed as a block property.
##
## Cross this against outputs/mcmc/ais_block_convergence_<tag>.csv: a parameter
## that fails R-hat AND carries a large decile contrast is load-bearing; one that
## fails R-hat with no contrast is a reporting caveat, as ais_iceflow0 already is.
##
##   julia --project=julia_v2 julia/diag_ais_block_propagation.jl [n_per_chain] [--tag=L14]
## Writes outputs/diag_ais_block_propagation_<tag>.csv
## ============================================================================
using CSV, DataFrames, Statistics, Printf

include(joinpath(@__DIR__, "ladrillo_projection.jl"))

const REPO   = LADRILLO_REPO
const SEEDS  = [2026, 2027, 2028, 2029]
const NITER  = 2000000
const NBURN  = 1000000
const TAG    = let i = findfirst(a -> startswith(a, "--tag="), ARGS)
    i === nothing ? "L14" : ARGS[i][7:end]
end
const N_TARGET = let p = findfirst(a -> !startswith(a, "--"), ARGS)
    p === nothing ? 1000 : parse(Int, ARGS[p])
end
const SSPS     = ["ssp245", "ssp585"]
const Y0, Y1   = 1850, 2300
const HORIZONS = [2100, 2150, 2300]
const COMPONENT = :ais
## The AIS block, grouped as in diag_ais_block_convergence.jl so the two tables join on
## `param` and read in the same order.
##
## ⚠⚠ THE SET IS DERIVED FROM THE CHAIN, NOT TYPED. This list was the seventeen L14-era
## parameters and was hard-coded, so on 2026-09-26 the diagnostic REFUSED to run on L27 --
## correctly and loudly ("missing: antarctic_temp_threshold, antarctic_lambda,
## antarctic_gamma, ais_precip0_LOG"), because L27's flags (--cut-fastdyn, --fix-gamma,
## --precip-reparam) remove the fast-dynamics channel and reparameterise precipitation.
## A typed list makes a vintage difference an ERROR instead of a fact about the arm. So the
## CANDIDATES below are the superset (ordering only) and the parameters actually used are
## the intersection with the chain's OWN header, PRINTED and stamped into the output.
##
## ⛔ WHAT MUST NOT HAPPEN is a silent ranking over a different set than the reader assumes,
## so: the used set is printed, the absent ones are named with the flag that removes them,
## and the count is written into every row's `provenance`.
const AIS_CANDIDATES = ["ais_mu", "ais_bedheight0", "ais_slope", "ais_iceflow0",
                    "ais_precip0_LOG", "ais_precip_u", "ais_runoff_Ton", "ais_c",
                    "antarctic_alpha", "antarctic_nu", "antarctic_lambda",
                    "antarctic_gamma", "antarctic_kappa", "antarctic_temp_threshold",
                    "ais_ocean_temperature₀", "anto_alpha", "anto_beta",
                    "ais_gmst_amp"]
## why each candidate can be absent, so the log explains itself rather than just listing gaps
const ABSENT_REASON = Dict("antarctic_lambda" => "--cut-fastdyn",
                           "antarctic_temp_threshold" => "--cut-fastdyn",
                           "antarctic_gamma" => "--fix-gamma",
                           "ais_precip0_LOG" => "--precip-reparam (replaced by ais_precip_u)",
                           "ais_precip_u" => "no --precip-reparam (this vintage uses ais_precip0_LOG)")
const MIN_AIS_PARAMS = 8   # below this the chain is not an AIS-sampling vintage at all
const DECILE = 0.10
const OUT = joinpath(REPO, "outputs", "diag_ais_block_propagation_$(TAG).csv")

chain_path(sd) = joinpath(REPO, "outputs/mcmc", "chain_$(TAG)_seed$(sd)_n$(NITER).csv")
hdr(sd) = String.(propertynames(CSV.read(chain_path(sd), DataFrame; limit = 0)))
for sd in SEEDS; isfile(chain_path(sd)) || error("missing chain $(chain_path(sd))"); end

## the set this run actually uses = candidates ∩ the chain's own header (order preserved)
## ⚠⚠ TWO DIFFERENT SETS, AND CONFLATING THEM WOULD SILENTLY DROP THE ANSWER.
##   AIS_READ  = what to SELECT from the chain CSV  (the chain's own header)
##   AIS_PARAMS = what to RANK                      (the draws AFTER propagation)
## Under --cut-fastdyn the calibrator does NOT sample antarctic_lambda / temp_threshold, but
## `ladrillo_attach_propagated!` attaches them at PROJECTION time as joint paleo draws
## ("propagated, not estimated", calibrate_mcmc_ext.jl:857-860). They therefore DRIVE the
## projection while being absent from the chain. Ranking on the header would omit exactly the
## parameter most likely to dominate -- and would have reported its absence as if it were a
## zero effect. The rank set is taken from the post-attachment draws below.
const CHAIN_HDR = hdr(first(SEEDS))
const AIS_READ  = [p for p in AIS_CANDIDATES if p in CHAIN_HDR]
length(AIS_READ) >= MIN_AIS_PARAMS || error(
    "only $(length(AIS_READ)) AIS parameters found in chain_$(TAG) (need >= $MIN_AIS_PARAMS); " *
    "this does not look like an AIS-sampling vintage")
flush(stdout)
const VARIANT = ladrillo_gis_variant(hdr(SEEDS[1]))

"""Spearman rank correlation. Ties are averaged, which matters because a chain that
sticks repeats values exactly and a naive ordinal rank would invent an ordering."""
function spearman(x::Vector{Float64}, y::Vector{Float64})
    rk(v) = begin
        p = sortperm(v); r = similar(v); i = 1
        while i <= length(v)
            j = i
            while j < length(v) && v[p[j + 1]] == v[p[i]]; j += 1; end
            for k in i:j; r[p[k]] = (i + j) / 2; end
            i = j + 1
        end
        r
    end
    cor(rk(x), rk(y))
end

"""Read N_TARGET post-burn draws from one chain, in the coordinates the kernel wants."""
function read_draws(sd)
    ## Same slow-channel handling as diag_iceflow0_propagation.jl: read the Greenland
    ## coordinates the FILE carries, then map to native before applying. Selecting the
    ## native names on an L11+ chain throws "column gis_alpha_s not found".
    h = hdr(sd)
    ## ⚠⚠ USE THE HEADER-AWARE OVERLOAD. `ladrillo_used_cols(VARIANT)` returns the RAW column
    ## list; `ladrillo_used_cols(VARIANT, header)` is the one that knows about vintages -- the
    ## precip reparameterisation, the propagated/fixed paleo parameters that L27+ attaches AFTER
    ## reading rather than sampling, and the L30 ramp columns. Calling the one-argument form made
    ## this diagnostic demand `antarctic_lambda` etc. from an L27 chain and refuse to run
    ## (2026-09-26). The manual Greenland-slow remap that used to live here is deleted because the
    ## overload already does it -- two copies of that rule is how they drift apart.
    rd = vcat(ladrillo_used_cols(VARIANT, h), AIS_READ) |> unique
    miss = setdiff(rd, h)
    isempty(miss) || error("chain_$(TAG)_seed$(sd) is missing: " * join(miss, ", ") *
                           " — this diagnostic cannot read that vintage")
    df = CSV.read(chain_path(sd), DataFrame; select = rd)
    step = max(1, (nrow(df) - NBURN) ÷ N_TARGET)
    draws = ladrillo_native_greenland!(df[collect((NBURN + 1):step:nrow(df))[1:N_TARGET], :])
    df = nothing; GC.gc()
    return draws
end

out = DataFrame(scenario = String[], horizon = Int[], param = String[],
                pearson_r = Float64[], r2 = Float64[], spearman_rho = Float64[],
                decile_contrast_cm = Float64[], spread_p05_p95_cm = Float64[],
                contrast_frac_spread = Float64[], provenance = String[])

@printf("AIS block propagation | tag %s | %d draws/chain x %d chains | component %s\n",
        TAG, N_TARGET, length(SEEDS), String(COMPONENT))
@printf("  decile contrast = median(top %d%%) - median(bottom %d%%), as a fraction of p05-p95\n\n",
        round(Int, 100DECILE), round(Int, 100DECILE))
flush(stdout)

## READ THE CHAINS ONCE, NOT ONCE PER SCENARIO. The CSV read dominates the runtime
## (2e6 rows x ~60 columns x 4 chains); the projections themselves are seconds. Reading
## inside the scenario loop doubled the cost for identical draws.
const DRAWS = [(@printf("  reading chain seed%d ...\n", sd); flush(stdout); read_draws(sd))
               for sd in SEEDS]

## the RANK set = candidates present in the ATTACHED draws (superset of AIS_READ)
const DRAW_COLS  = String.(propertynames(first(DRAWS)))
const AIS_PARAMS = [p for p in AIS_CANDIDATES if p in DRAW_COLS]
const AIS_PROPAG = [p for p in AIS_PARAMS if !(p in AIS_READ)]
const AIS_ABSENT = [p for p in AIS_CANDIDATES if !(p in DRAW_COLS)]
@printf("  RANKED (%d): %s\n", length(AIS_PARAMS), join(AIS_PARAMS, ", "))
if !isempty(AIS_PROPAG)
    @printf("  of which PROPAGATED at projection time, not sampled (%d): %s\n",
            length(AIS_PROPAG), join(AIS_PROPAG, ", "))
    println("  ⭐ these are EXACT prior draws, so a high contrast on one of them means the band " *
            "is SAMPLED, not inferred -- which is the finding, not an artefact.")
end
if !isempty(AIS_ABSENT)
    @printf("  absent from this vintage entirely (%d): %s\n", length(AIS_ABSENT),
            join([haskey(ABSENT_REASON, p) ? "$p [$(ABSENT_REASON[p])]" : p for p in AIS_ABSENT], ", "))
end
flush(stdout)

## ⚠ the USED SET travels with the numbers: a ranking read out of this CSV months from now
## must not be assumed to cover parameters the arm never sampled.
const PROV = "diag_ais_block_propagation.jl | tag " * TAG * " | " * string(N_TARGET) *
             " draws/chain x " * string(length(SEEDS)) * " chains | AIS params used " *
             string(length(AIS_PARAMS)) * "/" * string(length(AIS_CANDIDATES)) * ": " *
             join(AIS_PARAMS, " ") * " | propagated-not-sampled: " *
             (isempty(AIS_PROPAG) ? "none" : join(AIS_PROPAG, " ")) * " | absent: " *
             (isempty(AIS_ABSENT) ? "none" : join(AIS_ABSENT, " ")) * " | decile " *
             string(DECILE) * " | cm"

for ssp in SSPS
    bf = ladrillo_setup(ssp = ssp, y0 = Y0, y1 = Y1, gis_variant = VARIANT)
    proj = Dict(y => Float64[] for y in HORIZONS)
    pars = Dict(p => Float64[] for p in AIS_PARAMS)
    for (sd, draws) in zip(SEEDS, DRAWS)
        t0 = time()
        for r in eachrow(draws)
            ladrillo_run_draw!(bf, r)
            s = ladrillo_series(bf, COMPONENT)
            for y in HORIZONS; push!(proj[y], s[ladrillo_yi(bf, y)]); end
        end
        for p in AIS_PARAMS; append!(pars[p], Float64.(draws[!, p])); end
        @printf("  %s seed%d: %d draws in %.0fs\n", ssp, sd, N_TARGET, time() - t0)
        flush(stdout)
    end

    for y in HORIZONS
        v = proj[y]
        spread = quantile(v, 0.95) - quantile(v, 0.05)
        @printf("\n%s @%d | n=%d | median %.2f cm | p05-p95 %.2f cm\n",
                ssp, y, length(v), median(v), spread)
        @printf("%-26s %9s %8s %9s %12s %10s\n",
                "param", "pearson", "R^2", "spearman", "contrast_cm", "frac")
        ## Rank by the decile contrast, not by r: that ordering IS the deliverable of
        ## this file, and sorting by r would bury a mixture-weight parameter.
        rows = NamedTuple[]
        for p in AIS_PARAMS
            x = pars[p]
            r = cor(x, v)
            rho = spearman(x, v)
            lo, hi = quantile(x, DECILE), quantile(x, 1 - DECILE)
            ## Strict inequalities on both sides so a parameter that is constant over a
            ## decile (a stuck chain) yields an empty set and NaN rather than a
            ## contrast computed against itself.
            vlo = v[x .<= lo]; vhi = v[x .>= hi]
            contrast = (isempty(vlo) || isempty(vhi)) ? NaN :
                       median(vhi) - median(vlo)
            push!(rows, (param = p, r = r, rho = rho, contrast = contrast,
                         frac = contrast / spread))
        end
        sort!(rows, by = t -> isfinite(t.frac) ? -abs(t.frac) : Inf)
        for t in rows
            @printf("%-26s %9.3f %8.4f %9.3f %12.2f %10.3f\n",
                    t.param, t.r, t.r^2, t.rho, t.contrast, t.frac)
            push!(out, (ssp, y, t.param, t.r, t.r^2, t.rho, t.contrast, spread, t.frac, PROV))
        end
    end
end

CSV.write(OUT, out)
@printf("\nwrote %s\n", relpath(OUT, REPO))

## ---- the headline: what to hand the next calibration ---------------------
@printf("\n%s\nRANKING at 2300 (the horizon Antarctica dominates)\n%s\n",
        repeat("=", 78), repeat("=", 78))
for ssp in SSPS
    sub = sort(out[(out.scenario .== ssp) .& (out.horizon .== 2300), :],
               :contrast_frac_spread, by = x -> -abs(x))
    @printf("%s: top 5 by |contrast/spread|  %s\n", ssp,
            join([@sprintf("%s %.2f", r.param, r.contrast_frac_spread)
                  for r in eachrow(first(sub, 5))], " | "))
end
