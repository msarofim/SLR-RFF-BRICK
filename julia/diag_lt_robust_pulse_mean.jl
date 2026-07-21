# Is a pulse-size-ROBUST pulse mean straightforward? Compare raw mean, median, and a
# Lemoine-Traeger tip-decomposed mean at 0.1 vs 10 GtCO2 for the phase-2 posterior.
# LT idea: split the marginal into (i) a smooth part from NON-tip draws (~linear, robust) and
# (ii) a tip part = [fraction of draws the pulse newly tips]/pulse x [mean SLR jump when tipped].
# As pulse->0 the tip part converges to hazard x jump; if the DECOMPOSED mean matches across
# 0.1 and 10 GtCO2 while the RAW mean does not, the LT estimator is the robust one.
using CSV, DataFrames, Mimi, MimiBRICK, Statistics, Printf
REPO="/Users/MarcusMarcus/Documents/2026/CodeProjects/SLR-RFF-BRICK"
FRC="/Users/MarcusMarcus/Documents/2026/CodeProjects/FaIRtoFrEDI/magicc_comparison/processed/curv_wide"
include(joinpath(REPO,"julia/brick_mengel.jl"))
Y0,Y1=1850,2150; years=collect(Y0:Y1); tidx(y)=findfirst(==(y),years)
OHCS=0.1; NDRAW=400; TANT0=-15.42/0.8365
A=:antarctic_icesheet; G=:glaciers_small_icecaps
FREE=[("ais_ocean_temperature₀",A,:ais_ocean_temperature₀),("antarctic_alpha",A,:ais_α),("antarctic_nu",A,:ais_ν),
("antarctic_temp_threshold",A,:temperature_threshold),("anto_alpha",:antarctic_ocean,:anto_α),("anto_beta",:antarctic_ocean,:anto_β),
("greenland_a",:greenland_icesheet,:greenland_a),("greenland_b",:greenland_icesheet,:greenland_b),("greenland_alpha",:greenland_icesheet,:greenland_α),
("greenland_beta",:greenland_icesheet,:greenland_β),("greenland_v0",:greenland_icesheet,:greenland_v₀),("thermal_alpha",:thermal_expansion,:te_α),
("gic_a",G,:gic_a),("gic_b",G,:gic_b),("gic_T_lia",G,:gic_T_lia),("gic_f",G,:gic_f),("gic_tau_fast",G,:gic_tau_fast),("gic_tau_slow",G,:gic_tau_slow),
("antarctic_lambda",A,:λ),("antarctic_gamma",A,:ais_γ),("antarctic_kappa",A,:ais_κ),
("ais_mu",A,:ais_μ),("ais_bedheight0",A,:ais_bedheight₀),("ais_slope",A,:ais_slope),("ais_iceflow0",A,:ais_iceflow₀),
("ais_precip0_LOG",A,:ais_precipitation₀),("ais_c",A,:ais_c)]
FN=[f[1] for f in FREE]
lw(p;s=1.0)=(d=CSV.read(p,DataFrame); keep=[y in years for y in d.year]; (Matrix(d[keep,2:end]).*s))
gb=lw(joinpath(FRC,"ssp245_gmst_base.csv")); ob=lw(joinpath(FRC,"ssp245_ohc_base.csv");s=OHCS)
g01=lw(joinpath(FRC,"ssp245_gmst_pulse.csv")); o01=lw(joinpath(FRC,"ssp245_ohc_pulse.csv");s=OHCS)
g10=lw(joinpath(FRC,"ssp245_gmst_pulse10gt.csv")); o10=lw(joinpath(FRC,"ssp245_ohc_pulse10gt.csv");s=OHCS)
post=CSV.read(joinpath(REPO,"data/MimiBRICK/parameters_subsample_brick_mengel_ext.csv"),DataFrame)
med=CSV.read(joinpath(REPO,"outputs/recalib_central_row.csv"),DataFrame)[1,:]
m=build_brick_mengel(ssp="ssp245",y0=Y0,y1=Y1)
update_brick_mengel!(m,med,(a=0.45,b=0.52,T_lia=-0.45,f=0.5,tau_fast=40.0,tau_slow=250.0,sl0=0.0);precip_log=true)
setrow(r)=begin
  for f in FREE; update_param!(m,f[2],f[3],Float64(r[f[1]])); end
  update_param!(m,A,:ais_runoffline_snowheight₀,-Float64(r["ais_runoff_Ton"])*Float64(r["ais_c"]))
  a=Float64(r["ais_gmst_amp"]); update_param!(m,A,:ais_temperature_coefficient,1.0/a); update_param!(m,A,:ais_temperature_intercept,-TANT0/a)
end
runforce(g,o)=begin set_forcing!(m,g,o); run(m); (100 .*m[:global_sea_level,:sea_level_rise], m[:antarctic_icesheet,:antartic_surface_temperature]) end
N=min(NDRAW,size(gb,2),nrow(post))
Y=[2100,2150]
# collect per-draw: base level, p01 level, p10 level, and tip-time (first year AIS surface T>threshold) for base/p01/p10
res=Dict(y=>Dict(:b=>Float64[],:p01=>Float64[],:p10=>Float64[]) for y in Y)
tip=Dict(:b=>Bool[],:p01=>Bool[],:p10=>Bool[])
for i in 1:N
  setrow(post[i,:]); thr=Float64(post[i,"antarctic_temp_threshold"])
  lb,ab=runforce(gb[:,i],ob[:,i]); l1,a1=runforce(g01[:,i],o01[:,i]); l2,a2=runforce(g10[:,i],o10[:,i])
  for y in Y; push!(res[y][:b],lb[tidx(y)]); push!(res[y][:p01],l1[tidx(y)]); push!(res[y][:p10],l2[tidx(y)]); end
  rng=tidx(1990):tidx(2100)
  push!(tip[:b], any(ab[rng].>thr)); push!(tip[:p01], any(a1[rng].>thr)); push!(tip[:p10], any(a2[rng].>thr))
end
q(v,p)=quantile(v,p)
@printf("Phase-2 pulse marginal robustness (N=%d, cm/GtCO2):\n",N)
for y in Y
  b=res[y][:b]
  m01=(res[y][:p01].-b)./0.1; m10=(res[y][:p10].-b)./10.0
  # LT decomposition at each pulse: newtip = tipped in pulse, not base
  function lt(marg, tp, ps)
    newtip = tp .& .!tip[:b]                       # draws the pulse newly tipped
    smooth = mean(marg[.!newtip])                  # non-newtip: smooth ~linear part
    fnt = count(newtip)/length(marg)               # fraction newly tipped
    tipjump = isempty(marg[newtip]) ? 0.0 : mean(marg[newtip])  # per-tonne jump for newly tipped
    (smooth + fnt*(tipjump-smooth), fnt, smooth)   # LT mean = smooth + fraction*(extra jump)
  end
  lt01,f01,sm01 = lt(m01, tip[:p01], 0.1)
  lt10,f10,sm10 = lt(m10, tip[:p10], 10.0)
  @printf("\n @%d:\n", y)
  @printf("   RAW mean:   0.1GtCO2 %.3e   10GtCO2 %.3e   (ratio %.2f)  <- pulse-size sensitive?\n", mean(m01),mean(m10), mean(m10)/mean(m01))
  @printf("   MEDIAN:     0.1GtCO2 %.3e   10GtCO2 %.3e   (ratio %.2f)\n", q(m01,.5),q(m10,.5), q(m10,.5)/q(m01,.5))
  @printf("   LT mean:    0.1GtCO2 %.3e   10GtCO2 %.3e   (ratio %.2f)  smooth %.3e/%.3e newtipfrac %.3f/%.3f\n", lt01,lt10, lt10/lt01, sm01,sm10, f01,f10)
end
