## ============================================================================
## diag_ais_ramp_likelihood_profile.jl — WHY DIDN'T L30 TAKE THE RAMP?
##
## L30 (L28 + --ais-ramp) put the ramp slope at ~1e-4 against a prior floor of 0.5e-4, left the
## onset unidentified across its whole prior, kept rho_ais at 0.966 and reproduced L28's hindcast
## and projections to the digit (CHANGELOG 09-22e). Two readings:
##   (a) the AR(1) persistence absorbs the acceleration more cheaply than the physics can, so the
##       ramp has nothing to earn — the L28 mechanism, which the rho cap (L29) exposed from the
##       other side;
##   (b) the ramp genuinely does not improve the OBJECTIVE, whatever rho does — the window rates
##       the sweep scored are not what the likelihood scores.
## This distinguishes them WITHOUT a 4 h refit: it evaluates the calibrator's OWN Antarctic term —
## `hetero_logl_ar1(model - obs, sd_ais, rho_ais, eps, L)` on the IMBIE target over 1900-2026 —
## for a grid of ramp settings at FIXED L30 median parameters, at each of several rho. If (a), the
## profile's optimum moves to a large slope as rho falls and is flat-to-declining at rho = 0.966;
## if (b), it declines in the slope at EVERY rho.
##
## The likelihood is re-implemented here (12 lines) rather than imported, because
## calibrate_mcmc_ext.jl runs a chain on load. It is checked against the shipped objective by
## [MATCH]: the stock arm's AIS term must reproduce what the calibrator computes for the same
## parameters to within floating noise of the covariance build. What is NOT re-implemented is the
## rest of the objective (glaciers, Greenland, steric, total, priors) — those do not involve the
## ramp, so a DIFFERENCE between ramp settings is exact even though the LEVEL is not the logpost.
##
##   julia --project=julia_v2 julia/diag_ais_ramp_likelihood_profile.jl [--tag=L30] [ndraw=1]
## Writes outputs/diag_ais_ramp_likelihood_profile_<tag>.csv
## ============================================================================
using CSV, DataFrames, Mimi, MimiBRICK, Statistics, Printf, Dates, LinearAlgebra, Distributions
include(joinpath(@__DIR__, "ladrillo_projection.jl"))
include(joinpath(@__DIR__, "antarctic_icesheet_magdep_component.jl"))

const SCRIPT = "diag_ais_ramp_likelihood_profile.jl"
const TAG    = (i = findfirst(a -> startswith(a, "--tag="), ARGS); i === nothing ? "L30" : ARGS[i][7:end])
const NDRAW  = (p = filter(a -> !startswith(a, "--"), ARGS); length(p) >= 1 ? parse(Int, p[1]) : 1)
const PATH   = joinpath(LADRILLO_REPO, "data/MimiBRICK/parameters_subsample_brick_mengel_$TAG.csv")
## The calibration's own frame, copied from calibrate_mcmc_ext.jl (Y0/Y1/B0/B1, forcing, target).
const Y0, Y1, B0, B1 = 1850, 2026, 1995, 2005
const FORCING = "ssp245harm"
const TARGETS = joinpath(LADRILLO_REPO, "outputs/recalib_targets_ext.csv")
const OBS_CORR_LEN = 100.0                      # --obs-corr-len=100, the L27+ setting
ϵband(lo, hi) = max.((hi .- lo) ./ (2 * 1.645), 0.05)
function hetero_logl_ar1(res, σ, ρ, ϵ, L = OBS_CORR_LEN)
    n = length(res); σp = σ^2 / (1 - ρ^2)
    H = abs.(collect(1:n)' .- collect(1:n))
    Σ = L > 0 ? σp .* ρ .^ H .+ (ϵ * ϵ') .* exp.(-H ./ L) : σp .* ρ .^ H .+ Diagonal(ϵ .^ 2)
    return logpdf(MvNormal(Symmetric(Σ)), res)
end

tg = CSV.read(TARGETS, DataFrame)
fy = [Int(tg.year[i]) for i in 1:nrow(tg) if tg.year[i] >= 1900 && !ismissing(tg.ais[i]) && !isnan(Float64(tg.ais[i]))]
sort!(fy); @assert fy == collect(fy[1]:fy[end]) "AIS target has a year gap"
ri  = [findfirst(==(y), tg.year) for y in fy]
obs = Float64.(tg.ais[ri]); eps = ϵband(Float64.(tg.ais_lo[ri]), Float64.(tg.ais_hi[ri]))
@printf("%s | tag %s | AIS target %d-%d (%d yr), eps mean %.4f cm | forcing %s\n",
        SCRIPT, TAG, fy[1], fy[end], length(fy), mean(eps), FORCING)

post = ladrillo_posterior(path = PATH, cols = :all, nthin = NDRAW)
ladrillo_attach_propagated!(post)
has_ramp = ladrillo_has_ramp(String.(names(post)))
bf = ladrillo_setup(ssp = "ssp245", y0 = Y0, y1 = Y1, forcing_tag = FORCING, ref = (B0, B1),
                    lws = :central, gis_variant = ladrillo_posterior_variant(PATH), ais_ramp = has_ramp)
myi = [ladrillo_yi(bf, y) for y in fy]

## The grid. G_on in GLOBAL warming (the sampled coordinate); slope in m SLE/yr per degC of excess.
## `0.0` is the no-ramp control and must reproduce the stock arm exactly.
const G_ON   = [0.45, 0.60, 0.75, 0.90]
const SLOPE  = [0.0, 0.5e-4, 1.0e-4, 2.0e-4, 3.0e-4, 6.0e-4, 12.0e-4, 20.0e-4]
## rho: the posterior's own value, the L29 cap, and two lower ones, so the trend in rho is visible
## rather than a two-point difference.
const RHOS   = [0.966, 0.90, 0.80, 0.60]

rows = DataFrame()
## The control is run ONCE per draw (it does not depend on G_on) and recorded with G_on = NaN; the
## ramp cells then follow. ⚠ `for gon in G_ON, s in SLOPE` is ONE loop in Julia, so a `break` inside
## it leaves BOTH — which is how the first version of this script wrote a single row.
function cell!(di, r, σ, gon, s)
    if has_ramp
        r["ais_ramp_gon"] = isnan(gon) ? 0.75 : gon
        r["ais_ramp_log10s"] = s == 0.0 ? -12.0 : log10(s)   # -12 -> slope 1e-12: below the component's literal skip in effect
    end
    ladrillo_run_draw!(bf, r)
    ser = ladrillo_series(bf, :ais)
    res = ser[myi] .- obs
    row = DataFrame(draw = di, G_on = gon, slope = s, sd_ais = σ,
                    rate_2011_17 = (ser[ladrillo_yi(bf, 2017)] - ser[ladrillo_yi(bf, 2010)]) / 7,
                    cum_1979_2023 = ser[ladrillo_yi(bf, 2023)] - ser[ladrillo_yi(bf, 1978)])
    for ρ in RHOS
        row[!, "ll_rho$(replace(string(ρ), "." => "p"))"] = [hetero_logl_ar1(res, σ, ρ, eps)]
    end
    append!(rows, row)
end
for (di, r) in enumerate(eachrow(post))
    σ = Float64(r["sd_ais"])
    cell!(di, r, σ, NaN, 0.0)                    # the no-ramp control
    for gon in G_ON, s in SLOPE
        s == 0.0 && continue
        cell!(di, r, σ, gon, s)
    end
    di % 5 == 0 && (@printf("  %d/%d draws\n", di, nrow(post)); flush(stdout))
end
rows.provenance .= "$SCRIPT | tag $TAG ($(nrow(post)) draw(s)) | AIS term only: hetero_logl_ar1(model-obs, sd_ais, rho, eps, L=$OBS_CORR_LEN) on $(fy[1])-$(fy[end]) of $(basename(TARGETS)) | model at the draw's own parameters, ramp OVERRIDDEN per cell | slope 0 = no ramp | $(now())"
CSV.write(joinpath(LADRILLO_REPO, "outputs/diag_ais_ramp_likelihood_profile_$TAG.csv"), rows)

## Report: the gain over the no-ramp control, per rho, as a function of the ramp setting.
base = Dict(d => rows[(rows.draw .== d) .& (rows.slope .== 0.0), :][1, :] for d in unique(rows.draw))
println("\nAIS log-likelihood GAIN over the no-ramp control, mean over draws (positive = the objective prefers the ramp)")
for ρ in RHOS
    c = "ll_rho$(replace(string(ρ), "." => "p"))"
    @printf("\n  rho = %.3f        slope:", ρ)
    for s in SLOPE[2:end]; @printf("%9.1e", s); end
    println()
    for gon in G_ON
        @printf("  G_on %.2f              :", gon)
        for s in SLOPE[2:end]
            sub = rows[(rows.G_on .=== gon) .& (rows.slope .== s), :]
            @printf("%9.2f", mean(sub[!, c] .- [base[d][c] for d in sub.draw]))
        end
        println()
    end
end
@printf("\ncontrol (mean over draws): 2011-17 rate %.4f cm/yr, cumulative 1979-2023 %.3f cm (IMBIE 0.0556, 1.328)\n",
        mean(rows[rows.slope .== 0.0, :rate_2011_17]), mean(rows[rows.slope .== 0.0, :cum_1979_2023]))
for gon in G_ON, s in SLOPE[2:end]
    sub = rows[(rows.G_on .=== gon) .& (rows.slope .== s), :]
    @printf("  G_on %.2f s %.1e: rate %.4f  cum %.3f\n", gon, s, mean(sub.rate_2011_17), mean(sub.cum_1979_2023))
end
println("\nwrote outputs/diag_ais_ramp_likelihood_profile_$TAG.csv")
