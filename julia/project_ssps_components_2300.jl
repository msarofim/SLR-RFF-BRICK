## ============================================================================
## project_ssps_components_2300.jl — BRICK-AM per-COMPONENT projections, 3 SSPs, to 2300.
##
## Workstream B2 (handoff 2026-08-05): component-resolved BRICK-AM (extA108) bands for
## SSP1-2.6 / SSP2-4.5 / SSP5-8.5, for comparison against FACTS n200 per-module output
## (experiments/global.coupling.{ssp126,ssp245,ssp585}.n200) and AR6 Ch9. The scenario
## SPREAD per component is the saturation diagnostic that caught the Mengel glacier bug.
##
## Basis: extA108 posterior (full 29-physical-param apply incl. A4 h0=-T_on*c and A6
## amp anchor-preserved map), FaIR mean forcing fair_mean_{gmst,ohc}_<ssp>.csv
## (RCMIP-native run_fair_ssps.py splice), LWS seeded (LWS_SEED via build_brick_mengel).
## Baseline 1995-2014 (≈ FACTS baseyear 2005; matches the MAGICC-comparison convention).
## Bands are 17-83% (AR6 likely) + 5-95%, finite draws only (AIS tip can go non-finite);
## nonfinite count is reported per SSP.
##
##   julia --project=julia_v2 julia/project_ssps_components_2300.jl
## ============================================================================
using CSV, DataFrames, Mimi, MimiBRICK, Printf, Statistics, Random
include(joinpath(@__DIR__, "brick_mengel.jl"))

const REPO   = abspath(joinpath(@__DIR__, ".."))
const OBSDIR = joinpath(REPO, "data/observations")
const POST   = joinpath(REPO, "data/MimiBRICK/parameters_subsample_brick_mengel_extA108.csv")
const OUT    = joinpath(REPO, "outputs/ssps_components_2300_extA108.csv")
const Y0, Y1 = 1850, 2300
const BASE0, BASE1 = 1995, 2014          # ≈ FACTS baseyear 2005
const NTHIN  = 2000                      # posterior draws after thinning
const SSPS   = [("ssp126","SSP1-2.6"), ("ssp245","SSP2-4.5"), ("ssp585","SSP5-8.5")]
const HORIZONS = (2100, 2150, 2300)

years = collect(Y0:Y1); yi(y) = findfirst(==(y), years)
const IB = [yi(y) for y in BASE0:BASE1]
const A = :antarctic_icesheet
const TANT0 = -15.42 / 0.8365            # A6 preserved anchor (calibrate_mcmc_ext.jl)

# full extA108 apply: 27 direct params + 2 derived (ais_runoff_Ton, ais_gmst_amp)
FREE = [("ais_ocean_temperature₀",A,:ais_ocean_temperature₀),("antarctic_alpha",A,:ais_α),
  ("antarctic_nu",A,:ais_ν),("antarctic_temp_threshold",A,:temperature_threshold),
  ("anto_alpha",:antarctic_ocean,:anto_α),("anto_beta",:antarctic_ocean,:anto_β),
  ("greenland_a",:greenland_icesheet,:greenland_a),("greenland_b",:greenland_icesheet,:greenland_b),
  ("greenland_alpha",:greenland_icesheet,:greenland_α),("greenland_beta",:greenland_icesheet,:greenland_β),
  ("greenland_v0",:greenland_icesheet,:greenland_v₀),("thermal_alpha",:thermal_expansion,:te_α),
  ("gic_a",_MENGEL_GLAC_SLOT,:gic_a),("gic_b",_MENGEL_GLAC_SLOT,:gic_b),
  ("gic_T_lia",_MENGEL_GLAC_SLOT,:gic_T_lia),("gic_f",_MENGEL_GLAC_SLOT,:gic_f),
  ("gic_tau_fast",_MENGEL_GLAC_SLOT,:gic_tau_fast),("gic_tau_slow",_MENGEL_GLAC_SLOT,:gic_tau_slow),
  ("antarctic_lambda",A,:λ),("antarctic_gamma",A,:ais_γ),("antarctic_kappa",A,:ais_κ),
  ("ais_mu",A,:ais_μ),("ais_bedheight0",A,:ais_bedheight₀),("ais_slope",A,:ais_slope),
  ("ais_iceflow0",A,:ais_iceflow₀),("ais_precip0_LOG",A,:ais_precipitation₀),("ais_c",A,:ais_c)]
FN = [f[1] for f in FREE]

load_traj(path, vcol) = (df=CSV.read(path,DataFrame);
    by=Dict(Int(df[i,"year"])=>Float64(df[i,vcol]) for i in 1:nrow(df)); [by[y] for y in years])

post  = CSV.read(POST, DataFrame; select=vcat(FN, ["ais_runoff_Ton","ais_gmst_amp"]))
stepp = max(1, nrow(post) ÷ NTHIN); rows = collect(1:stepp:nrow(post))
@printf("B2 components | posterior=%s (%d draws, thinned %d) | forcing=fair_mean_*_<ssp>.csv | base %d-%d\n",
        basename(POST), nrow(post), length(rows), BASE0, BASE1)

Random.seed!(2026)
m = build_brick_mengel(ssp="ssp245", y0=Y0, y1=Y1)
med = CSV.read(joinpath(REPO,"outputs/recalib_central_row.csv"), DataFrame)[1,:]
update_brick_mengel!(m, med, (a=0.45,b=0.52,T_lia=-0.45,f=0.5,tau_fast=40.0,tau_slow=250.0,sl0=0.0); precip_log=true)

function apply_draw!(r)
    for f in FREE; update_param!(m, f[2], f[3], Float64(r[f[1]])); end
    update_param!(m, A, :ais_runoffline_snowheight₀, -Float64(r["ais_runoff_Ton"])*Float64(r["ais_c"]))
    amp = Float64(r["ais_gmst_amp"])
    update_param!(m, A, :ais_temperature_coefficient, 1.0/amp)
    update_param!(m, A, :ais_temperature_intercept, -TANT0/amp)
end

const COMPS = [("glaciers", _MENGEL_GLAC_SLOT, :gsic_sea_level),
               ("gis",      :greenland_icesheet, :greenland_sea_level),
               ("ais",      A, :ais_sea_level),
               ("te",       :thermal_expansion, :te_sea_level),
               ("lws",      :landwater_storage, :lws_sea_level),
               ("total",    :global_sea_level, :sea_level_rise)]

reref(v) = (x = [ismissing(e) ? NaN : 100*Float64(e) for e in v]; x .- mean(x[IB]))

out = DataFrame(year=Int[], ssp=String[], component=String[], gmst=Float64[],
                med=Float64[], p05=Float64[], p17=Float64[], p83=Float64[], p95=Float64[],
                n_finite=Int[])
for (ssp, label) in SSPS
    gmst = load_traj(joinpath(OBSDIR,"fair_mean_gmst_$ssp.csv"), "gmst_C")
    ohc  = load_traj(joinpath(OBSDIR,"fair_mean_ohc_$ssp.csv"),  "ohc_1e22J")
    set_forcing!(m, gmst, ohc)
    series = Dict(c[1] => Array{Float64}(undef, length(years), length(rows)) for c in COMPS)
    for (j, ri) in enumerate(rows)
        apply_draw!(post[ri, :])
        run(m)
        for (nm, comp, var) in COMPS
            series[nm][:, j] = reref(m[comp, var])
        end
        j % 200 == 0 && (print("."); flush(stdout))
    end
    println()
    for (nm, _, _) in COMPS, (i, y) in enumerate(years)
        y >= 1990 || continue
        v = filter(isfinite, @view series[nm][i, :])
        push!(out, (y, label, nm, gmst[i], median(v), quantile(v,0.05), quantile(v,0.17),
                    quantile(v,0.83), quantile(v,0.95), length(v)))
    end
    for y in HORIZONS
        r(nm) = out[(out.year.==y).&(out.ssp.==label).&(out.component.==nm), :]
        @printf("%-9s @%d GMST %+0.2f | glac %5.1f  gis %5.1f  ais %5.1f  te %5.1f  lws %4.1f  TOTAL %6.1f [%5.1f,%6.1f] cm  (finite %d/%d)\n",
                label, y, gmst[yi(y)], r("glaciers").med[1], r("gis").med[1], r("ais").med[1],
                r("te").med[1], r("lws").med[1], r("total").med[1], r("total").p17[1], r("total").p83[1],
                r("total").n_finite[1], length(rows))
    end
end
CSV.write(OUT, out)
println("wrote ", relpath(OUT, REPO))
