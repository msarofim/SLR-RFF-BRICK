#!/usr/bin/env python3
"""
diag_glambie_observational_density.py — how much OBSERVATION actually underlies
each Ladrillo glacier block, by method.

Asked by Marcus 2026-08-14 while deciding which of GlaMBIE / OGGM / GloGEM should
constrain which period. GlaMBIE is the only OBSERVATIONAL product of the three,
but it is a reconciliation of contributed estimates and its input density varies
enormously by region — so "GlaMBIE says X" is not equally strong everywhere, and
R19 is exactly where that has to be checked rather than assumed.

Counts the contributed input datasets per method in the archived GlaMBIE input
tree (data/observations/raw/glambie_data.zip), aggregated to the three blocks.

  GlaMBIE (2024) Dataset 1.0.0, WGMS, doi 10.5904/wgms-glambie-2024-07;
  paper: The GlaMBIE Team (2025), Nature, doi 10.1038/s41586-024-08545-z.

  source ~/climate-env/bin/activate
  python3 python/diag_glambie_observational_density.py
"""
import collections
import os
import zipfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ZIP = os.path.join(REPO, "data/observations/raw/glambie_data.zip")
INPUT_PREFIX = "glambie_input_"
METHODS = ("gravimetry", "altimetry", "demdiff", "glaciological", "combined")
DIR2RGI = {"1_alaska": "01", "2_western_canada_us": "02", "3_arctic_canada_north": "03",
           "4_arctic_canada_south": "04", "5_greenland_periphery": "05",
           "6_iceland": "06", "7_svalbard": "07", "8_scandinavia": "08",
           "9_russian_arctic": "09", "10_north_asia": "10", "11_central_europe": "11",
           "12_caucasus_middle_east": "12", "13_central_asia": "13",
           "14_south_asia_west": "14", "15_south_asia_east": "15",
           "16_low_latitudes": "16", "17_southern_andes": "17",
           "18_new_zealand": "18", "19_antarctic_and_subantarctic": "19"}
BLOCKS = {"R19": ["19"], "SLOWP": ["03", "09", "07", "06"],
          "FAST": ["01", "04", "17", "13", "14", "02", "15", "08", "10", "11",
                   "16", "18", "12"]}


def main():
    per_region = collections.defaultdict(collections.Counter)
    with zipfile.ZipFile(ZIP) as z:
        for n in z.namelist():
            if INPUT_PREFIX not in n or not n.endswith(".csv"):
                continue
            parts = n.split("/")
            region_dir = parts[-2]
            rgi = DIR2RGI.get(region_dir)
            if rgi is None:
                continue
            for m in METHODS:
                if f"_{m}_" in parts[-1]:
                    per_region[rgi][m] += 1
    print("GlaMBIE contributed input datasets per Ladrillo block, by method")
    print(f"  {'block':7s} {'regions':>7s} {'total':>6s} {'per-region':>11s} "
          + "".join(f"{m[:9]:>11s}" for m in METHODS))
    for b, mem in BLOCKS.items():
        t = collections.Counter()
        for r in mem:
            t.update(per_region[r])
        tot = sum(t.values())
        print(f"  {b:7s} {len(mem):7d} {tot:6d} {tot / len(mem):11.1f} "
              + "".join(f"{t[m]:11d}" for m in METHODS))
    print("\n  R19 has NO gravimetry at all: GRACE cannot separate the Antarctic")
    print("  periphery from the ice sheet. It also has a single DEM-differencing")
    print("  estimate (Hugonnet), and geodetic elevation change does not capture")
    print("  frontal ablation — the very process GloGEM and OGGM disagree about.")


if __name__ == "__main__":
    main()
