"""Round r1121 edits (2026-11-21) on Marcus's save of GMD.Ladrillo.v1.2026-11-20c.clean.docx (his fast-dynamics wording
is a pending tracked insertion of his own, kept as is). Marcus 11-21 (AskUserQuestion): "Yes, all of them" = the
MAGICC/FACTS fixes from the 11-21 review + the "Sönke" typo. All edits author "Claude".

Receipts:
- MAGICC 7.5.3 ocean: CORE_OCN_NLEVELS = 50 ("number of levels of the ocean, incl. the mixed layer"), MAGCFG_DEFAULTALL.CFG
  line 109 and default_params.csv; the AR6 drawnset JSON sets no override. "40" was MAGICC6.
- MAGICC Antarctica: slr_ais_sid_parameterisation = "EDWARDS", D = k*V*(T - T0)*|T - T0| (memory
  magicc_source_ch4_ais_permafrost); negative below T0; T0 = 1.19/1.52/1.73 K for 3 of the 5 pairs, at or above
  MAGICC's ~1.2 K present-day warming (memory magicc_ais_fails_imbie_hindcast).
- LARMIP: 200-yr response functions zero-padded for the ocean-driven term; its SMB term keeps the full temperature
  integral (memory facts_post2100_module_audit).
- FACTS versions: FittedISMIP crateyear_end None (fit evaluated to 2300) at ipccar6 / v1.0.0 / v1.1.0, = 2100 from
  v1.1.1; the ipccar6-tag scripts pass --crateyear_start 2080 --crateyear_end 2100 to FittedISMIP, ar5 icesheets and
  larmip (memory facts_post2100_module_audit). Not confirmed that those scripts produced the published AR6 numbers,
  hence "run scripts tagged for AR6".
"""

EDITS = [
    ("40 layers", "40 layers", "50 layers", "MAGICC 7.5.3 ocean levels (Table 2)"),
    ("MAGICC-SLR uses a 40-layer approach", "40-layer", "50-layer", "MAGICC 7.5.3 ocean levels (Sect. 4)"),
    ("quadratic in GSAT", "quadratic in GSAT", "rate quadratic in GSAT", "MAGICC Antarctica is a rate (Table 2)"),
    ("MAGICC-SLR’s Antarctic term is quadratic in global surface air temperature, with each member assigned one of five "
     "curves fitted to",
     "Antarctic term is quadratic in global surface air temperature, with each member assigned one of five curves",
     "Antarctic discharge rate is quadratic in global surface air temperature relative to a threshold temperature, and "
     "negative below it, with each member assigned one of five (rate, threshold) pairs",
     "MAGICC Antarctica is a rate about a threshold (Sect. 4.3)"),
    ("give no weight to pre-2100 forcing by 2300", "pre-2100 forcing", "pre-2100 ocean forcing",
     "LARMIP: the SMB term keeps the full integral"),
    ("post-2100 behaviour read from its code.", "read from its code.", "read from its v1.1.4 code at default settings.",
     "FACTS version (Table 1 caption)"),
    ("and Sanke Dangendorf for updated files", "Sanke", "Sönke", "typo"),
]

INSERTS = [
    ("Workflow totals that include these modules are omitted past 2100.",
     "Workflow totals that include these modules are omitted past 2100.",
     " These descriptions apply to FACTS v1.1.4 at its default settings. The post-2100 options differ between versions "
     "and run configurations: before v1.1.1, FittedISMIP evaluated its fit through 2300 by default, and the run scripts "
     "tagged for AR6 extend the FittedISMIP, AR5 and LARMIP ice-sheet terms at their 2080–2100 rates. FACTS projections "
     "made for AR6 or SLEIP may therefore behave differently after 2100.",
     "FACTS version caveat (Marcus 11-21)"),
    ("about half of its members gain Antarctic mass over 2002–2023, when IMBIE",
     "about half of its members gain Antarctic mass over 2002–2023",
     " (three of the five thresholds are at or above MAGICC’s present-day warming)",
     "why MAGICC members gain mass"),
]
