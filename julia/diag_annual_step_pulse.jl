# Before/after the sub-annual DAIS correction: annual-step pulse mean+median for BRICK-AM and
# BRICK2.0 (MAGICC + FaIR-stochastic, canonical forcing). Compare to the sub-annual values in
# outputs/nonoise_pulse_median.csv (its MAGICC + FaIR_stoch rows are the PATCHED numbers) to
# quantify whether the sub-annual update is what lifted BRICK's pulse marginal up to MAGICC-native
# levels (Marcus 2026-07-24: "MAGICC used to be the only pulse outlier"). Runs on the PRISTINE depot.
using CSV, DataFrames, Mimi, MimiBRICK, Statistics, Printf, Random
REPO="/Users/MarcusMarcus/Documents/2026/CodeProjects/SLR-RFF-BRICK"
FRC="/Users/MarcusMarcus/Documents/2026/CodeProjects/FaIRtoFrEDI/magicc_comparison/processed/curv_wide"
DEPOT=joinpath(homedir(),".julia/packages/MimiBRICK/edplP/src/components/antarctic_icesheet_component.jl")
occursin("frac", read(DEPOT,String)) && error("depot is PATCHED — this must run on the PRISTINE (annual-step) depot")
include(joinpath(REPO,"julia/brick_mengel.jl"))
Y0,Y1=1850,2150; years=collect(Y0:Y1); tidx(y)=findfirst(==(y),years); IREF=[tidx(y) for y in 1995:2014]
OHCS=0.1; PULSE=10.0; TANT0=-15.42/0.8365; A=:antarctic_icesheet; G=:glaciers_small_icecaps
lw(p;s=1.0)=(d=CSV.read(p,DataFrame); keep=[y in years for y in d.year]; Matrix(d[keep,2:end]).*s)
q(v,p)=quantile(filter(!isnan,v),p)
drivers=[("MAGICC","ssp245_gmst_base.csv","ssp245_ohc_base.csv","ssp245_gmst_pulse10gt.csv","ssp245_ohc_pulse10gt.csv"),
         ("FaIR_stoch","fair_gmst_base_wide.csv","fair_ohc_base_wide.csv","fair_gmst_pulse_wide.csv","fair_ohc_pulse_wide.csv")]
out=DataFrame(model=String[],driver=String[],year=Int[],N=Int[],pulse_median=Float64[],pulse_mean=Float64[])
function sweep!(mlabel, model, setr!, npar)
    for (dn,gbf,obf,gpf,opf) in drivers
        gb=lw(joinpath(FRC,gbf)); ob=lw(joinpath(FRC,obf);s=OHCS); gp=lw(joinpath(FRC,gpf)); op=lw(joinpath(FRC,opf);s=OHCS)
        N=min(size(gb,2),npar); PM=Dict(y=>Float64[] for y in (2100,2150))
        for i in 1:N
            setr!(i)
            lb=(set_forcing!(model,gb[:,i],ob[:,i]); run(model); 100 .*[x===missing ? NaN : Float64(x) for x in model[:global_sea_level,:sea_level_rise]])
            lp=(set_forcing!(model,gp[:,i],op[:,i]); run(model); 100 .*[x===missing ? NaN : Float64(x) for x in model[:global_sea_level,:sea_level_rise]])
            for y in (2100,2150); push!(PM[y],(lp[tidx(y)]-lb[tidx(y)])/PULSE); end
            i%150==0 && (print("."); flush(stdout))
        end
        println()
        for y in (2100,2150)
            push!(out,(mlabel,dn,y,N,1e3*q(PM[y],.5),1e3*mean(filter(!isnan,PM[y]))))
            @printf("  ANNUAL-STEP %-9s %-10s @%d: pulse median %.2f mean %.2f (x10^-3 cm/GtCO2)\n",
                mlabel,dn,y,1e3*q(PM[y],.5),1e3*mean(filter(!isnan,PM[y]))); flush(stdout)
        end
    end
end
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
println("=== BRICK-AM (a=1.08) — ANNUAL STEP ==="); sweep!("BRICK-AM",M_AM,setr_am,nrow(P_AM))
Random.seed!(2026); M_20=MimiBRICK.get_model(ssprcp_scenario="ssp245",start_year=Y0,end_year=Y1)
P_20=CSV.read(joinpath(REPO,"data/MimiBRICK/parameters_subsample_brick.csv"),DataFrame)
setr_20(i)=update_brick_params!(M_20,P_20[i,:];precip_log=true,skip_glaciers=false)
println("=== BRICK 2.0 (Wong) — ANNUAL STEP ==="); sweep!("BRICK2.0",M_20,setr_20,nrow(P_20))
CSV.write(joinpath(REPO,"outputs/annual_step_pulse.csv"),out)
println("wrote outputs/annual_step_pulse.csv")
