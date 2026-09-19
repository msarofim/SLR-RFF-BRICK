## test_ladrillo_precip_reparam.jl — the projection kernel derives log P0 = u - kappa*TBAR_ANT for a
## --precip-reparam posterior EXACTLY as feeding it the derived column would (gate 0.0 cm), and a TBAR
## off by 1 K is caught (mutation). Inputs: a 100-draw thinning of chain_L26d_seed2026_n500000.csv.
##   julia --project=julia_v2 julia/test_ladrillo_precip_reparam.jl
using CSV, DataFrames, Mimi, MimiBRICK, Statistics, Printf
include(joinpath("/Users/MarcusMarcus/Documents/2026/CodeProjects/SLR-RFF-BRICK/julia", "ladrillo_projection.jl"))
S = joinpath(LADRILLO_REPO, "outputs/mcmc")   # inputs written by the test itself, from the L26d chain
ch = CSV.read(joinpath(S, "chain_L26d_seed2026_n500000.csv"), DataFrame)
raw0 = select(ch[250001:2500:end, :], Not(:log_post)); CSV.write(joinpath(S,"sub_L26d_raw.csv"), raw0)
der0 = copy(raw0); der0.ais_precip0_LOG = raw0.ais_precip_u .- raw0.antarctic_kappa .* LADRILLO_TBAR_ANT
select!(der0, Not(:ais_precip_u)); CSV.write(joinpath(S,"sub_L26d_der.csv"), der0)
der2f = copy(raw0); der2f.ais_precip0_LOG = raw0.ais_precip_u .- raw0.antarctic_kappa .* (LADRILLO_TBAR_ANT + 1.0)
select!(der2f, Not(:ais_precip_u)); CSV.write(joinpath(S,"sub_L26d_der2.csv"), der2f)
raw = ladrillo_posterior(path=joinpath(S,"sub_L26d_raw.csv"), cols=:all, nthin=100)
der = ladrillo_posterior(path=joinpath(S,"sub_L26d_der.csv"), cols=:all, nthin=100)
der2 = ladrillo_posterior(path=joinpath(S,"sub_L26d_der2.csv"), cols=:all, nthin=100)
bf = ladrillo_setup(ssp="ssp245", y0=1850, y1=2300, gis_variant=ladrillo_posterior_variant(LADRILLO_POSTERIOR_CSV))
maxd = 0.0
for i in 1:nrow(raw)
    ladrillo_run_draw!(bf, raw[i, :]); a = ladrillo_series(bf, :total)
    ladrillo_run_draw!(bf, der[i, :]); b = ladrillo_series(bf, :total)
    global maxd = max(maxd, maximum(abs.(a .- b)))
end
@printf("[GATE] kernel on ais_precip_u vs on the derived ais_precip0_LOG: max |Δ total| over %d draws x 451 yr = %.3e cm  %s\n", nrow(raw), maxd, maxd < 1e-9 ? "PASS" : "FAIL")
## mutation: a wrong TBAR must show
ladrillo_run_draw!(bf, raw[1, :]); a = ladrillo_series(bf, :total); ladrillo_run_draw!(bf, der2[1, :]); c = ladrillo_series(bf, :total)
@printf("[MUT]  TBAR off by 1 K moves the total by %.3f cm at 2300 (must be > 0)\n", abs(a[end]-c[end]))
