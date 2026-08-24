## ============================================================================
## diag_curvature_deficit_2x2.jl — IS THE SHARED CURVATURE DEFICIT THE DRIVER,
##                                 THE LIKELIHOOD FORM, OR THE RESPONSE?
##
## THE FINDING UNDER TEST. Greenland under-runs observed 1993-2024 acceleration
## 0.65x (`gis_obs_accel_deficit`) and Antarctica 0.727x
## (`ais_curvature_deficit_shared`) -- same estimator, same window, two
## independent ice sheets, both matching LEVEL and RATE. Three candidate causes
## were on the table: (a) our DRIVER's own curvature is too low, (b) the
## AR(1)-on-LEVELS likelihood constrains levels and rates but not second
## derivatives, (c) the RESPONSE lacks the lagged/committed acceleration a real
## ice sheet carries.
##
## THE 2x2 THAT SEPARATES THEM. The components do NOT share a hindcast driver --
## `ladrillo_setup` splices OBSERVED regional T into Greenland (`gis_obs`) and
## the glacier blocks (`obs_driver`), while AIS and steric are driven by
## FaIR-mean GMST/OHC (`fair_mean_{gmst,ohc}_<ssp>.csv`). All four are FITTED
## likelihood streams (`calibrate_mcmc_ext.jl:1242`). So:
##
##            | OBSERVED-driven | FaIR-driven
##   ---------|-----------------|-------------
##   ice/glac |   gis, gsic     |   ais
##   ocean    |       --        |   steric
##
##   * deficit in the FaIR-driven pair ONLY      => (a) the driver
##   * deficit in ALL FOUR                       => (b) the likelihood form
##   * deficit in the ICE rows but NOT steric    => (c) response memory
##
## ALREADY ESTABLISHED BEFORE THIS RUN, from the drivers alone (no model needed):
##   * (a) IS REFUTED FOR GREENLAND. Its hindcast driver IS the observed record,
##     and it still under-runs. A driver cannot be blamed for a deficit measured
##     against the very observations that ARE the driver.
##   * Our FaIR GMST driver has NEGATIVE 1993-2024 curvature (-3.271e-4 degC/yr^2)
##     where observed GMST is POSITIVE (+2.445e-4) -- ratio -1.338. So (a) is
##     still live for AIS and steric, and it is a SIGN error, not a magnitude one.
##   * The observed REGIONAL drivers are also strongly negative in curvature
##     (south Greenland -1.014e-2). So Greenland's ice ACCELERATES while its own
##     observed driver DECELERATES -- which is exactly the signature (c) predicts
##     and which no driver correction can produce.
##
##   julia --project=julia_v2 julia/diag_curvature_deficit_2x2.jl [n_per_chain] [--tag=L14] [--maxrows=N]
## Writes outputs/diag_curvature_deficit_2x2_<tag>.csv
## ============================================================================
using CSV, DataFrames, Statistics, Printf

include(joinpath(@__DIR__, "ladrillo_projection.jl"))

const REPO  = LADRILLO_REPO
const SEEDS = [2026, 2027, 2028, 2029]
const NITER = 2000000
const NBURN = 1000000
const TAG = let i = findfirst(a -> startswith(a, "--tag="), ARGS)
    i === nothing ? "L14" : ARGS[i][7:end]
end
const MAXROWS = let i = findfirst(a -> startswith(a, "--maxrows="), ARGS)
    i === nothing ? nothing : parse(Int, ARGS[i][11:end])
end
const SMOKE = MAXROWS !== nothing
const N_TARGET = let p = findfirst(a -> !startswith(a, "--"), ARGS)
    p === nothing ? 500 : parse(Int, ARGS[p])
end
const SSP = "ssp245"          # hindcast only; the scenario is irrelevant before 2025
const Y0, Y1 = 1850, 2300
const ACCEL_WIN = (1993, 2024)
const RATE_WIN  = (1995, 2024)
## component -> (ladrillo series, target column, hindcast driver)
const PANEL = [(:ais,    "ais",    "FaIR-mean GMST"),
               (:gis,    "gis",    "OBSERVED regional T (spliced)"),
               (:gsic_hind, "gsic", "OBSERVED block T (spliced)"),
               (:te,     "steric", "FaIR-mean OHC"),
               (:total,  "dang",   "mixed")]
const TARGETS_CSV = joinpath(REPO, "outputs/recalib_targets_ext.csv")
const OUT = joinpath(REPO, "outputs",
                     "diag_curvature_deficit_2x2_$(TAG)$(SMOKE ? "_SMOKE" : "").csv")
## ADDED 2026-08-24 (open item 1 of handoff -24g): the panel below collapses 2000 draws
## to a MEDIAN before measuring, so the posterior spread of our own acceleration -- the
## bar the 0.65x / 0.727x / 0.571x deficits have never carried -- is discarded. This
## second output keeps the per-draw rate and accel on the SAME per-series window, so the
## deficit can be scored against the ensemble's own width. `OUT` is unchanged and the
## [IDENT] gate below asserts the shipped numbers still reproduce bit-for-bit.
const OUT_PERDRAW = joinpath(REPO, "outputs",
                     "diag_curvature_deficit_perdraw_$(TAG)$(SMOKE ? "_SMOKE" : "").csv")

chain_path(sd) = joinpath(REPO, "outputs/mcmc", "chain_$(TAG)_seed$(sd)_n$(NITER).csv")
hdr(sd) = String.(propertynames(CSV.read(chain_path(sd), DataFrame; limit = 0)))
for sd in SEEDS; isfile(chain_path(sd)) || error("missing chain $(chain_path(sd))"); end
const VARIANT = ladrillo_gis_variant(hdr(SEEDS[1]))

rate_of(v, yrs, w) = let i0 = findfirst(==(w[1]), yrs), i1 = findfirst(==(w[2]), yrs)
    (i0 === nothing || i1 === nothing) ? NaN : (v[i1] - v[i0]) / (w[2] - w[1])
end
"""Quadratic-fit acceleration of a cumulative series (cm/yr^2)."""
function accel_of(v, yrs, w)
    i0 = findfirst(==(w[1]), yrs); i1 = findfirst(==(w[2]), yrs)
    (i0 === nothing || i1 === nothing) && return NaN
    x = Float64.(yrs[i0:i1] .- yrs[i0]); y = Float64.(v[i0:i1])
    any(isnan, y) && return NaN
    2 * (hcat(ones(length(x)), x, x .^ 2) \ y)[3]
end

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

@printf("Curvature-deficit 2x2 | tag %s%s | %d draws/chain x %d\n",
        TAG, SMOKE ? "  ** SMOKE **" : "", N_TARGET, length(SEEDS))
flush(stdout)
const DRAWS = [(@printf("  reading chain seed%d ...\n", sd); flush(stdout); read_draws(sd))
               for sd in SEEDS]
## draw index -> originating chain, in the SAME order the `for d in DRAWS, r in eachrow(d)`
## loop below fills `acc`. Measured from the frames, never assumed to be N_TARGET each.
const DRAW_SEED = vcat([fill(sd, nrow(d)) for (sd, d) in zip(SEEDS, DRAWS)]...)

bf = ladrillo_setup(ssp = SSP, y0 = Y0, y1 = Y1, gis_variant = VARIANT)
yrs = bf.years
acc = Dict(c => Vector{Vector{Float64}}() for (c, _, _) in PANEL)
for d in DRAWS, r in eachrow(d)
    ladrillo_run_draw!(bf, r)
    for (c, _, _) in PANEL
        push!(acc[c], coalesce.(ladrillo_series(bf, c), NaN))
    end
end
@printf("  %d draws run\n", length(acc[PANEL[1][1]]))

const TGT = CSV.read(TARGETS_CSV, DataFrame)
## snapshot of the shipped panel, read before CSV.write overwrites it, for [IDENT].
const REF = isfile(OUT) ? CSV.read(OUT, DataFrame) : nothing
perdraw = DataFrame(component = String[], draw = Int[], chain_seed = Int[],
                    rate = Float64[], accel = Float64[])
out = DataFrame(component = String[], driver = String[], fitted = Bool[],
                ours_rate = Float64[], obs_rate = Float64[], rate_ratio = Float64[],
                ours_accel = Float64[], obs_accel = Float64[], accel_ratio = Float64[],
                accel_window = String[])

@printf("\n%s\nCURVATURE DEFICIT BY COMPONENT — the 2x2\n%s\n", repeat("=", 96), repeat("=", 96))
@printf("%-10s %-30s %-9s %9s %9s %7s | %11s %11s %7s\n",
        "component", "hindcast driver", "window", "our rate", "obs rate", "ratio",
        "our accel", "obs accel", "ratio")
for (c, col, drv) in PANEL
    series = acc[c]
    med = [median(getindex.(series, i)) for i in eachindex(yrs)]
    sub = dropmissing(TGT[:, [:year, Symbol(col)]])
    oy = Int.(sub.year); ov = Float64.(sub[!, Symbol(col)])
    ## PER-SERIES windows, clipped to this target's own last valid year -- the same
    ## per-series-valid-window convention the calibrator uses (`calibrate_mcmc_ext.jl`
    ## header item 3). gsic ends at 2023, so a hardcoded 2024 endpoint silently NaNs it.
    ## The realised window is PRINTED and stored, never assumed (labels-from-constants).
    ylast = min(maximum(oy), maximum(yrs))
    aw = (ACCEL_WIN[1], min(ACCEL_WIN[2], ylast))
    rw = (RATE_WIN[1],  min(RATE_WIN[2],  ylast))
    i0 = findfirst(==(oy[1]), yrs)
    mr = med .- med[i0]; ovr = ov .- ov[1]
    om, oa = rate_of(ovr, oy, rw), accel_of(ovr, oy, aw)
    mm, ma = rate_of(mr, yrs, rw), accel_of(mr, yrs, aw)
    ## per-draw, on the SAME window `aw`/`rw` this component just resolved. Both
    ## statistics are shift-invariant (a rate is a difference, an accel is the
    ## quadratic term), so the `- s[i0]` baselining the median gets is irrelevant
    ## here and is omitted rather than reproduced -- verified by [SHIFT] below.
    for (k, sv) in enumerate(series)
        push!(perdraw, (String(c), k, DRAW_SEED[k],
                        rate_of(sv, yrs, rw), accel_of(sv, yrs, aw)))
    end
    @printf("%-10s %-30s %-9s %9.4f %9.4f %7.3f | %11.6f %11.6f %7.3f\n",
            String(c), drv, "$(aw[1])-$(aw[2])", mm, om, mm / om, ma, oa, ma / oa)
    push!(out, (String(c), drv, true, mm, om, mm / om, ma, oa, ma / oa,
                "$(aw[1])-$(aw[2])"))
end
CSV.write(OUT, out)
@printf("\nwrote %s\n", relpath(OUT, REPO))
CSV.write(OUT_PERDRAW, perdraw)
@printf("wrote %s  (%d rows = %d components x %d draws)\n",
        relpath(OUT_PERDRAW, REPO), nrow(perdraw), length(PANEL), length(DRAW_SEED))

## ---- [IDENT] the shipped panel must be unchanged by this addition ---------
## REF was read BEFORE CSV.write overwrote OUT (see the const near the top).
function ident_gate(out, ref)
    ref === nothing && (@printf("  [IDENT] no prior panel on disk -- nothing to compare\n"); return)
    worst, worstc = 0.0, ""
    for r in eachrow(out)
        m = findfirst(==(r.component), ref.component)
        m === nothing && error("[IDENT] component $(r.component) absent from the prior panel")
        for f in (:ours_rate, :obs_rate, :ours_accel, :obs_accel)
            d = abs(r[f] - ref[m, f])
            if d > worst; worst = d; worstc = "$(r.component).$(f)"; end
        end
        r.accel_window == ref[m, :accel_window] ||
            error("[IDENT] window moved for $(r.component)")
    end
    @printf("  [IDENT] max |new - shipped| = %.3e (%s) -> %s\n", worst, worstc,
            worst < 1e-12 ? "PASS" : "FAIL")
    ## a SMOKE reference was written at whatever --maxrows was in force at the time,
    ## so it is reported but not asserted; only the full run gates.
    SMOKE || @assert worst < 1e-12 "[IDENT] the panel moved; the per-draw addition was not additive"
end
ident_gate(out, REF)

## ---- [SHIFT] the two statistics are shift-invariant, as claimed above ----
let v = acc[PANEL[1][1]][1], w = (1993, 2020)
    d1 = accel_of(v, yrs, w) - accel_of(v .+ 7.3, yrs, w)
    d2 = rate_of(v, yrs, RATE_WIN) - rate_of(v .+ 7.3, yrs, RATE_WIN)
    @printf("  [SHIFT] accel %.3e / rate %.3e under a +7.3 cm offset -> %s\n",
            abs(d1), abs(d2), (abs(d1) < 1e-12 && abs(d2) < 1e-12) ? "PASS" : "FAIL")
    @assert abs(d1) < 1e-12 && abs(d2) < 1e-12
end

## ---- the verdict ---------------------------------------------------------
obsdrv = out[occursin.("OBSERVED", out.driver), :]
fairdrv = out[occursin.("FaIR", out.driver), :]
ice = out[in.(out.component, Ref(["ais", "gis", "gsic_hind"])), :]
ster = out[out.component .== "te", :]
@printf("\n%s\nVERDICT\n%s\n", repeat("=", 96), repeat("=", 96))
@printf("  OBSERVED-driven mean accel ratio : %.3f  (%s)\n",
        mean(skipmissing(obsdrv.accel_ratio)), join(obsdrv.component, ", "))
@printf("  FaIR-driven     mean accel ratio : %.3f  (%s)\n",
        mean(skipmissing(fairdrv.accel_ratio)), join(fairdrv.component, ", "))
@printf("  ICE components  mean accel ratio : %.3f\n", mean(skipmissing(ice.accel_ratio)))
@printf("  STERIC          accel ratio      : %.3f\n", ster.accel_ratio[1])
@printf("\n  (a) DRIVER  -> expects a deficit in the FaIR-driven pair ONLY\n")
@printf("  (b) LIKELIHOOD FORM -> expects it in ALL FOUR\n")
@printf("  (c) RESPONSE MEMORY -> expects it in the ICE rows but NOT steric\n")
