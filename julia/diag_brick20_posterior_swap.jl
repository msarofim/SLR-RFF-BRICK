# Is the Zenodo MimiBRICK v2.0.0 JOINT posterior a drop-in for the BRICK 2.0 arm's May-22 file?
#
# Asked 2026-10-15 (Marcus: "download it and run the test"); CHANGELOG 2026-10-15b found that the 10-08h test had
# compared Zenodo's STANDALONE brick posterior with the BRICK slice of our JOINT one. This runs the like-for-like pair:
# the BRICK columns of each JOINT SNEASY-BRICK posterior, through Ladrillo's BRICK 2.0 machinery, on FaIR forcing.
#
#   julia --project=<Ladrillo> julia/diag_brick20_posterior_swap.jl        (run from SLR-RFF-BRICK/)
#
# Two parts, each copying an existing Ladrillo script step for step:
#   hindcast   = scripts/posterior_predictive_brick20.jl: run 1850-HINDCAST_END on ssp245harm mean forcing, cm rel
#                FIT_REF; RMSE of the p50 path against each calibration target (steric for TE, Dangendorf for the total
#                with the observed land water added), over the years the target exists.
#   projection = the FIXED arm of scripts/brick20_joint.jl: ssp245 mean forcing 1850-2300, land water :observed,
#                cm rel 1995-2014, rows 1:10:10000.
# Gate [ID]: the May-22 projection cells must equal Ladrillo's published fixed-arm cells (brick20_cells_ssp245.csv)
#   to within ID_TOL. Mutation: the same comparison against the JOINT-arm cells must fail.
#
# Posterior conventions: the May-22 file stores antarctic_precip0 linearly (apply_brick20! logs it). The Zenodo
# v2.0.0 files store it as a log, so it is exponentiated here and apply_brick20! logs it back.

using Ladrillo, CSV, DataFrames, Mimi, MimiBRICK, Printf, Random, Statistics, SHA

const LADRILLO = pkgdir(Ladrillo)
const POSTERIORS = [
    (label = "May-22 joint (BRICK slice; arm input)", path = joinpath(LADRILLO, "data", "brick20", "parameters_subsample_brick.csv"),
     precip = :linear),
    (label = "Zenodo 20592337 v2.0.0 joint sneasybrick", path = joinpath("data", "MimiBRICK",
     "parameters_subsample_sneasybrick_zenodo20592337.csv"), precip = :log),
]
const NDRAW = 1000
const HIND_FORCING = "ssp245harm"
const PROJ_SCENARIO = "ssp245"
const HIND_Y0, HIND_Y1 = 1850, Ladrillo.HINDCAST_END
const PROJ_YEARS = collect(1850:2300)
const PROJ_REF = (1995, 2014)
const HORIZONS = [2100, 2150, 2300]
const PUBLISHED_CELLS = joinpath(LADRILLO, "outputs", "projections", "brick20_cells_$(PROJ_SCENARIO).csv")
const ID_TOL = 1e-9          # cm; same code, same inputs, same machine: only summation-order noise is allowed
const OUT = joinpath("outputs", "diag_brick20_posterior_swap.csv")
const HIND_TARGET = Dict("ais" => :ais, "glaciers" => :gsic, "gis" => :gis, "te" => :steric, "total" => :dang)

function load_posterior(p)
    df = CSV.read(p.path, DataFrame)
    p.precip === :log && (df.antarctic_precip0 = exp.(df.antarctic_precip0))
    step = max(1, nrow(df) ÷ NDRAW)
    return df, collect(1:step:nrow(df)), step
end

function hindcast(post, rows)
    years = collect(HIND_Y0:HIND_Y1)
    ib = [findfirst(==(y), years) for y in Ladrillo.FIT_REF[1]:Ladrillo.FIT_REF[2]]
    tgt = Ladrillo.calibration_targets()
    myi = [findfirst(==(y), years) for y in tgt.years]
    g, o = mean_forcing(HIND_FORCING; years = years)
    m = Ladrillo.brick20_model(years = years)
    Ladrillo.set_brick20_forcing!(m, g, o)
    store = Dict(c => Matrix{Float64}(undef, length(rows), length(tgt.years)) for c in keys(HIND_TARGET))
    for (k, r) in enumerate(rows)
        Ladrillo.apply_brick20!(m, post[r, :])
        run(m)
        v = Dict(c => Ladrillo.brick20_sea_level(m, c, ib)[myi] for c in (:ais, :glaciers, :gis, :te))
        store["ais"][k, :] = v[:ais]; store["glaciers"][k, :] = v[:glaciers]
        store["gis"][k, :] = v[:gis]; store["te"][k, :] = v[:te]
        store["total"][k, :] = v[:ais] .+ v[:glaciers] .+ v[:gis] .+ v[:te] .+ tgt.lws
    end
    out = Dict{String,Tuple{Float64,Int,Int,Int}}()
    for (c, key) in HIND_TARGET
        p50 = [median(store[c][:, j]) for j in eachindex(tgt.years)]
        ok = .!isnan.(tgt.obs[key])
        out[c] = (sqrt(mean((p50[ok] .- tgt.obs[key][ok]) .^ 2)), count(ok), tgt.years[ok][1], tgt.years[ok][end])
    end
    return out
end

function project_fixed(post, rows)
    ib = [findfirst(==(y), PROJ_YEARS) for y in PROJ_REF[1]:PROJ_REF[2]]
    reref(v) = 100 .* (v .- sum(v[ib]) / length(ib))
    g, o = mean_forcing(PROJ_SCENARIO; years = PROJ_YEARS)
    m = Ladrillo.brick20_model(years = PROJ_YEARS)
    Ladrillo.set_lws!(m, :observed; anchor = Ladrillo.LWS_OBS_ANCHOR)
    Ladrillo.set_brick20_forcing!(m, g, o)
    comps = ["glaciers", "gis", "ais", "te", "lws", "total"]
    hi = [findfirst(==(H), PROJ_YEARS) for H in HORIZONS]
    store = Dict(c => Matrix{Float64}(undef, length(rows), length(HORIZONS)) for c in comps)
    for (k, r) in enumerate(rows)
        Ladrillo.apply_brick20!(m, post[r, :])
        run(m)
        ais  = reref(m[:antarctic_icesheet,     :ais_sea_level])
        gsic = reref(m[:glaciers_small_icecaps, :gsic_sea_level])
        gis  = reref(m[:greenland_icesheet,     :greenland_sea_level])
        te   = reref(m[:thermal_expansion,      :te_sea_level])
        lws  = reref(m[:landwater_storage,      :lws_sea_level])
        tot = ais .+ gsic .+ gis .+ te .+ lws
        for (c, v) in zip(comps, (gsic, gis, ais, te, lws, tot)); store[c][k, :] = v[hi]; end
    end
    return store
end

pub = CSV.read(PUBLISHED_CELLS, DataFrame)
pubcell(c, H, arm, col) = only(pub[(pub.component .== c) .& (pub.horizon .== H) .& (pub.arm .== arm), col])

rows_out = DataFrame(posterior = String[], file = String[], sha256 = String[], part = String[], component = String[],
                     horizon = Int[], stat = String[], value = Float64[])
for p in POSTERIORS
    post, rows, step = load_posterior(p)
    sha = bytes2hex(open(sha256, p.path))
    @printf("\n== %s | %s | sha256 %s… | rows 1:%d:%d\n", p.label, basename(p.path), sha[1:12], step, nrow(post))
    t0 = time()
    h = hindcast(post, rows)
    for c in ("te", "glaciers", "gis", "ais", "total")
        r, n, a, b = h[c]
        @printf("  hindcast RMSE of p50 vs %-7s %-8s %.3f cm (%d yr, %d-%d)\n", HIND_TARGET[c], c, r, n, a, b)
        push!(rows_out, (p.label, basename(p.path), sha, "hindcast", c, 0, "rmse_p50_cm", r))
    end
    s = project_fixed(post, rows)
    for c in ("te", "ais", "glaciers", "gis", "total"), (j, H) in enumerate(HORIZONS)
        v = s[c][:, j]
        @printf("  %s fixed %-8s %d  p50 %7.2f  [p05 %7.2f, p95 %7.2f]\n", PROJ_SCENARIO, c, H, median(v),
                quantile(v, 0.05), quantile(v, 0.95))
    end
    for c in keys(s), (j, H) in enumerate(HORIZONS), (st, f) in (("med_cm", median), ("p05_cm", x -> quantile(x, 0.05)),
                                                                   ("p95_cm", x -> quantile(x, 0.95)))
        push!(rows_out, (p.label, basename(p.path), sha, "projection_fixed_$(PROJ_SCENARIO)", c, H, st, f(s[c][:, j])))
    end
    @printf("  %.0f s\n", time() - t0)
    if p.precip === :linear
        dev(arm) = maximum(abs(median(s[c][:, j]) - pubcell(c, H, arm, :med_cm)) for c in keys(s), (j, H) in enumerate(HORIZONS))
        dfix, djoint = dev("fixed"), dev("joint")
        @printf("  [ID] max |p50 - published fixed| = %.2e cm (tol %.0e) ; mutation vs joint arm = %.2e cm\n", dfix, ID_TOL, djoint)
        dfix <= ID_TOL || error("[ID] FAIL: May-22 cells do not reproduce $(basename(PUBLISHED_CELLS)) fixed arm")
        djoint > ID_TOL || error("[ID] mutation did not fail: the gate cannot tell the fixed arm from the joint arm")
        println("  [ID] PASS (and the mutation fails as it should)")
    end
end
rows_out.provenance .= "SLR-RFF-BRICK julia/diag_brick20_posterior_swap.jl @ " *
    readchomp(`git rev-parse --short HEAD`) * " | Ladrillo $(pkgversion(Ladrillo)) BRICK 2.0 machinery (MimiBRICK " *
    "v2.0.0) | rows 1:10:10000 | Random.seed!($(Ladrillo.BRICK20_SEED)) immediately before get_model | hindcast " *
    "$(HIND_FORCING) $(HIND_Y0)-$(HIND_Y1) cm rel $(Ladrillo.FIT_REF) | projection fixed arm $(PROJ_SCENARIO) land " *
    "water :observed ($(Ladrillo.LWS_OBS_ANCHOR)) cm rel $(PROJ_REF) | FaIR 2.2.4 (calib 1.6.0) | Zenodo precip0 " *
    "exp() before apply_brick20! | julia $(VERSION)"
CSV.write(OUT, rows_out)
println("\nwrote ", OUT)
