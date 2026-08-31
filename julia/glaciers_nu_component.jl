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
##   transient:    dS/dt   = κ · (S_eq − S) · |T − T_eq|^ν        (Nauels 2017 Eq. 3,
##                                                                 regrowth at 1/R)
##   ⚠ S_eq is FLOORED at the pre-industrial state: max(S_eq, 0).
##
## Conventions (documented decisions, 2026-08-07):
##   * ⚠ SUPERSEDED 2026-08-31 (Marcus): THE POSITIVE-PART CLAMP IS GONE, replaced by a
##     FLOORED equilibrium plus bounded regrowth at 1/R (R = 1, symmetric). The reasoning
##     that retired it, and the price, are in glaciers_nu3_component.jl `_nu_step`. The
##     history below is kept because it records WHY the ratchet was there and how its
##     justification went stale — not because it still describes the code.
##   * [HISTORICAL] POSITIVE-PART CLAMP: melt-only ratchet — no regrowth on these timescales
##     (accumulation-limited asymmetry). Nauels 2017 states no convention; a
##     non-integer ν forces a choice.
##     ⚠ IT IS NOT A DORMANT CONVENTION — corrected 2026-08-31, the original
##     "only binds under strong-cooling scenarios" was written when the SSPs
##     were the only scenario family. On the van Vuuren markers it binds on 4
##     of 7, and it binds inside the HINDCAST for SLOWP and FAST. It is
##     nonetheless still worth keeping, on PRICE rather than on dormancy:
##     removing it entirely (symmetric relaxation) moves 2300 by ≤ 0.24 cm and
##     2100/2150 by exactly zero on every marker, while shifting the in-scope
##     hindcast by 0.014 cm = 3% of the gsic target's median 1σ — active but
##     invisible, so a regrowth rate could not be fitted here in any case.
##     Under MAGICC's own (colder) climate the same bound rises to ~10 cm, so
##     the price is a statement about OUR forcing, not about the law.
##     python/scope_glacier_regrowth.py, python/scope_glacier_equilibrium.py.
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

## THE REGROWTH ASYMMETRY. ⚠ DEFINED HERE, IN THE FIRST-INCLUDED FILE, and read by BOTH
## glacier components. It lived in glaciers_nu3_component.jl for one commit, which is
## included SECOND (brick_mengel.jl:24-25) -- the reference from this file resolved only
## because Julia looks a global up at CALL time, so including this file alone would have
## thrown UndefVarError at the first timestep rather than at load. Regrowth runs at 1/R of the melt rate at the same distance
## from equilibrium. R = 1 is SYMMETRIC relaxation -- the fastest this law permits, and the
## value the clamp pricing was computed at (python/scope_glacier_regrowth.py's R_LADDER
## starts here). ⚠ IT IS A STATED CONVENTION, NOT A FITTED QUANTITY: the hindcast moves by
## 0.014 cm = 3 % of the gsic target's median 1 sigma when the clamp is removed, so a
## regrowth rate is LIKELIHOOD-INERT here and no refit can inform it (`no_power_null`).
## Changing it is a one-line change on purpose; the ladder [1, 3, 10, 30, 100] is priced in
## outputs/scope_glacier_regrowth_L21.csv.
const GIC_REGROW_R = 1.0



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
            # FLOOR + BOUNDED REGROWTH — see the CONVENTIONS block above and the full
            # rationale in glaciers_nu3_component.jl `_nu_step`, which is the SHIPPED module.
            S_eq = max(p.gic_a * (1 - exp(-p.gic_b * (T - p.gic_T_off))), 0.0)
            frac_left = max(1 - S / p.gic_a, 1e-12)
            T_eq = p.gic_T_off - log(frac_left) / p.gic_b
            d    = T - T_eq
            mult = min(p.gic_kappa * abs(d)^p.gic_nu, 1.0)
            d < 0.0 && (mult /= GIC_REGROW_R)
            v.gsic_sea_level[t] = S + mult * (S_eq - S)
        end
    end
end
