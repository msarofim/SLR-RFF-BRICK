# Component hindcast bands for BRICK-AM (extA108) and BRICK 2.0 (Wong post-#93) on the common
# FaIR-mean SSP2-4.5 forcing, for the walkthrough's validation figure. Per-component posterior
# p5/p50/p95, rebaselined 1995-2005 (matching outputs/recalib_targets_ext.csv). Levels only (no
# pulse) so the pristine depot is fine. Output: outputs/component_hindcast_bands.csv.
using CSV, DataFrames, Mimi, MimiBRICK, Statistics, Printf, Random
REPO="/Users/MarcusMarcus/Documents/2026/CodeProjects/SLR-RFF-BRICK"
OBS=joinpath(REPO,"data/observations")
DEPOT=joinpath(homedir(),".julia/packages/MimiBRICK/edplP/src/components/antarctic_icesheet_component.jl")
occursin("frac", read(DEPOT,String)) && error("depot is PATCHED — run this on the pristine depot")
include(joinpath(REPO,"julia/brick_mengel.jl"))
Y0,Y1=1850,2025; years=collect(Y0:Y1); tidx(y)=findfirst(==(y),years)
IREF=[tidx(y) for y in 1995:2005]; NDRAW=500
A=:antarctic_icesheet; G=:glaciers_small_icecaps; TANT0=-15.42/0.8365
lc(p,c)=(d=CSV.read(p,DataFrame); Dict(Int(d[i,"year"])=>Float64(d[i,c]) for i in 1:nrow(d)))
gm=lc(joinpath(OBS,"fair_mean_gmst_ssp245harm.csv"),"gmst_C"); oh=lc(joinpath(OBS,"fair_mean_ohc_ssp245harm.csv"),"ohc_1e22J")
gmst=[gm[y] for y in years]; ohc=[oh[y] for y in years]
COMPS=[("ais",:antarctic_icesheet,:ais_sea_level),("gis",:greenland_icesheet,:greenland_sea_level),
       ("gsic",:glaciers_small_icecaps,:gsic_sea_level),("te",:thermal_expansion,:te_sea_level),
       ("total",:global_sea_level,:sea_level_rise)]
getc(m,cn,vn)=(v=100 .*[x===missing ? NaN : Float64(x) for x in m[cn,vn]]; v .- mean(v[IREF]))
out=DataFrame(model=String[],component=String[],year=Int[],p5=Float64[],p50=Float64[],p95=Float64[])
function bands!(mlabel, model, setr!, npar)
    acc=Dict(c[1]=>[Float64[] for _ in years] for c in COMPS)   # per-year vectors
    N=min(NDRAW,npar)
    for i in 1:N
        setr!(i); run(model)
        for (nm,cn,vn) in COMPS
            v=getc(model,cn,vn); for t in eachindex(years); push!(acc[nm][t], v[t]); end
        end
        i%100==0 && (print("."); flush(stdout))
    end
    println(" $mlabel done ($N draws)")
    q(v,p)=quantile(filter(isfinite,v),p)
    for (nm,_,_) in COMPS, t in eachindex(years)
        vv=acc[nm][t]
        push!(out,(mlabel,nm,years[t],q(vv,.05),q(vv,.5),q(vv,.95)))
    end
end
# ---- BRICK-AM (extA108) ----
FREE=[("ais_ocean_temperature₀",A,:ais_ocean_temperature₀),("antarctic_alpha",A,:ais_α),("antarctic_nu",A,:ais_ν),
("antarctic_temp_threshold",A,:temperature_threshold),("anto_alpha",:antarctic_ocean,:anto_α),("anto_beta",:antarctic_ocean,:anto_β),
("greenland_a",:greenland_icesheet,:greenland_a),("greenland_b",:greenland_icesheet,:greenland_b),("greenland_alpha",:greenland_icesheet,:greenland_α),
("greenland_beta",:greenland_icesheet,:greenland_β),("greenland_v0",:greenland_icesheet,:greenland_v₀),("thermal_alpha",:thermal_expansion,:te_α),
("gic_a",G,:gic_a),("gic_b",G,:gic_b),("gic_T_lia",G,:gic_T_lia),("gic_f",G,:gic_f),("gic_tau_fast",G,:gic_tau_fast),("gic_tau_slow",G,:gic_tau_slow),
("antarctic_lambda",A,:λ),("antarctic_gamma",A,:ais_γ),("antarctic_kappa",A,:ais_κ),
("ais_mu",A,:ais_μ),("ais_bedheight0",A,:ais_bedheight₀),("ais_slope",A,:ais_slope),("ais_iceflow0",A,:ais_iceflow₀),
("ais_precip0_LOG",A,:ais_precipitation₀),("ais_c",A,:ais_c)]
FN=[f[1] for f in FREE]
M_AM=build_brick_mengel(ssp="ssp245",y0=Y0,y1=Y1)
med=CSV.read(joinpath(REPO,"outputs/recalib_central_row.csv"),DataFrame)[1,:]
update_brick_mengel!(M_AM,med,(a=0.45,b=0.52,T_lia=-0.45,f=0.5,tau_fast=40.0,tau_slow=250.0,sl0=0.0);precip_log=true)
set_forcing!(M_AM,gmst,ohc)
P_AM=CSV.read(joinpath(REPO,"data/MimiBRICK/parameters_subsample_brick_mengel_extA108.csv"),DataFrame; select=vcat(FN,["ais_runoff_Ton","ais_gmst_amp"]))
setr_am(i)=begin r=P_AM[i,:]
  for f in FREE; update_param!(M_AM,f[2],f[3],Float64(r[f[1]])); end
  update_param!(M_AM,A,:ais_runoffline_snowheight₀,-Float64(r["ais_runoff_Ton"])*Float64(r["ais_c"]))
  a=Float64(r["ais_gmst_amp"]); update_param!(M_AM,A,:ais_temperature_coefficient,1.0/a); update_param!(M_AM,A,:ais_temperature_intercept,-TANT0/a)
end
println("BRICK-AM:"); bands!("BRICK-AM",M_AM,setr_am,nrow(P_AM))
# ---- BRICK 2.0 (Wong) ----
Random.seed!(2026); M_20=MimiBRICK.get_model(ssprcp_scenario="ssp245",start_year=Y0,end_year=Y1)
set_forcing!(M_20,gmst,ohc)
P_20=CSV.read(joinpath(REPO,"data/MimiBRICK/parameters_subsample_brick.csv"),DataFrame)
setr_20(i)=update_brick_params!(M_20,P_20[i,:];precip_log=true,skip_glaciers=false)
println("BRICK 2.0:"); bands!("BRICK2.0",M_20,setr_20,nrow(P_20))
CSV.write(joinpath(REPO,"outputs/component_hindcast_bands.csv"),out)
println("wrote outputs/component_hindcast_bands.csv")
