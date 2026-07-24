# Focused diagnostic: WHY does the a=1.08 BRICK pulse MEDIAN differ ~2x between MAGICC and
# FaIR drivers, when the tipped fraction, crossing timing and pulse ΔGMST are all driver-
# consistent (and the annual-step median was driver-consistent too)? Dump the per-draw
# sub-annual pulse marginal @2100 for both drivers so the distributions can be compared
# directly. REQUIRES the sub-annual depot patch active (aborts otherwise).
using CSV, DataFrames, Mimi, MimiBRICK, Statistics, Printf
REPO="/Users/MarcusMarcus/Documents/2026/CodeProjects/SLR-RFF-BRICK"
FRC="/Users/MarcusMarcus/Documents/2026/CodeProjects/FaIRtoFrEDI/magicc_comparison/processed/curv_wide"
DEPOT_AIS=joinpath(homedir(),".julia/packages/MimiBRICK/edplP/src/components/antarctic_icesheet_component.jl")
occursin("frac", read(DEPOT_AIS,String)) || error("sub-annual patch NOT active — apply it first")
include(joinpath(REPO,"julia/brick_mengel.jl"))
Y0,Y1=1850,2150; years=collect(Y0:Y1); tidx(y)=findfirst(==(y),years); OHCS=0.1; PULSE=10.0; TANT0=-15.42/0.8365
A=:antarctic_icesheet; G=:glaciers_small_icecaps
FREE=[("ais_ocean_temperature₀",A,:ais_ocean_temperature₀),("antarctic_alpha",A,:ais_α),("antarctic_nu",A,:ais_ν),
("antarctic_temp_threshold",A,:temperature_threshold),("anto_alpha",:antarctic_ocean,:anto_α),("anto_beta",:antarctic_ocean,:anto_β),
("greenland_a",:greenland_icesheet,:greenland_a),("greenland_b",:greenland_icesheet,:greenland_b),("greenland_alpha",:greenland_icesheet,:greenland_α),
("greenland_beta",:greenland_icesheet,:greenland_β),("greenland_v0",:greenland_icesheet,:greenland_v₀),("thermal_alpha",:thermal_expansion,:te_α),
("gic_a",G,:gic_a),("gic_b",G,:gic_b),("gic_T_lia",G,:gic_T_lia),("gic_f",G,:gic_f),("gic_tau_fast",G,:gic_tau_fast),("gic_tau_slow",G,:gic_tau_slow),
("antarctic_lambda",A,:λ),("antarctic_gamma",A,:ais_γ),("antarctic_kappa",A,:ais_κ),
("ais_mu",A,:ais_μ),("ais_bedheight0",A,:ais_bedheight₀),("ais_slope",A,:ais_slope),("ais_iceflow0",A,:ais_iceflow₀),
("ais_precip0_LOG",A,:ais_precipitation₀),("ais_c",A,:ais_c)]
FN=[f[1] for f in FREE]; DCOL=["ais_runoff_Ton","ais_gmst_amp"]
lw(p;s=1.0)=(d=CSV.read(p,DataFrame); keep=[y in years for y in d.year]; Matrix(d[keep,2:end]).*s)
P=CSV.read(joinpath(REPO,"data/MimiBRICK/parameters_subsample_brick_mengel_extA108.csv"),DataFrame; select=vcat(FN,DCOL))
med=CSV.read(joinpath(REPO,"outputs/recalib_central_row.csv"),DataFrame)[1,:]
m=build_brick_mengel(ssp="ssp245",y0=Y0,y1=Y1)
update_brick_mengel!(m,med,(a=0.45,b=0.52,T_lia=-0.45,f=0.5,tau_fast=40.0,tau_slow=250.0,sl0=0.0);precip_log=true)
setrow(r)=begin
  for f in FREE; update_param!(m,f[2],f[3],Float64(r[f[1]])); end
  update_param!(m,A,:ais_runoffline_snowheight₀,-Float64(r["ais_runoff_Ton"])*Float64(r["ais_c"]))
  a=Float64(r["ais_gmst_amp"]); update_param!(m,A,:ais_temperature_coefficient,1.0/a); update_param!(m,A,:ais_temperature_intercept,-TANT0/a)
end
f64(v)=[x===missing ? NaN : Float64(x) for x in v]
runlv(g,o)=(set_forcing!(m,g,o); run(m); 100 .*f64(m[:global_sea_level,:sea_level_rise]))
drivers=Dict("MAGICC"=>("ssp245_gmst_base.csv","ssp245_ohc_base.csv","ssp245_gmst_pulse10gt.csv","ssp245_ohc_pulse10gt.csv"),
             "FaIR"=>("fair_gmst_base_wide.csv","fair_ohc_base_wide.csv","fair_gmst_pulse_wide.csv","fair_ohc_pulse_wide.csv"))
hi=tidx(2100)
rows=DataFrame(driver=String[],draw=Int[],pm=Float64[],ais_base=Float64[],ais_pulse=Float64[])
for dn in ("MAGICC","FaIR")
  gbf,obf,gpf,opf=drivers[dn]
  gb=lw(joinpath(FRC,gbf)); ob=lw(joinpath(FRC,obf);s=OHCS); gp=lw(joinpath(FRC,gpf)); op=lw(joinpath(FRC,opf);s=OHCS)
  N=min(size(gb,2),nrow(P))
  for i in 1:N
    setrow(P[i,:])
    set_forcing!(m,gb[:,i],ob[:,i]); run(m); aisb=100*f64(m[A,:ais_sea_level])[hi]; lb=100*f64(m[:global_sea_level,:sea_level_rise])[hi]
    set_forcing!(m,gp[:,i],op[:,i]); run(m); aisp=100*f64(m[A,:ais_sea_level])[hi]; lp=100*f64(m[:global_sea_level,:sea_level_rise])[hi]
    push!(rows,(dn,i,(lp-lb)/PULSE,aisb,aisp))
    i%150==0 && (println("  $dn $i/$N"); flush(stdout))
  end
  pm=rows[rows.driver.==dn,:pm]
  @printf("%-6s @2100 (N=%d): pulse med %.3e mean %.3e | frac|pm|<1e-4: %.0f%% | q25 %.3e q75 %.3e | max %.3e\n",
    dn,length(pm),median(pm),mean(pm),100*mean(abs.(pm).<1e-4),quantile(pm,.25),quantile(pm,.75),maximum(pm))
end
CSV.write(joinpath(REPO,"outputs/diag_a108_pulse_perdraw.csv"),rows)
println("wrote outputs/diag_a108_pulse_perdraw.csv")
