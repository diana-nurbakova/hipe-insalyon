"""Tests for the MASK template builders and encoder configuration logic.

These tests don't require a downloaded BERT checkpoint — they exercise the
pure-Python parts of ``hipe.mask`` (template strings, marker placement,
configuration dataclasses).
"""

from __future__ import annotations

import pytest

from hipe.data import RelationInstance
from hipe.mask import (
    LOC_CLOSE,
    LOC_OPEN,
    PERS_CLOSE,
    PERS_OPEN,
    build_template,
    locate_entity_spans,
)
from hipe.mask.encoder import DEFAULT_LAYERS, MASKEncoderConfig


def _instance(text: str = "Napoleon was born in Ajaccio in 1769.") -> RelationInstance:
    return RelationInstance(
        document_id="doc1",
        pers_entity_id="p1",
        loc_entity_id="l1",
        language="en",
        date="1769-08-15",
        pers_mentions_list=["Napoleon"],
        loc_mentions_list=["Ajaccio"],
        pers_wikidata_QID=None,
        loc_wikidata_QID=None,
        text=text,
        context=text,
    )


def test_locate_entity_spans_inserts_markers_when_present():
    inst = _instance()
    out, pers_in, loc_in = locate_entity_spans(inst)
    assert pers_in is True and loc_in is True
    assert f"{PERS_OPEN} Napoleon {PERS_CLOSE}" in out
    assert f"{LOC_OPEN} Ajaccio {LOC_CLOSE}" in out


def test_locate_entity_spans_falls_back_to_prefix_when_missing():
    # OCR garbled Napoleon → entity not found inline; templates spec says
    # prefix the marker block so the model still sees [E1]/[E2].
    inst = _instance(text="N4po1eon was born somewhere.")
    out, pers_in, loc_in = locate_entity_spans(inst)
    assert pers_in is False
    # Loc still appears? No — text doesn't have "Ajaccio".
    assert loc_in is False
    # locate_entity_spans prepends the location prefix block last, so it
    # ends up at the front: "[E2] ... [/E2] . [E1] ... [/E1] . <orig>".
    assert out.startswith(f"{LOC_OPEN} Ajaccio {LOC_CLOSE} . {PERS_OPEN} Napoleon {PERS_CLOSE} . ")


@pytest.mark.parametrize("template", ["M1", "M2", "M3", "M4", "M5"])
def test_build_template_each_variant_contains_required_tokens(template):
    inst = _instance()
    rendered = build_template(inst, template=template, mask_token="[MASK]")
    assert "[MASK]" in rendered
    if template == "M1":
        # Minimal template: no context, just person-MASK-location.
        assert "Napoleon" in rendered and "Ajaccio" in rendered
        # Must NOT contain article context tokens.
        assert "born" not in rendered
    elif template in {"M2", "M3", "M4", "M5"}:
        assert "Napoleon" in rendered and "Ajaccio" in rendered
        # M2 says "the relationship between [E1] and [E2] is [MASK]"
        if template == "M2":
            assert "relationship between" in rendered.lower()
        if template == "M3":
            # Date must be embedded.
            assert "1769" in rendered
        if template == "M4":
            # Two MASK slots.
            assert rendered.count("[MASK]") == 2
        if template == "M5":
            # Three consecutive MASKs.
            assert "[MASK] [MASK] [MASK]" in rendered


def test_build_template_unknown_raises():
    with pytest.raises(ValueError):
        build_template(_instance(), template="MX", mask_token="[MASK]")


def test_mask_encoder_config_defaults():
    cfg = MASKEncoderConfig()
    assert cfg.template == "M2"
    assert cfg.field == "context"
    assert cfg.layers == tuple(DEFAULT_LAYERS) == (-1,)
    assert cfg.add_entity_markers_as_special_tokens is True


def test_mask_encoder_config_custom_layers_preserved():
    cfg = MASKEncoderConfig(layers=(-1, -4, -7))
    assert cfg.layers == (-1, -4, -7)
