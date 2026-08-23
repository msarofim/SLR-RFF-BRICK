## ============================================================================
## test_gis_tap_wiring.jl — is the GREENLAND VOLUME TAP wired the way it was priced?
##
## The shipped cell (2-STAGE CASCADE, onset 4.69 K / V 5.64 m / tau 800 yr,
## WHOLE-SHEET home) is a PRIOR SPECIFICATION, not a fit, and it was priced on an
## OFFLINE MOCK whose reservoir is UNCAPPED ADDITIVE
## (python/scope_gis_reservoir_offline.py). Inside greenland_3basin it meets a
## capacity clamp. Handoff 2026-08-20c section 5: "Do not assume it survives."
## These gates measure the difference rather than assuming it away.
##
##   G3  NESTING      — at V = 0 the model is BIT-IDENTICAL to the untapped one.
##   G2  HORIZONS     — 2100 is an IDENTITY gate (exactly unmoved: the validated
##                      horizon). 2150 is a SPREAD-SCALED PLAUSIBILITY gate — it may
##                      move, by less than TOL_FRAC of Greenland's own sampled
##                      p05-p95 width there. The two are different in KIND and the
##                      code keeps them apart; see the block above PROTECTED_EXACT.
##   G2b SCENARIOS    — at the shipped onset the tap fires on ssp585 ONLY; cooler
##                      scenarios must deviate EXACTLY 0.0.
##   CAP              — does the capacity clamp ever bind? If not, this wiring IS
##                      the mock's additive reservoir and the pricing transfers.
##   VTILDE           — does the 1-D collapse (only V*u_2300 identified) survive
##                      wiring? Two cells with the SAME V*u_2300 must agree at 2300.
##   MUTATION         — every gate above must FAIL when the cell is perturbed.
##
## Run:  julia --project=julia_v2 julia/test_gis_tap_wiring.jl [--tag=L14]
## ============================================================================
using CSV, DataFrames, Printf, Statistics
include(joinpath(@__DIR__, "ladrillo_projection.jl"))

const REPO  = LADRILLO_REPO
const TAG   = let i = findfirst(a -> startswith(a, "--tag="), ARGS)
    i === nothing ? "L14" : ARGS[i][7:end]
end
const Y0, Y1     = 1850, 2300
const N_DRAWS    = 6
const EXACT_TOL  = 1e-12        # cm; "bit-identical" for a projection comparison
const LIVE_TOL   = 1e-2         # cm; a "must MOVE" check needs a floor
## ---- THE TWO PROTECTED HORIZONS, AND WHY THEY ARE DIFFERENT IN KIND ---------
##
## 2100 IS AN IDENTITY GATE. It is the horizon at which Greenland has genuine
## independent validation (ISMIP6, 16 ice-sheet models), and the shipped tap is
## exactly inert there: the onset is our own fair_mean ssp585's 2100 GMT, so the
## reservoir has released nothing by then. "Exactly 0.000e+00" is the correct
## assertion and it stays EXACT.
##
## 2150 IS A PLAUSIBILITY GATE, SCALED TO THE MODEL'S OWN SAMPLED SPREAD (rewritten
## 2026-08-23). History of this line, because it has been wrong twice in opposite
## directions:
##
##   * Until 2026-08-21 it read "6.5 K first fires 2155 ... so 2150 is protected",
##     which derives the protected horizon FROM THE CHOSEN CELL'S OWN FIRST-FIRE
##     YEAR — circular. That was corrected in place.
##   * Until 2026-08-23 it was an IDENTITY gate at 2150, and the comment it carried
##     named its own condition for revision: "do NOT narrow the admissible set on
##     2150 without a PHYSICS-BASED source at that horizon". At the time the only
##     two sources there were FACTS-FittedISMIP (an emulator fitted to ISMIP6) and
##     bamber19 (structured expert judgment) — neither physics.
##
## THAT CONDITION IS NOW MET. As of commit 166e1d2, SICOPOLIS (Greve) IS a
## physics-based source at 2150, and it reads 0.61-0.89x: we are LOW there, not
## high. So 2150 is no longer a horizon at which movement is presumptively wrong —
## it is one at which LARGE movement would be implausible. An identity gate cannot
## express that; a spread-scaled one can. Per the standing rule (memory
## `tolerance_scaled_to_spread`): plausibility tolerances scale to the sampled
## spread, identity gates stay exact. A bare cm figure here would be a plausibility
## gate held to an identity gate's tightness, which is exactly what was silently
## choosing tau at 2100 before 2026-08-23g.
##
## THE 2150 EVIDENCE IS CONTRADICTORY and that is a REPORTED result, not a bug:
## NORCE-CISM on the hot x2300 forcing says adding mass by 2150 pushes us out the
## top; SICOPOLIS on ssp585 GCM forcing says we are low. Both are like-for-like in
## forcing. The shipped cell sits inside BOTH bands.
const PROTECTED_EXACT  = 2100   # identity: the validated horizon, exactly unmoved
const PROTECTED_SCALED = 2150   # plausibility: may move, by < TOL_FRAC of the spread
## Fraction of Greenland's OWN sampled p05-p95 width at PROTECTED_SCALED that the
## tap may move the total by. 0.5 is the same fraction the 2100 offline tolerance
## settled on 2026-08-23g, where the score SATURATED between 0.5 and 1.0 — so the
## fraction is not delicate. The shipped cell uses 22.3% of the width.
const TOL_FRAC = 0.5
## The untapped deliverable the spread is MEASURED from, rather than a hardcoded cm
## figure that could drift away from the vintage under test. It is the same posterior
## and the same `gis_shape=true` configuration these arms run.
const SPREAD_SRC = joinpath(REPO, "outputs/ssps_components_2300_$(TAG).csv")
const FIRST_FIRE_MAX = 2200     # it must actually fire by here, or the cell is inert
const SUB = joinpath(REPO, "data/MimiBRICK/parameters_subsample_brick_mengel_$(TAG).csv")

fails = String[]
function chk(label, ok, detail="")
    @printf("  %-58s %s%s\n", label, ok ? "PASS" : "FAIL", isempty(detail) ? "" : "  ($detail)")
    ok || push!(fails, label)
    ok
end

isfile(SUB) || error("missing posterior subsample $SUB")
hdr = String.(propertynames(CSV.read(SUB, DataFrame; limit = 0)))
const VARIANT = ladrillo_gis_variant(hdr)
VARIANT in (:basins, :basins2) ||
    error("$TAG reads as :$VARIANT — the tap needs a basin posterior")
@printf("GIS tap wiring gate | tag %s | :%s | %d-%d\n", TAG, VARIANT, Y0, Y1)
@printf("  shipped cell: onset %.2f K / V %.1f m / tau %.0f yr / stages %d / %s home\n",
        GIS_TAP_CELL.onset_K, GIS_TAP_CELL.V_m, GIS_TAP_CELL.tau_yr,
        Int(GIS_TAP_CELL.stages), GIS_TAP_CELL.wholesheet ? "WHOLE-SHEET" : "high-basin")

## Greenland's OWN sampled p05-p95 width at PROTECTED_SCALED, on the scenario the
## 2150 gate is asserted on. Read, not assumed — and the read is asserted, because a
## silently-missing column would make the tolerance NaN and the gate vacuous.
## ⚠ `--no-tap` IS REQUIRED IN THAT COMMAND. The driver's default arm became the
## TAPPED one on 2026-08-23; this gate needs the BASE model's spread, or the
## tolerance it scales by would already contain the effect it is bounding.
isfile(SPREAD_SRC) || error("test_gis_tap_wiring: no untapped deliverable at " *
    "$SPREAD_SRC to measure the $(PROTECTED_SCALED) spread from. Produce it with\n" *
    "  julia --project=julia_v2 julia/project_ssps_components_ladrillo.jl <n> " *
    "--tag=$TAG --no-tap")
const SPREAD_2150 = let d = CSV.read(SPREAD_SRC, DataFrame),
                        m = (d.year .== PROTECTED_SCALED) .& (d.ssp .== "SSP5-8.5") .&
                            (d.component .== "gis")
    count(m) == 1 || error("$(count(m)) rows for gis/SSP5-8.5/$(PROTECTED_SCALED) in " *
                           relpath(SPREAD_SRC, REPO) * " — expected exactly 1")
    w = d.p95[m][1] - d.p05[m][1]
    isfinite(w) && w > 0 || error("degenerate sampled width $w cm at $(PROTECTED_SCALED)")
    w
end
const TOL_2150 = TOL_FRAC * SPREAD_2150
@printf("  %d gate: |move| < %.2f x %.2f = %.2f cm  (Greenland ssp585 p05-p95, %s)\n",
        PROTECTED_SCALED, TOL_FRAC, SPREAD_2150, TOL_2150,
        relpath(SPREAD_SRC, REPO))

need = ladrillo_used_cols(VARIANT)
rd = ladrillo_gis_needs_native(hdr) ?
    vcat(setdiff(need, LADRILLO_GIS_SLOW_NATIVE_COLS), LADRILLO_GIS_SLOW_REPARAM_COLS) : need
sub = CSV.read(SUB, DataFrame; select = unique(rd))
rows = Int.(round.(collect(range(1, nrow(sub), length = N_DRAWS))))
draws = ladrillo_native_greenland!(sub[rows, :])
sub = nothing; GC.gc()

"""Total and Greenland series for every draw, on one scenario, at one tap setting."""
function arm(ssp; v = 0.0, onset = GIS_TAP_CELL.onset_K, tau = GIS_TAP_CELL.tau_yr,
             stages = GIS_TAP_CELL.stages, wholesheet = GIS_TAP_CELL.wholesheet)
    bf = ladrillo_setup(ssp = ssp, y0 = Y0, y1 = Y1, gis_variant = VARIANT, gis_shape = true)
    v > 0 ? ladrillo_set_tap!(bf; v = v, onset = onset, tau = tau,
                              stages = stages, wholesheet = wholesheet) :
            update_gis3_tap!(bf.m, bf.gmst; v = 0.0)
    tot, gis = Vector{Float64}[], Vector{Float64}[]
    want, appl = Float64[], Float64[]
    for r in eachrow(draws)
        ladrillo_run_draw!(bf, r)
        push!(tot, Float64.(ladrillo_series(bf, :total)))
        push!(gis, Float64.(ladrillo_series(bf, :gis)))
        push!(want, maximum(Float64.(bf.m[_GIS_SLOT, :gis_tap_wanted])))
        push!(appl, maximum(Float64.(bf.m[_GIS_SLOT, :gis_tap_applied])))
    end
    (bf = bf, tot = tot, gis = gis, want = want, appl = appl)
end
yidx(bf, y) = ladrillo_yi(bf, y)
maxdiff(a, b) = maximum(maximum(abs.(x .- y)) for (x, y) in zip(a, b))

println("\n[G3] NESTING — V = 0 must be bit-identical to the untapped model")
a_off = arm("ssp585"; v = 0.0)
a_off2 = arm("ssp585"; v = 0.0, onset = 4.0, tau = 400.0)   # cell varied, V still 0
chk("[G3] V = 0 ignores onset and tau entirely", maxdiff(a_off.tot, a_off2.tot) <= EXACT_TOL,
    @sprintf("max|diff| = %.3e cm", maxdiff(a_off.tot, a_off2.tot)))
chk("[G3] V = 0 applies exactly zero tap", maximum(a_off.appl) == 0.0)

println("\n[G2] HORIZONS — identity at $PROTECTED_EXACT, spread-scaled at $PROTECTED_SCALED")
a_on = arm("ssp585"; v = GIS_TAP_CELL.V_m)
bf = a_on.bf
## IDENTITY. The validated horizon, and the tap is inert there by construction.
let i = yidx(bf, PROTECTED_EXACT)
    d = maximum(abs(a_on.tot[k][i] - a_off.tot[k][i]) for k in 1:N_DRAWS)
    chk("[G2] ssp585 total at $PROTECTED_EXACT is EXACTLY unmoved", d <= EXACT_TOL,
        @sprintf("max|diff| = %.3e cm", d))
end
## PLAUSIBILITY. May move; must stay small relative to what the model itself resolves.
let i = yidx(bf, PROTECTED_SCALED)
    d = maximum(abs(a_on.tot[k][i] - a_off.tot[k][i]) for k in 1:N_DRAWS)
    med = median(a_on.tot[k][i] - a_off.tot[k][i] for k in 1:N_DRAWS)
    chk("[G2] ssp585 total at $PROTECTED_SCALED moves < $(round(TOL_FRAC*100))% of its own spread",
        d < TOL_2150,
        @sprintf("max|move| %.2f cm = %.1f%% of the %.2f cm p05-p95 (median %+.2f cm)",
                 d, 100 * d / SPREAD_2150, SPREAD_2150, med))
end
## first year the tapped and untapped Greenland series part company
ff = let bfi = bf, first = nothing
    for (j, y) in enumerate(bf.years)
        d = maximum(abs(a_on.gis[k][j] - a_off.gis[k][j]) for k in 1:N_DRAWS)
        if d > EXACT_TOL; first = y; break; end
    end
    first
end
chk("[G2] first divergence is AFTER $PROTECTED_EXACT", ff !== nothing && ff > PROTECTED_EXACT,
    "first year = $(something(ff, "NEVER"))")
chk("[G2] and it does fire by $FIRST_FIRE_MAX", ff !== nothing && ff <= FIRST_FIRE_MAX,
    "first year = $(something(ff, "NEVER"))")
i23 = yidx(bf, 2300)
d23 = median(a_on.gis[k][i23] - a_off.gis[k][i23] for k in 1:N_DRAWS)
chk("[G2] and it MOVES 2300", abs(d23) > LIVE_TOL,
    @sprintf("median Greenland@2300 shift = %+.2f cm", d23))

println("\n[G2b] SCENARIOS — at the shipped onset the tap acts on ssp585 ONLY")
for ssp in ("ssp126", "ssp245")
    off, on = arm(ssp; v = 0.0), arm(ssp; v = GIS_TAP_CELL.V_m)
    d = maxdiff(on.tot, off.tot)
    chk("[G2b] $ssp deviates EXACTLY 0.0 over 1850-$Y1", d == 0.0,
        @sprintf("max|diff| = %.3e cm; peak GMT %.2f K vs onset %.1f K",
                 d, maximum(off.bf.gmst), GIS_TAP_CELL.onset_K))
end

println("\n[CAP] does the capacity clamp bind? (whole-sheet home ⇒ v0, not k_high*v0)")
bite = maximum(a_on.want .- a_on.appl)
chk("[CAP] measured", true, @sprintf("max(wanted - applied) = %.4f m over %d draws", bite, N_DRAWS))
if bite <= 1e-12
    println("      ⇒ the clamp NEVER binds at this cell, so this wiring IS the mock's " *
            "uncapped additive tap and the offline pricing transfers exactly.")
else
    println("      ⇒ the clamp BITES by $(round(bite, digits=4)) m. This wiring is NOT the " *
            "mock's reservoir and the cell must be RE-PRICED here, not reused.")
end

println("\n[VTILDE] does the 1-D collapse survive wiring? same V*u_2300, different (V, tau)")
## The offline scorecard identified only Vtilde = V * u_2300. If that survives, two
## cells with equal Vtilde agree at 2300. u_2300 is read from the model, not assumed.
##
## THE DELIVERED UNIT IS gis_tap_s2 ON A CASCADE, not gis_tap_s (2026-08-23). At
## stages >= 2 the released volume is V * s2 and s1 is an internal state — reading s1
## here would overstate u_2300 by ~4x and silently pick a matching V that is 4x too
## small, so the whole gate would compare the wrong pair and still print "SURVIVES".
u(a) = maximum(Float64.(a.bf.m[_GIS_SLOT,
              GIS_TAP_CELL.stages >= 2 ? :gis_tap_s2 : :gis_tap_s]))
vt_a = GIS_TAP_CELL.V_m * u(a_on)
## THE ALT CELL IS FASTER, NOT SLOWER. Matching Vtilde at a LONGER tau needs a LARGER
## V, and at these tau the required V runs past the whole sheet (gis_v0 ~ 7.4 m) —
## the capacity clamp would then bind and the comparison would be of two different
## objects. A shorter tau needs a smaller V and stays inside the sheet. The property
## under test is direction-agnostic; the clamp is not, so the bite is checked below.
const VT_TAU_FACTOR = 0.25
a_tau = arm("ssp585"; v = GIS_TAP_CELL.V_m, tau = GIS_TAP_CELL.tau_yr * VT_TAU_FACTOR)
u_tau = u(a_tau)
v_match = vt_a / u_tau
a_match = arm("ssp585"; v = v_match, tau = GIS_TAP_CELL.tau_yr * VT_TAU_FACTOR)
d_match = median(a_match.gis[k][i23] - a_on.gis[k][i23] for k in 1:N_DRAWS)
bite_match = maximum(a_match.want .- a_match.appl)
@printf("  cell A: V %.2f m  tau %4.0f  u_2300 %.4f  Vtilde %.4f m\n",
        GIS_TAP_CELL.V_m, GIS_TAP_CELL.tau_yr, u(a_on), vt_a)
@printf("  cell B: V %.2f m  tau %4.0f  u_2300 %.4f  Vtilde %.4f m\n",
        v_match, GIS_TAP_CELL.tau_yr * VT_TAU_FACTOR, u_tau, v_match * u_tau)
@printf("  Greenland@2300 median difference between them: %+.3f cm  (cell B clamp bite %.4f m)\n",
        d_match, bite_match)
println(bite_match > 1e-12 ?
    "      ⇒ VOID: the clamp bit on cell B, so the two cells are not the same object " *
    "and this comparison says nothing. Lower VT_TAU_FACTOR further." :
    abs(d_match) <= 0.5 ?
    "      ⇒ the Vtilde collapse SURVIVES wiring (< 0.5 cm) — the scorecard's 1-D " *
    "identification still holds and the shortlist carries over." :
    "      ⇒ the Vtilde collapse does NOT survive wiring. The design principle still " *
    "holds but the specific cell may move; RECOMPUTE the shortlist in the component.")

println("\n[MUT] the gates must FAIL when the cell is perturbed")
## REPOINTED 2026-08-23 AT THE *NEW* BOUND. The old mutation (onset 4.0 K) was built
## to violate an IDENTITY gate at 2150 and would still "pass" trivially against a
## spread-scaled one — a mutation that cannot break the gate under test leaves that
## gate untested. tau is the knob the 2150 bound actually constrains: at the shipped
## V and onset it is the delivery SPEED that decides how much arrives by 2150, so a
## short tau is the perturbation the bound exists to catch.
const MUT_TAU = 100.0
a_fast = arm("ssp585"; v = GIS_TAP_CELL.V_m, tau = MUT_TAU)
i50 = yidx(bf, PROTECTED_SCALED)
d_fast = maximum(abs(a_fast.tot[k][i50] - a_off.tot[k][i50]) for k in 1:N_DRAWS)
chk("[MUT] tau $(Int(MUT_TAU)) yr DOES breach the $PROTECTED_SCALED bound (so [G2] can fail)",
    d_fast > TOL_2150,
    @sprintf("max|move| = %.2f cm vs bound %.2f cm", d_fast, TOL_2150))
## and the IDENTITY half must be breakable too, or [G2]'s exact gate is untested
a_early = arm("ssp585"; v = GIS_TAP_CELL.V_m, onset = 3.0)
i00 = yidx(bf, PROTECTED_EXACT)
d_early = maximum(abs(a_early.tot[k][i00] - a_off.tot[k][i00]) for k in 1:N_DRAWS)
chk("[MUT] onset 3.0 K DOES move $PROTECTED_EXACT (so [G2]'s identity gate can fail)",
    d_early > LIVE_TOL, @sprintf("max|diff| = %.3f cm", d_early))
off245, on245e = arm("ssp245"; v = 0.0), arm("ssp245"; v = GIS_TAP_CELL.V_m, onset = 2.0)
d245 = maxdiff(on245e.tot, off245.tot)
chk("[MUT] onset 2.0 K DOES fire on ssp245 (so [G2b] can fail)", d245 > LIVE_TOL,
    @sprintf("max|diff| = %.3f cm", d245))

println()
if isempty(fails)
    println("ALL TAP WIRING GATES PASS.")
else
    println("FAILURES: ", join(fails, ", ")); exit(1)
end
