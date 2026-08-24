# MPI PAI reduction — repair and measurement

Mask recipe held fixed: sftlf >= 50.0% south of -60.0 deg; baseline 1850-1900.

## Coordinate overlap the original reduction silently used

| model         | experiment   | coord   |   n_data |   n_kept |   frac_kept |   max_abs_diff |
|:--------------|:-------------|:--------|---------:|---------:|------------:|---------------:|
| MPI-ESM1-2-LR | historical   | lat     |       96 |       56 |      0.5833 |      1.421e-14 |
| MPI-ESM1-2-LR | historical   | lon     |      192 |      192 |      1      |      0         |
| MPI-ESM1-2-LR | ssp245       | lat     |       96 |       56 |      0.5833 |      1.421e-14 |
| MPI-ESM1-2-LR | ssp245       | lon     |      192 |      192 |      1      |      0         |
| MPI-ESM1-2-LR | ssp585       | lat     |       96 |       56 |      0.5833 |      1.421e-14 |
| MPI-ESM1-2-LR | ssp585       | lon     |      192 |      192 |      1      |      0         |
| MPI-ESM1-2-HR | historical   | lat     |      192 |      120 |      0.625  |      2.842e-14 |
| MPI-ESM1-2-HR | historical   | lon     |      384 |      384 |      1      |      0         |
| MPI-ESM1-2-HR | ssp245       | lat     |      192 |      120 |      0.625  |      2.842e-14 |
| MPI-ESM1-2-HR | ssp245       | lon     |      384 |      384 |      1      |      0         |
| MPI-ESM1-2-HR | ssp585       | lat     |      192 |      120 |      0.625  |      2.842e-14 |
| MPI-ESM1-2-HR | ssp585       | lon     |      384 |      384 |      1      |      0         |

## Baseline means, K

| model         | member   | grid_label   |   glob_old |   glob_fix |   glob_glac |   glob_delta |   ais_old |   ais_fix |   ais_delta |   rows |
|:--------------|:---------|:-------------|-----------:|-----------:|------------:|-------------:|----------:|----------:|------------:|-------:|
| MPI-ESM1-2-LR | r1i1p1f1 | gn           |   279.3105 |   286.6785 |    286.6785 |       7.3681 |  237.3948 |  237.9689 |      0.5741 |    337 |
| MPI-ESM1-2-HR | r1i1p1f1 | gn           |   279.4372 |   287.0824 |    287.0824 |       7.6452 |  238.4751 |  238.3496 |     -0.1255 |    337 |
