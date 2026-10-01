"""10-01c edit set L (Marcus 10-01: "'BRICK' for the family, 'BRICK 2.0' for the specific model").

Every bare "BRICK" that means the comparison arm (MimiBRICK v2.0.0 on its published posterior) becomes
"BRICK 2.0" by a tracked INSERTION of " 2.0", so the redline shows only the added text. "BRICK" stays
where the sentence is true of the family (title, abstract lede, "derivative of", design philosophy,
Wigley-Raper glaciers, the DAIS structure, the modular approach). Where a claim was verified only
against BRICK 2.0's code, it is named as BRICK 2.0 even if it may also hold for earlier versions:
the 1.196 amplification (the get_model default) and the OHC-proportional thermal expansion (read from
MimiBRICK v2.0.0's component; not checked against v0.2). The family is defined once, at "As a derivative of BRICK".

Also: the MimiBRICK citation in Code availability is pinned to the v2.0.0 tag and its commit
(GitHub, raddleverse/MimiBRICK.jl: tag v2.0.0 -> 11b2dff, checked 10-01c), in place of a Zenodo DOI.
"""
import os, sys
from xml.sax.saxutils import escape
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from trackedit import Doc

d = Doc(sys.argv[1] + "/word/document.xml")


def insert_in(context, prefix, new, why):
    """Tracked insertion of `new` right after `prefix`, where `context` (which starts with `prefix`)
    must occur exactly once in one untracked run. Lets a short insertion point be pinned by a longer,
    unique context without deleting and re-inserting the context."""
    assert context.startswith(prefix)
    m = d._locate(escape(context))
    rpr, txt = m.group(1), m.group(2)
    j = txt.index(escape(context)) + len(escape(prefix))
    out = d._run(rpr, txt[:j]) + d._ins(rpr, escape(new)) + d._run(rpr, txt[j:])
    d.x = d.x[:m.start()] + out + d.x[m.end():]
    d.log.append((context + " [+]", new, why))


ARM = " 2.0"
# (context that occurs once, prefix after which " 2.0" goes, why)
SITES = [
    ("projections relative to BRICK.", "projections relative to BRICK", "abstract: projections compared against the arm"),
    ("leaving BRICK as the only SLEIP model", "leaving BRICK", "the SLEIP-assessed model, named BRICK 2.0 earlier in the paragraph"),
    ("extended some of BRICK", "extended some of BRICK", "IMBIE 1992-2017 likelihood is BRICK 2.0's (IMBIE 2018 postdates v0.2)"),
    ("In terms of future projections, relative to BRICK", "In terms of future projections, relative to BRICK", "quantitative comparison with the arm"),
    ("less sensitive to scenarios than BRICK", "less sensitive to scenarios than BRICK", "quantitative comparison with the arm"),
    ("differences between BRICK and Ladrillo", "differences between BRICK", "the arm's likelihood"),
    ("since BRICK", "since BRICK", "the arm's likelihood"),
    ("The BRICK DAIS hard-codes", "The BRICK", "1.196 verified as BRICK 2.0's get_model default"),
    ("fixed at BRICK", "fixed at BRICK", "same paragraph opens with BRICK 2.0's module"),
    ("either Ladrillo or BRICK", "either Ladrillo or BRICK", "LWS handling is the arm's"),
    ("added to BRICK", "added to BRICK", "LWS added to the arm's total"),
    ("replace BRICK", "replace BRICK", "the components swapped are MimiBRICK v2.0.0's"),
    ("compensating errors in BRICK", "compensating errors in BRICK", "hindcast errors of the arm"),
    ("Over 1900–1919 BRICK", "Over 1900–1919 BRICK", "hindcast errors of the arm"),
    ("0.13 cm for BRICK", "0.13 cm for BRICK", "RMSE of the arm"),
    ("In both Ladrillo and BRICK", "In both Ladrillo and BRICK", "OHC-proportional TE verified in BRICK 2.0's code only"),
    ("Ladrillo, BRICK, and FACTS", "Ladrillo, BRICK", "projection arm"),
]
for ctx, pre, why in SITES:
    insert_in(ctx, pre, ARM, why)

# "native BRICK subtracts LWS" -> "BRICK 2.0 subtracts LWS" (its published calibration)
insert_in("native BRICK subtracts", "native BRICK", ARM, "the arm's published calibration")
# then delete only the word "native " (the bare word also occurs in "the native form", so pin by context)
m = d._locate(escape("whereas native BRICK"))
rpr, txt = m.group(1), m.group(2)
i = txt.index("whereas native BRICK") + len("whereas ")
out = d._run(rpr, txt[:i]) + d._del(rpr, "native ") + d._run(rpr, txt[i + len("native "):])
d.x = d.x[:m.start()] + out + d.x[m.end():]
d.log.append(("whereas native BRICK", "whereas BRICK", "'native' redundant once named BRICK 2.0"))

# Define the family once, where the paper first calls Ladrillo a derivative of it.
insert_in("As a derivative of BRICK,", "As a derivative of BRICK",
          " (Wong et al., 2017b, 2022; below, ‘BRICK’ is the model family and ‘BRICK 2.0’ its MimiBRICK"
          " v2.0.0 release, the version Ladrillo is compared against)",
          "define the family once (Marcus 10-01 naming ruling)")

# Code availability: pin the GitHub citation (no Zenodo record of v2.0.0 code exists). That paragraph is
# itself 10-01b's pending insertion (the back matter was moved after the Appendix), so split that
# insertion around the point and put this round's insertion between the halves, rather than nesting.
def insert_in_earlier_ins(context, prefix, new, why):
    import re
    from trackedit import AUTHOR, DATE
    c = escape(context)
    pat = re.compile(r'<w:ins (w:id="\d+") (w:author="[^"]*" w:date="[^"]*")>'
                     r'<w:r>((?:<w:rPr>(?:(?!</w:rPr>).)*</w:rPr>)?)<w:t(?: xml:space="preserve")?>([^<]*)</w:t></w:r></w:ins>', re.S)
    hits = [m for m in pat.finditer(d.x) if c in m.group(4)]
    assert len(hits) == 1, ("earlier insertion not unique", context, len(hits))
    m = hits[0]; attrs, rpr, t = m.group(2), m.group(3), m.group(4)
    assert DATE not in attrs, "that insertion is this round's own"
    j = t.index(c) + len(escape(prefix))
    half = lambda s: f'<w:ins w:id="{d._id()}" {attrs}><w:r>{rpr}{d._t(s)}</w:r></w:ins>' if s else ""
    d.x = d.x[:m.start()] + half(t[:j]) + d._ins(rpr, escape(new)) + half(t[j:]) + d.x[m.end():]
    d.log.append((context + " [+, in earlier ins]", new, why))


insert_in_earlier_ins("(Wong et al., 2022). The FaIR 2.2.4 climate", "(", "tag v2.0.0, commit 11b2dff; ",
                      "pin MimiBRICK to the exact release cited (Marcus 10-01: GitHub through review)")

d.save()
for o, n, w in d.log:
    print(f"- {o[:60]!r} -> {n[:70]!r}  [{w}]")
print(f"{len(d.log)} edits")
