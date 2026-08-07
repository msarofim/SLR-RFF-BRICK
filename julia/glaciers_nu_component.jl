## ============================================================================
## glaciers_nu_component.jl
##
## extB3 glacier (GIC) module: Mengel-2016 EQUILIBRIUM curve + Nauels-2017
## (MAGICC Eq. 3) single-reservoir CLIMATE-SENSITIVE-KINETICS transient,
## driven by GLACIER-AREA temperature (Option D). Replaces the 2-tau
## glaciers_mengel component after the D0 shootout (2026-08-06/07; memo
## §3e): the 2-tau fast/slow split existed to fake the onset behavior that
## the regional driver + nu now provide mechanistically.
##
##   equilibrium:  S_eq(T) = a · (1 − exp(−b·(T − T_off)))     (Mengel 2016 form)
##   inverse:      T_eq(S) = T_off − ln(1 − S/a)/b             (survival threshold
##                                                              of the CURRENT stock)
##   transient:    dS/dt   = κ · (S_eq − S) · max(T − T_eq, 0)^ν   (Nauels 2017 Eq. 3)
##
## Conventions (documented decisions, 2026-08-07):
##   * POSITIVE-PART CLAMP: melt-only ratchet — no regrowth on these timescales
##     (accumulation-limited asymmetry). Nauels 2017 states no convention; a
##     non-integer ν forces a choice. Only binds under strong-cooling scenarios.
##   * ν = 0 recovers single-τ Mengel EXACTLY with κ = 1/τ (0^0 = 1 in Julia, so
##     the ν=0 limit relaxes BOTH ways — the nested-model reference arm).
##   * step multiplier capped at 1: a step never overshoots equilibrium.
##   * FRAME CONTRACT: all gic_* parameters are GLACIER-FRAME quantities
##     (per glacier-area K). The driver parameter is deliberately NAMED
##     `glacier_surface_temperature` — NOT `global_surface_temperature` — so
##     Mimi cannot silently rewire raw GMST into this component. Feed it
##     observed T_glac historically and amp_g × GMST in projection
##     (data/observations/t_glac_hadcrut5.csv; amp_g = 1.8, GlacierMIP3).
##     Feeding raw GMST under-responds by ~amp_g. See t_glac provenance sidecar.
##
## Output var `gsic_sea_level` keeps its name so the component wires into
## global_sea_level (and every downstream diagnostic) unchanged.
## ============================================================================

using Mimi

@defcomp glaciers_nu begin
    gic_a     = Parameter()                            # total meltable stock (m SLE), glacier-frame scope excl r5 incl r19
    gic_b     = Parameter()                            # equilibrium curvature (1/K, PER GLACIER-FRAME K)
    gic_T_off = Parameter()                            # equilibrium temperature offset (glacier-frame K rel 1850-1900, <0)
    gic_kappa = Parameter()                            # rate constant (1/yr/K^nu)
    gic_nu    = Parameter()                            # kinetics exponent (dimensionless, >=0; 0 == Mengel single-tau)
    gic_sl0   = Parameter()                            # initial cumulative melt at start year (m; 0 for the A2 inventory accounting)
    glacier_surface_temperature = Parameter(index=[time])  # GLACIER-AREA T anomaly rel 1850-1900 (K) — NOT GMST

    gsic_sea_level = Variable(index=[time])            # cumulative SL contribution (m)

    function run_timestep(p, v, d, t)
        if is_first(t)
            v.gsic_sea_level[t] = p.gic_sl0
        else
            S    = v.gsic_sea_level[t-1]
            T    = p.glacier_surface_temperature[t-1]
            S_eq = p.gic_a * (1 - exp(-p.gic_b * (T - p.gic_T_off)))
            frac_left = max(1 - S / p.gic_a, 1e-12)
            T_eq = p.gic_T_off - log(frac_left) / p.gic_b
            exc  = max(T - T_eq, 0.0)
            mult = min(p.gic_kappa * exc^p.gic_nu, 1.0)
            v.gsic_sea_level[t] = S + mult * (S_eq - S)
        end
    end
end
