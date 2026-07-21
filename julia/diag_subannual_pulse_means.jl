# Artifact pulse-MEAN column: finite-diff 10 GtCO2 pulse means under the SUB-ANNUAL
# DAIS-crossing patch (approach 2, validated vs the analytic tip-time mean 2026-07-21),
# for {transient, equilib} x {MAGICC, FaIR} @ {2100, 2150}. Also reports pulse medians
# and level med/mean as cross-checks against the annual-step artifact numbers (medians
# and levels must move only ~1% — the quantization bias sits in the pulse MEAN).
# REQUIRES the depot antarctic_icesheet_component.jl to be patched (frac sub-annual
# crossing) BEFORE launch; aborts if the patch is absent.
# Side effect: writes data/MimiBRICK/parameters_subsample_brick_mengel_extA6eq.csv once
# (loadpost-identical thinning of the 4 A6eq chains) so equilib runs are reproducible.
using CSV, DataFrames, Mimi, MimiBRICK, Statistics, Printf
REPO="/Users/MarcusMarcus/Documents/2026/CodeProjects/SLR-RFF-BRICK"
FRC="/Users/MarcusMarcus/Documents/2026/CodeProjects/FaIRtoFrEDI/magicc_comparison/processed/curv_wide"
DEPOT_AIS=joinpath(homedir(),".julia/packages/MimiBRICK/edplP/src/components/antarctic_icesheet_component.jl")
occursin("frac", read(DEPOT_AIS,String)) || error("sub-annual patch NOT active in depot component — apply it first")
include(joinpath(REPO,"julia/brick_mengel.jl"))
Y0,Y1=1850,2150; years=collect(Y0:Y1); tidx(y)=findfirst(==(y),years); IREF=[tidx(y) for y in 1995:2014]
OHCS=0.1; PULSE=10.0; TANT0=-15.42/0.8365
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

# ---- equilib posterior subsample: write once with the EXACT loadpost thinning (2500/chain,
# post-burn second half, chains concatenated in seed order) so prefix-N draws reproduce the
# published artifact pairing. 39 param columns (bookkeeping cols dropped), like the transient CSV.
EQCSV=joinpath(REPO,"data/MimiBRICK/parameters_subsample_brick_mengel_extA6eq.csv")
PARAMCOLS=String.(split(readline(joinpath(REPO,"data/MimiBRICK/parameters_subsample_brick_mengel_ext.csv")),","))
function write_eq_subsample(out_csv, paramcols; ndraw=10000)
    println("writing equilib subsample CSV: $out_csv"); flush(stdout)
    paths=[joinpath(REPO,"outputs/mcmc","chain_extA6eq_seed$(s)_n2000000.csv") for s in 2026:2029]
    rows=DataFrame()
    for p in paths
        df=CSV.read(p,DataFrame; select=paramcols); n=nrow(df)
        step=max(1,(n÷2)÷(ndraw÷length(paths))); bi=collect((n÷2+1):step:n)[1:(ndraw÷length(paths))]
        rows=vcat(rows,df[bi,:]); df=nothing; GC.gc()
        println("  thinned $(basename(p))"); flush(stdout)
    end
    CSV.write(out_csv,rows)
end
isfile(EQCSV) || write_eq_subsample(EQCSV, PARAMCOLS)

lw(p;s=1.0)=(d=CSV.read(p,DataFrame); keep=[y in years for y in d.year]; Matrix(d[keep,2:end]).*s)
med=CSV.read(joinpath(REPO,"outputs/recalib_central_row.csv"),DataFrame)[1,:]
m=build_brick_mengel(ssp="ssp245",y0=Y0,y1=Y1)
update_brick_mengel!(m,med,(a=0.45,b=0.52,T_lia=-0.45,f=0.5,tau_fast=40.0,tau_slow=250.0,sl0=0.0);precip_log=true)
setrow(r)=begin
  for f in FREE; update_param!(m,f[2],f[3],Float64(r[f[1]])); end
  update_param!(m,A,:ais_runoffline_snowheight₀,-Float64(r["ais_runoff_Ton"])*Float64(r["ais_c"]))
  a=Float64(r["ais_gmst_amp"]); update_param!(m,A,:ais_temperature_coefficient,1.0/a); update_param!(m,A,:ais_temperature_intercept,-TANT0/a)
end
runf(g,o)=(set_forcing!(m,g,o); run(m); 100 .*[x===missing ? NaN : Float64(x) for x in m[:global_sea_level,:sea_level_rise]])
variants=Dict("transient"=>joinpath(REPO,"data/MimiBRICK/parameters_subsample_brick_mengel_ext.csv"),
              "equilib"=>EQCSV)
drivers=Dict("MAGICC"=>("ssp245_gmst_base.csv","ssp245_ohc_base.csv","ssp245_gmst_pulse10gt.csv","ssp245_ohc_pulse10gt.csv"),
             "FaIR"=>("fair_gmst_base_wide.csv","fair_ohc_base_wide.csv","fair_gmst_pulse_wide.csv","fair_ohc_pulse_wide.csv"))
q(v,p)=quantile(v,p)
out=DataFrame(variant=String[],driver=String[],year=Int[],N=Int[],
              pulse_mean=Float64[],pulse_median=Float64[],mean_over_median=Float64[],top5_share=Float64[],
              level_median=Float64[],level_mean=Float64[])
for vn in ("transient","equilib")
  P=CSV.read(variants[vn],DataFrame; select=vcat(FN,DCOL))
  for dn in ("MAGICC","FaIR")
    gbf,obf,gpf,opf=drivers[dn]
    gb=lw(joinpath(FRC,gbf)); ob=lw(joinpath(FRC,obf);s=OHCS); gp=lw(joinpath(FRC,gpf)); op=lw(joinpath(FRC,opf);s=OHCS)
    N=min(size(gb,2),nrow(P))
    L=Dict(y=>Float64[] for y in (2100,2150)); PM=Dict(y=>Float64[] for y in (2100,2150))
    for i in 1:N
      setrow(P[i,:])
      lb=runf(gb[:,i],ob[:,i]); rf=mean(lb[IREF]); lp=runf(gp[:,i],op[:,i])
      for y in (2100,2150); push!(L[y],lb[tidx(y)]-rf); push!(PM[y],(lp[tidx(y)]-lb[tidx(y)])/PULSE); end
      i%100==0 && (println("  $vn/$dn draw $i/$N"); flush(stdout))
    end
    for y in (2100,2150)
      s=sort(PM[y],rev=true); top5=sum(s[1:max(1,round(Int,0.05*N))])/sum(s)
      push!(out,(vn,dn,y,N,mean(PM[y]),q(PM[y],.5),mean(PM[y])/q(PM[y],.5),top5,q(L[y],.5),mean(L[y])))
      @printf("SUBANN %-9s %-6s @%d (N=%d): PULSE mean %.3e med %.3e (ratio %.2f, top5%% %.0f%%) | LEVEL med %.1f mean %.1f\n",
        vn,dn,y,N,mean(PM[y]),q(PM[y],.5),mean(PM[y])/q(PM[y],.5),100*top5,q(L[y],.5),mean(L[y]))
      flush(stdout)
    end
  end
end
CSV.write(joinpath(REPO,"outputs/crossmodel_pulse_means_subannual.csv"),out)
println("wrote outputs/crossmodel_pulse_means_subannual.csv")
