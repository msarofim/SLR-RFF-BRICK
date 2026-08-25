## ============================================================================
## scope_ais_fastdyn_shape.jl — WHAT IS DAIS'S BINARY FAST-DYNAMICS FORM WORTH?
##
## THE DEFECT. Stock DAIS disintegrates at a CONSTANT flux the moment T_ant
## clears T_crit and forever after, with no dependence on how far above it goes
## (`antarctic_icesheet_component.jl:180-184`). Measured on this very posterior,
## the median above-threshold excess is **0.391 degC at ssp245@2300 and 4.529 at
## ssp585@2300 — a factor of 11.6** — and the stock form charges both the SAME
## flux. That is the mechanism behind the scenario inversion
## (`ais_spread_is_lambda_prior`): once every ssp585 draw tips, WHETHER stops
## discriminating and the model has no channel left for HOW HOT.
##
## WHAT IS MEASURED HERE. `antarctic_icesheet_magdep_component.jl` generalises the
## flux to `-lambda * g * const` with `g = (excess/ref)^n`, n = 0 being stock. This
## script propagates n over the L14 posterior and reports the six
## scenario x horizon cells.
##
## WHY NO REFIT IS NEEDED — AND WHY IT IS MEASURED, NOT ASSUMED.
## `ais_lambda_rests_on_lig` established that 0.00% of draws cross the threshold
## anywhere in 1850-2024, so the disintegration term is identically zero across the
## whole calibration window for EVERY n. Gate [INERT] asserts the 1850-2024 AIS
## series is bit-identical across arms rather than trusting that argument.
##
## THE ANCHOR IS A METHODOLOGICAL CHOICE AND IS NOT RESOLVED HERE.
## `ref_excess` sets where lambda keeps its stock meaning, and it moves the LEVELS a
## lot. So this script does NOT pick one. It runs a `lam0` arm (lambda forced to
## zero) which isolates the fast-dynamics contribution per draw, verifies with gate
## [AFFINE] that AIS is affine in lambda, and then reports the WHOLE ANCHOR
## ENVELOPE arithmetically — every cell used in turn as the anchor — instead of one
## number. Reporting the envelope rather than one alternative is the same
## discipline `scope_ais_lambda_prior.jl` applied to the prior.
##
## WHAT IS ANCHOR-FREE. A lambda rescale is a constant multiplier on the
## disintegration part, so the ssp585-vs-ssp245 SEPARATION of that part is
## invariant to the anchor. That ratio, not the levels, is the robust finding.
##
##   julia --project=julia_v2 julia/scope_ais_fastdyn_shape.jl [n_per_chain] [--tag=L14] [--maxrows=N]
## Writes outputs/scope_ais_fastdyn_{cells,envelope,excess}_<tag>.csv
## ============================================================================
using CSV, DataFrames, Statistics, Printf, Mimi

include(joinpath(@__DIR__, "ladrillo_projection.jl"))
include(joinpath(@__DIR__, "antarctic_icesheet_magdep_component.jl"))

const REPO   = LADRILLO_REPO
const SEEDS  = [2026, 2027, 2028, 2029]
const NITER  = 2000000
const NBURN  = 1000000
const TAG    = let i = findfirst(a -> startswith(a, "--tag="), ARGS)
    i === nothing ? "L14" : ARGS[i][7:end]
end
const MAXROWS = let i = findfirst(a -> startswith(a, "--maxrows="), ARGS)
    i === nothing ? nothing : parse(Int, ARGS[i][11:end])
end
const SMOKE = MAXROWS !== nothing
const N_TARGET = let p = findfirst(a -> !startswith(a, "--"), ARGS)
    p === nothing ? 500 : parse(Int, ARGS[p])
end
const SSPS     = ["ssp245", "ssp585"]
const HORIZONS = [2100, 2150, 2300]
const Y0, Y1   = 1850, 2300
const AIS_SLOT = :antarctic_icesheet          # name kept by Mimi replace!
## [INERT] window: the calibration's own span. Nothing may move inside it.
const INERT_WIN = (1850, 2024)
const INERT_TOL = 1e-12                       # cm; this is an identity, so float noise
## [AFFINE] tolerance, scaled to the band the affinity is being used to rebuild
## (`tolerance_scaled_to_spread`), not an absolute cm.
const AFFINE_TOL_FRAC = 1e-6
## ref_excess -- where lambda keeps its stock meaning. It CANCELS out of the anchored
## envelope below (it is absorbed into the lambda rescale), but it is NOT free: left at
## 1.0 degC the n = 2 arm applies g up to 51 and EXHAUSTS the ice sheet, `ais_volume`
## goes negative and stock DAIS's own cone geometry inverts. So it is set to the MEDIAN
## ABOVE-THRESHOLD EXCESS AT A NAMED ANCHOR CELL, which makes g ~ 1 there by
## construction and keeps every arm inside the model's domain. Derived from the draws
## and the (deterministic) GMST path -- no model run needed to compute it.
const ANCHOR_SSP, ANCHOR_H = "ssp585", 2300
const GMAX = Inf                              # uncapped; the realised max g is REPORTED
## DOMAIN GUARD ON THE ARITHMETIC ENVELOPE (added 2026-08-24, after Marcus).
## The envelope rebuilds a rescaled arm as `base + s*(arm - base)`. That identity is
## licensed by [AFFINE] and checked by [ANCHOR-EXACT] -- but only AT THE SCALES THOSE
## GATES RAN AT (s = 1.42 and 1.70). Applied at s = 35 or s = 1240 it is an
## extrapolation of a locally-verified linearity by ~700x, and it knows nothing about
## the component's mass floor or its cone geometry. Unguarded it printed 153210 cm =
## 26.9x THE WHOLE ICE SHEET as if it were a model result. Two guards, both REPORTED:
## the component reports 57.0*(1 - V/V0), so 57 m is total deglaciation and nothing
## above it is a number at all; and any |log(s)| beyond the verified band is marked
## UNVERIFIED rather than silently trusted.
const DEGLACIATION_CM = 5700.0                # 57 m SLE = the component's own ceiling
const SCALE_VERIFIED_MAX = 3.0                # [ANCHOR-EXACT] ran at 1.42 and 1.70
## Preserved T_ant(GMST = 0) anchor of the DAIS temperature map, as ladrillo_projection
## sets it: T_ant = amp * GMST + TANT0.
const TANT0 = LADRILLO_AIS_TANT0
## The arms. `n0` must reproduce the shipped panel; `lam0` isolates the base.
const EXPONENTS = [0.0, 1.0, 2.0]
const ARM_NAME(n) = "n$(replace(string(n), "." => "p"))"

chain_path(sd) = joinpath(REPO, "outputs/mcmc", "chain_$(TAG)_seed$(sd)_n$(NITER).csv")
hdr(sd) = String.(propertynames(CSV.read(chain_path(sd), DataFrame; limit = 0)))
for sd in SEEDS; isfile(chain_path(sd)) || error("missing chain $(chain_path(sd))"); end
const VARIANT = ladrillo_gis_variant(hdr(SEEDS[1]))

function read_draws(sd)
    need = ladrillo_used_cols(VARIANT)
    h = hdr(sd)
    rd = ladrillo_gis_needs_native(h) ?
        vcat(setdiff(need, LADRILLO_GIS_SLOW_NATIVE_COLS),
             LADRILLO_GIS_SLOW_REPARAM_COLS) |> unique : need
    df = SMOKE ? CSV.read(chain_path(sd), DataFrame; select = rd, limit = MAXROWS) :
                 CSV.read(chain_path(sd), DataFrame; select = rd)
    nb = SMOKE ? 0 : NBURN
    step = max(1, (nrow(df) - nb) ÷ N_TARGET)
    idx = collect((nb + 1):step:nrow(df))
    d = ladrillo_native_greenland!(df[idx[1:N_TARGET], :]); df = nothing; GC.gc(); d
end

@printf("AIS fast-dynamics SHAPE propagation | tag %s%s | %d draws/chain x %d chains\n",
        TAG, SMOKE ? "  ** SMOKE (--maxrows=$(MAXROWS)) **" : "", N_TARGET, length(SEEDS))
@printf("  arms: lam0, %s   gmax %s\n", join(ARM_NAME.(EXPONENTS), ", "), string(GMAX))
flush(stdout)
const DRAWS = [(@printf("  reading chain seed%d ...\n", sd); flush(stdout); read_draws(sd))
               for sd in SEEDS]
const NDRAW = sum(nrow.(DRAWS))

"""Above-threshold excess T_ant - T_crit at year `y` under `ssp`, per draw (0 if below)."""
function excess_at(ssp::String, y::Int)
    g = CSV.read(joinpath(LADRILLO_OBS, "fair_mean_gmst_$(ssp).csv"), DataFrame)
    yc, gc = propertynames(g)[1], propertynames(g)[2]
    i = findfirst(==(y), Int.(g[!, yc]))
    i === nothing && error("excess_at: $y absent from fair_mean_gmst_$(ssp).csv")
    gm = Float64(g[i, gc])
    [max(Float64(r["ais_gmst_amp"]) * gm + TANT0 - Float64(r["antarctic_temp_threshold"]), 0.0)
     for d in DRAWS for r in eachrow(d)]
end
const REF_EXCESS = let e = filter(>(0), excess_at(ANCHOR_SSP, ANCHOR_H))
    isempty(e) ? error("no draw tips at the anchor cell") : median(e)
end
@printf("  ref_excess = %.4f degC = median above-threshold excess at %s@%d (%.1f%% tipped)\n",
        REF_EXCESS, ANCHOR_SSP, ANCHOR_H,
        100 * count(>(0), excess_at(ANCHOR_SSP, ANCHOR_H)) / NDRAW)

"""Build a Ladrillo whose AIS slot carries the magnitude-dependent fork.
`replace!` keeps the slot NAME, so `ladrillo_run_draw!` needs no change --
the same property `brick_mengel.jl` relies on for the glacier slot."""
function build_magdep(ssp; n::Float64, ref::Float64 = REF_EXCESS, gmax::Float64 = GMAX)
    bf = ladrillo_setup(ssp = ssp, y0 = Y0, y1 = Y1, gis_variant = VARIANT)
    replace!(bf.m, AIS_SLOT => antarctic_icesheet_magdep)
    update_param!(bf.m, AIS_SLOT, :ais_fastdyn_exponent, n)
    update_param!(bf.m, AIS_SLOT, :ais_fastdyn_ref_excess, ref)
    update_param!(bf.m, AIS_SLOT, :ais_fastdyn_gmax, gmax)
    bf
end

"""Run every draw through `bf`, returning (ais_by_draw::Matrix, years, maxg).

`lambda_map` rewrites `antarctic_lambda` per draw (`nothing` = use the draw's own).
It goes through a ONE-ROW COPY of the frame rather than mutating `DRAWS`, so the
shared posterior sample is never touched and arms cannot contaminate each other."""
function run_arm(bf; lambda_map = nothing)
    yrs = bf.years
    out = Matrix{Float64}(undef, NDRAW, length(yrs))
    maxg, k, nfloor = 0.0, 0, 0
    for d in DRAWS, i in 1:nrow(d)
        k += 1
        if lambda_map === nothing
            ladrillo_run_draw!(bf, d[i, :])
        else
            rr = DataFrame(d[i:i, :])
            rr[1, "antarctic_lambda"] = lambda_map(Float64(d[i, "antarctic_lambda"]))
            ladrillo_run_draw!(bf, rr[1, :])
        end
        out[k, :] = coalesce.(ladrillo_series(bf, :ais), NaN)
        g, fl = ladrillo_ais_factor(bf)
        maxg = max(maxg, g); nfloor += fl
    end
    out, yrs, maxg, nfloor
end

"""(largest magnitude factor g applied, number of years the mass floor bound)."""
function ladrillo_ais_factor(bf)
    v = bf.m[AIS_SLOT, :disintegration_factor]
    f = bf.m[AIS_SLOT, :disintegration_floored]
    m, nf = 0.0, 0
    for i in eachindex(v)
        x = v[i]
        if !(x === missing) && isfinite(x) && x > m; m = x; end
        y = f[i]
        if !(y === missing) && y > 0.5; nf += 1; end
    end
    m, nf
end

yidx(yrs, y) = findfirst(==(y), yrs)

## ---- run every arm for every scenario ------------------------------------
function run_all_arms()
    res  = Dict{Tuple{String,String}, Matrix{Float64}}()   # (ssp, arm) -> draws x years
    maxg = Dict{Tuple{String,String}, Float64}()
    yrs_out = Int[]
    for ssp in SSPS
        for n in EXPONENTS
            arm = ARM_NAME(n)
            @printf("  running %s / %s ...\n", ssp, arm); flush(stdout)
            bf = build_magdep(ssp; n = n)
            A, yrs, mg, nf = run_arm(bf)
            res[(ssp, arm)] = A; maxg[(ssp, arm)] = mg
            nf > 0 && @printf("    [FLOOR] %s %s: the mass floor bound in %d draw-years\n",
                              ssp, arm, nf)
            isempty(yrs_out) && (yrs_out = yrs)
        end
        ## lambda = 0 on the STOCK form: the fast-dynamics-free base. Shape is
        ## irrelevant when the flux is zero, so one lam0 arm serves every n.
        @printf("  running %s / lam0 ...\n", ssp); flush(stdout)
        bf = build_magdep(ssp; n = 0.0)
        A, _, _, _ = run_arm(bf; lambda_map = _ -> 0.0)
        res[(ssp, "lam0")] = A; maxg[(ssp, "lam0")] = 0.0
    end
    res, maxg, yrs_out
end
const RES, MAXG, YRS = run_all_arms()
const res, maxg = RES, MAXG

## ==========================================================================
## GATES
## ==========================================================================
@printf("\n%s\nGATES\n%s\n", repeat("=", 92), repeat("=", 92))

## [FORK] the n = 0 arm must reproduce the SHIPPED projection, not merely itself.
const SHIPPED = CSV.read(joinpath(REPO, "outputs", "ssps_components_2300_$(TAG).csv"),
                         DataFrame)
const SSP_LABEL = Dict("ssp245" => "SSP2-4.5", "ssp585" => "SSP5-8.5")
for ssp in SSPS, H in HORIZONS
    A = res[(ssp, ARM_NAME(0.0))]
    med = median(A[:, yidx(YRS, H)])
    row = SHIPPED[(SHIPPED.year .== H) .& (SHIPPED.ssp .== SSP_LABEL[ssp]) .&
                  (SHIPPED.component .== "ais"), :]
    if nrow(row) == 1
        d = med - row.med[1]
        @printf("  [FORK] %s @%d  n0 median %8.3f vs shipped %8.3f  diff %+8.4f cm -> %s\n",
                ssp, H, med, row.med[1], d, abs(d) < 0.5 ? "PASS" : "CHECK")
    end
end

## [INERT] the historical window must be bit-identical across every arm: the
## change is only licensed if it cannot touch the likelihood.
function inert_gate()
    for ssp in SSPS
        base = RES[(ssp, ARM_NAME(0.0))]
        i0, i1 = yidx(YRS, INERT_WIN[1]), yidx(YRS, INERT_WIN[2])
        worst = 0.0
        for n in EXPONENTS
            A = RES[(ssp, ARM_NAME(n))]
            worst = max(worst, maximum(abs.(A[:, i0:i1] .- base[:, i0:i1])))
        end
        @printf("  [INERT] %s %d-%d  max |arm - n0| = %.3e cm -> %s\n",
                ssp, INERT_WIN[1], INERT_WIN[2], worst, worst < INERT_TOL ? "PASS" : "FAIL")
        @assert worst < INERT_TOL "[INERT] a shaped arm moved the calibration window for $ssp"
    end
end
inert_gate()

## [AFFINE] is AIS affine in lambda? The anchored envelope below is arithmetic on
## (arm - lam0) and is only licensed if it is. Checked by halving lambda on the
## stock form and asking whether base + 0.5*(full - base) reproduces it.
function affine_gate()
    ok = true
    for ssp in SSPS
        bf = build_magdep(ssp; n = 0.0)
        lamhalf, _, _, _ = run_arm(bf; lambda_map = x -> 0.5 * x)
        b = RES[(ssp, "lam0")]; f = RES[(ssp, ARM_NAME(0.0))]
        iH = yidx(YRS, 2300)
        pred = b[:, iH] .+ 0.5 .* (f[:, iH] .- b[:, iH])
        err = maximum(abs.(pred .- lamhalf[:, iH]))
        band = quantile(f[:, iH], 0.95) - quantile(f[:, iH], 0.05)
        rel = err / band
        @printf("  [AFFINE] %s @2300  max |pred - actual| = %.4f cm = %.2e of the %.1f cm band -> %s\n",
                ssp, err, rel, band, rel < AFFINE_TOL_FRAC ? "PASS (exact)" : "APPROXIMATE")
        ok = ok && (rel < AFFINE_TOL_FRAC)
    end
    ok
end
const AFFINE_OK = affine_gate()

## [GMAX] report the realised magnitude factor -- capping must never be silent.
for ssp in SSPS, n in EXPONENTS
    n == 0.0 && continue
    @printf("  [GMAX] %s %s  max realised g = %.2f (cap %s)\n",
            ssp, ARM_NAME(n), maxg[(ssp, ARM_NAME(n))], string(GMAX))
end

## ==========================================================================
## THE CELLS
## ==========================================================================
cells = DataFrame(ssp = String[], horizon = Int[], arm = String[], n_draws = Int[],
                  med_cm = Float64[], p05_cm = Float64[], p95_cm = Float64[],
                  spread_cm = Float64[], fastdyn_med_cm = Float64[],
                  fastdyn_frac_of_med = Float64[], fastdyn_frac_of_spread = Float64[])
@printf("\n%s\nCELLS -- ref_excess = %.4f degC (anchored on %s@%d); levels are anchor-dependent\n%s\n",
        repeat("=", 92), REF_EXCESS, ANCHOR_SSP, ANCHOR_H, repeat("=", 92))
@printf("  %-7s %-6s %-6s %9s %9s %9s %9s | %11s %9s\n",
        "ssp", "horiz", "arm", "median", "p05", "p95", "spread", "fastdyn cm", "% of med")
for ssp in SSPS, H in HORIZONS
    iH = yidx(YRS, H)
    b = res[(ssp, "lam0")][:, iH]
    for arm in vcat("lam0", ARM_NAME.(EXPONENTS))
        v = res[(ssp, arm)][:, iH]
        fd = median(v .- b)
        sp = quantile(v, 0.95) - quantile(v, 0.05)
        spb = quantile(v .- b, 0.95) - quantile(v .- b, 0.05)
        push!(cells, (ssp, H, arm, length(v), median(v), quantile(v, 0.05),
                      quantile(v, 0.95), sp, fd,
                      fd / median(v), sp == 0 ? NaN : spb / sp))
        @printf("  %-7s %-6d %-6s %9.2f %9.2f %9.2f %9.2f | %11.2f %8.1f%%\n",
                ssp, H, arm, median(v), quantile(v, 0.05), quantile(v, 0.95), sp, fd,
                100 * fd / median(v))
    end
end
CSV.write(joinpath(REPO, "outputs", "scope_ais_fastdyn_cells_$(TAG)$(SMOKE ? "_SMOKE" : "").csv"), cells)

## ==========================================================================
## THE ANCHOR ENVELOPE -- arithmetic, licensed by [AFFINE]
## For anchor cell (s*, H*), rescale lambda by the factor that restores the SHIPPED
## n0 median there, then report every cell under that rescale.
## ==========================================================================
env = DataFrame(arm = String[], anchor_ssp = String[], anchor_horizon = Int[],
                lambda_rescale = Float64[], ssp = String[], horizon = Int[],
                med_cm = Float64[], spread_cm = Float64[], vs_n0_med = Float64[],
                domain = String[])
@printf("\n%s\nANCHOR ENVELOPE -- each cell used in turn as the anchor\n%s\n",
        repeat("=", 92), repeat("=", 92))
for n in EXPONENTS
    n == 0.0 && continue
    arm = ARM_NAME(n)
    @printf("\n  arm %s\n  %-18s %8s | %s\n", arm, "anchored at", "lam scale",
            join([@sprintf("%7s@%d", s == "ssp245" ? "245" : "585", H)
                  for s in SSPS for H in HORIZONS], " "))
    for as in SSPS, aH in HORIZONS
        iA = yidx(YRS, aH)
        bA = res[(as, "lam0")][:, iA]
        tgt = median(res[(as, ARM_NAME(0.0))][:, iA]) - median(bA)
        cur = median(res[(as, arm)][:, iA] .- bA)
        ## An anchor cell with NO fast-dynamics contribution cannot define a rescale
        ## (0/0). ssp245@2100 is such a cell -- only 28.9% of draws have tipped by then
        ## and the median draw contributes nothing. Skipped and SAID, not silently NaN'd.
        if !(isfinite(cur)) || abs(cur) < 1e-9
            @printf("  %-18s %8s | (no fast-dynamics contribution at this cell -- cannot anchor here)\n",
                    "$(as)@$(aH)", "--")
            continue
        end
        s = tgt / cur
        line = String[]
        for ssp in SSPS, H in HORIZONS
            iH = yidx(YRS, H)
            b = res[(ssp, "lam0")][:, iH]
            v = b .+ s .* (res[(ssp, arm)][:, iH] .- b)
            m0 = median(res[(ssp, ARM_NAME(0.0))][:, iH])
            md = median(v)
            dom = md > DEGLACIATION_CM ? "IMPOSSIBLE" :
                  (s > SCALE_VERIFIED_MAX ? "UNVERIFIED" : "ok")
            push!(env, (arm, as, aH, s, ssp, H, md,
                        quantile(v, 0.95) - quantile(v, 0.05), md - m0, dom))
            push!(line, dom == "IMPOSSIBLE" ? @sprintf("%11s", ">57m") :
                        dom == "UNVERIFIED" ? @sprintf("%10.1f?", md) :
                        @sprintf("%11.1f", md))
        end
        @printf("  %-18s %8.4f | %s\n", "$(as)@$(aH)", s, join(line, " "))
    end
end
CSV.write(joinpath(REPO, "outputs", "scope_ais_fastdyn_envelope_$(TAG)$(SMOKE ? "_SMOKE" : "").csv"), env)
@printf("\n  KEY: `>57m` = above TOTAL DEGLACIATION (%.0f cm) -- the arithmetic left the model's\n",
        DEGLACIATION_CM)
@printf("       domain entirely and the cell is not a number. `?` = lambda rescale above %.1f,\n",
        SCALE_VERIFIED_MAX)
@printf("       outside the range [ANCHOR-EXACT] verified; re-run before quoting.\n")
@printf("  %d of %d envelope cells are IMPOSSIBLE, %d UNVERIFIED.\n",
        count(==("IMPOSSIBLE"), env.domain), nrow(env), count(==("UNVERIFIED"), env.domain))

## ==========================================================================
## [ANCHOR-EXACT] the arithmetic envelope above rides on [AFFINE], which came back
## APPROXIMATE, not exact. So the HEADLINE anchor -- ANCHOR_SSP@ANCHOR_H, the cell
## the reference excess is set from -- is additionally RE-RUN at the rescaled lambda
## and the two are compared. `offline_emulator`: emulate offline, then verify the
## cell you are going to quote.
## ==========================================================================
@printf("\n%s\n[ANCHOR-EXACT] arithmetic envelope vs an actual re-run at the rescaled lambda\n%s\n",
        repeat("=", 92), repeat("=", 92))
function anchor_exact()
    iA = yidx(YRS, ANCHOR_H)
    for n in EXPONENTS
        n == 0.0 && continue
        arm = ARM_NAME(n)
        bA = RES[(ANCHOR_SSP, "lam0")][:, iA]
        tgt = median(RES[(ANCHOR_SSP, ARM_NAME(0.0))][:, iA]) - median(bA)
        cur = median(RES[(ANCHOR_SSP, arm)][:, iA] .- bA)
        sc = tgt / cur
        bf = build_magdep(ANCHOR_SSP; n = n)
        A, _, mg, nf = run_arm(bf; lambda_map = x -> sc * x)
        for H in HORIZONS
            iH = yidx(YRS, H)
            b = RES[(ANCHOR_SSP, "lam0")][:, iH]
            approx = b .+ sc .* (RES[(ANCHOR_SSP, arm)][:, iH] .- b)
            d = median(A[:, iH]) - median(approx)
            band = quantile(A[:, iH], 0.95) - quantile(A[:, iH], 0.05)
            @printf("  %s %s @%d  exact %8.2f  arithmetic %8.2f  diff %+7.3f cm = %.2e of band\n",
                    ANCHOR_SSP, arm, H, median(A[:, iH]), median(approx), d, abs(d) / band)
        end
        @printf("     lambda rescale %.4f, max g %.2f, floor bound in %d draw-years\n",
                sc, mg, nf)
    end
end
anchor_exact()

## ==========================================================================
## THE ANCHOR-FREE NUMBER -- the ssp585/ssp245 separation of the fast-dynamics
## part. A lambda rescale multiplies numerator and denominator alike.
## ==========================================================================
@printf("\n%s\nANCHOR-FREE: ssp585/ssp245 ratio of the FAST-DYNAMICS contribution\n%s\n",
        repeat("=", 92), repeat("=", 92))
@printf("  %-6s %-6s %14s %14s %10s\n", "horiz", "arm", "ssp245 fd cm", "ssp585 fd cm", "ratio")
for H in HORIZONS, arm in ARM_NAME.(EXPONENTS)
    iH = yidx(YRS, H)
    f245 = median(res[("ssp245", arm)][:, iH] .- res[("ssp245", "lam0")][:, iH])
    f585 = median(res[("ssp585", arm)][:, iH] .- res[("ssp585", "lam0")][:, iH])
    @printf("  %-6d %-6s %14.3f %14.3f %10.2f\n", H, arm, f245, f585,
            f245 == 0 ? NaN : f585 / f245)
end
@printf("\ndone.\n")
