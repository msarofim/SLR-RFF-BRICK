"""
validate_palette.py -- colourblind-safety check for a figure palette.

Python replacement for the `dataviz` skill's scripts/validate_palette.js, which cannot run here
(no node on this machine). Checks, per PAIR of colours:
  * normal-vision OKLab dE x100   -- hard floor 15 (below this, full-colour readers cannot tell them apart)
  * protan / deutan / tritan dE   -- target >= 8; 6-8 is legal ONLY with a secondary encoding
  * WCAG contrast on the surface  -- >= 3:1 for a mark

Dichromat simulation is Vienot, Brettel & Mollon (1999) in LMS. OKLab is Ottosson (2020).

  python python/validate_palette.py "#2166ac,#b2182b,#7f7f7f" [--surface=#ffffff]
Exit status is 1 if any pair FAILs, so it can gate a figure build.
"""
import sys, itertools, numpy as np

CVD_TARGET, CVD_FLOOR, NORMAL_FLOOR, CONTRAST_MIN = 8.0, 6.0, 15.0, 3.0

def hex2lin(h):
    h = h.strip().lstrip("#")
    c = np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)])
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)

def lin2oklab(l):
    M1 = np.array([[0.4122214708, 0.5363325363, 0.0514459929],
                   [0.2119034982, 0.6806995451, 0.1073969566],
                   [0.0883024619, 0.2817188376, 0.6299787005]])
    M2 = np.array([[0.2104542553, 0.7936177850, -0.0040720468],
                   [1.9779984951, -2.4285922050, 0.4505937099],
                   [0.0259040371, 0.7827717662, -0.8086757660]])
    return M2 @ np.cbrt(M1 @ l)

RGB2LMS = np.array([[17.8824, 43.5161, 4.11935],
                    [3.45565, 27.1554, 3.86714],
                    [0.0299566, 0.184309, 1.46709]])
LMS2RGB = np.linalg.inv(RGB2LMS)
ROW = {"protan": (0, np.array([0, 2.02344, -2.52581])),
       "deutan": (1, np.array([0.494207, 0, 1.24827])),
       "tritan": (2, np.array([-0.395913, 0.801109, 0]))}

def cvd(lin, kind):
    lms = RGB2LMS @ lin
    i, row = ROW[kind]
    out = lms.copy(); out[i] = row @ lms
    return np.clip(LMS2RGB @ out, 0, 1)

def dE(a, b):
    return float(np.linalg.norm((lin2oklab(a) - lin2oklab(b)) * 100))

def relL(lin):
    return float(0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2])

def main(argv):
    pal = [c for c in argv[1].split(",") if c.strip()]
    surface = next((a.split("=")[1] for a in argv[2:] if a.startswith("--surface=")), "#ffffff")
    lins = [hex2lin(h) for h in pal]
    sL = relL(hex2lin(surface))
    bad = 0
    print("pair separation (OKLab dE x100; normal floor %.0f, CVD target %.0f)\n" % (NORMAL_FLOOR, CVD_TARGET))
    print("%-22s %8s %8s %8s %8s  %s" % ("pair", "normal", "protan", "deutan", "tritan", "verdict"))
    for i, j in itertools.combinations(range(len(pal)), 2):
        n = dE(lins[i], lins[j])
        ds = {k: dE(cvd(lins[i], k), cvd(lins[j], k)) for k in ROW}
        m = min(ds.values())
        if n < NORMAL_FLOOR or m < CVD_FLOOR:
            v = "FAIL"; bad += 1
        elif m < CVD_TARGET:
            v = "FLOOR (needs secondary encoding)"
        else:
            v = "PASS"
        print("%-22s %8.1f %8.1f %8.1f %8.1f  %s"
              % (pal[i] + " / " + pal[j], n, ds["protan"], ds["deutan"], ds["tritan"], v))
    print("\ncontrast on %s (mark floor %.1f:1)" % (surface, CONTRAST_MIN))
    for h, l in zip(pal, lins):
        L = relL(l)
        c = (max(L, sL) + 0.05) / (min(L, sL) + 0.05)
        if c < CONTRAST_MIN:
            bad += 1
        print("  %-9s %5.2f:1  %s" % (h, c, "ok" if c >= CONTRAST_MIN else "WARN -- needs a visible label"))
    print("\n%d problem(s)" % bad)
    return 1 if bad else 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))
