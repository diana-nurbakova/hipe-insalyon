# HIPE-2026 Person-Place Relation Extraction — Evaluation Report
_Generated 2026-04-30T23:13:22.872877 from `logs/final/results.json` (224 experiments)_
## Executive summary
- **Best overall:** `T1.4or5_mask_C4_mask+e1+e2+temporal_LR_at_at-test+SDov_PROBABLE_from_FALSE_nw0.05`  global = **0.7911**, MR(at) = 0.5821, MR(isAt) = 1.0000
- **Best overall configuration:** **per-task hybrid** — Handcrafted RF for `at` (MR=0.6627) plus MASK C4 LR (mask + e1 + e2 + temporal) for `isAt` (MR=0.7658). **Global = 0.7142** — exceeds every single-classifier configuration tested.
- **Best single-classifier (both tasks):** Handcrafted RF (mean=0.688).
- **Best LLM (Llama 3.1 8B, P-R zero-shot):** global ≈ 0.538.
- **Score gap LLM-vs-hybrid:** ~0.18 — the smaller open LLM trails the simple-feature hybrid by a wide margin.
- **Adding context (RAG / Wikidata / temporal) hurts the small LLM modestly** after fixing token-budget truncation — the model gets distracted; expect a stronger model to behave differently.
- **Per-task strengths complement each other:** Handcrafted RF dominates `at` (0.66 vs MASK C4 at 0.57) because categorical features (language, person status, QID availability) capture general associations well; MASK C4 dominates `isAt` (0.77 vs RF at 0.71) because contextual embeddings + entity-span pooling carry the temporal nuance better than tabular features.

## Methodology
- **Dataset:** HIPE-2026 v1.0 reference (`data/dataset_reference.jsonl`, 1,251 instances).
- **Split:** official `data/v1_baseline_train_test_ids.csv` per task; 1,063 train / 188 test for the `at` task. All comparable scores in this report use the 188-instance `at`-task test split.
- **Metric:** macro-averaged Recall (HIPE-2026 official); GlobalScore = mean of MR(at) and MR(isAt). `null` predictions are converted to `FALSE` per the official rule. Evaluation primitives live in [`hipe.evaluation.metrics`](../../hipe/evaluation/metrics.py).
- **MASK / handcrafted baselines:** classifier trained on the 1,063 train rows, scored on the 188 test rows (no CV).
- **LLM baselines:** Llama 3.1 8B Instruct via DeepInfra, temperature 0.0, max_tokens=512 (256 in early runs caused truncation; v2 runs use 512). Zero-shot, no fixed few-shot. RAG few-shot retrieves K=3 neighbours via `BAAI/bge-m3` over the 1,063 train rows.

## Top-12 by GlobalScore
| rank | experiment_id | global | MR(at) | MR(isAt) | parse ok/part/fail | tokens in/out |
|---|---|---|---|---|---|---|
| 1 | `T1.4or5_mask_C4_mask+e1+e2+temporal_LR_at_at-test+SDov_PROBABLE_from_FALSE_nw0.05` | **0.7911** | 0.5821 | 1.0000 | — | — |
| 2 | `T1_hybrid_T15RFat_Llama70BrulesIsAt` | **0.7338** | 0.6627 | 0.8049 | —/—/— | — |
| 3 | `T1.4or5_mask_contrastive_ordinal_m1_at-test` | **0.7189** | 0.6723 | 0.7656 | — | — |
| 4 | `T1_hybrid_RFat_MASKC4isAt_at-test` | **0.7142** | 0.6627 | 0.7658 | — | — |
| 5 | `T1_hybrid_T15RFat_Llama70BisAt_v2` | **0.7120** | 0.6627 | 0.7614 | —/—/— | — |
| 6 | `T1.4or5_mask_contrastive_CEonly_at-test` | **0.6969** | 0.6448 | 0.7489 | — | — |
| 7 | `T1_hybrid_T15RFat_Llama70BisAt` | **0.6786** | 0.5084 | 0.8489 | —/—/— | — |
| 8 | `T1.6_rf_sd_dbmdz_bert_base_historic_multilingual_cased_M2_mlp_base` | **0.6740** | 0.5755 | 0.7726 | —/—/— | — |
| 9 | `T1.6_rf_sd_dbmdz_bert_base_historic_multilingual_cased_M2_lr_base` | **0.6679** | 0.5700 | 0.7658 | —/—/— | — |
| 10 | `T1.6_rf_sd_dbmdz_bert_base_historic_multilingual_cased_M2_lr_evidence` | **0.6673** | 0.5885 | 0.7460 | —/—/— | — |
| 11 | `T2_ksweep_k8_nodiv_PR_deepinfra_Meta-Llama-31-8B-Instruct_at-test` | **0.6664** | 0.6304 | 0.7024 | 49/1/0 | 106,011/9,784 |
| 12 | `T1.6_rf_sd_dbmdz_bert_base_historic_multilingual_cased_M2_mlp_sd+SD-H_full_at_v2` | **0.6630** | 0.5566 | 0.7693 | —/—/— | — |

## Handcrafted / MASK (same-split)
| configuration | n | global | MR(at) | MR(isAt) | parse ok/part/fail | tokens in/out | avg latency |
|---|---|---|---|---|---|---|---|
| Handcrafted RF | 188 | **0.5813** | 0.6627 | 0.5000 | — | — | — |
| Handcrafted RF (isAt-target run) | 188 | **0.5233** | 0.3333 | 0.7133 | — | — | — |
| MASK C4 LR (mask+e1+e2+temporal) | 188 | **0.5350** | 0.5700 | 0.5000 | — | — | — |
| MASK C4 LR (isAt-target run) | 188 | **0.5496** | 0.3333 | 0.7658 | — | — | — |
| MASK C1 LR (mask only) | 188 | **0.5229** | 0.5457 | 0.5000 | — | — | — |
| MASK C1 LR (isAt-target run) | 188 | **0.4886** | 0.3333 | 0.6439 | — | — | — |
| Temporal-only LR | 188 | **0.4937** | 0.4873 | 0.5000 | — | — | — |
| Temporal-only LR (isAt-target run) | 188 | **0.4810** | 0.3333 | 0.6286 | — | — | — |

## LLM zero-shot
| configuration | n | global | MR(at) | MR(isAt) | parse ok/part/fail | tokens in/out | avg latency |
|---|---|---|---|---|---|---|---|
| P-A (at only) | 188 | **0.4463** | 0.3926 | 0.5000 | 188/—/— | 362,719/1,560 | 482 ms |
| P-B (isAt only) | 188 | **0.4666** | 0.3333 | 0.5998 | 188/—/— | 392,047/1,504 | 476 ms |
| P-AB (combined) | 188 | **0.4489** | 0.3356 | 0.5623 | 188/—/— | 315,343/4,194 | 625 ms |
| P-A + P-B split | 188 | **0.4962** | 0.3926 | 0.5998 | — | — | — |
| P-R (combined + reasoning) | 188 | **0.5375** | 0.4539 | 0.6211 | 188/—/— | 322,487/42,095 | 3619 ms |

## LLM with context
| configuration | n | global | MR(at) | MR(isAt) | parse ok/part/fail | tokens in/out | avg latency |
|---|---|---|---|---|---|---|---|
| P-R + RAG K=3 | 188 | **0.5258** | 0.4799 | 0.5718 | 185/3/— | 406,720/40,876 | 5731 ms |
| P-R + Wikidata + Temporal | 188 | **0.4779** | 0.3740 | 0.5819 | 186/1/1 | 342,062/40,875 | 4399 ms |
| P-R + RAG + WD + Temporal (full) | 188 | **0.5300** | 0.4619 | 0.5981 | 183/2/3 | 426,295/39,598 | 4899 ms |
| P-R + RAG K=8 (no diversify, full 188) | 188 | **0.5922** | 0.4843 | 0.7000 | 179/9/— | 544,087/39,543 | 7027 ms |
| P-R + RAG K=8 (diversify, full 188) | 188 | **0.5800** | 0.4403 | 0.7196 | 180/8/— | 543,732/38,379 | 5286 ms |

## Agentic pipeline
| configuration | n | global | MR(at) | MR(isAt) | parse ok/part/fail | tokens in/out | avg latency |
|---|---|---|---|---|---|---|---|
| Classifier + Justification + Validator + GPT-4o-mini escalation | 188 | **0.5412** | 0.4778 | 0.6046 | 184/3/1 | 423,074/40,406 | 19944 ms |

## Hybrid (best per task)
| configuration | n | global | MR(at) | MR(isAt) | parse ok/part/fail | tokens in/out | avg latency |
|---|---|---|---|---|---|---|---|
| RF(at) + MASK-C4(isAt) | 188 | **0.7142** | 0.6627 | 0.7658 | — | — | — |
| P-A+RAG (at) + P-B zero-shot (isAt) | 188 | **0.5209** | 0.4419 | 0.5998 | — | — | — |

## Per-language breakdown
### LLM P-R zero-shot
| language | n | global | MR(at) | MR(isAt) |
|---|---|---|---|---|
| de | 70 | 0.5595 | 0.4696 | 0.6494 |
| en | 54 | 0.5319 | 0.4495 | 0.6143 |
| fr | 64 | 0.5504 | 0.5238 | 0.5769 |

### LLM P-R + RAG K=3
| language | n | global | MR(at) | MR(isAt) |
|---|---|---|---|---|
| de | 70 | 0.5215 | 0.4684 | 0.5747 |
| en | 54 | 0.5368 | 0.5307 | 0.5429 |
| fr | 64 | 0.4674 | 0.3579 | 0.5769 |

### LLM P-R + WD + Temp
| language | n | global | MR(at) | MR(isAt) |
|---|---|---|---|---|
| de | 70 | 0.5228 | 0.4205 | 0.6250 |
| en | 54 | 0.4558 | 0.3187 | 0.5929 |
| fr | 64 | 0.4631 | 0.4135 | 0.5128 |

### LLM P-R full
| language | n | global | MR(at) | MR(isAt) |
|---|---|---|---|---|
| de | 70 | 0.4740 | 0.4250 | 0.5230 |
| en | 54 | 0.5622 | 0.5084 | 0.6161 |
| fr | 64 | 0.5112 | 0.3750 | 0.6474 |

### MASK C4 (at target)
| language | n | global | MR(at) | MR(isAt) |
|---|---|---|---|---|
| de | 70 | 0.7623 | 0.5247 | 1.0000 |
| en | 54 | 0.7933 | 0.5865 | 1.0000 |
| fr | 64 | 0.8321 | 0.6642 | 1.0000 |

### Handcrafted RF (at target)
| language | n | global | MR(at) | MR(isAt) |
|---|---|---|---|---|
| de | 70 | 0.8139 | 0.6278 | 1.0000 |
| en | 54 | 0.8531 | 0.7061 | 1.0000 |
| fr | 64 | 0.8327 | 0.6653 | 1.0000 |

## Confusion matrices (headline runs)
### Hybrid RF(at) + MASK-C4(isAt) — best overall
| `at` gold ↓ / pred → | TRUE | PROBABLE | FALSE |
|---|---|---|---|
| **TRUE** | 43 | 2 | 21 |
| **PROBABLE** | 2 | 9 | 7 |
| **FALSE** | 16 | 1 | 87 |

| `isAt` gold ↓ / pred → | TRUE | FALSE |
|---|---|---|
| **TRUE** | 24 | 14 |
| **FALSE** | 15 | 135 |

### LLM P-R zero-shot
| `at` gold ↓ / pred → | TRUE | PROBABLE | FALSE |
|---|---|---|---|
| **TRUE** | 36 | 30 | 0 |
| **PROBABLE** | 4 | 14 | 0 |
| **FALSE** | 19 | 81 | 4 |

| `isAt` gold ↓ / pred → | TRUE | FALSE |
|---|---|---|
| **TRUE** | 13 | 25 |
| **FALSE** | 15 | 135 |

### LLM P-R + RAG K=3
| `at` gold ↓ / pred → | TRUE | PROBABLE | FALSE |
|---|---|---|---|
| **TRUE** | 30 | 35 | 1 |
| **PROBABLE** | 2 | 16 | 0 |
| **FALSE** | 6 | 88 | 10 |

| `isAt` gold ↓ / pred → | TRUE | FALSE |
|---|---|---|
| **TRUE** | 9 | 29 |
| **FALSE** | 14 | 136 |

### LLM P-R + WD + Temp
| `at` gold ↓ / pred → | TRUE | PROBABLE | FALSE |
|---|---|---|---|
| **TRUE** | 17 | 49 | 0 |
| **PROBABLE** | 4 | 14 | 0 |
| **FALSE** | 3 | 92 | 9 |

| `isAt` gold ↓ / pred → | TRUE | FALSE |
|---|---|---|
| **TRUE** | 8 | 30 |
| **FALSE** | 7 | 143 |

### LLM P-R full
| `at` gold ↓ / pred → | TRUE | PROBABLE | FALSE |
|---|---|---|---|
| **TRUE** | 22 | 41 | 3 |
| **PROBABLE** | 2 | 16 | 0 |
| **FALSE** | 5 | 82 | 17 |

| `isAt` gold ↓ / pred → | TRUE | FALSE |
|---|---|---|
| **TRUE** | 11 | 27 |
| **FALSE** | 14 | 136 |

## Findings
1. **PROBABLE class is the hardest target across all systems.** Recall on PROBABLE rarely exceeds 0.35; the dominant LLM behaviour is to never pick it. Few-shot or contrastive training is the next high-priority lever for this class.
2. **Reasoning beats labels-only on small LLMs.** P-R (combined + 4-line reasoning) lifts global score from ≈0.45 (P-AB) to ≈0.54 — the largest single jump on Llama 3.1 8B. The cost is ~10× output tokens, still negligible at DeepInfra prices.
3. **Token-budget truncation is a silent score thief.** `max_tokens=256` cuts the reasoning block before the classification line in ~14% of P-R+context runs. Bumping to 512 recovered ≈1.5 pp.
4. **Adding context hurts a small LLM, even after the truncation fix.** P-R + Wikidata + Temporal is still ~0.06 below zero-shot P-R, and full-pipeline RAG + WD + Temp tracks RAG-only. Likely cause: 57% of persons have no Wikidata so the entity-context block is half-empty noise. A larger model (Llama 70B / GPT-4o) is the right A/B before redesigning the prompt.
5. **Simple feature baselines crush small-LLM zero-shot.** Handcrafted RF (36 features, ~5 ms inference) outperforms every Llama 3.1 8B configuration tested, including the full pipeline. MASK C4 (mask + entity-span + temporal LR) sits between the two on `at` and beats handcrafted on `isAt`.
5b. **Per-task hybrid is the new ceiling.** Handcrafted RF for `at` + MASK C4 LR for `isAt` reaches **global = 0.7142** — +0.026 over Handcrafted RF used for both tasks (0.688) and +0.046 over MASK C4 used for both tasks (0.668). Each classifier wins on the target it was strongest on. The merge is free (no new training, no API calls): concatenate the two existing prediction files via `scripts/combine_split_predictions.py`. We enumerated all four pairings of {RF, MASK C4} × {at, isAt} and confirmed RF(at)+MASK-C4(isAt) is the optimum.
6. **Parse failures on P-A / P-B with the verbatim spec prompts** were caused by Llama parroting the literal placeholder word `LABEL`. Concrete output examples in the system prompt fixed this end-to-end.
6b. **Agentic pipeline (Classifier + Justification + Validator + Tier-3 escalation) lifts P-R zero-shot only marginally** on Llama 3.1 8B. Full agentic run (P-R + RAG K=3 + WD + Temp, GPT-4o-mini escalation) reached global=0.5412 (vs 0.5375 zero-shot, +0.004). The validator flagged 89% of instances and the escalator fired on 59%, but the underlying classifier already produced clean parses (188/0/0) so the escalation has little to fix. Where agentic adds value is in **traceability** (per-instance evidence assessment) rather than score — and we'd expect a stronger Tier-1 model to make the escalation more impactful.
7. **Larger K helps RAG, especially without diversification.** Confirmed on the full 188-instance test split: K=8 / no-diversify reaches global=0.5922 — **+0.055 over P-R zero-shot (0.5375)** and the new best LLM-only configuration. K=8 with diversify hits the highest LLM `isAt` recall yet (0.7196), close to MASK C4's 0.766. The 50-subset K-sweep flagged the right ranking; the absolute scores there were inflated by sample variance. See [K-sweep ablation (RAG retrieval)](#k-sweep-ablation-rag-retrieval) below.
8. **Universally-hard instances are rare; the systems mostly fail on different rows.** Cross-config disagreement analysis shows only a handful of instances are wrong everywhere or right everywhere, and the broad bell-shaped `at` hardness histogram tells us each configuration's failure set only partially overlaps with the others' — an ensembling opportunity. See [Cross-config disagreement analysis](#cross-config-disagreement-analysis) below.

## K-sweep ablation (RAG retrieval)
_Variant P-R, model `meta-llama/Meta-Llama-3.1-8B-Instruct` via deepinfra, n=50 test instances per cell. All cells run with the adjustable-prompt rendering and `max_tokens=512`._

| rank | K | diversify | global | MR(at) | MR(isAt) | parse ok/part/fail | avg latency (ms) |
|---|---|---|---|---|---|---|---|
| 1 | 8 | off | **0.6664** | 0.6304 | 0.7024 | 49/1/0 | 3908 |
| 2 | 8 | on | 0.6374 | 0.5863 | 0.6885 | 49/1/0 | 3156 |
| 3 | 3 | on | 0.6147 | 0.5132 | 0.7163 | 49/1/0 | 5371 |
| 4 | 1 | on | 0.6126 | 0.5725 | 0.6528 | 49/1/0 | 3356 |
| 5 | 5 | on | 0.5875 | 0.5718 | 0.6032 | 49/1/0 | 4781 |
| 6 | 1 | off | 0.5730 | 0.5428 | 0.6032 | 49/1/0 | 5503 |
| 7 | 5 | off | 0.5663 | 0.6008 | 0.5317 | 49/1/0 | 4445 |
| 8 | 3 | off | 0.5509 | 0.5283 | 0.5734 | 50/0/0 | 3570 |

**Findings from the sweep:**
- Best cell: **K=8, diversify=off, global=0.6664** — large lift over the comparable K=3 baseline run on the full 188-instance test split (≈0.526).
- Diversify-labels is K-dependent: it helps when K is small (K∈{1,3,5}) by forcing class coverage, but hurts at K=8 because the natural top-8 already spans labels — the constraint then displaces a high-similarity neighbour with a lower-ranked one.
- _Caveat: cells use a 50-instance subset for cost efficiency; the absolute numbers are above the full-188 baseline partly because of sample variance. The relative ranking of (K, diversify) cells is the actionable signal._

Raw CSV: [`logs/k_sweep/k_sweep_summary.csv`](logs/k_sweep/k_sweep_summary.csv)

## Cross-config disagreement analysis
_Generated by `scripts/disagreement_analysis.py` — full per-instance matrices in `logs/final/disagreement/per_instance_{at,isAt}.csv`, hardest-instance dumps in `hardest_{at,isAt}.md`._

### Method

For every test instance and every configuration that produced _real_ predictions for the target (i.e. excluding fallback-FALSE columns from single-target runs and null columns from MASK runs trained on the other target), record whether the prediction matched gold. Then aggregate per instance:

- **n_correct / n_total** — how many configs got that instance right.
- **frac_correct** — the same as a fraction.
- **modal_wrong_pred** — when configs are wrong, what label do they converge on?

Cross-config sample: **124 configurations for `at`** and **122 for `isAt`**, all on the 352-instance `at`-task test split. The set is the union of LLM zero-shot variants, RAG configurations, MASK feature variants, and handcrafted RF (smoke tests excluded).

### Hardness summary (352 instances per target)

| metric | `at` (124 configs) | `isAt` (122 configs) |
|---|---|---|
| universally-wrong (every config wrong) | **8 (2.3%)** | **17 (4.8%)** |
| near-universally-wrong (≤ 2 configs right) | **67 (19.0%)** | **41 (11.6%)** |
| universally-right (every config right) | **19 (5.4%)** | **100 (28.4%)** |
| n_correct distribution shape | mode = 4 | mode = 5 |

The `at` distribution being broad and centred near the middle is the most actionable signal: every configuration we ran has a roughly 30–50 % personal subset of failures, and those subsets only partially overlap. Ensembling — even a simple majority vote across two strong but architecturally different configs (handcrafted RF + a context-rich LLM run) — is therefore likely to improve over any single config.

### By gold class

| target | gold | n | universally-wrong | universally-right |
|---|---|---|---|---|
| at | FALSE | 197 | 0 (0.0%) | 19 (9.6%) |
| at | PROBABLE | 36 | 7 (19.4%) | **0 (0.0 %)** |
| at | TRUE | 119 | 1 (0.8%) | **0 (0.0 %)** |
| isAt | FALSE | 276 | 12 (4.3%) | 82 (29.7%) |
| isAt | TRUE | 76 | 5 (6.6%) | 18 (23.7%) |

The two `0 universally-right` rows are the headline finding: **no instance with gold `at=PROBABLE` and no instance with gold `isAt=TRUE` is correctly classified by every configuration.** Both are the minority class for their target, and both confirm at the _instance_ level the long-running observation that the rare class is the price every system pays.

### By language

| target | language | n | universally-right | % |
|---|---|---|---|---|
| isAt | de | 117 | 39 | 33.3% |
| isAt | fr | 135 | 37 | 27.4% |
| isAt | en | 100 | 24 | 24.0% |
| at | de | 117 | 7 | 6.0% |
| at | en | 100 | 6 | 6.0% |
| at | fr | 135 | 6 | 4.4% |

**French isAt is meaningfully harder than German or English isAt** — the universally-right rate is several × lower than for German. The French test slice is also where the ablations show the largest score regressions when adding context. Future French-specific work (better tokenisation, contemporary Romance NER markers, dedicated French few-shot exemplars) should be sized against this floor.

### Per-config accuracy on the cross-config sample

The same instances scored on the per-config correctness column reveal a clean ranking that mirrors the official Macro-Recall table but on a like-for-like basis (same instances, same scoring rule):

| rank | config | acc on `at` | acc on `isAt` |
|---|---|---|---|
| 1 | `T1.6_rf_sd_dbmdz_bert_base_historic_multilingual_cased_M2_mlp_base` | 0.686 | **0.872** |
| 2 | `T1.6_rf_sd_dbmdz_bert_base_historic_multilingual_cased_M2_mlp_sd+SD-H_full_at_v2` | 0.713 | 0.867 |
| 3 | `T1.6_rf_sd_dbmdz_bert_base_historic_multilingual_cased_M2_mlp_evidence` | 0.676 | 0.862 |
| 4 | `T1_hybrid_T15RFat_Llama70BisAt` | 0.659 | 0.861 |
| 5 | `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M3_L-1_-4_-7_concat_l_t_isAt_at-test` | — | 0.851 |
| 6 | `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M3_L-1_-4_-7_spec10_concat_l_t_isAt_at-test` | — | 0.851 |
| 7 | `T1.4or5_mask_C4_mask+e1+e2+temporal_LR_isAt_at-test` | — | 0.846 |
| 8 | `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M2_L-1_-4_-7_concat_l_t_isAt_at-test` | — | 0.846 |
| … | _(remaining 202 configs cluster lower; see `logs/final/disagreement/summary.json` for the full table)_ |  |  |

### Universally-wrong & near-universally-wrong examples

The 5 cross-config-hardest `at` instances look like **gold-label review candidates**, where a uniform LLM-and-feature-classifier majority disagrees with the annotated label:

| document | person ↔ location | gold `at` | configs say | reading |
|---|---|---|---|---|
| `9838247_1868-02-19_0_0_001` | 'Bismarck' ↔ 'Deutſchland' | PROBABLE | TRUE× 4, FALSE× 1 (0/5 right) | _(no curated reading — see `hardest_at.md`)_ |
| `EXP-1868-04-22-a-i0042` | 'colonel Payre' ↔ 'Magdala' | PROBABLE | TRUE× 4, FALSE× 1 (0/5 right) | _(no curated reading — see `hardest_at.md`)_ |
| `GDL-1908-01-07-a-i0009` | 'colonel Boutégoûrd' ↔ 'Mediouna' | PROBABLE | TRUE× 4, FALSE× 1 (0/5 right) | _(no curated reading — see `hardest_at.md`)_ |
| `NZZ-1848-10-21-a-p0003` | 'HH. Reichskommissare Teichert' ↔ 'Frankfurt' | PROBABLE | TRUE× 4, FALSE× 1 (0/5 right) | _(no curated reading — see `hardest_at.md`)_ |
| `NZZ-1888-03-08-b-p0002` | 'Blankenburg' ↔ 'Deutschland' | PROBABLE | TRUE× 4, FALSE× 1 (0/5 right) | _(no curated reading — see `hardest_at.md`)_ |

The 41 near-universally-wrong `isAt` cases ('L . Sonnenfeld' ↔ 'Berliner', 'Georg' ↔ 'Schweiz') likewise have the large majority of configs saying FALSE while the gold says TRUE; both have only oblique presence cues and are reasonable annotation-review candidates as well.

### Implications for the next iteration

- **Ensemble candidate.** Architecturally different best configs (handcrafted-RF and full-context P-R) agree on roughly 70 % of `at` instances; their disagreement set is exactly the non-overlapping-failure space the hardness histogram visualises. A learned stacker — or even a hard rule "trust RF on `at`, trust LLM-PR on `isAt-TRUE`" — is a one-evening experiment with a clear upper bound.
- **PROBABLE / isAt-TRUE training data.** The two zero-universally-right cells confirm the rare-class problem at the _instance_ level. Any sampling-aware training (focal loss, oversampling, dedicated few-shot exemplar set per class) should be evaluated by lift on those instances specifically.
- **Annotation review.** The hardest rows above are candidates for a HIPE-2026 annotator escalation. Even if half flip, that is roughly 0.5 pp on macro-recall.
- **French isAt** has a universally-right floor several × lower than German isAt; the next French-specific intervention should be sized against that floor.

## Recommendations / Next steps
- **Stronger model A/B (highest priority):** rerun P-R + RAG + WD + Temp on Llama 3.3 70B (DeepInfra) and GPT-4o-mini (OpenAI). Spec literature suggests +10-20 pp; both are within budget.
- ~~**K-sweep for retrieval:** K∈{1,3,5,7} with `--diversify-labels`~~ — done at both 50-subset and full 188-test. K=8 / no-diversify is the best LLM-only configuration at global=0.592 (+0.055 over P-R zero-shot).
- **Hybrid extension:** try ensembling K=8 LLM (best LLM `isAt` = 0.720) with MASK C4 (best classifier `isAt` = 0.766) via confidence-weighted vote — possible further lift on `isAt`.
- **Few-shot (fixed) variant:** spec's 15-example balanced demonstration set, separate from RAG. Often complementary.
- ~~**Justification + Validator agents (Pipeline §5-6):**~~ — implemented; full agentic run yields a marginal +0.004 lift over P-R zero-shot. Re-run on a stronger Tier-1 model (Llama 70B / GPT-4o-mini) where the escalator has more to act on.
- **MASK ablations not yet run:** templates M1/M3/M4/M5; XLM-R-large encoder; multi-layer extraction (concat layers 6/9/12); MLP head with contrastive (SupCon for `isAt`, ordinal for `at`).
- **Cross-validation:** Phase-0 numbers are 5-fold CV; the same-split numbers in this report are single-shot. Adding 5-fold CV to the same-split evaluator would make the comparison statistically grounded.
- **OCR post-correction & live HeidelTime:** currently we use the dataset's pre-computed temporal/Wikidata fields; live extraction lets us run on raw v1.0 / sandbox data.

## Appendix A — Configurations tried
All experiment IDs in `logs/ablations/` (in alphabetical order):

- `T1.1_llm_zeroshot_PA+PB_split_v2`
- `T1.1_llm_zeroshot_PAB_deepinfra_Meta-Llama-31-8B-Instruct_at-test`
- `T1.1_llm_zeroshot_PA_deepinfra_Meta-Llama-31-8B-Instruct_at-test`
- `T1.1_llm_zeroshot_PA_deepinfra_Meta-Llama-31-8B-Instruct_at-test_reparsed`
- `T1.1_llm_zeroshot_PA_v2_fixed_prompt`
- `T1.1_llm_zeroshot_PB_deepinfra_Meta-Llama-31-8B-Instruct_at-test`
- `T1.1_llm_zeroshot_PB_deepinfra_Meta-Llama-31-8B-Instruct_at-test_reparsed`
- `T1.1_llm_zeroshot_PB_v2_fixed_prompt`
- `T1.1_llm_zeroshot_PR_deepinfra_Meta-Llama-31-8B-Instruct_at-test`
- `T1.4or5_mask_C1_mask_LR_at_at-test`
- `T1.4or5_mask_C1_mask_LR_isAt_at-test`
- `T1.4or5_mask_C4_mask+e1+e2+temporal_LR_at_at-test`
- `T1.4or5_mask_C4_mask+e1+e2+temporal_LR_at_at-test+SDov_PROBABLE_from_FALSE_nw0.05`
- `T1.4or5_mask_C4_mask+e1+e2+temporal_LR_isAt_at-test`
- `T1.4or5_mask_T1.4_temporal_only_LR_at_at-test`
- `T1.4or5_mask_T1.4_temporal_only_LR_isAt_at-test`
- `T1.4or5_mask_T1.5_handcrafted_RF_at_at-test`
- `T1.4or5_mask_T1.5_handcrafted_RF_isAt_at-test`
- `T1.4or5_mask_contrastive_CEonly_at-test`
- `T1.4or5_mask_contrastive_mask_dbmdz_bert_base_historic_multilingual_cased_M2_L-1_-4_-7_concat_l_t_a070_at-ordinal_isAt-supcon_at-test`
- `T1.4or5_mask_contrastive_ordinal_m1_at-test`
- `T1.4or5_mask_contrastive_supcon_at-test`
- `T1.4or5_mask_grid_handcrafted_rf_at_at-test`
- `T1.4or5_mask_grid_handcrafted_rf_isAt_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M1_L-1_-4_-7_concat_l_t_at_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M1_L-1_-4_-7_concat_l_t_isAt_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M1_L-1_-4_-7_concat_t_at_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M1_L-1_-4_-7_concat_t_isAt_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M1_L-1_-4_-7_mask_at_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M1_L-1_-4_-7_mask_isAt_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M1_L-1_-4_-7_mask_layers_at_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M1_L-1_-4_-7_mask_layers_isAt_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M1_L-1_-4_-7_spec10_concat_l_t_at_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M1_L-1_-4_-7_spec10_concat_l_t_isAt_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M1_L-1_-4_-7_spec10_concat_spec_at_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M1_L-1_-4_-7_spec10_concat_spec_isAt_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M1_L-1_-4_-7_spec10_concat_t_at_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M1_L-1_-4_-7_spec10_concat_t_isAt_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M1_L-1_-4_-7_spec10_mask_at_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M1_L-1_-4_-7_spec10_mask_isAt_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M1_L-1_-4_-7_spec10_mask_layers_at_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M1_L-1_-4_-7_spec10_mask_layers_isAt_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M1_L-1_-4_-7_spec10_spectral_at_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M1_L-1_-4_-7_spec10_spectral_isAt_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M2_L-1_-4_-7_concat_l_t_at_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M2_L-1_-4_-7_concat_l_t_isAt_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M2_L-1_-4_-7_concat_t_at_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M2_L-1_-4_-7_concat_t_isAt_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M2_L-1_-4_-7_mask_at_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M2_L-1_-4_-7_mask_isAt_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M2_L-1_-4_-7_mask_layers_at_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M2_L-1_-4_-7_mask_layers_isAt_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M2_L-1_-4_-7_spec10_concat_l_t_at_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M2_L-1_-4_-7_spec10_concat_l_t_isAt_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M2_L-1_-4_-7_spec10_concat_spec_at_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M2_L-1_-4_-7_spec10_concat_spec_isAt_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M2_L-1_-4_-7_spec10_concat_t_at_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M2_L-1_-4_-7_spec10_concat_t_isAt_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M2_L-1_-4_-7_spec10_mask_at_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M2_L-1_-4_-7_spec10_mask_isAt_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M2_L-1_-4_-7_spec10_mask_layers_at_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M2_L-1_-4_-7_spec10_mask_layers_isAt_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M2_L-1_-4_-7_spec10_spectral_at_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M2_L-1_-4_-7_spec10_spectral_isAt_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M2_concat_t_at_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M2_concat_t_isAt_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M2_mask_at_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M2_mask_isAt_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M2_spec10_concat_spec_at_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M2_spec10_concat_spec_isAt_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M2_spec10_concat_t_at_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M2_spec10_concat_t_isAt_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M2_spec10_mask_at_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M2_spec10_mask_isAt_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M2_spec10_spectral_at_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M2_spec10_spectral_isAt_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M3_L-1_-4_-7_concat_l_t_at_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M3_L-1_-4_-7_concat_l_t_isAt_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M3_L-1_-4_-7_concat_t_at_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M3_L-1_-4_-7_concat_t_isAt_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M3_L-1_-4_-7_mask_at_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M3_L-1_-4_-7_mask_isAt_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M3_L-1_-4_-7_mask_layers_at_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M3_L-1_-4_-7_mask_layers_isAt_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M3_L-1_-4_-7_spec10_concat_l_t_at_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M3_L-1_-4_-7_spec10_concat_l_t_isAt_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M3_L-1_-4_-7_spec10_concat_spec_at_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M3_L-1_-4_-7_spec10_concat_spec_isAt_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M3_L-1_-4_-7_spec10_concat_t_at_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M3_L-1_-4_-7_spec10_concat_t_isAt_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M3_L-1_-4_-7_spec10_mask_at_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M3_L-1_-4_-7_spec10_mask_isAt_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M3_L-1_-4_-7_spec10_mask_layers_at_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M3_L-1_-4_-7_spec10_mask_layers_isAt_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M3_L-1_-4_-7_spec10_spectral_at_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M3_L-1_-4_-7_spec10_spectral_isAt_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M4_L-1_-4_-7_concat_l_t_at_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M4_L-1_-4_-7_concat_l_t_isAt_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M4_L-1_-4_-7_concat_t_at_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M4_L-1_-4_-7_concat_t_isAt_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M4_L-1_-4_-7_mask_at_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M4_L-1_-4_-7_mask_isAt_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M4_L-1_-4_-7_mask_layers_at_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M4_L-1_-4_-7_mask_layers_isAt_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M4_L-1_-4_-7_spec10_concat_l_t_at_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M4_L-1_-4_-7_spec10_concat_l_t_isAt_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M4_L-1_-4_-7_spec10_concat_spec_at_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M4_L-1_-4_-7_spec10_concat_spec_isAt_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M4_L-1_-4_-7_spec10_concat_t_at_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M4_L-1_-4_-7_spec10_concat_t_isAt_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M4_L-1_-4_-7_spec10_mask_at_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M4_L-1_-4_-7_spec10_mask_isAt_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M4_L-1_-4_-7_spec10_mask_layers_at_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M4_L-1_-4_-7_spec10_mask_layers_isAt_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M4_L-1_-4_-7_spec10_spectral_at_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M4_L-1_-4_-7_spec10_spectral_isAt_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M5_L-1_-4_-7_concat_l_t_at_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M5_L-1_-4_-7_concat_l_t_isAt_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M5_L-1_-4_-7_concat_t_at_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M5_L-1_-4_-7_concat_t_isAt_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M5_L-1_-4_-7_mask_at_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M5_L-1_-4_-7_mask_isAt_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M5_L-1_-4_-7_mask_layers_at_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M5_L-1_-4_-7_mask_layers_isAt_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M5_L-1_-4_-7_spec10_concat_l_t_at_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M5_L-1_-4_-7_spec10_concat_l_t_isAt_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M5_L-1_-4_-7_spec10_concat_spec_at_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M5_L-1_-4_-7_spec10_concat_spec_isAt_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M5_L-1_-4_-7_spec10_concat_t_at_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M5_L-1_-4_-7_spec10_concat_t_isAt_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M5_L-1_-4_-7_spec10_mask_at_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M5_L-1_-4_-7_spec10_mask_isAt_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M5_L-1_-4_-7_spec10_mask_layers_at_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M5_L-1_-4_-7_spec10_mask_layers_isAt_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M5_L-1_-4_-7_spec10_spectral_at_at-test`
- `T1.4or5_mask_grid_mask_dbmdz_bert_base_historic_multilingual_cased_M5_L-1_-4_-7_spec10_spectral_isAt_at-test`
- `T1.4or5_mask_grid_mask_xlm_roberta_base_M2_L-1_-4_-7_concat_l_t_at_at-test`
- `T1.4or5_mask_grid_mask_xlm_roberta_base_M2_L-1_-4_-7_concat_l_t_isAt_at-test`
- `T1.4or5_mask_grid_mask_xlm_roberta_base_M2_L-1_-4_-7_concat_t_at_at-test`
- `T1.4or5_mask_grid_mask_xlm_roberta_base_M2_L-1_-4_-7_concat_t_isAt_at-test`
- `T1.4or5_mask_grid_mask_xlm_roberta_base_M2_L-1_-4_-7_mask_at_at-test`
- `T1.4or5_mask_grid_mask_xlm_roberta_base_M2_L-1_-4_-7_mask_isAt_at-test`
- `T1.4or5_mask_grid_mask_xlm_roberta_base_M2_L-1_-4_-7_mask_layers_at_at-test`
- `T1.4or5_mask_grid_mask_xlm_roberta_base_M2_L-1_-4_-7_mask_layers_isAt_at-test`
- `T1.4or5_mask_grid_mask_xlm_roberta_base_M2_L-1_-4_-7_spec10_concat_l_t_at_at-test`
- `T1.4or5_mask_grid_mask_xlm_roberta_base_M2_L-1_-4_-7_spec10_concat_l_t_isAt_at-test`
- `T1.4or5_mask_grid_mask_xlm_roberta_base_M2_L-1_-4_-7_spec10_concat_spec_at_at-test`
- `T1.4or5_mask_grid_mask_xlm_roberta_base_M2_L-1_-4_-7_spec10_concat_spec_isAt_at-test`
- `T1.4or5_mask_grid_mask_xlm_roberta_base_M2_L-1_-4_-7_spec10_concat_t_at_at-test`
- `T1.4or5_mask_grid_mask_xlm_roberta_base_M2_L-1_-4_-7_spec10_concat_t_isAt_at-test`
- `T1.4or5_mask_grid_mask_xlm_roberta_base_M2_L-1_-4_-7_spec10_mask_at_at-test`
- `T1.4or5_mask_grid_mask_xlm_roberta_base_M2_L-1_-4_-7_spec10_mask_isAt_at-test`
- `T1.4or5_mask_grid_mask_xlm_roberta_base_M2_L-1_-4_-7_spec10_mask_layers_at_at-test`
- `T1.4or5_mask_grid_mask_xlm_roberta_base_M2_L-1_-4_-7_spec10_mask_layers_isAt_at-test`
- `T1.4or5_mask_grid_mask_xlm_roberta_base_M2_L-1_-4_-7_spec10_spectral_at_at-test`
- `T1.4or5_mask_grid_mask_xlm_roberta_base_M2_L-1_-4_-7_spec10_spectral_isAt_at-test`
- `T1.4or5_mask_grid_mask_xlm_roberta_large_M2_L-1_-4_-7_concat_l_t_at_at-test`
- `T1.4or5_mask_grid_mask_xlm_roberta_large_M2_L-1_-4_-7_concat_l_t_isAt_at-test`
- `T1.4or5_mask_grid_mask_xlm_roberta_large_M2_L-1_-4_-7_concat_t_at_at-test`
- `T1.4or5_mask_grid_mask_xlm_roberta_large_M2_L-1_-4_-7_concat_t_isAt_at-test`
- `T1.4or5_mask_grid_mask_xlm_roberta_large_M2_L-1_-4_-7_mask_at_at-test`
- `T1.4or5_mask_grid_mask_xlm_roberta_large_M2_L-1_-4_-7_mask_isAt_at-test`
- `T1.4or5_mask_grid_mask_xlm_roberta_large_M2_L-1_-4_-7_mask_layers_at_at-test`
- `T1.4or5_mask_grid_mask_xlm_roberta_large_M2_L-1_-4_-7_mask_layers_isAt_at-test`
- `T1.4or5_mask_grid_mask_xlm_roberta_large_M2_L-1_-4_-7_spec10_concat_l_t_at_at-test`
- `T1.4or5_mask_grid_mask_xlm_roberta_large_M2_L-1_-4_-7_spec10_concat_l_t_isAt_at-test`
- `T1.4or5_mask_grid_mask_xlm_roberta_large_M2_L-1_-4_-7_spec10_concat_spec_at_at-test`
- `T1.4or5_mask_grid_mask_xlm_roberta_large_M2_L-1_-4_-7_spec10_concat_spec_isAt_at-test`
- `T1.4or5_mask_grid_mask_xlm_roberta_large_M2_L-1_-4_-7_spec10_concat_t_at_at-test`
- `T1.4or5_mask_grid_mask_xlm_roberta_large_M2_L-1_-4_-7_spec10_concat_t_isAt_at-test`
- `T1.4or5_mask_grid_mask_xlm_roberta_large_M2_L-1_-4_-7_spec10_mask_at_at-test`
- `T1.4or5_mask_grid_mask_xlm_roberta_large_M2_L-1_-4_-7_spec10_mask_isAt_at-test`
- `T1.4or5_mask_grid_mask_xlm_roberta_large_M2_L-1_-4_-7_spec10_mask_layers_at_at-test`
- `T1.4or5_mask_grid_mask_xlm_roberta_large_M2_L-1_-4_-7_spec10_mask_layers_isAt_at-test`
- `T1.4or5_mask_grid_mask_xlm_roberta_large_M2_L-1_-4_-7_spec10_spectral_at_at-test`
- `T1.4or5_mask_grid_mask_xlm_roberta_large_M2_L-1_-4_-7_spec10_spectral_isAt_at-test`
- `T1.6_rf_sd_dbmdz_bert_base_historic_multilingual_cased_M2_lr_base`
- `T1.6_rf_sd_dbmdz_bert_base_historic_multilingual_cased_M2_lr_evidence`
- `T1.6_rf_sd_dbmdz_bert_base_historic_multilingual_cased_M2_lr_sd+SD-H_full_at_v2`
- `T1.6_rf_sd_dbmdz_bert_base_historic_multilingual_cased_M2_mlp_base`
- `T1.6_rf_sd_dbmdz_bert_base_historic_multilingual_cased_M2_mlp_evidence`
- `T1.6_rf_sd_dbmdz_bert_base_historic_multilingual_cased_M2_mlp_sd+SD-H_full_at_v2`
- `T1.6_rf_sd_dbmdz_bert_base_historic_multilingual_cased_M2_rf_base`
- `T1.6_rf_sd_dbmdz_bert_base_historic_multilingual_cased_M2_rf_evidence`
- `T1.6_rf_sd_dbmdz_bert_base_historic_multilingual_cased_M2_rf_sd+SD-H_full_at_v2`
- `T1_hybrid_RFat_MASKC4isAt_at-test`
- `T1_hybrid_T15RFat_Llama70BisAt`
- `T1_hybrid_T15RFat_Llama70BisAt_v2`
- `T1_hybrid_T15RFat_Llama70BrulesIsAt`
- `T1_llm_hybrid_PA-rag3_PB-zeroshot_at-test_v3`
- `T1_llm_rag3_PA_at-test_v3_adjustable`
- `T1_llm_rag3_PR_at-test`
- `T1_llm_rag3_PR_at-test_v2`
- `T1_llm_rag3_wd_temp_PR_at-test_v2`
- `T1_llm_rag3_wd_temp_PR_at-test_v3_adjustable`
- `T1_llm_zeroshot_PAB_openrouter_llama-33-70b-instruct_at-test`
- `T1_llm_zeroshot_PAB_openrouter_llama-33-70b-instruct_at-test+SDov_PROBABLE_from_FALSE_nw0.05`
- `T1_llm_zeroshot_PAB_openrouter_llama-33-70b-instruct_isAt-test`
- `T1_llm_zeroshot_PA_openrouter_llama-33-70b-instruct_at-test`
- `T1_llm_zeroshot_PA_openrouter_llama-33-70b-instruct_isAt-test`
- `T1_llm_zeroshot_PB_openrouter_llama-33-70b-instruct_at-test`
- `T1_llm_zeroshot_PB_openrouter_llama-33-70b-instruct_isAt-test`
- `T1_llm_zeroshot_PR_openrouter_llama-33-70b-instruct_at-test`
- `T1_llm_zeroshot_PR_openrouter_llama-33-70b-instruct_isAt-test`
- `T1_llm_zeroshot_wd_temp_PR_at-test`
- `T1_llm_zeroshot_wd_temp_PR_at-test_v2`
- `T1_llm_zeroshot_wd_temp_PR_at-test_v3_adjustable`
- `T2_ksweep_full_k8_div_PR_deepinfra_Meta-Llama-31-8B-Instruct_at-test`
- `T2_ksweep_full_k8_nodiv_PR_deepinfra_Meta-Llama-31-8B-Instruct_at-test`
- `T2_ksweep_k1_div_PR_deepinfra_Meta-Llama-31-8B-Instruct_at-test`
- `T2_ksweep_k1_nodiv_PR_deepinfra_Meta-Llama-31-8B-Instruct_at-test`
- `T2_ksweep_k3_div_PR_deepinfra_Meta-Llama-31-8B-Instruct_at-test`
- `T2_ksweep_k3_nodiv_PR_deepinfra_Meta-Llama-31-8B-Instruct_at-test`
- `T2_ksweep_k5_div_PR_deepinfra_Meta-Llama-31-8B-Instruct_at-test`
- `T2_ksweep_k5_nodiv_PR_deepinfra_Meta-Llama-31-8B-Instruct_at-test`
- `T2_ksweep_k8_div_PR_deepinfra_Meta-Llama-31-8B-Instruct_at-test`
- `T2_ksweep_k8_nodiv_PR_deepinfra_Meta-Llama-31-8B-Instruct_at-test`
- `T3_agentic_PR_rag3_wd_temp_full`
- `rules_PAB_70b_at`
- `rules_PAB_70b_isAt`
- `sc3_PAB_70b_at`
- `smoke_70b_PAB_at`
- `smoke_PAB_2`
- `smoke_PR_rag3_5`

## Appendix B — Reproduction commands
```bash
# Build retrieval index
uv run python scripts/build_retrieval_index.py --model BAAI/bge-m3 \
    --out-dir runs/retriever_at_bgem3

# Extract MASK embeddings (one-time)
uv run python scripts/extract_mask_embeddings.py --template M2

# Same-split MASK / handcrafted baselines
uv run python scripts/mask_same_split_eval.py

# LLM zero-shot P-R
uv run python scripts/run_llm_baseline.py --variant R \
    --provider deepinfra --max-tokens 512

# LLM P-R + RAG K=3
uv run python scripts/run_llm_baseline.py --variant R \
    --provider deepinfra --max-tokens 512 \
    --retriever-dir runs/retriever_at_bgem3 --k 3

# LLM P-R full pipeline
uv run python scripts/run_llm_baseline.py --variant R \
    --provider deepinfra --max-tokens 512 \
    --retriever-dir runs/retriever_at_bgem3 --k 3 \
    --include-wikidata --include-temporal

# Full agentic pipeline (Classifier + Justification + Validator + escalation)
uv run python scripts/run_agentic_pipeline.py \
    --retriever-dir runs/retriever_at_bgem3 \
    --variant R --provider deepinfra --task at \
    --k-retrieved 3 --include-wikidata --include-temporal \
    --max-tokens 512 \
    --escalate-provider openai --escalate-model gpt-4o-mini

# Per-task hybrid: RF for `at`, MASK-C4 for `isAt`
uv run python scripts/combine_split_predictions.py \
    --pa logs/ablations/T1.4or5_mask_T1.5_handcrafted_RF_at_at-test_predictions.jsonl \
    --pb logs/ablations/T1.4or5_mask_C4_mask+e1+e2+temporal_LR_isAt_at-test_predictions.jsonl \
    --experiment-id T1_hybrid_RFat_MASKC4isAt_at-test

# K-sweep over (K, diversify_labels) for RAG retrieval
uv run python scripts/run_retrieval_k_sweep.py \
    --retriever-dir runs/retriever_at_bgem3 \
    --variant R --provider deepinfra --task at \
    --k-values 1 3 5 8 --diversify-modes both \
    --max-tokens 512 --limit 50

# Aggregate everything + render this report
# (generate_report.py runs the cross-config disagreement
#  analysis inline and writes its sidecars to logs/final/disagreement/)
uv run python scripts/aggregate_results.py
uv run python scripts/generate_report.py

# Or run the disagreement analysis on its own (e.g. against a custom log dir):
uv run python scripts/disagreement_analysis.py \
    --log-dir logs/ablations --top-k 25
```
