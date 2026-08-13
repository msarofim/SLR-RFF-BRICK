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
#   [4] gis_amp IS LIVE. Two draws differing ONLY in gis_amp must give different
#       2100 GIS, and in the right direction. "Applied per draw" is precisely the
#       kind of claim that can be silently inert -- if the driver were built once
#       at a fixed amp, every check above would still pass.
#   [5] THE amp(GMST) LAW (2026-08-13). The projector's amplification is now a
#       function of warming level while the calibrator's is a scalar, so [1]'s
#       constant comparison is no longer the whole drift guard: [5] asserts the
#       function MEETS the calibrator at the anchor, S(dT_eff) = 1, and that the
#       shape has the measured form (declining over 0.75-2.75 K, held flat
#       outside). It also gates the driver itself -- anchor-preserving, inert
#       over the observed years, and reducing to the constant-amp splice exactly
#       when switched off.
#
# Run:  julia --project=julia_v2 julia/validate_gis_projection_ab.jl

using CSV, DataFrames, Printf
include(joinpath(@__DIR__, "ladrillo_projection.jl"))

const TOL_CM = 0.10          # kernel-vs-offline 2100 GIS; the two build GMST differently
# python/gis_offline_cell.py cell A+B at g = 0 (outputs/gis_g_betaf_variants.csv)
const OFFLINE_THETA = Dict(
    "gis_c1" => 0.032766, "gis_c0" => 0.0404293, "gis_f" => 0.782569,
    "gis_alpha_f" => 0.00284865, "gis_beta_f" => 0.00736838,
    "gis_alpha_s" => 0.00707271, "gis_beta_s" => 1e-6, "gis_amp" => 1.92)
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
stock_hdr = String.(propertynames(CSV.read(LADRILLO_POSTERIOR_EXTC_CSV, DataFrame; limit=0)))
chk("the extC posterior reads as :stock", ladrillo_gis_variant(stock_hdr) === :stock)
ab_hdr = vcat([c for c in stock_hdr if !(c in LADRILLO_GIS_STOCK_COLS)], LADRILLO_GIS_AB_COLS)
chk("an A+B header reads as :ab", ladrillo_gis_variant(ab_hdr) === :ab)
chk("the CANONICAL posterior reads as :ab", ladrillo_posterior_variant() === :ab,
    basename(LADRILLO_POSTERIOR_CSV))
partial = [c for c in ab_hdr if c != "gis_beta_s"]
chk("a header missing one gis_* column is REJECTED",
    (try; ladrillo_gis_variant(partial); false; catch; true; end))

println("\n[3] end-to-end: an A+B draw reproduces the offline cell at 2100")
# The offline cell is CONSTANT-amp, so this parity is with the amp law OFF. The
# law's own gates are [5]; the constant-parity reading of [1] moved there too.
# Build a one-row A+B posterior from the extC posterior's non-Greenland columns.
src_post = ladrillo_posterior(path=LADRILLO_POSTERIOR_EXTC_CSV, cols=:all, nthin=1)
row = DataFrame(src_post[1:1, :])
select!(row, Not(intersect(names(row), LADRILLO_GIS_STOCK_COLS)))
for (k, v) in OFFLINE_THETA; row[!, k] .= v; end
for (ssp, want) in OFFLINE_2100
    bf = ladrillo_setup(ssp=ssp, y0=1850, y1=2300, gis_ab=true, gis_shape=false)
    ladrillo_apply_draw!(bf, row[1, :])
    run(bf.m)
    got = ladrillo_series(bf, :gis)[findfirst(==(2100), bf.years)]
    chk("$ssp 2100 GIS within $TOL_CM cm of the offline cell", abs(got - want) <= TOL_CM,
        @sprintf("kernel %.3f vs offline %.3f cm", got, want))
end

println("\n[4] gis_amp is live, not baked in at a fixed value")
let bf = ladrillo_setup(ssp="ssp585", y0=1850, y1=2300, gis_ab=true),
    iy = findfirst(==(2100), bf.years), got = Float64[]
    for amp in (1.51, 1.92, 2.28)
        r = DataFrame(row[1:1, :]); r[!, "gis_amp"] .= amp
        ladrillo_apply_draw!(bf, r[1, :]); run(bf.m)
        push!(got, ladrillo_series(bf, :gis)[iy])
    end
    @printf("  ssp585 2100 GIS at amp 1.51 / 1.92 / 2.28: %.2f / %.2f / %.2f cm\n",
            got[1], got[2], got[3])
    chk("changing gis_amp moves the projection", maximum(got) - minimum(got) > 1.0,
        @sprintf("range %.2f cm", maximum(got) - minimum(got)))
    chk("and it moves MONOTONICALLY upward in amp", issorted(got))
end

println("\n[5] the amp(GMST) law")
# [1] used to assert that the projector's amp CONSTANT equals the calibrator's,
# which is what stopped the two files drifting onto different Greenlands. Now the
# projector's amplification is a FUNCTION, so the constant comparison is no
# longer the whole contract: what must hold is that the function MEETS the
# calibrator at the point the calibration was made, S(dT_eff) = 1.
let dta = LADRILLO_GIS_SHAPE_ANCHOR_DT, s_anchor = ladrillo_gis_shape(dta)
    chk("S(anchor dT_eff) == 1 exactly", abs(s_anchor - 1.0) < 1e-12,
        @sprintf("dT_eff %.4f K, S %.15f", dta, s_anchor))
    chk("amp law meets the calibrator at the anchor",
        LADRILLO_GIS_AMP * s_anchor == LADRILLO_GIS_AMP,
        @sprintf("amp(dT_eff) %.6f vs calibrator GIS_AMP %.6f",
                 LADRILLO_GIS_AMP * s_anchor, LADRILLO_GIS_AMP))
    # the measured shape: declining over the fitted support, held flat outside it
    inner = [ladrillo_gis_shape(d) for d in 0.75:0.25:2.75]
    chk("S declines monotonically over the fitted support 0.75-2.75 K",
        issorted(inner, rev=true),
        @sprintf("S(0.75) %.3f -> S(2.75) %.3f", inner[1], inner[end]))
    chk("S is held FLAT above the fitted support",
        ladrillo_gis_shape(3.5) == ladrillo_gis_shape(2.75) ==
            ladrillo_gis_shape(8.0) == ladrillo_gis_shape(99.0))
    chk("S is held FLAT below the fitted support",
        ladrillo_gis_shape(0.5) == ladrillo_gis_shape(0.75) == ladrillo_gis_shape(-1.0))
end
# Structural gates on the driver itself: the law must not move the observed
# splice anchor (it is anchor-preserving by construction), it must be inert
# before the seam, and switching it off must reproduce the constant-amp splice.
let bfon  = ladrillo_setup(ssp="ssp585", y0=1850, y1=2300, gis_ab=true, gis_shape=true),
    bfoff = ladrillo_setup(ssp="ssp585", y0=1850, y1=2300, gis_ab=true, gis_shape=false),
    amp = LADRILLO_GIS_AMP
    don, doff = ladrillo_gis_driver(bfon, amp), ladrillo_gis_driver(bfoff, amp)
    ianch = [findfirst(==(y), bfon.years) for y in 2014:2024]
    fut = .!bfoff.gis_mask
    const_splice = amp .* bfoff.gmst_rb .+ (bfoff.gis_anchor - amp * bfoff.gmst_anchor)
    chk("law OFF reproduces the constant-amp splice", doff[fut] == const_splice[fut])
    chk("the 11-yr splice anchor is preserved with the law ON",
        abs(mean(don[ianch]) - mean(doff[ianch])) < 1e-12,
        @sprintf("%.12f vs %.12f K", mean(don[ianch]), mean(doff[ianch])))
    chk("the law is inert over the observed years", don[bfon.gis_mask] == doff[bfoff.gis_mask])
    iy2100 = findfirst(==(2100), bfon.years)
    chk("the law LOWERS the ssp585 driver at 2100",
        don[iy2100] < doff[iy2100],
        @sprintf("%.3f vs %.3f K (S = %.3f)", don[iy2100], doff[iy2100],
                 bfon.gis_shape[iy2100]))
    gon  = (ladrillo_apply_draw!(bfon,  row[1, :]); run(bfon.m);
            ladrillo_series(bfon,  :gis)[iy2100])
    goff = (ladrillo_apply_draw!(bfoff, row[1, :]); run(bfoff.m);
            ladrillo_series(bfoff, :gis)[iy2100])
    @printf("  ssp585 2100 GIS: law ON %.2f cm vs OFF %.2f cm (%.2f cm lower)\n",
            gon, goff, goff - gon)
    chk("and it LOWERS the ssp585 2100 GIS projection", gon < goff)
end

println()
if isempty(fails)
    println("ALL PASS — the projection kernel consumes Ladrillo 1.0 and matches the calibrator.")
else
    println("FAILURES: ", join(fails, ", "))
    exit(1)
end
