## ============================================================================
## build_overdispersed_starts.jl — build outputs/mcmc/overdispersed_starts.csv
##
## Over-dispersed starts for the 4 production chains MUST be REAL posterior draws:
## a jointly-perturbed geometry/AIS vector leaves the feasible region even when every
## marginal is in bounds (200/200 random-jitter starts gave non-finite logposterior;
## see calibrate_mcmc_ext.jl --overdisperse comment). We pick 4 draws from a TUNING
## chain's 2nd half at `ais_iceflow0` quantiles 0.02 / 0.35 / 0.65 / 0.98 — dispersed
## along the direction that actually fails to mix (the AIS-geometry ridge), feasible by
## construction. Rows land in seed order 2026/2027/2028/2029.
##
##   julia --project=julia_v2 julia/build_overdispersed_starts.jl <tuning_chain.csv>
## ============================================================================
using CSV, DataFrames, Statistics

const REPO = abspath(joinpath(@__DIR__, ".."))
chain_path = length(ARGS) >= 1 ? ARGS[1] :
    joinpath(REPO, "outputs/mcmc/chain_ext_seed2026_n1000000.csv")
isfile(chain_path) || error("tuning chain not found: $chain_path")

df = CSV.read(chain_path, DataFrame)
"ais_iceflow0" in names(df) || error("chain missing ais_iceflow0 column")
burn = df[(nrow(df)÷2 + 1):end, :]                       # 2nd half
# drop the bookkeeping columns; the starts file must carry exactly the θ columns pn0
for c in ("log_post", "accept_rate"); c in names(burn) && select!(burn, Not(c)); end

QUANTILES = [0.02, 0.35, 0.65, 0.98]
iceflow = burn.ais_iceflow0
targets = quantile(iceflow, QUANTILES)
# nearest ACTUAL draw to each quantile target (a real, feasible θ — not an interpolated one)
rows = [argmin(abs.(iceflow .- t)) for t in targets]
starts = burn[rows, :]

out = joinpath(REPO, "outputs/mcmc/overdispersed_starts.csv")
CSV.write(out, starts)
println("Wrote $out")
println("  seed / ais_iceflow0-quantile / picked ais_iceflow0:")
for (i, (q, r)) in enumerate(zip(QUANTILES, rows))
    println("    seed $([2026,2027,2028,2029][i])  q=$(q)  ais_iceflow0=$(round(iceflow[r], digits=4))")
end
# spread sanity: the starts should straddle the ridge
println("  ais_iceflow0 start spread: $(round(minimum(starts.ais_iceflow0),digits=3)) .. " *
        "$(round(maximum(starts.ais_iceflow0),digits=3))  (chain 2nd-half range " *
        "$(round(minimum(iceflow),digits=3)) .. $(round(maximum(iceflow),digits=3)))")
