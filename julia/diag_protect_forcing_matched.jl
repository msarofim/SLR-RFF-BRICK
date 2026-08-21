## ============================================================================
## diag_protect_forcing_matched.jl — the tapped Greenland cell under the PROTECT
## x2300 arm's OWN forcing, which is the comparison the 2150/2300 gap needs.
##
## WHY (2026-08-21, notes/handoff_2026-08-21_protect_greenland.md section 5 item 1)
##   The handoff compared our tapped Greenland at 2150/2300 against the PROTECT
##   x2300 physics ensemble and read "2300 agrees to 1.4%, 2150 is 38% low" as
##   evidence that the tap ONSET IS TOO LATE. Step 5.1 was to check the x2300
##   forcing path before acting. It is NOT our path:
##       11-yr GSAT, C vs 1850-1900   2100   2150   2300
##       ours                         4.70   6.40   7.78
##       PROTECT x2300 (12 IPSL-CM6A-LR : 6 CESM2-WACCM)
##                                    6.61   9.86  13.64
##   Our path crosses the 6.5 K onset in 2154; theirs crosses it in 2097-2101.
##   So the 2150 comparison was between worlds ~3.5 K apart, and the 2300
##   "agreement" was between worlds ~5.9 K apart. This driver re-runs OUR model
##   on THEIR forcing so the two numbers are about the ice sheet, not the climate.
##
## WHAT IS AND IS NOT VARIED
##   Only GMST is swapped (`gmst=` override on ladrillo_setup). OHC stays on our
##   ssp585 (fair_mean_ohc_ssp585.csv), so THERMAL EXPANSION AND `total` ARE NOT
##   INTERPRETABLE in these runs and are written out only so the schema matches.
##   READ `gis` AND NOTHING ELSE. Asserted below rather than left to a caption.
##
## ARMS (each x {shipped cell, whole admissible set})
##   ours      the shipped forcing — reproduces the existing run, the control
##   spliced   ours through 2014, PROTECT thereafter (11-yr smoothed): the
##             controlled experiment, changes only the future path
##   raw       PROTECT on its own 1850-1900 baseline throughout: prices the
##             splice choice (it also moves the hindcast anchor)
##   Smoothing is a CHOICE and is priced: our driver is an ensemble mean and is
##   already smooth, the PROTECT path is one member per GCM, and the tap consumes
##   gmt unsmoothed. `--unsmoothed` reruns the PROTECT arms on annual values.
##
##   julia --project=julia_v2 julia/diag_protect_forcing_matched.jl [n_draws] [--family=r2300] [--set] [--untapped] [--unsmoothed]
##   julia --project=julia_v2 julia/diag_protect_forcing_matched.jl --scan=<cells.csv>   (exploratory)
## ============================================================================

using CSV, DataFrames, Mimi, Printf, Statistics
include(joinpath(@__DIR__, "ladrillo_projection.jl"))

const Y0, Y1  = 1850, 2300
const NTHIN   = let p = filter(a -> !startswith(a, "--"), ARGS)
    isempty(p) ? 2000 : parse(Int, p[1])
end
const DO_SET     = "--set" in ARGS
## --untapped SEPARATES THE TWO EXPLANATIONS. At matched forcing the shipped cell
## overshoots PROTECT at 2150 by 3.5x, and that could be (a) our BASE Greenland
## being more GMST-sensitive than NORCE-CISM or (b) the tap draining too fast.
## Running v = 0 on the same forcing measures (a) alone; the tapped-minus-untapped
## difference is (b). Without this split the 3.5x is uninterpretable.
const UNTAPPED   = "--untapped" in ARGS
## --scan=<csv> runs ARBITRARY cells, INCLUDING ones outside the priced grid, and
## is EXPLORATORY ONLY. It deliberately skips the --set membership check: the
## question it answers is "what shape would fit the physics", and by construction
## the answer may lie outside the admissible set. Nothing from a --scan run is a
## candidate for shipping until it has been through the pre-registered 2300 gates
## (python/scope_gis_tap_l13.py) on OUR forcing, where an onset above ssp585's own
## 7.81 K peak fires never and contributes exactly zero.
const SCAN_CSV = let i = findfirst(a -> startswith(a, "--scan="), ARGS)
    i === nothing ? "" : ARGS[i][8:end]
end
!(!isempty(SCAN_CSV) && DO_SET) || error("--scan and --set are different arms; pass one")
const UNSMOOTHED = "--unsmoothed" in ARGS
## --family selects WHICH PROTECT experiment family this arm compares against.
##   x2300  natural CMIP6 extension. 18 runs, 2 GCMs, several CISM configs, and it
##          runs at 9.8-13.6 K -- far above our own 4.7-7.8 K.
##   r2300  forcing HELD at the 2100 level (Goelzer 2025). 35 usable runs, 5 GCMs,
##          ONE CISM config, plateau 5.58 K. Closer to our scenario and a wider
##          climate sample, but the tap NEVER FIRES on it (plateau < 6.5 K onset),
##          so it tests the BASE model's committed-loss response, not the tap.
## The family is in the output filename: the two arms are otherwise identical in
## schema and would be indistinguishable on disk.
const FAMILY = let i = findfirst(a -> startswith(a, "--family="), ARGS)
    i === nothing ? "x2300" : ARGS[i][10:end]
end
FAMILY in ("x2300", "r2300") || error("--family must be x2300 or r2300, got $FAMILY")
const FAM_TAG = FAMILY == "x2300" ? "" : "_$(FAMILY)"
const SSP        = "ssp585"
const LABEL      = "SSP5-8.5"
const HORIZONS   = (2100, 2150, 2300)
const COMPONENTS = [:gis]                      # see "WHAT IS AND IS NOT VARIED"
const SUF        = UNSMOOTHED ? "" : "_11yr"
const TAG        = let b = basename(LADRILLO_POSTERIOR_CSV)
    replace(replace(b, "parameters_subsample_brick_mengel_" => ""), ".csv" => "")
end
## THE SHAPE TABLE IS IN THE FILENAME. `LADRILLO_GIS_SHAPE` swaps the amp(GMST)
## law for a pre-registered sensitivity arm, and a fullcurve run and a default run
## are otherwise identical in schema, units and header — so without this, running
## the arm OVERWRITES the deliverable with a sensitivity result under the
## deliverable's own name. Default resolves to "" so default runs keep their exact
## pre-existing filenames and are bit-identical.
const SHAPE_TAG = LADRILLO_GIS_SHAPE_STEM == "gis_amp_shape" ? "" :
    "_" * replace(LADRILLO_GIS_SHAPE_STEM, "gis_amp_shape_" => "shape")
const OUT = joinpath(LADRILLO_REPO,
    "outputs/diag_protect_forcing_matched_$(TAG)$(FAM_TAG)$(SHAPE_TAG)$(DO_SET ? "_set" : "")$(isempty(SCAN_CSV) ? "" : "_scan")$(UNTAPPED ? "_untapped" : "")$(UNSMOOTHED ? "_raw" : "").csv")

const FORCING = joinpath(LADRILLO_REPO, "outputs/protect_$(FAMILY)_forcing_gmst.csv")
isfile(FORCING) || error("no $FORCING — run python3 python/build_protect_$(FAMILY)_forcing.py")
fdf = CSV.read(FORCING, DataFrame)
years = collect(Y0:Y1)
fmap(col) = (d = Dict(Int(fdf[i, "year"]) => Float64(fdf[i, col]) for i in 1:nrow(fdf));
             [d[y] for y in years])

## The `ours` arm must be the SHIPPED driver, not a smoothed copy of it — otherwise
## the control is not the run it is controlling for.
const OURS_SHIPPED = [_yearmap(joinpath(LADRILLO_OBS, "fair_mean_gmst_$(SSP).csv"), "gmst_C")[y]
                      for y in years]
let chk = maximum(abs.(OURS_SHIPPED .- fmap("gmst_ours")))
    chk < 1e-9 || error("the forcing table's gmst_ours column ($(chk)) is not " *
                        "fair_mean_gmst_$(SSP).csv — the control would be wrong")
end

const ARMS = [("ours", OURS_SHIPPED),
              ("spliced", fmap("gmst_spliced$(SUF)")),
              ("raw", fmap("gmst_raw$(SUF)"))]

const CELLS = if !isempty(SCAN_CSV)
    isfile(SCAN_CSV) || error("--scan: no file at $SCAN_CSV")
    d = CSV.read(SCAN_CSV, DataFrame)
    println("--scan: $(nrow(d)) EXPLORATORY cells from $SCAN_CSV — NOT an admissible set")
    [(onset_K=Float64(r.tap_onset_K), V_m=Float64(r.tap_V_m),
      tau_yr=Float64(r.tap_tau), ramp_w_K=GIS_TAP_CELL.ramp_w_K) for r in eachrow(d)]
elseif !DO_SET
    [GIS_TAP_CELL]
else
    csv = joinpath(LADRILLO_REPO, "outputs/gis_tap_admissible_$(TAG).csv")
    isfile(csv) || error("--set: no admissible-set file at $csv (see " *
                         "project_ssps_components_ladrillo.jl --tap-set)")
    d = CSV.read(csv, DataFrame)
    cells = [(onset_K=Float64(r.tap_onset_K), V_m=Float64(r.tap_V_m),
              tau_yr=Float64(r.tap_tau), ramp_w_K=GIS_TAP_CELL.ramp_w_K) for r in eachrow(d)]
    any(c -> c.onset_K == GIS_TAP_CELL.onset_K && c.V_m == GIS_TAP_CELL.V_m &&
             c.tau_yr == GIS_TAP_CELL.tau_yr, cells) ||
        error("--set: GIS_TAP_CELL is not in $csv — the set is from another grid")
    cells
end

const VARIANT = ladrillo_posterior_variant(LADRILLO_POSTERIOR_CSV)
post = ladrillo_posterior(path=LADRILLO_POSTERIOR_CSV, nthin=NTHIN)
@printf("PROTECT %s matched-forcing | posterior %s (%d draws) | Greenland :%s | %s | %d cell(s) | %s\n",
        FAMILY, basename(LADRILLO_POSTERIOR_CSV), nrow(post), VARIANT, LABEL, length(CELLS),
        UNSMOOTHED ? "PROTECT arms ANNUAL (unsmoothed)" : "PROTECT arms 11-yr centred")
@printf("  amp law: %s, fitted support %.2f-%.2f K, FLAT-HELD above it | amp*S high-dT = %.3f\n",
        LADRILLO_GIS_SHAPE_STEM, _GIS_SHAPE_META.dt_min, _GIS_SHAPE_META.dt_max,
        1.922 * ladrillo_gis_shape(99.0))
UNTAPPED && println("  TAP OFF (v = 0) — this arm measures the BASE Greenland model only.")
println("  GIS ONLY — OHC is left on ours, so te/total from this driver are meaningless.")

out = DataFrame(year=Int[], arm=String[], component=String[], gmst=Float64[],
                med=Float64[], p05=Float64[], p17=Float64[], p83=Float64[], p95=Float64[],
                n_finite=Int[], tap_onset_K=Float64[], tap_V_m=Float64[], tap_tau=Float64[])

for cell in CELLS, (arm, gm) in ARMS
    bf = ladrillo_setup(ssp=SSP, y0=Y0, y1=Y1, gis_variant=VARIANT, gmst=gm)
    ladrillo_set_tap!(bf; v=(UNTAPPED ? 0.0 : cell.V_m), onset=cell.onset_K, tau=cell.tau_yr)
    series = Dict(c => Array{Float64}(undef, length(bf.years), nrow(post)) for c in COMPONENTS)
    t0 = time()
    for (j, r) in enumerate(eachrow(post))
        ladrillo_run_draw!(bf, r)
        for c in COMPONENTS; series[c][:, j] = ladrillo_series(bf, c); end
        j % 500 == 0 && (print("."); flush(stdout))
    end
    for c in COMPONENTS, (i, y) in enumerate(bf.years)
        y >= 1990 || continue
        v = filter(isfinite, @view series[c][i, :])
        push!(out, (y, arm, string(c), bf.gmst[i], median(v), quantile(v, 0.05),
                    quantile(v, 0.17), quantile(v, 0.83), quantile(v, 0.95), length(v),
                    cell.onset_K, cell.V_m, cell.tau_yr))
    end
    if !DO_SET && (isempty(SCAN_CSV) || arm == "spliced")
        @printf("\n%-8s onset %.1f K V %.1f m tau %.0f yr | %d draws in %.0fs\n",
                arm, cell.onset_K, cell.V_m, cell.tau_yr, nrow(post), time() - t0)
        for y in HORIZONS
            ## PIN THE CELL. `out` accumulates across cells, so a selector on
            ## (year, arm, component) alone returns the FIRST cell's row for every
            ## later cell — which printed twelve identical scan lines before this
            ## was caught. Same trap project_ssps_components_ladrillo.jl flags for
            ## its --tap-set arm; the CSV was always right, only the console lied.
            r = out[(out.year .== y) .& (out.arm .== arm) .& (out.component .== "gis") .&
                    (out.tap_onset_K .== cell.onset_K) .& (out.tap_V_m .== cell.V_m) .&
                    (out.tap_tau .== cell.tau_yr), :]
            @printf("  @%d GMST %+0.2f | gis %6.1f [%6.1f, %6.1f] cm\n",
                    y, bf.gmst[ladrillo_yi(bf, y)], r.med[1], r.p05[1], r.p95[1])
        end
    end
end

CSV.write(OUT, out)
println("\nwrote ", relpath(OUT, LADRILLO_REPO))
