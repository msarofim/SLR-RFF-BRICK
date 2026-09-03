## ============================================================================
## scope_slr_pulse_vv.jl -- THE LADRILLO PULSE ARM on the van Vuuren markers
##
## STAGE 2 of the pulse comparison. Stage 1 (FaIRtoFrEDI/scripts/build_fair_pulse_vv_v160.py)
## built PAIRED baseline/pulse GMST and OHC cubes per marker; this file runs Ladrillo on
## both and reports the PAIRED difference. Stages 3-5 (BRICK 2.0, MAGICC, FACTS) consume the
## same cubes so the climate axis is held.
##
## MARCUS'S SPEC, settled 2026-09-03: 10 GtCO2 or 1 GtCH4, pulse year 2030, on each of the
## seven van Vuuren markers, JOINT driver, against BRICK 2.0 / MAGICC / FACTS.
##
## ⚠ WHY BOTH ARMS RUN IN ONE PROCESS, AND WHY THAT IS THE WHOLE POINT.
## The pulse response is a DIFFERENCE of two numbers that are individually ~100 cm and
## differ by ~0.05 cm. If draw k saw posterior sample A against config X in the baseline
## and anything else in the pulse, the difference is noise at 2000x the size of the signal.
## `scope_slr_fair_uncertainty.jl` derives its pairing from a seed, which two SEPARATE runs
## would reproduce -- but "would reproduce" is an assumption about two processes, and the
## cost of it being wrong is a plausible-looking number with no signal in it. Here ONE
## `ASSIGN` vector, ONE `ROWS` list and ONE model build serve both arms, so the pairing is
## an IDENTITY rather than a reproduction. [PRE-PULSE-ZERO] then MEASURES that identity
## instead of asserting it: before the pulse year the two arms must agree EXACTLY.
##
## ⚠ THE CONVENTION IS INHERITED, NOT REINVENTED. Splice, reference window, pairing seed,
## component list and the tap all mirror `scope_slr_fair_uncertainty.jl` -- read that file's
## header for why each is what it is. Two properties matter for a DIFFERENCE specifically:
##   * the splice pivots on the 1995-2014 mean, and the two cubes are identical there
##     (the pulse is 2030), so `cref` and `mref` are equal across arms and the splice
##     PRESERVES the difference exactly rather than rescaling it;
##   * the mean driver is the MARKER's own `fair_mean_gmst_vv<M>.csv`, the SAME file for
##     both arms, so the pre-2014 half of the spliced path is identical by construction.
##
## ⚠ THE TAP IS A REPORTED CHOICE, NOT A DEFAULT. It fires at 4.69 K on each config's own
## GMST, so on the high markers a pulse can push a draw across the onset in the pulse arm
## that did not cross it in the baseline. That is a real physical response and also the
## single biggest way this number can be misread, so --tap carries the arm in the filename
## and [TAP-CROSSING] COUNTS the draws that differ rather than leaving it to be assumed.
##
##   julia --project=julia_v2 julia/scope_slr_pulse_vv.jl [n_per_chain] --marker=H --specie=CO2
##        [--tag=L24] [--tap] [--maxrows=N] [--forcing=spliced|raw] [--chain-tag=L24]
##
## Writes outputs/pulse_ladrillo_{cells,draws,paths,gates}_vv<M>_<SPECIE>_<TAG><TAP_TAG>.csv
## ============================================================================
using CSV, DataFrames, Statistics, Printf, Mimi, Random

include(joinpath(@__DIR__, "ladrillo_projection.jl"))

const REPO   = LADRILLO_REPO
const SEEDS  = [2026, 2027, 2028, 2029]
const NITER  = 2000000
const NBURN  = 1000000

argval(flag, dflt) = let i = findfirst(a -> startswith(a, flag), ARGS)
    i === nothing ? dflt : ARGS[i][(length(flag) + 1):end]
end

const TAG     = argval("--tag=", "L24")
const MARKER  = argval("--marker=", "")
const SPECIE  = argval("--specie=", "CO2")
const FORCING = argval("--forcing=", "spliced")
const MAXROWS = let v = argval("--maxrows=", ""); v == "" ? nothing : parse(Int, v); end
const SMOKE   = MAXROWS !== nothing
const N_TARGET = let p = findfirst(a -> !startswith(a, "--"), ARGS)
    p === nothing ? 500 : parse(Int, ARGS[p])
end
const CHAIN_TAG = argval("--chain-tag=", TAG)

## THE SEVEN MARKERS, in van Vuuren's own order. Named here so an unrecognised marker
## FAILS LOUDLY at argument parse rather than as a missing-file error 3 minutes into setup.
const MARKERS = ["VL", "L", "LN", "ML", "M", "HL", "H"]
@assert MARKER in MARKERS "--marker must be one of $(MARKERS); got '$(MARKER)'"
@assert FORCING in ("spliced", "raw") "--forcing must be spliced or raw"

## ⚠ UNITS ARE THE 1000x CLASS OF ERROR. These strings are not cosmetic -- they are the
## filename the FaIR stage wrote, and they encode the pulse SIZE that every per-tonne
## number downstream divides by. `PULSE_GT` is the divisor; it must agree with the cube's
## own name, which is why both are derived from ONE table.
const SPECIE_SPEC = Dict(
    "CO2" => (size_tag = "10Gt", pulse_Gt = 10.0,  unit = "GtCO2"),
    "CH4" => (size_tag = "1Gt",  pulse_Gt = 1.0,   unit = "GtCH4"))
@assert haskey(SPECIE_SPEC, SPECIE) "--specie must be CO2 or CH4; got '$(SPECIE)'"
const SPEC = SPECIE_SPEC[SPECIE]
const PULSE_YEAR = 2030

## ⚠ CH4 IS NOT A SMALL PERTURBATION and the FaIR stage measured it: 1 GtCH4 = 260% of one
## year's CH4 emission at 2030, and the DOUBLING gate came back 2.0332, i.e. measurably
## SUPERLINEAR. Small enough to divide through, not small enough to divide through
## silently -- so any per-tonne CH4 number carries this ratio beside it. The CO2 pulse is
## 26% of a year and doubles at 1.9999. Source: FaIRtoFrEDI scripts/build_fair_pulse_vv_v160.py
## gate output, 2026-09-03; NOT a literature constant.
const FAIR_DOUBLING = Dict("CO2" => 1.9999, "CH4" => 2.0332)

const HORIZONS = [2100, 2150, 2300]
const Y0, Y1   = 1850, 2300
const YEARS    = collect(Y0:Y1)
const COMPONENTS = [:glaciers, :gis, :ais, :te, :lws, :total]
const SUM_PARTS  = [:glaciers, :gis, :ais, :te, :lws]
const SUM_TOL_CM = 1e-6          # an identity in BRICK; float noise only
const PAIR_SEED  = 2026          # the draw -> config permutation; same seed as the joint arm
const SPLICE_YEAR = 2014
const ARMS = ["base", "pulse"]

cube(kind, arm) = joinpath(LADRILLO_OBS,
    "fair_cube_$(kind)_vv$(MARKER)_$(arm == "base" ? "pulsebase" : "pulse")_" *
    "$(SPECIE)_$(SPEC.size_tag)_$(PULSE_YEAR)_raw.csv")

chain_path(sd) = joinpath(REPO, "outputs/mcmc", "chain_$(CHAIN_TAG)_seed$(sd)_n$(NITER).csv")
hdr(sd) = String.(propertynames(CSV.read(chain_path(sd), DataFrame; limit = 0)))
for sd in SEEDS; isfile(chain_path(sd)) || error("missing chain $(chain_path(sd))"); end
for k in ("gmst", "ohc"), a in ARMS
    isfile(cube(k, a)) || error("missing cube $(cube(k, a))\n  build it with " *
        "FaIRtoFrEDI/scripts/build_fair_pulse_vv_v160.py --marker=$(MARKER) --specie=$(SPECIE)")
end
const VARIANT = ladrillo_gis_variant(hdr(SEEDS[1]))

## The tap tag mirrors project_ssps_components_ladrillo.jl and scope_slr_fair_uncertainty.jl
## so a tapped run can never overwrite an untapped one. Same rule, same construction.
const TAP_ON  = "--tap" in ARGS
const TAP_TAG = TAP_ON ? "_tap$(replace(string(GIS_TAP_CELL.onset_K), "." => "p"))K" *
                         "_V$(replace(string(GIS_TAP_CELL.V_m), "." => "p"))m" *
                         "_tau$(Int(GIS_TAP_CELL.tau_yr))" : ""
const OUTSTEM = "vv$(MARKER)_$(SPECIE)_$(SPEC.size_tag)_$(PULSE_YEAR)_$(FORCING)_$(TAG)$(TAP_TAG)$(SMOKE ? "_SMOKE" : "")"

function read_draws(sd)
    need = ladrillo_used_cols(VARIANT)
    h = hdr(sd)
    rd = ladrillo_gis_needs_native(h) ?
        vcat(setdiff(need, LADRILLO_GIS_SLOW_NATIVE_COLS),
             LADRILLO_GIS_SLOW_REPARAM_COLS) |> unique : need
    df = SMOKE ? CSV.read(chain_path(sd), DataFrame; select = rd, limit = MAXROWS) :
                 CSV.read(chain_path(sd), DataFrame; select = rd)
    df = df[((SMOKE ? 0 : NBURN) + 1):end, :]
    step = max(1, nrow(df) ÷ N_TARGET)
    idx = collect(1:step:nrow(df))
    d = ladrillo_native_greenland!(df[idx[1:min(N_TARGET, length(idx))], :]); df = nothing; GC.gc(); d
end

@printf("LADRILLO PULSE ARM | marker vv%s | %s pulse %.0f %s at %d | tag %s%s%s%s\n",
        MARKER, SPECIE, SPEC.pulse_Gt, SPEC.unit, PULSE_YEAR, TAG,
        CHAIN_TAG == TAG ? "" : "  (chains from $(CHAIN_TAG))",
        TAP_ON ? "  [TAPPED Greenland]" : "  [untapped Greenland]",
        SMOKE ? "  ** SMOKE (--maxrows=$(MAXROWS)) **" : "")
@printf("  climate: FaIR 2.2.4 calib 1.6.0 + CMIP7, marker forcing volcanic_solar_%s.csv, forcing=%s\n",
        MARKER, FORCING)
flush(stdout)

const DRAWS = [(@printf("  reading chain seed%d ...\n", sd); flush(stdout); read_draws(sd))
               for sd in SEEDS]
const ROWS  = [r for d in DRAWS for r in eachrow(d)]
const NDRAW = length(ROWS)

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

const IREF = findall(y -> LADRILLO_REF[1] <= y <= LADRILLO_REF[2], YEARS)
## ONE mean driver, the marker's own, SHARED by both arms -- see the header.
const MEAN_G = [_yearmap(joinpath(LADRILLO_OBS, "fair_mean_gmst_vv$(MARKER).csv"), "gmst_C")[y] for y in YEARS]
const MEAN_O = [_yearmap(joinpath(LADRILLO_OBS, "fair_mean_ohc_vv$(MARKER).csv"), "ohc_1e22J")[y] for y in YEARS]

function convention(raw::Vector{Float64}, mean_path::Vector{Float64})
    FORCING == "raw" && return raw
    mref, cref = mean(mean_path[IREF]), mean(raw[IREF])
    [y <= SPLICE_YEAR ? mean_path[i] : mref + (raw[i] - cref) for (i, y) in enumerate(YEARS)]
end
gmst_of(a, c) = convention(Float64.(CG[a][!, c]), MEAN_G)
ohc_of(a, c)  = convention(Float64.(CO[a][!, c]), MEAN_O)

## ---- the pairing: ONE assignment, both arms ------------------------------
const ASSIGN = let rng = MersenneTwister(PAIR_SEED)
    a = Int[]
    while length(a) < NDRAW; append!(a, randperm(rng, NCFG)); end
    a[1:NDRAW]
end
const CFG_OF_DRAW = [CFG[i] for i in ASSIGN]

const BUILD_SSP = argval("--build-ssp=", "ssp245")   # see scope_slr_fair_uncertainty.jl:BUILD_SSP

## What each arm ACTUALLY ran, per draw, recorded at the call site. [DRAW-PAIRING] reads
## these back; without them the pairing claim rests on ASSIGN being used twice, which is
## the assumption this whole file exists to avoid making.
const RAN_CFG = Dict(a => fill("", NDRAW) for a in ARMS)
const RAN_ROW = Dict(a => fill(-1, NDRAW) for a in ARMS)

function run_into!(out, idx, g, o, arm, cfgname)
    bf = ladrillo_setup(ssp = BUILD_SSP, y0 = Y0, y1 = Y1, gis_variant = VARIANT, gmst = g, ohc = o)
    TAP_ON && ladrillo_set_tap!(bf)
    for k in idx
        ladrillo_run_draw!(bf, ROWS[k])
        RAN_CFG[arm][k] = cfgname
        RAN_ROW[arm][k] = k
        for c in COMPONENTS
            out[c][k, :] = coalesce.(ladrillo_series(bf, c), NaN)
        end
    end
    bf
end
alloc() = Dict(c => Matrix{Float64}(undef, NDRAW, length(YEARS)) for c in COMPONENTS)

const RES = Dict(a => alloc() for a in ARMS)
let groups = Dict{String, Vector{Int}}()
    for k in 1:NDRAW; push!(get!(groups, CFG_OF_DRAW[k], Int[]), k); end
    @printf("\n  %d draws over %d configs; running BOTH arms per config ...\n",
            NDRAW, length(groups)); flush(stdout)
    n = 0
    for (c, idx) in groups
        ## Both arms for THIS config back to back. Grouping this way (rather than arm-major)
        ## keeps the two runs of a given draw adjacent in time, so a drift in any global
        ## state would show up in [PRE-PULSE-ZERO] instead of cancelling between arms.
        for a in ARMS; run_into!(RES[a], idx, gmst_of(a, c), ohc_of(a, c), a, c); end
        n += 1
        n % 100 == 0 && (@printf("    %d/%d configs\n", n, length(groups)); flush(stdout))
    end
end

yidx(y) = findfirst(==(y), YEARS)
const DIFF = Dict(c => RES["pulse"][c] .- RES["base"][c] for c in COMPONENTS)

## ==========================================================================
## GATES
## ==========================================================================
@printf("\n%s\nGATES\n%s\n", repeat("=", 92), repeat("=", 92))
rowsg = DataFrame(gate = String[], key = String[], value = Float64[], verdict = String[])
push_g!(g, k, v, ok) = push!(rowsg, (g, k, Float64(v), ok ? "PASS" : "FAIL"))

## ---------------------------------------------------------------------------
## THE IDENTITY GATES. Read this block before changing any bound in it.
##
## ⚠ THE IDENTITY HORIZON IS NOT THE PULSE YEAR, and the first version of this gate got
## that wrong. Ladrillo's Greenland shape law evaluates S on a CENTRED running mean of
## width LADRILLO_GIS_SHAPE_WIN (30 yr), so a forcing change at 2031 legitimately moves
## the mean at 2031 - WIN/2 = 2016 and Greenland responds BEFORE the pulse. Measured on
## the real arm: gis first differs 2026, ais 2027 (DAIS reads total sea level, so it is
## downstream of gis), and glaciers / te / lws are EXACTLY zero throughout. The bound is
## therefore DERIVED from the window rather than set to PULSE_YEAR -- an identity bound on
## the wrong year is a gate that fires forever (`gate_bound_matches_its_claim`), which is
## exactly what it did.
##
## ⚠ THIS IS `smoother_wider_than_feature` IN THE OUTPUT, NOT ONLY IN THE GATE. A 30-yr
## smoother relocates part of a pulse response ~15 yr earlier than the pulse. It is small
## (see [REACHBACK] for the measured share) and it is the model's own definition, not an
## error -- but a reader who sees sea level moving in 2026 in response to a 2030 pulse is
## owed the mechanism, so it is MEASURED and printed rather than trimmed away.
##
## ⚠ AND THE POWER OF THE ZERO GATE IS BOUNDED, said out loud (`no_power_null`). Pre-2014
## the spliced path is the MEAN driver, IDENTICAL for every config -- so this gate is BLIND
## to a config mis-pairing and would pass one. It has power against a posterior-draw
## mis-pairing, state leaking between the two model builds, and an unseeded LWS. The config
## pairing is certified separately and structurally by [DRAW-PAIRING], which records what
## each arm actually ran instead of trusting that one ASSIGN vector reached both.
const REACH      = LADRILLO_GIS_SHAPE_WIN ÷ 2
const IDENT_LAST = PULSE_YEAR - REACH - 1
## Components with NO reach-back mechanism at all: no smoother, no sea-level coupling.
## For these the identity holds right up to the pulse, so they get the stronger bound.
const NO_REACHBACK = [:glaciers, :te, :lws]

let iy = yidx(IDENT_LAST), worst = 0.0
    for c in COMPONENTS
        m = maximum(abs.(@view DIFF[c][:, 1:iy]))
        worst = max(worst, m)
        push_g!("PRE-PULSE-ZERO", "max_abs_cm_$(c)", m, m == 0.0)
    end
    @printf("  [PRE-PULSE-ZERO] max |pulse - base| over %d-%d = %.3e cm, all %d components (bound EXACT 0)  %s\n",
            Y0, IDENT_LAST, worst, length(COMPONENTS), worst == 0.0 ? "PASS" : "FAIL")
    @printf("                   horizon DERIVED: pulse %d - shape window %d/2 - 1. Blind to a config\n",
            PULSE_YEAR, LADRILLO_GIS_SHAPE_WIN)
    @printf("                   mis-pairing (pre-splice forcing is config-independent); see [DRAW-PAIRING].\n")
    worst == 0.0 || error("[PRE-PULSE-ZERO] the arms differ before the shape window can reach; " *
                          "the difference is not a pulse response. Do not use these outputs.")
end

## [NO-REACHBACK-MECHANISM] the components that CANNOT reach back must not. This is where
## the identity claim keeps its teeth all the way to the pulse year, and it is the half of
## the check that a mis-derived window cannot explain away.
let iy = yidx(PULSE_YEAR) - 1, worst = 0.0, wc = ""
    for c in NO_REACHBACK
        m = maximum(abs.(@view DIFF[c][:, 1:iy]))
        m > worst && ((worst, wc) = (m, String(c)))
        push_g!("NO-REACHBACK", "max_abs_cm_$(c)", m, m == 0.0)
    end
    @printf("  [NO-REACHBACK] %s max |pulse - base| through %d = %.3e cm (bound EXACT 0)  %s\n",
            join(String.(NO_REACHBACK), "/"), PULSE_YEAR - 1, worst, worst == 0.0 ? "PASS" : "FAIL")
    worst == 0.0 || error("[NO-REACHBACK] $(wc) moved before the pulse and has no mechanism to; " *
                          "that is a defect, not the shape window.")
end

## [REACHBACK] MEASURE the smoother's relocation instead of asserting it is negligible.
## The share is quoted against the SAME component's own 2100 response, because a share of
## the total would hide a large relative effect in a small component (`ratio_needs_its_base`).
let i0 = yidx(IDENT_LAST) + 1, i1 = yidx(PULSE_YEAR) - 1, i2100 = yidx(2100)
    for c in COMPONENTS
        m = maximum(abs.(@view DIFF[c][:, i0:i1]))
        sig = abs(median(DIFF[c][:, i2100]))
        j = m > 0 ? findfirst(k -> any(!=(0.0), @view DIFF[c][:, k]), 1:i1) : nothing
        @printf("  [REACHBACK] %-9s %.3e cm in %d-%d = %6.3f%% of its own 2100 response%s\n",
                c, m, IDENT_LAST + 1, PULSE_YEAR - 1, sig > 0 ? 100m / sig : 0.0,
                j === nothing ? "  (none)" : @sprintf("  first differs %d", YEARS[j]))
        push_g!("REACHBACK", "max_abs_cm_$(c)", m, true)
        push_g!("REACHBACK", "pct_of_2100_$(c)", sig > 0 ? 100m / sig : 0.0, true)
    end
    @printf("              REPORTED, not gated: this is the model's own 30-yr centred window\n")
    @printf("              (`smoother_wider_than_feature`), not an error to be tuned away.\n")
end

## [DRAW-PAIRING] the pairing certified by what the arms RECORDED, not by one ASSIGN vector
## being read twice. `recorded_but_never_restored` is the failure this closes: a value that
## is written and never checked against the thing it is supposed to equal.
let bad = count(k -> RAN_CFG["base"][k] != RAN_CFG["pulse"][k], 1:NDRAW),
    badr = count(k -> RAN_ROW["base"][k] != RAN_ROW["pulse"][k], 1:NDRAW)
    @printf("  [DRAW-PAIRING] %d/%d draws saw a different CONFIG across arms, %d a different DRAW ROW  %s\n",
            bad, NDRAW, badr, (bad == 0 && badr == 0) ? "PASS" : "FAIL")
    push_g!("DRAW-PAIRING", "config_mismatches", bad, bad == 0)
    push_g!("DRAW-PAIRING", "row_mismatches", badr, badr == 0)
    (bad == 0 && badr == 0) || error("[DRAW-PAIRING] the arms are not paired; every difference is noise.")
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
## linear, so this is the parent driver's identity carried through -- and it is worth
## re-checking because it is the cheapest way to catch a component matrix written to the
## wrong arm's slot.
let worst = 0.0
    for H in HORIZONS
        s = sum(DIFF[c][:, yidx(H)] for c in SUM_PARTS)
        worst = max(worst, maximum(abs.(s .- DIFF[:total][:, yidx(H)])))
    end
    @printf("  [SUM] max |sum(parts) - total| in the DIFFERENCE = %.3e cm (tol %.0e)  %s\n",
            worst, SUM_TOL_CM, worst <= SUM_TOL_CM ? "PASS" : "FAIL")
    push_g!("SUM", "max_abs_cm", worst, worst <= SUM_TOL_CM)
end

## [SIGN] a positive emission pulse warms, and every Ladrillo component is monotone in
## warming, so the paired difference should be >= 0. Reported as a FRACTION rather than
## gated hard: with the tap on, a draw that crosses the 4.69 K onset in one arm only makes
## the response lumpy -- still positive, but no longer smooth -- and a hard sign gate would
## then be measuring the tap, not the pulse.
for H in HORIZONS
    v = DIFF[:total][:, yidx(H)]
    neg = count(<(0.0), v) / length(v)
    @printf("  [SIGN] %d: median %+.5f cm, %.2f%% of draws negative  %s\n",
            H, median(v), 100neg, median(v) > 0 ? "PASS" : "FAIL")
    push_g!("SIGN", "median_cm_$(H)", median(v), median(v) > 0)
    push_g!("SIGN", "frac_negative_$(H)", neg, true)
end

## [TAP-CROSSING] the §6.3 open question, MEASURED. A draw whose baseline never reaches the
## 4.69 K onset but whose pulsed arm does gets a whole Greenland tap charged to a 10 GtCO2
## pulse. That is a real threshold response and it is also the number a reader most needs to
## see, because it is the difference between "the pulse raises sea level 0.05 cm" and "on
## 0.3% of draws it raises it 40 cm". With --tap OFF this is structurally zero and says so.
if TAP_ON
    let i23 = yidx(2300), n = 0
        for k in 1:NDRAW
            g = gmst_of("base", CFG_OF_DRAW[k]); gp = gmst_of("pulse", CFG_OF_DRAW[k])
            (maximum(g) < GIS_TAP_CELL.onset_K) && (maximum(gp) >= GIS_TAP_CELL.onset_K) && (n += 1)
        end
        @printf("  [TAP-CROSSING] %d of %d draws (%.3f%%) cross the %.2f K onset ONLY in the pulsed arm\n",
                n, NDRAW, 100n / NDRAW, GIS_TAP_CELL.onset_K)
        push_g!("TAP-CROSSING", "n_draws_crossing", n, true)
    end
else
    @printf("  [TAP-CROSSING] not applicable -- running the UNTAPPED Greenland arm\n")
    push_g!("TAP-CROSSING", "n_draws_crossing", 0, true)
end

## [MAGNITUDE] REPORTED, NOT GATED, and the reason is `threshold_from_obs_or_law`: the only
## comparator on the shelf is the old FACTS proof-of-concept, which is a DIFFERENT MODEL on
## a DIFFERENT CALIBRATION (FaIR->BRICK 5.08e-3 cm/GtCO2 @2100, MAGICC-native 1.54e-2, both
## pre-1.6.0). A gate whose threshold comes from another model's old vintage cannot reject
## anything honestly, so this prints the number with the comparator's vintage named and
## leaves the verdict to a reader who can see both.
let H = 2100, v = DIFF[:total][:, yidx(H)], per = median(v) / SPEC.pulse_Gt
    @printf("  [MAGNITUDE] %d: %.4e cm per %s (median)  -- REPORTED, not gated\n", H, per, SPEC.unit)
    @printf("              context: FACTS PoC FaIR->BRICK 5.08e-03 cm/GtCO2 @2100 -- OLD model AND\n")
    @printf("              old calibration (pre-1.6.0), an order-of-magnitude check only.\n")
    if SPECIE == "CH4"
        @printf("              ⚠ CH4 DOUBLING RATIO %.4f (FaIR stage): the pulse is SUPERLINEAR.\n",
                FAIR_DOUBLING["CH4"])
        @printf("                Quote this ratio beside any per-tonne CH4 marginal.\n")
    end
    push_g!("MAGNITUDE", "cm_per_$(SPEC.unit)_$(H)", per, true)
end
CSV.write(joinpath(REPO, "outputs", "pulse_ladrillo_gates_$(OUTSTEM).csv"), rowsg)

## ==========================================================================
## THE CELLS -- the paired difference, per component and horizon
## ==========================================================================
## THE PAIRED MEDIAN, NOT THE DIFFERENCE OF MEDIANS. They are different statistics and the
## L24 deliverable already has one incident of the two being quoted as if interchangeable
## (`gic_regrow_not_the_penalty`: 1.0 cm apart at 2150). Both are carried, side by side and
## named, so a later reader cannot silently pick up the wrong one. MEAN is carried too --
## the AIS tipped fraction makes the median sample-fragile at ssp245-like forcing.
cells = DataFrame(marker = String[], specie = String[], pulse_Gt = Float64[],
                  component = String[], horizon = Int[], n_draws = Int[],
                  base_med_cm = Float64[], pulse_med_cm = Float64[],
                  paired_med_cm = Float64[], diff_of_med_cm = Float64[],
                  paired_mean_cm = Float64[], paired_p05_cm = Float64[], paired_p95_cm = Float64[],
                  per_unit_cm = Float64[])
@printf("\n%s\nPULSE RESPONSE -- vv%s, %.0f %s at %d, cm rel %d-%d%s\n%s\n",
        repeat("=", 92), MARKER, SPEC.pulse_Gt, SPEC.unit, PULSE_YEAR,
        LADRILLO_REF[1], LADRILLO_REF[2], TAP_ON ? ", TAPPED" : ", untapped", repeat("=", 92))
@printf("  %-9s %-6s %10s %12s %12s %12s %12s\n",
        "comp", "horiz", "base med", "paired med", "diff of med", "paired p05", "paired p95")
for c in COMPONENTS
    for H in HORIZONS
        i = yidx(H)
        b, p, d = RES["base"][c][:, i], RES["pulse"][c][:, i], DIFF[c][:, i]
        push!(cells, (MARKER, SPECIE, SPEC.pulse_Gt, String(c), H, NDRAW,
                      median(b), median(p), median(d), median(p) - median(b),
                      mean(d), quantile(d, 0.05), quantile(d, 0.95),
                      median(d) / SPEC.pulse_Gt))
        @printf("  %-9s %-6d %10.3f %12.5f %12.5f %12.5f %12.5f\n",
                c, H, median(b), median(d), median(p) - median(b),
                quantile(d, 0.05), quantile(d, 0.95))
    end
    println()
end
CSV.write(joinpath(REPO, "outputs", "pulse_ladrillo_cells_$(OUTSTEM).csv"), cells)

## per-draw differences at the horizons, so any statistic can be recomputed without a re-run
let dr = DataFrame(draw = Int[], config = String[], component = String[], horizon = Int[],
                   base_cm = Float64[], pulse_cm = Float64[], diff_cm = Float64[])
    for c in COMPONENTS, H in HORIZONS, k in 1:NDRAW
        i = yidx(H)
        push!(dr, (k, CFG_OF_DRAW[k], String(c), H,
                   RES["base"][c][k, i], RES["pulse"][c][k, i], DIFF[c][k, i]))
    end
    CSV.write(joinpath(REPO, "outputs", "pulse_ladrillo_draws_$(OUTSTEM).csv"), dr)
end

## the response PATH -- when the pulse's sea-level signal actually arrives, which is the
## question a 2100/2150/2300 table cannot answer
paths = DataFrame(year = Int[], component = String[], med_diff_cm = Float64[],
                  p05_diff_cm = Float64[], p95_diff_cm = Float64[])
for c in COMPONENTS, (i, y) in enumerate(YEARS)
    y < PULSE_YEAR - 5 && continue
    v = DIFF[c][:, i]
    push!(paths, (y, String(c), median(v), quantile(v, 0.05), quantile(v, 0.95)))
end
CSV.write(joinpath(REPO, "outputs", "pulse_ladrillo_paths_$(OUTSTEM).csv"), paths)
@printf("\nwrote outputs/pulse_ladrillo_{cells,draws,paths,gates}_%s.csv\n", OUTSTEM)
