#!/usr/bin/env python3
"""
build_gmd_otosaka.py -- add the Otosaka/IMBIE-2026 material to the CURRENT review draft.

⚠⚠ BASE IS THE REVIEW DRAFT, NOT GMD.Ladrillo.v1.docx. My earlier v2 was built on v1, which is
obsolete: the review draft is ~3,900 words longer, carries Marcus's comments and live tracked
changes, and ALREADY CONTAINS every L27 correction v2 applied (50 parameters, 42 of 50 converged,
ais_precip_u, 314 cm, no "L24 is therefore accepted"). Its antarctic_lambda sentence is also better
written than mine. ⇒ NOTHING from v2 is merged except the IMBIE-2026 content, which is the one thing
the review draft does not have (no "IMBIE 2026", no "Otosaka" anywhere in it).

⛔ THE FIGURES ARE ALREADY BEING FIXED, AS TRACKED CHANGES -- DO NOT TOUCH THEM. image3/5/7/9 (the
L24 renders) sit inside <w:del> and image4/6/8/10 are their replacements; image1/2 are inside
<w:ins>. Marcus is mid-review of exactly that swap, and rewriting the media would destroy it.

⭐ EVERY ADDITION IS A TRACKED INSERTION attributed to "Claude", matching the convention already in
the file (w:author="Claude"), so the new text appears as markup rather than silently becoming part
of the accepted prose. Untracked edits in a document under review are invisible in the accepted view
-- which is exactly how a reviewer loses track of what changed.

  python3 python/build_gmd_otosaka.py [--in <review.docx>] [--out <new.docx>]
"""
import argparse, os, re, shutil, subprocess, sys, tempfile, zipfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEL  = os.path.join(REPO, "deliverables")
AUTHOR, DATE = "Claude", "2026-09-28T00:00:00Z"
ANCHOR = "Deliberately removed: IMBIE, and the total."
REF_BEFORE = "Rignot, E., Mouginot, J., Scheuchl, B."   # bibliography is alphabetical

_id = [1000]
def nid():
    _id[0] += 1
    return _id[0]

def ins_para(lead, body, style="BodyText"):
    """One tracked-inserted paragraph: the runs AND the paragraph mark are marked inserted."""
    pm = f'<w:rPr><w:ins w:id="{nid()}" w:author="{AUTHOR}" w:date="{DATE}"/></w:rPr>'
    runs = ""
    if lead:
        runs += (f'<w:ins w:id="{nid()}" w:author="{AUTHOR}" w:date="{DATE}">'
                 f'<w:r><w:rPr><w:b/><w:bCs/></w:rPr>'
                 f'<w:t xml:space="preserve">{lead}</w:t></w:r></w:ins>')
    runs += (f'<w:ins w:id="{nid()}" w:author="{AUTHOR}" w:date="{DATE}">'
             f'<w:r><w:t xml:space="preserve">{body}</w:t></w:r></w:ins>')
    return f'<w:p><w:pPr><w:pStyle w:val="{style}"/>{pm}</w:pPr>{runs}</w:p>'

PARAS = [
 ("IMBIE 2026 as an out-of-sample check.",
  " Because IMBIE is not a likelihood term for either ice sheet, the 2026 reconciled record "
  "(Otosaka et al., 2026), which extends Antarctica to 1979 and Greenland to 1972, is an "
  "out-of-sample comparison for both. For Antarctica the posterior reproduces the record’s "
  "dynamics anomaly within its published uncertainty in every window — its largest departure, "
  "+48 Gt yr⁻¹ over 2018–23, is 0.4 of IMBIE’s own uncertainty for that window — "
  "while underpredicting the cumulative 1979–2023 level by 2.6σ. The two are not "
  "independent: net mass balance is the sum of surface mass balance and dynamics by construction, "
  "and because the module’s surface mass balance cannot reproduce the record’s "
  "+141 Gt yr⁻¹ 2018–23 snowfall anomaly, a calibration that matched the net exactly "
  "would necessarily understate the dynamics anomaly by about 114 Gt yr⁻¹."),
 ("The Greenland record, which is new below 1992.",
  " The Greenland comparison is the cleaner of the two, since no vintage of the Greenland target has "
  "contained IMBIE. From 2003 onward the modelled rate is within 8 % of the record in every "
  "assessment window (0.92, 0.99 and 0.93 times observed over 2003–10, 2011–17 and "
  "2018–23). Over 1972–1991 the model loses 0.50 cm SLE against the record’s 0.13 "
  "(+3.7σ), and 83 % of the full-period 1972–2023 discrepancy of +0.44 cm accumulates in "
  "those two decades; about a quarter of the early gap is the calibration target itself running high "
  "against the record (+0.09 cm) and the remainder is the model departing from its own target. The "
  "pattern is an acceleration deficit measured over a longer baseline than the satellite era allows: "
  "the record’s Greenland loss rate rises by a factor of 10.5 between 1972–91 and "
  "2011–17 while the model’s rises by 2.7. The ratio itself is not a stable statistic — "
  "the observed 1972–91 rate is 0.0064 ± 0.0041 cm yr⁻¹ — so the level "
  "comparison, not the rate ratio, carries the result."),
 ("The two ice sheets depart in opposite directions.",
  " Greenland is +0.44 cm over 1972–2023 and Antarctica −0.38 cm over 1979–2023, "
  "summing to +0.07 cm, so neither departure is visible in a comparison made on total sea level "
  "alone. The same opposition appears between the observational products themselves: relative to "
  "IMBIE, the Frederikse-based target used here is low on Antarctica by 0.41 cm and high on Greenland "
  "by 0.24 cm, each about two of IMBIE’s standard deviations. We do not treat the sea-level "
  "budget as adjudicating between the two products: over 1972–2021 the component sum already "
  "closes against the independent total to within 0.5σ, and substituting IMBIE for the "
  "Frederikse ice sheets changes the residual by a tenth of its own uncertainty, with a sign that "
  "depends on the window chosen."),
 ("The Antarctic innovation variance.",
  " The record also constrains the error model. Its Antarctic surface-mass-balance anomaly varies "
  "from year to year with a standard deviation of first differences of 118 Gt yr⁻¹ over "
  "1979–2019, a variability present in every decade since the 1980s and of which global mean "
  "surface temperature explains 4 %, so it is weather rather than a forced signal the module could "
  "reproduce. Expressed as a sea-level innovation this implies a lower bound of 0.033 cm "
  "yr⁻¹ on the Antarctic AR(1) innovation standard deviation; the posterior fits 0.0216 cm "
  "(5–95 %: 0.0188–0.0249), a factor 1.5 below that bound and outside its own 95th "
  "percentile. Refitting with that standard deviation floored at the implied value, and nothing else "
  "changed, leaves the configuration marginally worse on both the full-record and altimetry-era "
  "Antarctic scorers (0.73 against 0.70 and 1.32 against 1.27 σ), so the correction is reported "
  "rather than adopted."),
]

REF = ("Otosaka, I. N., Shepherd, A., Amory, C., Horwath, M., Ivins, E. R., King, M. D., Nowicki, S., "
       "Payne, A. J., Rignot, E., Sørensen, L. S., Schlegel, N. J., Simon, K. M., Smith, B. E., "
       "Sutterley, T. C., van den Broeke, M. R., Velicogna, I., A, G., Agosta, C., Ditmar, P., "
       "Döhne, T., Engdahl, M. E., Fettweis, X., Forsberg, R., Gardner, A. S., Gilbert, L., "
       "Goelzer, H., Gourmelen, N., Groh, A., Hansen, N., Harig, C., Helm, V., Khan, S. A., "
       "Kittel, C., Langen, P. L., Larsen, M., Loomis, B. D., McMillan, M., Medley, B., Melini, D., "
       "Mottram, R. H., Muir, A., Nilsson, J., Noël, B., Pattle, M. E., Roca i Aparici, M., "
       "Sasgen, I., Save, H. V., Scheuchl, B., Schrama, E. J. O., Schröder, L., Seo, K. W., "
       "Simonsen, S. B., Slater, T., Spada, G., Vishwakarma, B. D., Wever, N., Wiese, D. N., and "
       "Wouters, B.: Mass balance of the Greenland and Antarctic ice sheets from the 1970s to 2023, "
       "Sci. Data, 13, 1301, https://doi.org/10.1038/s41597-026-08088-0, 2026.")

def refuse_if_wrong_base(x):
    if ANCHOR not in x:
        sys.exit(f"*** anchor not found: {ANCHOR!r}. Wrong base document.")
    if "IMBIE 2026" in x or "Otosaka" in x:
        sys.exit("*** this draft ALREADY contains IMBIE 2026 / Otosaka material. REFUSING to "
                 "duplicate it -- rerunning this script on its own output is not idempotent.")
    for s in ["50 parameters are sampled", "ais_precip_u", "314 and 405 cm"]:
        if s not in x:
            sys.exit(f"*** {s!r} missing: this base is NOT the L27-corrected review draft, so the "
                     "L27 fixes would also be needed and this script does not apply them.")
    print("  base gate: review draft, already L27-corrected, no IMBIE content yet")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in",  dest="src",
                    default=os.path.join(DEL, "GMD.Ladrillo.v1_review-2026-09-21c_L27.docx"))
    ap.add_argument("--out", dest="out",
                    default=os.path.join(DEL, "GMD.Ladrillo.v1_review-2026-09-28_L27_otosaka.docx"))
    a = ap.parse_args()
    tmp = tempfile.mkdtemp()
    with zipfile.ZipFile(a.src) as z:
        z.extractall(tmp)
        n_ins0 = z.read("word/document.xml").decode("utf8").count("<w:ins ")
        n_del0 = z.read("word/document.xml").decode("utf8").count("<w:del ")
        media0 = {n: z.read(n) for n in z.namelist()
                  if n.startswith("word/media/") and not n.endswith("/")}
    dx = os.path.join(tmp, "word/document.xml")
    x = open(dx, encoding="utf8").read()
    refuse_if_wrong_base(x)

    # keep new w:id values clear of the ones already in the file
    _id[0] = max(int(i) for i in re.findall(r'w:id="(\d+)"', x)) + 1000

    j = x.index("</w:p>", x.index(ANCHOR)) + len("</w:p>")
    x = x[:j] + "".join(ins_para(h, b) for h, b in PARAS) + x[j:]
    print(f"  inserted {len(PARAS)} tracked paragraphs after: {ANCHOR}")

    k = x.rindex("<w:p ", 0, x.index(REF_BEFORE))
    x = x[:k] + ins_para("", REF, style="BodyText") + x[k:]
    print("  inserted the Otosaka reference before the Rignot entry (alphabetical)")

    open(dx, "w", encoding="utf8").write(x)
    if os.path.exists(a.out):
        os.remove(a.out)
    subprocess.run(["zip", "-Xqr", a.out, "."], cwd=tmp, check=True)
    shutil.rmtree(tmp)

    # ---- gates: nothing of Marcus's may be lost, and every change must be tracked -------------
    with zipfile.ZipFile(a.out) as z:
        d = z.read("word/document.xml").decode("utf8")
        media = {n: z.read(n) for n in z.namelist()
                 if n.startswith("word/media/") and not n.endswith("/")}
        com = "word/comments.xml" in z.namelist() and len(
            re.sub(r"<[^>]+>", " ", z.read("word/comments.xml").decode("utf8")).strip())
    # ⚠ compare the BYTES, not the entry count: `zip -r` adds a `word/media/` DIRECTORY entry, which
    # made the first version of this gate fire on a run that had not touched a single image.
    if set(media) != set(media0):
        sys.exit(f"*** the set of figures changed: {sorted(set(media) ^ set(media0))}")
    changed = [n for n in media0 if media[n] != media0[n]]
    if changed:
        sys.exit(f"*** these figures were modified and must not have been: {changed}")
    if d.count("<w:del ") != n_del0:
        sys.exit(f"*** tracked deletions changed {n_del0} -> {d.count('<w:del ')}")
    if d.count("<w:ins ") <= n_ins0:
        sys.exit("*** no tracked insertion was added")
    if not com:
        sys.exit("*** the comments were lost")
    txt = subprocess.run(["textutil", "-convert", "txt", "-stdout", a.out],
                         capture_output=True, text=True).stdout
    for s in ["IMBIE 2026 as an out-of-sample check", "The Greenland record, which is new below 1992",
              "Otosaka, I. N., Shepherd, A.", "innovation variance"]:
        if s not in txt:
            sys.exit(f"*** independent reader cannot find: {s}")
    print(f"  gates: all {len(media)} figures byte-identical, w:del {n_del0} unchanged, w:ins {n_ins0} -> "
          f"{d.count('<w:ins ')}, comments {com} chars kept, {len(txt.split())} words")
    print(f"OK -- {os.path.relpath(a.out, REPO)}")

if __name__ == "__main__":
    main()
