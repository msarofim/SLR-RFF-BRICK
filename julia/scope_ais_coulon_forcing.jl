## ============================================================================
## scope_ais_coulon_forcing.jl — AT COULON'S FORCING, WHAT DOES OUR AIS GIVE?
##
## THE OPEN ITEM. handoff_2026-08-24i_ais_items123.md section 0.5B, item 1. Item 2
## of that session established that the Coulon 2025 comparison was never
## like-for-like: their Antarctic warming at 2300 is +12.0 to +17.0 degC and our
## WHOLE ais_gmst_amp p05-p95 is +5.46 to +7.72, so their band had to be
## interpolated DOWN to our forcing (~131 cm) before it could be compared, and
## that FLIPPED the sign of the shipped reading. The interpolation rests on two
## anchors and a convexity argument, which is why it yields a BOUND and not a
## value. This script completes the like-for-like in the direction we control:
## instead of moving Coulon to us, it moves US to Coulon.
##
## THE PRE-CHECK CAME BACK YES, AND IT CHANGES THE INSTRUMENT.
## The handoff asked, before any new scenario was built, whether the FaIR
## ensemble's own hot tail already spans CMIP6-like forcing. It does
## (FaIRtoFrEDI/run_fair_ssp585_spread.py, outputs/diag_fair_ssp585_hot_tail.csv):
## at 2300, vs 1995-2014, the 841-config ssp585 spread is p05 3.49 / p50 6.56 /
## p95 11.25 / max 21.39 degC, while the SHIPPED DRIVER -- the ensemble MEAN --
## reaches 6.95. Sixteen configs clear T_ant = 12 degC at the posterior-median amp.
## So the arms below are driven by REAL, SELF-CONSISTENT FaIR TRAJECTORIES chosen
## out of that tail, not by an arbitrary rescaling of the mean. Their ensemble
## percentiles (98.0 / 99.4 / 99.8) are reported with every cell, because a real
## config at pctile 99.8 is a rare draw and must never read as a central case.
##
## WHY THIS IS AN AIS-ONLY READING, SAID OUT LOUD. A hotter GMST moves every
## component -- ANTO, the runoff line, precipitation, glaciers, Greenland, thermal
## expansion. Only the AIS number is reported here and only it should be quoted.
## OHC is not even touched: in Ladrillo, OHC reaches `thermal_expansion` alone
## (brick_mengel.jl:92-95), while AIS and ANTO read
## `model_global_surface_temperature`, so the AIS arm is a pure GMST override.
##
## THE SPLICE IS THE CONTROLLED EXPERIMENT, and the convention is
## build_protect_x2300_forcing.py's, unchanged: our own path through 2014, then
## the config's anomaly re-referenced to its own 1995-2014 mean. The hindcast
## anchor is therefore bit-identical to the shipped run through 2014. It is NOT
## identical over 2015-2024, which is inside the AIS calibration window, so
## [CALIB-MOVE] MEASURES that movement against the window's own scale (the AIS
## target spans 1.404 cm over 1900-2025 with a mean 1-sigma of 0.141 cm) rather
## than asserting inertness the way the fast-dynamics arms could.
##
## NOTHING IS RECALIBRATED. These are prior propagations on the L14 posterior.
##
##   julia --project=julia_v2 julia/scope_ais_coulon_forcing.jl [n_per_chain] [--tag=L14] [--maxrows=N]
## Writes outputs/scope_ais_coulon_{cells,paths}_<tag>.csv
## ============================================================================
using CSV, DataFrames, Statistics, Printf, Mimi

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
const SSP      = "ssp585"                 # Coulon's high scenario; the comparison cell
const HORIZONS = [2100, 2150, 2300]
const Y0, Y1   = 1850, 2300
## The arm drivers, built by FaIRtoFrEDI/run_fair_ssp585_spread.py.
## --pathtest=v145|v160 (2026-08-28, DEFAULT-OFF): swap the arm file and the ARMS list for the
## PATH-vs-ENDPOINT test. Two configs matched at T_ant@2300 but ~11-14% apart in the 2015-2300
## temperature INTEGRAL. The arms are selected on the ENDPOINT, but AIS integrates temperature, so
## the endpoint is not a sufficient statistic for the path: among configs matched at 2300, the
## integral's residual sd is 48% (v145) / 78% (v160) of its unconditioned spread. If the two bands
## agree, the endpoint IS sufficient and an n=1 arm is tolerable; if not, the arm has to be
## specified on the integral. Omitting the flag reproduces the previous behaviour exactly.
## ⚠ VINTAGE-LOCKED: v145 pairs with an L14-line posterior, v160 with L21. The control column is
## that vintage's own mean driver, so a mismatch shows up as a [CONTROL] failure, not a silent mix.
const PATHTEST = let i = findfirst(a -> startswith(a, "--pathtest="), ARGS)
    i === nothing ? nothing : ARGS[i][12:end]
end
@assert PATHTEST === nothing || PATHTEST in ("v145", "v160", "integral") "--pathtest must be v145, v160 or integral"
const ARM_CSV  = PATHTEST === nothing ? joinpath(LADRILLO_OBS, "fair_coulon_arm_$(SSP).csv") :
                 joinpath(LADRILLO_OBS, PATHTEST == "v145" ? "fair_coulon_pathtest_$(SSP).csv" :
                          PATHTEST == "v160" ? "fair_coulon_pathtest_$(SSP)_v160.csv" :
                          "fair_coulon_arm_integral_$(SSP)_v160.csv")
## arm key => (driver column, label, Coulon T_ant target degC, ensemble pctile)
## Targets and percentiles are Coulon 2025's and the FaIR ensemble's respectively;
## both are carried here so every printed label derives from a named constant.
const ARMS = PATHTEST === nothing ?
    [("control", "gmst_control_spliced", "shipped MEAN driver", NaN,   NaN),
     ("tant12",  "gmst_tant12p0_spliced", "Coulon coldest",     12.0,  98.0),
     ("tant14",  "gmst_tant14p5_spliced", "Coulon midpoint",    14.5,  99.4),
     ("tant17",  "gmst_tant17p0_spliced", "Coulon hottest",     17.0,  99.8)] :
    ## PATH TEST: both arms sit at the SAME T_ant@2300 (13.59/13.75 v145; 13.40/13.25 v160)
    ## and differ only in the PATH taken to get there (integral 22.41 vs 24.96 = 10.8% v145;
    ## 25.72 vs 22.42 = 13.7% v160). Targets/percentiles are NaN: these are not Coulon arms.
    PATHTEST == "integral" ?
    ## INTEGRAL-CENTRED ARMS (Marcus 2026-08-28). Selected as the MEDIAN INTEGRAL of the configs
    ## within +-1.25 degC (half the target spacing) of Coulon's endpoint target, instead of the
    ## endpoint argmin. ⚠ tant17 IS ABSENT BY CONSTRUCTION: 0 of 841 configs fall within the band
    ## of 17.0 degC. It is omitted rather than filled with a nearest-config substitute, because
    ## that substitution is exactly the silent duplicate that made the old tant17 dangerous.
    [("control", "gmst_control_spliced",  "shipped MEAN driver",             NaN,  NaN),
     ("tant12",  "gmst_tant12p0_spliced", "Coulon coldest, integral-centred", 12.0, NaN),
     ("tant14",  "gmst_tant14p5_spliced", "Coulon midpoint, integral-centred",14.5, NaN)] :
    [("control", "gmst_control_spliced", "shipped MEAN driver",      NaN, NaN),
     ("pathA",   "gmst_pathA_spliced",   "same endpoint, LOW integral",  NaN, NaN),
     ("pathB",   "gmst_pathB_spliced",   "same endpoint, HIGH integral", NaN, NaN)]
const CONTROL = "control"
## Coulon et al. 2025, Nat. Commun. 16:10385 -- ssp585 AIS at 2300, cm SLE.
const COULON_BAND = (73.0, 595.0)
const COULON_MED  = (267.0, 273.0)        # the two ice-sheet models' medians
const COULON_BASEYEAR = 2015              # theirs; ours is LADRILLO_REF = 1995-2014
## [CALIB-MOVE] scale: the AIS target's own span and 1-sigma over 1900-2025,
## from outputs/recalib_targets_ext.csv. Derived from the thing the gate tests
## (`derive_gate_from_the_thing`), not picked.
const AIS_TARGET_SPAN_CM = 1.404
const AIS_TARGET_SIGMA_CM = 0.141
const CALIB_WIN = (1850, 2024)
## [CONTROL] tolerance: the arm must reproduce the SHIPPED panel, not merely itself.
const CONTROL_TOL_CM = 0.5                # scope_ais_fastdyn_shape.jl's [FORK] tolerance
const TANT0 = LADRILLO_AIS_TANT0

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

@printf("AIS at COULON'S FORCING | tag %s%s | %d draws/chain x %d chains | %s\n",
        TAG, SMOKE ? "  ** SMOKE (--maxrows=$(MAXROWS)) **" : "", N_TARGET, length(SEEDS), SSP)
flush(stdout)
const DRAWS = [(@printf("  reading chain seed%d ...\n", sd); flush(stdout); read_draws(sd))
               for sd in SEEDS]
const NDRAW = sum(nrow.(DRAWS))
const AMP = [Float64(r["ais_gmst_amp"]) for d in DRAWS for r in eachrow(d)]
@printf("  ais_gmst_amp over %d draws: p05 %.4f  med %.4f  p95 %.4f\n",
        NDRAW, quantile(AMP, 0.05), median(AMP), quantile(AMP, 0.95))

## ---- the drivers ---------------------------------------------------------
const ARMDF = CSV.read(ARM_CSV, DataFrame)
const YEARS = collect(Y0:Y1)
function driver(col::String)
    m = Dict(Int(ARMDF[i, "year"]) => Float64(ARMDF[i, col]) for i in 1:nrow(ARMDF))
    [haskey(m, y) ? m[y] : error("driver $col: year $y missing") for y in YEARS]
end
const GMST = Dict(k => driver(c) for (k, c, _, _, _) in ARMS)
## The reference the warming anomalies are quoted against -- Coulon's, and
## LADRILLO_REF is the same window, so one constant serves both.
const IREF = findall(y -> LADRILLO_REF[1] <= y <= LADRILLO_REF[2], YEARS)
const I2300 = findfirst(==(2300), YEARS)

@printf("\n%s\nTHE ARMS -- real FaIR ssp585 configs, spliced at 2014 (%s)\n%s\n",
        repeat("=", 92), basename(ARM_CSV), repeat("=", 92))
@printf("  %-8s %-22s %8s %8s %8s %8s  %s\n",
        "arm", "label", "dGMST", "T_ant", "target", "pctile", "(degC @2300 vs $(LADRILLO_REF[1])-$(LADRILLO_REF[2]))")
for (k, _, lab, tgt, pct) in ARMS
    g = GMST[k]
    dg = g[I2300] - mean(g[IREF])
    @printf("  %-8s %-22s %8.2f %8.2f %8s %8s\n", k, lab, dg, dg * median(AMP),
            isnan(tgt) ? "--" : @sprintf("%.1f", tgt),
            isnan(pct) ? "--" : @sprintf("%.1f", pct))
end
flush(stdout)

## ---- run -----------------------------------------------------------------
"""Run every draw on `bf`; returns AIS (draws x years), cm rel LADRILLO_REF."""
function run_arm(bf)
    yrs = bf.years
    out = Matrix{Float64}(undef, NDRAW, length(yrs))
    k = 0
    for d in DRAWS, i in 1:nrow(d)
        k += 1
        ladrillo_run_draw!(bf, d[i, :])
        out[k, :] = coalesce.(ladrillo_series(bf, :ais), NaN)
    end
    out, yrs
end

function run_all()
    res, yrs_out = Dict{String, Matrix{Float64}}(), Int[]
    for (k, _, lab, _, _) in ARMS
        @printf("  running arm %s (%s) ...\n", k, lab); flush(stdout)
        bf = ladrillo_setup(ssp = SSP, y0 = Y0, y1 = Y1, gis_variant = VARIANT,
                            gmst = GMST[k])
        A, yrs = run_arm(bf)
        res[k] = A; isempty(yrs_out) && (yrs_out = yrs)
    end
    res, yrs_out
end
const RES, YRS = run_all()
yidx(y) = findfirst(==(y), YRS)

## ==========================================================================
## GATES
## ==========================================================================
@printf("\n%s\nGATES\n%s\n", repeat("=", 92), repeat("=", 92))
rowsg = DataFrame(gate = String[], key = String[], value = Float64[], verdict = String[])

## [CONTROL] the control arm must reproduce the SHIPPED panel.
const SHIPPED = CSV.read(joinpath(REPO, "outputs", "ssps_components_2300_$(TAG).csv"), DataFrame)
const SSP_LABEL = Dict("ssp245" => "SSP2-4.5", "ssp585" => "SSP5-8.5")
for H in HORIZONS
    A = RES[CONTROL]; med = median(A[:, yidx(H)])
    r = SHIPPED[(SHIPPED.year .== H) .& (SHIPPED.ssp .== SSP_LABEL[SSP]) .&
                (SHIPPED.component .== "ais"), :]
    if nrow(r) == 1
        d = med - r.med[1]
        v = abs(d) < CONTROL_TOL_CM ? "PASS" : "CHECK"
        @printf("  [CONTROL] @%d  control median %8.3f vs shipped %8.3f  diff %+7.4f cm -> %s\n",
                H, med, r.med[1], d, v)
        push!(rowsg, ("CONTROL", "ais_med_$(H)", d, v))
    end
end

## [CALIB-MOVE] the splice is at 2014 but the AIS calibration window runs to 2025,
## so 2015-2024 DOES move. Measure it against the target's own scale.
let i0 = yidx(CALIB_WIN[1]), i1 = yidx(CALIB_WIN[2]), base = RES[CONTROL]
    for (k, _, lab, _, _) in ARMS
        k == CONTROL && continue
        w = maximum(abs.(RES[k][:, i0:i1] .- base[:, i0:i1]))
        @printf("  [CALIB-MOVE] %-7s %d-%d  max |arm - control| = %.4f cm = %.1f%% of the %.3f cm AIS target span = %.2f sigma\n",
                k, CALIB_WIN[1], CALIB_WIN[2], w, 100 * w / AIS_TARGET_SPAN_CM,
                AIS_TARGET_SPAN_CM, w / AIS_TARGET_SIGMA_CM)
        push!(rowsg, ("CALIB-MOVE", "$(k)_max_cm", w, "measured"))
        push!(rowsg, ("CALIB-MOVE", "$(k)_sigma", w / AIS_TARGET_SIGMA_CM, "measured"))
    end
end

## [BASEYEAR] Coulon quotes sea level from 2015, we rebase to 1995-2014. Price it
## rather than assume it is negligible.
let i = yidx(COULON_BASEYEAR), A = RES[CONTROL]
    off = median(A[:, i])
    @printf("  [BASEYEAR] our AIS at %d = %+.3f cm rel %d-%d -> Coulon's baseline is %.3f cm ABOVE ours\n",
            COULON_BASEYEAR, off, LADRILLO_REF[1], LADRILLO_REF[2], off)
    push!(rowsg, ("BASEYEAR", "ais_$(COULON_BASEYEAR)_cm", off, "measured"))
end
CSV.write(joinpath(REPO, "outputs", "scope_ais_coulon_gates_$(TAG)$(SMOKE ? "_SMOKE" : "").csv"), rowsg)

## ==========================================================================
## THE CELLS
## ==========================================================================
cells = DataFrame(ssp = String[], horizon = Int[], arm = String[], label = String[],
                  tant_target = Float64[], tant_realised = Float64[],
                  gmst_pctile = Float64[], n_draws = Int[],
                  med_cm = Float64[], p05_cm = Float64[], p95_cm = Float64[],
                  spread_cm = Float64[], vs_control_med = Float64[])
@printf("\n%s\nAIS at %s, cm rel %d-%d -- AIS COMPONENT ONLY\n%s\n",
        repeat("=", 92), SSP, LADRILLO_REF[1], LADRILLO_REF[2], repeat("=", 92))
@printf("  %-6s %-8s %-22s %9s %9s %9s %9s %10s\n",
        "horiz", "arm", "label", "median", "p05", "p95", "spread", "x control")
for H in HORIZONS
    iH = yidx(H); cm = median(RES[CONTROL][:, iH])
    for (k, _, lab, tgt, pct) in ARMS
        v = RES[k][:, iH]
        g = GMST[k]; dg = g[I2300] - mean(g[IREF])
        push!(cells, (SSP, H, k, lab, tgt, dg * median(AMP), pct, length(v),
                      median(v), quantile(v, 0.05), quantile(v, 0.95),
                      quantile(v, 0.95) - quantile(v, 0.05), median(v) / cm))
        @printf("  %-6d %-8s %-22s %9.2f %9.2f %9.2f %9.2f %9.2fx\n",
                H, k, lab, median(v), quantile(v, 0.05), quantile(v, 0.95),
                quantile(v, 0.95) - quantile(v, 0.05), median(v) / cm)
    end
    println()
end
CSV.write(joinpath(REPO, "outputs", "scope_ais_coulon_cells_$(TAG)$(SMOKE ? "_SMOKE" : "").csv"), cells)

## ==========================================================================
## THE COMPARISON — the point of the whole thing
## ==========================================================================
@printf("%s\nLIKE-FOR-LIKE AT 2300: OUR AIS AT COULON'S OWN FORCING\n%s\n",
        repeat("=", 92), repeat("=", 92))
@printf("  Coulon ssp585 @2300 : %.0f to %.0f cm (5-95%%), model medians %.0f / %.0f cm\n",
        COULON_BAND[1], COULON_BAND[2], COULON_MED[1], COULON_MED[2])
let iH = yidx(2300), cmed = COULON_MED[1] / 2 + COULON_MED[2] / 2
    for (k, _, lab, tgt, pct) in ARMS
        v = RES[k][:, iH]; m = median(v)
        @printf("  %-8s %-22s median %8.2f cm = %5.2fx Coulon's %.0f cm; band [%7.2f, %7.2f] vs [%.0f, %.0f]\n",
                k, lab, m, m / cmed, cmed, quantile(v, 0.05), quantile(v, 0.95),
                COULON_BAND[1], COULON_BAND[2])
    end
    ## [WIDTH] the shipped comparison also called our band "2.4x narrower" than
    ## Coulon's and read that as over-confidence. Their width spans a 12-17 degC
    ## forcing range and ours a 5.5-7.7 degC one, so the comparison has to be
    ## remade at matched forcing before it means anything.
    cw = COULON_BAND[2] - COULON_BAND[1]
    @printf("\n  [WIDTH] Coulon's band is %.0f cm wide. Ours, per arm:\n", cw)
    for (k, _, lab, _, _) in ARMS
        v = RES[k][:, iH]; w = quantile(v, 0.95) - quantile(v, 0.05)
        @printf("     %-8s %7.1f cm = %.2fx theirs\n", k, w, w / cw)
    end

    ## The reading the shipped comparison could not make.
    m0 = median(RES[CONTROL][:, iH])
    @printf("\n  the shipped control is %.2fx Coulon's median at %.2fx their forcing;\n", m0 / cmed,
            (GMST[CONTROL][I2300] - mean(GMST[CONTROL][IREF])) * median(AMP) / 14.5)
    ## ⚠ the Coulon summary is hardcoded to the tant14 arm and is MEANINGLESS under
    ## --pathtest, whose arms are not Coulon arms (targets are NaN). Guard it rather than
    ## letting it KeyError after the table has already printed.
    if PATHTEST === nothing
        @printf("  at MATCHED forcing (tant14, T_ant %.2f vs their 12-17 degC) we are %.2fx.\n",
                (GMST["tant14"][I2300] - mean(GMST["tant14"][IREF])) * median(AMP),
                median(RES["tant14"][:, iH]) / cmed)
        ## ⚠ THE TWO DISPLACEMENTS ARE DIFFERENT QUANTITIES AND NEED NOT AGREE.
        ## diag_ais_coulon_like_for_like.py moves COULON DOWN to our forcing and gets
        ## ">= 2.14x". This moves US UP to theirs. Both are like-for-like; they measure
        ## the gap at two different points on the forcing axis, and the gap is not
        ## constant along it. Quote each with its forcing, never one as the other.
        @printf("\n  NOTE: %.2fx here is the gap AT THEIR FORCING. The >=2.14x in\n",
                median(RES["tant14"][:, iH]) / cmed)
        @printf("        diag_ais_coulon_like_for_like.py is the gap AT OURS. Different cells.\n")
    end

    ## the median path of every arm, for the figure and for re-reading without a re-run
    end
paths = DataFrame(year = Int[], arm = String[], med_cm = Float64[],
                  p05_cm = Float64[], p95_cm = Float64[])
for (k, _, _, _, _) in ARMS, (i, y) in enumerate(YRS)
    y < 1990 && continue
    v = RES[k][:, i]
    push!(paths, (y, k, median(v), quantile(v, 0.05), quantile(v, 0.95)))
end
CSV.write(joinpath(REPO, "outputs", "scope_ais_coulon_paths_$(TAG)$(SMOKE ? "_SMOKE" : "").csv"), paths)
@printf("\nwrote outputs/scope_ais_coulon_{cells,paths,gates}_%s%s.csv\n", TAG, SMOKE ? "_SMOKE" : "")
