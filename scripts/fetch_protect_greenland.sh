#!/usr/bin/env bash
# Fetch the PROTECT-Greenland scalar ensemble (Goelzer 2025) and verify checksums.
#
#   Goelzer et al. 2025, "Extending the range and reach of physically-based
#   Greenland ice sheet sea-level projections", doi 10.5194/egusphere-2025-3098
#   Data: doi 10.11582/2025.lf9m2wd0 (NIRD / Sigma2 archive), CC-BY, 74.3 MB.
#
# WHY IT IS HERE: it is the only PHYSICS-BASED Greenland source in this repo that
# carries ANNUAL series past 2100. Everything else at 2150 is an emulator
# (FACTS-FittedISMIP) or expert judgment (bamber19); MAGICC-SLR and emuGrIS stop
# at 2100. See notes/handoff_2026-08-21_protect_greenland.md.
#
# READ THE COVERAGE CAVEAT in data/comparison/protect_greenland/README.md before
# using it as a constraint: the 4-model ensemble is 2100-ONLY. All 209 runs that
# reach 2150+ are NORCE-CISM.
set -euo pipefail
cd "$(dirname "$0")/.."
DEST=data/comparison/protect_greenland
ID=19bb9a66-19b6-4029-8979-3e1fc9442f6a
BASE="https://data.archive.sigma2.no/dataset/$ID/download"
mkdir -p "$DEST"
curl -fL --retry 3 "$BASE/README.txt" -o "$DEST/README.txt"
for f in IMAU.tgz NORCE.tgz IGE.tgz VUB.tgz info_p11.tgz; do
  echo "  fetching $f"
  curl -fL --retry 3 "$BASE/p11/$f" -o "$DEST/$f"
done
echo "verifying checksums (published in the dataset table of contents)"
cd "$DEST"
cat > .expected.md5 <<'MD5'
ea875381fa3a7a1af13c1abbcc5f100b  README.txt
8cd65ec390476fb72d143cc8b21e8aeb  IMAU.tgz
cf0486589637e637af5681fd038c1cd0  NORCE.tgz
cdf0ce0fbc52013a33785078b5c6389c  IGE.tgz
5f07cdac8dd4cf67d032067701924f84  VUB.tgz
04ae81cd2a6701398fa5d450eeab082b  info_p11.tgz
MD5
fail=0
while read -r want f; do
  got=$(md5 -q "$f" 2>/dev/null || md5sum "$f" | awk '{print $1}')
  if [[ "$got" == "$want" ]]; then echo "  OK   $f"; else echo "  FAIL $f"; fail=1; fi
done < .expected.md5
[[ $fail -eq 0 ]] || { echo "checksum failure — do NOT use this copy"; exit 1; }
for f in IMAU NORCE IGE VUB info_p11; do tar xzf "$f.tgz"; done
echo "unpacked. next: python3 python/extract_protect_greenland.py"
