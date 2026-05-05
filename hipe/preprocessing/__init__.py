"""Block-1 feature extractor for the official test set.

Replicates the temporal / discourse / Wikidata-status fields in
``data/dataset_reference.jsonl`` using the rules from
``specs/HIPE2026_Pipeline_Specs_v4.md`` §2.3 — sufficient input for the
RF and C4 LR base models.

Public surface
--------------
- :func:`enrich_instance`           — one official-format pair -> enriched RelationInstance
- :func:`enrich_official_jsonl`     — official nested JSONL -> flat enriched JSONL
- :func:`extract_temporal_signals`  — regex/lexicon -> (list, category)
- :func:`extract_tense_aspect`      — spaCy -> verb clusters
- :func:`derive_sentence_position`  — locate the entity-pair sentence
- :func:`derive_temporal_person_status`     — Wikidata birth/death + pub_date
- :func:`extract_temporal_expressions_heideltime` — optional, requires Java
"""

from hipe.preprocessing.enrich import (
    derive_known_relations,
    derive_location_context,
    derive_nearest_timex_distance,
    derive_person_context,
    derive_person_location_match,
    derive_sentence_position,
    derive_similar_examples,
    derive_temporal_person_status,
    enrich_instance,
    enrich_official_jsonl,
    extract_context,
    extract_tense_aspect,
    extract_temporal_expressions_heideltime,
    extract_temporal_signals,
)

__all__ = [
    "derive_known_relations",
    "derive_location_context",
    "derive_nearest_timex_distance",
    "derive_person_context",
    "derive_person_location_match",
    "derive_sentence_position",
    "derive_similar_examples",
    "derive_temporal_person_status",
    "enrich_instance",
    "enrich_official_jsonl",
    "extract_context",
    "extract_tense_aspect",
    "extract_temporal_expressions_heideltime",
    "extract_temporal_signals",
]
