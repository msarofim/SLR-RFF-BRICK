"""
cube_to_npy.py

Convert the chunked .npz cubes (from lhs_climate_pilot.py) into flat,
uncompressed .npy files so that Julia (or any consumer) can mmap them and
work with just the slices it needs — instead of decompressing the full
30 GB compressed cube into memory.

Outputs four files in the same dir as the .npz, with the same stem:
  <stem>_gmst.npy    (n_rff, n_cfg, n_seed, n_year)  float32
  <stem>_ohc.npy     same shape, float32
  <stem>_years.npy   (n_year,)  int64
  <stem>_rffs.npy    (n_rff,)   int64

Peak memory: 1 chunk in RAM (~1.5 GB). Runs fine on a login node.

Usage:
    python python/scripts/cube_to_npy.py outputs/lhs_pilot_gmst_full_chunk_*.npz \
        --output-stem outputs/lhs_pilot_full_N2000
"""
import argparse
import glob
from pathlib import Path

import numpy as np


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inputs", nargs="+",
                    help=".npz chunk files (or globs).")
    ap.add_argument("--output-stem", required=True,
                    help="Output prefix (e.g. 'outputs/lhs_pilot_full_N2000'). "
                         "Will write <stem>_gmst.npy, <stem>_ohc.npy, "
                         "<stem>_years.npy, <stem>_rffs.npy.")
    args = ap.parse_args()

    paths = []
    for inp in args.inputs:
        m = glob.glob(inp) if "*" in inp or "?" in inp else [inp]
        paths.extend(m)
    paths = sorted(set(paths))
    print(f"Streaming {len(paths)} chunks into .npy files...")

    # PASS 1: size + shape discovery
    years_ref = None
    rffs_all  = []
    other_dims = None
    has_ohc = None
    for p in paths:
        nz = np.load(p)
        if years_ref is None:
            years_ref = nz["years"]
            other_dims = nz["gmst_traj_rff"].shape[1:]
            has_ohc = "ohc_traj_rff" in nz.files
        else:
            if not np.array_equal(years_ref, nz["years"]):
                raise ValueError(f"year mismatch in {p}")
            if nz["gmst_traj_rff"].shape[1:] != other_dims:
                raise ValueError(f"shape mismatch in {p}")
        rffs_all.append(nz["unique_rffs"])
        nz.close()

    rffs_concat = np.concatenate(rffs_all)
    total_n = len(rffs_concat)
    # Sort
    order = np.argsort(rffs_concat)
    rffs_sorted = rffs_concat[order]

    if len(set(rffs_sorted.tolist())) != total_n:
        print(f"WARNING: duplicate RFFs in chunks; will use first occurrence "
              f"({total_n} → {len(set(rffs_sorted.tolist()))} unique)")

    out_shape = (total_n,) + other_dims
    print(f"Output shape: {out_shape} (per-cube uncompressed size "
          f"{int(np.prod(out_shape) * 4 / 1e9)} GB)")

    # Map: rff_idx -> output position (sorted order)
    rff_to_pos = {int(r): i for i, r in enumerate(rffs_sorted)}

    # Open memmapped output .npy files
    stem = args.output_stem
    gmst_path  = stem + "_gmst.npy"
    ohc_path   = stem + "_ohc.npy"
    years_path = stem + "_years.npy"
    rffs_path  = stem + "_rffs.npy"

    print(f"Opening output files for writing...")
    gmst_out = np.lib.format.open_memmap(
        gmst_path, dtype=np.float32, mode="w+", shape=out_shape)
    ohc_out = None
    if has_ohc:
        ohc_out = np.lib.format.open_memmap(
            ohc_path, dtype=np.float32, mode="w+", shape=out_shape)

    # PASS 2: stream chunks into the right slots
    print("Streaming chunks into output...")
    written = set()
    for p in paths:
        nz = np.load(p)
        chunk_rffs = nz["unique_rffs"]
        chunk_gmst = nz["gmst_traj_rff"]
        chunk_ohc  = nz["ohc_traj_rff"] if has_ohc else None
        for j, r in enumerate(chunk_rffs):
            ri = int(r)
            if ri in written:
                continue
            pos = rff_to_pos[ri]
            gmst_out[pos] = chunk_gmst[j]
            if has_ohc:
                ohc_out[pos] = chunk_ohc[j]
            written.add(ri)
        nz.close()
        print(f"  {p}: done ({len(written)}/{total_n} rffs written)")

    # Flush + close memmaps
    gmst_out.flush()
    del gmst_out
    if has_ohc:
        ohc_out.flush()
        del ohc_out

    # Save metadata as plain .npy
    np.save(years_path, years_ref)
    np.save(rffs_path,  rffs_sorted)

    print(f"\nWrote:")
    print(f"  {gmst_path}")
    if has_ohc:
        print(f"  {ohc_path}")
    print(f"  {years_path}")
    print(f"  {rffs_path}")
    print(f"\nDtype info: dtype=float32, shape={out_shape}, fortran_order=False")
    print(f"            (so Julia mmap should declare Array{{Float32, 4}} "
          f"with size {out_shape})")


if __name__ == "__main__":
    main()
