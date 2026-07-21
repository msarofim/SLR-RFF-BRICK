# VALIDATION (approach 3): with the sub-annual-crossing patch active in
# antarctic_icesheet_component.jl, the finite-diff pulse MEAN should (a) become pulse-size-robust
# (0.1 ~ 10 GtCO2) and (b) match the analytic tip-time mean from diag_analytic_pulse_mean.jl
# (transient @2100 ~1.37e-2, @2150 ~2.30e-2). If so, approach 1 is confirmed and approach 2 works.
using CSV, DataFrames, Mimi, MimiBRICK, Statistics, Printf
REPO="/Users/MarcusMarcus/Documents/2026/CodeProjects/SLR-RFF-BRICK"
FRC="/Users/MarcusMarcus/Documents/2026/CodeProjects/FaIRtoFrEDI/magicc_comparison/processed/curv_wide"
include(joinpath(REPO,"julia/brick_mengel.jl"))
Y0,Y1=1850,2150; years=collect(Y0:Y1); tidx(y)=findfirst(==(y),years); OHCS=0.1; TANT0=-15.42/0.8365
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
lw(p;s=1.0)=(d=CSV.read(p,DataFrame); keep=[y in years for y in d.year]; Matrix(d[keep,2:end]).*s)
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
tot(g,o)=(set_forcing!(m,g,o); run(m); 100 .*[x===missing ? NaN : Float64(x) for x in m[:global_sea_level,:sea_level_rise]])
N=min(150,size(gb,2),nrow(post)); q(v,p)=quantile(v,p)
for H in (2100,2150)
  hi=tidx(H); m01=Float64[]; m10=Float64[]
  for i in 1:N
    setrow(post[i,:]); tb=tot(gb[:,i],ob[:,i]); t1=tot(g01[:,i],o01[:,i]); t2=tot(g10[:,i],o10[:,i])
    push!(m01,(t1[hi]-tb[hi])/0.1); push!(m10,(t2[hi]-tb[hi])/10.0)
  end
  @printf("SUB-ANNUAL @%d (N=%d): mean 0.1GtCO2 %.3e  mean 10GtCO2 %.3e  (ratio %.2f)  median %.3e\n",
    H,N,mean(m01),mean(m10),mean(m10)/mean(m01),q(m10,.5))
end
