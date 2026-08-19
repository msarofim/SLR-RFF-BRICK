## ============================================================================
## diag_l13_projection_variant.jl — was the L13 SLR certificate computed on the
## model that was actually CALIBRATED?
##
## THE QUESTION. L13 sampled two 3-basin Greenland rate scales (`gis_s_mid`,
## `gis_s_high`, LOG10) under `greenland_3basin`. Before 2026-08-19,
## ladrillo_projection.jl knew only :stock and :ab: `ladrillo_gis_variant` returned
## :ab for an L13 chain, `ladrillo_used_cols(:ab)` did not even READ the two basin
## columns, and `ladrillo_setup(gis_ab=true)` built `build_brick_nu3_gis`. So every
## L13 projection ran at s = 1 — the partition-invariance NULL — while the shared
## Greenland parameters had been fitted against s_high ~ 0.26. This script measures
## the size of that gap on the deliverable, using the SAME chains, burn-in and
## thinning as diag_slr_convergence_by_chain_ladrillo.jl so the :ab arm must
## reproduce outputs/mcmc/slr_convergence_L13.csv exactly.
##
## THREE ARMS, one draw set:
##   ARM_AB     :ab      — the shipped path; Greenland = greenland_ab
##   ARM_BASINS :basins  — greenland_3basin at the draw's OWN (s_mid, s_high)
##   ARM_S1     :basins  with both log10 scales forced to 0, i.e. s = 1
##
## GATE. ARM_S1 must equal ARM_AB draw-for-draw: at s = 1 the 3-basin component is
## algebraically greenland_ab (test_greenland_3basin_nesting.jl gate [3], 4.4e-16).
## A non-zero max|ARM_S1 - ARM_AB| means the new :basins path differs from :ab for
## some reason OTHER than the scales, and nothing below may be read.
##
##   julia --project=julia_v2 julia/diag_l13_projection_variant.jl [n_per_chain] [--tag=L13]
## ============================================================================
using CSV, DataFrames, Statistics, Printf, MCMCDiagnosticTools

include(joinpath(@__DIR__, "ladrillo_projection.jl"))

const REPO      = LADRILLO_REPO
const SEEDS     = [2026, 2027, 2028, 2029]
const NITER     = 2000000
const NBURN     = 1000000
const CHAIN_TAG = let i = findfirst(a -> startswith(a, "--tag="), ARGS)
    i === nothing ? "L13" : ARGS[i][7:end]
end
const N_TARGET  = let p = findfirst(a -> !startswith(a, "--"), ARGS)
    p === nothing ? 400 : parse(Int, ARGS[p])
end
const SSP       = "ssp245"
const GIS_SHAPE = true                  # certifies the SHIPPED amp law, as the gate does
const Y0, Y1    = 1850, 2150
const HORIZONS  = [2100, 2150]
const RHAT_OK   = 1.05
## Arm labels are named constants so every table, message and column below moves
## with them (CLAUDE.md: labels derive from named constants).
const ARM_AB, ARM_BASINS, ARM_S1 = "ab_shipped", "basins_fitted_s", "basins_s1"
const GATE_TOL  = 1e-9                  # metres-SLE-scale exactness, in cm

chain_path(sd) = joinpath(REPO, "outputs/mcmc",
                          "chain_$(CHAIN_TAG)_seed$(sd)_n$(NITER).csv")
for sd in SEEDS
    isfile(chain_path(sd)) || error("missing chain file $(chain_path(sd))")
end
chain_header(sd) = String.(propertynames(CSV.read(chain_path(sd), DataFrame; limit = 0)))

const VARIANTS = Dict(sd => ladrillo_gis_variant(chain_header(sd)) for sd in SEEDS)
allequal(values(VARIANTS)) || error("the chains disagree on the Greenland variant: $VARIANTS")
const VARIANT = VARIANTS[SEEDS[1]]
VARIANT === :basins || error("chain_$(CHAIN_TAG) reads as :$VARIANT, not :basins — this " *
    "diagnostic exists to compare the 3-basin projection against the A+B one, so it " *
    "needs a chain that carries $(join(LADRILLO_GIS_BASIN_COLS, ", "))")

@printf("L13 projection-variant diagnostic\n")
@printf("  tag %s | %s | %d-%d | rebaseline %d-%d | amp law %s\n",
        CHAIN_TAG, SSP, Y0, Y1, LADRILLO_REF[1], LADRILLO_REF[2], GIS_SHAPE ? "ON" : "OFF")
@printf("  burn = first %d of %d, thinned to %d draws per chain\n\n", NBURN, NITER, N_TARGET)

bf_ab  = ladrillo_setup(ssp=SSP, y0=Y0, y1=Y1, gis_variant=:ab,     gis_shape=GIS_SHAPE)
bf_b3  = ladrillo_setup(ssp=SSP, y0=Y0, y1=Y1, gis_variant=:basins, gis_shape=GIS_SHAPE)

## ---- draws ---------------------------------------------------------------
need = ladrillo_used_cols(VARIANT)
slr = Dict(a => Dict(y => Vector{Float64}[] for y in HORIZONS)
           for a in (ARM_AB, ARM_BASINS, ARM_S1))
gate_max = Ref(0.0)
chain_labels = String[]
## Parameters carried into the per-draw dump: the handoff's three SLR-failure
## candidates plus the two restructure knobs, so the dump can settle which of them
## actually moves the 2100 projection.
const DUMP_COLS = ["gis_amp", "gis_f", "gis_c1", "gis_alpha_f", "gis_beta_f",
                   "gis_s_mid", "gis_s_high", "ais_iceflow0", "ais_c",
                   "antarctic_alpha", "thermal_alpha"]
dump = Dict{String,Vector{Float64}}(c => Float64[] for c in vcat(DUMP_COLS, "chain"))
dump_slr = Dict("$(a)_$(y)" => Float64[] for a in (ARM_AB, ARM_BASINS) for y in HORIZONS)
t00 = time()
for sd in SEEDS
    t0 = time()
    hdr = chain_header(sd)
    rd = ladrillo_gis_needs_native(hdr) ?
        vcat(setdiff(need, LADRILLO_GIS_SLOW_NATIVE_COLS), LADRILLO_GIS_SLOW_REPARAM_COLS) : need
    rd = unique(vcat(rd, DUMP_COLS))   # the dump columns are read too, not re-derived
    missing_cols = setdiff(rd, hdr)
    isempty(missing_cols) || error("chain_$(CHAIN_TAG)_seed$(sd) is missing: $(join(missing_cols, ", "))")

    df = CSV.read(chain_path(sd), DataFrame; select = rd)
    nrow(df) == NITER || error("$(basename(chain_path(sd))): expected $NITER rows, got $(nrow(df))")
    step = max(1, (nrow(df) - NBURN) ÷ N_TARGET)
    rows = collect((NBURN + 1):step:nrow(df))[1:N_TARGET]
    draws = ladrillo_native_greenland!(df[rows, :])
    df = nothing; GC.gc()

    vals = Dict(a => Dict(y => Float64[] for y in HORIZONS)
                for a in (ARM_AB, ARM_BASINS, ARM_S1))
    # Per-draw dump. The whole point is that the between-chain SLR disagreement can
    # then be regressed on the parameters WITHIN a chain (a real sensitivity)
    # instead of being read off 4 chain medians (n = 4, no power).
    for c in DUMP_COLS; append!(dump[c], Float64.(draws[!, c])); end
    append!(dump["chain"], fill(Float64(sd), nrow(draws)))
    # The s = 1 arm is the SAME draws with both log10 scales zeroed. Built as a
    # separate frame rather than mutating the row, so the fitted-s arm cannot be
    # contaminated by the gate arm.
    draws_s1 = copy(draws)
    draws_s1[!, "gis_s_mid"]  .= 0.0        # log10(1)
    draws_s1[!, "gis_s_high"] .= 0.0
    for (r, r1) in zip(eachrow(draws), eachrow(draws_s1))
        ladrillo_run_draw!(bf_ab, r);  tab = ladrillo_series(bf_ab, :total)
        ladrillo_run_draw!(bf_b3, r);  tb3 = ladrillo_series(bf_b3, :total)
        ladrillo_run_draw!(bf_b3, r1); ts1 = ladrillo_series(bf_b3, :total)
        for y in HORIZONS
            i = ladrillo_yi(bf_ab, y)
            push!(vals[ARM_AB][y],     tab[i])
            push!(vals[ARM_BASINS][y], tb3[i])
            push!(vals[ARM_S1][y],     ts1[i])
            gate_max[] = max(gate_max[], abs(ts1[i] - tab[i]))
            push!(dump_slr["$(ARM_AB)_$(y)"], tab[i])
            push!(dump_slr["$(ARM_BASINS)_$(y)"], tb3[i])
        end
    end
    for a in (ARM_AB, ARM_BASINS, ARM_S1), y in HORIZONS
        push!(slr[a][y], vals[a][y])
    end
    push!(chain_labels, "seed$(sd)")
    @printf("  seed%d: %d draws x 3 arms (thin %d)  %.0fs\n", sd, N_TARGET, step, time() - t0)
end
@printf("  total %.0fs\n", time() - t00)

## ---- the gate, first ------------------------------------------------------
@printf("\n%s\nNESTING GATE  max|%s - %s| = %.3e cm  (tol %.0e)\n%s\n",
        "="^78, ARM_S1, ARM_AB, gate_max[], GATE_TOL, "="^78)
gate_max[] <= GATE_TOL || error("the :basins path at s = 1 does NOT reproduce :ab " *
    "(max diff $(gate_max[]) cm > $GATE_TOL). Nothing below is interpretable.")
println("PASS — at s = 1 the 3-basin projection is greenland_ab, so every difference\n" *
        "between $(ARM_BASINS) and $(ARM_AB) below is the FITTED basin scales and nothing else.")

## ---- distributions + convergence, per arm --------------------------------
q(v, p) = quantile(v, p)
rows_out = DataFrame(arm=String[], horizon=Int[], rhat=Float64[], ess=Float64[],
                     sd_medians=Float64[], mean_sd_wc=Float64[], pooled_q50=Float64[],
                     pooled_q05=Float64[], pooled_q95=Float64[],
                     n_chains=Int[], n_per_chain=Int[], niter=Int[], tag=String[])
for a in (ARM_AB, ARM_BASINS)
    @printf("\n%s\nARM %s\n%s\n", "-"^78, a, "-"^78)
    for y in HORIZONS
        @printf("\nSLR @%d (cm, rel. %d-%d)\n", y, LADRILLO_REF[1], LADRILLO_REF[2])
        @printf("  %-10s %8s %8s %8s %8s %8s\n", "chain", "q05", "q50", "q95", "mean", "sd")
        for (ci, lab) in enumerate(chain_labels)
            v = slr[a][y][ci]
            @printf("  %-10s %8.2f %8.2f %8.2f %8.2f %8.2f\n",
                    lab, q(v,0.05), q(v,0.50), q(v,0.95), mean(v), std(v))
        end
        pooled = vcat(slr[a][y]...)
        @printf("  %-10s %8.2f %8.2f %8.2f %8.2f %8.2f\n",
                "POOLED", q(pooled,0.05), q(pooled,0.50), q(pooled,0.95), mean(pooled), std(pooled))
        arr = reduce(hcat, slr[a][y])
        r = rhat(arr); e = ess(arr; maxlag = size(arr,1))
        meds = [median(c) for c in slr[a][y]]
        push!(rows_out, (a, y, r, e, std(meds), mean([std(c) for c in slr[a][y]]),
                         q(pooled,0.50), q(pooled,0.05), q(pooled,0.95),
                         length(SEEDS), N_TARGET, NITER, CHAIN_TAG))
        @printf("  R-hat %.3f  ESS %.1f  sd(medians) %.3f  %s\n",
                r, e, std(meds), r < RHAT_OK ? "PASS" : "FAIL")
    end
end

@printf("\n%s\nWHAT THE FITTED BASIN SCALES ARE WORTH ON THE DELIVERABLE\n%s\n", "="^78, "="^78)
@printf("  %-10s %10s %12s %12s %10s\n", "horizon", "arm", "pooled q50", "sd(medians)", "R-hat")
for y in HORIZONS, a in (ARM_AB, ARM_BASINS)
    rr = only(eachrow(rows_out[(rows_out.arm .== a) .& (rows_out.horizon .== y), :]))
    @printf("  %-10d %10s %12.2f %12.3f %10.3f\n", y, a, rr.pooled_q50, rr.sd_medians, rr.rhat)
end
for y in HORIZONS
    ab = only(rows_out[(rows_out.arm .== ARM_AB)     .& (rows_out.horizon .== y), :pooled_q50])
    b3 = only(rows_out[(rows_out.arm .== ARM_BASINS) .& (rows_out.horizon .== y), :pooled_q50])
    @printf("  @%d: correcting the projection moves the median %+.2f cm (%.2f -> %.2f)\n",
            y, b3 - ab, ab, b3)
end

out = joinpath(REPO, "outputs/mcmc/projection_variant_$(CHAIN_TAG).csv")
CSV.write(out, rows_out)
println("\nWrote $out")

dump_df = DataFrame(dump)
for (k, v) in dump_slr; dump_df[!, k] = v; end
dump_path = joinpath(REPO, "outputs/mcmc/projection_variant_draws_$(CHAIN_TAG).csv")
CSV.write(dump_path, dump_df)
println("Wrote $dump_path  ($(nrow(dump_df)) draws x $(ncol(dump_df)) cols)")
