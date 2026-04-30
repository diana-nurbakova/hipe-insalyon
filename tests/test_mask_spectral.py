"""Tests for ``hipe.mask.spectral``: shape checks + label-NMI sanity."""

from __future__ import annotations

import numpy as np
import pytest

pytest.importorskip("scipy")
pytest.importorskip("sklearn")

from hipe.mask.spectral import (
    SpectralFeatureExtractor,
    compute_spectral_features_full,
    eigenvector_label_nmi,
)


def _three_blob_dataset(seed: int = 0) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    centers = np.array([[5.0, 0.0], [0.0, 5.0], [-5.0, -5.0]])
    n_per = 30
    X = np.vstack([
        centers[i] + rng.normal(scale=0.3, size=(n_per, 2))
        for i in range(3)
    ]).astype(np.float32)
    y = np.repeat(np.arange(3), n_per)
    return X, y


def test_spectral_features_full_shape():
    X, _ = _three_blob_dataset()
    feats, eigvals = compute_spectral_features_full(
        X, n_components=4, n_neighbors=8
    )
    assert feats.shape == (X.shape[0], 4)
    assert eigvals.shape == (4,)
    # Eigenvalues are sorted ascending.
    assert np.all(np.diff(eigvals) >= -1e-6)


def test_spectral_features_capture_blob_structure():
    X, y = _three_blob_dataset()
    feats, _ = compute_spectral_features_full(
        X, n_components=4, n_neighbors=8
    )
    # The first non-trivial eigenvector(s) should encode the 3-cluster
    # structure → high NMI on at least one of the leading components.
    nmis = eigenvector_label_nmi(feats, y, n_bins=3)
    assert max(nmis) > 0.5, f"expected blob structure to surface, got NMIs={nmis}"


def test_spectral_extractor_train_returns_cached_eigenvectors():
    X, _ = _three_blob_dataset()
    extractor = SpectralFeatureExtractor(n_components=3, n_neighbors=6).fit(X)
    Z = extractor.transform(X)
    assert Z.shape == (X.shape[0], 3)
    assert np.allclose(Z, extractor.train_eigvecs_)


def test_spectral_extractor_nystrom_extends_to_new_points():
    X, _ = _three_blob_dataset()
    extractor = SpectralFeatureExtractor(n_components=3, n_neighbors=6).fit(X)
    rng = np.random.default_rng(1)
    new_pts = X[:5] + rng.normal(scale=0.05, size=(5, 2)).astype(np.float32)
    Z_new = extractor.transform(new_pts)
    assert Z_new.shape == (5, 3)
    assert np.all(np.isfinite(Z_new))
    # Nearby copies should land near their source's eigenvector.
    Z_train = extractor.transform(X)
    for i in range(5):
        assert np.linalg.norm(Z_new[i] - Z_train[i]) < 0.5
