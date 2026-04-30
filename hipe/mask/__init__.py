"""MASK-based encoder approach (Spec: Prompting & MASK §M, Experiment Spec).

Wraps an MLM (default ``dbmdz/bert-base-historic-multilingual-cased``)
with entity markers ``[E1]/[/E1]`` (person) and ``[E2]/[/E2]`` (location)
plus a ``[MASK]`` token in a relation template. The hidden state at the
MASK position is the ``mask_emb`` used as input to a downstream classifier.

Modules
-------
- ``encoder``       : single-instance encoding (multi-layer aware)
- ``templates``     : five MLM templates M1–M5
- ``contrastive``   : SupCon / OrdinalContrastive losses + MLP classifier
- ``spectral``      : Laplacian-eigenmap features (transductive + inductive)
"""

from hipe.mask.encoder import MASKBatch, MASKEncoder, MASKEncoderConfig
from hipe.mask.templates import (
    DEFAULT_TEMPLATE,
    LOC_CLOSE,
    LOC_OPEN,
    PERS_CLOSE,
    PERS_OPEN,
    build_template,
    locate_entity_spans,
)

__all__ = [
    "MASKEncoder",
    "MASKEncoderConfig",
    "MASKBatch",
    "DEFAULT_TEMPLATE",
    "PERS_OPEN", "PERS_CLOSE", "LOC_OPEN", "LOC_CLOSE",
    "build_template",
    "locate_entity_spans",
]
