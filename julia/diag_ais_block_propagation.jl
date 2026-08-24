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
## The seventeen sampled AIS parameters, grouped as in diag_ais_block_convergence.jl
## so the two tables join on `param` and read in the same order.
const AIS_PARAMS = ["ais_mu", "ais_bedheight0", "ais_slope", "ais_iceflow0",
                    "ais_precip0_LOG", "ais_runoff_Ton", "ais_c",
                    "antarctic_alpha", "antarctic_nu", "antarctic_lambda",
                    "antarctic_gamma", "antarctic_kappa", "antarctic_temp_threshold",
                    "ais_ocean_temperature₀", "anto_alpha", "anto_beta",
                    "ais_gmst_amp"]
const DECILE = 0.10
const OUT = joinpath(REPO, "outputs", "diag_ais_block_propagation_$(TAG).csv")

chain_path(sd) = joinpath(REPO, "outputs/mcmc", "chain_$(TAG)_seed$(sd)_n$(NITER).csv")
hdr(sd) = String.(propertynames(CSV.read(chain_path(sd), DataFrame; limit = 0)))
for sd in SEEDS; isfile(chain_path(sd)) || error("missing chain $(chain_path(sd))"); end
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
    need = vcat(ladrillo_used_cols(VARIANT), AIS_PARAMS) |> unique
    h = hdr(sd)
    rd = ladrillo_gis_needs_native(h) ?
        vcat(setdiff(need, LADRILLO_GIS_SLOW_NATIVE_COLS),
             LADRILLO_GIS_SLOW_REPARAM_COLS) |> unique : need
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
                contrast_frac_spread = Float64[])

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
            push!(out, (ssp, y, t.param, t.r, t.r^2, t.rho, t.contrast, spread, t.frac))
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
