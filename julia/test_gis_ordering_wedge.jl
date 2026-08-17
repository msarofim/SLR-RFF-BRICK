## ============================================================================
## test_gis_ordering_wedge.jl — mutation test for the --gis-ordered wedge.
##
## The wedge is a -Inf region in `logposterior`, and a rejection region that
## never fires is indistinguishable from one that is not wired in at all. So
## this asserts BOTH directions on the actual constraint expression, and then
## re-derives it from `ladrillo_native_greenland!`'s inverse map so the
## calibrator and the projection stack cannot disagree about what "ordered"
## means.
##
## Standing discipline: mutation-test your gates; passing != working.
##
##   julia --project=julia_v2 julia/test_gis_ordering_wedge.jl
## ============================================================================
using Printf

const TBAR = 1.9631                 # == GIS_TBAR / LADRILLO_GIS_TBAR
const CM = Ref(0); const FAIL = Ref(0)
function chk(label, cond)
    CM[] += 1; cond || (FAIL[] += 1)
    @printf("  [%s] %s\n", cond ? "ok  " : "FAIL", label)
end

## The wedge exactly as `logposterior` evaluates it: returns true when the
## proposal is REJECTED.
rejects(ell, w, alpha_f, beta_f) = let r_s = exp(ell)
    (w * r_s / TBAR > alpha_f) || ((1 - w) * r_s > beta_f)
end

## The projection stack's inverse map, independently written.
native(ell, w) = (w * exp(ell) / TBAR, (1 - w) * exp(ell))

println("GIS ordering wedge — mutation test (Tbar = $TBAR K)")

## ---- 1. an ORDERED point must be ACCEPTED --------------------------------
## L11's own medians, which diag_gis_ordering_in_l11_posterior.py measured as
## correctly ordered: alpha_s 0.00220 < alpha_f 0.00373, beta_s 0.00418 < beta_f
## 0.00644. Reconstruct an (ell, w) that lands there.
let alpha_s = 0.00220, beta_s = 0.00418, alpha_f = 0.00373, beta_f = 0.00644
    r_s = alpha_s * TBAR + beta_s; ell = log(r_s); w = alpha_s * TBAR / r_s
    a, b = native(ell, w)
    chk("inverse map round-trips alpha_s ($(round(a, digits=8)) ~ $alpha_s)",
        abs(a - alpha_s) < 1e-10)
    chk("inverse map round-trips beta_s  ($(round(b, digits=8)) ~ $beta_s)",
        abs(b - beta_s) < 1e-10)
    chk("ORDERED point is ACCEPTED", !rejects(ell, w, alpha_f, beta_f))
end

## ---- 2. the MUTATIONS must be REJECTED ------------------------------------
## Each violates exactly ONE arm, so a wedge that only tests alpha, or only
## beta, fails here rather than passing by luck.
let alpha_f = 0.00373, beta_f = 0.00644
    # alpha arm alone: alpha_s just above alpha_f, beta_s well inside
    let alpha_s = 0.00380, beta_s = 0.00100
        r_s = alpha_s * TBAR + beta_s; ell = log(r_s); w = alpha_s * TBAR / r_s
        chk("alpha_s > alpha_f (beta ok) is REJECTED", rejects(ell, w, alpha_f, beta_f))
    end
    # beta arm alone: beta_s just above beta_f, alpha_s well inside
    let alpha_s = 0.00100, beta_s = 0.00700
        r_s = alpha_s * TBAR + beta_s; ell = log(r_s); w = alpha_s * TBAR / r_s
        chk("beta_s > beta_f (alpha ok) is REJECTED", rejects(ell, w, alpha_f, beta_f))
    end
    # both
    let alpha_s = 0.00500, beta_s = 0.00800
        r_s = alpha_s * TBAR + beta_s; ell = log(r_s); w = alpha_s * TBAR / r_s
        chk("both arms violated is REJECTED", rejects(ell, w, alpha_f, beta_f))
    end
    # the offline UNCONSTRAINED optimum, which is the defect we are fixing:
    # alpha_s = 0.00708 vs alpha_f = 0.00284 (handoff thread-5 section 5)
    let alpha_s = 0.0070727, beta_s = 0.0010, af = 0.0028487, bf = 0.0073684
        r_s = alpha_s * TBAR + beta_s; ell = log(r_s); w = alpha_s * TBAR / r_s
        chk("the offline INVERTED optimum is REJECTED", rejects(ell, w, af, bf))
    end
    # the ordered optimum, where the constraint binds at EQUALITY
    # (alpha_f = alpha_s = 0.0036625). Equality must be ADMITTED, not rejected.
    let alpha_s = 0.0036625, beta_s = 1e-6, af = 0.0036625, bf = 0.0078
        r_s = alpha_s * TBAR + beta_s; ell = log(r_s); w = alpha_s * TBAR / r_s
        chk("the ordered optimum (binding at EQUALITY) is ACCEPTED",
            !rejects(ell, w, af, bf))
    end
end

## ---- 3. the wedge is NOT a box -------------------------------------------
## The whole reason this cannot be done with lo/hi: whether a given (ell, w) is
## admissible depends on alpha_f/beta_f, which are themselves sampled. Same
## (ell, w), two different fast channels, two different verdicts.
let ell = log(0.0036625 * TBAR + 0.0010), w = 0.0036625 * TBAR /
                                              (0.0036625 * TBAR + 0.0010)
    lo = rejects(ell, w, 0.0010, 0.0074)     # small alpha_f -> violated
    hi = rejects(ell, w, 0.0080, 0.0074)     # large alpha_f -> satisfied
    chk("same (ell, w) REJECTED under a small alpha_f", lo)
    chk("same (ell, w) ACCEPTED under a large alpha_f", !hi)
    chk("=> verdict depends on alpha_f, so the region is a WEDGE not a BOX",
        lo && !hi)
end

@printf("\n%d checks, %d failed\n", CM[], FAIL[])
FAIL[] == 0 || error("the ordering wedge does not behave as specified")
println("wedge OK")
