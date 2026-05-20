# Conference Abstract — AGU Chapman SLR conference

This is the abstract that was submitted to the AGU Chapman SLR conference
for the poster delivered from this repository.

**Authors:** Marcus C. Sarofim, James E. Neumann, Megan Sheahan

---

Probabilistic coastal damage projections for arbitrary future scenarios
are important for both adaptation planning and mitigation policy. One
approach uses fully integrated models projecting from emissions through
thermal expansion and glacial melt which are then combined with local
land uplift and subsidence to spatially resolved relative sea level rise.
An alternative separates the problem into components: reduced complexity
models paired with damage functions offer a more tractable and
computationally feasible approach. This poster focuses on the latter,
using the Framework for Evaluating Damages and Impacts (FrEDI) to
translate global sea level rise estimates into state specific damage
estimates.

FrEDI is an open-sourced reduced complexity model which uses projections
of future global temperature, global sea level rise, national GDP, and
state-level population to project damages across 20+ different impacts,
based on damage functions that relate temperature or sea level rise to
specific damages. These damage functions are derived using damage modules
with a high level of spatial resolution and other details, but the high
level of aggregation involved allows FrEDI to project state-level damages
for the full century in seconds. This computational speed makes it
feasible to run FrEDI hundreds or thousands of times, which is important
for probabilistic analysis.

We use three case studies to illustrate this component-based approach:
projected mortality risk to elder populations from high tide flooding
(Sheahan et al. 2025), economic damages to coastal properties and
infrastructure (Neumann et al. 2021 and Lorie et al. 2020), and
disruption to road-based transportation due to high tide flooding
(Fant et al. 2021). The damage functions for these three studies were
developed using Sweet et al. scenarios for six spatially resolved future
scenarios, creating relationships between damage and centimeters of
global sea level rise for any given year. The damage functions can then
be used with global sea level rise projections from models such as BRICK
or FACTS that include probabilistic parameter sets, and can also be
driven with probabilistic climate parameters from a model like FaIR and
probabilistic emissions scenarios from a dataset such as the RFF-SPs.

---

## Scope of this repository relative to the abstract

The abstract describes a pipeline that runs **RFF-SP × FaIR × BRICK →
FrEDI → state-level damages**. This GitHub repository covers the
**upstream climate side** (RFF-SP × FaIR × MimiBRICK → probabilistic
GMST and GMSL, plus their Hawkins-Sutton variance decomposition and
pulse-marginal sensitivities). The **downstream FrEDI side** (translating
GMSL to state-level damages via the Sheahan/Neumann/Fant damage functions)
is run separately using EPA's open-source FrEDI tool — the integration
scripts are out of scope for this repository. The poster's Panels H, I,
and J display FrEDI-produced damage estimates that consume this
repository's GMSL projections as input.

## How to cite the poster

- **Poster artifact (tagged release):** `v1.0-poster-agu-chapman` on
  github.com/msarofim/SLR-RFF-BRICK (Zenodo DOI minted on release).
- **Companion substack post**, "Certainties and Uncertainties" (Sarofim,
  2026-05-20): <https://thesaraphreport.substack.com/p/certainties-and-uncertainties>
- **Underlying methods paper** (in preparation): TBD.
