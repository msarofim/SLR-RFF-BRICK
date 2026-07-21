# PROTOTYPE — approach 1: analytic tip-time decomposition of the pulse mean.
# Per draw:  marginal = smooth(non-AIS finite diff)  +  tip_channel
#   tip_channel = disint_rate(@horizon) * [pulse warming @ continuous crossing / tonne]
#                                        / [warming rate @ crossing]
# Continuous (sub-annual) crossing + near-horizon disintegration rate -> small-pulse
# (derivative) limit, pulse-size-INDEPENDENT by construction. Tests: (i) analytic mean via the
# 0.1 vs 10 GtCO2 T-pulse must agree; (ii) vs raw finite-diff mean/median; (iii) tail dominance.
using CSV, DataFrames, Mimi, MimiBRICK, Statistics, Printf
REPO="/Users/MarcusMarcus/Documents/2026/CodeProjects/SLR-RFF-BRICK"
FRC="/Users/MarcusMarcus/Documents/2026/CodeProjects/FaIRtoFrEDI/magicc_comparison/processed/curv_wide"
include(joinpath(REPO,"julia/brick_mengel.jl"))
Y0,Y1=1850,2150; years=collect(Y0:Y1); tidx(y)=findfirst(==(y),years)
OHCS=0.1; TANT0=-15.42/0.8365; HOR=(2100,2150)
A=:antarctic_icesheet; G=:glaciers_small_icecaps
FREE=[("ais_ocean_temperature₀",A,:ais_ocean_temperature₀),("antarctic_alpha",A,:ais_α),("antarctic_nu",A,:ais_ν),
("antarctic_temp_threshold",A,:temperature_threshold),("anto_alpha",:antarctic_ocean,:anto_α),("anto_beta",:antarctic_ocean,:anto_β),
("greenland_a",:greenland_icesheet,:greenland_a),("greenland_b",:greenland_icesheet,:greenland_b),("greenland_alpha",:greenland_icesheet,:greenland_α),
("greenland_beta",:greenland_icesheet,:greenland_β),("greenland_v0",:greenland_icesheet,:greenland_v₀),("thermal_alpha",:thermal_expansion,:te_α),
("gic_a",G,:gic_a),("gic_b",G,:gic_b),("gic_T_lia",G,:gic_T_lia),("gic_f",G,:gic_f),("gic_tau_fast",G,:gic_tau_fast),("gic_tau_slow",G,:gic_tau_slow),
("antarctic_lambda",A,:λ),("antarctic_gamma",A,:ais_γ),("antarctic_kappa",A,:ais_κ),
("ais_mu",A,:ais_μ),("ais_bedheight0",A,:ais_bedheight₀),("ais_slope",A,:ais_slope),("ais_iceflow0",A,:ais_iceflow₀),
("ais_precip0_LOG",A,:ais_precipitation₀),("ais_c",A,:ais_c)]
FN=[f[1] for f in FREE]
lw(p;s=1.0)=(d=CSV.read(p,DataFrame); keep=[y in years for y in d.year]; Matrix(d[keep,2:end]).*s)
gb=lw(joinpath(FRC,"ssp245_gmst_base.csv")); ob=lw(joinpath(FRC,"ssp245_ohc_base.csv");s=OHCS)
g01=lw(joinpath(FRC,"ssp245_gmst_pulse.csv")); o01=lw(joinpath(FRC,"ssp245_ohc_pulse.csv");s=OHCS)
g10=lw(joinpath(FRC,"ssp245_gmst_pulse10gt.csv")); o10=lw(joinpath(FRC,"ssp245_ohc_pulse10gt.csv");s=OHCS)
loadpost(paths,ndraw)=begin
  rows=DataFrame()
  for p in paths
    df=CSV.read(p,DataFrame; select=vcat(FN,["ais_runoff_Ton","ais_gmst_amp"])); n=nrow(df)
    step=max(1,(n÷2)÷(ndraw÷length(paths))); bi=collect((n÷2+1):step:n)[1:(ndraw÷length(paths))]
    rows=vcat(rows,df[bi,:])
  end; rows
end
med=CSV.read(joinpath(REPO,"outputs/recalib_central_row.csv"),DataFrame)[1,:]
m=build_brick_mengel(ssp="ssp245",y0=Y0,y1=Y1)
update_brick_mengel!(m,med,(a=0.45,b=0.52,T_lia=-0.45,f=0.5,tau_fast=40.0,tau_slow=250.0,sl0=0.0);precip_log=true)
setrow(r)=begin
  for f in FREE; update_param!(m,f[2],f[3],Float64(r[f[1]])); end
  update_param!(m,A,:ais_runoffline_snowheight₀,-Float64(r["ais_runoff_Ton"])*Float64(r["ais_c"]))
  a=Float64(r["ais_gmst_amp"]); update_param!(m,A,:ais_temperature_coefficient,1.0/a); update_param!(m,A,:ais_temperature_intercept,-TANT0/a)
end
f64(v)=[x===missing ? NaN : Float64(x) for x in v]
runf(g,o)=(set_forcing!(m,g,o); run(m); (f64(m[:antarctic_icesheet,:antartic_surface_temperature]),
   100 .*f64(m[:global_sea_level,:sea_level_rise]), 100 .*f64(m[:antarctic_icesheet,:ais_sea_level])))
function tcross(T,thr)
  for k in 2:length(T); if T[k-1]<thr<=T[k]; return (k-1)+(thr-T[k-1])/(T[k]-T[k-1]); end; end; return nothing
end
interp(v,x)=(k=floor(Int,x); k>=length(v) ? v[end] : v[k]+(x-k)*(v[k+1]-v[k]))
variants=Dict("transient"=>[joinpath(REPO,"data/MimiBRICK/parameters_subsample_brick_mengel_ext.csv")],
              "equilib"=>[joinpath(REPO,"outputs/mcmc","chain_extA6eq_seed$(s)_n2000000.csv") for s in 2026:2029])
q(v,p)=quantile(v,p)
for vn in ("transient","equilib")
  P = vn=="transient" ? CSV.read(variants[vn][1],DataFrame) : loadpost(variants[vn],10000)
  N=min(300,size(gb,2),nrow(P))
  acc=Dict(H=>(raw01=Float64[],raw10=Float64[],ana01=Float64[],ana10=Float64[]) for H in HOR); ntip=Dict(H=>0 for H in HOR)
  for i in 1:N
    setrow(P[i,:]); thr=Float64(P[i,"antarctic_temp_threshold"])
    Tb,totb,aisb=runf(gb[:,i],ob[:,i]); T01,tot01,ais01=runf(g01[:,i],o01[:,i]); T10,tot10,ais10=runf(g10[:,i],o10[:,i])
    nonb=totb.-aisb; non01=tot01.-ais01; non10=tot10.-ais10
    xc=tcross(Tb,thr)
    for H in HOR
      hi=tidx(H)
      push!(acc[H].raw01,(tot01[hi]-totb[hi])/0.1); push!(acc[H].raw10,(tot10[hi]-totb[hi])/10.0)
      smooth=(non10[hi]-nonb[hi])/10.0                      # non-AIS is linear -> 10gt fine
      tip01=0.0; tip10=0.0
      if xc!==nothing && xc<hi
        wr=Tb[Int(ceil(xc))]-Tb[Int(floor(xc))]
        if wr>1e-6
          drate=(aisb[hi]-aisb[hi-5])/5.0                   # disint SLR rate near horizon (cm/yr)
          pw01=(interp(T01,xc)-interp(Tb,xc))/0.1; pw10=(interp(T10,xc)-interp(Tb,xc))/10.0
          tip01=drate*pw01/wr; tip10=drate*pw10/wr
        end
        ntip[H]+=1
      end
      push!(acc[H].ana01,smooth+tip01); push!(acc[H].ana10,smooth+tip10)
    end
  end
  for H in HOR
    a=acc[H]; s=sort(a.ana10,rev=true); top5=s[1:max(1,round(Int,0.05*N))]; tdom=sum(top5)/sum(a.ana10)
    @printf("\n%-9s @%d (N=%d, %d tip):\n",vn,H,N,ntip[H])
    @printf("  RAW finite-diff mean:  0.1GtCO2 %.3e   10GtCO2 %.3e   (ratio %.2f)\n",mean(a.raw01),mean(a.raw10),mean(a.raw10)/mean(a.raw01))
    @printf("  MEDIAN (raw 10gt):     %.3e\n",q(a.raw10,.5))
    @printf("  ANALYTIC mean:         via0.1Tpulse %.3e   via10Tpulse %.3e   (ratio %.3f) <- want ~1.00\n",mean(a.ana01),mean(a.ana10),mean(a.ana10)/mean(a.ana01))
    @printf("  ANALYTIC median:       %.3e   |  top-5%% draws supply %.0f%% of the analytic mean\n",q(a.ana10,.5),100*tdom)
  end
end
