"""Temporal + handcrafted feature extractors.

The 15-d ``TemporalFeatureVector`` follows HIPE-2026 Pipeline Spec §2.4
verbatim. The broader handcrafted vector serves as the spec's "no text
embedding" baseline (T1.5 in the ablation tier) — language one-hot,
temporal-signal one-hot, QID availability, length features, etc.
"""

from __future__ import annotations

from typing import Iterable, Sequence

import numpy as np

from hipe.data import RelationInstance

# Spec-aligned ``isAt`` window. The official HIPE-2026 guidelines
# (Evaluation Specs §1.2 / §8.1) widened the window from the ±14-day rule
# used in our preprocessed dataset_reference.jsonl to "approximately one
# month" before the publication date. ``recompute_has_timex_in_window``
# applies the spec window to the pre-computed ``nearest_timex_distance``.
DEFAULT_ISAT_WINDOW_DAYS = 30


def recompute_has_timex_in_window(
    inst: RelationInstance,
    *,
    window_days: int = DEFAULT_ISAT_WINDOW_DAYS,
) -> bool:
    """Recompute the boolean ``has_timex_in_isat_window`` for the spec window.

    The dataset's pre-computed flag uses the obsolete ±14-day window. This
    helper derives the spec-aligned (~1 month) flag from
    ``nearest_timex_distance`` (signed days from the publication date),
    which is a verified field in the dataset.
    """
    d = inst.nearest_timex_distance
    if d is None:
        return False
    return abs(int(d)) <= window_days

# 15-d feature names — matches the spec's TemporalFeatureVector dataclass exactly.
TEMPORAL_FEATURE_NAMES: tuple[str, ...] = (
    "verb_is_present",
    "verb_is_past",
    "verb_is_negated",
    "verb_is_future",
    "sentence_position_norm",
    "is_lead_paragraph",
    "signal_negation",
    "signal_present",
    "signal_relative",
    "signal_none",
    "has_timex_in_window",
    "nearest_timex_distance_norm",
    "person_is_deceased",
    "person_status_known",
    "ocr_quality",
)

# Aggregate categorical fields used for the handcrafted vector.
_LANGUAGES = ("en", "fr", "de", "lb")
_PERSON_STATUSES = (
    "unknown",
    "no_match",
    "alive_past",
    "alive_now",
    "alive_no_longer",
    "dead_historical",
    "timex_in_lifespan",
    "timex_after_death",
)

HANDCRAFTED_FEATURE_NAMES: tuple[str, ...] = (
    *TEMPORAL_FEATURE_NAMES,
    *(f"lang_{lc}" for lc in _LANGUAGES),
    *(f"person_status_{st}" for st in _PERSON_STATUSES),
    "has_pers_qid",
    "has_loc_qid",
    "n_pers_mentions",
    "n_loc_mentions",
    "n_temporal_expressions",
    "n_temporal_signals",
    "n_tense_aspect_clusters",
    "text_len_chars_norm",
    "context_len_chars_norm",
)


def _verb_features(inst: RelationInstance) -> tuple[float, float, float, float]:
    """Aggregate verb-cluster annotations into present / past / negated / future bits.

    The dataset stores ``tense_aspect`` as a list of clusters; we OR them so any
    matching cluster turns the bit on.
    """
    present = past = negated = future = 0.0
    for cl in inst.tense_aspect or []:
        tense = (cl.get("tense") or "").lower()
        if tense.startswith("pres"):
            present = 1.0
        elif tense.startswith("past"):
            past = 1.0
        elif tense.startswith("fut"):
            future = 1.0
        if cl.get("negated"):
            negated = 1.0
    return present, past, negated, future


def extract_temporal_features(inst: RelationInstance) -> np.ndarray:
    """15-d vector matching :data:`TEMPORAL_FEATURE_NAMES`."""
    vp, vt, vn, vf = _verb_features(inst)
    sp = inst.sentence_position if inst.sentence_position is not None else -1
    sp_norm = max(0.0, min(1.0, sp / 50.0)) if sp >= 0 else 0.0
    is_lead = 1.0 if 0 <= sp <= 1 else 0.0

    cat = inst.temporal_signal_category or "no_signal"
    sig_neg = 1.0 if cat == "negation" else 0.0
    sig_pres = 1.0 if cat == "present" else 0.0
    sig_rel = 1.0 if cat == "relative_only" else 0.0
    sig_none = 1.0 if cat in {"no_signal", ""} else 0.0

    # Spec §8.1 widens the isAt window from ±14 days to ~1 month. The
    # dataset's pre-computed boolean still reflects the old 14-day rule;
    # recompute from `nearest_timex_distance` to align with the guidelines.
    has_timex = 1.0 if recompute_has_timex_in_window(inst) else 0.0
    nearest = inst.nearest_timex_distance
    nearest_norm = 0.0 if nearest is None else max(0.0, min(1.0, abs(nearest) / 365.0))

    status = inst.temporal_person_status or "unknown"
    is_deceased = 1.0 if status == "dead_historical" else 0.0
    status_known = 1.0 if status not in {"unknown", "no_match"} else 0.0

    ocr = inst.ocr_quality if inst.ocr_quality is not None else 1.0

    return np.array(
        [
            vp,
            vt,
            vn,
            vf,
            sp_norm,
            is_lead,
            sig_neg,
            sig_pres,
            sig_rel,
            sig_none,
            has_timex,
            nearest_norm,
            is_deceased,
            status_known,
            float(ocr),
        ],
        dtype=np.float32,
    )


def extract_handcrafted_features(inst: RelationInstance) -> np.ndarray:
    """Broader handcrafted vector for the spec's T1.5 baseline."""
    base = extract_temporal_features(inst)

    lang_oh = np.zeros(len(_LANGUAGES), dtype=np.float32)
    if inst.language in _LANGUAGES:
        lang_oh[_LANGUAGES.index(inst.language)] = 1.0

    status_oh = np.zeros(len(_PERSON_STATUSES), dtype=np.float32)
    if inst.temporal_person_status in _PERSON_STATUSES:
        status_oh[_PERSON_STATUSES.index(inst.temporal_person_status)] = 1.0

    extras = np.array(
        [
            1.0 if inst.pers_wikidata_QID else 0.0,
            1.0 if inst.loc_wikidata_QID else 0.0,
            float(len(inst.pers_mentions_list or [])),
            float(len(inst.loc_mentions_list or [])),
            float(len(inst.temporal_expressions or [])),
            float(len(inst.temporal_signals or [])),
            float(len(inst.tense_aspect or [])),
            min(1.0, len(inst.text or "") / 12000.0),  # text length saturates at 12k chars
            min(1.0, len(inst.context or "") / 2000.0),  # context length saturates at 2k chars
        ],
        dtype=np.float32,
    )
    return np.concatenate([base, lang_oh, status_oh, extras]).astype(np.float32, copy=False)


def temporal_matrix(instances: Iterable[RelationInstance]) -> np.ndarray:
    return np.stack([extract_temporal_features(i) for i in instances]).astype(np.float32, copy=False)


def handcrafted_matrix(instances: Iterable[RelationInstance]) -> np.ndarray:
    return np.stack([extract_handcrafted_features(i) for i in instances]).astype(np.float32, copy=False)
