## ============================================================================
## project_ssps_gsic_2300_mengel.jl — Mengel-2016 glacier melt to 2300, all SSPs.
##
## Companion to project_ssps_gsic_2300.jl (Wigley–Raper / BRICK 2.0). SAME SSP temperatures feed both;
## only the glacier MODEL differs. Mengel has a finite, temperature-dependent equilibrium
## S_eq(ΔT)=a(1−e^{−bΔT}) relaxed on two timescales, so LOW-SSP glacier melt should STABILIZE once
## temperature plateaus — the opposite of Wigley–Raper's "everything eventually goes" commitment.
##
## Glacier posterior = the Mengel gic_* params from the BRICK-AM extA108 subsample (calibrated ON the
## same FaIR GMST → baseline-consistent). GSIC depends only on GMST; set only the 7 glacier params.
##
##   julia --project=julia_v2 julia/project_ssps_gsic_2300_mengel.jl [--set=ssp|vv]
## ============================================================================
using CSV, DataFrames, Mimi, MimiBRICK, Printf, Statistics, Random
include(joinpath(@__DIR__, "brick_mengel.jl"))     # build_brick_mengel, _MENGEL_GLAC_SLOT (Mengel glacier)

const REPO = abspath(joinpath(@__DIR__, ".."))
const OBSDIR = joinpath(REPO, "data/observations")
const POST = joinpath(REPO, "data/MimiBRICK/parameters_subsample_brick_mengel_extA108.csv")
const Y0, Y1 = 1850, 2300
const BASE0, BASE1 = 1995, 2014
const NTHIN = 1000
const GIC_SL0 = 0.0                                # fixed in calibration (not sampled)
const BCF = 0.52                                   # counterfactual b (Mengel-published multi-model median).
                                                   # extA108 fits b→0.89 (railed at its 1.0 bound), which
                                                   # saturates S_eq by ~1.3°C and collapses the scenario spread;
                                                   # history only pins the slope a·b, not b. This arm sets b=0.52
                                                   # and rescales a per draw to PRESERVE that draw's a·b (same
                                                   # historical fit) → shows the physically-expected spread.
years = collect(Y0:Y1)
const IB = [findfirst(==(y), years) for y in BASE0:BASE1]
reref(v) = 100 .* (v .- sum(v[IB])/length(IB))
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
              scens = [("ssp119","SSP1-1.9"), ("ssp126","SSP1-2.6"), ("ssp245","SSP2-4.5"),
                       ("ssp460","SSP4-6.0"), ("ssp370","SSP3-7.0"), ("ssp585","SSP5-8.5")],
              spread = ("SSP1-1.9", "SSP5-8.5")),
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

post = CSV.read(POST, DataFrame)
stepp = max(1, nrow(post) ÷ NTHIN); rows = collect(1:stepp:nrow(post))
@printf("Mengel-2016 glacier (BRICK-AM extA108 posterior); %d draws (thinned from %d)\n", length(rows), nrow(post))

mkcols() = DataFrame(year=Int[], ssp=String[], gmst=Float64[], gsic_med=Float64[], gsic_lo=Float64[], gsic_hi=Float64[])
out, out_cf = mkcols(), mkcols()
for (ssp, label) in SSPS
    gmst = load_traj(joinpath(OBSDIR, "fair_mean_gmst_$ssp.csv"), "gmst_C")
    Random.seed!(2026)
    m = build_brick_mengel(ssp="ssp245", y0=Y0, y1=Y1)          # Mengel glacier swapped in
    update_param!(m, :model_global_surface_temperature, gmst)
    G   = Array{Float64}(undef, length(years), length(rows))    # posterior (b→0.89)
    Gcf = Array{Float64}(undef, length(years), length(rows))    # counterfactual (b=0.52, a·b preserved)
    for (j, ri) in enumerate(rows)
        r = post[ri, :]
        update_param!(m, _MENGEL_GLAC_SLOT, :gic_T_lia,    r.gic_T_lia)
        update_param!(m, _MENGEL_GLAC_SLOT, :gic_f,        r.gic_f)
        update_param!(m, _MENGEL_GLAC_SLOT, :gic_tau_fast, r.gic_tau_fast)
        update_param!(m, _MENGEL_GLAC_SLOT, :gic_tau_slow, r.gic_tau_slow)
        update_param!(m, _MENGEL_GLAC_SLOT, :gic_sl0,      GIC_SL0)
        # --- posterior arm ---
        update_param!(m, _MENGEL_GLAC_SLOT, :gic_a, r.gic_a)
        update_param!(m, _MENGEL_GLAC_SLOT, :gic_b, r.gic_b)
        run(m); G[:, j] = reref(m[:glaciers_small_icecaps, :gsic_sea_level])
        # --- counterfactual arm: b=0.52, a rescaled to keep this draw's a·b (same historical fit) ---
        update_param!(m, _MENGEL_GLAC_SLOT, :gic_b, BCF)
        update_param!(m, _MENGEL_GLAC_SLOT, :gic_a, r.gic_a * r.gic_b / BCF)
        run(m); Gcf[:, j] = reref(m[:glaciers_small_icecaps, :gsic_sea_level])
    end
    for (i, y) in enumerate(years)
        y >= 1990 || continue
        v = @view G[i, :]; vc = @view Gcf[i, :]
        push!(out,    (y, label, gmst[i], median(v),  quantile(v,0.05),  quantile(v,0.95)))
        push!(out_cf, (y, label, gmst[i], median(vc), quantile(vc,0.05), quantile(vc,0.95)))
    end
    medG(y)  = median(@view G[yi(y), :]);  medC(y) = median(@view Gcf[yi(y), :])
    @printf("%-9s  GMST@2300 %+.2f °C   GSIC@2300 post %.2f / cf(b=.52) %.2f cm\n",
            label, gmst[yi(2300)], medG(2300), medC(2300))
end
CSV.write(joinpath(REPO, "outputs/$(STEM)_mengel.csv"), out)
CSV.write(joinpath(REPO, "outputs/$(STEM)_mengel_b052.csv"), out_cf)
lo, hi = SCEN.spread
sp(df) = (d=df[(df.year.==2300),:]; d[d.ssp.==hi,:gsic_med][1] - d[d.ssp.==lo,:gsic_med][1])
@printf("\n%s→%s spread @2300:  posterior %.1f cm   counterfactual(b=0.52) %.1f cm\n", lo, hi, sp(out), sp(out_cf))
@printf("wrote outputs/%s_mengel{,_b052}.csv\n", STEM)
