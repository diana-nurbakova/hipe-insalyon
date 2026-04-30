"""Wikidata P131 location-hierarchy features (Specs v2 §4.1.2).

Optional. The features capture mentions of *child* locations (Lyon → France)
and *parent* locations (France → Lyon) that implicitly support — or weaken —
the person-location association. Building the cache requires SPARQL queries
to ``query.wikidata.org``; if no cache is supplied, the matrix falls back to
zeros so callers can opt out without code changes.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import Any

import numpy as np

from hipe.data import RelationInstance


HIERARCHY_FEATURE_NAMES: tuple[str, ...] = (
    "direct_loc_count",
    "hierarchical_loc_count",
    "parent_location_mentioned",
)

_SPARQL_URL = "https://query.wikidata.org/sparql"


def build_location_hierarchy(
    loc_qid: str, *, max_depth: int = 5, timeout: float = 10.0
) -> list[tuple[str, str]]:
    """Return the P131 chain ``[(qid, label), ...]`` from specific to general.

    Network call. Wraps any exception and returns whatever was collected so
    far so the caller can opportunistically build a cache offline.
    """
    import requests

    chain: list[tuple[str, str]] = []
    current = loc_qid
    for _ in range(max_depth):
        if not current:
            break
        query = f"""
        SELECT ?parent ?parentLabel WHERE {{
          wd:{current} wdt:P131 ?parent .
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en,fr,de". }}
        }}
        LIMIT 1
        """
        try:
            resp = requests.get(
                _SPARQL_URL,
                params={"query": query, "format": "json"},
                timeout=timeout,
                headers={"User-Agent": "HIPE-2026/0.1 (research)"},
            )
            data = resp.json()
            bindings = data.get("results", {}).get("bindings", [])
            if not bindings:
                break
            parent = bindings[0]
            parent_qid = parent["parent"]["value"].rsplit("/", 1)[-1]
            parent_label = parent["parentLabel"]["value"]
            chain.append((parent_qid, parent_label))
            current = parent_qid
        except Exception:
            break
    return chain


def compute_hierarchical_mention_count(
    inst: RelationInstance,
    hierarchy_cache: dict[str, dict[str, list[str]]] | None = None,
) -> dict[str, float]:
    """Return the 3-d hierarchy feature dict.

    ``hierarchy_cache`` schema::

        {
            target_qid: {
                child_qid: [child_surface_forms],   # mentions of children
                "_parents": [parent_label, ...],    # ancestor labels
            },
            ...
        }

    If ``hierarchy_cache`` is None or lacks an entry for the target, returns
    zeros for the hierarchical/parent features and the direct-mention count
    from the surface forms in the instance.
    """
    text = inst.text or ""
    direct_mentions = [m for m in (inst.loc_mentions_list or []) if m]
    direct_count = sum(text.count(m) for m in direct_mentions)

    child_count = 0
    parent_mentioned = 0.0
    if hierarchy_cache and inst.loc_wikidata_QID:
        entry = hierarchy_cache.get(inst.loc_wikidata_QID)
        if entry:
            for child_qid, child_mentions in entry.items():
                if child_qid == "_parents":
                    continue
                if not isinstance(child_mentions, (list, tuple)):
                    continue
                child_count += sum(text.count(m) for m in child_mentions if m)
            for parent_label in entry.get("_parents", []) or []:
                if parent_label and parent_label in text:
                    parent_mentioned = 1.0
                    break

    return {
        "direct_loc_count": float(min(direct_count / 10.0, 1.0)),
        "hierarchical_loc_count": float(min((direct_count + child_count) / 10.0, 1.0)),
        "parent_location_mentioned": parent_mentioned,
    }


def hierarchy_matrix(
    instances: Iterable[RelationInstance],
    hierarchy_cache: dict[str, dict[str, list[str]]] | None = None,
) -> np.ndarray:
    rows = [compute_hierarchical_mention_count(i, hierarchy_cache) for i in instances]
    return np.array(
        [[r[name] for name in HIERARCHY_FEATURE_NAMES] for r in rows],
        dtype=np.float32,
    )


def load_hierarchy_cache(path: str | Path) -> dict[str, dict[str, list[str]]]:
    """Load a JSON-serialised hierarchy cache from disk."""
    import json

    p = Path(path)
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


__all__ = [
    "HIERARCHY_FEATURE_NAMES",
    "build_location_hierarchy",
    "compute_hierarchical_mention_count",
    "hierarchy_matrix",
    "load_hierarchy_cache",
]
