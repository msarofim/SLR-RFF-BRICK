## ============================================================================
## test_sneasy_posterior.jl
##
## Diagnostic: run BRICK with full posterior + SNEASY internal inputs
## (Tony's setup). Compare TE-at-2018 and the AIS trajectory to:
##   - default-mode BRICK (no posterior; verified at +3.10 cm TE at 2018)
##   - our obs-driven BRICK (posterior + external obs OHC; +0.67 cm TE)
##   - Frederikse 2020 Steric (+2.31 cm) and AIS (+0.69 cm)
##
## First-principles prediction with posterior te_α ≈ 0.057 and SNEASY ΔOHC
## (1900-2018) ≈ 75 ZJ: ΔTE ≈ 2.84 cm. Verifying.
##
## Usage:
##   julia --project=. test_sneasy_posterior.jl
##
## Sample size kept small (100 posterior members by default) for fast local
## turnaround; the median is well-estimated at this size. Override with
## MAX_POST env var if you want the full 10k.
## ============================================================================

using Mimi
using MimiBRICK
using CSV
using DataFrames
using Statistics

const POSTERIOR_CSV = joinpath(@__DIR__, "..", "data", "MimiBRICK",
                               "parameters_subsample_brick.csv")
const MAX_POST = parse(Int, get(ENV, "MAX_POST", "100"))
const START_YEAR = 1850
const END_YEAR   = 2100

# Mirrors run_mimibrick_obs_driven.jl:update_brick_params!.
function update_brick_params!(m, prow)
    update_param!(m, :antarctic_ocean, :anto_α, prow.anto_alpha)
    update_param!(m, :antarctic_ocean, :anto_β, prow.anto_beta)
    update_param!(m, :antarctic_icesheet, :ais_sea_level₀,             prow.antarctic_s0)
    update_param!(m, :antarctic_icesheet, :ais_bedheight₀,             prow.antarctic_bed_height0)
    update_param!(m, :antarctic_icesheet, :ais_slope,                  prow.antarctic_slope)
    update_param!(m, :antarctic_icesheet, :ais_μ,                      prow.antarctic_mu)
    update_param!(m, :antarctic_icesheet, :ais_runoffline_snowheight₀, prow.antarctic_runoff_height0)
    update_param!(m, :antarctic_icesheet, :ais_c,                      prow.antarctic_c)
    update_param!(m, :antarctic_icesheet, :ais_precipitation₀,         prow.antarctic_precip0)
    update_param!(m, :antarctic_icesheet, :ais_κ,                      prow.antarctic_kappa)
    update_param!(m, :antarctic_icesheet, :ais_ν,                      prow.antarctic_nu)
    update_param!(m, :antarctic_icesheet, :ais_iceflow₀,               prow.antarctic_flow0)
    update_param!(m, :antarctic_icesheet, :ais_γ,                      prow.antarctic_gamma)
    update_param!(m, :antarctic_icesheet, :ais_α,                      prow.antarctic_alpha)
    update_param!(m, :antarctic_icesheet, :temperature_threshold,      prow.antarctic_temp_threshold)
    update_param!(m, :antarctic_icesheet, :λ,                          prow.antarctic_lambda)
    update_param!(m, :glaciers_small_icecaps, :gsic_β₀, prow.glaciers_beta0)
    update_param!(m, :glaciers_small_icecaps, :gsic_v₀, prow.glaciers_v0)
    update_param!(m, :glaciers_small_icecaps, :gsic_s₀, prow.glaciers_s0)
    update_param!(m, :glaciers_small_icecaps, :gsic_n,  prow.glaciers_n)
    update_param!(m, :greenland_icesheet, :greenland_a, prow.greenland_a)
    update_param!(m, :greenland_icesheet, :greenland_b, prow.greenland_b)
    update_param!(m, :greenland_icesheet, :greenland_α, prow.greenland_alpha)
    update_param!(m, :greenland_icesheet, :greenland_β, prow.greenland_beta)
    update_param!(m, :greenland_icesheet, :greenland_v₀, prow.greenland_v0)
    update_param!(m, :thermal_expansion, :te_α,  prow.thermal_alpha)
    update_param!(m, :thermal_expansion, :te_s₀, prow.thermal_s0)
end

println("Building BRICK with MimiBRICK.get_model(RCP45, $START_YEAR-$END_YEAR)...")
m = MimiBRICK.get_model(
    rcp_scenario = "RCP45",
    start_year   = START_YEAR,
    end_year     = END_YEAR,
)

println("Loading posterior from $POSTERIOR_CSV ...")
posterior = DataFrame(CSV.File(POSTERIOR_CSV))
n_post = nrow(posterior)
cap = min(MAX_POST, n_post)
println("  posterior: $n_post members, processing $cap")

years = collect(START_YEAR:END_YEAR)
i1900 = findfirst(==(1900), years)
i1850 = findfirst(==(1850), years)
i2000 = findfirst(==(2000), years)
i2018 = findfirst(==(2018), years)
i2024 = findfirst(==(2024), years)

# Pre-allocate per-cell collectors
results = DataFrame(
    post_idx = Int[],
    ais_1850 = Float64[], ais_1900 = Float64[], ais_2018 = Float64[], ais_2024 = Float64[],
    gis_1850 = Float64[], gis_1900 = Float64[], gis_2018 = Float64[], gis_2024 = Float64[],
    gsic_1850= Float64[], gsic_1900= Float64[], gsic_2018= Float64[], gsic_2024= Float64[],
    te_1850  = Float64[], te_1900  = Float64[], te_2018  = Float64[], te_2024  = Float64[],
    lws_1850 = Float64[], lws_1900 = Float64[], lws_2018 = Float64[], lws_2024 = Float64[],
    total_1850=Float64[], total_1900=Float64[], total_2018=Float64[], total_2024=Float64[],
)

println("Running BRICK over $cap posterior members (Tony-like: posterior + SNEASY internal) ...")
t0 = time()
for i in 1:cap
    prow = posterior[i, :]
    update_brick_params!(m, prow)
    # DO NOT override :ocean_heat_interior or :model_global_surface_temperature
    # That's the whole point — we want SNEASY defaults for those.
    run(m)

    ais  = m[:antarctic_icesheet,     :ais_sea_level]
    gsic = m[:glaciers_small_icecaps, :gsic_sea_level]
    gis  = m[:greenland_icesheet,     :greenland_sea_level]
    te   = m[:thermal_expansion,      :te_sea_level]
    lws  = m[:landwater_storage,      :lws_sea_level]
    gmsl = m[:global_sea_level,       :sea_level_rise]

    push!(results, (
        post_idx = i,
        ais_1850  = 100 * (ais[i1850]  - ais[i2000]),
        ais_1900  = 100 * (ais[i1900]  - ais[i2000]),
        ais_2018  = 100 * (ais[i2018]  - ais[i2000]),
        ais_2024  = 100 * (ais[i2024]  - ais[i2000]),
        gis_1850  = 100 * (gis[i1850]  - gis[i2000]),
        gis_1900  = 100 * (gis[i1900]  - gis[i2000]),
        gis_2018  = 100 * (gis[i2018]  - gis[i2000]),
        gis_2024  = 100 * (gis[i2024]  - gis[i2000]),
        gsic_1850 = 100 * (gsic[i1850] - gsic[i2000]),
        gsic_1900 = 100 * (gsic[i1900] - gsic[i2000]),
        gsic_2018 = 100 * (gsic[i2018] - gsic[i2000]),
        gsic_2024 = 100 * (gsic[i2024] - gsic[i2000]),
        te_1850   = 100 * (te[i1850]   - te[i2000]),
        te_1900   = 100 * (te[i1900]   - te[i2000]),
        te_2018   = 100 * (te[i2018]   - te[i2000]),
        te_2024   = 100 * (te[i2024]   - te[i2000]),
        lws_1850  = 100 * (lws[i1850]  - lws[i2000]),
        lws_1900  = 100 * (lws[i1900]  - lws[i2000]),
        lws_2018  = 100 * (lws[i2018]  - lws[i2000]),
        lws_2024  = 100 * (lws[i2024]  - lws[i2000]),
        total_1850 = 100 * (gmsl[i1850] - gmsl[i2000]),
        total_1900 = 100 * (gmsl[i1900] - gmsl[i2000]),
        total_2018 = 100 * (gmsl[i2018] - gmsl[i2000]),
        total_2024 = 100 * (gmsl[i2024] - gmsl[i2000]),
    ))

    if i % 25 == 0 || i == cap
        elapsed = time() - t0
        rate = i / max(elapsed, 1e-6)
        println("  [$i/$cap] $(round(rate, digits=1)) runs/s, elapsed $(round(elapsed, digits=1)) s")
    end
end

println()
println("=== BRICK with posterior + SNEASY internal (Tony-like setup) ===")
println("Component medians (cm rel year 2000) across $cap posterior draws:")
println(rpad("year", 6) * lpad("AIS", 9) * lpad("GSIC", 9) *
        lpad("GIS", 9) * lpad("TE", 9) * lpad("LWS", 9) * lpad("Total", 9))
for y in [1850, 1900, 2018, 2024]
    vals = [median(results[!, Symbol(c, "_", y)]) for c in ["ais","gsic","gis","te","lws","total"]]
    println(rpad(string(y), 6) * join([lpad(string(round(v, digits=2)), 9) for v in vals]))
end

println()
println("ΔTE(1900-2018) statistics:")
dte = results.te_2018 .- results.te_1900
println("  median: $(round(median(dte), digits=2)) cm")
println("  5-95%:  $(round(quantile(dte, 0.05), digits=2)) to $(round(quantile(dte, 0.95), digits=2)) cm")
println("  mean:   $(round(mean(dte), digits=2)) cm")

println()
println("ΔAIS(1900-2018) statistics:")
dais = results.ais_2018 .- results.ais_1900
println("  median: $(round(median(dais), digits=2)) cm")
println("  5-95%:  $(round(quantile(dais, 0.05), digits=2)) to $(round(quantile(dais, 0.95), digits=2)) cm")

println()
println("Δtotal(1900-2018) statistics:")
dtot = results.total_2018 .- results.total_1900
println("  median: $(round(median(dtot), digits=2)) cm")
println("  5-95%:  $(round(quantile(dtot, 0.05), digits=2)) to $(round(quantile(dtot, 0.95), digits=2)) cm")

println()
println("Compare:")
println("  First-principles prediction (te_α=0.057, ΔOHC=75 ZJ): ΔTE = 2.84 cm")
println("  Frederikse 2020 Steric:                                +5.68 cm")
println("  Our obs-driven BRICK (te_α=0.057, ΔOHC=45 ZJ):         +1.64 cm")

# Save results for downstream Python plotting
out_csv = joinpath(@__DIR__, "..", "outputs", "brick_sneasy_posterior_diagnostic.csv")
CSV.write(out_csv, results)
println("\nwrote $out_csv")
