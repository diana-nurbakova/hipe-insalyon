"""FAISS-backed dense index with on-disk persistence.

Uses ``IndexFlatIP`` over L2-normalised vectors → inner product equals
cosine similarity. Suitable for the HIPE-2026 train pool size (~1K rows);
swap to IVF-PQ when the index grows past ~100K.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import faiss
import numpy as np
import orjson


@dataclass(slots=True)
class FaissIndex:
    index: faiss.Index
    metadata: list[dict[str, Any]]
    dim: int

    @classmethod
    def build(
        cls,
        embeddings: np.ndarray,
        metadata: list[dict[str, Any]],
    ) -> FaissIndex:
        if embeddings.ndim != 2:
            raise ValueError(f"embeddings must be 2-D, got shape {embeddings.shape}")
        if len(embeddings) != len(metadata):
            raise ValueError(
                f"embeddings ({len(embeddings)}) and metadata ({len(metadata)}) must align"
            )
        emb = np.ascontiguousarray(embeddings, dtype=np.float32)
        dim = emb.shape[1]
        index = faiss.IndexFlatIP(dim)
        index.add(emb)
        return cls(index=index, metadata=list(metadata), dim=dim)

    def search(self, query: np.ndarray, k: int = 5) -> tuple[np.ndarray, np.ndarray]:
        if query.ndim == 1:
            query = query[None, :]
        q = np.ascontiguousarray(query, dtype=np.float32)
        scores, idx = self.index.search(q, k)
        return scores, idx

    def save(self, dir_path: str | Path) -> None:
        d = Path(dir_path)
        d.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(d / "index.faiss"))
        with (d / "metadata.jsonl").open("wb") as f:
            for m in self.metadata:
                f.write(orjson.dumps(m))
                f.write(b"\n")
        with (d / "config.json").open("wb") as f:
            f.write(orjson.dumps({"dim": self.dim, "size": len(self.metadata)}))

    @classmethod
    def load(cls, dir_path: str | Path) -> FaissIndex:
        d = Path(dir_path)
        index = faiss.read_index(str(d / "index.faiss"))
        metadata: list[dict[str, Any]] = []
        with (d / "metadata.jsonl").open("rb") as f:
            for raw in f:
                if raw.strip():
                    metadata.append(orjson.loads(raw))
        return cls(index=index, metadata=metadata, dim=index.d)

    def __len__(self) -> int:
        return len(self.metadata)
