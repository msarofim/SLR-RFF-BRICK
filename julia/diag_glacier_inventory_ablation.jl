## diag_glacier_inventory_ablation.jl -- how much of the BRICK 2.0 -> Ladrillo glacier difference is the inventory?
##
##   julia --project=<Ladrillo.jl checkout> julia/diag_glacier_inventory_ablation.jl
##
## Writes outputs/diag_glacier_inventory_ablation_L27_draws.csv (per draw, scenario, horizon) and
## outputs/diag_glacier_inventory_ablation_L27.csv (summary). Marcus 2026-11-05: "Run the glacier ablation with
## Ladrillo's inventory in BRICK."
##
## THE ABLATION. BRICK 2.0 (stock MimiBRICK v2.0.0, Wigley-Raper glaciers) is given Ladrillo's glacier inventory and
## nothing else: each BRICK 2.0 draw k gets the remaining ice at INV_YEAR of Ladrillo draw k (its partner in the joint
## arm: same FaIR configuration), and its initial volume gsic_v0 is solved so that BRICK's own remaining ice at INV_YEAR
## equals it. BRICK's other glacier parameters (beta0, n, s0, Teq) are left as calibrated. The three arms then run the
## paper's joint arm on all seven van Vuuren scenarios:
##   B   = BRICK 2.0 as published (must reproduce the canonical draws: [IDENTITY])
##   B'  = BRICK 2.0 with Ladrillo's inventory
##   L   = Ladrillo (read from the canonical draws files)
## so med(B') - med(B) is the inventory's part of the gap and med(L) - med(B') the rest (glacier structure, driver
## frame and the other calibration differences). The split is ordered: inventory first.
##
## REMAINING ICE, defined as each model's own equations use it, on the calibration forcing (RECORD_FORCING):
##   Ladrillo: sum_b a_b - S_all(INV_YEAR), the quantity its likelihood scores against Farinotti (29.0 +- 6.0 cm;
##             calibrate_mcmc_ext.jl @43d84aa:1352-1371, 1568-1570).
##   BRICK 2.0: gsic_v0 - g(INV_YEAR), with g the component's sea level. g starts at gsic_s0 (median 1.9 cm, not 0) and
##             the Wigley-Raper cap and rate both count it as melted (MimiBRICK glaciers_small_icecaps_component.jl:36-39),
##             so this is the ice the model can still melt. Table 2 note 7's 37.4 cm is gsic_v0 minus the 1850-2000
##             INCREMENT (diag_brick_gsic_melt_1850_2000.jl), which leaves s0 in; both are reported.
##
## GATES
##  [IDENTITY]  arm B reproduces the canonical BRICK 2.0 glacier draws (every scenario, both horizons) value for value.
##  [TARGET]    every B' draw's remaining ice equals its Ladrillo partner's to TOL_CM; mutation: arm B must fail it.
##  [PAIRING]   BRICK draw k and Ladrillo draw k run on the same configuration (checked against the canonical files).

using Ladrillo, CSV, DataFrames, Mimi, MimiBRICK, Printf, Random, Statistics

const SLR = dirname(@__DIR__)
const OUTD = joinpath(SLR, "outputs")
const TAG = "L27"
const STEM = "L27_tap4p69K_V5p64m_tau800"
const SCEN = ["vvVL", "vvLN", "vvL", "vvML", "vvM", "vvHL", "vvH"]
const LABEL = Dict("vvVL" => "Very Low", "vvLN" => "Low-to-Negative", "vvL" => "Low", "vvML" => "Medium-to-Low",
                   "vvM" => "Medium", "vvHL" => "High-to-Low", "vvH" => "High")
const HI, LO = "vvH", "vvVL"
const YEARS = 1850:2300
const HORIZONS = (2100, 2300)
const INV_YEAR = 2000
const CAL_YEARS = 1850:Ladrillo.record_end()       # the calibration window (to 2025)
const ROWS = 1:5:10000                       # Ladrillo joint arm = scripts/project_joint.jl
const PAIR_SEED = 2026                       # = project_joint.jl / brick20_joint.jl
const N_ITER, TOL_CM = 20, 1e-6
const QS = [0.05, 0.5, 0.95]

yi(y) = findfirst(==(y), collect(YEARS))
ci(y) = findfirst(==(y), collect(CAL_YEARS))
commit = strip(read(`git -C $SLR rev-parse --short HEAD`, String))

## ---- 1. Ladrillo's remaining ice at INV_YEAR, per joint draw, on the calibration forcing -------------------------
post = posterior(rows = ROWS)
const NB = 1000                              # BRICK 2.0's joint arm: draws 1..1000
cg, co = mean_forcing(Ladrillo.RECORD_FORCING; years = CAL_YEARS)
lmc = LadrilloModel(cg, co; years = CAL_YEARS)
gcomp, gvar = Ladrillo.COMPONENTS[:glaciers]
R_L = Vector{Float64}(undef, NB)             # m SLE
for k in 1:NB
    run_draw!(lmc, post[k, :])
    g = Float64.(lmc.m[gcomp, gvar])
    R_L[k] = sum(Float64(post[k, "gic_a_$b"]) for b in ("R19", "SLOWG", "FASTG")) - (g[ci(INV_YEAR)] - g[ci(1850)])
end
@printf("Ladrillo remaining ice at %d (draws 1..%d): median %.2f cm (5-95 %.2f-%.2f)\n", INV_YEAR, NB,
        100median(R_L), 100quantile(R_L, 0.05), 100quantile(R_L, 0.95))

## ---- 2. BRICK 2.0 on the calibration forcing: its remaining ice, and the v0' that gives Ladrillo's --------------
const BPOST = Ladrillo.brick20_posterior()
const BROWS = collect(1:max(1, nrow(BPOST) ÷ 1000):nrow(BPOST))
Mc = Ladrillo.brick20_model(years = collect(CAL_YEARS))
Ladrillo.set_brick20_forcing!(Mc, cg, co)
gsic(m) = Float64.(m[:glaciers_small_icecaps, :gsic_sea_level])
v0_orig, v0_new = zeros(NB), zeros(NB)
R_B_eff, R_B_inc, R_Bp_eff = zeros(NB), zeros(NB), zeros(NB)
hind_B, hind_Bp = zeros(NB), zeros(NB)       # 1900 -> 2020 glacier change, cm, on the calibration forcing
for k in 1:NB
    r = BPOST[BROWS[k], :]
    Ladrillo.apply_brick20!(Mc, r); run(Mc); g = gsic(Mc)
    v0_orig[k] = Float64(r.glaciers_v0)
    R_B_eff[k] = v0_orig[k] - g[ci(INV_YEAR)]
    R_B_inc[k] = v0_orig[k] - (g[ci(INV_YEAR)] - g[ci(1850)])
    hind_B[k] = 100 * (g[ci(2020)] - g[ci(1900)])
    v = R_L[k] + g[ci(INV_YEAR)]             # fixed point: v0' = target + g(INV_YEAR; v0')
    for it in 1:N_ITER
        update_param!(Mc, :glaciers_small_icecaps, :gsic_v₀, v); run(Mc); g2 = gsic(Mc)
        vnew = R_L[k] + g2[ci(INV_YEAR)]
        abs(vnew - v) * 100 < TOL_CM / 10 && (v = vnew; break)
        v = vnew
    end
    update_param!(Mc, :glaciers_small_icecaps, :gsic_v₀, v); run(Mc); g2 = gsic(Mc)
    v0_new[k] = v
    R_Bp_eff[k] = v - g2[ci(INV_YEAR)]
    hind_Bp[k] = 100 * (g2[ci(2020)] - g2[ci(1900)])
end
gates = DataFrame(gate = String[], value = Float64[], verdict = String[])
wt = maximum(abs.(R_Bp_eff .- R_L)) * 100
push!(gates, ("TARGET_max_cm", wt, wt <= TOL_CM ? "PASS" : "FAIL"))
wm = maximum(abs.(R_B_eff .- R_L)) * 100
push!(gates, ("TARGET-MUTATION_armB_max_cm", wm, wm > TOL_CM ? "PASS (gate can fail)" : "FAIL (gate is blind)"))

## ---- 3. the joint arm, B and B', all seven scenarios ---------------------------------------------------------
const M = Ladrillo.brick20_model(years = collect(YEARS))
Ladrillo.set_lws!(M, :observed; anchor = Ladrillo.LWS_OBS_ANCHOR)
const IREF = [yi(y) for y in 1995:2014]
reref(v) = 100 .* (v .- sum(v[IREF]) / length(IREF))
rows = DataFrame()
for s in SCEN
    mg, mo = mean_forcing(s; years = YEARS)
    yrs, cfg, G, O = forcing_cube(s)
    assign = let rng = MersenneTwister(PAIR_SEED), a = Int[]
        while length(a) < NB; append!(a, randperm(rng, length(cfg))); end
        a[1:NB]
    end
    B, Bp = zeros(NB, length(HORIZONS)), zeros(NB, length(HORIZONS))
    groups = Dict{Int,Vector{Int}}()
    for k in 1:NB; push!(get!(groups, assign[k], Int[]), k); end
    for (j, ks) in groups
        Ladrillo.set_brick20_forcing!(M, splice(G[:, j], mg, yrs), splice(O[:, j], mo, yrs))
        for k in ks
            Ladrillo.apply_brick20!(M, BPOST[BROWS[k], :]); run(M)
            g = reref(M[:glaciers_small_icecaps, :gsic_sea_level])
            B[k, :] = [g[yi(h)] for h in HORIZONS]
            update_param!(M, :glaciers_small_icecaps, :gsic_v₀, v0_new[k]); run(M)
            g = reref(M[:glaciers_small_icecaps, :gsic_sea_level])
            Bp[k, :] = [g[yi(h)] for h in HORIZONS]
        end
    end
    ## [IDENTITY] and [PAIRING] against the canonical draws files
    cb = CSV.read(joinpath(OUTD, "scope_slr_fairunc_draws_$(s)_spliced_oldbrick.csv"), DataFrame)
    cl = CSV.read(joinpath(OUTD, "scope_slr_fairunc_draws_$(s)_spliced_$(STEM).csv"), DataFrame)
    for (h_i, h) in enumerate(HORIZONS)
        c = sort(cb[(cb.arm .== "joint") .& (cb.component .== "glaciers") .& (cb.horizon .== h), :], :draw)
        same = c.draw == collect(1:NB)
        w = same ? maximum(abs.(B[:, h_i] .- c.value_cm)) : Inf
        push!(gates, ("IDENTITY_$(s)_$(h)_max_cm", w, same && w == 0 ? "PASS" : "FAIL"))
        l = sort(cl[(cl.arm .== "joint") .& (cl.component .== "glaciers") .& (cl.horizon .== h), :], :draw)
        cfgB = Dict(zip(c.draw, c.config)); okp = all(cfgB[d] == cf for (d, cf) in zip(l.draw, l.config) if d <= NB)
        push!(gates, ("PAIRING_$(s)_$(h)", okp ? 1.0 : 0.0, okp ? "PASS" : "FAIL"))
        Lv = Dict(zip(l.draw, l.value_cm))
        for k in 1:NB
            push!(rows, (scenario = s, label = LABEL[s], horizon = h, draw = k, config = cfg[assign[k]],
                         brick20_cm = B[k, h_i], brick20_ladinv_cm = Bp[k, h_i],
                         ladrillo_cm = get(Lv, k, NaN), ladrillo_all_draws = false))
        end
        ## Ladrillo's draws 1001..2000: no BRICK partner, kept so Ladrillo's medians are the paper's
        for (d, v) in zip(l.draw, l.value_cm)
            d > NB || continue
            push!(rows, (scenario = s, label = LABEL[s], horizon = h, draw = d, config = "", brick20_cm = NaN,
                         brick20_ladinv_cm = NaN, ladrillo_cm = v, ladrillo_all_draws = true))
        end
    end
    @printf("  %s done\n", s); flush(stdout)
end
for r in eachrow(gates); @printf("  [%s] %.3e  %s\n", r.gate, r.value, r.verdict); end
any(startswith.(gates.verdict, "FAIL")) && error("a gate FAILED; outputs not written")

## ---- 4. summary --------------------------------------------------------------------------------------------
med(v) = median(filter(!isnan, v))
summ = DataFrame()
for s in SCEN, h in HORIZONS
    d = rows[(rows.scenario .== s) .& (rows.horizon .== h), :]
    mL, mB, mBp = med(d.ladrillo_cm), med(d.brick20_cm), med(d.brick20_ladinv_cm)
    push!(summ, (scenario = s, label = LABEL[s], horizon = h, statistic = "median_cm", ladrillo = mL, brick20 = mB,
                 brick20_ladinv = mBp, gap_L_minus_B = mL - mB, inventory_part = mBp - mB, remainder = mL - mBp,
                 inventory_share = (mBp - mB) / (mL - mB)))
end
for h in HORIZONS
    f(col) = (x = summ[(summ.horizon .== h), :]; x[x.scenario .== HI, col][1] - x[x.scenario .== LO, col][1])
    rL, rB, rBp = f(:ladrillo), f(:brick20), f(:brick20_ladinv)
    push!(summ, (scenario = "$(HI)-$(LO)", label = "High minus Very Low", horizon = h, statistic = "range_cm",
                 ladrillo = rL, brick20 = rB, brick20_ladinv = rBp, gap_L_minus_B = rL - rB, inventory_part = rBp - rB,
                 remainder = rL - rBp, inventory_share = (rBp - rB) / (rL - rB)))
end
q3(v) = quantile(v, QS)
for (nm, v) in (("ladrillo_remaining_$(INV_YEAR)_cm", 100R_L), ("brick20_remaining_$(INV_YEAR)_effective_cm", 100R_B_eff),
                ("brick20_remaining_$(INV_YEAR)_table2_cm", 100R_B_inc), ("brick20_ladinv_remaining_$(INV_YEAR)_cm", 100R_Bp_eff),
                ("brick20_v0_cm", 100v0_orig), ("brick20_ladinv_v0_cm", 100v0_new),
                ("brick20_hindcast_1900_2020_cm", hind_B), ("brick20_ladinv_hindcast_1900_2020_cm", hind_Bp))
    qq = q3(v)
    push!(summ, (scenario = "calibration forcing", label = "p05 / p50 / p95 in ladrillo / brick20 / brick20_ladinv",
                 horizon = INV_YEAR, statistic = nm, ladrillo = qq[1], brick20 = qq[2], brick20_ladinv = qq[3],
                 gap_L_minus_B = NaN, inventory_part = NaN, remainder = NaN, inventory_share = NaN))
end
const PROV = "diag_glacier_inventory_ablation.jl @ $commit | Ladrillo $(pkgversion(Ladrillo)) (posterior $TAG) joint arm " *
             "(rows $(ROWS), pairing seed $PAIR_SEED; canonical draws files) | BRICK 2.0 = $(Ladrillo.BRICK20_LABEL), joint " *
             "arm as scripts/brick20_joint.jl (draws 1..$NB) | B' = BRICK 2.0 with gsic_v0 solved per draw so its remaining " *
             "ice at $INV_YEAR (v0 - g($INV_YEAR), $(Ladrillo.RECORD_FORCING) forcing) equals Ladrillo draw k's (sum a_b - " *
             "S($INV_YEAR)); other glacier parameters unchanged | glaciers, cm rel 1995-2014 | no RNG beyond the pairing " *
             "seed | julia $(VERSION)"
rows.provenance .= PROV; summ.provenance .= PROV
CSV.write(joinpath(OUTD, "diag_glacier_inventory_ablation_$(TAG)_draws.csv"), rows)
CSV.write(joinpath(OUTD, "diag_glacier_inventory_ablation_$(TAG).csv"), summ)
for r in eachrow(summ)
    @printf("  %-20s %-22s %4d %-44s L %7.2f  B %7.2f  B' %7.2f  inv %7.2f  rest %7.2f  share %5.2f\n", r.scenario,
            first(r.label, 22), r.horizon, r.statistic, r.ladrillo, r.brick20, r.brick20_ladinv, r.inventory_part,
            r.remainder, r.inventory_share)
end
println("wrote outputs/diag_glacier_inventory_ablation_$(TAG){,_draws}.csv")
