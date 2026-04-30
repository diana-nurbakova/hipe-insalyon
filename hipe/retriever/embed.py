"""Entity-aware sentence embedding for RAG retrieval.

Per HIPE-2026 Pipeline Spec §3.2: before encoding, wrap entity mentions
with ``[E1]/[/E1]`` (person) and ``[E2]/[/E2]`` (location) markers so the
embedding captures the entity-pair relationship rather than generic
sentence semantics.

Default model: ``BAAI/bge-m3`` (multilingual, 568M, dense+sparse). Override
via the ``model_name`` argument; ``intfloat/multilingual-e5-small`` is a
lightweight alternative for fast iteration.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
from sentence_transformers import SentenceTransformer

from hipe.data import RelationInstance

DEFAULT_MODEL = "BAAI/bge-m3"

PERS_OPEN, PERS_CLOSE = "[E1]", "[/E1]"
LOC_OPEN, LOC_CLOSE = "[E2]", "[/E2]"


def _wrap_first_match(text: str, mentions: list[str], open_tag: str, close_tag: str) -> tuple[str, bool]:
    """Wrap the earliest occurrence of any mention in *text* with marker tags.

    Returns (new_text, found_flag). Case-insensitive search; original casing
    preserved in the output. Tries longest mentions first so substring
    matches don't preempt longer surface forms.
    """
    if not mentions or not text:
        return text, False

    lowered = text.lower()
    best: tuple[int, int, str] | None = None  # (start, end, matched_substring)
    # Sort mentions longest-first so we don't match a substring inside a longer mention.
    for m in sorted({m for m in mentions if m}, key=len, reverse=True):
        idx = lowered.find(m.lower())
        if idx == -1:
            continue
        if best is None or idx < best[0]:
            best = (idx, idx + len(m), text[idx : idx + len(m)])
    if best is None:
        return text, False
    start, end, matched = best
    return f"{text[:start]}{open_tag} {matched} {close_tag}{text[end:]}", True


def format_with_markers(instance: RelationInstance, *, field: str = "context") -> str:
    """Return the instance's text field with entity markers inserted.

    Falls back to a marker prefix when surface forms can't be located in the
    chosen field, so the embedding still sees the entity pair.
    """
    base = instance.context if field == "context" else instance.text
    base = base or ""
    pers_mentions = instance.pers_mentions_list or []
    loc_mentions = instance.loc_mentions_list or []

    base, pers_found = _wrap_first_match(base, pers_mentions, PERS_OPEN, PERS_CLOSE)
    base, loc_found = _wrap_first_match(base, loc_mentions, LOC_OPEN, LOC_CLOSE)

    if not pers_found or not loc_found:
        # Prepend a synthetic marker block so retrieval still reflects the pair.
        prefix_parts = []
        if not pers_found and pers_mentions:
            prefix_parts.append(f"{PERS_OPEN} {pers_mentions[0]} {PERS_CLOSE}")
        if not loc_found and loc_mentions:
            prefix_parts.append(f"{LOC_OPEN} {loc_mentions[0]} {LOC_CLOSE}")
        if prefix_parts:
            base = " ".join(prefix_parts) + " . " + base
    return base


@dataclass(slots=True)
class EncoderConfig:
    model_name: str = DEFAULT_MODEL
    field: str = "context"  # "context" or "text"
    batch_size: int = 16
    max_seq_length: int | None = None  # None -> model default
    device: str | None = None  # None -> auto


class EntityAwareEncoder:
    """Wraps a SentenceTransformer to embed RelationInstances with entity markers."""

    def __init__(self, config: EncoderConfig | None = None) -> None:
        self.config = config or EncoderConfig()
        self.model = SentenceTransformer(self.config.model_name, device=self.config.device)
        if self.config.max_seq_length:
            self.model.max_seq_length = self.config.max_seq_length

    @property
    def dim(self) -> int:
        return int(self.model.get_sentence_embedding_dimension())

    def format(self, instance: RelationInstance) -> str:
        return format_with_markers(instance, field=self.config.field)

    def encode_instances(
        self,
        instances: Iterable[RelationInstance],
        *,
        show_progress_bar: bool = True,
    ) -> np.ndarray:
        """Embed an iterable of instances. Returns L2-normalised float32 array.

        Normalisation is applied so the embeddings can be searched with FAISS
        IndexFlatIP (inner product == cosine similarity).
        """
        texts = [self.format(inst) for inst in instances]
        return self.encode_texts(texts, show_progress_bar=show_progress_bar)

    def encode_texts(
        self,
        texts: list[str],
        *,
        show_progress_bar: bool = True,
    ) -> np.ndarray:
        embeddings = self.model.encode(
            texts,
            batch_size=self.config.batch_size,
            normalize_embeddings=True,
            show_progress_bar=show_progress_bar,
            convert_to_numpy=True,
        )
        return embeddings.astype(np.float32, copy=False)
