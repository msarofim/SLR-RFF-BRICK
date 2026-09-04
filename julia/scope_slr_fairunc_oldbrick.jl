## ============================================================================
## scope_slr_fairunc_oldbrick.jl — BRICK 2.0 WITH FaIR CLIMATE UNCERTAINTY
##
## WHY. `ladrillo_model_comparison.py` reports Ladrillo on the JOINT arm (posterior
## parameters x 841 FaIR configs) but BRICK 2.0 on MEAN forcing, so BRICK 2.0's WIDTHS
## were the one column in the table not comparable to any other. The document said BRICK
## 2.0 "can never be made joint". THAT WAS WRONG: `set_forcing!(m, gmst, ohc)` is a plain
## two-vector setter, so the Ladrillo joint recipe transfers directly. It had simply never
## been run that way.
##
## ⚠ THIS IS A PRIOR PROPAGATION, NOT A REFIT — the same caveat the Ladrillo joint arm
## carries. BRICK 2.0's published posterior was calibrated under ITS own fixed forcing;
## propagating it under a spread of drivers is the right object to COMPARE against
## ensembles that carry climate uncertainty, and is NOT a recalibration.
##
## EVERY CONVENTION IS THE LADRILLO ONE, DELIBERATELY. Same raw cubes, same 2014 splice
## pivot, same 1995-2014 re-reference, same PAIR_SEED, same draw->config permutation, same
## output schema. If these diverged, the two joint bands would not be comparable and the
## whole point would be lost.
##
## ⚠ THE MODEL IS BUILT ONCE PER SSP, NOT ONCE PER CONFIG. `MimiBRICK.get_model` is
## non-deterministic (~1e-5 m) and LWS is seeded before it, so rebuilding per config would
## re-roll LWS and inject noise INTO THE JOINT ARM ONLY -- which would then be misread as
## forcing spread. `set_forcing!` mutates the built model instead.
##
## ⚠ DRAW COUNT IS PINNED TO THE SHIPPED PANEL'S THINNING. The [CONTROL] gate below only
## means something if the fixed arm uses the SAME draws as ssps_components_2300_oldbrick.csv.
##
##   julia --project=julia_v2 julia/scope_slr_fairunc_oldbrick.jl [--ssp=ssp585] [--ndraw=1000]
## Writes outputs/scope_slr_fairunc_{draws,cells}_<ssp>_spliced_oldbrick.csv
## ============================================================================
using CSV, DataFrames, Mimi, MimiBRICK, Statistics, Printf, Random
include(joinpath(@__DIR__, "brick_mengel.jl"))      # set_forcing! + update_brick_params!

const REPO = abspath(joinpath(@__DIR__, ".."))
const OBS  = joinpath(REPO, "data/observations")
const POST = joinpath(REPO, "data/MimiBRICK/parameters_subsample_brick.csv")
_arg(p) = (i = findfirst(a -> startswith(a, p), ARGS); i === nothing ? nothing : ARGS[i][length(p)+1:end])
const SSP   = something(_arg("--ssp="), "ssp585")
const NDRAW = parse(Int, something(_arg("--ndraw="), "1000"))
## ---- which climate drives the JOINT arm ----------------------------------
## `fair`   our 841-config FaIR cube (the default; every existing product).
## `magicc` MAGICC-SLR's own 600-member climate, per member, from the run that
##          produced the MAGICC-SLR comparison series.
## WHY. Ladrillo's level driver gained this 2026-08-31c and its pulse driver 2026-09-04e;
## BRICK 2.0 had no such arm, so every BRICK-vs-MAGICC statement stayed a TWO-variable
## comparison (`magicc_colder_than_fair_2300`: 0.38-0.93 K colder at 2300 on the declining
## markers). Driving BRICK's UNCHANGED modules with MAGICC's climate holds the module axis.
## ⚠ THE REVERSE ARM IS IMPOSSIBLE (`runnable_is_not_undrivable`): MAGICC-SLR lives inside
## MAGICC and consumes MAGICC's own climate module. One direction only.
## ⚠ ONLY THE JOINT ARM MOVES. FIXED runs on MEAN_G/MEAN_O, which stay FaIR's mean path in
## both climates -- so [CONTROL] below remains a live gate under `--climate=magicc`, and its
## passing is what shows the swap reached the joint arm ONLY.
const CLIMATE = something(_arg("--climate="), "fair")
@assert CLIMATE in ("fair", "magicc") "--climate must be fair or magicc"
## The filename carries the climate, so a MAGICC-climate run cannot overwrite the
## FaIR-climate arm it is compared against. Empty on the default arm: existing names untouched.
const CLIM_TAG = CLIMATE == "fair" ? "" : "_magiccclim"
## ⚠ MAGICC reports `Heat Content|Ocean` in ZJ = 1e21 J; BRICK wants 1e22 J. 0.1 because ZJ
## is a DEFINITION -- never from a ratio (`magicc_ohc_zj_not_1e22j`: the MAGICC/FaIR OHC
## ratio drifts 11.3x -> 7.7x over 2020-2300, so a fitted factor would hide a real difference).
const ZJ_TO_1E22J = 0.1
const MAGICC_WIDE = joinpath(homedir(), "Documents/2026/CodeProjects/FaIRtoFrEDI",
                             "magicc_comparison/processed/vv_wide_20260831")
const MAGICC_N = 600                            # the AR6 drawnset this run used
const Y0, Y1       = 1850, 2300
const BASE0, BASE1 = 1995, 2014                 # AR6 SLR reference, = LADRILLO_REF
const SPLICE_YEAR  = 2014                       # build_protect_x2300_forcing.py's convention
const SEED         = 2026                       # get_model non-determinism; oldbrick's seed
const PAIR_SEED    = 2026                       # draw -> config permutation; Ladrillo's seed
const HORIZONS     = [2100, 2150, 2300]
const COMPS        = ["glaciers", "gis", "ais", "te", "lws", "total"]
const CONTROL_TOL_CM = 0.5                      # Ladrillo joint driver's own tolerance
const SPLICE_MATCH_TOL = 2e-6                   # derived in scope_slr_fair_uncertainty.jl
const SSP_LABEL = Dict("ssp119"=>"SSP1-1.9","ssp126"=>"SSP1-2.6","ssp245"=>"SSP2-4.5",
                       "ssp460"=>"SSP4-6.0","ssp370"=>"SSP3-7.0","ssp585"=>"SSP5-8.5")

const YEARS = collect(Y0:Y1)
const IB    = [findfirst(==(y), YEARS) for y in BASE0:BASE1]
const IREF  = IB
idx(y) = findfirst(==(y), YEARS)
reref(v) = 100 .* (v .- sum(v[IB])/length(IB))  # m -> cm, rel 1995-2014

lc(p, c) = (d = CSV.read(p, DataFrame);
            by = Dict(Int(d[i,"year"]) => Float64(d[i,c]) for i in 1:nrow(d));
            [by[y] for y in YEARS])

## ---- forcing: the cubes and the Ladrillo splice --------------------------
"""Read a MAGICC per-member wide CSV and cut it to Y0:Y1. The files run 1750-2305;
`end_year_2300` is the horizon for all our work, and the extra years are dropped
DELIBERATELY rather than silently carried. Mirrors scope_slr_fair_uncertainty.jl."""
function read_magicc_wide(path, scale)
    isfile(path) || error("missing $(path)\n  build it with " *
        "FaIRtoFrEDI/magicc_comparison/build_magicc_wide_ssp_overshoot.py")
    d = CSV.read(path, DataFrame)
    yr = Int.(d.year)
    ix = [findfirst(==(y), yr) for y in YEARS]
    any(isnothing, ix) && error("$(basename(path)) does not cover $(Y0):$(Y1)")
    cols = [c for c in String.(propertynames(d)) if startswith(c, "m")]
    out = DataFrame(year = YEARS)
    for c in cols; out[!, c] = Float64.(d[ix, c]) .* scale; end
    out
end
const CG, CO = CLIMATE == "fair" ?
    (CSV.read(joinpath(OBS, "fair_cube_gmst_$(SSP)_raw.csv"), DataFrame),
     CSV.read(joinpath(OBS, "fair_cube_ohc_$(SSP)_raw.csv"),  DataFrame)) :
    (read_magicc_wide(joinpath(MAGICC_WIDE, "magicc_gmst_$(SSP)_wide.csv"), 1.0),
     read_magicc_wide(joinpath(MAGICC_WIDE, "magicc_ohc_$(SSP)_wide_rel1850.csv"), ZJ_TO_1E22J))
const MEMBER_PREFIX = CLIMATE == "fair" ? "cfg_" : "m"
const CFG = [c for c in String.(propertynames(CG)) if startswith(c, MEMBER_PREFIX)]
@assert Int.(CG.year) == YEARS "the gmst cube's year axis is not $(Y0):$(Y1)"
@assert String.(propertynames(CO))[2:end] == CFG "gmst and ohc cubes disagree on configs"
## [CLIMATE-SOURCE] the member COUNT catches a truncated build; the ORDER equality above is
## what lets member j's temperature pair with member j's ocean heat; and the 1850-1900 mean
## being ~0 is the FRAME check -- a file still on MAGICC's native 1750 zero would sail past
## every other gate here while putting the whole run on the wrong frame (it would miss by
## ~0.1-0.3 K, so 1e-9 discriminates by eight orders of magnitude).
if CLIMATE == "magicc"
    length(CFG) == MAGICC_N || error("[CLIMATE-SOURCE] $(length(CFG)) members, expected $(MAGICC_N)")
    let ib = findall(y -> 1850 <= y <= 1900, YEARS),
        w = maximum(abs(mean(Float64[CG[i, c] for i in ib])) for c in CFG)
        @printf("[CLIMATE-SOURCE] %d members, max |mean GMST 1850-1900| = %.3e degC (tol 1e-09)  %s\n",
                length(CFG), w, w <= 1e-9 ? "PASS" : "FAIL")
        w <= 1e-9 || error("[CLIMATE-SOURCE] the GMST files are not on the 1850-1900 frame")
    end
end
const MEAN_G = lc(joinpath(OBS, "fair_mean_gmst_$(SSP).csv"), "gmst_C")
const MEAN_O = lc(joinpath(OBS, "fair_mean_ohc_$(SSP).csv"),  "ohc_1e22J")

"""Ladrillo's `spliced` convention: our own mean path through SPLICE_YEAR, then the
config's anomaly re-referenced to its own BASE0-BASE1 mean. Uncertainty enters the
FUTURE only, because the posterior was calibrated on the shipped historical driver."""
function convention(raw::Vector{Float64}, mean_path::Vector{Float64})
    mref, cref = mean(mean_path[IREF]), mean(raw[IREF])
    [y <= SPLICE_YEAR ? mean_path[i] : mref + (raw[i] - cref) for (i, y) in enumerate(YEARS)]
end
gmst_of(c) = convention(Float64.(CG[!, c]), MEAN_G)
ohc_of(c)  = convention(Float64.(CO[!, c]), MEAN_O)

## [SPLICE-MATCH] where a python-spliced cube exists, the Julia splice must reproduce it.
let ref = joinpath(OBS, "fair_cube_gmst_$(SSP)_spliced.csv")
    ## ⚠ NOT APPLICABLE on the MAGICC arm: the python reference cube is a FaIR product, so
    ## there is nothing for a MAGICC-driven splice to reproduce. Stated, never silently skipped.
    if CLIMATE != "fair"
        @printf("[SPLICE-MATCH] NOT APPLICABLE -- climate=%s, the reference cube is a FaIR product\n", CLIMATE)
    elseif isfile(ref)
        R = CSV.read(ref, DataFrame)
        w = maximum(maximum(abs.(gmst_of(c) .- Float64.(R[!, c]))) for c in CFG)
        @printf("[SPLICE-MATCH] max |julia splice - python cube| = %.3e degC (tol %.0e)  %s\n",
                w, SPLICE_MATCH_TOL, w <= SPLICE_MATCH_TOL ? "PASS" : "FAIL")
        @assert w <= SPLICE_MATCH_TOL "the Julia splice does not reproduce the committed cube"
    else
        @printf("[SPLICE-MATCH] no python-spliced cube for %s -- convention UNVERIFIED here\n", SSP)
    end
end

## ---- posterior: the SAME thinning the shipped panel used -----------------
post = CSV.read(POST, DataFrame)
const STEPP = max(1, nrow(post) ÷ NDRAW)
const ROWS  = collect(1:STEPP:nrow(post))
@printf("BRICK 2.0 + FaIR CLIMATE UNCERTAINTY | %s | %d draws (thinned from %d) | %d configs\n",
        SSP, length(ROWS), nrow(post), length(CFG)); flush(stdout)

## draw -> config, seeded permutation (Ladrillo's recipe)
const ASSIGN = let rng = MersenneTwister(PAIR_SEED)
    a = Int[]; while length(a) < length(ROWS); append!(a, randperm(rng, length(CFG))); end
    a[1:length(ROWS)]
end
const CFG_OF_DRAW = [CFG[i] for i in ASSIGN]

const OI = [idx(y) for y in HORIZONS]
## ⚠ THE FULL YEAR AXIS IS STORED, NOT JUST THE THREE HORIZON SLICES (2026-08-31).
## This driver used to allocate `length(ROWS) x length(HORIZONS)` and emit only cells and
## draws, which meant BRICK 2.0 had NO joint-arm TIME SERIES for any scenario or marker --
## so every trajectory figure had to fall back on the DECADAL fixed-arm
## ssps_components_2300_oldbrick.csv for the SSPs, and had nothing at all for van Vuuren.
## Storing the whole axis costs ~43 MB at NDRAW=1000 and lets this driver emit `paths` in
## the SAME schema as scope_slr_fair_uncertainty.jl, so a figure can read either model
## through one code path. The horizon columns are now INDEXED OUT of the full matrix
## (`[:, OI[j]]`), so cells and draws are unchanged -- verified bit-identical.
alloc() = Dict(c => Matrix{Float64}(undef, length(ROWS), length(YEARS)) for c in COMPS)

Random.seed!(SEED)
const M = MimiBRICK.get_model(ssprcp_scenario="ssp245", start_year=Y0, end_year=Y1)

"""Run draw indices `ks` on forcing (g,o); write the FULL year axis into `store`."""
function run_into!(store, ks, g, o)
    set_forcing!(M, g, o)
    for k in ks
        update_brick_params!(M, post[ROWS[k], :]; precip_log=true)
        run(M)
        ais  = reref(M[:antarctic_icesheet,     :ais_sea_level])
        gsic = reref(M[:glaciers_small_icecaps, :gsic_sea_level])
        gis  = reref(M[:greenland_icesheet,     :greenland_sea_level])
        te   = reref(M[:thermal_expansion,      :te_sea_level])
        lws  = reref(M[:landwater_storage,      :lws_sea_level])
        store["ais"][k,:]=ais; store["glaciers"][k,:]=gsic; store["gis"][k,:]=gis
        store["te"][k,:]=te;   store["lws"][k,:]=lws
        store["total"][k,:] = ais .+ gsic .+ gis .+ te .+ lws
    end
end

@printf("  arm `fixed` (shipped MEAN driver) ...\n"); flush(stdout)
const FIXED = alloc()
@time run_into!(FIXED, 1:length(ROWS), MEAN_G, MEAN_O)

@printf("  arm `joint` (one FaIR config per draw) ...\n"); flush(stdout)
const JOINT = alloc()
@time let groups = Dict{String,Vector{Int}}()
    for k in 1:length(ROWS); push!(get!(groups, CFG_OF_DRAW[k], Int[]), k); end
    for (c, ks) in groups; run_into!(JOINT, ks, gmst_of(c), ohc_of(c)); end
end

## ---- [CONTROL] the fixed arm must reproduce the shipped panel ------------
## ⚠ The shipped panel covers the CMIP6 SSPs only. A van Vuuren marker
## (--ssp=vvH etc.) has no row in it, and `SSP_LABEL[SSP]` used to throw a
## KeyError on any such key. The control is a check on the fixed-arm CODE PATH,
## which is scenario-independent, so a van Vuuren run inherits the SSP runs'
## verification -- but it must SAY so rather than quietly compare nothing. The
## `nchk == 0` error below stays exactly as it was for scenarios that DO have a
## panel: skipping is allowed only where a panel provably cannot exist.
if !haskey(SSP_LABEL, SSP)
    @printf("  [CONTROL] SKIPPED -- %s has no shipped panel row (the panel covers %s).\n",
            SSP, join(sort(collect(keys(SSP_LABEL))), ", "))
    @printf("            The fixed-arm code path is verified by those runs, NOT by this one.\n")
else
let shipped = CSV.read(joinpath(REPO, "outputs/ssps_components_2300_oldbrick.csv"), DataFrame),
    nbad = 0, nchk = 0
    for (j, H) in enumerate(HORIZONS), c in COMPS
        r = shipped[(shipped.year .== H) .& (shipped.ssp .== SSP_LABEL[SSP]) .&
                    (shipped.component .== c), :]
        nrow(r) == 1 || continue
        nchk += 1
        ## ⛔ FIXED 2026-09-04: this read `FIXED[c][:, j]` -- raw j in 1:3, i.e. years
        ## 1850/1851/1852 -- ever since the 2026-08-31 refactor widened these matrices from
        ## `length(ROWS) x length(HORIZONS)` to the full year axis. `cells` and `draws` were
        ## moved to `OI[j]` and verified bit-identical; THIS GATE WAS NOT. It therefore
        ## compared the model's first three simulated years against 2100/2150/2300 shipped
        ## values and reported "18 cells, 18 over tolerance" on EVERY scenario -- identical
        ## numbers for ssp126 and ssp585, which is what exposed it. ⚠ It is NON-FATAL
        ## (only `nchk == 0` raises), which is why four days of runs carried a failing
        ## control without stopping. The MODEL was never wrong: the cells it writes already
        ## match the shipped panel to 3 dp.
        d = median(FIXED[c][:, OI[j]]) - r.med[1]
        v = abs(d) < CONTROL_TOL_CM ? "PASS" : "CHECK"
        v == "CHECK" && (nbad += 1)
        @printf("  [CONTROL] %-8s @%d  fixed %9.3f vs shipped %9.3f  diff %+8.4f -> %s\n",
                c, H, median(FIXED[c][:, OI[j]]), r.med[1], d, v)
    end
    nchk == 0 && error("[CONTROL] compared ZERO cells -- vacuous, not passing.")
    @printf("  [CONTROL] %d cells compared, %d over tolerance\n", nchk, nbad)
end
end

## ---- output, in the Ladrillo joint schema so the comparison can read it --
draws = DataFrame(draw=Int[], config=String[], component=String[], horizon=Int[],
                  arm=String[], value_cm=Float64[])
cells = DataFrame(ssp=String[], component=String[], horizon=Int[], arm=String[],
                  n_draws=Int[], med_cm=Float64[], mean_cm=Float64[],
                  p05_cm=Float64[], p95_cm=Float64[], spread_cm=Float64[],
                  spread_ratio=Float64[], med_ratio=Float64[])
@printf("\n%s\nBRICK 2.0 WITH vs WITHOUT FaIR CLIMATE UNCERTAINTY -- %s, cm rel %d-%d\n%s\n",
        repeat("=",84), SSP, BASE0, BASE1, repeat("=",84))
@printf("  %-9s %-6s %-6s %9s %9s %9s %9s %11s\n","comp","horiz","arm","median","p05","p95","spread","x fixed")
for c in COMPS, (j,H) in enumerate(HORIZONS)
    f = FIXED[c][:, OI[j]]; sf = quantile(f,0.95) - quantile(f,0.05)
    for (arm, A) in (("fixed",FIXED[c]), ("joint",JOINT[c]))
        v = A[:, OI[j]]; sp = quantile(v,0.95) - quantile(v,0.05)
        push!(cells, (SSP, c, H, arm, length(v), median(v), mean(v),
                      quantile(v,0.05), quantile(v,0.95), sp, sp/sf, median(v)/median(f)))
        for k in 1:length(ROWS)
            push!(draws, (k, arm == "joint" ? CFG_OF_DRAW[k] : "MEAN", c, H, arm, A[k,OI[j]]))
        end
        @printf("  %-9s %-6d %-6s %9.2f %9.2f %9.2f %9.2f %10.2fx\n",
                c, H, arm, median(v), quantile(v,0.05), quantile(v,0.95), sp, sp/sf)
    end
end
CSV.write(joinpath(REPO,"outputs","scope_slr_fairunc_draws_$(SSP)_spliced_oldbrick$(CLIM_TAG).csv"), draws)
CSV.write(joinpath(REPO,"outputs","scope_slr_fairunc_cells_$(SSP)_spliced_oldbrick$(CLIM_TAG).csv"), cells)

## ---- paths: the SAME schema scope_slr_fair_uncertainty.jl writes, so a figure reads
## both models through one code path. Starts at 1990 for the same reason it does there.
paths = DataFrame(year=Int[], component=String[], arm=String[],
                  med_cm=Float64[], p05_cm=Float64[], p95_cm=Float64[])
for c in COMPS, (arm, A) in (("fixed",FIXED[c]), ("joint",JOINT[c])), (i,y) in enumerate(YEARS)
    y < 1990 && continue
    v = A[:, i]
    push!(paths, (y, String(c), arm, median(v), quantile(v,0.05), quantile(v,0.95)))
end
CSV.write(joinpath(REPO,"outputs","scope_slr_fairunc_paths_$(SSP)_spliced_oldbrick$(CLIM_TAG).csv"), paths)
@printf("\nwrote outputs/scope_slr_fairunc_{draws,cells,paths}_%s_spliced_oldbrick%s.csv\n", SSP, CLIM_TAG)
