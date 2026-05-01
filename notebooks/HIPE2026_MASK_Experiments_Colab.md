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

> ⚠️ **Always mount Drive (Cell 2).** Colab disconnects free-tier runtimes without warning, and Phase 1 takes the better part of an hour. Cell 6 below symlinks both `runs/` and `logs/` into Drive so every cache, prediction file, and report survives a disconnect — pick up the next session by re-running Cells 1–6 and skipping straight to whichever phase you stopped at.

---

## Cell 1 — Sanity check the runtime

Confirms a GPU is attached. Switch the runtime via **Runtime → Change runtime type → T4 GPU** if it isn't.

```python
!nvidia-smi -L 2>/dev/null || echo "No NVIDIA GPU visible — switch runtime type."
import sys
print("Python:", sys.version)
```

---

## Cell 2 — Mount Google Drive (required)

This notebook **requires Drive** — Cell 6 below replaces the repo's `runs/` and `logs/` with symlinks into `MyDrive/HIPE2026_workdir/`, so every embedding cache, prediction file, and evaluation report is written straight to Drive. If the runtime disconnects mid-extraction, your work is safe; just reconnect and re-run Cells 1–6.

```python
from google.colab import drive
drive.mount('/content/drive')

import os, pathlib

# Single shared workdir for everything this notebook produces. Pick a fresh
# subfolder name if you want to keep multiple experiment generations separate
# (e.g. HIPE2026_workdir_v2). Re-using the same folder lets the grid runner
# skip caches it has already extracted.
DRIVE_BASE = pathlib.Path('/content/drive/MyDrive/HIPE2026_workdir')
DRIVE_BASE.mkdir(parents=True, exist_ok=True)
(DRIVE_BASE / 'runs').mkdir(exist_ok=True)
(DRIVE_BASE / 'logs').mkdir(exist_ok=True)
print('Drive workdir:', DRIVE_BASE)
print('  runs/  ->', list((DRIVE_BASE / 'runs').iterdir())[:5] or '(empty)')
print('  logs/  ->', list((DRIVE_BASE / 'logs').iterdir())[:5] or '(empty)')
```

If you genuinely want an ephemeral run (e.g. a quick smoke test), comment out the `drive.mount` line and change `DRIVE_BASE` to `/content/HIPE2026_workdir`. Cell 6 doesn't care whether the target is on Drive or local disk — it just symlinks.

---

## Cell 3 — Get the repo

Pick **one** of the two paths below.

**Path A — clone from GitHub** (works if you've pushed your branch).

For a public repo, no token is needed. For a private repo, **add a fine-grained PAT to Colab secrets first** (Sidebar key icon → Secrets → **New** → name it `GITHUB_TOKEN`, paste the token, **toggle Notebook access**). The token never appears in cell output or shell history; only the cloned `.git/config` ends up with it embedded, and we strip that immediately after cloning.

```python
import os, subprocess
from google.colab import userdata

REPO = 'YOUR-USER/HIPE'   # ← edit this: 'org-or-user/repo-name'
WORKDIR = '/content/HIPE'

# Pull the token from Colab secrets. Skip this block for a public repo and
# replace `clone_url` below with the plain HTTPS URL.
try:
    GH_TOKEN = userdata.get('GITHUB_TOKEN')
except Exception as e:
    raise SystemExit(
        f"Couldn't read GITHUB_TOKEN from Colab secrets ({e}). "
        "Add it via the Secrets pane (key icon in the sidebar) and toggle "
        "'Notebook access', or use Path B (zip upload) below."
    )

# Fine-grained PATs accept any username; 'oauth2' is the convention.
clone_url = f'https://oauth2:{GH_TOKEN}@github.com/{REPO}.git'

if os.path.exists(WORKDIR):
    subprocess.check_call(['rm', '-rf', WORKDIR])
subprocess.check_call(['git', 'clone', '--depth', '1', clone_url, WORKDIR])

# Scrub the token out of .git/config so it isn't accidentally read by
# subsequent !git commands (or echoed if the dir is later inspected).
subprocess.check_call(
    ['git', '-C', WORKDIR, 'remote', 'set-url', 'origin',
     f'https://github.com/{REPO}.git']
)

os.chdir(WORKDIR)
print('HEAD:', subprocess.check_output(
    ['git', 'rev-parse', '--short', 'HEAD']).decode().strip())
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

**For the MASK notebook, none of the keys in your local `.env` are strictly required.** The cells below run on public HuggingFace encoders (hmBERT, XLM-R, mGTE) and never make an LLM API call. `HF_TOKEN` is *optional* — useful only to lift HuggingFace's anonymous download rate limits on a freshly-created runtime, or to fetch a gated/private encoder if you point Cell 10 at one.

If you'll later run LLM-based notebooks (P-A / P-B / P-R / agentic pipeline), add the relevant provider keys then; this cell already knows how to load them.

Locally the project reads API keys via `python-dotenv` from `.env`. **Never** copy `.env` itself into Colab — Colab session state and Drive are not the right place for API keys. Use Colab's per-user secret store instead (Sidebar key icon → *Secrets*, **Add new secret**, **toggle "Notebook access"**).

| Secret | Used by | Needed for this notebook? |
| --- | --- | --- |
| `HF_TOKEN` | `transformers.from_pretrained` | Optional (rate-limit / gated models) |
| `OPENAI_API_KEY` | OpenAI LLM client | No |
| `DEEPINFRA_API_KEY` | DeepInfra LLM client | No |
| `ANTHROPIC_API_KEY` | Anthropic client | No |
| `OPENROUTER_API_KEY` | OpenRouter routing | No |
| `OLLAMA_API_KEY` / `OLLAMA_BASE_URL` | Self-hosted Ollama | No |
| `GITHUB_TOKEN` | Cell 3 private-repo clone | Already consumed in Cell 3 (don't load into env) |

Cell 3 reads `GITHUB_TOKEN` directly from `userdata.get` and never puts it in `os.environ`, so it's deliberately absent from the list below.

```python
import os
from google.colab import userdata

# All secrets below are OPTIONAL for the MASK notebook. The loop tolerates
# missing keys; it only loads what you've added in the Secrets pane.
SECRET_KEYS = [
    'HF_TOKEN',           # optional — only needed for gated HF models
    # Uncomment if you'll run LLM cells in a sister notebook later:
    # 'OPENAI_API_KEY',
    # 'DEEPINFRA_API_KEY',
    # 'ANTHROPIC_API_KEY',
    # 'OPENROUTER_API_KEY',
    # 'OLLAMA_API_KEY',
    # 'OLLAMA_BASE_URL',
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

print('Loaded :', loaded or '(none — that is fine for MASK-only runs)')
print('Missing:', missing or '(none)')

# HuggingFace-specific aliases (the various HF libraries each look at a slightly
# different variable; setting all three keeps `from_pretrained` happy for gated
# models and avoids the interactive `huggingface-cli login` prompt).
if 'HF_TOKEN' in os.environ:
    os.environ.setdefault('HUGGINGFACE_HUB_TOKEN', os.environ['HF_TOKEN'])
    os.environ.setdefault('HUGGING_FACE_HUB_TOKEN', os.environ['HF_TOKEN'])
```

A clean run for MASK-only work prints `Loaded : []` (no secrets needed) — that's the expected output, not an error.

Verify HuggingFace recognises the token (optional):

```python
from huggingface_hub import whoami
try:
    print(whoami())
except Exception as e:
    print('No HF token recognised:', e)
```

---

## Cell 6 — Symlink `runs/` and `logs/` into Drive (and run the unit tests)

This is the cell that makes the runtime disconnect-safe. We replace the cloned-repo's `runs/` and `logs/` directories with symlinks pointing at `DRIVE_BASE` from Cell 2, so every script that writes under those paths (extraction, eval grid, contrastive trainer, aggregator, disagreement analysis, report generator) lands its output on Drive.

The repo ships an empty `runs/` directory; if anything is in it (e.g. you uploaded the zip with prior local artefacts), the contents are migrated to Drive before the symlink is installed.

```python
import os, shutil, pathlib

PROJECT = pathlib.Path('/content/HIPE')
DRIVE_BASE = pathlib.Path('/content/drive/MyDrive/HIPE2026_workdir')

if not pathlib.Path('/content/drive/MyDrive').exists():
    raise SystemExit(
        'Drive is not mounted. Re-run Cell 2 first — every cache and log file '
        'is otherwise lost when the runtime disconnects (which it will).'
    )
DRIVE_BASE.mkdir(parents=True, exist_ok=True)

# Symlink the WHOLE runs/ and logs/ trees, not just specific subfolders.
# That way new subdirs (logs/agentic/, logs/k_sweep/, runs/phase0_mask_diag/, ...)
# inherit the persistence automatically without needing to be listed here.
#
# Conflict rule on a re-run: Drive is the canonical persistent store, so when
# Drive already has an entry with the same name, drop the local (freshly-cloned)
# copy rather than overwriting Drive. The local clone is immutable per session,
# so this only ever loses redundant copies — never new work.
for sub in ('runs', 'logs'):
    src = PROJECT / sub
    dst = DRIVE_BASE / sub
    dst.mkdir(parents=True, exist_ok=True)

    if src.is_symlink():
        # Stale symlink from a prior session — refresh it.
        src.unlink()
    elif src.is_dir():
        for child in list(src.iterdir()):
            target = dst / child.name
            if target.exists():
                # Drive already has this entry — delete the local clone copy.
                if child.is_symlink() or not child.is_dir():
                    child.unlink()
                else:
                    shutil.rmtree(child)
            else:
                shutil.move(str(child), str(target))
        src.rmdir()
    src.symlink_to(dst, target_is_directory=True)
    print(f'  {src}  ->  {dst}')

# Sanity check: writes through the symlink should hit Drive.
probe = PROJECT / 'runs' / '.persistence_probe'
probe.write_text('ok')
assert (DRIVE_BASE / 'runs' / '.persistence_probe').read_text() == 'ok'
probe.unlink()
print('\nPersistence verified — outputs survive runtime disconnects.')
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
import json
from pathlib import Path

PROJECT = Path('/content/HIPE')
res = json.loads((PROJECT / 'runs' / 'phase0_mask_diag' / 'results.json').read_text())
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
!cd /content/HIPE && for f in runs/mask_*.npz; do \
    [[ "$f" == *_spec* ]] && continue; \
    echo "==> $f"; \
    python scripts/extract_spectral_features.py \
        --npz "$f" \
        --base mask_emb_layers \
        --n-components 10 \
        --n-neighbors 20; \
done
```

Sanity check NMI (eigenvector vs label) for one cache. We resolve the path against the absolute project root (set in Cell 3 via `os.chdir`), and we glob-match `*_spec*.npz` so this works regardless of which encoder/template/layer combination Cell 9 produced — it just picks the first multi-layer hmBERT spectral cache it finds.

```python
import numpy as np, json
from pathlib import Path

PROJECT = Path('/content/HIPE')
runs_dir = PROJECT / 'runs'

# Prefer the multi-layer hmBERT spectral cache; fall back to any spectral cache.
candidates = sorted(runs_dir.glob('mask_dbmdz_*_M2_L*_spec*.npz')) \
          or sorted(runs_dir.glob('mask_*_spec*.npz'))
if not candidates:
    raise FileNotFoundError(
        f"No *_spec*.npz cache under {runs_dir}. Did Cell 11 finish?\n"
        f"runs/ contents: {[p.name for p in runs_dir.glob('*.npz')]}"
    )
cache_path = candidates[0]
print('Using cache:', cache_path)

z = np.load(cache_path, allow_pickle=True)
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
experiment_id                                                  global   MR(at)  MR(isAt)
T1.4or5_mask_grid_mask_dbmdz..._M2_L-1_-4_-7_concat_l_t_at    0.5950  0.6321  0.5579
T1.4or5_mask_grid_mask_xlm_roberta_base_M2_concat_t_at        0.5810  0.6024  0.5596
...
```

Open the aggregate JSON for the full table:

```python
import json, pandas as pd
from pathlib import Path

PROJECT = Path('/content/HIPE')
rows = json.loads((PROJECT / 'runs' / 'mask_grid_eval' / 'summary.json').read_text())['rows']
df = pd.DataFrame(rows).sort_values('global_score', ascending=False)
df[['experiment_id', 'feature_set', 'target', 'input_dim',
    'global_score', 'macro_recall_at', 'macro_recall_isAt']].head(20)
```

---

## Cell 13 — Phase 4: contrastive training (MLP + ordinal/SupCon)

We resolve the cache path once via glob over the absolute project root, so the cell works regardless of which encoder / template / layer settings Cell 9 actually used (and we don't have to hand-write the layer-tagged filename, which contains literal `-` characters that are easy to mistype).

```python
from pathlib import Path

PROJECT = Path('/content/HIPE')
runs_dir = PROJECT / 'runs'

# Prefer the multi-layer hmBERT cache; fall back to the single-layer hmBERT one.
candidates = (
    sorted(runs_dir.glob('mask_dbmdz_*_M2_L*.npz'))
    or sorted(runs_dir.glob('mask_dbmdz_*_M2.npz'))
)
candidates = [p for p in candidates if '_spec' not in p.name]  # base cache, not spectral
if not candidates:
    raise FileNotFoundError(
        f'No hmBERT M2 cache under {runs_dir}. Run Cell 9 first.\n'
        f"runs/ contents: {[p.name for p in runs_dir.glob('*.npz')]}"
    )
CACHE = candidates[0]
FEATURE_SET = 'concat_l_t' if '_L' in CACHE.name else 'concat_t'
print(f'Cache       : {CACHE}')
print(f'Feature set : {FEATURE_SET}')
```

Joint head — ordinal contrastive on `at` + SupCon on `isAt`:

```bash
!python scripts/train_mask_contrastive.py \
    --npz "$CACHE" --feature-set "$FEATURE_SET" \
    --epochs 25 --alpha 0.7 \
    --contrastive-at ordinal --contrastive-isAt supcon \
    --val-fraction 0.1 --patience 6
```

Useful ablations (all idempotent, ~2 min each on a T4):

```bash
# CE-only baseline (no contrastive contribution)
!python scripts/train_mask_contrastive.py \
    --npz "$CACHE" --feature-set "$FEATURE_SET" \
    --alpha 1.0 --contrastive-at none --contrastive-isAt none \
    --experiment-id T1.4or5_mask_contrastive_CEonly_at-test

# SupCon on at (vs the ordinal default)
!python scripts/train_mask_contrastive.py \
    --npz "$CACHE" --feature-set "$FEATURE_SET" \
    --contrastive-at supcon --contrastive-isAt supcon \
    --experiment-id T1.4or5_mask_contrastive_supcon_at-test

# Aggressive ordinal margin
!python scripts/train_mask_contrastive.py \
    --npz "$CACHE" --feature-set "$FEATURE_SET" \
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
from pathlib import Path

PROJECT = Path('/content/HIPE')
results = json.loads((PROJECT / 'logs' / 'final' / 'results.json').read_text())
print(f"Total experiments scored: {results['n_experiments']}")
print('\nTop-12 by GlobalScore:')
for r in results['ranking_by_global_score'][:12]:
    eid = r['experiment_id']
    gs = r['global_score']
    print(f"  {eid:75s} {gs:.4f}")
```

Open the new evaluation report:

```python
from pathlib import Path

PROJECT = Path('/content/HIPE')
print((PROJECT / 'logs' / 'final' / 'evaluation_report.md').read_text()[:4000])  # head only
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
