# Handoff — the MAGICC-climate arm is RUN, and the gap splits differently in every component

**Start here.** Repo `SLR-RFF-BRICK`, branch `ladrillo-dev`, HEAD **`88a33d1`**, **NOT yet
pushed** (previous arc pushed at `bf43043`/`20cb1f9`). Written 2026-08-31, continuing
`handoff_2026-08-31f_glacier_equilibrium_and_magicc_climate.md`, whose §6 was the ⭐ open item
and is now done.

⚠ **STILL THREE REPOS. The standing instruction from `31f` holds**: *"Push Ladrillo. Don't push
anything to shared repos with MAGICC or Nauels GitLab."* `facts` and `MAGICC/slr-refresh` stay
local. This session also touched **`FaIRtoFrEDI`** (2 commits, branch `heat-ed-morbidity`).

| what | where | branch | state |
|---|---|---|---|
| the arm, the scopes, this note | `SLR-RFF-BRICK/` | `ladrillo-dev` | 6 commits, **unpushed** |
| the MAGICC wide-CSV builder | `FaIRtoFrEDI/` | `heat-ed-morbidity` | 2 commits |
| MAGICC run outputs (read only) | `MAGICC/slr-refresh/` | — | untouched |

---

## 1. THE DESIGN DECISION WAS MADE, NOT ASSUMED

`31f` §6.3 said the spliced-vs-raw choice must be flagged and awaited. **Marcus 2026-08-31:
SPLICED primary, RAW as a check; Ladrillo only, not the four-model version.** Everything below
follows that.

Before asking, the thing the choice turns on was measured — `31f` §6.3 said nobody had.
`python/scope_magicc_climate_history_gap.py` (`65d3f27`):

* GMST over 1850-2014: MAGICC's ensemble median is **+0.105 K rms** above the FaIR mean-config
  driver (markers; +0.085 SSPs), **+0.143 K at 2014**. Eleven times the 0.01 K we quote to.
* **The difference is NOT a scalar shift**: MAGICC is **warmer over the history** and **0.38-0.93 K
  colder at 2300** on the declining markers. A swap moves the hindcast one way and the tail the other.
* OHC: removing the 1995-2014 mean difference the TE module re-references on still leaves a
  **6.9e22 J rms** residual. Track C's constant-offset cancellation does not make the histories equal.
* Gated at the same time: the **7 markers share ONE history exactly** (0.000e+00 K), and the SSP
  control's history differs from theirs by up to **0.0737 K** — RCMIP vs CMIP7 inputs, by design.

---

## 2. THE PORT (`8c2657e`) — and it IS a port

`julia/scope_slr_fair_uncertainty.jl` gained `--climate=fair|magicc`. The splice, the pairing,
the two arms and every pre-existing gate are **reused verbatim**; both climate sources land in
the same (year × member) shape and nothing downstream branches on which one it got.
**Verified byte-identical**: on `--climate=fair` the cells, draws and paths files match pre-patch
HEAD exactly, with only the two new gate rows added.

⚠ **THE FILENAME CARRIES THE CLIMATE** (`_magiccclim`). Twelve consumers read these files by
explicit path; a MAGICC run must not overwrite the FaIR arm it is compared against.

**Three new gates, all mutation-tested on the real driver** (not a retyped verdict expression):

| gate | what it guards | mutation | result |
|---|---|---|---|
| `[CLIMATE-SOURCE]` | member count, member order, 1850-1900 frame | shift GMST to MAGICC's 1750 zero | caught, 3.0e-01 K vs 1e-9 |
| | | drop one member | caught |
| `[SPLICE-IDENTITY]` | the spliced arm is bit-identical to fixed while the forcings are | splice at 1980, leave the gate on 2014 | caught, 8.6e-01 cm |
| `[OHC-OFFSET]` | `31f` §6.4's "re-verify on L21, don't inherit" | scale OHC ×1.01 instead of adding | test SEES it, 0.305 cm ⇒ the null has power |

⚠ **`[SPLICE-IDENTITY]`'s reach comes from a mechanism I had written down WRONG**, found by M3:
`ladrillo_series` re-references to 1995-2014, so a mutant changing forcing inside that window
moved the arms apart at **1850**, not 1981. The derived horizon (1998, from the GIS shape window)
is conservative; the **measured** first divergence is **2015**, one year past the splice, and is
printed beside it so the conservatism stays visible.

---

## 3. ⭐ THE RESULT — the gap is MODULE or CLIMATE depending on the component

24 runs, posterior/tap/draws/modules held fixed, only the climate swapped.
`python/scope_ladrillo_on_magicc_climate.py` → `outputs/scope_ladrillo_on_magicc_climate.csv`.
All gates pass on all runs; **LWS moves exactly 0.00** under every swap (the prescribed-component
check, `[LWS-ZERO]`).

| component | CLIMATE | BOTH | MODULE | OPPOSED | OVERSHOOT | AGREE |
|---|---|---|---|---|---|---|
| **te** | **24** | 0 | 0 | 0 | 4 | 2 |
| **ais** | 2 | 7 | **17** | 2 | 0 | 2 |
| **gis** | 1 | 3 | 10 | **10** | 2 | 4 |
| glaciers | 2 | 3 | **13** | 10 | 1 | 1 |
| total | 1 | 1 | 3 | 4 | **13** | 8 |

* **TE is the climate, essentially entirely** — 28 of 30 cells; module residual < 5 cm everywhere.
* **AIS is not.** ssp585/2300 gap **445.7 cm**, climate accounts for **29.4 = 7 %**. Antarctica is
  where the two models genuinely differ, and it never was the climate.
* **GIS is OPPOSED** — the swap moves Greenland the *wrong way*, so the module gap is **larger**
  than the raw gap (vvLN/2300: gap +8.5, climate −1.3, module +9.8). MAGICC being colder had been
  partly **masking** the Greenland disagreement.
* ⚠ **THE TOTAL AGREES BY CANCELLATION.** vvHL/2300: total gap **6.8 cm** against climate **−18.5**
  and module **+25.2**. **A comparison quoted on totals reports agreement where none exists.**
  Quote the component split — the same lesson the HL-vs-H path dependence already carries.

**The verdict is FIVE-VALUED on purpose.** A bare share misleads: at vvVL/gis/2300 the gap is
+5.13 while the climate term is −2.83, and printing "−55 %" reads like a small climate
contribution when it is the opposite. The "no gap to explain" floor is **scaled to the arm's own
band**, not set in cm — a fixed 0.5 cm would be a third of the band at vvVL/2100 and a fortieth
at vvH/2300.

---

## 4. THE CONVENTION CHECK — it is worth ~nothing EXCEPT through AIS

Spliced minus raw, both on MAGICC's climate. The two differ only in the history, so this IS §1's
history disagreement in centimetres.

* **te, glaciers, lws: exactly 0.00 cm** everywhere. The TE reference window absorbs the OHC
  offset (`[OHC-OFFSET]` proved it cancels *on L21*, with power measured), and the glacier driver
  is spliced from observations regardless.
* **gis: ≤ 0.16 cm** outside one cell (vvH/2300, −2.17).
* **ais: all of it.** −0.2 to −1 cm typically, but **−7.9 vvM/2150, −10.4 vvM/2300, −5.9 vvH/2300,
  −42.7 ssp245/2300**. That is a **threshold crossing shifting year** — the DAIS fast-dynamics
  behaviour already documented under a pulse — not smooth propagation.

⇒ **the spliced-vs-raw choice is immaterial for three of five components and decisive for one.**
Carry the convention sensitivity on AIS numbers; no other component needs it.

---

## 5. WHAT THE ARM DOES NOT DO

**It decomposes; it does not adjudicate.** Nothing here says whose climate is right. That question
(`31f` open item 3) is now carrying an **AIS and a Greenland** conclusion as well as a glacier one,
which raises its priority rather than lowering it.

**The reverse arm is IMPOSSIBLE, not unbuilt** — MAGICC-SLR is inside MAGICC and consumes MAGICC's
own climate module. RUN / RUNNABLE / IMPOSSIBLE: this one is IMPOSSIBLE.

---

## 6. OPEN ITEM 2 IS PARTLY CLOSED (`d74d5a5`)

`python/scope_magicc_glacier_drawnset.py` reads MAGICC's glacier module out of the drawnset the
2025 run actually used.

* **Form**: a tabulated `S_eq(T)` on a shared **0.0-10.3 K** grid at 0.1 K, **15 curves**, one per
  **CMIP5 GCM tune**, plus a rate and an exponent ⇒ the **Nauels 2017** parameter family on
  CMIP5-vintage tunes. **The 2025 run is not a new-generation glacier module.**
* **Domain**: the axis **never goes negative** and `S_eq(0 K)` is a **positive 27.6-135.9 mm**
  committed loss. MAGICC's own equilibrium is undefined below pre-industrial — an **external**
  comparator for our curve going negative below `T_off`, and independent support for arguing only
  from the floored bound.
* **Does NOT settle whether MAGICC clamps** — the update law is in the closed binary.
* **Width caveat**: MAGICC's glacier band is **15 discrete tunes** (Greenland 4) against **600
  continuous** values for AIS basal melt and thermal expansion. Its glacier width is an
  inter-model spread, not a posterior width.

⚠ **TWO DRAWNSETS ON THIS MACHINE.** `MAGICC/drawnset/…-drawnset.json` is the plain AR6 one and
carries **only `SLR_EXPANSION`** — I read it first, and it would have supported the flatly wrong
claim that MAGICC samples no glacier uncertainty at all. The run loads the **`_with_slr`** variant
(`302_run-magicc-vv.py:58`), 41 SLR keys, **top level a LIST not a dict**. The `[SOURCE]` gate
discriminates on the glacier keys, not the filename.

---

## 7. OPEN ITEMS

1. **⭐ Is MAGICC's decline-phase cooling RIGHT?** (`31f` item 3, promoted.) Now load-bearing for
   TE, AIS and Greenland conclusions, not just glaciers. Needs an OBSERVATION or a LAW, not a
   model-vs-model vote.
2. **Does MAGICC clamp?** §6 narrows it to the update law in the binary. The equilibrium is
   floored at `S_eq(0 K) > 0`, so whatever regrowth it does is bounded by that.
3. **The κ/ν scope** — `31f` §2.4 says both glacier gaps live there. Not started.
4. **Should the four-model version be run?** Marcus said Ladrillo only for now. BRICK 2.0 and
   FACTS both take injected drivers and were verified drivable 2026-08-31; the TE result in
   particular would be worth checking against a second module.
5. **`INDEX_cmp.md` is 14.5 KB against a 14 KB soft budget** (hard 18). Over soft — merge when
   convenient, do not restructure yet.
6. Inherited and untouched: the phantom `wf*e` FACTS files; the `ais@2300` CONTROL exceedance;
   the hindcast driver-file mismatch; `plot_ladrillo_memo_figures.py` SystemExit on `--tag=L21`;
   `scope_ladrillo_vs_brick20_scorecard.py` has no L21 run; `plot_ssps_gsic_wr_vs_mengel.py`
   still carries the extA108 arms.

---

## 8. NON-OBVIOUS STATE

* **The MAGICC wide CSVs are 121 MB and UNTRACKED**, at
  `FaIRtoFrEDI/magicc_comparison/processed/vv_wide_20260831/`. `build_magicc_wide_vv.py` rebuilds
  them in ~2 min from the source whose **sha256 is in the tracked `PROVENANCE.md`**. GMST is K rel
  1850-1900; **OHC is ZJ and the consumer owes ×0.1** — the driver applies it.
* ⚠ **ssp126 and ssp245 must run at `500` draws/chain, everything else at `2000`.** Their shipped
  FaIR comparator carries 2000 draws where the markers and ssp585 carry 8000. `[ARM-MATCH]`
  derives the expectation from each comparator's own file; a first version hardcoded 8000 and
  fired immediately.
* **A run is ~330 s** (~270 s at 500/chain). 10 cores; 3 concurrent is comfortable.
  **Torch verdict: not worth it** — the blocker is SUBSTRATE (Julia depot, MimiBRICK, the four
  L21 chains, the 121 MB of wide CSVs) for a run measured in tens of minutes.
* ⚠ **macOS ships bash 3.2 — `wait -n` does not exist and `pgrep -fc` is not a valid flag.** The
  first queue script used `wait -n`, errored, and launched all 20 runs at once (killed before
  damage); the second used `pgrep -fc`, errored, and ran 4 concurrently instead of 2 (harmless).
  Poll with `pgrep -f … | wc -l` and check it.
* Memories written/updated: `ladrillo_on_magicc_climate` (new), `magicc_glacier_drawnset` (new),
  `magicc_colder_than_fair_2300` (**amended** — the history half, and its `description:` refreshed),
  `INDEX_cmp.md` pointers.
