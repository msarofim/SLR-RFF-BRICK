## ============================================================================
## diag_pulse_size_vv_ladder.jl -- IS 10 GtCO2 INSIDE THE LINEAR REGIME FOR LADRILLO L24?
##
## THE QUESTION (Marcus, 2026-09-03). The van Vuuren pulse spec is 10 GtCO2, and memory
## `dais_fastdynamics_quant` records a MEASURED 9-20% per-tonne OVERSTATEMENT of the median
## at 10 GtCO2 -- but that was BRICK-Mengel, in July, on a different posterior. The ladder
## has never been re-run for Ladrillo L24, so every per-tonne number stages 3-5 will emit
## rests on an untested assumption. `diag_pulse_size_robustness.jl` is the BRICK-Mengel
## ancestor of this file; the method is its method.
##
## TWO EFFECTS PULL OPPOSITE WAYS AND A LADDER SEPARATES THEM.
##   * SMALL pulses suffer QUANTIZATION -- DAIS fires on a hard annual step, so few draws
##     change their integer year count and the estimate gets noisy. MEASURED and found
##     UNBIASED (`pulse_threshold_is_variance_not_bias`): mean(integer) / mean(continuous
##     time above threshold) = 0.917-1.039 over 42 cells. So this is variance, not drift.
##   * LARGE pulses suffer GENUINE NONLINEARITY -- disintegration compounds as the ice
##     radius shrinks, and the AIS geometry is not affine.
## A per-tonne median that is FLAT across the ladder says 10 Gt is safe; a monotone rise
## toward the top says it is not, and the size must come down.
##
## METHOD. Every rung's climate is the REAL 10-GtCO2 pair's IRF, scaled:
##     GMST_pulse(P) = GMST_base + (P/P0) * (GMST_pulse(P0) - GMST_base)   [same for OHC]
## ⚠ SCALING IS NOT ASSUMED, IT IS GATED. A REAL 1-GtCO2 FaIR cube is built alongside
## (`build_fair_pulse_vv_v160.py --pulse-size=1`) and [IRF-VALID] pushes BOTH the real and
## the scaled 1-Gt climate through Ladrillo and compares them per draw. If FaIR's own
## non-linearity mattered, that gate is where it shows.
##
## PAIRED DISCIPLINE. One process, one ROWS list, one PAIR_SEED permutation, ONE baseline
## reused by every rung -- so a rung-to-rung difference cannot be a re-seeded baseline.
## [P0-IDENTITY] then proves the P=10 rung against the SHIPPED stage-2 draws file rather
## than trusting that this file reproduces it.
##
##   julia --project=julia_v2 julia/diag_pulse_size_vv_ladder.jl [n_per_chain] [--marker=M]
##        [--specie=CO2] [--tag=L24] [--tap] [--maxrows=N]
## Writes outputs/pulse_ladder_{cells,draws,gates}_vv<M>_<SPECIE>_<TAG><TAP_TAG>.csv
## ============================================================================
using CSV, DataFrames, Statistics, Printf, Mimi, Random

include(joinpath(@__DIR__, "ladrillo_projection.jl"))

const REPO  = LADRILLO_REPO
const SEEDS = [2026, 2027, 2028, 2029]
const NITER = 2000000
const NBURN = 1000000

argval(flag, dflt) = let i = findfirst(a -> startswith(a, flag), ARGS)
    i === nothing ? dflt : ARGS[i][(length(flag) + 1):end]
end

const TAG     = argval("--tag=", "L24")
const MARKER  = argval("--marker=", "M")
const SPECIE  = argval("--specie=", "CO2")
const MAXROWS = let v = argval("--maxrows=", ""); v == "" ? nothing : parse(Int, v); end
const SMOKE   = MAXROWS !== nothing
const N_TARGET = let p = findfirst(a -> !startswith(a, "--"), ARGS)
    p === nothing ? 500 : parse(Int, ARGS[p])
end
const CHAIN_TAG = argval("--chain-tag=", TAG)

## The reference pair the IRF comes from, and the validation pair the gate uses. Both are
## FILENAMES as well as numbers -- `size_lab` in build_fair_pulse_vv_v160.py writes "10Gt"
## and "1Gt" from exactly these, and letting the two drift is the 1000x error class.
const SPECIE_SPEC = Dict(
    "CO2" => (p0 = 10.0, p0_tag = "10Gt", pv = 1.0, pv_tag = "1Gt", unit = "GtCO2"),
    "CH4" => (p0 = 1.0,  p0_tag = "1Gt",  pv = 0.1, pv_tag = "0p1Gt", unit = "GtCH4"))
@assert haskey(SPECIE_SPEC, SPECIE)
const SPEC = SPECIE_SPEC[SPECIE]
## The rung set brackets the shipped size by 100x below and 3x above. 0.1 is small enough
## that quantization dominates and 30 large enough that compounding must show if it exists;
## anything flat over that range is flat where it is used.
const LADDER = [0.1, 0.3, 1.0, 3.0, 10.0, 30.0]

const PULSE_YEAR  = 2030
const Y0, Y1      = 1850, 2300
const YEARS       = collect(Y0:Y1)
const HORIZONS    = [2100, 2150, 2300]
const COMPONENTS  = [:glaciers, :gis, :ais, :te, :lws, :total]
const PAIR_SEED   = 2026
const SPLICE_YEAR = 2014
const TANT0       = LADRILLO_AIS_TANT0

const TAP_ON  = "--tap" in ARGS
const TAP_TAG = TAP_ON ? "_tap$(replace(string(GIS_TAP_CELL.onset_K), "." => "p"))K" *
                         "_V$(replace(string(GIS_TAP_CELL.V_m), "." => "p"))m" *
                         "_tau$(Int(GIS_TAP_CELL.tau_yr))" : ""
const OUTSTEM = "vv$(MARKER)_$(SPECIE)_$(TAG)$(TAP_TAG)$(SMOKE ? "_SMOKE" : "")"

cube(kind, arm, tag) = joinpath(LADRILLO_OBS,
    "fair_cube_$(kind)_vv$(MARKER)_$(arm)_$(SPECIE)_$(tag)_$(PULSE_YEAR)_raw.csv")
chain_path(sd) = joinpath(REPO, "outputs/mcmc", "chain_$(CHAIN_TAG)_seed$(sd)_n$(NITER).csv")
hdr(sd) = String.(propertynames(CSV.read(chain_path(sd), DataFrame; limit = 0)))
for sd in SEEDS; isfile(chain_path(sd)) || error("missing chain $(chain_path(sd))"); end
const VARIANT = ladrillo_gis_variant(hdr(SEEDS[1]))

for k in ("gmst", "ohc"), (a, t) in (("pulsebase", SPEC.p0_tag), ("pulse", SPEC.p0_tag),
                                     ("pulsebase", SPEC.pv_tag), ("pulse", SPEC.pv_tag))
    isfile(cube(k, a, t)) || error("missing cube $(cube(k, a, t))\n  build it with " *
        "FaIRtoFrEDI/scripts/build_fair_pulse_vv_v160.py --marker=$(MARKER) " *
        "--specie=$(SPECIE) --pulse-size=$(t == SPEC.p0_tag ? SPEC.p0 : SPEC.pv)")
end

function read_draws(sd)
    need = ladrillo_used_cols(VARIANT); h = hdr(sd)
    rd = ladrillo_gis_needs_native(h) ?
        vcat(setdiff(need, LADRILLO_GIS_SLOW_NATIVE_COLS), LADRILLO_GIS_SLOW_REPARAM_COLS) |> unique : need
    df = SMOKE ? CSV.read(chain_path(sd), DataFrame; select = rd, limit = MAXROWS) :
                 CSV.read(chain_path(sd), DataFrame; select = rd)
    df = df[((SMOKE ? 0 : NBURN) + 1):end, :]
    step = max(1, nrow(df) ÷ N_TARGET)
    idx = collect(1:step:nrow(df))
    d = ladrillo_native_greenland!(df[idx[1:min(N_TARGET, length(idx))], :]); df = nothing; GC.gc(); d
end

@printf("LADRILLO PULSE-SIZE LADDER | vv%s | %s at %d | tag %s%s%s\n",
        MARKER, SPECIE, PULSE_YEAR, TAG, TAP_ON ? "  [TAPPED]" : "  [untapped]",
        SMOKE ? "  ** SMOKE **" : "")
@printf("  ladder %s %s   IRF from the real %g pair, validated against the real %g pair\n",
        string(LADDER), SPEC.unit, SPEC.p0, SPEC.pv)
flush(stdout)

const DRAWS = [(@printf("  reading chain seed%d ...\n", sd); flush(stdout); read_draws(sd)) for sd in SEEDS]
const ROWS  = [r for d in DRAWS for r in eachrow(d)]
const NDRAW = length(ROWS)

## ---- the cubes; the IRF; and the two identity checks that come free ----------------
const CG0 = Dict(a => CSV.read(cube("gmst", a, SPEC.p0_tag), DataFrame) for a in ("pulsebase", "pulse"))
const CO0 = Dict(a => CSV.read(cube("ohc",  a, SPEC.p0_tag), DataFrame) for a in ("pulsebase", "pulse"))
const CGV = Dict(a => CSV.read(cube("gmst", a, SPEC.pv_tag), DataFrame) for a in ("pulsebase", "pulse"))
const COV = Dict(a => CSV.read(cube("ohc",  a, SPEC.pv_tag), DataFrame) for a in ("pulsebase", "pulse"))
const CFG = [c for c in String.(propertynames(CG0["pulsebase"])) if startswith(c, "cfg_")]
for (lab, D) in (("gmst/P0", CG0), ("ohc/P0", CO0), ("gmst/Pv", CGV), ("ohc/Pv", COV)), a in keys(D)
    Int.(D[a].year) == YEARS || error("$(lab)/$(a) year axis is not $(Y0):$(Y1)")
    cs = [c for c in String.(propertynames(D[a])) if startswith(c, "cfg_")]
    cs == CFG || error("[CUBE-ALIGN] $(lab)/$(a) config ORDER differs from gmst/P0/pulsebase")
end

const IREF  = findall(y -> LADRILLO_REF[1] <= y <= LADRILLO_REF[2], YEARS)
const MEAN_G = [_yearmap(joinpath(LADRILLO_OBS, "fair_mean_gmst_vv$(MARKER).csv"), "gmst_C")[y] for y in YEARS]
const MEAN_O = [_yearmap(joinpath(LADRILLO_OBS, "fair_mean_ohc_vv$(MARKER).csv"), "ohc_1e22J")[y] for y in YEARS]
function convention(raw::Vector{Float64}, mp::Vector{Float64})
    mref, cref = mean(mp[IREF]), mean(raw[IREF])
    [y <= SPLICE_YEAR ? mp[i] : mref + (raw[i] - cref) for (i, y) in enumerate(YEARS)]
end

rowsg = DataFrame(gate = String[], key = String[], value = Float64[], verdict = String[])
push_g!(g, k, v, ok) = push!(rowsg, (g, k, Float64(v), ok ? "PASS" : "FAIL"))

## [BASE-IDENTITY] the two builds' BASELINE arms must be the same climate, exactly. They
## are separate FaIR invocations of the same emissions, so this is a real check on the
## builder's determinism -- and if it fails, every rung below compares two baselines.
let w = 0.0
    for c in CFG
        w = max(w, maximum(abs.(Float64.(CG0["pulsebase"][!, c]) .- Float64(1) .* Float64.(CGV["pulsebase"][!, c]))))
        w = max(w, maximum(abs.(Float64.(CO0["pulsebase"][!, c]) .- Float64.(COV["pulsebase"][!, c]))))
    end
    @printf("\n  [BASE-IDENTITY] max |P0 base - Pv base| over gmst+ohc = %.3e   %s\n",
            w, w == 0.0 ? "PASS" : "FAIL")
    push_g!("BASE-IDENTITY", "max_abs", w, w == 0.0)
end

## climate per config: baseline, the P0 IRF, and the REAL validation pulse
const GB   = Dict(c => Float64.(CG0["pulsebase"][!, c]) for c in CFG)
const OB   = Dict(c => Float64.(CO0["pulsebase"][!, c]) for c in CFG)
const IRFG = Dict(c => Float64.(CG0["pulse"][!, c]) .- GB[c] for c in CFG)
const IRFO = Dict(c => Float64.(CO0["pulse"][!, c]) .- OB[c] for c in CFG)
const GRV  = Dict(c => Float64.(CGV["pulse"][!, c]) for c in CFG)
const ORV  = Dict(c => Float64.(COV["pulse"][!, c]) for c in CFG)

const ASSIGN = let rng = MersenneTwister(PAIR_SEED); a = Int[]
    while length(a) < NDRAW; append!(a, randperm(rng, length(CFG))); end; a[1:NDRAW]
end
const CFG_OF_DRAW = [CFG[i] for i in ASSIGN]
const BUILD_SSP = argval("--build-ssp=", "ssp245")

## ---- the run ------------------------------------------------------------------------
## ARMS is the baseline plus one entry per rung plus the real validation rung. Every arm
## is run inside the SAME config group as the baseline, back to back, so a drift in global
## state cannot cancel between a rung and the baseline it is differenced against.
const ARM_SPEC = vcat([("base", 0.0, :base)],
                      [("P$(replace(string(p), "." => "p"))", p, :scaled) for p in LADDER],
                      [("real$(SPEC.pv_tag)", SPEC.pv, :real)])
alloc() = Dict(c => Matrix{Float64}(undef, NDRAW, length(YEARS)) for c in COMPONENTS)
const RES = Dict(a[1] => alloc() for a in ARM_SPEC)

function climate(name, p, kind, c)
    kind === :base   && return (GB[c], OB[c])
    kind === :real   && return (GRV[c], ORV[c])
    s = p / SPEC.p0
    return (GB[c] .+ s .* IRFG[c], OB[c] .+ s .* IRFO[c])
end

let groups = Dict{String, Vector{Int}}()
    for k in 1:NDRAW; push!(get!(groups, CFG_OF_DRAW[k], Int[]), k); end
    @printf("\n  %d draws over %d configs x %d arms ...\n", NDRAW, length(groups), length(ARM_SPEC))
    flush(stdout); n = 0
    for (c, idx) in groups
        for (name, p, kind) in ARM_SPEC
            g_raw, o_raw = climate(name, p, kind, c)
            bf = ladrillo_setup(ssp = BUILD_SSP, y0 = Y0, y1 = Y1, gis_variant = VARIANT,
                                gmst = convention(g_raw, MEAN_G), ohc = convention(o_raw, MEAN_O))
            TAP_ON && ladrillo_set_tap!(bf)
            for k in idx
                ladrillo_run_draw!(bf, ROWS[k])
                for comp in COMPONENTS; RES[name][comp][k, :] = coalesce.(ladrillo_series(bf, comp), NaN); end
            end
        end
        n += 1
        n % 100 == 0 && (@printf("    %d/%d configs\n", n, length(groups)); flush(stdout))
    end
end

yidx(y) = findfirst(==(y), YEARS)
diffof(name, comp) = RES[name][comp] .- RES["base"][comp]

## ---- the closed-form threshold classifier, as in diag_ais_crossing_pulse_vv.jl -------
const AMP = [Float64(r["ais_gmst_amp"]) for r in ROWS]
const THR = [Float64(r["antarctic_temp_threshold"]) for r in ROWS]
function tant(name, p, kind, k)
    g_raw, _ = climate(name, p, kind, CFG_OF_DRAW[k])
    g = convention(g_raw, MEAN_G)
    T = Vector{Float64}(undef, length(YEARS)); T[1] = -Inf
    @inbounds for t in 2:length(YEARS); T[t] = AMP[k] * g[t - 1] + TANT0; end
    T
end
nyears_above(T, thr, iH) = count(>(thr), @view T[2:iH])

@printf("\n%s\nGATES\n%s\n", repeat("=", 92), repeat("=", 92))

## [P0-IDENTITY] the shipped stage-2 run, reproduced. Same chains, same thinning, same
## permutation, same tap -- so the P=10 rung must land on the SHIPPED per-draw totals. A
## ladder that cannot reproduce the number it is auditing is auditing something else.
let sp = joinpath(REPO, "outputs", "pulse_ladrillo_draws_vv$(MARKER)_$(SPECIE)_$(SPEC.p0_tag)_" *
                  "$(PULSE_YEAR)_spliced_$(TAG)$(TAP_TAG).csv")
    if isfile(sp) && !SMOKE
        sh = CSV.read(sp, DataFrame); w = 0.0
        for H in HORIZONS
            s = sh[(sh.horizon .== H) .& (sh.component .== "total"), :]; sort!(s, :draw)
            mine = diffof("P10p0", :total)[:, yidx(H)]
            nrow(s) == NDRAW || error("[P0-IDENTITY] shipped file has $(nrow(s)) draws, not $(NDRAW)")
            w = max(w, maximum(abs.(s.diff_cm .- mine)))
        end
        @printf("  [P0-IDENTITY] max |ladder P0 - shipped stage 2| = %.3e cm   %s\n",
                w, w <= 1e-9 ? "PASS" : "FAIL")
        push_g!("P0-IDENTITY", "max_abs_cm", w, w <= 1e-9)
    else
        @printf("  [P0-IDENTITY] SKIPPED -- %s\n", SMOKE ? "smoke run" : "no shipped file at $(basename(sp))")
        push_g!("P0-IDENTITY", "skipped", 1, true)
    end
end

## [IRF-VALID] the scaled climate against the REAL one, THROUGH Ladrillo, per draw. This is
## the gate that makes the ladder's method legitimate; without it every rung but P0 is an
## assumption. ⚠ It compares the two 1-Gt arms, so it is an ORDERING against the SIGNAL:
## the real-vs-scaled disagreement must be small COMPARED TO the response itself
## (`tolerance_scaled_to_spread`), not small against a number picked here.
let name_s = "P1p0"
    for H in HORIZONS
        a = diffof(name_s, :total)[:, yidx(H)]
        b = diffof("real$(SPEC.pv_tag)", :total)[:, yidx(H)]
        d = maximum(abs.(a .- b)); sig = median(abs.(b))
        ok = d < sig
        @printf("  [IRF-VALID] %d: max |scaled - real| %.3e cm  vs  median |real| %.3e cm  (%.2f%%)  %s\n",
                H, d, sig, 100d / sig, ok ? "PASS" : "FAIL")
        push_g!("IRF-VALID", "max_abs_cm_$(H)", d, ok)
        push_g!("IRF-VALID", "pct_of_median_$(H)", 100d / sig, ok)
    end
end

## ---- the ladder ---------------------------------------------------------------------
cells = DataFrame(marker = String[], specie = String[], pulse_Gt = Float64[], arm = String[],
                  horizon = Int[], component = String[], median_cm = Float64[], mean_cm = Float64[],
                  per_Gt_median = Float64[], per_Gt_mean = Float64[], p_fired = Float64[],
                  smooth_term_cm = Float64[], premium_cm = Float64[])
@printf("\n%s\nTHE LADDER -- per-%s, TOTAL and AIS\n%s\n", repeat("=", 92), SPEC.unit, repeat("=", 92))
@printf("  %-8s %-6s | %12s %12s | %12s %12s | %7s %11s %11s\n",
        "pulse", "horiz", "tot med/Gt", "tot mean/Gt", "ais med/Gt", "ais mean/Gt",
        "p_fired", "smooth/Gt", "premium/Gt")
const TB = [tant("base", 0.0, :base, k) for k in 1:NDRAW]
for (name, p, kind) in ARM_SPEC
    kind === :base && continue
    TP = [tant(name, p, kind, k) for k in 1:NDRAW]
    for H in HORIZONS
        iH = yidx(H)
        fired = [nyears_above(TP[k], THR[k], iH) != nyears_above(TB[k], THR[k], iH) for k in 1:NDRAW]
        pf = count(fired) / NDRAW
        for comp in (:total, :ais)
            v = diffof(name, comp)[:, iH]
            sm = .!fired
            e_sm = any(sm)    ? mean(v[sm])    : 0.0
            e_fi = any(fired) ? mean(v[fired]) : 0.0
            push!(cells, (MARKER, SPECIE, p, name, H, String(comp), median(v), mean(v),
                          median(v) / p, mean(v) / p, pf,
                          (1 - pf) * e_sm / p, pf * e_fi / p))
        end
        tt = diffof(name, :total)[:, iH]; aa = diffof(name, :ais)[:, iH]
        sm = .!fired
        e_sm = any(sm) ? mean(aa[sm]) : 0.0; e_fi = any(fired) ? mean(aa[fired]) : 0.0
        @printf("  %-8s %-6d | %12.4e %12.4e | %12.4e %12.4e | %6.2f%% %11.4e %11.4e\n",
                name, H, median(tt) / p, mean(tt) / p, median(aa) / p, mean(aa) / p,
                100pf, (1 - pf) * e_sm / p, pf * e_fi / p)
    end
end

## [FLAT] the actual question, as an ORDERING between MEASURED quantities: does the P0 rung
## sit inside the spread of the rungs BELOW it? Reported per horizon for TOTAL and AIS, and
## the small-pulse limit is taken as the 0.1-1.0 Gt mean rather than any single rung, since
## those rungs are the noisy ones.
for comp in ("total", "ais"), H in HORIZONS
    sub = cells[(cells.component .== comp) .& (cells.horizon .== H) .& (cells.arm .!= "real$(SPEC.pv_tag)"), :]
    small = sub[sub.pulse_Gt .<= 1.0, :]
    p0row = sub[sub.pulse_Gt .== SPEC.p0, :]
    isempty(p0row) && continue
    lim = mean(small.per_Gt_median); at0 = p0row.per_Gt_median[1]
    @printf("  [FLAT] %-5s %d: per-%s median  small-limit %.4e  P0 %.4e  ratio %.4f\n",
            comp, H, SPEC.unit, lim, at0, at0 / lim)
    push_g!("FLAT", "$(comp)_$(H)_ratio_P0_over_smalllimit", at0 / lim, true)
end

CSV.write(joinpath(REPO, "outputs", "pulse_ladder_cells_$(OUTSTEM).csv"), cells)
CSV.write(joinpath(REPO, "outputs", "pulse_ladder_gates_$(OUTSTEM).csv"), rowsg)
@printf("\nwrote outputs/pulse_ladder_cells_%s.csv  (%d rows)\n", OUTSTEM, nrow(cells))
@printf("      outputs/pulse_ladder_gates_%s.csv  (%d rows, %d FAIL)\n",
        OUTSTEM, nrow(rowsg), count(==("FAIL"), rowsg.verdict))
