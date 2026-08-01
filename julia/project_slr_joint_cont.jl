## ============================================================================
## ‼ STATUS 2026-08-01: DIAGNOSTIC (supports the REJECTED joint free-forcing calibration) — see
## notes/negresult_2026-08-01_joint_forcing_calibration.md. Canonical BRICK-AM = mean-forcing
## calibrate_mcmc_ext.jl + forward-propagated FaIR uncertainty.
## project_slr_joint_cont.jl — forward-project total SLR on the continuous-joint posterior draws,
## then split-R̂ the DELIVERABLE (total SLR @ 2050/2100/2150/2300 + components @2100).
##
## Why: the raw-parameter R̂ leaves a few weakly-identified nuisance/AIS-degenerate params >1.05
## (rho_gsic 1.44, ...). The quantity we actually report is the SLR band, not those params. The ext
## (mean-forcing) calibration's SLR-deliverable R̂ was 1.003/1.002 despite the same param sloppiness —
## so this tests whether the joint bands are converged too. CRUCIAL: each draw uses its OWN forcing,
## reconstructed from its fpc scores (the coupled forcing), NOT fair_mean.
##
## Reuses calibrate_mcmc_joint_cont.jl's exact FREE list + θ→BRICK apply logic via `include` (guarded).
## Run:  julia --project=julia_v2 julia/project_slr_joint_cont.jl --amp-mu=1.08 --amp-sigma=0.15 [--smoke]
## ============================================================================
include(joinpath(@__DIR__, "calibrate_mcmc_joint_cont.jl"))   # sets up FREE, NP, NK, NPC, PCB, GS, OS,
                                                              # AMP_IDX, TON_IDX, C_IDX, AIS_TANT0, medoid, ...
using Statistics, Printf, CSV

const SMOKE   = "--smoke" in ARGS
const SEEDS   = [2026, 2027, 2028, 2029]
const NITER_P = 4_000_000
const BURN_P  = SMOKE ? 0 : NITER_P ÷ 2     # smoke: grab first rows (machinery test, not convergence)
const THIN_P  = SMOKE ? 1 : 500             # every 500th post-burn draw → ~4000/chain
const YP0, YP1 = 1850, 2300
const YRS2 = collect(YP0:YP1)
ty(y) = findfirst(==(y), YRS2)
const IB2 = [ty(y) for y in 1995:2005]      # 1995–2005 rebaseline (same as calibrator)
const HORIZONS = [2050, 2100, 2150, 2300]

# forcing basis re-sliced to the projection window (PCB is a const from the include)
const _pk2   = [findfirst(==(y), PCB.year) for y in YRS2]
const GMEAN2 = Float64.(PCB.gmean[_pk2]); const OMEAN2 = Float64.(PCB.omean[_pk2])
const GLOAD2 = [Float64.(PCB[_pk2, Symbol("Gload$k")]) for k in 1:NPC]
const OLOAD2 = [Float64.(PCB[_pk2, Symbol("Oload$k")]) for k in 1:NPC]
reconstruct2(a) = (g = copy(GMEAN2); o = copy(OMEAN2);
    @inbounds for k in 1:NPC; g .+= (GS*a[k]).*GLOAD2[k]; o .+= (OS*a[k]).*OLOAD2[k]; end; (g, o))

# projection model (1850–2300), medoid geometry + precip_log, same as calibrator's m but longer horizon
const m2 = build_brick_mengel(ssp="ssp245", y0=YP0, y1=YP1)
update_brick_mengel!(m2, medoid, (a=0.45,b=0.52,T_lia=-0.45,f=0.5,tau_fast=40.0,tau_slow=250.0,sl0=0.0); precip_log=true)
setp2!(k, v) = update_param!(m2, k.comp, k.sym, k.islog ? log(v) : v)
reref2(v) = 100 .* (v .- mean(v[IB2]))

function project(θ, a)                       # returns (tot@horizons..., ais,gsic,gis,te @2100)
    g, o = reconstruct2(a); set_forcing!(m2, g, o)
    @inbounds for k in 1:NP; (k==AMP_IDX || k==TON_IDX) && continue; setp2!(FREE[k], θ[k]); end
    update_param!(m2, :antarctic_icesheet, :ais_runoffline_snowheight₀, -θ[TON_IDX]*θ[C_IDX])
    update_param!(m2, :antarctic_icesheet, :ais_temperature_coefficient, 1.0/θ[AMP_IDX])
    update_param!(m2, :antarctic_icesheet, :ais_temperature_intercept, -AIS_TANT0/θ[AMP_IDX])
    run(m2)
    tot = reref2(m2[:global_sea_level, :sea_level_rise])
    i100 = ty(2100)
    (tot[[ty(y) for y in HORIZONS]]...,
     reref2(m2[:antarctic_icesheet, :ais_sea_level])[i100],
     reref2(m2[:glaciers_small_icecaps, :gsic_sea_level])[i100],
     reref2(m2[:greenland_icesheet, :greenland_sea_level])[i100],
     reref2(m2[:thermal_expansion, :te_sea_level])[i100])
end

function project_chain(seed)
    path = joinpath(REPO, "outputs/mcmc/chain_jcont_seed$(seed)_n$(NITER_P).csv")
    rows = Vector{NTuple{8,Float64}}()
    i = 0
    for row in CSV.Rows(path; types=Float64, reusebuffer=true)
        i += 1; d = i - 1
        (d < BURN_P || (d - BURN_P) % THIN_P != 0) && continue
        θ = ntuple(j -> Float64(row[j]), NP)
        a = ntuple(k -> Float64(row[NK+k]), NPC)
        push!(rows, project(collect(θ), collect(a)))
        SMOKE && length(rows) >= 20 && break
    end
    rows
end

println("projecting $(length(SEEDS)) chains to $YP1 (thin=$THIN_P, burn=$BURN_P)$(SMOKE ? "  [SMOKE]" : "") ...")
per = Dict{Int,Vector{NTuple{8,Float64}}}()
for s in SEEDS
    t = @elapsed per[s] = project_chain(s)
    @printf("  seed %d: %d draws  (%.1fs)\n", s, length(per[s]), t)
    SMOKE && break
end

function split_rhat(vs)
    halves = Vector{Vector{Float64}}()
    for c in vs; m = length(c)÷2; push!(halves, c[1:m]); push!(halves, c[m+1:2m]); end
    N = minimum(length.(halves)); H = [h[1:N] for h in halves]
    W = mean(var.(H)); B = N*var(mean.(H))
    W <= 0 ? NaN : sqrt(((N-1)/N*W + B/N)/W)
end

LABELS = ["total@2050","total@2100","total@2150","total@2300","ais@2100","gsic@2100","gis@2100","te@2100"]
println("\n=== SLR-deliverable split-R̂ + pooled bands (4 chains) ===")
if SMOKE
    r = per[SEEDS[1]]
    for (j,lab) in enumerate(LABELS)
        v = [x[j] for x in r]; @printf("  %-12s median %.2f cm  [%.2f, %.2f]\n", lab, median(v), quantile(v,.05), quantile(v,.95))
    end
else
    summ = NamedTuple[]
    for (j,lab) in enumerate(LABELS)
        chainvecs = [Float64[x[j] for x in per[s]] for s in SEEDS]
        rh = split_rhat(chainvecs); pool = vcat(chainvecs...)
        @printf("  %-12s R̂ %.4f   median %.2f cm  [%.2f, %.2f]\n", lab, rh, median(pool), quantile(pool,.05), quantile(pool,.95))
        push!(summ, (metric=lab, rhat=rh, median=median(pool), q05=quantile(pool,.05), q95=quantile(pool,.95)))
    end
    out = joinpath(REPO, "outputs/mcmc/slr_projection_rhat_jcont.csv")
    CSV.write(out, DataFrame(summ))
    maxr = maximum(s.rhat for s in summ)
    @printf("\nDELIVERABLE CONVERGENCE: max R̂ = %.4f  →  %s   (ext benchmark 1.003/1.002)\n",
            maxr, maxr < 1.05 ? "PASS" : "CHECK")
    println("wrote $(relpath(out, REPO))")
end
