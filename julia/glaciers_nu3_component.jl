# glaciers_nu3_component.jl — 3-reservoir Nauels-ν glacier component (extC surgery,
# 2026-08-09). Offline provenance: python/d1d_fourrung_seam.py (structure C_both:
# R19 {19} / SLOWP {03,09,07,06} / FAST {13 regions}) + d1e_dside_ledger.py (D-ledger)
# + build_extc_inputs.py (constants). Marcus green-light 2026-08-09.
#
# Per-reservoir law (identical to glaciers_nu, replicated per block; the python
# reference is integrate_N in d0_glacier_shootout.py). The CONVENTIONS block in
# glaciers_nu_component.jl governs this module too — including the corrected
# note on the positive-part clamp (it binds on 4 of 7 van Vuuren markers and in
# the hindcast; it is kept on price, ≤ 0.24 cm at 2300, not on dormancy):
#   S_eq,b = a_b (1 − exp(−b_b (T_b − T_off_b)))
#   dS_b   = min(κ_b exc^ν_b, 1) (S_eq,b − S_b),  exc = T_b − T_eq(S_b)
# with LAGGED per-block drivers T_b[t−1] (frame: glacier-area K rel 1850–1900,
# amp_b-spliced forward — the frame contract from glaciers_nu applies to every
# block driver: the names deliberately do NOT match Mimi's shared
# :model_global_surface_temperature, so nothing auto-connects raw GMST).
#
# OUTPUT CONTRACT: gsic_sea_level (the block SUM) must remain the single slot
# Variable — :global_sea_level reads it and AIS consumes the summed path.
# gsic_hind (SLOWP+FAST) is the hindcast/ledger scope (r19 seam: the target's
# Frederikse segment assumes zero r19 melt; GlaMBIE r19 is removed 2019+ on the
# obs side). Per-block Variables are exported for the GlaMBIE rate terms.

using Mimi

@defcomp glaciers_nu3 begin
    gic_a_R19       = Parameter()
    gic_b_R19       = Parameter()
    gic_T_off_R19   = Parameter()
    gic_kappa_R19   = Parameter()
    gic_nu_R19      = Parameter()
    gic_a_SLOWP     = Parameter()
    gic_b_SLOWP     = Parameter()
    gic_T_off_SLOWP = Parameter()
    gic_kappa_SLOWP = Parameter()
    gic_nu_SLOWP    = Parameter()
    gic_a_FAST      = Parameter()
    gic_b_FAST      = Parameter()
    gic_T_off_FAST  = Parameter()
    gic_kappa_FAST  = Parameter()
    gic_nu_FAST     = Parameter()
    gic_sl0         = Parameter()          # initial cumulative melt per block (0)
    glacier_surface_temperature_R19   = Parameter(index=[time])
    glacier_surface_temperature_SLOWP = Parameter(index=[time])
    glacier_surface_temperature_FAST  = Parameter(index=[time])

    gsic_r19       = Variable(index=[time])
    gsic_slowp     = Variable(index=[time])
    gsic_fast      = Variable(index=[time])
    gsic_hind      = Variable(index=[time])    # SLOWP + FAST (hindcast/ledger scope)
    gsic_sea_level = Variable(index=[time])    # ALL blocks — the slot contract

    function run_timestep(p, v, d, t)
        if is_first(t)
            v.gsic_r19[t] = p.gic_sl0
            v.gsic_slowp[t] = p.gic_sl0
            v.gsic_fast[t] = p.gic_sl0
        else
            v.gsic_r19[t] = _nu_step(v.gsic_r19[t-1],
                p.glacier_surface_temperature_R19[t-1],
                p.gic_a_R19, p.gic_b_R19, p.gic_T_off_R19,
                p.gic_kappa_R19, p.gic_nu_R19)
            v.gsic_slowp[t] = _nu_step(v.gsic_slowp[t-1],
                p.glacier_surface_temperature_SLOWP[t-1],
                p.gic_a_SLOWP, p.gic_b_SLOWP, p.gic_T_off_SLOWP,
                p.gic_kappa_SLOWP, p.gic_nu_SLOWP)
            v.gsic_fast[t] = _nu_step(v.gsic_fast[t-1],
                p.glacier_surface_temperature_FAST[t-1],
                p.gic_a_FAST, p.gic_b_FAST, p.gic_T_off_FAST,
                p.gic_kappa_FAST, p.gic_nu_FAST)
        end
        v.gsic_hind[t] = v.gsic_slowp[t] + v.gsic_fast[t]
        v.gsic_sea_level[t] = v.gsic_hind[t] + v.gsic_r19[t]
    end
end

# one reservoir, one step — bit-matches integrate_N (d0_glacier_shootout.py)
function _nu_step(S, T, a, b, T_off, kappa, nu)
    ## FLOOR (2026-08-31, Marcus). S_eq = a(1 − exp(−b(T − T_off))) goes NEGATIVE below
    ## T_off, i.e. equilibrium BELOW the 1850 state, on 12.9 % of block × draw cells at
    ## vvLN/2300 on our own climate and 47.6 % on MAGICC's. Under the old melt-only ratchet
    ## that was unreachable and therefore harmless; once regrowth is allowed it would let
    ## glaciers regrow PAST their pre-industrial extent, which nothing we calibrate against
    ## speaks to and which is LESS defensible than the ratchet it replaces. The floor is not
    ## our invention: MAGICC's own tabulated equilibrium is defined on 0.0-10.3 K with NO
    ## negative branch and a POSITIVE 27.6-135.9 mm committed loss at zero warming
    ## (`magicc_glacier_drawnset`), so the one comparator that does regrow regrows toward a
    ## positive floor too. Price on our forcing: it removes 0.33 cm of the 2.16 cm headroom
    ## at vvLN (15 %) and 0.20 of 2.40 at vvML (8 %).
    S_eq = max(a * (1 - exp(-b * (T - T_off))), 0.0)
    frac_left = max(1 - S / a, 1e-12)
    T_eq = T_off - log(frac_left) / b
    ## BOUNDED REGROWTH replaces the positive-part ratchet. `exc` is a DISTANCE from
    ## equilibrium and the old clamp discarded its sign; keeping the sign is the natural
    ## continuation of the same law, not a reparameterisation. Because `mult` is capped at 1
    ## the step is a convex combination of S and S_eq, so with S_eq >= 0 the stock can never
    ## be driven below the floor -- the boundedness is structural, not a second clamp.
    d = T - T_eq
    mult = min(kappa * abs(d)^nu, 1.0)
    d < 0.0 && (mult /= GIC_REGROW_R)
    return S + mult * (S_eq - S)
end
