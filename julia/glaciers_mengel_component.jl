## ============================================================================
## glaciers_mengel_component.jl
##
## Temperature-dependent-equilibrium mountain-glacier (GIC) module, ported from
## Mengel et al. 2016 (PNAS 113:2597; github.com/matthiasmengel/sealevel,
## contributor_functions.py). Drop-in replacement for BRICK's single-reservoir
## Wigley-Raper-Bakker `glaciers_small_icecaps`, fixing its commit-everything
## pathology (any sustained T>teq melts the WHOLE reservoir).
##
##   equilibrium:  S_eq(ΔT) = a · (1 − exp(−b·ΔT))     (saturates at a; 0 at ΔT=0)
##   transient:    dS/dt = (S_eq(ΔT) − S)/τ            (Mengel Eq. 1)
##
## A sustained warming ΔT* commits only S_eq(ΔT*) < a — a temperature-appropriate
## remnant survives (NO full depletion unless ΔT→∞). ΔT = GMT anomaly rel
## pre-industrial (K = °C), i.e. BRICK's global_surface_temperature on the
## 1850-1900 baseline. Output variable name `gsic_sea_level` is kept identical to
## the original so the component wires into global_sea_level unchanged.
##
## Mengel published equilibrium coeffs (19 glacier-model fits, median a≈0.47 m,
## b≈0.52 /K); τ is calibrated to obs. We calibrate (a,b,τ,S₀) to Frederikse
## Glaciers 1900-2018 + Dyurgerov 1961-2003.
## ============================================================================

using Mimi

@defcomp glaciers_mengel begin
    gic_a   = Parameter()                                  # asymptotic max contribution (m SLE)
    gic_b   = Parameter()                                  # temperature sensitivity (1/K)
    gic_tau = Parameter()                                  # response timescale (yr)
    gic_sl0 = Parameter()                                  # initial SL contribution at start year (m)
    global_surface_temperature = Parameter(index=[time])   # ΔT rel pre-industrial (K)

    gsic_sea_level = Variable(index=[time])                # cumulative SL contribution (m)

    function run_timestep(p, v, d, t)
        if is_first(t)
            v.gsic_sea_level[t] = p.gic_sl0
        else
            S_eq = p.gic_a * (1 - exp(-p.gic_b * p.global_surface_temperature[t-1]))
            v.gsic_sea_level[t] = v.gsic_sea_level[t-1] + (S_eq - v.gsic_sea_level[t-1]) / p.gic_tau
        end
    end
end
