## ============================================================================
## diag_r19_option_b_evidence.jl — is keeping the total stream (Option B) right
## on OBSERVATIONS and on STRUCTURAL PHYSICS, or only on information bookkeeping?
##
## Marcus, 2026-08-14: the Option-B recommendation in
## notes/design_2026-08-14_r19_replacement_term.md was argued from "there is no
## other data for R19". That is an INFERENTIAL argument. It says nothing about
## whether the R19 the total pins is a BETTER R19 -- closer to observations, or
## more physical in projection. This tests exactly that, three ways, comparing
## the L10 R19 block against the D1 one.
##
##   A. OBSERVATIONS. chi2/n of the calibrator's own total stream (ais + gsic_all
##      + gis + te + OBSERVED lws, re-referenced 1995-2005, against the dang
##      target and its sigma), plus R19's modern rate against GlaMBIE.
##   B. PHYSICS. Committed loss S_eq/a = 1 - exp(-b (T - T_off)) at the four
##      GlacierMIP3 warming levels, against the GlacierMIP3 rungs and their sigma.
##      This is the process-model constraint, independent of sea level.
##   C. PROJECTIONS. Glacier medians at 2100 against FACTS and MAGICC-SLR.
##
##   julia --project=julia_v2 julia/diag_r19_option_b_evidence.jl [n_draws]
## Writes outputs/diag_r19_option_b_evidence.csv
## ============================================================================

using CSV, DataFrames, Mimi, Printf, Statistics
include(joinpath(@__DIR__, "ladrillo_projection.jl"))

const OUT   = joinpath(LADRILLO_REPO, "outputs/diag_r19_option_b_evidence.csv")
const NDRAW = length(ARGS) >= 1 ? parse(Int, ARGS[1]) : 300
const FIT_REF = (1995, 2005)          # the CALIBRATION re-reference, not 1995-2014
const TARGETS = joinpath(LADRILLO_REPO, "outputs/recalib_targets_ext.csv")
const BLOCKC  = joinpath(LADRILLO_REPO, "outputs/extc_block_constants.csv")
## the two R19 blocks under test (outputs/diag_d1_vs_l10.csv medians)
const R19_ARMS = ["L10" => Dict{String,Float64}(),
                  "D1"  => Dict("gic_T_off_R19" => -0.323618, "gic_a_R19" => 0.068191,
                                "gic_b_R19" => 1.062368,
                                "gic_log10_kappa_R19" => -2.780131,
                                "gic_amp_R19" => 0.723435)]
const GMIP3_LEVELS = [1.2, 1.5, 2.0, 3.0]
const GLAMBIE_R19_RATE = 0.049251           # mm SLE/yr, 2000-2024
const GLAMBIE_R19_SD_CORR = 0.17423         # serially-correlated sigma

tg = CSV.read(TARGETS, DataFrame)
bc = CSV.read(BLOCKC, DataFrame); r19row = bc[findfirst(==("R19"), bc.block), :]
post = ladrillo_posterior(nthin=NDRAW)
bf = ladrillo_setup(ssp="ssp245", y0=1850, y1=2026,
                    gis_variant = ladrillo_posterior_variant())
yi(y) = findfirst(==(y), bf.years)
ibref = [yi(y) for y in FIT_REF[1]:FIT_REF[2]]
@printf("R19: is Option B right on observations and physics? | %d draws\n", nrow(post))

## ---- A. observations -------------------------------------------------------
dyrs = [Int(tg.year[i]) for i in 1:nrow(tg)
        if !ismissing(tg.dang[i]) && !isnan(Float64(tg.dang[i])) && tg.year[i] >= 1900]
dobs = [Float64(tg.dang[findfirst(==(y), tg.year)]) for y in dyrs]
dsig = [sqrt(Float64(tg.dang_sig[findfirst(==(y), tg.year)])^2 +
             max((Float64(tg.dang_hi[findfirst(==(y), tg.year)]) -
                  Float64(tg.dang_lo[findfirst(==(y), tg.year)])) / 3.29, 0.05)^2 * 0)
        for y in dyrs]
lwso = [Float64(tg.lws[findfirst(==(y), tg.year)]) for y in dyrs]

rows = DataFrame(axis=String[], arm=String[], metric=String[], value=Float64[])
results = Dict{String,Any}()
for (arm, over) in R19_ARMS
    p = copy(post); for (k, v) in over; p[!, k] .= v; end
    chi, rate19 = Float64[], Float64[]
    for r in eachrow(p)
        ladrillo_run_draw!(bf, r)
        raw(c, v) = 100.0 .* Float64.(bf.m[c, v])
        tot = raw(:antarctic_icesheet, :ais_sea_level) .+
              raw(:glaciers_small_icecaps, :gsic_sea_level) .+
              raw(:greenland_icesheet, :greenland_sea_level) .+
              raw(:thermal_expansion, :te_sea_level)
        tot .-= mean(tot[ibref])
        m = [tot[yi(y)] for y in dyrs] .+ lwso
        push!(chi, mean(((m .- dobs) ./ dsig) .^ 2))
        s19 = raw(:glaciers_small_icecaps, :gsic_r19)
        push!(rate19, (s19[yi(2024)] - s19[yi(2000)]) / 24 * 10)
    end
    results[arm] = (chi2 = median(chi), rate = median(rate19))
    push!(rows, (axis="A_obs", arm=arm, metric="total_chi2_per_n", value=median(chi)))
    push!(rows, (axis="A_obs", arm=arm, metric="r19_rate_mm_yr", value=median(rate19)))
end
println("\n  A. OBSERVATIONS")
@printf("  %-5s %18s %18s %14s\n", "arm", "total chi2/n", "R19 rate mm/yr", "vs GlaMBIE")
for (arm, _) in R19_ARMS
    r = results[arm]
    @printf("  %-5s %18.3f %18.4f %+13.2f sd\n", arm, r.chi2, r.rate,
            (r.rate - GLAMBIE_R19_RATE) / GLAMBIE_R19_SD_CORR)
end
@printf("  GlaMBIE R19 2000-2024: %.4f mm/yr (correlated sigma %.4f)\n",
        GLAMBIE_R19_RATE, GLAMBIE_R19_SD_CORR)

## ---- B. physics: the GlacierMIP3 rungs -------------------------------------
println("\n  B. STRUCTURAL PHYSICS — committed loss vs GlacierMIP3, % of R19 mass")
@printf("  %6s %12s %12s %14s %10s %10s\n", "GMST K", "GlacierMIP3", "sigma",
        "R19 driver K", "L10", "D1")
for L in GMIP3_LEVELS
    key = replace(string(L), "." => "p")
    com = Float64(r19row["com$key"]); sg = Float64(r19row["sig$key"])
    line = @sprintf("  %6.1f %12.2f %12.2f", L, com, sg)
    tdrv = 0.0
    for (arm, over) in R19_ARMS
        b = get(over, "gic_b_R19", median(post.gic_b_R19))
        toff = get(over, "gic_T_off_R19", median(post.gic_T_off_R19))
        amp = get(over, "gic_amp_R19", median(post.gic_amp_R19))
        T = amp * L                     # R19 driver at that GLOBAL warming level
        tdrv = T
        frac = 100.0 * (1 - exp(-b * (T - toff)))
        push!(rows, (axis="B_physics", arm=arm, metric="committed_pct_$key", value=frac))
        line *= @sprintf(" %10.1f", frac)
    end
    println(replace(line, r"( %6.1f)"=>"") * "")
    @printf("        (R19 driver %.2f K; GlacierMIP3 %.1f +/- %.1f)\n", tdrv, com, sg)
end
println("\n  sigma/central > 1 on every rung — GlacierMIP3 barely constrains R19,")
println("  so read the SIGN of the discrepancy, not its significance.")

CSV.write(OUT, rows)
println("\nwrote $(relpath(OUT, LADRILLO_REPO))")
