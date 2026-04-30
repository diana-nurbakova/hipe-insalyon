# HIPE-2026 — MASK experiments on Google Colab

This document is a **Colab notebook in markdown form** — every fenced code block is meant to be pasted into its own cell. The cells are written so you can either run them top-to-bottom on a fresh runtime or jump in and out as needed (every step is idempotent and skips work that's already on disk).

> **Why markdown not .ipynb?** Real notebooks frequently corrupt under git, render badly in GitHub, and lose Colab-specific cell metadata. Copy-pasting from this doc into a fresh Colab tab is more reliable.

**Recommended runtime:** T4 GPU (free tier is fine). A100 is faster but not necessary; everything below is GPU-aware and will fall back to CPU when needed.

**Total wall-clock budget on T4** with `--templates M1 M2 M3 M4 M5 --layers -1 -4 -7`:

| Step | T4 time |
| --- | --- |
| Setup + clone | ~2 min |
| Phase 0 (M2 baseline) | ~10 min |
| Phase 1a (5 templates × hmBERT) | ~50 min |
| Phase 1b (encoder sweep, M2 × {XLM-R-base, mGTE}) | ~50 min |
| Phase 2 (spectral features) | <1 min × N caches |
| Phase 3 (eval grid) | ~3 min |
| Phase 4 (contrastive training) | ~2 min × variant |

The first run of Phase 1+2 fills `runs/` with `.npz` caches; subsequent runs reuse them.

---

## Cell 1 — Sanity check the runtime

Confirms a GPU is attached. Switch the runtime via **Runtime → Change runtime type → T4 GPU** if it isn't.

```python
!nvidia-smi -L 2>/dev/null || echo "No NVIDIA GPU visible — switch runtime type."
import sys
print("Python:", sys.version)
```

---

## Cell 2 — (Optional) Mount Google Drive

Use this if you want extracted `.npz` caches and `logs/ablations/` to persist across Colab sessions. **Skip this cell** if you'd rather keep everything in the ephemeral runtime and download artefacts at the end.

```python
from google.colab import drive
drive.mount('/content/drive')

import os
DRIVE_BASE = '/content/drive/MyDrive/HIPE2026'
os.makedirs(DRIVE_BASE, exist_ok=True)
print('Drive base:', DRIVE_BASE)
```

---

## Cell 3 — Get the repo

Pick **one** of the two paths below.

**Path A — clone from GitHub** (works if you've pushed your branch). Replace the URL with your fork. For a private repo, use a fine-grained PAT:

```bash
%cd /content
!rm -rf HIPE
# Public repo:
# !git clone --depth 1 https://github.com/YOUR-USER/HIPE.git
# Private repo (HTTPS + token):
!git clone --depth 1 https://USERNAME:GITHUB_TOKEN@github.com/YOUR-USER/HIPE.git HIPE
%cd /content/HIPE
!git rev-parse --short HEAD
```

**Path B — upload a zip** (works without GitHub access). Locally run `Compress-Archive -Path C:\Users\dnurb\Documents\MilitIA\HIPE\* -DestinationPath HIPE.zip`, drop the file into Colab's file panel, then:

```bash
%cd /content
!rm -rf HIPE
!unzip -q HIPE.zip -d HIPE
%cd /content/HIPE
!ls
```

---

## Cell 4 — Install dependencies

The project ships an `ml` extra that pins torch / transformers / sklearn / faiss / numpy. Add `viz` for matplotlib + UMAP (used by Phase-0 diagnostics) and `dev` for pytest.

```bash
!pip install -q --upgrade pip
!pip install -q -e ".[ml,viz,dev]"
# UMAP-learn pulls numba; this can take a minute on a fresh runtime.
```

Verify the install:

```python
import torch, transformers, sklearn, scipy, umap
print('torch       :', torch.__version__, '  CUDA:', torch.cuda.is_available())
print('transformers:', transformers.__version__)
print('scikit-learn:', sklearn.__version__)
print('scipy       :', scipy.__version__)
print('umap        :', umap.__version__)
```

---

## Cell 5 — Load secrets from Colab's secret store (replaces `.env`)

Locally the project reads API keys via `python-dotenv` from `.env`. **Never** copy `.env` into Colab — its history is shared and the file ends up in the runtime, in the GitHub-zip Path B uses, and (if Drive is mounted) potentially in your Drive. Instead use Colab's per-user secret store.

**Set the secrets once** (this is a one-time UI action, not a code cell):

1. Click the key icon in Colab's left sidebar (under the file panel) — _Secrets_ pane.
2. **Add new secret** for each variable in your local `.env`:
   - `HF_TOKEN` — required for downloading some gated HuggingFace models (not needed for hmBERT / XLM-R / mGTE used in Phase 1, but harmless to set).
   - `OPENAI_API_KEY` — only for OpenAI-backed LLM runs (not used in this MASK notebook).
   - `DEEPINFRA_API_KEY` — only for DeepInfra Llama runs (not used here either).
   - `ANTHROPIC_API_KEY`, `OPENROUTER_API_KEY`, `OLLAMA_API_KEY`, `OLLAMA_BASE_URL` — only if you also run LLM experiments.
3. For each secret, **toggle "Notebook access"** so the current notebook can read it. Toggle is per-notebook — if you reopen this doc in a new tab, you'll need to re-grant access.

Now read them into the runtime environment so everything downstream (HuggingFace `transformers.from_pretrained`, the project's `LLMClient`, etc.) finds them as if they came from `.env`:

```python
import os
from google.colab import userdata

# Map: Colab-secret-name -> environment-variable-name. Identity mapping by default.
SECRET_KEYS = [
    'HF_TOKEN',
    'OPENAI_API_KEY',
    'DEEPINFRA_API_KEY',
    'ANTHROPIC_API_KEY',
    'OPENROUTER_API_KEY',
    'OLLAMA_API_KEY',
    'OLLAMA_BASE_URL',
]

loaded, missing = [], []
for name in SECRET_KEYS:
    try:
        val = userdata.get(name)
    except userdata.SecretNotFoundError:
        missing.append(name); continue
    except userdata.NotebookAccessError:
        missing.append(f'{name} (no notebook access)'); continue
    if val:
        os.environ[name] = val
        loaded.append(name)
    else:
        missing.append(name)

print('Loaded :', loaded)
print('Missing:', missing)

# HuggingFace-specific aliases (the various HF libraries each look at a slightly
# different variable; setting all three keeps `from_pretrained` happy for gated
# models and avoids the interactive `huggingface-cli login` prompt).
if 'HF_TOKEN' in os.environ:
    os.environ.setdefault('HUGGINGFACE_HUB_TOKEN', os.environ['HF_TOKEN'])
    os.environ.setdefault('HUGGING_FACE_HUB_TOKEN', os.environ['HF_TOKEN'])
```

For the MASK experiments below, **only `HF_TOKEN` is genuinely needed**, and only if you point Cell 10 at a gated encoder. Missing LLM keys are fine — they'll just block the LLM scripts in `scripts/run_llm_baseline.py` (out of scope here).

Verify HuggingFace recognises the token (optional):

```python
from huggingface_hub import whoami
try:
    print(whoami())
except Exception as e:
    print('No HF token recognised:', e)
```

---

## Cell 6 — Wire up cache paths (and run the unit tests)

If you mounted Drive in Cell 2, point `runs/` and `logs/` at Drive so the artefacts persist:

```python
import os, pathlib

PROJECT = pathlib.Path('/content/HIPE')
USE_DRIVE = pathlib.Path('/content/drive/MyDrive').exists()
if USE_DRIVE:
    DRIVE_BASE = '/content/drive/MyDrive/HIPE2026'
    for sub in ('runs', 'logs/ablations', 'logs/final'):
        os.makedirs(f'{DRIVE_BASE}/{sub}', exist_ok=True)
        target = PROJECT / sub
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            os.symlink(f'{DRIVE_BASE}/{sub}', target)
            print(f'symlink {target} -> {DRIVE_BASE}/{sub}')
        else:
            print(f'exists  {target}')
else:
    print('Drive not mounted — using ephemeral runtime storage.')
```

Run the test suite (catches install-related issues before any GPU work):

```bash
!pytest -x -q
```

You should see **71 passed** in ~10 s.

---

## Cell 7 — Verify the dataset

The repo ships `data/dataset_reference.jsonl` (1,251 instances) and the official baseline split CSV. If those files aren't present (e.g. the zip you uploaded was filtered), upload them now.

```python
import pathlib

required = [
    'data/dataset_reference.jsonl',
    'data/v1_baseline_train_test_ids.csv',
]
for rel in required:
    p = pathlib.Path('/content/HIPE') / rel
    print(f"{'OK ' if p.exists() else 'MISSING'}  {rel}  "
          f"({p.stat().st_size/1e6:.1f} MB)" if p.exists() else f"MISSING  {rel}")
```

If any line says **MISSING**, copy the file in via the Colab file panel, then re-run.

---

## Cell 8 — Phase 0: M2 baseline + diagnostics

This reproduces the existing baseline (matches the on-disk artefact in `runs/mask_dbmdz_..._M2.npz`). On a T4 expect ~10 minutes including the model download.

```bash
!python scripts/extract_mask_embeddings.py \
    --template M2 --field context \
    --max-seq-length 256 --batch-size 32
```

PCA / UMAP / silhouette + go-no-go gate (Spec §0):

```bash
!python scripts/phase0_mask_diagnostics.py \
    --npz runs/mask_dbmdz_bert_base_historic_multilingual_cased_M2.npz \
    --skip-umap   # drop this flag if you want the UMAP plots (~2 min)
```

Inspect the gate decision:

```python
import json, pathlib
res = json.loads(pathlib.Path('runs/phase0_mask_diag/results.json').read_text())
print(json.dumps(res['gate'], indent=2))
```

---

## Cell 9 — Phase 1a: extract all five templates on hmBERT (multi-layer)

Recommended setup from the spec: `layers=(-1, -4, -7)` (≈ layers 12 / 9 / 6 of hmBERT). The grid runner re-uses any `.npz` already on disk, so re-running this cell after a partial failure is cheap.

```bash
!python scripts/run_mask_template_encoder_grid.py \
    --templates M1 M2 M3 M4 M5 \
    --encoders dbmdz/bert-base-historic-multilingual-cased \
    --layers -1 -4 -7 \
    --max-seq-length 256 --batch-size 32
```

Inspect the resulting cache index:

```bash
!ls -la runs/mask_*.npz
```

---

## Cell 10 — Phase 1b: encoder comparison on M2

The two extra encoders test different hypotheses. **Skip whichever you don't have time for** — neither blocks downstream cells.

```bash
# XLM-R-base (multilingual baseline; ~12 min on T4)
!python scripts/run_mask_template_encoder_grid.py \
    --templates M2 \
    --encoders xlm-roberta-base \
    --layers -1 -4 -7 \
    --max-seq-length 256 --batch-size 32

# mGTE (long-context; ~15 min on T4) — context fits the full 8k window so
# we deliberately use a longer max-seq-length here.
!python scripts/run_mask_template_encoder_grid.py \
    --templates M2 \
    --encoders Alibaba-NLP/gte-multilingual-base \
    --layers -1 -4 -7 \
    --max-seq-length 512 --batch-size 16

# XLM-R-large (heavier; ~25 min on T4, may OOM at batch_size=16 — drop to 8)
!python scripts/run_mask_template_encoder_grid.py \
    --templates M2 \
    --encoders xlm-roberta-large \
    --layers -1 -4 -7 \
    --max-seq-length 256 --batch-size 8
```

Free GPU memory between encoders if you ran them in one cell:

```python
import gc, torch
gc.collect(); torch.cuda.empty_cache()
```

---

## Cell 11 — Phase 2: spectral features

For each cache, build a Laplacian eigenmap on the **same set of instances** (transductive — appropriate when train + test share a single closed pool). The augmented file is written next to the original with a `_spec<k>` suffix; `mask_grid_eval.py` picks them up automatically.

```bash
!for f in runs/mask_*.npz; do \
    [[ "$f" == *_spec* ]] && continue; \
    echo "==> $f"; \
    python scripts/extract_spectral_features.py \
        --npz "$f" \
        --base mask_emb_layers \
        --n-components 10 \
        --n-neighbors 20; \
done
```

Sanity check NMI (eigenvector vs label) for one cache:

```python
import numpy as np, json
z = np.load('runs/mask_dbmdz_bert_base_historic_multilingual_cased_M2_L_1__4__7_spec10.npz',
            allow_pickle=True)
meta = json.loads(z['_meta_spectral'].item())
print('eigenvalues :', np.round(meta['eigenvalues'], 4))
print('NMI(at)     :', np.round(meta['nmi_at'], 3))
print('NMI(isAt)   :', np.round(meta['nmi_isAt'], 3))
```

A high NMI on any of the leading eigenvectors means the spectral features are likely useful as classifier inputs.

---

## Cell 12 — Phase 3: score every cache against the official metric

This is the workhorse cell. It loads every `runs/mask_*.npz`, trains LR / RF on the at-task train slice, predicts on the at-task test slice, and writes `_predictions.jsonl` + `_report.json` per cell into `logs/ablations/`. Same format as the LLM runs, so the cross-config disagreement matrix and final report pick them up automatically.

```bash
!python scripts/mask_grid_eval.py \
    --task at \
    --feature-sets mask mask_layers concat_t concat_l_t \
                   mask_at mask_isAt mask_multi \
    --include-spectral \
    --include-handcrafted
```

The script prints a top-15 leaderboard at the end, e.g.:

```text
==============================================================================
Top 15 cells by GlobalScore (task=at)
==============================================================================
experiment_id                                                global   MR(at)  MR(isAt)
T1.4or5_mask_grid_mask_dbmdz..._M2_L_1__4__7_concat_l_t_at  0.5950  0.6321  0.5579
T1.4or5_mask_grid_mask_xlm_roberta_base_M2_concat_t_at     0.5810  0.6024  0.5596
...
```

Open the aggregate JSON for the full table:

```python
import json, pandas as pd
rows = json.loads(open('runs/mask_grid_eval/summary.json').read())['rows']
df = pd.DataFrame(rows).sort_values('global_score', ascending=False)
df[['experiment_id', 'feature_set', 'target', 'input_dim',
    'global_score', 'macro_recall_at', 'macro_recall_isAt']].head(20)
```

---

## Cell 13 — Phase 4: contrastive training (MLP + ordinal/SupCon)

Pick the strongest cache from Cell 12 (typically the multi-layer hmBERT one) and train the joint head:

```bash
!python scripts/train_mask_contrastive.py \
    --npz runs/mask_dbmdz_bert_base_historic_multilingual_cased_M2_L_1__4__7.npz \
    --feature-set concat_l_t \
    --epochs 25 \
    --alpha 0.7 \
    --contrastive-at ordinal \
    --contrastive-isAt supcon \
    --val-fraction 0.1 \
    --patience 6
```

Useful ablations (all idempotent, ~2 min each):

```bash
# CE-only baseline (no contrastive contribution)
!python scripts/train_mask_contrastive.py \
    --npz runs/mask_dbmdz_bert_base_historic_multilingual_cased_M2_L_1__4__7.npz \
    --feature-set concat_l_t \
    --alpha 1.0 --contrastive-at none --contrastive-isAt none \
    --experiment-id T1.4or5_mask_contrastive_CEonly_at-test

# SupCon-only on at (vs ordinal)
!python scripts/train_mask_contrastive.py \
    --npz runs/mask_dbmdz_bert_base_historic_multilingual_cased_M2_L_1__4__7.npz \
    --feature-set concat_l_t \
    --contrastive-at supcon --contrastive-isAt supcon \
    --experiment-id T1.4or5_mask_contrastive_supcon_at-test

# Aggressive ordinal margin
!python scripts/train_mask_contrastive.py \
    --npz runs/mask_dbmdz_bert_base_historic_multilingual_cased_M2_L_1__4__7.npz \
    --feature-set concat_l_t \
    --contrastive-at ordinal --base-margin 1.0 \
    --experiment-id T1.4or5_mask_contrastive_ordinal_m1_at-test
```

---

## Cell 14 — Refresh the cross-config disagreement matrix + report

After every batch of new runs, re-aggregate so the comparison tables and disagreement matrix include the MASK cells:

```bash
!python scripts/aggregate_results.py
!python scripts/disagreement_analysis.py
!python scripts/generate_report.py
```

Inspect the headline numbers:

```python
import json
results = json.loads(open('logs/final/results.json').read())
print(f"Total experiments scored: {results['n_experiments']}")
print('\nTop-12 by GlobalScore:')
for r in results['ranking_by_global_score'][:12]:
    eid = r['experiment_id']
    gs = r['global_score']
    print(f"  {eid:75s} {gs:.4f}")
```

Open the new evaluation report:

```python
from IPython.display import Markdown
print(open('logs/final/evaluation_report.md').read()[:4000])  # head only
```

---

## Cell 15 — Bundle artefacts for download

Compress and download what you need. With Drive mounted, the caches are already persisted; this just packages the things small enough to ship over a browser.

```bash
!tar czf /content/hipe_mask_artefacts.tar.gz \
    logs/ablations \
    logs/final \
    runs/mask_grid_eval \
    runs/phase0_mask_diag

!ls -la /content/hipe_mask_artefacts.tar.gz
```

```python
from google.colab import files
files.download('/content/hipe_mask_artefacts.tar.gz')
```

If you also want the raw `.npz` caches (~25 MB each), bundle them separately:

```bash
!tar czf /content/hipe_mask_caches.tar.gz runs/mask_*.npz
!ls -la /content/hipe_mask_caches.tar.gz
```

---

## Troubleshooting

**"CUDA out of memory" while extracting on XLM-R-large**
Drop `--batch-size 8 → 4` and `--max-seq-length 256 → 192`. The encoder grid runner empties the CUDA cache between cells, so a single-encoder failure won't poison subsequent cells.

**Drive symlink errors after a runtime reset**
Re-run Cell 6 — the symlinks are recreated idempotently.

**`scripts/extract_spectral_features.py` runs forever on a large cache**
That script is CPU-only and uses sklearn k-NN; on the multi-layer concat (≈ 2304-d) the graph build can take a minute. Reduce `--n-neighbors` if it's a problem, or pass `--base mask_emb` to use the smaller 768-d projection.

**Test failures related to torch / transformers**
The pinned versions in `pyproject.toml` work cleanly with Colab's CUDA 12.x runtime. If torch fails to import, run `!pip install torch --upgrade --index-url https://download.pytorch.org/whl/cu121` and re-run Cell 4.

**A cell aborts mid-extraction**
The grid runner skips caches that already exist on disk, so just re-run the same cell. To force a re-extraction, add `--force`.

---

## Mapping back to the spec

| Spec section | Notebook cell | Output |
| --- | --- | --- |
| MASK Spec §3 (templates M1–M5) | Cell 9 | `runs/mask_*_M{1..5}*.npz` |
| MASK Spec §2 (encoders) | Cell 10 | `runs/mask_xlm_roberta*.npz`, `runs/mask_*gte*.npz` |
| MASK Spec §4.2, §8.7 (multi-layer) | Cell 9 (`--layers -1 -4 -7`) | `mask_emb_layers` array in cache |
| Prompting & MASK Spec §8.6.4 (spectral) | Cell 11 | `runs/mask_*_spec10.npz` |
| Prompting & MASK Spec §9 (contrastive) | Cell 13 | `logs/ablations/T1.4or5_mask_contrastive_*` |
| MASK Spec §6 (classifiers C1–C8) | Cell 12 (LR) + Cell 13 (MLP) | `logs/ablations/T1.4or5_mask_grid_*` + `T1.4or5_mask_contrastive_*` |
| Phase 0 go/no-go (Spec §7.1) | Cell 8 | `runs/phase0_mask_diag/results.json` |

Every produced row also feeds into `scripts/disagreement_analysis.py` (Cell 14) so the new MASK runs join the existing cross-config matrix without further wiring.
