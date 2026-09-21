"""Round 7 (2026-09-21): one sentence in the Convergence paragraph — the between-refit precision measured
overnight by L27r/L27b (CHANGELOG 09-21a). Base = the r6 review docx as it is on disk. A PURE insertion: a new
<w:ins> run appended after the paragraph's last inserted run, so nothing is deleted and reject-all is the base.
Every number is read from outputs/diag_refit_precision_L26_L27_L27r_L27b.csv."""
import re
import pandas as pd
from redline import *
import redline

redline.DATE = "2026-09-21T00:00:00Z"
x = load()
start_ids_above(x)
D = pd.read_csv(HERE.parent.parent / "outputs/diag_refit_precision_L26_L27_L27r_L27b.csv")
def v(tag, blk, q):
    return float(D[(D.tag == tag) & (D.block == blk) & (D.quantity == q)].value.iloc[0])
cells = [q for q in D[(D.block == "ssp_fixed")].quantity.unique() if q.endswith("|med") and "|ais|" in q]
d_ais = max(abs(v("L27r", "ssp_fixed", q) - v("L27", "ssp_fixed", q)) for q in cells)
d_rmse = max(abs(v("L27r", "hindcast_rmse", c) - v("L27", "hindcast_rmse", c)) for c in ("glaciers", "ais", "gis", "te"))
g = D[(D.block == "ais_geometry") & (D.tag.isin(["L27", "L27r"]))].pivot_table(index="quantity", columns="tag", values="value")
d_geo = float((g["L27r"] - g["L27"]).abs().max())
assert d_ais < 1.5 and d_rmse < 0.005 and 0.7 < d_geo < 1.0, (d_ais, d_rmse, d_geo)
sentence = (" Two independent refits of the same objective (different seeds, starting points and proposal covariance) "
            "reproduce every Antarctic projection median to within %.1f cm at 2300 and the hindcast to %.3f cm; the weakly "
            "identified geometry directions differ by up to %.1f posterior standard deviations between refits without "
            "moving the projections." % (d_ais, round(d_rmse + 0.0005, 3), d_geo))
ps, pe = find_para(x, "the 1,600 thinned draws used for the diagnostic")
p = x[ps:pe]
j = p.rfind("</w:ins>") + len("</w:ins>")
assert j > len("</w:ins>"), "no inserted run to append after"
p = p[:j] + mk_ins(esc(sentence)) + p[j:]
x = x[:ps] + p + x[pe:]
save(x); print("r7 applied:", sentence.strip())
