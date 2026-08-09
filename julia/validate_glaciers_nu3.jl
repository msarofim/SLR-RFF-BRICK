# validate_glaciers_nu3.jl — extC port validation (2026-08-09).
#
# Includes calibrate_mcmc_ext.jl (its PROGRAM_FILE guard skips sampling), so the
# ACTUAL surgery code paths are validated, not a re-implementation:
#   [1] per-block spliced drivers (tg3) == python extend_obs reference  (<= 1e-9)
#   [2] per-block integrated melt series through the Mimi glaciers_nu3
#       component at the reference theta == python integrate_N            (<= 1e-9)
#   [3] slot contract: gsic_sea_level == gsic_r19 + gsic_hind (bitwise-ish)
#   [4] logposterior(theta0) is finite (end-to-end smoke incl rung/ledger/
#       GlaMBIE/F_unch/delta terms)
#
# Reference (python ground truth): outputs/extc_port_reference{,_theta}.csv,
# emitted by python/emit_extc_port_reference.py at the anchored theta.
#
# Run BOTH bases:
#   julia --project=julia_v2 julia/validate_glaciers_nu3.jl 2000 2026
#   julia --project=julia_v2 julia/validate_glaciers_nu3.jl 2000 2026 --amp-basis=obsfit

include(joinpath(@__DIR__, "calibrate_mcmc_ext.jl"))

SAMPLED_AMP && error("port validation needs a FIXED amp basis (the python reference " *
                     "is at the regchar/obsfit amps; sampled-mode drivers sit at the " *
                     "prior centers) — run with --amp-basis=regchar or --amp-basis=obsfit")
const REF = CSV.read(joinpath(REPO, "outputs/extc_port_reference.csv"), DataFrame)
const REF_TH = CSV.read(joinpath(REPO, "outputs/extc_port_reference_theta.csv"), DataFrame)
const BKEY = AMP_BASIS == "regchar" ? "reg" : "obs"
@assert Int.(REF.year) == years "reference year grid mismatch"

fails = String[]
tol = 1e-9

# [1] driver identity
for b in BLOCKS
    d = maximum(abs.(getproperty(tg3, Symbol(b)) .- Float64.(REF[!, "drv_$(BKEY)_$b"])))
    println("[1] driver $b: max|diff| = $d $(d <= tol ? "PASS" : "FAIL")")
    d <= tol || push!(fails, "driver $b")
end

# [2] series identity at the reference theta
for r in eachrow(REF_TH)
    r.basis == BKEY || continue
    blk = r.block
    update_param!(m, G, Symbol("gic_a_$blk"),     Float64(r.a))
    update_param!(m, G, Symbol("gic_b_$blk"),     Float64(r.b))
    update_param!(m, G, Symbol("gic_T_off_$blk"), Float64(r.T_off))
    update_param!(m, G, Symbol("gic_kappa_$blk"), Float64(r.kappa))
    update_param!(m, G, Symbol("gic_nu_$blk"),    Float64(r.nu))
end
run(m)
sers = Dict("R19" => m[G, :gsic_r19], "SLOWP" => m[G, :gsic_slowp],
            "FAST" => m[G, :gsic_fast])
for b in BLOCKS
    d = maximum(abs.(Float64.(sers[b]) .- Float64.(REF[!, "s_$(BKEY)_$b"])))
    println("[2] series $b: max|diff| = $d $(d <= tol ? "PASS" : "FAIL")")
    d <= tol || push!(fails, "series $b")
end

# [3] slot contract
d3 = maximum(abs.(Float64.(m[G, :gsic_sea_level]) .-
                  (Float64.(m[G, :gsic_hind]) .+ Float64.(m[G, :gsic_r19]))))
println("[3] slot contract gsic_sea_level == hind + r19: max|diff| = $d3 " *
        (d3 <= 1e-12 ? "PASS" : "FAIL"))
d3 <= 1e-12 || push!(fails, "slot contract")

# [4] logposterior finite at theta0 (restore theta0's glacier params first)
lp0 = logposterior(θ0)
println("[4] logposterior(theta0) = $lp0 " * (isfinite(lp0) ? "PASS" : "FAIL"))
isfinite(lp0) || push!(fails, "logposterior(theta0) non-finite")

if isempty(fails)
    println("VALIDATION PASS (basis=$AMP_BASIS)")
else
    error("VALIDATION FAILED (basis=$AMP_BASIS): " * join(fails, ", "))
end
