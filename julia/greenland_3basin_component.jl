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
# ---- the TWO-BASIN configuration (Marcus 2026-08-20) --------------------------
# Merge NW into the active basin; leave the high basin alone. k_mid = 0 makes this
# component a genuine two-basin model BY CONSTRUCTION rather than by test: the clamp
# algebra above gives eq_b == k_b * eq_whole IDENTICALLY, so a zero share contributes
# a zero series to every sum and to gis_fast / gis_slow / greenland_sea_level.
#
#   active = SW + CW + CE + SE + NW   carried in the `south` SLOT, which is NOT
#                                     renamed: the output contract is what every
#                                     downstream consumer reads
#   high   = NO + NE                  unchanged
#
# = (0.628571, 0, 0.371429). DERIVED here, ONCE, so the calibrator's --gis-basins2
# and test_greenland_3basin_nesting.jl [4] cannot drift apart, and so a revision of
# the Mouginot inventory (GIS3_VOL_M) propagates to both.
#
# WHY two. Refitting every structure in the offline harness returns s_mid = 1.024;
# pinning it to 1 costs Delta nlp 0.0023 and the profile is WELL CURVED (+6.3 at
# s_mid 0.25, +7.3 at 3.98), so s_mid is IDENTIFIED-and-equal-to-1, not merely
# unconstrained. Two basins also fit the Mouginot windows better (worst |z| 0.69 vs
# 1.01) with one fewer parameter. See notes/handoff_2026-08-20b_tap_priced.md.
const GIS2_VSHARE = (south = GIS3_VSHARE.south + GIS3_VSHARE.mid,
                     mid   = 0.0,
                     high  = GIS3_VSHARE.high)

# ---- the HIGH-BASIN VOLUME TAP (Marcus 2026-08-20) ---------------------------
# WHAT IT IS. A third discharge channel on the high (NO+NE) basin that opens above
# a GLOBAL temperature onset: a unit tap S_t relaxes with timescale tau toward a
# soft ramp in GMT, and V*S_t of extra loss is released. Form ported verbatim from
# python/scope_gis_tap_l13.py's tap_unit().
#
# WHY IT EXISTS. No basin structure buys the 2300 scenario separation: 1/2/3 basins
# give ssp585/ssp245 Greenland ratios 2.69x / 2.73x / 2.72x — and the CALIBRATED
# L14 confirms it at 2.73x (50.0 vs 18.3 cm) — against the literature's 7.9-31.9x.
# The restructure fixes the PARTITION; the tap fixes the SEPARATION.
#
# IT IS A PRIOR SPECIFICATION, NOT A FIT — say so in any methods text. It is also
# exactly LIKELIHOOD-INERT: G-INERT is 0.0 over the calibration window at this cell
# (the onset is 4.69 K against a calibration topping out at 1.385 K), so it is
# prior-propagated projection-side like `gis_amp` and needs NO refit. If anyone
# asks for a recalibration on account of the tap, that is a separate and much
# larger decision, not one this cell implies.
#
# ---- THE SHIPPED CELL, chosen 2026-08-23 (Marcus) ---------------------------
#   stages 2 (CASCADE) | V 6.0 m | tau 800 yr | onset 4.69 K | whole-sheet home
#
# WHY A CASCADE, AND NOT THE FIRST-ORDER FORM THIS BLOCK USED TO SHIP. The joint
# constraint is <= 8.1 cm added at 2150 on the ssp585 x2300 arm and 48.6 cm needed
# at 2300 to reach the matched p50 — a delivery ratio R = 6.03. A reservoir's
# response to its ramp is an n-fold repeated integral, so in the long-tau limit
# (the most back-loaded any n can be) n=1 gives 2.82, n=2 gives 7.86, n=3 gives
# 21.71; swept over onsets 1.6-7.5 K, n=1 peaks at 2.89. NO (V, tau, onset) of the
# first-order form can do it, and the same exact bound refutes every completely
# monotone family (ladder, Prony, stretched-exponential, Mittag-Leffler, power-law).
# A cascade is NOT completely monotone, so the bound does not reach it. See
# python/diag_gis_2150_band_veto.py and notes/handoff_2026-08-23c_form_refuted_cascade.md.
#
# WHY ONSET 4.69 AND NOT ~2.1-2.35 K, which several late-horizon scores prefer.
# Marcus 2026-08-23: "we aren't trying to match between-model spread (we don't have
# the precipitation level), just between-scenario spreads." Scored that way at 2300,
# a LOW onset fires the reservoir in SSP2-4.5 and SHRINKS ssp585/ssp245 BELOW the
# untapped model (2.73x -> 2.60x at onset 2.35) — the exact quantity the reservoir
# exists to buy. 4.69 K gives the highest separation on the whole ladder (5.38x),
# lands ssp585@2300 on the matched p50 (98.6 vs 98.5 cm) and is closest to Greve at
# 3001 (1.05x). A composite w-score mildly preferred 4.35 K, and that score is the
# one to DISCOUNT: it scores LEVEL agreement against ISM medians, which is a
# between-MODEL criterion in disguise. Report the scenario RATIO alongside any level
# score, and let the ratio break ties.
# CONSEQUENCE, recorded deliberately: the moderate-scenario per-tonne SC-GHG
# commitment term is EXACTLY ZERO at this onset. Buying it costs the scenario
# separation the model exists to produce. A nonzero moderate-scenario term needs a
# second, separately-justified arm, not a change to this cell.
#
# WHY THE WHOLE-SHEET HOME. V = 6.0 m exceeds the high basin's own k_high*v0 ~ 2.76 m
# ledger, so the high-basin clamp would silently deliver a fraction of what was
# priced. `wholesheet = 1` clamps against the whole sheet's headroom and keeps the
# tap out of the per-basin ledger; port-tested at 400 draws, the clamp NEVER binds
# (max(wanted - applied) = 0.0000 m), so the wiring IS the uncapped additive
# reservoir the cell was priced on. See julia/diag_gis_cascade_port.jl.
#
# 2150 IS NO LONGER AN IDENTITY-PROTECTED HORIZON, and that is EVIDENCE-DRIVEN.
# The old block protected 2150 because the free (V, tau) direction bit there, not
# because the model was validated there — and it said so, adding: "do NOT narrow the
# admissible set on 2150 without a physics-based source at that horizon". As of
# commit 166e1d2 SICOPOLIS IS such a source at 2150, and it reads 0.61-0.89x: we are
# LOW there, not high. The shipped cell moves 2150 by +2.58 cm = 22.3% of Greenland's
# own sampled p05-p95 width there, inside every version of the 2150 band. The gate is
# now a spread-scaled plausibility assertion, not an identity — see
# julia/test_gis_tap_wiring.jl [G2].
#
# THE 2150 EVIDENCE IS GENUINELY CONTRADICTORY, and that is a reported result, not an
# unresolved bug: NORCE-CISM on the hot x2300 forcing says adding mass by 2150 pushes
# us out the top, SICOPOLIS on ssp585 GCM forcing says we are low. Both are
# like-for-like in forcing. The chosen cell sits inside BOTH bands, which is why the
# contradiction does not block it.
#
# SUPERSEDED CELL, for provenance: (onset_K = 6.5, V_m = 2.0, tau_yr = 50.0,
# ramp_w_K = 1.0), first-order, high-basin home. Its outputs are quarantined under
# outputs/quarantine/20260823_old_tap_cell/.
const GIS_TAP_CELL = (onset_K = 4.69, V_m = 6.0, tau_yr = 800.0, ramp_w_K = 1.0,
                      stages = 2.0, wholesheet = true)
# THE ONSET IS IN GLOBAL MEAN TEMPERATURE, NOT the regional Greenland driver.
# 4.69 K is quoted in GMT — it is our own fair_mean ssp585's 2100 GMT — so the
# component takes its OWN gmt series. Using the regional driver would fire the tap
# roughly `gis_amp` (~1.92x) too early, and nothing would flag it.
const GIS_TAP_OFF = 0.0        # gis_tap_v = 0 is the OFF switch; the default
# ---- COMPONENT-LEVEL DEFAULTS vs THE SHIPPED CELL (kept DELIBERATELY apart) ---
# These two are what a model gets at BUILD time, and they stay at the PRE-CASCADE
# behaviour on purpose: anything that builds greenland_3basin without asking for the
# tap is bit-identical to every result predating 2026-08-23. The shipped cell's
# stages and home are carried by GIS_TAP_CELL and passed EXPLICITLY by
# update_gis3_tap! / ladrillo_set_tap!, so "build the model" and "turn the shipped
# tap on" are two separate acts and only the second one moves anything.
const GIS_TAP_STAGES_DEFAULT = 1.0    # BUILD-time; first-order. Shipped cell = 2.0
const GIS_TAP_WHOLESHEET_OFF = 0.0    # high-basin home + k_high*v0 clamp
const GIS_TAP_WHOLESHEET_ON  = 1.0    # whole-sheet clamp, tap OUT of the basin ledger

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
    # --- the high-basin volume tap. gis_tap_v = 0 is OFF and is the default, so
    # every existing consumer is bit-identical until it is switched on.
    gis_tap_v      = Parameter()              # m SLE released by the tap; 0 = OFF
    gis_tap_onset  = Parameter()              # K, GLOBAL mean temp rel 1850-1900
    gis_tap_tau    = Parameter()              # yr, tap discharge timescale
    gis_tap_ramp_w = Parameter()              # K, width of the soft GMT ramp
    gis_tap_gmt    = Parameter(index=[time])  # GLOBAL driver, K rel 1850-1900
    # --- TWO ADDITIVE CAPABILITIES, BOTH OFF BY DEFAULT (2026-08-23) ----------
    # Each defaults to the pre-existing behaviour EXACTLY, so every existing
    # consumer, every gate in test_gis_tap_wiring.jl and the shipped cell are
    # bit-identical until they are switched on. See the block in run_timestep.
    gis_tap_stages     = Parameter()   # 1 = first-order (DEFAULT); 2 = cascade
    gis_tap_wholesheet = Parameter()   # 0 = high-basin home (DEFAULT); 1 = whole sheet

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
    # tap diagnostics. `wanted` is V*S_t before the capacity clamp and `applied` is
    # what reached the basin, so `wanted - applied` measures EXACTLY how much the
    # k_b*v0 cap bit — the difference between this wiring and the offline mock's
    # uncapped additive tap, which is what the cell was priced on.
    gis_tap_s           = Variable(index=[time])   # the unit tap S_t, in [0, 1]
    gis_tap_s2          = Variable(index=[time])   # 2nd cascade stage, in [0, 1]
    gis_tap_wanted      = Variable(index=[time])   # V * S_t, m
    gis_tap_applied     = Variable(index=[time])   # after the capacity clamp, m
    gis_fast            = Variable(index=[time])   # basin SUM — contract preserved
    gis_slow            = Variable(index=[time])   # basin SUM + the tap — see below
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
        # THE CHANNEL STATES ARE PURE. The tap is deliberately NOT folded into
        # gis_slow_high[t]: that variable is carried to t+1 and relaxes toward
        # (1-f)*eq, so adding the tap to it would feed the tap back through the
        # basin's own relaxation and decay it — a completely different model from
        # the one the cell was priced on, and one that would look plausible.
        v.gis_slow_south[t], v.gis_slow_mid[t], v.gis_slow_high[t] = slow_b
        # --- the volume tap / reservoir ------------------------------------
        # S_t = first-order relaxation toward a soft ramp in GMT, using the
        # PREVIOUS year's ramp value, exactly as the fast/slow channels use T[t-1].
        # Ported from python/scope_gis_tap_l13.py tap_unit().
        #
        # STAGES (2026-08-23). `gis_tap_stages = 2` routes the ramp through a
        # SECOND reservoir in series. Why it exists: the joint 2150/2300 constraint
        # needs a delivery ratio of 6.03 and a single first-order reservoir cannot
        # exceed 2.89 at ANY onset (python/diag_gis_2150_band_veto.py), because its
        # response to a ramp is ~t early where a 2-stage cascade's is ~t^2. A
        # cascade is also NOT completely monotone, so the exact bound that refuted
        # the ladder / Prony / stretched-exponential / Mittag-Leffler / power-law
        # families does not reach it.
        #
        # tau REMAINS THE TOTAL MEAN DELAY -- each stage runs at stages/tau -- so at
        # stages = 1 the rate is 1/tau and this is the pre-existing recursion TERM
        # FOR TERM. That is why the default is bit-identical and is gated as such,
        # not argued. Mirrors scope_gis_reservoir_offline.reservoir_unit_n().
        if is_first(t)
            v.gis_tap_s[t] = 0.0
            v.gis_tap_s2[t] = 0.0
        else
            seqm = min(max((p.gis_tap_gmt[t-1] - p.gis_tap_onset) / p.gis_tap_ramp_w,
                           0.0), 1.0)
            rate = p.gis_tap_stages / p.gis_tap_tau
            v.gis_tap_s[t] = v.gis_tap_s[t-1] + (seqm - v.gis_tap_s[t-1]) * rate
            # stage 2 sees stage 1's PREVIOUS year, the same explicit scheme
            v.gis_tap_s2[t] = v.gis_tap_s2[t-1] +
                              (v.gis_tap_s[t-1] - v.gis_tap_s2[t-1]) * rate
        end
        tap_u = p.gis_tap_stages >= 2 ? v.gis_tap_s2[t] : v.gis_tap_s[t]
        v.gis_tap_wanted[t] = p.gis_tap_v * tap_u
        # CAPACITY CLAMP, per the component's own standing principle: a basin cannot
        # lose more ice than it has, [0, k_b*v0]. The offline mock's tap is UNCAPPED
        # additive, so this is the one place the wiring can differ from the pricing —
        # which is why `wanted` and `applied` are both exported rather than just the
        # sum. If the headroom never binds, the two are identical and the offline
        # pricing transfers exactly; that is a measurement, not an assumption.
        #
        # WHOLE-SHEET HOME (2026-08-23). The cells now under consideration carry
        # V up to the WHOLE SHEET (6.0-7.42 m). Clamping that against the high
        # basin's own k_high*v0 ~ 2.76 m ledger would silently deliver a fraction
        # of what was priced, and booking it into gis_sl_high would attribute
        # whole-sheet mass to one basin. `gis_tap_wholesheet = 1` clamps against
        # the WHOLE sheet's headroom and keeps the tap OUT of the per-basin
        # ledger entirely -- which is the component's own "THE CHANNEL STATES ARE
        # PURE" principle applied one level up. gis_slow and the total still carry
        # it, so the output contract is unchanged either way.
        head = p.gis_tap_wholesheet >= 0.5 ?
            max(p.gis_v0 - (fast_b[1] + fast_b[2] + fast_b[3] +
                            slow_b[1] + slow_b[2] + slow_b[3]), 0.0) :
            max(ks[3] * p.gis_v0 - (fast_b[3] + slow_b[3]), 0.0)
        v.gis_tap_applied[t] = min(v.gis_tap_wanted[t], head)
        v.gis_sl_south[t] = fast_b[1] + slow_b[1]
        v.gis_sl_mid[t]   = fast_b[2] + slow_b[2]
        v.gis_sl_high[t]  = fast_b[3] + slow_b[3] +
                            (p.gis_tap_wholesheet >= 0.5 ? 0.0 : v.gis_tap_applied[t])
        v.gis_fast[t] = fast_b[1] + fast_b[2] + fast_b[3]
        # THE TAP RIDES IN gis_slow, not gis_fast. It is a DYNAMIC discharge, not
        # surface mass balance, so this keeps gis_fast/total meaning "the SMB share"
        # — which is what the Mouginot surface-share term scores — and it keeps the
        # output contract greenland_sea_level == gis_fast + gis_slow intact, which
        # every downstream consumer and nesting gate [2] rely on.
        v.gis_slow[t] = slow_b[1] + slow_b[2] + slow_b[3] + v.gis_tap_applied[t]
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
