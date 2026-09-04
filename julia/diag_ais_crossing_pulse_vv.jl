## ============================================================================
## diag_ais_crossing_pulse_vv.jl -- THE THRESHOLD CHANNEL THE PULSE GATES MISS
##
## THE OBSERVATION THAT PROMPTED IT (2026-09-03). `scope_slr_pulse_vv.jl` carries exactly
## one threshold gate, [TAP-CROSSING], and it watches GREENLAND: 6 draws on vvM/CH4, 2 on
## vvHL, ZERO on vvH. Read from the shipped draws files, the ANTARCTIC channel is one to
## two orders of magnitude larger -- vvVL/CH4 has 185 of 2000 draws above 1 cm and 72 above
## 5 cm at 2300, with a maximum of 67.3 cm charged to a 1 GtCH4 pulse, and gis contributes
## 0.17 cm of it. The gate that exists is BLIND to the threshold that dominates, which is
## the `two_statistics_can_be_blind` failure mode.
##
## THE MECHANISM. `antarctic_icesheet_magdep_component.jl:241` fires fast-dynamics
## disintegration on a HARD ANNUAL STEP, `if T_ant[t] > temperature_threshold`, at the full
## rate regardless of how far above ([[ais_binary_form_priced]]). In Ladrillo the map is
## closed form -- `ais_temperature_coefficient = 1/amp`, `ais_temperature_intercept =
## -TANT0/amp` (ladrillo_projection.jl:816-817) -- so
##
##     T_ant[t] = amp * GMST[t-1] + TANT0            (NOTE THE t-1 LAG, line 165)
##
## needs no model run. A pulse can therefore act on the AIS in exactly two ways:
##   (a) BIFURCATION  -- a draw that never crosses at baseline crosses under the pulse, and
##                       is charged a whole disintegration;
##   (b) QUANTIZATION -- a draw that crosses in both arms crosses one INTEGER YEAR earlier,
##                       and is charged one whole year of flux, or zero.
## (b) is the one that decides whether the pulse mean is biased or merely noisy, and it is
## measurable: the CONTINUOUS crossing-date advance dt_cross (linear interpolation of T_ant
## through the threshold) is what a de-quantized model would charge. If mean(dn_int) and
## mean(dt_cross) agree, the annual step adds VARIANCE but no BIAS and the mean is
## rescuable by more draws; if they disagree, the mean is biased and no ensemble size fixes
## it. Nobody has measured which.
##
## ⚠ THIS IS A DIAGNOSTIC OF THE PRODUCTION RUN'S OWN ARITHMETIC, not an independent check.
## It reconstructs the same chains, the same thinning and the same PAIR_SEED permutation the
## driver used, and [CONFIG-IDENTITY] PROVES the reconstruction against the config column
## the driver recorded per draw rather than assuming it.
##
##   julia --project=julia_v2 julia/diag_ais_crossing_pulse_vv.jl [--tag=L24] [--marker=M]
## Writes outputs/diag_ais_crossing_pulse_vv_<TAG>.csv (+ _draws_<TAG>.csv)
## ============================================================================
using CSV, DataFrames, Statistics, Printf, Random

include(joinpath(@__DIR__, "ladrillo_projection.jl"))

const REPO   = LADRILLO_REPO
const SEEDS  = [2026, 2027, 2028, 2029]
const NITER  = 2000000
const NBURN  = 1000000

argval(flag, dflt) = let i = findfirst(a -> startswith(a, flag), ARGS)
    i === nothing ? dflt : ARGS[i][(length(flag) + 1):end]
end

const TAG       = argval("--tag=", "L24")
const CHAIN_TAG = argval("--chain-tag=", TAG)
const FORCING   = argval("--forcing=", "spliced")
const N_TARGET  = 500
const ONE_MARK  = argval("--marker=", "")
## ⚠ MUTATION TEST HARNESS. A gate that passes is not a gate that works, so each of the two
## hard gates here has a switch that BREAKS exactly what it guards; both must FAIL under it.
##   --mutate=seed     perturbs the pairing permutation  -> [CONFIG-IDENTITY] must FAIL
##   --mutate=shuffle  randomises the channel labels     -> [EXPLAINS-TAIL]   must FAIL
## Never leave a mutation on: the banner says so on every line it touches.
const MUTATE = argval("--mutate=", "")
@assert MUTATE in ("", "seed", "shuffle") "--mutate must be seed or shuffle"
MUTATE == "" || @printf("\n  ** MUTATION TEST ACTIVE: --mutate=%s -- OUTPUT IS DELIBERATELY WRONG **\n\n", MUTATE)
## ⚠ THE OUTPUT NAME CARRIES THE ARM. A mutation run and a single-marker run are NOT the
## sweep, and letting either write the sweep's filename is how a deliberately-broken table
## becomes the canonical one -- caught the first time this was run, 2026-09-03.
const OUTSUF = (ONE_MARK == "" ? "" : "_vv$(ONE_MARK)") * (MUTATE == "" ? "" : "_MUT$(uppercase(MUTATE))")

## The seven markers and two species the production sweep ran, and the pulse sizes that
## name their cubes. Derived from ONE table exactly as the driver does -- the size tag is
## the filename AND the per-tonne divisor, and letting them drift is the 1000x error class.
const MARKERS = ONE_MARK == "" ? ["VL", "L", "LN", "ML", "M", "HL", "H"] : [ONE_MARK]
const SPECIE_SPEC = Dict(
    "CO2" => (size_tag = "10Gt", pulse_Gt = 10.0, unit = "GtCO2"),
    "CH4" => (size_tag = "1Gt",  pulse_Gt = 1.0,  unit = "GtCH4"))
const SPECIES = ["CO2", "CH4"]

const PULSE_YEAR  = 2030
const Y0, Y1      = 1850, 2300
const YEARS       = collect(Y0:Y1)
const HORIZONS    = [2100, 2150, 2300]
const PAIR_SEED   = 2026          # MUST match scope_slr_pulse_vv.jl
const SPLICE_YEAR = 2014
const TANT0       = LADRILLO_AIS_TANT0
const IREF        = findall(y -> LADRILLO_REF[1] <= y <= LADRILLO_REF[2], YEARS)
const ARMS        = ["base", "pulse"]

## The tapped-arm tag, built the same way the driver builds it, so this diagnostic reads
## the SHIPPED file rather than a name that merely looks like it.
const TAP_TAG = "_tap$(replace(string(GIS_TAP_CELL.onset_K), "." => "p"))K" *
                "_V$(replace(string(GIS_TAP_CELL.V_m), "." => "p"))m" *
                "_tau$(Int(GIS_TAP_CELL.tau_yr))"

chain_path(sd) = joinpath(REPO, "outputs/mcmc", "chain_$(CHAIN_TAG)_seed$(sd)_n$(NITER).csv")
cube(kind, marker, specie, arm) = joinpath(LADRILLO_OBS,
    "fair_cube_$(kind)_vv$(marker)_$(arm == "base" ? "pulsebase" : "pulse")_" *
    "$(specie)_$(SPECIE_SPEC[specie].size_tag)_$(PULSE_YEAR)_raw.csv")
draws_path(marker, specie) = joinpath(REPO, "outputs",
    "pulse_ladrillo_draws_vv$(marker)_$(specie)_$(SPECIE_SPEC[specie].size_tag)_" *
    "$(PULSE_YEAR)_$(FORCING)_$(TAG)$(TAP_TAG).csv")

## ---- the two sampled columns, thinned EXACTLY as scope_slr_pulse_vv.jl thins ----------
## read_draws() drops NBURN, then strides nrow/N_TARGET and truncates. The column SELECTION
## differs (it needs the whole Ladrillo vector); the ROW selection does not, and rows are
## all this file needs. ladrillo_native_greenland! reparametrises GIS columns in place and
## does not reorder, so the k-th row here is the k-th ROWS entry there.
function read_two(sd)
    df = CSV.read(chain_path(sd), DataFrame;
                  select = ["ais_gmst_amp", "antarctic_temp_threshold"])
    df = df[(NBURN + 1):end, :]
    step = max(1, nrow(df) ÷ N_TARGET)
    idx  = collect(1:step:nrow(df))
    df[idx[1:min(N_TARGET, length(idx))], :]
end
const D     = vcat([read_two(sd) for sd in SEEDS]...)
const NDRAW = nrow(D)
const AMP   = Float64.(D.ais_gmst_amp)
const THR   = Float64.(D.antarctic_temp_threshold)

@printf("AIS CROSSING UNDER A PULSE | tag %s | %d draws | pair seed %d | forcing %s\n",
        TAG, NDRAW, PAIR_SEED, FORCING)
@printf("  T_ant[t] = amp*GMST[t-1] + %.4f   (closed form; no model run)\n", TANT0)
@printf("  amp  %.4f [%.4f, %.4f]   threshold  %.4f [%.4f, %.4f] degC\n\n",
        median(AMP), minimum(AMP), maximum(AMP),
        median(THR), minimum(THR), maximum(THR))

out  = DataFrame(marker = String[], specie = String[], horizon = Int[], metric = String[],
                 value = Float64[], note = String[])
push_o!(m, s, h, k, v, n = "") = push!(out, (m, s, h, k, Float64(v), n))
perdraw = DataFrame(marker = String[], specie = String[], draw = Int[], config = String[],
                    horizon = Int[], ais_diff_cm = Float64[], total_diff_cm = Float64[],
                    n_yr_base = Int[], n_yr_pulse = Int[], dn_years = Int[],
                    dtime_above_yr = Float64[], dt_cross_yr = Float64[], channel = String[])
gates = DataFrame(marker = String[], specie = String[], gate = String[], key = String[],
                  value = Float64[], verdict = String[])
push_g!(m, s, g, k, v, ok) = push!(gates, (m, s, g, k, Float64(v), ok ? "PASS" : "FAIL"))

## Continuous FIRST-crossing date: the first year T_ant clears the threshold, less the
## fraction of that step already above it. Returns Inf when the path never crosses by `iH`.
function cross_time(T::Vector{Float64}, thr::Float64, iH::Int)
    @inbounds for t in 2:iH
        if T[t] > thr
            prev = T[t - 1]
            f = T[t] > prev ? (T[t] - thr) / (T[t] - prev) : 0.0
            return YEARS[t] - clamp(f, 0.0, 1.0)
        end
    end
    return Inf
end

## What the model ACTUALLY charges: one whole year of flux for every annual step whose
## end-of-step T_ant is above threshold. This is the integer the hard step at
## antarctic_icesheet_magdep_component.jl:241 counts.
nyears_above(T::Vector{Float64}, thr::Float64, iH::Int) = count(>(thr), @view T[2:iH])

## What a SUB-ANNUAL solver would charge: the Lebesgue measure of {t : T_ant(t) > thr},
## linear within each annual step. ⚠ THIS IS NOT THE FIRST-CROSSING ADVANCE. On a
## peak-and-decline marker the path leaves the threshold as well as entering it, so the
## pulse buys time at BOTH ends and the entry-side advance alone understates it by ~2x --
## which is exactly the error this function exists to avoid making.
function time_above(T::Vector{Float64}, thr::Float64, iH::Int)
    s = 0.0
    @inbounds for t in 3:iH          # step (t-1 -> t); T[1] is the -Inf sentinel
        a, b = T[t - 1], T[t]
        if a > thr && b > thr
            s += 1.0
        elseif a <= thr && b > thr
            s += (b - thr) / (b - a)
        elseif a > thr && b <= thr
            s += (a - thr) / (a - b)
        end
    end
    return s
end

for marker in MARKERS, specie in SPECIES
    dp = draws_path(marker, specie)
    isfile(dp) || (@printf("  -- skipping vv%s/%s: no shipped draws file\n", marker, specie); continue)
    for a in ARMS
        isfile(cube("gmst", marker, specie, a)) ||
            error("missing cube $(cube("gmst", marker, specie, a))")
    end

    CG = Dict(a => CSV.read(cube("gmst", marker, specie, a), DataFrame) for a in ARMS)
    CFG = [c for c in String.(propertynames(CG["base"])) if startswith(c, "cfg_")]
    for a in ARMS
        Int.(CG[a].year) == YEARS || error("[$(marker)/$(specie)] $(a) year axis is not $(Y0):$(Y1)")
        cs = [c for c in String.(propertynames(CG[a])) if startswith(c, "cfg_")]
        cs == CFG || error("[CUBE-ALIGN] $(marker)/$(specie)/$(a) config ORDER differs from base")
    end

    MEAN_G = [_yearmap(joinpath(LADRILLO_OBS, "fair_mean_gmst_vv$(marker).csv"), "gmst_C")[y]
              for y in YEARS]
    mref = mean(MEAN_G[IREF])
    function convention(raw)
        FORCING == "raw" && return raw
        cref = mean(raw[IREF])
        [y <= SPLICE_YEAR ? MEAN_G[i] : mref + (raw[i] - cref) for (i, y) in enumerate(YEARS)]
    end
    G = Dict(a => Dict(c => convention(Float64.(CG[a][!, c])) for c in CFG) for a in ARMS)

    assign = let rng = MersenneTwister(MUTATE == "seed" ? PAIR_SEED + 1 : PAIR_SEED); a = Int[]
        while length(a) < NDRAW; append!(a, randperm(rng, length(CFG))); end; a[1:NDRAW]
    end
    cfg_of_draw = [CFG[i] for i in assign]

    dr = CSV.read(dp, DataFrame)
    ## [CONFIG-IDENTITY] the reconstruction PROVED, not assumed. If the thinning or the
    ## permutation here differed from the driver's by even one row, every number below
    ## would be a difference between two unrelated climates and every other gate would
    ## still pass. Mutation test: perturb PAIR_SEED and this must FAIL.
    let rec = combine(groupby(dr, :draw), :config => first => :config)
        sort!(rec, :draw)
        n_mis = count(k -> rec.config[k] != cfg_of_draw[rec.draw[k]], 1:nrow(rec))
        @printf("  [CONFIG-IDENTITY] vv%-2s %-3s  %d of %d draws mismatch  %s\n",
                marker, specie, n_mis, nrow(rec), n_mis == 0 ? "PASS" : "FAIL")
        push_g!(marker, specie, "CONFIG-IDENTITY", "mismatches", n_mis, n_mis == 0)
        (n_mis == 0 || MUTATE == "seed") ||
            error("[CONFIG-IDENTITY] FAILED for vv$(marker)/$(specie) -- STOP")
    end

    ## T_ant per draw per arm, with the t-1 lag the component uses.
    TA = Dict(a => [begin
                        g = G[a][cfg_of_draw[k]]
                        T = Vector{Float64}(undef, length(YEARS))
                        T[1] = -Inf
                        @inbounds for t in 2:length(YEARS); T[t] = AMP[k] * g[t - 1] + TANT0; end
                        T
                    end for k in 1:NDRAW] for a in ARMS)

    for H in HORIZONS
        iH = findfirst(==(H), YEARS)
        nb = [nyears_above(TA["base"][k],  THR[k], iH) for k in 1:NDRAW]
        np = [nyears_above(TA["pulse"][k], THR[k], iH) for k in 1:NDRAW]
        tb = [cross_time(TA["base"][k],  THR[k], iH) for k in 1:NDRAW]
        tp = [cross_time(TA["pulse"][k], THR[k], iH) for k in 1:NDRAW]
        dn = np .- nb
        ## the CONTINUOUS advance, defined only where both arms cross; that is precisely the
        ## population for which a de-quantized model would charge a finite derivative.
        both = findall(k -> isfinite(tb[k]) && isfinite(tp[k]), 1:NDRAW)
        dt   = [tb[k] - tp[k] for k in both]
        ## the continuous time-above measure, on the SAME population the integer count sees
        sb   = [time_above(TA["base"][k],  THR[k], iH) for k in 1:NDRAW]
        sp   = [time_above(TA["pulse"][k], THR[k], iH) for k in 1:NDRAW]
        ds   = sp .- sb
        ## the BIFURCATION population: never at baseline, crossed under the pulse.
        bif  = findall(k -> !isfinite(tb[k]) && isfinite(tp[k]), 1:NDRAW)

        sub = dr[(dr.horizon .== H) .& (dr.component .== "ais"), :]
        sort!(sub, :draw)
        tot = dr[(dr.horizon .== H) .& (dr.component .== "total"), :]
        sort!(tot, :draw)
        ais_d = zeros(NDRAW); tot_d = zeros(NDRAW)
        for r in eachrow(sub); ais_d[r.draw] = r.diff_cm; end
        for r in eachrow(tot); tot_d[r.draw] = r.diff_cm; end

        chan = [k in bif ? "bifurcation" : (dn[k] != 0 ? "quantization" : "smooth") for k in 1:NDRAW]
        MUTATE == "shuffle" && shuffle!(MersenneTwister(7), chan)
        for k in 1:NDRAW
            push!(perdraw, (marker, specie, k, cfg_of_draw[k], H, ais_d[k], tot_d[k],
                            nb[k], np[k], dn[k], ds[k],
                            (isfinite(tb[k]) && isfinite(tp[k])) ? tb[k] - tp[k] : NaN, chan[k]))
        end

        sm = findall(==( "smooth"), chan); qz = findall(==("quantization"), chan)
        fired = vcat(qz, bif)
        p_fire = length(fired) / NDRAW

        ## ---- the Lemoine-Traeger split of the AIS marginal -----------------------------
        ## E[d] = P(smooth)*E[d|smooth] + P(fired)*E[d|fired]. Reported as BOTH terms, never
        ## as the sum alone: the sum is the mean, and the mean is the statistic the tail
        ## owns ([[paired_mean_crosses_on_a_tail]], [[dais_fastdynamics_quant]]).
        e_sm  = isempty(sm)    ? 0.0 : mean(ais_d[sm])
        e_fi  = isempty(fired) ? 0.0 : mean(ais_d[fired])
        prem  = p_fire * e_fi
        @printf("  vv%-2s %-3s %d | fired %4d/%d (%.2f%%)  bif %3d  quant %3d | AIS mean %8.4f = smooth %8.4f + premium %8.4f (%.1f%%) | med %8.5f\n",
                marker, specie, H, length(fired), NDRAW, 100p_fire, length(bif), length(qz),
                mean(ais_d), (1 - p_fire) * e_sm, prem,
                mean(ais_d) == 0 ? 0.0 : 100prem / mean(ais_d), median(ais_d))

        push_o!(marker, specie, H, "n_draws", NDRAW)
        push_o!(marker, specie, H, "n_bifurcation", length(bif), "never crosses at base, crosses under pulse")
        push_o!(marker, specie, H, "n_quantization", length(qz), "crosses in both, integer year count differs")
        push_o!(marker, specie, H, "p_fired", p_fire)
        push_o!(marker, specie, H, "ais_mean_cm", mean(ais_d))
        push_o!(marker, specie, H, "ais_median_cm", median(ais_d))
        push_o!(marker, specie, H, "ais_smooth_term_cm", (1 - p_fire) * e_sm, "P(smooth)*E[d|smooth]")
        push_o!(marker, specie, H, "ais_premium_cm", prem, "P(fired)*E[d|fired]")
        push_o!(marker, specie, H, "ais_cond_mean_fired_cm", e_fi)
        push_o!(marker, specie, H, "ais_median_smooth_cm", isempty(sm) ? NaN : median(ais_d[sm]))
        push_o!(marker, specie, H, "total_mean_cm", mean(tot_d))
        push_o!(marker, specie, H, "total_median_cm", median(tot_d))

        ## ---- QUANTIZATION: BIAS OR ONLY VARIANCE? --------------------------------------
        ## mean(dn_integer) vs mean(dt_continuous) over the SAME population (crossed in both
        ## arms). Equal => the annual step is an unbiased randomisation and more draws fix
        ## the mean. Unequal => the step BIASES the mean and no ensemble size fixes it.
        let mdn = mean(Float64.(dn)), mds = mean(ds)
            push_o!(marker, specie, H, "n_cross_both", length(both))
            push_o!(marker, specie, H, "mean_dn_years_int", mdn, "what the annual step charges")
            push_o!(marker, specie, H, "mean_dtime_above_yr", mds, "what a sub-annual solver would charge")
            push_o!(marker, specie, H, "quantization_bias_yr", mdn - mds)
            push_o!(marker, specie, H, "quantization_bias_ratio", mds == 0 ? NaN : mdn / mds)
            push_o!(marker, specie, H, "sd_dn_years_int", std(Float64.(dn)))
            push_o!(marker, specie, H, "sd_dtime_above_yr", std(ds))
            push_o!(marker, specie, H, "mean_dt_firstcross_yr", isempty(dt) ? NaN : mean(dt),
                    "entry side only; understates on peak-and-decline")
            @printf("      quantization: mean dn_int %+.5f yr  vs  continuous %+.5f yr  bias %+.5f (%.3fx)  sd %.4f vs %.4f\n",
                    mdn, mds, mdn - mds, mds == 0 ? NaN : mdn / mds,
                    std(Float64.(dn)), std(ds))
        end

        ## [EXPLAINS-TAIL] an ORDERING between two MEASURED quantities, not an invented cut
        ## (`threshold_from_obs_or_law`): if the closed-form classifier really identifies the
        ## threshold channel, the smooth population's p99.9 must sit BELOW the fired
        ## population's MEDIAN. Mutation test: shuffle `chan` and this must FAIL.
        if !isempty(fired) && !isempty(sm)
            hi = quantile(ais_d[sm], 0.999); lo = median(ais_d[fired])
            ok = hi < lo
            @printf("      [EXPLAINS-TAIL] smooth p99.9 %.5f  <  fired median %.5f  %s\n",
                    hi, lo, ok ? "PASS" : "FAIL")
            push_g!(marker, specie, "EXPLAINS-TAIL", "smooth_p999_cm_$(H)", hi, ok)
            push_g!(marker, specie, "EXPLAINS-TAIL", "fired_median_cm_$(H)", lo, ok)
        end

        ## [MEAN-MEDIAN-SIGN] the one-line diagnostic `paired_mean_crosses_on_a_tail`
        ## prescribes and that no pulse gate runs. Reported for TOTAL, which is the headline.
        let mn = mean(tot_d), md = median(tot_d), agree = sign(mn) == sign(md)
            push_g!(marker, specie, "MEAN-MEDIAN-SIGN", "ratio_$(H)", md == 0 ? NaN : mn / md, agree)
        end
    end
end

CSV.write(joinpath(REPO, "outputs", "diag_ais_crossing_pulse_vv_$(TAG)$(OUTSUF).csv"), out)
CSV.write(joinpath(REPO, "outputs", "diag_ais_crossing_pulse_vv_draws_$(TAG)$(OUTSUF).csv"), perdraw)
CSV.write(joinpath(REPO, "outputs", "diag_ais_crossing_pulse_vv_gates_$(TAG)$(OUTSUF).csv"), gates)
@printf("\nwrote outputs/diag_ais_crossing_pulse_vv_%s%s.csv  (%d rows)\n", TAG, OUTSUF, nrow(out))
@printf("      outputs/diag_ais_crossing_pulse_vv_draws_%s%s.csv  (%d rows)\n", TAG, OUTSUF, nrow(perdraw))
@printf("      outputs/diag_ais_crossing_pulse_vv_gates_%s%s.csv  (%d rows, %d FAIL)\n",
        TAG, OUTSUF, nrow(gates), count(==("FAIL"), gates.verdict))
