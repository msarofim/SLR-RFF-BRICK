"""Paired per-config comparison of the ML arms (same 841 configs, same order, deterministic)."""
import sys, numpy as np
D = sys.argv[1]
A = {k: np.load(f"{D}/ml_{k}.npz") for k in ("live", "a", "b")}
yrs = A["a"]["years"]
assert all(np.array_equal(A[k]["configs"], A["a"]["configs"]) for k in A)
Y = [2030, 2050, 2100, 2150, 2200, 2300]
iy = [int(np.where(yrs == y)[0][0]) for y in Y]
q = lambda x: np.percentile(x, [5, 50, 95])
PAIRS = [("a", "b"), ("b", "live"), ("a", "live")]
def table(var, unit, fmt="{:+.3f}"):
    print(f"\n### {var} [{unit}]   medians, then PAIRED per-config difference: median [5%, 95%]")
    print(f"{'year':>6} " + "".join(f"{'med '+k:>10}" for k in ("live", "a", "b")) +
          "".join(f"{x+'-'+y:>30}" for x, y in PAIRS) + f"{'5-95 width (b)':>16}")
    for y, i in zip(Y, iy):
        row = f"{y:>6} " + "".join(f"{np.median(A[k][var][i]):10.3f}" for k in ("live", "a", "b"))
        for x, z in PAIRS:
            d = q(A[x][var][i] - A[z][var][i])
            row += f"{fmt.format(d[1]):>12} [{fmt.format(d[0])}, {fmt.format(d[2])}]".rjust(30)
        p = q(A["b"][var][i]); row += f"{p[2]-p[0]:16.3f}"
        print(row)
table("erf_total", "W/m2 rel 1750, FaIR native, not re-referenced")
for g in ("halogens", "ozone", "aerosol", "ch4", "n2o", "co2"):
    table(f"erf_{g}", "W/m2 rel 1750", "{:+.4f}")
table("gmst", "K rel 1850-1900")
table("gmst_raw", "K rel 1750 model start")
table("ohc", "1e22 J rel 1850-1900", "{:+.2f}")
# hindcast window and the 1850-1900 reference
w = (yrs >= 2015) & (yrs <= 2024); pi = (yrs >= 1850) & (yrs <= 1900)
print("\n### history: ensemble-mean GMST 2015-2024 (rel 1850-1900) and the 1850-1900 reference (rel 1750)")
for k in ("live", "a", "b"):
    print(f"  {k:5s} GMST 2015-2024 = {A[k]['gmst'][w].mean():.4f} K   1850-1900 ref (raw) = {A[k]['gmst_raw'][pi].mean():.5f} K")
d = (A["a"]["gmst"] - A["b"]["gmst"])[(yrs >= 1850) & (yrs <= 2023)]
print(f"  a-b GMST over 1850-2023: max |median diff| = {np.abs(np.median(d, axis=1)).max():.4f} K "
      f"at {int(yrs[(yrs >= 1850) & (yrs <= 2023)][np.argmax(np.abs(np.median(d, axis=1)))])}")
# where does a-b total ERF peak?
dm = np.median(A["a"]["erf_total"] - A["b"]["erf_total"], axis=1)
k = np.argmax(np.abs(dm)); print(f"  a-b total ERF: largest |median paired diff| {dm[k]:+.4f} W/m2 at {int(yrs[k])}")
dg = np.median(A["a"]["gmst"] - A["b"]["gmst"], axis=1)
k = np.argmax(np.abs(dg)); print(f"  a-b GMST: largest |median paired diff| {dg[k]:+.4f} K at {int(yrs[k])}")
for k in A: print("provenance", k, ":", str(A[k]["provenance"]))
