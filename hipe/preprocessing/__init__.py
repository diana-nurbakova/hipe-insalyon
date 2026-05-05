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
    enrich_instance,
    enrich_official_jsonl,
    extract_tense_aspect,
    extract_temporal_expressions_heideltime,
    extract_temporal_signals,
    derive_sentence_position,
    derive_temporal_person_status,
)

__all__ = [
    "enrich_instance",
    "enrich_official_jsonl",
    "extract_tense_aspect",
    "extract_temporal_expressions_heideltime",
    "extract_temporal_signals",
    "derive_sentence_position",
    "derive_temporal_person_status",
]
