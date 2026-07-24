# BRICK2.0 (Wong glacier, post-#93 Wong posterior, a=1.196 equilibrium) cross-model numbers
# for the artifact's 2nd row, matching diag_subannual_pulse_means.jl: level median/mean and
# sub-annual pulse median/mean @2100/2150, both MAGICC and FaIR drivers, rel. 1995-2014.
# REQUIRES the sub-annual depot patch active. Pulse reported by MEAN in the artifact (the
# median is not driver-comparable under FaIR stochastic forcing — see diag_a108_pulse_smoothforce).
using CSV, DataFrames, Mimi, MimiBRICK, Statistics, Printf, Random
REPO="/Users/MarcusMarcus/Documents/2026/CodeProjects/SLR-RFF-BRICK"
FRC="/Users/MarcusMarcus/Documents/2026/CodeProjects/FaIRtoFrEDI/magicc_comparison/processed/curv_wide"
DEPOT=joinpath(homedir(),".julia/packages/MimiBRICK/edplP/src/components/antarctic_icesheet_component.jl")
occursin("frac", read(DEPOT,String)) || error("sub-annual patch NOT active")
include(joinpath(REPO,"julia/brick_mengel.jl"))   # for update_brick_params!, set_forcing!
Y0,Y1=1850,2150; years=collect(Y0:Y1); tidx(y)=findfirst(==(y),years); IREF=[tidx(y) for y in 1995:2014]
OHCS=0.1; PULSE=10.0
lw(p;s=1.0)=(d=CSV.read(p,DataFrame); keep=[y in years for y in d.year]; Matrix(d[keep,2:end]).*s)
P=CSV.read(joinpath(REPO,"data/MimiBRICK/parameters_subsample_brick.csv"),DataFrame)   # Wong posterior
Random.seed!(2026); m=MimiBRICK.get_model(ssprcp_scenario="ssp245",start_year=Y0,end_year=Y1)  # BRICK2.0, no Mengel
runf(g,o)=(set_forcing!(m,g,o); run(m); 100 .*[x===missing ? NaN : Float64(x) for x in m[:global_sea_level,:sea_level_rise]])
drivers=Dict("MAGICC"=>("ssp245_gmst_base.csv","ssp245_ohc_base.csv","ssp245_gmst_pulse10gt.csv","ssp245_ohc_pulse10gt.csv"),
             "FaIR"=>("fair_gmst_base_wide.csv","fair_ohc_base_wide.csv","fair_gmst_pulse_wide.csv","fair_ohc_pulse_wide.csv"))
q(v,p)=quantile(filter(!isnan,v),p)
out=DataFrame(driver=String[],year=Int[],N=Int[],level_median=Float64[],level_mean=Float64[],pulse_median=Float64[],pulse_mean=Float64[])
for dn in ("MAGICC","FaIR")
    gbf,obf,gpf,opf=drivers[dn]
    gb=lw(joinpath(FRC,gbf)); ob=lw(joinpath(FRC,obf);s=OHCS); gp=lw(joinpath(FRC,gpf)); op=lw(joinpath(FRC,opf);s=OHCS)
    N=min(size(gb,2),nrow(P))
    L=Dict(y=>Float64[] for y in (2100,2150)); PM=Dict(y=>Float64[] for y in (2100,2150))
    for i in 1:N
        update_brick_params!(m,P[i,:];precip_log=true,skip_glaciers=false)   # Wong mapping, a=1.196 default
        lb=runf(gb[:,i],ob[:,i]); rf=mean(lb[IREF]); lp=runf(gp[:,i],op[:,i])
        for y in (2100,2150); push!(L[y],lb[tidx(y)]-rf); push!(PM[y],(lp[tidx(y)]-lb[tidx(y)])/PULSE); end
        i%150==0 && (println("  $dn $i/$N"); flush(stdout))
    end
    for y in (2100,2150)
        push!(out,(dn,y,N,q(L[y],.5),mean(filter(!isnan,L[y])),q(PM[y],.5),mean(filter(!isnan,PM[y]))))
        @printf("BRICK2.0 %-6s @%d (N=%d): LEVEL med %.1f mean %.1f | PULSE med %.3e mean %.3e (x10^-3: %.2f/%.2f)\n",
            dn,y,N,q(L[y],.5),mean(filter(!isnan,L[y])),q(PM[y],.5),mean(filter(!isnan,PM[y])),1e3*q(PM[y],.5),1e3*mean(filter(!isnan,PM[y]))); flush(stdout)
    end
end
CSV.write(joinpath(REPO,"outputs/brick20_crossmodel.csv"),out)
println("wrote outputs/brick20_crossmodel.csv")
