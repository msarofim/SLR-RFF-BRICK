#!/usr/bin/env python3
"""
build_gmd_v2_L27.py -- produce GMD.Ladrillo.v2_L27.docx from the v1 draft.

⭐ WHY A SCRIPT AND NOT A ONE-OFF EDIT. Marcus edits the manuscript .docx directly and it has no
markdown source, so the only reproducible artifact is the EDIT LIST. Every change below is a
verifiable number with a named source (see deliverables/GMD_L24_to_L27_CORRECTIONS.md); the prose
and framing remain his.

⛔ THIS SCRIPT DOES NOT REGENERATE THE DOCUMENT. It unzips v1, applies exact string replacements to
word/document.xml, and rezips. It never rewrites XML with ElementTree, which renames namespace
prefixes and makes Word report "unreadable content" while a round-trip cannot see it.

⛔ IT REFUSES TO RUN IF THE INPUT CARRIES TRACKED CHANGES OR COMMENTS. A rebuild would destroy them
silently. Sync them into the source first.

⚠ EVERY REPLACEMENT IS ANCHORED AND COUNTED. A replacement that does not match is a hard error, not
a silent no-op -- a stale draft would otherwise produce a "new version" that changed nothing.

  python3 python/build_gmd_v2_L27.py [--in v1.docx] [--out v2.docx]
"""
import argparse, glob, os, re, shutil, subprocess, sys, tempfile, zipfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEL  = os.path.join(REPO, "deliverables")

# ---- the edit list: (label, exact_old, exact_new). Sources are in GMD_L24_to_L27_CORRECTIONS.md
EDITS = [
 ("parameter count + breakdown (ladrillo_prior_posterior_L27.csv; grouping validated on L24)",
  "58 parameters are sampled: 17 Antarctic, 9 Greenland, 19 glacier, 13 remaining (thermal expansion, two discrepancy bases of two coefficients each, and four AR(1) noise pairs).",
  "50 parameters are sampled: 14 Antarctic, 9 Greenland, 16 glacier, 11 remaining (thermal expansion, one discrepancy basis of two coefficients, and four AR(1) noise pairs)."),
 ("convergence counts + failure locus (log_l27_postprocess_driver.txt)",
  "39 of the 58 parameters pass it. The 19 that fail are concentrated in the Antarctic block (the geometry ridge and the ocean-temperature parameters; ",
  "42 of the 50 parameters pass it. The 8 that fail are all in the Antarctic block (the geometry ridge and the ocean-temperature parameters; "),
 ("ais_iceflow0 R-hat 1.26 -> 1.03",
  " R̂ = 1.26, ", " R̂ = 1.03, "),
 ("antarctic_alpha R-hat, the L24 verdict tag, and the deliverable-level numbers",
  " 1.28) and in Greenland's slow channel, directions that are weakly identified and compensate for each other. L24 is therefore accepted on the deliverable-level criterion: projected sea level converges (R̂ = 1.008 at 2100 and 1.011 at 2150 on SSP2-4.5, with an effective sample size of about 1050 on the 1,600 thinned draws used for the diagnostic).",
  " 1.05), directions that are weakly identified and compensate for each other; several fail on effective sample size rather than on R̂. Ladrillo 1.0 is therefore accepted on the deliverable-level criterion: projected sea level converges (R̂ = 1.001 at 2100 and 1.002 at 2150 on SSP2-4.5, with an effective sample size of about 1240 on the 1,600 thinned draws used for the diagnostic)."),
 ("the reparameterised precipitation parameter (--precip-reparam)",
  "<w:t>ais_precip0_LOG</w:t>", "<w:t>ais_precip_u</w:t>"),
 ("FIG 1 caption: the vintage, and the new IMBIE series on the two ice-sheet panels",
  "Ladrillo L24 (solid, with its 5\u201395% band) and BRICK 2.0 (dashed) are both run starting in 1850, plotted from 1900, and driven by the same ssp245harm forcing.",
  "Ladrillo 1.0 (solid, with its 5\u201395% band) and BRICK 2.0 (dashed) are both run starting in 1850, plotted from 1900, and driven by the same ssp245harm forcing. The two ice-sheet panels also show the IMBIE 2026 reconciled record with its \u00b11\u03c3 band, from 1979 for Antarctica and 1972 for Greenland; it is not a calibration target for either."),
 ("lambda moments (now PROPAGATED paleo draws) + the 2300 band width, joint arm both models",
  "(mean 0.0105, sd 0.0033 in Ladrillo; 0.0104, 0.0036 in BRICK 2.0), which is why the two Antarctic spreads are alike (5–95% widths of 329 and 405 cm at SSP5-8.5 in 2300).",
  "(mean 0.0104, sd 0.0036 in Ladrillo; 0.0104, 0.0036 in BRICK 2.0 — in Ladrillo these parameters are not estimated but propagated, one joint paleo draw per posterior draw, so the two models now draw them from the same ensemble), which is why the two Antarctic spreads are alike (5–95% widths of 314 and 405 cm at SSP5-8.5 in 2300)."),
]

ANCHOR = "Deliberately removed: IMBIE, and the total."

def _p(runs): return '<w:p><w:pPr><w:pStyle w:val="BodyText"/></w:pPr>' + runs + '</w:p>'
def _b(t):    return f'<w:r><w:rPr><w:b/><w:bCs/></w:rPr><w:t xml:space="preserve">{t}</w:t></w:r>'
def _t(t):    return f'<w:r><w:t xml:space="preserve">{t}</w:t></w:r>'

NEW_PARAS = [
 ("IMBIE 2026 as an out-of-sample check.",
  " Because IMBIE is not a likelihood term for either ice sheet, the 2026 reconciled record "
  "(Otosaka et al. 2026), which extends Antarctica to 1979 and Greenland to 1972, is an out-of-sample "
  "comparison for both. For Antarctica the shipped posterior reproduces the record’s dynamics anomaly "
  "within its published uncertainty in every window — its largest departure, +48 Gt yr⁻¹ over "
  "2018–23, is 0.4 of IMBIE’s own uncertainty for that window — while underpredicting the "
  "cumulative 1979–2023 level by 2.6σ. Those two are not independent: net mass balance is the sum "
  "of surface mass balance and dynamics by construction, and because the module’s surface mass balance "
  "cannot reproduce the record’s +141 Gt yr⁻¹ 2018–23 snowfall anomaly, a calibration that "
  "matched the net exactly would necessarily understate the dynamics anomaly by about 114 Gt yr⁻¹."),
 ("The Greenland record, which is new below 1992.",
  " The Greenland comparison is the cleaner of the two, since no vintage of the Greenland target has ever "
  "contained IMBIE. From 2003 onward the modelled rate is within 8 % of the record in every assessment "
  "window (0.92, 0.99 and 0.93 times observed over 2003–10, 2011–17 and 2018–23). Over "
  "1972–1991 the model loses 0.50 cm SLE against the record’s 0.13 (+3.7σ), and 83 % of the "
  "full-period 1972–2023 discrepancy of +0.44 cm accumulates in those two decades; about a quarter of "
  "the early gap is the calibration target itself running high against the record (+0.09 cm) and the "
  "remainder is the model departing from its own target. The pattern is the acceleration deficit already "
  "visible in the satellite era, measured over a longer baseline: the record’s Greenland loss rate rises "
  "by a factor of 10.5 between 1972–91 and 2011–17 while the model’s rises by 2.7. The "
  "1972–91 ratio itself is not a stable statistic — the observed rate in that window is 0.0064 "
  "± 0.0041 cm yr⁻¹ — so the level comparison, not the rate ratio, carries the result."),
 ("A caution on aggregate checks.",
  " The two ice-sheet departures have opposite sign and fall in different periods: Greenland +0.44 cm over "
  "1972–2023 and Antarctica −0.38 cm over 1979–2023, summing to +0.07 cm. Neither is visible "
  "in a comparison made on total sea level alone."),
 ("The Antarctic innovation variance.",
  " The record also constrains the error model. Its Antarctic surface-mass-balance anomaly varies from year "
  "to year with a standard deviation of first differences of 118 Gt yr⁻¹ over 1979–2019, a "
  "variability that is present in every decade since the 1980s and that global mean surface temperature "
  "explains 4 % of, so it is weather rather than a forced signal the module could reproduce. Expressed as a "
  "sea-level innovation this implies a lower bound of 0.033 cm yr⁻¹ on the Antarctic AR(1) "
  "innovation standard deviation; the shipped posterior fits 0.0216 cm (5–95 %: 0.0188–0.0249), a "
  "factor 1.5 below that bound and outside its own 95th percentile. Refitting with the innovation standard "
  "deviation floored at the implied value, and nothing else changed, leaves the shipped configuration "
  "marginally worse on both the full-record and altimetry-era Antarctic scorers (0.73 against 0.70 and 1.32 "
  "against 1.27 σ), so the correction is reported rather than adopted."),
]

def refuse_if_edited(path):
    z = zipfile.ZipFile(path)
    d = z.read("word/document.xml").decode("utf8", "replace")
    ins, dele = d.count("<w:ins "), d.count("<w:del ")
    com = ""
    if "word/comments.xml" in z.namelist():
        com = re.sub(r"<[^>]+>", " ", z.read("word/comments.xml").decode("utf8", "replace")).strip()
    if ins or dele or com:
        sys.exit(f"*** {os.path.basename(path)} carries edits (ins {ins}, del {dele}, "
                 f"comments {len(com)} chars). Sync them into the source first. REFUSING.")
    print("  preserve-gate: no tracked changes, no comments in the input")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in",  dest="src", default=os.path.join(DEL, "GMD.Ladrillo.v1.docx"))
    ap.add_argument("--out", dest="out", default=os.path.join(DEL, "GMD.Ladrillo.v2_L27.docx"))
    a = ap.parse_args()
    if not os.path.exists(a.src): sys.exit(f"missing input {a.src}")
    refuse_if_edited(a.src)

    tmp = tempfile.mkdtemp()
    with zipfile.ZipFile(a.src) as z: z.extractall(tmp)
    dx = os.path.join(tmp, "word/document.xml")
    x = open(dx, encoding="utf8").read()

    # ⛔ NO RUN-COALESCING. The first version of this script ran a regex that deleted
    # `</w:t></w:r><w:r><w:t>` boundaries to make phrases contiguous. That regex also merges runs
    # with DIFFERENT formatting -- it swallowed the VerbatimChar run around `ais_precip0_LOG` into
    # the plain run after it, which would have silently destroyed the monospace styling of every
    # parameter name it touched. Its own edit-match gate caught it. Verified 2026-09-27: all six
    # edits and the insertion anchor match the RAW document.xml with no merging at all, so the step
    # was unnecessary as well as wrong. If a future edit does not match, merge with the docx skill's
    # scripts/merge_runs.py (which merges only IDENTICALLY-formatted runs) -- never with a regex.

    for label, old, new in EDITS:
        if old not in x:
            sys.exit(f"*** EDIT DID NOT MATCH: {label}\n    looking for: {old[:90]}\n"
                     "    the input is not the draft this script was written against. REFUSING.")
        x = x.replace(old, new, 1)
        print(f"  applied: {label}")

    i = x.find(ANCHOR)
    if i < 0: sys.exit(f"*** anchor paragraph not found: {ANCHOR!r}")
    j = x.find("</w:p>", i) + len("</w:p>")
    x = x[:j] + "".join(_p(_b(h) + _t(b)) for h, b in NEW_PARAS) + x[j:]
    print(f"  inserted {len(NEW_PARAS)} paragraphs after: {ANCHOR}")

    open(dx, "w", encoding="utf8").write(x)

    # ---- FIG 1 is still the L24 RENDER, not just an L24 caption ---------------------------------
    # ⚠ The audit that caught the L24 prose checked TEXT only. word/media/image1.png is
    # hindcast_components_L24.png byte-for-byte. Swapping it is the other half of the vintage fix,
    # and it is done by MD5 so the script cannot replace the wrong image if the draft is reordered.
    import hashlib
    fig = os.path.join(REPO, "figures", "hindcast_components_L27.png")
    if not os.path.exists(fig):
        sys.exit("*** missing %s -- run python/plot_hindcast_components.py --tag=L27" % fig)
    want = hashlib.md5(open(os.path.join(REPO, "figures",
                                         "hindcast_components_L24.png"), "rb").read()).hexdigest()
    swapped = None
    for m in sorted(glob.glob(os.path.join(tmp, "word/media/*"))):
        if hashlib.md5(open(m, "rb").read()).hexdigest() == want:
            shutil.copyfile(fig, m); swapped = os.path.basename(m); break
    if swapped is None:
        sys.exit("*** FIG 1 image not found in word/media by MD5: the embedded figure is not "
                 "hindcast_components_L24.png. REFUSING to guess which image to replace.")
    print(f"  FIG 1 image swapped ({swapped}): hindcast_components_L24.png -> _L27.png "
          f"(now carries the IMBIE 2026 series)")
    if os.path.exists(a.out): os.remove(a.out)
    subprocess.run(["zip", "-Xqr", a.out, "."], cwd=tmp, check=True)
    shutil.rmtree(tmp)

    # ⭐ INDEPENDENT-READER GATE: this script wrote it, so something that is NOT this script must read
    # it back. A structurally broken .docx still unzips fine and still has a plausible byte size.
    txt = subprocess.run(["textutil", "-convert", "txt", "-stdout", a.out],
                         capture_output=True, text=True).stdout
    words = len(txt.split())
    if words < 3000: sys.exit(f"*** independent reader got {words} words; expected >3000. STOP")
    must_have = ["50 parameters are sampled", "42 of the 50 parameters pass", "ais_precip_u",
                 "314 and 405 cm", "IMBIE 2026 as an out-of-sample check", "innovation variance",
                 "Ladrillo 1.0 (solid, with its 5\u201395% band)",
                 "IMBIE 2026 reconciled record with its \u00b11\u03c3 band"]
    must_be_gone = ["58 parameters are sampled", "39 of the 58", "L24 is therefore accepted",
                    "ais_precip0_LOG", "329 and 405", "1.008 at 2100", "Ladrillo L24 (solid"]
    bad = [s for s in must_have if s not in txt] + [f"STILL PRESENT: {s}" for s in must_be_gone if s in txt]
    if bad: sys.exit("*** independent reader disagrees:\n  " + "\n  ".join(bad))
    print(f"  independent reader: {words} words, {len(must_have)} new strings present, "
          f"{len(must_be_gone)} stale strings gone")
    print(f"OK -- {os.path.relpath(a.out, REPO)}")

if __name__ == "__main__":
    main()
