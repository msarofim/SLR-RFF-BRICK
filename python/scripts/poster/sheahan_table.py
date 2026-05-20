"""
sheahan_table.py
================

Render Sheahan et al. 2025 (Lancet Planetary Health) HTF elder-mortality
headline numbers as a poster-ready table figure.

Source: Sheahan et al. (2025) Tables 2 and 3 (without / with stylized
adaptation), under the Rennert et al. (2022) RFF+FaIR+BRICK distribution.

Output:
  outputs/poster/sheahan_table.{png,pdf}
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "outputs" / "poster"
OUT.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Sheahan et al. (2025) Tables 2 & 3 — additional elder (65+) deaths per year
# from high-tide flooding, by decade and Rennert et al. (2022) percentile.
# Monetized at the EPA VSL ($7.9M, 1990$), inflated to 2023$.
# ---------------------------------------------------------------------------
NO_ADAPT = {
    # year: (p5, p50, p95) — P25/P75 dropped per poster review (May 16)
    2020: ( 206,   228,   244),
    2050: (1381,  1515,  1996),
    2100: (4281,  9661, 27963),
}
NO_ADAPT_USD_B = {
    2020: (2.8, 3.1, 3.4),
    2050: (30.0, 32.9, 43.3),
    2100: (170.9, 385.6, 1116.0),
}
WITH_ADAPT_2100 = (2765, 5555, 13312)
WITH_ADAPT_2100_USD_B = (110.3, 221.7, 531.3)


def fmt_int(n):
    if n >= 1000:
        return f"{n:,}"
    return f"{n}"


def main():
    fig, ax = plt.subplots(figsize=(11, 5.6))
    ax.axis("off")

    # Build the table contents
    header_rows = [
        ["", "5th percentile", "50th (median)", "95th percentile"],
    ]
    body_rows = []

    # Section 1: deaths/yr by year (no adaptation)
    body_rows.append(["—  No additional adaptation  (Sheahan 2025 Table 2)  —",
                      "", "", ""])
    for yr, vals in NO_ADAPT.items():
        body_rows.append([f"Additional deaths/yr, {yr}",
                          *[fmt_int(v) for v in vals]])
    for yr, vals in NO_ADAPT_USD_B.items():
        body_rows.append([f"VSL-monetized damages, {yr} (USD billion)",
                          *[f"${v:,.1f}" for v in vals]])

    # Section 2: with stylized adaptation (95th-percentile baseline cap)
    body_rows.append(["—  With stylized adaptation (cap at 95th-pct baseline)  (Table 3)  —",
                      "", "", ""])
    body_rows.append(["Additional deaths/yr, 2100",
                      *[fmt_int(v) for v in WITH_ADAPT_2100]])
    body_rows.append(["VSL-monetized damages, 2100 (USD billion)",
                      *[f"${v:,.1f}" for v in WITH_ADAPT_2100_USD_B]])
    # Footer: % reduction from adaptation, computed per percentile
    p5_red  = 100.0 * (1.0 - WITH_ADAPT_2100[0] / NO_ADAPT[2100][0])
    p50_red = 100.0 * (1.0 - WITH_ADAPT_2100[1] / NO_ADAPT[2100][1])
    p95_red = 100.0 * (1.0 - WITH_ADAPT_2100[2] / NO_ADAPT[2100][2])
    body_rows.append(["—  Reduction at 2100 from stylized adaptation  —",
                      f"≈ {p5_red:.0f}%", f"≈ {p50_red:.0f}%", f"≈ {p95_red:.0f}%"])

    table_data = header_rows + body_rows
    n_rows = len(table_data)

    # Render as a matplotlib table with manual styling
    col_widths = [0.46, 0.18, 0.18, 0.18]
    table = ax.table(cellText=table_data,
                     colWidths=col_widths,
                     cellLoc="center",
                     loc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 1.6)

    # Style cells
    for r in range(n_rows):
        for c in range(len(col_widths)):
            cell = table[(r, c)]
            cell.set_edgecolor("#cccccc")
            cell.set_linewidth(0.6)
            if r == 0:
                cell.set_facecolor("#1F4E79")
                cell.set_text_props(color="white", fontweight="bold")
            elif "—  No additional adaptation" in table_data[r][0] or \
                 "—  With stylized adaptation" in table_data[r][0] or \
                 "—  Reduction at median" in table_data[r][0]:
                cell.set_facecolor("#E0E6EE")
                cell.set_text_props(color="#1F4E79", fontweight="bold",
                                    style="italic")
            elif c == 0:
                cell.set_text_props(ha="left")
                cell.PAD = 0.04

    # Internal suptitle dropped per poster review (May 17): duplicates the
    # poster's panel-J label "J. HTF ELDER MORTALITY (Sheahan 2025)".

    fig.tight_layout(rect=[0, 0.06, 1, 0.93])
    fig.savefig(OUT / "sheahan_table.png", dpi=300, bbox_inches="tight")
    fig.savefig(OUT / "sheahan_table.pdf", bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {OUT / 'sheahan_table.png'}")


if __name__ == "__main__":
    main()
