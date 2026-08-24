## ============================================================================
## diag_ais_block_convergence.jl — is the ANTARCTIC BLOCK converged at L14?
##
## Companion to diag_gis_block_convergence.jl, and written for the same reason:
## `postprocess_mcmc_ext.jl` names only the worst few marginals, so the block that
## actually drives the deliverable has never had a certificate of its own at the
## canonical vintage. Greenland got one on 2026-08-23 (3 of 9 fail, worst 1.075).
## Antarctica is 54.8% of the ssp585 2300 total with 9.4x Greenland's spread, is
## the only component still on stock MimiBRICK, and carries the marginal that sets
## the projections-only rule -- `ais_iceflow0`, R-hat 2.359 at L10 and 2.449 at
## L11, NEVER RE-MEASURED AT L14. Handoff 2026-08-24 sec 7 item 2: do not quote an
## AIS convergence number without measuring it. This file measures it.
##
## CONVENTION, matching postprocess_mcmc_ext.jl and the Greenland certificate
## exactly, so the two blocks are comparable side by side:
##   * burn the FIRST HALF of each chain;
##   * R-hat and ESS from MCMCDiagnosticTools;
##   * ESS with maxlag passed EXPLICITLY, min(n-4, 200_000). The default 250 floors
##     ESS (memory `mcmc_ess_maxlag`); maxlag = n overflows past ~1e6 draws and
##     returns a silently inflated value.
##
## THE SPREAD STATISTIC IS NOT THE GREENLAND ONE, and that is the point of this
## file rather than a `--block=` flag on the other. Greenland reports
## med_spread_ratio = max/min of the chain medians on the native scale. TWO AIS
## parameters are STRICTLY NEGATIVE over their whole posterior support --
## `antarctic_temp_threshold` in [-16.40, -14.52] and `ais_runoff_Ton` in
## [-18.05, -17.41] -- where max/min is < 1 and SHRINKS as the true spread grows.
## That is exactly the inversion memory `ratio_needs_native_scale` records, on
## precisely the parameters an AIS report must carry. So:
##   * MED_SPREAD_SD is the HEADLINE and is always defined: the chain-median range
##     in units of the pooled WITHIN-chain sd. It is the direct numerical form of
##     "four chain medians spanning four places", it is sign-safe, and it is
##     comparable across parameters of different units.
##   * med_spread_ratio is retained for continuity with the Greenland file but is
##     computed on |native| and GATED on all four medians sharing one sign and
##     being nonzero; otherwise NaN, with the reason in the `sign` column.
## Both are written, so the two can never be silently swapped for each other.
##
##   julia --project=julia_v2 julia/diag_ais_block_convergence.jl [--tag=L14]
## Writes outputs/mcmc/ais_block_convergence_<tag>.csv
## ============================================================================
using CSV, DataFrames, Printf, Statistics, MCMCDiagnosticTools

const REPO  = abspath(joinpath(@__DIR__, ".."))
## Default = the CANONICAL vintage, same convention as the Greenland certificate:
## not derived from LADRILLO_POSTERIOR_CSV, because that constant lives in
## ladrillo_projection.jl which pulls in Mimi/MimiBRICK and this is a pure-CSV
## diagnostic. That constant remains the authority -- update both together.
const TAG   = let i = findfirst(a -> startswith(a, "--tag="), ARGS)
    i === nothing ? "L14" : ARGS[i][7:end]
end
const SEEDS = [2026, 2027, 2028, 2029]
const NITER = 2000000
const RHAT_OK = 1.05
## SMOKE TEST ONLY. Reading four 2.3 GB chains costs ~4 minutes, which is a slow way
## to discover a typo -- `--maxrows=N` reads only the first N rows of each chain so the
## whole path can be exercised in seconds. A truncated run is NOT a certificate and
## must never be mistaken for one, so it writes to a DIFFERENT filename and says so on
## every line of output. Burn-in still takes the second half of what was read.
const MAXROWS = let i = findfirst(a -> startswith(a, "--maxrows="), ARGS)
    i === nothing ? typemax(Int) : parse(Int, ARGS[i][11:end])
end
const SMOKE = MAXROWS != typemax(Int)

## THE COLUMN SET IS GROUPED BY WHAT THE PARAMETER DOES, not alphabetically,
## because the question this file answers is "which PART of Antarctica fails".
## Names are the posterior columns; the Mimi parameters they map to are in
## ladrillo_projection.jl's LADRILLO_PHYSICAL_PARAMS and LADRILLO_DERIVED_COLS.
##
##   geometry  the DAIS bed/flux geometry -- ais_iceflow0 lives here
##   dynamics  the response coefficients and the melt threshold
##   ocean     the ANTO ocean-temperature map feeding the sheet
##   driver    ais_gmst_amp, consumed as 1/amp by the temperature map
const AIS_GEOM_COLS   = ["ais_mu", "ais_bedheight0", "ais_slope", "ais_iceflow0",
                         "ais_precip0_LOG", "ais_runoff_Ton", "ais_c"]
const AIS_DYN_COLS    = ["antarctic_alpha", "antarctic_nu", "antarctic_lambda",
                         "antarctic_gamma", "antarctic_kappa",
                         "antarctic_temp_threshold"]
const AIS_OCEAN_COLS  = ["ais_ocean_temperature₀", "anto_alpha", "anto_beta"]
const AIS_DRIVER_COLS = ["ais_gmst_amp"]
## Reported but NOT counted in the block verdict: these are the AR(1) residual
## model for the AIS observation stream, not the ice sheet. Memory
## `ladrillo_noise_model` records that the noise model is misspecified, so their
## R-hats are a statement about the likelihood's nuisance layer.
const AIS_NOISE_COLS  = ["sd_ais", "rho_ais"]

const AIS_GROUP = vcat([c => "geometry" for c in AIS_GEOM_COLS],
                       [c => "dynamics" for c in AIS_DYN_COLS],
                       [c => "ocean"    for c in AIS_OCEAN_COLS],
                       [c => "driver"   for c in AIS_DRIVER_COLS],
                       [c => "noise"    for c in AIS_NOISE_COLS]) |> Dict

## ais_precip0_LOG is sampled in LOG space because MimiBRICK v2.0.0's AIS
## component computes exp(ais_precipitation0) (calibrate_mcmc_ext.jl:1133-1134);
## the column name carries the convention. Everything else is applied straight
## through, so :linear. ais_gmst_amp is consumed as 1/amp but is positive over its
## whole support, so a ratio on the sampled scale is the reciprocal of a ratio on
## the applied scale -- same magnitude, and the `scale` column says which.
const AIS_COL_SCALE = Dict("ais_precip0_LOG" => :log)
ais_native(m::Float64, sc::Symbol) = sc === :log ? exp(m) : m

const CORE  = vcat(AIS_GEOM_COLS, AIS_DYN_COLS, AIS_OCEAN_COLS, AIS_DRIVER_COLS)
const COLS  = vcat(CORE, AIS_NOISE_COLS)
const OUT   = joinpath(REPO, "outputs/mcmc",
                       "ais_block_convergence_$(TAG)$(SMOKE ? "_SMOKE" : "").csv")

const HDR = String.(names(CSV.read(joinpath(REPO, "outputs/mcmc",
                "chain_$(TAG)_seed$(first(SEEDS))_n$(NITER).csv"), DataFrame; limit = 1)))
let miss = setdiff(COLS, HDR)
    ## A missing AIS column is NOT a variant case the way Greenland's slow channel
    ## was: AIS has never been reparameterised in this repo, so an absent column
    ## means the chain is not what the caller thinks it is.
    isempty(miss) || error("chain_$(TAG)_seed$(first(SEEDS)) is missing AIS columns " *
                           join(miss, ", ") * " -- AIS has never been reparameterised " *
                           "here, so this is not an L-series joint chain")
end

## Read one chain at a time into a preallocated post-burn array and let the
## DataFrame go: all four chains x 20 columns x 2e6 rows as DataFrames would be
## ~2.6 GB before burn-in is dropped. Post-burn it is ~640 MB.
function read_postburn(tag::String)
    arr = nothing
    n   = 0
    for (j, sd) in enumerate(SEEDS)
        f = joinpath(REPO, "outputs/mcmc", "chain_$(tag)_seed$(sd)_n$(NITER).csv")
        isfile(f) || error("missing chain file $f")
        d = SMOKE ? CSV.read(f, DataFrame; select = COLS, limit = MAXROWS) :
                    CSV.read(f, DataFrame; select = COLS)
        keep = (nrow(d) ÷ 2 + 1):nrow(d)
        if arr === nothing
            n = length(keep)
            arr = Array{Float64}(undef, n, length(SEEDS), length(COLS))
        end
        ## Chains of one tag must be the same length; a shorter one would otherwise be
        ## silently truncated against the first and R-hat computed on mismatched draws.
        length(keep) == n || error("$(basename(f)) has $(length(keep)) post-burn draws, " *
                                   "the first chain has $n -- the chains of tag $tag " *
                                   "are not the same length")
        for (k, c) in enumerate(COLS)
            arr[:, j, k] = Float64.(d[keep, c])
        end
        @printf("  %s  (%d post-burn)\n", basename(f), n)
        flush(stdout)
        d = nothing
        GC.gc()
    end
    return arr, n
end

const arr, n = read_postburn(TAG)

out = DataFrame(vcat(["param" => String[], "group" => String[], "scale" => String[],
                      "sign" => String[], "rhat" => Float64[], "ess" => Float64[],
                      "converged" => Bool[], "med_spread_sd" => Float64[],
                      "med_spread_ratio" => Float64[]],
                     ["med_seed$sd" => Float64[] for sd in SEEDS]))

@printf("\nAntarctic block convergence | tag %s | %d chains x %d post-burn | R-hat OK < %.2f%s\n",
        TAG, length(SEEDS), n, RHAT_OK,
        SMOKE ? "  *** SMOKE TEST, maxrows=$(MAXROWS) -- NOT A CERTIFICATE ***" : "")
println("headline spread statistic: chain-median RANGE / pooled within-chain sd " *
        "(sign-safe; the ratio is gated)\n")
@printf("%-26s %-9s %7s %6s %9s %9s %9s  %s\n",
        "param", "group", "scale", "sign", "rhat", "ess", "med/sd", "per-chain medians (sampled)")
for (k, c) in enumerate(COLS)
    sc  = get(AIS_COL_SCALE, c, :linear)
    sub = @view arr[:, :, k]
    r   = rhat(reshape(sub, n, length(SEEDS), 1))[1]
    e   = ess(reshape(sub, n, length(SEEDS), 1); maxlag = min(n - 4, 200_000))[1]
    meds = [median(@view sub[:, j]) for j in 1:length(SEEDS)]
    nat  = [ais_native(m, sc) for m in meds]
    ## Pooled WITHIN-chain sd -- the denominator that makes the median range read as
    ## "how far apart are the chains relative to how wide each one is".
    w_sd = sqrt(mean([var(@view sub[:, j]) for j in 1:length(SEEDS)]))
    spread_sd = w_sd > 0 ? (maximum(meds) - minimum(meds)) / w_sd : NaN
    allpos = all(>(0), nat); allneg = all(<(0), nat)
    sgn = allpos ? "+" : allneg ? "-" : "mixed"
    ## Gated, on |native|: for an all-negative parameter max/min inverts, and for a
    ## sign-crossing one no ratio is defined at all.
    ratio = (allpos || allneg) ? maximum(abs.(nat)) / minimum(abs.(nat)) : NaN
    ok = isfinite(r) && r < RHAT_OK
    push!(out, (c, AIS_GROUP[c], String(sc), sgn, r, e, ok, spread_sd, ratio, meds...))
    @printf("%-26s %-9s %7s %6s %9.3f %9.1f %9.3f  %s  %s\n",
            c, AIS_GROUP[c], String(sc), sgn, r, e, spread_sd,
            join([@sprintf("%.4g", m) for m in meds], " "),
            ok ? "" : "NOT CONVERGED")
end
CSV.write(OUT, out)

core_rows = out[in.(out.param, Ref(CORE)), :]
nbad = count(.!core_rows.converged)
@printf("\n%d of %d STRUCTURAL AIS marginals NOT converged (noise params excluded)\n",
        nbad, nrow(core_rows))
worst = core_rows[argmax(core_rows.rhat), :]
@printf("worst R-hat: %s = %.3f (ESS %.1f, chain medians span %.2f within-chain sd)\n",
        worst.param, worst.rhat, worst.ess, worst.med_spread_sd)
for g in ["geometry", "dynamics", "ocean", "driver"]
    gr = core_rows[core_rows.group .== g, :]
    @printf("  %-9s %d/%d fail, worst %.3f\n", g, count(.!gr.converged), nrow(gr),
            maximum(gr.rhat))
end
@printf("\nwrote %s%s\n", relpath(OUT, REPO),
        SMOKE ? "  *** SMOKE TEST OUTPUT -- NOT A CERTIFICATE ***" : "")
