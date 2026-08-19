# greenland_3basin_component.jl — the 3-basin (Mouginot sector) Greenland, 2026-08-19.
#
# WHY THIS EXISTS. `greenland_ab` is calibrated to the TOTAL Greenland loss while
# driven by a single regional temperature, so its fitted parameters compensate for
# mass that came from basins it does not represent. Scored against Mouginot 2019
# Dataset S2, NW is the most OVER-active region in Greenland (17.3% of the volume,
# 31.7% of the 1972-2018 loss) — the shipped model absorbs that into the south
# basin's rate constants. This component carries the three Mouginot SECTOR groups
# separately so a per-sector SHARES likelihood term has per-sector state to score.
#
#   south = SW + CW + CE + SE      mid = NW      high = NO + NE
#
# Geometry lives ENTIRELY IN THE LIKELIHOOD, not in the drivers: all three basins
# read the SAME `greenland_surface_temperature`, per Marcus 2026-08-18 ("a single
# Greenland amplification number would probably be acceptable, and the different
# temperatures for the different basins would probably be internalized in the
# calibration process"). Stated cost, on the record: a single amp assumes the basin
# temperature RATIOS stay fixed, and they do not (north amp 2.83 vs south 1.92).
# Cheap to revisit — the per-zone drivers exist and are guard-proved.
#
# THE REDUCTION (Marcus 2026-08-19, matching python/scope_gis_3basin_partition.py
# so P1/P2/P3 in that prototype remain the reference for this component):
#
#   * each basin keeps the shipped A+B SHAPE parameters (c1, c0, f, alpha, beta)
#   * its commitment is scaled by its FIXED volume share k_b (sum_b k_b == 1)
#   * its ONE free knob is the rate scale s_b, multiplying BOTH channel rates
#
# So the restructure adds exactly THREE sampled parameters. The high basin's
# volume TAP is deliberately NOT here — deferred to a later commit (it only bites
# near 2300, where the shares term cannot see it). The mid basin gets NO tap at
# all: Aschwanden (PMC6584365) has NW outlet glaciers going land-terminating with
# "ice discharge there ... greatly reduced" by 2300 under RCP8.5 — a DECELERATION,
# the opposite sign from a tap. Carried as a stated caveat that NW is biased
# slightly HIGH at 2300, not parameterised.
#
# NESTING. With k = (1, 0, 0) and s = (1, 1, 1) this component reproduces
# `greenland_ab` EXACTLY (julia/test_greenland_3basin_nesting.jl gates it at the
# floating-point level). That is the analogue of the mock's 6e-17 gate and is what
# separates a wiring bug from a physics result.
#
# COMMITMENT CLAMP — PER-BASIN, [0, k_b * gis_v0] (Marcus 2026-08-19). A basin
# cannot lose more ice than it has, and the 2300 regime under SSP5-8.5 — where a
# whole-sheet cap and a per-basin cap diverge for the high basin — is exactly the
# regime the restructure exists to get right.
#
# It is also the choice that keeps the partition EXACT rather than merely
# approximate, which the prototype's form does not:
#
#     min(max(k*x, 0), k*v0)  ==  k * min(max(x, 0), v0)     for k > 0
#
# so eq_b == k_b * eq_whole IDENTICALLY, in the saturated regime as well as out of
# it, and sum_b eq_b == eq_whole always. The prototype's ab_series() clamps each
# basin to the WHOLE-SHEET v0, which agrees over the hindcast (the cap never binds
# there, so P1/P2/P3 are unaffected) but BREAKS additivity once the commitment
# exceeds v0: the basins would then sum to x rather than to v0.
#
# OUTPUT CONTRACT. greenland_sea_level / gis_fast / gis_slow are the BASIN SUMS and
# keep their meaning from greenland_ab, so every downstream consumer — the slot
# read by :global_sea_level, the Mouginot ice-sheet-WIDE share term, --gis-check,
# ladrillo_projection — is unchanged. The per-basin series are exported ADDITIONALLY
# as gis_sl_{south,mid,high} for the sector shares term and its diagnostic.
#
# UNITS: metres SLE throughout, BRICK's convention, as in greenland_ab.

using Mimi

# Mouginot 2019 Dataset S2 sector volumes, m SLE (python/diag_gis_basin_lit_check.py):
# south 3.35 / mid 1.27 / high 2.73, summing to 7.35 against the calibrator's
# structural GIS_V0_M = 7.42. The k_b below are SHARES of the sector sum, applied to
# whichever v0 the calibrator sets, so the 0.07 m discrepancy does not enter twice.
const GIS3_VOL_M = (south = 3.35, mid = 1.27, high = 2.73)
const GIS3_VSHARE = (south = GIS3_VOL_M.south / sum(GIS3_VOL_M),
                     mid   = GIS3_VOL_M.mid   / sum(GIS3_VOL_M),
                     high  = GIS3_VOL_M.high  / sum(GIS3_VOL_M))
const GIS3_BASINS = (:south, :mid, :high)

@defcomp greenland_3basin begin
    gis_c1      = Parameter()   # equilibrium sensitivity, m SLE per K of the REGIONAL driver
    gis_c0      = Parameter()   # committed loss at zero driver anomaly, m SLE
    gis_v0      = Parameter()   # total Greenland volume, m SLE (the commitment cap)
    gis_f       = Parameter()   # fast (surface-mass-balance) share of the commitment
    gis_alpha_f = Parameter()   # fast rate, per yr per K
    gis_beta_f  = Parameter()   # fast rate at zero anomaly, per yr
    gis_alpha_s = Parameter()   # slow (dynamic) rate, per yr per K
    gis_beta_s  = Parameter()   # slow rate at zero anomaly, per yr
    gis_g       = Parameter()   # fraction of the 1850 commitment already realised

    # per-basin volume shares — FIXED, never sampled (they are Mouginot geometry)
    gis_k_south = Parameter()
    gis_k_mid   = Parameter()
    gis_k_high  = Parameter()
    # per-basin rate scales — the three sampled knobs the restructure adds
    gis_s_south = Parameter()
    gis_s_mid   = Parameter()
    gis_s_high  = Parameter()

    greenland_surface_temperature = Parameter(index=[time])   # REGIONAL, shared by all basins

    gis_eq              = Variable(index=[time])   # WHOLE-SHEET committed loss, m SLE
    # per-basin CHANNEL state. These are the integrated quantities — the basin
    # totals below are derived from them, so they must be Variables (carried to
    # t+1), not locals.
    gis_fast_south      = Variable(index=[time])
    gis_fast_mid        = Variable(index=[time])
    gis_fast_high       = Variable(index=[time])
    gis_slow_south      = Variable(index=[time])
    gis_slow_mid        = Variable(index=[time])
    gis_slow_high       = Variable(index=[time])
    gis_sl_south        = Variable(index=[time])
    gis_sl_mid          = Variable(index=[time])
    gis_sl_high         = Variable(index=[time])
    gis_fast            = Variable(index=[time])   # basin SUM — contract preserved
    gis_slow            = Variable(index=[time])   # basin SUM — contract preserved
    greenland_sea_level = Variable(index=[time])   # the slot contract

    function run_timestep(p, v, d, t)
        # the whole-sheet commitment, reported for continuity with greenland_ab;
        # each basin re-derives its own from k_b so the clamp applies per basin
        v.gis_eq[t] = _gis3_eq(p.greenland_surface_temperature[t], 1.0,
                               p.gis_c1, p.gis_c0, p.gis_v0)
        ks = (p.gis_k_south, p.gis_k_mid, p.gis_k_high)
        ss = (p.gis_s_south, p.gis_s_mid, p.gis_s_high)
        if is_first(t)
            fast_b = ntuple(b -> p.gis_g * p.gis_f *
                                 _gis3_eq(p.greenland_surface_temperature[t], ks[b],
                                          p.gis_c1, p.gis_c0, p.gis_v0), 3)
            slow_b = ntuple(b -> p.gis_g * (1 - p.gis_f) *
                                 _gis3_eq(p.greenland_surface_temperature[t], ks[b],
                                          p.gis_c1, p.gis_c0, p.gis_v0), 3)
        else
            Tm = p.greenland_surface_temperature[t-1]
            prev_f = (v.gis_fast_south[t-1], v.gis_fast_mid[t-1], v.gis_fast_high[t-1])
            prev_s = (v.gis_slow_south[t-1], v.gis_slow_mid[t-1], v.gis_slow_high[t-1])
            fast_b = ntuple(3) do b
                eqm = _gis3_eq(Tm, ks[b], p.gis_c1, p.gis_c0, p.gis_v0)
                rf = _gis3_rate(Tm, ss[b], p.gis_alpha_f, p.gis_beta_f)
                prev_f[b] + (p.gis_f * eqm - prev_f[b]) * rf
            end
            slow_b = ntuple(3) do b
                eqm = _gis3_eq(Tm, ks[b], p.gis_c1, p.gis_c0, p.gis_v0)
                rs = _gis3_rate(Tm, ss[b], p.gis_alpha_s, p.gis_beta_s)
                prev_s[b] + ((1 - p.gis_f) * eqm - prev_s[b]) * rs
            end
        end
        v.gis_fast_south[t], v.gis_fast_mid[t], v.gis_fast_high[t] = fast_b
        v.gis_slow_south[t], v.gis_slow_mid[t], v.gis_slow_high[t] = slow_b
        v.gis_sl_south[t] = fast_b[1] + slow_b[1]
        v.gis_sl_mid[t]   = fast_b[2] + slow_b[2]
        v.gis_sl_high[t]  = fast_b[3] + slow_b[3]
        v.gis_fast[t] = fast_b[1] + fast_b[2] + fast_b[3]
        v.gis_slow[t] = slow_b[1] + slow_b[2] + slow_b[3]
        v.greenland_sea_level[t] = v.gis_fast[t] + v.gis_slow[t]
    end
end

"""Basin committed loss, commitment scaled by k_b and clamped to the basin's OWN
capacity [0, k_b*v0]. Identically equal to k_b * (the whole-sheet committed loss),
saturated or not — see the header note."""
_gis3_eq(T, k, c1, c0, v0) = min(max(k * (c1 * T + c0), 0.0), k * v0)

"""Relaxation rate per year, BOTH channels scaled by the basin rate scale s_b.
The 1e-9 floor and 1.0 ceiling are applied AFTER the scaling, matching
ab_series(): np.clip(s_r * (alpha*T + beta), 1e-9, 1.0)."""
_gis3_rate(T, s, alpha, beta) = min(max(s * (alpha * T + beta), 1e-9), 1.0)
