# Handoff — RED-TEAM the MimiBRICK PR1 (Mengel glacier option) before showing Tony

## Your job (new session)
Red-team **all the code in PR1** of the MimiBRICK fork — the upstream contribution
that will be shown to Tony Wong (raddleverse/MimiBRICK.jl). Goal: make it **more
readable, tighter, better documented, and error-free** while preserving the
invariants below. This is a pre-review polish pass; **do NOT push to raddleverse or
open the PR.** Propose + apply improvements on the `mengel-glaciers` branch (amend or
add commits), and report what you changed and why.

## Where
- Fork: `~/Documents/2026/CodeProjects/MimiBRICK.jl`, branch **`mengel-glaciers`**,
  commit **`4fdc612`** ("Add optional Mengel-2016 glacier component"). `origin`=fork
  (`msarofim/MimiBRICK.jl`), `upstream`=`raddleverse/MimiBRICK.jl`.
- Diff vs `master`: 4 files, +165/−5. See `git -C <fork> diff master`.
- Reference (the source these were ported from): `~/Documents/2026/CodeProjects/MimiBRICK-FM/`
  (`julia/glaciers_mengel_component.jl`, `julia/brick_mengel.jl`, `METHODS.md`).

## What PR1 does
Adds the temperature-dependent-equilibrium **Mengel-2016 glaciers-and-ice-caps
emulator** as an OPTIONAL alternative to the default single-reservoir
`glaciers_small_icecaps`, selectable via `glacier_model=:mengel` on `get_model`,
`create_brick_doeclim`, and `create_sneasy_brick`. Implemented with **`Mimi.replace!`**
into the `:glaciers_small_icecaps` slot (preserves slot name + name-matched I/O), so
the model bodies are untouched and only a guarded block is appended to each constructor.

Files:
- `src/components/glaciers_mengel_component.jl` — NEW component (+ `const MENGEL_GLACIER_DEFAULTS`).
- `src/MimiBRICK.jl` — include the component; `get_model` kwarg + guarded `replace!` block.
- `src/create_models/BRICK_DOECLIM.jl`, `SNEASY_BRICK.jl` — kwarg + guarded `replace!` block.

## INVARIANTS — must still hold after your changes (verify!)
1. **Default `:gsic` path byte-identical to upstream.** `create_brick_doeclim()`
   `gsic_sea_level@2020` == **0.07635871278455457** exactly. The model bodies must
   stay untouched (additions only).
2. **`:mengel` runs in all three constructors** and its glacier SLR differs from `:gsic`
   (create_brick_doeclim mengel@2020 ≈ 0.1271535233).
3. **Mengel covers glaciers AND small ice caps** (same inventory as the component it
   replaces — do not reintroduce any "mountain glaciers only" wording).
4. Bad `glacier_model` symbol errors cleanly.

## RED-TEAM CHECKLIST (prioritised — these are the things I'm least sure about)
1. **Component numerics** (`glaciers_mengel_component.jl run_timestep`):
   - It uses forward-Euler with an **implicit Δt = 1 yr** (`(target − S)/τ`, no `*dt`).
     CHECK this matches how BRICK's OTHER components integrate (esp. the default
     `glaciers_small_icecaps_component.jl`) — if they carry an explicit `dt`/`deltat`,
     the Mengel one should too, or document why annual-only is fine.
   - Temperature is read at **`[t-1]`** (previous step). Confirm this matches the
     convention the default GSIC + other BRICK components use (consistency matters for
     a clean PR; the FM version also used t-1).
   - `is_first` init splits `gic_sl0` into fast/slow by `f`. Sanity-check.
2. **DRY / tightness:** the 7-line `update_param!(... :gic_* ...)` block is **repeated
   verbatim in all 3 constructors**. Consider a small helper
   (e.g. `_apply_mengel_glacier!(m)`) to remove the triplication — a readability +
   maintainability win. (Weigh against keeping the diff flat/obvious for reviewers.)
3. **`Mimi.replace!` robustness:** confirm the reconnect-by-name semantics are correct
   and version-stable (temperature input + `gsic_sea_level` output reconnect; old
   `gsic_*` params are dropped). Is setting `:gic_*` params via the slot name
   `:glaciers_small_icecaps` (post-replace) the idiomatic Mimi pattern?
4. **`MENGEL_GLACIER_DEFAULTS`:** values `(a=0.45,b=0.52,T_lia=-0.45,f=0.5,
   tau_fast=40,tau_slow=250,sl0=0)`. Provenance comment must stay honest (these are
   FM starting-point values, NOT a tuned posterior central — don't let any comment
   overclaim a calibration). Is the component file the right home for it?
5. **Docs:** docstrings complete + consistent across the 3 constructors; the
   `glacier_model` arg documented identically; the component header accurate.
6. **Mimi `@defcomp` conventions:** parameter/variable declarations, units in comments,
   naming — compare against the upstream components for house style.
7. **Error/edge cases:** the `glacier_model in (:gsic,:mengel) || error(...)` guard is
   in all 3; any other inputs to validate? Any `replace!`-before-`run` assumptions?
8. **Consistency with the FM source** — diff `glaciers_mengel_component.jl` against
   `MimiBRICK-FM/julia/glaciers_mengel_component.jl`; flag any unintended divergence.

## SETTLED DECISIONS — do NOT relitigate (Marcus + Tony, 2026-06-21)
- Implementation = **Option B `Mimi.replace!`** into the existing slot (matches FM;
  accurate name since Mengel = glaciers + small ice caps). NOT a separate `add_comp!`.
- Kwarg on **all three** constructors (incl. `get_model`).
- `glacier_model::Symbol` with values `:gsic` (default) / `:mengel`.
- Calibration / MCMC priors / FaIR-driving / updated calibration data = **PR2**, NOT
  this PR. Keep PR1 to "construct a model with the Mengel option," default unchanged.

## VERIFY (Julia env already instantiated)
```
cd ~/Documents/2026/CodeProjects/MimiBRICK.jl
julia --project=. -e 'using MimiBRICK; md=MimiBRICK.create_brick_doeclim(); run(md);
  mm=MimiBRICK.create_brick_doeclim(glacier_model=:mengel); run(mm);
  i=findfirst(==(2020), collect(Mimi.dim_keys(md,:time)));
  @assert md[:glaciers_small_icecaps,:gsic_sea_level][i] == 0.07635871278455457;
  println("default byte-identical OK; mengel=", mm[:glaciers_small_icecaps,:gsic_sea_level][i])'
```
(Also exercise `get_model` and `create_sneasy_brick` in both modes; precompile ~5 s.)

## CONTEXT (not your job, but useful)
- Plan + FM→fork mapping + PR2 scope: `handoff_2026-06-21_mimibrick_upstream_fork.md`.
- The CH4-pulse study that preceded this is committed in FaIRtoFrEDI; unrelated to PR1.
- After your polish: Marcus reviews, then (on his go) push `mengel-glaciers` to the fork
  and open PR1 to `raddleverse/MimiBRICK.jl:master`. PR2 (full FM) gets its own red-team.
