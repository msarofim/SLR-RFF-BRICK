## ============================================================================
## diag_r19_deliverable_leverage.jl — does the R19 posterior shift that D1 causes
## actually MOVE the deliverable, or is it a reporting caveat?
##
## WHY, BEFORE DESIGNING A REPLACEMENT TERM. The D1 short chains showed
## `gic_T_off_R19` moving −1.9095 → −0.3236 (+2.05 L10 sd, mixing-gated 5.5×)
## when the total stream is dropped, and I called that "D1 needs an R19
## replacement term before production". That conclusion was drawn from a MARGINAL,
## and this repo has a standing precedent against exactly that: `ais_iceflow0`
## fails its marginal R̂ at 2.359 and is nevertheless a REPORTING CAVEAT, because
## thread 3 measured it explaining R² < 0.001 of the projection. The acceptance
## criterion here is the DELIVERABLE, not the marginal.
##
## R19 is small by construction. Its inventory is a0 = 0.069 m SLE (against 0.146
## SLOWP / 0.140 FAST), its observed cumulative melt to 2020 is 0.058 cm, and its
## GlaMBIE modern rate is 0.049 ± 0.036 mm/yr — a σ 73% of the signal, the noisiest
## block in every product. So a 2σ wander in its temperature offset may be
## immaterial downstream, in which case a replacement term is unnecessary work and
## the honest answer is a caveat.
##
## METHOD. Take the L10 posterior and overwrite the R19 block with the D1 medians
## — first `gic_T_off_R19` alone (the only R19 parameter that moved), then all
## five together — and re-read the glacier and total projections. Everything else
## stays at its L10 draw, so what is measured is the R19 shift and nothing else.
## This needs no D1 chain (they were cleared; regenerable in ~17 min from
## `--drop-total`), only its recorded medians.
##
##   julia --project=julia_v2 julia/diag_r19_deliverable_leverage.jl [n_draws]
## Writes outputs/diag_r19_deliverable_leverage.csv
## ============================================================================

using CSV, DataFrames, Mimi, Printf, Statistics
include(joinpath(@__DIR__, "ladrillo_projection.jl"))

const OUT    = joinpath(LADRILLO_REPO, "outputs/diag_r19_deliverable_leverage.csv")
const Y0, Y1 = 1850, 2300
const NDRAW  = length(ARGS) >= 1 ? parse(Int, ARGS[1]) : 400
const HORIZONS = (2100, 2300)
const SSPS   = [("ssp126", "SSP1-2.6"), ("ssp245", "SSP2-4.5"), ("ssp585", "SSP5-8.5")]
const COMPONENTS = [:glaciers, :total]

## D1 posterior medians for the R19 block (outputs/diag_d1_vs_l10.csv). Only
## gic_T_off_R19 moved by more than 0.19 L10 sd; the rest are carried so the
## "whole block" arm is honest rather than a single-parameter caricature.
const D1_R19 = Dict("gic_T_off_R19"       => -0.323618,
                    "gic_a_R19"           =>  0.068191,
                    "gic_b_R19"           =>  1.062368,
                    "gic_log10_kappa_R19" => -2.780131,
                    "gic_amp_R19"         =>  0.723435)
## The threshold below which a shift is a reporting caveat rather than a blocker.
## 0.1 cm is well inside the 2100 posterior band on every component and scenario.
const MATERIAL_CM = 0.10

post0 = ladrillo_posterior(nthin=NDRAW)
@printf("R19 deliverable leverage | %s | %d draws\n",
        basename(LADRILLO_POSTERIOR_CSV), nrow(post0))
for k in keys(D1_R19)
    k in names(post0) || error("posterior has no column $k")
end

const ARMS = [("BASE_L10",        String[]),
              ("D1_Toff_only",    ["gic_T_off_R19"]),
              ("D1_whole_R19",    collect(keys(D1_R19)))]

function run_arm(post, ssp)
    bf = ladrillo_setup(ssp=ssp, y0=Y0, y1=Y1,
                        gis_variant = ladrillo_posterior_variant())
    iy = Dict(y => findfirst(==(y), bf.years) for y in HORIZONS)
    acc = Dict(c => Dict(y => Float64[] for y in HORIZONS) for c in COMPONENTS)
    for r in eachrow(post)
        ladrillo_run_draw!(bf, r)
        for c in COMPONENTS
            s = ladrillo_series(bf, c)
            for y in HORIZONS
                push!(acc[c][y], s[iy[y]])
            end
        end
    end
    return Dict(c => Dict(y => median(filter(isfinite, acc[c][y])) for y in HORIZONS)
                for c in COMPONENTS)
end

rows = DataFrame(arm=String[], ssp=String[], component=String[], year=Int[],
                 med_cm=Float64[], delta_vs_base_cm=Float64[])
base = Dict{String,Any}()
t0 = time()
for (arm, cols) in ARMS
    p = copy(post0)
    for c in cols
        p[!, c] .= D1_R19[c]
    end
    for (ssp, label) in SSPS
        res = run_arm(p, ssp)
        for c in COMPONENTS, y in HORIZONS
            v = res[c][y]
            key = "$label|$c|$y"
            arm == "BASE_L10" && (base[key] = v)
            push!(rows, (arm=arm, ssp=label, component=String(c), year=y,
                         med_cm=v, delta_vs_base_cm=v - base[key]))
        end
    end
    @printf("  %-14s done (%.0f s)\n", arm, time() - t0)
end

CSV.write(OUT, rows)
println("\n  Median projection shift from moving R19 to its D1 posterior, cm")
@printf("  %-10s %-10s %5s %12s %12s\n", "scenario", "component", "year",
        "Toff only", "whole R19")
for (ssp, label) in SSPS, c in COMPONENTS, y in HORIZONS
    d1 = only(rows[(rows.arm .== "D1_Toff_only") .& (rows.ssp .== label) .&
                   (rows.component .== String(c)) .& (rows.year .== y), :delta_vs_base_cm])
    d2 = only(rows[(rows.arm .== "D1_whole_R19") .& (rows.ssp .== label) .&
                   (rows.component .== String(c)) .& (rows.year .== y), :delta_vs_base_cm])
    @printf("  %-10s %-10s %5d %12.4f %12.4f\n", label, String(c), y, d1, d2)
end

worst = maximum(abs.(rows.delta_vs_base_cm))
@printf("\n  Largest |shift| anywhere: %.4f cm  (threshold %.2f cm)\n", worst, MATERIAL_CM)
println(worst < MATERIAL_CM ?
    "  VERDICT: IMMATERIAL. The R19 marginal moves but the deliverable does not.\n" *
    "  D1 does NOT need a replacement term to protect the projection — the same\n" *
    "  reading as ais_iceflow0 (marginal R-hat 2.359, R^2 < 0.001 of the projection).\n" *
    "  A replacement term would be for INFERENTIAL honesty about R19 itself, not\n" *
    "  for the deliverable, and should be argued on that basis or not at all." :
    "  VERDICT: MATERIAL. The R19 shift moves the deliverable, so D1 needs a\n" *
    "  replacement term before production, as the D1 write-up claimed.")
@printf("\nwrote %s  (%.0f s)\n", relpath(OUT, LADRILLO_REPO), time() - t0)
