## diag_ais_constant_climate_vs_poinelli2026.jl -- Ladrillo's and BRICK 2.0's whole-Antarctic COMMITTED loss to 2100 under
## held climate, beside Poinelli et al. (2026)'s Thwaites-alone constant-climate projection (GMD queued item 7 context).
##
##   julia --project=<Ladrillo.jl checkout> julia/diag_ais_constant_climate_vs_poinelli2026.jl
##
## Writes outputs/diag_ais_constant_climate_vs_poinelli2026_L27_draws.csv (one row per draw, model and climate) and
## outputs/diag_ais_constant_climate_vs_poinelli2026_L27.csv (the summary).
##
## POINELLI ET AL. 2026 (Nat. Commun. 17, 10364, doi:10.1038/s41467-026-77976-1): ISSM, Thwaites + Haynes domain, Thwaites
## reported. Calibrated on 1996-2023 retreat, thinning, discharge and speed-up; projected to 2100 under a CONSTANT forcing,
## surface mass balance and ocean melt held at their 1996-2023 averages, fixed ice front. Thwaites' 2100 sea-level
## equivalent at a 110 m/yr melt rate is POI_MM below, by grounding-zone length. The ISMIP6 constant-forcing Thwaites mean
## (Seroussi et al. 2024, as quoted there) is ISMIP6_THW_MM. Origin: the curves in Fig. 4b start at about 2021 (read off the
## axis; the text does not state it), hence Y_ORIGIN. The comparison is an ORDERING: a whole-sheet committed loss below one
## glacier's committed loss needs the rest of the sheet to gain mass under constant climate.
##
## LIN ET AL. 2026's drift-corrected row (the comparator ruled 10-17) removes each ISMIP6 control run and adds a linear
## background trend LIN_BG_MM_YR (the AR6 approach) in its place, so its constant-climate loss is linear by construction.
## Lin does not report the posterior value of that term; the prior value is used here.
##
## THE HOLDS (a methodological choice left to Marcus; both are reported). Each draw runs on the paper's joint arm (its own
## spliced FaIR 2.2.4 calib 1.6.0 config, as scripts/project_joint.jl pairs it), with GMST and OHC replaced from the first
## held year on by that config's own mean over the hold window:
##   hold_1996_2023  Poinelli's forcing window, held from 2024 (the year after it ends)
##   hold_2015_2024  present-day commitment: the last decade of shared history, held from 2025
## SSPs share GMST and OHC through HIST_END (checked 10-17: max |dGMST| between SSPs is 0 through 2024), so one SSP's cube
## (HIST_SCEN) is the history for both holds and the result is scenario-free. The unheld SSP2-4.5 arm is reported beside it.
## The draw set is the paper's: record conditioning is evaluated on the UNHELD climate, as project_joint.jl does.
##
## GATES
##  [IDENTITY]      the unheld re-run reproduces the canonical SSP2-4.5 AIS(2100) draws value for value (the paper's arm).
##  [HOLD-PRE]      each held path equals the unheld path exactly through the year before the first held year; its
##                  mutation (the same comparison through first held year + 5) must see a difference.
##  [HOLD-NOFIRE]   under each hold no draw's fast dynamics fires by 2100, and the lambda = 0 re-run is bit-identical, so
##                  the held loss is the slow channel alone; the mutation (one unheld fired draw added) must fail.

using Ladrillo, CSV, DataFrames, Mimi, MimiBRICK, Printf, Random, Statistics

const SLR = dirname(@__DIR__)
const OUTD = joinpath(SLR, "outputs")
const TAG = "L27"
const TAP_STEM = "_tap4p69K_V5p64m_tau800"
const HIST_SCEN = "ssp245"                   # history source for the holds, and the unheld reference arm
const HIST_END = 2024                        # last year the SSPs share
const ROWS = 1:5:10000                       # = scripts/project_joint.jl
const PAIR_SEED = 2026                       # = scripts/project_joint.jl
const YEARS = 1850:2300
const HOLDS = [(label = "hold_1996_2023", win = 1996:2023, y0 = 2024),
               (label = "hold_2015_2024", win = 2015:2024, y0 = 2025)]
const UNHELD = "none ($(HIST_SCEN))"
const Y_ORIGIN = 2021                        # Poinelli Fig. 4b origin, read off the axis
const Y_LIN = 2015                           # Lin et al. 2026's origin
const Y_END = 2100
const RATE_EARLY, RATE_LATE = 2021:2030, 2091:2100
## COMPARATORS. Poinelli et al. 2026 text and Fig. 4b: Thwaites 2100 SLE, mm, at 110 m/yr melt, mean +- spread as printed.
const POI_MM = [("poinelli_no_gz", "no grounding zone", 8.3, 3.0),
                ("poinelli_gz1km", "1 +- 1 km grounding zone", 14.3, 3.1),
                ("poinelli_gz3km", "3 +- 1 km (posterior maximum)", 19.4, 5.2),
                ("poinelli_gz5km", "5 +- 1 km (2020s observed extent)", 30.1, 5.7)]
const ISMIP6_THW_MM = (15.2, 21.8)           # ISMIP6 constant forcing, Thwaites, mean +- sd (Seroussi et al. 2024 via Poinelli)
const LIN_BG_MM_YR = (0.33, 0.16)            # Lin et al. 2026 drift-corrected background trend, mean +- 1 sd (prior)
const QS = [0.05, 0.16, 0.5, 0.84, 0.95]

yi(y) = findfirst(==(y), collect(YEARS))
ols_slope(y, v) = (x = Float64.(y) .- mean(y); sum(x .* (v .- mean(v))) / sum(x .^ 2))
function held(x, h)
    lvl = mean(x[[yi(y) for y in h.win]])
    return [y >= h.y0 ? lvl : x[i] for (i, y) in enumerate(YEARS)]
end
commit = strip(read(`git -C $SLR rev-parse --short HEAD`, String))
const PROV = "diag_ais_constant_climate_vs_poinelli2026.jl @ $commit | Ladrillo $(pkgversion(Ladrillo)) (posterior $TAG) | " *
             "joint arm as scripts/project_joint.jl (rows $(ROWS), pairing seed $PAIR_SEED, record conditioning ON on the " *
             "unheld climate, tap on) | FaIR 2.2.4 (calib 1.6.0) CMIP7-basis spliced at $(Ladrillo.SPLICE_YEAR), history " *
             "$(HIST_SCEN) | holds: GMST and OHC = the config's own mean over the window from the first held year " *
             "($(join(["$(h.label) from $(h.y0)" for h in HOLDS], ", "))) | AIS cm SLE, change $(Y_ORIGIN)->$(Y_END) and " *
             "$(Y_LIN)->$(Y_END) per draw | BRICK 2.0 = $(Ladrillo.BRICK20_LABEL), joint arm as scripts/brick20_joint.jl " *
             "(1,000 draws, not conditioned, global RNG seeded by brick20_model) | comparators Poinelli et al. 2026 " *
             "(Thwaites, constant 1996-2023 forcing, origin ~$(Y_ORIGIN) read off Fig. 4b), Lin et al. 2026 drift-corrected " *
             "background trend | julia $(VERSION)"
const LAD, B20 = "Ladrillo $(TAG)", "BRICK 2.0"

rows = DataFrame()
gates = DataFrame(model = String[], climate = String[], gate = String[], value = Float64[], verdict = String[])
function push_rows!(mdl, clim, draws, cfgs, A, A0, fired, lvl)
    io, il, ie = yi(Y_ORIGIN), yi(Y_LIN), yi(Y_END)
    ire, irl = yi(first(RATE_EARLY)):yi(last(RATE_EARLY)), yi(first(RATE_LATE)):yi(last(RATE_LATE))
    for (n, k) in enumerate(draws)
        push!(rows, (model = mdl, climate = clim, draw = k, config = cfgs[n], fired_by_2100 = fired[n],
                     held_gmst_K = lvl[n],
                     d_origin_cm = A[n, ie] - A[n, io], d_origin_nofd_cm = A0[n, ie] - A0[n, io],
                     d_lin_cm = A[n, ie] - A[n, il],
                     rate_early_mm_yr = 10 * ols_slope(collect(RATE_EARLY), A[n, ire]),
                     rate_late_mm_yr = 10 * ols_slope(collect(RATE_LATE), A[n, irl])))
    end
end
## [HOLD-PRE] and its mutation, [HOLD-NOFIRE] and its mutation
function hold_gates!(mdl, h, A, Ah, Ah0, fired_h, fired_unheld)
    ipre, imut = 1:yi(h.y0 - 1), 1:yi(h.y0 + 5)
    w = maximum(abs.(Ah[:, ipre] .- A[:, ipre]))
    push!(gates, (mdl, h.label, "HOLD-PRE_max_cm", w, w == 0 ? "PASS" : "FAIL"))
    wm = maximum(abs.(Ah[:, imut] .- A[:, imut]))
    push!(gates, (mdl, h.label, "HOLD-PRE-MUTATION_max_cm", wm, wm > 0 ? "PASS (gate can fail)" : "FAIL (gate is blind)"))
    nf = count(fired_h)
    push!(gates, (mdl, h.label, "HOLD-NOFIRE_draws_fired", Float64(nf), nf == 0 ? "PASS" : "FAIL"))
    wi = maximum(abs.(Ah .- Ah0))
    push!(gates, (mdl, h.label, "HOLD-NOFIRE_lambda0_max_cm", wi, wi == 0 ? "PASS" : "FAIL"))
    return nothing
end

## ---- Ladrillo, the paper's joint arm ---------------------------------------------------------------------------
post = posterior(rows = ROWS)
post0 = copy(post); post0.antarctic_lambda .= 0.0
const NDRAW = nrow(post)
mg, mo = mean_forcing(HIST_SCEN; years = YEARS)
yrs, cfg, G, O = forcing_cube(HIST_SCEN)
assign = let rng = MersenneTwister(PAIR_SEED), a = Int[]
    while length(a) < NDRAW; append!(a, randperm(rng, length(cfg))); end
    a[1:NDRAW]
end
NY = length(YEARS)
A, A0 = zeros(NDRAW, NY), zeros(NDRAW, NY)
AH = Dict(h.label => (zeros(NDRAW, NY), zeros(NDRAW, NY)) for h in HOLDS)
gmst, lvl = Dict{Int,Vector{Float64}}(), Dict(h.label => zeros(NDRAW) for h in HOLDS)
onset_h = Dict(h.label => fill(typemax(Int), NDRAW) for h in HOLDS)
for j in unique(assign)
    g, o = splice(G[:, j], mg, yrs), splice(O[:, j], mo, yrs)
    gmst[j] = g
    ks = findall(==(j), assign)
    lm = LadrilloModel(g, o; years = YEARS)
    for k in ks
        run_draw!(lm, post[k, :]);  A[k, :]  = sea_level(lm, :ais)
        run_draw!(lm, post0[k, :]); A0[k, :] = sea_level(lm, :ais)
    end
    for h in HOLDS
        gh, oh = held(g, h), held(o, h)
        lmh = LadrilloModel(gh, oh; years = YEARS)
        Ah, Ah0 = AH[h.label]
        for k in ks
            run_draw!(lmh, post[k, :]);  Ah[k, :]  = sea_level(lmh, :ais)
            run_draw!(lmh, post0[k, :]); Ah0[k, :] = sea_level(lmh, :ais)
            lvl[h.label][k] = gh[end]
            onset_h[h.label][k] = Ladrillo.fastdyn_onset_year(post[k, :], gh, YEARS)
        end
    end
end
onset = [Ladrillo.fastdyn_onset_year(post[k, :], gmst[assign[k]], YEARS) for k in 1:NDRAW]
keep = findall(>(Ladrillo.record_end()), onset)

can = CSV.read(joinpath(OUTD, "scope_slr_fairunc_draws_$(HIST_SCEN)_spliced_$(TAG)$(TAP_STEM).csv"), DataFrame)
can = sort(can[(can.arm .== "joint") .& (can.component .== "ais") .& (can.horizon .== Y_END), :], :draw)
same_set = can.draw == keep
w = same_set ? maximum(abs.(A[keep, yi(Y_END)] .- can.value_cm)) : Inf
push!(gates, (LAD, UNHELD, "IDENTITY_max_cm", w, same_set && w == 0 ? "PASS" : "FAIL"))

fired_u = [onset[k] <= Y_END for k in keep]
push_rows!(LAD, UNHELD, keep, cfg[assign[keep]], A[keep, :], A0[keep, :], fired_u, fill(NaN, length(keep)))
for h in HOLDS
    Ah, Ah0 = AH[h.label]
    fired_h = [onset_h[h.label][k] <= Y_END for k in keep]
    hold_gates!(LAD, h, A[keep, :], Ah[keep, :], Ah0[keep, :], fired_h, fired_u)
    ## mutation of HOLD-NOFIRE: add one unheld fired draw's unheld paths; the lambda-0 comparison must then see it
    kf = findfirst(fired_u)
    if kf !== nothing
        k = keep[kf]
        wm = maximum(abs.([Ah[keep, :]; A[k:k, :]] .- [Ah0[keep, :]; A0[k:k, :]]))
        push!(gates, (LAD, h.label, "HOLD-NOFIRE-MUTATION_max_cm", wm, wm > 0 ? "PASS (gate can fail)" : "FAIL (gate is blind)"))
    end
    push_rows!(LAD, h.label, keep, cfg[assign[keep]], Ah[keep, :], Ah0[keep, :], fired_h, lvl[h.label][keep])
end
@printf("  %s: %d draws kept\n", LAD, length(keep)); flush(stdout)

## ---- BRICK 2.0, as scripts/brick20_joint.jl ---------------------------------------------------------------------
const BPOST = Ladrillo.brick20_posterior()
const BROWS = collect(1:max(1, nrow(BPOST) ÷ 1000):nrow(BPOST))
const BPOST0 = let d = copy(BPOST); d.antarctic_lambda .= 0.0; d end
const IREF = [yi(y) for y in 1995:2014]
reref(v) = 100 .* (v .- sum(v[IREF]) / length(IREF))
const M = Ladrillo.brick20_model(years = collect(YEARS))   # seeds the global RNG to BRICK20_SEED, then get_model
Ladrillo.set_lws!(M, :observed; anchor = Ladrillo.LWS_OBS_ANCHOR)
function b20_onset(m)
    ta, tc = m[:antarctic_icesheet, :antartic_surface_temperature], m[:antarctic_icesheet, :temperature_threshold]
    for (i, y) in enumerate(YEARS)
        i >= 2 && !ismissing(ta[i]) && ta[i] > tc && return y
    end
    return typemax(Int)
end
nb = length(BROWS)
bassign = let rng = MersenneTwister(PAIR_SEED), a = Int[]
    while length(a) < nb; append!(a, randperm(rng, length(cfg))); end
    a[1:nb]
end
groups = Dict{Int,Vector{Int}}()
for k in 1:nb; push!(get!(groups, bassign[k], Int[]), k); end
function b20_run!(g, o, ks, B, B0, on)
    Ladrillo.set_brick20_forcing!(M, g, o)
    for k in ks
        Ladrillo.apply_brick20!(M, BPOST[BROWS[k], :]);  run(M)
        B[k, :] = reref(M[:antarctic_icesheet, :ais_sea_level]); on[k] = b20_onset(M)
        Ladrillo.apply_brick20!(M, BPOST0[BROWS[k], :]); run(M)
        B0[k, :] = reref(M[:antarctic_icesheet, :ais_sea_level])
    end
end
B, B0, bon = zeros(nb, NY), zeros(nb, NY), fill(typemax(Int), nb)
BH = Dict(h.label => (zeros(nb, NY), zeros(nb, NY), fill(typemax(Int), nb), zeros(nb)) for h in HOLDS)
for (j, ks) in groups
    g, o = splice(G[:, j], mg, yrs), splice(O[:, j], mo, yrs)
    b20_run!(g, o, ks, B, B0, bon)
    for h in HOLDS
        Bh, Bh0, onh, lv = BH[h.label]
        gh = held(g, h)
        b20_run!(gh, held(o, h), ks, Bh, Bh0, onh)
        lv[ks] .= gh[end]
    end
end
can = CSV.read(joinpath(OUTD, "scope_slr_fairunc_draws_$(HIST_SCEN)_spliced_oldbrick.csv"), DataFrame)
can = sort(can[(can.arm .== "joint") .& (can.component .== "ais") .& (can.horizon .== Y_END), :], :draw)
same_set = can.draw == collect(1:nb)
w = same_set ? maximum(abs.(B[:, yi(Y_END)] .- can.value_cm)) : Inf
push!(gates, (B20, UNHELD, "IDENTITY_max_cm", w, same_set && w == 0 ? "PASS" : "FAIL"))
bfired = bon .<= Y_END
push_rows!(B20, UNHELD, 1:nb, cfg[bassign], B, B0, bfired, fill(NaN, nb))
for h in HOLDS
    Bh, Bh0, onh, lv = BH[h.label]
    fh = onh .<= Y_END
    hold_gates!(B20, h, B, Bh, Bh0, fh, bfired)
    kf = findfirst(bfired)
    if kf !== nothing
        wm = maximum(abs.([Bh; B[kf:kf, :]] .- [Bh0; B0[kf:kf, :]]))
        push!(gates, (B20, h.label, "HOLD-NOFIRE-MUTATION_max_cm", wm, wm > 0 ? "PASS (gate can fail)" : "FAIL (gate is blind)"))
    end
    push_rows!(B20, h.label, 1:nb, cfg[bassign], Bh, Bh0, fh, lv)
end
@printf("  %s: %d draws\n", B20, nb); flush(stdout)

for r in eachrow(gates); @printf("  [%s | %s] %-30s %.3e  %s\n", r.model, r.climate, r.gate, r.value, r.verdict); end
any(startswith.(gates.verdict, "FAIL")) && error("a gate FAILED; outputs not written")

## ---- summary ------------------------------------------------------------------------------------------------------
summ = DataFrame()
q(v) = quantile(v, QS)
pushq!(mdl, clim, stat, v) = (qq = q(v); push!(summ, (model = mdl, climate = clim, statistic = stat, n = length(v),
    p05 = qq[1], p16 = qq[2], p50 = qq[3], p84 = qq[4], p95 = qq[5], mean = mean(v))))
pushs!(mdl, clim, stat, n, x) = push!(summ, (model = mdl, climate = clim, statistic = stat, n = n, p05 = NaN, p16 = NaN,
    p50 = x, p84 = NaN, p95 = NaN, mean = x))
for mdl in (LAD, B20), clim in [UNHELD; [h.label for h in HOLDS]]
    d = rows[(rows.model .== mdl) .& (rows.climate .== clim), :]
    for stat in ("d_origin_cm", "d_origin_nofd_cm", "d_lin_cm", "rate_early_mm_yr", "rate_late_mm_yr")
        pushq!(mdl, clim, stat, d[!, stat])
    end
    clim == UNHELD || pushq!(mdl, clim, "held_gmst_K", d.held_gmst_K)
    pushs!(mdl, clim, "share_fired_by_2100", nrow(d), mean(d.fired_by_2100))
    pushs!(mdl, clim, "late_over_early_rate_of_medians", nrow(d), median(d.rate_late_mm_yr) / median(d.rate_early_mm_yr))
    ## the ordering: whole-sheet committed loss below one glacier's (Thwaites, Poinelli) central value
    for (key, _, mu, _) in POI_MM
        pushs!(mdl, clim, "share_below_$(key)_central", nrow(d), mean(d.d_origin_cm .< mu / 10))
    end
end
## the comparators themselves, in cm, so the receipt carries what it is compared against
for (key, lab, mu, sd) in POI_MM
    push!(summ, (model = "Poinelli et al. 2026, Thwaites ($lab)", climate = "constant 1996-2023", statistic = "d_origin_cm",
                 n = 0, p05 = NaN, p16 = (mu - sd) / 10, p50 = mu / 10, p84 = (mu + sd) / 10, p95 = NaN, mean = mu / 10))
end
push!(summ, (model = "ISMIP6, Thwaites (Seroussi et al. 2024 via Poinelli)", climate = "constant forcing",
             statistic = "d_origin_cm", n = 0, p05 = NaN, p16 = (ISMIP6_THW_MM[1] - ISMIP6_THW_MM[2]) / 10,
             p50 = ISMIP6_THW_MM[1] / 10, p84 = (ISMIP6_THW_MM[1] + ISMIP6_THW_MM[2]) / 10, p95 = NaN, mean = ISMIP6_THW_MM[1] / 10))
for (stat, y0) in (("d_origin_cm", Y_ORIGIN), ("d_lin_cm", Y_LIN))
    yrs_n = Y_END - y0
    mu, sd = LIN_BG_MM_YR[1] * yrs_n / 10, LIN_BG_MM_YR[2] * yrs_n / 10
    push!(summ, (model = "Lin et al. 2026, drift-corrected background trend (prior)", climate = "linear by construction",
                 statistic = stat, n = 0, p05 = mu - 1.645sd, p16 = mu - sd, p50 = mu, p84 = mu + sd, p95 = mu + 1.645sd, mean = mu))
end
rows.provenance .= PROV; summ.provenance .= PROV
CSV.write(joinpath(OUTD, "diag_ais_constant_climate_vs_poinelli2026_$(TAG)_draws.csv"), rows)
CSV.write(joinpath(OUTD, "diag_ais_constant_climate_vs_poinelli2026_$(TAG).csv"), summ)
for r in eachrow(summ)
    @printf("  %-44s %-16s %-36s n=%4d  p05 %7.3f  p16 %7.3f  p50 %7.3f  p84 %7.3f  p95 %7.3f\n",
            first(r.model, 44), r.climate, r.statistic, r.n, r.p05, r.p16, r.p50, r.p84, r.p95)
end
println("wrote outputs/diag_ais_constant_climate_vs_poinelli2026_$(TAG){,_draws}.csv")
