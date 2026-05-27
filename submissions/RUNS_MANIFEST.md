# INSALyon — submissions/ folder manifest

What each subfolder of `submissions/` contains, and which model produced it.
The official submission set is **run1, run2, run3** (described in
`INSALyon_model_info.txt`). The other folders are development candidates and
duplicates kept for provenance.

All fingerprints below are `md5(...)[:8]` over the per-pair label sequence,
sorted by `(document_id, pers_entity_id, loc_entity_id)`, across all 1,118
official-test pairs (de 238 + en 162 + fr 238 + surprise-fr 480). They were
recomputed from the base-model prediction files in `logs/official_test/` and
`runs/materials/`, so the attribution is verified, not assumed.

## Mapping

| Folder | `at` predictor | `isAt` predictor | Status |
|--------|----------------|------------------|--------|
| `pure-gemma` | Gemma 4 31B (raw P-AB) | Gemma 4 31B (raw P-AB) | early baseline |
| `4-model-stacker` | lookup stacker: RF + C4-SDov + OrdContM1 + Gemma | Gemma (with `at=FALSE → isAt=FALSE` constraint) | dev candidate |
| `ambig-route-isAt` | mDeBERTa-v3 | ambiguity-routed isAt | dev candidate |
| `run1` | plurality(xlm-roberta-large, 4-model-stacker, Gemma); tiebreak = ordinal median | majority(xlm-roberta-large, Gemma 4 31B, Llama 3.3 70B) | **OFFICIAL Run 1** (highest performance) |
| `run2` | mDeBERTa-v3 (joint head) | mDeBERTa-v3 (joint head) | **OFFICIAL Run 2** (single-model baseline) |
| `run3` | plurality(xlm-roberta-large, mDeBERTa, RF); tiebreak = ordinal median | xlm-roberta-large | **OFFICIAL Run 3** (no LLM at inference) |
| `run4` | mDeBERTa-v3 | majority(xlm, Gemma, Llama) | candidate, NOT submitted |
| `run5` | 4-model-stacker | majority(xlm, Gemma, Llama) | candidate, NOT submitted |
| `run6` | plurality(xlm, stacker, Gemma) | majority(xlm, Gemma, Llama) | **byte-identical to run1** |

## Component fingerprints

`at` source → hash:
- mDeBERTa-v3 ....................... `48cb5eb5`  (run2, run4, ambig-route-isAt, materials/sub2, materials/sub3)
- 4-model lookup stacker ............ `327b7ea3`  (4-model-stacker, run5)
- Gemma 4 31B (raw) ................. `78d1870c`  (pure-gemma)
- plurality(xlm, stacker, Gemma) .... `26cac53a`  (run1, run6)
- plurality(xlm, mDeBERTa, RF) ...... `1dcec57a`  (run3)

`isAt` source → hash:
- mDeBERTa-v3 ....................... `ce780d71`  (run2, materials/sub2)
- xlm-roberta-large ................. `2df5290c`  (run3, materials/sub3)
- majority(xlm, Gemma, Llama) ....... `53e3e020`  (run1, run4, run5, run6)
- Gemma + at-constraint ............. `8c342638`  (4-model-stacker)
- ambiguity-routed ................. `18309baa`  (ambig-route-isAt)
- Gemma 4 31B (raw) ................. `d97dc8d8`  (pure-gemma)

## Verification notes
- `run1` ≡ `run6` (identical per-pair labels in all 4 test files).
- `run2` ≡ `runs/materials/submission_2_official_test_mdeberta_only`.
- `run3` ≡ `runs/materials/submission_3_official_test_mdeberta_at_roberta_isAt`
  on `isAt` (xlm-roberta), but `run3`'s `at` is the 3-way plurality, not
  mDeBERTa alone — so the official Run 3 is NOT the same as materials/sub3.
- majority(xlm, Gemma, Llama) `isAt` recomputed from
  `logs/official_test/{gemma4_31b_PAB,llama_33_70b_PAB}_official_test_predictions.jsonl`
  + xlm `isAt` from `runs/materials/.../submission_3_*` → reproduces `53e3e020`.
- `run3.at` matches mDeBERTa∧RF on all 730 pairs where they agree;
  `run1.at` matches stacker∧Gemma on all 704 pairs where they agree.

## Base-model prediction sources
- `logs/official_test/RF_official_test_{at,isAt[,isAt_calibrated]}_predictions.jsonl`
- `logs/official_test/C4_official_test_{at,isAt}_predictions.jsonl`
- `logs/official_test/OrdContM1_official_test_at_predictions.jsonl`
- `logs/official_test/gemma4_31b_PAB_official_test_predictions.jsonl`
- `logs/official_test/llama_33_70b_PAB_official_test_predictions.jsonl`
- xlm-roberta-large + mDeBERTa-v3 official-test outputs: `runs/materials/` and
  `runs/test_outputs_mdeberta/` (configs: `*_task_*_config.json`).
