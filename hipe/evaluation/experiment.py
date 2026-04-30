"""Ablation experiment harness.

Given a ``predict_fn`` over flat instances, runs predictions with timing,
applies the official scoring rules, writes per-prediction logs and a JSON
report. See HIPE2026_Evaluation_Submission_Specs.md §7.3.
"""

from __future__ import annotations

import json
import time
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any

from hipe.data import RelationInstance
from hipe.evaluation.report import generate_evaluation_report

PredictFn = Callable[[RelationInstance], dict[str, Any]]


def run_ablation_experiment(
    experiment_id: str,
    predict_fn: PredictFn,
    dev_instances: Iterable[RelationInstance],
    *,
    log_dir: str | Path = "logs/ablations",
    extra_metadata: dict[str, Any] | None = None,
    print_summary: bool = True,
) -> dict[str, Any]:
    """Run ``predict_fn`` over ``dev_instances``, score, and persist artefacts.

    ``predict_fn(instance)`` must return at minimum ``{'at': str, 'isAt': str}``.
    Optional keys: ``at_explanation``, ``isAt_explanation``, ``raw_output``.

    Logs land under ``log_dir``:
        <experiment_id>_predictions.jsonl   one line per instance with
                                            gold + pred + latency + raw_output
        <experiment_id>_report.json         the evaluation report (scores,
                                            confusion matrices, metadata).
    """
    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, Any]] = []
    total_time = 0.0
    instances = list(dev_instances)
    for inst in instances:
        start = time.perf_counter()
        pred = predict_fn(inst)
        elapsed = time.perf_counter() - start
        total_time += elapsed

        rows.append(
            {
                "document_id": inst.document_id,
                "pers_entity_id": inst.pers_entity_id,
                "loc_entity_id": inst.loc_entity_id,
                "language": inst.language,
                "at_predicted": pred.get("at"),
                "isAt_predicted": pred.get("isAt"),
                "at_gold": inst.at,
                "isAt_gold": inst.isAt,
                "at_explanation": pred.get("at_explanation"),
                "isAt_explanation": pred.get("isAt_explanation"),
                "latency_ms": elapsed * 1000.0,
                "raw_output": pred.get("raw_output"),
            }
        )

    at_gold = [r["at_gold"] for r in rows]
    at_pred = [r["at_predicted"] for r in rows]
    isAt_gold = [r["isAt_gold"] for r in rows]
    isAt_pred = [r["isAt_predicted"] for r in rows]

    metadata = {
        "n_instances": len(rows),
        "total_time_seconds": total_time,
        "avg_latency_ms": (total_time / len(rows) * 1000.0) if rows else 0.0,
    }
    if extra_metadata:
        metadata.update(extra_metadata)

    report = generate_evaluation_report(
        experiment_id, at_gold, at_pred, isAt_gold, isAt_pred,
        metadata=metadata, print_summary=print_summary,
    )

    pred_path = log_dir / f"{experiment_id}_predictions.jsonl"
    with pred_path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False, default=str) + "\n")

    report_path = log_dir / f"{experiment_id}_report.json"
    with report_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2, default=str)

    print(f"Wrote {pred_path}")
    print(f"Wrote {report_path}")
    return report
