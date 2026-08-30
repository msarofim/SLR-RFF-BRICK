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
const CG = CSV.read(joinpath(OBS, "fair_cube_gmst_$(SSP)_raw.csv"), DataFrame)
const CO = CSV.read(joinpath(OBS, "fair_cube_ohc_$(SSP)_raw.csv"),  DataFrame)
const CFG = [c for c in String.(propertynames(CG)) if startswith(c, "cfg_")]
@assert Int.(CG.year) == YEARS "the gmst cube's year axis is not $(Y0):$(Y1)"
@assert String.(propertynames(CO))[2:end] == CFG "gmst and ohc cubes disagree on configs"
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
    if isfile(ref)
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
alloc() = Dict(c => Matrix{Float64}(undef, length(ROWS), length(HORIZONS)) for c in COMPS)

Random.seed!(SEED)
const M = MimiBRICK.get_model(ssprcp_scenario="ssp245", start_year=Y0, end_year=Y1)

"""Run draw indices `ks` on forcing (g,o); write horizon slices into `store`."""
function run_into!(store, ks, g, o)
    set_forcing!(M, g, o)
    for k in ks
        update_brick_params!(M, post[ROWS[k], :]; precip_log=true)
        run(M)
        ais  = reref(M[:antarctic_icesheet,     :ais_sea_level])[OI]
        gsic = reref(M[:glaciers_small_icecaps, :gsic_sea_level])[OI]
        gis  = reref(M[:greenland_icesheet,     :greenland_sea_level])[OI]
        te   = reref(M[:thermal_expansion,      :te_sea_level])[OI]
        lws  = reref(M[:landwater_storage,      :lws_sea_level])[OI]
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
let shipped = CSV.read(joinpath(REPO, "outputs/ssps_components_2300_oldbrick.csv"), DataFrame),
    nbad = 0, nchk = 0
    for (j, H) in enumerate(HORIZONS), c in COMPS
        r = shipped[(shipped.year .== H) .& (shipped.ssp .== SSP_LABEL[SSP]) .&
                    (shipped.component .== c), :]
        nrow(r) == 1 || continue
        nchk += 1
        d = median(FIXED[c][:, j]) - r.med[1]
        v = abs(d) < CONTROL_TOL_CM ? "PASS" : "CHECK"
        v == "CHECK" && (nbad += 1)
        @printf("  [CONTROL] %-8s @%d  fixed %9.3f vs shipped %9.3f  diff %+8.4f -> %s\n",
                c, H, median(FIXED[c][:, j]), r.med[1], d, v)
    end
    nchk == 0 && error("[CONTROL] compared ZERO cells -- vacuous, not passing.")
    @printf("  [CONTROL] %d cells compared, %d over tolerance\n", nchk, nbad)
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
    f = FIXED[c][:, j]; sf = quantile(f,0.95) - quantile(f,0.05)
    for (arm, A) in (("fixed",FIXED[c]), ("joint",JOINT[c]))
        v = A[:, j]; sp = quantile(v,0.95) - quantile(v,0.05)
        push!(cells, (SSP, c, H, arm, length(v), median(v), mean(v),
                      quantile(v,0.05), quantile(v,0.95), sp, sp/sf, median(v)/median(f)))
        for k in 1:length(ROWS)
            push!(draws, (k, arm == "joint" ? CFG_OF_DRAW[k] : "MEAN", c, H, arm, A[k,j]))
        end
        @printf("  %-9s %-6d %-6s %9.2f %9.2f %9.2f %9.2f %10.2fx\n",
                c, H, arm, median(v), quantile(v,0.05), quantile(v,0.95), sp, sp/sf)
    end
end
CSV.write(joinpath(REPO,"outputs","scope_slr_fairunc_draws_$(SSP)_spliced_oldbrick.csv"), draws)
CSV.write(joinpath(REPO,"outputs","scope_slr_fairunc_cells_$(SSP)_spliced_oldbrick.csv"), cells)
@printf("\nwrote outputs/scope_slr_fairunc_{draws,cells}_%s_spliced_oldbrick.csv\n", SSP)
