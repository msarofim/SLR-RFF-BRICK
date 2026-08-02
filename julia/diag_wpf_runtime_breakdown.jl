# Runtime breakdown for weight_and_project_brick_fair.jl's run2300: where do the ~29 ms/run go?
# Times (1) run(m) alone, (2) scalar params + run (MCMC-like), (3) set_forcing! + run,
# (4) the full run2300 body. Informs whether a forcing-sweep restructure is worth it.
include(joinpath(@__DIR__, "calibrate_mcmc_ext.jl"))
using Statistics, Printf, CSV, DataFrames

const FRC = joinpath(REPO, "..", "FaIRtoFrEDI", "magicc_comparison", "processed", "curv_wide")
const YP0, YP1 = 1850, 2300
const YRS2 = collect(YP0:YP1); ty2(y)=findfirst(==(y),YRS2)
loadw(p; s=1.0)=(d=CSV.read(p,DataFrame); keep=[y in YRS2 for y in d.year]; Matrix(d[keep,2:end]).*s)
GW2 = loadw(joinpath(FRC,"fair_gmst_base_wide.csv")); OW2 = loadw(joinpath(FRC,"fair_ohc_base_wide.csv"); s=0.1)

sub = CSV.read(joinpath(REPO,"data/MimiBRICK/parameters_subsample_brick_mengel_extA108.csv"), DataFrame)
θ = Float64[Float64(sub[1, Symbol(FREE[k].name)]) for k in 1:NP]
medoid2 = CSV.read(joinpath(REPO,"outputs/recalib_central_row.csv"), DataFrame)[1,:]
m2 = build_brick_mengel(ssp="ssp245", y0=YP0, y1=YP1)
update_brick_mengel!(m2, medoid2, (a=0.45,b=0.52,T_lia=-0.45,f=0.5,tau_fast=40.0,tau_slow=250.0,sl0=0.0); precip_log=true)
setp2!(k,v)=update_param!(m2,k.comp,k.sym, k.islog ? log(v) : v)
setscalars!() = begin
    @inbounds for k in 1:NP; (k==AMP_IDX||k==TON_IDX) && continue; setp2!(FREE[k], θ[k]); end
    update_param!(m2,:antarctic_icesheet,:ais_runoffline_snowheight₀, -θ[TON_IDX]*θ[C_IDX])
    update_param!(m2,:antarctic_icesheet,:ais_temperature_coefficient, 1.0/θ[AMP_IDX])
    update_param!(m2,:antarctic_icesheet,:ais_temperature_intercept, -AIS_TANT0/θ[AMP_IDX])
end
extract() = begin
    ib2=[ty2(y) for y in 1995:2005]
    rr(v)=100 .* (v .- mean(v[ib2]))
    ais=rr(m2[:antarctic_icesheet,:ais_sea_level]); gsic=rr(m2[:glaciers_small_icecaps,:gsic_sea_level])
    gis=rr(m2[:greenland_icesheet,:greenland_sea_level]); te=rr(m2[:thermal_expansion,:te_sea_level])
    gtot=rr(m2[:global_sea_level,:sea_level_rise])
    (sum(ais)+sum(gsic)+sum(gis)+sum(te)+sum(gtot))
end

g1=GW2[:,1]; o1=OW2[:,1]; g2=GW2[:,2]; o2=OW2[:,2]
set_forcing!(m2,g1,o1); setscalars!(); run(m2)   # warm/compile
N=200
bench(f) = (t=time(); for _ in 1:N; f(); end; 1000*(time()-t)/N)

t_run       = bench(() -> run(m2))
t_scal      = bench(() -> (setscalars!(); run(m2)))
t_frc       = bench(() -> (set_forcing!(m2,g1,o1); run(m2)))
flip=Ref(false)
t_frcalt    = bench(() -> (set_forcing!(m2, flip[] ? g1 : g2, flip[] ? o1 : o2); flip[]=!flip[]; run(m2)))
t_full      = bench(() -> (set_forcing!(m2,g1,o1); setscalars!(); run(m2); extract()))
t_extract   = bench(extract)

@printf("run(m) only              : %7.2f ms\n", t_run)
@printf("scalars + run            : %7.2f ms\n", t_scal)
@printf("set_forcing!(same) + run : %7.2f ms\n", t_frc)
@printf("set_forcing!(alt)  + run : %7.2f ms\n", t_frcalt)
@printf("full run2300 equivalent  : %7.2f ms\n", t_full)
@printf("extraction only          : %7.2f ms\n", t_extract)

# ---- follow-up: is the cost per-update-call overhead (batchable) or intrinsic? ----
t_one = bench(() -> (update_param!(m2,:thermal_expansion,:te_α, θ[12]); run(m2)))
@printf("ONE scalar + run         : %7.2f ms\n", t_one)
using Mimi
pd = Dict{Tuple{Symbol,Symbol},Any}()
for k in 1:NP
    (k==AMP_IDX||k==TON_IDX) && continue
    pd[(FREE[k].comp, FREE[k].sym)] = FREE[k].islog ? log(θ[k]) : θ[k]
end
pd[(:antarctic_icesheet,:ais_runoffline_snowheight₀)] = -θ[TON_IDX]*θ[C_IDX]
pd[(:antarctic_icesheet,:ais_temperature_coefficient)] = 1.0/θ[AMP_IDX]
pd[(:antarctic_icesheet,:ais_temperature_intercept)] = -AIS_TANT0/θ[AMP_IDX]
try
    Mimi.update_params!(m2, pd); run(m2)
    t_batch = bench(() -> (Mimi.update_params!(m2, pd); run(m2)))
    @printf("BATCH update_params!+run : %7.2f ms\n", t_batch)
catch e
    println("batch update_params! failed: ", sprint(showerror, e))
end
println("Mimi version: ", pkgversion(Mimi))
