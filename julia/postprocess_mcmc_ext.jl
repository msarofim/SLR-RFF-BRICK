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
const TAG  = let i = findfirst(a -> startswith(a, "--tag="), ARGS)   # 2026-07-22: allow
    i === nothing ? "ext" : ARGS[i][7:end]                            # alternate chain sets
end
const ESS_MIN = 400
# Writing a posterior subsample or a proposal seed from NON-CONVERGED chains is how a bad
# posterior reaches downstream consumers silently. Both writes are gated on convergence;
# pass --force to override (the files then carry a _NOTCONVERGED suffix).
#
# --accept-slr: accepted-on-deliverable criterion (Marcus 2026-07-19). The AIS geometry
# block is a compensating ridge whose MARGINALS will not converge in feasible compute,
# but the chains agree on projected SLR. If outputs/mcmc/slr_convergence_ext.csv
# (written by diag_slr_convergence_by_chain.jl, and FRESHER than every chain file)
# shows R̂<1.05 at all horizons, the canonical subsample/seed are written even though
# the parameter-level gate fails.
const FORCE = "--force" in ARGS
const ACCEPT_SLR = "--accept-slr" in ARGS
N_SUB = length(ARGS)>=1 && !startswith(ARGS[1],"--") ? parse(Int,ARGS[1]) : 10000
const MCMCDIR = joinpath(REPO, "outputs/mcmc")
files = [joinpath(MCMCDIR,f) for f in readdir(MCMCDIR) if startswith(f,"chain_$(TAG)_seed") && endswith(f,".csv")]
isempty(files) && error("no chain_$(TAG)_seed*.csv files in outputs/mcmc/")
println("Combining $(length(files)) chains:")
# Read column-selectively. A full 37-col x 2e6-row x 4-chain read is ~5.7 GB and on a
# swap-bound machine the reads come back CORRUPTED (rhat/ess silently return NaN for every
# param -- which, combined with a NaN-permissive gate, once falsely certified a non-converged
# run). Read only the columns we diagnose.
hdr = propertynames(CSV.read(files[1], DataFrame; limit=0))
wanted = [c for c in hdr if c != :accept_rate]
chains = DataFrame[]
chain_files = String[]
for f in files
    d = CSV.read(f, DataFrame; select=wanted)
    burn = d[(nrow(d)÷2+1):end, :]
    push!(chains, burn)
    push!(chain_files, f)
    @printf("  %s  (%d post-burn)\n", basename(f), nrow(burn))
end
# Guard against stray short chains (smoke tests, aborted runs) matching the glob:
# one 2-iteration file once collapsed nmin to 1 (all R̂/ESS non-finite) AND leaked a
# smoke-test draw into the subsample. Refuse loudly rather than skip silently.
nrows = nrow.(chains)
if minimum(nrows) < 0.5 * maximum(nrows)
    for (f, n) in zip(chain_files, nrows)
        @printf("  %-60s %d post-burn rows\n", basename(f), n)
    end
    error("chain length mismatch: shortest ($(minimum(nrows))) < half of longest " *
          "($(maximum(nrows))). A stray non-current chain matches the chain_$(TAG)_seed* " *
          "glob — quarantine it (see outputs/quarantine/20260720_smoke_chain_n2/).")
end
pnames = [n for n in names(chains[1]) if !(n in ["accept_rate"])]   # log_post IS diagnosed (see below)

nmin = minimum(nrow.(chains)); nc = length(chains)
println("\n$(nc) chains × $nmin draws. Convergence (target R̂<1.05, ESS>$(ESS_MIN)):")
bad = String[]
for p in pnames
    arr = Array{Float64}(undef, nmin, nc)
    for (ci,ch) in enumerate(chains); arr[:,ci] = Float64.(ch[1:nmin, p]); end
    # ESS MUST pass maxlag explicitly. MCMCDiagnosticTools' default maxlag=250 truncates the
    # Geyer initial-monotone sum at tau<=500, which FLOORS ESS at ntotal/500 -- a censored
    # constant, not a measurement. With tau>1e5 for the AIS geometry block, the default
    # over-reported ESS by 150-270x (e.g. ais_iceflow0 run-2: reported 4034, true 15) and made
    # the `e < ESS_MIN` half of the gate dead code for any run over 200k pooled draws.
    # BUT maxlag = size(arr,1) is ALSO wrong: for >=1e6-draw chains it trips an internal
    # "draws after splitting is 0" path and returns NaN, and NaN < ESS_MIN is FALSE -- so a
    # NaN-ESS param silently PASSES the gate (this falsely certified the sigma-fix re-baseline
    # as converged). Cap maxlag well below the chain length, and treat non-finite ESS as FAIL.
    r = rhat(arr); e = ess(arr; maxlag = min(nmin - 4, 200_000))
    conv = isfinite(r) && isfinite(e) && r <= 1.05 && e >= ESS_MIN
    τ = (nmin*nc) / max(e, 1e-9)
    conv || (push!(bad, p); @printf("  %-24s R̂=%.3f ESS=%.1f τ=%.0f  <-- check\n", p, r, e, τ))
end
isempty(bad) ? println("  all params converged (R̂<1.05, ESS>$(ESS_MIN)).") :
               println("  $(length(bad)) params NOT converged.")
const CONVERGED = isempty(bad)

# --accept-slr: check the deliverable-level diagnostic. Freshness is load-bearing —
# a stale CSV from a previous run would bless chains it never saw.
slr_accepted = false
if !CONVERGED && ACCEPT_SLR
    slr_csv = joinpath(MCMCDIR, "slr_convergence_$(TAG).csv")
    if !isfile(slr_csv)
        println("\n--accept-slr: $slr_csv not found. Run diag_slr_convergence_by_chain.jl first.")
    elseif mtime(slr_csv) < maximum(mtime.(files))
        println("\n--accept-slr: $slr_csv is OLDER than the newest chain file -> STALE; refusing.")
        println("Re-run diag_slr_convergence_by_chain.jl on the current chains.")
    else
        sd = CSV.read(slr_csv, DataFrame)
        ok = all(isfinite.(sd.rhat)) && all(sd.rhat .< 1.05)
        println("\n--accept-slr: deliverable-level convergence from $(basename(slr_csv)):")
        for r in eachrow(sd)
            @printf("  SLR@%d  R̂=%.3f  ESS=%.1f\n", r.horizon, r.rhat, r.ess)
        end
        if ok
            slr_accepted = true
            println("ACCEPTED ON DELIVERABLE: parameter marginals not converged (compensating")
            println("AIS-geometry ridge), but projected SLR R̂<1.05 at all horizons -> writing")
            println("canonical outputs (accepted-on-deliverable criterion, Marcus 2026-07-19).")
        else
            println("SLR-level R̂ >= 1.05 at some horizon -> NOT accepted.")
        end
    end
end

pool = vcat(chains...)
n = nrow(pool); step = max(1, n ÷ N_SUB)
sub = pool[1:step:end, :][1:min(N_SUB, end), :]
parnames = [p for p in pnames if p != "log_post"]     # subsample/cov exclude log_post

if CONVERGED || slr_accepted || FORCE
    sfx = (CONVERGED || slr_accepted) ? "" : "_NOTCONVERGED"
    out = joinpath(REPO, "data/MimiBRICK/parameters_subsample_brick_mengel_$(TAG)$(sfx).csv")
    CSV.write(out, sub[:, parnames])
    @printf("\nWrote %s  (%d-member subsample of %d pooled draws)\n", out, nrow(sub), n)
    # The proposal seed is cov over POOLED draws = within + between chain variance. For a
    # non-converged ensemble that inflates the seed by ~R̂^2 in exactly the worst directions.
    M = Matrix{Float64}(pool[:, parnames])
    cout = joinpath(MCMCDIR, "adapted_cov_$(TAG)$(sfx).csv")
    CSV.write(cout, DataFrame(cov(M) .+ 1e-10*I(size(M,2)), :auto))
    println("Wrote $(basename(cout)) (empirical posterior cov) -> seeds the next ext run.")
else
    println("\nNOT CONVERGED -> REFUSING to write the canonical posterior subsample or the")
    println("proposal seed. A subsample drawn from non-converged chains silently becomes the")
    println("posterior for every downstream consumer; a proposal seed pooled over disagreeing")
    println("chains is inflated by between-chain variance. Re-run with --force to write both")
    println("with a _NOTCONVERGED suffix (they will NOT land on the canonical paths).")
end

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
    if slr_accepted
        println("\n** $(length(bad)) marginals not converged; ACCEPTED ON DELIVERABLE (--accept-slr). **")
    else
        println("\n** NOT CONVERGED ** ($(length(bad)) params). Re-run longer, or check the")
        println("deliverable with diag_slr_convergence_by_chain.jl and re-run with --accept-slr.")
    end
end
