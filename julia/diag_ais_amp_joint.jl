## diag_ais_amp_joint.jl -- the Antarctic-amplification numbers of the GMD draft's Sect. 2.2.3, on the JOINT arm.
##
##   julia --project=<Ladrillo.jl checkout> julia/diag_ais_amp_joint.jl
##
## Writes outputs/diag_ais_amp_joint_L27.csv. Marcus 2026-11-07 (notes on the draft): move every result to the joint arm.
## The fixed-arm originals are julia/diag_ais_amp_leverage.jl (outputs/diag_ais_amp_leverage_L27.csv, "perturbation"
## rows) and the AIS-amp-1.196 arm of the 2026-10-08 v1.1 number diff. Same three statistics here:
##   (a) LEVERAGE: every draw re-run with ais_gmst_amp + SIGMA, all else held; MEAN (and median) of the per-draw change
##       in Antarctic sea level at each horizon. The draft quotes the mean (45 cm, SSP2-4.5, 2300, fixed arm).
##   (b) SHARE: that mean as a percentage of the scenario's median total at the horizon.
##   (c) REVERT: every draw re-run with ais_gmst_amp = AMP_BRICK (BRICK 2.0's DAIS ratio); difference of the MEDIAN
##       totals, reverted minus base.
## The draw set is the paper's joint arm (scripts/project_joint.jl: rows 1:5:10000, pairing seed 2026, own spliced
## FaIR config, record conditioning on the UNPERTURBED climate). A perturbed run may cross the fast-dynamics threshold
## earlier, including before 2025; it is kept, as in the fixed-arm perturbation.
##
## GATES
##  [IDENTITY]  the base runs reproduce the canonical joint draws (AIS and total, both horizons) value for value.
##  [PERTURB]   the +SIGMA runs differ from the base (the perturbation reaches the model); share of draws changed printed.

using Ladrillo, CSV, DataFrames, Mimi, MimiBRICK, Printf, Random, Statistics

const SLR = dirname(@__DIR__)
const OUTD = joinpath(SLR, "outputs")
const TAG = "L27"
const TAP_STEM = "_tap4p69K_V5p64m_tau800"
const SCEN = ["ssp245", "ssp585"]
const ROWS = 1:5:10000
const PAIR_SEED = 2026
const YEARS = 1850:2300
const HORIZONS = (2100, 2300)
const SIGMA = 0.180                          # the prior sd of ais_gmst_amp, N(1.09, 0.180) (Table A1)
const AMP_BRICK = 1 / 0.8365                 # MimiBRICK v2.0.0 ais_temperature_coefficient 0.8365 -> 1.196

yi(y) = findfirst(==(y), collect(YEARS))
commit = strip(read(`git -C $SLR rev-parse --short HEAD`, String))
post = posterior(rows = ROWS)
NDRAW = nrow(post)
withamp(df, f) = (d = copy(df); d.ais_gmst_amp .= f.(Float64.(d.ais_gmst_amp)); d)
postP = withamp(post, a -> a + SIGMA)
postR = withamp(post, a -> AMP_BRICK)
gates = DataFrame(scenario = String[], gate = String[], value = Float64[], verdict = String[])
summ = DataFrame()
for s in SCEN
    mg, mo = mean_forcing(s; years = YEARS)
    yrs, cfg, G, O = forcing_cube(s)
    assign = let rng = MersenneTwister(PAIR_SEED), a = Int[]
        while length(a) < NDRAW; append!(a, randperm(rng, length(cfg))); end
        a[1:NDRAW]
    end
    NH = length(HORIZONS)
    A0, T0, AP, TR = (zeros(NDRAW, NH) for _ in 1:4)
    gmst = Dict{Int,Vector{Float64}}()
    for j in unique(assign)
        g, o = splice(G[:, j], mg, yrs), splice(O[:, j], mo, yrs)
        gmst[j] = g
        lm = LadrilloModel(g, o; years = YEARS)
        for k in findall(==(j), assign)
            run_draw!(lm, post[k, :]); a = sea_level(lm, :ais); t = sea_level(lm, :total)
            A0[k, :] = [a[yi(h)] for h in HORIZONS]; T0[k, :] = [t[yi(h)] for h in HORIZONS]
            run_draw!(lm, postP[k, :]); a = sea_level(lm, :ais)
            AP[k, :] = [a[yi(h)] for h in HORIZONS]
            run_draw!(lm, postR[k, :]); t = sea_level(lm, :total)
            TR[k, :] = [t[yi(h)] for h in HORIZONS]
        end
    end
    onset = [Ladrillo.fastdyn_onset_year(post[k, :], gmst[assign[k]], YEARS) for k in 1:NDRAW]
    keep = findall(>(Ladrillo.record_end()), onset)

    can = CSV.read(joinpath(OUTD, "scope_slr_fairunc_draws_$(s)_spliced_$(TAG)$(TAP_STEM).csv"), DataFrame)
    for (h_i, h) in enumerate(HORIZONS), (comp, X) in (("ais", A0), ("total", T0))
        c = sort(can[(can.arm .== "joint") .& (can.component .== comp) .& (can.horizon .== h), :], :draw)
        same = c.draw == keep
        w = same ? maximum(abs.(X[keep, h_i] .- c.value_cm)) : Inf
        push!(gates, (s, "IDENTITY_$(comp)_$(h)_max_cm", w, same && w == 0 ? "PASS" : "FAIL"))
    end
    chg = mean(abs.(AP[keep, end] .- A0[keep, end]) .> 0)
    push!(gates, (s, "PERTURB_share_changed_2300", chg, chg > 0 ? "PASS" : "FAIL"))

    for (h_i, h) in enumerate(HORIZONS)
        d = AP[keep, h_i] .- A0[keep, h_i]
        mtot = median(T0[keep, h_i])
        push!(summ, (scenario = s, horizon = h, n = length(keep), leverage_mean_cm = mean(d), leverage_median_cm = median(d),
                     share_of_total_pct = 100 * mean(d) / mtot, total_median_cm = mtot, ais_median_cm = median(A0[keep, h_i]),
                     revert_1196_total_cm = median(TR[keep, h_i]) - mtot))
    end
    @printf("  %s: %d draws kept\n", s, length(keep)); flush(stdout)
end
for r in eachrow(gates); @printf("  [%s] %-26s %.3e  %s\n", r.scenario, r.gate, r.value, r.verdict); end
any(startswith.(gates.verdict, "FAIL")) && error("a gate FAILED; outputs not written")
summ.provenance .= "diag_ais_amp_joint.jl @ $commit | Ladrillo $(pkgversion(Ladrillo)) (posterior $TAG) | joint arm as " *
    "scripts/project_joint.jl (rows $(ROWS), pairing seed $PAIR_SEED, record conditioning on the unperturbed climate, tap " *
    "on) | leverage: ais_gmst_amp + $SIGMA (prior sd), mean/median per-draw change in AIS | share: mean / median total | " *
    "revert: ais_gmst_amp = $(round(AMP_BRICK, digits = 4)), median total minus base median total | cm rel 1995-2014 | " *
    "no RNG beyond the pairing seed | julia $(VERSION)"
CSV.write(joinpath(OUTD, "diag_ais_amp_joint_$(TAG).csv"), summ)
show(stdout, MIME("text/plain"), summ[:, Not(:provenance)]; allrows = true, allcols = true); println()
println("wrote outputs/diag_ais_amp_joint_$(TAG).csv")
