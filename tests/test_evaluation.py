"""Tests for hipe.evaluation: macro recall, global score, null handling."""

from __future__ import annotations

import math

import pytest

from hipe.evaluation import (
    AT_LABELS,
    ISAT_LABELS,
    classification_report,
    compute_global_score,
    compute_macro_recall,
    confusion_matrix,
    generate_evaluation_report,
    null_to_false,
)


def test_null_to_false():
    assert null_to_false(None) == "FALSE"
    assert null_to_false("TRUE") == "TRUE"
    assert null_to_false("PROBABLE") == "PROBABLE"
    assert null_to_false("FALSE") == "FALSE"


def test_macro_recall_perfect_predictions():
    gold = ["TRUE", "TRUE", "PROBABLE", "FALSE", "FALSE", "FALSE"]
    pred = list(gold)
    out = compute_macro_recall(gold, pred, label_set=AT_LABELS)
    assert out["recall_TRUE"] == 1.0
    assert out["recall_PROBABLE"] == 1.0
    assert out["recall_FALSE"] == 1.0
    assert out["macro_recall"] == 1.0


def test_macro_recall_handles_zero_support_label():
    # PROBABLE never appears in gold; it must drop from the average,
    # not contribute a 0.
    gold = ["TRUE", "FALSE", "FALSE"]
    pred = ["TRUE", "FALSE", "FALSE"]
    out = compute_macro_recall(gold, pred, label_set=AT_LABELS)
    assert out["recall_PROBABLE"] is None
    assert out["recall_TRUE"] == 1.0
    assert out["recall_FALSE"] == 1.0
    # Average is over the two non-null labels.
    assert out["macro_recall"] == 1.0


def test_macro_recall_partial():
    gold = ["TRUE", "TRUE", "FALSE", "FALSE", "FALSE", "FALSE"]
    pred = ["TRUE", "FALSE", "FALSE", "FALSE", "FALSE", "TRUE"]
    out = compute_macro_recall(gold, pred, label_set=ISAT_LABELS)
    # TRUE: 1/2 = 0.5; FALSE: 3/4 = 0.75; macro = 0.625
    assert out["recall_TRUE"] == 0.5
    assert out["recall_FALSE"] == 0.75
    assert math.isclose(out["macro_recall"], 0.625)


def test_macro_recall_length_mismatch():
    with pytest.raises(ValueError):
        compute_macro_recall(["TRUE"], ["TRUE", "FALSE"])


def test_global_score_balances_two_subtasks():
    at_gold = ["TRUE", "TRUE", "PROBABLE", "FALSE"]
    at_pred = ["TRUE", "TRUE", "PROBABLE", "FALSE"]  # perfect on at
    isAt_gold = ["TRUE", "FALSE", "FALSE", "FALSE"]
    isAt_pred = ["FALSE", "FALSE", "FALSE", "FALSE"]  # missed the only TRUE
    res = compute_global_score(at_gold, at_pred, isAt_gold, isAt_pred)
    assert res["macro_recall_at"] == 1.0
    # isAt: TRUE recall 0/1=0; FALSE recall 3/3=1; macro = 0.5
    assert res["macro_recall_isAt"] == 0.5
    assert res["global_score"] == 0.75


def test_global_score_rejects_unknown_labels():
    with pytest.raises(ValueError):
        compute_global_score(["YES"], ["TRUE"], ["TRUE"], ["TRUE"])


def test_confusion_matrix_layout():
    cm = confusion_matrix(
        ["TRUE", "TRUE", "FALSE"], ["TRUE", "FALSE", "FALSE"], ISAT_LABELS,
    )
    # rows = gold, cols = pred. ISAT_LABELS = (TRUE, FALSE)
    # gold TRUE: pred TRUE 1, pred FALSE 1
    # gold FALSE: pred TRUE 0, pred FALSE 1
    assert cm == [[1, 1], [0, 1]]


def test_classification_report_shape():
    rep = classification_report(
        ["TRUE", "TRUE", "FALSE"], ["TRUE", "FALSE", "FALSE"], ISAT_LABELS,
    )
    assert rep["TRUE"]["recall"] == 0.5
    assert rep["FALSE"]["recall"] == 1.0
    assert "macro avg" in rep
    assert "weighted avg" in rep


def test_generate_evaluation_report_applies_null_to_false():
    at_gold = ["TRUE", "FALSE", "FALSE"]
    at_pred = ["TRUE", None, "FALSE"]  # null -> FALSE
    isAt_gold = ["TRUE", "FALSE", "FALSE"]
    isAt_pred = ["TRUE", None, "FALSE"]
    rep = generate_evaluation_report(
        "smoke", at_gold, at_pred, isAt_gold, isAt_pred, print_summary=False,
    )
    # Both perfect once nulls become FALSE.
    assert rep["scores"]["global_score"] == 1.0
    assert rep["n_instances"] == 3
    assert rep["at_labels"] == list(AT_LABELS)
    assert rep["isAt_labels"] == list(ISAT_LABELS)
