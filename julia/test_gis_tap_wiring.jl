## ============================================================================
## test_gis_tap_wiring.jl — is the HIGH-BASIN VOLUME TAP wired the way it was priced?
##
## The cell (onset 6.5 K / V 2.0 m / tau 50 yr) is a PRIOR SPECIFICATION, not a fit,
## and it was priced on an OFFLINE MOCK whose tap is UNCAPPED ADDITIVE
## (python/scope_gis_tap_l13.py). Inside greenland_3basin the tap meets the basin's
## own k_b*v0 capacity clamp. Handoff 2026-08-20c section 5: "Do not assume it
## survives." These gates measure the difference rather than assuming it away.
##
##   G3  NESTING      — at V = 0 the model is BIT-IDENTICAL to the untapped one.
##   G2  HORIZONS     — tap-on equals tap-off through 2150 and diverges only after.
##                      This IS the design principle the cell was chosen by: the tap
##                      must not move a horizon at which the model has independent
##                      validation.
##   G2b SCENARIOS    — inside the Tier-1 bracket the tap fires on ssp585 ONLY;
##                      cooler scenarios must deviate EXACTLY 0.0.
##   CAP              — does k_b*v0 ever bind? If not, this wiring IS the mock's
##                      additive tap and the offline pricing transfers exactly.
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
## The horizon the tap must not move, and the first year it may. 6.5 K first fires
## 2155 on ssp585 per the offline narrowing, so 2150 is protected and 2155 is not.
const PROTECTED_THRU = 2150
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
@printf("GIS tap wiring gate | tag %s | :%s | %d-%d | cell onset %.1f K / V %.1f m / tau %.0f yr\n",
        TAG, VARIANT, Y0, Y1, GIS_TAP_CELL.onset_K, GIS_TAP_CELL.V_m, GIS_TAP_CELL.tau_yr)

need = ladrillo_used_cols(VARIANT)
rd = ladrillo_gis_needs_native(hdr) ?
    vcat(setdiff(need, LADRILLO_GIS_SLOW_NATIVE_COLS), LADRILLO_GIS_SLOW_REPARAM_COLS) : need
sub = CSV.read(SUB, DataFrame; select = unique(rd))
rows = Int.(round.(collect(range(1, nrow(sub), length = N_DRAWS))))
draws = ladrillo_native_greenland!(sub[rows, :])
sub = nothing; GC.gc()

"""Total and Greenland series for every draw, on one scenario, at one tap setting."""
function arm(ssp; v = 0.0, onset = GIS_TAP_CELL.onset_K, tau = GIS_TAP_CELL.tau_yr)
    bf = ladrillo_setup(ssp = ssp, y0 = Y0, y1 = Y1, gis_variant = VARIANT, gis_shape = true)
    v > 0 ? ladrillo_set_tap!(bf; v = v, onset = onset, tau = tau) :
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

println("\n[G2] HORIZONS — tap-on must not move a validated horizon")
a_on = arm("ssp585"; v = GIS_TAP_CELL.V_m)
bf = a_on.bf
for y in (2100, PROTECTED_THRU)
    i = yidx(bf, y)
    d = maximum(abs(a_on.tot[k][i] - a_off.tot[k][i]) for k in 1:N_DRAWS)
    chk("[G2] ssp585 total at $y is UNMOVED", d <= EXACT_TOL, @sprintf("max|diff| = %.3e cm", d))
end
## first year the tapped and untapped Greenland series part company
ff = let bfi = bf, first = nothing
    for (j, y) in enumerate(bf.years)
        d = maximum(abs(a_on.gis[k][j] - a_off.gis[k][j]) for k in 1:N_DRAWS)
        if d > EXACT_TOL; first = y; break; end
    end
    first
end
chk("[G2] first divergence is AFTER $PROTECTED_THRU", ff !== nothing && ff > PROTECTED_THRU,
    "first year = $(something(ff, "NEVER"))")
chk("[G2] and it does fire by $FIRST_FIRE_MAX", ff !== nothing && ff <= FIRST_FIRE_MAX,
    "first year = $(something(ff, "NEVER"))")
i23 = yidx(bf, 2300)
d23 = median(a_on.gis[k][i23] - a_off.gis[k][i23] for k in 1:N_DRAWS)
chk("[G2] and it MOVES 2300", abs(d23) > LIVE_TOL,
    @sprintf("median Greenland@2300 shift = %+.2f cm", d23))

println("\n[G2b] SCENARIOS — inside the bracket the tap acts on ssp585 ONLY")
for ssp in ("ssp126", "ssp245")
    off, on = arm(ssp; v = 0.0), arm(ssp; v = GIS_TAP_CELL.V_m)
    d = maxdiff(on.tot, off.tot)
    chk("[G2b] $ssp deviates EXACTLY 0.0 over 1850-$Y1", d == 0.0,
        @sprintf("max|diff| = %.3e cm; peak GMT %.2f K vs onset %.1f K",
                 d, maximum(off.bf.gmst), GIS_TAP_CELL.onset_K))
end

println("\n[CAP] does the k_b*v0 capacity clamp bind?")
bite = maximum(a_on.want .- a_on.appl)
chk("[CAP] measured", true, @sprintf("max(wanted - applied) = %.4f m over %d draws", bite, N_DRAWS))
if bite <= 1e-12
    println("      ⇒ the clamp NEVER binds at this cell, so this wiring IS the mock's " *
            "uncapped additive tap and the offline pricing transfers exactly.")
else
    println("      ⇒ the clamp BITES by $(round(bite, digits=4)) m. This wiring is NOT the " *
            "mock's tap and the six-cell shortlist must be RE-PRICED here, not reused.")
end

println("\n[VTILDE] does the 1-D collapse survive wiring? same V*u_2300, different (V, tau)")
## The offline scorecard identified only Vtilde = V * u_2300. If that survives, two
## cells with equal Vtilde agree at 2300. u_2300 is read from the model, not assumed.
u(a) = maximum(Float64.(a.bf.m[_GIS_SLOT, :gis_tap_s]))
vt_a = GIS_TAP_CELL.V_m * u(a_on)
a_alt = arm("ssp585"; v = GIS_TAP_CELL.V_m * 2, tau = GIS_TAP_CELL.tau_yr)
u_alt = u(a_alt)
## match Vtilde by solving for the V that pairs with the ALT tau
a_tau = arm("ssp585"; v = GIS_TAP_CELL.V_m, tau = GIS_TAP_CELL.tau_yr * 4)
u_tau = u(a_tau)
v_match = vt_a / u_tau
a_match = arm("ssp585"; v = v_match, tau = GIS_TAP_CELL.tau_yr * 4)
d_match = median(a_match.gis[k][i23] - a_on.gis[k][i23] for k in 1:N_DRAWS)
@printf("  cell A: V %.2f m  tau %3.0f  u_2300 %.4f  Vtilde %.4f m\n",
        GIS_TAP_CELL.V_m, GIS_TAP_CELL.tau_yr, u(a_on), vt_a)
@printf("  cell B: V %.2f m  tau %3.0f  u_2300 %.4f  Vtilde %.4f m\n",
        v_match, GIS_TAP_CELL.tau_yr * 4, u_tau, v_match * u_tau)
@printf("  Greenland@2300 median difference between them: %+.3f cm\n", d_match)
println(abs(d_match) <= 0.5 ?
    "      ⇒ the Vtilde collapse SURVIVES wiring (< 0.5 cm) — the scorecard's 1-D " *
    "identification still holds and the shortlist carries over." :
    "      ⇒ the Vtilde collapse does NOT survive wiring. The design principle still " *
    "holds but the specific cell may move; RECOMPUTE the shortlist in the component.")

println("\n[MUT] the gates must FAIL when the cell is perturbed")
a_early = arm("ssp585"; v = GIS_TAP_CELL.V_m, onset = 4.0)
i50 = yidx(bf, PROTECTED_THRU)
d_early = maximum(abs(a_early.tot[k][i50] - a_off.tot[k][i50]) for k in 1:N_DRAWS)
chk("[MUT] onset 4.0 K DOES move $PROTECTED_THRU (so [G2] can fail)", d_early > LIVE_TOL,
    @sprintf("max|diff| = %.3f cm", d_early))
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
