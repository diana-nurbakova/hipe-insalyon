# Stacked-model component analysis — HIPE-2026 official test

Scored against the released gold in `data/reference/` (source: https://github.com/hipe-eval/hipe-2026-eval/tree/main/data/reference).

- Official test pairs: **1118** (Test A: de+en+fr newspapers, 638 pairs scored on `at`+`isAt`; Test B: surprise-fr, 480 pairs, `at` only).
- Gold `at` distribution: {'FALSE': 629, 'PROBABLE': 145, 'TRUE': 344}
- Gold `isAt` distribution (Test A): {'FALSE': 425, 'TRUE': 213}

Primary metric is **macro recall (MR)** — the official HIPE-2026 metric (global = mean(MR_at, MR_isAt)). We also report **accuracy**, **macro precision**, **macro F1**, **weighted F1**, and **Cohen's κ** (agreement with gold beyond chance). Macro averages are over labels with gold support, so MR here equals the official macro recall.

## 1. `at` task — all components vs the final stacker (Test A)

The **4-model stacker** combines RF, C4-SDov, OrdContM1 and Gemma. **xlm-roberta-large** and **mDeBERTa-v3** are fine-tuned encoders used in the official ensemble runs (run1/run2/run3) but *not* in the lookup stacker; Llama 3.3 70B is shown for reference.

| Component | Accuracy | Macro-P | **MR** (Macro-R) | Macro-F1 | Weighted-F1 | Cohen κ |
|---|---|---|---|---|---|---|
| RF (handcrafted) | 0.5408 | 0.3741 | **0.3473** | 0.2707 | 0.4085 | 0.0352 |
| C4-SDov | 0.5658 | 0.4398 | **0.4187** | 0.4108 | 0.5264 | 0.1929 |
| OrdContM1 | 0.5235 | 0.4095 | **0.3785** | 0.3594 | 0.4827 | 0.1090 |
| xlm-roberta-large | 0.4592 | 0.3191 | **0.3416** | 0.3249 | 0.4354 | 0.0275 |
| mDeBERTa-v3 | 0.5737 | 0.3742 | **0.4208** | 0.3958 | 0.5364 | 0.2199 |
| Gemma 4 31B (PAB) | 0.7006 | 0.5228 | **0.5625** | 0.5155 | 0.6732 | 0.4977 |
| Llama 3.3 70B (PAB) | 0.6144 | 0.5114 | **0.5138** | 0.4752 | 0.5966 | 0.3701 |
| **STACKER (final)** | 0.6520 | 0.4246 | **0.4659** | 0.4349 | 0.5906 | 0.3304 |

### `at` — MR across splits + train→test shift

| Component | Test A MR | Test B MR | all-1118 MR | CV MR | shift |
|---|---|---|---|---|---|
| RF (handcrafted) | 0.3473 | 0.3776 | 0.3566 | 0.5844 | -0.2371 |
| C4-SDov | 0.4187 | 0.4049 | 0.4136 | 0.5787 | -0.16 |
| OrdContM1 | 0.3785 | 0.3801 | 0.3806 | 0.5545 | -0.176 |
| xlm-roberta-large | 0.3416 | 0.3505 | 0.3509 | n/a | n/a |
| mDeBERTa-v3 | 0.4208 | 0.4231 | 0.4253 | n/a | n/a |
| Gemma 4 31B (PAB) | 0.5625 | 0.5352 | 0.5494 | 0.5506 | 0.0119 |
| Llama 3.3 70B (PAB) | 0.5138 | 0.5110 | 0.5115 | n/a | n/a |
| **STACKER (final)** | 0.4659 | 0.4611 | — | 0.6443 | -0.1784 |

> **shift** = official-test Test-A MR − CV MR. Large negative = overfit the 1,251-instance labelled pool. CV blank where no comparable CV MR exists.

### `at` — per-class precision / recall / F1 (Test A)

| Component | TRUE P/R/F1 | PROBABLE P/R/F1 | FALSE P/R/F1 |
|---|---|---|---|
| RF (handcrafted) | 0.58/0.07/0.12 | 0.00/0.00/0.00 | 0.54/0.98/0.69 |
| C4-SDov | 0.52/0.30/0.38 | 0.18/0.11/0.13 | 0.62/0.85/0.72 |
| OrdContM1 | 0.39/0.36/0.37 | 0.25/0.02/0.04 | 0.59/0.75/0.66 |
| xlm-roberta-large | 0.36/0.41/0.38 | 0.05/0.01/0.02 | 0.55/0.60/0.57 |
| mDeBERTa-v3 | 0.47/0.50/0.48 | 0.00/0.00/0.00 | 0.65/0.77/0.70 |
| Gemma 4 31B (PAB) | 0.57/0.98/0.72 | 0.04/0.01/0.02 | 0.96/0.70/0.81 |
| Llama 3.3 70B (PAB) | 0.51/0.93/0.66 | 0.13/0.06/0.08 | 0.90/0.56/0.69 |
| STACKER (final) | 0.60/0.46/0.52 | 0.00/0.00/0.00 | 0.67/0.94/0.78 |

### Per-language MR(at) (Test A)

| Component | de | en | fr |
|---|---|---|---|
| RF (handcrafted) | 0.3288 | 0.3463 | 0.3519 |
| C4-SDov | 0.4228 | 0.3985 | 0.3916 |
| OrdContM1 | 0.3914 | 0.3664 | 0.3666 |
| xlm-roberta-large | 0.3264 | 0.3275 | 0.3063 |
| mDeBERTa-v3 | 0.3792 | 0.4514 | 0.4045 |
| Gemma 4 31B (PAB) | 0.5662 | 0.5058 | 0.5828 |
| Llama 3.3 70B (PAB) | 0.5218 | 0.4705 | 0.5235 |

## 2. `isAt` task — components (Test A)

| Component | Accuracy | Macro-P | **MR** | Macro-F1 | Weighted-F1 | Cohen κ | TRUE P/R/F1 | FALSE P/R/F1 |
|---|---|---|---|---|---|---|---|---|
| RF isAt | 0.6661 | 0.3331 | **0.5000** | 0.3998 | 0.5326 | 0.0000 | 0.00/0.00/0.00 | 0.67/1.00/0.80 |
| RF isAt (calibrated) | 0.5298 | 0.4515 | **0.4550** | 0.4522 | 0.5207 | -0.0930 | 0.26/0.23/0.25 | 0.64/0.68/0.66 |
| C4 isAt | 0.6567 | 0.5800 | **0.5468** | 0.5344 | 0.6138 | 0.1082 | 0.47/0.22/0.30 | 0.69/0.88/0.77 |
| xlm-roberta-large | 0.6034 | 0.5789 | **0.5864** | 0.5779 | 0.6124 | 0.1624 | 0.43/0.54/0.47 | 0.73/0.64/0.68 |
| mDeBERTa-v3 | 0.6646 | 0.5859 | **0.5304** | 0.4946 | 0.5920 | 0.0747 | 0.49/0.13/0.20 | 0.68/0.93/0.79 |
| Gemma isAt | 0.8339 | 0.8139 | **0.8109** | 0.8124 | 0.8335 | 0.6247 | 0.76/0.74/0.75 | 0.87/0.88/0.88 |
| Llama isAt | 0.7524 | 0.7420 | **0.7708** | 0.7419 | 0.7591 | 0.4931 | 0.59/0.83/0.69 | 0.89/0.72/0.79 |
| STACKER (Gemma isAt + constraint) | 0.7586 | 0.7800 | **0.6595** | 0.6704 | 0.7271 | 0.3703 | 0.81/0.36/0.50 | 0.75/0.96/0.84 |

## 3. Agreement among the 4 stacker `at` components

- All four agree on `at`: **28.9%** of 1118 pairs.
- Pairwise agreement:

| Pair | agreement |
|---|---|
| RF (handcrafted) vs C4-SDov | 72.7% |
| RF (handcrafted) vs OrdContM1 | 68.1% |
| RF (handcrafted) vs Gemma 4 31B (PAB) | 42.4% |
| C4-SDov vs OrdContM1 | 76.2% |
| C4-SDov vs Gemma 4 31B (PAB) | 48.2% |
| OrdContM1 vs Gemma 4 31B (PAB) | 48.3% |

## 4. Oracle upper bound on `at`

- If we always picked the *correct* one of the 4 components when any was right, plain accuracy would be **87.9%** (1118 pairs).
- Individual plain accuracy: RF=56.7%, C4-SDov=58.6%, OrdContM1=54.8%, Gemma 4 31B=67.1%.
> The gap between the oracle and the best single model bounds how much *any* stacker could have gained from these four components.

## 5. Lookup-stacker vote cells (official test)

Vote tuple order: RF (handcrafted) , C4-SDov , OrdContM1 , Gemma 4 31B (PAB) — letters = T/P/F.

| Cell (RF,C4,Ord,Gemma) | n pairs | stacker correct |
|---|---|---|
| FFFT | 321 | 122 |
| FFFF | 304 | 294 |
| FTTT | 92 | 51 |
| FFTT | 67 | 39 |
| FFTF | 52 | 51 |
| FTFT | 39 | 5 |
| TFFT | 32 | 18 |
| FTTF | 28 | 28 |
| FFFP | 25 | 23 |
| FPFT | 25 | 15 |
| TTTT | 19 | 14 |
| FPTT | 18 | 9 |

## 6. Per-test-file evaluation

### impresso-test-**de** (German)  —  n=238

- Gold `at`: {'FALSE': 146, 'PROBABLE': 38, 'TRUE': 54}  ·  Gold `isAt`: {'FALSE': 171, 'TRUE': 67}

**`at` components** — MR / Accuracy / Macro-F1 / κ, then per-class recall

| Component | MR | Acc | Macro-F1 | κ | rec TRUE | rec PROB | rec FALSE |
|---|---|---|---|---|---|---|---|
| RF (handcrafted) | 0.3288 | 0.6050 | 0.2520 | -0.0090 | 0.0000 | 0.0000 | 0.9863 |
| C4-SDov | 0.4228 | 0.5966 | 0.4252 | 0.2095 | 0.2222 | 0.2105 | 0.8356 |
| OrdContM1 | 0.3914 | 0.5294 | 0.3624 | 0.1525 | 0.4630 | 0.0263 | 0.6849 |
| xlm-roberta-large | 0.3264 | 0.4958 | 0.3117 | 0.0116 | 0.2407 | 0.0263 | 0.7123 |
| mDeBERTa-v3 | 0.3792 | 0.5546 | 0.3531 | 0.1424 | 0.3704 | 0.0000 | 0.7671 |
| Gemma 4 31B (PAB) | 0.5662 | 0.6555 | 0.4787 | 0.4365 | 1.0000 | 0.0000 | 0.6986 |
| Llama 3.3 70B (PAB) | 0.5218 | 0.5714 | 0.4449 | 0.3245 | 0.9444 | 0.0526 | 0.5685 |
| **STACKER (final)** | **0.5064** | 0.7101 | 0.4597 | 0.4205 | 0.5741 | 0.0000 | 0.9452 |

**`isAt` components** — MR / Accuracy / Macro-F1 / κ, then per-class recall

| Component | MR | Acc | Macro-F1 | κ | rec TRUE | rec FALSE |
|---|---|---|---|---|---|---|
| RF isAt | 0.5000 | 0.7185 | 0.4181 | 0.0000 | 0.0000 | 1.0000 |
| RF isAt (calibrated) | 0.5026 | 0.4874 | 0.4693 | 0.0040 | 0.5373 | 0.4678 |
| C4 isAt | 0.5350 | 0.6513 | 0.5350 | 0.0749 | 0.2687 | 0.8012 |
| xlm-roberta-large | 0.5261 | 0.5798 | 0.5200 | 0.0478 | 0.4030 | 0.6491 |
| mDeBERTa-v3 | 0.5078 | 0.7101 | 0.4539 | 0.0212 | 0.0448 | 0.9708 |
| Gemma isAt | 0.9247 | 0.9244 | 0.9097 | 0.8196 | 0.9254 | 0.9240 |
| Llama isAt | 0.8015 | 0.7605 | 0.7437 | 0.5046 | 0.8955 | 0.7076 |
| **STACKER (final)** | **0.7676** | 0.8487 | 0.7924 | 0.5887 | 0.5821 | 0.9532 |

**Submission runs** — global = mean(MR_at, MR_isAt) is the official score

| Run | MR(at) | Macro-F1(at) | MR(isAt) | Macro-F1(isAt) | **global** | global(F1) |
|---|---|---|---|---|---|---|
| 4-model-stacker | 0.5064 | 0.4597 | 0.7676 | 0.7924 | **0.6370** | 0.6260 |
| ambig-route-isAt | 0.3792 | 0.3531 | 0.6678 | 0.6881 | **0.5235** | 0.5206 |
| pure-gemma | 0.5662 | 0.4787 | 0.9247 | 0.9097 | **0.7454** | 0.6942 |
| run1 | 0.4953 | 0.4507 | 0.8497 | 0.8147 | **0.6725** | 0.6327 |
| run2 | 0.3792 | 0.3531 | 0.5078 | 0.4539 | **0.4435** | 0.4035 |
| run3 | 0.3442 | 0.3208 | 0.5261 | 0.5200 | **0.4352** | 0.4204 |
| run4 | 0.3792 | 0.3531 | 0.8497 | 0.8147 | **0.6144** | 0.5839 |
| run5 | 0.5064 | 0.4597 | 0.8497 | 0.8147 | **0.6781** | 0.6372 |
| run6 | 0.4953 | 0.4507 | 0.8497 | 0.8147 | **0.6725** | 0.6327 |

### impresso-test-**en** (English)  —  n=162

- Gold `at`: {'TRUE': 75, 'FALSE': 59, 'PROBABLE': 28}  ·  Gold `isAt`: {'FALSE': 97, 'TRUE': 65}

**`at` components** — MR / Accuracy / Macro-F1 / κ, then per-class recall

| Component | MR | Acc | Macro-F1 | κ | rec TRUE | rec PROB | rec FALSE |
|---|---|---|---|---|---|---|---|
| RF (handcrafted) | 0.3463 | 0.3889 | 0.2367 | 0.0276 | 0.1067 | 0.0000 | 0.9322 |
| C4-SDov | 0.3985 | 0.4815 | 0.3633 | 0.1556 | 0.4667 | 0.0000 | 0.7288 |
| OrdContM1 | 0.3664 | 0.4383 | 0.3401 | 0.0614 | 0.4533 | 0.0357 | 0.6102 |
| xlm-roberta-large | 0.3275 | 0.4198 | 0.3026 | 0.0142 | 0.6267 | 0.0000 | 0.3559 |
| mDeBERTa-v3 | 0.4514 | 0.5617 | 0.4140 | 0.2540 | 0.6933 | 0.0000 | 0.6610 |
| Gemma 4 31B (PAB) | 0.5058 | 0.6420 | 0.4788 | 0.3723 | 0.9733 | 0.0357 | 0.5085 |
| Llama 3.3 70B (PAB) | 0.4705 | 0.5926 | 0.4497 | 0.2773 | 0.9333 | 0.0714 | 0.4068 |
| **STACKER (final)** | **0.4490** | 0.5432 | 0.3973 | 0.2384 | 0.5333 | 0.0000 | 0.8136 |

**`isAt` components** — MR / Accuracy / Macro-F1 / κ, then per-class recall

| Component | MR | Acc | Macro-F1 | κ | rec TRUE | rec FALSE |
|---|---|---|---|---|---|---|
| RF isAt | 0.5000 | 0.5988 | 0.3745 | 0.0000 | 0.0000 | 1.0000 |
| RF isAt (calibrated) | 0.4743 | 0.5679 | 0.3622 | -0.0608 | 0.0000 | 0.9485 |
| C4 isAt | 0.5049 | 0.5802 | 0.4536 | 0.0110 | 0.1231 | 0.8866 |
| xlm-roberta-large | 0.6141 | 0.5926 | 0.5926 | 0.2121 | 0.7231 | 0.5052 |
| mDeBERTa-v3 | 0.5741 | 0.6420 | 0.5475 | 0.1660 | 0.2308 | 0.9175 |
| Gemma isAt | 0.7407 | 0.7654 | 0.7468 | 0.4965 | 0.6154 | 0.8660 |
| Llama isAt | 0.7147 | 0.7160 | 0.7097 | 0.4208 | 0.7077 | 0.7216 |
| **STACKER (final)** | **0.6331** | 0.6914 | 0.6253 | 0.2931 | 0.3385 | 0.9278 |

**Submission runs** — global = mean(MR_at, MR_isAt) is the official score

| Run | MR(at) | Macro-F1(at) | MR(isAt) | Macro-F1(isAt) | **global** | global(F1) |
|---|---|---|---|---|---|---|
| 4-model-stacker | 0.4490 | 0.3973 | 0.6331 | 0.6253 | **0.5411** | 0.5113 |
| ambig-route-isAt | 0.4514 | 0.4140 | 0.6742 | 0.6764 | **0.5628** | 0.5452 |
| pure-gemma | 0.5058 | 0.4788 | 0.7407 | 0.7468 | **0.6233** | 0.6128 |
| run1 | 0.4745 | 0.4406 | 0.7225 | 0.7231 | **0.5985** | 0.5818 |
| run2 | 0.4514 | 0.4140 | 0.5741 | 0.5475 | **0.5128** | 0.4808 |
| run3 | 0.4074 | 0.3662 | 0.6141 | 0.5926 | **0.5108** | 0.4794 |
| run4 | 0.4514 | 0.4140 | 0.7225 | 0.7231 | **0.5870** | 0.5685 |
| run5 | 0.4490 | 0.3973 | 0.7225 | 0.7231 | **0.5857** | 0.5602 |
| run6 | 0.4745 | 0.4406 | 0.7225 | 0.7231 | **0.5985** | 0.5818 |

### impresso-test-**fr** (French)  —  n=238

- Gold `at`: {'FALSE': 134, 'TRUE': 85, 'PROBABLE': 19}  ·  Gold `isAt`: {'FALSE': 157, 'TRUE': 81}

**`at` components** — MR / Accuracy / Macro-F1 / κ, then per-class recall

| Component | MR | Acc | Macro-F1 | κ | rec TRUE | rec PROB | rec FALSE |
|---|---|---|---|---|---|---|---|
| RF (handcrafted) | 0.3519 | 0.5798 | 0.2850 | 0.0553 | 0.0706 | 0.0000 | 0.9851 |
| C4-SDov | 0.3916 | 0.5924 | 0.3742 | 0.1637 | 0.2118 | 0.0526 | 0.9104 |
| OrdContM1 | 0.3666 | 0.5756 | 0.3355 | 0.0901 | 0.2118 | 0.0000 | 0.8881 |
| xlm-roberta-large | 0.3063 | 0.4496 | 0.2936 | -0.0638 | 0.3294 | 0.0000 | 0.5896 |
| mDeBERTa-v3 | 0.4045 | 0.6008 | 0.3872 | 0.1949 | 0.4000 | 0.0000 | 0.8134 |
| Gemma 4 31B (PAB) | 0.5828 | 0.7857 | 0.5484 | 0.6127 | 0.9647 | 0.0000 | 0.7836 |
| Llama 3.3 70B (PAB) | 0.5235 | 0.6723 | 0.4986 | 0.4362 | 0.9059 | 0.0526 | 0.6119 |
| **STACKER (final)** | **0.4357** | 0.6681 | 0.4158 | 0.2870 | 0.3294 | 0.0000 | 0.9776 |

**`isAt` components** — MR / Accuracy / Macro-F1 / κ, then per-class recall

| Component | MR | Acc | Macro-F1 | κ | rec TRUE | rec FALSE |
|---|---|---|---|---|---|---|
| RF isAt | 0.5000 | 0.6597 | 0.3975 | 0.0000 | 0.0000 | 1.0000 |
| RF isAt (calibrated) | 0.4528 | 0.5462 | 0.4391 | -0.1029 | 0.1605 | 0.7452 |
| C4 isAt | 0.6012 | 0.7143 | 0.5928 | 0.2413 | 0.2469 | 0.9554 |
| xlm-roberta-large | 0.6004 | 0.6345 | 0.5987 | 0.1979 | 0.4938 | 0.7070 |
| mDeBERTa-v3 | 0.5078 | 0.6345 | 0.4684 | 0.0188 | 0.1111 | 0.9045 |
| Gemma isAt | 0.7661 | 0.7899 | 0.7661 | 0.5321 | 0.6914 | 0.8408 |
| Llama isAt | 0.7919 | 0.7689 | 0.7611 | 0.5315 | 0.8642 | 0.7197 |
| **STACKER (final)** | **0.5892** | 0.7143 | 0.5696 | 0.2190 | 0.1975 | 0.9809 |

**Submission runs** — global = mean(MR_at, MR_isAt) is the official score

| Run | MR(at) | Macro-F1(at) | MR(isAt) | Macro-F1(isAt) | **global** | global(F1) |
|---|---|---|---|---|---|---|
| 4-model-stacker | 0.4357 | 0.4158 | 0.5892 | 0.5696 | **0.5124** | 0.4927 |
| ambig-route-isAt | 0.4045 | 0.3872 | 0.6593 | 0.6691 | **0.5319** | 0.5282 |
| pure-gemma | 0.5828 | 0.5484 | 0.7661 | 0.7661 | **0.6744** | 0.6573 |
| run1 | 0.4772 | 0.4618 | 0.8146 | 0.7954 | **0.6459** | 0.6286 |
| run2 | 0.4045 | 0.3872 | 0.5078 | 0.4684 | **0.4562** | 0.4278 |
| run3 | 0.3463 | 0.3143 | 0.6004 | 0.5987 | **0.4734** | 0.4565 |
| run4 | 0.4045 | 0.3872 | 0.8146 | 0.7954 | **0.6096** | 0.5913 |
| run5 | 0.4357 | 0.4158 | 0.8146 | 0.7954 | **0.6251** | 0.6056 |
| run6 | 0.4772 | 0.4618 | 0.8146 | 0.7954 | **0.6459** | 0.6286 |

### **surprise**-test-fr (French literary, Test B — `at` only)  —  n=480

- Gold `at`: {'TRUE': 130, 'FALSE': 290, 'PROBABLE': 60}

**`at` components** — MR / Accuracy / Macro-F1 / κ, then per-class recall

| Component | MR | Acc | Macro-F1 | κ | rec TRUE | rec PROB | rec FALSE |
|---|---|---|---|---|---|---|---|
| RF (handcrafted) | 0.3776 | 0.6021 | 0.3591 | 0.1284 | 0.2231 | 0.0167 | 0.8931 |
| C4-SDov | 0.4049 | 0.6125 | 0.3959 | 0.1742 | 0.2923 | 0.0500 | 0.8724 |
| OrdContM1 | 0.3801 | 0.5813 | 0.3558 | 0.1158 | 0.3231 | 0.0000 | 0.8172 |
| xlm-roberta-large | 0.3505 | 0.5583 | 0.3248 | 0.0449 | 0.2308 | 0.0000 | 0.8207 |
| mDeBERTa-v3 | 0.4231 | 0.6438 | 0.4014 | 0.2256 | 0.3692 | 0.0000 | 0.9000 |
| Gemma 4 31B (PAB) | 0.5352 | 0.6312 | 0.4632 | 0.3982 | 0.9923 | 0.0167 | 0.5966 |
| Llama 3.3 70B (PAB) | 0.5110 | 0.5792 | 0.4445 | 0.3309 | 0.9692 | 0.0500 | 0.5138 |
| **STACKER (final)** | **0.4611** | 0.6687 | 0.4441 | 0.3185 | 0.4769 | 0.0167 | 0.8897 |

**Submission runs** — global = mean(MR_at, MR_isAt) is the official score

| Run | MR(at) | Acc(at) | Macro-F1(at) |
|---|---|---|---|
| 4-model-stacker | 0.4611 | 0.6687 | 0.4441 |
| ambig-route-isAt | 0.4231 | 0.6438 | 0.4014 |
| pure-gemma | 0.5352 | 0.6312 | 0.4632 |
| run1 | 0.4705 | 0.6604 | 0.4437 |
| run2 | 0.4231 | 0.6438 | 0.4014 |
| run3 | 0.3986 | 0.6375 | 0.3786 |
| run4 | 0.4231 | 0.6438 | 0.4014 |
| run5 | 0.4611 | 0.6687 | 0.4441 |
| run6 | 0.4705 | 0.6604 | 0.4437 |

## 7. Takeaways

1. **Gemma 4 31B is the best single component on both tasks and on every metric** — `at` MR 0.5625 / Macro-F1 0.5155 / κ 0.4977, and `isAt` MR 0.8109 / κ 0.6247. It is also the only `at` model whose official-test score tracks its CV estimate (shift +0.01), because it is zero-shot and never saw our labelled pool.
2. **The conclusion is metric-robust.** MR, Macro-F1 and Cohen's κ all rank the models identically (Gemma > Llama > mDeBERTa ≈ C4 > OrdContM1 > RF ≈ xlm on `at`), so the result is not an artifact of balanced accuracy. Accuracy alone is misleading — e.g. RF `isAt` scores 0.67 accuracy but κ = 0.00 (it predicts all-FALSE); the macro metrics expose that.
3. **Every trained model overfit and collapsed out-of-distribution.** RF/C4/OrdContM1 lost 0.16–0.24 MR vs CV (`shift` column); the two fine-tuned encoders are no better — xlm-roberta-large is the *worst* `at` model on the test (MR 0.3416, κ 0.0275), despite being a 560M-param model and a voter in official run1/run3. Cohen's κ for RF (`at` 0.0352) and the trained `isAt` heads (≤0.16) confirms near-chance agreement.
4. **PROBABLE is effectively unlearnable here.** Per-class F1 for PROBABLE is 0.00 for RF, mDeBERTa and the stacker, and only ~0.02 for Gemma — the entire field fails the third `at` class on the official test, which caps MR(at) for everyone.
5. **Stacking and voting hurt.** The 4-model stacker `at` (MR 0.4659) lands below Gemma alone, and the majority-vote `isAt` used in run1/4/5/6 (0.7991) is below Gemma `isAt` alone (0.8109). Mixing the robust LLM with the collapsed trained models consistently loses ground — **pure Gemma would have been our strongest submission** (Test A global 0.6867 vs run1's 0.6472).
6. **The components are complementary in principle but not exploitable in practice.** The oracle upper bound on `at` is 87.9% accuracy vs 67.1% for the best single model — the headroom exists, but the lookup table cannot realise it because the trained voters are unreliable OOD (see the `FFFT` cell: Gemma says TRUE, the trees overrule it, and the stacker is right only 122/321 times).

### Practical implications for the notebook paper

- Report **pure Gemma 4 31B** as the headline system; present the stacker as a negative result on small labelled pools (severe train→test shift).
- The frugal, no-LLM runs (run2/run3) are the weakest by a wide margin — useful only as an efficiency baseline, not for accuracy.
- A larger or more representative training pool, or calibration against the official distribution, would be needed before any trained component could help an ensemble.
