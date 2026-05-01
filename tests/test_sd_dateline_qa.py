"""Tests for the Dateline & QA Specs (§2 + §3) feature blocks."""

from __future__ import annotations

import numpy as np
import pytest

from hipe.data import RelationInstance
from hipe.subgroup_discovery import (
    DATELINE_FEATURE_NAMES,
    QA_DATELINE_CROSS_FEATURE,
    QA_FEATURE_NAMES,
    build_sd_feature_matrix,
    cross_check_qa_dateline,
    dateline_matrix,
    detect_dateline,
    qa_threshold_classifier,
)


def _inst(
    *,
    text: str,
    context: str | None = None,
    pers: list[str] | None = None,
    locs: list[str] | None = None,
    language: str = "en",
    date: str = "1900-01-01",
    at: str = "FALSE",
) -> RelationInstance:
    return RelationInstance(
        document_id="doc",
        pers_entity_id="p1",
        loc_entity_id="l1",
        language=language,
        date=date,
        pers_mentions_list=pers or ["John"],
        loc_mentions_list=locs or ["Paris"],
        pers_wikidata_QID="Q1",
        loc_wikidata_QID="Q123",
        text=text,
        context=context if context is not None else text,
        at=at,
        isAt="FALSE",
    )


# --------------------------------------------------------------- dateline §2

def test_dateline_feature_names_match_dict_keys():
    inst = _inst(text="John lives in Paris.")
    f = detect_dateline(inst)
    assert set(f.keys()) == set(DATELINE_FEATURE_NAMES)
    assert len(f) == 5


def test_no_dateline_for_plain_prose():
    inst = _inst(text="John lives in Paris and works there.", locs=["Paris"])
    f = detect_dateline(inst)
    assert f["location_is_dateline"] == 0.0
    assert f["location_dateline_only"] == 0.0


def test_opening_dateline_german():
    text = (
        "Berlin, 14. Oktober. — Die Regierung hat heute "
        "eine wichtige Entscheidung getroffen."
    )
    inst = _inst(text=text, locs=["Berlin"], language="de")
    f = detect_dateline(inst)
    assert f["location_is_opening_dateline"] == 1.0
    assert f["location_is_dateline"] == 1.0


def test_opening_dateline_english_caps():
    text = (
        "LONDON, Dec. 31. The official account of the events "
        "is finally available to the public."
    )
    inst = _inst(text=text, locs=["LONDON"], language="en")
    f = detect_dateline(inst)
    assert f["location_is_opening_dateline"] == 1.0


def test_opening_dateline_french():
    text = "Paris, le 12 mars. — On apprend que le ministre a démissionné."
    inst = _inst(text=text, locs=["Paris"], language="fr")
    f = detect_dateline(inst)
    assert f["location_is_opening_dateline"] == 1.0


def test_closing_dateline_signoff():
    text = (
        "Le ministre a déclaré ses intentions hier au parlement, "
        "selon notre correspondant particulier.\n"
        "    Paris, le 22 avril 1918."
    )
    inst = _inst(text=text, locs=["Paris"], language="fr")
    f = detect_dateline(inst)
    assert f["location_is_closing_dateline"] == 1.0


def test_mid_dateline_section_break():
    text = (
        "Mailand. Der gestern erwähnte Vertrag wurde unterzeichnet.\n"
        "Frankfurt. Am 14. Oktober haben die HH. Reichskommissare "
        "Teichert eine Sitzung abgehalten."
    )
    inst = _inst(text=text, locs=["Frankfurt"], language="de")
    f = detect_dateline(inst)
    assert f["location_is_mid_dateline"] == 1.0


def test_dateline_only_when_no_prose_mention():
    head_dateline = "LONDON, Dec. 31."
    body = " The official account was published " + ("today " * 60) + "."
    text = head_dateline + body
    inst = _inst(text=text, locs=["LONDON"], language="en")
    f = detect_dateline(inst)
    assert f["location_is_dateline"] == 1.0
    assert f["location_dateline_only"] == 1.0


def test_dateline_only_off_when_location_appears_in_prose():
    head_dateline = "LONDON, Dec. 31."
    body = (
        " The official account from many sources " + ("today " * 40) +
        " confirmed that LONDON was the destination of the visit. " +
        ("more text " * 20) + "."
    )
    text = head_dateline + body
    inst = _inst(text=text, locs=["LONDON"], language="en")
    f = detect_dateline(inst)
    assert f["location_is_dateline"] == 1.0
    assert f["location_dateline_only"] == 0.0


def test_dateline_matrix_shape_and_dtype():
    insts = [_inst(text="Berlin, 14. Oktober. — Die Lage."), _inst(text="No dateline here.")]
    M = dateline_matrix(insts)
    assert M.shape == (2, len(DATELINE_FEATURE_NAMES))
    assert M.dtype == np.float32


def test_dateline_handles_empty_text():
    inst = _inst(text="", locs=["Paris"])
    f = detect_dateline(inst)
    assert f["location_is_dateline"] == 0.0


# --------------------------------------------------------- SD builder wiring

def _toy_instances(n: int = 6):
    return [
        _inst(
            text="John reportedly might have been in Paris.",
            pers=["John"], locs=["Paris"], language="en", at="PROBABLE",
        )
        for _ in range(n)
    ]


def test_sd_h_includes_dateline_block():
    X, names, _ = build_sd_feature_matrix(
        _toy_instances(), mask_embeddings=None, config="SD-H", verbose=False
    )
    for name in DATELINE_FEATURE_NAMES:
        assert name in names
    # Dimension equals temporal(15)+evidence(13)+verb(7)+hierarchy(3)+
    # dateline(5)+lang(4) = 47
    assert X.shape[1] == 47


def test_sd_hq_uses_cached_qa_features():
    insts = _toy_instances(4)
    qa_dim = len(QA_FEATURE_NAMES) + 1  # + qa_evidence_is_dateline
    qa_cached = np.zeros((len(insts), qa_dim), dtype=np.float32)
    qa_cached[:, 0] = 0.7  # qa_at_score
    X, names, meta = build_sd_feature_matrix(
        insts,
        mask_embeddings=None,
        config="SD-HQ",
        qa_features=qa_cached,
        verbose=False,
    )
    assert "qa_at_score" in names
    assert QA_DATELINE_CROSS_FEATURE in names
    assert meta["qa"]["source"] == "cached"
    assert X.shape[1] == 47 + qa_dim


def test_sd_hqs_requires_mask_embeddings():
    insts = _toy_instances(4)
    qa_dim = len(QA_FEATURE_NAMES) + 1
    qa_cached = np.zeros((len(insts), qa_dim), dtype=np.float32)
    with pytest.raises(ValueError):
        build_sd_feature_matrix(
            insts, mask_embeddings=None, config="SD-HQS",
            qa_features=qa_cached, verbose=False,
        )


def test_sd_hqs_combines_qa_and_spectral():
    insts = _toy_instances(8)
    qa_dim = len(QA_FEATURE_NAMES) + 1
    qa_cached = np.zeros((len(insts), qa_dim), dtype=np.float32)
    rng = np.random.RandomState(0)
    emb = rng.randn(len(insts), 32).astype(np.float32)
    X, names, meta = build_sd_feature_matrix(
        insts,
        mask_embeddings=emb,
        config="SD-HQS",
        qa_features=qa_cached,
        spectral_n_components=3,
        spectral_n_neighbors=4,
        verbose=False,
    )
    assert "qa_at_score" in names
    assert any(n.startswith("spectral_EV") for n in names)
    assert meta["qa"]["source"] == "cached"
    assert meta["spectral"] is not None


def test_qa_features_shape_validation():
    insts = _toy_instances(4)
    bad = np.zeros((3, len(QA_FEATURE_NAMES) + 1), dtype=np.float32)  # wrong N
    with pytest.raises(ValueError):
        build_sd_feature_matrix(
            insts, mask_embeddings=None, config="SD-HQ",
            qa_features=bad, verbose=False,
        )


# ------------------------------------------------------- QA cross-check §3.8

def test_cross_check_marks_dateline_when_span_is_at_head():
    text = "LONDON, Dec. 31. The official account follows below."
    inst = _inst(text=text, locs=["LONDON"], language="en")
    qa = {
        "qa_at_score": 0.5,
        "qa_at_has_answer": 1.0,
        "qa_at_span": "LONDON, Dec. 31",
        QA_DATELINE_CROSS_FEATURE: 0.0,
    }
    cross_check_qa_dateline(qa, inst)
    assert qa[QA_DATELINE_CROSS_FEATURE] == 1.0


def test_cross_check_no_flag_without_dateline():
    text = "Plain prose with no dateline. John was reportedly in Paris."
    inst = _inst(text=text, locs=["Paris"], language="en")
    qa = {
        "qa_at_score": 0.5,
        "qa_at_has_answer": 1.0,
        "qa_at_span": "in Paris",
        QA_DATELINE_CROSS_FEATURE: 0.0,
    }
    cross_check_qa_dateline(qa, inst)
    assert qa[QA_DATELINE_CROSS_FEATURE] == 0.0


# ---------------------------------------------------------- ablation §5.4

def test_qa_threshold_classifier_buckets():
    high = {"qa_at_score": 0.8, "qa_isAt_score": 0.6}
    mid = {"qa_at_score": 0.2, "qa_isAt_score": 0.05}
    low = {"qa_at_score": 0.01, "qa_isAt_score": 0.0}
    assert qa_threshold_classifier(high) == ("TRUE", "TRUE")
    assert qa_threshold_classifier(mid) == ("PROBABLE", "FALSE")
    assert qa_threshold_classifier(low) == ("FALSE", "FALSE")
