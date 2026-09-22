## ============================================================================
## scope_ais_onset_sweep.jl — CAN AN ONSET INSIDE THE OBSERVED RANGE REACH IMBIE'S
## 2011-17 RATE, AND AT WHAT PROJECTION COST?  (fixed-parameter sweep, no sampler)
##
## WHY THIS EXISTS. IMBIE 2026's reconciled AIS record doubles its loss-per-K between
## 0.45 and 1.02 K of global warming while staying flat before that; L28/L29 showed
## DAIS's linear discharge response has no direction that produces it, and scoping §6
## (notes/scoping_2026-09-21_dais_structure_vs_imbie2026.md) showed a free exponent on
## the ocean-temperature ratio is inert on the historical range (needs n ~ 20). The
## shape is a KINK near 0.5 K — an onset. This script asks, on the L29 posterior with
## everything else FIXED, whether a linear ramp above an onset temperature can carry the
## modern rate, and what the same ramp does at 2100 / 2300 on three SSPs.
##
## THE TERM. The magdep component's fast-dynamics flux, -lambda * (excess/ref)^n * const,
## with n = 1 and ref = 1 K, is a LINEAR RAMP: rate = -s * max(T_ant - T_crit, 0), s in
## m SLE/yr per K of excess. The onset is swept in GLOBAL warming, G_on, and mapped per
## draw through that draw's own amp: T_crit = TANT0 + amp * G_on, so "onset at +0.5 K
## global" means the same thing on every draw. The stock paleo pair (lambda, T_crit
## attached from outputs/paleo_fastdyn_draws.csv; fires at ~+2.8 C T_ant) is REPLACED by
## the ramp in the onset arms; the `stock` arm keeps it, the `none` arm zeroes it, so the
## projection difference between the two shipped-form arms is separated from the ramp.
##
## WHAT IT DOES NOT DO. It does not refit. Every arm adds the ramp ON TOP of L29's fitted
## level, so the 1979-2023 cumulative will overshoot where the modern rate is reached —
## a refit would re-buy the level through SMB / ais_c the way L28 and L29 did. Read the
## SHAPE columns (window rates, the acceleration, the discharge anomaly), not the level.
##
##   julia --project=julia_v2 julia/scope_ais_onset_sweep.jl [ndraw=150] [--tag=L29] [--smoke]
## Writes outputs/scope_ais_onset_sweep_{hindcast,proj}_<tag>.csv (+ _draws_ for the hindcast)
## ============================================================================
using CSV, DataFrames, Mimi, MimiBRICK, Statistics, Printf, Dates
include(joinpath(@__DIR__, "ladrillo_projection.jl"))
include(joinpath(@__DIR__, "antarctic_icesheet_magdep_component.jl"))

const SCRIPT = "scope_ais_onset_sweep.jl"
const TAG    = (i = findfirst(a -> startswith(a, "--tag="), ARGS); i === nothing ? "L29" : ARGS[i][7:end])
const SMOKE  = "--smoke" in ARGS
const NDRAW  = (p = filter(a -> !startswith(a, "--"), ARGS); length(p) >= 1 ? parse(Int, p[1]) : (SMOKE ? 3 : 150))
const PATH   = joinpath(LADRILLO_REPO, "data/MimiBRICK/parameters_subsample_brick_mengel_$TAG.csv")
const TANT0  = LADRILLO_AIS_TANT0
const M3ICE_TO_GT = 917.0 / 1e12
## Hindcast exactly as the calibrator and diag_ais_flux_split_vs_imbie.jl see it.
const HY0, HY1 = 1850, 2026
const HFORCING = "ssp245harm"; const HREF = (1995, 2005)
const WINS = [(1900, 1978), (1979, 1991), (1992, 2002), (2003, 2010), (2011, 2017), (2018, 2023), (1979, 2008), (1979, 2023)]
## IMBIE 2026 window rates (cm/yr, level; from diag_imbie2026_vs_targets_windows) and their use here: the
## SUCCESS LINE pre-registered in handoff 09-22 §1 is 2011-17 within 1 sigma of 0.0556 (sigma 0.007).
const IMBIE_RATE = Dict((1979,1991) => 0.013, (1992,2002) => 0.022, (2003,2010) => 0.044, (2011,2017) => 0.0556, (2018,2023) => 0.029)
const IMBIE_2011_17_SD = 0.007
const IMBIE_CUM_1979_2023 = (1.328, 0.14)
## Projections: three SSPs, fixed FaIR-mean climate, the paper's horizons.
const SSPS = ["ssp126", "ssp245", "ssp585"]; const PY0, PY1 = 1850, 2300; const HORIZONS = [2100, 2300]
## THE GRID. G_on in K of global warming (1850-1900 frame of the driver): the record's kink is near 0.5 K;
## the driver crosses 0.3 K ~1970s, 0.45 ~1980s, 0.6 ~late 1990s, 0.75 ~2000s. s in m SLE/yr per K: the
## acceleration-window discharge shortfall (IMBIE -106 vs L29 -52 Gt/yr ~ 1.5e-4 m/yr) over a ~0.5 K
## excess puts the centre near 3e-4; the grid brackets it by 4x each way.
const G_ON  = SMOKE ? [0.5] : [0.3, 0.45, 0.6, 0.75]
const SLOPE = SMOKE ? [3e-4] : [0.75e-4, 1.5e-4, 3e-4, 6e-4, 12e-4]

post = ladrillo_posterior(path=PATH, cols=:all, nthin=NDRAW)
ladrillo_attach_propagated!(post)          # stock paleo (lambda, T_crit) per draw; no-op if carried
const VARIANT = ladrillo_posterior_variant(PATH)
n = nrow(post)
@printf("%s | tag %s | %d draws | grid G_on %s x s %s%s\n", SCRIPT, TAG, n, string(G_ON), string(SLOPE), SMOKE ? "  ** SMOKE **" : "")
flush(stdout)

## Arm = (name, lambda_fn(row), tcrit_fn(row), nfd). Stock keeps the paleo pair with the binary flux (n = 0).
arms = Any[("stock", r -> r.antarctic_lambda, r -> r.antarctic_temp_threshold, 0.0),
           ("none",  r -> 0.0,                r -> r.antarctic_temp_threshold, 0.0)]
for g in G_ON, s in SLOPE
    push!(arms, (@sprintf("on%.2f_s%.2e", g, s), r -> s, r -> TANT0 + r.ais_gmst_amp * g, 1.0))
end
arm_gon(a)   = (m = match(r"on([0-9.]+)_s", a); m === nothing ? NaN : parse(Float64, m[1]))
arm_slope(a) = (m = match(r"_s([0-9.e+-]+)$", a); m === nothing ? NaN : parse(Float64, m[1]))

function build(ssp, y0, y1; forcing_tag, ref, nfd)
    bf = ladrillo_setup(ssp=ssp, y0=y0, y1=y1, forcing_tag=forcing_tag, ref=ref, lws=:central, gis_variant=VARIANT)
    replace!(bf.m, :antarctic_icesheet => antarctic_icesheet_magdep)
    update_param!(bf.m, :antarctic_icesheet, :ais_fastdyn_exponent, nfd)
    update_param!(bf.m, :antarctic_icesheet, :ais_fastdyn_ref_excess, 1.0)
    update_param!(bf.m, :antarctic_icesheet, :ais_fastdyn_gmax, Inf)
    bf
end
function arm_rows(post, lam, tc)
    d = copy(post)
    d.antarctic_lambda = [Float64(lam(r)) for r in eachrow(post)]
    d.antarctic_temp_threshold = [Float64(tc(r)) for r in eachrow(post)]
    d
end
f(v) = [ismissing(e) ? NaN : Float64(e) for e in v]
q(v, p) = (w = filter(!isnan, v); isempty(w) ? NaN : quantile(w, p))

## Driver crossing years, for reading the grid
let g = _yearmap(joinpath(LADRILLO_OBS, "fair_mean_gmst_$(HFORCING).csv"), "gmst_C")
    yrs = collect(HY0:HY1); gg = [g[y] for y in yrs]
    gg .-= mean(gg[1:51])       # 1850-1900 frame, as the glacier driver is rebased
    for gon in G_ON
        i = findfirst(>=(gon), gg)
        @printf("  driver (%s) first crosses %.2f K in %s; 2011-17 mean %.3f K, 1900-78 mean %.3f K\n", HFORCING, gon,
                i === nothing ? "never" : string(yrs[i]), mean(gg[findfirst(==(2011), yrs):findfirst(==(2017), yrs)]),
                mean(gg[findfirst(==(1900), yrs):findfirst(==(1978), yrs)]))
    end
end

## ---- hindcast ----
hy = collect(HY0:HY1); hyi(y) = findfirst(==(y), hy)
ri = hyi(1979):hyi(2008)
hind = DataFrame(); hind_draws = DataFrame()
bfh = Dict(nfd => build("ssp245", HY0, HY1; forcing_tag=HFORCING, ref=HREF, nfd=nfd) for nfd in (0.0, 1.0))
t0 = time()
for (name, lam, tc, nfd) in arms
    d = arm_rows(post, lam, tc); bf = bfh[nfd]
    SMB = zeros(n, length(hy)); DIS = zeros(n, length(hy)); FD = zeros(n, length(hy)); LVL = zeros(n, length(hy)); FLOOR = zeros(n)
    for (i, r) in enumerate(eachrow(d))
        ladrillo_run_draw!(bf, r); m = bf.m
        SMB[i, :] = f(m[:antarctic_icesheet, :β_total]) .* M3ICE_TO_GT
        DIS[i, :] = f(m[:antarctic_icesheet, :ice_flux]) .* M3ICE_TO_GT
        FD[i, :]  = f(m[:antarctic_icesheet, :disintegration_rate]) .* M3ICE_TO_GT
        FLOOR[i]  = sum(f(m[:antarctic_icesheet, :disintegration_floored])[2:end])
        LVL[i, :] = ladrillo_series(bf, :ais)
    end
    pd = DataFrame(arm=fill(name, n), draw=1:n)
    for (y0, y1) in WINS
        ii = hyi(y0):hyi(y1)
        pd[!, "rate_$(y0)_$(y1)"] = (LVL[:, hyi(y1)] .- LVL[:, hyi(y0) - 1]) ./ (y1 - y0 + 1)
        pd[!, "net_$(y0)_$(y1)"]  = vec(mean(SMB[:, ii] .+ DIS[:, ii] .+ FD[:, ii], dims=2))
        pd[!, "dyn_anom_$(y0)_$(y1)"] = vec(mean(DIS[:, ii] .+ FD[:, ii], dims=2)) .- vec(mean(DIS[:, ri] .+ FD[:, ri], dims=2))
        pd[!, "fd_$(y0)_$(y1)"] = vec(mean(FD[:, ii], dims=2))
    end
    pd.cum_1979_2023 = LVL[:, hyi(2023)] .- LVL[:, hyi(1978)]
    pd.accel = pd.rate_2011_2017 .- pd.rate_1992_2002
    pd.dyn_accel = pd.dyn_anom_2011_2017 .- pd.dyn_anom_1992_2002
    pd.floor_years = FLOOR
    append!(hind_draws, pd)
    row = DataFrame(arm=name, G_on=arm_gon(name), slope_m_yr_K=arm_slope(name), nfd=nfd)
    for c in names(pd)[3:end]
        row[!, c * "_p50"] = [q(pd[!, c], .5)]; row[!, c * "_p05"] = [q(pd[!, c], .05)]; row[!, c * "_p95"] = [q(pd[!, c], .95)]
    end
    row.z_2011_17 = [(row.rate_2011_2017_p50[1] - IMBIE_RATE[(2011,2017)]) / IMBIE_2011_17_SD]
    row.z_cum = [(row.cum_1979_2023_p50[1] - IMBIE_CUM_1979_2023[1]) / IMBIE_CUM_1979_2023[2]]
    append!(hind, row)
    @printf("[%5.0fs] %-16s rate 92-02 %.4f  03-10 %.4f  11-17 %.4f (z %+.2f)  18-23 %.4f | 1900-78 net %.0f | dyn accel %.0f Gt/yr | cum79-23 %.2f (z %+.2f) | fd 11-17 %.0f | floor yrs %.1f\n",
            time() - t0, name, row.rate_1992_2002_p50[1], row.rate_2003_2010_p50[1], row.rate_2011_2017_p50[1], row.z_2011_17[1],
            row.rate_2018_2023_p50[1], row.net_1900_1978_p50[1], row.dyn_accel_p50[1], row.cum_1979_2023_p50[1], row.z_cum[1],
            row.fd_2011_2017_p50[1], mean(FLOOR))
    flush(stdout)
end
prov = "$SCRIPT | tag $TAG ($n thinned draws of $(basename(PATH))) | hindcast $HY0-$HY1 forcing $HFORCING LWS central ref $HREF | ramp: rate = -s*max(T_ant - T_crit,0), T_crit = TANT0 + amp*G_on per draw, n_fd 1, ref 1 K; stock = paleo pair binary; none = lambda 0 | IMBIE 2011-17 $(IMBIE_RATE[(2011,2017)]) +- $IMBIE_2011_17_SD cm/yr; cum 1979-2023 $(IMBIE_CUM_1979_2023) | units cm/yr, Gt/yr ice-mass sign | $(now())"
hind.provenance .= prov; hind_draws.provenance .= prov
CSV.write(joinpath(LADRILLO_REPO, "outputs/scope_ais_onset_sweep_hindcast_$TAG.csv"), hind)
CSV.write(joinpath(LADRILLO_REPO, "outputs/scope_ais_onset_sweep_hindcast_draws_$TAG.csv"), hind_draws)

## ---- projections ----
proj = DataFrame()
for ssp in SSPS
    bfp = Dict(nfd => build(ssp, PY0, PY1; forcing_tag=ssp, ref=LADRILLO_REF, nfd=nfd) for nfd in (0.0, 1.0))
    py = collect(PY0:PY1); pyi(y) = findfirst(==(y), py)
    for (name, lam, tc, nfd) in arms
        d = arm_rows(post, lam, tc); bf = bfp[nfd]
        A = zeros(n, length(HORIZONS)); FL = zeros(n); FDC = zeros(n, length(HORIZONS))
        for (i, r) in enumerate(eachrow(d))
            ladrillo_run_draw!(bf, r); m = bf.m
            lv = ladrillo_series(bf, :ais)
            A[i, :] = [lv[pyi(h)] for h in HORIZONS]
            fd = f(m[:antarctic_icesheet, :disintegration_rate]); fd[isnan.(fd)] .= 0.0
            FDC[i, :] = [-sum(fd[1:pyi(h)]) * 57.0 / 24.78e15 * 100 for h in HORIZONS]   # cm SLE from the ramp/binary term
            FL[i] = sum(f(m[:antarctic_icesheet, :disintegration_floored])[2:end])
        end
        row = DataFrame(ssp=ssp, arm=name, G_on=arm_gon(name), slope_m_yr_K=arm_slope(name), nfd=nfd)
        for (k, h) in enumerate(HORIZONS)
            row[!, "ais_$(h)_p50"] = [q(A[:, k], .5)]; row[!, "ais_$(h)_p05"] = [q(A[:, k], .05)]; row[!, "ais_$(h)_p95"] = [q(A[:, k], .95)]
            row[!, "ais_$(h)_mean"] = [mean(A[:, k])]
            row[!, "fd_cm_$(h)_p50"] = [q(FDC[:, k], .5)]
            row[!, "tipped15_$(h)"] = [count(>(15.0), A[:, k]) / n]
        end
        row.floor_years_mean = [mean(FL)]
        append!(proj, row)
        @printf("[%5.0fs] %s %-16s AIS 2100 p50 %6.1f p95 %6.1f (ramp/fd part %5.1f) | 2300 p50 %6.1f p95 %6.1f (fd %6.1f) | floor yrs %.1f\n",
                time() - t0, ssp, name, row.ais_2100_p50[1], row.ais_2100_p95[1], row.fd_cm_2100_p50[1],
                row.ais_2300_p50[1], row.ais_2300_p95[1], row.fd_cm_2300_p50[1], row.floor_years_mean[1])
        flush(stdout)
    end
end
proj.provenance .= "$SCRIPT | tag $TAG ($n draws) | projections $PY0-$PY1 fixed FaIR-mean climate, ref $(LADRILLO_REF), LWS central | arms as hindcast file | fd_cm = cumulative fast-dynamics (ramp or binary) contribution, cm SLE | tipped15 = share of draws with AIS@h > 15 cm | $(now())"
CSV.write(joinpath(LADRILLO_REPO, "outputs/scope_ais_onset_sweep_proj_$TAG.csv"), proj)
println("wrote outputs/scope_ais_onset_sweep_{hindcast,hindcast_draws,proj}_$TAG.csv")
