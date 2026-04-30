"""Feature-space builders for MCMC subgroup discovery.

Three configurations are supported (Specs v2 §4.3):

    SD-H    handcrafted only (~41 dims)
    SD-HS   handcrafted + spectral eigenvectors (~51 dims)
    SD-HSP  handcrafted + spectral + PCA-MASK (~61 dims)

The handcrafted block is composed of the existing temporal block plus the
new evidence-strength, verb-type, optional location-hierarchy, and language
metadata features. ``build_hybrid_features`` is kept for backward compatibility
with the v1 SD-P configuration (handcrafted ⊕ PCA-MASK, no evidence block).
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Any

import numpy as np

from hipe.data import RelationInstance
from hipe.features import HANDCRAFTED_FEATURE_NAMES
from hipe.features.temporal import TEMPORAL_FEATURE_NAMES, temporal_matrix
from hipe.subgroup_discovery.evidence import (
    EVIDENCE_FEATURE_NAMES,
    VERB_TYPE_FEATURE_NAMES,
    evidence_matrix,
    verb_type_matrix,
)
from hipe.subgroup_discovery.hierarchy import (
    HIERARCHY_FEATURE_NAMES,
    hierarchy_matrix,
)


# ---------------------------------------------------------------------------
# v1 helper: SD-P (handcrafted ⊕ PCA-MASK)
# ---------------------------------------------------------------------------

def build_hybrid_features(
    handcrafted_X: np.ndarray,
    mask_embeddings: np.ndarray,
    *,
    n_pca: int = 20,
    handcrafted_names: Sequence[str] = HANDCRAFTED_FEATURE_NAMES,
    random_state: int = 42,
    verbose: bool = True,
):
    """Concatenate handcrafted features with PCA-reduced MASK embeddings.

    Returns ``(X_hybrid, feature_names, fitted_pca)``.
    """
    from sklearn.decomposition import PCA

    handcrafted_X = np.asarray(handcrafted_X, dtype=np.float32)
    mask_embeddings = np.asarray(mask_embeddings, dtype=np.float32)
    if handcrafted_X.shape[0] != mask_embeddings.shape[0]:
        raise ValueError(
            f"Row count mismatch: handcrafted={handcrafted_X.shape[0]}, "
            f"mask={mask_embeddings.shape[0]}"
        )
    if len(handcrafted_names) != handcrafted_X.shape[1]:
        raise ValueError(
            f"handcrafted_names ({len(handcrafted_names)}) does not match "
            f"handcrafted_X.shape[1] ({handcrafted_X.shape[1]})"
        )

    n_pca = int(min(n_pca, mask_embeddings.shape[1], mask_embeddings.shape[0]))
    pca = PCA(n_components=n_pca, random_state=random_state)
    mask_pca = pca.fit_transform(mask_embeddings)
    if verbose:
        ev = float(pca.explained_variance_ratio_.sum() * 100.0)
        print(f"PCA: {n_pca} components explain {ev:.1f}% of MASK variance")

    X_hybrid = np.hstack([handcrafted_X, mask_pca]).astype(np.float32, copy=False)
    pca_names = [f"MASK_PC{i+1}" for i in range(n_pca)]
    feature_names = list(handcrafted_names) + pca_names
    return X_hybrid, feature_names, pca


def transform_hybrid(
    handcrafted_X: np.ndarray,
    mask_embeddings: np.ndarray,
    pca,
) -> np.ndarray:
    """Apply a fitted hybrid feature transform to new rows."""
    handcrafted_X = np.asarray(handcrafted_X, dtype=np.float32)
    mask_embeddings = np.asarray(mask_embeddings, dtype=np.float32)
    mask_pca = pca.transform(mask_embeddings)
    return np.hstack([handcrafted_X, mask_pca]).astype(np.float32, copy=False)


# ---------------------------------------------------------------------------
# v2 spectral preprocessing
# ---------------------------------------------------------------------------

def spectral_preprocessing_for_sd(
    mask_embeddings: np.ndarray,
    y: np.ndarray | Sequence[str] | None = None,
    *,
    n_components: int = 10,
    n_neighbors: int = 15,
    metric: str = "cosine",
    sigma: float | None = None,
    verbose: bool = True,
    do_subtypes: bool = False,
) -> dict[str, Any]:
    """Run spectral analysis as a preprocessor for SD (Specs v2 §4.2).

    Returns a dict with ``eigenvalues``, ``eigenvectors``, ``n_clusters_suggested``,
    and (optionally) ``probable_subtypes``. The eigenvectors form the
    spectral feature block for SD-HS.
    """
    from hipe.mask.spectral import compute_spectral_features_full

    mask_embeddings = np.asarray(mask_embeddings, dtype=np.float32)
    feats, eigvals = compute_spectral_features_full(
        mask_embeddings,
        n_components=n_components,
        n_neighbors=n_neighbors,
        metric=metric,
        sigma=sigma,
    )
    out: dict[str, Any] = {
        "eigenvalues": eigvals,
        "eigenvectors": feats,
        "n_clusters_suggested": _suggest_clusters(eigvals),
    }
    if verbose:
        gaps = np.diff(eigvals)
        print(f"  spectral eigenvalues : {np.round(eigvals[:6], 4)}")
        if len(gaps) > 0:
            print(f"  spectral gaps        : {np.round(gaps[:5], 4)}")
        print(f"  suggested clusters   : {out['n_clusters_suggested']}")
        if y is not None:
            from hipe.mask.spectral import eigenvector_label_nmi

            y_arr = np.asarray(y).astype(str)
            label_to_idx = {lbl: i for i, lbl in enumerate(np.unique(y_arr))}
            y_int = np.array([label_to_idx[lbl] for lbl in y_arr])
            nmi = eigenvector_label_nmi(feats, y_int, n_bins=3)
            tops = ", ".join(f"{v:.3f}" for v in nmi[: min(5, len(nmi))])
            print(f"  eigenvector NMI(y)   : [{tops}]")

    if do_subtypes and y is not None:
        out["probable_subtypes"] = _probable_subtypes(
            mask_embeddings, np.asarray(y).astype(str)
        )
    return out


def _suggest_clusters(eigenvalues: np.ndarray) -> int:
    """Pick the number of clusters from the largest eigenvalue gap (>=2)."""
    if eigenvalues.size < 2:
        return 1
    gaps = np.diff(eigenvalues)
    return int(np.argmax(gaps) + 2)


def _probable_subtypes(
    mask_embeddings: np.ndarray, y: np.ndarray
) -> dict[str, Any] | None:
    """Subtype the PROBABLE manifold via spectral clustering (§4.2)."""
    from sklearn.cluster import SpectralClustering
    from sklearn.neighbors import kneighbors_graph

    probable_mask = (y == "PROBABLE")
    n_pos = int(probable_mask.sum())
    if n_pos < 6:
        return None
    A = kneighbors_graph(
        mask_embeddings[probable_mask],
        n_neighbors=min(10, n_pos - 1),
        mode="connectivity",
        include_self=False,
    )
    A = 0.5 * (A + A.T)
    out: dict[str, Any] = {"sizes": {}}
    true_centroid = (
        mask_embeddings[y == "TRUE"].mean(axis=0)
        if (y == "TRUE").any()
        else mask_embeddings.mean(axis=0)
    )
    false_centroid = (
        mask_embeddings[y == "FALSE"].mean(axis=0)
        if (y == "FALSE").any()
        else mask_embeddings.mean(axis=0)
    )
    last_subtypes = None
    for k in (2, 3):
        if n_pos < k:
            continue
        sc = SpectralClustering(n_clusters=k, affinity="precomputed", random_state=42)
        sub = sc.fit_predict(A.toarray())
        cluster_info = []
        for st in range(k):
            members = mask_embeddings[probable_mask][sub == st]
            if len(members) == 0:
                continue
            d_t = float(np.linalg.norm(members.mean(0) - true_centroid))
            d_f = float(np.linalg.norm(members.mean(0) - false_centroid))
            cluster_info.append(
                {
                    "subtype": int(st),
                    "size": int((sub == st).sum()),
                    "closer_to": "TRUE" if d_t < d_f else "FALSE",
                    "d_TRUE": d_t,
                    "d_FALSE": d_f,
                }
            )
        out[f"k={k}"] = cluster_info
        last_subtypes = sub
    out["assignments"] = last_subtypes.tolist() if last_subtypes is not None else None
    return out


# ---------------------------------------------------------------------------
# v2 unified feature builder
# ---------------------------------------------------------------------------

_LANG_CODES: tuple[str, ...] = ("en", "fr", "de", "lb")
_LANG_FEATURE_NAMES: tuple[str, ...] = tuple(f"lang_{lc}" for lc in _LANG_CODES)


def _language_matrix(instances: Iterable[RelationInstance]) -> np.ndarray:
    insts = list(instances)
    rows = np.zeros((len(insts), len(_LANG_CODES)), dtype=np.float32)
    for i, inst in enumerate(insts):
        lang = (inst.language or "").lower()
        if lang in _LANG_CODES:
            rows[i, _LANG_CODES.index(lang)] = 1.0
    return rows


def build_sd_feature_matrix(
    instances: Sequence[RelationInstance],
    mask_embeddings: np.ndarray | None = None,
    *,
    config: str = "SD-HS",
    hierarchy_cache: dict | None = None,
    spectral_n_components: int = 10,
    spectral_n_neighbors: int = 15,
    pca_n_components: int = 10,
    random_state: int = 42,
    verbose: bool = True,
):
    """Build the SD feature matrix for the requested config (Specs v2 §4.5).

    Parameters
    ----------
    instances : sequence of RelationInstance
    mask_embeddings : (N, D) array or None
        Required for ``SD-HS`` and ``SD-HSP``. Ignored for ``SD-H``.
    config : {'SD-H', 'SD-HS', 'SD-HSP'}
    hierarchy_cache : optional Wikidata P131 hierarchy cache. If None, the
        hierarchy block contributes only the direct mention count plus zeros.
    """
    config = config.upper()
    if config not in {"SD-H", "SD-HS", "SD-HSP"}:
        raise ValueError(f"unknown config {config!r}; choose SD-H / SD-HS / SD-HSP")

    insts = list(instances)
    blocks: list[np.ndarray] = []
    feature_names: list[str] = []

    # 1. Temporal block (15)
    blocks.append(temporal_matrix(insts))
    feature_names.extend(TEMPORAL_FEATURE_NAMES)

    # 2. Evidence (13)
    blocks.append(evidence_matrix(insts))
    feature_names.extend(EVIDENCE_FEATURE_NAMES)

    # 3. Verb type (7)
    blocks.append(verb_type_matrix(insts))
    feature_names.extend(VERB_TYPE_FEATURE_NAMES)

    # 4. Optional Wikidata location hierarchy (3)
    blocks.append(hierarchy_matrix(insts, hierarchy_cache))
    feature_names.extend(HIERARCHY_FEATURE_NAMES)

    # 5. Language one-hot (4)
    blocks.append(_language_matrix(insts))
    feature_names.extend(_LANG_FEATURE_NAMES)

    X = np.hstack(blocks).astype(np.float32, copy=False)
    if verbose:
        print(f"  handcrafted block    : {X.shape[1]}-d")

    spectral_meta: dict[str, Any] | None = None
    if config in ("SD-HS", "SD-HSP"):
        if mask_embeddings is None:
            raise ValueError(f"config {config!r} requires --mask-embeddings")
        spectral_meta = spectral_preprocessing_for_sd(
            mask_embeddings,
            y=np.array([inst.at for inst in insts]),
            n_components=spectral_n_components,
            n_neighbors=spectral_n_neighbors,
            verbose=verbose,
        )
        ev = spectral_meta["eigenvectors"].astype(np.float32, copy=False)
        X = np.hstack([X, ev]).astype(np.float32, copy=False)
        feature_names.extend(
            f"spectral_EV{i+2}" for i in range(ev.shape[1])
        )

    pca_meta = None
    if config == "SD-HSP":
        from sklearn.decomposition import PCA

        n_pca = int(min(pca_n_components, mask_embeddings.shape[1], mask_embeddings.shape[0]))
        pca_meta = PCA(n_components=n_pca, random_state=random_state)
        mask_pca = pca_meta.fit_transform(mask_embeddings).astype(np.float32, copy=False)
        if verbose:
            ev = float(pca_meta.explained_variance_ratio_.sum() * 100.0)
            print(f"  PCA-MASK             : {n_pca} comps ({ev:.1f}% var)")
        X = np.hstack([X, mask_pca]).astype(np.float32, copy=False)
        feature_names.extend(f"MASK_PC{i+1}" for i in range(n_pca))

    if verbose:
        print(f"Config {config}: {X.shape[1]} total features (rows: {X.shape[0]})")

    return X, feature_names, {"spectral": spectral_meta, "pca": pca_meta}
