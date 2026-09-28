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
 # ⭐ SIMPLIFIED 2026-09-28 (Marcus). The first draft ran to four paragraphs and ~470 words, most of
 # it numbers. This keeps what the reader cannot reconstruct -- that the record is out-of-sample for
 # both sheets, where each one departs, that the departures oppose and so cancel in the total, and
 # that the record sets a floor the posterior sits below -- and drops the supporting arithmetic,
 # which lives in the CHANGELOG and in deliverables/obs_consistency_vs_imbie2026.md.
 ("IMBIE 2026 as an out-of-sample check.",
  " IMBIE is not a likelihood term for either ice sheet, so the 2026 reconciled record (Otosaka et "
  "al., 2026) — which extends Antarctica to 1979 and Greenland to 1972 — is an out-of-sample "
  "comparison for both. Antarctica reproduces the record’s dynamics anomaly within its published "
  "uncertainty in every window while underpredicting the cumulative 1979–2023 level by "
  "2.6σ; the two are linked by construction, since net mass balance is the sum of surface mass "
  "balance and dynamics and the module cannot reproduce the record’s 2018–23 snowfall "
  "anomaly. Greenland tracks the record to within 8 % in every window from 2003 onward, but over "
  "1972–1991 loses 0.50 cm SLE against the record’s 0.13, which is most of the "
  "full-period discrepancy and reflects an acceleration deficit the satellite era alone is too "
  "short to expose."),
 ("The two departures oppose each other.",
  " Greenland is +0.44 cm too high over 1972–2023 and Antarctica −0.38 cm too low over "
  "1979–2023, so they nearly cancel and neither is visible in a comparison made on total sea "
  "level. The observational products disagree the same way: relative to IMBIE the Frederikse-based "
  "target used here is low on Antarctica and high on Greenland, each by about two of IMBIE’s "
  "standard deviations. We do not read the sea-level budget as adjudicating between them — the "
  "component sum already closes against the independent total to within 0.5σ, and substituting "
  "one product for the other moves the residual by a tenth of its own uncertainty. The record does "
  "constrain the error model: its Antarctic surface-mass-balance variability implies a floor on the "
  "Antarctic innovation standard deviation that the posterior sits a factor 1.5 below. Imposing "
  "that floor leaves the calibration marginally worse on both Antarctic scorers, so it is reported "
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
    # ⚠ zip runs with cwd=tmp, so a relative --out would be written INSIDE the temp dir and then
    # deleted with it. Resolve both paths before anything uses them.
    a.src, a.out = os.path.abspath(a.src), os.path.abspath(a.out)
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

    # ---- Table 3: strip the Consolas (VerbatimChar) styling, UNTRACKED (Marcus 2026-09-28) ------
    # ⭐ WHY ONLY TABLE 3, AND ONLY SOME RUNS. Consolas there was doing four different jobs. The nine
    # DOIs and the release tag go to body font: the paper's own 36 reference entries set DOIs as
    # plain text and Table 3 was the ONLY place in the document that did otherwise. The N(mu, sigma)
    # expression goes too -- every other one of the ~30 in the paper, including all of Table 6's
    # prior column, is plain text, so the monospaced one was the outlier. ⛔ The .nc FILENAME KEEPS
    # its monospace: it is a literal a reader must type exactly, which is the one job monospace is
    # actually for, and the same reason Table 6's parameter names keep it.
    KEEP_MONO = ".nc"          # substring test; the DAISfastdyn file is the only such run
    tbls = re.findall(r"<w:tbl>.*?</w:tbl>", x, re.S)
    if len(tbls) < 3:
        sys.exit(f"*** expected at least 3 tables, found {len(tbls)}")
    t3 = tbls[2]
    if "data source" not in re.sub(r"<[^>]+>", "", t3)[:200]:
        sys.exit("*** table 3 is not the calibration-inputs table; the table order changed")
    new_t3, stripped, kept = t3, 0, 0
    for run in re.findall(r"<w:r[ >].*?</w:r>", t3, re.S):
        if 'w:val="VerbatimChar"' not in run:
            continue
        txt = "".join(re.findall(r"<w:t[^>]*>(.*?)</w:t>", run, re.S))
        if KEEP_MONO in txt:
            kept += 1
            continue
        # drop ONLY the rStyle reference; every other property of the run is left alone
        fixed = re.sub(r'<w:rStyle w:val="VerbatimChar"/>', "", run)
        fixed = re.sub(r"<w:rPr>\s*</w:rPr>", "", fixed)
        new_t3 = new_t3.replace(run, fixed, 1)
        stripped += 1
    x = x.replace(t3, new_t3, 1)
    print(f"  Table 3: {stripped} runs un-monospaced, {kept} kept (the .nc filename)")
    if stripped < 9:
        sys.exit(f"*** only {stripped} runs stripped; expected the 9 DOIs plus the tag and the math")

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
    for s in ["IMBIE 2026 as an out-of-sample check", "The two departures oppose each other",
              "Otosaka, I. N., Shepherd, A.", "innovation standard deviation"]:
        if s not in txt:
            sys.exit(f"*** independent reader cannot find: {s}")
    print(f"  gates: all {len(media)} figures byte-identical, w:del {n_del0} unchanged, w:ins {n_ins0} -> "
          f"{d.count('<w:ins ')}, comments {com} chars kept, {len(txt.split())} words")
    print(f"OK -- {os.path.relpath(a.out, REPO)}")

if __name__ == "__main__":
    main()
