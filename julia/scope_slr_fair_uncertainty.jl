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
##        [--chain-tag=L16] [--ton-band=LOW|MID|HIGH]
##
## --chain-tag  READ the chains from a different tag than the one outputs are named for.
##              Everything else (output names, the [CONTROL] comparison against
##              ssps_components_2300_<TAG>.csv) still keys off --tag, so a derived arm
##              cannot overwrite the arm it was derived from.
## --ton-band   Keep only post-burn draws whose `ais_runoff_Ton` falls in one band of the
##              multimodal A4 runoff-line coordinate (memory `ais_ton_multimodal`). Used to
##              ask what an arm projects CONDITIONAL on sitting in the good mode, without
##              re-running a chain. DEFAULT OFF; when off this file behaves exactly as before.
##              ⚠ Conditioning is NOT resampling: the result answers 'what do this arm's
##              in-band draws project', not 'what would a chain confined to the band find'.
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
const SSP      = let i = findfirst(a -> startswith(a, "--ssp="), ARGS)
    i === nothing ? "ssp585" : ARGS[i][7:end]
end
## THE FORCING CONVENTION IS A REAL CHOICE AND IS SWITCHABLE, NOT BAKED IN.
##  `spliced` our own path through SPLICE_YEAR, then the config's anomaly re-referenced
##           to its own LADRILLO_REF mean. Uncertainty enters the FUTURE only, so the
##           hindcast the posterior was calibrated against is untouched. DEFAULT.
##  `raw`    the config's own path throughout -- the convention the CANONICAL
##           forward-propagation pipeline used (`weight_brick_conditional_fair.jl`,
##           memory `fair_brick_coupling`), which carries each config's history too.
## Compared head-to-head because the band is being promoted to the reported one, so
## the convention must be settled by measurement rather than inherited by default.
const FORCING = let i = findfirst(a -> startswith(a, "--forcing="), ARGS)
    i === nothing ? "spliced" : ARGS[i][11:end]
end
@assert FORCING in ("spliced", "raw") "--forcing must be spliced or raw"
const SPLICE_YEAR = 2014            # build_protect_x2300_forcing.py's convention
const HORIZONS = [2100, 2150, 2300]
const Y0, Y1   = 1850, 2300
## ALL FIVE BRICK COMPONENTS PLUS THE TOTAL. Reading only :ais and :total would let
## the band be re-ranked but not DECOMPOSED, and the whole point of restoring the
## forcing spread is that it redistributes which component carries the uncertainty
## (`ais_share_was_a_fixed_driver_artifact`). The five sum to :total in BRICK
## (glaciers + GIS + AIS + TE + LWS), so [SUM] can check the decomposition closes.
const COMPONENTS = [:glaciers, :gis, :ais, :te, :lws, :total]
const SUM_PARTS = [:glaciers, :gis, :ais, :te, :lws]
const SUM_TOL_CM = 1e-6                    # an identity in BRICK; float noise only
const PAIR_SEED = 2026                     # the draw -> config permutation
const CUBE_G = joinpath(LADRILLO_OBS, "fair_cube_gmst_$(SSP)_raw.csv")
const CUBE_O = joinpath(LADRILLO_OBS, "fair_cube_ohc_$(SSP)_raw.csv")
## [SPLICE-MATCH] reference: the cube this file's predecessor spliced in python.
## Only ssp585 has one; where it exists the Julia splice must reproduce it.
const SPLICED_REF_G = joinpath(LADRILLO_OBS, "fair_cube_gmst_$(SSP)_spliced.csv")
## Tolerance DERIVED from the thing it tests (`derive_gate_from_the_thing`), not picked.
## Both cubes are written at 6 decimals => half-ulp 5e-7. The Julia splice accumulates
## three such roundings: the raw value (5e-7), the config's LADRILLO_REF mean (a mean of
## rounded values, bounded by 5e-7), and the reference cube's own rounding (5e-7).
## Worst case 1.5e-6; the gate sits just above at 2e-6. A REAL convention change would
## show up at 1e-2 or larger, so this still discriminates by ~4 orders of magnitude.
const SPLICE_MATCH_TOL = 2e-6
## [CALIB-MOVE] scale -- the AIS target's own span and sigma over 1900-2025.
const AIS_TARGET_SPAN_CM, AIS_TARGET_SIGMA_CM = 1.404, 0.141
const CALIB_WIN = (1850, 2024)
const CONTROL_TOL_CM = 0.5
## Coulon et al. 2025 Nat. Commun. 16:10385, ssp585 AIS @2300 vs 2015, cm.
## Their band spans FOUR GCMs, which is exactly why ours has to carry climate too.
const COULON_BAND, COULON_MED = (73.0, 595.0), 270.0

## Band edges: the KDE valley floors defined by scope_ais_ton_band_hindcast.jl, which is the
## SOURCE OF TRUTH. Keep in sync -- a silent divergence would make two 'MID's mean two things.
const TON_EDGE_LOW, TON_EDGE_HIGH = -18.5, -17.4
ton_band(v) = v <= TON_EDGE_LOW ? "LOW" : (v <= TON_EDGE_HIGH ? "MID" : "HIGH")
const TON_BAND = let i = findfirst(a -> startswith(a, "--ton-band="), ARGS)
    i === nothing ? "" : ARGS[i][12:end]
end
@assert TON_BAND in ("", "LOW", "MID", "HIGH") "--ton-band must be LOW, MID or HIGH"
const CHAIN_TAG = let i = findfirst(a -> startswith(a, "--chain-tag="), ARGS)
    i === nothing ? TAG : ARGS[i][13:end]
end

chain_path(sd) = joinpath(REPO, "outputs/mcmc", "chain_$(CHAIN_TAG)_seed$(sd)_n$(NITER).csv")
hdr(sd) = String.(propertynames(CSV.read(chain_path(sd), DataFrame; limit = 0)))
for sd in SEEDS; isfile(chain_path(sd)) || error("missing chain $(chain_path(sd))"); end
const VARIANT = ladrillo_gis_variant(hdr(SEEDS[1]))

## ---------------------------------------------------------------------------
## --tap  (2026-08-30). RUN THE TAPPED GREENLAND ARM.
##
## WHY THIS EXISTS. This driver had NO tap support, so it projected the UNTAPPED
## Greenland while ladrillo_model_comparison.py reports the TAPPED deliverable. The
## joint band was therefore the WRONG ARM wherever the tap fires, and 6 of 54 reported
## cells had to be held on the fixed band rather than silently lose 41.3 cm of GIS at
## ssp585/2300.
##
## THE COUPLING IS THE POINT, NOT AN INCIDENTAL. `ladrillo_set_tap!` passes `bf.gmst`
## to `update_gis3_tap!`, and in this driver `bf.gmst` is THE CONFIG'S OWN spliced path.
## So each config fires its own tap at its own date, and a config that never reaches the
## 4.69 K onset never fires it at all. That threshold crossing is exactly the kind of
## nonlinearity a mean driver cannot represent, which is the whole reason this arm exists.
## ⚠ The onset is quoted in GLOBAL temperature; update_gis3_tap! asserts this, because
## passing the amplified regional series would fire the tap ~gis_amp (1.92x) too early.
##
## OPT-IN, NOT DEFAULT. The projection driver has the tap ON by default; this one keeps
## it OFF so every previously written scope_slr_fairunc_* file keeps meaning what it said.
## ⚠ THE TAG CARRIES THE ARM, so a tapped run cannot overwrite an untapped one -- the
## same rule that scope_ais_ton_band_hindcast.jl violated and that cost a measurement.
const TAP_ON  = "--tap" in ARGS
const TAP_TAG = TAP_ON ? "_tap$(replace(string(GIS_TAP_CELL.onset_K), "." => "p"))K" *
                         "_V$(replace(string(GIS_TAP_CELL.V_m), "." => "p"))m" *
                         "_tau$(Int(GIS_TAP_CELL.tau_yr))" : ""
## The [CONTROL] arm must compare against the SHIPPED file of the SAME arm, or it would
## charge the tap as a control failure. project_ssps_components_ladrillo.jl builds the
## tapped name from the same cell fields; this mirrors it.
const SHIPPED_TAG = TAP_ON ?
    "$(TAG)_tap$(replace(string(GIS_TAP_CELL.onset_K), "." => "p"))K" *
    "_V$(replace(string(GIS_TAP_CELL.V_m), "." => "p"))m" *
    "_tau$(Int(GIS_TAP_CELL.tau_yr))_n$(Int(GIS_TAP_CELL.stages))" *
    "$(GIS_TAP_CELL.wholesheet ? "_ws" : "")" : TAG

function read_draws(sd)
    need = ladrillo_used_cols(VARIANT)
    h = hdr(sd)
    rd = ladrillo_gis_needs_native(h) ?
        vcat(setdiff(need, LADRILLO_GIS_SLOW_NATIVE_COLS),
             LADRILLO_GIS_SLOW_REPARAM_COLS) |> unique : need
    df = SMOKE ? CSV.read(chain_path(sd), DataFrame; select = rd, limit = MAXROWS) :
                 CSV.read(chain_path(sd), DataFrame; select = rd)
    nb = SMOKE ? 0 : NBURN
    ## Drop burn-in FIRST so the band filter and the stride both act on post-burn rows only.
    ## With TON_BAND == "" this is arithmetically identical to the previous
    ## `idx = (nb+1):step:nrow(df)` -- same stride, same rows.
    df = df[(nb + 1):end, :]
    if TON_BAND != ""
        keep = [ton_band(v) == TON_BAND for v in df.ais_runoff_Ton]
        nk = count(keep)
        @printf("    seed%d: %d of %d post-burn draws in T_on band %s (%.1f%%)\n",
                sd, nk, nrow(df), TON_BAND, 100nk / nrow(df)); flush(stdout)
        nk >= N_TARGET || error("--ton-band=$(TON_BAND): seed$(sd) has only $(nk) post-burn " *
              "draws in band, need $(N_TARGET). Lower n_per_chain or pick another band.")
        df = df[keep, :]
    end
    step = max(1, nrow(df) ÷ N_TARGET)
    idx = collect(1:step:nrow(df))
    d = ladrillo_native_greenland!(df[idx[1:N_TARGET], :]); df = nothing; GC.gc(); d
end

@printf("SLR WITH FaIR CLIMATE UNCERTAINTY | tag %s%s%s%s | %d draws/chain x %d chains | %s | forcing=%s\n",
        TAG, CHAIN_TAG == TAG ? "" : "  (chains from $(CHAIN_TAG))",
        TON_BAND == "" ? "" : "  [T_on band $(TON_BAND) only]",
        SMOKE ? "  ** SMOKE (--maxrows=$(MAXROWS)) **" : "", N_TARGET, length(SEEDS), SSP, FORCING)
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
const IREF = findall(y -> LADRILLO_REF[1] <= y <= LADRILLO_REF[2], YEARS)
## the shipped MEAN driver -- the control arm, and the pre-splice half of every arm
const MEAN_G = [_yearmap(joinpath(LADRILLO_OBS, "fair_mean_gmst_$(SSP).csv"), "gmst_C")[y] for y in YEARS]
const MEAN_O = [_yearmap(joinpath(LADRILLO_OBS, "fair_mean_ohc_$(SSP).csv"), "ohc_1e22J")[y] for y in YEARS]
"""Apply the forcing convention to a RAW per-config path. `spliced` pivots on the
LADRILLO_REF mean, so the level is continuous and the pre-SPLICE_YEAR half is the
shipped driver EXACTLY."""
function convention(raw::Vector{Float64}, mean_path::Vector{Float64})
    FORCING == "raw" && return raw
    mref, cref = mean(mean_path[IREF]), mean(raw[IREF])
    [y <= SPLICE_YEAR ? mean_path[i] : mref + (raw[i] - cref) for (i, y) in enumerate(YEARS)]
end
gmst_of(c) = convention(Float64.(CG[!, c]), MEAN_G)
ohc_of(c)  = convention(Float64.(CO[!, c]), MEAN_O)
const I2300 = findfirst(==(2300), YEARS)

## [SPLICE-MATCH] the Julia splice must reproduce the python-spliced cube the
## 2026-08-25 result was computed from -- otherwise "raw cube + convention in Julia"
## is a silent change of the input, not a refactor. Only ssp585 has the reference.
if FORCING == "spliced" && isfile(SPLICED_REF_G)
    R = CSV.read(SPLICED_REF_G, DataFrame)
    w = maximum(maximum(abs.(gmst_of(c) .- Float64.(R[!, c]))) for c in CFG)
    @printf("[SPLICE-MATCH] max |julia splice - python cube| = %.3e degC (tol %.0e)  %s\n",
            w, SPLICE_MATCH_TOL, w <= SPLICE_MATCH_TOL ? "PASS" : "FAIL")
    @assert w <= SPLICE_MATCH_TOL "the Julia splice does not reproduce the committed cube"
elseif FORCING == "spliced"
    @printf("[SPLICE-MATCH] no python reference for %s -- gate not applicable\n", SSP)
end

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
    # BOTH arms get the same treatment: `fixed` taps on the MEAN path (so it still
    # reproduces the shipped tapped panel) and `joint` taps on each config's OWN path.
    TAP_ON && ladrillo_set_tap!(bf)
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
run_into!(FIXED, 1:NDRAW, MEAN_G, MEAN_O)

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
const SHIPPED = CSV.read(joinpath(REPO, "outputs", "ssps_components_2300_$(SHIPPED_TAG).csv"), DataFrame)
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
## [SUM] the five components must sum to the total -- otherwise the decomposition
## that the re-ranking rests on is not a decomposition. An identity in BRICK, so
## the tolerance is float noise, and it is checked PER DRAW, not on the medians
## (medians of parts need not sum to the median of the whole).
for (arm, R) in (("fixed", FIXED), ("joint", JOINT))
    w = 0.0
    for H in HORIZONS
        i = yidx(H)
        w = max(w, maximum(abs.(sum(R[c][:, i] for c in SUM_PARTS) .- R[:total][:, i])))
    end
    @printf("  [SUM] %-5s max |sum(parts) - total| over draws x horizons = %.3e cm -> %s\n",
            arm, w, w < SUM_TOL_CM ? "PASS" : "FAIL")
    push!(rowsg, ("SUM", "$(arm)_max_cm", w, w < SUM_TOL_CM ? "PASS" : "FAIL"))
    @assert w < SUM_TOL_CM "[SUM] the components do not sum to the total for arm $arm"
end
CSV.write(joinpath(REPO, "outputs", "scope_slr_fairunc_gates_$(SSP)_$(FORCING)_$(TAG)$(TAP_TAG)$(SMOKE ? "_SMOKE" : "").csv"), rowsg)

## ==========================================================================
## THE CELLS
## ==========================================================================
## MEAN AND TIPPED FRACTION ARE CARRIED, NOT JUST THE MEDIAN. At ssp245@2300 the
## AIS tipped fraction sits at 48.3% (`diag_ais_tipping_under_forcing`), so the 50th
## percentile lands in the gap of a BIMODAL density and is sample-fragile -- the same
## failure the pulse work hit (`fair_brick_coupling`: "quote the MEAN or a
## mode-decomposition, never the bare pooled median"). The per-draw values are also
## dumped so any statistic can be recomputed later WITHOUT a re-run.
cells = DataFrame(ssp = String[], component = String[], horizon = Int[], arm = String[],
                  n_draws = Int[], med_cm = Float64[], mean_cm = Float64[],
                  p05_cm = Float64[], p95_cm = Float64[],
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
            push!(cells, (SSP, String(c), H, arm, length(v), median(v), mean(v),
                          quantile(v, 0.05), quantile(v, 0.95), sp, sp / sf,
                          median(v) / median(f)))
            @printf("  %-6s %-6d %-6s %9.2f %9.2f %9.2f %9.2f %10.2fx\n",
                    c, H, arm, median(v), quantile(v, 0.05), quantile(v, 0.95), sp, sp / sf)
        end
    end
    println()
end
CSV.write(joinpath(REPO, "outputs", "scope_slr_fairunc_cells_$(SSP)_$(FORCING)_$(TAG)$(TAP_TAG)$(SMOKE ? "_SMOKE" : "").csv"), cells)

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

## per-draw values at the horizons -- so mean / mode-decomposition / any other
## statistic can be recomputed without paying the run again.
let dr = DataFrame(draw = Int[], config = String[], component = String[],
                   horizon = Int[], arm = String[], value_cm = Float64[])
    for c in COMPONENTS, H in HORIZONS, (arm, A) in (("fixed", FIXED[c]), ("joint", JOINT[c])), k in 1:NDRAW
        push!(dr, (k, CFG_OF_DRAW[k], String(c), H, arm, A[k, yidx(H)]))
    end
    CSV.write(joinpath(REPO, "outputs", "scope_slr_fairunc_draws_$(SSP)_$(FORCING)_$(TAG)$(TAP_TAG)$(SMOKE ? "_SMOKE" : "").csv"), dr)
end

paths = DataFrame(year = Int[], component = String[], arm = String[],
                  med_cm = Float64[], p05_cm = Float64[], p95_cm = Float64[])
for c in COMPONENTS, (arm, A) in (("fixed", FIXED[c]), ("joint", JOINT[c])), (i, y) in enumerate(YEARS)
    y < 1990 && continue
    v = A[:, i]
    push!(paths, (y, String(c), arm, median(v), quantile(v, 0.05), quantile(v, 0.95)))
end
CSV.write(joinpath(REPO, "outputs", "scope_slr_fairunc_paths_$(SSP)_$(FORCING)_$(TAG)$(TAP_TAG)$(SMOKE ? "_SMOKE" : "").csv"), paths)
@printf("\nwrote outputs/scope_slr_fairunc_{cells,paths,gates}_%s_%s_%s%s%s.csv\n", SSP, FORCING, TAG, TAP_TAG, SMOKE ? "_SMOKE" : "")
