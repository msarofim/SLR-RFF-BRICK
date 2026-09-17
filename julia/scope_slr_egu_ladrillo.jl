## ============================================================================
## scope_slr_egu_ladrillo.jl -- LADRILLO SENSITIVITY for the power-plant (EGU) SPRM mirror
##
## Marcus 2026-09-16: "Do a Ladrillo sensitivity test too to compare to BRICK 1.2.1 and
## BRICK 2.0, but just for EGU 50%." The headline SLR stays BRICK v1.2.1 + zenodo-v3 (= EPA's
## v1.0.1 in driven mode); BRICK 2.0 and Ladrillo L24 are INTERNAL sensitivities.
##
## PAIRED baseline / policy arms through Ladrillo L24 on the SAME per-config FaIR 2.2.4
## (calib 1.6.0) GMST + OHC cubes the BRICK arms used (FaIRtoFrEDI/fair_outputs/
## fair_{baseline,<arm>}_{gmst,ohc}_v160_egu.csv; 841 configs, 1850-2300, rel 1850-1900,
## OHC in 1e22 J). This is scope_slr_pulse_vv.jl's recipe with the marker cubes replaced by
## two explicit cube paths: ONE draw->config assignment, ONE chain read, ONE model build per
## config for BOTH arms, so the pairing is an identity and [PRE-POLICY-ZERO] measures it.
##
## CONVENTION (inherited from the joint arm, `scope_slr_fair_uncertainty.jl`):
##   * --forcing=spliced (DEFAULT, Ladrillo's standing convention): pre-2014 the MEAN driver
##     (`fair_mean_*_ssp245harm.csv` -- which our baseline cube reproduces to 4e-16 degC, so
##     the splice removes only per-config HISTORY spread), post-2014 the config's own
##     anomaly about the 1995-2014 pivot. The policy starts 2026 > 2014, so cref/mref are
##     identical across arms and the splice PRESERVES the difference exactly.
##     --forcing=raw feeds the cubes as-is, which is what the BRICK arms in this pipeline do.
##   * --tap: the Greenland onset tap (4.69 K on the config's own GMST), the shipped pulse-arm
##     choice; [TAP-CROSSING] counts draws that cross only under one arm. Default OFF here
##     because the BRICK comparators have no such mechanism; run both and REPORT.
##   * N draws = 4 chains x n_per_chain (default 500 -> 2000) assigned to the 841 configs by
##     the seeded permutation. BRICK arms pair 841 draws to 841 configs; medians are comparable,
##     the Monte Carlo bars differ.
##
##   julia --project=julia_v2 julia/scope_slr_egu_ladrillo.jl [n_per_chain] \
##        --base=<gmst cube> --policy=<gmst cube> --arm=noegu50 [--forcing=spliced|raw] [--tap]
##        [--tag=L24] [--maxrows=N] [--mean-tag=ssp245harm]
##   (the OHC cubes are the gmst paths with "gmst" -> "ohc")
##
## Writes outputs/egu_ladrillo_{cells,draws,gates}_<arm>_<forcing>_<TAG><TAP><SMOKE>.csv
## ============================================================================
using CSV, DataFrames, Statistics, Printf, Mimi, Random

include(joinpath(@__DIR__, "ladrillo_projection.jl"))

const REPO   = LADRILLO_REPO
const SEEDS  = [2026, 2027, 2028, 2029]
const NITER  = 2000000
const NBURN  = 1000000

argval(flag, dflt) = let i = findfirst(a -> startswith(a, flag), ARGS)
    i === nothing ? dflt : ARGS[i][(length(flag) + 1):end]
end

const TAG      = argval("--tag=", "L24")
const ARM      = argval("--arm=", "")
const BASE_G   = argval("--base=", "")
const POL_G    = argval("--policy=", "")
const FORCING  = argval("--forcing=", "spliced")
const MEAN_TAG = argval("--mean-tag=", "ssp245harm")
const MAXROWS  = let v = argval("--maxrows=", ""); v == "" ? nothing : parse(Int, v); end
const SMOKE    = MAXROWS !== nothing
const N_TARGET = let p = findfirst(a -> !startswith(a, "--"), ARGS)
    p === nothing ? 500 : parse(Int, ARGS[p])
end
const TAP_ON   = "--tap" in ARGS
ARM == "" && error("--arm=<name> is required (names the outputs)")
isfile(BASE_G) || error("--base cube not found: $(BASE_G)")
isfile(POL_G)  || error("--policy cube not found: $(POL_G)")
FORCING in ("spliced", "raw") || error("--forcing must be spliced or raw")
ohc_path(p) = replace(p, "gmst" => "ohc")
for p in (ohc_path(BASE_G), ohc_path(POL_G)); isfile(p) || error("OHC cube not found: $(p)"); end

const POLICY_YEAR = 2026            # the EGU removal starts in EPA's baseline year
const HORIZONS    = [2050, 2100, 2150, 2200, 2300]
const Y0, Y1      = 1850, 2300
const YEARS       = collect(Y0:Y1)
const COMPONENTS  = [:glaciers, :gis, :ais, :te, :lws, :total]
const SUM_PARTS   = [:glaciers, :gis, :ais, :te, :lws]
const SUM_TOL_CM  = 1e-6
const PAIR_SEED   = 2026
const SPLICE_YEAR = 2014
const ARMS        = ["base", "policy"]
const CUBE_OHC_UNIT = "1e22 J"     # what FaIRtoFrEDI's dumps write; Ladrillo's ohc input unit

chain_path(sd) = joinpath(REPO, "outputs/mcmc", "chain_$(TAG)_seed$(sd)_n$(NITER).csv")
hdr(sd) = String.(propertynames(CSV.read(chain_path(sd), DataFrame; limit = 0)))
for sd in SEEDS; isfile(chain_path(sd)) || error("missing chain $(chain_path(sd))"); end
const VARIANT = ladrillo_gis_variant(hdr(SEEDS[1]))
const TAP_TAG = TAP_ON ? "_tap$(replace(string(GIS_TAP_CELL.onset_K), "." => "p"))K" *
                         "_V$(replace(string(GIS_TAP_CELL.V_m), "." => "p"))m" *
                         "_tau$(Int(GIS_TAP_CELL.tau_yr))" : ""
const OUTSTEM = "$(ARM)_$(FORCING)_$(TAG)$(TAP_TAG)$(SMOKE ? "_SMOKE" : "")"

function read_draws(sd)
    need = ladrillo_used_cols(VARIANT)
    h = hdr(sd)
    rd = ladrillo_gis_needs_native(h) ?
        vcat(setdiff(need, LADRILLO_GIS_SLOW_NATIVE_COLS),
             LADRILLO_GIS_SLOW_REPARAM_COLS) |> unique : need
    df = SMOKE ? CSV.read(chain_path(sd), DataFrame; select = rd, limit = MAXROWS) :
                 CSV.read(chain_path(sd), DataFrame; select = rd)
    df = df[((SMOKE ? 0 : NBURN) + 1):end, :]
    step = max(1, nrow(df) ÷ N_TARGET)
    idx = collect(1:step:nrow(df))
    d = ladrillo_native_greenland!(df[idx[1:min(N_TARGET, length(idx))], :]); df = nothing; GC.gc(); d
end

@printf("LADRILLO EGU SENSITIVITY | arm %s | tag %s | forcing=%s%s%s\n", ARM, TAG, FORCING,
        TAP_ON ? "  [TAPPED Greenland]" : "  [untapped Greenland]",
        SMOKE ? "  ** SMOKE (--maxrows=$(MAXROWS)) **" : "")
@printf("  base   : %s\n  policy : %s\n  climate: FaIR 2.2.4 calib 1.6.0, per-config cubes, OHC %s\n",
        basename(BASE_G), basename(POL_G), CUBE_OHC_UNIT); flush(stdout)

const DRAWS = [(@printf("  reading chain seed%d ...\n", sd); flush(stdout); read_draws(sd)) for sd in SEEDS]
const ROWS  = [r for d in DRAWS for r in eachrow(d)]
const NDRAW = length(ROWS)

## ---- the paired climate cubes ------------------------------------------------------------
const CG = Dict("base" => CSV.read(BASE_G, DataFrame), "policy" => CSV.read(POL_G, DataFrame))
const CO = Dict("base" => CSV.read(ohc_path(BASE_G), DataFrame), "policy" => CSV.read(ohc_path(POL_G), DataFrame))
const CFG = [c for c in String.(propertynames(CG["base"])) if startswith(c, "cfg_")]
const NCFG = length(CFG)
for a in ARMS
    Int.(CG[a].year) == YEARS || error("$(a) gmst cube year axis is not $(Y0):$(Y1)")
    Int.(CO[a].year) == YEARS || error("$(a) ohc cube year axis is not $(Y0):$(Y1)")
end
for a in ARMS, (k, D) in (("gmst", CG), ("ohc", CO))
    cs = [c for c in String.(propertynames(D[a])) if startswith(c, "cfg_")]
    cs == CFG || error("[CUBE-ALIGN] $(k)/$(a) config ORDER differs from gmst/base")
end
## [CUBE-PAIRED] the two cubes are the same climate before the policy year -- exactly.
let ip = findfirst(==(POLICY_YEAR), YEARS) - 1
    w = maximum(maximum(abs.(Float64.(CG["base"][1:ip, c]) .- Float64.(CG["policy"][1:ip, c]))) for c in CFG)
    wo = maximum(maximum(abs.(Float64.(CO["base"][1:ip, c]) .- Float64.(CO["policy"][1:ip, c]))) for c in CFG)
    @printf("[CUBE-PAIRED] max |policy - base| before %d: gmst %.3e degC, ohc %.3e %s (bound EXACT 0)  %s\n",
            POLICY_YEAR, w, wo, CUBE_OHC_UNIT, (w == 0.0 && wo == 0.0) ? "PASS" : "FAIL")
    (w == 0.0 && wo == 0.0) || error("[CUBE-PAIRED] the cubes differ before the policy starts")
end

const IREF = findall(y -> LADRILLO_REF[1] <= y <= LADRILLO_REF[2], YEARS)
const MEAN_G = [_yearmap(joinpath(LADRILLO_OBS, "fair_mean_gmst_$(MEAN_TAG).csv"), "gmst_C")[y] for y in YEARS]
const MEAN_O = [_yearmap(joinpath(LADRILLO_OBS, "fair_mean_ohc_$(MEAN_TAG).csv"), "ohc_1e22J")[y] for y in YEARS]
## [MEAN-MATCH] the mean driver the splice pins history to must BE this cube's own mean;
## otherwise the splice would move the operating point by a vintage gap, not a convention.
let m = [mean(Float64.(CG["base"][i, c]) for c in CFG) for i in 1:length(YEARS)]
    w = maximum(abs.(m .- MEAN_G))
    @printf("[MEAN-MATCH] max |cube mean - %s mean driver| = %.3e degC (tol 1e-9)  %s\n",
            MEAN_TAG, w, w <= 1e-9 ? "PASS" : "FAIL")
    w <= 1e-9 || error("[MEAN-MATCH] the cube is not the $(MEAN_TAG) stack; pick --mean-tag to match")
end

function convention(raw::Vector{Float64}, mean_path::Vector{Float64})
    FORCING == "raw" && return raw
    mref, cref = mean(mean_path[IREF]), mean(raw[IREF])
    [y <= SPLICE_YEAR ? mean_path[i] : mref + (raw[i] - cref) for (i, y) in enumerate(YEARS)]
end
gmst_of(a, c) = convention(Float64.(CG[a][!, c]), MEAN_G)
ohc_of(a, c)  = convention(Float64.(CO[a][!, c]), MEAN_O)

## ---- the pairing: ONE assignment, both arms ----------------------------------------------
const ASSIGN = let rng = MersenneTwister(PAIR_SEED)
    a = Int[]
    while length(a) < NDRAW; append!(a, randperm(rng, NCFG)); end
    a[1:NDRAW]
end
const CFG_OF_DRAW = [CFG[i] for i in ASSIGN]
const RAN_CFG = Dict(a => fill("", NDRAW) for a in ARMS)
const RAN_ROW = Dict(a => fill(-1, NDRAW) for a in ARMS)

function run_into!(out, idx, g, o, arm, cfgname)
    bf = ladrillo_setup(ssp = "ssp245", y0 = Y0, y1 = Y1, gis_variant = VARIANT, gmst = g, ohc = o)
    TAP_ON && ladrillo_set_tap!(bf)
    for k in idx
        ladrillo_run_draw!(bf, ROWS[k])
        RAN_CFG[arm][k] = cfgname
        RAN_ROW[arm][k] = k
        for c in COMPONENTS
            out[c][k, :] = coalesce.(ladrillo_series(bf, c), NaN)
        end
    end
    bf
end
alloc() = Dict(c => Matrix{Float64}(undef, NDRAW, length(YEARS)) for c in COMPONENTS)

const RES = Dict(a => alloc() for a in ARMS)
let groups = Dict{String, Vector{Int}}()
    for k in 1:NDRAW; push!(get!(groups, CFG_OF_DRAW[k], Int[]), k); end
    @printf("\n  %d draws over %d configs; running BOTH arms per config ...\n", NDRAW, length(groups)); flush(stdout)
    n = 0; t0 = time()
    for (c, idx) in groups
        for a in ARMS; run_into!(RES[a], idx, gmst_of(a, c), ohc_of(a, c), a, c); end
        n += 1
        n % 100 == 0 && (@printf("    %d/%d configs  (%.0f s)\n", n, length(groups), time() - t0); flush(stdout))
    end
    @printf("  done: %d configs x 2 arms in %.0f s\n", n, time() - t0)
end

yidx(y) = findfirst(==(y), YEARS)
const DIFF = Dict(c => RES["base"][c] .- RES["policy"][c] for c in COMPONENTS)   # AVOIDED = base - policy

## ==========================================================================
## GATES (the pulse arm's identity gates, with the policy year in place of the pulse year)
## ==========================================================================
@printf("\n%s\nGATES\n%s\n", repeat("=", 92), repeat("=", 92))
rowsg = DataFrame(gate = String[], key = String[], value = Float64[], verdict = String[])
push_g!(g, k, v, ok) = push!(rowsg, (g, k, Float64(v), ok ? "PASS" : "FAIL"))

const REACH      = LADRILLO_GIS_SHAPE_WIN ÷ 2
const IDENT_LAST = POLICY_YEAR - REACH - 1
const NO_REACHBACK = [:glaciers, :te, :lws]

let iy = yidx(IDENT_LAST), worst = 0.0
    for c in COMPONENTS
        m = maximum(abs.(@view DIFF[c][:, 1:iy])); worst = max(worst, m)
        push_g!("PRE-POLICY-ZERO", "max_abs_cm_$(c)", m, m == 0.0)
    end
    @printf("  [PRE-POLICY-ZERO] max |base - policy| over %d-%d = %.3e cm, all components (bound EXACT 0)  %s\n",
            Y0, IDENT_LAST, worst, worst == 0.0 ? "PASS" : "FAIL")
    worst == 0.0 || error("[PRE-POLICY-ZERO] the arms differ before the shape window can reach")
end
let iy = yidx(POLICY_YEAR) - 1, worst = 0.0, wc = ""
    for c in NO_REACHBACK
        m = maximum(abs.(@view DIFF[c][:, 1:iy])); m > worst && ((worst, wc) = (m, String(c)))
        push_g!("NO-REACHBACK", "max_abs_cm_$(c)", m, m == 0.0)
    end
    @printf("  [NO-REACHBACK] %s max |diff| through %d = %.3e cm (bound EXACT 0)  %s\n",
            join(String.(NO_REACHBACK), "/"), POLICY_YEAR - 1, worst, worst == 0.0 ? "PASS" : "FAIL")
    worst == 0.0 || error("[NO-REACHBACK] $(wc) moved before the policy and has no mechanism to")
end
let bad = count(k -> RAN_CFG["base"][k] != RAN_CFG["policy"][k], 1:NDRAW),
    badr = count(k -> RAN_ROW["base"][k] != RAN_ROW["policy"][k], 1:NDRAW)
    @printf("  [DRAW-PAIRING] %d/%d draws saw a different CONFIG across arms, %d a different DRAW ROW  %s\n",
            bad, NDRAW, badr, (bad == 0 && badr == 0) ? "PASS" : "FAIL")
    push_g!("DRAW-PAIRING", "config_mismatches", bad, bad == 0)
    push_g!("DRAW-PAIRING", "row_mismatches", badr, badr == 0)
    (bad == 0 && badr == 0) || error("[DRAW-PAIRING] the arms are not paired")
end
let used = length(unique(CFG_OF_DRAW)), cnt = [count(==(c), CFG_OF_DRAW) for c in unique(CFG_OF_DRAW)]
    @printf("  [PAIRING] %d of %d configs used, each %d-%d times (seed %d), ONE assignment for both arms\n",
            used, NCFG, minimum(cnt), maximum(cnt), PAIR_SEED)
    push_g!("PAIRING", "configs_used", used, used == min(NCFG, NDRAW))
end
let worst = 0.0
    for H in HORIZONS
        s = sum(DIFF[c][:, yidx(H)] for c in SUM_PARTS)
        worst = max(worst, maximum(abs.(s .- DIFF[:total][:, yidx(H)])))
    end
    @printf("  [SUM] max |sum(parts) - total| in the DIFFERENCE = %.3e cm (tol %.0e)  %s\n",
            worst, SUM_TOL_CM, worst <= SUM_TOL_CM ? "PASS" : "FAIL")
    push_g!("SUM", "max_abs_cm", worst, worst <= SUM_TOL_CM)
end
for H in HORIZONS
    v = DIFF[:total][:, yidx(H)]; neg = count(<(0.0), v) / length(v)
    @printf("  [SIGN] %d: median avoided %+.5f cm, %.2f%% of draws negative  %s\n", H, median(v), 100neg, median(v) > 0 ? "PASS" : "FAIL")
    push_g!("SIGN", "median_cm_$(H)", median(v), median(v) > 0)
    push_g!("SIGN", "frac_negative_$(H)", neg, true)
end
if TAP_ON
    let n = 0
        for k in 1:NDRAW
            g = gmst_of("base", CFG_OF_DRAW[k]); gp = gmst_of("policy", CFG_OF_DRAW[k])
            (maximum(gp) < GIS_TAP_CELL.onset_K) && (maximum(g) >= GIS_TAP_CELL.onset_K) && (n += 1)
        end
        @printf("  [TAP-CROSSING] %d of %d draws (%.3f%%) cross the %.2f K onset ONLY in the baseline arm\n",
                n, NDRAW, 100n / NDRAW, GIS_TAP_CELL.onset_K)
        push_g!("TAP-CROSSING", "n_draws_crossing", n, true)
    end
end
CSV.write(joinpath(REPO, "outputs", "egu_ladrillo_gates_$(OUTSTEM).csv"), rowsg)

## ==========================================================================
## RESULTS
## ==========================================================================
cells = DataFrame(arm = String[], model = String[], forcing = String[], tap = Bool[], component = String[],
                  horizon = Int[], n_draws = Int[], base_med_cm = Float64[], policy_med_cm = Float64[],
                  avoided_med_cm = Float64[], avoided_mean_cm = Float64[], avoided_p2_5_cm = Float64[],
                  avoided_p97_5_cm = Float64[], avoided_p05_cm = Float64[], avoided_p95_cm = Float64[])
@printf("\n%s\nAVOIDED SLR (base - policy), arm %s, Ladrillo %s, cm rel %d-%d, %s%s\n%s\n",
        repeat("=", 92), ARM, TAG, LADRILLO_REF[1], LADRILLO_REF[2], FORCING, TAP_ON ? ", TAPPED" : ", untapped", repeat("=", 92))
@printf("  %-9s %-6s %10s %12s %12s %12s %12s\n", "comp", "horiz", "base med", "avoided med", "avoided mean", "p2.5", "p97.5")
for c in COMPONENTS, H in HORIZONS
    i = yidx(H); b, p, d = RES["base"][c][:, i], RES["policy"][c][:, i], DIFF[c][:, i]
    push!(cells, (ARM, "Ladrillo $(TAG)", FORCING, TAP_ON, String(c), H, NDRAW, median(b), median(p),
                  median(d), mean(d), quantile(d, 0.025), quantile(d, 0.975), quantile(d, 0.05), quantile(d, 0.95)))
    @printf("  %-9s %-6d %10.3f %12.4f %12.4f %12.4f %12.4f\n", c, H, median(b), median(d), mean(d),
            quantile(d, 0.025), quantile(d, 0.975))
end
CSV.write(joinpath(REPO, "outputs", "egu_ladrillo_cells_$(OUTSTEM).csv"), cells)

## per-draw avoided totals at the horizons (+ the config and posterior row each draw ran on)
draws = DataFrame(draw = 1:NDRAW, cfg = CFG_OF_DRAW)
for c in COMPONENTS, H in HORIZONS
    draws[!, "avoided_$(c)_$(H)_cm"] = DIFF[c][:, yidx(H)]
end
CSV.write(joinpath(REPO, "outputs", "egu_ladrillo_draws_$(OUTSTEM).csv"), draws)
@printf("\nwrote outputs/egu_ladrillo_{cells,draws,gates}_%s.csv\n", OUTSTEM)
@printf("PROVENANCE: Ladrillo %s (chains seeds %s, %d draws), FaIR 2.2.4 calib 1.6.0 per-config cubes %s / %s, forcing %s, mean driver %s, pair seed %d, tap %s\n",
        TAG, join(string.(SEEDS), "/"), NDRAW, basename(BASE_G), basename(POL_G), FORCING, MEAN_TAG, PAIR_SEED, TAP_ON)
