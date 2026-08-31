#!/usr/bin/env python3
"""validate_glacier_floor_regrowth.py -- does the floor + bounded regrowth do what it says?

  python3 python/validate_glacier_floor_regrowth.py

THE PORT GATE CANNOT ANSWER THIS. validate_glaciers_nu3.jl checks the Julia module against
`integrate_N` at 1e-9, and both were changed together on 2026-08-31 -- so it would pass just as
happily if the change were a no-op, or if the floor leaked into the melt branch. It proves the
two implementations AGREE, not that they agree on the right thing. These four properties are
what the change actually claims, each stated so that a wrong implementation FAILS it.

  [LIVE]     on a cooling path the new law must DIFFER from the old melt-only ratchet.
             Guards against a change that was edited but never reached.
  [MELT-ONLY-UNCHANGED]  on a monotonically warming path the two must be BIT-IDENTICAL.
             This is the regression guarantee for vvM and vvH, which never cool: their
             numbers must not move by so much as a ulp, and the refit must not either.
  [REGROWS]  on a cooling path the stock must actually DECREASE somewhere.
  [FLOOR]    the stock must never go below the pre-industrial state, on any path, including
             one driven far below T_off where the UNFLOORED equilibrium is deeply negative.
             This is the property the floor exists for.
"""
import os

import numpy as np

## ⚠ DO NOT `import d0_glacier_shootout`. Everything below its "run all cells" marker is
## top-level, so a plain import RUNS THE WHOLE SHOOTOUT and overwrites
## outputs/d0_glacier_shootout.csv + figures/d0_glacier_shootout.png as a side effect of
## asking for one function. The first version of this file did exactly that and silently
## rewrote both. The repo already has an idiom for taking definitions without the run --
## d1e/d1f/emit_extc_port_reference all exec the source ABOVE a run marker -- so use it.
## d0's marker text differs from the others', hence the literal below rather than the
## shared one; the uniqueness assert is what stops a renamed marker exec'ing the analysis.
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_D0_SRC = os.path.join(REPO, "python/d0_glacier_shootout.py")
_MARKER = "# ------------------------------------------------------------------ run all cells"
_src = open(_D0_SRC).read()
assert _src.count(_MARKER) == 1, "d0 run marker not unique - refusing to exec"


class _D0:
    pass


d0 = _D0()
exec(_src.split(_MARKER)[0], d0.__dict__)

## The reference block. Values are the R19 anchor from the committed extC constants; the
## properties tested are structural and do not depend on the exact theta, but pinning one
## makes the numbers in the log reproducible.
THETA = dict(a=0.30, b=0.60, T_off=-0.50, kappa=0.020, nu=0.70)
NY = 300
TOL_IDENTICAL = 0.0          # [MELT-ONLY-UNCHANGED] is an IDENTITY, not an approximation


def integrate_old(T, a, b, T_off, kappa, nu):
    """The SHIPPED-BEFORE-2026-08-31 law: melt-only ratchet, unfloored equilibrium.
    Kept here, in the validator, so the comparison has something to be a comparison WITH --
    deleting the old law would leave [LIVE] and [MELT-ONLY-UNCHANGED] with no reference."""
    S, out = 0.0, np.empty(len(T) + 1)
    out[0] = 0.0
    for k in range(len(T)):
        seq = a * (1 - np.exp(-b * (T[k] - T_off)))
        frac_left = max(1.0 - S / a, 1e-12)
        T_eq = T_off - np.log(frac_left) / b
        exc = max(T[k] - T_eq, 0.0)
        S += min(kappa * exc ** nu, 1.0) * (seq - S)
        out[k + 1] = S
    return out


def main():
    fails = []
    warm = np.linspace(0.0, 4.0, NY)                       # monotone warming, never cools
    peak = np.concatenate([np.linspace(0.0, 3.5, NY // 2),  # peak and decline
                           np.linspace(3.5, 0.2, NY - NY // 2)])
    ## deliberately driven far below T_off, where the UNFLOORED S_eq is strongly negative
    deep = np.concatenate([np.linspace(0.0, 3.0, NY // 2),
                           np.linspace(3.0, -3.0, NY - NY // 2)])

    def check(name, ok, detail):
        print("  [%-22s] %-4s  %s" % (name, "PASS" if ok else "FAIL", detail))
        if not ok:
            fails.append(name)

    print("glacier floor + bounded regrowth, theta = %s" % THETA)

    # [MELT-ONLY-UNCHANGED]
    nw, ow = d0.integrate_N(warm, **THETA), integrate_old(warm, **THETA)
    d = float(np.max(np.abs(nw - ow)))
    check("MELT-ONLY-UNCHANGED", d <= TOL_IDENTICAL,
          "monotone warming: max|new-old| = %.3e (bound %.0e, an identity)" % (d, TOL_IDENTICAL))

    # [LIVE]
    npk, opk = d0.integrate_N(peak, **THETA), integrate_old(peak, **THETA)
    dp = float(np.max(np.abs(npk - opk)))
    check("LIVE", dp > 1e-6,
          "peak-and-decline: max|new-old| = %.4f m (must be > 1e-6, or nothing changed)" % dp)

    # [REGROWS]
    worst = float(np.min(np.diff(npk)))
    check("REGROWS", worst < 0.0,
          "peak-and-decline: most negative annual step = %.3e m (must be < 0)" % worst)
    ## the old law must NOT regrow -- confirms the property is the new law's, not the driver's
    check("OLD-DID-NOT-REGROW", float(np.min(np.diff(opk))) >= 0.0,
          "same path under the old law: most negative step = %.3e m"
          % float(np.min(np.diff(opk))))

    # [FLOOR]
    nd = d0.integrate_N(deep, **THETA)
    mn = float(np.min(nd))
    ## what the UNFLOORED equilibrium reaches on the same path, to show the floor is not
    ## idle -- a floor that never binds would pass [FLOOR] while doing nothing.
    seq_min = float(np.min(THETA["a"] * (1 - np.exp(-THETA["b"] * (deep - THETA["T_off"])))))
    check("FLOOR", mn >= 0.0,
          "T driven to %.1f K: min stock = %.3e m (must be >= 0); unfloored S_eq reaches "
          "%.3f m, so the floor BINDS" % (deep.min(), mn, seq_min))

    print()
    if fails:
        raise SystemExit("FAILED: %s" % ", ".join(fails))
    print("ALL PROPERTIES HOLD")


if __name__ == "__main__":
    main()
