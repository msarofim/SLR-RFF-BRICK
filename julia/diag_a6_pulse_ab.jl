# A6-on-pulse A/B: same phase-2 draws + same 0.1 GtCO2 forcing, amp transient vs equilibrium.
# Isolates A6's DIRECT effect on the pulse marginal (holding the posterior fixed).
using CSV, DataFrames, Mimi, MimiBRICK, Statistics, Printf
REPO="/Users/MarcusMarcus/Documents/2026/CodeProjects/SLR-RFF-BRICK"
FRC="/Users/MarcusMarcus/Documents/2026/CodeProjects/FaIRtoFrEDI/magicc_comparison/processed/curv_wide"
include(joinpath(REPO,"julia/brick_mengel.jl"))
Y0,Y1=1850,2150; years=collect(Y0:Y1); tidx(y)=findfirst(==(y),years)
PULSE=0.1; OHCS=0.1; NDRAW=250; AMP_EQ=1.0/0.8365
A=:antarctic_icesheet; G=:glaciers_small_icecaps; TANT0=-15.42/0.8365
FREE=[("ais_ocean_temperature₀",A,:ais_ocean_temperature₀),("antarctic_alpha",A,:ais_α),("antarctic_nu",A,:ais_ν),
("antarctic_temp_threshold",A,:temperature_threshold),("anto_alpha",:antarctic_ocean,:anto_α),("anto_beta",:antarctic_ocean,:anto_β),
("greenland_a",:greenland_icesheet,:greenland_a),("greenland_b",:greenland_icesheet,:greenland_b),("greenland_alpha",:greenland_icesheet,:greenland_α),
("greenland_beta",:greenland_icesheet,:greenland_β),("greenland_v0",:greenland_icesheet,:greenland_v₀),("thermal_alpha",:thermal_expansion,:te_α),
("gic_a",G,:gic_a),("gic_b",G,:gic_b),("gic_T_lia",G,:gic_T_lia),("gic_f",G,:gic_f),("gic_tau_fast",G,:gic_tau_fast),("gic_tau_slow",G,:gic_tau_slow),
("antarctic_lambda",A,:λ),("antarctic_gamma",A,:ais_γ),("antarctic_kappa",A,:ais_κ),
("ais_mu",A,:ais_μ),("ais_bedheight0",A,:ais_bedheight₀),("ais_slope",A,:ais_slope),("ais_iceflow0",A,:ais_iceflow₀),
("ais_precip0_LOG",A,:ais_precipitation₀),("ais_c",A,:ais_c)]
FN=[f[1] for f in FREE]; CC=findfirst(==("ais_c"),FN)
# forcing (wide: year x member), slice to Y0:Y1
lw(p;s=1.0)=(d=CSV.read(p,DataFrame); keep=[y in years for y in d.year]; (Matrix(d[keep,2:end]).*s))
gb=lw(joinpath(FRC,"ssp245_gmst_base.csv")); gp=lw(joinpath(FRC,"ssp245_gmst_pulse.csv"))
ob=lw(joinpath(FRC,"ssp245_ohc_base.csv");s=OHCS); op=lw(joinpath(FRC,"ssp245_ohc_pulse.csv");s=OHCS)
nmem=size(gb,2)
post=CSV.read(joinpath(REPO,"data/MimiBRICK/parameters_subsample_brick_mengel_ext.csv"),DataFrame)
N=min(NDRAW,nmem,nrow(post))
med=CSV.read(joinpath(REPO,"outputs/recalib_central_row.csv"),DataFrame)[1,:]
m=build_brick_mengel(ssp="ssp245",y0=Y0,y1=Y1)
update_brick_mengel!(m,med,(a=0.45,b=0.52,T_lia=-0.45,f=0.5,tau_fast=40.0,tau_slow=250.0,sl0=0.0);precip_log=true)
setrow(r,ampval)=begin
  for (k,f) in enumerate(FREE); update_param!(m,f[2],f[3],Float64(post[r,f[1]])); end
  update_param!(m,A,:ais_runoffline_snowheight₀, -Float64(post[r,"ais_runoff_Ton"])*Float64(post[r,"ais_c"]))
  update_param!(m,A,:ais_temperature_coefficient,1.0/ampval)
  update_param!(m,A,:ais_temperature_intercept,-TANT0/ampval)
end
function run_mode(ampmode)
  tot2100=Float64[];tot2150=Float64[];ais2100=Float64[]
  for i in 1:N
    ampval = ampmode==:transient ? Float64(post[i,"ais_gmst_amp"]) : AMP_EQ
    setrow(i,ampval)
    set_forcing!(m,gb[:,i],ob[:,i]); run(m)
    lb=100 .*m[:global_sea_level,:sea_level_rise]; ab=100 .*m[:antarctic_icesheet,:ais_sea_level]
    set_forcing!(m,gp[:,i],op[:,i]); run(m)
    lp=100 .*m[:global_sea_level,:sea_level_rise]; ap=100 .*m[:antarctic_icesheet,:ais_sea_level]
    push!(tot2100,(lp[tidx(2100)]-lb[tidx(2100)])/PULSE)
    push!(tot2150,(lp[tidx(2150)]-lb[tidx(2150)])/PULSE)
    push!(ais2100,(ap[tidx(2100)]-ab[tidx(2100)])/PULSE)
  end
  (tot2100,tot2150,ais2100)
end
q(v,p)=quantile(v,p)
@printf("A6-on-PULSE A/B (%d paired draws, 0.1 GtCO2, SSP2-4.5):\n",N)
for mode in (:transient,:equilibrium)
  t21,t215,a21=run_mode(mode)
  @printf("  amp=%-11s  PULSE tot @2100 median %.3e mean %.3e | @2150 median %.3e mean %.3e | AIS-part @2100 median %.3e mean %.3e  (cm/GtCO2)\n",
    string(mode),q(t21,.5),mean(t21),q(t215,.5),mean(t215),q(a21,.5),mean(a21))
end
