## ============================================================================
## project_ssps_gsic_2300.jl — BRICK 2.0 (Wigley–Raper GSIC) glacier melt to 2300, all SSPs.
##
## Commitment test: under the Wigley–Raper glacier model (BRICK 2.0's default GSIC, dV/dt ∝ (T−teq)
## with equilibrium = TOTAL loss for any sustained T>teq), do the LOW-SSP glacier trajectories
## stabilize once temperature plateaus/declines, or keep melting? Wigley–Raper has no finite
## temperature-dependent equilibrium (unlike Mengel), so the expectation is they keep melting.
##
## WR GSIC = the DEFAULT MimiBRICK.get_model glacier component (no Mengel `replace!`). GSIC depends
## only on GMST, so we set ONLY the 4 glacier params per draw and override temperature with each
## scenario's FaIR 2.2.4 (calib 1.6.0) ensemble-mean GMST. The SSP set is ssp126/245/585 since 2026-10-15: the
## ssp119/370/460 inputs remain only as calib 1.4.5 `_pre160` files, so those rows would mix calibrations, and
## Ladrillo's panel (project_ssps_components_ladrillo.jl) runs the same three. The 08-30 six-SSP file is in
## outputs/quarantine/20261015_brick20_may22_posterior/. (data/observations/fair_mean_gmst_<ssp>.csv). v2.0.0 WR
## posterior = brick20_posterior_rel() (brick_param_updates.jl; gsic_teq is NOT sampled).
##
##   julia --project=julia_v2 julia/project_ssps_gsic_2300.jl [--set=ssp|vv]
## ============================================================================
using CSV, DataFrames, Mimi, MimiBRICK, Printf, Statistics, Random

const REPO = abspath(joinpath(@__DIR__, ".."))
const OBSDIR = joinpath(REPO, "data/observations")
include(joinpath(@__DIR__, "brick_param_updates.jl"))     # brick20_posterior_path, load_brick20_posterior
const POST = brick20_posterior_path(REPO)
const Y0, Y1 = 1850, 2300
const BASE0, BASE1 = 1995, 2014          # AR6 SLR reference window
const NTHIN = 1000
years = collect(Y0:Y1)
const IB = [findfirst(==(y), years) for y in BASE0:BASE1]
reref(v) = 100 .* (v .- sum(v[IB])/length(IB))   # m -> cm, rel 1995-2014
yi(y) = findfirst(==(y), years)

## ---------------------------------------------------------------------------
## SCENARIO SET (van Vuuren markers added 2026-08-31). The markers use the SAME
## fair_mean_gmst_<key>.csv convention as the SSPs, so the only things that differ are the
## (key, label) list, the output STEM, and the spread pair -- and all three come from the
## SAME entry here. That is deliberate: a figure captioned for one set can never be drawn
## from the other's file, because the set chooses the filename.
## ⚠ The SSP stem is UNCHANGED so that every existing consumer keeps resolving; the van
## Vuuren stem is `vv_gsic_2300`, NOT `ssps_gsic_2300_vv`, because no van Vuuren marker IS
## an SSP and a filename that says "ssps" would assert otherwise.
const SCEN_SETS = Dict(
    "ssp" => (stem = "ssps_gsic_2300",
              # ordered by radiative forcing (low -> high); low SSPs are the commitment test
              scens = [("ssp126","SSP1-2.6"), ("ssp245","SSP2-4.5"), ("ssp585","SSP5-8.5")],
              spread = ("SSP1-2.6", "SSP5-8.5")),
    "vv"  => (stem = "vv_gsic_2300",
              # ordered coolest-ENDPOINT first. FOUR of these peak and decline (Very Low,
              # Low-to-Neg, Medium-to-Low, High-to-Low) against the SSP set's one, which is
              # what makes this set the better commitment test.
              scens = [("vvVL","Very Low"), ("vvLN","Low-to-Neg"), ("vvL","Low"),
                       ("vvML","Medium-to-Low"), ("vvM","Medium"),
                       ("vvHL","High-to-Low"), ("vvH","High")],
              spread = ("Very Low", "High")),
)
const SET = let a = findfirst(s -> startswith(s, "--set="), ARGS)
    s = a === nothing ? "ssp" : ARGS[a][7:end]
    haskey(SCEN_SETS, s) || error("--set=$s is not one of $(sort(collect(keys(SCEN_SETS))))")
    s
end
const SCEN = SCEN_SETS[SET]
const SSPS = SCEN.scens
const STEM = SCEN.stem
@printf("scenario set `%s`: %d scenarios -> outputs/%s*.csv\n", SET, length(SSPS), STEM)

load_traj(path, vcol) = (df=CSV.read(path,DataFrame); by=Dict(Int(df[i,"year"])=>Float64(df[i,vcol]) for i in 1:nrow(df)); [by[y] for y in years])

post = load_brick20_posterior(POST)
stepp = max(1, nrow(post) ÷ NTHIN); rows = collect(1:stepp:nrow(post))
@printf("BRICK 2.0 Wigley–Raper GSIC; posterior %d draws (thinned from %d)\n", length(rows), nrow(post))

out = DataFrame(year=Int[], ssp=String[], gmst=Float64[], gsic_med=Float64[], gsic_lo=Float64[], gsic_hi=Float64[])
for (ssp, label) in SSPS
    gmst = load_traj(joinpath(OBSDIR, "fair_mean_gmst_$ssp.csv"), "gmst_C")
    Random.seed!(2026)                                    # get_model is non-deterministic (~1e-5 m); seed
    m = MimiBRICK.get_model(ssprcp_scenario="ssp245", start_year=Y0, end_year=Y1)   # DEFAULT = WR GSIC
    update_param!(m, :model_global_surface_temperature, gmst)
    G = Array{Float64}(undef, length(years), length(rows))
    for (j, ri) in enumerate(rows)
        r = post[ri, :]
        update_param!(m, :glaciers_small_icecaps, :gsic_β₀, r.glaciers_beta0)
        update_param!(m, :glaciers_small_icecaps, :gsic_v₀, r.glaciers_v0)
        update_param!(m, :glaciers_small_icecaps, :gsic_s₀, r.glaciers_s0)
        update_param!(m, :glaciers_small_icecaps, :gsic_n,  r.glaciers_n)
        run(m)
        G[:, j] = reref(m[:glaciers_small_icecaps, :gsic_sea_level])
    end
    for (i, y) in enumerate(years)
        y >= 1990 || continue
        v = @view G[i, :]
        push!(out, (y, label, gmst[i], median(v), quantile(v,0.05), quantile(v,0.95)))
    end
    med(y) = median(@view G[yi(y), :])
    @printf("%-9s  GMST 2100/2300 %+.2f/%+.2f °C   GSIC med 2100/2300 %.2f/%.2f cm   (Δ2100→2300 %+.2f)\n",
            label, gmst[yi(2100)], gmst[yi(2300)], med(2100), med(2300), med(2300)-med(2100))
end
CSV.write(joinpath(REPO, "outputs/$(STEM).csv"), out)
@printf("\nwrote outputs/%s.csv\n", STEM)
