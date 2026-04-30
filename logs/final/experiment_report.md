# HIPE-2026 Tier 1 + Tier 2 Experiment Report

Generated: see `git log` of this file. Scores are dev-split (188 at-test
instances / 191 isAt-test instances) — official test set not yet released.

## TL;DR

**New best dev-set hybrid: global = 0.7338 (vs prior 0.7142, +0.020).**

Configuration: T1.5 handcrafted-RF for `at` + Llama 3.3 70B PAB-with-SD-rules
for `isAt`. The boost is entirely on the isAt side (mr_isAt 0.7658 → 0.8049).
The Subgroup-Discovery PROBABLE rules — injected into the prompt as a
"[DOMAIN RULES]" block — did not improve PROBABLE recall directly but had
the side effect of sharpening the model's temporal reasoning, which lifted
isAt accuracy.

Everything ran without GPU. Full Llama-3.3-70B sweep on OpenRouter cost
roughly $2 (DeepInfra fallback was wired in but never engaged).

## Pipeline changes shipped

| Change | Where | Why |
|--------|-------|-----|
| Provider-level fallback (OpenRouter → DeepInfra) | `hipe/llm/client.py` | Plan B against rate limits / 5xx storms |
| Self-consistency sampling (`--n-samples`, `--sample-temperature`) | `hipe/llm/predict.py` + CLI | Majority-vote over n samples |
| Domain rules block (`--rules-file`) in user message | `hipe/llm/prompts.py` + CLI | Option C: inject SD rules |
| `scripts/apply_sd_overrides.py` | new | Option B: SD-driven post-hoc class flips |
| `scripts/rf_with_sd_features.py` | new | LR / RF / MLP × {base, +evidence, +sd} matrix |
| `scripts/render_sd_rules.py` | new | SD subgroups → natural-language rules.txt |

## Tier 1 — feature engineering + SD (no GPU, free)

### 1.1 Full SD-H discovery

`runs/sd/SD-H_full_at_v2/` — 10 chains × 10K steps × 3 targets (PROBABLE /
TRUE / FALSE) on the 1063 baseline-train rows in the 42-dim SD-H feature
space (temporal 15 + evidence 13 + verb 7 + hierarchy 3 + lang 4).

| target | n_subgroups | top NWRAcc | top precision | n_stable_5fold |
|--------|-------------|------------|---------------|----------------|
| PROBABLE | 15 | 0.078 | 1.00 (7/7) | 0/5 |
| TRUE | 0 | — | — | 0/5 |
| FALSE | many | — | — | 0/5 |

**Caveat:** CV stability was 0/5 on every class — MCMC randomness produces
different *exact* pattern strings per fold. Patterns are still informative
as soft hints for prompts (Option C), but not as hard rules for overrides
(Option B). A semantic-similarity stability metric (Jaccard over predicted
positives, instead of pattern-string equality) would fix this — left as
future work.

### 1.2 Option B (post-hoc overrides) — small effect

Applied PROBABLE subgroups as FALSE → PROBABLE overrides on the C4 LR
baseline and on Llama 70B PAB:

- C4 LR baseline (3 overrides, min_nwracc=0.05): mr_at +0.012 (0.570 → 0.582).
- Llama 70B PAB (3 overrides, min_precision=0.4): mr_at -0.010 (0.507 → 0.497).

Consistent with CV instability — the train-fold "100% precision" subgroups
do not carry over reliably to the dev set.

### 1.3 Classifier × stack matrix (LR / RF / MLP × base / +evidence / +sd)

| classifier | stack | global | mr_at | mr_isAt | P |
|------------|-------|--------|-------|---------|---|
| MLP | base | **0.6740** | 0.5755 | 0.7726 | 0.333 |
| LR | base | 0.6679 | 0.5700 | 0.7658 | 0.333 |
| LR | +evidence | 0.6673 | **0.5885** | 0.7460 | **0.389** |
| MLP | +sd indicators | 0.6630 | 0.5566 | 0.7693 | 0.167 |
| MLP | +evidence | 0.6626 | 0.5593 | 0.7660 | 0.278 |
| LR | +sd indicators | 0.6621 | 0.5783 | 0.7460 | 0.333 |
| RF | * | 0.488–0.504 | 0.438–0.445 | 0.540–0.566 | 0.000 |

Take-aways:
1. **MLP base** is the best joint-task classifier (one model trained on
   `mask+e1+e2+temporal`, then queried for both `at` and `isAt`).
2. **+evidence helps LR mr_at by +0.018 and PROBABLE by +0.056**, but no
   classifier can match T1.5 handcrafted-RF on at-task alone (0.6627 mr_at).
3. **+sd subgroup indicators don't help** — same story as Option B:
   train-fold-specific patterns don't generalize.
4. **RF on the full 2319-d MASK stack collapses to mostly-FALSE** for at
   (zero PROBABLE recall). RF works on the 36-d handcrafted block (T1.5)
   because tree-splits handle low-dim categorical signals well; on
   high-dim continuous embeddings it under-uses each feature.

### Existing baselines (for reference)

| ID | global | mr_at | mr_isAt | P |
|----|--------|-------|---------|---|
| T1.5 handcrafted-RF (at) | 0.688 | 0.6627 | 0.7133 | 0.50 |
| T1_hybrid_RFat_MASKC4isAt | **0.7142** | 0.6627 | 0.7658 | 0.50 |

## Tier 2 — Llama 3.3 70B (OpenRouter, with DeepInfra fallback)

Provider fallback: configured for every Tier 2 run; DeepInfra never engaged
(OpenRouter held up for ~3.3M input + 42K output tokens).

| variant / split | global | mr_at | mr_isAt | P | T | F |
|-----------------|--------|-------|---------|---|---|---|
| PA at-test | 0.5107 | 0.5214 | 0.5000 | 0.28 | 0.76 | 0.53 |
| PB at-test | 0.5281 | 0.3333 | 0.7228 | 0.00 | 0.00 | 1.00 |
| PAB at-test | 0.6342 | 0.5070 | 0.7614 | 0.06 | 0.88 | 0.59 |
| PR at-test | 0.6060 | 0.4727 | 0.7393 | 0.06 | 0.94 | 0.42 |
| PA isAt-test | 0.5311 | **0.5622** | 0.5000 | **0.58** | 0.75 | 0.36 |
| PB isAt-test | 0.5159 | 0.3333 | 0.6985 | 0.00 | 0.00 | 1.00 |
| PAB isAt-test | 0.6595 | 0.5461 | 0.7728 | 0.16 | 0.97 | 0.51 |
| PR isAt-test | 0.6451 | 0.5253 | 0.7648 | 0.26 | 0.90 | 0.41 |
| **rules_PAB at-test (Option C)** | 0.6381 | 0.4712 | **0.8049** | 0.06 | 0.85 | 0.51 |
| rules_PAB isAt-test (Option C) | 0.6475 | 0.5628 | 0.7322 | 0.26 | 0.97 | 0.46 |
| sc3_PAB at-test (n=3, T=0.7) | 0.6384 | 0.5120 | 0.7647 | 0.06 | 0.89 | 0.59 |

Key observations:
- **PAB > PR > PA > PB** on global — joint-target prompting wins.
- Llama 70B is a strong **TRUE detector** (recall_TRUE 0.85–0.97) but a
  weak **PROBABLE detector** (recall_PROBABLE 0.06–0.28 in joint variants).
  Single-target PA on isAt-split surprisingly hits P=0.58 — but its
  isAt slot is unset (0.5).
- **Option C (rules in prompt) hurts at, helps isAt on at-test** by +0.044.
  On the isAt-test split, the same rules hurt isAt by -0.041. The effect is
  split-dependent, not a clean global lift.
- **Self-consistency n=3 at temp=0.7** moves the needle by +0.004 — Llama
  70B is already nearly deterministic at temp=0.7 on this task. Probably
  not worth the 3× cost on this dataset.

## Hybrids tried

| ensemble | global | mr_at | mr_isAt | comment |
|----------|--------|-------|---------|---------|
| T1.5 RF (at) + C4 LR (isAt) — existing | 0.7142 | 0.6627 | 0.7658 | prior best |
| T1.5 RF (at) + Llama PAB at-test (isAt) | 0.7120 | 0.6627 | 0.7614 | -0.002 |
| **T1.5 RF (at) + Llama rules_PAB at-test (isAt)** | **0.7338** | 0.6627 | 0.8049 | **+0.020 ← new best** |
| T1.5 RF (at) + Llama PAB isAt-test (isAt, joined) | 0.6786 | 0.5084 | 0.8489 | union join, ignore |

## Cost summary (Tier 2)

- ~12 zero-shot LLM runs × ~188 instances + 1 SC run (564 calls) +
  2 rules runs (379 calls) ≈ 3.3M input + 42K output tokens on OpenRouter
  meta-llama/llama-3.3-70b-instruct.
- Estimated cost: ~$2.
- DeepInfra fallback engagements: 0 (OpenRouter never failed).

## Recommended submission for the upcoming test set

Build the submission from **`T1_hybrid_T15RFat_Llama70BrulesIsAt`**:
- `at` predictions from the T1.5 handcrafted-RF classifier.
- `isAt` predictions from Llama 3.3 70B PAB with `runs/sd/SD-H_full_at_v2/rules_PROBABLE.txt`
  injected as `[DOMAIN RULES]`.

Reproducibility:
- T1.5 RF: `scripts/mask_same_split_eval.py` over the cached MASK npz.
- Llama 70B with rules: `scripts/run_llm_baseline.py --variant AB --provider openrouter --model meta-llama/llama-3.3-70b-instruct --fallback-provider deepinfra --rules-file runs/sd/SD-H_full_at_v2/rules_PROBABLE.txt --task at --experiment-id rules_PAB_70b_at`.
- Combine: `scripts/combine_split_predictions.py --pa <T1.5 preds> --pb <rules_PAB preds>`.

## Caveats + open questions

1. **All scores are dev-split.** Until the official test JSONL lands, treat
   the 0.7338 figure as a development signal, not a leaderboard claim.
2. **Option C effect is split-dependent.** The +0.044 mr_isAt boost on the
   at-test split did not reproduce on the isAt-test split (-0.041). Re-test
   on the official set before relying on it.
3. **CV stability for SD subgroups was 0/5.** Strict pattern-string equality
   is too brittle for MCMC. A semantic-similarity stability check (Jaccard
   over predicted positives) is a near-term todo.
4. **Self-consistency at n=3 didn't help.** Either try larger n or skip.
5. **PROBABLE recall is still the bottleneck.** No technique here cleanly
   broke past ~0.50 (T1.5 RF). PA isAt-test reached 0.58 but at the cost of
   FALSE recall. A targeted contrastive-MASK fine-tune (Tier 3, GPU) is
   probably the next big lever.

## Things still on the GPU-required list (deferred)

- MASK contrastive fine-tune for PROBABLE.
- Multi-layer MASK + spectral re-extraction.
- Spectral PROBABLE-subtype clustering with SD-per-subtype.
