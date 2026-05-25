## ============================================================================
## test_sneasy_default.jl
##
## Diagnostic: run BRICK in pure-default mode (MimiBRICK.get_model with no
## parameter overrides, no posterior, no external GMST/OHC). The default
## inputs come from sneasy_temperature_RCP45_1850_2300.csv and
## sneasy_oceanheat_RCP45_1850_2300.csv (BRICK's MAP-mode internal inputs).
##
## Purpose: localize whether the 3× TE undershoot in our obs-driven runs is
## (a) from the inputs we feed BRICK (SNEASY vs external), or
## (b) from BRICK itself (implementation/parameter issue).
##
## If this default run gives TE-at-2018 ~ 2 cm (close to Frederikse Steric
## +2.3 cm), the diagnosis is confirmed: te_α is calibrated for SNEASY OHC,
## and feeding it our 40-50%-smaller external OHC produces a too-small TE.
##
## If TE-at-2018 here is also ~0.7 cm (matching our obs-driven runs despite
## the different inputs), the diagnosis needs revision.
## ============================================================================

using Mimi
using MimiBRICK

println("Building BRICK with MimiBRICK.get_model(RCP45, 1850-2100) defaults...")
m = MimiBRICK.get_model(
    rcp_scenario = "RCP45",
    start_year   = 1850,
    end_year     = 2100,
)
println("Running with no parameter overrides (uses default + SNEASY inputs)...")
run(m)

ais  = m[:antarctic_icesheet,     :ais_sea_level]
gsic = m[:glaciers_small_icecaps, :gsic_sea_level]
gis  = m[:greenland_icesheet,     :greenland_sea_level]
te   = m[:thermal_expansion,      :te_sea_level]
lws  = m[:landwater_storage,      :lws_sea_level]
gmsl = m[:global_sea_level,       :sea_level_rise]

years = collect(1850:2100)
i2000 = findfirst(==(2000), years)

println("\n=== BRICK default-mode (RCP45, SNEASY inputs, no posterior, no overrides) ===")
println("Components in cm rel year 2000:")
println(rpad("year", 6) * lpad("AIS", 8) * lpad("GSIC", 8) *
        lpad("GIS", 8) * lpad("TE", 8) * lpad("LWS", 8) *
        lpad("Total", 9))
for y in [1900, 1920, 1950, 1980, 2000, 2018, 2024, 2050, 2100]
    i = findfirst(==(y), years)
    if i === nothing
        continue
    end
    ais_v = 100 * (ais[i]  - ais[i2000])
    gsic_v= 100 * (gsic[i] - gsic[i2000])
    gis_v = 100 * (gis[i]  - gis[i2000])
    te_v  = 100 * (te[i]   - te[i2000])
    lws_v = 100 * (lws[i]  - lws[i2000])
    gmsl_v= 100 * (gmsl[i] - gmsl[i2000])
    println(rpad(string(y), 6) *
            lpad(string(round(ais_v,  digits=2)), 8) *
            lpad(string(round(gsic_v, digits=2)), 8) *
            lpad(string(round(gis_v,  digits=2)), 8) *
            lpad(string(round(te_v,   digits=2)), 8) *
            lpad(string(round(lws_v,  digits=2)), 8) *
            lpad(string(round(gmsl_v, digits=2)), 9))
end

println()
println("Reference points:")
println("  Frederikse 2020 Steric at 2018: +2.31 cm rel 2000  (full-depth)")
println("  Our obs_obs BRICK TE at 2018:   +0.67 cm rel 2000  (driver-fed obs OHC)")
println("  First-principles expectation:    ~4.6 cm rel 2000  (α=1.5e-4, our obs ΔOHC)")
println()
println("If this default-mode TE-at-2018 is ~2-3 cm, the SNEASY-OHC calibration")
println("mismatch hypothesis is confirmed.")
