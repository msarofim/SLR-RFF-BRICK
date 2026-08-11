# Gate 3.1 — component-vs-total target conflict, decomposed

All series relative to 1995-2005. Positive residual = the component budget carries MORE sea level than the independent total target.

## Exact decomposition by window (cm)

| window | Sigma comps | total | residual | = closure | + reconstruction | closure z (vs F ens) | recon z (vs Dang SE) |
|---|---|---|---|---|---|---|---|
| 1900-1930 | -12.455 | -12.202 | -0.253 | +0.260 | -0.513 | -0.01 | -0.23 |
| 1950-1980 | -3.878 | -4.616 | +0.738 | +1.109 | -0.371 | +0.01 | -0.24 |
| 1942-1982 | -4.269 | -4.982 | +0.713 | +1.163 | -0.450 | +0.01 | -0.28 |
| 1993-2018 | +1.777 | +1.723 | +0.054 | +0.086 | -0.031 | -0.02 | -0.04 |

## Frederikse's own budget closure (ensemble, window means)

| window | our closure | ensemble median | ensemble 5-95% | ensemble sd |
|---|---|---|---|---|
| 1900-1930 | +0.260 | +0.277 | [-2.698, +3.082] | 1.763 |
| 1950-1980 | +1.109 | +1.104 | [-0.188, +2.452] | 0.792 |
| 1942-1982 | +1.163 | +1.154 | [-0.198, +2.590] | 0.836 |
| 1993-2018 | +0.086 | +0.089 | [-0.244, +0.409] | 0.195 |

## Component target sigma over 1950-1980 (what could absorb a Greenland change)

| component | mean (cm) | sigma (cm) | share of summed sigma |
|---|---|---|---|
| ais | -0.281 | 0.133 | 10.0% |
| gsic | -1.729 | 0.438 | 32.8% |
| gis | -0.724 | 0.154 | 11.5% |
| steric | -2.059 | 0.255 | 19.1% |
| lws | +0.915 | 0.356 | 26.6% |

## Provenance checks

- earliest spliced (modern-product) year in any component: 2019; reaches the 1950-1980 window: **False**
- Dangendorf total target finite throughout 1950-1980: **True** (so the total is the reconstruction, not the STAR splice)
