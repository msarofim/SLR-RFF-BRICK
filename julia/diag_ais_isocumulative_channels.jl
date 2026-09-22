## ============================================================================
## diag_ais_isocumulative_channels.jl — DOES A DYNAMICS CHANNEL ADD INDEPENDENT INFORMATION,
## OR IS IT THE CUMULATIVE RE-READ WITH A SIGN FLIP?
##
## ⚠⚠ THIS EXISTS BECAUSE THE ARM-TO-ARM COMPARISON CANNOT ANSWER THE QUESTION.
## diag_ais_channel_separation.jl measured (n=100) that the level channel prefers L28 over L27 by
## 7.4 +- 0.4 log-units while the dynamics channel prefers L27 by 3.1 +- 0.5 (IND). That looks like
## two channels carrying different information. It is NOT yet evidence of that, because of
## [[ais_net_dynamics_tradeoff_identity]]: IMBIE's net == smb + dyn, and Ladrillo's SMB cannot move,
## so dyn_misfit == net_misfit - smb_misfit with smb_misfit pinned. An arm that misses the
## CUMULATIVE low is thereby GUARANTEED a better dynamics anomaly. Across the four arms that is
## exactly what is seen (cum 0.948 -> 1.300 cm as the 2018-23 dynamics anomaly degrades
## -119.1 -> -73.4 Gt/yr), so the dynamics channel's preference for L27 may be nothing but the
## level channel's own information, entering with the opposite sign.
##
## THE TEST. Hold the 1979-2023 CUMULATIVE FIXED and vary only the SHAPE of the discharge.
## Any preference the dynamics channel then expresses cannot come from the cumulative, because the
## cumulative is constant along the contour. This is the degeneracy direction the level channel was
## measured to be indifferent along (`diag_ais_objective_shape_sensitivity_L30.csv`: constant offset
## q 2.5343 vs late divergence 2.5308 at rho 0.966, ratio 1.001).
##
## HOW THE CONTOUR IS CONSTRUCTED. The DAIS grounding-line flux law
## (antarctic_icesheet_magdep_component.jl, the `speed =` line) reads
##     speed ~ ais_iceflow0 * ( (1 - antarctic_alpha) + antarctic_alpha * r(t)^2 ) * ...
## with r(t) the normalised ocean-temperature ratio. So `antarctic_alpha` partitions the flux
## between a TEMPERATURE-INDEPENDENT part (1 - alpha) and a TEMPERATURE-TRACKING part alpha*r^2:
## raising alpha converts flat discharge into ACCELERATING discharge, and `ais_iceflow0` is a pure
## multiplier that buys the mean back. That pair is the degeneracy axis, and it is inside the
## `RIDGE_PARAMS` set diag_ais_item4_sampler.jl already names.
##
## For each draw and each alpha multiplier, `ais_iceflow0` is solved by SECANT so that
## cum_1979_2023 returns to the draw's own unperturbed value to within ISO_TOL. ⚠ ISO_TOL is
## DERIVED FROM THE SAMPLED SPREAD, not hand-picked (~/.claude/CLAUDE.md): it is ISO_TOL_SD of the
## across-draw sd of cum_1979_2023, measured on this arm at run time and printed. A draw whose
## solve does not converge is DROPPED and counted, never silently kept off-contour.
##
## READING THE RESULT. Along the contour:
##   LEVEL channel nearly flat  + DYNAMICS channel sloped  => the dynamics channel carries
##       information the level channel does not, and D1 is an IDENTIFICATION gain.
##   BOTH nearly flat                                      => the shape is unidentified by either;
##       a dynamics channel buys nothing here.
##   Both sloped together                                  => the "independent channel" reading is
##       wrong and the dynamics channel is re-reading the level.
##
## ⚠ NOT A REFIT and NOT A PROPOSAL TO CHANGE THE OBJECTIVE. Changing what Ladrillo is fitted to is
## methodological and Marcus's (~/.claude/CLAUDE.md; [[objective_scores_levels_not_rates]]).
##
##   julia --project=julia_v2 julia/diag_ais_isocumulative_channels.jl [--tag=L27] [ndraw]
## Writes outputs/diag_ais_isocumulative_channels_<tag>_<axis>.csv
## ============================================================================
using CSV, DataFrames, Mimi, MimiBRICK, Statistics, Printf, Dates, LinearAlgebra, Distributions

include(joinpath(@__DIR__, "ladrillo_projection.jl"))
include(joinpath(@__DIR__, "antarctic_icesheet_magdep_component.jl"))

const SCRIPT = "diag_ais_isocumulative_channels.jl"
const TAG    = (i = findfirst(a -> startswith(a, "--tag="), ARGS); i === nothing ? "L27" : ARGS[i][7:end])
const NDRAW  = (p = filter(a -> !startswith(a, "--"), ARGS); length(p) >= 1 ? parse(Int, p[1]) : 60)
const PATH   = joinpath(LADRILLO_REPO, "data/MimiBRICK/parameters_subsample_brick_mengel_$TAG.csv")

const Y0, Y1, B0, B1 = 1850, 2026, 1995, 2005
const FORCING      = "ssp245harm"
const TARGETS      = joinpath(LADRILLO_REPO, "outputs/recalib_targets_ext.csv")
const IMBIE        = joinpath(LADRILLO_REPO, "data/observations/raw/imbie2026/imbie3_antarctica_Gt_partitioned.csv")
const OBS_CORR_LEN = 100.0
const LEVEL_Y0     = 1900
const M3ICE_TO_GT  = 917.0 / 1e12
const REF_Y0, REF_Y1 = 1979, 2008
const FIT_Y0, FIT_Y1 = 1979, 2023
const WINS      = [(1979, 1991), (1992, 2002), (2003, 2010), (2011, 2017), (2018, 2023)]
const AR1_RHO   = 0.8
const TREND_WIN = (2018, 2023)
const CUM_Y0, CUM_Y1 = 1978, 2023          # cum_1979_2023 = series[2023] - series[1978]

## The degeneracy axis. ALPHA_MULT multiplies the draw's own antarctic_alpha; ais_iceflow0 is then
## solved to restore the cumulative. 1.0 is the unperturbed control and MUST return f0_mult == 1.
## ⚠ THE AXIS IS AN ARGUMENT, NOT A HARD-CODED PAIR. One axis cannot establish that a channel is
## weak everywhere -- it establishes it along that axis. `--axis=alpha` is the flux-law partition
## (antarctic_alpha tilts discharge about the reference period, ais_iceflow0 restores the mean);
## `--axis=anto` is the OCEAN-TEMPERATURE response instead (anto_alpha is the slope of T_oc in
## GMST, anto_beta its offset), a different tilt mechanism reaching the same flux.
const AXIS = (i = findfirst(a -> startswith(a, "--axis="), ARGS); i === nothing ? "alpha" : ARGS[i][8:end])
const ALPHA_PAR, FLOW_PAR =
    AXIS == "alpha" ? ("antarctic_alpha", "ais_iceflow0") :
    AXIS == "anto"  ? ("anto_alpha", "anto_beta") :
    error("unknown --axis=$AXIS (expected alpha or anto)")
const ALPHA_MULT = [0.50, 0.75, 1.00, 1.30, 1.60]
const ISO_TOL_SD = 0.05                    # iso-cumulative tolerance, in units of the SAMPLED sd
const MAX_IT     = 24

ϵband(lo, hi) = max.((hi .- lo) ./ (2 * 1.645), 0.05)
function hetero_logl_ar1(res, σ, ρ, ϵ, L = OBS_CORR_LEN)
    n = length(res); σp = σ^2 / (1 - ρ^2)
    H = abs.(collect(1:n)' .- collect(1:n))
    Σ = L > 0 ? σp .* ρ .^ H .+ (ϵ * ϵ') .* exp.(-H ./ L) : σp .* ρ .^ H .+ Diagonal(ϵ .^ 2)
    return logpdf(MvNormal(Symmetric(Σ)), res)
end

tg = CSV.read(TARGETS, DataFrame)
ly = [Int(tg.year[i]) for i in 1:nrow(tg)
      if tg.year[i] >= LEVEL_Y0 && !ismissing(tg.ais[i]) && !isnan(Float64(tg.ais[i]))]
sort!(ly); @assert ly == collect(ly[1]:ly[end]) "AIS level target has a year gap"
ti      = [findfirst(==(y), tg.year) for y in ly]
lev_obs = Float64.(tg.ais[ti]); lev_eps = ϵband(Float64.(tg.ais_lo[ti]), Float64.(tg.ais_hi[ti]))

raw = CSV.read(IMBIE, DataFrame; comment = "#")
yr  = [parse(Int, first(string(d), 4)) for d in raw[!, "Date"]]
ann = combine(groupby(DataFrame(year = yr,
                                dyn = raw[!, "Dynamics mass balance anomaly (Gt/yr)"],
                                sig = raw[!, "Dynamics mass balance anomaly uncertainty (Gt/yr)"]), :year),
              :dyn => mean => :dyn, :sig => mean => :sig)
sort!(ann, :year); ann = ann[(ann.year .>= FIT_Y0) .& (ann.year .<= FIT_Y1), :]
ann.anom = ann.dyn .- mean(ann[(ann.year .>= REF_Y0) .& (ann.year .<= REF_Y1), :dyn])
dy = ann.year; nY = length(dy)
Σ_ind = Diagonal(ann.sig .^ 2)
Hd    = abs.(collect(1:nY)' .- collect(1:nY))
Σ_ar1 = (ann.sig * ann.sig') .* (AR1_RHO .^ Hd)
ll(res, Σ) = logpdf(MvNormal(Symmetric(Matrix(Σ))), res)

pp = CSV.read(joinpath(LADRILLO_REPO, "outputs/ladrillo_prior_posterior_$TAG.csv"), DataFrame)
gp(n) = Float64(pp[findfirst(==(n), pp.name), :p50])
const SD_AIS, RHO_AIS = gp("sd_ais"), gp("rho_ais")

post = ladrillo_posterior(path = PATH, cols = :all, nthin = NDRAW)
ladrillo_attach_propagated!(post)
has_ramp = ladrillo_has_ramp(String.(names(post)))
bf = ladrillo_setup(ssp = "ssp245", y0 = Y0, y1 = Y1, forcing_tag = FORCING, ref = (B0, B1),
                    lws = :central, gis_variant = ladrillo_posterior_variant(PATH), ais_ramp = has_ramp)
lmi = [ladrillo_yi(bf, y) for y in ly]
dmi = [ladrillo_yi(bf, y) for y in dy]
rmi = [ladrillo_yi(bf, y) for y in REF_Y0:REF_Y1]
ci0, ci1 = ladrillo_yi(bf, CUM_Y0), ladrillo_yi(bf, CUM_Y1)

@printf("%s | tag %s | %d draws | axis %s (x%s) with %s solved to hold cum %d-%d\n",
        SCRIPT, TAG, nrow(post), ALPHA_PAR, join(ALPHA_MULT, "/"), FLOW_PAR, CUM_Y0 + 1, CUM_Y1)
@printf("  LEVEL at the arm's own (sd_ais %.4f, rho_ais %.4f) | DYNAMICS vs IMBIE %d-%d\n",
        SD_AIS, RHO_AIS, dy[1], dy[end])

"""Run the draw with the given multipliers; return (cum, level ll, dyn lls, trend anomaly)."""
function evaluate!(r, a0, f0, am, fm)
    r[ALPHA_PAR] = a0 * am
    r[FLOW_PAR]  = f0 * fm
    ladrillo_run_draw!(bf, r)
    ser = ladrillo_series(bf, :ais)
    gv(s) = [ismissing(e) ? NaN : Float64(e) for e in bf.m[:antarctic_icesheet, s]] .* M3ICE_TO_GT
    dis  = gv(:ice_flux) .+ gv(:disintegration_rate)
    anom = dis[dmi] .- mean(dis[rmi])
    dres = anom .- ann.anom
    zs = 0.0
    for (a, b) in WINS
        k = findall(y -> a <= y <= b, dy)
        zs += ((mean(anom[k]) - mean(ann.anom[k])) / (mean(ann.sig[k]) / sqrt(length(k))))^2
    end
    return (cum = ser[ci1] - ser[ci0],
            lev = hetero_logl_ar1(ser[lmi] .- lev_obs, SD_AIS, RHO_AIS, lev_eps),
            ind = ll(dres, Σ_ind), ar1 = ll(dres, Σ_ar1), win = -0.5 * zs,
            tr  = mean(anom[findall(y -> TREND_WIN[1] <= y <= TREND_WIN[2], dy)]))
end

## Pass 1: the unperturbed cumulative per draw, so the tolerance can be scaled to its SAMPLED sd.
base = Vector{NamedTuple}(undef, nrow(post))
a0s  = Float64[]; f0s = Float64[]
for (di, r) in enumerate(eachrow(post))
    a0, f0 = Float64(r[ALPHA_PAR]), Float64(r[FLOW_PAR])
    push!(a0s, a0); push!(f0s, f0)
    base[di] = evaluate!(r, a0, f0, 1.0, 1.0)
end
cum_sd  = std([b.cum for b in base])
ISO_TOL = ISO_TOL_SD * cum_sd
@printf("  cum %d-%d across draws: mean %.3f cm, sd %.3f  =>  ISO_TOL = %.2f sd = %.5f cm\n",
        CUM_Y0 + 1, CUM_Y1, mean([b.cum for b in base]), cum_sd, ISO_TOL_SD, ISO_TOL)

rows = DataFrame(); ndrop = 0
for (di, r) in enumerate(eachrow(post))
    a0, f0 = a0s[di], f0s[di]
    for am in ALPHA_MULT
        ## secant on log(f_mult): cum is smooth and monotone in the flux multiplier
        x0, x1 = 0.0, (am > 1 ? -0.05 : 0.05)
        g0 = evaluate!(r, a0, f0, am, exp(x0)).cum - base[di].cum
        res, ok = nothing, false
        for _ in 1:MAX_IT
            e  = evaluate!(r, a0, f0, am, exp(x1))
            g1 = e.cum - base[di].cum
            if abs(g1) <= ISO_TOL; res, ok = (e, exp(x1)), true; break; end
            abs(g1 - g0) < 1e-14 && break
            x0, g0, x1 = x1, g1, x1 - g1 * (x1 - x0) / (g1 - g0)
            (!isfinite(x1) || abs(x1) > 3) && break
        end
        if !ok; global ndrop += 1; continue; end
        e, fm = res
        append!(rows, DataFrame(draw = di, alpha_mult = am, f0_mult = fm,
                                alpha = a0 * am, iceflow0 = f0 * fm,
                                cum_1979_2023 = e.cum, cum_base = base[di].cum,
                                dis_trend_anom = e.tr, dis_trend_anom_base = base[di].tr,
                                ll_lev = e.lev, ll_dyn_ind = e.ind,
                                ll_dyn_ar1 = e.ar1, ll_dyn_win = e.win,
                                d_lev = e.lev - base[di].lev, d_ind = e.ind - base[di].ind,
                                d_ar1 = e.ar1 - base[di].ar1, d_win = e.win - base[di].win))
    end
    di % 10 == 0 && (@printf("  %d/%d draws (%d cells dropped)\n", di, nrow(post), ndrop); flush(stdout))
end

rows.provenance .= "$SCRIPT | tag $TAG | axis $AXIS ($ALPHA_PAR scaled, $FLOW_PAR solved) ($(nrow(post)) draws, DETERMINISTIC even thinning, no RNG) | " *
    "paleo rows by FIXED seed $LADRILLO_PALEO_SEED | ISO-CUMULATIVE contour: $ALPHA_PAR scaled by " *
    "$(join(ALPHA_MULT, "/")) with $FLOW_PAR solved by secant to hold cum $(CUM_Y0+1)-$CUM_Y1 to " *
    "$ISO_TOL_SD sd (= $(round(ISO_TOL, digits=5)) cm) of its across-draw spread; $ndrop non-converged cells DROPPED | " *
    "LEVEL = hetero_logl_ar1(model-obs, sd_ais $SD_AIS, rho_ais $RHO_AIS, eps, L=$OBS_CORR_LEN) on " *
    "$(ly[1])-$(ly[end]) of $(basename(TARGETS)) | DYNAMICS = model (ice_flux + disintegration_rate) " *
    "anomaly vs IMBIE 2026 dynamics anomaly $(dy[1])-$(dy[end]), common ref $REF_Y0-$REF_Y1 | " *
    "IND/AR1(rho $AR1_RHO)/WIN reported, none adopted | no refit | forcing $FORCING | $(now())"
CSV.write(joinpath(LADRILLO_REPO, "outputs/diag_ais_isocumulative_channels_$(TAG)_$(AXIS).csv"), rows)

se(v) = isempty(v) ? NaN : std(v) / sqrt(length(v))
@printf("\n%s\nALONG THE ISO-CUMULATIVE CONTOUR (%d/%d cells converged)\n", "="^104,
        nrow(rows), nrow(post) * length(ALPHA_MULT))
@printf("Each row is a SHAPE change at FIXED cumulative. d_* = log-likelihood change vs the draw's own control.\n")
@printf("\n  %-10s %10s %14s %14s | %14s %14s %14s %14s\n", "alpha x", "f0 x",
        "cum drift cm", "$(TREND_WIN[1])-$(TREND_WIN[2]) anom", "d LEVEL", "d DYN ind", "d DYN ar1", "d DYN win")
for am in ALPHA_MULT
    g = rows[rows.alpha_mult .== am, :]
    isempty(g) && continue
    @printf("  %-10.2f %10.3f %8.5f±%-5.5f %8.1f±%-5.1f | %8.2f±%-5.2f %8.2f±%-5.2f %8.2f±%-5.2f %8.2f±%-5.2f\n",
            am, mean(g.f0_mult), mean(g.cum_1979_2023 .- g.cum_base), se(g.cum_1979_2023 .- g.cum_base),
            mean(g.dis_trend_anom), se(g.dis_trend_anom),
            mean(g.d_lev), se(g.d_lev), mean(g.d_ind), se(g.d_ind),
            mean(g.d_ar1), se(g.d_ar1), mean(g.d_win), se(g.d_win))
end
@printf("\n  IMBIE's own %d-%d dynamics anomaly = %.1f Gt/yr\n", TREND_WIN[1], TREND_WIN[2],
        mean(ann[(ann.year .>= TREND_WIN[1]) .& (ann.year .<= TREND_WIN[2]), :anom]))
println("\n  RANGE ACROSS THE CONTOUR (max - min of the means): the channel's TOTAL discrimination")
for (c, h) in ["d_lev" => "LEVEL", "d_ind" => "DYN ind", "d_ar1" => "DYN ar1", "d_win" => "DYN win"]
    m = [mean(rows[rows.alpha_mult .== am, c]) for am in ALPHA_MULT if any(rows.alpha_mult .== am)]
    @printf("    %-9s %6.2f log-units\n", h, maximum(m) - minimum(m))
end
println("\nwrote outputs/diag_ais_isocumulative_channels_$(TAG)_$(AXIS).csv")
