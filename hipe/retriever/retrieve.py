"""Retriever query API combining encoder + FAISS index.

Implements the retrieval policy described in HIPE-2026 Pipeline Spec §3.3:
prefer same-language examples, fall back to cross-lingual when there
aren't enough; optionally enforce label diversity so each (at, isAt) class
is represented when possible.
"""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np

from hipe.data import RelationInstance
from hipe.retriever.embed import EncoderConfig, EntityAwareEncoder
from hipe.retriever.index import FaissIndex


@dataclass(slots=True)
class RetrievedExample:
    score: float
    metadata: dict
    rank: int

    @property
    def sample_id(self) -> str:
        return self.metadata.get("sample_id", "")

    @property
    def language(self) -> str:
        return self.metadata.get("language", "")

    @property
    def at(self) -> str | None:
        return self.metadata.get("at")

    @property
    def isAt(self) -> str | None:
        return self.metadata.get("isAt")


def instance_to_metadata(instance: RelationInstance) -> dict:
    """Compact metadata kept alongside each indexed embedding.

    Keep this small — it's loaded into memory at query time. Full text
    retrieval should re-load the source jsonl by ``sample_id`` if needed.
    """
    return {
        "sample_id": instance.sample_id,
        "document_id": instance.document_id,
        "pers_entity_id": instance.pers_entity_id,
        "loc_entity_id": instance.loc_entity_id,
        "language": instance.language,
        "date": instance.date,
        "pers_mention": (instance.pers_mentions_list or [None])[0],
        "loc_mention": (instance.loc_mentions_list or [None])[0],
        "context": instance.context,
        "at": instance.at,
        "isAt": instance.isAt,
    }


class Retriever:
    """Combines an :class:`EntityAwareEncoder` with a :class:`FaissIndex`."""

    def __init__(self, encoder: EntityAwareEncoder, index: FaissIndex) -> None:
        self.encoder = encoder
        self.index = index

    @classmethod
    def from_disk(
        cls,
        index_dir: str | Path,
        *,
        model_name: str | None = None,
        device: str | None = None,
    ) -> "Retriever":
        index = FaissIndex.load(index_dir)
        cfg = EncoderConfig(
            model_name=model_name or EncoderConfig().model_name,
            device=device,
        )
        encoder = EntityAwareEncoder(cfg)
        if encoder.dim != index.dim:
            raise ValueError(
                f"Encoder dim ({encoder.dim}) != index dim ({index.dim}); "
                f"the index was built with a different model."
            )
        return cls(encoder=encoder, index=index)

    def search(
        self,
        query: RelationInstance,
        k: int = 5,
        *,
        prefer_language: str | None = "auto",
        diversify_labels: bool = False,
        exclude_sample_ids: Iterable[str] | None = None,
    ) -> list[RetrievedExample]:
        """Return top-k retrieved examples for *query*.

        Parameters
        ----------
        query : RelationInstance
            Query instance — its language is used when ``prefer_language="auto"``.
        k : int
            Number of examples to return.
        prefer_language : str | "auto" | None
            ``"auto"`` (default) prefers the query's own language;
            a string code (e.g. ``"fr"``) prefers that language;
            ``None`` disables language filtering.
        diversify_labels : bool
            If True, ensure ≥1 example per (at, isAt) combination present in
            the candidate pool (Spec §3.3).
        exclude_sample_ids : iterable of str
            Skip these sample IDs (e.g. the query's own row when running
            leave-one-out on the train pool).
        """
        prefer = query.language if prefer_language == "auto" else prefer_language

        # Over-fetch to give us room for filtering and diversification.
        fetch_k = max(k * 4, 20) if (prefer or diversify_labels) else k
        fetch_k = min(fetch_k, len(self.index))

        emb = self.encoder.encode_instances([query], show_progress_bar=False)
        scores, idx = self.index.search(emb, k=fetch_k)
        scores = scores[0].tolist()
        idx = idx[0].tolist()

        excludes = set(exclude_sample_ids or ())
        candidates: list[RetrievedExample] = []
        for rank, (s, i) in enumerate(zip(scores, idx)):
            if i < 0:
                continue
            md = self.index.metadata[i]
            if md.get("sample_id") in excludes:
                continue
            candidates.append(RetrievedExample(score=float(s), metadata=md, rank=rank))

        return _select_topk(candidates, k=k, prefer_language=prefer, diversify_labels=diversify_labels)


def _select_topk(
    candidates: list[RetrievedExample],
    *,
    k: int,
    prefer_language: str | None,
    diversify_labels: bool,
) -> list[RetrievedExample]:
    """Apply language preference and (optionally) label diversification.

    Strategy:
    1. If ``prefer_language``, partition candidates into same-lang vs others.
    2. If ``diversify_labels``, walk same-lang first, picking one example per
       (at, isAt) bucket greedily (highest-scoring first), then fill the rest
       by raw score.
    3. Pad from the cross-lingual pool if same-lang didn't yield k.
    """
    if prefer_language:
        same = [c for c in candidates if c.language == prefer_language]
        other = [c for c in candidates if c.language != prefer_language]
    else:
        same, other = candidates, []

    chosen: "OrderedDict[str, RetrievedExample]" = OrderedDict()

    if diversify_labels:
        seen_buckets: set[tuple[str | None, str | None]] = set()
        for c in same:
            bucket = (c.at, c.isAt)
            if bucket not in seen_buckets:
                chosen[c.sample_id] = c
                seen_buckets.add(bucket)
            if len(chosen) >= k:
                break

    # Fill from same-language by score order.
    for c in same:
        if len(chosen) >= k:
            break
        chosen.setdefault(c.sample_id, c)

    # Fall back to cross-lingual if needed.
    for c in other:
        if len(chosen) >= k:
            break
        chosen.setdefault(c.sample_id, c)

    return list(chosen.values())[:k]
