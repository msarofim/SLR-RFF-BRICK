# Ladrillo's own driver functions (src/model.jl: glacier_driver, greenland_driver) on one scenario's ensemble-mean FaIR
# GMST (the fixed-climate arm), at the posterior-median amplifications of the projection draws (rows 1:5:10000).
# The independent check for python/substack_glacier_blocks.py, which re-implements the same formulas in Python.
#
#   julia --project=../Ladrillo julia/substack_glacier_blocks_check.jl <scenario> <out.csv>
using Ladrillo, CSV, DataFrames, Statistics

const SCEN, OUT = ARGS[1], ARGS[2]
const ROWS = 1:5:10000
const YEARS = 1850:2300
isfile(OUT) && error("refusing to overwrite $OUT")

post = CSV.read(Ladrillo.datapath("posterior", "ladrillo_L27_posterior.csv"), DataFrame)[ROWS, :]
amp = Dict(b => median(post[!, "gic_amp_$b"]) for b in Ladrillo.GLACIER_BLOCKS)
gamp = median(post.gis_amp)
mg, mo = Ladrillo.mean_forcing(SCEN; years = YEARS)
lm = Ladrillo.LadrilloModel(mg, mo; years = YEARS)

df = DataFrame(year = collect(YEARS), gmst_rb = lm.gmst_rb)
for b in Ladrillo.GLACIER_BLOCKS
    df[!, b] = Ladrillo.glacier_driver(lm, b, amp[b])
end
df[!, "south"] = Ladrillo.greenland_driver(lm, gamp)
df[!, "provenance"] .= ""
df[1, "provenance"] = "Ladrillo $(pkgversion(Ladrillo)) glacier_driver/greenland_driver | scenario $SCEN fixed arm " *
    "(mean_forcing) | median amps over posterior rows $ROWS: " *
    join(["$b=$(round(amp[b], digits=6))" for b in Ladrillo.GLACIER_BLOCKS], " ") * " gis=$(round(gamp, digits=6))"
CSV.write(OUT, df)
println("wrote $OUT")
