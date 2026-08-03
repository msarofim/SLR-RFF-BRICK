## ============================================================================
## retrofit_provenance.jl — emit provenance sidecars for the 2026-08-02 production runs that
## completed BEFORE provenance emission was wired into the driver.
##
## HONESTY REQUIREMENT: these sidecars are RECONSTRUCTED from the archived run logs + the (unchanged)
## input files, not emitted by the run itself. Every one carries
## `provenance_source = RECONSTRUCTED ...` so it is never mistaken for a live record.
##
## Reuses `provenance()` from run_provenance.jl so there is exactly ONE field schema — a second
## hand-written schema here would drift from the driver's and defeat the purpose.
##
## Validation (do not trust a retrofit you have not checked): re-run ONE of the four cases with the
## provenance-wired driver and confirm (a) the numeric columns are byte-identical to the existing
## bands CSV and (b) the emitted sidecar agrees with the reconstruction on every run-invariant field.
##
## Usage: julia --project=julia_v2 julia/retrofit_provenance.jl
## ============================================================================
using Mimi, MimiBRICK, CSV, DataFrames, Printf
const REPO = abspath(joinpath(@__DIR__, ".."))
include(joinpath(@__DIR__, "run_provenance.jl"))

const MCMC = joinpath(REPO, "outputs/mcmc")
const LOGS = joinpath(MCMC, "logs")
const POST = joinpath(REPO, "data/MimiBRICK/parameters_subsample_brick_mengel_extA108.csv")
const FRC  = joinpath(REPO, "..", "FaIRtoFrEDI", "magicc_comparison", "processed", "curv_wide")

# The code state that produced these runs: the pulse-arm + fast-engine commit. (dafb300 only ADDED
# docs/results on top; no driver change between them.)
const RUN_COMMIT = "4debe87 (pulse arm + fast engine; docs-only commit dafb300 followed)"

"parse c, ESS/N, config/draw counts and pulse-unit out of an archived run log"
function parse_log(path)
    txt = read(path, String)
    m_c   = match(r"c = ([\d.eE+-]+) → mean conditional ESS/N = ([\d.]+)", txt)
    m_n   = match(r"(\d+) configs × (\d+) draws\)", txt)   # NB no leading paren: the log line is "(c=…, ESS/N=…, 841 configs × 2000 draws)"
    m_u   = match(r"pulse marginal.*?cm per ([^;]+);"is, txt)
    m_t   = match(r"projection loop: ([\d.]+) s = ([\d.]+) ms/run over (\d+) runs", txt)
    (c = m_c === nothing ? "UNKNOWN" : m_c[1],
     ess = m_c === nothing ? "UNKNOWN" : m_c[2],
     ncfg = m_n === nothing ? "UNKNOWN" : m_n[1],
     nd = m_n === nothing ? "UNKNOWN" : m_n[2],
     unit = m_u === nothing ? "GtCO2" : strip(m_u[1]),
     wall = m_t === nothing ? "UNKNOWN" : @sprintf("%.0f s (%s ms/run over %s runs)", parse(Float64,m_t[1]), m_t[2], m_t[3]))
end

# (output suffix, archived log, basis suffix, integrator, pulse size+unit)
const RUNS = [
 ("_annualstep",                    "production_stoch.log",       "",                      "ANNUAL-STEP (pristine component)",  "10 GtCO2"),
 ("_nonoise_flatsolar_annualstep",  "production_nnfs.log",        "_nonoise_flatsolar",    "ANNUAL-STEP (pristine component)",  "10 GtCO2"),
 ("_subann",                        "production_stoch_subann.log", "",                     "SUB-ANNUAL (frac patch ACTIVE)",    "10 GtCO2"),
 ("_nonoise_flatsolar_subann",      "production_nnfs_subann.log", "_nonoise_flatsolar",    "SUB-ANNUAL (frac patch ACTIVE)",    "10 GtCO2"),
]

for (sfx, logname, basis, integ, pulse) in RUNS
    logpath = joinpath(LOGS, logname)
    isfile(logpath) || (@warn "missing archived log, skipping" logname; continue)
    L = parse_log(logpath)
    unit = split(pulse)[2] * (length(split(pulse)) > 2 ? " " * split(pulse)[3] : "")
    rec = provenance(
        driver = "weight_and_project_brick_fair.jl",
        repo   = REPO,
        posterior = POST,
        forcing_files = [joinpath(FRC,"fair_$(v)_$(a)_wide$(basis).csv") for v in ("gmst","ohc") for a in ("base","pulse")],
        units  = "SLR cm; pulse marginals are cm per 1 $(unit)",
        reference_period = "1995-2005 mean (SLR anomalies re-referenced per draw)",
        weighting = "COUPLED = conditional importance weighting w_{i|k} ∝ exp[c·(ℓ^FB−ℓ^B)] normalized " *
                    "within each FaIR config (p(config) uniform; forcing marginal untouched); " *
                    "c=$(L.c), achieved mean conditional ESS/N=$(L.ess). INDEPENDENT = equal weights.",
        integrator_override = integ,
        extra = [
            "provenance_source"   => "RECONSTRUCTED post-hoc from archived run log ($(logname)) + " *
                                     "unchanged input files — NOT emitted by the run. Later runs emit live records.",
            "code_git_commit_run" => RUN_COMMIT,
            "forcing_basis"       => (occursin("nonoise", basis) ?
                                       "DETERMINISTIC (stochastic_run=False + future solar held at trailing 11-yr cycle mean)" :
                                       "STOCHASTIC (FaIR internal variability ON, canonical)") *
                                     (isempty(basis) ? "" : "; wide-file suffix '$(basis)'"),
            "pulse_spec"          => "+$(pulse) @2030, SSP2-4.5, paired in-process per (config,draw)",
            "amplification_prior" => "amp ~ N(1.080, 0.150) on [0.630, 1.530] (A6 CMIP6 land-frame secant)",
            "lws_mode"            => "build_brick_mengel default (:seeded, LWS_SEED=2026)",
            "ensemble_size"       => "$(L.ncfg) FaIR configs × $(L.nd) BRICK-AM posterior draws",
            "projection_window"   => "1850-2300",
            "engine"              => "fast (in-place instance mutation; validated byte-identical to update_param!)",
            "wall_time"           => L.wall,
            "archived_log"        => "outputs/mcmc/logs/$(logname)",
            "quotability"         => occursin("annualstep", sfx) ?
                "DIAGNOSTIC ONLY — annual stepping freezes the DAIS tip channel and suppresses pulse statistics; do not quote" :
                "QUOTABLE — report the MEAN, or a mode decomposition (smooth-mode median + tip fraction + tip mass); the pooled MEDIAN is sample-fragile",
        ])
    write_provenance(joinpath(MCMC, "wong_cond_runmeta$(sfx).csv"), rec)
end
println("\nRetrofit done. Sidecars are marked RECONSTRUCTED; validate against a live re-run before citing.")
