#!/bin/bash
# Compress one MCMC chain CSV to <name>.csv.gz and verify the round trip byte for byte.
# The original .csv is left in place; removing it is a separate step that reads this script's log.
# Usage: compress_chain_verified.sh <mcmc_dir> <chain_file_basename>
# Prints one TSV line: STATUS  file  md5(original)  bytes(original)  bytes(gz)
set -u
M="${1:?mcmc dir}"; f="${2:?chain file}"
src="$M/$f"; gz="$src.gz"; tmp="$gz.partial"

if [ ! -f "$src" ]; then printf 'MISSING\t%s\n' "$f"; exit 0; fi
if [ -e "$gz" ]; then printf 'GZ_EXISTS\t%s\n' "$f"; exit 0; fi

if ! gzip -6 -c "$src" > "$tmp"; then rm -f "$tmp"; printf 'FAIL_COMPRESS\t%s\n' "$f"; exit 0; fi
if ! gzip -t "$tmp"; then rm -f "$tmp"; printf 'FAIL_GZIP_TEST\t%s\n' "$f"; exit 0; fi

h_src=$(md5 -q "$src")
h_rt=$(gzip -dc "$tmp" | md5 -q)
s_src=$(stat -f %z "$src")
if [ "$h_src" != "$h_rt" ]; then
  rm -f "$tmp"; printf 'MISMATCH\t%s\t%s\t%s\n' "$f" "$h_src" "$h_rt"; exit 0
fi

mv "$tmp" "$gz"
touch -r "$src" "$gz"    # keep the chain's original mtime on the .gz
printf 'OK\t%s\t%s\t%s\t%s\n' "$f" "$h_src" "$s_src" "$(stat -f %z "$gz")"
