"""Mutation test of verify_r1115.py: break what each check guards and require the gate to FAIL.

    python mutation_test_verify.py <tracked base> <tracked out> <clean base> <clean out>   (writes mutation_result_verify.txt)
"""
import os, re, subprocess, sys, tempfile, zipfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from trackedit import AUTHOR, DATE  # noqa: E402
OWN = f'w:author="{AUTHOR}" w:date="{DATE}"'
D = "word/document.xml"


def mutate(src, dst, edits):
    with zipfile.ZipFile(src) as zi:
        infos = zi.infolist()
        data = {it.filename: zi.read(it.filename) for it in infos}
    with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zo:
        for it in infos:
            b = data[it.filename]
            if it.filename in edits:
                b = edits[it.filename](b, data)
            zo.writestr(it, b)


def txt(f):
    return lambda b, data: f(b.decode("utf8")).encode("utf8")


def once(old, new):
    def f(s):
        assert old in s, old[:50]
        return s.replace(old, new, 1)
    return f


def nest(s):
    m = re.search(r'<w:ins w:id="\d+" ' + re.escape(OWN) + r'>.*?</w:ins>', s, re.S)
    return s[:m.start()] + f'<w:ins w:id="999991" {OWN}>' + m.group(0) + "</w:ins>" + s[m.end():]


def drop_avail(s):
    return re.sub(r'<w:ins w:id="\d+" ' + re.escape(OWN) + r'><w:r>(?:(?!</w:ins>).)*?The archive also includes(?:(?!</w:ins>).)*</w:ins>',
                  "", s, count=1, flags=re.S)


def third_done(s):   # resolve one more, still-open comment
    return re.sub(r'w15:done="0"', 'w15:done="1"', s, count=1)


def undone(s):       # reopen the last resolved comment (one of the two stale ones is resolved last in file order? any)
    i = s.rfind('w15:done="1"')
    return s[:i] + 'w15:done="0"' + s[i + len('w15:done="1"'):]


def swap_image(b, data):
    return data["word/media/image2.png"]


TRACKED = [("V1", {D: txt(once("A user manual", "A userZ manual"))}), ("V2", {D: txt(nest)}),
           ("V3", {D: txt(drop_avail)}), ("V4", {"word/commentsExtended.xml": txt(third_done)})]
CLEAN = [("C1", {D: txt(once("<w:r><w:t>", f'<w:ins w:id="999992" {OWN}><w:r><w:t>X</w:t></w:r></w:ins><w:r><w:t>'))}),
         ("C2", {D: txt(once("archived as used", "archived as is"))}),
         ("C3", {"word/media/image3.png": swap_image}),
         ("C4", {"word/commentsExtended.xml": txt(undone)})]

if __name__ == "__main__":
    tb, to, cb, co = sys.argv[1:5]
    lines = []
    with tempfile.TemporaryDirectory() as t:
        for name, ed in TRACKED + CLEAN:
            dst = os.path.join(t, name + ".docx")
            if name.startswith("V"):
                mutate(to, dst, ed); args = [tb, dst, cb, co]
            else:
                mutate(co, dst, ed); args = [tb, to, cb, dst]
            r = subprocess.run([sys.executable, os.path.join(HERE, "verify_r1115.py")] + args, capture_output=True, text=True)
            fails = [l for l in r.stdout.splitlines() if "FAIL" in l and "ALL" not in l and not l.startswith("[VERIFY] FAIL")]
            lines.append(f"{name}: {'KILLED' if r.returncode else 'SURVIVED'}  {fails[0][:110] if fails else ''}")
            print(lines[-1])
    open(os.path.join(HERE, "mutation_result_verify.txt"), "w").write(
        f"verify_r1115.py mutation test on {os.path.basename(to)} + {os.path.basename(co)}\n" + "\n".join(lines) + "\n")
    sys.exit(0 if all("KILLED" in l for l in lines) else 1)
