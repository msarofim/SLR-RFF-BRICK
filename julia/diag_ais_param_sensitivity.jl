## ============================================================================
## diag_ais_param_sensitivity.jl — the ALIGNMENT CONTROL for the propagation test
##
## diag_iceflow0_propagation.jl reports that `ais_iceflow0` explains R^2 < 0.001
## of the projected Antarctic contribution at 2100, 2150 and 2300. For a
## grounding-line flux coefficient that is a surprising result, and a surprising
## result is presumptively an implementation problem: a draw/projection
## MISALIGNMENT would produce exactly that table, with every correlation ~0.
##
## This is the control. It correlates the same projection against parameters the
## AIS demonstrably depends on. If those come back ~0 too, the pipeline does not
## resolve parameter->projection dependence and the propagation verdict is void.
## If they come back large, `ais_iceflow0`'s ~0 is physics.
##
## It runs off the ACCEPTED POSTERIOR SUBSAMPLE rather than the chains, because
## the question is about the projection kernel, not about between-chain
## behaviour, and the subsample is 10 MB against 4 x 2.2 GB. (Reading the chains
## for this is what put the box into memory pressure and killed a run.)
##
##   julia --project=julia_v2 julia/diag_ais_param_sensitivity.jl [n_draws]
## ============================================================================
using CSV, DataFrames, Statistics, Printf

include(joinpath(@__DIR__, "ladrillo_projection.jl"))

const NTHIN    = length(ARGS) >= 1 ? parse(Int, ARGS[1]) : 1000
const SSP      = "ssp245"
const Y0, Y1   = 1850, 2300
const HORIZONS = [2100, 2150, 2300]
const AXIS     = "ais_iceflow0"
## Parameters the AIS projection MUST depend on, for the control:
##   antarctic_temp_threshold  the fast-dynamics tipping threshold
##   ais_gmst_amp              the GMST -> T_ant map (sets the forcing it sees)
##   antarctic_alpha           the ocean-forced ice-flow sensitivity
##   antarctic_gamma           the water-depth exponent in the flux law
##   ais_mu                    the ice-profile constant (sets volume per radius)
const CONTROLS = ["antarctic_temp_threshold", "ais_gmst_amp", "antarctic_alpha",
                  "antarctic_gamma", "ais_mu"]
const OUT = joinpath(LADRILLO_REPO, "outputs/diag_ais_param_sensitivity.csv")

const VARIANT = ladrillo_posterior_variant()
post = ladrillo_posterior(nthin = NTHIN)
bf = ladrillo_setup(ssp = SSP, y0 = Y0, y1 = Y1, gis_variant = VARIANT)
@printf("AIS parameter sensitivity | %s (%d draws) | %s | %d-%d\n",
        basename(LADRILLO_POSTERIOR_CSV), nrow(post), SSP, Y0, Y1)

ais = Dict(y => Float64[] for y in HORIZONS)
t0 = time()
for r in eachrow(post)
    ladrillo_run_draw!(bf, r)
    s = ladrillo_series(bf, :ais)
    for y in HORIZONS
        push!(ais[y], s[ladrillo_yi(bf, y)])
    end
end
@printf("  %d draws in %.0fs\n\n", nrow(post), time() - t0)

out = DataFrame(param = String[], horizon = Int[], r = Float64[], r2 = Float64[])
@printf("%-28s %9s %9s %9s\n", "parameter", "r@2100", "r@2150", "r@2300")
ctlmax = 0.0
for p in vcat([AXIS], CONTROLS)
    v = Float64.(post[!, p])
    rs = Float64[]
    for y in HORIZONS
        a = ais[y]
        ok = isfinite.(a)
        r = cor(v[ok], a[ok])
        push!(rs, r)
        push!(out, (p, y, r, r^2))
    end
    global ctlmax
    p != AXIS && (ctlmax = max(ctlmax, maximum(abs.(rs))))
    @printf("%-28s %+9.3f %+9.3f %+9.3f%s\n", p, rs..., p == AXIS ? "   <- the axis" : "")
end
CSV.write(OUT, out)

axmax = maximum(abs.(out[out.param .== AXIS, :r]))
@printf("\nlargest |r|: axis %.3f, controls %.3f\n", axmax, ctlmax)
if ctlmax > 0.20
    println("CONTROL PASSES — the kernel resolves parameter->projection dependence " *
            "($(round(ctlmax / max(axmax, 1e-9), digits=1))x the axis), so $AXIS's " *
            "~0 is PHYSICS, not misalignment.")
else
    println("CONTROL FAILS — no parameter correlates with the projection. Suspect a " *
            "draw/projection ALIGNMENT BUG; the propagation verdict is VOID until " *
            "this is resolved.")
end
@printf("\nwrote %s\n", OUT)
