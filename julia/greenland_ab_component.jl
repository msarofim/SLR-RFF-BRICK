# greenland_ab_component.jl — Greenland pass 1, cell A+B (2026-08-10).
#
# Offline provenance: python/gis_offline_cell.py, cell "A+B". That cell was
# selected because it is the only one passing every pre-registered gate AND the
# Mouginot partition AND landing inside the FACTS/MAGICC 2100 spread band.
# Option C (the PISM equilibrium ladder as V_eq) FAILED there and is NOT in this
# component — see the CHANGELOG entry for 2026-08-10.
#
# TWO CHANGES from the stock MimiBRICK greenland_icesheet (SIMPLE / Bakker 2016):
#
#   A. REGIONAL DRIVER. The driver is southern-Greenland (59-70 N) annual
#      land-masked temperature, K rel 1850-1900, amp-spliced forward -- NOT
#      GMST. The parameter is deliberately named greenland_surface_temperature
#      so it does NOT auto-connect to Mimi's shared
#      :model_global_surface_temperature, exactly as the glacier blocks do.
#      This is what closes the 1942-1982 hindcast window: Greenland cooled at
#      -1.8 C/century from 1940 to 1990 while the globe warmed.
#
#   B. TWO CHANNELS. The commitment splits, fraction f realised fast (surface
#      mass balance) and 1-f slow (dynamic discharge), each on its own
#      alpha*T + beta rate. f is pinned by the Mouginot 2019 SMB/discharge
#      partition (73.5% surface), not by the sea-level history, which cannot
#      separate the channels on its own.
#
# The V/V0 damping of stock SIMPLE is DROPPED. Measured: it changes the 2100
# scenario spread by 0.0 cm (only ~1% of the ice sheet is gone by 2100, so
# V/V0 ~ 0.99) and it has the wrong sign physically.
#
# INITIAL CONDITION. gis_g is the fraction of the 1850 commitment already
# realised at 1850. Stock SIMPLE is gis_g = 0: it starts at V(1850) = v0, i.e.
# zero realised loss with a full v0 - V_eq(T_1850) = 0.71 m of disequilibrium
# already present. Getting this wrong makes the modern melt rate 0.11 mm/yr
# instead of ~0.7 -- it is the single easiest thing to break in this port.
#
# WHAT STEP 5 SAMPLES, decided 2026-08-12 (items 4.1 / 4.2 of
# notes/handoff_2026-08-11_greenland_pass1_complete.md §4). Evidence:
# python/diag_gis_g_betaf.py -> outputs/gis_g_betaf_{variants,profiles}.csv.
#
#   gis_g  -> FIX AT 0. NOT sampled. The hindcast cannot see it: profiled over
#     [0, 0.8] the objective moves by 4e-4 nlp and the 2100 projections do not
#     move at all (max |delta| 0.000 cm); the LR test accepts g = 0 at
#     2*delta = +0.001 against chi2(1) = 3.841. It is confounded with gis_c0 --
#     two converged fits returned (c0 61.99, g 0.917) and (c0 5.21, g 0.183)
#     at the same nlp = 17.856 with 2100 projections agreeing to < 0.001 cm.
#     It was only ever introduced so the (since-rejected) ladder cells could
#     start sensibly. Stock SIMPLE has g = 0 by construction, so this restores
#     BRICK's own initial condition.
#
#   gis_beta_f -> SAMPLED, FREE (Marcus, 2026-08-12). It is unidentified by the
#     GIS hindcast alone -- flat to delta < 2.3 across FIVE decades, 1e-6 to
#     9.8e-3 -- but it is NOT inconsequential: beta_f = 0 costs only
#     2*delta = +0.55 yet moves 2100 SSP5-8.5 by 1.70 cm and the scenario
#     spread by 1.28 cm. Fixing it would hide that uncertainty in a point
#     value; the joint likelihood is a different likelihood and may identify it.
#     NB the handoff's premise is FALSIFIED: a literature decadal SMB rate
#     (beta_f = 1/10 yr) is rejected at 2*delta = +133 and collapses the
#     Mouginot surface share to 0.34 against a 0.735 constraint. In the share
#     form the SMB channel drains a multi-millennial commitment, so "fast"
#     names which PHYSICS it carries, not a short time constant: at the
#     optimum tau_f = 86 yr. Do not re-fix it at a decadal value.
#     Flagged: the prior [1e-6, 0.5] spans four decades the offline fit
#     excludes; Marcus declined re-bounding, so watch sampler efficiency there.
#
# LAGGING. eq_volume and the rates are read at t-1, matching stock
# greenland_icesheet (which uses tau_inv[t-1] and eq_volume[t-1]) and matching
# the python reference integrate().
#
# UNITS: metres SLE throughout, BRICK's convention. The offline cell works in
# cm; python/emit_gis_port_reference.py does the conversion once, at emission.
#
# OUTPUT CONTRACT: greenland_sea_level is the single slot Variable that
# :global_sea_level reads. gis_fast / gis_slow are exported for the partition
# diagnostic and must sum to it exactly.

using Mimi

@defcomp greenland_ab begin
    gis_c1      = Parameter()   # equilibrium sensitivity, m SLE per K of the REGIONAL driver
    gis_c0      = Parameter()   # committed loss at zero driver anomaly, m SLE
    gis_v0      = Parameter()   # total Greenland volume, m SLE (the commitment cap)
    gis_f       = Parameter()   # fast (surface-mass-balance) share of the commitment
    gis_alpha_f = Parameter()   # fast rate, per yr per K
    gis_beta_f  = Parameter()   # fast rate at zero anomaly, per yr
    gis_alpha_s = Parameter()   # slow (dynamic) rate, per yr per K
    gis_beta_s  = Parameter()   # slow rate at zero anomaly, per yr
    gis_g       = Parameter()   # fraction of the 1850 commitment already realised
    greenland_surface_temperature = Parameter(index=[time])   # REGIONAL, not GMST

    gis_eq              = Variable(index=[time])   # committed loss, m SLE
    gis_fast            = Variable(index=[time])
    gis_slow            = Variable(index=[time])
    greenland_sea_level = Variable(index=[time])   # the slot contract

    function run_timestep(p, v, d, t)
        v.gis_eq[t] = _gis_eq(p.greenland_surface_temperature[t],
                              p.gis_c1, p.gis_c0, p.gis_v0)
        if is_first(t)
            v.gis_fast[t] = p.gis_g * p.gis_f * v.gis_eq[t]
            v.gis_slow[t] = p.gis_g * (1 - p.gis_f) * v.gis_eq[t]
        else
            Tm = p.greenland_surface_temperature[t-1]
            rf = _gis_rate(Tm, p.gis_alpha_f, p.gis_beta_f)
            rs = _gis_rate(Tm, p.gis_alpha_s, p.gis_beta_s)
            v.gis_fast[t] = v.gis_fast[t-1] +
                (p.gis_f * v.gis_eq[t-1] - v.gis_fast[t-1]) * rf
            v.gis_slow[t] = v.gis_slow[t-1] +
                ((1 - p.gis_f) * v.gis_eq[t-1] - v.gis_slow[t-1]) * rs
        end
        v.greenland_sea_level[t] = v.gis_fast[t] + v.gis_slow[t]
    end
end

"""Committed loss, clamped to [0, v0] — bit-matches np.clip in the reference."""
_gis_eq(T, c1, c0, v0) = min(max(c1 * T + c0, 0.0), v0)

"""Relaxation rate per year. The 1e-9 floor keeps it positive; the 1.0 ceiling
stops the explicit Euler step from overshooting. Both match the reference."""
_gis_rate(T, alpha, beta) = min(max(alpha * T + beta, 1e-9), 1.0)
