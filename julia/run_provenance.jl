## ============================================================================
## run_provenance.jl — self-documenting provenance for every big-analysis output.
##
## Standing convention (Marcus 2026-08-02): the output of every substantial analysis must carry the
## model version + updates, units, and other key aspects, so (a) consistency with other runs can be
## checked mechanically and (b) the run is citable in a paper months later without archaeology.
##
## The axes that silently move numbers by 2-3x in this project, and are therefore MANDATORY fields:
##   BRICK lineage (pre-#93 / BRICK2.0 / BRICK-AM) . posterior subsample vintage . amplification prior
##   . LWS mode . ANNUAL vs SUB-ANNUAL DAIS integrator . stochastic vs deterministic forcing basis
##   . pulse gas/size/UNIT . importance-weighted vs equal . reference period.
##
## DESIGN RULE: AUTO-DETECT, never hardcode. Hashes, depot patch state, pkgversion, git rev and file
## mtimes are read from the live environment — a hand-typed label is exactly the thing that goes stale
## (this is the labels-derive-from-named-constants discipline applied to provenance).
##
## Usage:
##   include("run_provenance.jl")
##   prov = provenance(; driver="weight_and_project_brick_fair.jl", repo=REPO, extra=Dict(...))
##   write_provenance(joinpath(REPO,"outputs/mcmc/foo_runmeta.csv"), prov)   # long key,value sidecar
##   stamp!(df, prov)                                                        # key cols INTO the results
## ============================================================================
using Dates, SHA, Printf, DataFrames, CSV

"short sha256 of a file's contents (identity that survives copying/renaming)"
function filehash(path::AbstractString; n::Int=12)
    isfile(path) || return "MISSING"
    bytes2hex(open(sha256, path))[1:n]
end

function _fileid(path)
    isfile(path) || return "MISSING:" * basename(path)
    sz = filesize(path)
    hs = sz < 1_000_000 ? @sprintf("%.0f KB", sz/1e3) : @sprintf("%.1f MB", sz/1e6)
    @sprintf("%s (%s, sha %s)", basename(path), hs, filehash(path))
end

"`git rev-parse` + dirty flag for the repo holding the code that produced a result"
function gitrev(repo::AbstractString)
    try
        rev = readchomp(`git -C $repo rev-parse --short HEAD`)
        dirty = !isempty(readchomp(`git -C $repo status --porcelain`))
        return dirty ? rev * "-DIRTY" : rev
    catch
        return "UNKNOWN(not a git repo or git unavailable)"
    end
end

"""
    dais_integrator()

Detect whether the LOADED MimiBRICK depot's Antarctic component carries the sub-annual crossing patch
(`frac`). This is THE field people get wrong by assertion: the annual-step integrator freezes the DAIS
tip channel and suppresses pulse statistics ~2-3x, and the patch is applied by hand to a shared depot,
so intent and reality diverge. Resolved via the actually-loaded MimiBRICK module path, NOT a glob over
depot slugs (there are several installed).
"""
function dais_integrator()
    path = try
        joinpath(dirname(dirname(pathof(MimiBRICK))), "src", "components", "antarctic_icesheet_component.jl")
    catch
        return ("UNKNOWN", "MimiBRICK not loaded")
    end
    isfile(path) || return ("UNKNOWN", "component file not found: $path")
    occursin("frac", read(path, String)) ?
        ("SUB-ANNUAL (frac patch ACTIVE)", _fileid(path)) :
        ("ANNUAL-STEP (pristine component)", _fileid(path))
end

"""
    provenance(; driver, repo, kwargs...)

Build the ordered (key => value) provenance record. Every value is a String so the sidecar is a clean
2-column CSV that diffs cleanly between runs. `extra` is merged last for run-specific fields.
"""
function provenance(; driver::AbstractString,
                      repo::AbstractString,
                      model_lineage::AbstractString = "BRICK-AM (Antarctic-Mengel; MimiBRICK v2.0.0 fork + Mengel-2016 glaciers)",
                      calibrator::AbstractString = "calibrate_mcmc_ext.jl (CANONICAL, mean forcing)",
                      posterior::AbstractString = "",
                      forcing_files::Vector{<:AbstractString} = String[],
                      units::AbstractString = "",
                      reference_period::AbstractString = "",
                      weighting::AbstractString = "",
                      extra::AbstractVector = Pair{String,String}[],
                      integrator_override = nothing)
    # integrator_override exists ONLY for post-hoc retrofits of runs whose depot state is no longer
    # live (see retrofit_provenance.jl). A live run must let this auto-detect — that is the whole point.
    integ, integ_file = integrator_override === nothing ? dais_integrator() :
                        (integrator_override, "N/A (post-hoc retrofit; depot state not live)")
    rec = Pair{String,String}[
        "run_timestamp_local"   => Dates.format(now(), "yyyy-mm-ddTHH:MM:SS"),
        "host"                  => gethostname(),
        "driver"                => driver,
        "code_git_commit"       => gitrev(repo),
        "code_repo"             => repo,
        # --- model identity -------------------------------------------------
        "model_lineage"         => model_lineage,
        "calibrator"            => calibrator,
        "posterior_subsample"   => isempty(posterior) ? "n/a" : _fileid(posterior),
        "dais_integrator"       => integ,
        "dais_component_file"   => integ_file,
        # --- climate driver -------------------------------------------------
        # Model is FaIR 2.2.4; "1.4.5" is the fair-calibrate CALIBRATION version, never the model.
        "climate_driver"        => "FaIR 2.2.4 (calib1.4.5), 841-config constrained posterior",
        # --- units / conventions -------------------------------------------
        "units"                 => units,
        "reference_period"      => reference_period,
        "weighting"             => weighting,
        # --- environment ----------------------------------------------------
        "julia_version"         => string(VERSION),
        "Mimi_version"          => string(pkgversion(Mimi)),
        "MimiBRICK_version"     => string(pkgversion(MimiBRICK)),
    ]
    for (i, f) in enumerate(forcing_files)
        push!(rec, "forcing_file_$i" => _fileid(f))
    end
    append!(rec, extra)
    return rec
end

"Write the provenance record as a 2-column key,value CSV sidecar (diffable between runs)."
function write_provenance(path::AbstractString, rec::AbstractVector)
    CSV.write(path, DataFrame(key=first.(rec), value=last.(rec)))
    println("wrote provenance sidecar: $(basename(path))  ($(length(rec)) fields)")
    return path
end

"""
    stamp!(df, rec; keys=STAMP_KEYS)

Add the load-bearing provenance fields as constant columns INSIDE a results DataFrame, so numbers never
travel naked when a CSV is copied into a notebook, table, or figure script. The full record stays in the
sidecar; this is the subset you must see to know whether two files are comparable.
"""
const STAMP_KEYS = ["model_lineage", "dais_integrator", "forcing_basis", "pulse_spec",
                    "units", "reference_period", "weighting", "code_git_commit"]

function stamp!(df::DataFrame, rec::AbstractVector; keys::Vector{String}=STAMP_KEYS)
    d = Dict(rec)
    for k in keys
        haskey(d, k) && (df[!, "prov_"*k] = fill(d[k], nrow(df)))
    end
    return df
end
