"""Render SD subgroups as natural-language prompt rules (Option C).

Converts a SD run's subgroups_<TARGET>.npz into a compact ``rules.txt`` that
can be passed to ``run_llm_baseline.py --rules-file``. The conversion:

  1. drops conditions whose interval spans the whole feature range (no-ops),
  2. keeps subgroups that meet --min-precision / --min-nwracc gates,
  3. picks the top-k most concise, highest-precision subgroups,
  4. formats each as one bullet per Subgroup Discovery Specs §6.3.

Usage::

    uv run python scripts/render_sd_rules.py \\
        --sd-run runs/sd/SD-H_full_at_v2 \\
        --target PROBABLE \\
        --top-k 6 --min-precision 0.4 --max-conditions 8 \\
        --out runs/sd/SD-H_full_at_v2/rules_PROBABLE.txt
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from hipe.subgroup_discovery import Subgroup, subgroup_to_prompt_rule


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _load_subgroups(npz_path: Path) -> list[Subgroup]:
    z = np.load(npz_path, allow_pickle=True)
    target = str(z["target"])
    feature_names = [str(n) for n in z["feature_names"]]
    active = z["active"]
    bounds = z["bounds"]
    extent_lens = z["extent_lens"]
    flat = z["extent_indices"]
    out: list[Subgroup] = []
    cursor = 0
    for k in range(active.shape[0]):
        n_ext = int(extent_lens[k])
        ext = flat[cursor : cursor + n_ext]
        cursor += n_ext
        out.append(
            Subgroup(
                pattern_desc="<placeholder>",
                active=active[k],
                bounds=bounds[k],
                nwracc=float(z["nwracc"][k]),
                support=int(z["support"][k]),
                support_pos=int(z["support_pos"][k]),
                precision=float(z["precision"][k]),
                extent_indices=ext,
                target_class=target,
                feature_names=tuple(feature_names),
            )
        )
    return out


def _trim_vacuous_conditions(
    sg: Subgroup,
    feature_global_mins: np.ndarray,
    feature_global_maxs: np.ndarray,
    eps: float = 1e-6,
) -> tuple[np.ndarray, np.ndarray, str]:
    """Deactivate conditions where bounds span the full feature range.

    Returns (active', bounds', pattern_desc) where ``pattern_desc`` is the
    human-readable AND-conjunction over the remaining active features.
    """
    active = sg.active.copy()
    bounds = sg.bounds.copy()
    for f in np.where(active)[0]:
        lo, hi = bounds[f]
        full_lo = feature_global_mins[f]
        full_hi = feature_global_maxs[f]
        if (lo - full_lo <= eps) and (full_hi - hi <= eps):
            active[f] = False  # condition is vacuous (covers full range)

    parts: list[str] = []
    for f in np.where(active)[0]:
        lo, hi = bounds[f]
        name = sg.feature_names[f] if sg.feature_names else f"x{f}"
        if abs(lo - hi) < eps:
            parts.append(f"{name}={lo:.3g}")
        else:
            parts.append(f"{name} in [{lo:.3g},{hi:.3g}]")
    desc = " AND ".join(parts) if parts else "(any)"
    return active, bounds, desc


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sd-run", required=True, help="SD run directory.")
    ap.add_argument("--target", default="PROBABLE")
    ap.add_argument("--top-k", type=int, default=6,
                    help="Number of rules to keep (max). Fewer is better for prompts.")
    ap.add_argument("--min-precision", type=float, default=0.5)
    ap.add_argument("--min-nwracc", type=float, default=0.05)
    ap.add_argument("--max-conditions", type=int, default=10,
                    help="Skip subgroups with more than this many non-vacuous conditions "
                         "(too verbose for prompt injection).")
    ap.add_argument("--out", default=None,
                    help="Output rules.txt path. Default: <sd-run>/rules_<TARGET>.txt")
    args = ap.parse_args()

    sd_dir = Path(args.sd_run)
    npz_path = sd_dir / f"subgroups_{args.target}.npz"
    if not npz_path.exists():
        ap.error(f"no subgroups file: {npz_path}")
    out_path = Path(args.out) if args.out else sd_dir / f"rules_{args.target}.txt"

    subgroups = _load_subgroups(npz_path)
    print(f"Loaded {len(subgroups)} subgroups from {npz_path.name}")
    if not subgroups:
        print("  no subgroups — exiting")
        out_path.write_text("", encoding="utf-8")
        return 0

    # To detect vacuous conditions reliably we need the actual feature-range
    # across the training pool. Reconstruct the SD-H feature matrix on the
    # baseline train split (cheap; 1063 rows × 42 cols) and use its per-column
    # min/max. The summary.json declares the run's config.
    import json as _json
    summary_path = sd_dir / "summary.json"
    if summary_path.exists():
        summary = _json.loads(summary_path.read_text(encoding="utf-8"))
        config = summary.get("config", "SD-H")
    else:
        # Run is mid-flight (summary.json is only written at the very end).
        # Infer config from feature_names length.
        n_feats = len(subgroups[0].feature_names or ())
        config = "SD-H" if n_feats == 42 else f"unknown({n_feats}d)"
        print(f"  summary.json missing — inferred config = {config}")
    if config != "SD-H":
        print(
            f"  warning: config is {config!r} — vacuous-condition trim only "
            "implemented for SD-H. Falling back to bounds-union heuristic."
        )
        bounds_stack = np.stack([s.bounds for s in subgroups], axis=0)
        feature_lo = bounds_stack[:, :, 0].min(axis=0)
        feature_hi = bounds_stack[:, :, 1].max(axis=0)
    else:
        from hipe.data import load_baseline_split, load_jsonl
        from hipe.subgroup_discovery import build_sd_feature_matrix

        instances = load_jsonl(PROJECT_ROOT / "data" / "dataset_reference.jsonl")
        sp = load_baseline_split(instances, task="at")
        X_tr, _names, _ = build_sd_feature_matrix(
            sp.train, mask_embeddings=None, config="SD-H", verbose=False
        )
        feature_lo = X_tr.min(axis=0)
        feature_hi = X_tr.max(axis=0)

    # Filter + trim
    rendered: list[tuple[Subgroup, int, str]] = []  # (sg, n_conditions, trimmed_desc)
    for sg in subgroups:
        if sg.precision < args.min_precision or sg.nwracc < args.min_nwracc:
            continue
        active, bounds, desc = _trim_vacuous_conditions(sg, feature_lo, feature_hi)
        n_cond = int(active.sum())
        if n_cond == 0 or n_cond > args.max_conditions:
            continue
        # Replace the subgroup's pattern_desc / active / bounds for rendering.
        sg2 = Subgroup(
            pattern_desc=desc,
            active=active,
            bounds=bounds,
            nwracc=sg.nwracc,
            support=sg.support,
            support_pos=sg.support_pos,
            precision=sg.precision,
            extent_indices=sg.extent_indices,
            target_class=sg.target_class,
            feature_names=sg.feature_names,
        )
        rendered.append((sg2, n_cond, desc))

    if not rendered:
        print(f"  no subgroups passed gates (precision>={args.min_precision}, "
              f"nwracc>={args.min_nwracc}, conditions<={args.max_conditions})")
        out_path.write_text("", encoding="utf-8")
        return 0

    # Sort: prefer concise + high-precision (higher precision first, then fewer conditions).
    rendered.sort(key=lambda t: (-t[0].precision, t[1], -t[0].nwracc))
    rendered = rendered[: args.top_k]

    lines = [
        f"High-precision triggers for class {args.target} discovered on the training pool.",
        "Use them as soft hints — only when the surface evidence supports the inference.",
        "",
    ]
    for i, (sg, n_cond, desc) in enumerate(rendered, start=1):
        rule = subgroup_to_prompt_rule(sg, target=args.target)
        lines.append(f"{i}. {rule}")
    body = "\n".join(lines) + "\n"

    out_path.write_text(body, encoding="utf-8")
    print(f"Wrote {len(rendered)} rules to {out_path}")
    # Avoid Unicode → cp1252 errors on Windows console — body is on disk anyway.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
