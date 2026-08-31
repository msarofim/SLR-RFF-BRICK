# ARCHIVED frozen comparator arm — FACTS on its own internal FaIR 1.6.4

**Archived 2026-08-31.** This is the `benchmark/reference/_fixed/` arm as it stood at
`frozen_git_head e6f0e9f` (frozen 2026-08-30), preserved verbatim before a deliberate
re-freeze.

## Why it was superseded — a CONVENTION change, not a bug

Nothing here is wrong. The FACTS rows were produced from `experiments/global.coupling.<ssp>.n200`,
i.e. **FACTS driven by its OWN INTERNAL FaIR 1.6.4**. The van Vuuren arm could only be built the
other way (external climate injected through the `facts/dummy` seam), so the FACTS column
straddled two climate-driver conventions across the two scenario sets.

On 2026-08-31 Marcus asked for one machinery everywhere. The live arm now reads
`outputs/facts_components_shared_n200.csv`, from `experiments/global.shared.<key>.n200` —
**FaIR 2.2.4 calib 1.6.0 + CMIP7 injected**, the same 841-config cubes, the same 2014 splice and
1995-2014 reference as Ladrillo and BRICK 2.0, produced by the same builder / config generator /
extractor as the van Vuuren arm.

## What moved

FACTS rows only; the 60 MAGICC-SLR rows are byte-identical. 90 of 150 literature rows changed.
Workflow totals, internal-1.6.4 → injected-2.2.4-calib-1.6.0:

* **median |move| 5.8%**, largest single move −59.85 cm (ssp585 `wf3f` @2150, the DeConto21
  MICI tail, which is threshold-sensitive and so moves hardest).
* Sign is coherent with the driver: **positive at ssp126/ssp245 (+0.2 to +11.8%), negative at
  ssp585 (−0.2 to −19.3%)**.
* The emulandice `e` workflows and the process `f` workflows move by comparable amounts
  (median 5.1% vs 4.5%), which is the check that the change is a climate-driver effect and not
  specific to one module family.

## Keep this for

1. Reproducing any score computed against the pre-2026-08-31 comparator.
2. Answering "how much of a score change was the comparator moving under us?".
3. Regression-testing the `[LIT]` gate, which is the thing that made this visible at all — it
   reported 90 of 150 rows moved rather than letting the swap pass silently.

## ⚠ Do not read this as live state

The canonical frozen arm is `benchmark/reference/_fixed/`. Nothing should point here except a
postmortem.
