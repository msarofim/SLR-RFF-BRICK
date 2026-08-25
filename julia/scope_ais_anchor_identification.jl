## ============================================================================
## scope_ais_anchor_identification.jl — DOES THE HISTORICAL RECORD IDENTIFY THE
##                                      DAIS ANCHOR, AND WHERE DOES IT WANT IT?
##
## THE DESIGN QUESTION (handoff 2026-08-25d §4c). Freeing `T_ant0` is proposed as the
## repair for L15's broken AIS hindcast. Before it can be coded, two things have to be
## known, and neither is currently measured:
##
##   1. WHERE DOES THE DATA WANT THE ANCHOR at L15's amp? §4b's -0.077 K is FIRST-ORDER
##      arithmetic on T_ant alone. T_ant enters precipitation as exp(kappa*T_ant) and the
##      runoff line as h0 + c*T_ant, so the LIKELIHOOD's preferred shift is a different
##      number and it is the one a refit would actually find.
##   2. HOW WELL IS IT IDENTIFIED? §4c flags a flat direction against
##      `antarctic_temp_threshold`: the fast-dynamics channel sees only the DIFFERENCE
##      (T_ant - threshold), so only the SMOOTH channels identify the anchor's absolute
##      level. If their curvature is weak, freeing T_ant0 samples its prior and drags the
##      crossing GMST with it; if it is strong relative to the threshold's own prior sd
##      (0.435 K, outputs/param_priors.csv), the degeneracy is bounded and the arm is safe.
##
## THE MEASUREMENT. Only the anchor moves, so every likelihood term that does not see
## T_ant is CONSTANT and cancels in a difference. What is left is exactly two terms, both
## reconstructed here from calibrate_mcmc_ext.jl:
##   * the AIS sea-level AR(1) term   hetero_logl_ar1(ais[myi] - obs, sd_ais, rho_ais, eps)
##   * the A5 SMB anchor              logpdf(N(SMB_TARGET_GT, SMB_SIGMA_GT), beta_total)
## ⚠ The TOTAL term is NOT included, and that is correct rather than an omission: the
## shipped calibration runs D1 (`DROP_TOTAL = !("--keep-total" in ARGS)`, and neither
## run_mcmc_L15.sh nor the L14 launcher passes it), so the total stream is not in the
## likelihood at all. The assertion below fails the run if the posterior carries the
## sd_dang/rho_dang pair that a --keep-total fit would have.
##
## ⚠ THIS IS A PROFILE AT FIXED PARAMETERS, NOT A MARGINAL. Every other parameter is held
## at the draw's value, so the curvature reported is the CONDITIONAL one -- an UPPER bound
## on the precision a refit would report, because a refit lets `ais_runoff_Ton` and the
## precipitation constant absorb part of the shift. Read the se as "no worse identified
## than this".
##
## THE CONTROL, and it is load-bearing (`no_power_null`). L14 is profiled through the
## SAME code path. L14's amp (0.945) fits the hindcast, so ITS profile must peak near
## zero. If it does not, the likelihood reconstruction is wrong and the L15 number means
## nothing. A test whose null cannot fail reports nothing.
##
##   julia --project=julia_v2 julia/scope_ais_anchor_identification.jl [n_draws] \
##         [--tag=L15] [--ref-tag=L14] [--lo=-0.6] [--hi=0.3] [--step=0.02]
##
## Writes outputs/scope_ais_anchor_identification_<TAG>.csv
## ============================================================================
using CSV, DataFrames, Distributions, LinearAlgebra, Mimi, Printf, Statistics

include(joinpath(@__DIR__, "ladrillo_projection.jl"))

const REPO = LADRILLO_REPO
_argval(p) = (i = findfirst(a -> startswith(a, p), ARGS); i === nothing ? nothing : ARGS[i][length(p)+1:end])
_fval(p, d) = (v = _argval(p); v === nothing ? d : parse(Float64, v))

const NTHIN = let p = filter(a -> !startswith(a, "--"), ARGS)
    isempty(p) ? 200 : parse(Int, p[1])
end
const TAG     = something(_argval("--tag="), "L15")
const REF_TAG = something(_argval("--ref-tag="), "L14")
## --axis: WHICH DIRECTION IS BEING PROFILED.
##   anchor  T_ant0 -> T_ant0 + delta, amp held at the draw's value. The §4c question.
##   amp     amp -> amp + delta, with the anchor PRESERVED exactly as the A6
##           reparameterization does it (coef = 1/amp, intercept = -T_ant0/amp). This is
##           the §4e question: how much does the historical record actually constrain the
##           amplification, i.e. is 0.945-vs-1.09 a thing the data have an opinion about?
const AXIS = something(_argval("--axis="), "anchor")
AXIS in ("anchor", "amp") || error("--axis must be anchor|amp")
const GRID = collect(_fval("--lo=", AXIS == "amp" ? -0.30 : -0.6) :
                     _fval("--step=", 0.02) :
                     _fval("--hi=", AXIS == "amp" ? 0.30 : 0.3))
const OUT = joinpath(REPO, "outputs",
                     "scope_ais_anchor_identification_$(TAG)$(AXIS == "amp" ? "_amp" : "").csv")

## ---- the calibrator's frame, copied by value (calibrate_mcmc_ext.jl:83) ----
const Y0, Y1, B0, B1 = 1850, 2026, 1995, 2005
const FORCING = "ssp245harm"
const SMB_Y0, SMB_Y1 = 1979, 2008
const SMB_TARGET_GT  = 2098.0 * (10.92 / 12.295)
const SMB_SIGMA_GT   = 133.0 * (10.92 / 12.295)
const M3ICE_TO_GT    = 917.0 / 1e12
## The threshold's prior sd, the yardstick the §4c degeneracy is measured against.
const THRESH_PRIOR_SD = let d = CSV.read(joinpath(REPO, "outputs/param_priors.csv"), DataFrame)
    Float64(d[findfirst(==("antarctic_temp_threshold"), d.param), :std])
end

const TG = CSV.read(joinpath(REPO, "outputs/recalib_targets_ext.csv"), DataFrame)
ϵband(lo, hi) = max.((hi .- lo) ./ (2 * 1.645), 0.05)
const AIS_YEARS = let ys = Int[]
    for i in 1:nrow(TG)
        v = TG[i, :ais]
        (TG.year[i] >= 1900 && !ismissing(v) && !isnan(Float64(v))) && push!(ys, Int(TG.year[i]))
    end
    ys = sort(ys)
    ys == collect(ys[1]:ys[end]) || error("ais target has a year gap — AR(1) assumes unit spacing")
    ys
end
const AIS_RI  = [findfirst(==(y), TG.year) for y in AIS_YEARS]
const AIS_OBS = Float64.(TG[AIS_RI, :ais])
const AIS_EPS = ϵband(Float64.(TG[AIS_RI, :ais_lo]), Float64.(TG[AIS_RI, :ais_hi]))
const AIS_H   = abs.(collect(1:length(AIS_YEARS))' .- collect(1:length(AIS_YEARS)))

"""calibrate_mcmc_ext.jl:130, with Σ built once per draw and reused across the grid."""
ais_mvn(σ, ρ) = MvNormal(Symmetric((σ^2 / (1 - ρ^2)) .* ρ .^ AIS_H .+ Diagonal(AIS_EPS .^ 2)))

## ---------------------------------------------------------------------------
## the profile
## ---------------------------------------------------------------------------
"""Vertex of the parabola through the three grid points around the maximum, and the
curvature there. Returns (argmax_shift, se, ll_at_max). `se` is 1/sqrt(-d2ll/dx2), the
conditional standard error of the anchor in DEGREES. NaN when the maximum sits on a grid
edge — a profile that has not turned over inside the window carries no curvature, and
reporting the edge as an argmax would invent one."""
function profile_peak(x, ll)
    k = argmax(ll)
    (k == 1 || k == length(ll)) && return (NaN, NaN, ll[k])
    h = x[k+1] - x[k]
    d2 = (ll[k+1] - 2ll[k] + ll[k-1]) / h^2
    d1 = (ll[k+1] - ll[k-1]) / (2h)
    d2 < 0 || return (NaN, NaN, ll[k])
    return (x[k] - d1 / d2, 1 / sqrt(-d2), ll[k])
end

rows = DataFrame(tag=String[], draw=Int[], shift=Float64[], ll_ais=Float64[],
                 ll_smb=Float64[], ll=Float64[])
peaks = DataFrame(tag=String[], draw=Int[], amp=Float64[], thresh=Float64[],
                  peak_shift=Float64[], se=Float64[], dll_at_zero=Float64[])

function cell!(tag, posterior)
    variant = ladrillo_posterior_variant(posterior)
    post = ladrillo_posterior(path=posterior, cols=:all, nthin=NTHIN)
    ## D1 assertion: the total stream must NOT be in the likelihood, or the two terms
    ## profiled here are not the whole anchor-dependent part of it.
    ("sd_dang" in names(post)) &&
        error("$tag carries sd_dang — that posterior was fit WITH the total stream " *
              "(--keep-total), so the AIS+SMB profile here omits an anchor-dependent " *
              "term. Add the total term before trusting this.")
    bf = ladrillo_setup(ssp="ssp245", y0=Y0, y1=Y1, forcing_tag=FORCING,
                        ref=(B0, B1), gis_variant=variant)
    imy = [ladrillo_yi(bf, y) for y in AIS_YEARS]
    ismb = [ladrillo_yi(bf, y) for y in SMB_Y0:SMB_Y1]
    t0 = time()
    for (i, r) in enumerate(eachrow(post))
        amp = Float64(r["ais_gmst_amp"])
        mvn = ais_mvn(Float64(r["sd_ais"]), Float64(r["rho_ais"]))
        ll = Vector{Float64}(undef, length(GRID))
        for (k, s) in enumerate(GRID)
            ladrillo_apply_draw!(bf, r)
            if AXIS == "anchor"
                update_param!(bf.m, :antarctic_icesheet, :ais_temperature_intercept,
                              -(LADRILLO_AIS_TANT0 + s) / amp)
            else
                ## The A6 pair, moved together — a coefficient without its matching
                ## intercept would move the anchor as a side effect and profile a
                ## direction that is neither axis.
                a = amp + s
                update_param!(bf.m, :antarctic_icesheet, :ais_temperature_coefficient, 1.0 / a)
                update_param!(bf.m, :antarctic_icesheet, :ais_temperature_intercept,
                              -LADRILLO_AIS_TANT0 / a)
            end
            run(bf.m)
            la = logpdf(mvn, ladrillo_series(bf, :ais)[imy] .- AIS_OBS)
            smb = mean(bf.m[:antarctic_icesheet, :β_total][ismb]) * M3ICE_TO_GT
            ls = logpdf(Normal(SMB_TARGET_GT, SMB_SIGMA_GT), smb)
            ll[k] = la + ls
            push!(rows, (tag, i, s, la, ls, ll[k]))
        end
        pk, se, llmax = profile_peak(GRID, ll)
        z0 = findfirst(x -> abs(x) < 1e-9, GRID)
        push!(peaks, (tag, i, amp, Float64(r["antarctic_temp_threshold"]), pk, se,
                      z0 === nothing ? NaN : llmax - ll[z0]))
        i % 25 == 0 && (print("."); flush(stdout))
    end
    @printf("\n  %s: %d draws x %d grid points in %.0fs\n", tag, nrow(post), length(GRID), time() - t0)
end

@printf("DAIS %s IDENTIFICATION | candidate %s | control %s | %d draws\n",
        uppercase(AXIS), TAG, REF_TAG, NTHIN)
@printf("  anchor %.4f degC | grid %.3f..%.3f step %.3f | AIS fit %d-%d (%d yr) | SMB %d-%d\n",
        LADRILLO_AIS_TANT0, GRID[1], GRID[end], GRID[2] - GRID[1],
        AIS_YEARS[1], AIS_YEARS[end], length(AIS_YEARS), SMB_Y0, SMB_Y1)
@printf("  threshold prior sd = %.3f K — the yardstick for the §4c degeneracy\n", THRESH_PRIOR_SD)
println("  ⚠ CONDITIONAL profile at fixed parameters: the se is an UPPER bound on precision.\n")

for t in (REF_TAG, TAG)
    p = joinpath(REPO, "data/MimiBRICK", "parameters_subsample_brick_mengel_$(t).csv")
    isfile(p) || error("no posterior for tag=$t at $p")
    cell!(t, p)
end

CSV.write(OUT, rows)
CSV.write(replace(OUT, ".csv" => "_peaks.csv"), peaks)

## ---------------------------------------------------------------------------
q(v, p) = (x = filter(isfinite, v); isempty(x) ? NaN : quantile(x, p))
println("\n", "="^92)
println(AXIS == "anchor" ?
        "WHERE THE HISTORICAL LIKELIHOOD WANTS THE ANCHOR (degrees, relative to the pinned value)" :
        "WHERE THE HISTORICAL LIKELIHOOD WANTS THE AMPLIFICATION (relative to each draw's own amp)")
println("="^92)
@printf("%-8s %8s %9s %9s %9s %9s %9s %9s\n",
        "arm", "amp med", "peak p05", "peak p50", "peak p95", "se p50", "off-grid", "dll(peak-0)")
for t in (REF_TAG, TAG)
    d = peaks[peaks.tag .== t, :]
    @printf("%-8s %8.3f %9.3f %9.3f %9.3f %9.3f %8.0f%% %9.2f\n", t,
            median(d.amp), q(d.peak_shift, 0.05), q(d.peak_shift, 0.50), q(d.peak_shift, 0.95),
            q(d.se, 0.50), 100 * mean(.!isfinite.(d.peak_shift)), q(d.dll_at_zero, 0.50))
end
## ⚠ EVERY LINE BELOW DERIVES FROM `AXIS`. The §4c yardstick is an ANCHOR question --
## printing it on the amp axis would compare an amplification's se to a temperature's
## prior sd and read as if it meant something.
println("\n  peak = the $(AXIS) shift the AIS series + SMB anchor jointly prefer, per draw.")
println("  se   = conditional 1-sigma on the $(AXIS) from those two terms alone.")
@printf("  CONTROL: %s must peak near 0 — it is the arm whose hindcast already passes.\n", REF_TAG)
if AXIS == "anchor"
    @printf("  §4c: se / threshold prior sd = %.2f (%s). <1 means the smooth channels pin the\n",
            q(peaks[peaks.tag .== TAG, :se], 0.50) / THRESH_PRIOR_SD, TAG)
    println("       anchor more tightly than the threshold's own prior pins the threshold.")
else
    println("  §4e: a peak at each draw's OWN amp is an EXACTLY-COMPENSATED direction, not an")
    println("       identified one. The evidence is the ASYMMETRY of moving BETWEEN the arms;")
    println("       read it off the ll columns of the CSV, not off this table.")
end
println("\nwrote ", relpath(OUT, REPO))
