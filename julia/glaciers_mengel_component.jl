## ============================================================================
## glaciers_mengel_component.jl
##
## Temperature-dependent-equilibrium mountain-glacier (GIC) module, ported from
## Mengel et al. 2016 (PNAS 113:2597; github.com/matthiasmengel/sealevel,
## contributor_functions.py). Drop-in replacement for BRICK's single-reservoir
## Wigley-Raper-Bakker `glaciers_small_icecaps`, fixing its commit-everything
## pathology (any sustained T>teq melts the WHOLE reservoir).
##
##   equilibrium:  S_eq(T) = a · (1 − exp(−b·(T − T_lia)))   (0 at T = T_lia; → a)
##   TWO-TIMESCALE transient (a single τ can't be fast-early + slow-modern):
##     dS_fast/dt = (f·S_eq − S_fast)/τ_fast      (committed early melt, short τ)
##     dS_slow/dt = ((1−f)·S_eq − S_slow)/τ_slow  (modern tracking, long τ)
##     S = S_fast + S_slow
##
## T = BRICK's global_surface_temperature (GMT anomaly rel 1850-1900, K = °C). The
## emulator is driven by TOTAL temperature (anthropogenic + natural forcing — they
## are NOT, and cannot be, disentangled, since the model sees one temperature).
##
## `gic_T_lia` = the glacier EQUILIBRIUM temperature ≈ the Little-Ice-Age climate
## (negative, rel 1850-1900). It makes glaciers OUT of equilibrium at the 1850-1900
## baseline (S_eq(0) = a(1−exp(b·T_lia)) > 0), so they are COMMITTED to melt by
## post-LIA warming that predates the forcing window — this SIMULATES the committed/
## disequilibrium early-20th-c melt directly (no external "natural" budget, no
## forcing split). It is the physical generalization of the single-reservoir gsic_teq.
##
## A sustained warming T* commits only S_eq(T*) < a — a temperature-appropriate
## remnant survives (NO full depletion). Output var `gsic_sea_level` kept identical
## so the component wires into global_sea_level unchanged. Mengel published coeffs
## (19 glacier-model fits, median a≈0.47 m, b≈0.52 /K); we calibrate (a,b,τ,T_lia,S₀)
## to Frederikse Glaciers 1900-2018 + Dyurgerov 1961-2003.
## ============================================================================

using Mimi

@defcomp glaciers_mengel begin
    gic_a        = Parameter()                             # asymptotic max contribution from the LIA state (m SLE)
    gic_b        = Parameter()                             # temperature sensitivity (1/K)
    gic_T_lia    = Parameter()                             # glacier equilibrium (LIA) temperature, rel 1850-1900 (°C, <0)
    gic_f        = Parameter()                             # fast-mode fraction of the equilibrium (0-1)
    gic_tau_fast = Parameter()                             # fast (committed) response timescale (yr)
    gic_tau_slow = Parameter()                             # slow (modern) response timescale (yr)
    gic_sl0      = Parameter()                             # initial SL contribution at start year (m)
    global_surface_temperature = Parameter(index=[time])   # total T anomaly rel 1850-1900 (K)

    gsic_fast      = Variable(index=[time])                # fast-mode contribution (m)
    gsic_slow      = Variable(index=[time])                # slow-mode contribution (m)
    gsic_sea_level = Variable(index=[time])                # total cumulative SL contribution (m)

    function run_timestep(p, v, d, t)
        if is_first(t)
            v.gsic_fast[t] = p.gic_f * p.gic_sl0
            v.gsic_slow[t] = (1 - p.gic_f) * p.gic_sl0
            v.gsic_sea_level[t] = p.gic_sl0
        else
            S_eq = p.gic_a * (1 - exp(-p.gic_b * (p.global_surface_temperature[t-1] - p.gic_T_lia)))
            v.gsic_fast[t] = v.gsic_fast[t-1] + (p.gic_f * S_eq       - v.gsic_fast[t-1]) / p.gic_tau_fast
            v.gsic_slow[t] = v.gsic_slow[t-1] + ((1-p.gic_f) * S_eq   - v.gsic_slow[t-1]) / p.gic_tau_slow
            v.gsic_sea_level[t] = v.gsic_fast[t] + v.gsic_slow[t]
        end
    end
end
