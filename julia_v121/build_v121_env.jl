# Build the MimiBRICK v1.2.1 env for the pre-#93 pulse arm.
# v1.2.1 get_model uses ssprcp_scenario= (ssp/RCP), precip_log=false.
using Pkg
Pkg.add(PackageSpec(url="https://github.com/raddleverse/MimiBRICK.jl", rev="v1.2.1"))
Pkg.add(["ArgParse","CSV","DataFrames","Mimi","NPZ"])
Pkg.precompile()
import MimiBRICK
println("MimiBRICK pkgversion = ", pkgversion(MimiBRICK))
