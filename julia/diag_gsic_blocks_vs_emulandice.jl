## ============================================================================
## diag_gsic_blocks_vs_emulandice.jl — Ladrillo's three glacier reservoirs on the
## SHARED FACTS climate, sample-matched to emulandice.
##
## THE QUESTION (Marcus 2026-09-14). Ladrillo projects ~25% less glacier melt at 2100
## than emulandice (the GlacierMIP2-trained GP that FACTS runs) on every scenario. Is
## that one block or all three, and is it the driver or the module? emulandice is
## GSAT-driven and ran on facts/experiments/global.shared.<scen>.n200 — 200 configs of
## the same FaIR cube, same 2014 splice, same 1995-2014 reference Ladrillo uses. So
## sample k of emulandice and sample k here saw the SAME GSAT path, and any residual
## is the glacier model (law, commitment, response time, regional amplification,
## initial disequilibrium), not the climate.
##
## ARMS.
##   joint  : posterior draw k on shared sample k (climate + parameter spread) — the
##            like-for-like arm against emulandice's climate + GP sampling.
##   fixed  : every draw on the MEAN of the 200 shared paths (parameter spread only),
##            so joint-minus-fixed is the climate's share of the spread.
##   joint_cmip6amp : joint with the per-block amplification overridden by the CMIP6
##            regional-characteristic ratio (see the arm's comment) — the driver lever.
## Draws: NDRAW rows of the canonical L24 subsample chosen by a SEEDED permutation;
## the seed and the row index of every draw are written into the output.
##
## OUTPUT (cm SLE, cumulative melt since the model start, i.e. NOT re-referenced;
## the python side rebases both models to FACTS's base year 2005):
##   outputs/diag_emu_blocks/ladrillo_blocks_<scen>.csv
##   columns scen, arm, sample, draw_row, block (R19/SLOWP/FAST), year, melt_cm
##   + ladrillo_blocks_<scen>_provenance.txt (driver, posterior, seed, climate, units)
##
##   julia --project=julia_v2 julia/diag_gsic_blocks_vs_emulandice.jl --scen=ssp245 [--ndraw=200] [--seed=2026]
## Needs outputs/diag_emu_blocks/shared_<scen>_{gmst,ohc}.csv from
## python/dump_shared_climate_for_blocks.py.
## ============================================================================
using CSV, DataFrames, Mimi, Printf, Statistics, Random
include(joinpath(@__DIR__, "ladrillo_projection.jl"))

_argval(p) = (i = findfirst(a -> startswith(a, p), ARGS); i === nothing ? nothing : ARGS[i][length(p)+1:end])
const SCEN  = something(_argval("--scen="), "ssp245")
const NDRAW = parse(Int, something(_argval("--ndraw="), "200"))
const SEED  = parse(Int, something(_argval("--seed="), "2026"))
const DIR   = joinpath(LADRILLO_REPO, "outputs/diag_emu_blocks")
const OUT   = joinpath(DIR, "ladrillo_blocks_$(SCEN).csv")
const YEARS_OUT = vcat(collect(2005:5:2100), [2150, 2300])
const SLOTS = ("R19" => :gsic_r19, "SLOWP" => :gsic_slowp, "FAST" => :gsic_fast)
const Y0, Y1 = 1850, 2300

cg = CSV.read(joinpath(DIR, "shared_$(SCEN)_gmst.csv"), DataFrame)
co = CSV.read(joinpath(DIR, "shared_$(SCEN)_ohc.csv"), DataFrame)
@assert Int.(cg.year) == collect(Y0:Y1) "gmst dump is not $(Y0):$(Y1)"
@assert names(cg) == names(co) "gmst/ohc dumps disagree on samples"
const SAMPLES = [c for c in names(cg) if startswith(c, "s")]
const NS = length(SAMPLES)
NS >= NDRAW || error("only $(NS) shared samples, asked for $(NDRAW) draws")
gpath(k) = Float64.(cg[!, SAMPLES[k]])
opath(k) = Float64.(co[!, SAMPLES[k]])
const MEAN_G = vec(mean(Matrix(cg[!, SAMPLES]), dims=2))
const MEAN_O = vec(mean(Matrix(co[!, SAMPLES]), dims=2))

## ---- draws: seeded permutation of the canonical subsample ------------------
post = ladrillo_posterior()
const DRAW_ROWS = randperm(MersenneTwister(SEED), nrow(post))[1:NDRAW]
const VARIANT = ladrillo_posterior_variant()
const PROV = "driver=diag_gsic_blocks_vs_emulandice.jl; posterior=$(basename(LADRILLO_POSTERIOR_CSV)) " *
             "($(nrow(post)) rows); draws=$(NDRAW) by randperm(MersenneTwister($(SEED))) applied " *
             "immediately before the draw selection; climate=shared_$(SCEN) (FACTS global.shared." *
             "$(SCEN).n200 input, spliced@2014, ref 1995-2014, K rel 1850-1900); run $(Y0)-$(Y1); " *
             "units cm SLE cumulative melt since $(Y0) (no re-referencing); nu basis $(LADRILLO_NU_BASIS)"

@printf("Ladrillo glacier blocks on the shared FACTS climate | %s | %d samples, %d draws (seed %d)\n",
        SCEN, NS, NDRAW, SEED)
@printf("  GMST@2100 over the samples: median %.2f [%.2f, %.2f] K; mean path %.2f\n",
        median([gpath(k)[end-200] for k in 1:NS]), quantile([gpath(k)[end-200] for k in 1:NS], 0.05),
        quantile([gpath(k)[end-200] for k in 1:NS], 0.95), MEAN_G[end-200])
flush(stdout)

rows = DataFrame(scen=String[], arm=String[], sample=Int[], draw_row=Int[], block=String[],
                 year=Int[], melt_cm=Float64[])

function record!(bf, arm, k, drow)
    for (b, slot) in SLOTS
        s = Float64.(bf.m[:glaciers_small_icecaps, slot])   # m SLE since 1850, raw
        for y in YEARS_OUT
            push!(rows, (SCEN, arm, k, drow, b, y, 100.0 * s[ladrillo_yi(bf, y)]))
        end
    end
end

## arm `fixed`: every draw on the ensemble-mean shared path
let bf = ladrillo_setup(ssp="ssp245", y0=Y0, y1=Y1, gis_variant=VARIANT, gmst=MEAN_G, ohc=MEAN_O)
    @printf("  arm fixed ... "); flush(stdout)
    for k in 1:NDRAW
        ladrillo_run_draw!(bf, post[DRAW_ROWS[k], :])
        record!(bf, "fixed", k, DRAW_ROWS[k])
    end
    println("done")
end
## arm `joint`: draw k on shared sample k (one model build per sample)
## arm `joint_cmip6amp`: the same, with every draw's per-block amplification REPLACED by
## the CMIP6 regional-characteristic ratio (`amp_regchar` in extc_block_constants.csv:
## the GCM-pattern value a GSAT-driven emulator trained on GCM-forced runs implicitly
## carries). Ladrillo's fitted amps are R19 0.72 / SLOWP 2.50 / FAST 1.45 (prior centres;
## sampled per draw); the CMIP6 values are 1.03 / 1.70 / 1.23. The arm measures how much
## of any block gap is the DRIVER amplification rather than the glacier law. Projection-
## side override only (the posterior was fitted with its own amps) — a lever, not a refit.
const BC = CSV.read(LADRILLO_BLOCK_CONSTANTS_CSV, DataFrame)
const AMP_CMIP6 = Dict(String(r.block) => Float64(r.amp_regchar) for r in eachrow(BC))
@printf("  CMIP6 regional-characteristic amps: %s\n",
        join(["$(b)=$(round(AMP_CMIP6[b], digits=2))" for b in LADRILLO_BLOCKS], " "))
for (arm, override) in (("joint", false), ("joint_cmip6amp", true))
    @printf("  arm %s ... ", arm); flush(stdout)
    for k in 1:NDRAW
        bf = ladrillo_setup(ssp="ssp245", y0=Y0, y1=Y1, gis_variant=VARIANT, gmst=gpath(k), ohc=opath(k))
        one = post[DRAW_ROWS[k]:DRAW_ROWS[k], :]        # one-row copy, mutable
        if override
            for b in LADRILLO_BLOCKS; one[1, "gic_amp_$b"] = AMP_CMIP6[b]; end
        end
        ladrillo_run_draw!(bf, one[1, :])
        record!(bf, arm, k, DRAW_ROWS[k])
        k % 50 == 0 && (@printf("%d ", k); flush(stdout))
    end
    println("done")
end

mkpath(DIR)
CSV.write(OUT, rows)
## provenance ONCE per file (a per-row column made the file 17 MB; the sidecar keeps the stamp)
open(replace(OUT, ".csv" => "_provenance.txt"), "w") do io; println(io, PROV); end
## summary: 2100 melt since 2005 per block, both arms
@printf("\n  %-6s %-6s %10s %18s\n", "arm", "block", "2100-2005", "5-95%")
for arm in ("fixed", "joint", "joint_cmip6amp"), (b, _) in SLOTS
    v = [rows.melt_cm[(rows.arm .== arm) .& (rows.block .== b) .& (rows.year .== 2100) .& (rows.sample .== k)][1] -
         rows.melt_cm[(rows.arm .== arm) .& (rows.block .== b) .& (rows.year .== 2005) .& (rows.sample .== k)][1]
         for k in 1:NDRAW]
    @printf("  %-6s %-6s %10.2f  [%6.2f, %6.2f]\n", arm, b, median(v), quantile(v, 0.05), quantile(v, 0.95))
end
println("\nwrote $(relpath(OUT, LADRILLO_REPO))")
