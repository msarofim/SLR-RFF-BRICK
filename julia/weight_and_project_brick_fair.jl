## ============================================================================
## weight_and_project_brick_fair.jl — FULL conditional-Wong forward propagation + coupled SLR bands.
##
## Combines weight_brick_conditional_fair.jl (conditional weighting) with a projection to 2300, so a
## SINGLE BRICK run per (config, draw) yields BOTH the historical fit ℓ^FB (for the weight) AND the
## future SLR (for the bands). Produces COUPLED bands (each FaIR config equally likely, BRICK draws
## conditionally weighted) vs INDEPENDENT bands (equal weight) — the deliverable comparison.
##
## Method: for each FaIR config k, w_{i|k} ∝ exp[c·(ℓ^FB_ik − ℓ^B_i)] normalized WITHIN config k, so
## p(config)=1/NCFG stays uniform (SLR never touches the forcing marginal). ℓ^B at the mean (calibration)
## forcing. c tuned to a gentle mean conditional ESS/N (default 0.6). See
## notes/negresult_2026-08-01_joint_forcing_calibration.md + weight_brick_conditional_fair.jl (validated).
##
## Usage (smoke): julia --project=julia_v2 julia/weight_and_project_brick_fair.jl 2000 2026 \
##                    --amp-mu=1.08 --amp-sigma=0.15 --draws=200 --configs=5
##        (full): ... --draws=2000 --configs=all     (≈1.68M runs to 2300, ~1–2.5 h single-core)
##
## PULSE ARM (2026-08-01 extension; defaults preserve the staged behaviour bit-for-bit):
##   --pulse=off|on|zero   off (default) = levels/bands only, exactly the staged run.
##                         on   = ALSO run the paired 10-GtCO2 2030 pulse forcing per (config,draw)
##                                IN-PROCESS (exact pairing on one model instance) and report the
##                                conditionally-weighted pulse marginal COUPLED vs INDEPENDENT.
##                         zero = wiring sanity: pulse arm fed the BASE forcing; every per-pair
##                                Δ must be exactly 0.0 (zero-perturbation test).
##   --basis=<sfx>         suffix for the wide forcing files (both arms), e.g. "_nonoise" or
##                         "_nonoise_flatsolar". Default "" = canonical stochastic basis.
##                         NB pulse MEDIANS on the stochastic basis are noise/solar-suppressed
##                         (see notes/handoff walkthrough 2026-07-24); the deterministic basis
##                         is the driver-comparable one for medians. Pulse MEANS additionally
##                         need the sub-annual DAIS patch (NOT applied on pristine depots) —
##                         per-pair output lets any statistic be recomputed in post.
##   --pulse-gt=<x>        pulse SIZE in the wide files (default 10). Marginals are reported per 1 unit.
##   --pulse-unit=<s>      unit LABEL (default "GtCO2"). **MUST be set for non-CO2 species** — e.g.
##                         CH4: --basis=_ch4bio1tg --pulse-gt=1 --pulse-unit="Tg CH4". Without it every
##                         printed line and CSV says "per GtCO2" while holding per-Tg numbers.
##   --engine=fast|legacy  fast (default) mutates the BUILT model instance in place, skipping the ~14 ms
##                         Mimi rebuild per run that update_param! forces on this 451-yr model (~30x;
##                         the legacy path made a full run ~12-14 h = a guaranteed SLURM timeout).
##                         Validated BYTE-IDENTICAL to legacy at smoke and 24k-pair scale.
##   --out-tag=<s>         extra output suffix so validation runs never clobber canonical paths.
##   Outputs are suffixed by --basis (+ tags) so non-canonical bases never clobber canonical files.
##
## !! ARG PRECEDENCE: `_arg` is `findfirst` — the FIRST occurrence of a flag WINS and any later
##    repeat is SILENTLY IGNORED. Never build a command as "$BASE_ARGS $OVERRIDES": appending
##    --draws/--configs/--pulse after a base string that already sets them does nothing, with no
##    warning. This bit a queued fossil-CH4 job on 2026-08-03 — an intended 3-config zero-pulse
##    smoke gate ran as a full 841x2000 production job because the base string led with
##    --pulse=on --draws=2000. State every flag exactly once per command line.
##
## PROVENANCE (2026-08-02): every run writes `wong_cond_runmeta<sfx>.csv` (model lineage, posterior
## hash, DAIS integrator AUTO-DETECTED from the loaded depot, forcing basis, pulse spec + units,
## weighting c/ESS, git commit, package versions) and stamps the key fields as `prov_*` columns INSIDE
## the bands CSVs, so numbers never travel without the axes needed to check run-to-run consistency.
## See julia/run_provenance.jl.
## ============================================================================
include(joinpath(@__DIR__, "calibrate_mcmc_ext.jl"))     # guarded: FREE, NP, AMP_IDX, TON_IDX, C_IDX,
                                                         # AIS_TANT0, setp!(unused), S, lws_dang,
                                                         # hetero_logl_ar1, build_brick_mengel, update_brick_mengel!
using Statistics, Printf, CSV, DataFrames
include(joinpath(@__DIR__, "run_provenance.jl"))          # provenance(), write_provenance(), stamp!()

_arg(p,d)=(i=findfirst(a->startswith(a,p),ARGS); i===nothing ? d : ARGS[i][length(p)+1:end])
const NDRAWS = parse(Int, _arg("--draws=", "2000"))
const CFGARG = _arg("--configs=", "all")
const ESSTGT = parse(Float64, _arg("--ess-target=", "0.6"))
const PULSEMODE = _arg("--pulse=", "off")                # off | on | zero (see header)
const BASIS = _arg("--basis=", "")                       # wide-file suffix ("", "_nonoise", "_nonoise_flatsolar")
const OUTTAG = _arg("--out-tag=", "")                    # extra output suffix (validation runs: keep canonical paths clean)
const ENGINE = _arg("--engine=", "fast")                 # fast = in-place instance mutation (no Mimi rebuild; ~10x);
                                                         # legacy = update_param! per run. VALIDATED bit-identical
                                                         # (all 5 components + full smoke CSVs) 2026-08-02.
ENGINE in ("fast","legacy") || error("--engine must be fast|legacy (got $ENGINE)")
PULSEMODE in ("off","on","zero") || error("--pulse must be off|on|zero (got $PULSEMODE)")
const PULSE_GT = parse(Float64, _arg("--pulse-gt=", "10.0"))  # pulse SIZE in fair_*_pulse_wide$(BASIS).csv, in PULSE_UNIT
                                                              # (CO2 @2030 SSP2-4.5 default; --basis=_20gt --pulse-gt=20,
                                                              #  CH4: --basis=_ch4bio1tg --pulse-gt=1 --pulse-unit="Tg CH4")
const PULSE_UNIT = _arg("--pulse-unit=", "GtCO2")             # label ONLY — all printed/CSV marginals are per 1 PULSE_UNIT.
                                                              # MUST be set for non-CO2 species or every label lies (per-gas
                                                              # unit confusion is the recurring bug class here).
const FRC = joinpath(REPO, "..", "FaIRtoFrEDI", "magicc_comparison", "processed", "curv_wide")
const OHCS = 0.1
const YP0, YP1 = 1850, 2300
const YRS2 = collect(YP0:YP1); ty(y)=findfirst(==(y),YRS2)
const IB2 = [ty(y) for y in 1995:2005]
# Horizons. The PAPER's key variable is YEARS SINCE THE EMISSION PULSE (Marcus: 100 and 150 yr from the
# emission point, consistent with the GWP-100 framing), NOT calendar 2100/2150 — with a 2030 pulse that
# is 2130 / 2180, and the 120-yr point Marcus cites is 2150. Defaults keep the original four for
# continuity with prior runs; pass --horizons= / --comp-years= to add the pulse-relative years.
const HORIZONS = [parse(Int,s) for s in split(_arg("--horizons=", "2050,2100,2150,2300"), ",")]
const COMPYRS  = [parse(Int,s) for s in split(_arg("--comp-years=", "2100,2150,2300"), ",")]
# first 8 labels/order = the staged schema (bit-compatible when --pulse=off writes only these)
const LABELS = vcat(["total@$y" for y in HORIZONS],
                    ["$(c)@$(y)" for y in COMPYRS for c in ("ais","gsic","gis","te")])
const NMET = length(LABELS)                              # 16
const NOUT = PULSEMODE=="off" ? min(length(HORIZONS)+4, NMET) : NMET   # levels-only keeps the staged 8-row schema on default horizons
const DANG_IDX2 = [ty(y) for y in S.dang.years]          # dang fit years mapped into the 1850–2300 array

# ---- FaIR ensemble forcing to 2300 ----
loadw(p; s=1.0)=(d=CSV.read(p,DataFrame); keep=[y in YRS2 for y in d.year]; Matrix(d[keep,2:end]).*s)
const GW2 = loadw(joinpath(FRC,"fair_gmst_base_wide$(BASIS).csv"))
const OW2 = loadw(joinpath(FRC,"fair_ohc_base_wide$(BASIS).csv"); s=OHCS)
const GP2 = PULSEMODE=="on"  ? loadw(joinpath(FRC,"fair_gmst_pulse_wide$(BASIS).csv"))         :
            PULSEMODE=="zero" ? GW2 : nothing
const OP2 = PULSEMODE=="on"  ? loadw(joinpath(FRC,"fair_ohc_pulse_wide$(BASIS).csv"); s=OHCS)  :
            PULSEMODE=="zero" ? OW2 : nothing
const NCFG_ALL = size(GW2,2)
const GMEAN2 = vec(mean(GW2,dims=2)); const OMEAN2 = vec(mean(OW2,dims=2))   # ensemble mean = calibration forcing
@printf("FaIR ensemble to 2300: %d configs × %d yr  (basis '%s', pulse %s)\n",
        NCFG_ALL, length(YRS2), BASIS, PULSEMODE)

# ---- BRICK-AM draws (extA108 subsample), thinned ----
sub = CSV.read(joinpath(REPO,"data/MimiBRICK/parameters_subsample_brick_mengel_extA108.csv"), DataFrame)
step = max(1, nrow(sub) ÷ NDRAWS); ridx = collect(1:step:nrow(sub))[1:min(NDRAWS,length(1:step:nrow(sub)))]
const ND = length(ridx)
θmat = [Float64[Float64(sub[r, Symbol(FREE[k].name)]) for k in 1:NP] for r in ridx]
sd_d = Float64[Float64(sub[r,:sd_dang])  for r in ridx]
rh_d = Float64[Float64(sub[r,:rho_dang]) for r in ridx]
te_i = Float64[Float64(sub[r,:thermal_alpha]) for r in ridx]
@printf("BRICK-AM draws: %d (thinned from %d)\n", ND, nrow(sub))

# ---- projection model (1850–2300) ----
medoid = CSV.read(joinpath(REPO,"outputs/recalib_central_row.csv"), DataFrame)[1,:]
const m2 = build_brick_mengel(ssp="ssp245", y0=YP0, y1=YP1)
update_brick_mengel!(m2, medoid, (a=0.45,b=0.52,T_lia=-0.45,f=0.5,tau_fast=40.0,tau_slow=250.0,sl0=0.0); precip_log=true)
setp2!(k,v)=update_param!(m2,k.comp,k.sym, k.islog ? log(v) : v)
reref2(v)=100 .* (v .- mean(v[IB2]))

# ---- fast engine: mutate the BUILT instance in place, run(mi) with no Mimi rebuild ----
# update_param! dirties the model and the next run() pays a ~14 ms rebuild of the 451-yr model
# (the integration itself is ~2 ms). The fast path writes the same state directly into the model
# instance: array params are SubArray views into SHARED external-param backing (one write reaches
# every consumer — asserted below), scalar params are mutable ScalarModelParameter boxes.
# Bit-identical to the legacy path (validated per component AND on full smoke CSVs, 2026-08-02).
# Mimi-internal layout (getfield(::ComponentInstanceParameters, :nt)) pinned to Mimi 1.6.0.
set_forcing!(m2, GMEAN2, OMEAN2); run(m2)                  # one legacy build to wire the instance
const MI2 = Mimi.modelinstance(m2)
_nt(c) = getfield(Mimi.compinstance(MI2, c).parameters, :nt)
const GVIEW = _nt(:antarctic_ocean)[:global_surface_temperature].data   # shared-backing view
const OVIEW = _nt(:thermal_expansion)[:ocean_heat_interior].data
let gpar = parent(GVIEW)
    for c in (:antarctic_icesheet, :glaciers_small_icecaps, :greenland_icesheet)
        @assert parent(_nt(c)[:global_surface_temperature].data) === gpar "GMST consumer $c does not alias the shared backing — fast engine unsafe"
    end
end
const BOXES = [k in (AMP_IDX, TON_IDX) ? nothing : _nt(FREE[k].comp)[FREE[k].sym] for k in 1:NP]
const BOX_H0   = _nt(:antarctic_icesheet)[:ais_runoffline_snowheight₀]
const BOX_TCO  = _nt(:antarctic_icesheet)[:ais_temperature_coefficient]
const BOX_TIN  = _nt(:antarctic_icesheet)[:ais_temperature_intercept]

# run once to 2300 → (historical ice+steric total at dang years, the NMET future metrics:
# total@HORIZONS then (ais,gsic,gis,te)@COMPYRS — first 8 in the staged order)
function run2300(θ, g, o)
    if ENGINE == "fast"
        GVIEW .= g; OVIEW .= o
        @inbounds for k in 1:NP
            (k==AMP_IDX||k==TON_IDX) && continue
            BOXES[k].value = FREE[k].islog ? log(θ[k]) : θ[k]
        end
        BOX_H0.value  = -θ[TON_IDX]*θ[C_IDX]
        BOX_TCO.value = 1.0/θ[AMP_IDX]
        BOX_TIN.value = -AIS_TANT0/θ[AMP_IDX]
        run(MI2)
    else
        set_forcing!(m2, g, o)
        @inbounds for k in 1:NP; (k==AMP_IDX||k==TON_IDX) && continue; setp2!(FREE[k], θ[k]); end
        update_param!(m2,:antarctic_icesheet,:ais_runoffline_snowheight₀, -θ[TON_IDX]*θ[C_IDX])
        update_param!(m2,:antarctic_icesheet,:ais_temperature_coefficient, 1.0/θ[AMP_IDX])
        update_param!(m2,:antarctic_icesheet,:ais_temperature_intercept, -AIS_TANT0/θ[AMP_IDX])
        run(m2)
    end
    ais=reref2(m2[:antarctic_icesheet,:ais_sea_level]); gsic=reref2(m2[:glaciers_small_icecaps,:gsic_sea_level])
    gis=reref2(m2[:greenland_icesheet,:greenland_sea_level]); te=reref2(m2[:thermal_expansion,:te_sea_level])
    icesteric = ais .+ gsic .+ gis .+ te
    gtot = reref2(m2[:global_sea_level,:sea_level_rise])           # projected total incl model LWS
    met = Vector{Float64}(undef, NMET)
    for (h,y) in enumerate(HORIZONS); met[h] = gtot[ty(y)]; end
    for (ci,y) in enumerate(COMPYRS)
        # offset MUST derive from length(HORIZONS), not a literal: with a hardcoded 4 and >4 horizons the
        # component writes clobbered horizon slots and left the tail of `met` UNINITIALIZED (caught by the
        # zero-pulse gate as NaN, 2026-08-02). Identical to the old code when length(HORIZONS)==4.
        i = ty(y); b = length(HORIZONS) + 4*(ci-1)
        met[b+1]=ais[i]; met[b+2]=gsic[i]; met[b+3]=gis[i]; met[b+4]=te[i]
    end
    (icesteric[DANG_IDX2], met)
end
dll(dang_tot, sd, rho) = hetero_logl_ar1(dang_tot .+ lws_dang .- S.dang.obs, sd, rho, S.dang.ϵ)

# ---- ℓ^B (mean forcing) per draw ----
println("ℓ^B (mean forcing) for $ND draws ...")
lB = Vector{Float64}(undef, ND)
for i in 1:ND; d,_ = run2300(θmat[i], GMEAN2, OMEAN2); lB[i]=dll(d, sd_d[i], rh_d[i]); end
@printf("  ℓ^B done; mean-forcing sanity: ensemble-mean GMST@2018 vs ext-mean not checked here (see weight_* driver)\n")

# ---- configs ----
ohc2018 = Float64[OW2[ty(2018),k]-OW2[ty(1850),k] for k in 1:NCFG_ALL]
cfgs = CFGARG=="all" ? collect(1:NCFG_ALL) :
       (n=parse(Int,CFGARG); sortperm(ohc2018)[round.(Int, range(1, NCFG_ALL, length=n))])
const NCFG = length(cfgs)
@printf("configs: %d (%s)\n", NCFG, CFGARG)

# ---- ℓ^FB + future SLR per (config, draw) [+ paired pulse arm, same model instance] ----
const DOPULSE = PULSEMODE != "off"
println("ℓ^FB + projection: $NCFG configs × $ND draws = $(NCFG*ND) runs to 2300" *
        (DOPULSE ? " × 2 arms (pulse paired in-process)" : "") * " ...")
lFB = Array{Float64}(undef, ND, NCFG)
FUT  = [Array{Float64}(undef, ND, NCFG) for _ in 1:NMET]
DFUT = DOPULSE ? [Array{Float64}(undef, ND, NCFG) for _ in 1:NMET] : nothing
tloop = time()
for (j,k) in enumerate(cfgs)
    g=GW2[:,k]; o=OW2[:,k]
    for i in 1:ND
        dang, met = run2300(θmat[i], g, o)
        lFB[i,j] = dll(dang, sd_d[i], rh_d[i])
        for h in 1:NMET; FUT[h][i,j]=met[h]; end
        if DOPULSE
            _, pmet = run2300(θmat[i], GP2[:,k], OP2[:,k])
            for h in 1:NMET; DFUT[h][i,j]=pmet[h]-met[h]; end
        end
    end
    j % 20 == 0 && (print("."); flush(stdout))
end
println()
@printf("projection loop: %.1f s = %.2f ms/run over %d runs\n", time()-tloop,
        1000*(time()-tloop)/(NCFG*ND*(DOPULSE ? 2 : 1)), NCFG*ND*(DOPULSE ? 2 : 1))
# zero-perturbation gate: base fed as the pulse arm ⇒ every Δ must be EXACTLY zero
if PULSEMODE == "zero"
    mx = maximum(D->maximum(abs, D), DFUT)
    zok = mx == 0.0
    println(zok ? "ZERO-PULSE TEST PASS: max|Δ| = 0.0 exactly ($(NMET) metrics × $(ND*NCFG) pairs)" :
                  "ZERO-PULSE TEST **FAIL**: max|Δ| = $mx (expected exactly 0.0 — wiring/state leak)")
    zok || exit(1)
end

# ---- conditional weights (per config), c tuned for gentle mean ESS ----
Δ = lFB .- lB
function condw(c)
    W=similar(Δ); for j in 1:NCFG; x=c.*@view Δ[:,j]; w=exp.(x.-maximum(x)); s=sum(w); W[:,j]= s>0 ? w./s : fill(1/ND,ND); end; W
end
essfrac(W)=mean(1.0 ./ (ND .* vec(sum(W.^2,dims=1))))
function tune_c(t); clo,chi=0.0,5.0; while essfrac(condw(chi))>t; chi*=2; chi>1e4&&break; end
    for _ in 1:40; cm=(clo+chi)/2; essfrac(condw(cm))>t ? (clo=cm) : (chi=cm); end; (clo+chi)/2; end
const C = tune_c(ESSTGT); W = condw(C)
@printf("c = %.4g → mean conditional ESS/N = %.3f (target %.2f)\n", C, essfrac(W), ESSTGT)

# ---- bands: COUPLED (w_{i|k}/NCFG) vs INDEPENDENT (equal) ----
function wq(v, w)                              # weighted quantiles 5/50/95
    p=sortperm(v); vs=v[p]; ws=cumsum(w[p])./sum(w); q=Float64[]
    for t in (0.05,0.5,0.95); push!(q, vs[searchsortedfirst(ws,t)]); end; q
end
wc = vec(W) ./ NCFG                            # coupled pair weights (config equal, draws conditional)
wi = fill(1.0/(ND*NCFG), ND*NCFG)              # independent (equal) pair weights
println("\n=== SLR bands  COUPLED vs INDEPENDENT  (median [5,95] cm, rel 1995-2005) ===")
summ = NamedTuple[]
for h in 1:NOUT
    lab = LABELS[h]
    v=vec(FUT[h]); qc=wq(v,wc); qi=wq(v,wi)
    @printf("  %-11s COUPLED %7.2f [%7.2f,%8.2f] | INDEP %7.2f [%7.2f,%8.2f] | Δmed %+6.2f Δw95-5 %+6.2f\n",
            lab, qc[2],qc[1],qc[3], qi[2],qi[1],qi[3], qc[2]-qi[2], (qc[3]-qc[1])-(qi[3]-qi[1]))
    push!(summ, (metric=lab, cpl_med=qc[2],cpl_lo=qc[1],cpl_hi=qc[3], ind_med=qi[2],ind_lo=qi[1],ind_hi=qi[3]))
end

# ---- pulse-marginal aggregation (per GtCO2; per-pair Δ from the exact in-process pairing) ----
if DOPULSE
    println("\n=== PULSE marginal Δ  COUPLED vs INDEPENDENT  (cm per $(PULSE_UNIT); $(PULSE_GT) $(PULSE_UNIT) pulse @2030) ===")
    psumm = NamedTuple[]
    for (h,lab) in enumerate(LABELS)
        v = vec(DFUT[h]) ./ PULSE_GT
        qc=wq(v,wc); qi=wq(v,wi)
        @printf("  Δ%-10s COUPLED %10.3e [%10.3e,%10.3e] | INDEP %10.3e [%10.3e,%10.3e] | Δmed %+9.2e\n",
                lab, qc[2],qc[1],qc[3], qi[2],qi[1],qi[3], qc[2]-qi[2])
        push!(psumm, (metric=lab, cpl_med=qc[2],cpl_lo=qc[1],cpl_hi=qc[3], ind_med=qi[2],ind_lo=qi[1],ind_hi=qi[3]))
    end
end

# ---- PROVENANCE: every results file self-documents its model version, units and key axes ----
# (standing convention, Marcus 2026-08-02 — see julia/run_provenance.jl header). Auto-detected, so it
# cannot drift from what actually ran: the DAIS integrator is read off the LOADED depot component, the
# posterior/forcing files are content-hashed, and the code commit comes from git.
PROV = provenance(
    driver   = "weight_and_project_brick_fair.jl",
    repo     = REPO,
    posterior= joinpath(REPO,"data/MimiBRICK/parameters_subsample_brick_mengel_extA108.csv"),
    forcing_files = DOPULSE ?
        [joinpath(FRC,"fair_$(v)_$(a)_wide$(BASIS).csv") for v in ("gmst","ohc") for a in ("base","pulse")] :
        [joinpath(FRC,"fair_$(v)_base_wide$(BASIS).csv") for v in ("gmst","ohc")],
    units    = DOPULSE ? "SLR cm; pulse marginals are cm per 1 $(PULSE_UNIT)" : "SLR cm",
    reference_period = "1995-2005 mean (SLR anomalies re-referenced per draw)",
    weighting = "COUPLED = conditional importance weighting w_{i|k} ∝ exp[c·(ℓ^FB−ℓ^B)] normalized " *
                "within each FaIR config (p(config)=1/$(NCFG) uniform; forcing marginal untouched); " *
                @sprintf("c=%.4g, achieved mean conditional ESS/N=%.3f. INDEPENDENT = equal weights.", C, essfrac(W)),
    extra = [
        # The basis suffix encodes BOTH the pulse arm (gas/size) and the noise setting, so report the
        # variability treatment explicitly — it is the axis that moves pulse medians/tip fractions.
        "forcing_basis"      => (occursin("nonoise", BASIS) ?
                                    "DETERMINISTIC (stochastic_run=False" *
                                    (occursin("flatsolar", BASIS) ? " + future solar held at trailing 11-yr cycle mean)" : ")") :
                                    "STOCHASTIC (FaIR internal variability ON, canonical)") *
                                (isempty(BASIS) ? "" : "; wide-file suffix '$(BASIS)'"),
        "pulse_spec"         => DOPULSE ? @sprintf("+%g %s @2030, SSP2-4.5, paired in-process per (config,draw); mode=%s",
                                                   PULSE_GT, PULSE_UNIT, PULSEMODE) : "none (levels/bands only)",
        "amplification_prior"=> @sprintf("amp ~ N(%.3f, %.3f) on [%.3f, %.3f] (A6 CMIP6 land-frame secant)",
                                         AMP_MU, AMP_SIGMA, AMP_LO, AMP_HI),
        "lws_mode"           => "build_brick_mengel default (:seeded, LWS_SEED=$(LWS_SEED))",
        "ensemble_size"      => "$(NCFG) FaIR configs × $(ND) BRICK-AM posterior draws = $(NCFG*ND) pairs",
        "projection_window"  => "$(YP0)-$(YP1)",
        "engine"             => ENGINE == "fast" ? "fast (in-place instance mutation; validated byte-identical to update_param!)" : "legacy (update_param! per run)",
        "sanity_zero_pulse"  => PULSEMODE=="zero" ? "THIS RUN IS THE ZERO-PULSE WIRING TEST" : "gated separately (--pulse=zero: max|Δ|=0.0 exactly)",
    ])

# ---- outputs (suffixed by basis; ZEROTEST runs never clobber canonical files) ----
const OUTSFX = BASIS * (PULSEMODE=="zero" ? "_ZEROTEST" : "") * OUTTAG
write_provenance(joinpath(REPO,"outputs/mcmc/wong_cond_runmeta$(OUTSFX).csv"), PROV)
CSV.write(joinpath(REPO,"outputs/mcmc/wong_cond_slr_bands$(OUTSFX).csv"), stamp!(DataFrame(summ), PROV))
CSV.write(joinpath(REPO,"outputs/mcmc/wong_cond_weights_full$(OUTSFX).csv"),
          DataFrame(config=repeat(cfgs,inner=ND), draw=repeat(ridx,outer=NCFG), w=vec(W), lFB=vec(lFB), lB=repeat(lB,outer=NCFG)))
if DOPULSE
    CSV.write(joinpath(REPO,"outputs/mcmc/wong_cond_pulse_bands$(OUTSFX).csv"), stamp!(DataFrame(psumm), PROV))
    pairs = DataFrame(config=repeat(cfgs,inner=ND), draw=repeat(ridx,outer=NCFG), w=vec(W))
    for (h,lab) in enumerate(LABELS); pairs[!, "base_"*lab] = vec(FUT[h]); end
    for (h,lab) in enumerate(LABELS); pairs[!, "d_"*lab]    = vec(DFUT[h]); end
    CSV.write(joinpath(REPO,"outputs/mcmc/wong_cond_pulse_pairs$(OUTSFX).csv"), pairs)   # per-pair: unstamped (huge); sidecar carries provenance
    @printf("wrote wong_cond_pulse_bands%s.csv + wong_cond_pulse_pairs%s.csv (%d pairs; bands are per 1 %s, pairs are raw Δ per %.0f %s)\n",
            OUTSFX, OUTSFX, ND*NCFG, PULSE_UNIT, PULSE_GT, PULSE_UNIT)
end
@printf("\nwrote outputs/mcmc/wong_cond_slr_bands%s.csv + wong_cond_weights_full%s.csv  (c=%.4g, ESS/N=%.3f, %d configs × %d draws)\n",
        OUTSFX, OUTSFX, C, essfrac(W), NCFG, ND)
println("provenance: ", Dict(PROV)["model_lineage"], " | ", Dict(PROV)["dais_integrator"],
        " | basis ", Dict(PROV)["forcing_basis"], " | ", Dict(PROV)["pulse_spec"])
