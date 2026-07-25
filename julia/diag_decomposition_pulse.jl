# PULSE-marginal decomposition BRICK2.0 -> BRICK-AM, paralleling diag_decomposition.jl (which did
# GMSL levels on deterministic forcing). Same 4 rungs; here on the MAGICC ENSEMBLE (base + 10-GtCO2
# pulse) with the SUB-ANNUAL DAIS patch, so the pulse median/mean match the artifact's MAGICC column.
#   X0  BRICK2.0        Wong glacier + Wong post-#93 posterior, a=1.196 (get_model default)
#   XM  BRICK2.0+Mengel Wong AIS/GIS/TE (Wong posterior) + Mengel glacier (central) -> structural Mengel
#   X2  extA6eq         our Mengel + our obs/recalibration, a=1.196 (equilibrium)
#   X3  extA108         our Mengel + our obs/recalibration, a=1.08  == BRICK-AM
# Deltas: Mengel = XM-X0 ; obs+recalib = X2-XM ; amplification = X3-X2 ; total = X3-X0.
# Reports level-median, pulse-median, pulse-mean @2100/2150 per rung (pulse x10^-3 cm/GtCO2).
using CSV, DataFrames, Mimi, MimiBRICK, Statistics, Printf, Random
REPO="/Users/MarcusMarcus/Documents/2026/CodeProjects/SLR-RFF-BRICK"
FRC="/Users/MarcusMarcus/Documents/2026/CodeProjects/FaIRtoFrEDI/magicc_comparison/processed/curv_wide"
DEPOT=joinpath(homedir(),".julia/packages/MimiBRICK/edplP/src/components/antarctic_icesheet_component.jl")
occursin("frac", read(DEPOT,String)) || error("sub-annual patch NOT active in depot — apply it first")
include(joinpath(REPO,"julia/brick_mengel.jl"))
Y0,Y1=1850,2150; years=collect(Y0:Y1); tidx(y)=findfirst(==(y),years); IREF=[tidx(y) for y in 1995:2014]
OHCS=0.1; PULSE=10.0; TANT0=-15.42/0.8365; A=:antarctic_icesheet; G=:glaciers_small_icecaps
lw(p;s=1.0)=(d=CSV.read(p,DataFrame); keep=[y in years for y in d.year]; Matrix(d[keep,2:end]).*s)
q(v,p)=quantile(filter(!isnan,v),p)
# MAGICC ensemble forcing (base + 10-GtCO2 pulse)
GB=lw(joinpath(FRC,"ssp245_gmst_base.csv")); OB=lw(joinpath(FRC,"ssp245_ohc_base.csv");s=OHCS)
GP=lw(joinpath(FRC,"ssp245_gmst_pulse10gt.csv")); OP=lw(joinpath(FRC,"ssp245_ohc_pulse10gt.csv");s=OHCS)
NF=size(GB,2)
slr(m)=(run(m); 100 .*[x===missing ? NaN : Float64(x) for x in m[:global_sea_level,:sea_level_rise]])
# per-rung: returns (levelmed, pulsemed, pulsemean) for @2100 and @2150
function tally(setforcing_and_run!)  # closure sets params for draw i and returns per-draw (levelvec,pulsevec)
    LV=Dict(y=>Float64[] for y in (2100,2150)); PM=Dict(y=>Float64[] for y in (2100,2150))
    setforcing_and_run!(LV,PM)
    Dict(y=>(q(LV[y],.5), 1e3*q(PM[y],.5), 1e3*mean(filter(!isnan,PM[y]))) for y in (2100,2150))
end

FREE=[("ais_ocean_temperature₀",A,:ais_ocean_temperature₀),("antarctic_alpha",A,:ais_α),("antarctic_nu",A,:ais_ν),
("antarctic_temp_threshold",A,:temperature_threshold),("anto_alpha",:antarctic_ocean,:anto_α),("anto_beta",:antarctic_ocean,:anto_β),
("greenland_a",:greenland_icesheet,:greenland_a),("greenland_b",:greenland_icesheet,:greenland_b),("greenland_alpha",:greenland_icesheet,:greenland_α),
("greenland_beta",:greenland_icesheet,:greenland_β),("greenland_v0",:greenland_icesheet,:greenland_v₀),("thermal_alpha",:thermal_expansion,:te_α),
("gic_a",G,:gic_a),("gic_b",G,:gic_b),("gic_T_lia",G,:gic_T_lia),("gic_f",G,:gic_f),("gic_tau_fast",G,:gic_tau_fast),("gic_tau_slow",G,:gic_tau_slow),
("antarctic_lambda",A,:λ),("antarctic_gamma",A,:ais_γ),("antarctic_kappa",A,:ais_κ),
("ais_mu",A,:ais_μ),("ais_bedheight0",A,:ais_bedheight₀),("ais_slope",A,:ais_slope),("ais_iceflow0",A,:ais_iceflow₀),
("ais_precip0_LOG",A,:ais_precipitation₀),("ais_c",A,:ais_c)]
FN=[f[1] for f in FREE]

# X0 / XM: BRICK2.0 (Wong posterior). mengel_swap replaces the glacier with Mengel(central).
function run_brick20(; mengel_swap::Bool)
    Random.seed!(2026); m=MimiBRICK.get_model(ssprcp_scenario="ssp245",start_year=Y0,end_year=Y1)
    mengel_swap && replace!(m, G => glaciers_mengel)
    P=CSV.read(joinpath(REPO,"data/MimiBRICK/parameters_subsample_brick.csv"),DataFrame); N=min(NF,nrow(P))
    tally() do LV,PM
        for i in 1:N
            update_brick_params!(m,P[i,:];precip_log=true,skip_glaciers=mengel_swap)
            if mengel_swap
                for (s,v) in [(:gic_a,0.45),(:gic_b,0.52),(:gic_T_lia,-0.45),(:gic_f,0.5),(:gic_tau_fast,40.0),(:gic_tau_slow,250.0),(:gic_sl0,0.0)]
                    update_param!(m,G,s,v); end
            end
            set_forcing!(m,GB[:,i],OB[:,i]); lb=slr(m); set_forcing!(m,GP[:,i],OP[:,i]); lp=slr(m); rf=mean(lb[IREF])
            for y in (2100,2150); push!(LV[y],lb[tidx(y)]-rf); push!(PM[y],(lp[tidx(y)]-lb[tidx(y)])/PULSE); end
            i%150==0 && (print("."); flush(stdout))
        end; println()
    end
end
# X2 / X3: our Mengel model + _ext posterior
function run_ext(tag)
    med=CSV.read(joinpath(REPO,"outputs/recalib_central_row.csv"),DataFrame)[1,:]
    m=build_brick_mengel(ssp="ssp245",y0=Y0,y1=Y1)
    update_brick_mengel!(m,med,(a=0.45,b=0.52,T_lia=-0.45,f=0.5,tau_fast=40.0,tau_slow=250.0,sl0=0.0);precip_log=true)
    P=CSV.read(joinpath(REPO,"data/MimiBRICK/parameters_subsample_brick_mengel_$(tag).csv"),DataFrame;select=vcat(FN,["ais_runoff_Ton","ais_gmst_amp"])); N=min(NF,nrow(P))
    tally() do LV,PM
        for i in 1:N
            r=P[i,:]; for f in FREE; update_param!(m,f[2],f[3],Float64(r[f[1]])); end
            update_param!(m,A,:ais_runoffline_snowheight₀,-Float64(r["ais_runoff_Ton"])*Float64(r["ais_c"]))
            a=Float64(r["ais_gmst_amp"]); update_param!(m,A,:ais_temperature_coefficient,1.0/a); update_param!(m,A,:ais_temperature_intercept,-TANT0/a)
            set_forcing!(m,GB[:,i],OB[:,i]); lb=slr(m); set_forcing!(m,GP[:,i],OP[:,i]); lp=slr(m); rf=mean(lb[IREF])
            for y in (2100,2150); push!(LV[y],lb[tidx(y)]-rf); push!(PM[y],(lp[tidx(y)]-lb[tidx(y)])/PULSE); end
            i%150==0 && (print("."); flush(stdout))
        end; println()
    end
end

res=Dict{String,Any}()
for (name,f) in (("X0_BRICK2.0",()->run_brick20(mengel_swap=false)),
                 ("XM_+Mengel",()->run_brick20(mengel_swap=true)),
                 ("X2_extA6eq",()->run_ext("extA6eq")),
                 ("X3_extA108",()->run_ext("extA108")))
    t0=time(); res[name]=f()
    for y in (2100,2150)
        lm,pmed,pmn=res[name][y]
        @printf("%-14s @%d  LEVEL med %.1f | PULSE med %.2f mean %.2f\n",name,y,lm,pmed,pmn)
    end
    @printf("  (%.0fs)\n",time()-t0); flush(stdout)
end

out=DataFrame(year=Int[],stat=String[],X0=Float64[],Mengel=Float64[],obs_recalib=Float64[],amplification=Float64[],X3=Float64[],total=Float64[])
si=Dict("level_median"=>1,"pulse_median"=>2,"pulse_mean"=>3)
for y in (2100,2150)
    println("\n=== DECOMPOSITION @$y (BRICK2.0 -> BRICK-AM) ===")
    for (sname,idx) in [("level_median",1),("pulse_median",2),("pulse_mean",3)]
        x0=res["X0_BRICK2.0"][y][idx]; xm=res["XM_+Mengel"][y][idx]; x2=res["X2_extA6eq"][y][idx]; x3=res["X3_extA108"][y][idx]
        me=xm-x0; ob=x2-xm; am=x3-x2; tot=x3-x0
        unit = sname=="level_median" ? "cm" : "x10^-3 cm/GtCO2"
        @printf("  %-13s  X0 %.2f  +Mengel %+.2f  +obs/recal %+.2f  +amp %+.2f  = %.2f  [total %+.2f, amp=%.0f%%] %s\n",
            sname,x0,me,ob,am,x3,tot,100*am/tot,unit)
        push!(out,(y,sname,x0,me,ob,am,x3,tot))
    end
end
CSV.write(joinpath(REPO,"outputs/decomposition_pulse.csv"),out)
println("\nwrote outputs/decomposition_pulse.csv")
