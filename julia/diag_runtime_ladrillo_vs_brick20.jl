## ============================================================================
## diag_runtime_ladrillo_vs_brick20.jl — how much slower is Ladrillo than BRICK 2.0 per draw?
##
## Marcus, GMD-draft comment 2026-09-18 [13]: "Can we calculate the relative speeds of
## BRICK 2.0 to Ladrillo?"  Both models built ONCE on the same span and the same FaIR
## driver (ssp245harm), then NDRAW posterior draws applied and run in a loop, exactly as the
## production drivers do (Ladrillo: ladrillo_apply_draw! + run, which rebuilds the regional
## drivers per draw; BRICK 2.0: update_brick_params! + run). Two spans: the hindcast
## 1850-2026 and the projection 1850-2300. Wall time per draw after a warm-up draw (JIT).
## Also times run(m) ALONE (no parameter update) to separate the Mimi model from the
## per-draw driver rebuild.
##
##   julia --project=julia_v2 julia/diag_runtime_ladrillo_vs_brick20.jl [ndraw=300] [--tag=L24]
## Writes outputs/diag_runtime_ladrillo_vs_brick20_<tag>.csv (one row per model x span x mode).
## ============================================================================
using CSV, DataFrames, Dates, Mimi, MimiBRICK, Printf, Random, Statistics
include(joinpath(@__DIR__, "ladrillo_projection.jl"))

const NDRAW = let p = filter(a -> !startswith(a, "--"), ARGS); length(p) >= 1 ? parse(Int, p[1]) : 300 end
const DEFAULT_TAG = replace(replace(basename(LADRILLO_POSTERIOR_CSV),
                                    "parameters_subsample_brick_mengel_" => ""), ".csv" => "")
const POST_TAG = let i = findfirst(a -> startswith(a, "--tag="), ARGS)
    i === nothing ? DEFAULT_TAG : ARGS[i][7:end]
end
const POSTERIOR = joinpath(LADRILLO_REPO, "data/MimiBRICK/parameters_subsample_brick_mengel_$(POST_TAG).csv")
const BRICK_POSTERIOR = joinpath(LADRILLO_REPO, "data/MimiBRICK/parameters_subsample_brick.csv")
const FORCING = "ssp245harm"
const BRICK_SEED = 2026
const OUT = joinpath(LADRILLO_REPO, "outputs/diag_runtime_ladrillo_vs_brick20_$(POST_TAG).csv")   # tagged since 09-21 (the L24/L27 files before that were renamed by hand)
const SPANS = [(1850, 2026), (1850, 2300)]

lc(p, c) = (d = CSV.read(p, DataFrame); Dict(Int(d[i, "year"]) => Float64(d[i, c]) for i in 1:nrow(d)))

post  = ladrillo_posterior(path=POSTERIOR, cols=:all, nthin=NDRAW)
const VARIANT = ladrillo_posterior_variant(POSTERIOR)
bpost_full = CSV.read(BRICK_POSTERIOR, DataFrame)
bpost = let v = collect(1:cld(nrow(bpost_full), NDRAW):nrow(bpost_full)); bpost_full[v[1:min(NDRAW, length(v))], :] end

rows = DataFrame(model=String[], span=String[], mode=String[], ndraw=Int[],
                 ms_per_draw=Float64[], ms_per_draw_sd=Float64[], ms_per_draw_median=Float64[])

function timeloop(f, n)
    f()                                   # warm-up (JIT + first allocation)
    ts = Float64[]
    for _ in 1:n
        t = @elapsed f()
        push!(ts, 1e3 * t)
    end
    mean(ts), std(ts), median(ts)
end

for (y0, y1) in SPANS
    span = "$y0-$y1"
    ## ---- Ladrillo: the production per-draw path ----
    bf = ladrillo_setup(ssp="ssp245", y0=y0, y1=y1, forcing_tag=FORCING, gis_variant=VARIANT)
    k = Ref(0)
    m1, s1, d1 = timeloop(NDRAW) do
        k[] = k[] % nrow(post) + 1
        ladrillo_run_draw!(bf, post[k[], :])
    end
    push!(rows, ("Ladrillo $POST_TAG", span, "apply_draw+run", NDRAW, m1, s1, d1))
    m2, s2, d2 = timeloop(NDRAW) do; run(bf.m); end
    push!(rows, ("Ladrillo $POST_TAG", span, "run_only", NDRAW, m2, s2, d2))
    @printf("Ladrillo %s %s: apply+run %.2f ms/draw (sd %.2f), run-only %.2f ms\n", POST_TAG, span, m1, s1, m2)

    ## ---- BRICK 2.0: stock MimiBRICK v2.0.0, same forcing ----
    years = collect(y0:y1)
    gmst = [lc(joinpath(LADRILLO_OBS, "fair_mean_gmst_$(FORCING).csv"), "gmst_C")[y] for y in years]
    ohc  = [lc(joinpath(LADRILLO_OBS, "fair_mean_ohc_$(FORCING).csv"), "ohc_1e22J")[y] for y in years]
    Random.seed!(BRICK_SEED)
    m = MimiBRICK.get_model(ssprcp_scenario="ssp245", start_year=y0, end_year=y1)
    set_forcing!(m, gmst, ohc)
    j = Ref(0)
    m3, s3, d3 = timeloop(NDRAW) do
        j[] = j[] % nrow(bpost) + 1
        update_brick_params!(m, bpost[j[], :]; precip_log=true)
        run(m)
    end
    push!(rows, ("BRICK 2.0", span, "apply_draw+run", NDRAW, m3, s3, d3))
    m4, s4, d4 = timeloop(NDRAW) do; run(m); end
    push!(rows, ("BRICK 2.0", span, "run_only", NDRAW, m4, s4, d4))
    @printf("BRICK 2.0 %s: apply+run %.2f ms/draw (sd %.2f), run-only %.2f ms\n", span, m3, s3, m4)
    @printf("  ratio Ladrillo/BRICK (means): apply+run %.2fx, run-only %.2fx | (medians) %.2fx, %.2fx\n", m1 / m3, m2 / m4, d1 / d3, d2 / d4)
end

rows.provenance .= "diag_runtime_ladrillo_vs_brick20.jl | Ladrillo $POST_TAG ($(basename(POSTERIOR)), variant $VARIANT) vs " *
    "stock MimiBRICK v2.0.0 get_model(ssp245) with Random.seed!($BRICK_SEED) before get_model | forcing $FORCING " *
    "(FaIR 2.2.4 calib 1.6.0 ensemble mean) | NDRAW=$NDRAW evenly thinned draws per model, one warm-up draw excluded | " *
    "wall ms per draw, mean, sd and median | Julia $(VERSION), $(Sys.CPU_NAME), $(Sys.cpu_info()[1].model), " *
    "threads $(Threads.nthreads()) | $(Dates.now())"
CSV.write(OUT, rows)
println("wrote $(relpath(OUT, LADRILLO_REPO))")
