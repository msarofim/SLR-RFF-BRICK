# test_greenland_3basin_nesting.jl — the nesting gate for the 3-basin Greenland.
#
# Handoff 2026-08-19 §8 step 2: "Confirm the total is unchanged when the basins
# are collapsed — a nesting check, the analogue of the mock's 6e-17 gate." A
# diagnostic that can already measure the thing is how you tell a wiring bug
# from a physics result, so this runs BEFORE the shares likelihood term exists.
#
# The three gates, in increasing strength:
#
#   [1] COLLAPSE. k = (1, 0, 0), s = (1, 1, 1): all commitment in the south basin,
#       unit rate scales. greenland_3basin must reproduce greenland_ab EXACTLY —
#       same driver, same shape parameters, same slot output.
#   [2] ADDITIVITY. At the production shares, the exported per-basin series must
#       sum to the slot output, and gis_fast/gis_slow must be the basin sums.
#       This is the contract every downstream consumer relies on.
#   [3] PARTITION INVARIANCE. k = the Mouginot shares (sum 1) but s = (1, 1, 1):
#       the total must STILL equal greenland_ab. The channel rates do not depend
#       on k, and eq_b is linear in k, so splitting a commitment three ways and
#       relaxing each at the same rate is exactly conservative. This is strictly
#       stronger than [1]: it fails if the per-basin clamp, the initial condition,
#       or the k wiring is wrong in a way that a single loaded basin hides.
#       It is ALSO the statement that the three s_b are the ONLY thing the
#       restructure adds — at s = 1 the model has not moved at all.
#   [4] TWO BASINS (added 2026-08-20, for --gis-basins2). k = GIS2_VSHARE =
#       (0.628571, 0, 0.371429), s = (1, 1, 1): the mid basin must be identically
#       zero, active + high must be the whole sheet, and the total must STILL equal
#       greenland_ab. This is what makes "greenland_3basin at k_mid = 0 IS a
#       two-basin model" a measurement rather than an assertion, and it is why
#       --gis-basins2 needs no new Mimi component.
#   [5] MUTATION TEST of [4] — per the mutation_test_gates discipline, a gate that
#       has only ever passed proves nothing. [5] perturbs a k and REQUIRES the [4]
#       comparisons to fail. If [5] does not trip, [4] is not measuring anything and
#       the whole file exits non-zero.
#
# Run:  julia --project=julia_v2 julia/test_greenland_3basin_nesting.jl

using CSV, DataFrames, Mimi, MimiBRICK, Printf
include(joinpath(@__DIR__, "brick_mengel.jl"))

const REPO = abspath(joinpath(@__DIR__, ".."))
const TOL = 1e-12                      # bit-level; the mock's analogue gate ran 6e-17

ref = CSV.read(joinpath(REPO, "outputs/gis_port_reference.csv"), DataFrame)
th = CSV.read(joinpath(REPO, "outputs/gis_port_reference_theta.csv"), DataFrame)
getp(n) = Float64(only(th[th.name .== n, :value_component]))
forcing = String(only(th[th.name .== "_forcing_tag", :unit_cell]))

y0, y1 = Int(minimum(ref.year)), Int(maximum(ref.year))
gis = (c1=getp("c1"), c0=getp("c0"), v0=getp("v0"), f=getp("f"),
       alpha_f=getp("alpha_f"), beta_f=getp("beta_f"),
       alpha_s=getp("alpha_s"), beta_s=getp("beta_s"), g=getp("g"))
driver = Float64.(ref.driver_K)
zero_drv = zeros(length(driver))

# glacier blocks: bound at the accepted extC anchors purely so Mimi will build
bc = CSV.read(joinpath(REPO, "outputs/extc_block_constants.csv"), DataFrame)
brow(b) = only(eachrow(bc[bc.block .== b, :]))
function bind_glaciers!(mm)
    for blk in NU3_BLOCKS
        r = brow(blk)
        update_param!(mm, _MENGEL_GLAC_SLOT, Symbol("gic_a_$blk"), Float64(r.a0))
        update_param!(mm, _MENGEL_GLAC_SLOT, Symbol("gic_b_$blk"), Float64(r.b_fit_obsfit))
        update_param!(mm, _MENGEL_GLAC_SLOT, Symbol("gic_T_off_$blk"), Float64(r.T_off_fit_obsfit))
        update_param!(mm, _MENGEL_GLAC_SLOT, Symbol("gic_kappa_$blk"), Float64(r.kappa_anch_obsfit))
        update_param!(mm, _MENGEL_GLAC_SLOT, Symbol("gic_nu_$blk"), Float64(r.nu_anch_obsfit))
    end
    update_param!(mm, _MENGEL_GLAC_SLOT, :gic_sl0, 0.0)
    set_glacier_forcing3!(mm, (R19=zero_drv, SLOWP=zero_drv, FAST=zero_drv))
    return mm
end

@printf("greenland_3basin nesting gate | %d-%d | forcing %s | tol %.0e\n",
        y0, y1, forcing, TOL)
@printf("  Mouginot volume shares: south %.6f  mid %.6f  high %.6f  (sum %.15f)\n",
        GIS3_VSHARE.south, GIS3_VSHARE.mid, GIS3_VSHARE.high, sum(GIS3_VSHARE))

# --- the A+B reference model -------------------------------------------------
mab = build_brick_nu3_gis(ssp=forcing, y0=y0, y1=y1)
update_gis_ab!(mab, gis); set_gis_forcing!(mab, driver); bind_glaciers!(mab)
run(mab)
ab_sl   = Float64.(mab[_GIS_SLOT, :greenland_sea_level])
ab_fast = Float64.(mab[_GIS_SLOT, :gis_fast])
ab_slow = Float64.(mab[_GIS_SLOT, :gis_slow])

function run3(k, s)
    mm = build_brick_nu3_gis3(ssp=forcing, y0=y0, y1=y1)
    update_gis_ab!(mm, gis)
    update_gis3_shares!(mm; k=k, s=s)
    set_gis_forcing!(mm, driver); bind_glaciers!(mm)
    run(mm)
    return mm
end

fails = String[]
function check(label, got, want)
    d = maximum(abs.(Float64.(got) .- Float64.(want)))
    ok = d <= TOL
    @printf("  %-46s max|diff| = %.3e  %s\n", label, d, ok ? "PASS" : "FAIL")
    ok || push!(fails, label)
    return ok
end

const UNIT_S = (south=1.0, mid=1.0, high=1.0)

println("\n[1] COLLAPSE — k = (1, 0, 0), s = 1: must reproduce greenland_ab")
m1 = run3((south=1.0, mid=0.0, high=0.0), UNIT_S)
check("[1] greenland_sea_level (m)", m1[_GIS_SLOT, :greenland_sea_level], ab_sl)
check("[1] gis_fast (m)", m1[_GIS_SLOT, :gis_fast], ab_fast)
check("[1] gis_slow (m)", m1[_GIS_SLOT, :gis_slow], ab_slow)
check("[1] south basin carries all of it", m1[_GIS_SLOT, :gis_sl_south], ab_sl)
check("[1] mid basin is identically zero", m1[_GIS_SLOT, :gis_sl_mid], zeros(length(ab_sl)))
check("[1] high basin is identically zero", m1[_GIS_SLOT, :gis_sl_high], zeros(length(ab_sl)))

println("\n[2] ADDITIVITY — at the production shares, the parts sum to the whole")
m2 = run3(GIS3_VSHARE, UNIT_S)
b_sl = (Float64.(m2[_GIS_SLOT, :gis_sl_south]), Float64.(m2[_GIS_SLOT, :gis_sl_mid]),
        Float64.(m2[_GIS_SLOT, :gis_sl_high]))
check("[2] sea_level == sum of the three basins",
      m2[_GIS_SLOT, :greenland_sea_level], b_sl[1] .+ b_sl[2] .+ b_sl[3])
check("[2] sea_level == gis_fast + gis_slow", m2[_GIS_SLOT, :greenland_sea_level],
      Float64.(m2[_GIS_SLOT, :gis_fast]) .+ Float64.(m2[_GIS_SLOT, :gis_slow]))
check("[2] gis_fast == sum of basin fast channels", m2[_GIS_SLOT, :gis_fast],
      Float64.(m2[_GIS_SLOT, :gis_fast_south]) .+ Float64.(m2[_GIS_SLOT, :gis_fast_mid]) .+
      Float64.(m2[_GIS_SLOT, :gis_fast_high]))
check("[2] gis_slow == sum of basin slow channels", m2[_GIS_SLOT, :gis_slow],
      Float64.(m2[_GIS_SLOT, :gis_slow_south]) .+ Float64.(m2[_GIS_SLOT, :gis_slow_mid]) .+
      Float64.(m2[_GIS_SLOT, :gis_slow_high]))
# and the slot is still what :global_sea_level consumes
check("[2] global_sea_level == 5 components", m2[:global_sea_level, :sea_level_rise],
      Float64.(m2[_GIS_SLOT, :greenland_sea_level]) .+
      Float64.(m2[_MENGEL_GLAC_SLOT, :gsic_sea_level]) .+
      Float64.(m2[:antarctic_icesheet, :ais_sea_level]) .+
      Float64.(m2[:thermal_expansion, :te_sea_level]) .+
      Float64.(m2[:landwater_storage, :lws_sea_level]))

println("\n[3] PARTITION INVARIANCE — Mouginot k, s = 1: the total must NOT move")
check("[3] greenland_sea_level (m)", m2[_GIS_SLOT, :greenland_sea_level], ab_sl)
check("[3] gis_fast (m)", m2[_GIS_SLOT, :gis_fast], ab_fast)
check("[3] gis_slow (m)", m2[_GIS_SLOT, :gis_slow], ab_slow)
# the shares at s = 1 are the VOLUME shares — the null the calibration moves away from
i72, i18 = findfirst(==(1972), ref.year), findfirst(==(2018), ref.year)
if i72 !== nothing && i18 !== nothing
    d = [b[i18] - b[i72] for b in b_sl]
    @printf("  s = 1 gives 1972-2018 loss shares  south %.3f  mid %.3f  high %.3f\n",
            (d ./ sum(d))...)
    @printf("  observed (Mouginot modern rate, 2002-2011) south 0.592  mid 0.207  high 0.201\n")
    println("  ⇒ the gap between those rows is exactly what the s_b are fitted to close.")
end

println("\n[4] TWO BASINS — k = GIS2_VSHARE, s = 1: k_mid = 0 IS a two-basin model")
@printf("  two-basin volume shares: active %.6f  mid %.6f  high %.6f  (sum %.15f)\n",
        GIS2_VSHARE.south, GIS2_VSHARE.mid, GIS2_VSHARE.high, sum(GIS2_VSHARE))
# The handoff's published numbers. Pinned here so a revision of GIS3_VOL_M shows up
# as a failing test naming the old numbers, rather than as a silent drift away from
# the configuration the offline evidence was collected at. Compared at the SIX
# DECIMALS they were published to — `check`'s 1e-12 is a bit-level tolerance for
# comparing two model runs, and 4.62/7.35 differs from a 6-dp literal by 4.3e-07.
const K2_PUBLISHED = (south = 0.628571, high = 0.371429)
function check6(label, got, want)
    ok = round(got, digits=6) == want
    @printf("  %-46s %.15f vs %.6f  %s\n", label, got, want, ok ? "PASS" : "FAIL")
    ok || push!(fails, label)
    return ok
end
check6("[4] k active == published (6 dp)", GIS2_VSHARE.south, K2_PUBLISHED.south)
check6("[4] k high == published (6 dp)", GIS2_VSHARE.high, K2_PUBLISHED.high)
check("[4] k sums to exactly 1", [sum(GIS2_VSHARE)], [1.0])
m4 = run3(GIS2_VSHARE, UNIT_S)
b4 = (Float64.(m4[_GIS_SLOT, :gis_sl_south]), Float64.(m4[_GIS_SLOT, :gis_sl_mid]),
      Float64.(m4[_GIS_SLOT, :gis_sl_high]))
check("[4] mid basin is identically zero", b4[2], zeros(length(ab_sl)))
check("[4] active + high == greenland_sea_level", m4[_GIS_SLOT, :greenland_sea_level],
      b4[1] .+ b4[3])
check("[4] greenland_sea_level (m) == greenland_ab", m4[_GIS_SLOT, :greenland_sea_level], ab_sl)
check("[4] gis_fast (m) == greenland_ab", m4[_GIS_SLOT, :gis_fast], ab_fast)
check("[4] gis_slow (m) == greenland_ab", m4[_GIS_SLOT, :gis_slow], ab_slow)
if i72 !== nothing && i18 !== nothing
    d4 = [b4[i][i18] - b4[i][i72] for i in 1:3]
    @printf("  s = 1 gives 1972-2018 loss shares  active %.3f  mid %.3f  high %.3f\n",
            (d4 ./ sum(d4))...)
    @printf("  observed (Mouginot modern rate, 2002-2011) active 0.799  mid 0.000  high 0.201\n")
end

# --- [5] MUTATION TEST of [4] -------------------------------------------------
# A gate that has only ever passed proves nothing (memory `mutation_test_gates`).
# Perturb k and REQUIRE the [4] comparisons to break. Two distinct mutations, because
# they fail through different mechanisms: MUT-A moves mass between basins with the sum
# still 1 (the partition is wrong but the total is conserved, so only the PER-BASIN
# series move — this is the mutation that catches a k wired to the wrong slot), while
# MUT-B breaks sum-to-one (the TOTAL moves, catching a k that never reaches the
# component at all).
println("\n[5] MUTATION TEST — [4] must FAIL when k is perturbed")
mutfails = String[]
function mustfail(label, got, want)
    d = maximum(abs.(Float64.(got) .- Float64.(want)))
    broke = d > TOL
    @printf("  %-46s max|diff| = %.3e  %s\n", label, d, broke ? "detected" : "NOT DETECTED")
    broke || push!(mutfails, label)
    return broke
end
const K2_MUT_A = (south = GIS2_VSHARE.south - 0.05, mid = 0.05, high = GIS2_VSHARE.high)
const K2_MUT_B = (south = GIS2_VSHARE.south, mid = 0.0, high = GIS2_VSHARE.high * 0.9)
mA = run3(K2_MUT_A, UNIT_S)
mustfail("[5A] mid = 0.05 must break 'mid is zero'", mA[_GIS_SLOT, :gis_sl_mid],
         zeros(length(ab_sl)))
mustfail("[5A] mid = 0.05 must break 'active + high == total'",
         mA[_GIS_SLOT, :greenland_sea_level],
         Float64.(mA[_GIS_SLOT, :gis_sl_south]) .+ Float64.(mA[_GIS_SLOT, :gis_sl_high]))
mB = run3(K2_MUT_B, UNIT_S)
mustfail("[5B] sum(k) = 0.963 must break '== greenland_ab'",
         mB[_GIS_SLOT, :greenland_sea_level], ab_sl)
# and the mutations must not be trivially detected by moving something unrelated:
# MUT-A conserves the total, so the whole-sheet series is UNCHANGED. If this one
# reports a difference, the per-basin clamp is not exact and [4] is passing for the
# wrong reason.
check("[5A] total is CONSERVED (k still sums to 1)",
      mA[_GIS_SLOT, :greenland_sea_level], ab_sl)
if !isempty(mutfails)
    push!(fails, "MUTATION TEST DID NOT TRIP: " * join(mutfails, "; ") *
                 " — gate [4] is not measuring what it claims")
end

println()
if isempty(fails)
    println("ALL NESTING GATES PASS — the 3-basin component is a strict " *
            "generalisation of greenland_ab, and at k_mid = 0 it is exactly the " *
            "two-basin model --gis-basins2 runs.")
else
    println("FAILURES: ", join(fails, ", "))
    exit(1)
end
