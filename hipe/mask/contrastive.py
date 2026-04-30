"""Supervised + ordinal contrastive losses and the MLP classifier head
described in MASK Experiment Spec §6 / Prompting & MASK Spec §9.

Components
----------
* :class:`SupConLoss`   — standard supervised contrastive loss (Khosla 2020).
* :class:`OrdinalContrastiveLoss` — margin-scaled push for the ordinal `at`
  label (FALSE < PROBABLE < TRUE) so PROBABLE ends up between TRUE and FALSE.
* :class:`BalancedContrastiveSampler` — yields class-balanced batches by
  oversampling the minority class with replacement (Spec §9.5).
* :class:`ContrastiveRelationClassifier` — shared MLP encoder + projection
  head (training-only) + per-task linear classification heads.
* :func:`train_contrastive` / :func:`predict` — single-file train/eval loop
  over fixed feature matrices (numpy → tensors), so the module is fully
  decoupled from the BERT extraction step.

Design notes
~~~~~~~~~~~~
The classifier consumes precomputed feature matrices (typically
``mask + e1 + e2 + temporal``). We don't fine-tune BERT here — the spec
distinguishes "frozen encoder + supervised head" (this module) from the
optional Phase-3 fine-tuning experiment, which is out of scope.

The contrastive loss is purely a *training-time regulariser*. The projection
head is discarded at inference; only the per-task linear heads are used.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Iterable

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


# ---------------------------------------------------------------------------
# Label utilities
# ---------------------------------------------------------------------------

AT_LABELS = ("FALSE", "PROBABLE", "TRUE")
ISAT_LABELS = ("FALSE", "TRUE")
AT_TO_IDX = {lbl: i for i, lbl in enumerate(AT_LABELS)}
ISAT_TO_IDX = {lbl: i for i, lbl in enumerate(ISAT_LABELS)}

# Ordinal positions — equal to the index above for `at` (FALSE=0, PROBABLE=1, TRUE=2).
AT_ORDINAL = AT_TO_IDX


def encode_labels(labels: list[str] | np.ndarray, mapping: dict[str, int]) -> np.ndarray:
    """Convert string labels to integer ids; raise on unknown labels."""
    out = np.empty(len(labels), dtype=np.int64)
    for i, lbl in enumerate(labels):
        out[i] = mapping[str(lbl)]
    return out


# ---------------------------------------------------------------------------
# Losses
# ---------------------------------------------------------------------------


class SupConLoss(nn.Module):
    """Supervised Contrastive Loss (Khosla et al., NeurIPS 2020).

    Treats all non-matching classes equally. Suitable as a baseline and for
    the binary ``isAt`` task. Inputs are L2-normalised projection vectors.
    """

    def __init__(self, temperature: float = 0.07) -> None:
        super().__init__()
        self.temperature = float(temperature)

    def forward(self, features: torch.Tensor, labels: torch.Tensor) -> torch.Tensor:
        if features.dim() != 2:
            raise ValueError(f"features must be 2D, got {tuple(features.shape)}")
        device = features.device
        batch_size = features.shape[0]
        if batch_size < 2:
            return features.new_zeros(())

        # Pairwise similarity / temperature
        similarity = torch.matmul(features, features.T) / self.temperature

        labels = labels.view(-1)
        labels_eq = (labels.unsqueeze(0) == labels.unsqueeze(1)).float()
        self_mask = torch.eye(batch_size, device=device)
        positive_mask = labels_eq - self_mask  # exclude self-pairs

        # Numerical stability
        logits_max, _ = similarity.max(dim=1, keepdim=True)
        logits = similarity - logits_max.detach()

        # log p over all non-self entries
        exp_logits = torch.exp(logits) * (1 - self_mask)
        denom = exp_logits.sum(dim=1, keepdim=True).clamp_min(1e-12)
        log_prob = logits - torch.log(denom)

        # Anchors with no positives contribute zero
        n_pos = positive_mask.sum(dim=1)
        valid = n_pos > 0
        if not valid.any():
            return features.new_zeros(())
        mean_log_prob = (positive_mask * log_prob).sum(dim=1) / n_pos.clamp_min(1)
        return -mean_log_prob[valid].mean()


class OrdinalContrastiveLoss(nn.Module):
    """Distance-based contrastive loss whose push margin scales with ordinal
    distance between class indices (Spec §9.3.2).

    Pull: same-class embeddings towards each other (squared distance).
    Push: different-class embeddings apart with margin = base_margin · |Δordinal|.

    Input ``labels`` are integer ordinal positions (e.g. FALSE=0, PROBABLE=1,
    TRUE=2). Embeddings are L2-normalised inside the loss.
    """

    def __init__(
        self,
        base_margin: float = 0.5,
        pull_weight: float = 1.0,
        push_weight: float = 1.0,
    ) -> None:
        super().__init__()
        self.base_margin = float(base_margin)
        self.pull_weight = float(pull_weight)
        self.push_weight = float(push_weight)

    def forward(self, embeddings: torch.Tensor, labels: torch.Tensor) -> torch.Tensor:
        embeddings = F.normalize(embeddings, dim=1)
        batch_size = embeddings.shape[0]
        if batch_size < 2:
            return embeddings.new_zeros(())
        device = embeddings.device

        ordinals = labels.float().view(-1)
        # Use Euclidean distance on unit sphere; ranges in [0, 2].
        dists = torch.cdist(embeddings.unsqueeze(0), embeddings.unsqueeze(0)).squeeze(0)

        same_mask = (ordinals.unsqueeze(0) == ordinals.unsqueeze(1)).float()
        self_mask = torch.eye(batch_size, device=device)
        same_mask = same_mask - self_mask  # exclude diagonal

        # Pull
        pull_count = same_mask.sum().clamp_min(1)
        pull_loss = (same_mask * dists.pow(2)).sum() / pull_count

        # Push (different-class pairs, margin = base_margin * |Δordinal|)
        diff_mask = 1.0 - same_mask - self_mask
        ordinal_dists = (ordinals.unsqueeze(0) - ordinals.unsqueeze(1)).abs()
        margins = self.base_margin * ordinal_dists
        push_count = diff_mask.sum().clamp_min(1)
        push_loss = (diff_mask * F.relu(margins - dists).pow(2)).sum() / push_count

        return self.pull_weight * pull_loss + self.push_weight * push_loss


# ---------------------------------------------------------------------------
# Sampler
# ---------------------------------------------------------------------------


class BalancedContrastiveSampler:
    """Yield class-balanced batches over a fixed integer label array.

    Each batch contains ``k_per_class`` instances per class (with replacement
    when a class has fewer than ``k_per_class`` items). One *epoch* covers
    ``ceil(n / batch_size)`` batches so total training work scales with the
    dataset size.
    """

    def __init__(self, labels: np.ndarray, k_per_class: int = 16, seed: int = 42) -> None:
        labels = np.asarray(labels, dtype=np.int64)
        self.labels = labels
        self.k = int(k_per_class)
        self.classes = sorted(set(labels.tolist()))
        self.batch_size = self.k * len(self.classes)
        self.class_indices = {
            c: np.where(labels == c)[0] for c in self.classes
        }
        for c, idx in self.class_indices.items():
            if idx.size == 0:
                raise ValueError(f"Class {c} has no examples in the label array.")
        self.rng = np.random.default_rng(seed)

    def __iter__(self) -> Iterable[np.ndarray]:
        n_batches = max(1, math.ceil(len(self.labels) / self.batch_size))
        for _ in range(n_batches):
            yield self.sample_batch()

    def __len__(self) -> int:
        return max(1, math.ceil(len(self.labels) / self.batch_size))

    def sample_batch(self) -> np.ndarray:
        batch = []
        for c in self.classes:
            pool = self.class_indices[c]
            replace = pool.size < self.k
            picks = self.rng.choice(pool, size=self.k, replace=replace)
            batch.append(picks)
        out = np.concatenate(batch)
        self.rng.shuffle(out)
        return out


# ---------------------------------------------------------------------------
# Classifier
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class ContrastiveModelConfig:
    input_dim: int
    hidden_dim: int = 256
    bottleneck_dim: int = 512
    projection_dim: int = 128
    dropout: float = 0.1
    n_at_classes: int = 3
    n_isAt_classes: int = 2


class ContrastiveRelationClassifier(nn.Module):
    """Shared MLP encoder + projection head + per-task linear heads.

    Forward returns ``(at_logits, isAt_logits)``. Set ``return_projection=True``
    to additionally retrieve the L2-normalised projection vector used by the
    contrastive losses.
    """

    def __init__(self, cfg: ContrastiveModelConfig) -> None:
        super().__init__()
        self.cfg = cfg
        self.encoder = nn.Sequential(
            nn.Linear(cfg.input_dim, cfg.bottleneck_dim),
            nn.ReLU(),
            nn.Dropout(cfg.dropout),
            nn.Linear(cfg.bottleneck_dim, cfg.hidden_dim),
            nn.ReLU(),
            nn.Dropout(cfg.dropout),
        )
        self.projection = nn.Sequential(
            nn.Linear(cfg.hidden_dim, cfg.projection_dim),
            nn.ReLU(),
            nn.Linear(cfg.projection_dim, cfg.projection_dim),
        )
        self.at_head = nn.Linear(cfg.hidden_dim, cfg.n_at_classes)
        self.isAt_head = nn.Linear(cfg.hidden_dim, cfg.n_isAt_classes)

    def forward(
        self,
        x: torch.Tensor,
        *,
        return_projection: bool = False,
    ) -> tuple[torch.Tensor, torch.Tensor] | tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        h = self.encoder(x)
        at_logits = self.at_head(h)
        isAt_logits = self.isAt_head(h)
        if return_projection:
            z = F.normalize(self.projection(h), dim=1)
            return at_logits, isAt_logits, z
        return at_logits, isAt_logits


# ---------------------------------------------------------------------------
# Train / predict
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class TrainConfig:
    epochs: int = 20
    lr: float = 2e-4
    weight_decay: float = 1e-4
    alpha: float = 0.7  # CE weight; (1-alpha) is contrastive weight
    contrastive_at: str = "ordinal"  # "ordinal" | "supcon" | "none"
    contrastive_isAt: str = "supcon"  # "supcon" | "none"
    base_margin: float = 0.5
    temperature: float = 0.07
    k_per_class_at: int = 16  # batch_size = k_per_class * 3 for at
    early_stopping_patience: int = 5
    grad_clip: float = 1.0
    seed: int = 42
    device: str | None = None
    log_every: int = 1
    class_weights_at: tuple[float, ...] | None = None
    class_weights_isAt: tuple[float, ...] | None = None
    # Standardisation: fit a feature-mean/std on train and apply to all
    # forward passes. Defaults on because LR baselines do this and want
    # parity for fair feature-set comparisons.
    standardise: bool = True


@dataclass(slots=True)
class TrainResult:
    model: ContrastiveRelationClassifier
    best_epoch: int
    best_val_score: float
    history: list[dict] = field(default_factory=list)
    feature_mean: np.ndarray | None = None
    feature_std: np.ndarray | None = None


def _compute_class_weights(y: np.ndarray, n_classes: int) -> torch.Tensor:
    counts = np.bincount(y, minlength=n_classes).astype(np.float64)
    counts = np.where(counts == 0, 1.0, counts)
    inv = 1.0 / counts
    weights = inv * (n_classes / inv.sum())
    return torch.tensor(weights, dtype=torch.float32)


def _macro_recall(y_true: np.ndarray, y_pred: np.ndarray, n_classes: int) -> float:
    recalls = []
    for c in range(n_classes):
        mask = y_true == c
        if mask.sum() == 0:
            continue
        recalls.append((y_pred[mask] == c).mean())
    return float(np.mean(recalls)) if recalls else 0.0


def train_contrastive(
    X_train: np.ndarray,
    at_train: np.ndarray,
    isAt_train: np.ndarray,
    *,
    X_val: np.ndarray | None = None,
    at_val: np.ndarray | None = None,
    isAt_val: np.ndarray | None = None,
    model_cfg: ContrastiveModelConfig | None = None,
    train_cfg: TrainConfig | None = None,
) -> TrainResult:
    """Train the contrastive classifier on precomputed features.

    The validation set, when provided, is used for early stopping by tracking
    the mean of macro-recall(at) and macro-recall(isAt) — the same global
    score the official evaluator reports. When ``X_val`` is None, the best
    model is the one at the last epoch.
    """
    cfg_train = train_cfg or TrainConfig()
    if model_cfg is None:
        model_cfg = ContrastiveModelConfig(input_dim=X_train.shape[1])
    if model_cfg.input_dim != X_train.shape[1]:
        raise ValueError(
            f"model_cfg.input_dim ({model_cfg.input_dim}) "
            f"!= X_train feature dim ({X_train.shape[1]})"
        )

    torch.manual_seed(cfg_train.seed)
    np.random.seed(cfg_train.seed)
    device = cfg_train.device or ("cuda" if torch.cuda.is_available() else "cpu")

    # Standardise.
    if cfg_train.standardise:
        feat_mean = X_train.mean(axis=0).astype(np.float32)
        feat_std = X_train.std(axis=0).astype(np.float32)
        feat_std = np.where(feat_std < 1e-6, 1.0, feat_std)
        X_train_s = (X_train - feat_mean) / feat_std
        if X_val is not None:
            X_val_s = (X_val - feat_mean) / feat_std
    else:
        feat_mean = None
        feat_std = None
        X_train_s = X_train.astype(np.float32, copy=False)
        X_val_s = X_val.astype(np.float32, copy=False) if X_val is not None else None

    Xtr_t = torch.from_numpy(np.ascontiguousarray(X_train_s, dtype=np.float32)).to(device)
    at_tr_t = torch.from_numpy(at_train.astype(np.int64)).to(device)
    isAt_tr_t = torch.from_numpy(isAt_train.astype(np.int64)).to(device)

    model = ContrastiveRelationClassifier(model_cfg).to(device)
    optim = torch.optim.AdamW(
        model.parameters(),
        lr=cfg_train.lr,
        weight_decay=cfg_train.weight_decay,
    )

    weights_at = (
        torch.tensor(cfg_train.class_weights_at, dtype=torch.float32).to(device)
        if cfg_train.class_weights_at
        else _compute_class_weights(at_train, model_cfg.n_at_classes).to(device)
    )
    weights_isAt = (
        torch.tensor(cfg_train.class_weights_isAt, dtype=torch.float32).to(device)
        if cfg_train.class_weights_isAt
        else _compute_class_weights(isAt_train, model_cfg.n_isAt_classes).to(device)
    )

    sampler = BalancedContrastiveSampler(
        at_train.astype(np.int64),
        k_per_class=cfg_train.k_per_class_at,
        seed=cfg_train.seed,
    )

    contrastive_at_fn: nn.Module | None = None
    if cfg_train.contrastive_at == "ordinal":
        contrastive_at_fn = OrdinalContrastiveLoss(base_margin=cfg_train.base_margin)
    elif cfg_train.contrastive_at == "supcon":
        contrastive_at_fn = SupConLoss(temperature=cfg_train.temperature)
    elif cfg_train.contrastive_at != "none":
        raise ValueError(f"Unknown contrastive_at: {cfg_train.contrastive_at!r}")

    contrastive_isAt_fn: nn.Module | None = None
    if cfg_train.contrastive_isAt == "supcon":
        contrastive_isAt_fn = SupConLoss(temperature=cfg_train.temperature)
    elif cfg_train.contrastive_isAt != "none":
        raise ValueError(f"Unknown contrastive_isAt: {cfg_train.contrastive_isAt!r}")

    history: list[dict] = []
    best_score = -1.0
    best_epoch = -1
    best_state: dict | None = None
    epochs_no_improve = 0

    for epoch in range(cfg_train.epochs):
        model.train()
        epoch_losses = []
        for batch_indices in sampler:
            x = Xtr_t[batch_indices]
            y_at = at_tr_t[batch_indices]
            y_isAt = isAt_tr_t[batch_indices]
            at_logits, isAt_logits, z = model(x, return_projection=True)

            ce_at = F.cross_entropy(at_logits, y_at, weight=weights_at)
            ce_isAt = F.cross_entropy(isAt_logits, y_isAt, weight=weights_isAt)
            classification_loss = ce_at + ce_isAt

            con_loss = z.new_zeros(())
            if contrastive_at_fn is not None:
                con_loss = con_loss + contrastive_at_fn(z, y_at)
            if contrastive_isAt_fn is not None:
                con_loss = con_loss + contrastive_isAt_fn(z, y_isAt)

            loss = (
                cfg_train.alpha * classification_loss
                + (1.0 - cfg_train.alpha) * con_loss
            )

            optim.zero_grad()
            loss.backward()
            if cfg_train.grad_clip > 0:
                nn.utils.clip_grad_norm_(model.parameters(), cfg_train.grad_clip)
            optim.step()
            epoch_losses.append(loss.item())

        epoch_record: dict = {
            "epoch": epoch,
            "train_loss_mean": float(np.mean(epoch_losses)) if epoch_losses else float("nan"),
        }

        # Validation
        if X_val is not None and at_val is not None and isAt_val is not None:
            val_at_pred, val_isAt_pred, _ = predict(
                model,
                X_val,
                feature_mean=feat_mean,
                feature_std=feat_std,
                device=device,
            )
            val_at_score = _macro_recall(at_val, val_at_pred, model_cfg.n_at_classes)
            val_isAt_score = _macro_recall(isAt_val, val_isAt_pred, model_cfg.n_isAt_classes)
            val_global = 0.5 * (val_at_score + val_isAt_score)
            epoch_record.update({
                "val_macro_recall_at": val_at_score,
                "val_macro_recall_isAt": val_isAt_score,
                "val_global": val_global,
            })

            if val_global > best_score + 1e-6:
                best_score = val_global
                best_epoch = epoch
                best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
                epochs_no_improve = 0
            else:
                epochs_no_improve += 1
        else:
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
            best_epoch = epoch

        if epoch % cfg_train.log_every == 0 or epoch == cfg_train.epochs - 1:
            msg = f"  epoch {epoch:3d}  loss={epoch_record['train_loss_mean']:.4f}"
            if "val_global" in epoch_record:
                msg += (
                    f"  val_global={epoch_record['val_global']:.4f}"
                    f"  val_at={epoch_record['val_macro_recall_at']:.4f}"
                    f"  val_isAt={epoch_record['val_macro_recall_isAt']:.4f}"
                )
            print(msg)
        history.append(epoch_record)

        if (
            X_val is not None
            and cfg_train.early_stopping_patience > 0
            and epochs_no_improve >= cfg_train.early_stopping_patience
        ):
            print(f"  [early stop] no val improvement for "
                  f"{cfg_train.early_stopping_patience} epochs")
            break

    if best_state is not None:
        model.load_state_dict(best_state)
    model.eval()

    return TrainResult(
        model=model,
        best_epoch=best_epoch,
        best_val_score=best_score,
        history=history,
        feature_mean=feat_mean,
        feature_std=feat_std,
    )


def predict(
    model: ContrastiveRelationClassifier,
    X: np.ndarray,
    *,
    feature_mean: np.ndarray | None = None,
    feature_std: np.ndarray | None = None,
    batch_size: int = 256,
    device: str | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Run the trained classifier and return ``(at_pred, isAt_pred, at_proba)``.

    ``at_proba`` is the softmax over `at` (shape (N, 3)) — useful for
    confidence estimates in downstream agentic stages.
    """
    if feature_mean is not None and feature_std is not None:
        Xs = (X - feature_mean) / feature_std
    else:
        Xs = X.astype(np.float32, copy=False)

    device = device or ("cuda" if torch.cuda.is_available() else "cpu")
    model.eval()
    at_logits_all = []
    isAt_logits_all = []
    with torch.no_grad():
        for start in range(0, len(Xs), batch_size):
            chunk = torch.from_numpy(np.ascontiguousarray(Xs[start : start + batch_size],
                                                          dtype=np.float32)).to(device)
            at_logits, isAt_logits = model(chunk)
            at_logits_all.append(at_logits.cpu())
            isAt_logits_all.append(isAt_logits.cpu())
    at_logits = torch.cat(at_logits_all, dim=0)
    isAt_logits = torch.cat(isAt_logits_all, dim=0)
    at_proba = F.softmax(at_logits, dim=1).numpy()
    at_pred = at_logits.argmax(dim=1).numpy()
    isAt_pred = isAt_logits.argmax(dim=1).numpy()
    return at_pred, isAt_pred, at_proba


__all__ = [
    "AT_LABELS", "ISAT_LABELS", "AT_TO_IDX", "ISAT_TO_IDX", "AT_ORDINAL",
    "encode_labels",
    "SupConLoss", "OrdinalContrastiveLoss",
    "BalancedContrastiveSampler",
    "ContrastiveModelConfig", "ContrastiveRelationClassifier",
    "TrainConfig", "TrainResult",
    "train_contrastive", "predict",
]
