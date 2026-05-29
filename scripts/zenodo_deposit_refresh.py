#!/usr/bin/env python3
"""
zenodo_deposit_refresh.py
=========================

Create a NEW VERSION of the SLR-RFF-BRICK intermediate-data Zenodo deposit
(concept DOI 10.5281/zenodo.20312325) and upload a curated file set via the
Zenodo REST API.

Design / safety:
  * Curation is decoupled from upload: you populate a STAGING DIR with exactly
    the files you want in the new version; this script uploads everything in it.
    (Build the staging dir with `--build-staging`, which copies the v5 manifest
    files listed in V5_MANIFEST below + rsyncs Torch-resident cubes.)
  * The new draft inherits the previous version's files; with --replace-files
    we delete those inherited files first so the new version contains ONLY the
    staged set. Without it, staged files are added/overwrite by name.
  * The script STOPS AT THE DRAFT STAGE and prints the draft URL. It does NOT
    publish unless you pass --publish (publishing is irreversible on Zenodo).
  * --dry-run does only GETs and prints the planned actions; no writes.

Token: read from --token-file (default ~/.zenodo_token) or $ZENODO_TOKEN.
Never commit the token; ~/.zenodo_token is outside the repo.

Usage:
  # 0. (one-time) populate the staging dir
  python scripts/zenodo_deposit_refresh.py --build-staging
  # 1. dry run — verify the plan (GET-only)
  python scripts/zenodo_deposit_refresh.py --dry-run
  # 2. real run — creates draft, uploads, sets metadata, STOPS at draft
  python scripts/zenodo_deposit_refresh.py --replace-files
  # 3. after reviewing the draft on zenodo.org, publish (either via the web
  #    'Publish' button, or:)
  python scripts/zenodo_deposit_refresh.py --publish-existing <draft_id>
"""
from __future__ import annotations
import argparse, json, os, shutil, subprocess, sys
from pathlib import Path

import requests  # pip install requests (in ~/climate-env)

ZENODO_BASE = "https://zenodo.org/api"
CONCEPT_RECORD_ID = "20312325"          # latest published version's record id
ROOT = Path(__file__).resolve().parents[1]
STAGING = ROOT / "outputs" / "_zenodo_staging_v5"
FAI_CUBES = Path.home() / "Documents/2026/CodeProjects/FaIRtoFrEDI/fair_outputs/cubes_v145"
TORCH = "torch:/scratch/ms17839"

# --- v5 manifest: (source_path_or_torch, dest_filename) --------------------
# Local files that back the FINAL Group-Sobol substack + poster figures, plus
# the prior v2.0 selection still relevant. Adjust freely before --build-staging.
V5_MANIFEST_LOCAL = [
    # LHS-10k_s noise-isolated ensemble — drives the Group-Sobol H-S figures
    (FAI_CUBES / "cube_v145_lhs10ks_baseline_flat2015.npz", None),
    (FAI_CUBES / "cube_v145_lhs10ks_pulse_co2_pos_001gt_flat2015.npz", None),
    (ROOT / "outputs/brick_v145_slim/brick_lhs10ks_baseline_to2300_weighted.csv", None),
    (ROOT / "outputs/brick_v145_slim/brick_lhs10ks_pulse_co2_pos_001gt_to2300.csv", None),
    # Prior v2.0 LHS-10k + ANOVA-18k slim CSVs (already local)
    (ROOT / "outputs/brick_v145_slim/brick_lhs10k_baseline_to2300_weighted.csv", None),
    (ROOT / "outputs/brick_v145_slim/brick_lhs10k_pulse_co2_pos_001gt_to2300.csv", None),
    (ROOT / "outputs/brick_v145_slim/brick_lhs10k_pulse_co2_pos_1gt_to2300.csv", None),
    (ROOT / "outputs/brick_v145_slim/brick_lhs10k_pulse_ch4_pos_001tg_to2300.csv", None),
    (ROOT / "outputs/brick_v145_slim/brick_anova18k_baseline_to2300_weighted.csv", None),
    (ROOT / "outputs/brick_v145_slim/brick_anova18k_pulse_co2_pos_1gt_to2300.csv", None),
    (ROOT / "outputs/brick_v145_slim/brick_anova18k_marginal_co2_pos_1gt_to2300_weighted.csv", None),
    # 324k ANOVA validator design metadata (raw 2.8 GB BRICK output is excluded
    # — regenerable from this metadata + the BRICK driver)
    (ROOT / "outputs/anova324k_brick_metadata.csv", None),
    (ROOT / "outputs/anova324k_fair_metadata.csv", None),
]
# Files to rsync down from Torch before staging (older cubes referenced by
# download_data.sh). Comment out if not wanted in this version.
V5_MANIFEST_TORCH = [
    f"{TORCH}/FaIRtoFrEDI/fair_outputs/cubes_v145/cube_v145_lhs10k_*.npz",
    f"{TORCH}/FaIRtoFrEDI/fair_outputs/cubes_v145/cube_v145_anova18k_*.npz",
]

METADATA = {
    "metadata": {
        "upload_type": "dataset",
        "title": "SLR-RFF-BRICK intermediate data v2.1 (FaIR v1.4.5 + post-PR#93 BRICK; LHS-10k_s + Group-Sobol)",
        "version": "2.1",
        "creators": [
            {"name": "Sarofim, Marcus",
             "affiliation": "NYU Marron Institute of Urban Management / Johns Hopkins EPCP"}
        ],
        "license": "cc-by-4.0",
        "description": (
            "Intermediate-data deposit v2.1 for the SLR-RFF-BRICK reproducible pipeline "
            "(github.com/msarofim/SLR-RFF-BRICK, release v2.1). Supersedes v1.0 (2025-09; "
            "v1.4.1 FaIR + pre-PR#93 BRICK). Covers the v1.4.5 FaIR-calibration update + "
            "Wong et al. 2026 post-PR#93 BRICK posterior. Adds the LHS-10k_s noise-isolated "
            "conditional-BRICK ensemble (FaIR cubes + BRICK slim weighted CSVs) that drives "
            "the canonical Group-Sobol Hawkins-Sutton variance decomposition of total and "
            "pulse-marginal SLR, plus the prior LHS-10k and ANOVA-18k slim CSVs and the 324k "
            "balanced-factorial ANOVA design metadata used for the independent model-free "
            "cross-check. The raw 324k per-cell BRICK output (~2.8 GB) and state-level FrEDI "
            "long CSV are excluded as regenerable from the included metadata + drivers."
        ),
        "keywords": [
            "sea-level rise", "probabilistic projections", "social cost of carbon",
            "FaIR", "MimiBRICK", "RFF-SP", "Hawkins-Sutton decomposition",
            "Group-Sobol", "climate uncertainty", "AIS tipping", "v1.4.5 calibration",
        ],
        "related_identifiers": [
            {"identifier": "https://github.com/msarofim/SLR-RFF-BRICK",
             "relation": "isSupplementTo", "scheme": "url"},
            {"identifier": "10.5281/zenodo.20312325",
             "relation": "isNewVersionOf", "scheme": "doi"},
            {"identifier": "10.1038/s41586-022-05224-9",
             "relation": "isDerivedFrom", "scheme": "doi"},
            {"identifier": "10.5194/gmd-17-8569-2024",
             "relation": "isDerivedFrom", "scheme": "doi"},
            {"identifier": "10.1038/s41558-025-02457-0",
             "relation": "references", "scheme": "doi"},
        ],
    }
}


def get_token(token_file: str) -> str:
    if os.environ.get("ZENODO_TOKEN"):
        return os.environ["ZENODO_TOKEN"].strip()
    p = Path(token_file).expanduser()
    if p.exists():
        return p.read_text().strip()
    sys.exit(f"ERROR: no token in $ZENODO_TOKEN or {p}. See SETUP_ZENODO.md.")


def build_staging() -> None:
    STAGING.mkdir(parents=True, exist_ok=True)
    for pat in V5_MANIFEST_TORCH:
        print(f"[rsync] {pat}")
        subprocess.run(["rsync", "-avz", "--progress", pat, str(STAGING) + "/"],
                       check=False)
    for src, dest in V5_MANIFEST_LOCAL:
        src = Path(src)
        if not src.exists():
            print(f"  [skip - missing] {src}")
            continue
        target = STAGING / (dest or src.name)
        if not target.exists():
            shutil.copy2(src, target)
        print(f"  [staged] {target.name}  ({target.stat().st_size/1e6:.1f} MB)")
    total = sum(f.stat().st_size for f in STAGING.glob("*"))
    print(f"\nStaging dir: {STAGING}\n  {len(list(STAGING.glob('*')))} files, "
          f"{total/1e9:.2f} GB total")


def api(method, url, token, **kw):
    kw.setdefault("params", {})["access_token"] = token
    r = requests.request(method, url, **kw)
    if not r.ok:
        sys.exit(f"ERROR {r.status_code} {method} {url}\n{r.text[:500]}")
    return r.json() if r.text else {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--token-file", default="~/.zenodo_token")
    ap.add_argument("--record-id", default=CONCEPT_RECORD_ID)
    ap.add_argument("--build-staging", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--replace-files", action="store_true",
                    help="delete inherited files so the version holds ONLY the staged set")
    ap.add_argument("--publish", action="store_true", help="publish immediately (irreversible)")
    ap.add_argument("--publish-existing", metavar="DRAFT_ID",
                    help="publish an already-created draft by deposition id")
    a = ap.parse_args()

    if a.build_staging:
        build_staging(); return

    token = get_token(a.token_file)

    if a.publish_existing:
        if a.dry_run:
            print(f"[dry-run] would publish deposition {a.publish_existing}"); return
        d = api("POST", f"{ZENODO_BASE}/deposit/depositions/{a.publish_existing}/actions/publish", token)
        print(f"PUBLISHED. DOI: {d.get('doi')}  record: {d.get('links',{}).get('record_html')}")
        return

    staged = sorted(STAGING.glob("*")) if STAGING.exists() else []
    if not staged:
        sys.exit(f"No staged files in {STAGING}. Run --build-staging first.")
    print(f"Staged files ({len(staged)}):")
    for f in staged:
        print(f"  {f.name}  ({f.stat().st_size/1e6:.1f} MB)")

    # locate latest deposition + create a new version draft
    dep = api("GET", f"{ZENODO_BASE}/deposit/depositions/{a.record_id}", token)
    print(f"\nLatest deposition: {dep['id']}  (v{dep['metadata'].get('version','?')})")
    if a.dry_run:
        print("[dry-run] would: newversion -> "
              + ("delete inherited files -> " if a.replace_files else "")
              + "upload staged files -> set metadata -> STOP at draft"
              + (" -> publish" if a.publish else ""))
        return

    nv = api("POST", f"{ZENODO_BASE}/deposit/depositions/{dep['id']}/actions/newversion", token)
    draft_url = nv["links"]["latest_draft"]
    draft = api("GET", draft_url, token)
    draft_id = draft["id"]
    bucket = draft["links"]["bucket"]
    print(f"New draft: {draft_id}")

    if a.replace_files:
        for f in draft.get("files", []):
            api("DELETE", f"{ZENODO_BASE}/deposit/depositions/{draft_id}/files/{f['id']}", token)
        print(f"  deleted {len(draft.get('files', []))} inherited files")

    for f in staged:
        print(f"  uploading {f.name} ...", flush=True)
        with open(f, "rb") as fh:
            requests.put(f"{bucket}/{f.name}", data=fh,
                         params={"access_token": token}).raise_for_status()

    api("PUT", f"{ZENODO_BASE}/deposit/depositions/{draft_id}", token,
        data=json.dumps(METADATA), headers={"Content-Type": "application/json"})
    print("  metadata set")

    if a.publish:
        d = api("POST", f"{ZENODO_BASE}/deposit/depositions/{draft_id}/actions/publish", token)
        print(f"PUBLISHED. version DOI: {d.get('doi')}")
    else:
        print(f"\nDRAFT READY (not published). Review + publish at:\n  "
              f"https://zenodo.org/uploads/{draft_id}\n"
              f"Then: python scripts/zenodo_deposit_refresh.py --publish-existing {draft_id}")


if __name__ == "__main__":
    main()
