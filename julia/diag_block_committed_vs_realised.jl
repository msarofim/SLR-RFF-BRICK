## ============================================================================
## diag_block_committed_vs_realised.jl — is the glacier 2300 gap a COMMITMENT
## gap or a TIMESCALE gap? Split it the same way the Greenland ridge was split.
##
## Prompted by the SLOWP 2300 discrepancy (Ladrillo 42.2% vs OGGM 58.6% of 2015
## mass under ssp126). Two prior corrections got us here:
##   * my first comparison used GlacierMIP3's committed loss at 1.5 K, but the
##     ssp126 run sits at 1.74 K in 2290-2300 (and peaks at 1.84 K near 2100).
##     Interpolated to 1.74 K the commitment is 58.0%, so OGGM at 58.6% is NOT
##     "exceeding its commitment" -- that contradiction was mine, and is withdrawn.
##   * the trajectory shapes (diag_block_trajectory_shape.jl) agree at 2050
##     (gap -0.6 pp) and part progressively to -16.4 pp by 2250 -- a relaxation-
##     rate signature, not an early base-rate offset.
##
## This computes Ladrillo's OWN committed loss S_eq = a(1 - exp(-b(T - T_off)))
## at the 2300 driver, against what it actually realises, so phi = realised /
## committed is directly comparable to the Greenland decomposition.
##
##   julia --project=julia_v2 julia/diag_block_committed_vs_realised.jl
## Writes nothing; prints the table (numbers recorded in the CHANGELOG).
## ============================================================================

using CSV, DataFrames, Mimi, Printf, Statistics
include(joinpath(@__DIR__, "ladrillo_projection.jl"))
post = ladrillo_posterior(nthin=200)
bf = ladrillo_setup(ssp="ssp126", y0=1850, y1=2300, gis_variant = ladrillo_posterior_variant())
yi(y)=findfirst(==(y), bf.years)
BLK = ["R19"=>:gsic_r19, "SLOWP"=>:gsic_slowp, "FAST"=>:gsic_fast]
println("Ladrillo ssp126: COMMITTED vs REALISED at 2300, % of 2015 block mass")
@printf("  %-7s %12s %12s %8s\n","block","S_eq/mass%","realised%","phi")
for (b,slot) in BLK
    seq, rea = Float64[], Float64[]
    for r in eachrow(post)
        ladrillo_run_draw!(bf, r)
        s = Float64.(bf.m[:glaciers_small_icecaps, slot])
        a  = Float64(r["gic_a_$b"]); bb = Float64(r["gic_b_$b"])
        to = Float64(r["gic_T_off_$b"]); amp = Float64(r["gic_amp_$b"])
        drv = amp * (bf.gmst_rb[yi(2300)])           # block driver at 2300
        Seq = a * (1 - exp(-bb*(drv - to)))          # committed loss, m SLE
        m15 = a - s[yi(2015)]
        push!(seq, 100*(Seq - s[yi(2015)])/m15)      # committed FURTHER loss, % of 2015 mass
        push!(rea, 100*(s[yi(2300)] - s[yi(2015)])/m15)
    end
    S=median(seq); R=median(rea)
    @printf("  %-7s %12.1f %12.1f %8.2f\n", b, S, R, R/S)
end
println("\n  (GlacierMIP3 committed at the 1.74 K 2300 level: R19 52.1, SLOWP 58.0, FAST 56.6)")
println("  (OGGM realised at 2300 ssp126:                     R19 59.8, SLOWP 58.6, FAST 67.4)")
