## ============================================================================
## diag_block_trajectory_shape.jl — WHERE IN TIME does Ladrillo's glacier
## trajectory part from OGGM's, and is it the base rate or the late phase?
##
## The SLOWP 2300 gap survives the warming-level correction: at the ssp126 2300
## level (1.74 K, not the 1.5 K I first compared against) GlacierMIP3's
## interpolated commitment is 58.0% for SLOWP, OGGM realises 58.6% (phi = 1.01,
## fully equilibrated) and Ladrillo 42.2% (phi = 0.73). So the two agree on the
## COMMITMENT and disagree on the RATE at which it is realised.
##
## Two rate hypotheses, and they call for different fixes:
##   H1 BASE RATE. Our kappa/nu are simply too small, and the trajectories part
##      from the beginning. Fix = constrain kappa, which the hindcast does not do
##      (gic_log10_kappa_SLOWP posterior/prior width ratio 1.24 -- WIDER than its
##      prior, flagged as prior-likelihood tension in spec section 8.4).
##   H2 LATE-PHASE FEEDBACK. The trajectories track early and part late, because
##      OGGM's flowline geometry lets a retreating glacier lose its accumulation
##      area and collapse, while a 3-reservoir relaxation approaches equilibrium
##      exponentially with no area feedback. Fix = a structural one; constraining
##      kappa would then mis-fit the early period to patch a late-phase defect.
##
## The discriminator is phi(t) = realised / committed through time, so this emits
## it every 50 years. Committed is GlacierMIP3 interpolated to the running
## warming level, the same construction on both sides.
##
##   julia --project=julia_v2 julia/diag_block_trajectory_shape.jl [n_draws]
## Writes outputs/diag_block_trajectory_shape.csv
## ============================================================================

using CSV, DataFrames, Mimi, Printf, Statistics
include(joinpath(@__DIR__, "ladrillo_projection.jl"))

const OUT   = joinpath(LADRILLO_REPO, "outputs/diag_block_trajectory_shape.csv")
const NDRAW = length(ARGS) >= 1 ? parse(Int, ARGS[1]) : 200
const REF   = 2015
const YEARS = [2050, 2100, 2150, 2200, 2250, 2300]
const SSP   = "ssp126"          # the ONLY 2300 scenario with discriminating power
const SLOTS = ["R19" => :gsic_r19, "SLOWP" => :gsic_slowp, "FAST" => :gsic_fast]
const ACOL  = Dict("R19" => "gic_a_R19", "SLOWP" => "gic_a_SLOWP", "FAST" => "gic_a_FAST")

post = ladrillo_posterior(nthin=NDRAW)
bf = ladrillo_setup(ssp=SSP, y0=1850, y1=2300,
                    gis_ab = ladrillo_posterior_variant() === :ab)
yi(y) = findfirst(==(y), bf.years)
acc = Dict(b => Dict(y => Float64[] for y in YEARS) for (b, _) in SLOTS)
for r in eachrow(post)
    ladrillo_run_draw!(bf, r)
    for (b, slot) in SLOTS
        s = Float64.(bf.m[:glaciers_small_icecaps, slot])
        m15 = Float64(r[ACOL[b]]) - s[yi(REF)]
        for y in YEARS
            push!(acc[b][y], 100 * (s[yi(y)] - s[yi(REF)]) / m15)
        end
    end
end

rows = DataFrame(block=String[], year=Int[], ladrillo_loss_pct=Float64[])
@printf("Ladrillo block loss, %% of %d mass, %s\n", REF, SSP)
println("  " * rpad("block", 7) * join([lpad(string(y), 9) for y in YEARS]))
for (b, _) in SLOTS
    v = [median(filter(isfinite, acc[b][y])) for y in YEARS]
    for (y, x) in zip(YEARS, v)
        push!(rows, (block=b, year=y, ladrillo_loss_pct=x))
    end
    println("  " * rpad(b, 7) * join([lpad(@sprintf("%.1f", x), 9) for x in v]))
end
CSV.write(OUT, rows)
println("\nwrote $(relpath(OUT, LADRILLO_REPO))")
