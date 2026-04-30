"""Tests for hipe.submission: parser, writer, constraint enforcement."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from hipe.data import (
    collect_pair_keys,
    iter_official_documents,
    parse_official_jsonl,
)
from hipe.submission import (
    Prediction,
    generate_submission_file,
    predictions_from_records,
    submission_filename,
)


def _sample_doc(doc_id: str, pairs: list[dict]) -> dict:
    return {
        "document_id": doc_id,
        "media": {
            "publication_title": "Demo",
            "time_period": "1900-1950",
            "source_type": "Newspaper",
        },
        "source": "demo",
        "language": "de",
        "date": "1900-01-01",
        "text": "Some OCR text mentioning Person and Place.",
        "sampled_pairs": pairs,
    }


def _write_jsonl(path: Path, docs: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for d in docs:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")


@pytest.fixture
def gold_file(tmp_path: Path) -> Path:
    docs = [
        _sample_doc(
            "doc-1",
            [
                {
                    "pers_entity_id": "doc-1_P1",
                    "pers_wikidata_QID": "Q1",
                    "pers_mentions_list": ["Alice"],
                    "loc_entity_id": "doc-1_L1",
                    "loc_wikidata_QID": "Q10",
                    "loc_mentions_list": ["Paris"],
                    "at": "TRUE",
                    "at_explanation": "",
                    "isAt": "FALSE",
                    "isAt_explanation": "",
                },
                {
                    "pers_entity_id": "doc-1_P1",
                    "pers_wikidata_QID": "Q1",
                    "pers_mentions_list": ["Alice"],
                    "loc_entity_id": "doc-1_L2",
                    "loc_wikidata_QID": "Q11",
                    "loc_mentions_list": ["Berlin"],
                    "at": "FALSE",
                    "at_explanation": "",
                    "isAt": "FALSE",
                    "isAt_explanation": "",
                },
            ],
        ),
        _sample_doc(
            "doc-2",
            [
                {
                    "pers_entity_id": "doc-2_P2",
                    "pers_wikidata_QID": "Q2",
                    "pers_mentions_list": ["Bob"],
                    "loc_entity_id": "doc-2_L3",
                    "loc_wikidata_QID": "Q12",
                    "loc_mentions_list": ["Lyon"],
                    "at": "PROBABLE",
                    "at_explanation": "",
                    "isAt": "TRUE",
                    "isAt_explanation": "",
                },
            ],
        ),
    ]
    p = tmp_path / "gold.jsonl"
    _write_jsonl(p, docs)
    return p


def test_parse_official_jsonl_yields_per_pair_instance(gold_file):
    instances = parse_official_jsonl(gold_file)
    assert len(instances) == 3
    assert instances[0].document_id == "doc-1"
    assert instances[0].pers_entity_id == "doc-1_P1"
    assert instances[0].at == "TRUE"
    assert instances[2].pers_entity_id == "doc-2_P2"
    assert instances[2].isAt == "TRUE"


def test_collect_pair_keys_preserves_order(gold_file):
    keys = collect_pair_keys(iter_official_documents(gold_file))
    assert keys == [
        ("doc-1", "doc-1_P1", "doc-1_L1"),
        ("doc-1", "doc-1_P1", "doc-1_L2"),
        ("doc-2", "doc-2_P2", "doc-2_L3"),
    ]


def test_generate_submission_file_round_trip(gold_file, tmp_path: Path):
    predictions = {
        ("doc-1", "doc-1_P1", "doc-1_L1"): Prediction(at="TRUE", isAt="TRUE",
                                                      at_explanation="explained"),
        ("doc-1", "doc-1_P1", "doc-1_L2"): Prediction(at="PROBABLE", isAt="FALSE"),
        # doc-2 pair intentionally missing -> should default to FALSE/FALSE.
    }
    out = tmp_path / "sub.jsonl"
    stats = generate_submission_file(gold_file, predictions, out)

    assert stats.total_pairs == 3
    assert stats.n_documents == 2
    assert stats.n_missing_predictions == 1
    assert stats.label_counts_at["TRUE"] == 1
    assert stats.label_counts_at["PROBABLE"] == 1
    assert stats.label_counts_at["FALSE"] == 1
    assert stats.label_counts_isAt["TRUE"] == 1
    assert stats.label_counts_isAt["FALSE"] == 2

    written = list(iter_official_documents(out))
    # Document and pair ordering preserved.
    assert [d["document_id"] for d in written] == ["doc-1", "doc-2"]
    pairs1 = written[0]["sampled_pairs"]
    assert pairs1[0]["at"] == "TRUE" and pairs1[0]["isAt"] == "TRUE"
    assert pairs1[0]["at_explanation"] == "explained"
    assert pairs1[1]["at"] == "PROBABLE" and pairs1[1]["isAt"] == "FALSE"
    pairs2 = written[1]["sampled_pairs"]
    assert pairs2[0]["at"] == "FALSE" and pairs2[0]["isAt"] == "FALSE"


def test_generate_submission_enforces_constraint(gold_file, tmp_path: Path):
    predictions = {
        ("doc-1", "doc-1_P1", "doc-1_L1"): Prediction(at="FALSE", isAt="TRUE"),
        ("doc-1", "doc-1_P1", "doc-1_L2"): Prediction(at="FALSE", isAt="FALSE"),
        ("doc-2", "doc-2_P2", "doc-2_L3"): Prediction(at="TRUE", isAt="TRUE"),
    }
    out = tmp_path / "sub.jsonl"
    stats = generate_submission_file(gold_file, predictions, out)
    assert stats.n_constraint_fixes == 1

    written = list(iter_official_documents(out))
    p = written[0]["sampled_pairs"][0]
    assert p["at"] == "FALSE" and p["isAt"] == "FALSE"


def test_generate_submission_rejects_unknown_label(gold_file, tmp_path: Path):
    predictions = {
        ("doc-1", "doc-1_P1", "doc-1_L1"): {"at": "MAYBE", "isAt": "FALSE"},
    }
    out = tmp_path / "sub.jsonl"
    with pytest.raises(ValueError):
        generate_submission_file(gold_file, predictions, out)


def test_predictions_from_records_round_trips_keys():
    records = [
        {
            "document_id": "d1",
            "pers_entity_id": "p",
            "loc_entity_id": "l",
            "at_predicted": "TRUE",
            "isAt_predicted": "FALSE",
            "at_explanation": "x",
        }
    ]
    out = predictions_from_records(records)
    assert ("d1", "p", "l") in out
    p = out[("d1", "p", "l")]
    assert p.at == "TRUE" and p.isAt == "FALSE"
    assert p.at_explanation == "x"


def test_submission_filename_format():
    name = submission_filename(
        "OURTEAM",
        "data/HIPE-2026-v1.0-impresso-test-de.jsonl",
        run=2,
    )
    assert name == "OURTEAM_HIPE-2026-v1.0-impresso-test-de_run2.jsonl"


def test_predictions_handle_null_via_null_to_false():
    records = [
        {
            "document_id": "d",
            "pers_entity_id": "p",
            "loc_entity_id": "l",
            "at_predicted": None,
            "isAt_predicted": None,
        }
    ]
    out = predictions_from_records(records)
    p = out[("d", "p", "l")]
    assert p.at == "FALSE" and p.isAt == "FALSE"
