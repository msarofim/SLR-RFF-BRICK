## ============================================================================
## diag_ais_ramp_objective_power.jl — CAN THE SHIPPED OBJECTIVE SEE A RAMP AT ALL?
##
## `diag_ais_ramp_likelihood_profile.jl` measured the objective against the REAL record and found
## that at the posterior's own rho every ramp setting LOSES (CHANGELOG 09-22e). That answers
## "does the record want a ramp?". It does NOT answer "would this objective find a ramp if one
## were there?" — and the two have opposite implications for the open ruling:
##   * objective BLIND  -> the null is uninformative, and changing what the model is fitted to
##                         (a rate/window term) is the warranted move;
##   * objective SIGHTED -> the objective looked and declined, the null is informative, and the
##                         honest paper statement is that the level record does not identify a ramp.
## Standing rule (~/.claude/CLAUDE.md): MEASURE A TEST'S POWER BEFORE BELIEVING ITS NULL.
##
## METHOD. At fixed L30 median parameters, build a SYNTHETIC Antarctic record from the model WITH a
## known ramp (the truth cell), then profile the calibrator's own AIS term over the same candidate
## grid against that synthetic record.
##   (a) NOISELESS: obs_syn = truth series. ll(truth cell) - ll(no ramp) is the IDENTIFIABILITY
##       CEILING — what the objective could gain if the data were the ramp exactly.
##   (b) NOISY: obs_syn = truth series + a realization drawn from the objective's OWN fitted noise
##       (AR(1) at rho_ais with the 100-yr-correlated observational eps). Detection = the best ramp
##       cell beats the no-ramp cell by at least DETECT_LR log-units. The detection FRACTION over
##       realizations is the power.
## Both are run at several rho, and the joint argmax over (cell, rho) is reported: if a record that
## GENUINELY CONTAINS a ramp is still best explained by no-ramp-at-high-rho, that is the absorption
## mechanism demonstrated on data whose truth we know.
##
## SCOPE / LIMITS, stated at the gate:
##   * Every other parameter is held FIXED. A real refit would let them absorb some of the signal,
##     so the power measured here is an UPPER BOUND on the refit's power.
##   * The rho profile is a profile LIKELIHOOD: rho_ais's prior is not carried. Differences between
##     cells at FIXED rho are exact; comparisons ACROSS rho ignore that prior.
##   * The likelihood is the same 12-line re-implementation the profile script uses and carries the
##     same caveat: if the calibrator's noise model changes, this copy must follow.
##
##   julia --project=julia_v2 julia/diag_ais_ramp_objective_power.jl [--tag=L30] [ndraw]
## Writes outputs/diag_ais_ramp_objective_power_<tag>.csv (cells) and _mc_<tag>.csv (realizations)
## ============================================================================
using CSV, DataFrames, Mimi, MimiBRICK, Statistics, Printf, Dates, LinearAlgebra, Distributions, Random

include(joinpath(@__DIR__, "ladrillo_projection.jl"))
include(joinpath(@__DIR__, "antarctic_icesheet_magdep_component.jl"))

const SCRIPT = "diag_ais_ramp_objective_power.jl"
const TAG    = (i = findfirst(a -> startswith(a, "--tag="), ARGS); i === nothing ? "L30" : ARGS[i][7:end])
const NDRAW  = (p = filter(a -> !startswith(a, "--"), ARGS); length(p) >= 1 ? parse(Int, p[1]) : 5)
const PATH   = joinpath(LADRILLO_REPO, "data/MimiBRICK/parameters_subsample_brick_mengel_$TAG.csv")

## The calibration's own frame, copied from calibrate_mcmc_ext.jl (must match the profile script).
const Y0, Y1, B0, B1 = 1850, 2026, 1995, 2005
const FORCING      = "ssp245harm"
const TARGETS      = joinpath(LADRILLO_REPO, "outputs/recalib_targets_ext.csv")
const OBS_CORR_LEN = 100.0                      # --obs-corr-len=100, the L27+ setting
const FIT_Y0       = 1900                       # the AIS term's span in the shipped objective

## The truth cells. The first is the onset sweep's best (all four pre-pause IMBIE windows inside
## +-0.5 sigma, CHANGELOG 09-22c); the second is its near-equal runner-up.
const TRUTH_CELLS  = [(0.75, 6.0e-4), (0.60, 3.0e-4)]
## The candidate grid, identical to diag_ais_ramp_likelihood_profile.jl so the two are readable
## side by side. slope 0.0 is the no-ramp candidate.
const G_ON         = [0.45, 0.60, 0.75, 0.90]
const SLOPE        = [0.0, 0.5e-4, 1.0e-4, 2.0e-4, 3.0e-4, 6.0e-4, 12.0e-4, 20.0e-4]
const RHOS         = [0.966, 0.90, 0.80, 0.60]
const RHO_TRUE     = 0.966                      # the noise realizations are drawn at L30's own rho_ais
const NOISE_DRAWS  = 200
const DETECT_LR    = 2.0                        # log-units by which a ramp must beat no-ramp to count as detected
const SEED         = 20260922                   # stamped into both artifacts; see ~/.claude/CLAUDE.md

epsband(lo, hi) = max.((hi .- lo) ./ (2 * 1.645), 0.05)
function ais_cov(σ, ρ, ϵ, n, L = OBS_CORR_LEN)
    σp = σ^2 / (1 - ρ^2)
    H  = abs.(collect(1:n)' .- collect(1:n))
    return L > 0 ? σp .* ρ .^ H .+ (ϵ * ϵ') .* exp.(-H ./ L) : σp .* ρ .^ H .+ Diagonal(ϵ .^ 2)
end
## The MvNormal is built ONCE per (draw, rho) and reused: constructing it factorizes the 127x127
## covariance, and the Monte Carlo evaluates ~46k residuals against the same few covariances.
ais_mvn(Σ) = MvNormal(Symmetric(Σ))
ais_logl(res, d::MvNormal) = logpdf(d, res)

## ---- target span and the observational eps band (the target VALUES are not used: the record here
## ---- is synthetic. Only its YEARS and its eps band enter.)
tg = CSV.read(TARGETS, DataFrame)
fy = [Int(tg.year[i]) for i in 1:nrow(tg) if tg.year[i] >= FIT_Y0 && !ismissing(tg.ais[i]) && !isnan(Float64(tg.ais[i]))]
sort!(fy); @assert fy == collect(fy[1]:fy[end]) "AIS target has a year gap"
ri  = [findfirst(==(y), tg.year) for y in fy]
eps = epsband(Float64.(tg.ais_lo[ri]), Float64.(tg.ais_hi[ri]))
nY  = length(fy)
@printf("%s | tag %s | synthetic AIS record %d-%d (%d yr) | eps mean %.4f cm | forcing %s | seed %d\n",
        SCRIPT, TAG, fy[1], fy[end], nY, mean(eps), FORCING, SEED)

post = ladrillo_posterior(path = PATH, cols = :all, nthin = NDRAW)
ladrillo_attach_propagated!(post)
has_ramp = ladrillo_has_ramp(String.(names(post)))
has_ramp || error("$TAG posterior has no ramp columns — this diagnostic needs an --ais-ramp posterior")
bf = ladrillo_setup(ssp = "ssp245", y0 = Y0, y1 = Y1, forcing_tag = FORCING, ref = (B0, B1),
                    lws = :central, gis_variant = ladrillo_posterior_variant(PATH), ais_ramp = true)
myi = [ladrillo_yi(bf, y) for y in fy]

"""Run one ramp setting at this draw's parameters and return the AIS series on the fit years.
`s == 0.0` sets the slope below the component's literal skip, i.e. the no-ramp arm."""
function series_at(r, gon, s)
    r["ais_ramp_gon"]    = isnan(gon) ? first(G_ON) : gon
    r["ais_ramp_log10s"] = s == 0.0 ? -12.0 : log10(s)
    ladrillo_run_draw!(bf, r)
    return ladrillo_series(bf, :ais)[myi]
end

## The candidate cells, in a fixed order; the no-ramp candidate is index 1.
cands = vcat([(NaN, 0.0)], [(g, s) for g in G_ON for s in SLOPE if s != 0.0])
cells = DataFrame(); mcrows = DataFrame()
Random.seed!(SEED)                              # immediately before the RNG stream is consumed

for (di, r) in enumerate(eachrow(post))
    σ = Float64(r["sd_ais"])
    ser = Dict{Tuple{Float64,Float64},Vector{Float64}}()
    for (g, s) in cands; ser[(g, s)] = copy(series_at(r, g, s)); end
    Σ  = Dict(ρ => ais_mvn(ais_cov(σ, ρ, eps, nY)) for ρ in RHOS)
    noise = rand(ais_mvn(ais_cov(σ, RHO_TRUE, eps, nY)), NOISE_DRAWS)     # nY x NOISE_DRAWS

    for (tg_on, tg_s) in TRUTH_CELLS
        truth = ser[(tg_on, tg_s)]
        ## (a) NOISELESS — the identifiability ceiling.
        for (g, s) in cands
            res = ser[(g, s)] .- truth
            row = DataFrame(draw = di, truth_G_on = tg_on, truth_slope = tg_s,
                            G_on = g, slope = s, sd_ais = σ, is_truth = (g === tg_on && s == tg_s))
            for ρ in RHOS; row[!, "ll_noiseless_rho$(replace(string(ρ), "." => "p"))"] = [ais_logl(res, Σ[ρ])]; end
            append!(cells, row)
        end
        ## (b) NOISY — the power.
        for k in 1:NOISE_DRAWS
            obs_syn = truth .+ noise[:, k]
            for ρ in RHOS
                lls  = [ais_logl(ser[c] .- obs_syn, Σ[ρ]) for c in cands]
                ll0  = lls[1]
                j    = argmax(@view lls[2:end]) + 1
                append!(mcrows, DataFrame(draw = di, rep = k, rho = ρ,
                    truth_G_on = tg_on, truth_slope = tg_s,
                    ll_noramp = ll0, ll_best_ramp = lls[j],
                    best_G_on = cands[j][1], best_slope = cands[j][2],
                    gain = lls[j] - ll0, detected = (lls[j] - ll0) >= DETECT_LR,
                    ll_at_truth = lls[findfirst(==((tg_on, tg_s)), cands)]))
            end
        end
    end
    @printf("  draw %d/%d done\n", di, nrow(post)); flush(stdout)
end

prov = "$SCRIPT | tag $TAG ($(nrow(post)) draw(s)) | SYNTHETIC AIS record: model at the draw's own " *
       "parameters WITH the truth ramp, years $(fy[1])-$(fy[end]) | noise ~ MvNormal(ais_cov(sd_ais, " *
       "rho=$RHO_TRUE, eps, L=$OBS_CORR_LEN)), $NOISE_DRAWS reps, SEED $SEED applied immediately before " *
       "the rand() that draws them | likelihood = hetero_logl_ar1 re-implementation, AIS term only | " *
       "all other parameters FIXED => power is an UPPER BOUND | detect = best ramp beats no-ramp by " *
       ">= $DETECT_LR log-units | cm SLE, rel $B0-$B1 | $(now())"
cells.provenance .= prov; mcrows.provenance .= prov
CSV.write(joinpath(LADRILLO_REPO, "outputs/diag_ais_ramp_objective_power_$TAG.csv"), cells)
CSV.write(joinpath(LADRILLO_REPO, "outputs/diag_ais_ramp_objective_power_mc_$TAG.csv"), mcrows)

## ---- Report
for (tg_on, tg_s) in TRUTH_CELLS
    @printf("\n=== TRUTH: onset %.2f K global, slope %.1e m SLE/yr/K ===\n", tg_on, tg_s)
    println("(a) NOISELESS identifiability ceiling: ll(truth cell) - ll(no ramp), mean over draws")
    for ρ in RHOS
        c = "ll_noiseless_rho$(replace(string(ρ), "." => "p"))"
        sub = cells[(cells.truth_G_on .== tg_on) .& (cells.truth_slope .== tg_s), :]
        t0  = sub[sub.slope .== 0.0, c]; tt = sub[sub.is_truth, c]
        @printf("    rho %.3f : %+8.2f log-units\n", ρ, mean(tt) - mean(t0))
    end
    println("(b) POWER over $NOISE_DRAWS noise realizations drawn at rho $RHO_TRUE")
    @printf("    %-8s %-10s %-12s %-12s %s\n", "rho", "detected", "median gain", "median slope", "median onset")
    for ρ in RHOS
        m = mcrows[(mcrows.rho .== ρ) .& (mcrows.truth_G_on .== tg_on) .& (mcrows.truth_slope .== tg_s), :]
        @printf("    %-8.3f %-10.1f %-12.2f %-12.1e %.2f\n", ρ, 100 * mean(m.detected), median(m.gain),
                median(m.best_slope), median(filter(!isnan, m.best_G_on)))
    end
    ## Joint argmax over (cell, rho): does a record that CONTAINS a ramp still prefer no-ramp-at-high-rho?
    m = mcrows[(mcrows.truth_G_on .== tg_on) .& (mcrows.truth_slope .== tg_s), :]
    nr = combine(groupby(m, [:draw, :rep]), :ll_noramp => maximum => :best_noramp,
                                            :ll_best_ramp => maximum => :best_ramp)
    @printf("    joint over (cell, rho): the ramp wins in %.1f%% of realizations\n",
            100 * mean(nr.best_ramp .> nr.best_noramp))
end
println("\nwrote outputs/diag_ais_ramp_objective_power_$TAG.csv and _mc_$TAG.csv")
