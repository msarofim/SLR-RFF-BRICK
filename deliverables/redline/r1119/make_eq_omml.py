"""Build the OMML (Word equation-editor XML) for Eqs. (1)-(14) from LaTeX with pandoc, once; the output
eq_omml.json is committed so the docx build does not depend on the pandoc version.

    python make_eq_omml.py            # writes eq_omml.json next to this file

Each LaTeX line transcribes the draft's plain-text equation symbol for symbol (same operators, same
grouping); only the notation changes: real sub/superscripts, descriptive subscripts upright (eq, off, thr,
r, f, s), index subscripts italic (b, i, j, k, m, t).
"""
import json, os, re, subprocess, tempfile, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))

# (number, plain text as in the draft, LaTeX)
EQS = [
    (1, "S_eq = max( a·(1 − exp(−b·(T − T_off))), 0 )",
     r"S_{\mathrm{eq}} = \max\left( a \cdot \left(1 - \exp\left(-b \cdot \left(T - T_{\mathrm{off}}\right)\right)\right),\ 0 \right)"),
    (2, "dS   = min( κ·|T − T_eq|^ν, 1 ) · (S_eq − S)",
     r"\mathrm{d}S = \min\left( \kappa \cdot \left|T - T_{\mathrm{eq}}\right|^{\nu},\ 1 \right) \cdot \left(S_{\mathrm{eq}} - S\right)"),
    (3, "E_b(T)   = min( max( k_b·(c₁·T + c₀), 0 ), k_b·V₀ )",
     r"E_b(T) = \min\left( \max\left( k_b \cdot \left(c_1 \cdot T + c_0\right),\ 0 \right),\ k_b \cdot V_0 \right)"),
    (4, "r_j,b(T) = min( max( s_b·(α_j·T + β_j), 10⁻⁹ ), 1 ),   j ∈ {f, s}",
     r"r_{j,b}(T) = \min\left( \max\left( s_b \cdot \left(\alpha_j \cdot T + \beta_j\right),\ 10^{-9} \right),\ 1 \right),\quad j \in \{\mathrm{f}, \mathrm{s}\}"),
    (5, "F_b(t)   = F_b(t−1) + [ f·E_b(T_t−1) − F_b(t−1) ] · r_f,b(T_t−1)",
     r"F_b(t) = F_b(t-1) + \left[ f \cdot E_b\left(T_{t-1}\right) - F_b(t-1) \right] \cdot r_{\mathrm{f},b}\left(T_{t-1}\right)"),
    (6, "D_b(t)   = D_b(t−1) + [ (1 − f)·E_b(T_t−1) − D_b(t−1) ] · r_s,b(T_t−1)",
     r"D_b(t) = D_b(t-1) + \left[ (1 - f) \cdot E_b\left(T_{t-1}\right) - D_b(t-1) \right] \cdot r_{\mathrm{s},b}\left(T_{t-1}\right)"),
    (7, "GIS(t)   = Σ_b [ F_b(t) + D_b(t) ] + P(t)",
     r"\mathrm{GIS}(t) = \sum_b \left[ F_b(t) + D_b(t) \right] + P(t)"),
    (8, "u(t)  = min( max( (G(t−1) − T_thr) / ΔT_r, 0 ), 1 )",
     r"u(t) = \min\left( \max\left( \left(G(t-1) - T_{\mathrm{thr}}\right) / \Delta T_{\mathrm{r}},\ 0 \right),\ 1 \right)"),
    (9, "q₁(t) = q₁(t−1) + [ u(t) − q₁(t−1) ] · n/τ",
     r"q_1(t) = q_1(t-1) + \left[ u(t) - q_1(t-1) \right] \cdot n / \tau"),
    (10, "q₂(t) = q₂(t−1) + [ q₁(t−1) − q₂(t−1) ] · n/τ",
     r"q_2(t) = q_2(t-1) + \left[ q_1(t-1) - q_2(t-1) \right] \cdot n / \tau"),
    (11, "P(t)  = min( V·q₂(t), max( V₀ − Σ_b [ F_b(t) + D_b(t) ], 0 ) )",
     r"P(t) = \min\left( V \cdot q_2(t),\ \max\left( V_0 - \sum_b \left[ F_b(t) + D_b(t) \right],\ 0 \right) \right)"),
    (12, "ln 𝓛_i   = ln N( r_i ; 0, Σ_i )",
     r"\ln 𝓛_i = \ln N\left( r_i;\ 0, \Sigma_i \right)"),
    (13, "(Σ_i)_jk = σ_i²·ρ_i^|j−k| / (1 − ρ_i²) + ε_j·ε_k·exp( −|j − k| / L )",
     r"\left(\Sigma_i\right)_{jk} = \sigma_i^2 \cdot \rho_i^{|j-k|} / \left(1 - \rho_i^2\right) + \varepsilon_j \cdot \varepsilon_k \cdot \exp\left( -|j - k| / L \right)"),
    (14, "ln p(θ)  = Σ_i ln 𝓛_i + Σ_m ln 𝓛_m + ln π(θ)",
     r"\ln p(\theta) = \sum_i \ln 𝓛_i + \sum_m \ln 𝓛_m + \ln \pi(\theta)"),
]


def tidy(o):
    """Merge adjacent math runs with identical properties (pandoc emits one run per character of \\mathrm{...})."""
    run = re.compile(r'<m:r>((?:<m:rPr>(?:(?!</m:rPr>).)*</m:rPr>)?)<m:t(?: xml:space="preserve")?>([^<]*)</m:t></m:r>', re.S)
    while True:
        m2 = None
        for m in run.finditer(o):
            nxt = run.match(o, m.end())
            if nxt and nxt.group(1) == m.group(1) and m.group(2) not in "=+−-⋅,()[]" and nxt.group(2) not in "=+−-⋅,()[]":
                m2 = (m, nxt)
                break
        if not m2:
            return o
        m, nxt = m2
        o = o[:m.start()] + f'<m:r>{m.group(1)}<m:t xml:space="preserve">{m.group(2)}{nxt.group(2)}</m:t></m:r>' + o[nxt.end():]


def main():
    md = "\n\n".join(f"${tex}$" for _, _, tex in EQS) + "\n"
    with tempfile.TemporaryDirectory() as t:
        open(f"{t}/e.md", "w", encoding="utf8").write(md)
        subprocess.run(["pandoc", f"{t}/e.md", "-o", f"{t}/e.docx"], check=True)
        x = zipfile.ZipFile(f"{t}/e.docx").read("word/document.xml").decode("utf8")
    oms = re.findall(r"<m:oMath>.*?</m:oMath>", x, re.S)
    assert len(oms) == len(EQS), (len(oms), len(EQS))
    oms = [tidy(re.sub(r" />", "/>", o)) for o in oms]
    ver = subprocess.run(["pandoc", "--version"], capture_output=True, text=True).stdout.splitlines()[0]
    out = {"pandoc": ver, "eqs": [{"n": n, "plain": p, "tex": tex, "omml": o} for (n, p, tex), o in zip(EQS, oms)]}
    json.dump(out, open(os.path.join(HERE, "eq_omml.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
    print(f"eq_omml.json: {len(oms)} equations ({ver})")


if __name__ == "__main__":
    main()
