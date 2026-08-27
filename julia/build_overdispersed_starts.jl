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
##
## ---------------------------------------------------------------------------
## 2026-08-27: OPTIONAL flags, all default-off. With none of them the behaviour is
## EXACTLY as above (one chain, ais_iceflow0 quantiles, canonical output path).
##
##   --param=NAME          dispersion axis            (default ais_iceflow0)
##   --targets=v1,v2,v3,v4 explicit target values on that axis, in seed order
##                         2026/2027/2028/2029       (default: the 4 quantiles)
##   --sources=f1,f2,f3,f4 per-row source chain files (default: ARGS[1] for all 4)
##   --filter=NAME:lo:hi   keep only draws with lo <= NAME <= hi (repeatable)
##   --out=PATH            output file                (default the canonical path)
##
## WHY --sources. The T_on modes do not co-exist in one chain: LOW, MID and HIGH each
## dominate a DIFFERENT chain, so a T_on-dispersed starts file has to draw one row from
## each. A single-chain quantile sweep cannot reach them.
##
## WHY --filter. Draws are real posterior samples FROM THE ARM THAT PRODUCED THEM, and a
## different arm's prior may exclude them. L16/L17 ran amp ~ N(1.09, 0.180) on [0.55, 1.63];
## an arm running L14's N(0.95, 0.10) on [0.70, 1.25] gives logposterior = -Inf for any start
## with amp outside ITS bounds, and every MH ratio becomes NaN. Filter at BUILD time.
## The calibrator's own finite-logposterior assertion remains the authoritative gate.
##
## WHY --out. outputs/mcmc/overdispersed_starts.csv is L14's file and is load-bearing: L14
## AND L18 both ran on it, and reusing it unrebuilt is what makes their comparison exactly
## controlled. Never overwrite it to build a different arm — write elsewhere and point the
## calibrator at it with its --starts= flag.
## ============================================================================
using CSV, DataFrames, Statistics, Printf

_argval(p) = (i = findfirst(a -> startswith(a, p), ARGS); i === nothing ? nothing : ARGS[i][length(p)+1:end])
const PARAM    = something(_argval("--param="), "ais_iceflow0")
const TARGETS  = (v = _argval("--targets="); v === nothing ? nothing : parse.(Float64, split(v, ",")))
const SOURCES  = (v = _argval("--sources="); v === nothing ? nothing : String.(split(v, ",")))
const OUTPATH  = _argval("--out=")
const FILTERS  = [(f = split(a[length("--filter=")+1:end], ":");
                   (name = String(f[1]), lo = parse(Float64, f[2]), hi = parse(Float64, f[3])))
                  for a in ARGS if startswith(a, "--filter=")]

const REPO = abspath(joinpath(@__DIR__, ".."))
chain_path = length(ARGS) >= 1 ? ARGS[1] :
    joinpath(REPO, "outputs/mcmc/chain_ext_seed2026_n1000000.csv")
isfile(chain_path) || error("tuning chain not found: $chain_path")

const SEEDS = [2026, 2027, 2028, 2029]
QUANTILES = [0.02, 0.35, 0.65, 0.98]

# post-burn (2nd half) of one source, minus bookkeeping columns, minus filtered-out draws
function post_burn(path)
    d = CSV.read(path, DataFrame)
    PARAM in names(d) || error("$(basename(path)) missing column $PARAM")
    b = d[(nrow(d)÷2 + 1):end, :]
    for c in ("log_post", "accept_rate"); c in names(b) && select!(b, Not(c)); end
    n0 = nrow(b)
    for f in FILTERS
        f.name in names(b) || error("$(basename(path)) missing filter column $(f.name)")
        b = b[(b[!, f.name] .>= f.lo) .& (b[!, f.name] .<= f.hi), :]
    end
    isempty(b) && error("$(basename(path)): every post-burn draw was excluded by --filter")
    !isempty(FILTERS) && println("  $(basename(path)): $(nrow(b))/$n0 post-burn draws pass the filters")
    return b
end

srcs = SOURCES === nothing ? fill(chain_path, 4) : SOURCES
length(srcs) == 4 || error("--sources needs exactly 4 comma-separated files, got $(length(srcs))")
for f in srcs; isfile(f) || error("source chain not found: $f"); end

if !isempty(FILTERS)
    println("Feasibility filters (a start outside ANOTHER arm's prior bounds gives logpost = -Inf):")
    for f in FILTERS; println("  $(f.name) in [$(f.lo), $(f.hi)]"); end
end

# per-row targets: explicit, or this source's own quantiles of PARAM
frames = [post_burn(f) for f in srcs]
targets = TARGETS === nothing ?
    [quantile(frames[i][!, PARAM], QUANTILES[i]) for i in 1:4] : TARGETS
length(targets) == 4 || error("--targets needs exactly 4 values, got $(length(targets))")

rows = [argmin(abs.(frames[i][!, PARAM] .- targets[i])) for i in 1:4]
starts = reduce(vcat, [frames[i][rows[i]:rows[i], :] for i in 1:4])

out = OUTPATH === nothing ? joinpath(REPO, "outputs/mcmc/overdispersed_starts.csv") : OUTPATH
CSV.write(out, starts)
println("\nWrote $out   (axis = $PARAM)")
println("  seed  target      picked      source")
for i in 1:4
    @printf("  %d  %10.4f  %10.4f      %s\n", SEEDS[i], targets[i],
            frames[i][rows[i], PARAM], basename(srcs[i]))
end
v = starts[!, PARAM]
println("  $PARAM start spread: $(round(minimum(v),digits=3)) .. $(round(maximum(v),digits=3))")
# ⚠ an all-one-mode starts file has NO POWER on the mode question — say so loudly.
if maximum(v) - minimum(v) < 1e-6
    println("  ⚠ WARNING: all four starts are identical on $PARAM — this arm has NO dispersion.")
end
