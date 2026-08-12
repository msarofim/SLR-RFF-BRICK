# validate_gis_projection_ab.jl — the PROJECTION kernel can consume a Ladrillo 1.0
# posterior, and it builds Greenland the same way the CALIBRATOR does.
#
# Why this exists. The Greenland A+B module is validated three times over before
# this: as a component (validate_greenland_ab.jl), inside the calibrator
# (calibrate_mcmc_ext.jl --gis-check), and against the offline cell that selected
# it. None of that covers the PROJECTION kernel, which is a separate code path
# with its own model build, its own driver construction and its own parameter
# map. Before this file existed, ladrillo_projection.jl was hard-wired to stock
# SIMPLE: it would load a Ladrillo 1.0 posterior without complaint (CSV.jl's
# `select=` silently returns only the columns it finds) and then fail at apply
# time -- i.e. the posterior the production run is about to produce could not be
# projected at all.
#
#   [1] CONSTANT PARITY. The four Greenland constants that must agree between
#       the calibrator and the projector (zone, amp, v0, g) are compared by
#       reading them out of calibrate_mcmc_ext.jl's source. If they ever drift,
#       the projections are run on a different model than the one calibrated,
#       and nothing else in the suite would notice.
#   [2] VARIANT DETECTION. A stock posterior reads as :stock, an A+B posterior as
#       :ab, and a posterior missing a required column FAILS rather than loading
#       a partial column set.
#   [3] END-TO-END. A draw at the offline g=0 parameter vector reproduces the
#       offline cell's 2100 GIS in all three scenarios.
#
# Run:  julia --project=julia_v2 julia/validate_gis_projection_ab.jl

using CSV, DataFrames, Printf
include(joinpath(@__DIR__, "ladrillo_projection.jl"))

const TOL_CM = 0.10          # kernel-vs-offline 2100 GIS; the two build GMST differently
# python/gis_offline_cell.py cell A+B at g = 0 (outputs/gis_g_betaf_variants.csv)
const OFFLINE_THETA = Dict(
    "gis_c1" => 0.032766, "gis_c0" => 0.0404293, "gis_f" => 0.782569,
    "gis_alpha_f" => 0.00284865, "gis_beta_f" => 0.00736838,
    "gis_alpha_s" => 0.00707271, "gis_beta_s" => 1e-6)
const OFFLINE_2100 = ("ssp126" => 6.928, "ssp245" => 9.834, "ssp585" => 17.367)

fails = String[]
chk(label, ok, detail="") = begin
    @printf("  %-52s %s%s\n", label, ok ? "PASS" : "FAIL", isempty(detail) ? "" : "  ($detail)")
    ok || push!(fails, label)
    ok
end

println("[1] Greenland constants agree between the calibrator and the projector")
src = read(joinpath(@__DIR__, "calibrate_mcmc_ext.jl"), String)
grab(pat) = (m = match(pat, src); m === nothing ? nothing : m.captures[1])
for (label, got, pat, parse_as) in (
        ("GIS_ZONE",  LADRILLO_GIS_ZONE,  r"const GIS_ZONE\s*=\s*\"([a-z]+)\"", :str),
        ("GIS_AMP",   LADRILLO_GIS_AMP,   r"const GIS_AMP\s*=\s*([0-9.]+)",     :num),
        ("GIS_V0_M",  LADRILLO_GIS_V0_M,  r"const GIS_V0_M\s*=\s*([0-9.]+)",    :num),
        ("GIS_G",     LADRILLO_GIS_G,     r"const GIS_G\s*=\s*([0-9.]+)",       :num))
    raw = grab(pat)
    want = raw === nothing ? nothing : (parse_as === :str ? raw : parse(Float64, raw))
    chk("$label matches calibrate_mcmc_ext.jl", want !== nothing && want == got,
        "projector $got vs calibrator $(something(want, "NOT FOUND"))")
end

println("\n[2] posterior variant detection")
stock_hdr = String.(propertynames(CSV.read(LADRILLO_POSTERIOR_CSV, DataFrame; limit=0)))
chk("the extC posterior reads as :stock", ladrillo_gis_variant(stock_hdr) === :stock)
ab_hdr = vcat([c for c in stock_hdr if !(c in LADRILLO_GIS_STOCK_COLS)], LADRILLO_GIS_AB_COLS)
chk("an A+B header reads as :ab", ladrillo_gis_variant(ab_hdr) === :ab)
partial = [c for c in ab_hdr if c != "gis_beta_s"]
chk("a header missing one gis_* column is REJECTED",
    (try; ladrillo_gis_variant(partial); false; catch; true; end))

println("\n[3] end-to-end: an A+B draw reproduces the offline cell at 2100")
# Build a one-row A+B posterior from the extC posterior's non-Greenland columns.
src_post = ladrillo_posterior(cols=:all, nthin=1)
row = DataFrame(src_post[1:1, :])
select!(row, Not(intersect(names(row), LADRILLO_GIS_STOCK_COLS)))
for (k, v) in OFFLINE_THETA; row[!, k] .= v; end
for (ssp, want) in OFFLINE_2100
    bf = ladrillo_setup(ssp=ssp, y0=1850, y1=2300, gis_ab=true)
    ladrillo_apply_draw!(bf, row[1, :])
    run(bf.m)
    got = ladrillo_series(bf, :gis)[findfirst(==(2100), bf.years)]
    chk("$ssp 2100 GIS within $TOL_CM cm of the offline cell", abs(got - want) <= TOL_CM,
        @sprintf("kernel %.3f vs offline %.3f cm", got, want))
end

println()
if isempty(fails)
    println("ALL PASS — the projection kernel consumes Ladrillo 1.0 and matches the calibrator.")
else
    println("FAILURES: ", join(fails, ", "))
    exit(1)
end
