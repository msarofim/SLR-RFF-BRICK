# STEP 1 diagnostic (Marcus 2026-07-24): how much does the BRICK<->FaIR coupling matter?
# Current approach calibrates BRICK on FaIR-MEAN, then pairs BRICK draw i with FaIR member i
# independently. If that pairing is historically inconsistent, requiring consistency (importance
# reweighting by the historical-SLR likelihood under each pair's OWN forcing) should tighten the
# projection bands. Output: weight ESS (how much the coupling bites) + reweighted vs unweighted
# TE/total @2100. Runs on the pristine depot (levels; <1% patch effect). NOT the joint calibration —
# a lower-bound proxy: it can only DOWN-weight existing draws, not generate the compensating
# low-te_α draws a true joint would (so it over-tightens vs the real joint; ESS is the robust signal).
using CSV, DataFrames, Mimi, MimiBRICK, Statistics, Printf, Random
REPO="/Users/MarcusMarcus/Documents/2026/CodeProjects/SLR-RFF-BRICK"; OBS=joinpath(REPO,"data/observations")
FRC="/Users/MarcusMarcus/Documents/2026/CodeProjects/FaIRtoFrEDI/magicc_comparison/processed/curv_wide"
DEPOT=joinpath(homedir(),".julia/packages/MimiBRICK/edplP/src/components/antarctic_icesheet_component.jl")
occursin("frac", read(DEPOT,String)) && error("depot is PATCHED — run on pristine")
include(joinpath(REPO,"julia/brick_mengel.jl"))
Y0,Y1=1850,2100; years=collect(Y0:Y1); tidx(y)=findfirst(==(y),years); IREF=[tidx(y) for y in 1995:2005]
OHCS=0.1; TANT0=-15.42/0.8365; A=:antarctic_icesheet; G=:glaciers_small_icecaps
lw(p;s=1.0)=(d=CSV.read(p,DataFrame); keep=[y in years for y in d.year]; Matrix(d[keep,2:end]).*s)
# FaIR ensemble forcing (841 members), historical + future to 2100
GB=lw(joinpath(FRC,"fair_gmst_base_wide.csv")); OB=lw(joinpath(FRC,"fair_ohc_base_wide.csv");s=OHCS)
NF=size(GB,2)
# obs targets + sigma (from _lo/_hi, 90% band -> sigma=(hi-lo)/(2*1.645))
T=CSV.read(joinpath(REPO,"outputs/recalib_targets_ext.csv"),DataFrame)
COMPS=[("ais",:antarctic_icesheet,:ais_sea_level,"ais"),("gis",:greenland_icesheet,:greenland_sea_level,"gis"),
       ("gsic",:glaciers_small_icecaps,:gsic_sea_level,"gsic"),("te",:thermal_expansion,:te_sea_level,"steric"),
       ("total",:global_sea_level,:sea_level_rise,"dang")]
# COARSE likelihood: total SLR at a few NEAR-INDEPENDENT epochs (the fine per-year/per-component
# product over ~600 points is grossly over-peaked vs the AR(1) effective DOF -> ESS collapses to 1).
# Total captures the integrated historical consistency; ~decadal epochs approximate independent info.
EPOCHS=[1930,1960,1990,2018]
obs=Dict{String,Any}()
trow(y)=findfirst(==(y),T.year)
obs["total"]=[(tidx(y), Float64(T[trow(y),:dang]),
               max((Float64(T[trow(y),:dang_hi])-Float64(T[trow(y),:dang_lo]))/(2*1.645),0.10))
              for y in EPOCHS]
# BRICK-AM model (extA108)
FREE=[("ais_ocean_temperature₀",A,:ais_ocean_temperature₀),("antarctic_alpha",A,:ais_α),("antarctic_nu",A,:ais_ν),
("antarctic_temp_threshold",A,:temperature_threshold),("anto_alpha",:antarctic_ocean,:anto_α),("anto_beta",:antarctic_ocean,:anto_β),
("greenland_a",:greenland_icesheet,:greenland_a),("greenland_b",:greenland_icesheet,:greenland_b),("greenland_alpha",:greenland_icesheet,:greenland_α),
("greenland_beta",:greenland_icesheet,:greenland_β),("greenland_v0",:greenland_icesheet,:greenland_v₀),("thermal_alpha",:thermal_expansion,:te_α),
("gic_a",G,:gic_a),("gic_b",G,:gic_b),("gic_T_lia",G,:gic_T_lia),("gic_f",G,:gic_f),("gic_tau_fast",G,:gic_tau_fast),("gic_tau_slow",G,:gic_tau_slow),
("antarctic_lambda",A,:λ),("antarctic_gamma",A,:ais_γ),("antarctic_kappa",A,:ais_κ),
("ais_mu",A,:ais_μ),("ais_bedheight0",A,:ais_bedheight₀),("ais_slope",A,:ais_slope),("ais_iceflow0",A,:ais_iceflow₀),
("ais_precip0_LOG",A,:ais_precipitation₀),("ais_c",A,:ais_c)]
FN=[f[1] for f in FREE]
m=build_brick_mengel(ssp="ssp245",y0=Y0,y1=Y1)
med=CSV.read(joinpath(REPO,"outputs/recalib_central_row.csv"),DataFrame)[1,:]
update_brick_mengel!(m,med,(a=0.45,b=0.52,T_lia=-0.45,f=0.5,tau_fast=40.0,tau_slow=250.0,sl0=0.0);precip_log=true)
P=CSV.read(joinpath(REPO,"data/MimiBRICK/parameters_subsample_brick_mengel_extA108.csv"),DataFrame; select=vcat(FN,["ais_runoff_Ton","ais_gmst_amp"]))
setr(i)=begin r=P[i,:]
  for f in FREE; update_param!(m,f[2],f[3],Float64(r[f[1]])); end
  update_param!(m,A,:ais_runoffline_snowheight₀,-Float64(r["ais_runoff_Ton"])*Float64(r["ais_c"]))
  a=Float64(r["ais_gmst_amp"]); update_param!(m,A,:ais_temperature_coefficient,1.0/a); update_param!(m,A,:ais_temperature_intercept,-TANT0/a)
end
getc(cn,vn)=(v=100 .*[x===missing ? NaN : Float64(x) for x in m[cn,vn]]; v .- mean(v[IREF]))
N=min(NF,nrow(P))
loglik=fill(-Inf,N); te2100=fill(NaN,N); tot2100=fill(NaN,N); ohc2018=[OB[tidx(2018),i]-OB[tidx(1850),i] for i in 1:N]
for i in 1:N
    setr(i); set_forcing!(m,GB[:,i],OB[:,i]); run(m)
    comp=Dict(nm=>getc(cn,vn) for (nm,cn,vn,_) in COMPS)
    ll=0.0
    for (ti,v,s) in obs["total"]
        x=comp["total"][ti]; ll += isfinite(x) ? -0.5*((x-v)/s)^2 : -1e6
    end
    loglik[i]=ll; te2100[i]=comp["te"][tidx(2100)]; tot2100[i]=comp["total"][tidx(2100)]
    i%100==0 && (print("."); flush(stdout))
end
println()
w=exp.(loglik .- maximum(loglik)); w ./= sum(w)
ESS=1/sum(w.^2)
wq(x,p)=begin idx=sortperm(x); xs=x[idx]; ws=cumsum(w[idx]); xs[findfirst(>=(p),ws)] end
uq(x,p)=quantile(filter(isfinite,x),p)
@printf("\n=== COUPLING REWEIGHT (N=%d pairs) ===\n",N)
@printf("weight ESS = %.0f / %d  (%.0f%%)  [low ESS => coupling bites; ~N => current pairing already consistent]\n",ESS,N,100*ESS/N)
@printf("corr(loglik, FaIR OHC@2018) = %.2f  [negative => hot-OHC members fit history worse under mean-calibrated te_α]\n",cor(loglik,ohc2018))
for (lab,x) in (("TE @2100",te2100),("Total @2100",tot2100))
    @printf("%-12s  UNWEIGHTED med %.1f [%.1f, %.1f]  ->  REWEIGHTED med %.1f [%.1f, %.1f]  (5-95%% width %.1f -> %.1f cm, %.0f%%)\n",
        lab,uq(x,.5),uq(x,.05),uq(x,.95),wq(x,.5),wq(x,.05),wq(x,.95),uq(x,.95)-uq(x,.05),wq(x,.95)-wq(x,.05),100*(wq(x,.95)-wq(x,.05))/(uq(x,.95)-uq(x,.05)))
end
CSV.write(joinpath(REPO,"outputs/coupling_reweight.csv"),DataFrame(draw=1:N,loglik=loglik,weight=w,ohc2018=ohc2018,te2100=te2100,tot2100=tot2100))
println("wrote outputs/coupling_reweight.csv")
