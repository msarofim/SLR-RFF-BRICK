"""Does the HISTORY want the same melt constant c as the PROTECT arms? In the T-space
form, while L is small Theta(L)~0 so dL/dt ~ c*T and the 1900-2025 constraint reads
directly as c = dL / integral(T dt). No fitting, one division."""
import os,sys
import numpy as np, pandas as pd
REPO=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,os.path.join(REPO,"python")); os.chdir(REPO)
g=pd.read_csv("outputs/protect_r2300_forcing_gmst.csv").set_index("year")["gmst_spliced"]
tgt=pd.read_csv("outputs/recalib_targets_ext.csv").set_index("year")["gis"]
dL=float(tgt.loc[2025]-tgt.loc[1900])
T=g.loc[1900:2025].to_numpy(); I=float(np.sum(np.clip(T,0,None)))
print(f"observed GIS loss 1900-2025      {dL:.2f} cm")
print(f"integral of max(GMST,0) dt       {I:.1f} K.yr   (GMST 1900 {T[0]:+.2f} K, 2025 {T[-1]:+.2f} K)")
print(f"=> c from HISTORY                {dL/I:.4f} cm/yr/K")
print(f"   c fitted to the 5 PROTECT arms 0.0954 cm/yr/K   -> ratio {dL/I/0.0954:.2f}x")
print()
print("With a nonzero Theta(L) the history number is an UPPER bound on c (some of the")
print("drive is spent against Theta), so the two agreeing to within a factor ~2 is the")
print("relevant statement, not the exact ratio.")
