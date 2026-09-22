## diag_ais_flux_split_vs_imbie.jl — DAIS's OWN mass-balance split on the hindcast, per posterior draw, for the
## structural question IMBIE 2026 raises: the observed Antarctic loss is 84 % dynamics (discharge) and ACCELERATES over
## 2005-2018; DAIS ties its discharge to GMST instantaneously (anto_alpha*GMST + anto_beta -> ice_flux ~ T_oc^2 * depth^gamma).
## Per draw on the calibration span (1850-2026, ssp245harm FaIR-mean forcing, LWS :central as the calibrator):
##   beta_total (SMB, m^3 ice/yr -> Gt/yr), ice_flux (discharge, negative), the AIS sea level (cm rel 1995-2005),
## and the window rates / accelerations that IMBIE measures. Writes per-year quantiles and per-draw window statistics.
##   julia --project=julia_v2 julia/diag_ais_flux_split_vs_imbie.jl --tag=L27 [ndraw=1000]
using CSV, DataFrames, Mimi, MimiBRICK, Statistics, Printf, Dates
include(joinpath(@__DIR__, "ladrillo_projection.jl"))
const SCRIPT = "diag_ais_flux_split_vs_imbie.jl"
const TAG    = (i = findfirst(a -> startswith(a, "--tag="), ARGS); i === nothing ? "L27" : ARGS[i][7:end])
const NTHIN  = (p = filter(a -> !startswith(a, "--"), ARGS); length(p) >= 1 ? parse(Int, p[1]) : 1000)
const Y0, Y1 = 1850, 2026
const FORCING = "ssp245harm"; const REF = (1995, 2005)
const M3ICE_TO_GT = 917.0 / 1e12
const PATH = joinpath(LADRILLO_REPO, "data/MimiBRICK/parameters_subsample_brick_mengel_$TAG.csv")
const WINS = [(1979, 1991), (1992, 2002), (2003, 2010), (2011, 2017), (2018, 2023), (1979, 2008), (1992, 2020)]

post = ladrillo_posterior(path=PATH, cols=:all, nthin=NTHIN)
bf = ladrillo_setup(ssp="ssp245", y0=Y0, y1=Y1, forcing_tag=FORCING, ref=REF, lws=:central, gis_variant=ladrillo_posterior_variant(PATH), ais_ramp=ladrillo_ramp_posterior(PATH))
yrs = collect(Y0:Y1); yi(y) = findfirst(==(y), yrs)
prov = "$SCRIPT | tag $TAG ($(nrow(post)) thinned draws) | hindcast $Y0-$Y1, forcing $FORCING, LWS central | SMB = beta_total, discharge = ice_flux (m^3 ice/yr x $M3ICE_TO_GT = Gt/yr; ice-mass sign) | AIS level cm rel $(REF) | $(now())"
n = nrow(post); ny = length(yrs)
SMB = zeros(n, ny); DIS = zeros(n, ny); LVL = zeros(n, ny); TOC = zeros(n, ny)
for (i, r) in enumerate(eachrow(post))
    ladrillo_run_draw!(bf, r)
    m = bf.m
    f(v) = [ismissing(e) ? NaN : Float64(e) for e in v]      # Mimi leaves the first timestep missing
    SMB[i, :] = f(m[:antarctic_icesheet, :β_total]) .* M3ICE_TO_GT
    DIS[i, :] = f(m[:antarctic_icesheet, :ice_flux]) .* M3ICE_TO_GT
    TOC[i, :] = f(m[:antarctic_ocean, :anto_temperature])
    LVL[i, :] = ladrillo_series(bf, :ais)
end
q(v, p) = (w = filter(!isnan, v); isempty(w) ? NaN : quantile(w, p))
# per-year quantiles
py = DataFrame(year=yrs)
for (nm, A) in (("smb_gt", SMB), ("discharge_gt", DIS), ("net_gt", SMB .+ DIS), ("ais_cm", LVL), ("t_ocean_C", TOC))
    py[!, nm * "_p05"] = [q(A[:, j], 0.05) for j in 1:ny]; py[!, nm * "_p50"] = [q(A[:, j], 0.5) for j in 1:ny]; py[!, nm * "_p95"] = [q(A[:, j], 0.95) for j in 1:ny]
end
py.provenance .= prov
CSV.write(joinpath(LADRILLO_REPO, "outputs/diag_ais_flux_split_vs_imbie_$TAG.csv"), py)
# per-draw window statistics: mean SMB, mean discharge, level rate; the dynamics ANOMALY relative to the 1979-2008 mean
# (IMBIE's anomalies are relative to a balanced reference; its 1979-2008 SMB anomaly is ~0 so that window is the natural
# common reference)
ref = (1979, 2008); ri = yi(ref[1]):yi(ref[2])
pd = DataFrame(draw=1:n)
for (y0, y1) in WINS
    ii = yi(y0):yi(y1)
    pd[!, "smb_$(y0)_$(y1)"] = vec(mean(SMB[:, ii], dims=2)); pd[!, "dis_$(y0)_$(y1)"] = vec(mean(DIS[:, ii], dims=2))
    pd[!, "dis_anom_$(y0)_$(y1)"] = vec(mean(DIS[:, ii], dims=2)) .- vec(mean(DIS[:, ri], dims=2))
    pd[!, "smb_anom_$(y0)_$(y1)"] = vec(mean(SMB[:, ii], dims=2)) .- vec(mean(SMB[:, ri], dims=2))
    pd[!, "rate_cm_yr_$(y0)_$(y1)"] = (LVL[:, yi(y1)] .- LVL[:, yi(y0) - 1]) ./ (y1 - y0 + 1)
end
pd.accel_2011_17_minus_1992_02 = pd.rate_cm_yr_2011_2017 .- pd.rate_cm_yr_1992_2002
pd.provenance .= prov
CSV.write(joinpath(LADRILLO_REPO, "outputs/diag_ais_flux_split_vs_imbie_draws_$TAG.csv"), pd)
for (y0, y1) in WINS
    @printf("%d-%d: SMB %.0f [%.0f, %.0f]  discharge %.0f [%.0f, %.0f]  net %.0f  | dis anomaly vs 1979-2008 %.0f | level rate %.4f cm/yr [%.4f, %.4f]\n",
        y0, y1, q(pd[!, "smb_$(y0)_$(y1)"], .5), q(pd[!, "smb_$(y0)_$(y1)"], .05), q(pd[!, "smb_$(y0)_$(y1)"], .95),
        q(pd[!, "dis_$(y0)_$(y1)"], .5), q(pd[!, "dis_$(y0)_$(y1)"], .05), q(pd[!, "dis_$(y0)_$(y1)"], .95),
        q(pd[!, "smb_$(y0)_$(y1)"] .+ pd[!, "dis_$(y0)_$(y1)"], .5), q(pd[!, "dis_anom_$(y0)_$(y1)"], .5),
        q(pd[!, "rate_cm_yr_$(y0)_$(y1)"], .5), q(pd[!, "rate_cm_yr_$(y0)_$(y1)"], .05), q(pd[!, "rate_cm_yr_$(y0)_$(y1)"], .95))
end
@printf("acceleration (2011-17 rate minus 1992-2002 rate), cm/yr: median %.4f, p95 %.4f, max %.4f\n",
        q(pd.accel_2011_17_minus_1992_02, .5), q(pd.accel_2011_17_minus_1992_02, .95), maximum(pd.accel_2011_17_minus_1992_02))
println("wrote outputs/diag_ais_flux_split_vs_imbie_$TAG.csv and _draws_$TAG.csv")
