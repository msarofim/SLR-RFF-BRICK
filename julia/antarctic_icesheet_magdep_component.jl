## ============================================================================
## antarctic_icesheet_magdep_component.jl — DAIS with a MAGNITUDE-DEPENDENT
##                                          fast-dynamics disintegration term
##
## VERBATIM FORK of MimiBRICK v2.0.0's `antarctic_icesheet_component.jl` (the
## `edplP` package dir, the one `julia_v2/Manifest.toml` actually resolves to).
## Every change is flagged `## MAGDEP` below -- three added parameters, three added
## reporting variables, and the fast-dynamics block itself. Every other line is
## byte-identical to the stock file, and `[FORK]` in the scope script asserts that
## the n = 0 arm still reproduces the SHIPPED projection.
##
## THE DEFECT THIS EXISTS TO PRICE. Stock DAIS's fast dynamics is a BINARY
## CONSTANT FLUX (stock lines 180-184):
##
##     if T_ant > T_crit ;  rate = -lambda * 24.78e15/57 ;  else 0
##
## Once tipped, the same flux forever — no dependence on HOW FAR above threshold,
## no rate dependence, no hysteresis. Measured on the L14 posterior, the median
## above-threshold excess is **0.391 degC at ssp245@2300 and 4.529 degC at
## ssp585@2300, a factor of 11.6**, and the stock form charges both the SAME flux.
## That is why `antarctic_temp_threshold` is rank 1 at ssp245 and rank 10 at
## ssp585 (`ais_spread_is_lambda_prior`): at ssp585 every draw tips, so WHETHER
## stops discriminating and the model has no channel left for HOW HOT.
##
## THE GENERALISED FORM.
##
##     excess = T_ant - T_crit
##     g      = clamp( (excess / ref_excess) ^ n , 0, gmax )
##     rate   = -lambda * g * 24.78e15/57      (excess > 0);  0 otherwise
##
##   * `n = 0` reproduces the stock form EXACTLY — g is set to the literal 1.0 by
##     an explicit branch, not by evaluating x^0.0, so the identity is bit-level
##     and not float-luck. This is the control arm.
##   * `ref_excess` is the excess at which lambda keeps its stock meaning. It is a
##     METHODOLOGICAL CHOICE and is deliberately NOT given a default here; the
##     scope script sets it and reports an ANCHOR ENVELOPE rather than one cell.
##   * `gmax` is reported, not silently applied: default Inf so nothing is capped
##     without saying so, and the scope script prints the realised max g.
##
## WHY THIS NEEDS NO REFIT. `ais_lambda_rests_on_lig` measured that 0.00% of draws
## cross the threshold anywhere in 1850-2024, so `disintegration_rate` is
## identically zero across the WHOLE calibration window for every n. The change is
## therefore likelihood-inert and prior-propagatable at projection time — the same
## status as `gis_amp` and the Greenland tap. `[INERT]` MEASURES that (the
## historical series must be bit-identical across arms) rather than assuming it.
##
## Swap in with `Mimi.replace!(m, :antarctic_icesheet => antarctic_icesheet_magdep)`,
## the same idiom `brick_mengel.jl` uses for the glacier and Greenland slots.
## ============================================================================
using Mimi

@defcomp antarctic_icesheet_magdep begin

    # --------------------
    # Model Parameters
    # --------------------

    seawater_freeze             = Parameter()             # Freezing temperature of seawater (°C).
    ais_ρ_ice                   = Parameter()             # Ice density (kg m⁻³).
    ais_ρ_seawater              = Parameter()             # Average seawater density (kg m⁻³).
    ais_ρ_rock                  = Parameter()             # Rock density (kg m⁻³).
    ais_sea_level₀              = Parameter()             # Initial sea level rise from Antarctic ice sheet (m).
    ais_ocean_temperature₀      = Parameter()             # Initial high-latitude ocean subsurface temperaturea (°C).
    ais_radius₀                 = Parameter()             # Initial reference ice sheet radius (m).
    ais_bedheight₀              = Parameter()             # Undisturbed bed height at the continent center (m).
    ais_slope                   = Parameter()             # Slope of the undisturbed ice sheet bed before loading.
    ais_μ                       = Parameter()             # Profile parameter for parabolic ice sheet surface, related to ice stress (m^0.5).
    ais_runoffline_snowheight₀  = Parameter()             # Height of runoff line above which precipitation accumulates as snow for 0 °C local temperatures (m).
    ais_c                       = Parameter()             # Proportionality constant for the dependency of runoff line height on local Antarctic surface temperaure (m/°C)
    ais_precipitation₀          = Parameter()             # Annual precipitation for for 0 °C local temperature (m ice equivalent yr⁻¹).
    ais_κ                       = Parameter()             # Coefficient for exponential dependency of precipitation on Antarctic temperature.
    ais_ν                       = Parameter()             # Proportionality constant relating the runoff decrease with height to precipitation.
    ais_iceflow₀                = Parameter()             # Proportionality constant for ice flow at the grounding line (m yr⁻¹).
    ais_γ                       = Parameter()             # Power for the relation of ice flow speed to water depth.
    ais_α                       = Parameter()             # Partition parameter for effect of ocean subsurface temperature on ice flux.
    ais_temperature_coefficient = Parameter()             # Linear regression coefficient relating global mean surface temperature to Antarctic mean surface temperature.
    ais_temperature_intercept   = Parameter()             # Linear regression intercept term relating global mean surface temperature to Antarctic mean surface temperature.
    ais_local_fingerprint       = Parameter()             # Mean AIS fingerprint at AIS shore.
    ocean_surface_area          = Parameter()             # Surface area of the ocean (m²).
    temperature_threshold       = Parameter()             # Trigger temperature at which fast dynamics disintegration begins to occur (°C).
    λ                           = Parameter()             # Antarctic fast dynamics disintegration rate when temperature is above trigger temperature (m yr⁻¹).
    ## MAGDEP -- the three added parameters. n = 0 recovers stock DAIS exactly.
    ais_fastdyn_exponent        = Parameter()             # n: exponent on the normalised above-threshold excess. 0 = stock binary flux.
    ais_fastdyn_ref_excess      = Parameter()             # Excess (°C) at which the magnitude factor is 1, i.e. where λ keeps its stock meaning.
    ais_fastdyn_gmax            = Parameter()             # Cap on the magnitude factor. Inf = uncapped (the default; capping is reported, never silent).
    include_ais_DSL             = Parameter{Bool}()       # Check for whether 'Δ_sea_level' represents contribution from all components including AIS (true) or all other components excluding AIS (false).
    global_surface_temperature  = Parameter(index=[time]) # Global mean surface temperature anomaly relative to pre-industrial (°C).
    antarctic_ocean_temperature = Parameter(index=[time]) # High-latitude ocean subsurface temperaturea (°C).
    global_sea_level            = Parameter(index=[time]) # Global sea level rise (m).

    # --------------------
    # Model Variables
    # --------------------

    Δ_sea_level                  = Variable(index=[time]) # rate of sea-level change from gic, gis, and te components (m/yr)
    antartic_surface_temperature = Variable(index=[time]) # Antarctic mean surface temperature ANOMALY for the previous year
    runoffline_snowheight        = Variable(index=[time]) # Height of runoff line above which precipitation accumulates as snow (m)
    precipitation                = Variable(index=[time]) # Annual precipitation (m ice)
    ais_β                        = Variable(index=[time]) # mass balance gradient  (m^0.5) (degree of change in net mass balance as a function of elevation)
    center2runoffline_distance   = Variable(index=[time]) # Distance from the continent center to where the runoff line intersects the ice sheet surface (m)
    center2sea_distance          = Variable(index=[time]) # Distance from the continent center to where the ice sheet enters the sea (m).
    ais_radius                   = Variable(index=[time]) # ice sheet radius (m)
    waterdepth                   = Variable(index=[time]) # water depth at grounding line
    ice_flux                     = Variable(index=[time]) # Total ice flux across the grounding line (m3/yr)
    ais_volume                   = Variable(index=[time]) # volume of antarctic ice sheet (m^3)
    β_total                      = Variable(index=[time]) # total rate of accumulation of mass on the Antarctic Ice Sheet (m^3/yr)
    disintegration_rate          = Variable(index=[time]) # rate of disintegration
    ## MAGDEP -- reported so the scope script can gate on the realised excess and factor.
    disintegration_excess        = Variable(index=[time]) # T_ant - T_crit, 0 when below threshold (°C)
    disintegration_factor        = Variable(index=[time]) # g, the magnitude factor actually applied (1.0 throughout when n = 0)
    disintegration_floored       = Variable(index=[time]) # 1.0 in any year the mass-conservation floor bound, else 0.0
    disintegration_volume        = Variable(index=[time]) # Volume of disintegrated ice during this time step [m SLE]
    ais_sea_level                = Variable(index=[time]) # the volume of the antarctic ice sheet in SLE equivilent (m)

    # --------------------
    # Model Equations
    # --------------------

    function run_timestep(p, v, d, t)

        # Define Δ_sea_level terms (note, Δ_sea_level initializes differently before being able to take differences from previous two periods).
        if is_first(t)
            v.Δ_sea_level[t] = 0.
        elseif t == TimestepIndex(2)
            v.Δ_sea_level[t] = p.global_sea_level[t-1]
        else
            v.Δ_sea_level[t] = p.global_sea_level[t-1] - p.global_sea_level[t-2]
        end

        # ---------------------------#
        # --- Initial Conditions --- #
        # ---------------------------#

        # Note: some initial values not required and will just be 'missing' model values.
        if is_first(t)

            # Initial distance from continent center to where the ice sheet enters the sea.
            v.center2sea_distance[t] = (p.ais_bedheight₀ - p.ais_sea_level₀) / p.ais_slope

            # Ice sheet radius.
            v.ais_radius[t] = p.ais_radius₀

            # Calculate initial ice sheet volume.
            v.ais_volume[t] = π * (1 + (p.ais_ρ_ice/(p.ais_ρ_rock - p.ais_ρ_ice))) * ((8/15) * p.ais_μ^0.5 * p.ais_radius₀^2.5 - (1/3) * p.ais_slope * p.ais_radius₀^3)

            # Check if ice sheet volume requires marine ice sheet correction term.
            if p.ais_radius₀ > v.center2sea_distance[t]
                v.ais_volume[t] = v.ais_volume[t] - (π * (p.ais_ρ_seawater/(p.ais_ρ_rock - p.ais_ρ_ice)) * ((2/3) * p.ais_slope * (p.ais_radius₀^3 - v.center2sea_distance[t]^3) - p.ais_bedheight₀ * (p.ais_radius₀^2 - v.center2sea_distance[t]^2)))
            end

            # Set initial sea level rise condition.
            v.ais_sea_level[t] = p.ais_sea_level₀

        # ----------------------------------------------#
        # --- Model Equations for All Other Periods --- #
        # ----------------------------------------------#

        else

            # Distance from continent center to where the ice sheet enters the sea.
            v.center2sea_distance[t] = (p.ais_bedheight₀ - p.global_sea_level[t-1]) / p.ais_slope

            # Calculate Antarctic surface temperature (based on previous year's global surface temperature anomaly).
            # Note: terms come from regression to predict global surface temperature anomalies from an Antarctic surface temperature reconstruction.
            v.antartic_surface_temperature[t] = (p.global_surface_temperature[t-1] - p.ais_temperature_intercept) / p.ais_temperature_coefficient

            # Calculate precipitation.
            v.precipitation[t] = exp(p.ais_precipitation₀) * exp(p.ais_κ * v.antartic_surface_temperature[t])

            # Calculate mass balance gradient.
            v.ais_β[t] = p.ais_ν * v.precipitation[t]^(0.5)

            # Height of runoff line above which precipitation accumulates as snow.
            v.runoffline_snowheight[t] = p.ais_runoffline_snowheight₀ + p.ais_c * v.antartic_surface_temperature[t]

            # Distance from the continent center to where the runoff line intersects the ice sheet surface.
            # Note, this term utilized only when Antartcic surface temperature warm enough for runoff to occur.
            v.center2runoffline_distance[t] = (v.ais_radius[t-1] - ((v.runoffline_snowheight[t] - p.ais_bedheight₀ + p.ais_slope * v.ais_radius[t-1])^2) / p.ais_μ)

            # Total rate of accumulation of mass on the Antarctic ice sheet.
            # Note: Terms with 'center2runoffline_distance' only used if runoff line height where precipitation accumulates as snow > 0.
            if v.runoffline_snowheight[t] > 0
                # Calculate additional terms separately (just for convenience).
                term1 = π * v.ais_β[t] * (v.runoffline_snowheight[t] - p.ais_bedheight₀ + p.ais_slope * v.ais_radius[t-1]) * (v.ais_radius[t-1]^2 - v.center2runoffline_distance[t]^2)
                term2 = (4 * π * v.ais_β[t] * p.ais_μ^0.5 * (v.ais_radius[t-1] - v.center2runoffline_distance[t]) ^(5/2)) / 5
                term3 = (4 * π * v.ais_β[t] * p.ais_μ^0.5 * v.ais_radius[t-1] * (v.ais_radius[t-1] - v.center2runoffline_distance[t]) ^(3/2)) / 3

                v.β_total[t] = v.precipitation[t] * π * (v.ais_radius[t-1]^2) - term1 - term2 + term3
            else
                v.β_total[t] = v.precipitation[t] * π * (v.ais_radius[t-1]^2)
            end

            # ------------------------------#
            # --- Marine Ice Sheet Case --- #
            # ------------------------------#

            # Create temporary variable reprsenting dV/dR ratio (for convenience).
            fac = π * (1 + p.ais_ρ_ice/(p.ais_ρ_rock - p.ais_ρ_ice)) * (4/3 * p.ais_μ^0.5 * v.ais_radius[t-1]^1.5 - p.ais_slope * v.ais_radius[t-1]^2)

            # Calculate model equations and adjustments when there is a marine ice sheet & grounding line.
            if (v.ais_radius[t-1] > v.center2sea_distance[t])

                # Apply adjustment term for dV/dR variable.
                fac = fac - (2 * π * (p.ais_ρ_seawater/(p.ais_ρ_rock - p.ais_ρ_ice)) * (p.ais_slope * v.ais_radius[t-1]^2 - p.ais_bedheight₀ * v.ais_radius[t-1]))

                # Water depth at grounding line (average around the ice sheet periphery over all ice streams).
                v.waterdepth[t] = p.ais_slope * v.ais_radius[t-1] - p.ais_bedheight₀ + p.global_sea_level[t-1]

                # Create temporary variable for ice speed at grounding line.
                speed = (p.ais_iceflow₀ * ((1 - p.ais_α) + p.ais_α * ((p.antarctic_ocean_temperature[t-1] - p.seawater_freeze)/(p.ais_ocean_temperature₀ - p.seawater_freeze))^2) * (v.waterdepth[t]^p.ais_γ) / ((p.ais_slope * p.ais_radius₀ - p.ais_bedheight₀) ^(p.ais_γ - 1)))

                # Total ice flux across the grounding line.
                v.ice_flux[t] = -(2 * π * v.ais_radius[t-1] * (p.ais_ρ_seawater/p.ais_ρ_ice) * v.waterdepth[t]) * speed

                # Create temporary variable for convenience (c_iso is ratio ISO / Δ_sea_level).
                c_iso = (2 * π * (p.ais_ρ_seawater/(p.ais_ρ_rock - p.ais_ρ_ice)) * (p.ais_slope * v.center2sea_distance[t]^2 - (p.ais_bedheight₀ / p.ais_slope) * v.center2sea_distance[t]))

                # Additional temporary variable requiring a check for whether sea level rise also includes Antarctic ice sheet contribution (or just contributions from other BRICK components).
                if p.include_ais_DSL
                    ISO = c_iso * v.Δ_sea_level[t]
                else
                    ISO = ((1-c_iso)/c_iso) * (v.Δ_sea_level[t] - p.ais_local_fingerprint * (v.β_total[t] - v.ice_flux[t]) / p.ocean_surface_area)
                end

            # Set terms for case without a marine ice sheet & grounding line.
            else
                v.waterdepth[t] = NaN
                v.ice_flux[t]   = 0.0
                ISO             = 0.0
            end

            # ------------------------------------------#
            # --- Antarctic Ice Sheet Fast Dynamics --- #
            # ------------------------------------------#

            # If local temperature above critical temperature, ice sheets disintegrate more rapidly.
            ## MAGDEP -- generalised from the stock binary flux. The `n == 0` branch
            ## returns the LITERAL 1.0 so the control arm is bit-identical to stock
            ## rather than relying on x^0.0; `[IDENT]` in the scope script checks it.
            v.disintegration_excess[t] = max(v.antartic_surface_temperature[t] - p.temperature_threshold, 0.0)
            if v.antartic_surface_temperature[t] > p.temperature_threshold
                v.disintegration_factor[t] = p.ais_fastdyn_exponent == 0.0 ? 1.0 :
                    min((v.disintegration_excess[t] / p.ais_fastdyn_ref_excess) ^ p.ais_fastdyn_exponent,
                        p.ais_fastdyn_gmax)
                ## MAGDEP mass floor. Stock DAIS has NO floor on disintegration -- it
                ## never needs one, because a binary flux is too small to reach the
                ## bottom. A magnitude-dependent flux does: at n = 2 with an
                ## un-anchored reference the sheet is exhausted, `ais_volume` goes
                ## negative and the cone geometry inverts (stock line
                ## `v.ais_radius[t-1]^1.5` throws a DomainError). This caps the term
                ## at the ice actually remaining, which is CONSERVATION, not tuning.
                ## `disintegration_floor_hits` counts the bindings so the scope script
                ## can report them instead of the model failing silently or loudly.
                want = p.λ * v.disintegration_factor[t] * 24.78e15 / 57.0
                avail = max(v.ais_volume[t-1], 0.0)
                v.disintegration_floored[t] = want > avail ? 1.0 : 0.0
                v.disintegration_rate[t] = -min(want, avail)
            else
                v.disintegration_factor[t] = 0.0
                v.disintegration_floored[t] = 0.0
                v.disintegration_rate[t] = 0.0
            end

            # Calculate total disintegration
            v.disintegration_volume[t] = -v.disintegration_rate[t] * 57.0 / 24.78e15

            # ---------------------------------------------------#
            # --- Antarctic Ice Sheet Sea Level Contribution --- #
            # ---------------------------------------------------#

            # Calculate ice sheet radius.
            v.ais_radius[t] = v.ais_radius[t-1] + (v.β_total[t] + v.ice_flux[t] + ISO + v.disintegration_rate[t]) / fac

            # Calculate ice sheet volume (accounting for potential rapid disintegration).
            v.ais_volume[t] = v.ais_volume[t-1] + v.β_total[t] + v.ice_flux[t] + ISO + v.disintegration_rate[t]

            # Calculate sea level contribution (assuming steady state present day volume corresponding to 57 mSLE).
            v.ais_sea_level[t] = 57.0 * (1 - v.ais_volume[t] / v.ais_volume[TimestepIndex(1)])
        end
    end
end
