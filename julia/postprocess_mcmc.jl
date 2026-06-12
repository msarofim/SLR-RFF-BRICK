## ============================================================================
## postprocess_mcmc.jl  —  combine chains, convergence diagnostics, subsample
##
## Reads all outputs/mcmc/chain_seed*_n*.csv (one RAM chain per seed), burns the
## first half, computes Gelman-Rubin R̂ + ESS per parameter (MCMCDiagnosticTools),
## reports non-converged params, and writes a thinned posterior subsample
## `parameters_subsample_brick_mengel.csv` that feeds the FaIR-forced projection +
## importance-weighting pipeline (project_ssps_2100_ensemble.jl analog).
##
##   julia --project=julia_v2 julia/postprocess_mcmc.jl [n_subsample]
## ============================================================================

using CSV, DataFrames, Statistics, Glob, Printf
using MCMCDiagnosticTools

const REPO = abspath(joinpath(@__DIR__, ".."))
N_SUB = length(ARGS)>=1 ? parse(Int,ARGS[1]) : 10000
files = glob("outputs/mcmc/chain_seed*_n*.csv", REPO)
isempty(files) && error("no chain files in outputs/mcmc/")
println("Combining $(length(files)) chains:")
chains = DataFrame[]
for f in files
    d = CSV.read(f, DataFrame)
    burn = d[(nrow(d)÷2+1):end, :]                    # discard first half (burn-in)
    push!(chains, burn)
    @printf("  %s  (%d post-burn, accept %.3f)\n", basename(f), nrow(burn), d.accept_rate[1])
end
pnames = [n for n in names(chains[1]) if !(n in ["log_post","accept_rate"])]

# Gelman-Rubin R̂ + ESS (per param, across chains) via MCMCDiagnosticTools
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

# pooled subsample
pool = vcat(chains...)
n = nrow(pool); step = max(1, n ÷ N_SUB)
sub = pool[1:step:end, :][1:min(N_SUB, end), :]
out = joinpath(REPO, "data/MimiBRICK/parameters_subsample_brick_mengel.csv")
CSV.write(out, sub[:, pnames])
@printf("\nWrote %s  (%d-member posterior subsample of %d pooled draws)\n", out, nrow(sub), n)
println("Drop-in for the FaIR-forced projection + importance-weighting pipeline (build_brick_mengel).")
