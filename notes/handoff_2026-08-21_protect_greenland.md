# Handoff — PROTECT-Greenland lands, and it says the TAP ONSET IS TOO LATE

**Start-here for the tap.** Repo `SLR-RFF-BRICK`, branch `ladrillo-dev`.
Companion: `handoff_2026-08-21_zone_axis_closed.md` (the session's other arcs).

---

## 0. THE HEADLINE

The tap's shipped cell reproduces the physics ensemble at **2300** almost exactly
and **undershoots it at 2150 by ~38%**. That is the signature of an onset set too
LATE — right endpoint, wrong trajectory. It also **inverts** the gate question I
posed earlier in the session: the 2150 evidence does not say the high cells are
too high, it says the shipped cell is too low.

| ssp585 Greenland, cm | ours (tapped) | PROTECT x2300 (physics) |
|---|---|---|
| **2150** | shipped **28.2** (band 28.2-139.5) | p05 **43.8**  p50 **45.7**  p95 **52.5** |
| **2300** | shipped **230.3** (band 175.3-293.3) | p05 217.9  p50 **233.6**  p95 301.1 |

2300 agrees to **1.4%**. 2150 is **15.6 cm low**, below even the ensemble's p05.

**NOT ACTED ON.** No gate changed, no cell moved, admissible set still all 25.

---

## 1. WHAT THE DATA IS

`data/comparison/protect_greenland/` — PROTECT-Greenland scalar output, Goelzer
2025 (v p11), doi **10.11582/2025.lf9m2wd0**, 74.3 MB, CC-BY. Paper:
doi 10.5194/egusphere-2025-3098; the repo already cites its sibling as TC19:6887.

Fetch + verify: `bash scripts/fetch_protect_greenland.sh` (all six md5s published
in the dataset TOC and checked by the script). The tarballs and 3136 unpacked
NetCDFs are **gitignored** per the repo's large-external-data convention; the
DERIVED summary is tracked.

Why it matters: it is the **only physics-based Greenland source in this repo with
ANNUAL series past 2100**. Everything else at 2150 is an emulator
(FACTS-FittedISMIP) or structured expert judgment (bamber19); MAGICC-SLR and
emuGrIS both stop at 2100.

### THE COVERAGE CAVEAT — the headline is a 2100 result

"1472 projections, four ice sheet models" describes **2100**. Of 1568 scalar
files, **1297 stop at 2100**. Every one of the 209 runs reaching 2150+ is
**NORCE-CISM**. Past 2100 this is ONE ice sheet model under many climate forcings,
so its spread is CLIMATE-forcing spread, not ice-sheet structural spread. Do not
use its p17-p83 as a hard cut — that is tighter than the evidence warrants.

---

## 2. THREE CORRECTIONS, EACH OF WHICH MOVES THE NUMBER

`python/extract_protect_greenland.py`.

1. **Control drift removed** (ISMIP6 convention). ssp585 2150 median goes
   **25.5 -> 39.7 cm**; 2300 **56.2 -> 95.5**. Not optional. 303 runs have no
   matching `ctrl-proj` and are REPORTED AND DROPPED, never silently kept.
2. **Sign.** `sle`/`slc` DECREASE with mass loss (README flags it twice);
   contribution = `-(x - x[0])`. `slc` preferred where present.
3. **Baseline NOT invented.** Series start end-2015; this repo reports rel
   1995-2014. The dataset has no pre-2015 data, so the offset is left to the
   consumer and the output carries `basis = "rel 2015"`. Adding an unsourced ~1 cm
   would be the single-year-baselining artefact the standing conventions forbid.
   **It does not explain a 15.6 cm gap.**

---

## 3. THE FAMILY SPLIT — GET THIS RIGHT OR THE COMPARISON IS MEANINGLESS

The long ssp585 runs are two different experiments:

| family | n | 2150 med | 2300 med | 2300 p95 |
|---|---|---|---|---|
| `r2300` | 40 | 29.8 | 66.6 | 108.3 |
| `x2300` | 18 | **45.7** | **233.6** | 301.1 |

**`x2300` = forcing CONTINUED to 2300, and it is the apples-to-apples arm** for
Ladrillo's own GMST paths (which keep warming to 7.81 K). That is the repo's own
standing distinction — `diag_gis_committed_loss.py` already warns that the
stabilised arm "FLATTERS" Ladrillo.

**INDEPENDENT VALIDATION OF THE EXTRACTION:** the repo's hand-transcribed
`LIT_2300_M` ssp585 "warming" band is **(1.732, 3.127) m = 173-313 cm**, sourced
as "SSP5-8.5-ext from IPSL-CM6A-LR and CESM2-WACCM". Our x2300 extraction gives
p05 217.9 / p50 233.6 / p95 301.1 cm. Same family, same range — a number
transcribed by hand months ago reproduced from the raw NetCDFs.

---

## 4. WHAT IT MEANS FOR THE TAP

Mapping the physics 2150 range onto the admissible set's onset structure:

| onset | our 2150 gis (cm) | vs PROTECT x2300 43.8-52.5 |
|---|---|---|
| 6.5, 7.0 (**shipped**) | 28.2 | **far below p05** |
| 6.0 | 31.8 - 41.9 | still below |
| 5.5 | 45.3 - 87.7 | **low end lands IN range** |
| 5.0 | 62.7 - 139.5 | above |

The physics-consistent cells sit near **onset 5.5** — the MIDDLE of the admissible
set. The "don't move 2150" principle pushed the shipped cell to onset >= 6.5,
which now looks like it undershoots the horizon it was meant to protect.

**The 2300-agrees / 2150-undershoots pattern is diagnostic**, not noise: if the
GMST paths were badly mismatched, 2300 would not land within 1.4%.

### CAVEATS, before anyone re-cells the tap on this
* **n = 18**, ONE ice sheet model (CISM), TWO GCMs (IPSL-CM6A-LR, CESM2-WACCM).
  The narrow p05-p95 (43.8-52.5) is small-n and single-model, NOT a tight
  physical constraint.
* The x2300 GMST trajectory has **not** been checked against ours year by year.
  The 2300 agreement is suggestive, not proof of a matched forcing path. **This is
  the first thing to check** before acting.
* Re-cell = moving `GIS_TAP_CELL`, which re-opens the capacity-clamp check
  (20e §2: the clamp not binding is a property of THIS cell) and needs the whole
  set re-priced.

---

## 5. NEXT

1. **Check the x2300 GMST path against ours.** Cheap, and it gates everything
   below. `info_p11.tgz` may carry the forcing metadata.
2. **If the paths match: re-open the onset choice.** The design principle chose
   onset >= 6.5 to protect 2150; the physics says that undershoots 2150. Those
   cannot both stand.
3. **Do NOT gate the admissible set on this yet** (n=18, single model). Marcus
   2026-08-21: the looser gate stands.
4. Per-basin check is available and unused: `scalars_rm_GIS` carries IMBIE2-Rignot
   basins `[no, ne, se, sw, cw, nw]`, so **NO+NE is exactly our high basin** — a
   direct physics check on `s_high` and on the tap's basin, not just the total.

## 6. TRAPS

* **A published ensemble's headline N is not its N at your horizon.** 1472
  projections / 4 models is a 2100 statement; at 2150 it is 209 runs of one model.
* **Control drift is not a detail** — it moved the 2300 median by 70%.
* **Experiment families are not interchangeable**: r2300 vs x2300 differ by 3.5x
  at 2300. Pooling them would have produced a meaningless comparison band.
