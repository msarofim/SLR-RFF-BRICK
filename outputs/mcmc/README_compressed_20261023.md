# Compressed MCMC chains (2026-10-23)

136 raw chain CSVs from superseded refits were gzipped in place to `<name>.csv.gz` to free disk space
(Marcus, 2026-10-23). 245.4 GB became 30.9 GB (7.94×). Every original's md5 and size is in
`COMPRESSED_20261023_manifest.tsv`.

## What stayed raw
- **L24, L27, L27r, L27b, L28, L32**, 4 seeds each. L27 is the paper's posterior and the projection
  drivers' default tag. L24 is still a named posterior constant in `julia/ladrillo_projection.jl`. L28 and
  L32 are the arms in the AIS decision record.
- Every chain under 100 MB (smoke, chk, GISB*, gate*). Gate and test scripts read some of them, and together
  they hold about 150 MB.

## What was compressed
L10–L23b, L25, L26 (and L26a–d), L29, L30, L31, L33, L34, the ext / extA108 / extA6eq / extB* / extC / extC1
runs, D2G / D2S / D2chk*, and the tuning chains (L10tune–L14tune, L27tune). L24DELTA0 and L24TOFF4 are L24
sensitivity variants and were compressed; the L24 production chains were not.

## How each file was verified
`scripts/compress_chain_verified.sh`: `gzip -6`, then `gzip -t`, then the md5 of the decompressed stream
compared with the md5 of the original `.csv`. The `.gz` was renamed into place only if both checks passed;
it carries the original's mtime. The check was mutation-tested before the run: a stream truncated by one
byte gave MISMATCH, and an archive with 4 overwritten bytes failed `gzip -t`. All 136 passed.

The originals were moved to `~/.Trash` with `/usr/bin/trash`, and each was confirmed there by `stat` at its
original size. They occupy disk space until the Trash is emptied.

## Using a compressed chain
The drivers find chains by name (`chain_<tag>_seed<s>_n<N>.csv`): `scope_slr_fair_uncertainty.jl`,
`scope_slr_egu_ladrillo.jl`, `postprocess_mcmc_ext.jl` and several `diag_*.jl`. Given a compressed tag they
stop with "missing chain" or "no chain files". Decompress first, keeping the archive, and check the md5:

```bash
gunzip -k outputs/mcmc/chain_L21_seed2026_n2000000.csv.gz
md5 -q outputs/mcmc/chain_L21_seed2026_n2000000.csv   # compare with the manifest
```

pandas reads the `.gz` directly (`pd.read_csv("….csv.gz")`). `postprocess_mcmc_ext.jl` selects files ending
in `.csv`, so a `.csv.gz` is never mistaken for a stray chain.
