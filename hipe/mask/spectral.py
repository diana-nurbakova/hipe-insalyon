"""Spectral feature extraction for MASK embeddings (Spec §8.6.4).

Builds a sparse k-NN similarity graph from the *training* embeddings,
computes the smallest non-trivial eigenvectors of the normalised Laplacian,
and provides Nyström-style out-of-sample extension so test instances get
the same spectral coordinates without rebuilding the full graph.

The module is deliberately small and dependency-light: it relies on
``scikit-learn`` for the k-NN graph and on ``scipy`` for the sparse
eigendecomposition (both already pinned via the ``ml`` extra).

Typical use:

    from hipe.mask.spectral import SpectralFeatureExtractor

    extractor = SpectralFeatureExtractor(n_components=10, n_neighbors=20).fit(X_train)
    Z_train = extractor.transform(X_train)  # (n_train, n_components)
    Z_test  = extractor.transform(X_test)   # (n_test,  n_components)

The simpler **transductive** path is :func:`compute_spectral_features_full`,
which fits the embedding on the *full dataset* in one shot — appropriate
when we only care about the labels of the same fixed set of instances (e.g.
augmenting the cache that downstream classifiers will train on).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


# ---------------------------------------------------------------------------
# Inductive extractor (fit on train, transform train + test)
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class SpectralFeatureExtractor:
    """Laplacian-eigenmap-style features with Nyström out-of-sample extension.

    Parameters
    ----------
    n_components : int
        Number of non-trivial eigenvectors to keep (the constant eigenvector
        with eigenvalue 0 is always discarded).
    n_neighbors : int
        Size of the k-NN neighbourhood used to build the affinity graph.
    metric : str
        Distance metric; passed through to ``sklearn.neighbors.NearestNeighbors``.
    sigma : float | None
        Heat-kernel bandwidth for the affinity weights ``exp(-d²/σ²)``.
        ``None`` → use the median of the train-set k-NN distances (a robust
        data-driven choice).
    """

    n_components: int = 10
    n_neighbors: int = 20
    metric: str = "cosine"
    sigma: float | None = None

    # Fitted state (populated by .fit())
    train_features_: np.ndarray | None = None
    train_eigvecs_: np.ndarray | None = None
    train_eigvals_: np.ndarray | None = None
    sigma_: float | None = None
    train_degree_: np.ndarray | None = None  # for the symmetric-normalised eigenmaps

    # ------------------------------------------------------------------ #
    def fit(self, X_train: np.ndarray) -> "SpectralFeatureExtractor":
        from scipy.sparse import csgraph
        from scipy.sparse.linalg import eigsh
        from sklearn.neighbors import NearestNeighbors

        X = np.asarray(X_train, dtype=np.float32)
        if X.ndim != 2:
            raise ValueError(f"X_train must be 2D, got shape {X.shape}")
        n = X.shape[0]
        if self.n_components >= n:
            raise ValueError(
                f"n_components={self.n_components} must be < n_train={n}"
            )
        k = min(self.n_neighbors, n - 1)

        # Symmetric weighted k-NN graph with heat-kernel weights.
        nn_model = NearestNeighbors(n_neighbors=k + 1, metric=self.metric).fit(X)
        dists, indices = nn_model.kneighbors(X)
        # Drop the self-edge in column 0
        dists = dists[:, 1:]
        indices = indices[:, 1:]

        # Bandwidth (heat-kernel sigma)
        sigma = float(self.sigma if self.sigma is not None else np.median(dists))
        if sigma <= 0:
            sigma = 1.0
        weights = np.exp(-(dists ** 2) / (sigma ** 2))

        # Build sparse affinity W (symmetrise via max).
        from scipy.sparse import coo_matrix

        rows = np.repeat(np.arange(n), k)
        cols = indices.flatten()
        data = weights.flatten()
        W = coo_matrix((data, (rows, cols)), shape=(n, n)).tocsr()
        W = W.maximum(W.T)  # symmetrise

        # Symmetric normalised Laplacian L_sym = I - D^{-1/2} W D^{-1/2}
        d = np.asarray(W.sum(axis=1)).flatten()
        # Avoid divide-by-zero on isolated nodes
        d_safe = np.where(d > 0, d, 1.0)

        L = csgraph.laplacian(W, normed=True)

        # Smallest n_components+1 eigenvalues (skip the constant eigenvector).
        # ``eigsh(..., which="SM")`` is unreliable for normalised Laplacians;
        # use shift-invert via sigma=0 instead.
        try:
            eigvals, eigvecs = eigsh(
                L, k=self.n_components + 1, sigma=0.0, which="LM"
            )
        except Exception:
            # Fallback: dense decomposition for small graphs.
            from scipy.linalg import eigh

            L_dense = L.toarray() if hasattr(L, "toarray") else np.asarray(L)
            eigvals_full, eigvecs_full = eigh(L_dense)
            eigvals = eigvals_full[: self.n_components + 1]
            eigvecs = eigvecs_full[:, : self.n_components + 1]

        # Sort ascending, drop the trivial smallest eigenvalue.
        order = np.argsort(eigvals)
        eigvals = eigvals[order]
        eigvecs = eigvecs[:, order]
        eigvals = eigvals[1 : self.n_components + 1]
        eigvecs = eigvecs[:, 1 : self.n_components + 1]

        self.train_features_ = X
        self.train_eigvecs_ = eigvecs.astype(np.float32, copy=False)
        self.train_eigvals_ = eigvals.astype(np.float32, copy=False)
        self.sigma_ = sigma
        self.train_degree_ = d_safe.astype(np.float32, copy=False)
        return self

    # ------------------------------------------------------------------ #
    def transform(self, X: np.ndarray) -> np.ndarray:
        """Project ``X`` into the eigenmap coordinates.

        For training points (matched by exact identity to ``X_train``), this
        returns the cached eigenvectors. For new points, we use a Nyström
        extension: weight each query's k nearest *training* neighbours by
        the heat kernel and combine the corresponding eigenvector rows.
        """
        if self.train_eigvecs_ is None:
            raise RuntimeError("Call .fit() before .transform().")
        from sklearn.neighbors import NearestNeighbors

        X = np.asarray(X, dtype=np.float32)
        # Quick path: same array as train.
        if (
            self.train_features_ is not None
            and X.shape == self.train_features_.shape
            and np.shares_memory(X, self.train_features_)
        ):
            return self.train_eigvecs_.copy()

        nn_model = NearestNeighbors(
            n_neighbors=min(self.n_neighbors, len(self.train_features_)),
            metric=self.metric,
        ).fit(self.train_features_)
        dists, indices = nn_model.kneighbors(X)
        weights = np.exp(-(dists ** 2) / (self.sigma_ ** 2))

        # Normalise rows so the projection is a convex combination.
        row_sums = weights.sum(axis=1, keepdims=True)
        row_sums = np.where(row_sums > 0, row_sums, 1.0)
        weights = weights / row_sums

        # Embed each query as the weighted average of neighbour eigenvectors.
        out = np.zeros((X.shape[0], self.n_components), dtype=np.float32)
        for i in range(X.shape[0]):
            out[i] = (
                weights[i, :, None] * self.train_eigvecs_[indices[i]]
            ).sum(axis=0)
        return out

    # ------------------------------------------------------------------ #
    def fit_transform(self, X_train: np.ndarray) -> np.ndarray:
        return self.fit(X_train).transform(X_train)


# ---------------------------------------------------------------------------
# Transductive convenience: full-dataset eigenmap
# ---------------------------------------------------------------------------


def compute_spectral_features_full(
    X: np.ndarray,
    *,
    n_components: int = 10,
    n_neighbors: int = 20,
    metric: str = "cosine",
    sigma: float | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Fit eigenmaps over the *whole* dataset and return ``(features, eigenvalues)``.

    Suitable when downstream classifiers train and evaluate on a fixed,
    closed pool (the official train/test split, in our case). The features
    encode the global manifold structure of the entire pool, which is exactly
    what we want to feed back into supervised classifiers as augmentation.
    """
    extractor = SpectralFeatureExtractor(
        n_components=n_components,
        n_neighbors=n_neighbors,
        metric=metric,
        sigma=sigma,
    )
    feats = extractor.fit_transform(X)
    return feats, extractor.train_eigvals_


# ---------------------------------------------------------------------------
# Diagnostics: eigenvalue spectrum + label NMI
# ---------------------------------------------------------------------------


def eigenvector_label_nmi(
    eigenvectors: np.ndarray,
    labels: np.ndarray,
    *,
    n_bins: int = 3,
) -> list[float]:
    """For each eigenvector, return NMI between its tertile-binned values
    and the integer label array. Useful as a quick "does the spectral
    embedding align with class structure?" check."""
    from sklearn.metrics import normalized_mutual_info_score

    out = []
    for i in range(eigenvectors.shape[1]):
        vals = eigenvectors[:, i]
        cuts = np.percentile(vals, [100 * (j + 1) / n_bins for j in range(n_bins - 1)])
        binned = np.digitize(vals, cuts)
        out.append(float(normalized_mutual_info_score(labels, binned)))
    return out


__all__ = [
    "SpectralFeatureExtractor",
    "compute_spectral_features_full",
    "eigenvector_label_nmi",
]
