"""Data loading and dataset utilities."""

from hipe.data.instance import RelationInstance, iter_jsonl, load_jsonl
from hipe.data.official import (
    collect_pair_keys,
    iter_official_documents,
    iter_official_instances,
    load_official_documents,
    official_pair_to_instance,
    parse_official_jsonl,
)
from hipe.data.split import load_baseline_split, stratified_random_split

__all__ = [
    "RelationInstance",
    "load_jsonl",
    "iter_jsonl",
    "load_baseline_split",
    "stratified_random_split",
    "iter_official_documents",
    "load_official_documents",
    "iter_official_instances",
    "parse_official_jsonl",
    "official_pair_to_instance",
    "collect_pair_keys",
]
