## ============================================================================
## diag_slr_convergence_by_chain.jl  —  is the DELIVERABLE converged?
##
## Several AIS marginals in the 35-param v-next calibration are badly mixed
## (ais_iceflow0 R-hat 1.320 / ESS 10.6; antarctic_alpha 1.156; ais_precip0_LOG
## 1.118; ais_slope 1.082).  Those are strongly correlated geometry params, so a
## poorly-identified ridge in parameter space can still map onto a well-determined
## projection.  This script asks the only question that matters downstream:
##
##     is projected SSP2-4.5 SLR at 2100 / 2150 converged ACROSS the 4 chains?
##
## Method: per chain, thin the post-burn half to ~N_TARGET evenly spaced draws,
## push each draw through BRICK-Mengel, and treat each chain's SLR sample as an
## MCMC chain for rank-normalized split R-hat / ESS (MCMCDiagnosticTools, with
## maxlag = size(arr,1) exactly as postprocess_mcmc_ext.jl does).
##
## Model construction, rebaselining and unit handling mirror
## julia/project_pulse_hybrid_mengel_lvl2150.jl; the FREE parameter mapping is
## lifted verbatim from julia/calibrate_mcmc_ext.jl.
##
##   julia --project=julia_v2 julia/diag_slr_convergence_by_chain.jl [n_per_chain]
## ============================================================================

using CSV, DataFrames, Mimi, MimiBRICK, Statistics, Printf, MCMCDiagnosticTools
include(joinpath(@__DIR__, "brick_mengel.jl"))

const REPO   = abspath(joinpath(@__DIR__, ".."))
const OBS    = joinpath(REPO, "data/observations")
const Y0, Y1 = 1850, 2150
const REF0, REF1 = 1995, 2014            # rebaseline window (project_pulse_*_lvl2150.jl)
const HORIZONS   = [2100, 2150]
const SEEDS      = [2026, 2027, 2028, 2029]
const NITER      = 2000000
const NBURN      = 1000000               # discard the FIRST HALF
const N_TARGET   = length(ARGS) >= 1 ? parse(Int, ARGS[1]) : 400
# Forcing: the SAME deterministic SSP2-4.5 HARMONIZED FaIR-mean splice the calibration
# ran on (calibrate_mcmc_ext.jl FORCING_TAG). A single forcing trajectory is deliberate:
# this diagnostic isolates PARAMETER spread across chains, so any FaIR-member spread
# would be a confound.  NB this file is already in 1e22 J, so there is NO OHC x0.1 here
# (that factor in project_pulse_hybrid_mengel_lvl2150.jl converts ZJ -> 1e22 J inputs).
const FORCING_TAG = "ssp245harm"

years = collect(Y0:Y1)
tidx(y) = findfirst(==(y), years)
const IREF = [tidx(y) for y in REF0:REF1]

## ---- forcing -------------------------------------------------------------
lc(p, c) = (d = CSV.read(p, DataFrame); Dict(Int(d[i, "year"]) => Float64(d[i, c]) for i in 1:nrow(d)))
gmst = [lc(joinpath(OBS, "fair_mean_gmst_$(FORCING_TAG).csv"), "gmst_C")[y]  for y in years]
ohc  = [lc(joinpath(OBS, "fair_mean_ohc_$(FORCING_TAG).csv"),  "ohc_1e22J")[y] for y in years]

## ---- FREE mapping: chain column -> (component, symbol) -------------------
## Verbatim from calibrate_mcmc_ext.jl.  EVERY entry there is islog=false -- including
## ais_precip0_LOG, because MimiBRICK v2.0.0's AIS component computes
## exp(ais_precipitation0) internally, so the log-space chain value is assigned DIRECTLY
## (the only islog mention in that file is the comment "do NOT set islog=true here").
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
    ("gic_a", G, :gic_a), ("gic_b", G, :gic_b), ("gic_T_lia", G, :gic_T_lia),
    ("gic_f", G, :gic_f), ("gic_tau_fast", G, :gic_tau_fast), ("gic_tau_slow", G, :gic_tau_slow),
    # phase-2 A2: DAIS fast-dynamics params freed under paleo marginals
    ("antarctic_lambda", A, :λ),
    ("antarctic_gamma",  A, :ais_γ),
    ("antarctic_kappa",  A, :ais_κ),
    # v-next: the 7 DAIS geometry params are SAMPLED (were fixed at the medoid pre-v-next)
    ("ais_mu",          A, :ais_μ),
    ("ais_bedheight0",  A, :ais_bedheight₀),
    ("ais_slope",       A, :ais_slope),
    ("ais_iceflow0",    A, :ais_iceflow₀),
    ("ais_precip0_LOG", A, :ais_precipitation₀),   # log-space -> assign directly
    ("ais_c",           A, :ais_c),
    # NB ais_runoffline_snowheight₀ and ais_temperature_coefficient/intercept are NOT here:
    # they are DERIVED from the phase-2 chain columns ais_runoff_Ton and ais_gmst_amp below.
]
const FREE_NAMES = [f[1] for f in FREE]
# phase-2 A4/A6 derived columns (present in the 39-param chains, set per-draw not via FREE):
const C_COL     = findfirst(==("ais_c"), FREE_NAMES)     # ais_c index within a draw row
const AIS_TANT0 = -15.42 / 0.8365                         # preserved GMST->AIS-temp anchor
const DERIVED_COLS = ["ais_runoff_Ton", "ais_gmst_amp"]

## ---- model base: medoid for everything NOT sampled -----------------------
medoid = CSV.read(joinpath(REPO, "outputs/recalib_central_row.csv"), DataFrame)[1, :]
m = build_brick_mengel(ssp="ssp245", y0=Y0, y1=Y1)
update_brick_mengel!(m, medoid, (a=0.45, b=0.52, T_lia=-0.45, f=0.5,
                                 tau_fast=40.0, tau_slow=250.0, sl0=0.0); precip_log=true)
set_forcing!(m, gmst, ohc)

@printf("BRICK-Mengel SLR convergence-by-chain diagnostic\n")
@printf("  window %d-%d | forcing fair_mean_{gmst,ohc}_%s.csv (SSP2-4.5 harmonized, deterministic)\n",
        Y0, Y1, FORCING_TAG)
@printf("  rebaseline %d-%d mean | %d sampled params set per draw | burn = first %d of %d\n\n",
        REF0, REF1, length(FREE), NBURN, NITER)

## ---- per-chain forward runs ---------------------------------------------
slr = Dict(y => Vector{Float64}[] for y in HORIZONS)   # y -> per-chain vectors
chain_labels = String[]
t00 = time()
for sd in SEEDS
    f = joinpath(REPO, "outputs/mcmc", "chain_ext_seed$(sd)_n$(NITER).csv")
    isfile(f) || error("missing chain file $f")
    df = CSV.read(f, DataFrame; select=vcat(FREE_NAMES, DERIVED_COLS))   # sampled + derived cols
    nrow(df) == NITER || error("$(basename(f)): expected $NITER rows, got $(nrow(df))")
    # thin: evenly spaced across the POST-BURN half (not a contiguous block)
    step = max(1, (nrow(df) - NBURN) ÷ N_TARGET)
    rows = collect((NBURN + 1):step:nrow(df))[1:N_TARGET]
    draws = Matrix{Float64}(df[rows, FREE_NAMES])
    ton  = Float64.(df[rows, "ais_runoff_Ton"])
    amp  = Float64.(df[rows, "ais_gmst_amp"])
    df = nothing; GC.gc()

    n = size(draws, 1)
    lev = fill(NaN, n, length(years))
    t0 = time()
    for i in 1:n
        @inbounds for k in eachindex(FREE)
            update_param!(m, FREE[k][2], FREE[k][3], draws[i, k])
        end
        # A4: runoff line reconstructed from the identified direction (h0 = -T_on*c)
        update_param!(m, A, :ais_runoffline_snowheight₀, -ton[i] * draws[i, C_COL])
        # A6: GMST->AIS temperature map from transient amplification (anchor preserved)
        update_param!(m, A, :ais_temperature_coefficient, 1.0 / amp[i])
        update_param!(m, A, :ais_temperature_intercept, -AIS_TANT0 / amp[i])
        run(m)
        lev[i, :] = 100 .* m[:global_sea_level, :sea_level_rise]   # m -> cm
    end
    ref = vec(mean(lev[:, IREF], dims=2))                          # 1995-2014 mean, per draw
    for y in HORIZONS
        push!(slr[y], lev[:, tidx(y)] .- ref)
    end
    push!(chain_labels, "seed$(sd)")
    @printf("  seed%d: %d draws (thin %d, rows %d..%d)  %.0fs\n",
            sd, n, step, rows[1], rows[end], time() - t0)
end
@printf("  total %.0fs\n", time() - t00)

## ---- per-chain distribution table ---------------------------------------
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

## ---- cross-chain convergence on the DELIVERABLE --------------------------
## rhat/ess called exactly as postprocess_mcmc_ext.jl does (rank-normalized split
## R-hat; ESS with maxlag = size(arr,1), NOT the censored default maxlag=250).
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
    arr = reduce(hcat, slr[y])                     # draws x chains
    r = rhat(arr)
    e = ess(arr; maxlag = size(arr, 1))
    meds   = [median(c) for c in slr[y]]
    sd_wc  = mean([std(c) for c in slr[y]])        # mean WITHIN-chain sd
    sd_med = std(meds)                             # BETWEEN-chain spread of medians
    @printf("  SLR@%-10d %8.3f %10.1f %12.3f %12.3f %10.3f\n",
            y, r, e, sd_med, sd_wc, sd_med / sd_wc)
    push!(diag_rows, (y, r, e, sd_med, sd_wc, length(SEEDS), N_TARGET, NITER))
end
# Machine-readable result so postprocess_mcmc_ext.jl --accept-slr can gate the canonical
# subsample write on THIS diagnostic (accepted-on-deliverable criterion, Marcus 2026-07-19).
slr_csv = joinpath(REPO, "outputs/mcmc/slr_convergence_ext.csv")
CSV.write(slr_csv, diag_rows)
println("\nWrote $slr_csv")
@printf("\n  median range across chains:")
for y in HORIZONS
    meds = [median(c) for c in slr[y]]
    @printf("  @%d %.2f-%.2f cm (spread %.2f)", y, minimum(meds), maximum(meds),
            maximum(meds) - minimum(meds))
end
println()
@printf("\nVERDICT: %s\n",
        all(r < 1.05 for r in diag_rows.rhat) ?
        "projected SLR IS converged across chains (R-hat < 1.05 at all horizons)" :
        "projected SLR is NOT converged across chains (R-hat >= 1.05 at some horizon)")
println("\nNOTE: ESS here is computed on the THINNED (every ~$(1_000_000 ÷ N_TARGET)th) sample, so it")
println("measures residual autocorrelation AFTER thinning, not the raw-chain ESS.")
println("R-hat is thinning-invariant in expectation and is the load-bearing number.")
