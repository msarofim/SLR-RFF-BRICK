# Attribution ladder: BRICK2.0 -> BRICK-FM(a=1.08). Decompose the SSP2-4.5 SLR change into
# Mengel-glacier / obs+recalibration / Antarctic-amplification, per Marcus 2026-07-24
# (rough "everything else" is fine). All rungs on the SAME deterministic fair_mean SSP2-4.5
# harmonized forcing, rebaselined 1995-2014, SLR@2100/2150 median over a posterior subsample.
#
#   X0  BRICK2.0        Wong glacier + Wong post-#93 posterior, a=1.196 (get_model default)
#   XM  BRICK2.0+Mengel Wong AIS/GIS/TE (Wong posterior) + Mengel glacier (central params) -> structural Mengel
#   X2  extA6eq         our Mengel + our obs/recalibration, a=1.196
#   X3  extA108         our Mengel + our obs/recalibration, a=1.08
# Deltas: Mengel = XM-X0 ; obs+recalib = X2-XM ; amplification = X3-X2 ; total = X3-X0.
using CSV, DataFrames, Mimi, MimiBRICK, Statistics, Printf, Random
REPO="/Users/MarcusMarcus/Documents/2026/CodeProjects/SLR-RFF-BRICK"; OBS=joinpath(REPO,"data/observations")
include(joinpath(REPO,"julia/brick_mengel.jl"))          # glaciers_mengel, build_brick_mengel, set_forcing!, update_brick_params!
Y0,Y1=1850,2150; years=collect(Y0:Y1); tidx(y)=findfirst(==(y),years); IREF=[tidx(y) for y in 1995:2014]
TANT0=-15.42/0.8365; A=:antarctic_icesheet; G=:glaciers_small_icecaps; NCAP=2000
lc(p,c)=(d=CSV.read(p,DataFrame); Dict(Int(d[i,"year"])=>Float64(d[i,c]) for i in 1:nrow(d)))
gm=lc(joinpath(OBS,"fair_mean_gmst_ssp245harm.csv"),"gmst_C"); oh=lc(joinpath(OBS,"fair_mean_ohc_ssp245harm.csv"),"ohc_1e22J")
gmst=[gm[y] for y in years]; ohc=[oh[y] for y in years]
FREE=[("ais_ocean_temperature₀",A,:ais_ocean_temperature₀),("antarctic_alpha",A,:ais_α),("antarctic_nu",A,:ais_ν),
("antarctic_temp_threshold",A,:temperature_threshold),("anto_alpha",:antarctic_ocean,:anto_α),("anto_beta",:antarctic_ocean,:anto_β),
("greenland_a",:greenland_icesheet,:greenland_a),("greenland_b",:greenland_icesheet,:greenland_b),("greenland_alpha",:greenland_icesheet,:greenland_α),
("greenland_beta",:greenland_icesheet,:greenland_β),("greenland_v0",:greenland_icesheet,:greenland_v₀),("thermal_alpha",:thermal_expansion,:te_α),
("gic_a",G,:gic_a),("gic_b",G,:gic_b),("gic_T_lia",G,:gic_T_lia),("gic_f",G,:gic_f),("gic_tau_fast",G,:gic_tau_fast),("gic_tau_slow",G,:gic_tau_slow),
("antarctic_lambda",A,:λ),("antarctic_gamma",A,:ais_γ),("antarctic_kappa",A,:ais_κ),
("ais_mu",A,:ais_μ),("ais_bedheight0",A,:ais_bedheight₀),("ais_slope",A,:ais_slope),("ais_iceflow0",A,:ais_iceflow₀),
("ais_precip0_LOG",A,:ais_precipitation₀),("ais_c",A,:ais_c)]
FN=[f[1] for f in FREE]
lev(m)=(run(m); v=100 .*[x===missing ? NaN : Float64(x) for x in m[:global_sea_level,:sea_level_rise]]; rf=mean(v[IREF]); (v[tidx(2100)]-rf,v[tidx(2150)]-rf))
q(v)=quantile(filter(!isnan,v),.5)

# ---- X0 / XM: BRICK2.0 (Wong posterior). mengel_swap replaces the glacier with Mengel(central). ----
function run_brick20(; mengel_swap::Bool)
    Random.seed!(2026); m=MimiBRICK.get_model(ssprcp_scenario="ssp245",start_year=Y0,end_year=Y1)
    mengel_swap && replace!(m, G => glaciers_mengel)
    P=CSV.read(joinpath(REPO,"data/MimiBRICK/parameters_subsample_brick.csv"),DataFrame); N=min(NCAP,nrow(P))
    L=(Float64[],Float64[])
    for i in 1:N
        update_brick_params!(m,P[i,:];precip_log=true,skip_glaciers=mengel_swap)
        if mengel_swap
            for (s,v) in [(:gic_a,0.45),(:gic_b,0.52),(:gic_T_lia,-0.45),(:gic_f,0.5),(:gic_tau_fast,40.0),(:gic_tau_slow,250.0),(:gic_sl0,0.0)]
                update_param!(m,G,s,v); end
        end
        set_forcing!(m,gmst,ohc); a,b=lev(m); push!(L[1],a); push!(L[2],b)
    end; L
end
# ---- X2 / X3: our Mengel model + _ext posterior (FREE + A4 + A6) ----
function run_ext(tag)
    med=CSV.read(joinpath(REPO,"outputs/recalib_central_row.csv"),DataFrame)[1,:]
    m=build_brick_mengel(ssp="ssp245",y0=Y0,y1=Y1)
    update_brick_mengel!(m,med,(a=0.45,b=0.52,T_lia=-0.45,f=0.5,tau_fast=40.0,tau_slow=250.0,sl0=0.0);precip_log=true)
    P=CSV.read(joinpath(REPO,"data/MimiBRICK/parameters_subsample_brick_mengel_$(tag).csv"),DataFrame;select=vcat(FN,["ais_runoff_Ton","ais_gmst_amp"])); N=min(NCAP,nrow(P))
    L=(Float64[],Float64[])
    for i in 1:N
        r=P[i,:]; for f in FREE; update_param!(m,f[2],f[3],Float64(r[f[1]])); end
        update_param!(m,A,:ais_runoffline_snowheight₀,-Float64(r["ais_runoff_Ton"])*Float64(r["ais_c"]))
        a=Float64(r["ais_gmst_amp"]); update_param!(m,A,:ais_temperature_coefficient,1.0/a); update_param!(m,A,:ais_temperature_intercept,-TANT0/a)
        set_forcing!(m,gmst,ohc); x,y=lev(m); push!(L[1],x); push!(L[2],y)
    end; L
end
res=Dict{String,Any}()
for (name,f) in (("X0_BRICK2.0",()->run_brick20(mengel_swap=false)),
                 ("XM_+Mengel",()->run_brick20(mengel_swap=true)),
                 ("X2_extA6eq",()->run_ext("extA6eq")),
                 ("X3_extA108",()->run_ext("extA108")))
    t0=time(); L=f(); res[name]=(q(L[1]),q(L[2]))
    @printf("%-14s SLR@2100 %.1f  @2150 %.1f cm  (N=%d, %.0fs)\n",name,q(L[1]),q(L[2]),length(L[1]),time()-t0); flush(stdout)
end
m2100(k)=res[k][1]; m2150(k)=res[k][2]
@printf("\n=== DECOMPOSITION @2100 (cm, SSP2-4.5, median) ===\n")
@printf("  BRICK2.0 baseline            %.1f\n",m2100("X0_BRICK2.0"))
@printf("  + Mengel glacier (structural) %+.1f\n",m2100("XM_+Mengel")-m2100("X0_BRICK2.0"))
@printf("  + obs & recalibration         %+.1f\n",m2100("X2_extA6eq")-m2100("XM_+Mengel"))
@printf("  + Antarctic amp 1.196->1.08   %+.1f\n",m2100("X3_extA108")-m2100("X2_extA6eq"))
@printf("  = BRICK-FM (a=1.08)          %.1f   [total %+.1f]\n",m2100("X3_extA108"),m2100("X3_extA108")-m2100("X0_BRICK2.0"))
open(joinpath(REPO,"outputs/decomposition_ssp245.csv"),"w") do io
    println(io,"rung,slr2100,slr2150")
    for k in ("X0_BRICK2.0","XM_+Mengel","X2_extA6eq","X3_extA108"); println(io,"$k,$(m2100(k)),$(m2150(k))"); end
end
println("wrote outputs/decomposition_ssp245.csv")
