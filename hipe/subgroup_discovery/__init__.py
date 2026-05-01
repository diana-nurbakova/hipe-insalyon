"""Subgroup discovery for PROBABLE-class discrimination.

Implements the MCMC-COTP algorithm specified in
``specs/HIPE2026_Subgroup_Discovery_Specs.md`` (v2). Methodological basis:
MonteCloPi (Mathonat, Nurbakova, Boulicaut, Kaytoue — DSAA 2021).

Public surface
--------------
- :class:`Subgroup`                — one discovered interval pattern
- :class:`MCMCSubgroupDiscovery`   — MCMC sampler with COTP closure + MEET
- :func:`build_sd_feature_matrix`  — v2 unified feature builder (SD-H/HS/HSP)
- :func:`build_hybrid_features`    — v1 SD-P (handcrafted ⊕ PCA-MASK)
- :func:`spectral_preprocessing_for_sd` — spectral diagnostics + features
- :func:`extract_evidence_features`, :func:`evidence_matrix`
- :func:`classify_verb_type`,       :func:`verb_type_matrix`
- :func:`expand_mentions`           — pronoun + title coreference heuristic
- :func:`hierarchy_matrix`,         :func:`build_location_hierarchy`
- :func:`add_subgroup_features`    — Option A: append match indicators to X
- :func:`apply_overrides`          — Option B: post-hoc class-flip from rules
- :func:`subgroup_to_prompt_rule`  — Option C: NL rule for LLM prompts
- :func:`cv_stability`             — k-fold stability evaluation (string + Jaccard)
- :func:`semantic_stability`       — Jaccard-on-extent stability over fold groups (v3 §7.1)
"""

from hipe.subgroup_discovery.evidence import (
    EVIDENCE_FEATURE_NAMES,
    VERB_LEXICON,
    VERB_TYPE_FEATURE_NAMES,
    classify_verb_type,
    evidence_matrix,
    expand_mentions,
    extract_evidence_features,
    verb_type_matrix,
)
from hipe.subgroup_discovery.features import (
    build_hybrid_features,
    build_sd_feature_matrix,
    spectral_preprocessing_for_sd,
    transform_hybrid,
)
from hipe.subgroup_discovery.hierarchy import (
    HIERARCHY_FEATURE_NAMES,
    build_location_hierarchy,
    compute_hierarchical_mention_count,
    hierarchy_matrix,
    load_hierarchy_cache,
)
from hipe.subgroup_discovery.integration import (
    add_subgroup_features,
    apply_overrides,
    subgroup_to_prompt_rule,
    subgroups_to_prompt_block,
    summarize,
)
from hipe.subgroup_discovery.mcmc import (
    MCMCSubgroupDiscovery,
    Subgroup,
)
from hipe.subgroup_discovery.stability import cv_stability, semantic_stability

__all__ = [
    # Algorithm
    "Subgroup",
    "MCMCSubgroupDiscovery",
    # Feature builders
    "build_sd_feature_matrix",
    "build_hybrid_features",
    "transform_hybrid",
    "spectral_preprocessing_for_sd",
    # v2 feature blocks
    "EVIDENCE_FEATURE_NAMES",
    "VERB_TYPE_FEATURE_NAMES",
    "VERB_LEXICON",
    "HIERARCHY_FEATURE_NAMES",
    "extract_evidence_features",
    "evidence_matrix",
    "classify_verb_type",
    "verb_type_matrix",
    "expand_mentions",
    "build_location_hierarchy",
    "compute_hierarchical_mention_count",
    "hierarchy_matrix",
    "load_hierarchy_cache",
    # Integration
    "add_subgroup_features",
    "apply_overrides",
    "subgroup_to_prompt_rule",
    "subgroups_to_prompt_block",
    "summarize",
    "cv_stability",
    "semantic_stability",
]
