## [INERT] gate: magdep with fastdyn n=0 AND ramp slope 0 must be BIT-IDENTICAL to the stock AIS slot.
using CSV, DataFrames, Mimi, MimiBRICK, Statistics, Printf
include(joinpath(@__DIR__, "..", "julia", "ladrillo_projection.jl"))
include(joinpath(LADRILLO_REPO, "julia/antarctic_icesheet_magdep_component.jl"))
post = ladrillo_posterior(path=joinpath(LADRILLO_REPO,"data/MimiBRICK/parameters_subsample_brick_mengel_L29.csv"), cols=:all, nthin=25)
ladrillo_attach_propagated!(post)
V = ladrillo_posterior_variant(joinpath(LADRILLO_REPO,"data/MimiBRICK/parameters_subsample_brick_mengel_L29.csv"))
a = ladrillo_setup(ssp="ssp245", y0=1850, y1=2300, lws=:central, gis_variant=V)
b = ladrillo_setup(ssp="ssp245", y0=1850, y1=2300, lws=:central, gis_variant=V)
replace!(b.m, :antarctic_icesheet => antarctic_icesheet_magdep)
update_param!(b.m, :antarctic_icesheet, :ais_fastdyn_exponent, 0.0)
update_param!(b.m, :antarctic_icesheet, :ais_fastdyn_ref_excess, 1.0)
update_param!(b.m, :antarctic_icesheet, :ais_fastdyn_gmax, Inf)
update_param!(b.m, :antarctic_icesheet, :ais_ramp_slope, 0.0)
update_param!(b.m, :antarctic_icesheet, :ais_ramp_threshold, 0.0)
bad = 0; tipped = 0
for r in eachrow(post)
    global bad, tipped
    ladrillo_run_draw!(a, r); ladrillo_run_draw!(b, r)
    sa = ladrillo_series(a, :ais); sb = ladrillo_series(b, :ais)
    ta = ladrillo_series(a, :total); tb = ladrillo_series(b, :total)
    maximum(abs.(sa .- sb)) == 0.0 || (bad += 1)
    maximum(abs.(ta .- tb)) == 0.0 || (bad += 1)
    sum(filter(!isnan, [ismissing(e) ? NaN : Float64(e) for e in b.m[:antarctic_icesheet,:disintegration_rate]])) < 0 && (tipped += 1)
end
## MUTATION (power): the same comparison with a nonzero ramp slope MUST differ.
update_param!(b.m, :antarctic_icesheet, :ais_ramp_slope, 6e-4)
update_param!(b.m, :antarctic_icesheet, :ais_ramp_threshold, LADRILLO_AIS_TANT0 + 1.09*0.75)
mdiff = 0.0
for r in eachrow(post)
    global mdiff
    ladrillo_run_draw!(a, r); ladrillo_run_draw!(b, r)
    mdiff = max(mdiff, maximum(abs.(ladrillo_series(a,:ais) .- ladrillo_series(b,:ais))))
end
@printf("[INERT] %d draws, %d tipped (paleo binary fires) | identity failures: %d | MUTATION max |diff| with slope 6e-4: %.3f cm\n", nrow(post), tipped, bad, mdiff)
println(bad == 0 && mdiff > 1.0 ? "[GATE] PASS (inert at slope 0, and the mutation has power)" : "[GATE] FAIL")
exit(bad == 0 && mdiff > 1.0 ? 0 : 1)
