## ============================================================================
## diag_ais_objective_shape_sensitivity.jl — WHICH SHAPES can the AIS term see?
##
## Memory `objective_scores_levels_not_rates` (09-22e) says the shipped objective scores the LEVEL
## series, which is why a smooth drift is nearly free. That framing decides the open ruling, so it
## is worth MEASURING rather than reasoning about: an AR(1) residual at rho -> 1 approaches a random
## walk, whose likelihood scores first DIFFERENCES, so "levels not rates" may be the wrong summary
## of the same covariance. ~/.claude/CLAUDE.md: confidence words need receipts.
##
## METHOD. No model runs. Take the objective's own AIS covariance Sigma(sd_ais, rho, eps, L=100) on
## the fit years and evaluate the quadratic penalty q = d' Sigma^-1 d for a set of UNIT-AMPLITUDE
## discrepancy SHAPES d(t), each normalised to the SAME amplitude at the end of the span. The ratio
## between shapes is what the objective can and cannot see; a shape with small q is one the
## objective is nearly blind to, whatever its size in cm.
##
##   julia --project=julia_v2 julia/diag_ais_objective_shape_sensitivity.jl [--tag=L30]
## Writes outputs/diag_ais_objective_shape_sensitivity_<tag>.csv
## ============================================================================
using CSV, DataFrames, Statistics, Printf, Dates, LinearAlgebra

const SCRIPT = "diag_ais_objective_shape_sensitivity.jl"
const TAG    = (i = findfirst(a -> startswith(a, "--tag="), ARGS); i === nothing ? "L30" : ARGS[i][7:end])
const REPO   = normpath(joinpath(@__DIR__, ".."))
const TARGETS = joinpath(REPO, "outputs/recalib_targets_ext.csv")
const POSTP   = joinpath(REPO, "data/MimiBRICK/parameters_subsample_brick_mengel_$TAG.csv")
const OBS_CORR_LEN = 100.0
const FIT_Y0  = 1900
const RHOS    = [0.966, 0.90, 0.80, 0.60]
const AMP     = 0.1            # cm SLE: every shape is scaled to this at the END of the span

epsband(lo, hi) = max.((hi .- lo) ./ (2 * 1.645), 0.05)
function ais_cov(σ, ρ, ϵ, n, L = OBS_CORR_LEN)
    σp = σ^2 / (1 - ρ^2); H = abs.(collect(1:n)' .- collect(1:n))
    return L > 0 ? σp .* ρ .^ H .+ (ϵ * ϵ') .* exp.(-H ./ L) : σp .* ρ .^ H .+ Diagonal(ϵ .^ 2)
end

tg = CSV.read(TARGETS, DataFrame)
fy = [Int(tg.year[i]) for i in 1:nrow(tg) if tg.year[i] >= FIT_Y0 && !ismissing(tg.ais[i]) && !isnan(Float64(tg.ais[i]))]
sort!(fy); ri = [findfirst(==(y), tg.year) for y in fy]
eps = epsband(Float64.(tg.ais_lo[ri]), Float64.(tg.ais_hi[ri])); nY = length(fy)
σ = median(CSV.read(POSTP, DataFrame).sd_ais)
@printf("%s | tag %s | %d-%d (%d yr) | sd_ais median %.4f | eps mean %.4f | amplitude %.2f cm at the end\n",
        SCRIPT, TAG, fy[1], fy[end], nY, σ, mean(eps), AMP)

## The shapes, all AMP at the final year. `onset2000_ramp` is the additional discharge response's own
## shape; `step2018` is the pause-like feature that the per-bin attribution found carries the penalty.
ramp_from(y) = (local d = Float64.(max.(fy .- y, 0)); d ./ d[end] .* AMP)
shapes = Dict(
  "constant_offset"  => fill(AMP, nY),
  "linear_1900"      => ramp_from(fy[1]),
  "onset1979_ramp"   => ramp_from(1979),
  "onset2000_ramp"   => ramp_from(2000),
  "step2018"         => Float64.(fy .>= 2018) .* AMP,
  "kink2018_flatten" => (local d = min.(Float64.(max.(fy .- 2000, 0)), 18.0); d ./ d[end] .* AMP),
  ## The shape the ramp ACTUALLY produces over the pause: flat through 2017, then diverging linearly
  ## to the end of the record. This -- not the idealised step -- is what the per-bin attribution is
  ## paying for, so it is the one to price.
  "divergence_2018_on" => ramp_from(2017),
)
ORDER = ["constant_offset", "linear_1900", "onset1979_ramp", "onset2000_ramp", "kink2018_flatten",
         "divergence_2018_on", "step2018"]

rows = DataFrame()
for ρ in RHOS
    Sinv = inv(Symmetric(ais_cov(σ, ρ, eps, nY)))
    for k in ORDER
        d = shapes[k]
        append!(rows, DataFrame(rho = ρ, shape = k, amp_cm = AMP, q = d' * Sinv * d,
                                dloglik = -0.5 * (d' * Sinv * d)))
    end
end
rows.provenance .= "$SCRIPT | tag $TAG | q = d'*Sigma^-1*d for unit shapes d, Sigma = ais_cov(sd_ais " *
    "median $(round(σ, digits=4)), rho, eps, L=$OBS_CORR_LEN) on $(fy[1])-$(fy[end]) of $(basename(TARGETS)) | " *
    "every shape = $AMP cm at the final year | no model runs, no RNG | $(now())"
CSV.write(joinpath(REPO, "outputs/diag_ais_objective_shape_sensitivity_$TAG.csv"), rows)

println("\nPenalty q for a $AMP cm discrepancy of each SHAPE (bigger = the objective sees it more clearly)")
@printf("  %-20s", "shape"); for ρ in RHOS; @printf("%12s", "rho $ρ"); end; println()
for k in ORDER
    @printf("  %-20s", k)
    for ρ in RHOS; @printf("%12.2f", rows[(rows.rho .== ρ) .& (rows.shape .== k), :q][1]); end
    println()
end
println("\nRelative to a constant offset of the same size (ratio; 1.0 = as visible as a pure level shift)")
for k in ORDER
    @printf("  %-20s", k)
    for ρ in RHOS
        b = rows[(rows.rho .== ρ) .& (rows.shape .== "constant_offset"), :q][1]
        @printf("%12.1f", rows[(rows.rho .== ρ) .& (rows.shape .== k), :q][1] / b)
    end
    println()
end
println("\nwrote outputs/diag_ais_objective_shape_sensitivity_$TAG.csv")
