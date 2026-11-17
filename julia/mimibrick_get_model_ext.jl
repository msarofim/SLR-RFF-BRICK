## brick_get_model: MimiBRICK.get_model, extended past 2300 when asked.
##
## MimiBRICK.get_model reads SNEASY placeholder series that end in 2300 (MimiBRICK.jl L45-46, both the v1 and the v2.0.0
## package versions) and so cannot build a longer model. For end_year <= 2300 this calls it unchanged. Past 2300 (the
## claim-10 pulse runs to 2500, Marcus 2026-11-17) it builds to 2300, extends the time dimension and every component's
## run period, and re-sets the four time-dimensioned inputs get_model filled. Their 1850-2300 values are KEPT exactly
## as get_model set them -- including the seeded random land-water draw that BRICK 2.0's pulse driver relies on, so the
## global RNG is consumed exactly as in a 2300 build -- and only the years after 2300 are new:
##   global temperature, interior ocean heat  -> last value held (placeholders: every caller overwrites both)
##   mixed-layer ocean heat                    -> 0, as get_model sets it
##   lws_random_sample                         -> LWS_EXT_TAIL (a caller that sets LWS itself overwrites it; BRICK 2.0's
##                                                pulse driver keeps get_model's draw, so its LWS after 2300 is this
##                                                constant. LWS is identical in both arms, so no pulse difference moves)
## Checked 2026-11-17 (scratch test): on the same inputs the extended model's 1850-2300 sea level equals a 2300 build's
## bit for bit, with no missing value to 2500.
using Mimi, MimiBRICK

const MIMIBRICK_LAST_YEAR = 2300
const LWS_EXT_TAIL = 0.0003      # m/yr, the mean of get_model's own Normal(0.0003, 0.00018)

function brick_get_model(; ssprcp_scenario::String, start_year::Int, end_year::Int)
    end_year <= MIMIBRICK_LAST_YEAR &&
        return MimiBRICK.get_model(ssprcp_scenario = ssprcp_scenario, start_year = start_year, end_year = end_year)
    m = MimiBRICK.get_model(ssprcp_scenario = ssprcp_scenario, start_year = start_year, end_year = MIMIBRICK_LAST_YEAR)
    ## read the 1850-2300 values before the dimension changes
    vals(p) = collect(Float64, p.values.data)
    T   = vals(Mimi.model_param(m.md, :model_global_surface_temperature))
    OHI = vals(Mimi.model_param(m.md, :thermal_expansion, :ocean_heat_interior))
    OHM = vals(Mimi.model_param(m.md, :thermal_expansion, :ocean_heat_mixed))
    LWS = vals(Mimi.model_param(m.md, :landwater_storage, :lws_random_sample))
    n0 = MIMIBRICK_LAST_YEAR - start_year + 1
    all(length(v) == n0 for v in (T, OHI, OHM, LWS)) || error("brick_get_model: unexpected parameter length")
    set_dimension!(m, :time, start_year:end_year)
    for c in Mimi.compdefs(m.md)
        Mimi.set_first_last!(m, nameof(c); first = start_year, last = end_year)
    end
    k = end_year - MIMIBRICK_LAST_YEAR
    update_param!(m, :model_global_surface_temperature, vcat(T, fill(T[end], k)))
    update_param!(m, :thermal_expansion, :ocean_heat_interior, vcat(OHI, fill(OHI[end], k)))
    update_param!(m, :thermal_expansion, :ocean_heat_mixed, vcat(OHM, zeros(k)))
    update_param!(m, :landwater_storage, :lws_random_sample, vcat(LWS, fill(LWS_EXT_TAIL, k)))
    return m
end
