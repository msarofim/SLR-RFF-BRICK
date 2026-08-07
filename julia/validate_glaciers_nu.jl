## ============================================================================
## validate_glaciers_nu.jl — port validation for the extB3 glaciers_nu component
## (climate-modeling port-testing discipline; run BEFORE any MCMC).
##
## Checks:
##   V1. glaciers_nu trajectories at the D0 self-consistent point for several
##       (kappa, nu) combos -> CSV, compared bit-level against the Python D0
##       integrator (python/validate_glaciers_nu_compare.py; tol 1e-9 m).
##   V2. nu = 0 == analytic single-tau Mengel (computed in the Python step).
##   V3. component swap is CLEAN: AIS/GIS/TE outputs of build_brick_nu vs
##       build_brick_mengel are IDENTICAL at identical params/forcing/seed
##       (the glacier replacement must not perturb any other component).
##
## Usage: julia --project=julia_v2 julia/validate_glaciers_nu.jl
## Output: outputs/validate_glaciers_nu.csv (+ console verdicts)
## ============================================================================

using CSV, DataFrames, Mimi, MimiBRICK, Statistics, Random
include(joinpath(@__DIR__, "brick_mengel.jl"))

const REPO = abspath(joinpath(@__DIR__, ".."))
const OBS  = joinpath(REPO, "data/observations")
const Y0, Y1 = 1850, 2026
const AMP_G = 1.8                      # projection-era glacier amplification (GlacierMIP3; Marcus 2026-08-07)
const SPLICE_ANCHOR = 2014:2024        # 11-yr anchor window for the tail splice
years = collect(Y0:Y1)

lc(p, c) = (d = CSV.read(p, DataFrame); Dict(Int(d[i, "year"]) => Float64(d[i, c]) for i in 1:nrow(d)))
gmst = [lc(joinpath(OBS, "fair_mean_gmst_ssp245harm.csv"), "gmst_C")[y] for y in years]
ohc  = [lc(joinpath(OBS, "fair_mean_ohc_ssp245harm.csv"), "ohc_1e22J")[y] for y in years]

# ---- T_glac driver: observed through 2024, amp_g x GMST anchor-preserving splice after
tg = lc(joinpath(OBS, "t_glac_hadcrut5.csv"), "t_glac_C")
tg_last = maximum(keys(tg))
gm = Dict(zip(years, gmst))
off = mean(tg[y] for y in SPLICE_ANCHOR) - AMP_G * mean(gm[y] for y in SPLICE_ANCHOR)
tglac = [y <= tg_last ? tg[y] : AMP_G * gm[y] + off for y in years]
println("T_glac driver: obs 1850-$(tg_last), splice x$(AMP_G) anchored $(SPLICE_ANCHOR) (offset $(round(off, digits=4)) K)")

# ---- SC glacier point (D0-final) + kappa/nu combos to validate
const SC = (a = 0.383, b = 0.286, T_off = -0.957, sl0 = 0.0)
const COMBOS = [(kappa = 0.0097, nu = 0.0), (kappa = 0.006, nu = 1.0), (kappa = 0.003, nu = 2.0)]

medoid = CSV.read(joinpath(REPO, "outputs/recalib_central_row.csv"), DataFrame)[1, :]

# ---- V1: trajectories per combo
out = DataFrame(year = years, tglac = tglac)
Random.seed!(42)                       # get_model has un-seeded internal RNG (quirk #1)
m = build_brick_nu(ssp = "ssp245", y0 = Y0, y1 = Y1)
for c in COMBOS
    update_brick_nu!(m, medoid, (a = SC.a, b = SC.b, T_off = SC.T_off,
                                 kappa = c.kappa, nu = c.nu, sl0 = SC.sl0); precip_log = true)
    set_forcing!(m, gmst, ohc)
    set_glacier_forcing!(m, tglac)
    run(m)
    out[!, "gsic_k$(c.kappa)_nu$(c.nu)"] = copy(m[:glaciers_small_icecaps, :gsic_sea_level])
end

# ---- V3: non-glacier outputs identical between the two builds at MATCHED glacier
# output. NB the AIS component consumes global_sea_level (Δ_sea_level forcing), so the
# glacier trajectory legitimately feeds AIS — the builds must produce the SAME glacier
# path for the comparison to isolate the swap. Match: glaciers_nu(nu=0, kappa=1/tau)
# == glaciers_mengel(f=1, tau_fast=tau, slow pool empty), driven by the SAME series
# (feed the Mengel build tglac as its GMST so both glacier components see one driver;
# GIS/TE are then compared on the m_nu-vs-m_me2 pair sharing the ORIGINAL gmst).
const TAU_MATCH = 103.0928
Random.seed!(42)
m_nu = build_brick_nu(ssp = "ssp245", y0 = Y0, y1 = Y1)
update_brick_nu!(m_nu, medoid, (a = SC.a, b = SC.b, T_off = SC.T_off,
                                kappa = 1.0 / TAU_MATCH, nu = 0.0, sl0 = 0.0); precip_log = true)
set_forcing!(m_nu, gmst, ohc); set_glacier_forcing!(m_nu, tglac); run(m_nu)
Random.seed!(42)
m_me = build_brick_mengel(ssp = "ssp245", y0 = Y0, y1 = Y1)
update_brick_mengel!(m_me, medoid, (a = SC.a, b = SC.b, T_lia = SC.T_off, f = 1.0,
                                    tau_fast = TAU_MATCH, tau_slow = 1.0e6, sl0 = 0.0); precip_log = true)
set_forcing!(m_me, gmst, ohc)
# the old component reads the SHARED model GMST — but only the glacier slot must see
# tglac. Disconnect its GMST link and feed tglac directly (old-component-only surgery,
# possible because the old param name survives in glaciers_mengel).
Mimi.disconnect_param!(m_me, :glaciers_small_icecaps, :global_surface_temperature)
update_param!(m_me, :glaciers_small_icecaps, :global_surface_temperature, tglac)
run(m_me)
v3max = 0.0
dg = maximum(abs.(m_nu[:glaciers_small_icecaps, :gsic_sea_level] .- m_me[:glaciers_small_icecaps, :gsic_sea_level]))
println("V3a glacier match (nu=0,kappa=1/tau vs mengel f=1,tau): max diff = $(dg)  ",
        dg < 1e-12 ? "PASS (validates nesting in Julia)" : "FAIL")
for (comp, var) in [(:antarctic_icesheet, :ais_sea_level), (:greenland_icesheet, :greenland_sea_level),
                    (:thermal_expansion, :te_sea_level), (:landwater_storage, :lws_sea_level)]
    d = maximum(abs.(m_nu[comp, var] .- m_me[comp, var]))
    global v3max = max(v3max, d)
    println("V3 $(comp): max |nu-build - mengel-build| = $(d)")
end
println(v3max < 1e-12 ? "V3 PASS: non-glacier components identical across the swap (glacier-matched)" :
        "V3 FAIL: swap perturbs other components beyond the glacier coupling ($(v3max))")

CSV.write(joinpath(REPO, "outputs/validate_glaciers_nu.csv"), out)
println("Wrote outputs/validate_glaciers_nu.csv — now run python/validate_glaciers_nu_compare.py")
