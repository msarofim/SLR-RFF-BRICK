## ============================================================================
## scope_slr_pulse_vv_brick2.jl -- THE BRICK 2.0 PULSE ARM on the van Vuuren markers
##
## STAGE 3 of the pulse comparison. Stage 1 (FaIRtoFrEDI/scripts/build_fair_pulse_vv_v160.py)
## built PAIRED baseline/pulse GMST and OHC cubes per marker; stage 2
## (`scope_slr_pulse_vv.jl`) ran LADRILLO on both. This file runs MimiBRICK **v2.0.0** on the
## SAME cubes, so the climate axis is held and the only thing that differs is the sea-level
## model. Stages 4-5 (MAGICC, FACTS) consume the same cubes for the same reason.
##
## MARCUS'S SPEC, REVISED 2026-09-04: **1 GtCO2 or 0.01 GtCH4**, pulse year 2030, on each of
## the seven van Vuuren markers, JOINT driver, against BRICK 2.0 / MAGICC / FACTS.
## ⚠ THE SIZES CHANGED, AND NOT BECAUSE OF A FLOOR. The original spec (10 GtCO2 / 1 GtCH4,
## settled 09-03) sits ABOVE the clean regime's CEILING, measured two independent ways:
##   * the L24 ladder (`diag_pulse_size_vv_ladder.jl`) put 10 GtCO2 at +20.6 % on the MEDIAN
##     at 2300, through the threshold-crossing probability;
##   * the MAGICC floor ladder (2026-09-04) found 10 GtCO2 puts 30/100 members >1 % off the
##     linear per-unit value at 2300 with SIX SIGN-FLIPS at 2100, and 1 GtCH4 puts 75/100 off
##     -- the only rung where even GMST departs. Both ends of MAGICC's clean window unify as
##     dGMST@2100 in roughly 3e-5 to 4e-4 degC; 1 GtCO2 and 0.01 GtCH4 sit inside it.
## Results carrying the OLD sizes keep the `10Gt`/`1Gt` tags and are not relabelled.
##
## ⚠ THIS ARM IS CORROBORATION, NOT INDEPENDENCE. Ladrillo descends from BRICK; the two share
## the DAIS structure, the Nauels glacier law's lineage and the same thermal-expansion form.
## What it isolates is the effect of Ladrillo's OWN changes (the freed `ais_gmst_amp`, the
## Greenland shape law and its tap, the recalibrated posterior) at held climate. A FACTS arm
## is the one that is methodologically independent.
##
## ⚠ WHY BOTH ARMS RUN IN ONE PROCESS -- the same argument as stage 2, and it binds harder
## here. The pulse response is a DIFFERENCE of two numbers that are individually ~100 cm and
## differ by ~0.05 cm. ONE model build, ONE posterior row list and ONE `ASSIGN` vector serve
## both arms, so the pairing is an IDENTITY rather than a reproduction that two processes
## "would" agree on. [PRE-PULSE-ZERO] then MEASURES the identity instead of asserting it.
##
## ⚠ THE MODEL IS BUILT ONCE, NOT ONCE PER CONFIG OR PER ARM. `MimiBRICK.get_model` is
## non-deterministic (~1e-5 m) and draws the landwater-storage sample at build time, so a
## rebuild would re-roll LWS. Building once means LWS is *literally the same vector* in both
## arms, which is why [PRE-PULSE-ZERO] can demand EXACT zero from `lws` at every year, not
## just before the pulse. `set_forcing!` mutates the built model instead.
##
## ⭐ THE LEMOINE-TRAEGER PAIR IS REQUIRED OF THIS ARM (Marcus, 2026-09-03). The reported
## headline is `P(smooth)*E[.|smooth]` and `P(fired)*E[.|fired]` as TWO numbers, never the sum
## alone and never a median: at stage 2 the tipping premium was 67-97 % of E[dAIS], so a
## median headline deletes ~90 % of the expected AIS response.
##
## ⭐⭐ BRICK 2.0'S ANTARCTIC MAP IS THE INVERSE FORM OF LADRILLO'S, AND ITS SLOPE IS FIXED.
##   BRICK 2.0 : T_ant[t] = (GMST[t-1] - ais_temperature_intercept) / ais_temperature_coefficient
##   Ladrillo  : T_ant[t] =  ais_gmst_amp * GMST[t-1] + LADRILLO_AIS_TANT0
## They are the same line -- Ladrillo's default `amp` IS 1/0.8365 and its TANT0 IS -15.42/0.8365
## -- but Ladrillo SAMPLES `ais_gmst_amp` from its posterior while BRICK 2.0 holds the slope at
## the regression value for every draw. So BRICK 2.0's crossing probability carries threshold
## uncertainty ONLY, while Ladrillo's carries threshold AND slope. That is a structural
## difference in what the two `p_fired` columns are ESTIMATES OF, and it must be said wherever
## they sit side by side. It predicts no DIRECTION on its own -- the two posteriors put
## different mass on `antarctic_temp_threshold` as well -- so the direction was MEASURED, in
## `julia/diag_gcrit_brick2_vs_ladrillo.jl`, after the sweep returned a BRICK 2.0 `p_fired`
## above Ladrillo's in all 28 cells (all-same-sign across N >> 1 gets a test, not a story).
## Putting both models' firing condition on ONE axis -- the critical GMST at which DAIS fires --
## gives, on the same draws the runs use:
##   LOCATION  median gcrit 2.313 degC (BRICK 2.0) vs 2.657 (Ladrillo): BRICK 2.0 fires 0.344 K
##             COLDER, so more of its draws sit inside the markers' 2100 range (1.64-3.32 K).
##   SPREAD    sd 0.364 vs 0.607: Ladrillo 1.67x WIDER, which is the sampled slope
##             (`ais_gmst_amp`, sd 0.173) against BRICK 2.0's fixed 1.1955.
## Both channels push the same way, and neither is a driver defect.
## ⚠ The coefficient and intercept are READ OFF THE BUILT MODEL, never typed here
## (`derived_must_mean_computed`), and [AIS-MAP-EXACT] checks the closed form against the
## model's OWN `antartic_surface_temperature` variable before any of it is used.
##
## ⚠ NO GREENLAND TAP AND NO SHAPE SMOOTHER. `[TAP-CROSSING]` has no counterpart cell here and
## says so rather than reporting a structural zero as agreement (the tap ruling: the comparator
## lacking the mechanism is the comparator's flaw, not a reason to drop it from Ladrillo). And
## with no centred 30-yr window there is no reach-back mechanism, so the identity bound is NOT
## `pulse - window/2 - 1`: it is DERIVED from the cubes' own first differing year and must
## reach the pulse year. If it does not, that is a real defect in this arm, not a smoother.
##
##   julia --project=julia_v2 julia/scope_slr_pulse_vv_brick2.jl --marker=M --specie=CO2
##        [--ndraw=2000] [--tag=B20] [--forcing=spliced|raw] [--maxrows=N] [--out-suffix=...]
##
## Writes outputs/pulse_brick2_{cells,draws,paths,gates}_vv<M>_<SPECIE>_<TAG>.csv
## in the SAME schema as pulse_ladrillo_* so one figure code path reads both models.
## ============================================================================
using CSV, DataFrames, Statistics, Printf, Mimi, MimiBRICK, Random

include(joinpath(@__DIR__, "brick_mengel.jl"))      # set_forcing! + update_brick_params!

const REPO = abspath(joinpath(@__DIR__, ".."))
const OBS  = joinpath(REPO, "data/observations")
const POST = joinpath(REPO, "data/MimiBRICK/parameters_subsample_brick.csv")

argval(flag, dflt) = let i = findfirst(a -> startswith(a, flag), ARGS)
    i === nothing ? dflt : ARGS[i][(length(flag) + 1):end]
end

const TAG     = argval("--tag=", "B20")
const MARKER  = argval("--marker=", "")
const SPECIE  = argval("--specie=", "CO2")
const FORCING = argval("--forcing=", "spliced")
const MAXROWS = let v = argval("--maxrows=", ""); v == "" ? nothing : parse(Int, v); end
const SMOKE   = MAXROWS !== nothing
## ⚠ OUT-SUFFIX EXISTS BECAUSE A MUTATION RUN ONCE CLOBBERED THE CANONICAL TABLE
## (`gate_reads_its_own_output`, in the OUTPUT direction). Any non-production variant of this
## driver must pass one; `outputs/*_MUT*.csv` is gitignored for the same incident.
const OUTSUF_ARG = argval("--out-suffix=", "")
## ⚠ MUTATION HARNESS. A gate that passes is not a gate that WORKS -- each mode below breaks
## exactly what one gate guards, and that gate must FAIL. The output of a mutated run is
## DELIBERATELY WRONG, so it is forced into a `_MUT*` filename, which `.gitignore` drops.
##   --mutate=lag      closed-form T_ant reads GMST[t], not GMST[t-1]  -> [AIS-MAP-EXACT] FAILS
##   --mutate=rebuild  rebuilds the model between arms (re-rolls LWS)  -> [LWS-EXACT-ZERO] FAILS
##   --mutate=shuffle  permutes the pulsed arm's config assignment     -> [DRAW-PAIRING]   FAILS
## MEASURED 2026-09-04 on vvM/CO2, and the DISCRIMINATING gate is named for each:
##   lag      [AIS-MAP-EXACT] 3.386e-01 degC FAIL, and it fails ALONE.
##   rebuild  [LWS-EXACT-ZERO] 1.183e+00 cm FAIL (+ [PRE-PULSE-ZERO] 1.694e-01, expected --
##            an unseeded rebuild perturbs every component, not only LWS). [DRAW-PAIRING] PASSES,
##            which is what makes LWS-EXACT-ZERO the discriminating one.
##   shuffle  [DRAW-PAIRING] 100/100 FAIL, + [PRE-PULSE-ZERO] 2.319 cm -- see the note on that
##            gate's power below; unlike stage 2's, this one is NOT blind to a config swap.
const MUTATE = argval("--mutate=", "")
@assert MUTATE in ("", "lag", "rebuild", "shuffle") "--mutate must be lag, rebuild or shuffle"
MUTATE == "" || @printf("\n  ** MUTATION TEST ACTIVE: --mutate=%s -- OUTPUT IS DELIBERATELY WRONG **\n\n", MUTATE)
const OUTSUF = OUTSUF_ARG * (MUTATE == "" ? "" : "_MUT$(uppercase(MUTATE))")

## THE SEVEN MARKERS, in van Vuuren's own order. Named here so an unrecognised marker FAILS
## LOUDLY at argument parse rather than as a missing-file error minutes into setup.
const MARKERS = ["VL", "L", "LN", "ML", "M", "HL", "H"]
@assert MARKER in MARKERS "--marker must be one of $(MARKERS); got '$(MARKER)'"
@assert FORCING in ("spliced", "raw") "--forcing must be spliced or raw"

## ⚠ UNITS ARE THE 1000x CLASS OF ERROR. These strings are not cosmetic -- they are the
## filename the FaIR stage wrote, and they encode the pulse SIZE that every per-tonne number
## downstream divides by. ONE table, so the divisor can never drift from the cube's own name.
const SPECIE_SPEC = Dict(
    "CO2" => (size_tag = "10Gt", pulse_Gt = 10.0, unit = "GtCO2"),
    "CH4" => (size_tag = "1Gt",  pulse_Gt = 1.0,  unit = "GtCH4"))
@assert haskey(SPECIE_SPEC, SPECIE) "--specie must be CO2 or CH4; got '$(SPECIE)'"
## ⚠ THE SIZE AND THE TAG MOVE TOGETHER OR NOT AT ALL, exactly as in the FaIR stage
## (`FaIRtoFrEDI/scripts/build_fair_pulse_vv_v160.py --pulse-size`). The tag is the cube
## FILENAME this driver opens AND the per-tonne divisor it reports, so both are rewritten from
## ONE number. The label construction mirrors the Python side character for character --
## `f"{g:g}".replace(".", "p") + "Gt"` -- because a tag that differs by one character opens a
## file that does not exist, or worse, opens the WRONG size's cube.
const PULSE_SIZE = let v = argval("--pulse-size=", ""); v == "" ? nothing : parse(Float64, v) end
PULSE_SIZE === nothing || PULSE_SIZE > 0 || error("--pulse-size must be > 0; got $(PULSE_SIZE)")
const SPEC = let s = SPECIE_SPEC[SPECIE]
    PULSE_SIZE === nothing ? s :
        (size_tag = replace(@sprintf("%g", PULSE_SIZE), "." => "p") * "Gt",
         pulse_Gt = PULSE_SIZE, unit = s.unit)
end
PULSE_SIZE === nothing ||
    @printf("  ** --pulse-size %g -> size tag %s, divisor %g %s **\n",
            PULSE_SIZE, SPEC.size_tag, SPEC.pulse_Gt, SPEC.unit)
const PULSE_YEAR = 2030

## ⚠ CH4 IS NOT A SMALL PERTURBATION and the FaIR stage measured it: 1 GtCH4 = 260 % of one
## year's CH4 emission at 2030, and the DOUBLING gate came back 2.0332, i.e. measurably
## SUPERLINEAR. CO2 is 26 % of a year and doubles at 1.9999. Source: FaIRtoFrEDI
## scripts/build_fair_pulse_vv_v160.py gate output 2026-09-03; NOT a literature constant.
const FAIR_DOUBLING = Dict("CO2" => 1.9999, "CH4" => 2.0332)

const HORIZONS   = [2100, 2150, 2300]
const Y0, Y1     = 1850, 2300
const YEARS      = collect(Y0:Y1)
const BASE0, BASE1 = 1995, 2014          # AR6 SLR reference, = LADRILLO_REF, = oldbrick's
const SPLICE_YEAR  = 2014                # build_protect_x2300_forcing.py's convention
const SEED       = 2026                  # get_model non-determinism + LWS; oldbrick's seed
const PAIR_SEED  = 2026                  # draw -> config permutation; Ladrillo's seed
const NDRAW_REQ  = parse(Int, something(argval("--ndraw=", nothing), "2000"))
const BUILD_SSP  = "ssp245"              # see scope_slr_fairunc_oldbrick.jl:122 for why
const COMPONENTS = [:glaciers, :gis, :ais, :te, :lws, :total]
const SUM_PARTS  = [:glaciers, :gis, :ais, :te, :lws]
const SUM_TOL_CM = 1e-6                  # an identity in BRICK; float noise only
const ARMS = ["base", "pulse"]

const IB   = [findfirst(==(y), YEARS) for y in BASE0:BASE1]
const IREF = IB
yidx(y) = findfirst(==(y), YEARS)
reref(v) = 100 .* (v .- sum(v[IB]) / length(IB))    # m -> cm, rel 1995-2014

cube(kind, arm) = joinpath(OBS,
    "fair_cube_$(kind)_vv$(MARKER)_$(arm == "base" ? "pulsebase" : "pulse")_" *
    "$(SPECIE)_$(SPEC.size_tag)_$(PULSE_YEAR)_raw.csv")
for k in ("gmst", "ohc"), a in ARMS
    isfile(cube(k, a)) || error("missing cube $(cube(k, a))\n  build it with " *
        "FaIRtoFrEDI/scripts/build_fair_pulse_vv_v160.py --marker=$(MARKER) --specie=$(SPECIE)")
end

const OUTSTEM = "vv$(MARKER)_$(SPECIE)_$(SPEC.size_tag)_$(PULSE_YEAR)_$(FORCING)_$(TAG)" *
                "$(SMOKE ? "_SMOKE" : "")$(OUTSUF)"

@printf("BRICK 2.0 PULSE ARM | marker vv%s | %s pulse %.0f %s at %d | tag %s%s\n",
        MARKER, SPECIE, SPEC.pulse_Gt, SPEC.unit, PULSE_YEAR, TAG,
        SMOKE ? "  ** SMOKE (--maxrows=$(MAXROWS)) **" : "")
@printf("  sea level: MimiBRICK v2.0.0 (`precip_log` shim), published posterior subsample\n")
@printf("  climate:   FaIR 2.2.4 calib 1.6.0 + CMIP7, marker forcing volcanic_solar_%s.csv, forcing=%s\n",
        MARKER, FORCING)
flush(stdout)

## ---- the paired climate cubes --------------------------------------------
const CG = Dict(a => CSV.read(cube("gmst", a), DataFrame) for a in ARMS)
const CO = Dict(a => CSV.read(cube("ohc",  a), DataFrame) for a in ARMS)
const CFG = [c for c in String.(propertynames(CG["base"])) if startswith(c, "cfg_")]
const NCFG = length(CFG)
for a in ARMS
    Int.(CG[a].year) == YEARS || error("$(basename(cube("gmst", a))) year axis is not $(Y0):$(Y1)")
    Int.(CO[a].year) == YEARS || error("$(basename(cube("ohc",  a))) year axis is not $(Y0):$(Y1)")
end
## ⚠ THE CONFIG ORDER MUST MATCH ACROSS ARMS, not merely the config SET. `cfg_017` being
## column 3 in one file and column 9 in the other would leave every gate here passing while
## every difference was between two different climates. Equality of the ORDERED vectors is
## the check; `issetequal` would be blind to exactly the failure that matters.
for a in ARMS, (k, D) in (("gmst", CG), ("ohc", CO))
    cs = [c for c in String.(propertynames(D[a])) if startswith(c, "cfg_")]
    cs == CFG || error("[CUBE-ALIGN] $(k)/$(a) config ORDER differs from gmst/base")
end

## ONE mean driver, the marker's own, SHARED by both arms: the splice pivots on the 1995-2014
## mean and the two cubes are identical there, so `cref` and `mref` are equal across arms and
## the splice cannot manufacture a difference.
_yrmap(path, col) = (d = CSV.read(path, DataFrame);
                     Dict(Int(d[i, "year"]) => Float64(d[i, col]) for i in 1:nrow(d)))
const MEAN_G = let m = _yrmap(joinpath(OBS, "fair_mean_gmst_vv$(MARKER).csv"), "gmst_C"); [m[y] for y in YEARS]; end
const MEAN_O = let m = _yrmap(joinpath(OBS, "fair_mean_ohc_vv$(MARKER).csv"),  "ohc_1e22J"); [m[y] for y in YEARS]; end

function convention(raw::Vector{Float64}, mean_path::Vector{Float64})
    FORCING == "raw" && return raw
    mref, cref = mean(mean_path[IREF]), mean(raw[IREF])
    [y <= SPLICE_YEAR ? mean_path[i] : mref + (raw[i] - cref) for (i, y) in enumerate(YEARS)]
end
gmst_of(a, c) = convention(Float64.(CG[a][!, c]), MEAN_G)
ohc_of(a, c)  = convention(Float64.(CO[a][!, c]), MEAN_O)

## ---- [CUBE-PREPULSE] the identity horizon, DERIVED FROM THE CUBES --------
## Stage 2's bound is `PULSE_YEAR - shape_window/2 - 1` because Ladrillo's Greenland law reads
## a centred 30-yr mean. BRICK 2.0 has NO smoother, so that derivation does not transfer and
## copying its NUMBER would be a bound that no longer matches its claim
## (`gate_bound_matches_its_claim`). Instead the horizon is MEASURED off the forcing itself:
## the last year at which every config's baseline and pulsed drivers are bitwise identical.
## Everything downstream of an identical driver must itself be identical, in every component.
const CUBE_FIRST_DIFF = let first = nothing
    for c in CFG, (a, b) in ((CG["base"][!, c], CG["pulse"][!, c]), (CO["base"][!, c], CO["pulse"][!, c]))
        j = findfirst(i -> Float64(a[i]) != Float64(b[i]), 1:length(YEARS))
        j === nothing && continue
        (first === nothing || j < first) && (first = j)
    end
    first === nothing && error("[CUBE-PREPULSE] the two arms' cubes are IDENTICAL EVERYWHERE -- " *
                               "there is no pulse in these files.")
    YEARS[first]
end
const IDENT_LAST = CUBE_FIRST_DIFF - 1
@printf("  [CUBE-PREPULSE] the arms' drivers first differ at %d over all %d configs\n",
        CUBE_FIRST_DIFF, NCFG)
@printf("                  => identity horizon DERIVED = %d (no smoother in BRICK 2.0, so it\n", IDENT_LAST)
@printf("                     must reach the pulse year %d; stage 2's %d bound is Ladrillo's\n",
        PULSE_YEAR, PULSE_YEAR - 15 - 1)
@printf("                     30-yr shape window and does NOT transfer here)\n")
IDENT_LAST >= PULSE_YEAR - 1 ||
    error("[CUBE-PREPULSE] the drivers differ at $(CUBE_FIRST_DIFF), BEFORE the pulse year " *
          "$(PULSE_YEAR). BRICK 2.0 has no reach-back mechanism to explain that.")

## ---- posterior: thinned, and the shipped thinning is a SUBSET ------------
## ⚠ `STEPP` reproduces `scope_slr_fairunc_oldbrick.jl`'s thinning rule exactly. At the
## default --ndraw=2000 the step is 5, and the shipped 1000-draw panel's step-10 rows are a
## strict SUBSET of these -- so this run neither re-rolls nor re-orders the published panel.
const post  = CSV.read(POST, DataFrame)
const STEPP = max(1, nrow(post) ÷ NDRAW_REQ)
const ROWS  = SMOKE ? collect(1:STEPP:nrow(post))[1:min(MAXROWS, length(1:STEPP:nrow(post)))] :
                      collect(1:STEPP:nrow(post))
const NDRAW = length(ROWS)
@printf("  posterior: %d draws (every %d of %d rows) x %d FaIR configs\n",
        NDRAW, STEPP, nrow(post), NCFG); flush(stdout)

## ---- the pairing: ONE assignment, both arms ------------------------------
const ASSIGN = let rng = MersenneTwister(PAIR_SEED)
    a = Int[]
    while length(a) < NDRAW; append!(a, randperm(rng, NCFG)); end
    a[1:NDRAW]
end
const CFG_OF_DRAW = [CFG[i] for i in ASSIGN]
## Both arms read this map. `--mutate=shuffle` gives the pulsed arm a DIFFERENT one, which is
## exactly the failure [DRAW-PAIRING] exists to catch and which [PRE-PULSE-ZERO] is blind to.
const CFG_OF_DRAW_ARM = Dict(
    "base"  => CFG_OF_DRAW,
    "pulse" => MUTATE == "shuffle" ? CFG_OF_DRAW[shuffle(MersenneTwister(7), 1:NDRAW)] : CFG_OF_DRAW)

## ---- the model: built ONCE, mutated per arm ------------------------------
Random.seed!(SEED)
## NOT `const`: `--mutate=rebuild` reassigns it deliberately. Production never does.
M = MimiBRICK.get_model(ssprcp_scenario = BUILD_SSP, start_year = Y0, end_year = Y1)
## Mimi builds the model instance lazily, so a parameter cannot be READ until the model has
## been run once. This first run is on MimiBRICK's own default forcing and is discarded --
## `run_into!` overwrites every parameter it reads before any result is stored.
run(M)
## Read the Antarctic map OFF THE BUILT MODEL. Typing 0.8365 / 15.42 here would be a COPY of a
## number that lives in MimiBRICK and can move under a package bump (`derived_must_mean_computed`).
const AIS_COEF = Float64(M[:antarctic_icesheet, :ais_temperature_coefficient])
const AIS_INT  = Float64(M[:antarctic_icesheet, :ais_temperature_intercept])
AIS_COEF > 0 || error("ais_temperature_coefficient = $(AIS_COEF) <= 0; the closed-form crossing " *
                      "map below assumes T_ant is INCREASING in GMST and would invert silently.")
@printf("  AIS map (read off the build): T_ant[t] = (GMST[t-1] - %.4f) / %.4f  -- slope FIXED,\n",
        AIS_INT, AIS_COEF)
@printf("            not sampled; Ladrillo frees the same slope as `ais_gmst_amp`.\n")
flush(stdout)

## What each arm ACTUALLY ran, per draw, recorded at the call site. [DRAW-PAIRING] reads these
## back; without them the pairing claim rests on ASSIGN being used twice, which is the
## assumption this whole file exists to avoid making.
const RAN_CFG = Dict(a => fill("", NDRAW) for a in ARMS)
const RAN_ROW = Dict(a => fill(-1, NDRAW) for a in ARMS)

alloc() = Dict(c => Matrix{Float64}(undef, NDRAW, length(YEARS)) for c in COMPONENTS)

"""Run draw indices `ks` on forcing (g,o); write the FULL year axis into `store`."""
function run_into!(store, ks, g, o, arm, cfgname)
    set_forcing!(M, g, o)
    for k in ks
        update_brick_params!(M, post[ROWS[k], :]; precip_log = true)
        run(M)
        RAN_CFG[arm][k] = cfgname
        RAN_ROW[arm][k] = k
        ais  = Float64.(reref(M[:antarctic_icesheet,     :ais_sea_level]))
        gsic = Float64.(reref(M[:glaciers_small_icecaps, :gsic_sea_level]))
        gis  = Float64.(reref(M[:greenland_icesheet,     :greenland_sea_level]))
        te   = Float64.(reref(M[:thermal_expansion,      :te_sea_level]))
        lws  = Float64.(reref(M[:landwater_storage,      :lws_sea_level]))
        store[:ais][k, :] = ais; store[:glaciers][k, :] = gsic; store[:gis][k, :] = gis
        store[:te][k, :]  = te;  store[:lws][k, :] = lws
        store[:total][k, :] = ais .+ gsic .+ gis .+ te .+ lws
    end
end

const RES = Dict(a => alloc() for a in ARMS)
let groups = Dict{String, Vector{Int}}()
    for k in 1:NDRAW; push!(get!(groups, CFG_OF_DRAW[k], Int[]), k); end
    @printf("\n  %d draws over %d configs; running BOTH arms per config ...\n",
            NDRAW, length(groups)); flush(stdout)
    n = 0
    t0 = time()
    for (c, idx) in groups
        ## Both arms for THIS config back to back, so a drift in any global model state shows
        ## up in [PRE-PULSE-ZERO] instead of cancelling between arms.
        for a in ARMS
            ## Under --mutate=shuffle each draw's PULSED config is whatever the permuted map
            ## says, so the two arms genuinely see different climates for the same draw.
            for k in idx
                cc = CFG_OF_DRAW_ARM[a][k]
                ## Deliberately NOT reseeded -- an unseeded rebuild is the actual defect
                ## [LWS-EXACT-ZERO] guards, and a reseeded one would re-roll LWS to the SAME
                ## vector and mutate nothing (the first version of this harness did exactly
                ## that and every gate passed: a mutation that changes no output is not a test).
                MUTATE == "rebuild" && (global M = MimiBRICK.get_model(ssprcp_scenario = BUILD_SSP,
                                                   start_year = Y0, end_year = Y1); run(M))
                run_into!(RES[a], [k], gmst_of(a, cc), ohc_of(a, cc), a, cc)
            end
        end
        n += 1
        n % 100 == 0 && (@printf("    %d/%d configs  (%.1f min)\n", n, length(groups),
                                 (time() - t0) / 60); flush(stdout))
    end
    @printf("    done, %.1f min\n", (time() - t0) / 60); flush(stdout)
end

const DIFF = Dict(c => RES["pulse"][c] .- RES["base"][c] for c in COMPONENTS)

## ==========================================================================
## GATES
## ==========================================================================
@printf("\n%s\nGATES\n%s\n", repeat("=", 92), repeat("=", 92))
rowsg = DataFrame(gate = String[], key = String[], value = Float64[], verdict = String[])
push_g!(g, k, v, ok) = push!(rowsg, (g, k, Float64(v), ok ? "PASS" : "FAIL"))
push_g!("CUBE-PREPULSE", "first_diff_year", CUBE_FIRST_DIFF, CUBE_FIRST_DIFF >= PULSE_YEAR)
push_g!("CUBE-PREPULSE", "ident_last_year", IDENT_LAST, IDENT_LAST >= PULSE_YEAR - 1)

## [AIS-MAP-EXACT] the closed form used by [AIS-CROSSING] below, checked against the MODEL'S
## OWN `antartic_surface_temperature` variable on the last draw actually run. Without this the
## crossing classifier is an assertion about MimiBRICK's internals; with it, it is measured.
## Bound is EXACT equality: both sides are the same two floating-point operations.
let Tm = Float64.(M[:antarctic_icesheet, :antartic_surface_temperature][2:end]),
    g  = MUTATE == "lag" ? Float64.(M[:antarctic_icesheet, :global_surface_temperature][2:end]) :
                           Float64.(M[:antarctic_icesheet, :global_surface_temperature][1:(end - 1)]),
    Tc = (g .- AIS_INT) ./ AIS_COEF,
    w  = maximum(abs.(Tm .- Tc))
    @printf("  [AIS-MAP-EXACT] max |model T_ant - closed form| = %.3e degC (bound EXACT 0)  %s\n",
            w, w == 0.0 ? "PASS" : "FAIL")
    @printf("                  also confirms the GMST[t-1] LAG: a GMST[t] form would fail here.\n")
    push_g!("AIS-MAP-EXACT", "max_abs_degC", w, w == 0.0)
    w == 0.0 || MUTATE != "" || error("[AIS-MAP-EXACT] the closed-form Antarctic map does not reproduce the model's " *
                      "own variable; the crossing classifier below would be measuring something else.")
end

## ---------------------------------------------------------------------------
## THE IDENTITY GATES.
##
## ⚠ THE POWER OF THIS ZERO GATE, said out loud (`no_power_null`) -- AND IT DIFFERS FROM
## STAGE 2'S. In `scope_slr_pulse_vv.jl` the identity window ends at 2014, entirely inside the
## region where the spliced path IS the config-independent mean driver, so that gate is BLIND
## to a config mis-pairing. Here the window runs to 2030, i.e. SIXTEEN YEARS PAST THE SPLICE,
## where each config carries its own anomaly -- so this gate does have power against a config
## mis-pairing, and `--mutate=shuffle` measures it: 2.319 cm, a clear FAIL. It also has power
## against a posterior-draw mis-pairing and against state leaking between the two
## `set_forcing!` calls. [DRAW-PAIRING] still certifies the pairing structurally rather than
## by consequence, because a gate that catches a fault only through its downstream effect
## cannot say WHICH fault it caught.
let iy = yidx(IDENT_LAST), worst = 0.0
    for c in COMPONENTS
        m = maximum(abs.(@view DIFF[c][:, 1:iy]))
        worst = max(worst, m)
        push_g!("PRE-PULSE-ZERO", "max_abs_cm_$(c)", m, m == 0.0)
    end
    @printf("  [PRE-PULSE-ZERO] max |pulse - base| over %d-%d = %.3e cm, all %d components (bound EXACT 0)  %s\n",
            Y0, IDENT_LAST, worst, length(COMPONENTS), worst == 0.0 ? "PASS" : "FAIL")
    worst == 0.0 || MUTATE != "" || error("[PRE-PULSE-ZERO] the arms differ while their drivers are still identical; " *
                          "the difference is not a pulse response. Do not use these outputs.")
end

## [LWS-EXACT-ZERO] the one component with NO temperature or sea-level input at all. It is a
## fixed random vector drawn ONCE at build time, so it must be identical in both arms at EVERY
## year, not merely before the pulse -- a stronger claim than [PRE-PULSE-ZERO] can make, and it
## is the check that would catch a per-arm model rebuild.
let w = maximum(abs.(DIFF[:lws]))
    @printf("  [LWS-EXACT-ZERO] max |pulse - base| over ALL years = %.3e cm (bound EXACT 0)  %s\n",
            w, w == 0.0 ? "PASS" : "FAIL")
    push_g!("LWS-EXACT-ZERO", "max_abs_cm", w, w == 0.0)
    w == 0.0 || MUTATE != "" || error("[LWS-EXACT-ZERO] landwater storage moved under a pulse it cannot see; the " *
                      "model was rebuilt between arms and LWS was re-rolled.")
end

## [DRAW-PAIRING] the pairing certified by what the arms RECORDED, not by one ASSIGN vector
## being read twice. `recorded_but_never_restored` is the failure this closes.
let bad = count(k -> RAN_CFG["base"][k] != RAN_CFG["pulse"][k], 1:NDRAW),
    badr = count(k -> RAN_ROW["base"][k] != RAN_ROW["pulse"][k], 1:NDRAW)
    @printf("  [DRAW-PAIRING] %d/%d draws saw a different CONFIG across arms, %d a different DRAW ROW  %s\n",
            bad, NDRAW, badr, (bad == 0 && badr == 0) ? "PASS" : "FAIL")
    push_g!("DRAW-PAIRING", "config_mismatches", bad, bad == 0)
    push_g!("DRAW-PAIRING", "row_mismatches", badr, badr == 0)
    (bad == 0 && badr == 0) || MUTATE != "" || error("[DRAW-PAIRING] the arms are not paired; every difference is noise.")
end

## [PAIRING] balance, and that the assigned forcing sample is not a biased draw from the cube.
let used = length(unique(CFG_OF_DRAW)),
    cnt = [count(==(c), CFG_OF_DRAW) for c in unique(CFG_OF_DRAW)],
    i23 = yidx(2300),
    drawn = [gmst_of("base", c)[i23] - mean(gmst_of("base", c)[IREF]) for c in CFG_OF_DRAW],
    all_  = [gmst_of("base", c)[i23] - mean(gmst_of("base", c)[IREF]) for c in CFG]
    @printf("  [PAIRING] %d of %d configs used, each %d-%d times (seed %d), ONE assignment for both arms\n",
            used, NCFG, minimum(cnt), maximum(cnt), PAIR_SEED)
    d = abs(median(drawn) - median(all_))
    push_g!("PAIRING", "configs_used", used, used == min(NCFG, NDRAW))
    push_g!("PAIRING", "median_dgmst_bias_degC", d, d < 0.1)
    @printf("            median dGMST@2300 bias vs whole cube = %.4f degC (tol 0.1)  %s\n",
            d, d < 0.1 ? "PASS" : "CHECK")
end

## [SUM] the five components must still sum to the total IN THE DIFFERENCE. Differencing is
## linear, so this carries the parent identity through -- and it is the cheapest way to catch a
## component matrix written to the wrong arm's slot.
let worst = 0.0
    for H in HORIZONS
        s = sum(DIFF[c][:, yidx(H)] for c in SUM_PARTS)
        worst = max(worst, maximum(abs.(s .- DIFF[:total][:, yidx(H)])))
    end
    @printf("  [SUM] max |sum(parts) - total| in the DIFFERENCE = %.3e cm (tol %.0e)  %s\n",
            worst, SUM_TOL_CM, worst <= SUM_TOL_CM ? "PASS" : "FAIL")
    push_g!("SUM", "max_abs_cm", worst, worst <= SUM_TOL_CM)
end

## [SIGN] a positive emission pulse warms, and BRICK's TOTAL is increasing in warming, so the
## paired difference should be >= 0. Gated on `total` only, and reported as a FRACTION rather
## than gated hard, for two separate reasons:
##   * a draw that crosses the DAIS threshold in one arm only makes the response lumpy -- still
##     positive, but no longer smooth -- and a hard sign gate would then be measuring the
##     threshold rather than the pulse;
##   * ⚠ AIS ALONE IS NOT MONOTONE. DAIS's accumulation term is `precipitation0 * exp(kappa*T_ant)`,
##     so warming ADDS snowfall, and before the disintegration term takes over a pulse can lower
##     the Antarctic contribution. Measured here: the AIS paired median at 2100 is slightly
##     NEGATIVE on vvM/CO2. That is the model's own physics, not a pairing defect -- a per-component
##     sign gate would fire on it forever (`gate_bound_matches_its_claim`).
for H in HORIZONS
    v = DIFF[:total][:, yidx(H)]
    neg = count(<(0.0), v) / length(v)
    @printf("  [SIGN] %d: median %+.5f cm, %.2f%% of draws negative  %s\n",
            H, median(v), 100neg, median(v) > 0 ? "PASS" : "FAIL")
    push_g!("SIGN", "median_cm_$(H)", median(v), median(v) > 0)
    push_g!("SIGN", "frac_negative_$(H)", neg, true)
end

## [TAP-CROSSING] NO COUNTERPART CELL. Stage 2's Ladrillo arm runs a TAPPED Greenland and
## counts the draws that cross its onset only when pulsed. BRICK 2.0 has no tap at all, so the
## honest report is "the mechanism is absent", NOT a zero that a reader could mistake for
## "measured, and it never fires" (`two_statistics_can_be_blind`). Per Marcus's tap ruling
## (2026-09-03) the comparator lacking the mechanism is the comparator's flaw; it is not a
## reason to drop the tap from Ladrillo's arm to make the columns match.
@printf("  [TAP-CROSSING] NO COUNTERPART -- BRICK 2.0 has no Greenland tap mechanism.\n")
@printf("                 Not a measured zero. Say this in any caption that puts the two arms\n")
@printf("                 side by side (Marcus's tap ruling, 2026-09-03).\n")
push_g!("TAP-CROSSING", "mechanism_present", 0, true)

## ---------------------------------------------------------------------------
## [AIS-CROSSING] the Antarctic hard annual step, ported from stage 2.
##
## DAIS fires on a HARD ANNUAL STEP at the full rate regardless of how far above
## (antarctic_icesheet_component.jl:180 in MimiBRICK v2.0.0). Stage 2 measured what that does:
## mean(integer years charged) / mean(continuous measure of {t : T_ant(t) > thr}) = 0.917-1.039
## over 42 cells -- an UNBIASED randomisation that inflates the per-draw sd up to 8.8x. ~1 means
## the mean is a SAMPLE-SIZE question; away from 1 means the step biases the expectation and no
## ensemble size fixes it. This arm re-measures it on BRICK 2.0's own map.
##
## Three channels: SMOOTH (same integer year count in both arms), QUANTIZATION (crosses in both,
## count differs) and BIFURCATION (never at baseline, crosses under the pulse).
AIS_FIRED = Dict{Int, Vector{Bool}}()
AIS_PFULL = Dict{Int, Float64}()
let thr = [Float64(post[ROWS[k], :antarctic_temp_threshold]) for k in 1:NDRAW]
    tant(a, k) = let g = gmst_of(a, CFG_OF_DRAW[k])
        T = Vector{Float64}(undef, length(YEARS)); T[1] = -Inf
        lag = MUTATE == "lag" ? 0 : 1        # --mutate=lag reads GMST[t]; [AIS-MAP-EXACT] must FAIL
        @inbounds for t in 2:length(YEARS); T[t] = (g[t - lag] - AIS_INT) / AIS_COEF; end; T
    end
    nyr(T, t0, iH) = count(>(t0), @view T[2:iH])
    ## the continuous measure -- NOT the first-crossing advance. On a peak-and-decline marker
    ## the pulse buys time at BOTH ends of the above-threshold window, so the entry-side advance
    ## understates it ~2x and over-attributes the rest to discretization.
    function tabove(T, t0, iH)
        sacc = 0.0
        @inbounds for t in 3:iH
            a, b = T[t - 1], T[t]
            if a > t0 && b > t0;        sacc += 1.0
            elseif a <= t0 && b > t0;   sacc += (b - t0) / (b - a)
            elseif a > t0 && b <= t0;   sacc += (a - t0) / (a - b)
            end
        end
        sacc
    end
    TB = [tant("base", k) for k in 1:NDRAW]; TP = [tant("pulse", k) for k in 1:NDRAW]

    ## ⭐ P(fired) RAO-BLACKWELLISED OVER THE FULL CROSS-PRODUCT, FOR FREE.
    ## Stage 2 measured that a median 53 % of the AIS mean's Monte Carlo variance is carried by
    ## P(fired) ALONE. And P needs no model run: AIS_COEF > 0, so
    ##     T_ant[t] > thr   <=>   GMST[t-1] > AIS_INT + AIS_COEF * thr
    ## turns the classification into a threshold on the CONFIG'S OWN GMST, one `gcrit` per draw.
    ## Sorting each config's window once makes the year count a binary search, so P is evaluated
    ## on all NDRAW x NCFG pairings -- NCFG times the sample the paired run sees -- in seconds.
    ## ⚠ Valid ONLY because the draw->config permutation is UNIFORM over configs, so the paired
    ## sample is an unbiased sample of the very cross-product P is computed on.
    ## ⚠ BRICK 2.0's `gcrit` varies ONLY through `thr`; Ladrillo's varies through `thr` AND the
    ## sampled slope. Expect a TIGHTER p_fired here for that structural reason.
    gcrit = [AIS_INT + AIS_COEF * thr[k] for k in 1:NDRAW]
    GS = Dict(a => Dict(c => gmst_of(a, c) for c in CFG) for a in ARMS)
    nabove(sorted, g0) = length(sorted) - searchsortedlast(sorted, g0)
    P_FULL = Dict{Int, Float64}()
    for H in HORIZONS
        iH = yidx(H)
        sb = Dict(c => sort(GS["base"][c][1:(iH - 1)]) for c in CFG)
        sp = Dict(c => sort(GS["pulse"][c][1:(iH - 1)]) for c in CFG)
        nfire = 0
        for c in CFG, k in 1:NDRAW
            nabove(sb[c], gcrit[k]) != nabove(sp[c], gcrit[k]) && (nfire += 1)
        end
        P_FULL[H] = nfire / (NCFG * NDRAW)
    end

    for H in HORIZONS
        iH = yidx(H)
        nb = [nyr(TB[k], thr[k], iH) for k in 1:NDRAW]; np = [nyr(TP[k], thr[k], iH) for k in 1:NDRAW]
        sb = [tabove(TB[k], thr[k], iH) for k in 1:NDRAW]; sp = [tabove(TP[k], thr[k], iH) for k in 1:NDRAW]
        bif = [nb[k] == 0 && np[k] > 0 for k in 1:NDRAW]
        fired = [nb[k] != np[k] for k in 1:NDRAW]
        pf = count(fired) / NDRAW
        mdn = mean(Float64.(np .- nb)); mds = mean(sp .- sb)
        @printf("  [AIS-CROSSING] %d: fired %d/%d (%.2f%%)  bifurcation %d  int/cont %.4f\n",
                H, count(fired), NDRAW, 100pf, count(bif), mds == 0 ? NaN : mdn / mds)
        push_g!("AIS-CROSSING", "n_fired_$(H)", count(fired), true)
        push_g!("AIS-CROSSING", "n_bifurcation_$(H)", count(bif), true)
        push_g!("AIS-CROSSING", "p_fired_$(H)", pf, true)
        push_g!("AIS-CROSSING", "int_over_cont_$(H)", mds == 0 ? NaN : mdn / mds, true)
        ## [P-FIRED-CONSISTENT] an ORDERING between two MEASURED quantities, not a chosen
        ## tolerance (`threshold_from_obs_or_law`): the paired sample's P must sit within 3 of
        ## its OWN binomial standard errors of the exact cross-product value. It is a check on
        ## the PAIRING, since a mis-permuted draw->config map biases the paired P while leaving
        ## the exact one untouched.
        let se = sqrt(max(P_FULL[H] * (1 - P_FULL[H]), eps()) / NDRAW), z = abs(pf - P_FULL[H]) / se
            @printf("      P(fired) paired %.4f  vs exact %.4f over %d pairings  z=%.2f  %s\n",
                    pf, P_FULL[H], NCFG * NDRAW, z, z <= 3 ? "PASS" : "FAIL")
            push_g!("P-FIRED-CONSISTENT", "p_fired_exact_$(H)", P_FULL[H], z <= 3)
            push_g!("P-FIRED-CONSISTENT", "z_$(H)", z, z <= 3)
        end
        AIS_FIRED[H] = fired
        AIS_PFULL[H] = P_FULL[H]
    end
end

## [MAGNITUDE] REPORTED, NOT GATED (`threshold_from_obs_or_law`): the comparator on the shelf is
## stage 2's own Ladrillo number, and a gate derived from the very quantity this run exists to
## compare against would be re-baselining in disguise -- it could never reject anything.
let H = 2100, v = DIFF[:total][:, yidx(H)], per = median(v) / SPEC.pulse_Gt
    @printf("  [MAGNITUDE] %d: %.4e cm per %s (median)  -- REPORTED, not gated\n", H, per, SPEC.unit)
    @printf("              context: stage 2 Ladrillo L24 tapped, and the FACTS PoC FaIR->BRICK\n")
    @printf("              5.08e-03 cm/GtCO2 @2100 (OLD model AND pre-1.6.0 calibration).\n")
    if SPECIE == "CH4"
        @printf("              ⚠ CH4 DOUBLING RATIO %.4f (FaIR stage): the pulse is SUPERLINEAR.\n",
                FAIR_DOUBLING["CH4"])
        @printf("                Quote this ratio beside any per-tonne CH4 marginal.\n")
    end
    push_g!("MAGNITUDE", "cm_per_$(SPEC.unit)_$(H)", per, true)
end
CSV.write(joinpath(REPO, "outputs", "pulse_brick2_gates_$(OUTSTEM).csv"), rowsg)

## ==========================================================================
## THE CELLS -- the paired difference, per component and horizon
## ==========================================================================
## SCHEMA IS pulse_ladrillo_cells_*'s, COLUMN FOR COLUMN, so one figure code path reads both
## models. THE PAIRED MEDIAN, NOT THE DIFFERENCE OF MEDIANS -- both are carried, side by side
## and named, so a later reader cannot silently pick up the wrong one.
cells = DataFrame(marker = String[], specie = String[], pulse_Gt = Float64[],
                  component = String[], horizon = Int[], n_draws = Int[],
                  base_med_cm = Float64[], pulse_med_cm = Float64[],
                  paired_med_cm = Float64[], diff_of_med_cm = Float64[],
                  paired_mean_cm = Float64[], paired_p05_cm = Float64[], paired_p95_cm = Float64[],
                  per_unit_cm = Float64[], se_mean_cm = Float64[], p_fired = Float64[],
                  smooth_term_cm = Float64[], premium_cm = Float64[])
@printf("\n%s\nBRICK 2.0 PULSE RESPONSE -- vv%s, %.0f %s at %d, cm rel %d-%d\n%s\n",
        repeat("=", 92), MARKER, SPEC.pulse_Gt, SPEC.unit, PULSE_YEAR, BASE0, BASE1, repeat("=", 92))
@printf("  %-9s %-6s %10s %12s %12s %12s %12s\n",
        "comp", "horiz", "base med", "paired med", "diff of med", "paired p05", "paired p95")
for c in COMPONENTS
    for H in HORIZONS
        i = yidx(H)
        b, p, d = RES["base"][c][:, i], RES["pulse"][c][:, i], DIFF[c][:, i]
        ## ⭐ THE LEMOINE-TRAEGER PAIR, reported as TWO terms and never as the sum alone.
        ## E[d] = P(smooth)*E[d|smooth] + P(fired)*E[d|fired]. At stage 2 the premium was
        ## 67-97 % of E[dAIS], so a median headline deletes ~90 % of the expected AIS response.
        ## P comes from the EXACT cross-product, the conditional means from the paired sample --
        ## the Rao-Blackwellised estimator, ~half the variance for no compute.
        ## ⚠ `smooth_term_cm` is (1-P)*E[.|smooth], so it falls partly because P RISES. Do not
        ## read its decline across markers as physical saturation without separating the two.
        ## ⚠ The pair's two terms are comparable across runs only AT THE SAME PULSE SIZE.
        fired = AIS_FIRED[H]; sm = .!fired; pf = AIS_PFULL[H]
        e_sm = any(sm) ? mean(d[sm]) : 0.0; e_fi = any(fired) ? mean(d[fired]) : 0.0
        push!(cells, (MARKER, SPECIE, SPEC.pulse_Gt, String(c), H, NDRAW,
                      median(b), median(p), median(d), median(p) - median(b),
                      mean(d), quantile(d, 0.05), quantile(d, 0.95),
                      median(d) / SPEC.pulse_Gt, std(d) / sqrt(NDRAW), pf,
                      (1 - pf) * e_sm, pf * e_fi))
        @printf("  %-9s %-6d %10.3f %12.5f %12.5f %12.5f %12.5f\n",
                c, H, median(b), median(d), median(p) - median(b),
                quantile(d, 0.05), quantile(d, 0.95))
    end
    println()
end
CSV.write(joinpath(REPO, "outputs", "pulse_brick2_cells_$(OUTSTEM).csv"), cells)

## per-draw differences at the horizons, so any statistic can be recomputed without a re-run
let dr = DataFrame(draw = Int[], config = String[], component = String[], horizon = Int[],
                   base_cm = Float64[], pulse_cm = Float64[], diff_cm = Float64[])
    for c in COMPONENTS, H in HORIZONS, k in 1:NDRAW
        i = yidx(H)
        push!(dr, (k, CFG_OF_DRAW[k], String(c), H,
                   RES["base"][c][k, i], RES["pulse"][c][k, i], DIFF[c][k, i]))
    end
    CSV.write(joinpath(REPO, "outputs", "pulse_brick2_draws_$(OUTSTEM).csv"), dr)
end

## the response PATH -- when the pulse's sea-level signal actually arrives, which is the
## question a 2100/2150/2300 table cannot answer. THE MEAN TRAVELS WITH THE MEDIAN: the mean is
## the statistic the threshold owns, and leaving it out of the only per-year output is how a
## threshold channel goes unreported without anyone deciding to omit it.
paths = DataFrame(year = Int[], component = String[], med_diff_cm = Float64[],
                  mean_diff_cm = Float64[], se_mean_cm = Float64[],
                  p05_diff_cm = Float64[], p95_diff_cm = Float64[])
for c in COMPONENTS, (i, y) in enumerate(YEARS)
    y < PULSE_YEAR - 5 && continue
    v = DIFF[c][:, i]
    push!(paths, (y, String(c), median(v), mean(v), std(v) / sqrt(NDRAW),
                  quantile(v, 0.05), quantile(v, 0.95)))
end
CSV.write(joinpath(REPO, "outputs", "pulse_brick2_paths_$(OUTSTEM).csv"), paths)
@printf("\nwrote outputs/pulse_brick2_{cells,draws,paths,gates}_%s.csv\n", OUTSTEM)
