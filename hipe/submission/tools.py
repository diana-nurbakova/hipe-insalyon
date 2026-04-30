"""Wrappers around the organizers' Python scripts.

The HIPE-2026 task ships three reference tools in
https://github.com/hipe-eval/HIPE-2026-data:

    scripts/dummy_predict.py            -- random baseline + format reference
    scripts/check_jsonlschema.py        -- schema validator
    scripts/file_scorer_evaluation.py   -- official scorer

This module shells out to those scripts (so we always run the *exact* code
the organizers run) and surfaces structured results. Configure the path to
the cloned repo via the ``HIPE2026_TOOLS_DIR`` environment variable, the
``tools_dir`` argument to each call, or by relying on the search heuristic
in :func:`default_tools_dir`.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path

DEFAULT_TOOLS_ENV = "HIPE2026_TOOLS_DIR"
DEFAULT_SUBPATH_CANDIDATES: tuple[str, ...] = (
    "HIPE-2026-data",
    "../HIPE-2026-data",
    "external/HIPE-2026-data",
    "third_party/HIPE-2026-data",
)


def default_tools_dir(start: str | Path | None = None) -> Path:
    """Locate the cloned ``HIPE-2026-data`` checkout.

    Search order:
      1. ``$HIPE2026_TOOLS_DIR`` if set.
      2. Walk up from ``start`` (default: cwd) looking for one of the known
         sibling locations.
    """
    env = os.environ.get(DEFAULT_TOOLS_ENV)
    if env:
        p = Path(env).expanduser().resolve()
        if p.exists():
            return p
        raise FileNotFoundError(
            f"{DEFAULT_TOOLS_ENV}={env!r} but path does not exist"
        )

    base = Path(start or Path.cwd()).resolve()
    for ancestor in (base, *base.parents):
        for sub in DEFAULT_SUBPATH_CANDIDATES:
            cand = (ancestor / sub).resolve()
            if (cand / "scripts" / "file_scorer_evaluation.py").exists():
                return cand
    raise FileNotFoundError(
        "Could not locate HIPE-2026-data tools dir. "
        f"Set {DEFAULT_TOOLS_ENV} or pass tools_dir= explicitly."
    )


def _resolve(tools_dir: str | Path | None) -> Path:
    if tools_dir is None:
        return default_tools_dir()
    p = Path(tools_dir).expanduser().resolve()
    if not (p / "scripts" / "file_scorer_evaluation.py").exists():
        raise FileNotFoundError(
            f"{p} does not look like the HIPE-2026-data checkout "
            "(missing scripts/file_scorer_evaluation.py)"
        )
    return p


def default_schema_file(tools_dir: str | Path | None = None) -> Path:
    """Return the path to the official JSON schema bundled with the toolkit."""
    p = _resolve(tools_dir)
    schema = p / "schemas" / "hipe-2026-data.schema.json"
    if not schema.exists():
        raise FileNotFoundError(f"Missing schema file at {schema}")
    return schema


@dataclass(slots=True)
class SchemaCheckResult:
    ok: bool
    stdout: str
    stderr: str
    returncode: int


@dataclass(slots=True)
class ScorerResult:
    stdout: str
    stderr: str
    returncode: int
    macro_recall_at: float | None
    macro_recall_isAt: float | None
    global_score: float | None


def validate_submission(
    submission_file: str | Path,
    *,
    schema_file: str | Path | None = None,
    tools_dir: str | Path | None = None,
    python_executable: str | None = None,
) -> SchemaCheckResult:
    """Run ``check_jsonlschema.py`` on a submission file."""
    tools = _resolve(tools_dir)
    schema = Path(schema_file) if schema_file else default_schema_file(tools)
    py = python_executable or sys.executable
    cmd = [
        py,
        str(tools / "scripts" / "check_jsonlschema.py"),
        "--schemafile",
        str(schema),
        str(submission_file),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(tools))
    return SchemaCheckResult(
        ok=proc.returncode == 0,
        stdout=proc.stdout,
        stderr=proc.stderr,
        returncode=proc.returncode,
    )


_FLOAT_RE = re.compile(r"-?\d+(?:\.\d+)?")


def _extract_metric(text: str, *needles: str) -> float | None:
    """Best-effort extraction: find a line containing every needle, return
    the first numeric token in it. Tolerates slight wording changes in the
    organizers' scorer output.
    """
    for line in text.splitlines():
        low = line.lower()
        if all(n.lower() in low for n in needles):
            m = _FLOAT_RE.search(line)
            if m:
                try:
                    return float(m.group(0))
                except ValueError:
                    pass
    return None


def run_official_scorer(
    gold_file: str | Path,
    prediction_file: str | Path,
    *,
    tools_dir: str | Path | None = None,
    python_executable: str | None = None,
) -> ScorerResult:
    """Run ``file_scorer_evaluation.py`` and try to parse the headline scores."""
    tools = _resolve(tools_dir)
    py = python_executable or sys.executable
    cmd = [
        py,
        str(tools / "scripts" / "file_scorer_evaluation.py"),
        "--gold_data_file",
        str(gold_file),
        "--predictions_file",
        str(prediction_file),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(tools))
    out = proc.stdout

    return ScorerResult(
        stdout=out,
        stderr=proc.stderr,
        returncode=proc.returncode,
        macro_recall_at=_extract_metric(out, "macro", "at"),
        macro_recall_isAt=_extract_metric(out, "macro", "isat"),
        global_score=_extract_metric(out, "global"),
    )


def run_dummy_predict(
    input_file: str | Path,
    output_file: str | Path,
    *,
    tools_dir: str | Path | None = None,
    python_executable: str | None = None,
) -> subprocess.CompletedProcess:
    """Run the organizers' random-baseline predictor (``dummy_predict.py``)."""
    tools = _resolve(tools_dir)
    py = python_executable or sys.executable
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        py,
        str(tools / "scripts" / "dummy_predict.py"),
        "--input_path",
        str(input_file),
        "--output_path",
        str(output_file),
    ]
    return subprocess.run(cmd, capture_output=True, text=True, cwd=str(tools))


def establish_baseline(
    gold_file: str | Path,
    *,
    tools_dir: str | Path | None = None,
    work_dir: str | Path = "logs/baselines",
    python_executable: str | None = None,
) -> dict[str, object]:
    """Random baseline pipeline: dummy predictions -> schema check -> scorer.

    Returns a dict with the raw subprocess results plus the parsed scorer
    metrics. Use the resulting numbers as a floor that every experiment must
    beat (see HIPE2026_Evaluation_Submission_Specs.md §3.4).
    """
    tools = _resolve(tools_dir)
    py = python_executable or sys.executable
    work = Path(work_dir)
    work.mkdir(parents=True, exist_ok=True)

    pred_path = work / (Path(gold_file).stem + "_random_baseline.jsonl")

    print(f"[baseline] dummy_predict -> {pred_path}")
    dummy = run_dummy_predict(gold_file, pred_path, tools_dir=tools, python_executable=py)
    if dummy.returncode != 0:
        print(dummy.stdout)
        print(dummy.stderr, file=sys.stderr)
        raise RuntimeError("dummy_predict.py failed")

    print("[baseline] schema validation")
    schema = validate_submission(pred_path, tools_dir=tools, python_executable=py)
    if not schema.ok:
        print(schema.stdout)
        print(schema.stderr, file=sys.stderr)
        raise RuntimeError("Schema validation failed for random baseline")
    print("[baseline] schema OK")

    print("[baseline] official scorer")
    scorer = run_official_scorer(
        gold_file, pred_path, tools_dir=tools, python_executable=py
    )
    print(scorer.stdout)
    if scorer.returncode != 0:
        print(scorer.stderr, file=sys.stderr)
        raise RuntimeError("file_scorer_evaluation.py failed")

    return {
        "prediction_file": str(pred_path),
        "schema_ok": schema.ok,
        "global_score": scorer.global_score,
        "macro_recall_at": scorer.macro_recall_at,
        "macro_recall_isAt": scorer.macro_recall_isAt,
        "scorer_stdout": scorer.stdout,
    }


def package_runs(
    team_name: str,
    run_files: list[str | Path],
    *,
    output_zip: str | Path | None = None,
) -> Path:
    """Zip the given submission files into ``team_name.zip``.

    Files are stored at the archive root (no directory prefix), matching
    what the organizers expect.
    """
    if not run_files:
        raise ValueError("package_runs requires at least one run file")
    zip_path = Path(output_zip) if output_zip else Path(f"{team_name}.zip")
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in run_files:
            p = Path(f)
            if not p.exists():
                raise FileNotFoundError(p)
            zf.write(p, arcname=p.name)
    print(f"Packaged {len(run_files)} run(s) into {zip_path}")
    return zip_path
