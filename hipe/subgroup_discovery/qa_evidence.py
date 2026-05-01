"""QA-based evidence extraction (Dateline & QA Specs §3).

Reframes the relation classification as extractive QA: a SQuAD2-style model
asks "is the person at the location?" and returns an evidence span plus a
confidence score. The score and span statistics become 14 features that
capture evidence strength in a *learned* way — handling coreference, long
range dependencies, and implicit relationships that the regex evidence
features in :mod:`hipe.subgroup_discovery.evidence` cannot.

Three query templates per language are issued per instance:

* ``at``       — "was {person} at or associated with {location}?"
* ``isAt``     — "is {person} currently present at {location}?"
* ``evidence`` — open-ended "what connects {person} to {location}?"

This module imports ``transformers`` lazily so non-GPU users don't pay the
import cost. The default model is the multilingual SQuAD2 checkpoint
recommended by the spec (``deepset/xlm-roberta-base-squad2``); pass
``model_name`` to override.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Any, Final

import numpy as np

from hipe.data import RelationInstance
from hipe.subgroup_discovery.dateline import detect_dateline


# ---------------------------------------------------------------------------
# Public feature names
# ---------------------------------------------------------------------------

QA_FEATURE_NAMES: Final[tuple[str, ...]] = (
    "qa_at_score",
    "qa_at_has_answer",
    "qa_at_span_length",
    "qa_at_span_position",
    "qa_isAt_score",
    "qa_isAt_has_answer",
    "qa_isAt_span_length",
    "qa_isAt_span_position",
    "qa_evidence_score",
    "qa_evidence_has_answer",
    "qa_evidence_span_length",
    "qa_evidence_span_position",
    "qa_at_isAt_score_gap",
    "qa_max_score",
)

# Cross-check feature, populated only when dateline metadata is supplied.
QA_DATELINE_CROSS_FEATURE: Final[str] = "qa_evidence_is_dateline"

# Full 15-d QA block including the dateline cross-check. This is what
# ``QAEvidenceExtractor.extract_matrix`` and ``build_sd_feature_matrix``
# both consume so the column count stays consistent end-to-end.
QA_FULL_FEATURE_NAMES: Final[tuple[str, ...]] = (
    *QA_FEATURE_NAMES,
    QA_DATELINE_CROSS_FEATURE,
)


QA_TEMPLATES: Final[dict[str, dict[str, str]]] = {
    "at": {
        "en": "Was {person} at or associated with {location}?",
        "fr": "Est-ce que {person} était à {location} ou y est associé ?",
        "de": "War {person} in {location} oder damit verbunden?",
        "lb": "War {person} zu {location} oder domat verbonnen?",
    },
    "isAt": {
        "en": "Is {person} currently present at {location}?",
        "fr": "Est-ce que {person} se trouve actuellement à {location} ?",
        "de": "Befindet sich {person} derzeit in {location}?",
        "lb": "Befënnt sech {person} am Moment zu {location}?",
    },
    "evidence": {
        "en": "What connects {person} to {location}?",
        "fr": "Quel est le lien entre {person} et {location} ?",
        "de": "Was verbindet {person} mit {location}?",
        "lb": "Wat verbënnt {person} mat {location}?",
    },
}

DEFAULT_QA_MODEL: Final[str] = "deepset/xlm-roberta-base-squad2"

# Threshold used by the spec to convert a raw QA score into a binary
# "has_answer" feature (§3.5).
HAS_ANSWER_THRESHOLD: Final[float] = 0.1


def _safe_first(items: Sequence[str] | None) -> str:
    if not items:
        return ""
    for x in items:
        if x:
            return x
    return ""


class QAEvidenceExtractor:
    """Extract QA-based evidence features for person-location pairs.

    Lazily loads a HuggingFace ``question-answering`` pipeline on first use.
    The model can be swapped via ``model_name`` for ablations.
    """

    def __init__(
        self,
        model_name: str = DEFAULT_QA_MODEL,
        device: str = "cuda",
        *,
        handle_impossible_answer: bool = True,
        max_seq_len: int = 384,
        doc_stride: int = 128,
    ) -> None:
        self.model_name = model_name
        self.device = device
        self._handle_impossible = handle_impossible_answer
        self._max_seq_len = max_seq_len
        self._doc_stride = doc_stride
        self._pipeline: Any | None = None

    # ----------------------------------------------------------- pipeline mgmt

    def _ensure_pipeline(self) -> Any:
        if self._pipeline is None:
            from transformers import pipeline  # local import to keep cold-start fast

            self._pipeline = pipeline(
                "question-answering",
                model=self.model_name,
                device=0 if self.device == "cuda" else -1,
            )
        return self._pipeline

    # -------------------------------------------------------------- inference

    def _ask(self, question: str, context: str) -> dict[str, Any]:
        qa = self._ensure_pipeline()
        return qa(
            question=question,
            context=context,
            handle_impossible_answer=self._handle_impossible,
            max_seq_len=self._max_seq_len,
            doc_stride=self._doc_stride,
        )

    # -------------------------------------------------------------- features

    def extract_features(self, inst: RelationInstance) -> dict[str, Any]:
        """Return the 14-d QA feature dict plus the raw span strings.

        The span strings (``qa_*_span``) are kept for logging and prompt
        injection but are NOT part of the numeric feature vector.
        """
        person = _safe_first(inst.pers_mentions_list)
        location = _safe_first(inst.loc_mentions_list)
        lang = (inst.language or "en").lower()
        context = inst.context or inst.text or ""

        features: dict[str, Any] = {}

        if not person or not location or not context:
            return _empty_qa_features()

        for query_type in ("at", "isAt", "evidence"):
            template = QA_TEMPLATES[query_type].get(lang, QA_TEMPLATES[query_type]["en"])
            question = template.format(person=person, location=location)
            try:
                result = self._ask(question, context)
                score = float(result.get("score", 0.0))
                answer = str(result.get("answer", ""))
                start = int(result.get("start", 0))
                features[f"qa_{query_type}_score"] = score
                features[f"qa_{query_type}_has_answer"] = float(score > HAS_ANSWER_THRESHOLD)
                features[f"qa_{query_type}_span_length"] = (
                    len(answer) / max(len(context), 1)
                )
                features[f"qa_{query_type}_span_position"] = (
                    start / max(len(context), 1)
                )
                features[f"qa_{query_type}_span"] = answer
            except Exception:
                features[f"qa_{query_type}_score"] = 0.0
                features[f"qa_{query_type}_has_answer"] = 0.0
                features[f"qa_{query_type}_span_length"] = 0.0
                features[f"qa_{query_type}_span_position"] = 0.5
                features[f"qa_{query_type}_span"] = ""

        features["qa_at_isAt_score_gap"] = (
            features["qa_at_score"] - features["qa_isAt_score"]
        )
        features["qa_max_score"] = max(
            features["qa_at_score"], features["qa_isAt_score"]
        )
        features[QA_DATELINE_CROSS_FEATURE] = 0.0  # filled in by cross_check_qa_dateline
        return features

    # --------------------------------------------------------- batch helpers

    def extract_matrix(
        self,
        instances: Sequence[RelationInstance],
        *,
        cross_check_dateline: bool = True,
        progress: bool = False,
    ) -> tuple[np.ndarray, list[dict[str, Any]]]:
        """Run QA extraction over a list of instances.

        Returns ``(X, raw_features)`` where ``X`` is the 15-d numeric
        matrix (``QA_FULL_FEATURE_NAMES`` — ``QA_FEATURE_NAMES`` plus the
        dateline cross-check column) and ``raw_features`` is a list of
        dicts including the span strings for inspection / prompt
        injection. When ``cross_check_dateline`` is True the cross-check
        (§3.8) is applied in place on each row before stacking; when
        False the cross-check column is left at its default 0.0.
        """
        rows: list[dict[str, Any]] = []
        iterator: Iterable[RelationInstance] = instances
        if progress:
            try:
                from tqdm import tqdm

                iterator = tqdm(instances, desc="QA evidence")
            except ImportError:
                iterator = instances

        for inst in iterator:
            feats = self.extract_features(inst)
            if cross_check_dateline:
                cross_check_qa_dateline(feats, inst)
            rows.append(feats)

        X = np.array(
            [[float(r[name]) for name in QA_FULL_FEATURE_NAMES] for r in rows],
            dtype=np.float32,
        )
        return X, rows


# ---------------------------------------------------------------------------
# Cross-check: QA evidence vs dateline (§3.8)
# ---------------------------------------------------------------------------


def cross_check_qa_dateline(
    qa_features: dict[str, Any],
    inst: RelationInstance,
    dateline_features: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Flag cases where the QA-extracted span lies in a dateline region.

    Mutates ``qa_features`` in place (sets ``qa_evidence_is_dateline`` to
    ``1.0`` when the ``at``-query span overlaps the dateline head/tail of
    the article) and returns it.
    """
    if dateline_features is None:
        dateline_features = detect_dateline(inst)

    if not dateline_features.get("location_is_dateline"):
        return qa_features
    if not qa_features.get("qa_at_has_answer"):
        return qa_features

    span = str(qa_features.get("qa_at_span", ""))
    if not span:
        return qa_features

    text = inst.text or ""
    span_start = text.find(span)
    if span_start < 0:
        return qa_features

    # Opening dateline: within first 100 chars.
    if span_start < 100:
        qa_features[QA_DATELINE_CROSS_FEATURE] = 1.0
    # Closing dateline: within last 100 chars.
    elif span_start > len(text) - 100:
        qa_features[QA_DATELINE_CROSS_FEATURE] = 1.0

    return qa_features


# ---------------------------------------------------------------------------
# Standalone QA threshold classifier (§5.4 ablation)
# ---------------------------------------------------------------------------


def qa_threshold_classifier(
    qa_features: dict[str, Any],
    *,
    at_threshold: float = 0.3,
    prob_threshold: float = 0.1,
) -> tuple[str, str]:
    """Classify ``at`` / ``isAt`` from raw QA confidence scores.

    Implements the ablation in §5.4. Returns the pair ``(at_pred, isAt_pred)``
    with labels in ``{"TRUE", "PROBABLE", "FALSE"}`` for ``at`` and in
    ``{"TRUE", "FALSE"}`` for ``isAt``.
    """
    at_score = float(qa_features.get("qa_at_score", 0.0))
    if at_score >= at_threshold:
        at_pred = "TRUE"
    elif at_score >= prob_threshold:
        at_pred = "PROBABLE"
    else:
        at_pred = "FALSE"

    isAt_score = float(qa_features.get("qa_isAt_score", 0.0))
    isAt_pred = "TRUE" if isAt_score >= at_threshold else "FALSE"
    return at_pred, isAt_pred


# ---------------------------------------------------------------------------
# Internals
# ---------------------------------------------------------------------------


def _empty_qa_features() -> dict[str, Any]:
    """Return a zero-filled QA feature dict (used when context is missing)."""
    feats: dict[str, Any] = {}
    for q in ("at", "isAt", "evidence"):
        feats[f"qa_{q}_score"] = 0.0
        feats[f"qa_{q}_has_answer"] = 0.0
        feats[f"qa_{q}_span_length"] = 0.0
        feats[f"qa_{q}_span_position"] = 0.5
        feats[f"qa_{q}_span"] = ""
    feats["qa_at_isAt_score_gap"] = 0.0
    feats["qa_max_score"] = 0.0
    feats[QA_DATELINE_CROSS_FEATURE] = 0.0
    return feats


__all__ = [
    "QA_FEATURE_NAMES",
    "QA_DATELINE_CROSS_FEATURE",
    "QA_TEMPLATES",
    "DEFAULT_QA_MODEL",
    "HAS_ANSWER_THRESHOLD",
    "QAEvidenceExtractor",
    "cross_check_qa_dateline",
    "qa_threshold_classifier",
]
