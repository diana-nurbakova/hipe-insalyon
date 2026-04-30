"""RAG retriever module: entity-aware embeddings + FAISS index."""

from hipe.retriever.embed import EntityAwareEncoder, format_with_markers
from hipe.retriever.index import FaissIndex
from hipe.retriever.retrieve import RetrievedExample, Retriever

__all__ = [
    "EntityAwareEncoder",
    "format_with_markers",
    "FaissIndex",
    "Retriever",
    "RetrievedExample",
]
