# Proposed edits — one departure from BRICK's philosophy, not two (2026-09-14)

Drafts for Marcus to rework; NOT applied to the .docx. Numbers from CHANGELOG 09-13j
(`outputs/diag_brick_philosophy_arms.csv`), memory `ais_amp_prior_dominated`, `amp_prior_decided_l14`,
`gis_tap_wired`. The reading: BRICK's philosophy (SLEIP §3.1, "preferentially calibrated using only
historical data products, as opposed to emulation of process-model output") is about the SEA-LEVEL
COMPONENTS. The two temperature amplifications are GMST→regional couplings — the same category as the
climate driver BRICK takes from SNEASY/DOECLIM — so the threshold channel is the only ice-sheet element
informed by a process model.

---

## 1. Introduction, second paragraph — replace the sentence beginning "However, while Ladrillo generally keeps…"

**Current:**
> However, while Ladrillo generally keeps to BRICK's design philosophy of physically based components calibrated on the historical record, it does depart from that philosophy in two places that observations cannot inform, namely a Greenland commitment above a threshold, informed by SICOPOLIS, and global-to-local temperature amplification, informed by CMIP6.

**Proposed:**
> Ladrillo keeps to BRICK's design philosophy of physically based sea-level components calibrated on the historical record, with one departure: Greenland's above-threshold discharge channel, a commitment that observations cannot inform, whose parameters are taken from ISMIP6 and SICOPOLIS. It acts only above 4.69 K of global warming and contributes nothing before 2150 on any scenario. Separately, the temperature couplings that translate global warming into regional warming — climate quantities rather than ice-sheet physics — are taken from CMIP6 where BRICK either drives Greenland with unamplified global temperature or, for Antarctica, keeps DAIS's fixed paleo-equilibrium ratio of 1.196; Ladrillo's Greenland ratio is anchored to the observed level and CMIP6 supplies only its change with warming, and its Antarctic ratio is sampled from the CMIP6 transient spread.

(Shorter alternative for the second sentence: "The global-to-regional temperature couplings are climate quantities rather than sea-level physics; where BRICK fixes them — no amplification for Greenland, DAIS's paleo-equilibrium 1.196 for Antarctica — Ladrillo takes them from CMIP6.")

## 2. Calibration section — replace "**Antarctic amplification is a key parameter.**"

**Current:**
> Stock DAIS hard-codes 1.196. Ladrillo samples it under N(1.09, 0.180), the measured CMIP6 between-model spread. The parameter is not strongly constrained by observation and its leverage is strongly scenario-dependent: across the posterior draws, a one-sigma change moves Antarctic sea level at 2300 by about 58 cm on SSP2-4.5 (roughly 23% of that scenario's total) but only about 24 cm on SSP5-8.5 (under 5%), because by SSP5-8.5 the Antarctic response is already past the thresholds where amplification matters.

**Proposed:**
> **Antarctic amplification is a key parameter, and no observation can set it.** DAIS maps global to Antarctic surface temperature through one ratio. Stock DAIS hard-codes 1.196, the inverted paleo regression — an equilibrium amplification applied to a multi-century transient. Ladrillo samples the transient ratio under N(1.09, 0.180), the CMIP6 between-model spread. The posterior returns the prior (posterior sd 0.95 of prior sd at either width tried): the parameter multiplies the temperature anomaly, so its footprint over the observed record is 0.08 °C against 0.46 °C at 2300, and a regression of the Antarctic temperature record on global temperature has a slope standard error of 0.27–0.54, wider than the CMIP6 spread. Its leverage is strongly scenario-dependent: a one-sigma change moves Antarctic sea level at 2300 by about 58 cm on SSP2-4.5 (roughly 23% of that scenario's total) but only about 24 cm on SSP5-8.5 (under 5%), because SSP5-8.5 is already past the thresholds where amplification matters. Reverting to DAIS's 1.196 on the shipped posterior adds 17 cm to the SSP2-4.5 total at 2100 and 42 cm at 2300 (9 and 19 cm on SSP5-8.5). The remaining exposure is which Antarctic temperature the ratio should describe: CMIP6 gives 0.92–0.98 for the polar cap including the Southern Ocean and 1.10–1.16 for land only, a span of 0.24 that is worth about 90 cm on SSP2-4.5 at 2300.

## 3. Consequential small edits

- **Table 1, note 4** — current: "Except two priors: Greenland's above-threshold discharge channel (SICOPOLIS) and temperature amplification (CMIP6)." Proposed: "Except the above-threshold discharge channel (ISMIP6/SICOPOLIS); the global-to-regional temperature couplings are from CMIP6." (Row stays "yes⁴".)
- **Greenland "Amplification." line** — current: "The ratio of Greenland warming to global warming is itself a function of temperature." Proposed: "The ratio of Greenland warming to global warming is anchored to its observed level (1.92) and falls with warming as CMIP6 indicates (1.50 to 1.28 over 0.75–2.75 K of global warming); holding it constant instead would raise Greenland by 1–9 cm depending on scenario and horizon."
- **"Above-threshold discharge channel." paragraph** — could add one sentence after "It is included in every projection here…": "Without it, Greenland's SSP5-8.5 to SSP2-4.5 ratio at 2300 is 2.7, against 7.9–31.9 across the process-model literature."

## Receipts
- Arms: `python/diag_brick_philosophy_arms.py` (projection-only; the AIS number is an override, corroborated by the refit slope 386 cm/unit, memory `amp_prior_mu_was_dropped`).
- Identifiability: memory `ais_amp_prior_dominated` (`notes/scoping_2026-09-01_ais_identifiability.md`).
- Frames: memory `amp_prior_decided_l14` (cap60 0.92/0.98; land secant 1.095/1.097; land PAI1 1.13/1.16).
- Ratio 2.7 vs 7.9–31.9: memory `gis_tap_wired`.
