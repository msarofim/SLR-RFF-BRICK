## ============================================================================
## diag_slr_convergence_by_chain_ladrillo.jl — is the DELIVERABLE converged?
##
## Ladrillo 1.0 (greenland_ab, 55-param L10 chains) counterpart of
## diag_slr_convergence_by_chain{,_extc}.jl. Those two are hard-wired to a
## Greenland block Ladrillo does not have: the base file demands `greenland_a`
## and dies on an L10 chain with
##     ArgumentError: column name :greenland_a not found in the data frame
## which is how this file came to exist.
##
## WHY IT IS NEEDED
## postprocess_mcmc_ext.jl --tag=L10 reports 19 non-converged parameter
## marginals, led by the AIS geometry block:
##     ais_iceflow0      R-hat 2.359  ESS 12.0  tau 334529
##     antarctic_alpha   R-hat 1.505  ESS 15.9
##     gis_f             R-hat 1.335  ESS 21.4
## and REFUSES to write the canonical subsample. That is the expected reading,
## not a surprise: the base diagnostic's own header records ais_iceflow0 at
## R-hat 1.320 / ESS 10.6 in the 35-param v-next calibration, and calibrate's
## --overdisperse comment predicts R-hat will LOOK WORSE than a common start
## "-- that is the diagnostic working, not a regression". Our number is worse
## still for a mechanical reason: overdispersed_starts.csv is built by drawing
## at ais_iceflow0 quantiles 0.02/0.35/0.65/0.98, so the four chains are
## deliberately spread along precisely this axis, and with tau ~ 3.3e5 a
## 1e6-draw post-burn half holds only ~3 effective samples of it.
##
## The AIS geometry params are strongly correlated, so a poorly-identified ridge
## in parameter space can still map onto a well-determined projection. This
## script asks the only question that matters downstream:
##
##     is projected SSP2-4.5 SLR at 2100 / 2150 converged ACROSS the 4 chains?
##
## Its output outputs/mcmc/slr_convergence_L10.csv is what
## postprocess_mcmc_ext.jl --tag=L10 --accept-slr reads to decide whether the
## parameter-level failures may be accepted on the deliverable.
##
## WHY IT DELEGATES TO ladrillo_projection.jl
## The extC diagnostic re-implements the draw->BRICK mapping inline, which is
## how the projection kernel came to be silently hard-wired to stock SIMPLE in
## the first place (handoff 2026-08-12c section 2). ladrillo_projection.jl is the
## ONE place that knows how to push a Ladrillo draw through MimiBRICK, it detects
## the Greenland variant from the posterior's own columns with no default and no
## fallback, and validate_gis_projection_ab.jl gates it end-to-end. Using it here
## means this diagnostic cannot drift onto a different model than the projections
## it is certifying.
##
##   julia --project=julia_v2 julia/diag_slr_convergence_by_chain_ladrillo.jl \
##         [n_per_chain] [--tag=L10] [--no-shape]
## ============================================================================
using CSV, DataFrames, Statistics, Printf, MCMCDiagnosticTools

include(joinpath(@__DIR__, "ladrillo_projection.jl"))

const REPO       = LADRILLO_REPO
const SEEDS      = [2026, 2027, 2028, 2029]
const NITER      = 2000000
const NBURN      = 1000000                # discard the FIRST HALF
const CHAIN_TAG  = let i = findfirst(a -> startswith(a, "--tag="), ARGS)
    i === nothing ? "L10" : ARGS[i][7:end]
end
const N_TARGET   = let p = findfirst(a -> !startswith(a, "--"), ARGS)
    p === nothing ? 400 : parse(Int, ARGS[p])
end
const SSP        = "ssp245"
## The certificate must describe the model that is actually SHIPPED. Since
## 2026-08-13 that model carries the Greenland amp(GMST) law, so the law is ON by
## default here and the arm is recorded in the output. --no-shape reproduces the
## constant-amp certificate (what the original acceptance was computed on).
const GIS_SHAPE  = !("--no-shape" in ARGS)
const Y0, Y1     = 1850, 2150
const HORIZONS   = [2100, 2150]
# R-hat threshold for the deliverable, matching diag_slr_convergence_by_chain*.jl
const RHAT_OK    = 1.05

## ---- variant first, THEN the model --------------------------------------
# ladrillo_setup(gis_ab=) decides which Greenland slot the model carries, and
# ladrillo_apply_draw! branches on it. So the variant has to be read off the
# chains BEFORE the model is built: setting up with the default (:stock) and
# then feeding it A+B draws fails on the missing greenland_a rather than
# silently projecting the wrong Greenland, but it fails after the setup cost.
chain_path(sd) = joinpath(REPO, "outputs/mcmc",
                          "chain_$(CHAIN_TAG)_seed$(sd)_n$(NITER).csv")
chain_header(sd) = String.(propertynames(CSV.read(chain_path(sd), DataFrame; limit = 0)))

for sd in SEEDS
    isfile(chain_path(sd)) || error("missing chain file $(chain_path(sd))")
end
const VARIANTS = Dict(sd => ladrillo_gis_variant(chain_header(sd)) for sd in SEEDS)
allequal(values(VARIANTS)) || error("the $(length(SEEDS)) chains disagree on the Greenland " *
    "variant: $(join(["seed$sd=>:$(VARIANTS[sd])" for sd in SEEDS], ", ")). " *
    "Mixing vintages in one R-hat would compare different models, not chains.")
const VARIANT = VARIANTS[SEEDS[1]]
VARIANT === :ab || error("chains read as :$VARIANT, not :ab — this is the Ladrillo 1.0 " *
    "(greenland_ab) diagnostic; use diag_slr_convergence_by_chain_extc.jl for " *
    "stock-SIMPLE chains")

bf = ladrillo_setup(ssp=SSP, y0=Y0, y1=Y1, gis_ab = VARIANT === :ab,
                    gis_shape = GIS_SHAPE)

@printf("Ladrillo 1.0 SLR convergence-by-chain diagnostic\n")
@printf("  tag %s | window %d-%d | %s | rebaseline %d-%d | Greenland :%s\n",
        CHAIN_TAG, Y0, Y1, SSP, LADRILLO_REF[1], LADRILLO_REF[2], VARIANT)
@printf("  burn = first %d of %d, thinned to %d draws per chain\n", NBURN, NITER, N_TARGET)
@printf("  amp law %s\n\n", GIS_SHAPE ?
        @sprintf("ON (S anchored at dT_eff = %.3f K) — certifies the SHIPPED model",
                 LADRILLO_GIS_SHAPE_ANCHOR_DT) :
        "OFF (constant-amp splice) — reproduces the original 2026-08-13 acceptance")

## ---- per-chain forward runs ---------------------------------------------
slr = Dict(y => Vector{Float64}[] for y in HORIZONS)
chain_labels = String[]
t00 = time()
for sd in SEEDS
    f = chain_path(sd)
    t0 = time()

    hdr = chain_header(sd)
    need = ladrillo_used_cols(VARIANT)
    # An L11+ chain carries the Greenland slow channel as the sampled (ell, w),
    # not the native (alpha_s, beta_s) the kernel applies. Read what the chain
    # HAS; ladrillo_native_greenland! derives the native pair below.
    ladrillo_gis_needs_native(hdr) &&
        (need = vcat(setdiff(need, LADRILLO_GIS_SLOW_NATIVE_COLS),
                     LADRILLO_GIS_SLOW_REPARAM_COLS))
    # CSV.jl's select= silently returns only the columns it FINDS, so demand them.
    missing_cols = setdiff(need, hdr)
    isempty(missing_cols) || error("chain_$(CHAIN_TAG)_seed$(sd) is missing " *
        "$(length(missing_cols)) column(s) the projection kernel reads: " *
        join(missing_cols, ", "))

    df = CSV.read(f, DataFrame; select = need)
    nrow(df) == NITER || error("$(basename(f)): expected $NITER rows, got $(nrow(df))")

    # thin: evenly spaced across the POST-BURN half (not a contiguous block)
    step = max(1, (nrow(df) - NBURN) ÷ N_TARGET)
    rows = collect((NBURN + 1):step:nrow(df))[1:N_TARGET]
    draws = ladrillo_native_greenland!(df[rows, :])
    df = nothing; GC.gc()

    vals = Dict(y => Float64[] for y in HORIZONS)
    for r in eachrow(draws)
        ladrillo_run_draw!(bf, r)
        total = ladrillo_series(bf, :total)
        for y in HORIZONS
            push!(vals[y], total[ladrillo_yi(bf, y)])
        end
    end
    for y in HORIZONS
        push!(slr[y], vals[y])
    end
    push!(chain_labels, "seed$(sd)")
    @printf("  seed%d: %d draws (thin %d, rows %d..%d)  %.0fs\n",
            sd, N_TARGET, step, rows[1], rows[end], time() - t0)
end
@printf("  total %.0fs\n", time() - t00)

## ---- distribution + convergence tables ----------------------------------
q(v, p) = quantile(v, p)
for y in HORIZONS
    @printf("\nSLR @%d (cm, rel. %d-%d)\n", y, LADRILLO_REF[1], LADRILLO_REF[2])
    @printf("  %-10s %8s %8s %8s %8s %8s\n", "chain", "q05", "q50", "q95", "mean", "sd")
    for (ci, lab) in enumerate(chain_labels)
        v = slr[y][ci]
        @printf("  %-10s %8.2f %8.2f %8.2f %8.2f %8.2f\n",
                lab, q(v, 0.05), q(v, 0.50), q(v, 0.95), mean(v), std(v))
    end
    pooled = vcat(slr[y]...)
    @printf("  %-10s %8.2f %8.2f %8.2f %8.2f %8.2f\n",
            "POOLED", q(pooled, 0.05), q(pooled, 0.50), q(pooled, 0.95),
            mean(pooled), std(pooled))
end

@printf("\n%s\n", "="^78)
@printf("CROSS-CHAIN CONVERGENCE OF PROJECTED SLR  (%d chains x %d thinned draws)\n",
        length(SEEDS), N_TARGET)
@printf("%s\n", "="^78)
@printf("  %-14s %8s %10s %12s %12s %10s\n",
        "quantity", "R-hat", "ESS", "sd(medians)", "mean(sd_wc)", "ratio")
# gis_shape is written into the certificate so the file says which model it
# certifies. Without it a constant-amp and an amp-law certificate are
# indistinguishable on disk, which is exactly the confusion this column prevents.
diag_rows = DataFrame(horizon=Int[], rhat=Float64[], ess=Float64[],
                      sd_medians=Float64[], mean_sd_wc=Float64[],
                      n_chains=Int[], n_per_chain=Int[], niter=Int[],
                      gis_shape=Bool[])
for y in HORIZONS
    arr = reduce(hcat, slr[y])
    r = rhat(arr)
    e = ess(arr; maxlag = size(arr, 1))
    meds   = [median(c) for c in slr[y]]
    sd_wc  = mean([std(c) for c in slr[y]])
    sd_med = std(meds)
    @printf("  SLR@%-10d %8.3f %10.1f %12.3f %12.3f %10.3f\n",
            y, r, e, sd_med, sd_wc, sd_med / sd_wc)
    push!(diag_rows, (y, r, e, sd_med, sd_wc, length(SEEDS), N_TARGET, NITER, GIS_SHAPE))
end
slr_csv = joinpath(REPO, "outputs/mcmc/slr_convergence_$(CHAIN_TAG).csv")
CSV.write(slr_csv, diag_rows)
println("\nWrote $slr_csv")
@printf("\nVERDICT: %s\n",
        all(r < RHAT_OK for r in diag_rows.rhat) ?
        "projected SLR IS converged across chains (R-hat < $RHAT_OK at all horizons)" :
        "projected SLR is NOT converged across chains (R-hat >= $RHAT_OK at some horizon)")
