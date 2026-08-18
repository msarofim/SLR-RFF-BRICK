## ============================================================================
## diag_gis_block_convergence.jl — is the GREENLAND BLOCK converged?
##
## `postprocess_mcmc_ext.jl --tag=L10` reports 19 non-converged marginals and
## names only the worst four in its summary, of which one is Greenland
## (`gis_f`, R-hat 1.335). That understates the situation: asked directly, FOUR
## of the seven sampled Greenland parameters fail, and they fail in a pattern
## that matters for how the module may be reported. This file asks the question
## for that block alone so the answer is on disk instead of in a handoff.
##
## CONVENTION, matching postprocess_mcmc_ext.jl exactly (so the numbers are
## comparable to the ones it prints):
##   * burn the FIRST HALF of each chain;
##   * R-hat and ESS from MCMCDiagnosticTools;
##   * ESS with maxlag passed EXPLICITLY and capped well below the chain length.
##     The default maxlag = 250 floors ESS (memory `feedback_mcmc_ess_maxlag_trap`),
##     but maxlag = n trips an internal overflow at >= 1e6 draws and returns a
##     silently inflated value. min(n-4, 200_000) is the same cap postprocess uses.
##
## Per-chain medians are printed alongside, because for a poorly-mixing axis the
## chain medians are the more convincing diagnostic: a large R-hat is a statistic,
## whereas four medians spanning 3x is four chains sampling four places.
##
##   julia --project=julia_v2 julia/diag_gis_block_convergence.jl [--tag=L10]
## Writes outputs/mcmc/gis_block_convergence_<tag>.csv
## ============================================================================
using CSV, DataFrames, Printf, Statistics, MCMCDiagnosticTools

const REPO  = abspath(joinpath(@__DIR__, ".."))
## Default = the CANONICAL vintage. Not derived from LADRILLO_POSTERIOR_CSV
## (ladrillo_projection.jl pulls in Mimi/MimiBRICK, and this is a pure-CSV
## diagnostic) — that constant remains the authority, so update both together.
const TAG   = let i = findfirst(a -> startswith(a, "--tag="), ARGS)
    i === nothing ? "L12" : ARGS[i][7:end]
end
const SEEDS = [2026, 2027, 2028, 2029]
const NITER = 2000000
const RHAT_OK = 1.05
## The seven sampled Greenland parameters, plus gis_amp. gis_amp is
## LIKELIHOOD-INERT (the calibrator runs to 2026, so only two of its years fall
## past the splice seam) and is included precisely as the control: it should
## reproduce its own truncated prior at a near-perfect R-hat, and if it does not,
## the problem is the sampler and not the Greenland likelihood.
const COLS = ["gis_c1", "gis_c0", "gis_f", "gis_alpha_f", "gis_beta_f",
              "gis_alpha_s", "gis_beta_s", "gis_amp"]
const OUT = joinpath(REPO, "outputs/mcmc", "gis_block_convergence_$(TAG).csv")

chains = DataFrame[]
for sd in SEEDS
    f = joinpath(REPO, "outputs/mcmc", "chain_$(TAG)_seed$(sd)_n$(NITER).csv")
    isfile(f) || error("missing chain file $f")
    d = CSV.read(f, DataFrame; select = COLS)
    missing_cols = setdiff(COLS, names(d))
    isempty(missing_cols) || error("$(basename(f)) is missing $(join(missing_cols, ", ")) " *
                                   "— is this a Ladrillo 1.0 (greenland_ab) chain?")
    push!(chains, d[(nrow(d) ÷ 2 + 1):end, :])
    @printf("  %s  (%d post-burn)\n", basename(f), nrow(chains[end]))
    flush(stdout)
end
n = minimum(nrow.(chains))

out = DataFrame(vcat(["param" => String[], "rhat" => Float64[], "ess" => Float64[],
                      "converged" => Bool[], "med_spread_ratio" => Float64[]],
                     ["med_seed$sd" => Float64[] for sd in SEEDS]))
@printf("\nGreenland block convergence | tag %s | %d chains x %d post-burn | R-hat OK < %.2f\n\n",
        TAG, length(chains), n, RHAT_OK)
@printf("%-14s %8s %9s  %s\n", "param", "rhat", "ess", "per-chain medians")
for c in COLS
    arr = Array{Float64}(undef, n, length(chains), 1)
    for (j, ch) in enumerate(chains)
        arr[:, j, 1] = Float64.(ch[1:n, c])
    end
    r = rhat(arr)[1]
    e = ess(arr; maxlag = min(n - 4, 200_000))[1]
    meds = [median(Float64.(ch[1:n, c])) for ch in chains]
    ok = isfinite(r) && r < RHAT_OK
    push!(out, (c, r, e, ok, maximum(meds) / minimum(meds), meds...))
    @printf("%-14s %8.3f %9.1f  %s  %s\n", c, r, e,
            join([@sprintf("%.4f", m) for m in meds], " "),
            ok ? "" : "NOT CONVERGED")
end
CSV.write(OUT, out)
@printf("\n%d of %d NOT converged\nwrote %s\n",
        count(.!out.converged), nrow(out), relpath(OUT, REPO))
