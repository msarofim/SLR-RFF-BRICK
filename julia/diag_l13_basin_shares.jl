# diag_l13_basin_shares.jl — does the FITTED 3-basin model reproduce the observed
# Mouginot sector partition? This is the number the whole restructure exists for.
#
# EXACT-DRIVER NOTE. Both shares windows (2002-2011, 2012-2018) end well before
# TGZ_LAST = 2024, and the model is integrated forward from 1850, so EVERY year
# that enters this diagnostic is inside the OBSERVED zone record. The calibrator's
# amp splice and GMST rebasing apply only to y > TGZ_LAST and therefore cannot
# touch these windows at all. So the driver here is the raw t_gis_zones column —
# not an approximation of the calibrator's driver, but identical to it over the
# span that matters. That is why this needs no forcing file.
#
# Run:  julia --project=julia_v2 julia/diag_l13_basin_shares.jl [chain.csv]

using CSV, DataFrames, Mimi, MimiBRICK, Printf, Statistics
const REPO = abspath(joinpath(@__DIR__, ".."))
include(joinpath(REPO, "julia", "brick_mengel.jl"))

const GIS_ZONE, GIS_V0_M, GIS_G = "south", 7.42, 0.0
const GIS_TBAR = 1.9631            # as printed by the calibrator for this zone
const WINS = ((2002, 2011), (2012, 2018))
const TARGET = ((south=0.592, mid=0.207, high=0.201),
                (south=0.554, mid=0.262, high=0.183))

chain_path = length(ARGS) >= 1 ? ARGS[1] :
    joinpath(REPO, "outputs/mcmc/chain_L13tune_seed2026_n1000000.csv")
df = CSV.read(chain_path, DataFrame)
h = df[(nrow(df)÷2 + 1):end, :]
med(c) = median(skipmissing(h[!, c]))

tgz = CSV.read(joinpath(REPO, "data/observations/t_gis_zones.csv"), DataFrame)
y0, y1 = 1850, Int(maximum(tgz.year))
obsd = Dict(Int(tgz[i, :year]) => Float64(tgz[i, GIS_ZONE]) for i in 1:nrow(tgz))
years = y0:y1
driver = [obsd[y] for y in years]
idx(y) = findfirst(==(y), years)

# (ell, w) -> the component's native slow pair, exactly as logposterior does
r_s = exp(med("gis_slow_ell")); w_s = med("gis_slow_w")
gis = (c1=med("gis_c1"), c0=med("gis_c0"), v0=GIS_V0_M, f=med("gis_f"),
       alpha_f=med("gis_alpha_f"), beta_f=med("gis_beta_f"),
       alpha_s=w_s * r_s / GIS_TBAR, beta_s=(1 - w_s) * r_s, g=GIS_G)
s = (south=1.0, mid=10.0^med("gis_s_mid"), high=10.0^med("gis_s_high"))

m = build_brick_nu3_gis3(ssp="ssp245", y0=y0, y1=y1)
update_gis_ab!(m, gis); update_gis3_shares!(m; k=GIS3_VSHARE, s=s)
set_gis_forcing!(m, driver)
bc = CSV.read(joinpath(REPO, "outputs/extc_block_constants.csv"), DataFrame)
brow(b) = only(eachrow(bc[bc.block .== b, :]))
zed = zeros(length(driver))
for blk in NU3_BLOCKS
    r = brow(blk)
    update_param!(m, _MENGEL_GLAC_SLOT, Symbol("gic_a_$blk"), Float64(r.a0))
    update_param!(m, _MENGEL_GLAC_SLOT, Symbol("gic_b_$blk"), Float64(r.b_fit_obsfit))
    update_param!(m, _MENGEL_GLAC_SLOT, Symbol("gic_T_off_$blk"), Float64(r.T_off_fit_obsfit))
    update_param!(m, _MENGEL_GLAC_SLOT, Symbol("gic_kappa_$blk"), Float64(r.kappa_anch_obsfit))
    update_param!(m, _MENGEL_GLAC_SLOT, Symbol("gic_nu_$blk"), Float64(r.nu_anch_obsfit))
end
update_param!(m, _MENGEL_GLAC_SLOT, :gic_sl0, 0.0)
set_glacier_forcing3!(m, (R19=zed, SLOWP=zed, FAST=zed))
run(m)

bsl = (south=m[_GIS_SLOT, :gis_sl_south], mid=m[_GIS_SLOT, :gis_sl_mid],
       high=m[_GIS_SLOT, :gis_sl_high])
@printf("L13tune posterior median | %s\n", basename(chain_path))
@printf("  rate scales: south 1.0000 (pinned)  mid %.4f  high %.4f\n", s.mid, s.high)
@printf("\n  %-11s %8s %8s %8s   %s\n", "window", "south", "mid", "high", "total cm/yr")
maxz = Ref(0.0)
for (w, tgt) in zip(WINS, TARGET)
    i0, i1, n = idx(w[1]), idx(w[2]), w[2] - w[1]
    d = map(b -> (Float64(getproperty(bsl, b)[i1]) - Float64(getproperty(bsl, b)[i0])) / n,
            GIS3_BASINS)
    sh = d ./ sum(d)
    @printf("  %-11s %8.3f %8.3f %8.3f   %11.4f\n", "$(w[1])-$(w[2])", sh..., 100*sum(d))
    @printf("  %-11s %8.3f %8.3f %8.3f\n", "  target", tgt.south, tgt.mid, tgt.high)
    z = [(sh[i] - getproperty(tgt, b)) / 0.05 for (i, b) in enumerate(GIS3_BASINS)]
    @printf("  %-11s %8.2f %8.2f %8.2f   (sigma = 0.05; high is NOT scored)\n",
            "  z-score", z...)
    maxz[] = max(maxz[], maximum(abs.(z[1:2])))
end
@printf("\n  s = 1 null, for reference: %.3f %.3f %.3f (the volume shares)\n",
        GIS3_VSHARE.south, GIS3_VSHARE.mid, GIS3_VSHARE.high)
@printf("  worst |z| on a SCORED share: %.2f\n", maxz[])
