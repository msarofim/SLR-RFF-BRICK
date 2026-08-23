## ============================================================================
## project_ssps_components_ladrillo.jl — Ladrillo per-component SSP projections
##
## Component-resolved sea-level bands for SSP1-2.6 / SSP2-4.5 / SSP5-8.5 from
## the accepted Ladrillo (extC) posterior, 1990-2300, cm relative to 1995-2014.
## This is the projection deliverable the sharing memo's SSP section and every
## comparison arm (FACTS, MAGICC, pre-Mengel BRICK 2.0) read.
##
## Basis
##   posterior : data/MimiBRICK/parameters_subsample_brick_mengel_<TAG>.csv,
##               --tag=, default L10 (Ladrillo 1.0, 4 x 2M chains, seeds
##               2026-2029; accepted on the deliverable 2026-08-13). L11 is the
##               D1+D2 change set, accepted 2026-08-15, and stores the Greenland
##               slow channel as (ell, w) — the loader derives the native pair.
##               The Greenland variant is read off the file, not assumed. CAVEAT
##               carried from both acceptances: the 2150 and 2300 columns rest on
##               the AIS tipping tail, the slowest-mixing feature (chain-median
##               spread at 2150 is 13x the 2100 value relative to within-chain
##               scatter, and R-hat is mean-based so it reads 1.000 there anyway).
##   model     : Ladrillo = MimiBRICK v2.0.0 + 3-reservoir glacier emulator +
##               Greenland A+B with the amp(GMST) law, applied through
##               julia/ladrillo_projection.jl (tested by
##               julia/test_ladrillo_projection.jl)
##   forcing   : FaIR mean GMST + OHC per SSP (fair_mean_{gmst,ohc}_<ssp>.csv,
##               RCMIP-native run_fair_ssps.py) — mean forcing, so the reported
##               spread is POSTERIOR-PARAMETER spread, not climate spread
##   baseline  : 1995-2014 (AR6; ~ FACTS baseyear 2005)
##   LWS       : seeded realization (build_brick_nu3 default, LWS_SEED)
##   F_unch    : excluded — hindcast-target construct (see ladrillo_projection.jl)
##
## Bands are 5-95% and 17-83% (AR6 "likely") over FINITE draws; the AIS
## fast-dynamics tail can go non-finite, so the finite count is reported per
## scenario and carried in the output.
##
##   julia --project=julia_v2 julia/project_ssps_components_ladrillo.jl [n_draws] [--tag=L11]
##
## --tag selects the posterior AND the output filename together (default L10).
## ============================================================================

using CSV, DataFrames, Mimi, Printf, Statistics
include(joinpath(@__DIR__, "ladrillo_projection.jl"))

const Y0, Y1   = 1850, 2300
const REPORT0  = 1990                      # first year written out
const NTHIN    = let p = filter(a -> !startswith(a, "--"), ARGS)
    isempty(p) ? 2000 : parse(Int, p[1])
end
## POSTERIOR TAG drives BOTH the input posterior and the output filename, so a
## run on one vintage cannot write a file labelled with another. The default
## tracks the CANONICAL posterior (L14 since 2026-08-20; L12 from 08-18, L11 from
## 08-17, L10 before that), so it
## is derived from LADRILLO_POSTERIOR_CSV rather than written out again — the
## two cannot drift. Passing --tag=X asserts the file exists rather than
## silently falling back, and older vintages stay reachable that way.
const DEFAULT_TAG = let b = basename(LADRILLO_POSTERIOR_CSV)
    replace(replace(b, "parameters_subsample_brick_mengel_" => ""), ".csv" => "")
end
const POST_TAG = let i = findfirst(a -> startswith(a, "--tag="), ARGS)
    i === nothing ? DEFAULT_TAG : ARGS[i][7:end]
end
## THE TAP IS PART OF THE MODULE AND IS ON BY DEFAULT (Marcus 2026-08-23).
## It was opt-in `--tap` while the cell was being chosen. Now that the cell is
## settled, the arm this driver produces with no flags is the SHIPPED Greenland:
## the base arm has to be asked for, by name, with `--no-tap`.
##
## WHAT DID **NOT** CHANGE, AND WHY. The untapped file keeps the plain
## `ssps_components_2300_<TAG>.csv` name and the tapped one keeps its cell-encoded
## name. Swapping the two would have been the tidier-looking flip and it is wrong:
## FOUR live consumers read the plain name meaning the BASE model --
##   python/scope_gis_reservoir_offline.py   (DELIVERABLE; the offline emulator the
##                                            whole cell selection is built on)
##   python/scope_gis_ridge_vs_ssp_bands.py  ("the untapped shipped arm")
##   python/diag_gis_npv_tau_sensitivity.py  ("L14 canonical, UNTAPPED base")
##   julia/test_gis_tap_wiring.jl            (SPREAD_SRC, the 2150 tolerance)
## -- and the last of those would become SELF-REFERENTIAL: it scales "how far may
## the tap move 2150" by a sampled spread that would then already contain the tap.
## So: the DEFAULT ARM moves, the FILENAMES keep their meanings, and no file on disk
## silently changes what it is. `--tap` is still accepted and is now a no-op.
const NO_TAP = "--no-tap" in ARGS
## --tap-set RUNS THE WHOLE ADMISSIBLE SET, not one cell (Marcus 2026-08-21).
##
## WHY. The tap is a PRIOR SPECIFICATION, not a fit: its cell was chosen by the
## don't-move-a-validated-horizon principle, and 25 cells of the priced grid clear
## EVERY pre-registered 2300 gate. Shipping one of them as a point estimate hides
## the larger of the two uncertainties on tapped Greenland@2300 --
##   sampled p05-p95 (reported)      0.268 m
##   cell choice across the 25       1.180 m   <- 4.4x bigger, previously unreported
## The two are different in KIND -- one is posterior spread, the other a choice
## among admissible priors -- so this arm reports them SEPARATELY and never sums
## them. The shipped cell stays the central line; the set gives it a band.
const TAP_SET = any(a -> a == "--tap-set" || startswith(a, "--tap-set="), ARGS)
const TAP_SET_CSV = let i = findfirst(a -> startswith(a, "--tap-set="), ARGS)
    i === nothing ? "" : ARGS[i][11:end]
end
TAP_SET && NO_TAP &&
    error("--no-tap and --tap-set contradict: --tap-set runs the admissible SET of " *
          "tap cells, so there is no untapped arm of it. Pass one.")
## Resolved AFTER TAP_SET is known: the set arm carries its own per-cell taps.
const TAP_ON = !NO_TAP && !TAP_SET
## THE TAP STATE IS IN THE FILENAME. A tapped and an untapped 2300 projection differ
## by ~180 cm on ssp585 and are otherwise identical in shape, units and header — the
## one thing that must never be ambiguous about a file on disk is which arm it is.
## THE STAGE COUNT AND THE HOME ARE IN THE FILENAME TOO (2026-08-23). A cascade run
## and a first-order run at the SAME (onset, V, tau) are different objects — the
## cascade is the whole reason the cell could move to V = 6.0 m — and they would
## otherwise collide on one name. Same for the high-basin vs whole-sheet home, which
## changes what the capacity clamp is measured against. Every element derives from
## GIS_TAP_CELL, so the name cannot drift from the cell it was produced with.
const TAP_STAGE_TAG = "_n$(Int(GIS_TAP_CELL.stages))"
const TAP_HOME_TAG  = GIS_TAP_CELL.wholesheet ? "_ws" : "_hb"
const TAG = TAP_ON ? "$(POST_TAG)_tap$(replace(string(GIS_TAP_CELL.onset_K), "." => "p"))K_V$(replace(string(GIS_TAP_CELL.V_m), "." => "p"))m_tau$(Int(GIS_TAP_CELL.tau_yr))$(TAP_STAGE_TAG)$(TAP_HOME_TAG)" :
            TAP_SET ? "$(POST_TAG)_tapset" : POST_TAG
const POSTERIOR = joinpath(LADRILLO_REPO,
    "data/MimiBRICK/parameters_subsample_brick_mengel_$(POST_TAG).csv")
isfile(POSTERIOR) || error("no posterior for --tag=$POST_TAG at $POSTERIOR")
POST_TAG != DEFAULT_TAG || POSTERIOR == LADRILLO_POSTERIOR_CSV ||
    error("the default tag '$DEFAULT_TAG' resolved to $POSTERIOR, which is not " *
          "LADRILLO_POSTERIOR_CSV ($LADRILLO_POSTERIOR_CSV)")
## THE SHAPE TABLE IS IN THE FILENAME. `LADRILLO_GIS_SHAPE` swaps the amp(GMST)
## law for a pre-registered sensitivity arm, and a fullcurve run and a default run
## are otherwise identical in schema, units and header — so without this, running
## the arm OVERWRITES the deliverable with a sensitivity result under the
## deliverable's own name. Default resolves to "" so default runs keep their exact
## pre-existing filenames and are bit-identical.
const SHAPE_TAG = LADRILLO_GIS_SHAPE_STEM == "gis_amp_shape" ? "" :
    "_" * replace(LADRILLO_GIS_SHAPE_STEM, "gis_amp_shape_" => "shape")
const OUT      = joinpath(LADRILLO_REPO, "outputs/ssps_components_2300_$(TAG)$(SHAPE_TAG).csv")
const SSPS     = [("ssp126", "SSP1-2.6"), ("ssp245", "SSP2-4.5"), ("ssp585", "SSP5-8.5")]
const HORIZONS = (2100, 2150, 2300)
const COMPONENTS = [:glaciers, :gis, :ais, :te, :lws, :total]

const VARIANT = ladrillo_posterior_variant(POSTERIOR)
post = ladrillo_posterior(path=POSTERIOR, nthin=NTHIN)
@printf("Ladrillo SSP components | posterior %s (%d draws) | Greenland :%s | base %d-%d | horizon %d\n",
        basename(POSTERIOR), nrow(post), VARIANT,
        LADRILLO_REF[1], LADRILLO_REF[2], Y1)
VARIANT === :ab && @printf("  amp law ON: S anchored at dT_eff = %.3f K, %d-yr window\n",
                           LADRILLO_GIS_SHAPE_ANCHOR_DT, LADRILLO_GIS_SHAPE_WIN)

## Non-set arms keep the EXACT pre-existing schema so downstream consumers of the
## single-cell files are untouched; the set arm adds three identity columns.
out = TAP_SET ?
    DataFrame(year=Int[], ssp=String[], component=String[], gmst=Float64[],
              med=Float64[], p05=Float64[], p17=Float64[], p83=Float64[], p95=Float64[],
              n_finite=Int[], tap_onset_K=Float64[], tap_V_m=Float64[], tap_tau=Float64[]) :
    DataFrame(year=Int[], ssp=String[], component=String[], gmst=Float64[],
              med=Float64[], p05=Float64[], p17=Float64[], p83=Float64[], p95=Float64[],
              n_finite=Int[])

## The cells to run. Non-set arms run exactly one "cell" of `nothing`, which
## leaves the pre-existing code path bit-identical.
const CELLS = if !TAP_SET
    [nothing]
else
    csv = isempty(TAP_SET_CSV) ?
        joinpath(LADRILLO_REPO, "outputs/gis_tap_admissible_$(POST_TAG).csv") : TAP_SET_CSV
    isfile(csv) || error("--tap-set: no admissible-set file at $csv. Produce it with\n" *
                         "  python3 python/scope_gis_tap_l13.py --tag=$(POST_TAG)\n" *
                         "which writes the passing cells. The set MUST be priced on the " *
                         "SAME vintage being projected — an L13-priced set on an L14 " *
                         "projection is an admissible set nobody re-scored.")
    d = CSV.read(csv, DataFrame)
    cells = [(onset_K=Float64(r.tap_onset_K), V_m=Float64(r.tap_V_m),
              tau_yr=Float64(r.tap_tau)) for r in eachrow(d)]
    isempty(cells) && error("--tap-set: $csv has no rows")
    ## The SHIPPED cell must be a member, or the central line of the band is not
    ## the number every other deliverable reports.
    any(c -> c.onset_K == GIS_TAP_CELL.onset_K && c.V_m == GIS_TAP_CELL.V_m &&
             c.tau_yr == GIS_TAP_CELL.tau_yr, cells) ||
        error("--tap-set: GIS_TAP_CELL (onset $(GIS_TAP_CELL.onset_K) K, V " *
              "$(GIS_TAP_CELL.V_m) m, tau $(GIS_TAP_CELL.tau_yr) yr) is NOT in $csv. " *
              "Either the shipped cell no longer clears the gates on this vintage — " *
              "which is a finding, report it — or the set is from another grid.\n" *
              "EXPECTED as of 2026-08-23: the shipped cell is a 2-STAGE CASCADE and " *
              "every admissible set on disk was priced on the FIRST-ORDER form, which " *
              "an exact n-fold-integral bound has since refuted at every (V, tau, " *
              "onset). The set arm needs a cascade-priced set before it means anything.")
    println("--tap-set: $(length(cells)) admissible cells from ", relpath(csv, LADRILLO_REPO))
    cells
end

for cell in CELLS, (ssp, label) in SSPS
    bf = ladrillo_setup(ssp=ssp, y0=Y0, y1=Y1, gis_variant = VARIANT)
    ## THE SET ARM IS EXPLICITLY FIRST-ORDER / HIGH-BASIN. Its cells were priced that
    ## way, and `ladrillo_set_tap!` now DEFAULTS to the shipped cascade — so omitting
    ## these two keywords would silently re-run a first-order admissible set as
    ## cascades and report the spread of an object nobody scored.
    cell === nothing || ladrillo_set_tap!(bf; v=cell.V_m, onset=cell.onset_K,
                                          tau=cell.tau_yr, stages=1, wholesheet=false)
    ## THE DEFAULT ARM: the Greenland volume tap at GIS_TAP_CELL — a 2-stage cascade,
    ## V = 5.64 m, tau = 800 yr, onset 4.69 K, whole-sheet home. PRIOR-PROPAGATED, not
    ## sampled: the calibration tops out at 1.385 K against the 4.69 K onset, so the
    ## tap is exactly likelihood-inert and the same posterior serves both arms.
    ## `--no-tap` produces the base arm instead.
    ## Gated by julia/test_gis_tap_wiring.jl — 2100 moves by 0.000e+00, cooler
    ## scenarios deviate EXACTLY 0.0, and 2150 moves by well under half Greenland's
    ## own sampled spread there — so a --tap run stays comparable to an untapped one
    ## at every horizon the model is validated at.
    TAP_ON && ladrillo_set_tap!(bf)
    ny = length(bf.years)
    series = Dict(c => Array{Float64}(undef, ny, nrow(post)) for c in COMPONENTS)
    t0 = time()
    for (j, r) in enumerate(eachrow(post))
        ladrillo_run_draw!(bf, r)
        for c in COMPONENTS
            series[c][:, j] = ladrillo_series(bf, c)
        end
        j % 250 == 0 && (print("."); flush(stdout))
    end
    @printf("\n%-9s %d draws in %.0fs\n", label, nrow(post), time() - t0)

    for c in COMPONENTS, (i, y) in enumerate(bf.years)
        y >= REPORT0 || continue
        v = filter(isfinite, @view series[c][i, :])
        base = (y, label, string(c), bf.gmst[i], median(v), quantile(v, 0.05),
                quantile(v, 0.17), quantile(v, 0.83), quantile(v, 0.95), length(v))
        push!(out, TAP_SET ? (base..., cell.onset_K, cell.V_m, cell.tau_yr) : base)
    end
    for y in HORIZONS
        ## in the set arm `out` holds every cell, so the row selector MUST also
        ## pin the cell or it silently averages across the admissible set.
        sel(c) = TAP_SET ?
            (out.year .== y) .& (out.ssp .== label) .& (out.component .== string(c)) .&
                (out.tap_onset_K .== cell.onset_K) .& (out.tap_V_m .== cell.V_m) .&
                (out.tap_tau .== cell.tau_yr) :
            (out.year .== y) .& (out.ssp .== label) .& (out.component .== string(c))
        row(c) = out[sel(c), :]
        @printf("  @%d GMST %+0.2f | glac %5.1f  gis %5.1f  ais %6.1f  te %5.1f  lws %4.1f | TOTAL %6.1f [%5.1f, %6.1f] cm  (finite %d/%d)\n",
                y, bf.gmst[ladrillo_yi(bf, y)], row(:glaciers).med[1], row(:gis).med[1],
                row(:ais).med[1], row(:te).med[1], row(:lws).med[1], row(:total).med[1],
                row(:total).p17[1], row(:total).p83[1], row(:total).n_finite[1], nrow(post))
    end
end

CSV.write(OUT, out)
println("\nwrote ", relpath(OUT, LADRILLO_REPO))

## ---- the ENVELOPE: the cell-choice band, reported SEPARATELY -----------------
## Across cells we take the spread of the per-cell MEDIANS. That is the term a
## single-cell deliverable omits. It is NOT combined with the within-cell p05-p95:
## posterior spread and choice-among-admissible-priors are different in kind, and
## summing them would misrepresent both.
if TAP_SET
    env = DataFrame(year=Int[], ssp=String[], component=String[],
                    med_shipped=Float64[], cell_lo=Float64[], cell_hi=Float64[],
                    cell_width=Float64[], post_p05=Float64[], post_p95=Float64[],
                    post_width=Float64[], n_cells=Int[])
    ship = (out.tap_onset_K .== GIS_TAP_CELL.onset_K) .&
           (out.tap_V_m .== GIS_TAP_CELL.V_m) .& (out.tap_tau .== GIS_TAP_CELL.tau_yr)
    for y in HORIZONS, (_, label) in SSPS, c in COMPONENTS
        m = (out.year .== y) .& (out.ssp .== label) .& (out.component .== string(c))
        any(m) || continue
        meds = out.med[m]
        sh = out[m .& ship, :]
        nrow(sh) == 1 || continue
        push!(env, (y, label, string(c), sh.med[1], minimum(meds), maximum(meds),
                    maximum(meds) - minimum(meds), sh.p05[1], sh.p95[1],
                    sh.p95[1] - sh.p05[1], count(m)))
    end
    ENVOUT = replace(OUT, "_tapset$(SHAPE_TAG).csv" => "_tapset$(SHAPE_TAG)_envelope.csv")
    CSV.write(ENVOUT, env)
    println("wrote ", relpath(ENVOUT, LADRILLO_REPO))
    println("\n=== CELL-CHOICE BAND vs SAMPLED SPREAD (cm) — reported separately ===")
    @printf("  %-6s %-9s %-8s %8s %18s %8s %18s\n",
            "year", "ssp", "comp", "shipped", "cell band", "width", "posterior p05-p95")
    for r in eachrow(env)
        r.component in ("gis", "total") || continue
        @printf("  %-6d %-9s %-8s %8.1f  [%6.1f, %6.1f] %8.1f  [%6.1f, %6.1f] %6.1f\n",
                r.year, r.ssp, r.component, r.med_shipped, r.cell_lo, r.cell_hi,
                r.cell_width, r.post_p05, r.post_p95, r.post_width)
    end
end
