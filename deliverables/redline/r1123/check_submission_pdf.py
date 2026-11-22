"""Checks on the Word-rendered submission PDF (2026-11-22), read with poppler (pdfinfo, pdffonts, pdftotext), not with
the code that built the docx.

    python check_submission_pdf.py <submission.pdf>

  [FONTS]         every font is embedded (GMD: non-standard fonts must be embedded).
  [PAGE-NUMBERS]  the last non-empty line of page i is "i", for every page.
  [LINE-NUMBERS]  page 1 starts at line 1, and each page's first line number is the previous page's last + 1
                  (continuous numbering, no restart per page).
  [TEXT-LAYER]    the extracted text has no ligature artefacts ("calibraMon", "observaMon") and reads "calibration".
Mutation: --mutate=restart re-numbers page 2 from 1 and must FAIL [LINE-NUMBERS].
"""
import re, subprocess, sys

pdf = sys.argv[1]
MUTATE = next((a.split("=", 1)[1] for a in sys.argv[2:] if a.startswith("--mutate=")), None)
fails = []


def gate(name, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + name + ("" if ok else f": {detail}"))
    if not ok:
        fails.append(name)


run = lambda *a: subprocess.run(a, capture_output=True, text=True, check=True).stdout
n = int(re.search(r"Pages:\s+(\d+)", run("pdfinfo", pdf)).group(1))
fonts = [l for l in run("pdffonts", pdf).splitlines()[2:] if l.strip()]
bad = [l for l in fonts if l.split()[-5] != "yes"]
gate("FONTS", fonts and not bad, bad)

pages = [run("pdftotext", "-f", str(i), "-l", str(i), "-layout", pdf, "-") for i in range(1, n + 1)]
last = [([l.strip() for l in p.splitlines() if l.strip()] or [""])[-1] for p in pages]
wrong = [(i + 1, s) for i, s in enumerate(last) if s != str(i + 1)]
gate("PAGE-NUMBERS", not wrong, wrong[:5])

MIN_CHAIN = 3                                       # consecutive numbers needed to count a page as line-numbered


def chain(nums):
    """Longest run of candidates in reading order that steps by exactly +1. A line number can stand alone (the line next
    to a figure) and a table cell can start with a digit, so candidates are filtered by continuity, not by layout."""
    best = []
    for i, a in enumerate(nums):
        run_, cur = [a], a
        for b in nums[i + 1:]:
            if b == cur + 1:
                run_.append(b)
                cur = b
        if len(run_) > len(best):
            best = run_
    return best


chains = []
for k, p in enumerate(pages):
    nums = [int(m.group(1)) for l in p.splitlines() for m in [re.match(r"^\s{0,3}(\d{1,5})(?:\s{2,}\S|\s*$)", l)] if m]
    nums = nums[:-1] if nums and str(nums[-1]) == last[k] else nums      # the footer's page number
    if MUTATE == "restart" and k == 1:
        nums = [v - nums[0] + 1 for v in nums]
    chains.append(chain(nums))
seen, breaks, used = 0, [], []
for k, c in enumerate(chains):
    if c and c[0] == seen + 1:
        seen = c[-1]                               # continues the sequence (any length: a page may hold 2 blank lines)
        used.append(c)
    elif len(c) >= MIN_CHAIN:
        breaks.append((k + 1, seen, c[0]))         # a real run of numbers that does not continue: a restart or a gap
        seen = c[-1]
        used.append(c)
    # else: no numbers, or a stray digit in a table cell (Word does not number table rows)
gate("LINE-NUMBERS", chains[0][:1] == [1] and not breaks,
     f"breaks (page, previous last, first) {breaks[:5]}")
lasts = [c[-1] for c in used]

t = run("pdftotext", pdf, "-")
gate("TEXT-LAYER", "calibraMon" not in t and "observaMon" not in t and t.count("calibration") > 10,
     f"calibraMon {t.count('calibraMon')}, calibration {t.count('calibration')}")
print(f"{n} pages; lines numbered 1-{max(lasts)} (tables are not numbered by Word)")
print("ALL PDF CHECKS PASS" if not fails else f"FAILED: {fails}")
sys.exit(1 if fails else 0)
