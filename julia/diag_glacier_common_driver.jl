# Common-driver test for the glacier hindcast comparison (2026-11-22).
#
# Marcus 11-22: "yes, run the common-driver test". In the GMD Table 4 hindcast, Ladrillo's glacier reservoirs are driven
# by OBSERVED regional HadCRUT5 temperatures through 2024 (data/drivers/glacier_block_temperature.csv), while MAGICC-SLR
# runs on its own GSAT and BRICK 2.0 on the FaIR mean GMST. This re-runs Ladrillo's glacier hindcast with the
# PROJECTION-MODE driver in every year, T_g = A_g * G + c_g (G = FaIR mean GMST, A_g the draw's gic_amp_<block>, c_g
# the anchor offset Ladrillo already uses after 2024), so its glaciers see the same kind of driver as BRICK 2.0.
# Nothing is refitted: the posterior is L27 as shipped.
#
# Everything else is scripts/posterior_predictive.jl's: forcing ssp245harm, 1850-2026, land water :central, tap off,
# FIT_REF 1995-2005, the same 2,000 rows (1:5:9996, read from the canonical band file's provenance), hindcast scope
# gsic_hind + the draw's uncharted-ice term.
#
# Gates
#   [REPRO-OBS]       the observed-driver arm's median equals the canonical band file's glaciers_p50 (identity).
#   [DRIVER-CHANGED]  for draw 1, the projection-mode driver differs from the observed one before 2025 in every block and
#                     is identical from 2025 on (the switch touches only the observed years).
#   Mutations (each must FAIL its gate): --mutate=mask leaves the observed mask on; --mutate=repro adds 1e-6 cm.
#
#   julia --project=../Ladrillo julia/diag_glacier_common_driver.jl [--mutate=mask|repro]
# Writes outputs/diag_glacier_common_driver_L27{,_drivers}.csv (not under --mutate). No RNG is used.

using Ladrillo, CSV, DataFrames, Printf, Statistics

const Y0, Y1 = 1850, 2026
const FORCING = "ssp245harm"
const ROWS = 1:5:9996
const LAD = joinpath(dirname(dirname(@__DIR__)), "Ladrillo")
const CANON = joinpath(LAD, "outputs", "hindcast", "postpred_components_timeseries.csv")
const OUTDIR = joinpath(dirname(@__DIR__), "outputs")
const OUT = joinpath(OUTDIR, "diag_glacier_common_driver_L27.csv")
const OUT_DRV = joinpath(OUTDIR, "diag_glacier_common_driver_L27_drivers.csv")
const DRV_WINDOWS = [(1900, 1919), (1920, 1949), (1950, 1992), (1993, 2024)]
const REPRO_TOL = 1e-10
const MUTATE = let i = findfirst(a -> startswith(a, "--mutate="), ARGS); i === nothing ? "" : ARGS[i][10:end]; end

canon = CSV.read(CANON, DataFrame)
occursin("draws rows $(ROWS)", canon.provenance[1]) ||
    error("canonical band file was not built on rows $(ROWS): $(canon.provenance[1])")

post = posterior(rows = ROWS)
gmst, ohc = mean_forcing(FORCING; years = Y0:Y1)
lm = LadrilloModel(gmst, ohc; years = Y0:Y1, lws = :central, tap = false, ref = Ladrillo.FIT_REF)
FY = Ladrillo.FIT_START:Y1
imy = [findfirst(==(y), lm.years) for y in FY]
n, ny = nrow(post), length(FY)
mask_obs = copy(lm.glac_mask)
mask_test = MUTATE == "mask" ? copy(mask_obs) : falses(length(mask_obs))
fails = String[]
gate(name, ok, msg) = (println("[$name] ", ok ? "PASS" : "FAIL", ": ", msg); ok || push!(fails, name))

# [DRIVER-CHANGED] on draw 1, and the driver window means at the posterior-median amplification
r1 = post[1, :]
pre, postw = lm.years .<= 2024, lm.years .>= 2025
ok_pre, ok_post = true, true
for b in Ladrillo.GLACIER_BLOCKS
    a = Float64(r1["gic_amp_$b"])
    lm.glac_mask .= mask_obs; d_obs = Ladrillo.glacier_driver(lm, b, a)
    lm.glac_mask .= mask_test; d_tst = Ladrillo.glacier_driver(lm, b, a)
    global ok_pre &= maximum(abs.(d_obs[pre] .- d_tst[pre])) > 0
    global ok_post &= all(d_obs[postw] .== d_tst[postw])
end
gate("DRIVER-CHANGED", ok_pre && ok_post,
     "projection-mode driver differs from the observed one before 2025 in every block: $ok_pre; identical from 2025: $ok_post")

drv = DataFrame(block = String[], window = String[], amp_median = Float64[], observed_K = Float64[],
                projection_mode_K = Float64[])
for b in Ladrillo.GLACIER_BLOCKS
    a = median(Float64.(post[!, "gic_amp_$b"]))
    lm.glac_mask .= mask_obs; d_obs = Ladrillo.glacier_driver(lm, b, a)
    lm.glac_mask .= falses(length(mask_obs)); d_pm = Ladrillo.glacier_driver(lm, b, a)
    for (y0, y1) in DRV_WINDOWS
        w = y0 .<= lm.years .<= y1
        push!(drv, (b, "$y0-$y1", a, mean(d_obs[w]), mean(d_pm[w])))
    end
end

obsdrv = Array{Float64}(undef, n, ny); pmdrv = similar(obsdrv); unch = similar(obsdrv)
t0 = time()
for (i, r) in enumerate(eachrow(post))
    u = Float64(r["gic_u_unch"])
    lm.glac_mask .= mask_obs
    run_draw!(lm, r)
    obsdrv[i, :] = sea_level(lm, :gsic_hind; funch = u)[imy]
    unch[i, :] = obsdrv[i, :] .- sea_level(lm, :gsic_hind)[imy]
    lm.glac_mask .= mask_test
    run_draw!(lm, r)
    pmdrv[i, :] = sea_level(lm, :gsic_hind; funch = u)[imy]
end
lm.glac_mask .= mask_obs
@printf("%d draws x 2 drivers in %.0fs\n", n, time() - t0)

q(x, p) = [quantile(view(x, :, j), p) for j in 1:size(x, 2)]
p50_obs = q(obsdrv, 0.5) .+ (MUTATE == "repro" ? 1e-6 : 0.0)
cj = [findfirst(==(y), canon.year) for y in FY]
worst = maximum(abs.(p50_obs .- Float64.(canon.glaciers_p50[cj])))
gate("REPRO-OBS", worst <= REPRO_TOL,
     @sprintf("observed-driver median vs %s glaciers_p50: largest |diff| %.2e cm (tol %g)", basename(CANON), worst, REPRO_TOL))

u_med = median(Float64.(post[!, "gic_u_unch"]))
prov = "SLR-RFF-BRICK julia/diag_glacier_common_driver.jl | Ladrillo $(pkgversion(Ladrillo)) (posterior L27, rows $(ROWS)) | " *
       "FaIR 2.2.4 (calib 1.6.0) forcing $FORCING | land water :central | tap off | scope gsic_hind + uncharted ice | " *
       "observed driver = HadCRUT5 regional through 2024; projection-mode = gic_amp * FaIR mean GMST + anchor offset, all years | " *
       "cm rel $(Ladrillo.FIT_REF[1])-$(Ladrillo.FIT_REF[2]) | no RNG | julia $(VERSION)"
out = DataFrame(year = collect(FY),
                obsdrv_p05 = q(obsdrv, 0.05), obsdrv_p50 = p50_obs, obsdrv_p95 = q(obsdrv, 0.95),
                pmdrv_p05 = q(pmdrv, 0.05), pmdrv_p50 = q(pmdrv, 0.5), pmdrv_p95 = q(pmdrv, 0.95),
                unch_p50 = q(unch, 0.5), u_unch_median_mm = fill(u_med, ny),
                target = Float64.(coalesce.(canon.glaciers_obs[cj], NaN)))
out.provenance = fill(prov, ny)
drv.provenance = fill(replace(prov, r"cm rel [0-9-]+" => "K rel 1850-1900 (block frame), at the posterior-median amplification"), nrow(drv))

println("\nGlacier driver window means (K, block frame), observed vs projection-mode, posterior-median amplification")
show(drv[:, Not(:provenance)], allrows = true); println()
println("\nGlacier hindcast median, cm rel 1995-2005 (selected years)")
for y in (1900, 1920, 1940, 1960, 1980, 2000, 2010, 2020, 2025)
    j = findfirst(==(y), FY)
    @printf("  %d  target %7.2f   observed driver %7.2f   projection-mode %7.2f\n", y, out.target[j], out.obsdrv_p50[j], out.pmdrv_p50[j])
end
if isempty(MUTATE)
    mkpath(OUTDIR); CSV.write(OUT, out); CSV.write(OUT_DRV, drv)
    println("\nwrote ", OUT, "\n      ", OUT_DRV)
end
isempty(fails) || (println("FAILED gates: ", fails); exit(1))
