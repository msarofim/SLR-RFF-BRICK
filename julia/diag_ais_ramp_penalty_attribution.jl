## ============================================================================
## diag_ais_ramp_penalty_attribution.jl — WHERE does the ramp's likelihood penalty come from?
##
## Two facts now stand side by side and they do not obviously fit:
##   * the objective HAS POWER on the ramp axis — it recovers a 6e-4 / 0.75 K ramp from a synthetic
##     record in 95.7% of realizations at its own rho (diag_ais_ramp_objective_power.jl, 09-22f);
##   * against the REAL record that same ramp loses 33.8 log-units at rho 0.966
##     (diag_ais_ramp_likelihood_profile.jl, CHANGELOG 09-22e) —
## yet the ramp's cumulative 1979-2023 (1.44 cm) is only ~0.8 sigma from IMBIE's 1.328 +- 0.143.
## A 34-log-unit penalty for a ~1 sigma level swing needs an explanation that is MEASURED, not
## reasoned: ~/.claude/CLAUDE.md, "implausible result = bug; diagnose with tests".
##
## METHOD. The AIS term is -0.5*(res' Sinv res) + const, and the quadratic form decomposes EXACTLY
## by year as  q_i = res_i * (Sinv*res)_i,  sum(q) = res' Sinv res. This attributes the penalty
## per year, so the difference (ramp - no ramp) in q localises where the objective is paying.
## Reported by ERA, because the target's provenance changes at 1979 (Frederikse before, IMBIE
## after; outputs/diag_imbie2026_vs_targets_windows_*.csv shows z_target_vs_imbie ~ 0 from 1979 on).
##
##   julia --project=julia_v2 julia/diag_ais_ramp_penalty_attribution.jl [--tag=L30] [ndraw]
## Writes outputs/diag_ais_ramp_penalty_attribution_<tag>.csv
## ============================================================================
using CSV, DataFrames, Mimi, MimiBRICK, Statistics, Printf, Dates, LinearAlgebra, Distributions

include(joinpath(@__DIR__, "ladrillo_projection.jl"))
include(joinpath(@__DIR__, "antarctic_icesheet_magdep_component.jl"))

const SCRIPT = "diag_ais_ramp_penalty_attribution.jl"
const TAG    = (i = findfirst(a -> startswith(a, "--tag="), ARGS); i === nothing ? "L30" : ARGS[i][7:end])
const NDRAW  = (p = filter(a -> !startswith(a, "--"), ARGS); length(p) >= 1 ? parse(Int, p[1]) : 5)
const PATH   = joinpath(LADRILLO_REPO, "data/MimiBRICK/parameters_subsample_brick_mengel_$TAG.csv")
const Y0, Y1, B0, B1 = 1850, 2026, 1995, 2005
const FORCING      = "ssp245harm"
const TARGETS      = joinpath(LADRILLO_REPO, "outputs/recalib_targets_ext.csv")
const OBS_CORR_LEN = 100.0
const FIT_Y0       = 1900
const SPLICE_Y     = 1979          # target provenance changes here: Frederikse before, IMBIE after
const CELLS        = [(0.75, 6.0e-4), (0.60, 3.0e-4), (0.45, 1.0e-4)]
const RHOS         = [0.966, 0.90, 0.80, 0.60]
const ERAS         = [("pre_splice", FIT_Y0, SPLICE_Y - 1), ("satellite", SPLICE_Y, 2025)]
## Finer bins inside the satellite era, aligned on the IMBIE windows the onset sweep scored, so the
## per-year attribution can be read against those windows directly. The 2018-23 PAUSE is its own bin:
## a monotone ramp cannot pause, and whether the level record's objection IS the pause decides
## whether a pre-pause-windows-only rate term is a defensible design.
const BINS         = [("1900_1978", 1900, 1978), ("1979_1991", 1979, 1991), ("1992_2002", 1992, 2002),
                      ("2003_2010", 2003, 2010), ("2011_2017", 2011, 2017), ("2018_2025", 2018, 2025)]

epsband(lo, hi) = max.((hi .- lo) ./ (2 * 1.645), 0.05)
function ais_cov(σ, ρ, ϵ, n, L = OBS_CORR_LEN)
    σp = σ^2 / (1 - ρ^2); H = abs.(collect(1:n)' .- collect(1:n))
    return L > 0 ? σp .* ρ .^ H .+ (ϵ * ϵ') .* exp.(-H ./ L) : σp .* ρ .^ H .+ Diagonal(ϵ .^ 2)
end

tg = CSV.read(TARGETS, DataFrame)
fy = [Int(tg.year[i]) for i in 1:nrow(tg) if tg.year[i] >= FIT_Y0 && !ismissing(tg.ais[i]) && !isnan(Float64(tg.ais[i]))]
sort!(fy); ri = [findfirst(==(y), tg.year) for y in fy]
obs = Float64.(tg.ais[ri]); eps = epsband(Float64.(tg.ais_lo[ri]), Float64.(tg.ais_hi[ri])); nY = length(fy)
@printf("%s | tag %s | AIS target %d-%d (%d yr) | splice at %d\n", SCRIPT, TAG, fy[1], fy[end], nY, SPLICE_Y)

post = ladrillo_posterior(path = PATH, cols = :all, nthin = NDRAW); ladrillo_attach_propagated!(post)
ladrillo_has_ramp(String.(names(post))) || error("$TAG posterior has no ramp columns")
bf = ladrillo_setup(ssp = "ssp245", y0 = Y0, y1 = Y1, forcing_tag = FORCING, ref = (B0, B1),
                    lws = :central, gis_variant = ladrillo_posterior_variant(PATH), ais_ramp = true)
myi = [ladrillo_yi(bf, y) for y in fy]
function series_at(r, gon, s)
    r["ais_ramp_gon"] = isnan(gon) ? first(first(CELLS)) : gon
    r["ais_ramp_log10s"] = s == 0.0 ? -12.0 : log10(s)
    ladrillo_run_draw!(bf, r); return ladrillo_series(bf, :ais)[myi]
end

rows = DataFrame()
for (di, r) in enumerate(eachrow(post))
    σ = Float64(r["sd_ais"]); base = copy(series_at(r, NaN, 0.0))
    for ρ in RHOS
        Sinv = inv(Symmetric(ais_cov(σ, ρ, eps, nY)))
        q(res) = res .* (Sinv * res)                       # exact per-year split of res' Sinv res
        q0 = q(base .- obs)
        for (gon, s) in CELLS
            series_ramp = copy(series_at(r, gon, s))
            qr = q(series_ramp .- obs)
            for (nm, a, b) in vcat(ERAS, BINS)
                k = findall(y -> a <= y <= b, fy)
                append!(rows, DataFrame(draw = di, rho = ρ, G_on = gon, slope = s, era = nm,
                    years = length(k), q_noramp = sum(q0[k]), q_ramp = sum(qr[k]),
                    dloglik = -0.5 * (sum(qr[k]) - sum(q0[k])),
                    res_noramp_end = (base .- obs)[k[end]], res_ramp_end = (series_ramp .- obs)[k[end]]))
            end
        end
    end
    @printf("  draw %d/%d\n", di, nrow(post)); flush(stdout)
end
rows.provenance .= "$SCRIPT | tag $TAG ($(nrow(post)) draw(s)) | per-year split of the AIS quadratic " *
    "form res'*Sinv*res, Sinv from ais_cov(sd_ais, rho, eps, L=$OBS_CORR_LEN) | target $(basename(TARGETS)) " *
    "$(fy[1])-$(fy[end]), splice $SPLICE_Y (Frederikse before / IMBIE after) | dloglik = -0.5*(q_ramp - " *
    "q_noramp), NEGATIVE = the ramp is penalised in that era | all other parameters FIXED | $(now())"
CSV.write(joinpath(LADRILLO_REPO, "outputs/diag_ais_ramp_penalty_attribution_$TAG.csv"), rows)

println("\nAIS log-likelihood change from adding the ramp, BY BIN (negative = the ramp is penalised there), mean over draws")
for ρ in RHOS
    @printf("\n  rho = %.3f\n", ρ); @printf("    %-20s", "ramp cell")
    for (nm, _, _) in BINS; @printf("%11s", nm); end; @printf("%11s\n", "TOTAL")
    for (gon, s) in CELLS
        m = rows[(rows.rho .== ρ) .& (rows.G_on .== gon) .& (rows.slope .== s), :]
        @printf("    on %.2f K s %.1e", gon, s)
        tot = 0.0
        for (nm, _, _) in BINS
            v = mean(m[m.era .== nm, :dloglik]); tot += v; @printf("%11.2f", v)
        end
        @printf("%11.2f\n", tot)
    end
end
println("\nModel minus obs at each bin's LAST year (cm SLE; + = model too high), mean over draws, rho-independent")
for (gon, s) in CELLS
    m = rows[(rows.rho .== first(RHOS)) .& (rows.G_on .== gon) .& (rows.slope .== s), :]
    @printf("    on %.2f K s %.1e  no-ramp:", gon, s)
    for (nm, _, _) in BINS; @printf("%8.3f", mean(m[m.era .== nm, :res_noramp_end])); end
    @printf("\n                          ramp   :")
    for (nm, _, _) in BINS; @printf("%8.3f", mean(m[m.era .== nm, :res_ramp_end])); end
    println()
end
println("\nwrote outputs/diag_ais_ramp_penalty_attribution_$TAG.csv")
