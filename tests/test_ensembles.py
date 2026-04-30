"""Tests for the new ensemble + bootstrap helpers (Spec v0.9 §13.2).

Covers:
- :func:`scripts.bootstrap_confidence.bootstrap_global_score` — point estimate
  matches :func:`compute_global_score`, CI is bracketed correctly, and a
  fixed seed produces reproducible bounds.
- ``scripts/build_three_way_ensemble.py`` flip rule (RF FALSE & LLM PROBABLE
  -> PROBABLE) via subprocess invocation.
- ``scripts/build_per_language_ensemble.py`` routing by language tag.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]


# ---------------------------------------------------------------------------
# bootstrap_confidence
# ---------------------------------------------------------------------------


def _bootstrap_module():
    """Import the script as a module (it has no package init)."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "bootstrap_confidence",
        PROJECT_ROOT / "scripts" / "bootstrap_confidence.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_bootstrap_point_matches_compute_global_score():
    from hipe.evaluation.metrics import compute_global_score

    bc = _bootstrap_module()
    at_g = ["TRUE", "PROBABLE", "FALSE", "FALSE", "TRUE", "PROBABLE", "FALSE"]
    at_p = ["TRUE", "PROBABLE", "FALSE", "TRUE", "TRUE", "FALSE", "FALSE"]
    is_g = ["TRUE", "FALSE", "FALSE", "FALSE", "TRUE", "FALSE", "FALSE"]
    is_p = ["TRUE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE", "FALSE"]

    out = bc.bootstrap_global_score(at_g, at_p, is_g, is_p, n_bootstrap=200, seed=42)
    direct = compute_global_score(at_g, at_p, is_g, is_p)

    assert out["global_score"]["point"] == pytest.approx(direct["global_score"])
    assert out["macro_recall_at"]["point"] == pytest.approx(direct["macro_recall_at"])
    assert out["macro_recall_isAt"]["point"] == pytest.approx(direct["macro_recall_isAt"])


def test_bootstrap_ci_brackets_point():
    bc = _bootstrap_module()
    at_g = ["TRUE", "PROBABLE", "FALSE"] * 10
    at_p = ["TRUE", "FALSE", "FALSE"] * 10
    is_g = ["TRUE", "FALSE", "FALSE"] * 10
    is_p = ["TRUE", "FALSE", "FALSE"] * 10

    out = bc.bootstrap_global_score(at_g, at_p, is_g, is_p, n_bootstrap=300, seed=7)
    g = out["global_score"]
    # The bootstrap mean and point should fall within (or right at the
    # boundary of) the 95% CI. Use a small tolerance for float jitter when
    # the resampled distribution is degenerate (low-variance toy inputs).
    eps = 1e-9
    assert g["ci_lower"] - eps <= g["bootstrap_mean"] <= g["ci_upper"] + eps
    assert g["ci_lower"] - eps <= g["point"] <= g["ci_upper"] + eps
    # Bounds are consistent.
    assert g["ci_lower"] <= g["ci_upper"]


def test_bootstrap_seed_reproducibility():
    bc = _bootstrap_module()
    at_g = ["TRUE", "FALSE", "PROBABLE", "FALSE", "TRUE"]
    at_p = ["TRUE", "FALSE", "PROBABLE", "TRUE", "FALSE"]
    is_g = ["TRUE", "FALSE", "FALSE", "FALSE", "TRUE"]
    is_p = ["TRUE", "FALSE", "FALSE", "FALSE", "FALSE"]

    a = bc.bootstrap_global_score(at_g, at_p, is_g, is_p, n_bootstrap=100, seed=11)
    b = bc.bootstrap_global_score(at_g, at_p, is_g, is_p, n_bootstrap=100, seed=11)
    assert a["global_score"]["bootstrap_mean"] == b["global_score"]["bootstrap_mean"]
    assert a["global_score"]["ci_lower"] == b["global_score"]["ci_lower"]


# ---------------------------------------------------------------------------
# Three-way ensemble (subprocess — exercises CLI + flip rule end-to-end)
# ---------------------------------------------------------------------------


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def test_three_way_ensemble_flips_rf_false_when_llm_says_probable(tmp_path):
    rf = [
        {"document_id": "d", "pers_entity_id": "p", "loc_entity_id": "l1",
         "language": "fr",
         "at_predicted": "FALSE", "isAt_predicted": "FALSE",
         "at_gold": "PROBABLE", "isAt_gold": "FALSE"},
        {"document_id": "d", "pers_entity_id": "p", "loc_entity_id": "l2",
         "language": "fr",
         "at_predicted": "TRUE", "isAt_predicted": "FALSE",
         "at_gold": "TRUE", "isAt_gold": "FALSE"},
    ]
    mask = [
        {"document_id": "d", "pers_entity_id": "p", "loc_entity_id": "l1",
         "language": "fr",
         "at_predicted": None, "isAt_predicted": "FALSE",
         "at_gold": "PROBABLE", "isAt_gold": "FALSE"},
        {"document_id": "d", "pers_entity_id": "p", "loc_entity_id": "l2",
         "language": "fr",
         "at_predicted": None, "isAt_predicted": "TRUE",
         "at_gold": "TRUE", "isAt_gold": "FALSE"},
    ]
    llm = [
        {"document_id": "d", "pers_entity_id": "p", "loc_entity_id": "l1",
         "language": "fr",
         "at_predicted": "PROBABLE", "isAt_predicted": "FALSE",
         "at_gold": "PROBABLE", "isAt_gold": "FALSE"},
        {"document_id": "d", "pers_entity_id": "p", "loc_entity_id": "l2",
         "language": "fr",
         "at_predicted": "PROBABLE", "isAt_predicted": "TRUE",
         "at_gold": "TRUE", "isAt_gold": "FALSE"},
    ]
    rf_path = tmp_path / "rf.jsonl"
    mask_path = tmp_path / "mask.jsonl"
    llm_path = tmp_path / "llm.jsonl"
    _write_jsonl(rf_path, rf)
    _write_jsonl(mask_path, mask)
    _write_jsonl(llm_path, llm)

    log_dir = tmp_path / "out"
    cmd = [
        sys.executable,
        str(PROJECT_ROOT / "scripts" / "build_three_way_ensemble.py"),
        "--rf-at", str(rf_path),
        "--mask-isAt", str(mask_path),
        "--llm", str(llm_path),
        "--experiment-id", "test_3way",
        "--log-dir", str(log_dir),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0, res.stderr

    pred_path = log_dir / "test_3way_predictions.jsonl"
    rows = [json.loads(l) for l in pred_path.read_text(encoding="utf-8").splitlines() if l.strip()]
    by_loc = {r["loc_entity_id"]: r for r in rows}
    # l1: RF FALSE + LLM PROBABLE -> flip to PROBABLE
    assert by_loc["l1"]["at_predicted"] == "PROBABLE"
    assert by_loc["l1"]["flipped"] is True
    # l2: RF TRUE -> stays TRUE
    assert by_loc["l2"]["at_predicted"] == "TRUE"
    assert by_loc["l2"]["flipped"] is False
    # isAt always comes from MASK
    assert by_loc["l1"]["isAt_predicted"] == "FALSE"
    assert by_loc["l2"]["isAt_predicted"] == "TRUE"


# ---------------------------------------------------------------------------
# Per-language routing
# ---------------------------------------------------------------------------


def test_per_language_routing_picks_per_language_source(tmp_path):
    fr_pred = [
        {"document_id": "d", "pers_entity_id": "p", "loc_entity_id": "l1",
         "language": "fr",
         "at_predicted": "TRUE", "isAt_predicted": "TRUE",
         "at_gold": "TRUE", "isAt_gold": "TRUE"},
    ]
    de_pred = [
        {"document_id": "d", "pers_entity_id": "p", "loc_entity_id": "l2",
         "language": "de",
         "at_predicted": "FALSE", "isAt_predicted": "FALSE",
         "at_gold": "FALSE", "isAt_gold": "FALSE"},
    ]
    default_pred = [
        # Should be picked for English row only.
        {"document_id": "d", "pers_entity_id": "p", "loc_entity_id": "l3",
         "language": "en",
         "at_predicted": "PROBABLE", "isAt_predicted": "FALSE",
         "at_gold": "PROBABLE", "isAt_gold": "FALSE"},
        # Default also has a French row but the route should win.
        {"document_id": "d", "pers_entity_id": "p", "loc_entity_id": "l1",
         "language": "fr",
         "at_predicted": "FALSE", "isAt_predicted": "FALSE",
         "at_gold": "TRUE", "isAt_gold": "TRUE"},
    ]

    fr_path = tmp_path / "fr.jsonl"
    de_path = tmp_path / "de.jsonl"
    default_path = tmp_path / "default.jsonl"
    _write_jsonl(fr_path, fr_pred)
    _write_jsonl(de_path, de_pred)
    _write_jsonl(default_path, default_pred)

    log_dir = tmp_path / "out"
    cmd = [
        sys.executable,
        str(PROJECT_ROOT / "scripts" / "build_per_language_ensemble.py"),
        "--route", f"fr={fr_path}",
        "--route", f"de={de_path}",
        "--default", str(default_path),
        "--experiment-id", "test_route",
        "--log-dir", str(log_dir),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0, res.stderr

    rows = [
        json.loads(l)
        for l in (log_dir / "test_route_predictions.jsonl").read_text(encoding="utf-8").splitlines()
        if l.strip()
    ]
    by_loc = {r["loc_entity_id"]: r for r in rows}
    # French row should come from fr_pred (TRUE), NOT default (FALSE).
    assert by_loc["l1"]["at_predicted"] == "TRUE"
    # German row from de_pred.
    assert by_loc["l2"]["at_predicted"] == "FALSE"
    # English (no route) falls through to default.
    assert by_loc["l3"]["at_predicted"] == "PROBABLE"


# ---------------------------------------------------------------------------
# OpenRouter provider wiring
# ---------------------------------------------------------------------------


def test_openrouter_provider_resolves_with_base_url(monkeypatch):
    from hipe.llm.client import (
        DEFAULT_MODELS, OPENROUTER_BASE_URL, PROVIDER_API_KEY_ENV, resolve_provider,
    )

    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test")
    provider, base_url, api_key = resolve_provider("openrouter")
    assert provider == "openrouter"
    assert base_url == OPENROUTER_BASE_URL
    assert api_key == "sk-test"
    assert "openrouter" in DEFAULT_MODELS
    assert PROVIDER_API_KEY_ENV["openrouter"] == "OPENROUTER_API_KEY"


def test_openrouter_provider_unknown_name_raises():
    from hipe.llm.client import resolve_provider

    with pytest.raises(ValueError, match="openrouter"):
        resolve_provider("not-a-provider")
