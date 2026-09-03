## ============================================================================
## scope_ais_refit_wander.jl — HOW MUCH DOES AIS MOVE BETWEEN EQUIVALENT FITS?
##
## THE QUESTION. Regenerating at L23 moved Antarctica by +69.3 cm at ssp245/2300 and
## +27.5 at ssp585/2300, while the glacier module — the ONLY thing that changed, and a
## change that is bit-identical on a monotonically warming path — moved 0.05 cm. So the
## L21 -> L23 difference cannot be the modelling change. The candidate explanation is that
## the AIS posterior is not identified well enough for a refit to be reproducible:
## `ais_iceflow0`, `ais_slope` and `antarctic_alpha` are exactly the parameters that fail
## R-hat (1.455 / 1.182 / 1.215 at L23; 2.323 / 1.566 / 1.479 at L21).
##
## THE CHEAP TEST, and why it needs no new chains. Each vintage ALREADY contains four
## independent chains. If the four disagree AMONG THEMSELVES about AIS@2300 by something
## comparable to 69 cm, then a difference of that size between two vintages is sampler
## wander and carries no information about either model. Running a fresh 3-hour refit to
## learn this would be paying for a number the existing chains already contain.
##
## ⚠ THIS MEASURES BETWEEN-CHAIN SPREAD, NOT BETWEEN-REFIT SPREAD, and they are not the
## same statistic. Four chains from one launch share a start distribution and an adapted
## proposal; two launches do not. Between-chain spread is therefore a LOWER BOUND on
## between-refit wander — which is the conservative direction for the question being asked:
## if the lower bound already covers 69 cm, the case is closed, and if it does not, the
## question stays open and needs the second refit. Say which one a number is.
##
## ⚠ R-HAT IS NOT THE STATISTIC HERE (`rhat_denominator_forgives`). AIS@2300 has a very
## wide band, so R-hat divides a real displacement by a large denominator and forgives it.
## This script reports the chain medians' RANGE and SD in CENTIMETRES, the units the
## deliverable is quoted in, and prints R-hat only beside them for contrast.
##
##   julia --project=julia_v2 julia/scope_ais_refit_wander.jl [n_per_chain] [--tag=L23] [--ssp=ssp245]
## Writes outputs/scope_ais_refit_wander_<TAG>_<SSP>.csv
##
## ⚠ THE SSP IS IN THE OUTPUT NAME (added 2026-09-03), because it is an ARM and every arm must
## be distinguishable on disk (`gis_targets.ssps_csv`'s rule). It was NOT, and the very first
## `--ssp=ssp585` run silently OVERWROTE the ssp245 file with numbers 2.4x smaller
## (322.75 vs 133.67 cm/unit on `ais_gmst_amp` at 2300) under an identical filename. Nothing
## errored; the only tell was that a slope had changed since the last read.
##
## ⚠ LEGACY FILES: `scope_ais_refit_wander_{L21,L23,L23b,L24}.csv` carry NO ssp suffix and are
## all the **ssp245** arm, written before this fix. They are kept under their old names because
## `notes/scoping_2026-09-01_ais_identifiability.md` cites them by those names. New runs never
## write those names, so a legacy file can no longer be clobbered by a fresh run of any arm.
## ============================================================================
using CSV, DataFrames, Statistics, Printf

include(joinpath(@__DIR__, "ladrillo_projection.jl"))

const REPO   = LADRILLO_REPO
## --seeds=a,b,c,d for a replicate bank (L23b runs 3026-3029 against the SAME start rows).
const SEEDS = let i = findfirst(a -> startswith(a, "--seeds="), ARGS)
    i === nothing ? [2026, 2027, 2028, 2029] :
        parse.(Int, split(ARGS[i][9:end], ","))
end
const NITER  = 2000000
const NBURN  = 1000000
const TAG = let i = findfirst(a -> startswith(a, "--tag="), ARGS)
    i === nothing ? "L23" : ARGS[i][7:end]
end
const N_TARGET = let p = findfirst(a -> !startswith(a, "--"), ARGS)
    p === nothing ? 300 : parse(Int, ARGS[p])
end
const SSP = let i = findfirst(a -> startswith(a, "--ssp="), ARGS)
    i === nothing ? "ssp245" : ARGS[i][7:end]
end
const Y0, Y1 = 1850, 2300
const HORIZONS = [2100, 2150, 2300]
## Every component, not just AIS: the claim "the move is ALL Antarctica" is only
## meaningful if the others are measured on the same draws and come out small.
const COMPONENTS = [:glaciers, :gis, :ais, :te, :total]

chain_path(sd) = joinpath(REPO, "outputs/mcmc", "chain_$(TAG)_seed$(sd)_n$(NITER).csv")
for sd in SEEDS
    isfile(chain_path(sd)) || error("missing chain $(chain_path(sd))")
end
chain_header(sd) = String.(propertynames(CSV.read(chain_path(sd), DataFrame; limit = 0)))
const VARIANTS = Dict(sd => ladrillo_gis_variant(chain_header(sd)) for sd in SEEDS)
allequal(values(VARIANTS)) || error("chains disagree on the Greenland variant")
const VARIANT = VARIANTS[SEEDS[1]]

@printf("AIS REFIT WANDER | tag %s | %s | %d draws/chain x %d chains | variant :%s\n",
        TAG, SSP, N_TARGET, length(SEEDS), VARIANT)
flush(stdout)

bf = ladrillo_setup(ssp = "ssp245", y0 = Y0, y1 = Y1, gis_variant = VARIANT,
                    forcing_tag = SSP)
yi(y) = ladrillo_yi(bf, y)

vals = Dict((c, y) => [Float64[] for _ in SEEDS] for c in COMPONENTS, y in HORIZONS)
## The parameters whose between-refit shift is largest in units of their own posterior sd
## (measured L21 vs L23: gmst_amp +1.45 sd, runoff_Ton +0.97, slope -0.60, iceflow0 +0.49).
## Sensitivity is measured for each so the AIS move can be ACCOUNTED FOR rather than
## attributed to whichever parameter was looked at first.
const SENS_PARAMS = [:ais_gmst_amp, :ais_runoff_Ton, :ais_iceflow0, :ais_slope]
const SENS_SHIFT = Dict(:ais_gmst_amp => 0.1405, :ais_runoff_Ton => 0.0800,
                        :ais_iceflow0 => 0.0967, :ais_slope => -1.55e-5)
sens = Dict(p => [Float64[] for _ in SEEDS] for p in SENS_PARAMS)
for (ci, sd) in enumerate(SEEDS)
    t0 = time()
    need = ladrillo_used_cols(VARIANT)
    h = chain_header(sd)
    rd = ladrillo_gis_needs_native(h) ?
        vcat(setdiff(need, LADRILLO_GIS_SLOW_NATIVE_COLS),
             LADRILLO_GIS_SLOW_REPARAM_COLS) |> unique : need
    df = CSV.read(chain_path(sd), DataFrame; select = rd)
    step = max(1, (nrow(df) - NBURN) ÷ N_TARGET)
    rows = collect((NBURN + 1):step:nrow(df))[1:N_TARGET]
    draws = ladrillo_native_greenland!(df[rows, :]); df = nothing; GC.gc()
    for r in eachrow(draws)
        ladrillo_run_draw!(bf, r)
        for c in COMPONENTS
            s = ladrillo_series(bf, c)
            for y in HORIZONS; push!(vals[(c, y)][ci], s[yi(y)]); end
        end
        ## T_on paired with the SAME draw, so the sensitivity below is measured on the
        ## posterior rather than assumed from a scan.
        for p in SENS_PARAMS; push!(sens[p][ci], Float64(r[p])); end
    end
    @printf("  seed%d: %d draws (%.0fs)\n", sd, N_TARGET, time() - t0); flush(stdout)
end

rows = DataFrame(tag = String[], ssp = String[], component = String[], horizon = Int[],
                 chain_med_min = Float64[], chain_med_max = Float64[],
                 range_cm = Float64[], sd_of_medians_cm = Float64[],
                 pooled_med_cm = Float64[], mean_within_sd_cm = Float64[], rhat = Float64[])

"""Split-less R-hat on the chain medians' scale, for CONTRAST with the cm numbers."""
function rhat_of(v)
    m = length(v); n = length(v[1])
    cm = mean.(v); B = n * var(cm); W = mean(var.(v))
    W <= 0 && return NaN
    sqrt(((n - 1) / n * W + B / n) / W)
end

@printf("\n%s\nBETWEEN-CHAIN SPREAD WITHIN ONE REFIT — %s, %s, cm rel %d-%d\n%s\n",
        repeat("=", 96), TAG, SSP, LADRILLO_REF[1], LADRILLO_REF[2], repeat("=", 96))
@printf("  %-9s %-6s %9s %9s %9s %9s %9s %7s\n",
        "component", "horiz", "med min", "med max", "RANGE", "sd(med)", "pooled", "R-hat")
for c in COMPONENTS, y in HORIZONS
    v = vals[(c, y)]
    meds = median.(v)
    rg = maximum(meds) - minimum(meds)
    push!(rows, (TAG, SSP, String(c), y, minimum(meds), maximum(meds), rg, std(meds),
                 median(vcat(v...)), mean(std.(v)), rhat_of(v)))
    @printf("  %-9s %-6d %9.2f %9.2f %9.2f %9.2f %9.2f %7.3f\n",
            c, y, minimum(meds), maximum(meds), rg, std(meds), median(vcat(v...)),
            rhat_of(v))
end
## ---- SENSITIVITY TO T_on -------------------------------------------------
## WHY. Both L21 and L23 sit ~100% in the MID mode of `ais_runoff_Ton`
## ([[ais_ton_multimodal]]), so a mode swap does NOT explain the difference between them.
## What differs is the median WITHIN the mode (L21 -17.86, L23 -17.78, about one
## within-chain sd). If AIS is steep in T_on there, a shift that small buys a large SLR
## move -- and that, not mode-hopping, is the identifiability problem. Measured on the
## pooled posterior draws, not from a scan.
for p in SENS_PARAMS
    t = vcat(sens[p]...)
    @printf("\n%s\nAIS SENSITIVITY TO %s (pooled draws, n=%d)\n%s\n",
            repeat("=", 96), p, length(t), repeat("=", 96))
    @printf("  %s: median %.4g, sd %.4g | L21->L23 shift %.4g\n",
            p, median(t), std(t), SENS_SHIFT[p])
    @printf("  %-6s %10s %14s %14s\n", "horiz", "corr", "slope cm/unit", "x shift (cm)")
    for y in HORIZONS
        a = vcat(vals[(:ais, y)]...)
        c = cor(t, a); b = cov(t, a) / var(t)
        @printf("  %-6d %10.3f %14.1f %14.2f\n", y, c, b, SENS_SHIFT[p] * b)
        push!(rows, (TAG, SSP, "sens_$(p)", y, NaN, NaN, NaN, NaN, b, c,
                     SENS_SHIFT[p] * b))
    end
end
@printf("\n  'x shift' is what each parameter's OBSERVED L21->L23 median shift buys at the\n")
@printf("  measured slope. Their sum is what the between-vintage AIS move must be made of;\n")
@printf("  a large residual means the move is NOT accounted for by these parameters.\n\n")

## THE ARM IS IN THE NAME, so the legacy unsuffixed files are safe STRUCTURALLY rather than by
## a guard: this path always carries an SSP, so no invocation can produce the old name at all.
const OUTCSV = joinpath(REPO, "outputs", "scope_ais_refit_wander_$(TAG)_$(SSP).csv")
CSV.write(OUTCSV, rows)
@printf("\nwrote outputs/scope_ais_refit_wander_%s_%s.csv\n", TAG, SSP)
