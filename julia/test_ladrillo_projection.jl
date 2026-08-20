## ============================================================================
## test_ladrillo_projection.jl — model tests for the Ladrillo projection kernel
##
## The kernel (julia/ladrillo_projection.jl) is what every extC-era driver runs,
## so it is tested against an INDEPENDENT reference rather than against itself:
##
##   [1] per-block glacier drivers == the python offline reference
##       (outputs/extc_port_reference.csv, emitted by
##       python/emit_extc_port_reference.py) at BOTH fixed amp bases
##   [2] per-block melt series through the Mimi component at the reference
##       theta == the python integrator                       (independent port)
##   [3] slot contract: gsic_sea_level == gsic_hind + gsic_r19
##   [4] posterior contract: every column the kernel reads exists; applying a
##       draw is deterministic (bit-identical on re-run)
##   [5] F_unch is a hindcast construct: flat after 2005, and worth ~1 mm as a
##       baseline sliver in a 1995-2014-referenced projection
##   [6] physical monotonicity: SSP1-2.6 < SSP2-4.5 < SSP5-8.5 at 2100, on
##       matched draws, for the total and for every ice component
##
## Tests [1]-[3] mirror julia/validate_glaciers_nu3.jl, which validates the same
## physics through the CALIBRATOR's code path. Both must pass: together they
## show the calibrator and the projection kernel build the same model.
##
##   julia --project=julia_v2 julia/test_ladrillo_projection.jl [n_draws]
## ============================================================================

using CSV, DataFrames, Mimi, Printf, Statistics
include(joinpath(@__DIR__, "ladrillo_projection.jl"))

# The canonical posterior decides which Greenland the model is built with;
# read it off the file rather than assuming the vintage (it moved extC -> L10).
const VARIANT = ladrillo_posterior_variant()

const NDRAW = length(ARGS) >= 1 ? parse(Int, ARGS[1]) : 100
const TOL_PORT = 1e-9      # python-vs-Julia port tolerance (full-precision CSVs)
const TOL_EXACT = 1e-12    # same-run algebraic identities

const REF    = CSV.read(joinpath(LADRILLO_REPO, "outputs/extc_port_reference.csv"), DataFrame)
const REF_TH = CSV.read(joinpath(LADRILLO_REPO, "outputs/extc_port_reference_theta.csv"), DataFrame)
const BC     = CSV.read(LADRILLO_BLOCK_CONSTANTS_CSV, DataFrame)
bcrow(b) = BC[findfirst(==(b), BC.block), :]

failures = String[]
function check(name, ok, detail="")
    @printf("  %-58s %s%s\n", name, ok ? "PASS" : "FAIL", isempty(detail) ? "" : "  ($detail)")
    ok || push!(failures, name)
    return ok
end

## ---------------------------------------------------------------------------
## The calibration-window setup: same years and same forcing as the calibrator,
## so the python reference is comparable.
## ---------------------------------------------------------------------------
println("[setup] calibration window 1850-2026, forcing ssp245harm")
hind = ladrillo_setup(gis_variant = VARIANT, ssp="ssp245", y0=1850, y1=2026, forcing_tag="ssp245harm", ref=(1995, 2005))
@assert Int.(REF.year) == hind.years "port reference year grid mismatch"
# The A+B Greenland slot has NO defaults: ladrillo_setup deliberately leaves its
# seven parameters unset so a projection cannot silently run on placeholder
# Greenland (Mimi refuses to build instead). The glacier tests below only need
# the model to build, so seed it with one posterior draw; [1]-[3] then overwrite
# every glacier parameter they actually test.
#
# THE CONDITION IS "not :stock", NOT ":ab". It was `=== :ab` until 2026-08-20, which
# was correct only while :ab was the sole non-stock variant. `greenland_3basin` carries
# the SAME seven unset shape parameters, so under :basins / :basins2 the seed was
# skipped and run(hind.m) failed to build — which is exactly what happened the moment
# L14 was promoted and VARIANT became :basins2. The reason in the comment above was
# always the right one; the condition just did not match it.
VARIANT !== :stock && ladrillo_apply_draw!(hind, ladrillo_posterior(nthin=1)[1, :])

## ---------------------------------------------------------------------------
## [1] drivers vs the python reference, both fixed amp bases
## ---------------------------------------------------------------------------
println("\n[1] per-block drivers vs python reference")
for (basis, key) in (("regchar", "reg"), ("obsfit", "obs")), b in LADRILLO_BLOCKS
    amp = Float64(bcrow(b)["amp_$basis"])
    d = maximum(abs.(ladrillo_driver(hind, b, amp) .- Float64.(REF[!, "drv_$(key)_$b"])))
    check("driver $b [$basis]", d <= TOL_PORT, @sprintf("max|diff| %.2e", d))
end

## ---------------------------------------------------------------------------
## [2] melt series at the reference theta, both bases
## ---------------------------------------------------------------------------
println("\n[2] per-block melt series at the reference theta vs python integrator")
for (basis, key) in (("regchar", "reg"), ("obsfit", "obs"))
    for r in eachrow(REF_TH)
        r.basis == key || continue
        blk = r.block
        update_param!(hind.m, :glaciers_small_icecaps, Symbol("gic_a_$blk"),     Float64(r.a))
        update_param!(hind.m, :glaciers_small_icecaps, Symbol("gic_b_$blk"),     Float64(r.b))
        update_param!(hind.m, :glaciers_small_icecaps, Symbol("gic_T_off_$blk"), Float64(r.T_off))
        update_param!(hind.m, :glaciers_small_icecaps, Symbol("gic_kappa_$blk"), Float64(r.kappa))
        update_param!(hind.m, :glaciers_small_icecaps, Symbol("gic_nu_$blk"),    Float64(r.nu))
        update_param!(hind.m, :glaciers_small_icecaps,
                      Symbol("glacier_surface_temperature_$blk"),
                      ladrillo_driver(hind, blk, Float64(r.amp)))
    end
    run(hind.m)
    for (b, var) in zip(LADRILLO_BLOCKS, (:gsic_r19, :gsic_slowp, :gsic_fast))
        d = maximum(abs.(Float64.(hind.m[:glaciers_small_icecaps, var]) .-
                         Float64.(REF[!, "s_$(key)_$b"])))
        check("series $b [$basis]", d <= TOL_PORT, @sprintf("max|diff| %.2e", d))
    end
    ## ---- [3] slot contract (holds for whatever is currently in the slot) ----
    if basis == "obsfit"
        println("\n[3] slot contract")
        d = maximum(abs.(Float64.(hind.m[:glaciers_small_icecaps, :gsic_sea_level]) .-
                         (Float64.(hind.m[:glaciers_small_icecaps, :gsic_hind]) .+
                          Float64.(hind.m[:glaciers_small_icecaps, :gsic_r19]))))
        check("gsic_sea_level == gsic_hind + gsic_r19", d <= TOL_EXACT,
              @sprintf("max|diff| %.2e", d))
    end
end

## ---------------------------------------------------------------------------
## [4] posterior contract + determinism
## ---------------------------------------------------------------------------
println("\n[4] posterior contract")
post_all = ladrillo_posterior(cols=:all)
missing_cols = setdiff(ladrillo_used_cols(VARIANT), names(post_all))
detail = isempty(missing_cols) ? "$(nrow(post_all)) draws x $(ncol(post_all)) cols" :
                                 string("missing ", join(missing_cols, ", "))
check("all kernel columns present in the subsample", isempty(missing_cols), detail)

post = ladrillo_posterior(nthin=NDRAW)
ladrillo_run_draw!(hind, post[1, :]); a1 = ladrillo_series(hind, :total)
ladrillo_run_draw!(hind, post[1, :]); a2 = ladrillo_series(hind, :total)
check("re-running draw 1 is bit-identical", maximum(abs.(a1 .- a2)) == 0.0)

## ---------------------------------------------------------------------------
## [5] F_unch behaves as a hindcast construct
## ---------------------------------------------------------------------------
println("\n[5] F_unch convention")
u = 25.0                                  # mm of uncharted stock (top of the prior)
i2005, i2026 = ladrillo_yi(hind, 2005), ladrillo_yi(hind, 2026)
funch_m = u .* hind.funch_unit
check("F_unch flat after 2005", abs(funch_m[i2026] - funch_m[i2005]) <= TOL_EXACT)
check("F_unch total stock == u", abs(1000 * funch_m[end] - u) <= 1e-9,
      @sprintf("%.4f mm", 1000 * funch_m[end]))
# In a 1995-2014-referenced projection the whole term is a constant offset that
# the re-referencing all but removes: quantify the residual sliver.
proj = ladrillo_setup(gis_variant = VARIANT, ssp="ssp245", y0=1850, y1=2300)
ladrillo_run_draw!(proj, post[1, :])
sliver = maximum(abs.(ladrillo_series(proj, :glaciers; funch=u) .-
                      ladrillo_series(proj, :glaciers))[[ladrillo_yi(proj, y) for y in 2050:2300]])
check("F_unch projection sliver < 2 mm at u=$(u) mm", sliver < 0.2,
      @sprintf("%.3f cm", sliver))

## ---------------------------------------------------------------------------
## [6] scenario monotonicity on matched draws
## ---------------------------------------------------------------------------
println("\n[6] scenario monotonicity at 2100 ($(nrow(post)) matched draws)")
const MONO_COMPONENTS = (:glaciers, :gis, :ais, :te, :total)
meds = Dict{String,Dict{Symbol,Float64}}()
for ssp in ("ssp126", "ssp245", "ssp585")
    bf = ssp == "ssp245" ? proj : ladrillo_setup(gis_variant = VARIANT, ssp=ssp, y0=1850, y1=2300)
    i2100 = ladrillo_yi(bf, 2100)
    vals = Dict(c => Float64[] for c in MONO_COMPONENTS)
    for r in eachrow(post)
        ladrillo_run_draw!(bf, r)
        for c in MONO_COMPONENTS
            v = ladrillo_series(bf, c)[i2100]
            isfinite(v) && push!(vals[c], v)
        end
    end
    meds[ssp] = Dict(c => median(vals[c]) for c in MONO_COMPONENTS)
    @printf("  %-8s %s  (finite %d/%d)\n", ssp,
            join([@sprintf("%s %6.1f", c, meds[ssp][c]) for c in MONO_COMPONENTS], "  "),
            length(vals[:total]), nrow(post))
end
for c in MONO_COMPONENTS
    check("$c median rises ssp126 < ssp245 < ssp585",
          meds["ssp126"][c] < meds["ssp245"][c] < meds["ssp585"][c])
end

## ---------------------------------------------------------------------------
println("\n" * "="^72)
if isempty(failures)
    println("ladrillo_projection: ALL TESTS PASS")
else
    error("ladrillo_projection: $(length(failures)) FAILED — " * join(failures, "; "))
end
