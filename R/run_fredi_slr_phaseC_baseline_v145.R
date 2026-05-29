# run_fredi_slr_phaseC_baseline_v145.R
# ====================================
#
# v1.4.5 calibration + post-PR#93 BRICK rerun of the FrEDI phaseC coastal-
# damage analysis. Same structure as the legacy archive driver but reads
# the 1000-draw SIR-resampled v145 inputs and writes _v145-suffixed outputs.
#
# Inputs (in outputs/), built by python/scripts/build_fredi_inputs_v145.py:
#   - fredi_input_rff_baseline_gmst_v145.csv  -- wide, 1000 rows, year cols
#                                                2000-2300, GMST °C rel 1986-2005
#   - fredi_input_rff_baseline_slr_v145.csv   -- wide, 1000 rows, year cols
#                                                2000-2300, SLR cm rel 2000
# Both carry draw_idx, rff_idx, fair_cfg_idx, seed_idx, post_idx, w_norm metadata.
# w_norm is uniformly 1/1000 (SIR resampling yields equal-weighted draws from
# the importance-weighted target).
#
# Output:
#   - outputs/fredi_slr_phaseC_rff_baseline_v145_long.csv         (national)
#   - outputs/fredi_slr_phaseC_rff_baseline_v145_state_long.csv   (state-level)
#
# Sectors run (all SLR-driven or have an SLR component in FrEDI):
#   - Coastal Properties              (variant: Reactive Adaptation)
#   - Transportation Impacts from High Tide Flooding
#                                     (variant: Reasonably Anticipated Adaptation)
# These are the two purely-SLR-driven FrEDI sectors. (Other sectors like Roads
# and Rail also accept SLR but are primarily temperature-driven; we keep this
# headline run focused on the two pure-coastal sectors. Easy to add later.)
#
# Conventions: aggregate to national × modelaverage × impactyear, then filter
# impactYear == "Interpolation".
#
# Wallclock: ~6s/draw × 2 sectors × 1000 draws / (parallel jobs).
# Single core: ~100 min. With parallel 4 cores: ~25 min. With parallel 8: ~13 min.
#
# Usage:
#   Rscript R/run_fredi_slr_phaseC_baseline_v145.R [n_parallel]
# Default n_parallel: detectCores() - 1.

suppressPackageStartupMessages({
  library(FrEDI)
  library(dplyr)
  library(tidyr)
  library(readr)
  library(parallel)
})

# ---------------------------------------------------------------------------
# Paths / constants
# ---------------------------------------------------------------------------
PROJ_DIR <- "/Users/MarcusMarcus/Documents/2026/CodeProjects/SLR-RFF-BRICK"
OUT_DIR  <- file.path(PROJ_DIR, "outputs")
# Defaults: v1.4.5 single-seed LHS-10k. Override via env vars to retarget the
# v5 LHS-10k_s noise-isolated ensemble (e.g. FREDI_TAG=v145_lhs10ks).
TAG           <- Sys.getenv("FREDI_TAG", "v145")
GMST_CSV      <- Sys.getenv("FREDI_GMST_CSV", file.path(OUT_DIR, sprintf("fredi_input_rff_baseline_gmst_%s.csv", TAG)))
SLR_CSV       <- Sys.getenv("FREDI_SLR_CSV",  file.path(OUT_DIR, sprintf("fredi_input_rff_baseline_slr_%s.csv",  TAG)))
OUT_CSV       <- Sys.getenv("FREDI_OUT_CSV",  file.path(OUT_DIR, sprintf("fredi_slr_phaseC_rff_baseline_%s_long.csv", TAG)))
OUT_STATE_CSV <- Sys.getenv("FREDI_OUT_STATE_CSV", file.path(OUT_DIR, sprintf("fredi_slr_phaseC_rff_baseline_%s_state_long.csv", TAG)))
cat(sprintf("TAG: %s\n  GMST input:  %s\n  SLR input:   %s\n  national out: %s\n  state out:    %s\n",
            TAG, GMST_CSV, SLR_CSV, OUT_CSV, OUT_STATE_CSV))
POP_FILE <- file.path(system.file(package = "FrEDI"),
                      "extdata/scenarios/State ICLUS Population.csv")

# Sectors of interest (SLR-driven coastal damages)
SECTORS <- c("Coastal Properties",
             "Transportation Impacts from High Tide Flooding")
SECTOR_VARIANTS <- c("Coastal Properties" = "Reactive Adaptation",
                     "Transportation Impacts from High Tide Flooding" =
                       "Reasonably Anticipated Adaptation")

# FrEDI calls — common settings
AGG_LEVELS <- c("national", "modelaverage", "impactyear")
MAX_YEAR <- 2300        # Phase C horizon
THRU_2300 <- TRUE       # required since maxYear > 2100

# CLI: optional n_parallel argument
args <- commandArgs(trailingOnly = TRUE)
n_parallel <- if (length(args) > 0) as.integer(args[[1]]) else max(1, detectCores() - 1)
cat(sprintf("Parallel workers: %d\n", n_parallel))

# ---------------------------------------------------------------------------
# Load inputs
# ---------------------------------------------------------------------------
cat("Loading inputs...\n")
gmst_wide <- read.csv(GMST_CSV, check.names = FALSE)
slr_wide  <- read.csv(SLR_CSV,  check.names = FALSE)
stopifnot(nrow(gmst_wide) == nrow(slr_wide))
stopifnot(all(gmst_wide$draw_idx == slr_wide$draw_idx))
n_draws <- nrow(gmst_wide)
cat(sprintf("  %d paired draws\n", n_draws))

# Year columns
year_cols <- grep("^[0-9]+$", names(gmst_wide), value = TRUE)
years <- as.integer(year_cols)
cat(sprintf("  year range: %d-%d (n=%d)\n", min(years), max(years), length(years)))

# Metadata columns (everything that isn't a year)
meta_cols <- setdiff(names(gmst_wide), year_cols)
cat(sprintf("  metadata columns: %s\n", paste(meta_cols, collapse = ", ")))

# ---------------------------------------------------------------------------
# Per-draw FrEDI runner
# ---------------------------------------------------------------------------
run_one_draw <- function(i) {
  # FrEDI needs the temperature global->CONUS conversion which only happens
  # inside import_inputs() when reading from a file. Override after-the-fact
  # doesn't trigger conversion. So write per-draw tempfiles to a session tempdir.
  td <- tempdir()
  temp_path <- file.path(td, sprintf("draw_%05d_temp.csv", i))
  slr_path  <- file.path(td, sprintf("draw_%05d_slr.csv",  i))
  write.csv(data.frame(year = years,
                       temp_C_global = unname(as.numeric(gmst_wide[i, year_cols]))),
            temp_path, row.names = FALSE)
  write.csv(data.frame(year = years,
                       slr_cm = unname(as.numeric(slr_wide[i, year_cols]))),
            slr_path, row.names = FALSE)

  # import_inputs() doesn't have a silent flag; wrap to silence the per-call
  # "Loading data... Checking values... Finished." output that floods the
  # parallel log when 8 workers fire simultaneously.
  inputs <- suppressMessages(invisible(
    capture.output(
      inputs_tmp <- import_inputs(
        tempfile = temp_path,
        slrfile  = slr_path,
        popfile  = POP_FILE,
        temptype = "global"
      )
    )
  ))
  inputs <- inputs_tmp

  per_sector <- list()
  for (sec in SECTORS) {
    variant <- SECTOR_VARIANTS[[sec]]
    res <- tryCatch(
      run_fredi(
        inputsList = inputs,
        sectorList = sec,
        aggLevels  = AGG_LEVELS,
        maxYear    = MAX_YEAR,
        thru2300   = THRU_2300,
        silent     = TRUE
      ),
      error = function(e) {
        warning(sprintf("draw %d sector '%s': %s", i, sec, conditionMessage(e)))
        NULL
      }
    )
    if (is.null(res)) next

    # FrEDI emits both per-state rows and a pre-aggregated state="All" row
    # when aggLevels includes "national". Keep both so we can do both the
    # national headline AND the state-level map. Save only headline years
    # to keep the state CSV reasonable in size.
    res <- res |>
      filter(variant == !!variant,
             impactYear == "Interpolation",
             !is.na(annual_impacts)) |>
      select(sector, variant, impactType, state, postal,
             year, annual_impacts, driverValue) |>
      mutate(draw_idx = gmst_wide$draw_idx[i])
    per_sector[[sec]] <- res
  }
  # Clean up tempfiles (small but accumulates over 500 draws)
  file.remove(temp_path, slr_path)
  if (length(per_sector) == 0) return(NULL)
  bind_rows(per_sector)
}

# ---------------------------------------------------------------------------
# Loop (parallel)
# ---------------------------------------------------------------------------
cat(sprintf("Running FrEDI for %d draws across %d sectors (parallel=%d)...\n",
            n_draws, length(SECTORS), n_parallel))

t0 <- Sys.time()
if (n_parallel > 1) {
  # mclapply works on macOS (fork-based). Each worker inherits the loaded
  # FrEDI namespace + the gmst_wide/slr_wide/years globals.
  results <- mclapply(seq_len(n_draws), run_one_draw,
                      mc.cores = n_parallel,
                      mc.preschedule = TRUE)
} else {
  results <- vector("list", n_draws)
  for (i in seq_len(n_draws)) {
    results[[i]] <- run_one_draw(i)
    if (i %% 25 == 0) {
      el <- as.numeric(Sys.time() - t0, units = "secs")
      cat(sprintf("  %d/%d done (%.0fs elapsed, ETA %.0fs)\n",
                  i, n_draws, el, el * (n_draws - i) / i))
    }
  }
}
el <- as.numeric(Sys.time() - t0, units = "secs")
cat(sprintf("Done in %.1f minutes.\n", el / 60))

# ---------------------------------------------------------------------------
# Combine + attach weights + write
# ---------------------------------------------------------------------------
results <- results[!sapply(results, is.null)]
all_long <- bind_rows(results)
cat(sprintf("Combined: %d rows\n", nrow(all_long)))

# Attach Wong w_norm
meta_df <- gmst_wide[, c("draw_idx", "w_norm")]
all_long <- left_join(all_long, meta_df, by = "draw_idx")

# Split into national + state-level
national_long <- all_long |> filter(state == "All")
state_long    <- all_long |> filter(state != "All")

dir.create(dirname(OUT_CSV), recursive = TRUE, showWarnings = FALSE)
write_csv(national_long, OUT_CSV)
write_csv(state_long,    OUT_STATE_CSV)
cat(sprintf("Wrote national: %s (%d rows)\n", OUT_CSV, nrow(national_long)))
cat(sprintf("Wrote state:    %s (%d rows)\n", OUT_STATE_CSV, nrow(state_long)))

# Quick headline (unweighted preview)
hl <- national_long |>
  group_by(sector, year) |>
  summarise(p10 = quantile(annual_impacts, 0.10, na.rm = TRUE),
            p50 = quantile(annual_impacts, 0.50, na.rm = TRUE),
            p90 = quantile(annual_impacts, 0.90, na.rm = TRUE),
            mean = mean(annual_impacts, na.rm = TRUE),
            .groups = "drop") |>
  filter(year %in% c(2050, 2100, 2150, 2300))

cat("\n=== Unweighted national preview (annual_impacts in USD) ===\n")
print(hl)
