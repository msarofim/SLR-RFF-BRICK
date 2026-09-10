"""
provenance.py — stamp an output with everything needed to RE-RUN it.

STANDING RULE (Marcus, 2026-09-10): whenever a seed is used for an analysis it must be RECORDED
for that analysis, so the run can be reproduced FROM THE ARTIFACT and not only from the script.
A seed that lives in the driver is lost the moment the CSV is handed to someone, copied into a
document, or read a year later.

Scope agreed 2026-09-10: L24 outputs and everything produced from here on. The ~400 existing L24
files are NOT retro-stamped — that would mean re-running the whole pipeline and re-rolling every
number for a metadata change. Instead the PRODUCERS are stamped, so each output gains provenance
the next time it is legitimately regenerated.

Usage:
    from provenance import stamp
    df = stamp(df, __file__, seed=SEED, tag="L24",
               inputs={"posterior": POST, "targets": TGT}, extra="cm rel 1995-2005")
    df.to_csv(OUT, index=False)

Adds ONE column, `provenance`, identical on every row. A column is used rather than a header
comment because pandas' read_csv would choke on the latter, and because a sidecar file gets
separated from its data. Consumers select columns BY NAME, so an extra column is safe — but
check for positional reads before stamping a new producer.
"""
import os
import subprocess


def git_commit(repo=None):
    """Short commit of the tree that produced this, or 'nogit'. Never raises."""
    try:
        repo = repo or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        out = subprocess.run(["git", "-C", repo, "rev-parse", "--short", "HEAD"],
                             capture_output=True, text=True, timeout=10)
        if out.returncode != 0:
            return "nogit"
        dirty = subprocess.run(["git", "-C", repo, "status", "--porcelain"],
                               capture_output=True, text=True, timeout=10).stdout.strip()
        return out.stdout.strip() + ("-dirty" if dirty else "")
    except Exception:
        return "nogit"


def provenance_string(script, seed=None, tag=None, inputs=None, extra=None):
    """One line carrying driver, seed, tag, inputs and units. Order is stable so a diff of two
    stamped files shows what actually changed."""
    parts = [os.path.basename(script)]
    if tag:
        parts.append(f"tag {tag}")
    # ⚠ seed=0 is a legitimate seed -- test for None, not falsiness.
    parts.append(f"seed {seed}" if seed is not None else "seed n/a (no RNG in this driver)")
    for k, v in (inputs or {}).items():
        parts.append(f"{k} {os.path.basename(str(v))}")
    parts.append(f"commit {git_commit()}")
    if extra:
        parts.append(str(extra))
    return " | ".join(parts)


def stamp(df, script, seed=None, tag=None, inputs=None, extra=None, col="provenance"):
    """Return df with a constant `provenance` column. Refuses to clobber an existing one."""
    if col in df.columns:
        raise ValueError(f"{col!r} already present — refusing to overwrite an existing stamp")
    out = df.copy()
    out[col] = provenance_string(script, seed=seed, tag=tag, inputs=inputs, extra=extra)
    return out
