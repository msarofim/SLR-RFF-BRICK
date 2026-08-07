## ============================================================================
## diag_pathology_terms.jl — WHICH likelihood term buys the wiggle-tracking
## pathology (extB3-family tuning chains camping at ν≈0, T_off≈−1.8)?
##
## Includes calibrate_mcmc_ext.jl for its full setup (FREE list, θ→BRICK apply
## logic, per-series AR(1) likelihood, targets, forcing — the sampling block is
## guarded off), then evaluates the posterior TERM BY TERM at:
##   A  = the best-log_post draw of the chain's 2nd half (noise as sampled)
##   A' = same draw, gsic+dang AR(1) noise re-optimized (grid) — sanity ≈ A
##   B  = same draw with the glacier block swapped to the D0 self-consistent
##        ν=1 point (a .383, b .28634, T_off −.95661, log10κ −2.2168, ν 1.0),
##        gsic+dang noise re-optimized (the wiggle mode tunes its noise, so a
##        fixed-noise comparison would be rigged against the SC point)
## Δ(B−A') per term isolates what the pathology buys and what the SC point
## would pay, under the LIKELIHOOD CURRENTLY DEFINED BY THE TARGETS ON DISK
## (pass --gsic-early-sigma-x2 to match extB3b/extB3c). CAVEAT: non-gic params
## stay at the chain draw (jointly adapted to its glacier), so Δ is a lower
## bound on what a re-optimized SC posterior could reach — read the SIGN and
## the TERM ATTRIBUTION, not the exact total.
##
##   julia --project=julia_v2 julia/diag_pathology_terms.jl <chain.csv> [--gsic-early-sigma-x2]
## ============================================================================
using CSV, DataFrames, Statistics, Printf

const CHAIN_PATH = ARGS[1]
const PASS_FLAGS = filter(a -> startswith(a, "--"), ARGS[2:end])

# D0 self-consistent point, ν=1 fitted κ (d0_final_selfconsistent.csv C_nu1.0)
const SC_GIC = Dict("gic_a" => 0.383, "gic_b" => 0.28634, "gic_T_off" => -0.95661,
                    "gic_log10_kappa" => log10(0.00607), "gic_nu" => 1.0)

# re-point ARGS for the calibrator include (it parses N_ITER/SEED/flags from ARGS)
empty!(ARGS); append!(ARGS, ["2000", "2026", "--tag=diagterms"]); append!(ARGS, PASS_FLAGS)
include(joinpath(@__DIR__, "calibrate_mcmc_ext.jl"))

const OUT = joinpath(REPO, "outputs/diag_pathology_terms_" *
                     replace(basename(CHAIN_PATH), "chain_" => "", ".csv" => "") * ".csv")

# ---- θ from the chain: best-log_post draw of the 2nd half ------------------
df = CSV.read(CHAIN_PATH, DataFrame)
burn = df[(nrow(df)÷2 + 1):end, :]
ibest = argmax(burn.log_post)
θA = Float64[burn[ibest, Symbol(nm)] for nm in pn0]
@printf("chain %s: best 2nd-half draw log_post = %.2f (as sampled)\n",
        basename(CHAIN_PATH), burn.log_post[ibest])

const GIC_IDX_ALL = [findfirst(==(nm), pn0) for nm in
                     ["gic_a","gic_b","gic_T_off","gic_log10_kappa","gic_nu"]]
const ISIG_GSIC, IRHO_GSIC = NP + 3, NP + 4        # SERIES order [ais,GSIC,gis,steric,DANG]
const ISIG_DANG, IRHO_DANG = NP + 9, NP + 10

# ---- per-term evaluation (mirrors logposterior term order exactly) ---------
function apply_and_run!(θ)
    @inbounds for k in 1:NP
        (k == AMP_IDX || k == TON_IDX || k == KAPPA_IDX) && continue
        setp!(FREE[k], θ[k])
    end
    update_param!(m, G, :gic_kappa, 10.0^θ[KAPPA_IDX])
    update_param!(m, :antarctic_icesheet, :ais_runoffline_snowheight₀, -θ[TON_IDX] * θ[C_IDX])
    update_param!(m, :antarctic_icesheet, :ais_temperature_coefficient, 1.0 / θ[AMP_IDX])
    update_param!(m, :antarctic_icesheet, :ais_temperature_intercept, -AIS_TANT0 / θ[AMP_IDX])
    run(m)
end

function residuals()
    ais = reref(m[:antarctic_icesheet, :ais_sea_level])
    gsic = reref(m[:glaciers_small_icecaps, :gsic_sea_level])
    gis = reref(m[:greenland_icesheet, :greenland_sea_level])
    te = reref(m[:thermal_expansion, :te_sea_level])
    tot = ais .+ gsic .+ gis .+ te
    res = Dict(:ais => ais[S.ais.myi] .- S.ais.obs, :gsic => gsic[S.gsic.myi] .- S.gsic.obs,
               :gis => gis[S.gis.myi] .- S.gis.obs, :steric => te[S.steric.myi] .- S.steric.obs,
               :dang => tot[S.dang.myi] .+ lws_dang .- S.dang.obs)
    return res
end

noise_prior(σ) = logpdf(truncated(Normal(0, 5), 0, Inf), σ)

function opt_noise(res, ϵ)
    best = (-Inf, NaN, NaN)
    for lσ in range(-3.0, 0.7, length=60), ρ in 0.0:0.02:0.98
        σ = 10.0^lσ
        l = hetero_logl_ar1(res, σ, ρ, ϵ) + noise_prior(σ)
        l > best[1] && (best = (l, σ, ρ))
    end
    return best
end

function term_table(θin; reopt::Bool)
    θ = copy(θin)
    apply_and_run!(θ)
    res = residuals()
    if reopt
        _, θ[ISIG_GSIC], θ[IRHO_GSIC] = opt_noise(res[:gsic], S.gsic.ϵ)
        _, θ[ISIG_DANG], θ[IRHO_DANG] = opt_noise(res[:dang], S.dang.ϵ)
    end
    σn = θ[NP+1:2:NK]; ρn = θ[NP+2:2:NK]
    t = DataFrame(term=String[], ll=Float64[])
    for (i, s) in enumerate(SERIES)
        push!(t, ("flow_$s", hetero_logl_ar1(res[s], σn[i], ρn[i],
                                             getfield(S, s).ϵ)))
    end
    smb_gt = mean(m[:antarctic_icesheet, :β_total][SMB_IDX]) * M3ICE_TO_GT
    push!(t, ("smb_anchor", logpdf(Normal(SMB_TARGET_GT, SMB_SIGMA_GT), smb_gt)))
    gsic_raw = m[G, :gsic_sea_level]
    push!(t, ("inv_A2", logpdf(Normal(INV_V_M, INV_SIGMA_M),
                               θ[GIC_A_IDX] - Float64(gsic_raw[INV_YEAR_IDX]))))
    push!(t, ("lec_A2b", logpdf(Normal(M19_MU_M, M19_SIGMA_M),
                                Float64(gsic_raw[M19_I1900]) - Float64(gsic_raw[M19_I1850]))))
    pr_gic = sum(logpdf(Normal(FREE[k].μ, FREE[k].σ), θ[k]) for k in GIC_IDX_ALL)
    pr_oth = sum(logpdf(Normal(FREE[k].μ, FREE[k].σ), θ[k])
                 for k in 1:NP if !(k in GEO_IDX) && !(k in GIC_IDX_ALL))
    push!(t, ("prior_gic", pr_gic))
    push!(t, ("prior_other", pr_oth + logpdf(GEO_PRIOR, (θ[GEO_IDX] .- GEO_MU) ./ GEO_SD)))
    push!(t, ("prior_noise", sum(noise_prior.(σn))))
    push!(t, ("TOTAL", sum(t.ll)))
    return t, θ
end

tA,  _  = term_table(θA; reopt=false)
tAp, θAp = term_table(θA; reopt=true)
θB = copy(θA)
for (nm, v) in SC_GIC; θB[findfirst(==(nm), pn0)] = v; end
tB, θBp = term_table(θB; reopt=true)

out = DataFrame(term=tA.term, A_chain=tA.ll, Ap_reopt=tAp.ll, B_SC=tB.ll,
                d_B_minus_Ap=tB.ll .- tAp.ll)
CSV.write(OUT, out)
println("\nterm decomposition (A = chain best draw; A' = noise re-opt; B = SC ν=1 glacier block):")
@printf("%-14s %10s %10s %10s %10s\n", "term", "A", "A'", "B_SC", "B−A'")
for r in eachrow(out)
    @printf("%-14s %10.2f %10.2f %10.2f %10.2f\n", r.term, r.A_chain, r.Ap_reopt, r.B_SC, r.d_B_minus_Ap)
end
@printf("\nnoise re-opt: gsic σ %.4f→%.4f ρ %.2f→%.2f (A'); SC variant σ %.4f ρ %.2f\n",
        θA[ISIG_GSIC], θAp[ISIG_GSIC], θA[IRHO_GSIC], θAp[IRHO_GSIC], θBp[ISIG_GSIC], θBp[IRHO_GSIC])
@printf("gsic-flag %s | targets on disk = CURRENT dang_sig | commit via git log\n",
        GSIC_EARLY_X2 ? "ON" : "OFF")
println("Wrote $OUT")
