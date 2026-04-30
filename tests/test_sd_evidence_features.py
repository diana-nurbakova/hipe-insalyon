"""Tests for v2 evidence-strength + verb-type + hierarchy + SD config builders."""

from __future__ import annotations

import numpy as np
import pytest

from hipe.data import RelationInstance
from hipe.subgroup_discovery import (
    EVIDENCE_FEATURE_NAMES,
    HIERARCHY_FEATURE_NAMES,
    VERB_TYPE_FEATURE_NAMES,
    build_sd_feature_matrix,
    classify_verb_type,
    compute_hierarchical_mention_count,
    evidence_matrix,
    expand_mentions,
    extract_evidence_features,
    hierarchy_matrix,
    verb_type_matrix,
)


def _inst(
    *,
    text: str,
    context: str | None = None,
    pers: list[str] | None = None,
    locs: list[str] | None = None,
    language: str = "en",
    location_context: dict | None = None,
    loc_qid: str | None = "Q123",
    at: str = "TRUE",
    isAt: str = "TRUE",
) -> RelationInstance:
    return RelationInstance(
        document_id="doc",
        pers_entity_id="p1",
        loc_entity_id="l1",
        language=language,
        date="1900-01-01",
        pers_mentions_list=pers or ["John"],
        loc_mentions_list=locs or ["Paris"],
        pers_wikidata_QID="Q1",
        loc_wikidata_QID=loc_qid,
        text=text,
        context=context if context is not None else text,
        location_context=location_context or {},
        at=at,
        isAt=isAt,
    )


# ---------------------------------------------------------- evidence features

def test_evidence_feature_names_match_dict_keys():
    inst = _inst(text="John lives in Paris.")
    f = extract_evidence_features(inst)
    assert set(f.keys()) == set(EVIDENCE_FEATURE_NAMES)
    assert len(f) == 13


def test_preposition_link_detected_en():
    inst = _inst(text="John in Paris was happy.", pers=["John"], locs=["Paris"], language="en")
    f = extract_evidence_features(inst)
    assert f["has_preposition_link"] == 1.0
    assert f["entities_adjacent"] == 1.0


def test_genitive_construction_detected_fr():
    inst = _inst(
        text="L'archevêque de Paris est arrivé.",
        pers=["archevêque"],
        locs=["Paris"],
        language="fr",
    )
    f = extract_evidence_features(inst)
    assert f["has_genitive_construction"] == 1.0


def test_role_title_detected_multilingual():
    f_fr = extract_evidence_features(
        _inst(text="Le ministre a parlé.", pers=["ministre"], locs=["Paris"], language="fr")
    )
    f_de = extract_evidence_features(
        _inst(text="Der Bürgermeister sagte.", pers=["Bürgermeister"], locs=["Berlin"], language="de")
    )
    assert f_fr["has_role_title"] == 1.0
    assert f_de["has_role_title"] == 1.0


def test_hedging_increases_with_more_words():
    f_low = extract_evidence_features(_inst(text="John reportedly lived in Paris."))
    f_high = extract_evidence_features(
        _inst(text="John reportedly allegedly possibly lived in Paris.")
    )
    assert f_low["has_hedging"] == 1.0
    assert f_high["n_hedging_words"] > f_low["n_hedging_words"]


def test_subjunctive_detected():
    f = extract_evidence_features(
        _inst(text="John would have been in Paris.", pers=["John"], locs=["Paris"])
    )
    assert f["has_subjunctive"] == 1.0


def test_entity_in_quotes_detected():
    f = extract_evidence_features(
        _inst(text='He said "John in Paris" yesterday.', pers=["John"], locs=["Paris"])
    )
    assert f["entity_in_quotes"] == 1.0


def test_cooccurrence_sentences_count():
    text = (
        "John was in Paris. The weather was nice. "
        "John walked through Paris in the morning. "
        "London is far. John in Paris met friends."
    )
    f = extract_evidence_features(_inst(text=text, pers=["John"], locs=["Paris"]))
    assert f["cooccurrence_sentences"] > 0.0


def test_far_entities_get_high_distance():
    far = "John was here. " + "lorem " * 200 + "Paris was beautiful."
    f = extract_evidence_features(_inst(text=far, context=far, pers=["John"], locs=["Paris"]))
    assert f["entities_adjacent"] == 0.0
    assert f["entity_char_distance"] > 0.5


def test_evidence_matrix_shape():
    insts = [_inst(text="t1") for _ in range(5)]
    M = evidence_matrix(insts)
    assert M.shape == (5, len(EVIDENCE_FEATURE_NAMES))
    assert M.dtype == np.float32


# -------------------------------------------------------------- verb features

def test_verb_type_role_detected_en():
    f = classify_verb_type(_inst(text="He served as governor.", language="en"))
    assert f["verb_type_role"] == 1.0
    assert f["verb_strong_evidence"] == 1.0


def test_verb_type_communication_signals_indirect():
    f = classify_verb_type(_inst(text="He declared himself in Paris.", language="en"))
    assert f["verb_type_communication"] == 1.0
    assert f["verb_indirect_evidence"] == 1.0


def test_verb_type_lb_uses_lb_lexicon():
    # "wunnen" is in the Luxembourgish stative lexicon.
    f = classify_verb_type(_inst(text="D'Leit wunnen zu Paräis.", language="lb"))
    assert f["verb_type_stative"] == 1.0


def test_verb_type_lb_falls_back_to_de():
    # German verb "wohnen" — Luxembourgish should fall back to it.
    f = classify_verb_type(_inst(text="D'Leit wohnen am Stadt.", language="lb"))
    assert f["verb_type_stative"] == 1.0


def test_verb_matrix_shape_and_names():
    insts = [_inst(text="She works.") for _ in range(3)]
    M = verb_type_matrix(insts)
    assert M.shape == (3, len(VERB_TYPE_FEATURE_NAMES))


# ------------------------------------------------------------- mention expand

def test_expand_mentions_adds_pronouns_in_same_sentence():
    # Pronouns are added only if the sentence also contains a named mention.
    inst = _inst(
        text="John arrived and he liked it.",
        context="John arrived and he liked it.",
        pers=["John"], locs=["Paris"], language="en",
    )
    pers_exp, _ = expand_mentions(inst)
    assert any(p.lower() == "he" for p in pers_exp)


def test_expand_mentions_pulls_wikidata_aliases():
    # Alias matching is case-sensitive (per spec).
    inst = _inst(
        text="the capital was busy.",
        context="the capital was busy.",
        pers=["John"], locs=["Paris"], language="en",
        location_context={"aliases": ["the capital"]},
    )
    _, locs_exp = expand_mentions(inst)
    assert "the capital" in locs_exp


# --------------------------------------------------------------- hierarchy

def test_hierarchy_zeros_without_cache():
    inst = _inst(text="Paris. Paris. Paris.", pers=["John"], locs=["Paris"])
    f = compute_hierarchical_mention_count(inst, hierarchy_cache=None)
    assert set(f.keys()) == set(HIERARCHY_FEATURE_NAMES)
    # Direct count > 0 (3 occurrences of Paris).
    assert f["direct_loc_count"] > 0.0
    # No cache -> hierarchical equals direct, parent = 0.
    assert f["parent_location_mentioned"] == 0.0


def test_hierarchy_uses_cache_when_provided():
    inst = _inst(
        text="Lyon was busy. France was bigger.",
        pers=["John"], locs=["France"], loc_qid="Q142", language="fr",
    )
    cache = {"Q142": {"Q456": ["Lyon"], "_parents": ["Europe"]}}
    f = compute_hierarchical_mention_count(inst, cache)
    assert f["hierarchical_loc_count"] > f["direct_loc_count"]


def test_hierarchy_matrix_shape():
    insts = [_inst(text="Paris.") for _ in range(4)]
    M = hierarchy_matrix(insts)
    assert M.shape == (4, len(HIERARCHY_FEATURE_NAMES))


# --------------------------------------------------- build_sd_feature_matrix

def _toy_instances(n_pos: int = 8, n_neg: int = 16):
    insts: list[RelationInstance] = []
    for _ in range(n_pos):
        insts.append(_inst(
            text="John reportedly might have been in Paris.",
            pers=["John"], locs=["Paris"], language="en",
            at="PROBABLE", isAt="FALSE",
        ))
    for _ in range(n_neg):
        insts.append(_inst(
            text="The weather was clear today.",
            pers=["John"], locs=["Paris"], language="en",
            at="FALSE", isAt="FALSE",
        ))
    return insts


def test_build_sd_feature_matrix_sd_h_no_mask_required():
    insts = _toy_instances()
    X, names, meta = build_sd_feature_matrix(
        insts, mask_embeddings=None, config="SD-H", verbose=False
    )
    assert X.shape[0] == len(insts)
    assert X.shape[1] == len(names)
    assert meta["spectral"] is None
    assert meta["pca"] is None
    # Sanity: handcrafted block has temporal + evidence + verb + hierarchy + lang
    assert "has_hedging" in names
    assert "verb_type_communication" in names
    assert "lang_en" in names


def test_build_sd_feature_matrix_sd_hs_uses_mask():
    insts = _toy_instances()
    rng = np.random.RandomState(0)
    emb = rng.randn(len(insts), 64).astype(np.float32)
    X, names, meta = build_sd_feature_matrix(
        insts, mask_embeddings=emb, config="SD-HS",
        spectral_n_components=4, spectral_n_neighbors=5, verbose=False,
    )
    assert any(n.startswith("spectral_EV") for n in names)
    assert meta["spectral"] is not None
    assert meta["pca"] is None


def test_build_sd_feature_matrix_sd_hsp_adds_pca():
    insts = _toy_instances()
    rng = np.random.RandomState(0)
    emb = rng.randn(len(insts), 32).astype(np.float32)
    X, names, meta = build_sd_feature_matrix(
        insts, mask_embeddings=emb, config="SD-HSP",
        spectral_n_components=3, spectral_n_neighbors=5,
        pca_n_components=4, verbose=False,
    )
    assert sum(n.startswith("MASK_PC") for n in names) == 4
    assert sum(n.startswith("spectral_EV") for n in names) == 3
    assert meta["pca"] is not None


def test_build_sd_feature_matrix_rejects_unknown_config():
    insts = _toy_instances(2, 4)
    with pytest.raises(ValueError):
        build_sd_feature_matrix(insts, config="SD-NOPE", verbose=False)


def test_build_sd_feature_matrix_requires_mask_for_hs():
    insts = _toy_instances(2, 4)
    with pytest.raises(ValueError):
        build_sd_feature_matrix(insts, config="SD-HS", verbose=False)
