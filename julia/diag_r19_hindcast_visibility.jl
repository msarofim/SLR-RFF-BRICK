## ============================================================================
## diag_r19_hindcast_visibility.jl — could ANY sea-level observation have
## constrained R19's temperature offset?
##
## The D1 chains moved `gic_T_off_R19` from -1.9095 to -0.3236 when the total
## stream was dropped, and the shift moves the 2300 glacier projection by
## 1.4-1.7 cm (diag_r19_deliverable_leverage.jl) — so it matters downstream. The
## design question for a replacement term is whether it CAN be replaced: what
## does that same shift do over the OBSERVED record, and is that above or below
## the noise floor of the observations we have?
##
## Reference points:
##   R19 observed cumulative melt to 2020      0.0584 cm
##   R19 GlaMBIE 2000-2024 cumulative          0.1182 cm  (rate 0.0493 +/- 0.0361
##                                             mm/yr as coded => 1.37 sigma; 0.28
##                                             sigma under the serial-correlation
##                                             assumption the GlaMBIE restructure
##                                             argued for)
##   total-stream sigma on a window mean       0.232-0.565 cm (spec section 2)
##
## If the hindcast signature of the shift is well below those, then no sea-level
## observation identifies R19's offset, the D1 "shift" is a weakly-identified
## parameter relaxing rather than information being lost, and a replacement term
## has to come from OUTSIDE the sea-level record.
##
##   julia --project=julia_v2 julia/diag_r19_hindcast_visibility.jl [n_draws]
## Writes outputs/diag_r19_hindcast_visibility.csv
## ============================================================================

using CSV, DataFrames, Mimi, Printf, Statistics
include(joinpath(@__DIR__, "ladrillo_projection.jl"))

const OUT   = joinpath(LADRILLO_REPO, "outputs/diag_r19_hindcast_visibility.csv")
const NDRAW = length(ARGS) >= 1 ? parse(Int, ARGS[1]) : 200
const Y0, Y1 = 1850, 2026
const HIND  = (1900, 2024)
const TOFF  = ("L10" => -1.909550, "D1" => -0.323618)
const COMPONENTS = [:glaciers, :total]

post = ladrillo_posterior(nthin=NDRAW)
bf = ladrillo_setup(ssp="ssp245", y0=Y0, y1=Y1,
                    gis_ab = ladrillo_posterior_variant() === :ab)
hi = [i for (i, y) in enumerate(bf.years) if HIND[1] <= y <= HIND[2]]
@printf("R19 hindcast visibility | %d draws | %d-%d\n", nrow(post), HIND...)

series = Dict(nm => Dict(c => zeros(length(hi), nrow(post)) for c in COMPONENTS)
              for (nm, _) in [TOFF...])
for (nm, v) in [TOFF...]
    p = copy(post); p[!, "gic_T_off_R19"] .= v
    for (j, r) in enumerate(eachrow(p))
        ladrillo_run_draw!(bf, r)
        for c in COMPONENTS
            series[nm][c][:, j] = ladrillo_series(bf, c)[hi]
        end
    end
end

rows = DataFrame(component=String[], stat=String[], value_cm=Float64[])
println("\n  Hindcast signature of moving gic_T_off_R19 from L10 to the D1 median")
@printf("  %-10s %14s %14s %14s\n", "component", "mean |diff|", "max |diff|", "diff at 2024")
for c in COMPONENTS
    d = vec(median(series["D1"][c] .- series["L10"][c], dims=2))
    push!(rows, (component=String(c), stat="mean_abs", value_cm=mean(abs.(d))))
    push!(rows, (component=String(c), stat="max_abs",  value_cm=maximum(abs.(d))))
    push!(rows, (component=String(c), stat="at_2024",  value_cm=d[end]))
    @printf("  %-10s %14.4f %14.4f %14.4f\n", String(c), mean(abs.(d)),
            maximum(abs.(d)), d[end])
end

const TOTAL_SIGMA_LO = 0.232      # spec section 2, window-mean offset
dtot = vec(median(series["D1"][:total] .- series["L10"][:total], dims=2))
mx = maximum(abs.(dtot))
@printf("\n  Largest total-stream signature %.4f cm vs a total sigma of %.3f-0.565 cm; ratio %.2f\n",
        mx, TOTAL_SIGMA_LO, mx / TOTAL_SIGMA_LO)
if mx < TOTAL_SIGMA_LO
    println("  => BELOW the total's noise floor: no sea-level observation identifies R19.")
else
    println("  => ABOVE the floor: the total genuinely measured this. Replacement is possible.")
end

## WHERE in time the information sits — this is what decides which replacement
## term can work. A modern-rate constraint can only see the recent end.
println("\n  Where the signature sits in time (total, cm):")
@printf("  %6s %12s\n", "year", "D1 - L10")
for y in (1920, 1950, 1980, 2000, 2010, 2024)
    i = findfirst(==(y), bf.years[hi])
    i === nothing && continue
    @printf("  %6d %12.4f\n", y, dtot[i])
    push!(rows, (component="total", stat="diff_$y", value_cm=dtot[i]))
end
mod_i = [i for (i, y) in enumerate(bf.years[hi]) if 2000 <= y <= 2024]
@printf("\n  mean |diff| over 1900-1999 : %.4f cm\n",
        mean(abs.(dtot[1:findfirst(==(2000), bf.years[hi]) - 1])))
@printf("  mean |diff| over 2000-2024 : %.4f cm   <- all a modern-rate term can see\n",
        mean(abs.(dtot[mod_i])))
CSV.write(OUT, rows)
println("\nwrote $(relpath(OUT, LADRILLO_REPO))")
