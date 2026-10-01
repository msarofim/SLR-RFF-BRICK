## ============================================================================
## test_ladrillo_reverts_to_brick20.jl — does the ASSEMBLED Ladrillo model, with its new components
## swapped back out, reproduce BRICK 2.0 bit for bit?
##
## Ladrillo is MimiBRICK v2.0.0 with the glacier and Greenland slots replaced (Mimi replace!) and its own
## setup (ladrillo_setup: forcing, regional drivers, medoid initialisation, land water). The other
## component tests check each new component against an independent implementation; none checked the
## ASSEMBLY. Here the Ladrillo build is taken as-is, the two slots are put back to MimiBRICK's stock
## components, a BRICK 2.0 posterior draw is applied with the BRICK 2.0 arm's own updater, and every
## component series plus the global sum must EQUAL (==, no tolerance) a stock MimiBRICK.get_model run
## built the way the paper's BRICK 2.0 comparison arm builds it (scope_slr_fairunc_oldbrick.jl).
##
## What this DOES cover: model construction through ladrillo_setup, the slot replacements being
## reversible, the shared Antarctic / Antarctic-ocean / thermal-expansion / land-water / global-sum
## code and its wiring (including DAIS's sea-level feedback), the forcing path, and that no Ladrillo
## setup value leaks past a full BRICK 2.0 parameter draw.
## What it does NOT cover: ladrillo_apply_draw!'s mapping of Ladrillo's own parameters (the sampled
## Antarctic amplification, the precipitation reparameterisation, propagated lambda/T_crit), which has
## no BRICK 2.0 counterpart to equal; those are covered by test_ladrillo_projection.jl.
##
##   R  IDENTITY  — ais, glaciers, Greenland, thermal expansion, land water and global sea level:
##                  raw metre series ==, for NDRAW BRICK 2.0 draws x two scenarios, 1850-2300.
##   MUTATION     — each must make R FAIL: (a) one-ulp change in one draw parameter on the Ladrillo
##                  side; (b) the land-water frame fix on one side only (reaches only DAIS's input,
##                  through the feedback); (c) the glacier slot left as Ladrillo's glaciers_nu3.
##
## Run:  julia --project=julia_v2 julia/test_ladrillo_reverts_to_brick20.jl
## ============================================================================
include(joinpath(@__DIR__, "ladrillo_projection.jl"))
using Printf, Random

const Y0, Y1  = 1850, 2300
const SSPS    = ("ssp245", "ssp585")
const NDRAW   = 20
const SEED    = 2026          # get_model's RNG (the BRICK 2.0 arm's seed); set_lws! overwrites what it draws
const POST20  = CSV.read(joinpath(LADRILLO_REPO, "data/MimiBRICK/parameters_subsample_brick.csv"), DataFrame)
const ROWS    = collect(1:(nrow(POST20) ÷ NDRAW):nrow(POST20))[1:NDRAW]
const SERIES  = [("ais",       :antarctic_icesheet,     :ais_sea_level),
                 ("glaciers",  :glaciers_small_icecaps, :gsic_sea_level),
                 ("Greenland", :greenland_icesheet,     :greenland_sea_level),
                 ("thermal",   :thermal_expansion,      :te_sea_level),
                 ("landwater", :landwater_storage,      :lws_sea_level),
                 ("total",     :global_sea_level,       :sea_level_rise)]

const FAILS = String[]
check(name, ok, detail="") = (@printf("  %-70s %s  %s\n", name, ok ? "PASS" : "FAIL", detail); ok || push!(FAILS, name))

forcing(ssp) = ([_yearmap(joinpath(LADRILLO_OBS, "fair_mean_gmst_$(ssp).csv"), "gmst_C")[y]    for y in Y0:Y1],
                [_yearmap(joinpath(LADRILLO_OBS, "fair_mean_ohc_$(ssp).csv"),  "ohc_1e22J")[y] for y in Y0:Y1])

"""The BRICK 2.0 comparison arm's build (scope_slr_fairunc_oldbrick.jl:183-192)."""
function stock_brick20(ssp)
    Random.seed!(SEED)
    M = MimiBRICK.get_model(ssprcp_scenario="ssp245", start_year=Y0, end_year=Y1)
    set_lws!(M, LWS_MODE)
    set_forcing!(M, forcing(ssp)...)
    return M
end

"""Ladrillo's own build, with the glacier slot put back to MimiBRICK's component (`revert_glaciers`)
and Greenland built as `:stock` (ladrillo_setup's own option)."""
function reverted_ladrillo(ssp; revert_glaciers::Bool=true, lws_anchor::Symbol=LWS_OBS_ANCHOR)
    g, o = forcing(ssp)
    bf = ladrillo_setup(ssp=ssp, y0=Y0, y1=Y1, gis_variant=:stock, ais_ramp=false, lws=LWS_MODE, gmst=g, ohc=o)
    if revert_glaciers
        replace!(bf.m, :glaciers_small_icecaps => MimiBRICK.glaciers_small_icecaps)
        # replace! drops the shared-temperature connection (glaciers_nu3 has no such parameter) and leaves
        # the stock component's unshared parameters unset: restore exactly what get_model does
        # (MimiBRICK.jl:109, :147); the four sampled ones come from the draw below.
        connect_param!(bf.m, :glaciers_small_icecaps, :global_surface_temperature, :model_global_surface_temperature)
        update_param!(bf.m, :glaciers_small_icecaps, :gsic_teq, -0.15)
    end
    set_lws!(bf.m, LWS_MODE; lws_anchor=lws_anchor)
    return bf.m
end

"""Max |difference| (m) over every series and year, and whether every series is ==."""
function compare(A, B)
    worst, same = 0.0, true
    for (_, c, v) in SERIES
        a, b = Float64.(A[c, v]), Float64.(B[c, v])
        same &= (a == b)
        worst = max(worst, maximum(abs.(a .- b)))
    end
    return same, worst
end

function run_pair!(A, B, row; bump::Union{Nothing,Symbol}=nothing)
    update_brick_params!(A, row; precip_log=true); run(A)
    update_brick_params!(B, row; precip_log=true)
    bump === nothing || update_param!(B, :thermal_expansion, bump, nextfloat(Float64(row.thermal_alpha)))
    run(B)
end

println("[R] reverted Ladrillo == stock BRICK 2.0 ($(NDRAW) draws of parameters_subsample_brick.csv, $(Y0)-$(Y1))")
for ssp in SSPS
    A, B = stock_brick20(ssp), reverted_ladrillo(ssp)
    nsame, worst, per = 0, 0.0, Dict(s => true for (s, _, _) in SERIES)
    for k in ROWS
        run_pair!(A, B, POST20[k, :])
        s, w = compare(A, B); nsame += s; worst = max(worst, w)
        for (nm, c, v) in SERIES; per[nm] &= (A[c, v] == B[c, v]); end
    end
    for (nm, _, _) in SERIES
        check("$ssp: $nm identical in every draw", per[nm])
    end
    check("$ssp: all series identical, $nsame/$(length(ROWS)) draws", nsame == length(ROWS), @sprintf("(max |diff| %.1e m)", worst))
    tot = 100 .* Float64.(A[:global_sea_level, :sea_level_rise])
    check("$ssp: the run is live (total moves > 10 cm, 1850-2300)", tot[end] - tot[1] > 10, @sprintf("(%.1f cm)", tot[end] - tot[1]))
end

println("[MUTATION] each perturbation must break R")
let ssp = "ssp245", row = POST20[ROWS[1], :]
    A, B = stock_brick20(ssp), reverted_ladrillo(ssp)
    run_pair!(A, B, row; bump=:te_α)
    s, w = compare(A, B)
    check("(a) one-ulp change in te_α on the Ladrillo side is detected", !s, @sprintf("(max |diff| %.1e m)", w))

    B2 = reverted_ladrillo(ssp; lws_anchor=:zero_at_first_year)
    run_pair!(A, B2, row)
    ais_moved = A[:antarctic_icesheet, :ais_sea_level] != B2[:antarctic_icesheet, :ais_sea_level]
    s2, w2 = compare(A, B2)
    check("(b) land-water frame fix on one side is detected", !s2, @sprintf("(max |diff| %.1e m)", w2))
    check("(b) ... and it reaches DAIS through the sea-level feedback", ais_moved)

    B3 = reverted_ladrillo(ssp; revert_glaciers=false)
    ok3 = try
        update_brick_params!(B3, row; precip_log=true, skip_glaciers=true); run(B3)
        update_brick_params!(A, row; precip_log=true); run(A)
        !compare(A, B3)[1]
    catch e
        true      # Ladrillo's glacier slot cannot even take BRICK 2.0's glacier parameters
    end
    check("(c) leaving Ladrillo's glacier component in place is detected", ok3)
end

println()
isempty(FAILS) || error("test_ladrillo_reverts_to_brick20: $(length(FAILS)) FAIL(s): $(join(FAILS, "; "))")
println("ALL REVERTED-LADRILLO == BRICK 2.0 TESTS PASS")
