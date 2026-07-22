# Level+rate decomposition (33-model common subset for fits; SSP3-7.0 excluded as the aerosol outlier)

pai = 1.196 - (1.196 - a0)exp(-dT/Ts) - c*rate; windows 41 yr; fit/table inclusion: centre year >= 2005 (excludes the ozone-hole/aerosol era, negative Antarctic trends under non-GHG forcing), global trend >= 0.1 K/dec (ratio degenerates + ozone-recovery confound in stabilized windows), dT >= 0.6 K.

- level-only: a0=0.996, Ts=10.00, RMSE 0.246
- level+rate: a0=0.767, Ts=10.00, **c=-0.643 [-1.062, 0.072] per (K/decade)**, RMSE 0.229

Models/scenario: ssp119 13, ssp126 33, ssp245 34, ssp585 35

|   level | scenario   |      pai |   year |     rate |   n |
|--------:|:-----------|---------:|-------:|---------:|----:|
|     1   | ssp119     | 0.942084 |   2018 | 0.232745 | 132 |
|     1   | ssp126     | 1.05745  |   2014 | 0.24809  | 297 |
|     1   | ssp245     | 1.08217  |   2013 | 0.253351 | 287 |
|     1   | ssp585     | 1.01043  |   2012 | 0.273657 | 252 |
|     1.5 | ssp119     | 1.30841  |   2027 | 0.25899  |  79 |
|     1.5 | ssp126     | 1.0637   |   2028 | 0.235925 | 322 |
|     1.5 | ssp245     | 1.07908  |   2030 | 0.255122 | 366 |
|     1.5 | ssp585     | 1.12128  |   2026 | 0.341169 | 283 |
|     2   | ssp119     | 1.18616  |   2036 | 0.176018 |  46 |
|     2   | ssp126     | 1.11923  |   2041 | 0.219749 | 195 |
|     2   | ssp245     | 1.12544  |   2050 | 0.249471 | 375 |
|     2   | ssp585     | 1.11689  |   2039 | 0.413343 | 243 |
|     2.5 | ssp126     | 0.764744 |   2058 | 0.155346 | 116 |
|     2.5 | ssp245     | 1.12945  |   2059 | 0.27164  | 243 |
|     2.5 | ssp585     | 1.14231  |   2051 | 0.455988 | 209 |
|     3   | ssp245     | 1.1865   |   2067 | 0.289878 | 135 |
|     3   | ssp585     | 1.09675  |   2061 | 0.517749 | 187 |
