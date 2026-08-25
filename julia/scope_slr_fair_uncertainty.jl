## ============================================================================
## scope_slr_fair_uncertainty.jl — PUT THE CLIMATE UNCERTAINTY BACK IN
##
## THE DEFECT. `ladrillo_setup` builds ONE `gmst` vector and `ladrillo_run_draw!`
## varies only BRICK parameters on it, so **every posterior draw sees the same
## forcing** and the shipped projection band carries **no climate-forcing
## uncertainty at all**. The driver is `fair_mean_gmst_<ssp>.csv` -- an ensemble
## MEAN over FaIR's 841 configs -- and `run_fair_ssps.py` takes that mean on the
## way out, so the spread had never even been on disk. Measured 2026-08-24
## (`ensemble_mean_driver_hides_the_tail`): the ssp585 config spread at 2300 is
## p05 3.49 / p50 6.56 / p95 11.25 / MAX 21.39 degC against the mean's 6.95.
##
## WHY IT MATTERS HERE. `ais_module_assessed` puts AIS at 94.7-100.9% of the total
## p05-p95 SPREAD at every scenario x horizon cell, and the AIS response crosses a
## retreat threshold, so it is CONVEX in warming. A missing forcing spread is
## therefore not a second-order widening -- it is missing from the one term that
## carries the band, at the one place the response is most nonlinear.
##
## MARCUS, 2026-08-25: "use the FaIR uncertainty if we are comparing to analyses
## that include climate uncertainty." Coulon 2025's band spans four GCMs; AR6 and
## FACTS bands carry climate uncertainty too. So the comparison band must carry it.
##
## THE PAIRING. Each posterior draw is assigned one FaIR config by a seeded
## permutation, giving a joint Monte Carlo sample over (BRICK parameters x climate).
## The two are independent by construction -- nothing in the calibration ties a
## BRICK draw to a FaIR config -- and [PAIRING] reports the realised assignment so
## the independence is visible rather than asserted.
##
## SPLICED, NOT RAW, AND THE REASON IS THE POSTERIOR. L14 was calibrated against
## observations on the shipped historical driver. Feeding each config's OWN hindcast
## would make the posterior inconsistent with the forcing it is conditioned on. The
## splice (our path through 2014, then the config's anomaly re-referenced to its own
## 1995-2014 mean -- `build_protect_x2300_forcing.py`'s convention) injects forcing
## uncertainty into the FUTURE only. [CALIB-MOVE] measures what still moves inside
## the calibration window against that window's own scale.
##
## ⚠ THIS IS A PRIOR PROPAGATION, NOT A REFIT. A posterior fitted under a fixed
## driver, then propagated under a spread of drivers, is not the same object as a
## posterior fitted jointly with the driver. It is the right band to COMPARE
## against ensembles that carry climate uncertainty; it is not a recalibration.
##
##   julia --project=julia_v2 julia/scope_slr_fair_uncertainty.jl [n_per_chain] [--tag=L14] [--maxrows=N]
## Writes outputs/scope_slr_fairunc_{cells,paths,gates}_<tag>.csv
## ============================================================================
using CSV, DataFrames, Statistics, Printf, Mimi, Random

include(joinpath(@__DIR__, "ladrillo_projection.jl"))

const REPO   = LADRILLO_REPO
const SEEDS  = [2026, 2027, 2028, 2029]
const NITER  = 2000000
const NBURN  = 1000000
const TAG    = let i = findfirst(a -> startswith(a, "--tag="), ARGS)
    i === nothing ? "L14" : ARGS[i][7:end]
end
const MAXROWS = let i = findfirst(a -> startswith(a, "--maxrows="), ARGS)
    i === nothing ? nothing : parse(Int, ARGS[i][11:end])
end
const SMOKE = MAXROWS !== nothing
const N_TARGET = let p = findfirst(a -> !startswith(a, "--"), ARGS)
    p === nothing ? 500 : parse(Int, ARGS[p])
end
const SSP      = "ssp585"
const HORIZONS = [2100, 2150, 2300]
const Y0, Y1   = 1850, 2300
const COMPONENTS = [:ais, :total]          # AIS carries the band; total is the deliverable
const PAIR_SEED = 2026                     # the draw -> config permutation
const CUBE_G = joinpath(LADRILLO_OBS, "fair_cube_gmst_$(SSP)_spliced.csv")
const CUBE_O = joinpath(LADRILLO_OBS, "fair_cube_ohc_$(SSP)_spliced.csv")
## [CALIB-MOVE] scale -- the AIS target's own span and sigma over 1900-2025.
const AIS_TARGET_SPAN_CM, AIS_TARGET_SIGMA_CM = 1.404, 0.141
const CALIB_WIN = (1850, 2024)
const CONTROL_TOL_CM = 0.5
## Coulon et al. 2025 Nat. Commun. 16:10385, ssp585 AIS @2300 vs 2015, cm.
## Their band spans FOUR GCMs, which is exactly why ours has to carry climate too.
const COULON_BAND, COULON_MED = (73.0, 595.0), 270.0

chain_path(sd) = joinpath(REPO, "outputs/mcmc", "chain_$(TAG)_seed$(sd)_n$(NITER).csv")
hdr(sd) = String.(propertynames(CSV.read(chain_path(sd), DataFrame; limit = 0)))
for sd in SEEDS; isfile(chain_path(sd)) || error("missing chain $(chain_path(sd))"); end
const VARIANT = ladrillo_gis_variant(hdr(SEEDS[1]))

function read_draws(sd)
    need = ladrillo_used_cols(VARIANT)
    h = hdr(sd)
    rd = ladrillo_gis_needs_native(h) ?
        vcat(setdiff(need, LADRILLO_GIS_SLOW_NATIVE_COLS),
             LADRILLO_GIS_SLOW_REPARAM_COLS) |> unique : need
    df = SMOKE ? CSV.read(chain_path(sd), DataFrame; select = rd, limit = MAXROWS) :
                 CSV.read(chain_path(sd), DataFrame; select = rd)
    nb = SMOKE ? 0 : NBURN
    step = max(1, (nrow(df) - nb) ÷ N_TARGET)
    idx = collect((nb + 1):step:nrow(df))
    d = ladrillo_native_greenland!(df[idx[1:N_TARGET], :]); df = nothing; GC.gc(); d
end

@printf("SLR WITH FaIR CLIMATE UNCERTAINTY | tag %s%s | %d draws/chain x %d chains | %s\n",
        TAG, SMOKE ? "  ** SMOKE (--maxrows=$(MAXROWS)) **" : "", N_TARGET, length(SEEDS), SSP)
flush(stdout)
const DRAWS = [(@printf("  reading chain seed%d ...\n", sd); flush(stdout); read_draws(sd))
               for sd in SEEDS]
const NDRAW = sum(nrow.(DRAWS))
## flatten to one row list so a draw index means one thing everywhere
const ROWS = [r for d in DRAWS for r in eachrow(d)]
@assert length(ROWS) == NDRAW

## ---- the FaIR cube -------------------------------------------------------
const CG = CSV.read(CUBE_G, DataFrame)
const CO = CSV.read(CUBE_O, DataFrame)
const CFG = [c for c in String.(propertynames(CG)) if startswith(c, "cfg_")]
const NCFG = length(CFG)
const CYEARS = Int.(CG.year)
const YEARS = collect(Y0:Y1)
@assert CYEARS == YEARS "the cube's year axis is not $(Y0):$(Y1)"
@assert String.(propertynames(CO))[2:end] == CFG "gmst and ohc cubes disagree on configs"
gmst_of(c) = Float64.(CG[!, c])
ohc_of(c)  = Float64.(CO[!, c])
const IREF = findall(y -> LADRILLO_REF[1] <= y <= LADRILLO_REF[2], YEARS)
const I2300 = findfirst(==(2300), YEARS)

## ---- the pairing ---------------------------------------------------------
## A seeded permutation, cycled if there are more draws than configs. Reported,
## not assumed: [PAIRING] prints the realised use counts and checks that the
## assigned forcing sample reproduces the cube's own 2300 distribution.
const ASSIGN = let rng = MersenneTwister(PAIR_SEED)
    a = Int[]
    while length(a) < NDRAW; append!(a, randperm(rng, NCFG)); end
    a[1:NDRAW]
end
const CFG_OF_DRAW = [CFG[i] for i in ASSIGN]

## ---- run -----------------------------------------------------------------
"""Run `idx` (draw indices) on a Ladrillo built at `g`/`o`; write into `out`."""
function run_into!(out, idx, g, o)
    bf = ladrillo_setup(ssp = SSP, y0 = Y0, y1 = Y1, gis_variant = VARIANT, gmst = g, ohc = o)
    for k in idx
        ladrillo_run_draw!(bf, ROWS[k])
        for c in COMPONENTS
            out[c][k, :] = coalesce.(ladrillo_series(bf, c), NaN)
        end
    end
    bf
end

alloc() = Dict(c => Matrix{Float64}(undef, NDRAW, length(YEARS)) for c in COMPONENTS)

## arm `fixed`: the shipped MEAN driver, every draw. The control.
@printf("\n  running arm `fixed` (shipped MEAN driver, %d draws) ...\n", NDRAW); flush(stdout)
const FIXED = alloc()
let g = [_yearmap(joinpath(LADRILLO_OBS, "fair_mean_gmst_$(SSP).csv"), "gmst_C")[y] for y in YEARS],
    o = [_yearmap(joinpath(LADRILLO_OBS, "fair_mean_ohc_$(SSP).csv"), "ohc_1e22J")[y] for y in YEARS]
    run_into!(FIXED, 1:NDRAW, g, o)
end

## arm `joint`: one FaIR config per draw. Grouped by config so `ladrillo_setup`
## (0.54 s warm) is paid once per config, not once per draw.
const JOINT = alloc()
let groups = Dict{String, Vector{Int}}()
    for k in 1:NDRAW; push!(get!(groups, CFG_OF_DRAW[k], Int[]), k); end
    @printf("  running arm `joint` (%d configs, %d draws) ...\n", length(groups), NDRAW); flush(stdout)
    n = 0
    for (c, idx) in groups
        run_into!(JOINT, idx, gmst_of(c), ohc_of(c))
        n += 1
        n % 100 == 0 && (@printf("    %d/%d configs\n", n, length(groups)); flush(stdout))
    end
end
yidx(y) = findfirst(==(y), YEARS)

## ==========================================================================
## GATES
## ==========================================================================
@printf("\n%s\nGATES\n%s\n", repeat("=", 92), repeat("=", 92))
rowsg = DataFrame(gate = String[], key = String[], value = Float64[], verdict = String[])

## [PAIRING] the assignment must be balanced and must not bias the forcing sample.
let used = length(unique(CFG_OF_DRAW)),
    cnt = [count(==(c), CFG_OF_DRAW) for c in unique(CFG_OF_DRAW)],
    drawn = [gmst_of(c)[I2300] - mean(gmst_of(c)[IREF]) for c in CFG_OF_DRAW],
    all_ = [gmst_of(c)[I2300] - mean(gmst_of(c)[IREF]) for c in CFG]
    @printf("  [PAIRING] %d of %d configs used, each %d-%d times (seed %d)\n",
            used, NCFG, minimum(cnt), maximum(cnt), PAIR_SEED)
    @printf("            assigned dGMST@2300  p05 %.2f p50 %.2f p95 %.2f  |  whole cube  p05 %.2f p50 %.2f p95 %.2f degC\n",
            quantile(drawn, 0.05), median(drawn), quantile(drawn, 0.95),
            quantile(all_, 0.05), median(all_), quantile(all_, 0.95))
    d = abs(median(drawn) - median(all_))
    push!(rowsg, ("PAIRING", "configs_used", used, used == min(NCFG, NDRAW) ? "PASS" : "CHECK"))
    push!(rowsg, ("PAIRING", "median_dgmst_bias_degC", d, d < 0.1 ? "PASS" : "CHECK"))
end

## [CONTROL] the fixed arm must reproduce the SHIPPED panel.
const SHIPPED = CSV.read(joinpath(REPO, "outputs", "ssps_components_2300_$(TAG).csv"), DataFrame)
const SSP_LABEL = Dict("ssp126" => "SSP1-2.6", "ssp245" => "SSP2-4.5", "ssp585" => "SSP5-8.5")
for c in COMPONENTS, H in HORIZONS
    med = median(FIXED[c][:, yidx(H)])
    r = SHIPPED[(SHIPPED.year .== H) .& (SHIPPED.ssp .== SSP_LABEL[SSP]) .&
                (SHIPPED.component .== String(c)), :]
    if nrow(r) == 1
        d = med - r.med[1]; v = abs(d) < CONTROL_TOL_CM ? "PASS" : "CHECK"
        @printf("  [CONTROL] %-5s @%d  fixed median %8.3f vs shipped %8.3f  diff %+7.4f cm -> %s\n",
                c, H, med, r.med[1], d, v)
        push!(rowsg, ("CONTROL", "$(c)_med_$(H)", d, v))
    end
end

## [CALIB-MOVE] what the splice still moves inside the calibration window.
let i0 = yidx(CALIB_WIN[1]), i1 = yidx(CALIB_WIN[2])
    for c in COMPONENTS
        w = maximum(abs.(JOINT[c][:, i0:i1] .- FIXED[c][:, i0:i1]))
        @printf("  [CALIB-MOVE] %-5s %d-%d  max |joint - fixed| = %.4f cm",
                c, CALIB_WIN[1], CALIB_WIN[2], w)
        c === :ais ? @printf(" = %.1f%% of the %.3f cm AIS target span = %.2f sigma\n",
                             100 * w / AIS_TARGET_SPAN_CM, AIS_TARGET_SPAN_CM, w / AIS_TARGET_SIGMA_CM) :
                     @printf("  (no single target scale for :total -- reported raw)\n")
        push!(rowsg, ("CALIB-MOVE", "$(c)_max_cm", w, "measured"))
    end
end
CSV.write(joinpath(REPO, "outputs", "scope_slr_fairunc_gates_$(TAG)$(SMOKE ? "_SMOKE" : "").csv"), rowsg)

## ==========================================================================
## THE CELLS
## ==========================================================================
cells = DataFrame(ssp = String[], component = String[], horizon = Int[], arm = String[],
                  n_draws = Int[], med_cm = Float64[], p05_cm = Float64[], p95_cm = Float64[],
                  spread_cm = Float64[], spread_ratio = Float64[], med_ratio = Float64[])
@printf("\n%s\nSLR WITH vs WITHOUT FaIR CLIMATE UNCERTAINTY -- %s, cm rel %d-%d\n%s\n",
        repeat("=", 92), SSP, LADRILLO_REF[1], LADRILLO_REF[2], repeat("=", 92))
@printf("  %-6s %-6s %-6s %9s %9s %9s %9s %11s\n",
        "comp", "horiz", "arm", "median", "p05", "p95", "spread", "x fixed sprd")
for c in COMPONENTS
    for H in HORIZONS
        f = FIXED[c][:, yidx(H)]; sf = quantile(f, 0.95) - quantile(f, 0.05)
        for (arm, A) in (("fixed", FIXED[c]), ("joint", JOINT[c]))
            v = A[:, yidx(H)]; sp = quantile(v, 0.95) - quantile(v, 0.05)
            push!(cells, (SSP, String(c), H, arm, length(v), median(v),
                          quantile(v, 0.05), quantile(v, 0.95), sp, sp / sf,
                          median(v) / median(f)))
            @printf("  %-6s %-6d %-6s %9.2f %9.2f %9.2f %9.2f %10.2fx\n",
                    c, H, arm, median(v), quantile(v, 0.05), quantile(v, 0.95), sp, sp / sf)
        end
    end
    println()
end
CSV.write(joinpath(REPO, "outputs", "scope_slr_fairunc_cells_$(TAG)$(SMOKE ? "_SMOKE" : "").csv"), cells)

## ==========================================================================
## THE COMPARISON that motivated it
## ==========================================================================
@printf("%s\nAGAINST COULON 2025, WHOSE BAND SPANS FOUR GCMs\n%s\n", repeat("=", 92), repeat("=", 92))
let iH = yidx(2300), cw = COULON_BAND[2] - COULON_BAND[1]
    @printf("  Coulon ssp585 AIS@2300: median %.0f, band %.0f-%.0f = %.0f cm wide\n",
            COULON_MED, COULON_BAND[1], COULON_BAND[2], cw)
    for (arm, A) in (("fixed", FIXED[:ais]), ("joint", JOINT[:ais]))
        v = A[:, iH]; sp = quantile(v, 0.95) - quantile(v, 0.05)
        @printf("  %-6s median %7.2f = %.2fx theirs;  band [%7.2f, %7.2f] = %6.2f cm = %.2fx their width\n",
                arm, median(v), median(v) / COULON_MED, quantile(v, 0.05), quantile(v, 0.95),
                sp, sp / cw)
    end
end

paths = DataFrame(year = Int[], component = String[], arm = String[],
                  med_cm = Float64[], p05_cm = Float64[], p95_cm = Float64[])
for c in COMPONENTS, (arm, A) in (("fixed", FIXED[c]), ("joint", JOINT[c])), (i, y) in enumerate(YEARS)
    y < 1990 && continue
    v = A[:, i]
    push!(paths, (y, String(c), arm, median(v), quantile(v, 0.05), quantile(v, 0.95)))
end
CSV.write(joinpath(REPO, "outputs", "scope_slr_fairunc_paths_$(TAG)$(SMOKE ? "_SMOKE" : "").csv"), paths)
@printf("\nwrote outputs/scope_slr_fairunc_{cells,paths,gates}_%s%s.csv\n", TAG, SMOKE ? "_SMOKE" : "")
