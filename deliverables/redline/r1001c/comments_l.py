"""10-01c: reply on Marcus's Code-availability comment recording the MimiBRICK decision. Text is never changed here."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from comments_lib import reply

reply(0, "Decision 10-01c (Marcus): MimiBRICK goes through review as a GitHub citation, since it is the comparison "
         "model, not the code this paper describes. The citation is now pinned to tag v2.0.0, commit 11b2dff (checked "
         "against raddleverse/MimiBRICK.jl 10-01c), so the exact version is unambiguous. No request to Tony for now. "
         "Fallback if the editor or a reviewer asks for a persistent identifier: the Software Heritage ID for that "
         "commit, which needs no action from anyone. Ladrillo's own Zenodo DOI is still owed at submission.")
