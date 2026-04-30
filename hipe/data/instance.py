"""RelationInstance dataclass and JSONL loader.

Schema follows HIPE-2026 Pipeline Specs §2.1 (verified against
data/dataset_reference.jsonl).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator

import orjson


@dataclass(slots=True)
class RelationInstance:
    # Core identifiers
    document_id: str
    pers_entity_id: str
    loc_entity_id: str
    language: str
    date: str  # ISO YYYY-MM-DD

    # Entity mentions
    pers_mentions_list: list[str]
    loc_mentions_list: list[str]
    pers_wikidata_QID: str | None
    loc_wikidata_QID: str | None

    # Text
    text: str
    context: str

    # Knowledge context (pre-fetched)
    person_context: dict[str, Any] = field(default_factory=dict)
    location_context: dict[str, Any] = field(default_factory=dict)
    known_person_location_relations: dict[str, Any] = field(default_factory=dict)
    similar_examples: list[Any] = field(default_factory=list)

    # Pre-computed temporal features
    temporal_expressions: list[Any] = field(default_factory=list)
    temporal_signals: list[Any] = field(default_factory=list)
    tense_aspect: list[dict[str, Any]] = field(default_factory=list)
    sentence_position: int = -1
    ocr_quality: float = 1.0
    has_timex_in_isat_window: bool = False
    nearest_timex_distance: int | None = None

    # Derived features
    person_location_match: str = "unknown"
    temporal_person_status: str = "unknown"
    temporal_signal_category: str = "no_signal"

    # Gold labels
    at: str | None = None  # "TRUE" | "PROBABLE" | "FALSE"
    isAt: str | None = None  # "TRUE" | "FALSE"
    at_explanation: str | None = None
    isAt_explanation: str | None = None

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> RelationInstance:
        # Tolerate extra/missing fields by filtering to declared slots.
        kwargs = {k: d[k] for k in cls.__dataclass_fields__ if k in d}
        return cls(**kwargs)

    @property
    def sample_id(self) -> str:
        """Composite ID matching v1_baseline_train_test_ids.csv."""
        return f"{self.document_id} | {self.pers_entity_id} | {self.loc_entity_id}"


def load_jsonl(path: str | Path) -> list[RelationInstance]:
    """Load all instances from a JSONL file."""
    return list(iter_jsonl(path))


def iter_jsonl(path: str | Path) -> Iterator[RelationInstance]:
    """Stream instances from a JSONL file."""
    p = Path(path)
    with p.open("rb") as f:
        for raw in f:
            raw = raw.strip()
            if not raw:
                continue
            yield RelationInstance.from_dict(orjson.loads(raw))
