"""10-01e: reply on Claude's land-water comment (id 10). Text is never changed here."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from comments_lib import reply

reply(10, "Clause added (10-01e), after measuring it: on all 2,000 L27 projection draws, feeding DAIS the observed "
          "series instead of the stylized one moves the Antarctic contribution by at most 0.014 cm over 1900–2025 "
          "and 0.012 cm to 2300; the hindcast misfit changes by 0.005 cm. The feedback as a whole matters more "
          "(switching it off removes 6.2 cm of Antarctic loss at 2300 under High), but the land-water choice "
          "does not. Separately, the projection code had a 1.565 cm land-water frame step in 1900 (≤0.012 cm on "
          "Antarctica); v1.0 keeps it for reproducibility and the code now refuses a model update until it is "
          "fixed (CHANGELOG 10-01f).")
