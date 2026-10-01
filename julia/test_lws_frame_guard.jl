## ============================================================================
## test_lws_frame_guard.jl — the v1.0 land-water FRAME STEP and the guard that makes a model update fix it
##
## Under LWS_MODE = :observed, Ladrillo v1.0 steps the land-water component from 0 to obs[first_year]
## (the series' 1995-2005 frame, +1.565 cm) in 1900, and DAIS's sea-level feedback sees the step
## (<= 0.012 cm of Antarctic contribution; CHANGELOG 2026-10-01f). v1.0 ships with it for reproducibility;
## LWS_OBS_ANCHOR = :zero_at_first_year is the fix, and lws_frame_guard() refuses a model update without it.
##
##   S  SHIPPED   — the default is still :v1_step, and the model's component carries the step (so the L27
##                  paper arms are unchanged by this code).
##   F  FIX       — :zero_at_first_year: the component is 0 at first_year (no step), and from first_year on
##                  it differs from the shipped one by EXACTLY the constant obs[first_year] (same increments).
##   G  GUARD     — passes for the shipped default, for L27 and for every closed experiment up to
##                  LWS_V1_NEWEST_TAG; errors for a different default and for any newer tag; passes for
##                  a newer tag once the fix is on.
##   MUTATION     — the F step check must FAIL on the shipped anchor, and the G refusals must come from the
##                  guard (a guard that never errors would pass every "passes" line above).
##
## Run:  julia --project=julia_v2 julia/test_lws_frame_guard.jl
## ============================================================================
include(joinpath(@__DIR__, "ladrillo_projection.jl"))   # the kernel (brick_mengel.jl inside it)
using Printf

const FAILS = String[]
check(name, ok, detail="") = (@printf("  %-66s %s  %s\n", name, ok ? "PASS" : "FAIL", detail); ok || push!(FAILS, name))
refuses(f) = try f(); false catch e; e isa ErrorException && occursin("lws_frame_guard", e.msg) end

## One L27 draw through the projection kernel, ssp245 to 2100; the land-water series does not depend on
## the draw, but DAIS's input does, so the run is the real wiring rather than the component alone.
const VARIANT = ladrillo_posterior_variant()
const ROW = ladrillo_posterior(nthin=1)[1, :]
function lws_series(anchor)
    bf = ladrillo_setup(gis_variant=VARIANT, ssp="ssp245", y0=1850, y1=2100, lws=:observed)
    set_lws!(bf.m, :observed; lws_anchor=anchor)
    ladrillo_run_draw!(bf, ROW)
    yrs = Int.(Mimi.dim_keys(bf.m, :time))
    return yrs, 100 .* Float64.(bf.m[:landwater_storage, :lws_sea_level])          # cm
end

println("[S] shipped behaviour")
check("default anchor is :v1_step", LWS_OBS_ANCHOR === :v1_step)
yrs, s_v1 = lws_series(:v1_step)
fy, lws0_m, _ = lws_observed_increments(yrs; anchor=:v1_step)
i0 = findfirst(==(fy), yrs)
step_v1 = s_v1[i0] - s_v1[i0-1]
check("shipped component steps by obs[first_year] at $fy", abs(step_v1 - 100lws0_m) < 1e-12,
      @sprintf("(step %.4f cm)", step_v1))
check("the step is the documented +1.565 cm", abs(step_v1 - 1.565) < 5e-4, @sprintf("(%.4f)", step_v1))

println("[F] the fix")
_, s_fx = lws_series(:zero_at_first_year)
step_fx = s_fx[i0] - s_fx[i0-1]
check("fixed component is 0 at $fy (no step)", abs(step_fx) < 1e-12, @sprintf("(step %.2e cm)", step_fx))
d = s_v1[i0:end] .- s_fx[i0:end]
check("from $fy on, shipped - fixed == obs[first_year] exactly", maximum(abs.(d .- 100lws0_m)) < 1e-9,
      @sprintf("(max dev %.1e cm)", maximum(abs.(d .- 100lws0_m))))
check("before $fy both are 0", all(==(0.0), s_v1[1:i0-1]) && all(==(0.0), s_fx[1:i0-1]))
check("MUTATION: the no-step check FAILS on the shipped anchor", !(abs(step_v1) < 1e-12))

println("[G] the guard")
P(t) = joinpath("data", "MimiBRICK", "parameters_subsample_brick_mengel_$(t).csv")
check("shipped default (L27) passes", !refuses(() -> lws_frame_guard(P("L27"); default=true)))
check("closed experiments L24, L32, L$(LWS_V1_NEWEST_TAG) load (non-default)",
      !any(refuses(() -> lws_frame_guard(P(t))) for t in ("L24", "L32", "L$(LWS_V1_NEWEST_TAG)")))
check("bare tags L27, L27b pass", !refuses(() -> lws_frame_guard("L27")) && !refuses(() -> lws_frame_guard("L27b")))
check("REFUSES a different default posterior (L32 as default)", refuses(() -> lws_frame_guard(P("L32"); default=true)))
nxt = "L$(LWS_V1_NEWEST_TAG + 1)"
check("REFUSES a newer posterior file ($nxt)", refuses(() -> lws_frame_guard(P(nxt))))
check("REFUSES a newer bare run tag ($(nxt)b)", refuses(() -> lws_frame_guard("$(nxt)b")))
check("with the fix on, $nxt passes (default too)",
      !refuses(() -> lws_frame_guard(P(nxt); default=true, anchor=:zero_at_first_year)))
check("an unknown anchor is an error", try lws_frame_guard("L27"; anchor=:bogus); false catch; true end)

println()
isempty(FAILS) || error("test_lws_frame_guard: $(length(FAILS)) FAIL(s): $(join(FAILS, "; "))")
println("ALL LWS FRAME-GUARD TESTS PASS")
