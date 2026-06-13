## ============================================================================
## postprocess_mcmc_ext.jl  —  postprocess the EXTENDED-target MCMC chains
##
## Variant of postprocess_mcmc.jl for the post-2018-extended re-fit
## (calibrate_mcmc_ext.jl). Globs chain_ext_seed*.csv, burns first half, R̂/ESS,
## and writes a SEPARATE posterior subsample + adapted cov so the 2018-baseline
## outputs (parameters_subsample_brick_mengel.csv, adapted_cov.csv) are NOT clobbered.
##
##   julia --project=julia_v2 julia/postprocess_mcmc_ext.jl [n_subsample]
## ============================================================================

using CSV, DataFrames, Statistics, Printf, LinearAlgebra
using MCMCDiagnosticTools

const REPO = abspath(joinpath(@__DIR__, ".."))
const TAG  = "ext"
N_SUB = length(ARGS)>=1 ? parse(Int,ARGS[1]) : 10000
const MCMCDIR = joinpath(REPO, "outputs/mcmc")
files = [joinpath(MCMCDIR,f) for f in readdir(MCMCDIR) if startswith(f,"chain_$(TAG)_seed") && endswith(f,".csv")]
isempty(files) && error("no chain_$(TAG)_seed*.csv files in outputs/mcmc/")
println("Combining $(length(files)) chains:")
chains = DataFrame[]
for f in files
    d = CSV.read(f, DataFrame)
    burn = d[(nrow(d)÷2+1):end, :]
    push!(chains, burn)
    @printf("  %s  (%d post-burn, accept %.3f)\n", basename(f), nrow(burn), d.accept_rate[1])
end
pnames = [n for n in names(chains[1]) if !(n in ["log_post","accept_rate"])]

nmin = minimum(nrow.(chains)); nc = length(chains)
println("\n$(nc) chains × $nmin draws. Convergence (target R̂<1.05, ESS>400):")
bad = String[]
for p in pnames
    arr = Array{Float64}(undef, nmin, nc)
    for (ci,ch) in enumerate(chains); arr[:,ci] = Float64.(ch[1:nmin, p]); end
    r = rhat(arr); e = ess(arr)
    (r > 1.05 || e < 400) && (push!(bad, p); @printf("  %-24s R̂=%.3f ESS=%.0f  <-- check\n", p, r, e))
end
isempty(bad) ? println("  all params converged (R̂<1.05, ESS>400).") :
               println("  $(length(bad)) params not yet converged -> longer chains.")

pool = vcat(chains...)
n = nrow(pool); step = max(1, n ÷ N_SUB)
sub = pool[1:step:end, :][1:min(N_SUB, end), :]
out = joinpath(REPO, "data/MimiBRICK/parameters_subsample_brick_mengel_$(TAG).csv")
CSV.write(out, sub[:, pnames])
@printf("\nWrote %s  (%d-member posterior subsample of %d pooled draws)\n", out, nrow(sub), n)

M = Matrix{Float64}(pool[:, pnames])
CSV.write(joinpath(MCMCDIR,"adapted_cov_$(TAG).csv"), DataFrame(cov(M) .+ 1e-10*I(size(M,2)), :auto))
println("Wrote outputs/mcmc/adapted_cov_$(TAG).csv (empirical posterior cov) -> seeds the next ext run.")

# quick A/B vs the 2018-baseline subsample for the key AIS knob + te_α
base = joinpath(REPO, "data/MimiBRICK/parameters_subsample_brick_mengel.csv")
if isfile(base)
    b = CSV.read(base, DataFrame)
    println("\nKey-param medians  (ext vs 2018-baseline):")
    for nm in ["ais_ocean_temperature₀","anto_alpha","thermal_alpha","gic_a","gic_T_lia","greenland_a"]
        (nm in pnames && nm in names(b)) || continue
        @printf("  %-24s ext %.3g   base %.3g   Δ %+.3g\n",
                nm, median(sub[!,nm]), median(b[!,nm]), median(sub[!,nm])-median(b[!,nm]))
    end
end
if !isempty(bad)
    println("\n** NOT CONVERGED ** ($(length(bad)) params). Re-run longer: bash run_mcmc_ext_local.sh 500000")
end
