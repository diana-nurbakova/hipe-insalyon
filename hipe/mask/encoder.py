"""hmBERT-family MASK encoder for relation embedding extraction.

For each instance, runs the rendered template through an MLM and returns the
hidden states at the relevant positions. Beyond the original "single-MASK,
last-layer" setup, the encoder now supports:

- **Multi-layer extraction** (Spec Prompting & MASK §8.7): pass
  ``layers=[-1, -4, -7]`` (default) to concatenate layer-12, 9, 6 hidden
  states. Only the last layer is used for ``e1_emb`` / ``e2_emb`` because
  the spec only motivates per-layer treatment for the [MASK] slot.
- **Dual-MASK (template M4)**: the two `[MASK]` positions are stored
  separately as ``mask_at_emb`` / ``mask_isAt_emb`` (in document order:
  first → at, second → isAt) so downstream classifiers can target one slot.
- **Multi-MASK (template M5)**: the three consecutive `[MASK]` hidden
  states are concatenated into ``mask_multi_emb`` (3·H) per the spec; the
  mean is also kept in ``mask_emb`` for backwards compatibility.

The default behaviour matches the previous version (template M2, last layer,
mean-pooled MASK) so existing caches and downstream scripts keep working.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

import numpy as np
import torch
from transformers import AutoModel, AutoTokenizer

from hipe.data import RelationInstance
from hipe.mask.templates import (
    ENTITY_MARKERS,
    LOC_CLOSE,
    LOC_OPEN,
    PERS_CLOSE,
    PERS_OPEN,
    build_template,
)

DEFAULT_MODEL = "dbmdz/bert-base-historic-multilingual-cased"
DEFAULT_LAYERS = (-1,)  # last hidden layer only — back-compat default


@dataclass(slots=True)
class MASKEncoderConfig:
    model_name: str = DEFAULT_MODEL
    template: str = "M2"
    field: str = "context"
    max_seq_length: int = 256
    batch_size: int = 16
    device: str | None = None
    # Layer selection. Pass a tuple/list of negative or positive indices into
    # ``output_hidden_states`` (which has length n_layers + 1: index 0 is the
    # embedding layer, index -1 the last block). The recommended multi-layer
    # setting from the spec is ``(-1, -4, -7)`` ≈ layers 12, 9, 6 for hmBERT.
    layers: tuple[int, ...] = DEFAULT_LAYERS
    add_entity_markers_as_special_tokens: bool = True


@dataclass(slots=True)
class MASKBatch:
    """One row's worth of extracted embeddings + metadata.

    ``mask_emb`` is the mean over MASK positions in the *last* layer (or the
    single layer when ``layers`` has length 1) — the same shape as before, so
    legacy callers keep working.

    ``mask_emb_layers`` carries the concatenation across requested layers
    (shape ``(len(layers) * H,)``). Equal to ``mask_emb`` when only one layer
    is requested.

    ``mask_at_emb`` / ``mask_isAt_emb`` are populated only for the dual-mask
    template M4. ``mask_multi_emb`` is populated only for the multi-mask
    template M5 (concatenation of the three MASK hidden states from the last
    layer).
    """

    sample_id: str
    language: str
    at: str | None
    isAt: str | None
    mask_emb: np.ndarray  # (H,)            — mean MASK on last layer
    mask_emb_layers: np.ndarray  # (L*H,)   — concat across requested layers
    e1_emb: np.ndarray  # (H,)              — last layer; zeros if span absent
    e2_emb: np.ndarray  # (H,)              — last layer; zeros if span absent
    pers_in_context: bool
    loc_in_context: bool
    mask_at_emb: np.ndarray | None = None  # (H,)  — M4 only
    mask_isAt_emb: np.ndarray | None = None  # (H,)  — M4 only
    mask_multi_emb: np.ndarray | None = None  # (n_masks*H,)  — M5 only


class MASKEncoder:
    """BERT-family encoder for MASK template extraction."""

    def __init__(self, config: MASKEncoderConfig | None = None) -> None:
        self.config = config or MASKEncoderConfig()
        self.tokenizer = AutoTokenizer.from_pretrained(self.config.model_name, use_fast=True)
        self.model = AutoModel.from_pretrained(self.config.model_name, output_hidden_states=True)

        if self.config.add_entity_markers_as_special_tokens:
            added = self.tokenizer.add_special_tokens(
                {"additional_special_tokens": list(ENTITY_MARKERS)}
            )
            if added:
                self.model.resize_token_embeddings(len(self.tokenizer))

        device = self.config.device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.device = device
        self.model.to(device)
        self.model.eval()

        # Cache marker token ids for span detection.
        self._mask_id = self.tokenizer.mask_token_id
        self._pers_open_id = self.tokenizer.convert_tokens_to_ids(PERS_OPEN)
        self._pers_close_id = self.tokenizer.convert_tokens_to_ids(PERS_CLOSE)
        self._loc_open_id = self.tokenizer.convert_tokens_to_ids(LOC_OPEN)
        self._loc_close_id = self.tokenizer.convert_tokens_to_ids(LOC_CLOSE)

    @property
    def hidden_size(self) -> int:
        return int(self.model.config.hidden_size)

    @property
    def n_layers_total(self) -> int:
        # +1 for the embedding layer that ``output_hidden_states`` returns.
        return int(self.model.config.num_hidden_layers) + 1

    def _resolve_layer_idx(self, idx: int, n_states: int) -> int:
        """Translate negative indices into absolute positions in ``hidden_states``."""
        return idx if idx >= 0 else n_states + idx

    def render(self, instance: RelationInstance) -> str:
        return build_template(
            instance,
            template=self.config.template,
            field=self.config.field,
            mask_token=self.tokenizer.mask_token,
        )

    @torch.no_grad()
    def encode_instances(
        self,
        instances: Sequence[RelationInstance],
        *,
        progress: bool = True,
    ) -> list[MASKBatch]:
        out: list[MASKBatch] = []
        bs = self.config.batch_size
        n = len(instances)
        ranges = range(0, n, bs)
        if progress:
            from tqdm import tqdm

            ranges = tqdm(list(ranges), desc=f"MASK[{self.config.template}]", unit="batch")
        for start in ranges:
            chunk = instances[start : start + bs]
            out.extend(self._encode_chunk(list(chunk)))
        return out

    def _encode_chunk(self, instances: list[RelationInstance]) -> list[MASKBatch]:
        texts = [self.render(inst) for inst in instances]
        tok = self.tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=self.config.max_seq_length,
            return_tensors="pt",
        )
        ids = tok["input_ids"].to(self.device)
        mask = tok["attention_mask"].to(self.device)
        outputs = self.model(input_ids=ids, attention_mask=mask, output_hidden_states=True)
        hidden_states = outputs.hidden_states  # tuple length L+1
        n_states = len(hidden_states)
        layer_idxs = [self._resolve_layer_idx(li, n_states) for li in self.config.layers]
        last_hidden = hidden_states[-1]  # (B, S, H) — used for span/single-layer ops

        results: list[MASKBatch] = []
        for i, inst in enumerate(instances):
            seq_ids = ids[i]
            last_h = last_hidden[i]  # (S, H)

            # Per-layer mean MASK embeddings → mask_emb_layers
            mask_positions = (seq_ids == self._mask_id).nonzero(as_tuple=False).flatten()
            per_layer_means = []
            for lyr in layer_idxs:
                layer_h = hidden_states[lyr][i]
                if mask_positions.numel() == 0:
                    per_layer_means.append(layer_h[0])  # CLS fallback
                else:
                    per_layer_means.append(layer_h[mask_positions].mean(dim=0))
            mask_emb_layers = torch.cat(per_layer_means, dim=0)
            mask_emb = per_layer_means[-1]  # last requested layer (typically -1)

            # Span embeddings on the last layer only (stable across templates)
            e1_emb, e1_present = self._mean_in_span(
                last_h, seq_ids, self._pers_open_id, self._pers_close_id
            )
            e2_emb, e2_present = self._mean_in_span(
                last_h, seq_ids, self._loc_open_id, self._loc_close_id
            )

            # Template-specific MASK breakdowns (all on the last layer).
            mask_at_emb = mask_isAt_emb = mask_multi_emb = None
            if self.config.template == "M4" and mask_positions.numel() >= 2:
                # First MASK -> at, second MASK -> isAt, per template wording.
                mask_at_emb = last_h[mask_positions[0]]
                mask_isAt_emb = last_h[mask_positions[1]]
            if self.config.template == "M5":
                # Three consecutive masks; concat in document order.
                if mask_positions.numel() >= 1:
                    parts = [last_h[p] for p in mask_positions[:3]]
                    # Pad with zeros if some MASK got truncated (rare, only if
                    # max_seq_length cut the last few tokens).
                    while len(parts) < 3:
                        parts.append(torch.zeros_like(last_h[0]))
                    mask_multi_emb = torch.cat(parts, dim=0)

            results.append(
                MASKBatch(
                    sample_id=inst.sample_id,
                    language=inst.language,
                    at=inst.at,
                    isAt=inst.isAt,
                    mask_emb=mask_emb.cpu().numpy().astype(np.float32),
                    mask_emb_layers=mask_emb_layers.cpu().numpy().astype(np.float32),
                    e1_emb=e1_emb.cpu().numpy().astype(np.float32),
                    e2_emb=e2_emb.cpu().numpy().astype(np.float32),
                    pers_in_context=e1_present,
                    loc_in_context=e2_present,
                    mask_at_emb=(
                        mask_at_emb.cpu().numpy().astype(np.float32)
                        if mask_at_emb is not None
                        else None
                    ),
                    mask_isAt_emb=(
                        mask_isAt_emb.cpu().numpy().astype(np.float32)
                        if mask_isAt_emb is not None
                        else None
                    ),
                    mask_multi_emb=(
                        mask_multi_emb.cpu().numpy().astype(np.float32)
                        if mask_multi_emb is not None
                        else None
                    ),
                )
            )
        return results

    def _mean_in_span(
        self,
        seq_h: torch.Tensor,
        seq_ids: torch.Tensor,
        open_id: int,
        close_id: int,
    ) -> tuple[torch.Tensor, bool]:
        opens = (seq_ids == open_id).nonzero(as_tuple=False).flatten().tolist()
        closes = (seq_ids == close_id).nonzero(as_tuple=False).flatten().tolist()
        if not opens or not closes:
            return torch.zeros_like(seq_h[0]), False
        s = opens[0]
        e_candidates = [c for c in closes if c > s]
        if not e_candidates:
            return torch.zeros_like(seq_h[0]), False
        e = e_candidates[0]
        if e - s <= 1:
            return torch.zeros_like(seq_h[0]), False
        return seq_h[s + 1 : e].mean(dim=0), True


def stack_embeddings(batches: Iterable[MASKBatch]) -> dict[str, np.ndarray | list]:
    """Stack a list of MASKBatch into arrays + parallel metadata.

    Always populates ``mask_emb`` (N,H), ``mask_emb_layers`` (N,L·H),
    ``e1_emb`` (N,H), ``e2_emb`` (N,H), ``concat_emb`` (N,3·H).

    Optionally populates ``mask_at_emb`` / ``mask_isAt_emb`` (M4) and
    ``mask_multi_emb`` (M5) if the batch list carries them.
    """
    items = list(batches)
    if not items:
        return {
            "mask_emb": np.zeros((0, 0), dtype=np.float32),
            "mask_emb_layers": np.zeros((0, 0), dtype=np.float32),
            "e1_emb": np.zeros((0, 0), dtype=np.float32),
            "e2_emb": np.zeros((0, 0), dtype=np.float32),
            "concat_emb": np.zeros((0, 0), dtype=np.float32),
            "sample_id": [],
            "language": [],
            "at": [],
            "isAt": [],
            "pers_in_context": np.zeros((0,), dtype=bool),
            "loc_in_context": np.zeros((0,), dtype=bool),
        }
    mask = np.stack([b.mask_emb for b in items])
    mask_layers = np.stack([b.mask_emb_layers for b in items])
    e1 = np.stack([b.e1_emb for b in items])
    e2 = np.stack([b.e2_emb for b in items])
    out: dict[str, np.ndarray | list] = {
        "mask_emb": mask,
        "mask_emb_layers": mask_layers,
        "e1_emb": e1,
        "e2_emb": e2,
        "concat_emb": np.concatenate([mask, e1, e2], axis=1),
        "sample_id": [b.sample_id for b in items],
        "language": [b.language for b in items],
        "at": [b.at for b in items],
        "isAt": [b.isAt for b in items],
        "pers_in_context": np.array([b.pers_in_context for b in items]),
        "loc_in_context": np.array([b.loc_in_context for b in items]),
    }
    # Optional template-specific arrays — only emit when every batch supplies
    # them so the npz schema is consistent.
    if all(b.mask_at_emb is not None for b in items):
        out["mask_at_emb"] = np.stack([b.mask_at_emb for b in items])
    if all(b.mask_isAt_emb is not None for b in items):
        out["mask_isAt_emb"] = np.stack([b.mask_isAt_emb for b in items])
    if all(b.mask_multi_emb is not None for b in items):
        out["mask_multi_emb"] = np.stack([b.mask_multi_emb for b in items])
    return out
