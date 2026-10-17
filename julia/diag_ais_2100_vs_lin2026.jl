## diag_ais_2100_vs_lin2026.jl -- Ladrillo's 2100 Antarctic contribution on Lin et al. (2026)'s basis, and how much of it
## is DAIS's fast-dynamics channel (GMD queued item 7: the Lin et al. 2026 comparison + the fast-dynamics attribution).
##
##   julia --project=<Ladrillo.jl checkout> julia/diag_ais_2100_vs_lin2026.jl
##
## Writes outputs/diag_ais_2100_vs_lin2026_L27_draws.csv (one row per kept joint-arm draw and scenario) and
## outputs/diag_ais_2100_vs_lin2026_L27.csv (the summary).
##
## LIN ET AL. 2026 (Nat. Geosci., doi:10.1038/s41561-026-02102-1, Table 1): an emulator of ISMIP6-2300, 2100 Antarctic
## SLR as the CHANGE SINCE 2015 (ISMIP6 projections start in 2015), cm SLE, on SSP1-1.9 / SSP2-4.5 / SSP5-8.5 warming
## from 500 FaIR v1.x projections "similar to those used in IPCC AR6", calibrated on the 2002-2021 rate 0.44 +- 0.04 mm/yr
## (King et al. 2023, variability removed) against the emulated 2015-2021 rate.
##
## LADRILLO ON THAT BASIS. The paper's joint arm exactly as Ladrillo.jl scripts/project_joint.jl builds it (posterior rows
## 1:5:10000, pairing seed 2026, own spliced FaIR 2.2.4 calib 1.6.0 config, record conditioning ON), per draw:
##   d2100     = AIS(2100) - AIS(2015)               the 2015 baseline per draw, not from medians
##   d2100_nofd = the same draw re-run with antarctic_lambda = 0 (fast-dynamics flux off)
##   fd        = d2100 - d2100_nofd                 the fast-dynamics channel's share of the 2015-2100 change
##   rate_2015_2021 = OLS of AIS(2015..2021), mm/yr  the quantity Lin's likelihood scores
## Only SSP2-4.5 and SSP5-8.5 are matched scenarios. Ladrillo's calib 1.6.0 forcing has SSP1-2.6, not SSP1-1.9.
##
## GATES
##  [IDENTITY]   the shipped re-run's AIS(2100) must equal the canonical SLR draws file value for value, and the kept
##               draw set must be the canonical one (the conditioning reproduces).
##  [NOFD-INERT] a draw whose fast dynamics never fire by 2100 must give exactly the same 2015..2100 AIS path with
##               lambda = 0; otherwise lambda acts outside the channel and "fd" is not the channel.
##  [NOFD-MUTATION] the inert gate must FAIL when a fired draw is included (it can see the channel).
##
## BRICK 2.0 on the same basis: stock MimiBRICK v2.0.0 with the Zenodo posterior exactly as scripts/brick20_joint.jl
## builds its joint arm (1,000 draws, rows 1:10:10000, the same pairing seed, NOT record-conditioned, as shipped). Its
## onset year is read from the model's own Antarctic temperature and threshold, so its [NOFD-INERT] gate is not
## tautological. [IDENTITY] is against scope_slr_fairunc_draws_<ssp>_spliced_oldbrick.csv.

using Ladrillo, CSV, DataFrames, Mimi, MimiBRICK, Printf, Random, Statistics

const SLR = dirname(@__DIR__)
const OUTD = joinpath(SLR, "outputs")
const TAG = "L27"
const TAP_STEM = "_tap4p69K_V5p64m_tau800"
const SCEN = ["ssp126", "ssp245", "ssp585"]
const LIN_MATCH = Dict("ssp126" => "none (Lin: SSP1-1.9)", "ssp245" => "SSP2-4.5", "ssp585" => "SSP5-8.5")
const ROWS = 1:5:10000                       # = scripts/project_joint.jl
const PAIR_SEED = 2026                       # = scripts/project_joint.jl
const YEARS = 1850:2300
const Y_BASE, Y_END = 2015, 2100
const RATE_WIN = 2015:2021                   # Lin's emulated calibration window
const AR6_WIN, PI_WIN = 2081:2100, 1850:1900 # the warming check against IPCC AR6 WG1 Table SPM.1
const LIN_HIGHEND_P95_585 = 25.4             # Lin Table 1, raw posterior high-end SSP5-8.5, 95th percentile (cm)
const LIN_POST_P95 = Dict("ssp245" => 8.8, "ssp585" => 14.8)    # Lin Table 1, raw posterior, 95th percentile (cm)
const QS = [0.05, 0.16, 0.5, 0.84, 0.95]

yi(y) = findfirst(==(y), collect(YEARS))
ols_slope(y, v) = (x = Float64.(y) .- mean(y); sum(x .* (v .- mean(v))) / sum(x .^ 2))
commit = strip(read(`git -C $SLR rev-parse --short HEAD`, String))
const PROV = "diag_ais_2100_vs_lin2026.jl @ $commit | Ladrillo $(pkgversion(Ladrillo)) (posterior $TAG) | joint arm as " *
             "scripts/project_joint.jl (rows $(ROWS), pairing seed $PAIR_SEED, record conditioning ON, tap on) | FaIR 2.2.4 " *
             "(calib 1.6.0) CMIP7-basis spliced at $(Ladrillo.SPLICE_YEAR) | AIS cm SLE, change $(Y_BASE)->$(Y_END) per draw | " *
             "nofd = antarctic_lambda 0 | rate OLS $(first(RATE_WIN))-$(last(RATE_WIN)) mm/yr | BRICK 2.0 = " *
             "$(Ladrillo.BRICK20_LABEL), joint arm as scripts/brick20_joint.jl (1,000 draws, not conditioned) | julia $(VERSION)"
const LAD, B20 = "Ladrillo $(TAG)", "BRICK 2.0"

post = posterior(rows = ROWS)
post0 = copy(post); post0.antarctic_lambda .= 0.0
const NDRAW = nrow(post)
rows = DataFrame()
gates = DataFrame(model = String[], scenario = String[], gate = String[], value = Float64[], verdict = String[])

for s in SCEN
    mg, mo = mean_forcing(s; years = YEARS)
    yrs, cfg, G, O = forcing_cube(s)
    assign = let rng = MersenneTwister(PAIR_SEED), a = Int[]
        while length(a) < NDRAW; append!(a, randperm(rng, length(cfg))); end
        a[1:NDRAW]
    end
    ib, ie = yi(Y_BASE), yi(Y_END)
    A, A0 = Matrix{Float64}(undef, NDRAW, length(YEARS)), Matrix{Float64}(undef, NDRAW, length(YEARS))
    gmst = Dict{Int,Vector{Float64}}()
    for j in unique(assign)
        g, o = splice(G[:, j], mg, yrs), splice(O[:, j], mo, yrs)
        gmst[j] = g
        lm = LadrilloModel(g, o; years = YEARS)
        for k in findall(==(j), assign)
            run_draw!(lm, post[k, :]);  A[k, :]  = sea_level(lm, :ais)
            run_draw!(lm, post0[k, :]); A0[k, :] = sea_level(lm, :ais)
        end
    end
    onset = [Ladrillo.fastdyn_onset_year(post[k, :], gmst[assign[k]], YEARS) for k in 1:NDRAW]
    keep = findall(>(Ladrillo.record_end()), onset)

    ## [IDENTITY] against the canonical research output
    can = CSV.read(joinpath(OUTD, "scope_slr_fairunc_draws_$(s)_spliced_$(TAG)$(TAP_STEM).csv"), DataFrame)
    can = sort(can[(can.arm .== "joint") .& (can.component .== "ais") .& (can.horizon .== Y_END), :], :draw)
    same_set = can.draw == keep
    w = same_set ? maximum(abs.(A[keep, ie] .- can.value_cm)) : Inf
    push!(gates, (LAD, s, "IDENTITY_max_cm", w, same_set && w == 0 ? "PASS" : "FAIL"))

    ## [NOFD-INERT] and its mutation
    unfired = [k for k in keep if onset[k] > Y_END]
    fired = [k for k in keep if onset[k] <= Y_END]
    wi = isempty(unfired) ? 0.0 : maximum(abs.(A[unfired, ib:ie] .- A0[unfired, ib:ie]))
    push!(gates, (LAD, s, "NOFD-INERT_max_cm", wi, wi == 0 ? "PASS" : "FAIL"))
    if !isempty(fired)
        wm = maximum(abs.(A[[unfired; fired[1]], ib:ie] .- A0[[unfired; fired[1]], ib:ie]))
        push!(gates, (LAD, s, "NOFD-MUTATION_max_cm", wm, wm > 0 ? "PASS (gate can fail)" : "FAIL (gate is blind)"))
    end

    i2081, i2100 = yi(first(AR6_WIN)), yi(last(AR6_WIN))
    ipi = yi(first(PI_WIN)):yi(last(PI_WIN))
    irate = yi(first(RATE_WIN)):yi(last(RATE_WIN))
    for k in keep
        g = gmst[assign[k]]
        push!(rows, (model = LAD, scenario = s, lin_match = LIN_MATCH[s], draw = k, config = cfg[assign[k]], onset_year = onset[k],
                     fired_by_2100 = onset[k] <= Y_END, ais_2015_cm = A[k, ib], ais_2100_cm = A[k, ie],
                     d2100_cm = A[k, ie] - A[k, ib], d2100_nofd_cm = A0[k, ie] - A0[k, ib],
                     fd_cm = (A[k, ie] - A[k, ib]) - (A0[k, ie] - A0[k, ib]),
                     rate_2015_2021_mm_yr = 10 * ols_slope(collect(RATE_WIN), A[k, irate]),
                     gmst_2100_rel2015_K = g[i2100] - g[ib],
                     gmst_2081_2100_rel1850_1900_K = mean(g[i2081:i2100]) - mean(g[ipi])))
    end
    @printf("  %s %s: %d draws kept, %d fired by %d\n", LAD, s, length(keep), length(fired), Y_END); flush(stdout)
end

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
for s in SCEN
    mg, mo = mean_forcing(s; years = YEARS)
    yrs, cfg, G, O = forcing_cube(s)
    nb = length(BROWS)
    assign = let rng = MersenneTwister(PAIR_SEED), a = Int[]
        while length(a) < nb; append!(a, randperm(rng, length(cfg))); end
        a[1:nb]
    end
    ib, ie = yi(Y_BASE), yi(Y_END)
    A, A0 = Matrix{Float64}(undef, nb, length(YEARS)), Matrix{Float64}(undef, nb, length(YEARS))
    onset, gm = fill(typemax(Int), nb), Dict{Int,Vector{Float64}}()
    groups = Dict{Int,Vector{Int}}()
    for k in 1:nb; push!(get!(groups, assign[k], Int[]), k); end
    for (j, ks) in groups
        g, o = splice(G[:, j], mg, yrs), splice(O[:, j], mo, yrs)
        gm[j] = g
        Ladrillo.set_brick20_forcing!(M, g, o)
        for k in ks
            Ladrillo.apply_brick20!(M, BPOST[BROWS[k], :]);  run(M)
            A[k, :] = reref(M[:antarctic_icesheet, :ais_sea_level]); onset[k] = b20_onset(M)
            Ladrillo.apply_brick20!(M, BPOST0[BROWS[k], :]); run(M)
            A0[k, :] = reref(M[:antarctic_icesheet, :ais_sea_level])
        end
    end
    can = CSV.read(joinpath(OUTD, "scope_slr_fairunc_draws_$(s)_spliced_oldbrick.csv"), DataFrame)
    can = sort(can[(can.arm .== "joint") .& (can.component .== "ais") .& (can.horizon .== Y_END), :], :draw)
    same_set = can.draw == collect(1:nb)
    w = same_set ? maximum(abs.(A[:, ie] .- can.value_cm)) : Inf
    push!(gates, (B20, s, "IDENTITY_max_cm", w, same_set && w == 0 ? "PASS" : "FAIL"))
    unfired, fired = findall(>(Y_END), onset), findall(<=(Y_END), onset)
    wi = isempty(unfired) ? 0.0 : maximum(abs.(A[unfired, ib:ie] .- A0[unfired, ib:ie]))
    push!(gates, (B20, s, "NOFD-INERT_max_cm", wi, wi == 0 ? "PASS" : "FAIL"))
    if !isempty(fired)
        wm = maximum(abs.(A[[unfired; fired[1]], ib:ie] .- A0[[unfired; fired[1]], ib:ie]))
        push!(gates, (B20, s, "NOFD-MUTATION_max_cm", wm, wm > 0 ? "PASS (gate can fail)" : "FAIL (gate is blind)"))
    end
    push!(gates, (B20, s, "draws_firing_by_record_end", Float64(count(<=(Ladrillo.record_end()), onset)), "measured"))
    i2081, i2100 = yi(first(AR6_WIN)), yi(last(AR6_WIN))
    ipi = yi(first(PI_WIN)):yi(last(PI_WIN))
    irate = yi(first(RATE_WIN)):yi(last(RATE_WIN))
    for k in 1:nb
        g = gm[assign[k]]
        push!(rows, (model = B20, scenario = s, lin_match = LIN_MATCH[s], draw = k, config = cfg[assign[k]],
                     onset_year = onset[k], fired_by_2100 = onset[k] <= Y_END, ais_2015_cm = A[k, ib],
                     ais_2100_cm = A[k, ie], d2100_cm = A[k, ie] - A[k, ib], d2100_nofd_cm = A0[k, ie] - A0[k, ib],
                     fd_cm = (A[k, ie] - A[k, ib]) - (A0[k, ie] - A0[k, ib]),
                     rate_2015_2021_mm_yr = 10 * ols_slope(collect(RATE_WIN), A[k, irate]),
                     gmst_2100_rel2015_K = g[i2100] - g[ib],
                     gmst_2081_2100_rel1850_1900_K = mean(g[i2081:i2100]) - mean(g[ipi])))
    end
    @printf("  %s %s: %d draws, %d fired by %d\n", B20, s, nb, length(fired), Y_END); flush(stdout)
end
for r in eachrow(gates); @printf("  [%s %s] %-28s %.3e  %s\n", r.model, r.scenario, r.gate, r.value, r.verdict); end
any(startswith.(gates.verdict, "FAIL")) && error("a gate FAILED; outputs not written")

summ = DataFrame()
q(v) = quantile(v, QS)
for mdl in (LAD, B20), s in SCEN
    d = rows[(rows.model .== mdl) .& (rows.scenario .== s), :]
    for (stat, v) in (("d2100_cm", d.d2100_cm), ("d2100_nofd_cm", d.d2100_nofd_cm), ("fd_cm", d.fd_cm),
                      ("rate_2015_2021_mm_yr", d.rate_2015_2021_mm_yr), ("gmst_2100_rel2015_K", d.gmst_2100_rel2015_K),
                      ("gmst_2081_2100_rel1850_1900_K", d.gmst_2081_2100_rel1850_1900_K))
        qq = q(v)
        push!(summ, (model = mdl, scenario = s, lin_match = LIN_MATCH[s], statistic = stat, n = length(v), p05 = qq[1], p16 = qq[2],
                     p50 = qq[3], p84 = qq[4], p95 = qq[5], mean = mean(v)))
    end
    nf = count(d.fired_by_2100)
    push!(summ, (model = mdl, scenario = s, lin_match = LIN_MATCH[s], statistic = "share_fired_by_2100", n = nrow(d), p05 = NaN,
                 p16 = NaN, p50 = nf / nrow(d), p84 = NaN, p95 = NaN, mean = nf / nrow(d)))
    push!(summ, (model = mdl, scenario = s, lin_match = LIN_MATCH[s], statistic = "fd_share_of_median_d2100", n = nrow(d), p05 = NaN,
                 p16 = NaN, p50 = 1 - median(d.d2100_nofd_cm) / median(d.d2100_cm), p84 = NaN, p95 = NaN, mean = NaN))
    if haskey(LIN_POST_P95, s)
        sh = mean(d.d2100_cm .> LIN_POST_P95[s])
        push!(summ, (model = mdl, scenario = s, lin_match = LIN_MATCH[s], statistic = "share_above_lin_posterior_p95", n = nrow(d),
                     p05 = NaN, p16 = NaN, p50 = sh, p84 = NaN, p95 = NaN, mean = sh))
    end
    if s == "ssp585"
        sh = mean(d.d2100_cm .> LIN_HIGHEND_P95_585)
        push!(summ, (model = mdl, scenario = s, lin_match = LIN_MATCH[s], statistic = "share_above_lin_highend_p95", n = nrow(d),
                     p05 = NaN, p16 = NaN, p50 = sh, p84 = NaN, p95 = NaN, mean = sh))
    end
end
rows.provenance .= PROV; summ.provenance .= PROV
CSV.write(joinpath(OUTD, "diag_ais_2100_vs_lin2026_$(TAG)_draws.csv"), rows)
CSV.write(joinpath(OUTD, "diag_ais_2100_vs_lin2026_$(TAG).csv"), summ)
for r in eachrow(summ)
    @printf("  %-12s %-7s %-30s n=%4d  p05 %8.3f  p16 %8.3f  p50 %8.3f  p84 %8.3f  p95 %8.3f\n",
            r.model, r.scenario, r.statistic, r.n, r.p05, r.p16, r.p50, r.p84, r.p95)
end
println("wrote outputs/diag_ais_2100_vs_lin2026_$(TAG){,_draws}.csv")
