## ============================================================================
## diag_slr_convergence_by_chain_extc.jl — deliverable convergence for extC
## chains (3-reservoir sampled-amp glacier block; 52-param chains).
##
## REPLACES diag_slr_convergence_by_chain.jl for extC-family tags (the old file
## keeps the 2-tau mapping for ext/extA108-era chains). Same method: per chain,
## thin the post-burn half to ~N_TARGET draws, push each through BRICK, compute
## rank-normalized split R-hat / ESS on projected SLR @2100/@2150.
##
## extC specifics:
##   - build_brick_nu3 to 2150; nu_b FIXED at the obsfit-anchored values
##     (the calibrator's FIT_BASIS in sampled mode; extc_block_constants.csv);
##   - per-block glacier params from chain columns (gic_a_*, gic_b_*,
##     gic_T_off_*; kappa = 10^gic_log10_kappa_* per draw);
##   - per-DRAW per-block drivers: t_glac_blocks.csv obs (to 2024) + sampled
##     gic_amp_* x ssp245harm GMST splice extended to 2150 (anchor-preserving,
##     11-yr window; offset is linear in amp so the rebuild is a cheap vector op);
##   - F_unch is a hindcast-target construct (flat after 2005): excluded from
##     the projected deliverable (its only effect rel 1995-2014 is a ~1 mm
##     baseline sliver, identical across chains — irrelevant to R-hat).
##
##   julia --project=julia_v2 julia/diag_slr_convergence_by_chain_extc.jl [n_per_chain] --tag=extC
## ============================================================================

using CSV, DataFrames, Mimi, MimiBRICK, Statistics, Printf, MCMCDiagnosticTools
include(joinpath(@__DIR__, "brick_mengel.jl"))

const REPO   = abspath(joinpath(@__DIR__, ".."))
const OBS    = joinpath(REPO, "data/observations")
const Y0, Y1 = 1850, 2150
const REF0, REF1 = 1995, 2014
const HORIZONS   = [2100, 2150]
const SEEDS      = [2026, 2027, 2028, 2029]
const NITER      = 2000000
const CHAIN_TAG  = let i = findfirst(a -> startswith(a, "--tag="), ARGS)
    i === nothing ? "extC" : ARGS[i][7:end]
end
const NBURN      = 1000000
const N_TARGET   = let p = findfirst(a -> !startswith(a, "--"), ARGS)
    p === nothing ? 400 : parse(Int, ARGS[p])
end
const FORCING_TAG = "ssp245harm"

years = collect(Y0:Y1)
tidx(y) = findfirst(==(y), years)
const IREF = [tidx(y) for y in REF0:REF1]

lc(p, c) = (d = CSV.read(p, DataFrame); Dict(Int(d[i, "year"]) => Float64(d[i, c]) for i in 1:nrow(d)))
gmst = [lc(joinpath(OBS, "fair_mean_gmst_$(FORCING_TAG).csv"), "gmst_C")[y]  for y in years]
ohc  = [lc(joinpath(OBS, "fair_mean_ohc_$(FORCING_TAG).csv"),  "ohc_1e22J")[y] for y in years]

## ---- non-glacier FREE mapping (verbatim from the 2-tau diag / calibrator) --
const G = :glaciers_small_icecaps
const A = :antarctic_icesheet
const FREE = [
    ("ais_ocean_temperature₀",   A, :ais_ocean_temperature₀),
    ("antarctic_alpha",          A, :ais_α),
    ("antarctic_nu",             A, :ais_ν),
    ("antarctic_temp_threshold", A, :temperature_threshold),
    ("anto_alpha",  :antarctic_ocean,    :anto_α),
    ("anto_beta",   :antarctic_ocean,    :anto_β),
    ("greenland_a",     :greenland_icesheet, :greenland_a),
    ("greenland_b",     :greenland_icesheet, :greenland_b),
    ("greenland_alpha", :greenland_icesheet, :greenland_α),
    ("greenland_beta",  :greenland_icesheet, :greenland_β),
    ("greenland_v0",    :greenland_icesheet, :greenland_v₀),
    ("thermal_alpha",   :thermal_expansion,  :te_α),
    ("antarctic_lambda", A, :λ),
    ("antarctic_gamma",  A, :ais_γ),
    ("antarctic_kappa",  A, :ais_κ),
    ("ais_mu",          A, :ais_μ),
    ("ais_bedheight0",  A, :ais_bedheight₀),
    ("ais_slope",       A, :ais_slope),
    ("ais_iceflow0",    A, :ais_iceflow₀),
    ("ais_precip0_LOG", A, :ais_precipitation₀),   # log-space -> assign directly
    ("ais_c",           A, :ais_c),
]
const FREE_NAMES = [f[1] for f in FREE]
const C_COL     = findfirst(==("ais_c"), FREE_NAMES)
const AIS_TANT0 = -15.42 / 0.8365
const BLOCKS = ["R19", "SLOWP", "FAST"]
const GIC_DIRECT = vcat([["gic_a_$b", "gic_b_$b", "gic_T_off_$b"] for b in BLOCKS]...)
const GIC_SYMS   = Dict(nm => Symbol(nm) for nm in GIC_DIRECT)
const DERIVED_COLS = vcat(["ais_runoff_Ton", "ais_gmst_amp"],
                          ["gic_log10_kappa_$b" for b in BLOCKS],
                          ["gic_amp_$b" for b in BLOCKS])

## ---- per-block driver machinery (obs part fixed; splice tail linear in amp) --
bc = CSV.read(joinpath(REPO, "outputs/extc_block_constants.csv"), DataFrame)
bcrow(b) = bc[findfirst(==(b), bc.block), :]
const NU_FIXED = Dict(b => Float64(bcrow(b).nu_anch_obsfit) for b in BLOCKS)
tgb = CSV.read(joinpath(REPO, "data/observations/t_glac_blocks.csv"), DataFrame)
const TGB_LAST = Int(maximum(tgb.year))
const IB5900 = findall(y -> 1850 <= y <= 1900, years)
gmst_rb = gmst .- mean(gmst[IB5900])
const ANCHOR = (TGB_LAST-10):TGB_LAST
const GM_ANCH = mean(gmst_rb[[tidx(y) for y in ANCHOR]])
const OBS_MASK = years .<= TGB_LAST
obs_part = Dict{String,Vector{Float64}}()
obs_anch = Dict{String,Float64}()
for b in BLOCKS
    d = Dict(Int(tgb[i, :year]) => Float64(tgb[i, b]) for i in 1:nrow(tgb))
    obs_part[b] = [get(d, y, 0.0) for y in years]
    obs_anch[b] = mean(d[y] for y in ANCHOR)
end
driver_of(b, amp) = ifelse.(OBS_MASK, obs_part[b],
                            amp .* gmst_rb .+ (obs_anch[b] - amp * GM_ANCH))

## ---- model base ----------------------------------------------------------
medoid = CSV.read(joinpath(REPO, "outputs/recalib_central_row.csv"), DataFrame)[1, :]
m = build_brick_nu3(ssp="ssp245", y0=Y0, y1=Y1)
gic3_init = (; (Symbol(b) => (a=Float64(bcrow(b).a0), b=Float64(bcrow(b).b_fit_obsfit),
                              T_off=Float64(bcrow(b).T_off_fit_obsfit),
                              kappa=Float64(bcrow(b).kappa_anch_obsfit),
                              nu=NU_FIXED[b]) for b in BLOCKS)...)
update_brick_nu3!(m, medoid, gic3_init; precip_log=true)
set_forcing!(m, gmst, ohc)

@printf("extC SLR convergence-by-chain diagnostic (3-reservoir sampled-amp)\n")
@printf("  window %d-%d | forcing %s | drivers t_glac_blocks + per-draw amp splice\n",
        Y0, Y1, FORCING_TAG)
@printf("  rebaseline %d-%d | burn = first %d of %d | tag=%s\n\n",
        REF0, REF1, NBURN, NITER, CHAIN_TAG)

## ---- per-chain forward runs ----------------------------------------------
slr = Dict(y => Vector{Float64}[] for y in HORIZONS)
chain_labels = String[]
t00 = time()
for sd in SEEDS
    f = joinpath(REPO, "outputs/mcmc", "chain_$(CHAIN_TAG)_seed$(sd)_n$(NITER).csv")
    isfile(f) || error("missing chain file $f")
    allcols = vcat(FREE_NAMES, GIC_DIRECT, DERIVED_COLS)
    df = CSV.read(f, DataFrame; select=allcols)
    nrow(df) == NITER || error("$(basename(f)): expected $NITER rows, got $(nrow(df))")
    step = max(1, (nrow(df) - NBURN) ÷ N_TARGET)
    rows = collect((NBURN + 1):step:nrow(df))[1:N_TARGET]
    draws = Matrix{Float64}(df[rows, FREE_NAMES])
    gdirect = Matrix{Float64}(df[rows, GIC_DIRECT])
    ton  = Float64.(df[rows, "ais_runoff_Ton"])
    amp  = Float64.(df[rows, "ais_gmst_amp"])
    k10  = Dict(b => Float64.(df[rows, "gic_log10_kappa_$b"]) for b in BLOCKS)
    bamp = Dict(b => Float64.(df[rows, "gic_amp_$b"]) for b in BLOCKS)
    df = nothing; GC.gc()

    n = size(draws, 1)
    lev = fill(NaN, n, length(years))
    t0 = time()
    for i in 1:n
        @inbounds for k in eachindex(FREE)
            update_param!(m, FREE[k][2], FREE[k][3], draws[i, k])
        end
        @inbounds for (j, nm) in enumerate(GIC_DIRECT)
            update_param!(m, G, GIC_SYMS[nm], gdirect[i, j])
        end
        for b in BLOCKS
            update_param!(m, G, Symbol("gic_kappa_$b"), 10.0^k10[b][i])
            update_param!(m, G, Symbol("glacier_surface_temperature_$b"),
                          driver_of(b, bamp[b][i]))
        end
        update_param!(m, A, :ais_runoffline_snowheight₀, -ton[i] * draws[i, C_COL])
        update_param!(m, A, :ais_temperature_coefficient, 1.0 / amp[i])
        update_param!(m, A, :ais_temperature_intercept, -AIS_TANT0 / amp[i])
        run(m)
        lev[i, :] = 100 .* m[:global_sea_level, :sea_level_rise]
    end
    ref = vec(mean(lev[:, IREF], dims=2))
    for y in HORIZONS
        push!(slr[y], lev[:, tidx(y)] .- ref)
    end
    push!(chain_labels, "seed$(sd)")
    @printf("  seed%d: %d draws (thin %d, rows %d..%d)  %.0fs\n",
            sd, n, step, rows[1], rows[end], time() - t0)
end
@printf("  total %.0fs\n", time() - t00)

## ---- distribution + convergence tables (unchanged method) ----------------
q(v, p) = quantile(v, p)
for y in HORIZONS
    @printf("\nSLR @%d (cm, rel. %d-%d)\n", y, REF0, REF1)
    @printf("  %-10s %8s %8s %8s %8s %8s\n", "chain", "q05", "q50", "q95", "mean", "sd")
    for (ci, lab) in enumerate(chain_labels)
        v = slr[y][ci]
        @printf("  %-10s %8.2f %8.2f %8.2f %8.2f %8.2f\n",
                lab, q(v, 0.05), q(v, 0.50), q(v, 0.95), mean(v), std(v))
    end
    pooled = vcat(slr[y]...)
    @printf("  %-10s %8.2f %8.2f %8.2f %8.2f %8.2f\n",
            "POOLED", q(pooled, 0.05), q(pooled, 0.50), q(pooled, 0.95), mean(pooled), std(pooled))
end

@printf("\n%s\n", "="^78)
@printf("CROSS-CHAIN CONVERGENCE OF PROJECTED SLR  (%d chains x %d thinned draws)\n",
        length(SEEDS), N_TARGET)
@printf("%s\n", "="^78)
@printf("  %-14s %8s %10s %12s %12s %10s\n",
        "quantity", "R-hat", "ESS", "sd(medians)", "mean(sd_wc)", "ratio")
diag_rows = DataFrame(horizon=Int[], rhat=Float64[], ess=Float64[],
                      sd_medians=Float64[], mean_sd_wc=Float64[],
                      n_chains=Int[], n_per_chain=Int[], niter=Int[])
for y in HORIZONS
    arr = reduce(hcat, slr[y])
    r = rhat(arr)
    e = ess(arr; maxlag = size(arr, 1))
    meds   = [median(c) for c in slr[y]]
    sd_wc  = mean([std(c) for c in slr[y]])
    sd_med = std(meds)
    @printf("  SLR@%-10d %8.3f %10.1f %12.3f %12.3f %10.3f\n",
            y, r, e, sd_med, sd_wc, sd_med / sd_wc)
    push!(diag_rows, (y, r, e, sd_med, sd_wc, length(SEEDS), N_TARGET, NITER))
end
slr_csv = joinpath(REPO, "outputs/mcmc/slr_convergence_$(CHAIN_TAG).csv")
CSV.write(slr_csv, diag_rows)
println("\nWrote $slr_csv")
@printf("\nVERDICT: %s\n",
        all(r < 1.05 for r in diag_rows.rhat) ?
        "projected SLR IS converged across chains (R-hat < 1.05 at all horizons)" :
        "projected SLR is NOT converged across chains (R-hat >= 1.05 at some horizon)")
