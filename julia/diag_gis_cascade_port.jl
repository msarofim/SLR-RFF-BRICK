## ============================================================================
## diag_gis_cascade_port.jl — DOES THE WIRED CASCADE REPRODUCE THE OFFLINE PRICE?
##
## The 2-stage cascade cell (V = 6.0 m, tau = 800 yr, onset 4.69 K, whole-sheet)
## was selected entirely offline, in python/scope_gis_reservoir_offline.py, on an
## emulator of this component. A cell priced on a mock and wired into the real
## model is two different objects until that is MEASURED — the standing port-test
## discipline. Three things can differ and all three are checked here:
##
##   [P] the LEVEL. Offline says Greenland ssp585@2300 goes 49.9 -> 98.2 cm.
##   [C] the CLAMP. The offline mock is UNCAPPED additive; the component clamps.
##       With V = 6.0 m on the WHOLE-SHEET home the headroom is v0 - (fast+slow),
##       not k_high*v0 ~ 2.76 m, which is exactly why the home had to move.
##   [I] INERTNESS. 2100 and the cool scenarios must be untouched, as offline.
##
## READ-ONLY: changes nothing, ships nothing, writes one CSV.
##   julia --project=julia_v2 julia/diag_gis_cascade_port.jl
## ============================================================================
using CSV, DataFrames, Mimi, Printf, Statistics
include(joinpath(@__DIR__, "ladrillo_projection.jl"))

const Y0, Y1 = 1850, 2300
const NTHIN  = 400
const CELL   = (V_m = 6.0, onset_K = 4.69, tau_yr = 800.0, stages = 2.0)
## The offline prediction this port is scored against, from
## outputs/scope_gis_reservoir_offline_wideV_n2_onsetladder_tolspread.csv.
const OFFLINE_2300 = (var"SSP1-2.6" = 10.1, var"SSP2-4.5" = 18.3, var"SSP5-8.5" = 98.2)
const OFFLINE_BASE_2300 = (var"SSP1-2.6" = 10.1, var"SSP2-4.5" = 18.3, var"SSP5-8.5" = 49.9)
const PORT_TOL_CM = 3.0      # emulator-vs-model; a LEVEL check, not an identity one
const SSPS = [("ssp126", "SSP1-2.6"), ("ssp245", "SSP2-4.5"), ("ssp585", "SSP5-8.5")]
const HORIZONS = (2100, 2150, 2300)

const POSTERIOR = LADRILLO_POSTERIOR_CSV
post = ladrillo_posterior(path=POSTERIOR, nthin=NTHIN)
const VARIANT = ladrillo_posterior_variant(POSTERIOR)
@printf("cascade port | %s (%d draws) | :%s | cell V %.2f m tau %.0f onset %.2f K stages %d | whole-sheet\n\n",
        basename(POSTERIOR), nrow(post), VARIANT, CELL.V_m, CELL.tau_yr,
        CELL.onset_K, Int(CELL.stages))

out = DataFrame(ssp=String[], year=Int[], untapped=Float64[], cascade=Float64[],
                delta=Float64[], offline=Float64[])
worst_clamp = 0.0
for (ssp, label) in SSPS
    bf0 = ladrillo_setup(ssp=ssp, y0=Y0, y1=Y1, gis_variant=VARIANT)
    bf1 = ladrillo_setup(ssp=ssp, y0=Y0, y1=Y1, gis_variant=VARIANT)
    ladrillo_set_tap!(bf1; v=CELL.V_m, onset=CELL.onset_K, tau=CELL.tau_yr,
                      stages=CELL.stages, wholesheet=true)
    ny = length(bf0.years)
    g0 = Array{Float64}(undef, ny, nrow(post)); g1 = similar(g0)
    for (j, r) in enumerate(eachrow(post))
        ladrillo_run_draw!(bf0, r); g0[:, j] = ladrillo_series(bf0, :gis)
        ladrillo_run_draw!(bf1, r); g1[:, j] = ladrillo_series(bf1, :gis)
        w = bf1.m[:greenland_icesheet, :gis_tap_wanted]
        a = bf1.m[:greenland_icesheet, :gis_tap_applied]
        global worst_clamp = max(worst_clamp, maximum(Float64.(w) .- Float64.(a)))
    end
    @printf("%-9s  %6s %10s %10s %9s %11s\n", label, "year", "untapped", "cascade",
            "delta", "offline")
    for y in HORIZONS
        i = ladrillo_yi(bf0, y)
        u = median(filter(isfinite, @view g0[i, :]))
        c = median(filter(isfinite, @view g1[i, :]))
        off = y == 2300 ? getproperty(OFFLINE_2300, Symbol(label)) : NaN
        @printf("           %6d %10.2f %10.2f %+9.3f %11s\n", y, u, c, c - u,
                isnan(off) ? "—" : @sprintf("%.1f", off))
        push!(out, (label, y, u, c, c - u, off))
    end
    println()
end
CSV.write(joinpath(LADRILLO_REPO, "outputs/diag_gis_cascade_port.csv"), out)

println("=== [C] THE CAPACITY CLAMP ===")
@printf("  max(wanted - applied) over every draw and year = %.4f m\n", worst_clamp)
println(worst_clamp == 0.0 ?
    "  NEVER BINDS ⇒ this wiring IS the offline mock's uncapped additive reservoir,\n  so the offline pricing transfers exactly." :
    "  IT BINDS ⇒ the wiring delivers LESS than was priced; the offline cell does NOT transfer.")

println("\n=== [P] THE PORT, and [I] INERTNESS ===")
fails = String[]
for (_, label) in SSPS
    r23 = out[(out.ssp .== label) .& (out.year .== 2300), :]
    d = abs(r23.cascade[1] - getproperty(OFFLINE_2300, Symbol(label)))
    ok = d <= PORT_TOL_CM
    @printf("  [P] %-9s 2300 wired %.2f vs offline %.1f cm  |diff| %.2f  %s\n",
            label, r23.cascade[1], getproperty(OFFLINE_2300, Symbol(label)), d,
            ok ? "PASS" : "FAIL")
    ok || push!(fails, "[P] $label")
    d21 = out[(out.ssp .== label) .& (out.year .== 2100), :].delta[1]
    ok2 = abs(d21) < 1e-9
    @printf("  [I] %-9s 2100 delta %+.3e cm  %s\n", label, d21,
            ok2 ? "PASS (exactly inert)" : "MOVES")
    label == "SSP5-8.5" || (ok2 || push!(fails, "[I] $label"))
end
println(isempty(fails) ? "\nPORT TEST PASSES." : "\nPORT FAILURES: " * join(fails, ", "))
