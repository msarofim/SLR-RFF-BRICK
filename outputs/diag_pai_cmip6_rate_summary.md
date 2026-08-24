# Level+rate decomposition (33-model common subset for fits; SSP3-7.0 excluded as the aerosol outlier)

pai = 1.196 - (1.196 - a0)exp(-dT/Ts) - c*rate; windows 41 yr; fit/table inclusion: centre year >= 2005 (excludes the ozone-hole/aerosol era, negative Antarctic trends under non-GHG forcing), global trend >= 0.1 K/dec (ratio degenerates + ozone-recovery confound in stabilized windows), dT >= 0.6 K.

- level-only: a0=1.001, Ts=10.00, RMSE 0.247
- level+rate: a0=0.772, Ts=10.00, **c=-0.645 [-1.066, 0.040] per (K/decade)**, RMSE 0.230

Models/scenario: ssp119 13, ssp126 33, ssp245 34, ssp585 35

|   level | scenario   |      pai |   year |     rate |   n |
|--------:|:-----------|---------:|-------:|---------:|----:|
|     1   | ssp119     | 0.942084 |   2018 | 0.232745 | 132 |
|     1   | ssp126     | 1.07653  |   2014 | 0.244909 | 307 |
|     1   | ssp245     | 1.13017  |   2014 | 0.249348 | 298 |
|     1   | ssp585     | 1.01039  |   2013 | 0.267776 | 259 |
|     1.5 | ssp119     | 1.30841  |   2027 | 0.25899  |  79 |
|     1.5 | ssp126     | 1.0619   |   2029 | 0.242031 | 308 |
|     1.5 | ssp245     | 1.09572  |   2031 | 0.250018 | 370 |
|     1.5 | ssp585     | 1.12533  |   2026 | 0.341169 | 283 |
|     2   | ssp119     | 1.18616  |   2036 | 0.176018 |  46 |
|     2   | ssp126     | 1.11923  |   2041 | 0.219749 | 195 |
|     2   | ssp245     | 1.11941  |   2052 | 0.248357 | 379 |
|     2   | ssp585     | 1.14145  |   2039 | 0.413654 | 242 |
|     2.5 | ssp126     | 0.764744 |   2058 | 0.155346 | 116 |
|     2.5 | ssp245     | 1.13954  |   2058 | 0.280961 | 224 |
|     2.5 | ssp585     | 1.14069  |   2051 | 0.453415 | 210 |
|     3   | ssp245     | 1.1865   |   2067 | 0.289878 | 135 |
|     3   | ssp585     | 1.0962   |   2061 | 0.514161 | 187 |
