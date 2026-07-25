# Diagnose the BRICK GMSL mean/median gap (Marcus 2026-07-24): the level mean~median despite
# Antarctic tipping. Distinguish BUG (high-SLR tipping draws dropped as non-finite -> tail clipped)
# from PHYSICS (DAIS disintegration is a fixed-RATE ramp; at high amplification most draws tip so
# non-tippers form a LEFT tail -> mean<=median genuine). Dumps full quantiles + non-finite count +
# skew for TOTAL GMSL and the AIS component alone, BRICK-AM & BRICK2.0, MAGICC & FaIR(stochastic).
# Runs on the PRISTINE depot (levels move <1% under the sub-annual patch; shape question is robust).
using CSV, DataFrames, Mimi, MimiBRICK, Statistics, Printf, Random
REPO="/Users/MarcusMarcus/Documents/2026/CodeProjects/SLR-RFF-BRICK"
FRC="/Users/MarcusMarcus/Documents/2026/CodeProjects/FaIRtoFrEDI/magicc_comparison/processed/curv_wide"
DEPOT=joinpath(homedir(),".julia/packages/MimiBRICK/edplP/src/components/antarctic_icesheet_component.jl")
occursin("frac", read(DEPOT,String)) && error("depot is PATCHED — run this on the pristine depot")
include(joinpath(REPO,"julia/brick_mengel.jl"))
Y0,Y1=1850,2150; years=collect(Y0:Y1); tidx(y)=findfirst(==(y),years); IREF=[tidx(y) for y in 1995:2014]
OHCS=0.1; TANT0=-15.42/0.8365; A=:antarctic_icesheet; G=:glaciers_small_icecaps
lw(p;s=1.0)=(d=CSV.read(p,DataFrame); keep=[y in years for y in d.year]; Matrix(d[keep,2:end]).*s)
finite(v)=filter(isfinite,v)
skew(v)=(x=finite(v); m=mean(x); s=std(x); mean(((x.-m)./s).^3))
function report(tag, tot, ais)  # per-draw vectors (cm anomaly) @ one horizon
    n=length(tot); nnf=count(!isfinite,tot); ft=finite(tot); fa=finite(ais)
    Q(v,p)=quantile(v,p)
    @printf("%-22s N=%d nonfinite=%d | TOTAL q05 %.1f q25 %.1f MED %.1f MEAN %.1f q75 %.1f q95 %.1f q99 %.1f max %.1f skew %+.2f\n",
        tag,n,nnf,Q(ft,.05),Q(ft,.25),Q(ft,.5),mean(ft),Q(ft,.75),Q(ft,.95),Q(ft,.99),maximum(ft),skew(ft))
    @printf("%-22s          AIS-only: MED %.1f MEAN %.1f q95 %.1f q99 %.1f max %.1f skew %+.2f | frac(AIS>MED+2cm)=%.2f\n",
        "",Q(fa,.5),mean(fa),Q(fa,.95),Q(fa,.99),maximum(fa),skew(fa),count(x->x>Q(fa,.5)+2,fa)/length(fa)); flush(stdout)
    (tag=tag,N=n,nonfinite=nnf,med=Q(ft,.5),mean=mean(ft),q95=Q(ft,.95),q99=Q(ft,.99),max=maximum(ft),skew=skew(ft),
     ais_med=Q(fa,.5),ais_mean=mean(fa),ais_q95=Q(fa,.95),ais_max=maximum(fa),ais_skew=skew(fa))
end
drivers=[("MAGICC","ssp245_gmst_base.csv","ssp245_ohc_base.csv"),
         ("FaIR","fair_gmst_base_wide.csv","fair_ohc_base_wide.csv")]
rows=NamedTuple[]

function sweep!(mlabel, model, setr!, npar)
    for (dn,gf,of) in drivers
        g=lw(joinpath(FRC,gf)); o=lw(joinpath(FRC,of);s=OHCS); N=min(size(g,2),npar)
        TOT=Dict(y=>Float64[] for y in (2100,2150)); AIS=Dict(y=>Float64[] for y in (2100,2150))
        for i in 1:N
            setr!(i)
            set_forcing!(model,g[:,i],o[:,i]); run(model)
            tv=[x===missing ? NaN : 100*Float64(x) for x in model[:global_sea_level,:sea_level_rise]]
            av=[x===missing ? NaN : 100*Float64(x) for x in model[:antarctic_icesheet,:ais_sea_level]]
            rt=mean(tv[IREF]); ra=mean(av[IREF])
            for y in (2100,2150); push!(TOT[y],tv[tidx(y)]-rt); push!(AIS[y],av[tidx(y)]-ra); end
            i%150==0 && (print("."); flush(stdout))
        end
        println()
        for y in (2100,2150); push!(rows,report("$mlabel $dn @$y",TOT[y],AIS[y])); end
    end
end

# BRICK-AM (a=1.08)
FREE=[("ais_ocean_temperature₀",A,:ais_ocean_temperature₀),("antarctic_alpha",A,:ais_α),("antarctic_nu",A,:ais_ν),
("antarctic_temp_threshold",A,:temperature_threshold),("anto_alpha",:antarctic_ocean,:anto_α),("anto_beta",:antarctic_ocean,:anto_β),
("greenland_a",:greenland_icesheet,:greenland_a),("greenland_b",:greenland_icesheet,:greenland_b),("greenland_alpha",:greenland_icesheet,:greenland_α),
("greenland_beta",:greenland_icesheet,:greenland_β),("greenland_v0",:greenland_icesheet,:greenland_v₀),("thermal_alpha",:thermal_expansion,:te_α),
("gic_a",G,:gic_a),("gic_b",G,:gic_b),("gic_T_lia",G,:gic_T_lia),("gic_f",G,:gic_f),("gic_tau_fast",G,:gic_tau_fast),("gic_tau_slow",G,:gic_tau_slow),
("antarctic_lambda",A,:λ),("antarctic_gamma",A,:ais_γ),("antarctic_kappa",A,:ais_κ),
("ais_mu",A,:ais_μ),("ais_bedheight0",A,:ais_bedheight₀),("ais_slope",A,:ais_slope),("ais_iceflow0",A,:ais_iceflow₀),
("ais_precip0_LOG",A,:ais_precipitation₀),("ais_c",A,:ais_c)]
FN=[f[1] for f in FREE]; DCOL=["ais_runoff_Ton","ais_gmst_amp"]
M_AM=build_brick_mengel(ssp="ssp245",y0=Y0,y1=Y1)
med=CSV.read(joinpath(REPO,"outputs/recalib_central_row.csv"),DataFrame)[1,:]
update_brick_mengel!(M_AM,med,(a=0.45,b=0.52,T_lia=-0.45,f=0.5,tau_fast=40.0,tau_slow=250.0,sl0=0.0);precip_log=true)
P_AM=CSV.read(joinpath(REPO,"data/MimiBRICK/parameters_subsample_brick_mengel_extA108.csv"),DataFrame; select=vcat(FN,DCOL))
setr_am(i)=begin r=P_AM[i,:]
  for f in FREE; update_param!(M_AM,f[2],f[3],Float64(r[f[1]])); end
  update_param!(M_AM,A,:ais_runoffline_snowheight₀,-Float64(r["ais_runoff_Ton"])*Float64(r["ais_c"]))
  a=Float64(r["ais_gmst_amp"]); update_param!(M_AM,A,:ais_temperature_coefficient,1.0/a); update_param!(M_AM,A,:ais_temperature_intercept,-TANT0/a)
end
println("=== BRICK-AM (a=1.08) ==="); sweep!("BRICK-AM",M_AM,setr_am,nrow(P_AM))

# BRICK 2.0 (Wong)
Random.seed!(2026); M_20=MimiBRICK.get_model(ssprcp_scenario="ssp245",start_year=Y0,end_year=Y1)
P_20=CSV.read(joinpath(REPO,"data/MimiBRICK/parameters_subsample_brick.csv"),DataFrame)
setr_20(i)=update_brick_params!(M_20,P_20[i,:];precip_log=true,skip_glaciers=false)
println("=== BRICK 2.0 (Wong, a=1.196) ==="); sweep!("BRICK2.0",M_20,setr_20,nrow(P_20))

CSV.write(joinpath(REPO,"outputs/brick_level_distribution.csv"),DataFrame(rows))
println("wrote outputs/brick_level_distribution.csv")
