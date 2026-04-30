"""Official HIPE-2026 nested JSONL parser.

The official files store one document per line with multiple ``sampled_pairs``
nested inside it (see HIPE2026_Evaluation_Submission_Specs.md §2.1). Our
internal pipeline operates on a flat per-pair :class:`RelationInstance`, so
this module bridges the two views.

Two iterators are provided:
- :func:`iter_official_documents` -- raw dicts straight from the JSONL.
- :func:`iter_official_instances` -- one :class:`RelationInstance` per pair.

Both stream the file lazily so they scale to the full ~10K-pair test set.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Any

import orjson

from hipe.data.instance import RelationInstance


def iter_official_documents(path: str | Path) -> Iterator[dict[str, Any]]:
    """Yield each document dict from an official-format JSONL file."""
    p = Path(path)
    with p.open("rb") as f:
        for raw in f:
            raw = raw.strip()
            if not raw:
                continue
            yield orjson.loads(raw)


def load_official_documents(path: str | Path) -> list[dict[str, Any]]:
    """Eager version of :func:`iter_official_documents`."""
    return list(iter_official_documents(path))


def official_pair_to_instance(
    doc: dict[str, Any],
    pair: dict[str, Any],
) -> RelationInstance:
    """Convert one (document, sampled_pair) pair into a flat RelationInstance.

    Document-level ``text`` is stored verbatim. ``context`` is left equal to
    ``text`` because the official format does not pre-extract a sentence-level
    context window -- downstream preprocessing should refine it.
    """
    media = doc.get("media") or {}
    text = doc.get("text", "") or ""

    return RelationInstance(
        document_id=doc["document_id"],
        pers_entity_id=pair["pers_entity_id"],
        loc_entity_id=pair["loc_entity_id"],
        language=doc.get("language", ""),
        date=doc.get("date", ""),
        pers_mentions_list=list(pair.get("pers_mentions_list") or []),
        loc_mentions_list=list(pair.get("loc_mentions_list") or []),
        pers_wikidata_QID=pair.get("pers_wikidata_QID"),
        loc_wikidata_QID=pair.get("loc_wikidata_QID"),
        text=text,
        context=text,
        at=pair.get("at"),
        isAt=pair.get("isAt"),
        at_explanation=pair.get("at_explanation"),
        isAt_explanation=pair.get("isAt_explanation"),
    )


def iter_official_instances(path: str | Path) -> Iterator[RelationInstance]:
    """Yield one :class:`RelationInstance` per ``sampled_pair`` in the file."""
    for doc in iter_official_documents(path):
        for pair in doc.get("sampled_pairs", []):
            yield official_pair_to_instance(doc, pair)


def parse_official_jsonl(path: str | Path) -> list[RelationInstance]:
    """Eagerly parse an official-format JSONL into a flat instance list."""
    instances = list(iter_official_instances(path))
    print(
        f"Parsed {path}: {len(instances)} instances "
        f"from {sum(1 for _ in iter_official_documents(path))} documents"
    )
    return instances


def collect_pair_keys(
    documents: Iterable[dict[str, Any]],
) -> list[tuple[str, str, str]]:
    """Return ``(document_id, pers_entity_id, loc_entity_id)`` triples in
    document/pair order, useful for cross-checking submission ordering."""
    keys: list[tuple[str, str, str]] = []
    for doc in documents:
        doc_id = doc["document_id"]
        for pair in doc.get("sampled_pairs", []):
            keys.append((doc_id, pair["pers_entity_id"], pair["loc_entity_id"]))
    return keys
