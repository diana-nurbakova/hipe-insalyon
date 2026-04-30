"""Evidence-strength features for SD (Specs v2 §4.1).

Captures how *directly* the surface text connects person to location — the
TRUE↔PROBABLE distinction the temporal block is largely blind to. All
features are extracted from existing fields (``context``, ``text``,
``pers_mentions_list``, ``loc_mentions_list``) with regex/counting; no new
NLP processing is required. Lexicons cover FR / DE / EN / LB, with German
serving as a fallback for Luxembourgish.
"""

from __future__ import annotations

import re
from typing import Iterable, Sequence

import numpy as np

from hipe.data import RelationInstance


# ---------------------------------------------------------------------------
# Public feature names
# ---------------------------------------------------------------------------

EVIDENCE_FEATURE_NAMES: tuple[str, ...] = (
    # 1. Entity proximity (2)
    "entity_char_distance",
    "entities_adjacent",
    # 2. Direct linguistic links (2)
    "has_preposition_link",
    "has_genitive_construction",
    # 3. Title / hedging / quotation / mood (5)
    "has_role_title",
    "has_hedging",
    "n_hedging_words",
    "entity_in_quotes",
    "has_subjunctive",
    # 4. Multi-mention + co-occurrence (4)
    "person_mention_count",
    "location_mention_count",
    "cooccurrence_sentences",
    "n_competing_locations",
)

VERB_TYPE_FEATURE_NAMES: tuple[str, ...] = (
    "verb_type_movement",
    "verb_type_stative",
    "verb_type_role",
    "verb_type_birth_death",
    "verb_type_communication",
    "verb_strong_evidence",
    "verb_indirect_evidence",
)


# ---------------------------------------------------------------------------
# Lexicons
# ---------------------------------------------------------------------------

ROLE_WORDS: tuple[str, ...] = (
    # FR
    "archevêque", "évêque", "ministre", "président", "directeur",
    "maire", "gouverneur", "ambassadeur", "consul", "préfet",
    # EN
    "archbishop", "bishop", "minister", "president", "director",
    "mayor", "governor", "ambassador", "consul", "prefect",
    # DE
    "Erzbischof", "Bischof", "Minister", "Präsident", "Direktor",
    "Bürgermeister", "Gouverneur", "Botschafter", "Konsul",
    # LB
    "Erzbëschof", "Bëschof", "President", "Direkter",
    "Buergermeeschter",
)

HEDGING_WORDS: tuple[str, ...] = (
    # EN
    "reportedly", "allegedly", "possibly", "perhaps", "apparently",
    # FR
    "vraisemblablement", "probablement", "sans doute", "peut-être",
    "paraît-il", "semble-t-il", "on dit que", "il paraît",
    # DE
    "angeblich", "vermutlich", "offenbar", "möglicherweise",
    "wahrscheinlich", "vielleicht", "anscheinend",
    # LB
    "wahrscheinlech", "vläicht", "eventuell",
    "vermeintlech", "offensichtlech", "scheinbar",
)

SUBJUNCTIVE_MARKERS: tuple[str, ...] = (
    # EN
    "would", "might", "could", "may have", "should have",
    # FR
    "aurait", "pourrait", "serait", "eût", "fût",
    # DE
    "dürfte", "könnte", "würde", "hätte", "wäre",
    # LB
    "géif", "kéint", "sollt", "hätt", "wier", "géing",
)

# Regex of prepositions that directly connect entities (FR/DE/EN/LB).
_PREP_PATTERN = (
    r"(?:de|à|en|au|aux|du|in|at|from|of|to|von|aus|nach|zu|vu|an|op|bei)\s+"
)
_GENITIVE_PATTERNS: tuple[str, ...] = (r"de\s+", r"du\s+", r"des\s+", r"von\s+", r"of\s+")

# Quotation regex: matches a balanced span of any quote-like character.
# Includes guillemets « », straight ", curly “ ”, and apostrophes ’ '.
_QUOTE_REGEX = re.compile(r"[«»\"“”'’](.*?)[«»\"“”'’]", re.DOTALL)

# Title pattern per language for mention expansion (§4.1.1).
_TITLE_PATTERNS = {
    "fr": (
        r"(?:M\.|Mme|Mgr|le président|le ministre|le général|"
        r"l'archevêque|le consul|le préfet|le directeur|le maire)"
    ),
    "de": (
        r"(?:Herr|Frau|der Präsident|der Minister|der General|"
        r"der Erzbischof|der Konsul|der Bürgermeister|der Direktor)"
    ),
    "en": (
        r"(?:Mr\.|Mrs\.|Ms\.|President|Minister|General|"
        r"Archbishop|Consul|Mayor|Director|the late)"
    ),
    "lb": (
        r"(?:Här|Fra|de President|de Minister|de General|"
        r"den Erzbischof|de Consul|de Buergermeeschter|den Direkter)"
    ),
}

_PRONOUNS = {
    "fr": ("il", "elle", "lui", "celui-ci", "celle-ci"),
    "de": ("er", "sie", "ihm", "ihr", "dieser", "diese"),
    "en": ("he", "she", "him", "her", "his", "himself", "herself"),
    "lb": ("hien", "si", "him", "hir", "dësen", "dës"),
}

VERB_LEXICON: dict[str, dict[str, tuple[str, ...]]] = {
    "movement": {
        "fr": (
            "arriver", "partir", "aller", "venir", "voyager", "se rendre",
            "rentrer", "revenir", "débarquer", "embarquer", "quitter",
            "traverser", "passer", "retourner", "fuir", "émigrer",
        ),
        "de": (
            "ankommen", "abreisen", "gehen", "kommen", "reisen", "fahren",
            "zurückkehren", "fliehen", "auswandern", "einwandern",
            "besuchen", "verlassen", "überqueren", "passieren",
        ),
        "en": (
            "arrive", "depart", "go", "come", "travel", "journey",
            "return", "flee", "emigrate", "immigrate", "visit",
            "leave", "cross", "pass through", "reach",
        ),
        "lb": (
            "ukommen", "ofreeën", "goen", "kommen", "reesen", "fueren",
            "zréckkommen", "fléien", "auswanderen", "besichen",
            "verloossen", "iwwerqueren", "passéieren",
        ),
    },
    "stative": {
        "fr": (
            "résider", "habiter", "vivre", "demeurer", "loger",
            "séjourner", "rester", "se trouver", "être",
        ),
        "de": (
            "wohnen", "leben", "residieren", "sich befinden", "sein",
            "bleiben", "sich aufhalten", "verweilen",
        ),
        "en": (
            "reside", "live", "dwell", "stay", "remain", "be",
            "be located", "be situated", "inhabit",
        ),
        "lb": (
            "wunnen", "liewen", "residéieren", "sech befannen", "sinn",
            "bleiwen", "sech ophalen", "verwuelen",
        ),
    },
    "role": {
        "fr": (
            "servir", "travailler", "exercer", "occuper", "diriger",
            "gouverner", "administrer", "représenter", "commander",
        ),
        "de": (
            "dienen", "arbeiten", "leiten", "regieren", "verwalten",
            "vertreten", "kommandieren", "amtieren",
        ),
        "en": (
            "serve", "work", "lead", "govern", "administer",
            "represent", "command", "preside", "manage",
        ),
        "lb": (
            "déngen", "schaffen", "leeden", "regéieren", "verwalten",
            "vertrieden", "kommandéieren", "amtéieren",
        ),
    },
    "birth_death": {
        "fr": ("naître", "mourir", "décéder", "être né", "être mort"),
        "de": ("geboren werden", "sterben", "versterben"),
        "en": ("born", "die", "pass away", "be born", "be buried"),
        "lb": ("gebuer ginn", "stierwen", "gestuerwen"),
    },
    "communication": {
        "fr": (
            "déclarer", "annoncer", "rapporter", "mentionner",
            "affirmer", "prétendre", "signaler", "indiquer",
        ),
        "de": (
            "erklären", "ankündigen", "berichten", "erwähnen",
            "behaupten", "melden", "angeben", "mitteilen",
        ),
        "en": (
            "declare", "announce", "report", "mention",
            "claim", "state", "indicate", "assert",
        ),
        "lb": (
            "erklären", "ukënnegen", "berichten", "ernimmen",
            "behaapt", "mellen", "uginn", "matdeelen",
        ),
    },
}


# ---------------------------------------------------------------------------
# Mention expansion
# ---------------------------------------------------------------------------

def expand_mentions(
    inst: RelationInstance,
) -> tuple[list[str], list[str]]:
    """Augment ``pers_mentions_list`` / ``loc_mentions_list`` with title
    patterns, pronoun heuristics, and Wikidata aliases (Specs v2 §4.1.1).

    Used for co-occurrence / proximity features. Exact-match features (e.g.
    preposition link, genitive) should keep using the original lists.
    """
    pers = list(inst.pers_mentions_list or [])
    locs = list(inst.loc_mentions_list or [])
    context = inst.context or ""
    lang = (inst.language or "en").lower()

    # 1. Title patterns near a named person mention.
    for pm in list(pers):
        if not pm:
            continue
        pos = context.find(pm)
        if pos < 0:
            continue
        before = context[max(0, pos - 80) : pos]
        after = context[pos + len(pm) : min(len(context), pos + len(pm) + 80)]
        pat = _TITLE_PATTERNS.get(lang, _TITLE_PATTERNS["en"])
        if lang == "lb":
            pat = f"(?:{_TITLE_PATTERNS['lb']}|{_TITLE_PATTERNS['de']})"
        for match in re.finditer(pat, before + " " + after, re.IGNORECASE):
            title = match.group().strip()
            if title and title not in pers:
                pers.append(title)

    # 2. Pronouns in same sentence as a named person mention.
    pron = list(_PRONOUNS.get(lang, _PRONOUNS["en"]))
    if lang == "lb":
        pron = list(set(pron + list(_PRONOUNS["de"])))
    sentences = re.split(r"[.!?]+", context)
    named = list(inst.pers_mentions_list or [])
    for sent in sentences:
        if any(pm in sent for pm in named if pm):
            for p in pron:
                if re.search(r"\b" + re.escape(p) + r"\b", sent, re.IGNORECASE):
                    if p not in pers:
                        pers.append(p)

    # 3. Wikidata location aliases (if available).
    loc_ctx = inst.location_context or {}
    aliases = loc_ctx.get("aliases", []) if isinstance(loc_ctx, dict) else []
    for alias in aliases:
        if alias and alias in context and alias not in locs:
            locs.append(alias)

    return pers, locs


# ---------------------------------------------------------------------------
# Evidence-strength features
# ---------------------------------------------------------------------------

def _has_match(haystack: str, needle: str) -> bool:
    return bool(needle) and (needle.lower() in haystack)


def extract_evidence_features(inst: RelationInstance) -> dict[str, float]:
    """Compute the 13-d evidence-strength feature dict for one instance."""
    context = inst.context or ""
    text = inst.text or ""
    pers_orig = [pm for pm in (inst.pers_mentions_list or []) if pm]
    loc_orig = [lm for lm in (inst.loc_mentions_list or []) if lm]
    pers_exp, loc_exp = expand_mentions(inst)

    feats: dict[str, float] = {}

    # 1. Entity proximity (use ORIGINAL named mentions for surface distance).
    min_dist = float("inf")
    for pm in pers_orig:
        for lm in loc_orig:
            p_pos = context.find(pm)
            l_pos = context.find(lm)
            if p_pos >= 0 and l_pos >= 0:
                gap = abs(p_pos - l_pos) - len(pm if p_pos < l_pos else lm)
                min_dist = min(min_dist, max(0, gap))
    feats["entity_char_distance"] = (
        min(min_dist / 500.0, 1.0) if min_dist < float("inf") else 1.0
    )
    feats["entities_adjacent"] = (
        float(min_dist < 20) if min_dist < float("inf") else 0.0
    )

    # 2. Direct preposition link (original mentions, surface form).
    has_prep = False
    for pm in pers_orig:
        for lm in loc_orig:
            p1 = re.search(
                re.escape(pm) + r"\s*,?\s*" + _PREP_PATTERN + re.escape(lm),
                context, re.IGNORECASE,
            )
            p2 = re.search(
                re.escape(lm) + r"\s*,?\s*" + _PREP_PATTERN + re.escape(pm),
                context, re.IGNORECASE,
            )
            if p1 or p2:
                has_prep = True
                break
        if has_prep:
            break
    feats["has_preposition_link"] = float(has_prep)

    # 3. Genitive construction (original mentions).
    has_gen = False
    for pat in _GENITIVE_PATTERNS:
        for lm in loc_orig:
            if re.search(pat + re.escape(lm), context, re.IGNORECASE):
                has_gen = True
                break
        if has_gen:
            break
    feats["has_genitive_construction"] = float(has_gen)

    # 4. Role / title words.
    ctx_lower = context.lower()
    feats["has_role_title"] = float(
        any(rw.lower() in ctx_lower for rw in ROLE_WORDS)
    )

    # 5. Hedging language (count + binary).
    n_hedges = sum(1 for hw in HEDGING_WORDS if hw.lower() in ctx_lower)
    feats["has_hedging"] = float(n_hedges > 0)
    feats["n_hedging_words"] = min(n_hedges / 3.0, 1.0)

    # 6. Quotation context (any entity inside quoted span).
    in_quotes = False
    quote_regions = [(m.start(), m.end()) for m in _QUOTE_REGEX.finditer(context)]
    for m in pers_orig + loc_orig:
        pos = context.find(m)
        if pos >= 0:
            for qs, qe in quote_regions:
                if qs <= pos <= qe:
                    in_quotes = True
                    break
            if in_quotes:
                break
    feats["entity_in_quotes"] = float(in_quotes)

    # 7. Subjunctive / conditional mood.
    feats["has_subjunctive"] = float(
        any(sm.lower() in ctx_lower for sm in SUBJUNCTIVE_MARKERS)
    )

    # 8. Multi-mention counts (use expanded lists).
    person_count = sum(text.count(pm) for pm in pers_exp if pm)
    loc_count = sum(text.count(lm) for lm in loc_exp if lm)
    feats["person_mention_count"] = min(person_count / 10.0, 1.0)
    feats["location_mention_count"] = min(loc_count / 10.0, 1.0)

    # 9. Co-occurrence (sentences containing BOTH a person and a location).
    sentences = re.split(r"[.!?]+", text)
    cooc = 0
    for sent in sentences:
        has_p = any(pm in sent for pm in pers_exp if pm)
        has_l = any(lm in sent for lm in loc_exp if lm)
        if has_p and has_l:
            cooc += 1
    feats["cooccurrence_sentences"] = min(cooc / 5.0, 1.0)

    # 10. Competing locations (rough heuristic on capitalised tokens after a prep).
    loc_indicators = re.findall(
        r"\b(?:à|en|de|in|at|from|von|aus|nach)\s+[A-Z][a-zéèêëàâôùûç]+",
        text,
    )
    n_other = max(0, len(set(loc_indicators)) - len(loc_orig))
    feats["n_competing_locations"] = min(n_other / 10.0, 1.0)

    return feats


def evidence_matrix(instances: Iterable[RelationInstance]) -> np.ndarray:
    """Stack ``extract_evidence_features`` over a list of instances → (N, 13)."""
    rows = [extract_evidence_features(i) for i in instances]
    return np.array(
        [[r[name] for name in EVIDENCE_FEATURE_NAMES] for r in rows],
        dtype=np.float32,
    )


# ---------------------------------------------------------------------------
# Verb-type classification
# ---------------------------------------------------------------------------

def classify_verb_type(inst: RelationInstance) -> dict[str, float]:
    """Compute the 7-d verb-type feature dict for one instance."""
    context = (inst.context or "").lower()
    lang = (inst.language or "en").lower()

    feats: dict[str, float] = {}
    for vtype, lang_verbs in VERB_LEXICON.items():
        verbs = list(lang_verbs.get(lang, ()))
        if lang == "lb":
            verbs = list(set(verbs + list(lang_verbs.get("de", ()))))
        if not verbs:
            verbs = list(lang_verbs.get("en", ()))
        feats[f"verb_type_{vtype}"] = float(any(v in context for v in verbs))

    feats["verb_strong_evidence"] = float(
        feats.get("verb_type_role", 0.0) or feats.get("verb_type_stative", 0.0)
    )
    feats["verb_indirect_evidence"] = float(
        feats.get("verb_type_communication", 0.0)
    )
    return feats


def verb_type_matrix(instances: Iterable[RelationInstance]) -> np.ndarray:
    rows = [classify_verb_type(i) for i in instances]
    return np.array(
        [[r[name] for name in VERB_TYPE_FEATURE_NAMES] for r in rows],
        dtype=np.float32,
    )


__all__ = [
    "EVIDENCE_FEATURE_NAMES",
    "VERB_TYPE_FEATURE_NAMES",
    "VERB_LEXICON",
    "ROLE_WORDS",
    "HEDGING_WORDS",
    "SUBJUNCTIVE_MARKERS",
    "expand_mentions",
    "extract_evidence_features",
    "evidence_matrix",
    "classify_verb_type",
    "verb_type_matrix",
]
