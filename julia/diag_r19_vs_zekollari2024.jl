## ============================================================================
## diag_r19_vs_zekollari2024.jl — Ladrillo's R19 against an INDEPENDENT
## process-model projection constraint.
##
## SOURCE (Marcus, 2026-08-14; verified fetched, now PUBLISHED not a preprint)
##   Zekollari, Huss, Schuster, Maussion, Rounce, Aguayo, Champollion, Compagno,
##   Hugonnet, Marzeion, Mojtabavi, Farinotti (2024), "21st century global
##   glacier evolution under CMIP6 scenarios and the role of glacier-specific
##   observations", The Cryosphere 18, 5045-5066, doi 10.5194/tc-18-5045-2024.
##   Three glacier models (GloGEM, OGGM v1.6.1, PyGEM), 12 CMIP6 GCMs, four SSPs,
##   calibrated to Hugonnet et al. 2021 glacier-specific geodetic mass balance.
##   Archives: GloGEM zenodo.10908278, OGGM zenodo.8286065, PyGEM NSIDC
##   10.5067/P8BN9VO9N5C7.
##
## WHY IT IS USEFUL HERE. It is TRANSIENT 2015-2100 loss per RGI region, which is
##   * independent of the sea-level total (the stream D1 drops),
##   * a DIFFERENT quantity from the GlacierMIP3 rungs already in the likelihood
##     (those are COMMITTED loss at a warming level; this is realised loss by
##     2100, so it constrains the response timescale too, not just S_eq), and
##   * on exactly the horizon the deliverable reports.
##
## REGION 19 NUMBERS, % of 2015 mass lost by 2100 (paper text):
##     GloGEM  SSP1-2.6 14 +/- 13    SSP5-8.5 33 +/- 24
##     OGGM    SSP1-2.6 21 +/- 18    SSP5-8.5 52 +/- 32
##
## CAVEATS, ALL FROM THE PAPER, ALL BINDING:
##   * Region 19 is where the two models disagree MOST -- projected volumes differ
##     significantly under every scenario (t test, 1%) -- because they treat
##     FRONTAL ABLATION differently (GloGEM simplified; the OGGM setup does not
##     explicitly represent it). The authors say it is "difficult to judge" which
##     is more trustworthy. So any term must span the inter-model spread, NOT pick
##     a model.
##   * This is a MODEL constraint, not an observation. It adds process
##     information, the same category as the GlacierMIP3 rungs.
##   * Our SSP runs use FaIR MEAN GMST, so our p05-p95 is posterior-parameter
##     spread only, while theirs includes 12-GCM spread. Compare MEDIANS, not
##     bands.
##   * The denominator is "% of 2015 mass"; ours uses the Farinotti a0 for region
##     19 (0.069 m SLE) net of melt to 2015. Consistency of the two inventories is
##     NOT verified here.
##
## The D1 arm freezes all five R19 parameters at their D1 medians, so it has no
## spread by construction -- read its median only.
##
##   julia --project=julia_v2 julia/diag_r19_vs_zekollari2024.jl
## ============================================================================

using CSV, DataFrames, Mimi, Printf, Statistics
include(joinpath(@__DIR__, "ladrillo_projection.jl"))
const BC = CSV.read(joinpath(LADRILLO_REPO,"outputs/extc_block_constants.csv"), DataFrame)
a0(b) = Float64(BC[findfirst(==(b), BC.block), :a0])
post = ladrillo_posterior(nthin=300)
D1 = Dict("gic_T_off_R19"=>-0.323618,"gic_a_R19"=>0.068191,"gic_b_R19"=>1.062368,
          "gic_log10_kappa_R19"=>-2.780131,"gic_amp_R19"=>0.723435)
println("R19 transient loss 2015-2100, % of 2015 mass  (Zekollari et al. 2024, TC 18:5045)")
@printf("  %-6s %-10s %10s %10s %10s\n","arm","ssp","median","p05","p95")
for (arm, over) in ["L10"=>Dict{String,Float64}(), "D1"=>D1]
    p = copy(post); for (k,v) in over; p[!,k] .= v; end
    for ssp in ("ssp126","ssp585")
        bf = ladrillo_setup(ssp=ssp, y0=1850, y1=2100, gis_variant = ladrillo_posterior_variant())
        yi(y)=findfirst(==(y), bf.years)
        pct = Float64[]
        for r in eachrow(p)
            ladrillo_run_draw!(bf, r)
            s = Float64.(bf.m[:glaciers_small_icecaps, :gsic_r19])       # m SLE cumulative loss
            aR = "gic_a_R19" in keys(over) ? over["gic_a_R19"] : Float64(r["gic_a_R19"])
            mass2015 = aR - s[yi(2015)]
            push!(pct, 100*(s[yi(2100)] - s[yi(2015)]) / mass2015)
        end
        @printf("  %-6s %-10s %10.1f %10.1f %10.1f\n", arm, ssp, median(pct),
                quantile(pct,0.05), quantile(pct,0.95))
    end
end
println("\n  Zekollari 2024 region 19:  GloGEM ssp126 14+/-13, ssp585 33+/-24")
println("                             OGGM   ssp126 21+/-18, ssp585 52+/-32")
