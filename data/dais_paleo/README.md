# DAISfastdyn paleo marginals — `lambda` and `Tcrit`

Extracted <stdin> 2026-08-24 from

    /Users/MarcusMarcus/.julia/packages/MimiBRICK/edplP/data/calibration_data/DAISfastdyn_calibratedParameters_gamma_29Jan2017.nc

(sha256[:16] = `0b53b45e2422563b`), the 16-parameter / 800,000-member DAIS paleo calibration ensemble
shipped with MimiBRICK and used by `MimiBRICK/src/calibration/create_log_posteriors/*.jl`
to build the Antarctic informative priors.

Two columns only — `lambda` (fast-dynamics disintegration rate) and `Tcrit`
(`temperature_threshold`) — the two fast-dynamics parameters that reach the
Ladrillo deliverable. n = 800000.

These are the EMPIRICAL marginals. `outputs/param_priors.csv` carries an
independent-Gaussian *approximation* of them, hard-truncated to a box; see
`julia/scope_ais_lambda_prior.jl` for what the approximation costs.
