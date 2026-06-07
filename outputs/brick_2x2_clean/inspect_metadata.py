import pandas as pd

files = {
    "fixed lhs10ks_brick_metadata.csv": "/Users/MarcusMarcus/Documents/2026/CodeProjects/SLR-RFF-BRICK/outputs/lhs10ks_brick_metadata.csv",
    "buggy lhs10k_metadata_v145.csv": "/Users/MarcusMarcus/Documents/2026/CodeProjects/FaIRtoFrEDI/fair_outputs/metadata_v145/lhs10k_metadata_v145.csv",
}
for name, p in files.items():
    df = pd.read_csv(p)
    print(name)
    print("  rows:", len(df), " cols:", list(df.columns))
    if "post_idx" in df.columns:
        print("  unique post_idx:", df.post_idx.nunique(),
              " min:", df.post_idx.min(), " max:", df.post_idx.max())
    print()
