# QUARANTINE — the 2026-08-31 L23 refit, run with the WRONG Greenland flags

## 1. What is wrong with these outputs

They were produced by

    julia/calibrate_mcmc_ext.jl 2000000 <seed> --tag=L23 --overdisperse

which OMITS the two flags L21 was calibrated with:

    --gis-ordered --gis-basins2

Recorded in `notes/memo_2026-08-23_greenland_module.md:372` and
`notes/handoff_2026-08-29_te_residual_and_the_ohc_depth_question.md:52`.

The consequence is that these chains are a DIFFERENT GREENLAND MODEL, not a
like-for-like successor to L21:

* `--gis-basins2` adds the sampled basin rate scale `gis_s_high` (two basins,
  active{SW+CW+CE+SE+NW} / high{NO+NE}, k_mid = 0). Without it the model resolves to
  the plain A+B Greenland (`:ab`), which is why
  `project_ssps_components_ladrillo.jl` died with "the tap lives in
  greenland_3basin, but this Ladrillo is :ab".
* `--gis-ordered` imposes `alpha_s <= alpha_f AND beta_s <= beta_f`, a wedge in
  (ell, w). It is **COLUMN-INVISIBLE**: it changes the likelihood and leaves the
  chain header identical, so a header diff alone can NEVER detect its absence.

The full column diff against L21 was exactly one name, `gis_s_high`. That is what
made the second flag so easy to miss, and it is the reason this README exists
rather than a one-line note.

## 2. Why this is quarantined rather than deleted

Two axes moved at once — the glacier law AND the Greenland variant — so any number
from these files confounds them. They are still a VALID run of a real model (an
`:ab` Greenland under the floored-equilibrium + bounded-regrowth glacier law) and
may be worth something later as a variant arm; they are simply not L23. Leaving
them on the canonical paths would invite exactly the silent retrieval this
directory exists to prevent.

## 3. Files here

* `chain_L23_seed{2026,2027,2028,2029}_n2000000.csv` — 4 x 2.13 GB, all rc=0,
  177-180 min, acceptance 0.236-0.238.
* `parameters_subsample_brick_mengel_L23.csv` — written on the
  accepted-on-deliverable criterion (`--accept-slr`).
* `slr_convergence_L23.csv` — SLR@2100 R-hat 1.000 / ESS 1289, @2150 1.001 / 1597.
* `adapted_cov_L23*`, `seed_diag_L23*`, and the `L23smoke` pair.

⚠ Their convergence numbers are NOT transferable to the replacement run: they
describe a different posterior. In particular do not reuse the finding that these
chains mixed better than L21's (`ais_iceflow0` R-hat 2.323 -> 1.455) as evidence
about the real L23 — that comparison is also confounded by the Greenland variant.

## 4. The canonical replacement

    julia/calibrate_mcmc_ext.jl 2000000 <seed> --tag=L23 \
        --gis-ordered --gis-basins2 --overdisperse

Verified BEFORE relaunch by a 4000-iteration smoke (`--tag=L23chk`) whose column
set is byte-identical to L21's — the check that would have caught this in three
minutes had it been run first.
