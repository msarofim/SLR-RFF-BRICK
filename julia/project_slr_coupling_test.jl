## ============================================================================
## project_slr_coupling_test.jl — "does the te_α↔OHC coupling change the reported SLR bands?"
## ‼ STATUS 2026-08-01: DIAGNOSTIC (the test that REJECTED the joint free-forcing calibration). Answer:
## the coupling is immaterial to total SLR; freeing the forcing is harmful (SLR re-infers it). Canonical
## BRICK-AM = mean-forcing calibrate_mcmc_ext.jl. See notes/negresult_2026-08-01_joint_forcing_calibration.md.
##
## Three forward-projections of total SLR (each draw run through BRICK to 2300, identical machinery):
##   COUPLED   — joint posterior draws paired as sampled (θ_i, fpc_i).            [= the joint bands]
##   DECOUPLED — SAME joint draws with the fpc triples SHUFFLED across draws.     [coupling broken,
##               BRICK + forcing marginals held EXACTLY fixed → isolates the coupling alone.]
##   EXT_MEAN  — the extA108 (mean-forcing) posterior subsample on deterministic mean forcing (fpc=0).
##               [= the current-pipeline central estimate, no forcing uncertainty.]
##
## COUPLED − DECOUPLED  = the pure coupling effect on the deliverable (matched marginals).
## COUPLED vs EXT_MEAN  = the practical shift from the current mean-forcing calibration.
##
## Reuses calibrate_mcmc_joint_cont.jl's FREE list + θ→BRICK apply logic via (guarded) include.
## Run:  julia --project=julia_v2 julia/project_slr_coupling_test.jl --amp-mu=1.08 --amp-sigma=0.15
## ============================================================================
include(joinpath(@__DIR__, "calibrate_mcmc_joint_cont.jl"))
using Statistics, Printf, CSV, DataFrames, Random

const SEEDS   = [2026, 2027, 2028, 2029]
const NITER_P = 4_000_000
const BURN_P  = NITER_P ÷ 2
const THIN_P  = 500
const SHUF_SEED = 20260801
const YP0, YP1 = 1850, 2300
const YRS2 = collect(YP0:YP1); ty(y) = findfirst(==(y), YRS2)
const IB2 = [ty(y) for y in 1995:2005]
const HORIZONS = [2050, 2100, 2150, 2300]
const LABELS = ["total@2050","total@2100","total@2150","total@2300","ais@2100","gsic@2100","gis@2100","te@2100"]

const _pk2   = [findfirst(==(y), PCB.year) for y in YRS2]
const GMEAN2 = Float64.(PCB.gmean[_pk2]); const OMEAN2 = Float64.(PCB.omean[_pk2])
const GLOAD2 = [Float64.(PCB[_pk2, Symbol("Gload$k")]) for k in 1:NPC]
const OLOAD2 = [Float64.(PCB[_pk2, Symbol("Oload$k")]) for k in 1:NPC]
reconstruct2(a) = (g = copy(GMEAN2); o = copy(OMEAN2);
    @inbounds for k in 1:NPC; g .+= (GS*a[k]).*GLOAD2[k]; o .+= (OS*a[k]).*OLOAD2[k]; end; (g, o))

const m2 = build_brick_mengel(ssp="ssp245", y0=YP0, y1=YP1)
update_brick_mengel!(m2, medoid, (a=0.45,b=0.52,T_lia=-0.45,f=0.5,tau_fast=40.0,tau_slow=250.0,sl0=0.0); precip_log=true)
setp2!(k, v) = update_param!(m2, k.comp, k.sym, k.islog ? log(v) : v)
reref2(v) = 100 .* (v .- mean(v[IB2]))
function project(θ, a)
    g, o = reconstruct2(a); set_forcing!(m2, g, o)
    @inbounds for k in 1:NP; (k==AMP_IDX || k==TON_IDX) && continue; setp2!(FREE[k], θ[k]); end
    update_param!(m2, :antarctic_icesheet, :ais_runoffline_snowheight₀, -θ[TON_IDX]*θ[C_IDX])
    update_param!(m2, :antarctic_icesheet, :ais_temperature_coefficient, 1.0/θ[AMP_IDX])
    update_param!(m2, :antarctic_icesheet, :ais_temperature_intercept, -AIS_TANT0/θ[AMP_IDX])
    run(m2)
    tot = reref2(m2[:global_sea_level, :sea_level_rise]); i100 = ty(2100)
    (tot[[ty(y) for y in HORIZONS]]...,
     reref2(m2[:antarctic_icesheet, :ais_sea_level])[i100], reref2(m2[:glaciers_small_icecaps, :gsic_sea_level])[i100],
     reref2(m2[:greenland_icesheet, :greenland_sea_level])[i100], reref2(m2[:thermal_expansion, :te_sea_level])[i100])
end

# ---- EXT_MEAN first (fail-fast on the subsample path before the 12-min chain stream) ----
println("projecting EXT_MEAN (extA108 subsample on mean forcing) ...")
sub = CSV.read(joinpath(REPO,"data/MimiBRICK/parameters_subsample_brick_mengel_extA108.csv"), DataFrame)
zeroA = zeros(NPC)
extmean = [project(Float64[Float64(sub[i, Symbol(FREE[k].name)]) for k in 1:NP], zeroA) for i in 1:nrow(sub)]
@printf("  ext_mean %d draws\n", length(extmean))

# ---- read joint posterior draws (thinned) ----
println("reading joint draws (thin=$THIN_P) ...")
Θ = Vector{Vector{Float64}}(); A = Vector{Vector{Float64}}()
for s in SEEDS
    path = joinpath(REPO, "outputs/mcmc/chain_jcont_seed$(s)_n$(NITER_P).csv"); i = 0
    for row in CSV.Rows(path; types=Float64, reusebuffer=true)
        i += 1; d = i - 1
        (d < BURN_P || (d - BURN_P) % THIN_P != 0) && continue
        push!(Θ, Float64[row[j] for j in 1:NP]); push!(A, Float64[row[NK+k] for k in 1:NPC])
    end
end
ND = length(Θ); @printf("  %d joint draws\n", ND)
# persist thinned draws for reuse (each row = one draw)
CSV.write(joinpath(REPO,"outputs/mcmc/jcont_thinned_draws.csv"),
          DataFrame(hcat(permutedims(reduce(hcat,Θ)), permutedims(reduce(hcat,A))),
                    vcat([FREE[k].name for k in 1:NP], ["fpc$k" for k in 1:NPC])))

# ---- three projections ----
println("projecting COUPLED, DECOUPLED (shuffled fpc), EXT_MEAN ...")
coupled = [project(Θ[i], A[i]) for i in 1:ND]
Random.seed!(SHUF_SEED); perm = shuffle(1:ND)
decoupled = [project(Θ[i], A[perm[i]]) for i in 1:ND]          # θ_i paired with a RANDOM fpc → coupling broken
@printf("  coupled %d  decoupled %d  ext_mean %d\n", length(coupled), length(decoupled), length(extmean))

band(rows, j) = (v = Float64[r[j] for r in rows]; (median(v), quantile(v,.05), quantile(v,.95), quantile(v,.95)-quantile(v,.05)))
println("\n=== SLR bands: COUPLED vs DECOUPLED vs EXT_MEAN  (median [5,95], width; cm, rel 1995-2005) ===")
summ = NamedTuple[]
for (j,lab) in enumerate(LABELS)
    c = band(coupled,j); d = band(decoupled,j); e = band(extmean,j)
    @printf("%-11s  COUPLED %6.2f [%6.2f,%7.2f] w%6.2f | DECOUP %6.2f [%6.2f,%7.2f] w%6.2f | EXTmean %6.2f [%6.2f,%7.2f]\n",
            lab, c[1],c[2],c[3],c[4], d[1],d[2],d[3],d[4], e[1],e[2],e[3])
    push!(summ, (metric=lab, cpl_med=c[1],cpl_lo=c[2],cpl_hi=c[3],cpl_w=c[4],
                 dec_med=d[1],dec_lo=d[2],dec_hi=d[3],dec_w=d[4], ext_med=e[1],ext_lo=e[2],ext_hi=e[3],
                 coupling_dmed=c[1]-d[1], coupling_dwidth=c[4]-d[4], vs_ext_dmed=c[1]-e[1]))
end
println("\n=== COUPLING effect (COUPLED − DECOUPLED, matched marginals) + practical shift vs EXT_MEAN ===")
for s in summ
    @printf("  %-11s  Δmedian %+6.2f cm  Δwidth %+6.2f cm  (%+5.1f%% width)   |  vs EXT_MEAN Δmedian %+6.2f cm\n",
            s.metric, s.coupling_dmed, s.coupling_dwidth, 100*s.coupling_dwidth/s.dec_w, s.vs_ext_dmed)
end
CSV.write(joinpath(REPO,"outputs/mcmc/slr_coupling_test.csv"), DataFrame(summ))
println("\nwrote outputs/mcmc/slr_coupling_test.csv  (shuffle seed $SHUF_SEED)")
