"""
download_obs.py

Fetch and locally cache observational datasets used to overlay on the
Hawkins-Sutton historical-fit figures.

Targets:
  * Berkeley Earth global land+ocean annual anomaly (1850-present)
  * NOAA STAR satellite altimetry global mean sea level (1993-present)
  * Dangendorf et al. 2024 global mean sea level reconstruction (1900-2018,
    annual; ESSD 16, 3471, https://doi.org/10.5281/zenodo.10621070).  This
    replaces the older CSIRO Recons 2015 file (1880-2013) used previously.
  * CSIRO Recons gmsl_yr_2015 (1880-2013) — kept as an optional fallback,
    fetched from a local MimiBRICK Julia depot if available.

Each dataset is written to <obs-dir>/<name>.csv with columns:
    year, value, sigma   (sigma optional / NaN if not provided)

Where 'value' uses dataset-native units:
  - GMST: degC anomaly (Berkeley Earth: rel to 1951-1980 baseline)
  - GMSL: mm (Dangendorf 2024: rel to a centred 20th-century baseline;
    NOAA STAR altimetry: rel to ~1993; CSIRO: rel to 1990).  Each source is
    stored in its native frame; plotting code re-baselines as needed.

The script is *intentionally* fault-tolerant: any one fetch can fail without
killing the others. Each output file is independent.

CLI:
    python python/download_obs.py --download --obs-dir data/observations/

Without --download, it just sanity-checks what's locally cached.
"""
import argparse
import os
import shutil
import sys
import urllib.error
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

_TORCH = Path("/scratch/ms17839/SLR-RFF-BRICK")
PROJ_DIR = _TORCH if _TORCH.exists() else Path(__file__).resolve().parents[1]

# Berkeley Earth candidate URLs. The site re-hosts these periodically; we try
# a small list. The summary file is sufficient (annual; columns include
# "annual anomaly" relative to 1951-1980).
BE_URLS = [
    # Current canonical S3 mirror (confirmed working 2026-05-14).
    "https://berkeley-earth-temperature.s3.us-west-1.amazonaws.com/Global/Land_and_Ocean_complete.txt",
    # Historical wp-content mirrors -- kept as fallback in case S3 moves.
    "https://berkeleyearth.org/wp-content/uploads/2025/05/Land_and_Ocean_summary.txt",
    "https://berkeleyearth.org/wp-content/uploads/2024/05/Land_and_Ocean_summary.txt",
    "https://berkeleyearth.org/wp-content/uploads/Land_and_Ocean_summary.txt",
    "https://berkeleyearth.org/wp-content/uploads/2025/05/Land_and_Ocean_complete.txt",
    "https://berkeleyearth.org/wp-content/uploads/2024/05/Land_and_Ocean_complete.txt",
]

# NASA satellite altimetry GMSL. Several mirrors exist; this one is the
# Goddard data product page; the file is a CSV-ish text file with two-line
# header. If this fails, the user can manually drop in a CSV with columns
# year,value,sigma (mm).
NASA_GMSL_URLS = [
    "https://podaac.jpl.nasa.gov/dataset/MERGED_TP_J1_OSTM_OST_GMSL_ASCII_V51",  # landing page; we'll degrade
    # The data product itself is gridded NetCDF. We instead try the simpler
    # Climate.gov / NOAA STAR replica which is plain text:
    "https://www.star.nesdis.noaa.gov/socd/lsa/SeaLevelRise/slr/slr_sla_gbl_free_txj1j2_90.csv",
]

# CSIRO Recons (annual global mean sea level reconstruction) -- shipped with
# MimiBRICK. Path on Torch:
CSIRO_TORCH = "/scratch/ms17839/.julia/packages/MimiBRICK/bpCAF/data/calibration_data/CSIRO_Recons_gmsl_yr_2015.csv"
# On laptop it's a different MimiBRICK depot but should live somewhere under
# the project's data/MimiBRICK/ tree.


def _http_get(url, timeout=30):
    """Fetch URL as bytes. Returns None on failure."""
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 SLR-RFF-BRICK/0.1"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as e:
        print(f"  [warn] GET {url} failed: {e}", flush=True)
        return None


def fetch_berkeley_earth(out_path: Path, download: bool) -> bool:
    """Berkeley Earth annual global L+O anomaly. Returns True on success."""
    if out_path.exists() and not download:
        print(f"  [BE] already cached at {out_path}; skipping fetch")
        return True

    if not download:
        print(f"  [BE] no cache and --download not set; skipping")
        return False

    raw_text = None
    for url in BE_URLS:
        print(f"  [BE] trying {url}")
        data = _http_get(url)
        if data is not None and len(data) > 1000:
            raw_text = data.decode("utf-8", errors="replace")
            print(f"  [BE] got {len(raw_text):,} chars")
            break
    if raw_text is None:
        print("  [BE] all URLs failed; no Berkeley Earth file written")
        return False

    # Berkeley Earth Land_and_Ocean_complete.txt format: monthly rows with
    # 12 columns:
    #   Year  Month  Monthly_Anom  Monthly_Unc  Annual_Anom  Annual_Unc
    #   FiveYear_Anom  FiveYear_Unc  TenYear_Anom  TenYear_Unc
    #   TwentyYear_Anom  TwentyYear_Unc
    # The file contains TWO sections: first uses air temperatures over sea
    # ice (recommended), second uses water temperatures below sea ice. We
    # only want the first section. Section breaks are marked by a '%' header
    # block after data has begun, so we stop on the first '%' line seen
    # after any data row.
    #
    # The "Annual_Anom" column is a 12-month centered average; taking the
    # Month==12 row gives one finalised annual value per year (and the file
    # only emits non-NaN Annual values once 6 months of context exist).
    rows = []
    seen_data = False
    for line in raw_text.splitlines():
        s = line.strip()
        if not s:
            continue
        if s.startswith("%"):
            if seen_data:
                # entering 2nd section's header block; stop here
                break
            continue
        parts = s.split()
        if len(parts) < 6:
            continue
        try:
            yr = int(float(parts[0]))
            month = int(float(parts[1]))
        except (ValueError, IndexError):
            continue
        seen_data = True
        if month != 12:
            continue
        a_anom_s, a_unc_s = parts[4], parts[5]
        if a_anom_s in ("NaN", "nan"):
            continue
        try:
            a_anom = float(a_anom_s)
            a_unc = float(a_unc_s) if a_unc_s not in ("NaN", "nan") else np.nan
        except ValueError:
            continue
        rows.append((yr, a_anom, a_unc))

    if not rows:
        print("  [BE] parsing produced 0 rows; aborting")
        return False

    annual = pd.DataFrame(rows, columns=["year", "value", "sigma"])
    annual = annual.drop_duplicates(subset="year").sort_values("year").reset_index(drop=True)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    annual.to_csv(out_path, index=False)
    print(f"  [BE] wrote {len(annual)} annual rows to {out_path} "
          f"(years {annual['year'].min()}-{annual['year'].max()})")
    return True


def fetch_nasa_gmsl(out_path: Path, download: bool) -> bool:
    """NASA / NOAA satellite altimetry GMSL. Plain-text CSV preferred."""
    if out_path.exists() and not download:
        print(f"  [GMSL] already cached at {out_path}; skipping fetch")
        return True
    if not download:
        print(f"  [GMSL] no cache and --download not set; skipping")
        return False

    # NOAA STAR canonical URLs (confirmed 2026-05-18 via LSA_SLR_timeseries.php).
    # Filename code: gbl = global; free/keep = seasonal-signals-free/kept;
    # ref_90 = referenced to the satellite-altimetry-era ~1993 baseline.
    # Prefer seasonal-free (smoother annual signal).
    for url in (
        "https://www.star.nesdis.noaa.gov/socd/lsa/SeaLevelRise/slr/slr_sla_gbl_free_ref_90.csv",
        "https://www.star.nesdis.noaa.gov/socd/lsa/SeaLevelRise/slr/slr_sla_gbl_keep_ref_90.csv",
    ):
        print(f"  [GMSL] trying {url}")
        data = _http_get(url)
        if data is not None and len(data) > 500:
            break
    if data is None or len(data) < 500:
        print("  [GMSL] no GMSL CSV could be fetched")
        return False

    text = data.decode("utf-8", errors="replace")
    # NOAA STAR header: comment lines start with 'HDR'. Then columns include
    # a decimal-year and SLA (mm). Format varies; we try to find numeric rows
    # with at least 2 fields.
    decimal_years = []
    slas = []
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("HDR") or s.startswith("#") or s.startswith("%"):
            continue
        # CSV split, then try float
        parts = [p.strip() for p in s.replace(",", " ").split()]
        if len(parts) < 2:
            continue
        try:
            dy = float(parts[0])
            sla = float(parts[1])
        except ValueError:
            continue
        if dy < 1990 or dy > 2050:
            continue
        decimal_years.append(dy)
        slas.append(sla)

    if not decimal_years:
        print("  [GMSL] parsing produced 0 rows; aborting")
        return False

    df = pd.DataFrame({"decimal_year": decimal_years, "sla_mm": slas})
    df["year"] = df["decimal_year"].astype(int)
    annual = (
        df.groupby("year")
        .agg(value=("sla_mm", "mean"), n=("sla_mm", "size"))
        .reset_index()
    )
    # Require >=6 months of data per year (high-frequency altimetry has many
    # records per month; this filter is just to drop partial first/last years)
    annual = annual[annual["n"] >= 20].drop(columns="n")
    annual["sigma"] = np.nan
    annual = annual.sort_values("year").reset_index(drop=True)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    annual[["year", "value", "sigma"]].to_csv(out_path, index=False)
    print(f"  [GMSL] wrote {len(annual)} annual rows to {out_path} "
          f"(years {annual['year'].min()}-{annual['year'].max()}; units mm)")
    return True


def fetch_csiro(out_path: Path, download: bool) -> bool:
    """CSIRO Recons gmsl_yr_2015.csv -- copy from MimiBRICK install if present."""
    if out_path.exists() and not download:
        print(f"  [CSIRO] already cached at {out_path}; skipping")
        return True

    candidates = [
        Path(CSIRO_TORCH),
        # laptop fallback paths -- MimiBRICK in the project tree
        PROJ_DIR / "data" / "MimiBRICK" / "data" / "calibration_data"
            / "CSIRO_Recons_gmsl_yr_2015.csv",
    ]
    # Also try a JULIA_DEPOT_PATH env-var driven search
    depot = os.environ.get("JULIA_DEPOT_PATH")
    if depot:
        for d in depot.split(":"):
            p = Path(d) / "packages" / "MimiBRICK"
            if p.exists():
                # Walk one level looking for the file
                for sub in p.iterdir():
                    cand = sub / "data" / "calibration_data" / "CSIRO_Recons_gmsl_yr_2015.csv"
                    if cand.exists():
                        candidates.append(cand)

    src = None
    for c in candidates:
        if c.exists():
            src = c
            break
    if src is None:
        print(f"  [CSIRO] not found in any of: "
              + ", ".join(str(c) for c in candidates))
        return False

    out_path.parent.mkdir(parents=True, exist_ok=True)
    # CSIRO file has a preamble of '#'-prefixed comment lines (some are
    # quoted, like '"# Citation: ...",,', so a simple comment='#' won't
    # catch them). Scan for the real header line and skiprows up to it.
    import io
    text = src.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    header_idx = None
    for i, line in enumerate(lines):
        if line.lower().lstrip().startswith("time,"):
            header_idx = i
            break
    if header_idx is None:
        print(f"  [CSIRO] could not find 'Time,...' header in {src}; aborting")
        return False
    try:
        raw = pd.read_csv(io.StringIO("\n".join(lines[header_idx:])))
    except Exception as e:
        print(f"  [CSIRO] failed to parse {src}: {e}; copying raw")
        shutil.copy(src, out_path)
        return True

    cols_lc = {c: c.lower().strip() for c in raw.columns}
    # find best matches
    yr_col = next((c for c, lc in cols_lc.items() if "time" in lc or "year" in lc), raw.columns[0])
    val_col = next((c for c, lc in cols_lc.items() if "gmsl" in lc and "unc" not in lc), raw.columns[1])
    sig_col = next((c for c, lc in cols_lc.items() if "unc" in lc), None)
    out = pd.DataFrame({
        "year": raw[yr_col].astype(int),
        "value": raw[val_col].astype(float),
        "sigma": raw[sig_col].astype(float) if sig_col else np.nan,
    })
    out.to_csv(out_path, index=False)
    print(f"  [CSIRO] copied + normalised to {out_path} ({len(out)} rows, "
          f"units mm rel. to 1990)")
    return True


def fetch_dangendorf(out_path: Path, download: bool) -> bool:
    """Dangendorf et al. 2024 (ESSD 16, 3471) GMSL reconstruction, 1900-2018.
    Source: Zenodo 10621070, file global_basin_timeseries.xlsx (Global sheet).
    Columns: Observed GMSL [lower / mean / upper] in mm relative to the
    paper's centred baseline."""
    if out_path.exists() and not download:
        print(f"  [Dangendorf] already cached at {out_path}; skipping")
        return True
    if not download:
        return False

    url = "https://zenodo.org/records/10621070/files/global_basin_timeseries.xlsx?download=1"
    print(f"  [Dangendorf] trying {url}")
    data = _http_get(url, timeout=60)
    if data is None or len(data) < 10000:
        print("  [Dangendorf] download failed; skipping")
        return False

    tmp_xlsx = out_path.with_suffix(".xlsx")
    tmp_xlsx.parent.mkdir(parents=True, exist_ok=True)
    tmp_xlsx.write_bytes(data)
    try:
        xl = pd.ExcelFile(tmp_xlsx, engine="openpyxl")
    except Exception as e:
        print(f"  [Dangendorf] failed to open xlsx ({e}); skipping")
        return False
    if "Global" not in xl.sheet_names:
        print(f"  [Dangendorf] no Global sheet in xlsx; sheets={xl.sheet_names}")
        return False
    raw = pd.read_excel(xl, sheet_name="Global", engine="openpyxl")
    # First column is unnamed (year), but pandas labels it 'Unnamed: 0'.
    year_col = raw.columns[0]
    out = pd.DataFrame({
        "year":        raw[year_col].astype(int),
        "value":       raw["Observed GMSL [mean]"].astype(float),
        "value_lower": raw["Observed GMSL [lower]"].astype(float),
        "value_upper": raw["Observed GMSL [upper]"].astype(float),
    })
    # Approximate symmetric sigma from the 5-95% / 17-83% bracket Dangendorf
    # reports.  Their bracket is the 90% interval, so sigma ≈ (upper-lower)/3.29.
    out["sigma"] = (out["value_upper"] - out["value_lower"]) / 3.29
    out = out.sort_values("year").reset_index(drop=True)
    out[["year", "value", "sigma", "value_lower", "value_upper"]].to_csv(
        out_path, index=False)
    tmp_xlsx.unlink(missing_ok=True)
    print(f"  [Dangendorf] wrote {len(out)} annual rows to {out_path} "
          f"(years {out['year'].min()}-{out['year'].max()}; units mm)")
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--obs-dir", type=str, default=str(PROJ_DIR / "data" / "observations"))
    ap.add_argument("--download", action="store_true",
                    help="Actually fetch from the web (else only inspect cache)")
    args = ap.parse_args()

    obs_dir = Path(args.obs_dir)
    obs_dir.mkdir(parents=True, exist_ok=True)
    print(f"=== download_obs.py === obs_dir = {obs_dir}  download = {args.download}")

    results = {}
    print("[1/4] Berkeley Earth annual GMST")
    results["berkeley_earth"] = fetch_berkeley_earth(
        obs_dir / "berkeley_earth_annual.csv", args.download)

    print("[2/4] NOAA STAR satellite altimetry GMSL")
    results["noaa_star_gmsl"] = fetch_nasa_gmsl(
        obs_dir / "nasa_gmsl_annual.csv", args.download)

    print("[3/4] Dangendorf 2024 reconstruction GMSL")
    results["dangendorf_2024"] = fetch_dangendorf(
        obs_dir / "dangendorf_2024_gmsl.csv", args.download)

    print("[4/4] CSIRO Recons GMSL (optional fallback)")
    results["csiro_fallback"] = fetch_csiro(
        obs_dir / "csiro_recons_gmsl.csv", args.download)

    print("\n=== summary ===")
    for k, ok in results.items():
        print(f"  {k:20s} : {'OK' if ok else 'MISSING'}")

    # Exit 0 always -- this script is best-effort, and the main analysis
    # should run even if some observations are missing.
    sys.exit(0)


if __name__ == "__main__":
    main()
