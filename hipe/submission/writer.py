"""Generate HIPE-2026 submission JSONL files.

The official format (HIPE2026_Evaluation_Submission_Specs.md §2.1) is one
document per line with nested ``sampled_pairs``. Submissions must mirror the
input file's structure, ordering, and metadata, with the per-pair ``at`` /
``isAt`` fields filled in from our predictions.

This module:
- accepts predictions keyed by ``(document_id, pers_entity_id, loc_entity_id)``,
- defaults missing predictions to ``FALSE`` (per §1.4 null-handling rule),
- enforces the consistency constraint ``at == FALSE -> isAt == FALSE``
  (§1.3 / §4.2),
- validates labels are within the official vocabularies,
- preserves all document-level metadata.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from hipe.evaluation.metrics import AT_LABELS, ISAT_LABELS, null_to_false

PredictionKey = tuple[str, str, str]  # (document_id, pers_entity_id, loc_entity_id)


@dataclass(slots=True)
class Prediction:
    at: str
    isAt: str
    at_explanation: str | None = None
    isAt_explanation: str | None = None


def _coerce(pred: Any) -> Prediction:
    """Accept either a Prediction or a plain dict with the required keys."""
    if isinstance(pred, Prediction):
        return pred
    if isinstance(pred, Mapping):
        return Prediction(
            at=null_to_false(pred.get("at")),
            isAt=null_to_false(pred.get("isAt")),
            at_explanation=pred.get("at_explanation"),
            isAt_explanation=pred.get("isAt_explanation"),
        )
    raise TypeError(f"prediction must be Prediction or Mapping, got {type(pred).__name__}")


@dataclass(slots=True)
class SubmissionStats:
    total_pairs: int
    n_documents: int
    n_missing_predictions: int  # defaulted to FALSE/FALSE
    n_constraint_fixes: int  # at=FALSE & isAt=TRUE -> isAt=FALSE
    label_counts_at: dict[str, int]
    label_counts_isAt: dict[str, int]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    def summary(self) -> str:
        return (
            f"docs={self.n_documents} pairs={self.total_pairs} "
            f"missing={self.n_missing_predictions} "
            f"constraint_fixes={self.n_constraint_fixes}\n"
            f"  at:   {self.label_counts_at}\n"
            f"  isAt: {self.label_counts_isAt}"
        )


def generate_submission_file(
    input_file: str | Path,
    predictions: Mapping[PredictionKey, Prediction | Mapping[str, Any]],
    output_file: str | Path,
    *,
    enforce_constraint: bool = True,
    overwrite_explanations: bool = True,
) -> SubmissionStats:
    """Merge ``predictions`` into the official ``input_file`` structure.

    Parameters
    ----------
    input_file : path
        Official-format JSONL (test or dev). Document and pair ordering is
        preserved exactly.
    predictions : mapping
        ``(document_id, pers_entity_id, loc_entity_id) -> Prediction`` (or a
        plain dict with the same fields). Missing entries default to FALSE/FALSE.
    output_file : path
        Where to write the submission JSONL.
    enforce_constraint : bool
        If True (default), force ``isAt = FALSE`` whenever ``at = FALSE``.
        The official scorer does not enforce this, but the guidelines describe
        it as a definitional constraint -- inconsistency would be wasted
        confidence at evaluation time.
    overwrite_explanations : bool
        If True (default), replace existing explanations even when the
        prediction does not provide them. If False, keep whatever was already
        in the input record (rarely useful for test data, where the field is
        empty anyway).
    """
    input_path = Path(input_file)
    output_path = Path(output_file)

    documents: list[dict[str, Any]] = []
    with input_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                documents.append(json.loads(line))

    label_counts_at: dict[str, int] = {lbl: 0 for lbl in AT_LABELS}
    label_counts_isAt: dict[str, int] = {lbl: 0 for lbl in ISAT_LABELS}

    n_missing = 0
    n_fixes = 0
    n_pairs = 0

    for doc in documents:
        doc_id = doc["document_id"]
        for pair in doc.get("sampled_pairs", []):
            n_pairs += 1
            key: PredictionKey = (doc_id, pair["pers_entity_id"], pair["loc_entity_id"])
            raw = predictions.get(key)
            if raw is None:
                pair["at"] = "FALSE"
                pair["isAt"] = "FALSE"
                if overwrite_explanations:
                    pair["at_explanation"] = None
                    pair["isAt_explanation"] = None
                n_missing += 1
            else:
                pred = _coerce(raw)
                if pred.at not in AT_LABELS:
                    raise ValueError(
                        f"Invalid at label {pred.at!r} for {key} "
                        f"(allowed: {list(AT_LABELS)})"
                    )
                if pred.isAt not in ISAT_LABELS:
                    raise ValueError(
                        f"Invalid isAt label {pred.isAt!r} for {key} "
                        f"(allowed: {list(ISAT_LABELS)})"
                    )

                at_label = pred.at
                isAt_label = pred.isAt
                if enforce_constraint and at_label == "FALSE" and isAt_label == "TRUE":
                    isAt_label = "FALSE"
                    n_fixes += 1

                pair["at"] = at_label
                pair["isAt"] = isAt_label
                if overwrite_explanations or pred.at_explanation is not None:
                    pair["at_explanation"] = pred.at_explanation
                if overwrite_explanations or pred.isAt_explanation is not None:
                    pair["isAt_explanation"] = pred.isAt_explanation

            label_counts_at[pair["at"]] += 1
            label_counts_isAt[pair["isAt"]] += 1

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        for doc in documents:
            f.write(json.dumps(doc, ensure_ascii=False) + "\n")

    stats = SubmissionStats(
        total_pairs=n_pairs,
        n_documents=len(documents),
        n_missing_predictions=n_missing,
        n_constraint_fixes=n_fixes,
        label_counts_at=label_counts_at,
        label_counts_isAt=label_counts_isAt,
    )
    print(f"Wrote {output_path}")
    print(f"  {stats.summary()}")
    return stats


def predictions_from_records(
    records: list[Mapping[str, Any]],
    *,
    at_field: str = "at_predicted",
    isAt_field: str = "isAt_predicted",
    at_explanation_field: str = "at_explanation",
    isAt_explanation_field: str = "isAt_explanation",
) -> dict[PredictionKey, Prediction]:
    """Convert a list of per-instance dicts (e.g. an experiment log) into the
    ``predictions`` mapping consumed by :func:`generate_submission_file`.

    Each record must carry ``document_id``, ``pers_entity_id``, ``loc_entity_id``
    plus the configured prediction fields.
    """
    out: dict[PredictionKey, Prediction] = {}
    for r in records:
        key: PredictionKey = (
            r["document_id"],
            r["pers_entity_id"],
            r["loc_entity_id"],
        )
        out[key] = Prediction(
            at=null_to_false(r.get(at_field)),
            isAt=null_to_false(r.get(isAt_field)),
            at_explanation=r.get(at_explanation_field),
            isAt_explanation=r.get(isAt_explanation_field),
        )
    return out


def submission_filename(team_name: str, input_file: str | Path, run: int) -> str:
    """Build the official submission filename: ``team_<input>_runN.jsonl``."""
    stem = Path(input_file).name
    if stem.endswith(".jsonl"):
        stem = stem[: -len(".jsonl")]
    return f"{team_name}_{stem}_run{run}.jsonl"


__all__ = [
    "Prediction",
    "PredictionKey",
    "SubmissionStats",
    "generate_submission_file",
    "predictions_from_records",
    "submission_filename",
]
