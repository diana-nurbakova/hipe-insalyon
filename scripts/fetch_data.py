"""Fetch HIPE-2026 raw data from the official GitHub repo.

Downloads:
- ``data/newspapers/v1.0/`` per-language train JSONL files (fr, de, en)
- ``data/sandbox/`` LLM-ensemble auto-annotated data ({fr,de,en}-{train,dev}.jsonl)

The master ``dataset_reference.jsonl`` (with pre-computed Wikidata + temporal
features) and ``v1_baseline_train_test_ids.csv`` are expected to already be in
``data/`` — those are not fetched here.

Usage:
    uv run python scripts/fetch_data.py
    uv run python scripts/fetch_data.py --skip-sandbox
"""

from __future__ import annotations

import argparse
import sys
import urllib.request
from pathlib import Path

REPO_RAW = "https://raw.githubusercontent.com/hipe-eval/HIPE-2026-data/main"

NEWSPAPER_FILES = [
    "data/newspapers/v1.0/HIPE-2026-v1.0-impresso-train-fr.jsonl",
    "data/newspapers/v1.0/HIPE-2026-v1.0-impresso-train-de.jsonl",
    "data/newspapers/v1.0/HIPE-2026-v1.0-impresso-train-en.jsonl",
]

SANDBOX_FILES = [
    "data/sandbox/fr-train.jsonl",
    "data/sandbox/fr-dev.jsonl",
    "data/sandbox/de-train.jsonl",
    "data/sandbox/de-dev.jsonl",
    "data/sandbox/en-train.jsonl",
    "data/sandbox/en-dev.jsonl",
    "data/sandbox/README.md",
]


def fetch(rel_path: str, project_root: Path, *, force: bool = False) -> Path:
    """Download one file, mirroring its repo path under project_root."""
    dest = project_root / rel_path
    if dest.exists() and not force:
        size = dest.stat().st_size
        print(f"  skip  {rel_path}  ({size:,} bytes, already exists)")
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    url = f"{REPO_RAW}/{rel_path}"
    print(f"  fetch {rel_path} ...", end="", flush=True)
    try:
        urllib.request.urlretrieve(url, dest)  # noqa: S310 (trusted GitHub URL)
        size = dest.stat().st_size
        print(f" ok ({size:,} bytes)")
    except Exception as exc:
        print(f" FAILED: {exc}")
        if dest.exists():
            dest.unlink()
        raise
    return dest


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--skip-newspapers", action="store_true")
    ap.add_argument("--skip-sandbox", action="store_true")
    ap.add_argument("--force", action="store_true", help="Re-download existing files")
    args = ap.parse_args()

    project_root = Path(__file__).resolve().parents[1]

    if not args.skip_newspapers:
        print(f"Newspaper files (v1.0) -> {project_root / 'data' / 'newspapers' / 'v1.0'}")
        for f in NEWSPAPER_FILES:
            fetch(f, project_root, force=args.force)

    if not args.skip_sandbox:
        print(f"\nSandbox files -> {project_root / 'data' / 'sandbox'}")
        for f in SANDBOX_FILES:
            fetch(f, project_root, force=args.force)

    print("\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
