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
## THE COLUMN SET IS VARIANT-AWARE as of 2026-08-23 — see GIS_CORE_COLS below.
## Before that it was the Ladrillo 1.0 list alone, so the only certificate ever
## produced (gis_block_convergence_L10.csv) describes the whole-sheet greenland_ab
## model, NOT the two-basin reparameterised Greenland that L14 ships.
##
##   julia --project=julia_v2 julia/diag_gis_block_convergence.jl [--tag=L14]
## Writes outputs/mcmc/gis_block_convergence_<tag>.csv
## ============================================================================
using CSV, DataFrames, Printf, Statistics, MCMCDiagnosticTools

const REPO  = abspath(joinpath(@__DIR__, ".."))
## Default = the CANONICAL vintage. Not derived from LADRILLO_POSTERIOR_CSV
## (ladrillo_projection.jl pulls in Mimi/MimiBRICK, and this is a pure-CSV
## diagnostic) — that constant remains the authority, so update both together.
const TAG   = let i = findfirst(a -> startswith(a, "--tag="), ARGS)
    i === nothing ? "L14" : ARGS[i][7:end]
end
const SEEDS = [2026, 2027, 2028, 2029]
const NITER = 2000000
const RHAT_OK = 1.05
## THE COLUMN SET FOLLOWS THE PARAMETERISATION — it is NOT one hardcoded list.
## The original list here was the seven sampled parameters of Ladrillo 1.0
## (greenland_ab, whole sheet, native slow channel). L12 reparameterised the slow
## channel to (ell, w) and L14 added a sampled basin scale, so a single list would
## hard-error on the CANONICAL vintage — which is exactly what it did until
## 2026-08-23: this diagnostic had never been run on the Greenland that ships.
##
## Resolved by composition, from the chain header, with every branch NAMED:
##   core     always sampled, unchanged since 1.0
##   slow     EITHER the native pair (alpha_s, beta_s)  = Ladrillo 1.0 / L10-L11
##            OR the reparameterised pair (ell, w)      = L12 onward
##   control  gis_amp
##   basins   whichever basin scales the chain carries (none / mid+high / high)
## The order reproduces the 1.0 list EXACTLY on a native-slow chain, so L10 is
## byte-identical.
##
## gis_amp is LIKELIHOOD-INERT (the calibrator runs to 2026, so only two of its
## years fall past the splice seam) and is included precisely as the control: it
## should reproduce its own truncated prior at a near-perfect R-hat, and if it does
## not, the problem is the sampler and not the Greenland likelihood.
const GIS_CORE_COLS    = ["gis_c1", "gis_c0", "gis_f", "gis_alpha_f", "gis_beta_f"]
const GIS_SLOW_NATIVE  = ["gis_alpha_s", "gis_beta_s"]
const GIS_SLOW_REPARAM = ["gis_slow_ell", "gis_slow_w"]
const GIS_CONTROL_COL  = "gis_amp"
const GIS_BASIN_COLS   = ["gis_s_mid", "gis_s_high"]

## THE SPREAD RATIO IS MEASURED ON THE NATIVE SCALE, and that is not cosmetic.
## med_spread_ratio exists to carry the sentence "four chain medians spanning 3x is
## four chains sampling four places" — max/min of the SAMPLED value only means that
## for a positive, linearly-sampled parameter. Two of the parameters this file must
## now report are sampled on a log scale and are NEGATIVE over their whole support
## (gis_slow_ell in [-7.06, -3.89], gis_s_high in [-1.24, -0.11] on the L14
## subsample), where max/min is < 1 and SHRINKS as the true spread grows — the
## statistic would have reported the opposite of what it claims, on precisely the
## two parameters the restructure added. Applied per the map the projection kernel
## uses: r_s = exp(gis_slow_ell), s_high = 10^gis_s_high (ladrillo_projection.jl).
## Everything absent from this map is :linear, so the 1.0 columns are unchanged.
const GIS_COL_SCALE = Dict("gis_slow_ell" => :log,
                           "gis_s_mid"    => :log10,
                           "gis_s_high"   => :log10)
gis_native(m::Float64, sc::Symbol) = sc === :log   ? exp(m) :
                                     sc === :log10 ? 10.0^m : m

"""Greenland block columns carried by a chain header, in report order."""
function gis_block_cols(hdr::Vector{String})
    core = intersect(GIS_CORE_COLS, hdr)
    length(core) == length(GIS_CORE_COLS) ||
        error("chain is missing core Greenland columns " *
              "$(join(setdiff(GIS_CORE_COLS, hdr), ", ")) — is this a Greenland chain at all?")
    has_native  = all(c -> c in hdr, GIS_SLOW_NATIVE)
    has_reparam = all(c -> c in hdr, GIS_SLOW_REPARAM)
    ## BOTH is not a merge case, it is a chain that cannot be interpreted: the two
    ## pairs are a forward map and its inverse, so a file carrying both has had a
    ## derived pair written back into it and we cannot tell which one was sampled.
    (has_native && has_reparam) &&
        error("chain carries BOTH the native slow pair and the reparameterised one — " *
              "cannot tell which was sampled; R-hat on a derived column is not a " *
              "convergence statement about the sampler")
    slow = has_native ? GIS_SLOW_NATIVE : has_reparam ? GIS_SLOW_REPARAM :
        error("chain carries NEITHER (" * join(GIS_SLOW_NATIVE, ", ") * ") nor (" *
              join(GIS_SLOW_REPARAM, ", ") * ") — the slow channel is unidentifiable " *
              "from this header")
    return vcat(core, slow, [GIS_CONTROL_COL], intersect(GIS_BASIN_COLS, hdr))
end

const HDR = String.(names(CSV.read(joinpath(REPO, "outputs/mcmc",
                "chain_$(TAG)_seed$(first(SEEDS))_n$(NITER).csv"), DataFrame; limit = 1)))
const COLS = gis_block_cols(HDR)
const SLOW_KIND = all(c -> c in COLS, GIS_SLOW_NATIVE) ? "native" : "reparam"
const OUT = joinpath(REPO, "outputs/mcmc", "gis_block_convergence_$(TAG).csv")

chains = DataFrame[]
for sd in SEEDS
    f = joinpath(REPO, "outputs/mcmc", "chain_$(TAG)_seed$(sd)_n$(NITER).csv")
    isfile(f) || error("missing chain file $f")
    d = CSV.read(f, DataFrame; select = COLS)
    missing_cols = setdiff(COLS, names(d))
    ## COLS is derived from the FIRST seed's header, so this fires when the four
    ## chains of one tag disagree with each other — a different failure from the
    ## one gis_block_cols reports, and a worse one.
    isempty(missing_cols) || error("$(basename(f)) is missing $(join(missing_cols, ", ")) " *
                                   "— the chains of tag $TAG do not carry the same " *
                                   "Greenland parameterisation")
    push!(chains, d[(nrow(d) ÷ 2 + 1):end, :])
    @printf("  %s  (%d post-burn)\n", basename(f), nrow(chains[end]))
    flush(stdout)
end
n = minimum(nrow.(chains))

out = DataFrame(vcat(["param" => String[], "scale" => String[], "rhat" => Float64[],
                      "ess" => Float64[], "converged" => Bool[],
                      "med_spread_ratio" => Float64[]],
                     ["med_seed$sd" => Float64[] for sd in SEEDS]))
@printf("\nGreenland block convergence | tag %s | %d chains x %d post-burn | R-hat OK < %.2f\n",
        TAG, length(chains), n, RHAT_OK)
@printf("slow channel: %s (%s)\n\n", SLOW_KIND, join(COLS[6:7], ", "))
@printf("%-14s %6s %8s %9s %8s  %s\n",
        "param", "scale", "rhat", "ess", "medratio", "per-chain medians (sampled scale)")
for c in COLS
    sc = get(GIS_COL_SCALE, c, :linear)
    arr = Array{Float64}(undef, n, length(chains), 1)
    for (j, ch) in enumerate(chains)
        arr[:, j, 1] = Float64.(ch[1:n, c])
    end
    r = rhat(arr)[1]
    e = ess(arr; maxlag = min(n - 4, 200_000))[1]
    meds = [median(Float64.(ch[1:n, c])) for ch in chains]
    ## Medians print on the SAMPLED scale (that is what the chain holds and what a
    ## reader will grep the chain for); the RATIO is on the native scale, per
    ## GIS_COL_SCALE above. The `scale` column is written so the two can never be
    ## silently compared against each other.
    nat = [gis_native(m, sc) for m in meds]
    ok = isfinite(r) && r < RHAT_OK
    push!(out, (c, String(sc), r, e, ok, maximum(nat) / minimum(nat), meds...))
    @printf("%-14s %6s %8.3f %9.1f %8.3f  %s  %s\n", c, String(sc), r, e,
            maximum(nat) / minimum(nat),
            join([@sprintf("%.4f", m) for m in meds], " "),
            ok ? "" : "NOT CONVERGED")
end
CSV.write(OUT, out)
@printf("\n%d of %d NOT converged\nwrote %s\n",
        count(.!out.converged), nrow(out), relpath(OUT, REPO))
