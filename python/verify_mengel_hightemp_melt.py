#!/usr/bin/env python3
"""
Verify the calibrated Mengel 2-tau glacier melts MOST global glaciers at high T.

Marcus 2026-06-13: the Mengel GIC parameterization is an improvement over the old
single-reservoir (commit-everything) GSIC, but the historical calibration only sees
dT < 1.3 C -- which constrains the INITIAL SLOPE (a*b) but barely the SATURATION RATE
b. A low posterior b would leave S_eq(T) far below the full glacier volume `a` even at
extreme warming, i.e. most glaciers would NEVER melt. This script checks that does NOT
happen: at high T the emulator commits ~all of `a`, and `a` is physically bounded.

Emulator (glaciers_mengel_component.jl), integrated here identically:
  S_eq(T) = a*(1 - exp(-b*(T - T_lia)))                 # equilibrium, -> a as T->inf
  S_fast += (f*S_eq     - S_fast)/tau_fast              # committed early melt
  S_slow += ((1-f)*S_eq - S_slow)/tau_slow              # slow modern tracking
  S = S_fast + S_slow                                   # cumulative SLE since 1850 (S0=gic_sl0=0)

Metrics reported (vs T and under SSP5-8.5 GMST 1850-2300):
  1. COMMITTED melt fraction  S_eq(T)/a = 1-exp(-b(T-T_lia))  vs dT  (does equilibrium -> ~1?)
  2. REALIZED melt fraction   S(year)/a  at 2100/2300  (tau-limited)
  3. gic_a posterior vs physical global glacier volume (Farinotti 2019 ~0.32 m SLE)

  python python/verify_mengel_hightemp_melt.py [TAG]   # TAG="" baseline (default) | "ext"
"""
import os, sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO = os.path.expanduser("~/Documents/2026/CodeProjects/SLR-RFF-BRICK")
TAG  = sys.argv[1] if len(sys.argv) > 1 else ""
SUF  = "" if TAG == "" else f"_{TAG}"
LABEL = "2018-baseline" if TAG == "" else TAG

POST = os.path.join(REPO, f"data/MimiBRICK/parameters_subsample_brick_mengel{SUF}.csv")
GMST = os.path.join(REPO, "data/observations/fair_mean_gmst_ssp585.csv")   # high-T scenario
OUT_PNG = os.path.join(REPO, f"outputs/mengel_hightemp_melt{SUF}.png")
OUT_MD  = os.path.join(REPO, f"outputs/mengel_hightemp_melt{SUF}_summary.md")

# physical reference: global glacier ice volume in SLE (excl. ice sheets)
GLAC_VOL_FARINOTTI = 0.324      # m SLE, Farinotti et al. 2019 (158e3 km^3); +/-0.084
GLAC_VOL_LO, GLAC_VOL_HI = 0.240, 0.408
MELT_FLOOR = 0.80               # "most glaciers": flag if committed fraction < 80% by dT=4C

p = pd.read_csv(POST)
a, b = p["gic_a"].values, p["gic_b"].values
Tlia, f = p["gic_T_lia"].values, p["gic_f"].values
tauf, taus = p["gic_tau_fast"].values, p["gic_tau_slow"].values
n = len(p)
print(f"Mengel high-T melt check [{LABEL}] -- {n} posterior draws")

# ---- 1. committed (equilibrium) melt fraction vs dT ----
print("\n1. COMMITTED melt fraction  S_eq/a = 1-exp(-b*(dT - T_lia))  (median [5-95%]):")
committed = {}
for dT in [1.3, 2, 3, 4, 5, 7, 8]:
    fr = 1 - np.exp(-b * (dT - Tlia))
    q = np.percentile(fr, [5, 50, 95]); committed[dT] = q
    print(f"   dT={dT:4.1f}C:  {q[1]*100:5.1f}%  [{q[0]*100:.0f}, {q[2]*100:.0f}]%")
frac4 = committed[4][1]
verdict = "PASS" if frac4 >= MELT_FLOOR else "FAIL"

# ---- 2. integrate the exact 2-reservoir ODE under SSP5-8.5 GMST ----
g = pd.read_csv(GMST); g = g[(g.year >= 1850) & (g.year <= 2300)].sort_values("year")
yrs = g.year.values; T = g.gmst_C.values
S_fast = np.zeros(n); S_slow = np.zeros(n)         # S0 = gic_sl0 = 0 at 1850
S_year, Seq_year = {}, {}
for k in range(1, len(yrs)):
    Seq = a * (1 - np.exp(-b * (T[k-1] - Tlia)))
    S_fast += (f * Seq       - S_fast) / tauf
    S_slow += ((1 - f) * Seq - S_slow) / taus
    if yrs[k] in (2050, 2100, 2200, 2300):
        S_year[yrs[k]]   = S_fast + S_slow
        Seq_year[yrs[k]] = a * (1 - np.exp(-b * (T[k] - Tlia)))

print("\n2. Under SSP5-8.5 (GMST 2100=4.7C, 2300=7.8C) -- realized vs committed (median [5-95%]):")
print("   year   realized S (m)     realized S/a (%)   committed S_eq/a (%)   remaining a-S (m)")
realized = {}
for y in [2050, 2100, 2200, 2300]:
    S = S_year[y]; fr_real = S / a; fr_com = Seq_year[y] / a; rem = a - S
    qs = np.percentile(S, [5, 50, 95]); qr = np.percentile(fr_real, [5, 50, 95])
    qc = np.percentile(fr_com, [5, 50, 95]); qrem = np.percentile(rem, [5, 50, 95])
    realized[y] = (qs, qr, qc, qrem)
    print(f"   {y}   {qs[1]:.3f} [{qs[0]:.3f},{qs[2]:.3f}]   {qr[1]*100:4.0f} [{qr[0]*100:.0f},{qr[2]*100:.0f}]"
          f"      {qc[1]*100:4.1f} [{qc[0]*100:.0f},{qc[2]*100:.0f}]      {qrem[1]:.3f} [{qrem[0]:.3f},{qrem[2]:.3f}]")

# ---- 3. gic_a vs physical glacier volume ----
qa = np.percentile(a, [5, 50, 95])
print(f"\n3. gic_a (asymptotic max SLE) = {qa[1]:.3f} m [{qa[0]:.3f}, {qa[2]:.3f}]")
print(f"   vs Farinotti 2019 global glacier volume {GLAC_VOL_FARINOTTI:.3f} m SLE [{GLAC_VOL_LO:.2f}, {GLAC_VOL_HI:.2f}]")
in_range = GLAC_VOL_LO <= qa[1] <= GLAC_VOL_HI

# ---- figure ----
fig, ax = plt.subplots(1, 3, figsize=(16, 4.6))
dTg = np.linspace(0, 8, 200)
fr_grid = np.array([1 - np.exp(-b * (t - Tlia)) for t in dTg])           # (200, n)
ax[0].fill_between(dTg, np.percentile(fr_grid, 5, axis=1)*100, np.percentile(fr_grid, 95, axis=1)*100,
                   color="C0", alpha=0.25, label="5-95%")
ax[0].plot(dTg, np.percentile(fr_grid, 50, axis=1)*100, "C0", lw=2, label="median")
ax[0].axhline(MELT_FLOOR*100, color="grey", ls=":", label=f"{MELT_FLOOR*100:.0f}% ('most')")
for dT, c in [(4, "SSP5-8.5 @2100"), (7.8, "@2300")]:
    ax[0].axvline(dT, color="C3", ls="--", lw=0.8); ax[0].text(dT, 30, c, rotation=90, fontsize=7, va="bottom")
ax[0].set_xlabel("ΔT rel 1850-1900 (°C)"); ax[0].set_ylabel("committed melt  S_eq/a  (%)")
ax[0].set_title("(a) Equilibrium melt fraction vs warming"); ax[0].set_ylim(0, 102); ax[0].legend(fontsize=8); ax[0].grid(alpha=0.3)

# realized trajectory under SSP5-8.5
S_fast = np.zeros(n); S_slow = np.zeros(n); traj = np.zeros((len(yrs), n)); seq_traj = np.zeros((len(yrs), n))
for k in range(1, len(yrs)):
    Seq = a * (1 - np.exp(-b * (T[k-1] - Tlia)))
    S_fast += (f*Seq - S_fast)/tauf; S_slow += ((1-f)*Seq - S_slow)/taus
    traj[k] = S_fast + S_slow; seq_traj[k] = a*(1-np.exp(-b*(T[k]-Tlia)))
m = yrs >= 1900
ax[1].fill_between(yrs[m], np.percentile(traj[m],5,axis=1), np.percentile(traj[m],95,axis=1), color="C1", alpha=0.25)
ax[1].plot(yrs[m], np.percentile(traj[m],50,axis=1), "C1", lw=2, label="realized S (median)")
ax[1].plot(yrs[m], np.percentile(seq_traj[m],50,axis=1), "C0", lw=1.5, ls="--", label="committed S_eq (median)")
ax[1].axhline(qa[1], color="k", ls=":", label=f"gic_a={qa[1]:.2f} m (full volume)")
ax[1].axhspan(GLAC_VOL_LO, GLAC_VOL_HI, color="green", alpha=0.08)
ax[1].set_xlabel("year"); ax[1].set_ylabel("glacier SLE since 1850 (m)")
ax[1].set_title("(b) SSP5-8.5: realized vs committed melt"); ax[1].legend(fontsize=8); ax[1].grid(alpha=0.3)

ax[2].hist(a, bins=40, color="C1", alpha=0.7, density=True)
ax[2].axvline(GLAC_VOL_FARINOTTI, color="green", lw=2, label="Farinotti 2019 (0.32 m)")
ax[2].axvspan(GLAC_VOL_LO, GLAC_VOL_HI, color="green", alpha=0.12, label="glacier vol range")
ax[2].set_xlabel("gic_a (m SLE)"); ax[2].set_ylabel("posterior density")
ax[2].set_title("(c) Max melt `a` vs glacier inventory"); ax[2].legend(fontsize=8); ax[2].grid(alpha=0.3)

fig.suptitle(f"Mengel GIC high-temperature melt check [{LABEL} posterior, {n} draws]  —  "
             f"committed@4°C = {frac4*100:.1f}%  →  {verdict}", fontsize=12)
fig.tight_layout(); fig.savefig(OUT_PNG, dpi=130); print(f"\nWrote {OUT_PNG}")

with open(OUT_MD, "w") as fh:
    fh.write(f"# Mengel GIC high-temperature melt check — {LABEL} posterior ({n} draws)\n\n")
    fh.write(f"**Verdict: {verdict}** — committed melt fraction at ΔT=4°C (SSP5-8.5 @2100) "
             f"= {frac4*100:.1f}% (threshold {MELT_FLOOR*100:.0f}% for 'most glaciers').\n\n")
    fh.write(f"`gic_b` median = {np.median(b):.3f} [{np.percentile(b,5):.3f}, {np.percentile(b,95):.3f}] "
             f"(saturation rate; high → fast saturation → near-complete high-T melt).\n\n")
    fh.write("## 1. Committed (equilibrium) melt fraction S_eq/a = 1-exp(-b(ΔT - T_lia))\n\n")
    fh.write("| ΔT (°C) | committed melt % (median [5-95%]) |\n|--|--|\n")
    for dT in [1.3, 2, 3, 4, 5, 7, 8]:
        q = committed[dT]; fh.write(f"| {dT} | {q[1]*100:.1f} [{q[0]*100:.0f}, {q[2]*100:.0f}] |\n")
    fh.write("\n## 2. Under SSP5-8.5 (GMST 2100=4.7°C, 2200=7.3°C, 2300=7.8°C)\n\n")
    fh.write("| year | realized S (m) | realized S/a (%) | committed S_eq/a (%) | remaining a-S (m) |\n|--|--|--|--|--|\n")
    for y in [2050, 2100, 2200, 2300]:
        qs, qr, qc, qrem = realized[y]
        fh.write(f"| {y} | {qs[1]:.3f} [{qs[0]:.3f}, {qs[2]:.3f}] | {qr[1]*100:.0f} [{qr[0]*100:.0f}, {qr[2]*100:.0f}] "
                 f"| {qc[1]*100:.1f} [{qc[0]*100:.0f}, {qc[2]*100:.0f}] | {qrem[1]:.3f} [{qrem[0]:.3f}, {qrem[2]:.3f}] |\n")
    fh.write(f"\n## 3. Max melt `a` vs physical glacier inventory\n\n")
    fh.write(f"`gic_a` = {qa[1]:.3f} m SLE [{qa[0]:.3f}, {qa[2]:.3f}] vs Farinotti 2019 "
             f"{GLAC_VOL_FARINOTTI} m [{GLAC_VOL_LO}, {GLAC_VOL_HI}] — "
             f"{'physically consistent' if in_range else 'OUT OF RANGE'}.\n")
    fh.write("\n**Caveat:** `S_eq`/`a` is relative to the Little-Ice-Age glacier state; the long "
             "`gic_tau_slow` means full realization of committed melt lags centuries past 2100 "
             "(physically expected for large/cold glaciers). At equilibrium / on multi-century "
             "timescales, near-all glacier volume melts at high T.\n")
print(f"Wrote {OUT_MD}")
print(f"\nVERDICT [{LABEL}]: committed@4C = {frac4*100:.1f}% -> {verdict};  "
      f"gic_a {qa[1]:.3f}m {'in' if in_range else 'OUT of'} glacier-volume range")
