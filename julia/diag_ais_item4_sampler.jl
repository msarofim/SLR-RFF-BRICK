## ============================================================================
## diag_ais_item4_sampler.jl — do the two BADLY-MIXED AIS parameters that REACH
## the deliverable actually corrupt it?
##
## THE QUESTION (handoff 2026-08-24d sec 5 item 1, "ITEM 4", agreed by Marcus).
## The L14 Antarctic certificate fails 9 of 17 structural marginals
## (`ais_l14_block_certified`). The propagation ranking says most of those
## failures sit in parameters that never reach the projection -- but TWO do:
##
##     ais_runoff_Ton     R-hat 1.092   rank 4 at ssp245 (contrast 0.55)
##     antarctic_alpha    R-hat 1.777   rank 5 at ssp245 (contrast 0.21)
##
## `ais_iceflow0` is worse (2.244) but is a reporting caveat. These two are the
## ones a sampler-side effort would be spent on. Before spending it, price the
## defect against the deliverable -- the discipline in memory `npv_retires_tau`.
##
## THREE TESTS, ONE CHAIN READ. They answer three different questions and only
## the first is a verdict.
##
## [1] DELIVERABLE CONVERGENCE. R-hat of the PROJECTION itself, per scenario and
##     horizon, for the AIS component and for the total. This is the only
##     assumption-free measurement here: every draw keeps its own value of every
##     parameter, so the between-chain spread of the projection is what the
##     sampler's failure to mix actually costs, correlations intact.
##     `diag_slr_convergence_by_chain_ladrillo.jl` already certifies the TOTAL at
##     ssp245 / 2100 / 2150 (R-hat 1.017 / 1.015). It has never been measured on
##     the AIS COMPONENT, at 2300, or at ssp585 -- which is the cell where AIS is
##     55% of the band. That gap is exactly this item.
##
## [2] IS THE FAILURE A RIDGE? `calibrate_mcmc_ext.jl:1166` records that the
##     posterior pins SMB - discharge to -145 +/- 15 Gt/yr while SMB and discharge
##     are individually +/- ~505 Gt/yr -- a 34:1 input-output degeneracy, and
##     `ais_iceflow0` and `antarctic_alpha` are precisely the discharge side of
##     it (`speed = iceflow0 * ((1-alpha) + alpha*x^2) * ...`,
##     antarctic_icesheet_component.jl:153). So the hypothesis with a mechanism
##     behind it is that the chains disagree on the two FLUXES and agree on their
##     NET. Measured here as R-hat of the model's own beta_total and ice_flux,
##     over the window the likelihood anchors (1979-2008, the Rignot SMB term)
##     and over a window it cannot see (2281-2300). A ridge that is pinned where
##     the data are and opens where they are not is a DIFFERENT finding from a
##     ridge that is pinned everywhere, and the two imply different fixes.
##
## [3] WHAT ARE THE TWO PARAMETERS WORTH, IN CM? Deterministic monotone transport
##     of one parameter's column onto each chain's own marginal, all other
##     columns untouched: draw i's alpha becomes Q_chain_c(F_pooled(alpha_i)).
##     Zero Monte Carlo noise, and the arm-to-arm difference is that parameter's
##     between-chain disagreement alone.
##     !! A single-parameter transport BREAKS whatever posterior correlation the
##     parameter carries, so on a ridge it is an AS-IF-INDEPENDENT bound, not a
##     posterior revision. The [RIDGE-CORR] gate below measures the correlation
##     so the bound can be read with the right sign of caution. Test [1] is the
##     correlation-respecting number; test [3] is the attribution.
##
## THE ENVELOPE IS THE CHAINS, NOT AN EXTERNAL SUPPORT -- unlike
## scope_ais_lambda_prior.jl, where the question was "what can any revision inside
## the paleo support do" and the arms had to span that support. Here the question
## is "what does the observed between-chain disagreement cost", so the arms span
## the four chains and nothing wider.
##
##   julia --project=julia_v2 julia/diag_ais_item4_sampler.jl [n_per_chain] \
##         [--tag=L14] [--maxrows=N]
## Writes outputs/diag_ais_item4_{deliverable,fluxes,arms}_<tag>.csv
## ============================================================================
using CSV, DataFrames, Statistics, Printf, MCMCDiagnosticTools

include(joinpath(@__DIR__, "ladrillo_projection.jl"))

const REPO   = LADRILLO_REPO
const SEEDS  = [2026, 2027, 2028, 2029]
const NITER  = 2000000
const NBURN  = 1000000
const TAG    = let i = findfirst(a -> startswith(a, "--tag="), ARGS)
    i === nothing ? "L14" : ARGS[i][7:end]
end
const N_TARGET = let p = findfirst(a -> !startswith(a, "--"), ARGS)
    p === nothing ? 500 : parse(Int, ARGS[p])
end
## SMOKE ONLY, and it reads from iteration 1 (nb = 0) so it INCLUDES burn-in.
## Every number it produces is pre-burn-in and none of them is a result; it writes
## to a _SMOKE filename and says so on every header line. Handoff 2026-08-24d sec 4.
const MAXROWS = let i = findfirst(a -> startswith(a, "--maxrows="), ARGS)
    i === nothing ? typemax(Int) : parse(Int, ARGS[i][11:end])
end
const SMOKE  = MAXROWS != typemax(Int)
## Run ONLY the control arm. Tests [1] and [2] and the per-draw table come from it;
## the transport arms of test [3] do not. Used to re-measure the control cheaply
## without paying for eight arms that have not changed.
const CONTROL_ONLY = "--control-only" in ARGS

const SSPS      = ["ssp245", "ssp585"]
const Y0, Y1    = 1850, 2300
const HORIZONS  = [2100, 2150, 2300]
const COMPONENTS = [:ais, :total]
## R-hat threshold for the DELIVERABLE, matching diag_slr_convergence_by_chain*.jl
## and the parameter-level certificate, so the three tables are read on one scale.
const RHAT_OK   = 1.05

## ---- the two parameters this item is about -------------------------------
const P_ALPHA = "antarctic_alpha"     # R-hat 1.777, chain medians span 4.84x
const P_TON   = "ais_runoff_Ton"      # R-hat 1.092, the runoff-onset T_ant
const ITEM4_PARAMS = [P_ALPHA, P_TON]
## The discharge ridge alpha lives on (antarctic_icesheet_component.jl:153) plus
## the ANTO map that feeds it. Reported by [RIDGE-CORR]; not transported.
const RIDGE_PARAMS = ["ais_iceflow0", P_ALPHA, "ais_ocean_temperature₀",
                      "anto_alpha", "anto_beta", "antarctic_gamma"]
## Ton's partner: h0 = -Ton * c, so (Ton, c) is the sampled pair and c is well
## mixed (R-hat 1.003). Reported alongside for the same reason.
const TON_PARAMS   = [P_TON, "ais_c"]

## ---- the flux windows ----------------------------------------------------
## SMB_WIN is the window the A5 Rignot term anchors (calibrate_mcmc_ext.jl:1177):
## inside it the likelihood has a direct opinion about beta_total. FUT_WIN is
## outside every observational stream. The contrast between the two is the test.
const SMB_WIN  = 1979:2008
const FUT_WIN  = 2281:2300
const M3ICE_TO_GT   = 917.0 / 1e12                    # ais_rho_ice = 917 kg/m3
const SMB_TARGET_GT = 2098.0 * (10.92 / 12.295)       # = 1863.4 Gt/yr, area-scaled
const SMB_SIGMA_GT  = 133.0  * (10.92 / 12.295)       # = 118.1 Gt/yr
## The A5 term's own reported outcome, quoted in calibrate_mcmc_ext.jl:1168 --
## used as the [SMB] gate's second leg, on the NET rather than on SMB alone.
const NET_PINNED_GT, NET_PINNED_SD = -145.0, 15.0
## `net` here is beta_total + ice_flux ONLY -- the input-output pair the degeneracy
## lives on. It is NOT the sheet's full dV/dt, which also carries the isostatic term
## and (post-threshold) fast dynamics. `ais_rate` is the scored observable.
const FLUX_QUANTITIES = ("smb", "discharge", "net", "ais_rate")
const FLUX_UNITS = Dict("smb" => "Gt/yr", "discharge" => "Gt/yr",
                        "net" => "Gt/yr", "ais_rate" => "mm/yr")

## --control-only produces a arms table with ONE row in it. Writing that to the full
## run's filename would silently destroy the eight transport arms of test [3] while
## leaving a file that still looks like the deliverable, so the suffix carries the
## mode as well as the smoke flag.
const SUFFIX  = (SMOKE ? "_SMOKE" : "") * (CONTROL_ONLY ? "_CTRLONLY" : "")
const OUT_DEL = joinpath(REPO, "outputs", "diag_ais_item4_deliverable_$(TAG)$(SUFFIX).csv")
const OUT_FLX = joinpath(REPO, "outputs", "diag_ais_item4_fluxes_$(TAG)$(SUFFIX).csv")
const OUT_ARM = joinpath(REPO, "outputs", "diag_ais_item4_arms_$(TAG)$(SUFFIX).csv")

chain_path(sd) = joinpath(REPO, "outputs/mcmc", "chain_$(TAG)_seed$(sd)_n$(NITER).csv")
hdr(sd) = String.(propertynames(CSV.read(chain_path(sd), DataFrame; limit = 0)))
for sd in SEEDS; isfile(chain_path(sd)) || error("missing chain $(chain_path(sd))"); end
const VARIANT = ladrillo_gis_variant(hdr(SEEDS[1]))

@printf("AIS ITEM 4 -- the two badly-mixed parameters that reach the deliverable\n")
@printf("  tag %s%s | %d draws/chain x %d chains | Greenland :%s\n", TAG,
        SMOKE ? "  *** SMOKE (--maxrows=$(MAXROWS)), PRE-BURN-IN, NOT A RESULT ***" : "",
        N_TARGET, length(SEEDS), VARIANT)
@printf("  subjects: %s (R-hat 1.777) and %s (R-hat 1.092)\n", P_ALPHA, P_TON)
@printf("  flux windows: anchored %d-%d (Rignot A5) | unobserved %d-%d\n",
        first(SMB_WIN), last(SMB_WIN), first(FUT_WIN), last(FUT_WIN))
flush(stdout)

"""Read N_TARGET post-burn draws from one chain, in the coordinates the kernel wants."""
function read_draws(sd)
    need = vcat(ladrillo_used_cols(VARIANT), ITEM4_PARAMS, RIDGE_PARAMS, TON_PARAMS) |> unique
    h = hdr(sd)
    rd = ladrillo_gis_needs_native(h) ?
        vcat(setdiff(need, LADRILLO_GIS_SLOW_NATIVE_COLS),
             LADRILLO_GIS_SLOW_REPARAM_COLS) |> unique : need
    miss = setdiff(rd, h)
    isempty(miss) || error("chain_$(TAG)_seed$(sd) is missing: " * join(miss, ", ") *
                           " -- this diagnostic cannot read that vintage")
    df = SMOKE ? CSV.read(chain_path(sd), DataFrame; select = rd, limit = MAXROWS) :
                 CSV.read(chain_path(sd), DataFrame; select = rd)
    nb = SMOKE ? 0 : NBURN
    step = max(1, (nrow(df) - nb) ÷ N_TARGET)
    idx = collect((nb + 1):step:nrow(df))
    length(idx) >= N_TARGET || error("only $(length(idx)) draws available; lower n_per_chain")
    draws = ladrillo_native_greenland!(df[idx[1:N_TARGET], :])
    df = nothing; GC.gc()
    return draws
end

const DRAWS = [(@printf("  reading chain seed%d ...\n", sd); flush(stdout); read_draws(sd))
               for sd in SEEDS]

## ---------------------------------------------------------------------------
## GATES
## ---------------------------------------------------------------------------
@printf("\n%s\nGATES\n%s\n", repeat("=", 78), repeat("=", 78))

pooled(c) = Float64.(vcat([d[!, c] for d in DRAWS]...))

## [RIDGE-CORR] How much posterior correlation does each transported parameter
## carry? A single-column transport breaks exactly this, so the number below is
## how far the test-[3] arms are from a posterior revision.
const USED = intersect(names(DRAWS[1]), ladrillo_used_cols(VARIANT))
for p in ITEM4_PARAMS
    local x = pooled(p)
    local best = 0.0; local bestn = "-"
    for c in USED
        c == p && continue
        local v = pooled(c)
        (std(v) == 0 || !all(isfinite, v)) && continue
        local r = abs(cor(x, v))
        if r > best; best = r; bestn = c; end
    end
    @printf("[RIDGE-CORR] %-18s max |corr| with any used param = %.4f  (%s)\n", p, best, bestn)
end
## and the ridge as a group, so the discharge degeneracy is visible as a matrix
@printf("[RIDGE-CORR] pairwise |corr| inside the discharge group %s:\n",
        join(RIDGE_PARAMS, ", "))
for i in 1:length(RIDGE_PARAMS), j in (i+1):length(RIDGE_PARAMS)
    local r = cor(pooled(RIDGE_PARAMS[i]), pooled(RIDGE_PARAMS[j]))
    abs(r) < 0.20 && continue
    @printf("             %-22s %-22s %+.3f\n", RIDGE_PARAMS[i], RIDGE_PARAMS[j], r)
end
flush(stdout)

## ---------------------------------------------------------------------------
## TRANSPORT
## ---------------------------------------------------------------------------
"""Empirical quantile of a PRE-SORTED vector at u in [0,1], linear interpolation."""
function eq(sorted::Vector{Float64}, u::Float64)
    n = length(sorted)
    h = clamp(u, 0.0, 1.0) * (n - 1) + 1
    lo = floor(Int, h); hi = min(lo + 1, n)
    sorted[lo] + (h - lo) * (sorted[hi] - sorted[lo])
end

"""Pooled-CDF level of each element of `x` against the pooled sample `ref`.
Ties get the midpoint rank, so a stuck chain does not receive an invented order."""
function pooled_u(x::Vector{Float64}, ref::Vector{Float64})
    rs = sort(ref); n = length(rs)
    [ (searchsortedfirst(rs, v) + searchsortedlast(rs, v) - 1) / (2n) for v in x ]
end

## The arms. `chain` is the untouched control and MUST be first: test [1] and the
## [IDENT] check both read it. Every other arm transports ONE column onto ONE
## chain's marginal, leaving every other column of every draw alone.
const ARMS = CONTROL_ONLY ? ["chain"] :
             vcat(["chain"],
                  ["$(p)_to_seed$(sd)" for p in ITEM4_PARAMS for sd in SEEDS])
arm_param(a) = a == "chain" ? "" : String(split(a, "_to_seed")[1])
arm_seed(a)  = a == "chain" ? 0   : parse(Int, split(a, "_to_seed")[2])

## Per-parameter sorted marginals, one per chain, plus the pooled reference.
const MARGINALS = Dict(p => Dict(sd => sort(Float64.(DRAWS[i][!, p]))
                                 for (i, sd) in enumerate(SEEDS)) for p in ITEM4_PARAMS)
const POOLED_REF = Dict(p => pooled(p) for p in ITEM4_PARAMS)

"""Column values for `arm`, given one chain's draws."""
function arm_col(arm::String, d::DataFrame)
    p = arm_param(arm)
    x = Float64.(d[!, p])
    tgt = MARGINALS[p][arm_seed(arm)]
    return [eq(tgt, u) for u in pooled_u(x, POOLED_REF[p])]
end

## ---------------------------------------------------------------------------
## RUN
## ---------------------------------------------------------------------------
del = DataFrame(scenario = String[], component = String[], horizon = Int[],
                rhat = Float64[], ess = Float64[], converged = Bool[],
                pooled_median_cm = Float64[], pooled_p05_cm = Float64[],
                pooled_p95_cm = Float64[], spread_p05_p95_cm = Float64[],
                med_range_cm = Float64[], med_range_over_sd_wc = Float64[],
                n_chains = Int[], n_per_chain = Int[])
for sd in SEEDS
    insertcols!(del, "med_seed$(sd)_cm" => Float64[])
end

## `units` is a COLUMN, not a suffix on the value names: `ais_rate` is mm/yr while
## the three fluxes are Gt/yr, and a `_gt` suffix on a mm/yr number is exactly the
## label-drift this repo's naming convention exists to prevent.
flx = DataFrame(scenario = String[], quantity = String[], window = String[],
                units = String[], rhat = Float64[], ess = Float64[], converged = Bool[],
                pooled_median = Float64[], pooled_p05 = Float64[],
                pooled_p95 = Float64[], med_range_over_sd_wc = Float64[],
                n_chains = Int[], n_per_chain = Int[])
for sd in SEEDS
    insertcols!(flx, "med_seed$(sd)" => Float64[])
end

## PER-DRAW control-arm table. Tests [1] and [2] each report a marginal R-hat, which
## cannot say whether the ONE deliverable cell that fails and the ONE flux quantity
## that fails are the same quantity. That is a correlation between two per-draw
## series, so the series have to be on disk.
perdraw = DataFrame(scenario = String[], seed = Int[], draw = Int[],
                    ais_2100_cm = Float64[], ais_2150_cm = Float64[], ais_2300_cm = Float64[],
                    smb_anchored_gt = Float64[], discharge_anchored_gt = Float64[],
                    net_anchored_gt = Float64[], ais_rate_anchored_mmyr = Float64[])
const OUT_PD = joinpath(REPO, "outputs", "diag_ais_item4_perdraw_$(TAG)$(SUFFIX).csv")

arms = DataFrame(scenario = String[], horizon = Int[], arm = String[], param = String[],
                 n = Int[], param_median = Float64[],
                 median_cm = Float64[], p05_cm = Float64[], p95_cm = Float64[],
                 spread_p05_p95_cm = Float64[])

"""R-hat / ESS from a vector-of-chains, with maxlag passed explicitly: the default
250 floors ESS (memory `mcmc_ess_maxlag`)."""
function rhat_ess(chains::Vector{Vector{Float64}})
    n = length(chains[1])
    a = reshape(reduce(hcat, chains), n, length(chains), 1)
    (rhat(a)[1], ess(a; maxlag = clamp(n - 4, 1, 200_000))[1])
end
med_range_sd(chains) = let m = [median(c) for c in chains],
                           w = sqrt(mean([var(c) for c in chains]))
    (maximum(m) - minimum(m), w > 0 ? (maximum(m) - minimum(m)) / w : NaN)
end

for ssp in SSPS
    local bf = ladrillo_setup(ssp = ssp, y0 = Y0, y1 = Y1, gis_variant = VARIANT)
    local iyr = Dict(y => ladrillo_yi(bf, y) for y in Y0:Y1)
    local ismb = [iyr[y] for y in SMB_WIN]
    local ifut = [iyr[y] for y in FUT_WIN]

    for arm in ARMS
        ## per-chain containers; only the control arm needs chain identity kept
        local proj = Dict((cmp, y) => [Float64[] for _ in SEEDS]
                          for cmp in COMPONENTS, y in HORIZONS)
        local flux = Dict((q, w) => [Float64[] for _ in SEEDS]
                          for q in FLUX_QUANTITIES, w in ("anchored", "unobserved"))
        local pv = Float64[]
        local t0 = time()
        for (ci, d) in enumerate(DRAWS)
            local dd = d
            if arm != "chain"
                dd = copy(d)
                dd[!, arm_param(arm)] = arm_col(arm, d)
                append!(pv, Float64.(dd[!, arm_param(arm)]))
            end
            for r in eachrow(dd)
                ladrillo_run_draw!(bf, r)
                for cmp in COMPONENTS
                    local s = ladrillo_series(bf, cmp)
                    for y in HORIZONS; push!(proj[(cmp, y)][ci], s[iyr[y]]); end
                end
                arm == "chain" || continue
                ## fluxes only on the control arm -- they are a property of the
                ## posterior, not of a transported counterfactual
                ## index FIRST, convert after: Mimi hands back a Union{Missing,Float64}
                ## array whenever a variable is unset in year 1, and a whole-array
                ## Float64.() would die on that rather than on anything real.
                local bt = bf.m[_AIS, :β_total]
                local ifx = bf.m[_AIS, :ice_flux]
                local sais = ladrillo_series(bf, :ais)
                for (wname, wyrs, widx) in (("anchored", SMB_WIN, ismb),
                                            ("unobserved", FUT_WIN, ifut))
                    local smb = mean(Float64.(bt[widx])) * M3ICE_TO_GT
                    local dis = mean(Float64.(ifx[widx])) * M3ICE_TO_GT
                    push!(flux[("smb", wname)][ci], smb)
                    push!(flux[("discharge", wname)][ci], dis)
                    push!(flux[("net", wname)][ci], smb + dis)
                    ## the SCORED observable: AIS sea level rate over the same window,
                    ## endpoint difference in mm/yr. This is what S.ais sees; the two
                    ## fluxes above are not observed separately by any stream.
                    push!(flux[("ais_rate", wname)][ci],
                          10.0 * (sais[iyr[last(wyrs)]] - sais[iyr[first(wyrs)]]) /
                          (last(wyrs) - first(wyrs)))
                end
            end
        end

        if arm == "chain"
            for cmp in COMPONENTS, y in HORIZONS
                local ch = proj[(cmp, y)]
                local r, e = rhat_ess(ch)
                local pool = vcat(ch...)
                local mr, mrsd = med_range_sd(ch)
                push!(del, (ssp, String(cmp), y, r, e, isfinite(r) && r < RHAT_OK,
                            median(pool), quantile(pool, 0.05), quantile(pool, 0.95),
                            quantile(pool, 0.95) - quantile(pool, 0.05), mr, mrsd,
                            length(SEEDS), N_TARGET,
                            [median(c) for c in ch]...))
            end
            for (ci, sd) in enumerate(SEEDS), k in 1:N_TARGET
                push!(perdraw, (ssp, sd, k,
                                proj[(:ais, 2100)][ci][k], proj[(:ais, 2150)][ci][k],
                                proj[(:ais, 2300)][ci][k],
                                flux[("smb", "anchored")][ci][k],
                                flux[("discharge", "anchored")][ci][k],
                                flux[("net", "anchored")][ci][k],
                                flux[("ais_rate", "anchored")][ci][k]))
            end
            for q in FLUX_QUANTITIES, w in ("anchored", "unobserved")
                local ch = flux[(q, w)]
                local r, e = rhat_ess(ch)
                local pool = vcat(ch...)
                local _, mrsd = med_range_sd(ch)
                push!(flx, (ssp, q, w, FLUX_UNITS[q], r, e, isfinite(r) && r < RHAT_OK,
                            median(pool), quantile(pool, 0.05), quantile(pool, 0.95),
                            mrsd, length(SEEDS), N_TARGET,
                            [median(c) for c in ch]...))
            end
        end

        for y in HORIZONS
            local v = vcat(proj[(:ais, y)]...)
            push!(arms, (ssp, y, arm, arm_param(arm), length(v),
                         isempty(pv) ? NaN : median(pv),
                         median(v), quantile(v, 0.05), quantile(v, 0.95),
                         quantile(v, 0.95) - quantile(v, 0.05)))
        end
        local v3 = vcat(proj[(:ais, 2300)]...)
        @printf("  %s / %-28s : %5d draws in %5.0fs | AIS@2300 median %8.2f  p05-p95 %8.2f cm\n",
                ssp, arm, length(v3), time() - t0,
                median(v3), quantile(v3, 0.95) - quantile(v3, 0.05))
        flush(stdout)
    end
end

CSV.write(OUT_DEL, del); CSV.write(OUT_FLX, flx); CSV.write(OUT_ARM, arms)
CSV.write(OUT_PD, perdraw)

## ---- [SAME-Q] is the failing deliverable cell the failing flux quantity? -----
## ssp245 AIS@2100 is the one cell of twelve that fails test [1], and the anchored
## NET is the one quantity of eight that fails test [2]. Their R-hats (1.070/1.069)
## and ESS (38/43) match, which is suggestive and nothing more -- two quantities can
## share a marginal diagnostic without being the same direction. Measured here as
## the per-draw correlation, which is the thing the coincidence would imply.
let a = perdraw[perdraw.scenario .== "ssp245", :]
    @printf("\n[SAME-Q] ssp245 per-draw corr(AIS@2100, anchored net)   = %+.4f\n",
            cor(a.ais_2100_cm, a.net_anchored_gt))
    @printf("[SAME-Q] ssp245 per-draw corr(AIS@2100, anchored SMB)   = %+.4f\n",
            cor(a.ais_2100_cm, a.smb_anchored_gt))
    @printf("[SAME-Q] ssp245 per-draw corr(AIS@2100, anchored disch) = %+.4f\n",
            cor(a.ais_2100_cm, a.discharge_anchored_gt))
    @printf("[SAME-Q] ssp245 per-draw corr(AIS@2100, anchored rate)  = %+.4f\n",
            cor(a.ais_2100_cm, a.ais_rate_anchored_mmyr))
    @printf("[SAME-Q] ssp245 per-draw corr(AIS@2300, anchored net)   = %+.4f\n",
            cor(a.ais_2300_cm, a.net_anchored_gt))
end

## ---------------------------------------------------------------------------
## [1] THE VERDICT
## ---------------------------------------------------------------------------
@printf("\n%s\n[1] DOES THE BLOCK'S FAILURE REACH THE DELIVERABLE?  (R-hat OK < %.2f)\n%s\n",
        repeat("=", 78), RHAT_OK, repeat("=", 78))
@printf("%-8s %-7s %6s %8s %9s %11s %10s %10s\n",
        "scen", "cmp", "yr", "R-hat", "ESS", "med range", "/sd_wc", "p05-p95")
for r in eachrow(del)
    @printf("%-8s %-7s %6d %8.3f %9.1f %10.2f  %10.3f %10.2f  %s\n",
            r.scenario, r.component, r.horizon, r.rhat, r.ess, r.med_range_cm,
            r.med_range_over_sd_wc, r.spread_p05_p95_cm,
            r.converged ? "" : "NOT CONVERGED")
end
@printf("\nVERDICT: %s\n", all(del.converged) ?
        "the projection IS converged in every scenario x component x horizon cell" :
        "the projection is NOT converged in $(count(.!del.converged)) of $(nrow(del)) cells")

## ---------------------------------------------------------------------------
## [2] THE RIDGE
## ---------------------------------------------------------------------------
@printf("\n%s\n[2] IS THE DISCHARGE DEGENERACY PINNED WHERE THE DATA ARE?  (Gt/yr)\n%s\n",
        repeat("=", 78), repeat("=", 78))
@printf("%-8s %-10s %-11s %7s %8s %9s %11s %10s %10s\n",
        "scen", "quantity", "window", "units", "R-hat", "ESS", "median", "/sd_wc", "p05-p95")
for r in eachrow(flx)
    @printf("%-8s %-10s %-11s %7s %8.3f %9.1f %11.2f %10.3f %10.2f  %s\n",
            r.scenario, r.quantity, r.window, r.units, r.rhat, r.ess, r.pooled_median,
            r.med_range_over_sd_wc, r.pooled_p95 - r.pooled_p05,
            r.converged ? "" : "NOT CONVERGED")
end
## [SMB] the anchored window must land on the term the likelihood put there. This
## is a validation of the flux extraction, not a result: if beta_total is being
## read or unit-converted wrongly, it fails here rather than silently downstream.
let a = flx[(flx.quantity .== "smb") .& (flx.window .== "anchored"), :]
    for r in eachrow(a)
        @printf("[SMB]   %s anchored SMB median %.1f Gt/yr vs Rignot A5 target %.1f +/- %.1f => %+.2f sigma  %s\n",
                r.scenario, r.pooled_median, SMB_TARGET_GT, SMB_SIGMA_GT,
                (r.pooled_median - SMB_TARGET_GT) / SMB_SIGMA_GT,
                abs(r.pooled_median - SMB_TARGET_GT) < 3 * SMB_SIGMA_GT ? "OK" :
                "** the flux extraction disagrees with the calibrator **")
    end
end
let a = flx[(flx.quantity .== "net") .& (flx.window .== "anchored"), :]
    for r in eachrow(a)
        @printf("[NET]   %s anchored NET (beta_total + ice_flux, no ISO/fast-dyn) median %.1f Gt/yr;\n",
                r.scenario, r.pooled_median)
        @printf("        the calibrator quotes the SMB-discharge pin as %.0f +/- %.0f Gt/yr\n",
                NET_PINNED_GT, NET_PINNED_SD)
    end
end

## [HIST-IDENT] the two scenarios share one forcing file over 1979-2008 (both GMST
## series are the historical splice through 2014), so every anchored-window flux
## must be BIT-identical between them. A difference here means the anchored window
## is picking up scenario forcing and the "where the data are" leg of test [2] is
## not what it claims.
let a = flx[flx.window .== "anchored", :]
    local worst = 0.0; local worstq = "all"
    for q in FLUX_QUANTITIES
        local v = a[a.quantity .== q, :pooled_median]
        length(v) < 2 && continue
        local d = abs(v[1] - v[2]) / max(abs(v[1]), 1e-12)
        if d > worst; worst = d; worstq = q; end
    end
    @printf("[HIST-IDENT] max cross-scenario rel. difference in the ANCHORED window = %.2e (%s)  %s\n",
            worst, worstq, worst < 1e-12 ? "IDENTICAL, as the shared forcing requires" :
            "** the anchored window is scenario-dependent -- test [2] is mis-scoped **")
end

## [IDENT] the control arm must reproduce the shipped propagation run bit for bit
## at the same n_per_chain -- it is the same draws through the same kernel, so any
## difference is a change in the projection path, not a result.
const SHIPPED = joinpath(REPO, "outputs", "diag_ais_block_propagation_$(TAG).csv")
if isfile(SHIPPED) && !SMOKE
    local sh = CSV.read(SHIPPED, DataFrame)
    for ssp in SSPS, y in HORIZONS
        local a = arms[(arms.scenario .== ssp) .& (arms.horizon .== y) .& (arms.arm .== "chain"), :]
        local b = sh[(sh.scenario .== ssp) .& (sh.horizon .== y), :]
        isempty(b) && continue
        local d = abs(a.spread_p05_p95_cm[1] - b.spread_p05_p95_cm[1]) / b.spread_p05_p95_cm[1]
        @printf("[IDENT] %s @%d control p05-p95 %8.3f vs shipped %8.3f cm  rel %.2e  %s\n",
                ssp, y, a.spread_p05_p95_cm[1], b.spread_p05_p95_cm[1], d,
                d < 1e-10 ? "IDENTICAL" :
                "** DIFFERS -- expected only if n_per_chain differs from that run **")
    end
end

## ---------------------------------------------------------------------------
## [3] THE PRICE, IN CM
## ---------------------------------------------------------------------------
@printf("\n%s\n[3] WHAT THE BETWEEN-CHAIN DISAGREEMENT IS WORTH (AIS component, cm)\n%s\n",
        repeat("=", 78), repeat("=", 78))
println("    as-if-independent: a one-column transport breaks the ridge correlations")
println("    reported by [RIDGE-CORR]; read test [1] for the correlation-respecting number.\n")
for ssp in SSPS, y in HORIZONS
    local base = arms[(arms.scenario .== ssp) .& (arms.horizon .== y) .& (arms.arm .== "chain"), :]
    @printf("\n%s @%d   control: median %8.2f  p05-p95 %8.2f cm\n",
            ssp, y, base.median_cm[1], base.spread_p05_p95_cm[1])
    for p in ITEM4_PARAMS
        local sub = arms[(arms.scenario .== ssp) .& (arms.horizon .== y) .& (arms.param .== p), :]
        isempty(sub) && continue
        for r in eachrow(sub)
            @printf("  %-30s median %8.2f (%+7.2f)  spread %8.2f (x%.3f)\n",
                    r.arm, r.median_cm, r.median_cm - base.median_cm[1],
                    r.spread_p05_p95_cm, r.spread_p05_p95_cm / base.spread_p05_p95_cm[1])
        end
        @printf("  %-30s ENVELOPE median %+.2f cm = %.1f%% of the control p05-p95\n", p,
                maximum(sub.median_cm) - minimum(sub.median_cm),
                100 * (maximum(sub.median_cm) - minimum(sub.median_cm)) / base.spread_p05_p95_cm[1])
    end
end

@printf("\nwrote %s\n      %s\n      %s\n      %s%s\n",
        relpath(OUT_DEL, REPO), relpath(OUT_FLX, REPO), relpath(OUT_ARM, REPO),
        relpath(OUT_PD, REPO),
        SMOKE ? "  *** SMOKE OUTPUT, PRE-BURN-IN -- NOT A RESULT ***" : "")
