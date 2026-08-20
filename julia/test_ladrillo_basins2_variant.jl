## ============================================================================
## test_ladrillo_basins2_variant.jl — can the PROJECTOR tell a 2-basin posterior
## from a 3-basin one, and does it project it under the right geometry?
##
## WHY THIS EXISTS, and it is not hypothetical. Before 2026-08-19 the projection
## kernel knew only :stock and :ab, so an L13 (3-basin) chain read as :ab and every
## L13 projection ran at s = 1 — the partition-invariance null, a model that was
## never calibrated. That was worth -1.7 cm on the 2100 median
## (diag_l13_projection_variant.jl). Adding :basins closed it BY PRESENCE:
##     hasb3 = all(c in cols for ["gis_s_mid", "gis_s_high"])
## An L14 (--gis-basins2) chain carries gis_s_high but NOT gis_s_mid, because that
## parameter is dropped from FREE at k_mid = 0. So `hasb3` is FALSE for an L14 chain
## and it falls through to :ab — the SAME hole, one layout later, and silent.
##
## The fix distinguishes the layouts by the ABSENCE of gis_s_mid and binds
## GIS2_VSHARE rather than GIS3_VSHARE. This file gates BOTH halves. Every gate is
## mutation-tested or paired with a liveness check, because a gate that has only
## ever passed proves nothing (`mutation_test_gates`).
##
## Run:  julia --project=julia_v2 julia/test_ladrillo_basins2_variant.jl
## ============================================================================
using CSV, DataFrames, Printf, Statistics
include(joinpath(@__DIR__, "ladrillo_projection.jl"))

const REPO      = LADRILLO_REPO
const SSP       = "ssp245"
const Y0, Y1    = 1850, 2150
const HORIZONS  = [2100, 2150]
const GIS_SHAPE = true
const EXACT_TOL = 1e-9      # cm; the s = 1 equivalence is algebraic, not approximate
const LIVE_TOL  = 1e-3      # cm; a "these must DIFFER" check needs a floor, not 0
## The s_mid liveness floor is MUCH lower than LIVE_TOL on purpose, and the reason is
## the finding rather than a weak gate: s_mid is ~0.95, the mid basin is 17% of the
## volume, so dropping it moves a 2100 projection by ~0.002-0.02 cm. That smallness IS
## the case for two basins. LIVE_TOL (0.4 cm) is right for s_high, whose scale is 0.26.
const S_MID_LIVE_TOL = 1e-6
const N_DRAWS   = 8         # enough to be a draw-for-draw check, cheap enough to gate
## The fixture is a REAL 3-basin chain with gis_s_mid dropped — the exact column set
## an L14 chain has. Using the real file rather than a hand-built header means the
## detection is tested against the thing it will actually meet.
const SRC_CHAIN = joinpath(REPO, "outputs/mcmc/chain_L13_seed2026_n2000000.csv")

fails = String[]
function chk(label, ok, detail="")
    @printf("  %-56s %s%s\n", label, ok ? "PASS" : "FAIL", isempty(detail) ? "" : "  ($detail)")
    ok || push!(fails, label)
    ok
end

isfile(SRC_CHAIN) || error("missing fixture chain $SRC_CHAIN")
const HDR3 = String.(propertynames(CSV.read(SRC_CHAIN, DataFrame; limit = 0)))
const HDR2 = [c for c in HDR3 if c != "gis_s_mid"]
const HDRAB = [c for c in HDR3 if !(c in ["gis_s_mid", "gis_s_high"])]
const HDR_PARTIAL = [c for c in HDR3 if c != "gis_s_high"]

println("[1] variant DETECTION from the column set")
chk("a 3-basin header reads as :basins", ladrillo_gis_variant(HDR3) === :basins,
    ":$(ladrillo_gis_variant(HDR3))")
chk("a 2-basin header reads as :basins2", ladrillo_gis_variant(HDR2) === :basins2,
    ":$(ladrillo_gis_variant(HDR2))")
## THE REGRESSION, stated as its own gate. This is the assertion that would have
## failed before the fix, and it is the whole reason this file exists.
chk("a 2-basin header does NOT read as :ab (the -1.7 cm hole)",
    ladrillo_gis_variant(HDR2) !== :ab)
chk("a plain A+B header still reads as :ab", ladrillo_gis_variant(HDRAB) === :ab,
    ":$(ladrillo_gis_variant(HDRAB))")
## gis_s_mid without gis_s_high matches no calibrated layout. It must be refused,
## not silently answered with :ab.
chk("gis_s_mid without gis_s_high is REFUSED",
    (try; ladrillo_gis_variant(HDR_PARTIAL); false; catch; true; end))

println("\n[2] the k vector FOLLOWS the variant")
chk("ladrillo_basin_k(:basins) is the 3-basin geometry",
    ladrillo_basin_k(:basins) === GIS3_VSHARE)
chk("ladrillo_basin_k(:basins2) is the 2-basin geometry",
    ladrillo_basin_k(:basins2) === GIS2_VSHARE)
chk("the two geometries are NOT the same object",
    ladrillo_basin_k(:basins) !== ladrillo_basin_k(:basins2),
    "3-basin south $(round(GIS3_VSHARE.south, digits=6)) vs 2-basin $(round(GIS2_VSHARE.south, digits=6))")
chk("the 2-basin k has k_mid == 0 exactly", ladrillo_basin_k(:basins2).mid == 0.0)
chk("both k vectors sum to 1",
    abs(sum(ladrillo_basin_k(:basins)) - 1) < 1e-12 &&
    abs(sum(ladrillo_basin_k(:basins2)) - 1) < 1e-12)
chk("ladrillo_basin_k rejects a non-basin variant",
    (try; ladrillo_basin_k(:ab); false; catch; true; end))

println("\n[3] the column contract")
chk("used_cols(:basins2) reads gis_s_high", "gis_s_high" in ladrillo_used_cols(:basins2))
chk("used_cols(:basins2) does NOT read gis_s_mid",
    !("gis_s_mid" in ladrillo_used_cols(:basins2)))
chk("used_cols(:basins) still reads both",
    all(c -> c in ladrillo_used_cols(:basins), ["gis_s_mid", "gis_s_high"]))

## ---- the projection gates, on real draws ---------------------------------
println("\n[4] projection: :basins2 at s = 1 must reproduce :ab, draw for draw")
need = unique(vcat(ladrillo_used_cols(:basins), "gis_s_mid", "gis_s_high"))
rd = ladrillo_gis_needs_native(HDR3) ?
    vcat(setdiff(need, LADRILLO_GIS_SLOW_NATIVE_COLS), LADRILLO_GIS_SLOW_REPARAM_COLS) : need
df = CSV.read(SRC_CHAIN, DataFrame; select = rd)
rows = collect(range(nrow(df) ÷ 2 + 1, nrow(df), length = N_DRAWS))
draws = ladrillo_native_greenland!(df[Int.(round.(rows)), :])
df = nothing; GC.gc()

bf_ab = ladrillo_setup(ssp=SSP, y0=Y0, y1=Y1, gis_variant=:ab,      gis_shape=GIS_SHAPE)
bf_b2 = ladrillo_setup(ssp=SSP, y0=Y0, y1=Y1, gis_variant=:basins2, gis_shape=GIS_SHAPE)
bf_b3 = ladrillo_setup(ssp=SSP, y0=Y0, y1=Y1, gis_variant=:basins,  gis_shape=GIS_SHAPE)

draws_s1 = copy(draws)
draws_s1[!, "gis_s_high"] .= 0.0      # log10(1)
draws_s1[!, "gis_s_mid"]  .= 0.0
## THE k IDENTITY ARM. k2 = (k_south + k_mid, 0, k_high), so with s_mid forced to 1
##     :basins  = k_s f(1) + k_m f(1) + k_h f(s_h)
##     :basins2 = (k_s + k_m) f(1)   + k_h f(s_h)
## are the SAME NUMBER, exactly. That identity — not "the two arms differ" — is the
## gate on ladrillo_basin_k actually reaching update_gis3_shares!: it is exact, so it
## needs no threshold, and it FAILS at the ~0.1 cm level if the projector binds
## GIS3_VSHARE to a :basins2 setup.
draws_sm1 = copy(draws)
draws_sm1[!, "gis_s_mid"] .= 0.0

d_s1, d_ident = Ref(0.0), Ref(0.0)
d_live_ab, d_live_mid = Ref(Inf), Ref(Inf)
## LIVENESS ONLY ON DRAWS AWAY FROM THE NULL, and this cost a failing gate to learn:
## a min-over-draws "these must differ" check is hostage to one draw. Draw 3 of this
## fixture has s_mid = 1.0030, so :basins2 and :basins agree there to 6.9e-04 cm for
## an entirely correct reason, and the min collapsed to 0.0000. Select the draws where
## the parameter is actually doing something, and require that at least one exists.
const S_MID_AWAY = log10(1.10)          # 10% off the null
n_away = 0
for (r, r1, rm) in zip(eachrow(draws), eachrow(draws_s1), eachrow(draws_sm1))
    ladrillo_run_draw!(bf_ab, r);  tab = ladrillo_series(bf_ab, :total)
    ladrillo_run_draw!(bf_b2, r1); ts1 = ladrillo_series(bf_b2, :total)
    ladrillo_run_draw!(bf_b2, r);  tb2 = ladrillo_series(bf_b2, :total)
    ladrillo_run_draw!(bf_b3, r);  tb3 = ladrillo_series(bf_b3, :total)
    ladrillo_run_draw!(bf_b3, rm); tb3s = ladrillo_series(bf_b3, :total)
    away = abs(Float64(r["gis_s_mid"])) > S_MID_AWAY
    away && (global n_away += 1)
    for y in HORIZONS
        i = ladrillo_yi(bf_ab, y)
        d_s1[]    = max(d_s1[],    abs(ts1[i] - tab[i]))
        d_ident[] = max(d_ident[], abs(tb2[i] - tb3s[i]))
        d_live_ab[] = min(d_live_ab[], abs(tb2[i] - tab[i]))
        away && (d_live_mid[] = min(d_live_mid[], abs(tb2[i] - tb3[i])))
    end
end
chk("[4] :basins2 at s = 1 == :ab", d_s1[] <= EXACT_TOL,
    @sprintf("max|diff| = %.3e cm over %d draws x %d horizons", d_s1[], N_DRAWS, length(HORIZONS)))
chk("[4] :basins2 == :basins at s_mid = 1 (the k identity)", d_ident[] <= EXACT_TOL,
    @sprintf("max|diff| = %.3e cm; k_active must equal k_south + k_mid", d_ident[]))

## ---- and the checks that stop [4] passing vacuously ----------------------
println("\n[5] LIVENESS — [4] must not be true for the trivial reason")
## If the fitted s_high never reached the model, [4] would pass because BOTH arms
## were secretly running :ab. This requires the fitted arm to MOVE.
chk("[5] :basins2 at the FITTED s_high differs from :ab", d_live_ab[] > LIVE_TOL,
    @sprintf("min|diff| = %.4f cm (s_high must actually bind)", d_live_ab[]))
chk("[5] the fixture has draws away from the s_mid null", n_away >= 1,
    @sprintf("%d of %d draws with |log10 s_mid| > %.4f", n_away, N_DRAWS, S_MID_AWAY))
## On THOSE draws the two structures must part company — otherwise s_mid is being
## ignored by the :basins path and the identity above would be trivially true.
chk("[5] on those draws :basins2 differs from :basins", d_live_mid[] > S_MID_LIVE_TOL,
    @sprintf("min|diff| = %.3e cm over the %d away-from-null draws (floor %.0e; small BY DESIGN — see S_MID_LIVE_TOL)",
             d_live_mid[], n_away, S_MID_LIVE_TOL))

println()
if isempty(fails)
    println("ALL BASINS2 VARIANT GATES PASS — a 2-basin posterior is detected as " *
            ":basins2 and projected under GIS2_VSHARE, not silently as :ab.")
else
    println("FAILURES: ", join(fails, ", "))
    exit(1)
end
