"""10-01: new comments for items only Marcus can settle."""
import sys
sys.path.insert(0, "/private/tmp/claude-501/-Users-MarcusMarcus-Documents-2026-CodeProjects-FaIRtoFrEDI/e88c7db1-5ed3-4ee0-bbf2-08bb6c77ecb6/scratchpad/v1001")
from comments_lib import comment
comment("Tessa Moeller",
        "Two checks: (1) the reference list spells her name Möller (Nauels et al., 2025, 2026); (2) Copernicus asks for the "
        "grant number in Financial support ('…supported by the Wellcome Trust (grant no. …)'), if there is one.")
comment("Component hindcasts against the observations, 1900–2026",
        "The Antarctic, Greenland and thermal-expansion observations end in 2025 (the L27 target is empty for 2026; GRACE "
        "2026 has under six months), glaciers in 2023 and the total in 2024. The model runs to 2026, so '1900–2026' and "
        "Table 4's '1993–2026' are run windows rather than observation windows. Worth a word, or relabel to 2025.")
comment("gives 112 cm",
        "No output file behind the 112 cm (CHANGELOG 09-12c only); the 47 cm is likewise from FACTS's own runs with no "
        "committed table. Either regenerate a receipt or soften to 'roughly double'.")
comment("about a 110-year relaxation timescale",
        "109 yr (62–191) and 289 yr (142–663) are posterior quantities at T̄ = 1.963 K recorded only in CHANGELOG (09-29); "
        "no committed output file. Fine to quote, but a small diagnostic CSV would make them reproducible.")
