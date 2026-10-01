"""10-01f edit set O (Marcus 10-01: "build the test"): Sect. 3.3's disclosed gap is closed.

julia/test_ladrillo_reverts_to_brick20.jl (suite step 12): Ladrillo's own build (ladrillo_setup) with the
glacier slot put back to MimiBRICK's component and Greenland built :stock, given a BRICK 2.0 posterior draw
through the BRICK 2.0 arm's updater, EQUALS stock MimiBRICK.get_model (as scope_slr_fairunc_oldbrick.jl
builds it) bit for bit: every component and the global sum, 20 draws x {ssp245, ssp585}, 1850-2300.
Mutation-tested (a one-ulp te_alpha change, the land-water frame fix on one side, the glacier slot left
in place: all detected). The suite is now twelve steps (11 = the land-water frame guard, 12 = this).
Base: Marcus's own save of 10-01e (he was accepting changes in Word), never the build output.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import edlib
from edlib import edit

d = edlib.open_doc(sys.argv[1] + "/word/document.xml")
edit("covered by a ten-step test suite", "ten-step", "twelve-step", "suite now has 12 steps")
edit("The suite does not run the complete model with the new components reverted against BRICK 2.0.",
     "The suite does not run the complete model with the new components reverted against BRICK 2.0.",
     "Finally, the complete model is checked against BRICK 2.0: with the glacier and Greenland components"
     " swapped back to MimiBRICK's and a BRICK 2.0 posterior draw applied, Ladrillo's build reproduces"
     " BRICK 2.0 bit for bit in every component and in the total (20 draws, SSP2-4.5 and SSP5-8.5,"
     " 1850–2300), so replacing components leaves the shared Antarctic, thermal-expansion, land-water and"
     " global-sum code and its wiring unchanged.",
     "the reverted-model test now exists and passes (Marcus 10-01)")
d.save()
for c, ch, w in d.log:
    print(f"- {c[:50]!r}: {ch[:110]}  [{w}]")
print(f"{len(d.log)} edits")
