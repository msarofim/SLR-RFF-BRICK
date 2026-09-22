## ============================================================================
## diag_ais_dynamics_channel_profile.jl — OPTION D1, PRICED BEFORE ANY REFIT
##
## D1 (scoping §9.5) = stop scoring the Antarctic ONLY as a net-mass-balance level, and add a channel
## that scores the model's DYNAMICS (discharge) against IMBIE's dynamics anomaly — the series that has
## no 2018-23 pause, because the pause is SMB ([[ais_ramp_rejected_by_the_pause]]).
##
## ⚠ TWO FACTS FIX THE DESIGN, both measured 09-22g and neither obvious:
##   1. IMBIE's partition is an IDENTITY: smb + dyn == mb to 4e-8 Gt/yr. SMB and dynamics are NOT two
##      independent observations, they are one TOTAL plus one PARTITION. Scoring both as separate
##      channels would double-count. D1 is therefore  level (as now) + ONE dynamics channel  --
##      never level + dynamics + SMB.
##   2. In 2020-23 it is the TOTAL whose uncertainty explodes (sigma_mb 62 -> 160 Gt/yr, sigma_dyn
##      74 -> 161) while sigma_smb FALLS to 27 (9.9 in 2022). IMBIE knows the snowfall and does not
##      know the total in those years, so the anomalous window arrives ALREADY down-weighted in the
##      channels D1 would score.
##
## THE QUESTION. The ramp LOSES 11.85 log-units on the level channel, almost all of it in 2018-25
## (diag_ais_ramp_penalty_attribution.jl). Does it GAIN more than that on a dynamics channel? If yes,
## D1 changes the answer and is worth a refit; if no, D1 is a better-posed likelihood that still does
## not take the ramp, and A (ship the null) stands.
##
## ⚠ THE NOISE MODEL IS A METHODOLOGICAL CHOICE AND IS NOT RESOLVED HERE (Marcus's, per
## ~/.claude/CLAUDE.md). Three are reported side by side so the choice is visible and priced:
##   IND   - independent per year, IMBIE's own published sigma_dyn. The most information (45 yr).
##   AR1   - AR(1) rho=0.8 on the same sigma, i.e. allowing correlated structural error.
##   WIN   - the five IMBIE windows only, window-mean sigma / sqrt(n). The most conservative.
## The anomaly reference is COMMON to model and obs (like-for-like, ~/.claude/CLAUDE.md).
##
##   julia --project=julia_v2 julia/diag_ais_dynamics_channel_profile.jl [--tag=L30] [ndraw]
## Writes outputs/diag_ais_dynamics_channel_profile_<tag>.csv
## ============================================================================
using CSV, DataFrames, Mimi, MimiBRICK, Statistics, Printf, Dates, LinearAlgebra, Distributions

include(joinpath(@__DIR__, "ladrillo_projection.jl"))
include(joinpath(@__DIR__, "antarctic_icesheet_magdep_component.jl"))

const SCRIPT = "diag_ais_dynamics_channel_profile.jl"
const TAG    = (i = findfirst(a -> startswith(a, "--tag="), ARGS); i === nothing ? "L30" : ARGS[i][7:end])
const NDRAW  = (p = filter(a -> !startswith(a, "--"), ARGS); length(p) >= 1 ? parse(Int, p[1]) : 5)
const PATH   = joinpath(LADRILLO_REPO, "data/MimiBRICK/parameters_subsample_brick_mengel_$TAG.csv")
const IMBIE  = joinpath(LADRILLO_REPO, "data/observations/raw/imbie2026/imbie3_antarctica_Gt_partitioned.csv")
const Y0, Y1, B0, B1 = 1850, 2026, 1995, 2005
const FORCING     = "ssp245harm"
const M3ICE_TO_GT = 917.0 / 1e12
const REF_Y0, REF_Y1 = 1979, 2008        # the COMMON anomaly reference, applied to model AND obs
const FIT_Y0, FIT_Y1 = 1979, 2023        # IMBIE Antarctica's own span
const WINS  = [(1979, 1991), (1992, 2002), (2003, 2010), (2011, 2017), (2018, 2023)]
const CELLS = [(NaN, 0.0), (0.45, 1.0e-4), (0.60, 3.0e-4), (0.75, 6.0e-4)]
const AR1_RHO = 0.8                      # the AR1 variant's correlation; a CHOICE, reported not adopted
## The level channel's verdict on the same cells, for the comparison this script exists to make
## (diag_ais_ramp_penalty_attribution.jl, rho 0.966, mean over draws).
const LEVEL_DLOGLIK = Dict(0.0 => 0.0, 1.0e-4 => +0.50, 3.0e-4 => -3.26, 6.0e-4 => -11.85)

## ---- IMBIE annual dynamics anomaly and its published sigma
raw = CSV.read(IMBIE, DataFrame; comment = "#")
yr  = [parse(Int, first(string(d), 4)) for d in raw[!, "Date"]]
dyncol, sigcol = "Dynamics mass balance anomaly (Gt/yr)", "Dynamics mass balance anomaly uncertainty (Gt/yr)"
ann = combine(groupby(DataFrame(year = yr, dyn = raw[!, dyncol], sig = raw[!, sigcol]), :year),
              :dyn => mean => :dyn, :sig => mean => :sig)
sort!(ann, :year)
ann = ann[(ann.year .>= FIT_Y0) .& (ann.year .<= FIT_Y1), :]
oref = mean(ann[(ann.year .>= REF_Y0) .& (ann.year .<= REF_Y1), :dyn])
ann.anom = ann.dyn .- oref
fy = ann.year; nY = length(fy)
@printf("%s | tag %s | IMBIE dynamics %d-%d (%d yr) | common anomaly ref %d-%d | obs ref mean %.1f Gt/yr\n",
        SCRIPT, TAG, fy[1], fy[end], nY, REF_Y0, REF_Y1, oref)
@printf("  published sigma_dyn: median %.1f, %d-%d mean %.1f Gt/yr\n", median(ann.sig), 2020, FIT_Y1,
        mean(ann[ann.year .>= 2020, :sig]))

post = ladrillo_posterior(path = PATH, cols = :all, nthin = NDRAW); ladrillo_attach_propagated!(post)
has_ramp = ladrillo_has_ramp(String.(names(post)))
bf = ladrillo_setup(ssp = "ssp245", y0 = Y0, y1 = Y1, forcing_tag = FORCING, ref = (B0, B1),
                    lws = :central, gis_variant = ladrillo_posterior_variant(PATH), ais_ramp = has_ramp)
yrs = collect(Y0:Y1); yi(y) = findfirst(==(y), yrs)
mi = [yi(y) for y in fy]; ri = [yi(y) for y in REF_Y0:REF_Y1]

## The three noise models, as covariance matrices on the ANOMALY DIFFERENCE.
Σ_ind = Diagonal(ann.sig .^ 2)
H     = abs.(collect(1:nY)' .- collect(1:nY))
Σ_ar1 = (ann.sig * ann.sig') .* (AR1_RHO .^ H)
ll(res, Σ) = logpdf(MvNormal(Symmetric(Matrix(Σ))), res)

rows = DataFrame()
for (di, r) in enumerate(eachrow(post))
    base = nothing
    for (gon, s) in CELLS
        if has_ramp
            r["ais_ramp_gon"]    = isnan(gon) ? 0.45 : gon
            r["ais_ramp_log10s"] = s == 0.0 ? -12.0 : log10(s)
        end
        ladrillo_run_draw!(bf, r)
        ## ⚠ MODEL DYNAMICS = ice_flux + disintegration_rate. The fast-dynamics term carries the RAMP
        ## (the component does `disintegration_rate += ramp_rate`), so reading `ice_flux` alone makes the
        ## ramp almost invisible on this channel -- which is exactly what the first run of this script
        ## showed (32.5 -> 32.7 Gt/yr), and is a diagnostic bug, not a finding.
        gv(sym) = [ismissing(e) ? NaN : Float64(e) for e in bf.m[:antarctic_icesheet, sym]] .* M3ICE_TO_GT
        dis = gv(:ice_flux) .+ gv(:disintegration_rate)
        smb = gv(:β_total)
        anom = dis[mi] .- mean(dis[ri])          # SAME reference construction as the obs
        res  = anom .- ann.anom
        row = DataFrame(draw = di, G_on = gon, slope = s,
                        ll_ind = ll(res, Σ_ind), ll_ar1 = ll(res, Σ_ar1),
                        dis_2011_17 = mean(dis[[yi(y) for y in 2011:2017]]),
                        dis_2018_23 = mean(dis[[yi(y) for y in 2018:2023]]),
                        smb_2011_17 = mean(smb[[yi(y) for y in 2011:2017]]),
                        smb_2018_23 = mean(smb[[yi(y) for y in 2018:2023]]))
        ## WIN: the five IMBIE windows, window means, sigma_dyn/sqrt(n) per window
        zs = 0.0
        for (a, b) in WINS
            k = findall(y -> a <= y <= b, fy)
            sw = mean(ann.sig[k]) / sqrt(length(k))
            zs += ((mean(anom[k]) - mean(ann.anom[k])) / sw)^2
            row[!, "win_$(a)_$(b)"] = [mean(anom[k]) - mean(ann.anom[k])]
        end
        row.ll_win = [-0.5 * zs]
        append!(rows, row)
    end
    @printf("  draw %d/%d\n", di, nrow(post)); flush(stdout)
end

rows.provenance .= "$SCRIPT | tag $TAG ($(nrow(post)) draw(s)) | model discharge = ice_flux x $M3ICE_TO_GT Gt/yr, " *
    "anomaly vs $REF_Y0-$REF_Y1 | obs = IMBIE 2026 Antarctica dynamics anomaly (Otosaka et al. Sci Data 13:1301), " *
    "SAME reference window | IND = independent per-year published sigma_dyn; AR1 = rho $AR1_RHO on the same sigma; " *
    "WIN = $(length(WINS)) window means, sigma/sqrt(n) | noise model NOT adopted, reported for the choice | " *
    "all other parameters FIXED, no refit | $(now())"
CSV.write(joinpath(LADRILLO_REPO, "outputs/diag_ais_dynamics_channel_profile_$TAG.csv"), rows)

b = Dict(d => rows[(rows.draw .== d) .& (rows.slope .== 0.0), :][1, :] for d in unique(rows.draw))
println("\nDYNAMICS-channel log-likelihood GAIN from the ramp (positive = this channel WANTS the ramp), mean over draws")
@printf("  %-22s %10s %10s %10s | %14s %10s\n", "ramp cell", "IND", "AR1", "WIN", "LEVEL (rho.966)", "NET (IND)")
for (gon, s) in CELLS
    s == 0.0 && continue
    m = rows[(rows.G_on .=== gon) .& (rows.slope .== s), :]
    gi = mean(m.ll_ind .- [b[d].ll_ind for d in m.draw])
    ga = mean(m.ll_ar1 .- [b[d].ll_ar1 for d in m.draw])
    gw = mean(m.ll_win .- [b[d].ll_win for d in m.draw])
    lv = LEVEL_DLOGLIK[s]
    @printf("  on %.2f K  s %.1e %10.2f %10.2f %10.2f | %14.2f %10.2f\n", gon, s, gi, ga, gw, lv, gi + lv)
end
println("\nDynamics anomaly MISFIT by IMBIE window (model - obs, Gt/yr; negative = model loses too little)")
@printf("  %-22s", "ramp cell"); for (a, bb) in WINS; @printf("%12s", "$(a)-$(bb)"); end; println()
for (gon, s) in CELLS
    m = rows[(rows.G_on .=== gon) .& (rows.slope .== s), :]
    @printf("  %-22s", s == 0.0 ? "no ramp" : @sprintf("on %.2f K s %.1e", gon, s))
    for (a, bb) in WINS; @printf("%12.1f", mean(m[!, "win_$(a)_$(bb)"])); end; println()
end
println("\nModel ABSOLUTE fluxes (Gt/yr, ice-mass sign), mean over draws -- for the pause comparison")
for (gon, s) in CELLS
    m = rows[(rows.G_on .=== gon) .& (rows.slope .== s), :]
    @printf("  %-22s dynamics %8.1f -> %8.1f   SMB %8.1f -> %8.1f   net %8.1f -> %8.1f  (2011-17 -> 2018-23)\n",
            s == 0.0 ? "no ramp" : @sprintf("on %.2f K s %.1e", gon, s),
            mean(m.dis_2011_17), mean(m.dis_2018_23), mean(m.smb_2011_17), mean(m.smb_2018_23),
            mean(m.dis_2011_17 .+ m.smb_2011_17), mean(m.dis_2018_23 .+ m.smb_2018_23))
end
println("\nwrote outputs/diag_ais_dynamics_channel_profile_$TAG.csv")
