## ============================================================================
## diag_r19_replacement_target.jl — distil the total stream's R19 information
## into an OBSERVABLE-space constraint, and check it is well posed.
##
## THE PROBLEM (measured, not assumed).
##  * Dropping the total (D1) moves gic_T_off_R19 by +2.05 L10 sd, mixing-gated
##    at 5.5x -- real information loss.
##  * It MATTERS: up to 1.7 cm on the 2300 glacier median
##    (diag_r19_deliverable_leverage.jl), so it is not an ais_iceflow0-style
##    reporting caveat.
##  * The total COULD see it: the shift's signature on the total is 1.47 cm max
##    against a total sigma of 0.232-0.565 cm (diag_r19_hindcast_visibility.jl).
##  * But NOTHING ELSE CAN. The Frederikse glacier target excludes R19 by
##    construction; the gsic component channel is HIND_BLOCKS = SLOWP+FAST; the
##    GlaMBIE partition term is on the SLOWP/FAST share only. R19's own GlaMBIE
##    rate is 0.0493 +/- 0.0361 mm/yr = 1.37 sigma as coded, 0.28 sigma under the
##    serial-correlation assumption the GlaMBIE restructure itself argued for.
##  * And a modern-rate term could not do it even if the data were sharp: the
##    signature is 0.750 cm mean over 1900-1999 but 0.087 cm over 2000-2024,
##    because everything is re-referenced to 1995-2005 and the two trajectories
##    converge at the reference. The information is PRE-2000.
##
## THE DESIGN. Replace the stream with a constraint on the OBSERVABLE it was
## measuring -- R19's own cumulative contribution over the 20th century -- rather
## than a prior on gic_T_off_R19. House rule: bound the observable, not the
## parameter (a bound bisected at defaults leaks). The mean and sigma are the L10
## posterior predictive for that observable, i.e. this MARGINALISES the total's
## R19 information rather than discarding it.
##
## WHAT THIS SCRIPT CHECKS BEFORE THE TERM CAN BE WRITTEN:
##  1. the L10 posterior predictive for R19 cumulative, per candidate window;
##  2. that the constraint DISCRIMINATES -- the D1 R19 block must sit far from it,
##     or the term would be decorative;
##  3. that the target is not degenerate with the parameters other terms already
##     pin (correlation with the SLOWP/FAST and ledger parameters);
##  4. Gaussianity, since the term will be written as a Normal.
##
##   julia --project=julia_v2 julia/diag_r19_replacement_target.jl [n_draws]
## Writes outputs/diag_r19_replacement_target.csv
## ============================================================================

using CSV, DataFrames, Mimi, Printf, Statistics
include(joinpath(@__DIR__, "ladrillo_projection.jl"))

const OUT   = joinpath(LADRILLO_REPO, "outputs/diag_r19_replacement_target.csv")
const NDRAW = length(ARGS) >= 1 ? parse(Int, ARGS[1]) : 500
const Y0, Y1 = 1850, 2026
## Candidate windows. The constraint must live where the information is (pre-2000)
## and must not need observations that do not exist for the Antarctic periphery.
const WINDOWS = [(1900, 1950), (1900, 1980), (1900, 2000), (1900, 2024)]
const D1_TOFF = -0.323618          # D1 posterior median (outputs/diag_d1_vs_l10.csv)

post = ladrillo_posterior(nthin=NDRAW)
bf = ladrillo_setup(ssp="ssp245", y0=Y0, y1=Y1,
                    gis_variant = ladrillo_posterior_variant())
yi(y) = findfirst(==(y), bf.years)
@printf("R19 replacement target | %s | %d draws\n",
        basename(LADRILLO_POSTERIOR_CSV), nrow(post))

"""R19 cumulative contribution over each window, cm, per draw. Uses the model's
own :gsic_r19 slot, so no differencing of aggregates is involved."""
function r19_cum(p)
    out = Dict(w => Float64[] for w in WINDOWS)
    for r in eachrow(p)
        ladrillo_run_draw!(bf, r)
        s = 100.0 .* Float64.(bf.m[:glaciers_small_icecaps, :gsic_r19])
        for w in WINDOWS
            push!(out[w], s[yi(w[2])] - s[yi(w[1])])
        end
    end
    return out
end

L = r19_cum(post)
pD = copy(post); pD[!, "gic_T_off_R19"] .= D1_TOFF
D = r19_cum(pD)

rows = DataFrame(window=String[], l10_mean=Float64[], l10_sd=Float64[],
                 l10_skew=Float64[], d1_mean=Float64[], separation_sd=Float64[])
println("\n  R19 cumulative contribution, cm — the candidate constraint")
@printf("  %-12s %10s %10s %8s %12s %12s\n", "window", "L10 mean", "L10 sd",
        "skew", "D1 mean", "separation")
for w in WINDOWS
    l, d = L[w], D[w]
    m, s = mean(l), std(l)
    sk = mean(((l .- m) ./ s) .^ 3)
    sep = abs(mean(d) - m) / s
    push!(rows, (window="$(w[1])-$(w[2])", l10_mean=m, l10_sd=s, l10_skew=sk,
                 d1_mean=mean(d), separation_sd=sep))
    @printf("  %-12s %10.4f %10.4f %8.2f %12.4f %10.2f sd\n",
            "$(w[1])-$(w[2])", m, s, sk, mean(d), sep)
end

println("\n  separation = how many L10 sd the D1 R19 block sits from the target.")
println("  A term only replaces the total if this is LARGE; near zero means the")
println("  constraint cannot tell the two apart and would be decorative.")

## does the target duplicate what other terms already pin?
println("\n  Degeneracy check — correlation of the target with parameters that")
println("  other likelihood terms already constrain")
best = rows[argmax(rows.separation_sd), :]
w = (parse(Int, split(best.window, "-")[1]), parse(Int, split(best.window, "-")[2]))
tgt = L[w]
for c in ["gic_a_R19", "gic_b_R19", "gic_T_off_R19", "gic_amp_R19",
          "gic_a_SLOWP", "gic_a_FAST", "gic_u_unch", "gic_delta", "gic_u_pre"]
    c in names(post) || continue
    @printf("    %-22s %+6.3f\n", c, cor(tgt, post[!, c]))
end

@printf("\n  RECOMMENDED WINDOW: %s   target = %.4f +/- %.4f cm  (separation %.2f sd)\n",
        best.window, best.l10_mean, best.l10_sd, best.separation_sd)
CSV.write(OUT, rows)
println("wrote $(relpath(OUT, LADRILLO_REPO))")
