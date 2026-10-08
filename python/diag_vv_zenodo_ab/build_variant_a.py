"""Variant (a): the Zenodo v1.1.1 ML series WHOLE, its own 1750.5-2023.5 history included, truncated at 2300.5,
in the exact row/column/unit layout of variant (b). Gates: (a)'s future == (b)'s future / per-species scale."""
import sys, numpy as np, pandas as pd
zen_file, b_file, out_file = sys.argv[1:4]
TO_FAIR = {"CO2 FFI": 1e-3, "CO2 AFOLU": 1e-3, "N2O": 1e-3}       # Mt CO2 -> Gt CO2, kt N2O -> Mt N2O
END = 2300.5
b = pd.read_csv(b_file)
cols = [c for c in b.columns if c.replace(".", "").isdigit()]
assert float(cols[0]) == 1750.5 and float(cols[-1]) == END, cols[:2] + cols[-2:]
z = pd.read_csv(zen_file); z = z[z.scenario == "ML"].set_index("variable")
a = b.copy()
for i, sp in enumerate(b["variable"]):
    a.loc[i, cols] = z.loc[sp, cols].to_numpy(float) * TO_FAIR.get(sp, 1.0)
a.to_csv(out_file, index=False)
# gates
A = a.set_index("variable")[cols].astype(float); B = b.set_index("variable")[cols].astype(float)
fut = [c for c in cols if float(c) > 2023.5]
hist = [c for c in cols if float(c) <= 2023.5]
s = B["2023.5"] / A["2023.5"].where(A["2023.5"].abs() > 1e-12)
bad = []
for sp in A.index:
    if abs(A.loc[sp, "2023.5"]) > 1e-12:
        r = B.loc[sp, fut].to_numpy() - A.loc[sp, fut].to_numpy() * s[sp]
        if np.max(np.abs(r)) > 1e-9 * max(1e-30, np.max(np.abs(B.loc[sp, fut]))): bad.append(sp)
print("FUTURE GATE (b future == a future x scale):", "PASS" if not bad else f"FAIL {bad}")
print("a NaN:", int(A.isna().sum().sum()), " species:", len(A), " years:", cols[0], "..", cols[-1])
print("\nper-species join scale s = hist(2023.5)/zenodo(2023.5), |s-1| > 1e-3:")
d = pd.DataFrame({"scale": s, "hist_2023": B["2023.5"], "zen_2023": A["2023.5"]})
d["dev"] = (d.scale - 1).abs()
print(d[(d.dev > 1e-3) | d.scale.isna()].sort_values("dev", ascending=False).to_string(float_format=lambda x: f"{x:.4g}"))
print("\nhistory-block max |a-b|/|b| over 1750.5-2023.5, top 8:")
den = B[hist].abs().where(B[hist].abs() > 0)
print(((A[hist] - B[hist]).abs() / den).max(axis=1).sort_values(ascending=False).head(8).to_string(float_format=lambda x: f"{x:.3g}"))
