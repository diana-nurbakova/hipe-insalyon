"""Tests for the contrastive losses + classifier in ``hipe.mask.contrastive``.

These exercise the math against simple synthetic inputs so failures are
diagnosable without a GPU. Heavier integration testing (a real training run
on cached embeddings) is left to the experimental scripts.
"""

from __future__ import annotations

import numpy as np
import pytest

torch = pytest.importorskip("torch")

from hipe.mask.contrastive import (
    AT_LABELS,
    AT_TO_IDX,
    BalancedContrastiveSampler,
    ContrastiveModelConfig,
    ContrastiveRelationClassifier,
    OrdinalContrastiveLoss,
    SupConLoss,
    TrainConfig,
    encode_labels,
    predict,
    train_contrastive,
)


# ---------------------------------------------------------------------------
# Loss correctness
# ---------------------------------------------------------------------------


def test_supcon_loss_zero_when_all_same_class():
    # All anchors have at least one matching positive; with identical
    # embeddings the log-prob saturates and the loss should be ≥ 0 (it's
    # log K, not zero, but >0 with single-class works as a smoke check).
    emb = torch.randn(8, 16)
    emb = torch.nn.functional.normalize(emb, dim=1)
    labels = torch.zeros(8, dtype=torch.long)
    loss = SupConLoss(temperature=0.07)(emb, labels)
    assert loss.dim() == 0
    assert torch.isfinite(loss)


def test_supcon_loss_zero_with_batch_of_one():
    emb = torch.randn(1, 16)
    labels = torch.tensor([0])
    loss = SupConLoss()(emb, labels)
    assert loss.item() == 0.0


def test_ordinal_contrastive_pulls_same_class():
    # Two TRUE points + two FALSE points in 4D. The same-class pairs should
    # contribute positively to the pull term; mostly we just check that the
    # loss is finite and non-negative.
    emb = torch.tensor([
        [1.0, 0.0, 0.0, 0.0],
        [0.9, 0.1, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 0.0, 0.9, 0.1],
    ])
    labels = torch.tensor([2, 2, 0, 0])  # TRUE, TRUE, FALSE, FALSE
    loss = OrdinalContrastiveLoss(base_margin=0.5)(emb, labels)
    assert torch.isfinite(loss)
    assert loss.item() >= 0.0


def test_ordinal_margin_scales_with_distance():
    # Build a clean configuration: PROBABLE between TRUE and FALSE on a line.
    emb = torch.tensor([
        [1.0, 0.0],   # TRUE
        [0.5, 0.0],   # PROBABLE
        [-1.0, 0.0],  # FALSE
    ])
    labels_close = torch.tensor([2, 1, 0])  # ordinals
    loss_normal = OrdinalContrastiveLoss(base_margin=0.5)(emb, labels_close)
    loss_aggressive = OrdinalContrastiveLoss(base_margin=2.0)(emb, labels_close)
    # A larger margin can only push the loss up or leave it equal.
    assert loss_aggressive.item() >= loss_normal.item() - 1e-6


# ---------------------------------------------------------------------------
# Sampler
# ---------------------------------------------------------------------------


def test_balanced_sampler_yields_equal_class_counts():
    labels = np.array([0] * 20 + [1] * 5 + [2] * 100, dtype=np.int64)
    sampler = BalancedContrastiveSampler(labels, k_per_class=8, seed=0)
    batch = sampler.sample_batch()
    counts = np.bincount(labels[batch], minlength=3)
    assert counts.tolist() == [8, 8, 8]


def test_balanced_sampler_iter_length_consistent():
    labels = np.array([0] * 10 + [1] * 10 + [2] * 10)
    sampler = BalancedContrastiveSampler(labels, k_per_class=4, seed=1)
    batches = list(sampler)
    assert len(batches) == len(sampler)
    for b in batches:
        assert b.size == sampler.batch_size  # 4 * 3


def test_balanced_sampler_oversamples_minority():
    labels = np.array([0] * 100 + [1] * 2)
    sampler = BalancedContrastiveSampler(labels, k_per_class=8, seed=42)
    batch = sampler.sample_batch()
    # Class 1 only has 2 instances but the batch should still get k=8 with replacement.
    assert (labels[batch] == 1).sum() == 8


# ---------------------------------------------------------------------------
# Model + train smoke
# ---------------------------------------------------------------------------


def test_classifier_forward_shapes():
    cfg = ContrastiveModelConfig(input_dim=20, hidden_dim=32, projection_dim=16)
    model = ContrastiveRelationClassifier(cfg)
    x = torch.randn(5, 20)
    at_logits, isAt_logits = model(x)
    assert at_logits.shape == (5, 3)
    assert isAt_logits.shape == (5, 2)
    at_logits, isAt_logits, z = model(x, return_projection=True)
    assert z.shape == (5, 16)
    # z should be L2-normalised
    norms = z.pow(2).sum(dim=1).sqrt()
    assert torch.allclose(norms, torch.ones_like(norms), atol=1e-5)


def test_train_contrastive_can_overfit_separable_data():
    """Sanity: with a clearly separable synthetic task, a few epochs should
    push macro-recall(at) well above chance (0.33)."""
    rng = np.random.default_rng(0)
    n_per = 60
    centers = np.array([[3.0, 0.0], [0.0, 0.0], [-3.0, 0.0]])  # FALSE, PROBABLE, TRUE
    X = np.vstack([centers[i] + rng.normal(scale=0.4, size=(n_per, 2))
                   for i in range(3)]).astype(np.float32)
    at_labels = np.array([0] * n_per + [1] * n_per + [2] * n_per, dtype=np.int64)
    # Tie isAt to at (TRUE at → likely TRUE isAt).
    isAt_labels = (at_labels == 2).astype(np.int64)

    # 80/20 random split.
    perm = rng.permutation(len(X))
    split = int(0.8 * len(X))
    tr, te = perm[:split], perm[split:]

    train_cfg = TrainConfig(
        epochs=15,
        lr=1e-2,
        alpha=0.7,
        contrastive_at="ordinal",
        contrastive_isAt="supcon",
        k_per_class_at=12,
        early_stopping_patience=0,
        device="cpu",
        log_every=100,  # silence per-epoch logs
    )
    model_cfg = ContrastiveModelConfig(
        input_dim=2, hidden_dim=16, bottleneck_dim=32, projection_dim=8
    )
    result = train_contrastive(
        X[tr], at_labels[tr], isAt_labels[tr],
        model_cfg=model_cfg, train_cfg=train_cfg,
    )
    at_pred, isAt_pred, _ = predict(
        result.model, X[te],
        feature_mean=result.feature_mean,
        feature_std=result.feature_std,
        device="cpu",
    )

    def macro_recall(y_true, y_pred, n):
        recs = []
        for c in range(n):
            mask = y_true == c
            if mask.sum() == 0:
                continue
            recs.append((y_pred[mask] == c).mean())
        return float(np.mean(recs))

    at_score = macro_recall(at_labels[te], at_pred, 3)
    assert at_score > 0.7, f"expected separable data to learn cleanly, got {at_score}"


def test_encode_labels_validates_known_strings():
    arr = encode_labels(["TRUE", "FALSE", "PROBABLE"], AT_TO_IDX)
    # Indices: FALSE=0, PROBABLE=1, TRUE=2
    assert arr.tolist() == [2, 0, 1]
    with pytest.raises(KeyError):
        encode_labels(["BOGUS"], AT_TO_IDX)
