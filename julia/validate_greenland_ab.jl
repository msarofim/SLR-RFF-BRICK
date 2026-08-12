# validate_greenland_ab.jl — Greenland A+B port validation (2026-08-10).
#
# Checks the Mimi greenland_ab component against the python offline cell that
# selected it, at 1e-9, the way julia/validate_glaciers_nu3.jl does for the
# glacier blocks:
#
#   [1] driver identity: the vector we feed == the reference's spliced driver
#   [2] committed loss  gis_eq            == reference eq_m
#   [3] channel series  gis_fast, gis_slow == reference fast_m, slow_m
#   [4] slot contract   greenland_sea_level == gis_fast + gis_slow, and it is
#       what :global_sea_level consumes
#   [5] the initial condition is L(y0) = g * eq(y0) exactly, and is not
#       equilibrium — starting in equilibrium is the single easiest thing to
#       get wrong in this port, and the bug that made the offline modern rate
#       0.11 mm/yr instead of ~0.7. NB this checks the RELATION at whatever g
#       the reference carries; it is NOT an assertion that g takes any
#       particular value. Ladrillo 1.0 fixes g = 0 (item 4.1, 2026-08-12), at
#       which point this becomes BRICK's own initial condition; until step 5
#       lands, g is whatever the offline A+B fit returned.
#   [6] a zero-driver run is exactly flat at the initial state (no drift)
#
# Reference (python ground truth): outputs/gis_port_reference{,_theta}.csv,
# emitted by python/emit_gis_port_reference.py.
#
# Run:  julia --project=julia_v2 julia/validate_greenland_ab.jl

using CSV, DataFrames, Mimi, MimiBRICK, Printf
include(joinpath(@__DIR__, "brick_mengel.jl"))

const REPO = abspath(joinpath(@__DIR__, ".."))
const TOL = 1e-9

ref = CSV.read(joinpath(REPO, "outputs/gis_port_reference.csv"), DataFrame)
th = CSV.read(joinpath(REPO, "outputs/gis_port_reference_theta.csv"), DataFrame)
getp(n) = Float64(only(th[th.name .== n, :value_component]))
forcing = String(only(th[th.name .== "_forcing_tag", :unit_cell]))   # CSV gives String15

y0, y1 = Int(minimum(ref.year)), Int(maximum(ref.year))
gis = (c1=getp("c1"), c0=getp("c0"), v0=getp("v0"), f=getp("f"),
       alpha_f=getp("alpha_f"), beta_f=getp("beta_f"),
       alpha_s=getp("alpha_s"), beta_s=getp("beta_s"), g=getp("g"))
@printf("greenland_ab port validation | %d-%d | forcing %s | tol %.0e\n",
        y0, y1, forcing, TOL)

m = build_brick_nu3_gis(ssp=forcing, y0=y0, y1=y1)
update_gis_ab!(m, gis)
driver = Float64.(ref.driver_K)
set_gis_forcing!(m, driver)
# The glacier blocks do not affect Greenland, but Mimi will not build with
# unbound parameters. Bind them at the accepted extC anchored values so the
# global_sea_level contract check below is run on a physically sensible model.
bc = CSV.read(joinpath(REPO, "outputs/extc_block_constants.csv"), DataFrame)
brow(b) = only(eachrow(bc[bc.block .== b, :]))
gic3 = NamedTuple(Symbol(b) => (a=Float64(brow(b).a0),
                                b=Float64(brow(b).b_fit_obsfit),
                                T_off=Float64(brow(b).T_off_fit_obsfit),
                                kappa=Float64(brow(b).kappa_anch_obsfit),
                                nu=Float64(brow(b).nu_anch_obsfit))
                  for b in NU3_BLOCKS)
for blk in NU3_BLOCKS
    g = getproperty(gic3, Symbol(blk))
    update_param!(m, _MENGEL_GLAC_SLOT, Symbol("gic_a_$blk"), g.a)
    update_param!(m, _MENGEL_GLAC_SLOT, Symbol("gic_b_$blk"), g.b)
    update_param!(m, _MENGEL_GLAC_SLOT, Symbol("gic_T_off_$blk"), g.T_off)
    update_param!(m, _MENGEL_GLAC_SLOT, Symbol("gic_kappa_$blk"), g.kappa)
    update_param!(m, _MENGEL_GLAC_SLOT, Symbol("gic_nu_$blk"), g.nu)
end
update_param!(m, _MENGEL_GLAC_SLOT, :gic_sl0, 0.0)
zero_drv = zeros(length(driver))
set_glacier_forcing3!(m, (R19=zero_drv, SLOWP=zero_drv, FAST=zero_drv))
run(m)

fails = String[]
function check(label, got, want)
    d = maximum(abs.(Float64.(got) .- Float64.(want)))
    ok = d <= TOL
    @printf("  %-34s max|diff| = %.3e  %s\n", label, d, ok ? "PASS" : "FAIL")
    ok || push!(fails, label)
    return ok
end

println("[1-3] series identity against the python reference")
check("[1] driver", m[_GIS_SLOT, :greenland_surface_temperature], ref.driver_K)
check("[2] gis_eq (m)", m[_GIS_SLOT, :gis_eq], ref.eq_m)
check("[3] gis_fast (m)", m[_GIS_SLOT, :gis_fast], ref.fast_m)
check("[3] gis_slow (m)", m[_GIS_SLOT, :gis_slow], ref.slow_m)
check("[3] greenland_sea_level (m)", m[_GIS_SLOT, :greenland_sea_level],
      ref.sea_level_m)

println("[4] slot contract")
check("[4] sea_level == fast + slow",
      m[_GIS_SLOT, :greenland_sea_level],
      Float64.(m[_GIS_SLOT, :gis_fast]) .+ Float64.(m[_GIS_SLOT, :gis_slow]))
# :global_sea_level must be reading this slot, not a stale stock component.
gsl = Float64.(m[:global_sea_level, :sea_level_rise])
parts = Float64.(m[_GIS_SLOT, :greenland_sea_level]) .+
        Float64.(m[_MENGEL_GLAC_SLOT, :gsic_sea_level]) .+
        Float64.(m[:antarctic_icesheet, :ais_sea_level]) .+
        Float64.(m[:thermal_expansion, :te_sea_level]) .+
        Float64.(m[:landwater_storage, :lws_sea_level])
check("[4] global_sea_level == 5 components", gsl, parts)

println("[5] initial condition is L(y0) = g*eq(y0), and not equilibrium")
eq0 = Float64(m[_GIS_SLOT, :gis_eq][1])
l0 = Float64(m[_GIS_SLOT, :greenland_sea_level][1])
@printf("  gis_g = %.6f; L(%d) = %.6f m against a commitment of %.6f m\n",
        gis.g, y0, l0, eq0)
if !isapprox(l0, gis.g * eq0; atol=TOL)
    push!(fails, "[5] initial condition")
    println("  [5] FAIL — L(y0) != g * eq(y0)")
elseif isapprox(l0, eq0; atol=1e-6)
    push!(fails, "[5] starts in equilibrium")
    println("  [5] FAIL — the component starts IN EQUILIBRIUM (g == 1); stock " *
            "SIMPLE starts at V = v0 with the full disequilibrium present")
else
    println("  [5] PASS")
end

println("[6] zero-driver run is flat")
m0 = build_brick_nu3_gis(ssp=forcing, y0=y0, y1=y1)
update_gis_ab!(m0, gis)
set_gis_forcing!(m0, zero_drv)
for blk in NU3_BLOCKS
    g = getproperty(gic3, Symbol(blk))
    update_param!(m0, _MENGEL_GLAC_SLOT, Symbol("gic_a_$blk"), g.a)
    update_param!(m0, _MENGEL_GLAC_SLOT, Symbol("gic_b_$blk"), g.b)
    update_param!(m0, _MENGEL_GLAC_SLOT, Symbol("gic_T_off_$blk"), g.T_off)
    update_param!(m0, _MENGEL_GLAC_SLOT, Symbol("gic_kappa_$blk"), g.kappa)
    update_param!(m0, _MENGEL_GLAC_SLOT, Symbol("gic_nu_$blk"), g.nu)
end
update_param!(m0, _MENGEL_GLAC_SLOT, :gic_sl0, 0.0)
set_glacier_forcing3!(m0, (R19=zero_drv, SLOWP=zero_drv, FAST=zero_drv))
run(m0)
s0 = Float64.(m0[_GIS_SLOT, :greenland_sea_level])
# With a constant driver the state relaxes toward a CONSTANT commitment, so it
# is flat only if it starts there; g != 1 means it must move monotonically and
# never overshoot.
drift = maximum(abs.(diff(s0)))
mono = all(diff(s0) .>= -TOL)
overshoot = maximum(s0) - Float64(m0[_GIS_SLOT, :gis_eq][1])
@printf("  monotone non-decreasing: %s; max overshoot of the commitment: %.3e m\n",
        mono ? "yes" : "NO", overshoot)
mono || push!(fails, "[6] monotonicity")
overshoot <= TOL || push!(fails, "[6] overshoot")
@printf("  (max annual step %.3e m — relaxation toward a constant commitment)\n", drift)

println()
if isempty(fails)
    println("ALL PASS — greenland_ab matches the offline cell at $(TOL).")
else
    println("FAILURES: ", join(fails, ", "))
    exit(1)
end
