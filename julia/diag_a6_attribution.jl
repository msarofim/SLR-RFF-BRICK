# A6 attribution: SLR (level, SSP2-4.5 harmonized mean forcing) + pulse (0.1 GtCO2 ensemble)
# for the FULLY-RECALIBRATED equilibrium-amp chains (extA6eq) vs the phase-2 production
# posterior (transient amp). Isolates A6 with each posterior fit to its own amp.
using CSV, DataFrames, Mimi, MimiBRICK, Statistics, Printf
REPO="/Users/MarcusMarcus/Documents/2026/CodeProjects/SLR-RFF-BRICK"
FRC="/Users/MarcusMarcus/Documents/2026/CodeProjects/FaIRtoFrEDI/magicc_comparison/processed/curv_wide"
include(joinpath(REPO,"julia/brick_mengel.jl"))
OBS=joinpath(REPO,"data/observations")
Y0,Y1=1850,2150; years=collect(Y0:Y1); tidx(y)=findfirst(==(y),years); IREF=[tidx(y) for y in 1995:2014]
A=:antarctic_icesheet; G=:glaciers_small_icecaps; TANT0=-15.42/0.8365; PULSE=0.1; OHCS=0.1
FREE=[("ais_ocean_temperature₀",A,:ais_ocean_temperature₀),("antarctic_alpha",A,:ais_α),("antarctic_nu",A,:ais_ν),
("antarctic_temp_threshold",A,:temperature_threshold),("anto_alpha",:antarctic_ocean,:anto_α),("anto_beta",:antarctic_ocean,:anto_β),
("greenland_a",:greenland_icesheet,:greenland_a),("greenland_b",:greenland_icesheet,:greenland_b),("greenland_alpha",:greenland_icesheet,:greenland_α),
("greenland_beta",:greenland_icesheet,:greenland_β),("greenland_v0",:greenland_icesheet,:greenland_v₀),("thermal_alpha",:thermal_expansion,:te_α),
("gic_a",G,:gic_a),("gic_b",G,:gic_b),("gic_T_lia",G,:gic_T_lia),("gic_f",G,:gic_f),("gic_tau_fast",G,:gic_tau_fast),("gic_tau_slow",G,:gic_tau_slow),
("antarctic_lambda",A,:λ),("antarctic_gamma",A,:ais_γ),("antarctic_kappa",A,:ais_κ),
("ais_mu",A,:ais_μ),("ais_bedheight0",A,:ais_bedheight₀),("ais_slope",A,:ais_slope),("ais_iceflow0",A,:ais_iceflow₀),
("ais_precip0_LOG",A,:ais_precipitation₀),("ais_c",A,:ais_c)]
FN=[f[1] for f in FREE]
lc(p,c)=(d=CSV.read(p,DataFrame); Dict(Int(d[i,"year"])=>Float64(d[i,c]) for i in 1:nrow(d)))
gmst_m=[lc(joinpath(OBS,"fair_mean_gmst_ssp245harm.csv"),"gmst_C")[y] for y in years]
ohc_m =[lc(joinpath(OBS,"fair_mean_ohc_ssp245harm.csv"),"ohc_1e22J")[y] for y in years]
lw(p;s=1.0)=(d=CSV.read(p,DataFrame); keep=[y in years for y in d.year]; (Matrix(d[keep,2:end]).*s))
gb=lw(joinpath(FRC,"ssp245_gmst_base.csv")); gp=lw(joinpath(FRC,"ssp245_gmst_pulse.csv"))
ob=lw(joinpath(FRC,"ssp245_ohc_base.csv");s=OHCS); op=lw(joinpath(FRC,"ssp245_ohc_pulse.csv");s=OHCS)
med=CSV.read(joinpath(REPO,"outputs/recalib_central_row.csv"),DataFrame)[1,:]
m=build_brick_mengel(ssp="ssp245",y0=Y0,y1=Y1)
update_brick_mengel!(m,med,(a=0.45,b=0.52,T_lia=-0.45,f=0.5,tau_fast=40.0,tau_slow=250.0,sl0=0.0);precip_log=true)
setrow(r)=begin
  for f in FREE; update_param!(m,f[2],f[3],Float64(r[f[1]])); end
  update_param!(m,A,:ais_runoffline_snowheight₀, -Float64(r["ais_runoff_Ton"])*Float64(r["ais_c"]))
  a=Float64(r["ais_gmst_amp"]); update_param!(m,A,:ais_temperature_coefficient,1.0/a); update_param!(m,A,:ais_temperature_intercept,-TANT0/a)
end
# posterior loader: read a set of chains, thin post-burn, return NDRAW rows
function loadpost(paths,ndraw)
  cols=vcat(FN,["ais_runoff_Ton","ais_gmst_amp"]); rows=DataFrame()
  for p in paths
    df=CSV.read(p,DataFrame; select=cols); n=nrow(df); bi=collect((n÷2+1):((n÷2)÷(ndraw÷length(paths))):n)[1:(ndraw÷length(paths))]
    rows=vcat(rows,df[bi,:])
  end
  rows
end
q(v,p)=quantile(v,p)
for (name,paths) in (("PHASE-2 (transient amp)", [joinpath(REPO,"outputs/mcmc","chain_ext_seed$(s)_n2000000.csv") for s in 2026:2029]),
                     ("A6-EQUILIBRIUM (recalib)",[joinpath(REPO,"outputs/mcmc","chain_extA6eq_seed$(s)_n2000000.csv") for s in 2026:2029]))
  P=loadpost(paths,240); N=nrow(P)
  # LEVEL (deterministic mean forcing)
  s21=Float64[];s215=Float64[];cross=0
  for i in 1:N
    setrow(P[i,:]); set_forcing!(m,gmst_m,ohc_m); run(m)
    lev=100 .*m[:global_sea_level,:sea_level_rise]; rf=mean(lev[IREF])
    push!(s21,lev[tidx(2100)]-rf); push!(s215,lev[tidx(2150)]-rf)
    at=m[:antarctic_icesheet,:antartic_surface_temperature]; any(at[tidx(1990):tidx(2100)].>Float64(P[i,"antarctic_temp_threshold"]))&&(cross+=1)
  end
  # PULSE (ensemble forcing, paired by index)
  np=min(N,size(gb,2)); t21=Float64[];t215=Float64[]
  for i in 1:np
    setrow(P[i,:]); set_forcing!(m,gb[:,i],ob[:,i]); run(m); lb=100 .*m[:global_sea_level,:sea_level_rise]
    set_forcing!(m,gp[:,i],op[:,i]); run(m); lp=100 .*m[:global_sea_level,:sea_level_rise]
    push!(t21,(lp[tidx(2100)]-lb[tidx(2100)])/PULSE); push!(t215,(lp[tidx(2150)]-lb[tidx(2150)])/PULSE)
  end
  @printf("\n%s  (N=%d level, %d pulse):\n",name,N,np)
  @printf("  LEVEL  SLR@2100 med %.1f [%.1f,%.1f] | @2150 med %.1f | threshold crossed %d%%\n",q(s21,.5),q(s21,.05),q(s21,.95),q(s215,.5),round(Int,100cross/N))
  @printf("  PULSE  @2100 med %.3e mean %.3e | @2150 med %.3e mean %.3e cm/GtCO2\n",q(t21,.5),mean(t21),q(t215,.5),mean(t215))
end
