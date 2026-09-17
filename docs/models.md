# Local Model Guide

Long Gate is designed so a new user does not need to understand GGUF filenames, quantization jargon, GPU-offload details, or model-hosting mechanics before getting started.

## Recommended entrypoint

Install:

```bash
pip install -e '.[models]'
```

Install `local-llm` separately after the base setup. It is a native extension,
so pip may compile it from source. On Windows, use Python 3.12 and the CPU
wheel when available:

```powershell
pip install -e ".[local-llm]"
pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu
```

Inspect the machine without downloading anything:

```bash
longgate setup --recommend-only
```

or:

```bash
longgate hardware
```

The local hardware advisor reports, when available:

- OS and architecture;
- logical CPU count;
- total system RAM;
- free disk space for the Model Vault;
- NVIDIA GPU and VRAM through local `nvidia-smi`;
- FAST / BALANCED / QUALITY model-fit guidance.

Hardware inventory stays local. GPU detection is best-effort only: failure never triggers a remote fallback and does not block CPU-only use.

To install the selected model:

```bash
longgate setup
```

This composes hardware advice with the existing Model Vault workflow:

```text
hardware inspection
      ↓
conservative RAM-led recommendation
      ↓
pinned model download
      ↓
SHA-256 verification
      ↓
default Model Vault alias
      ↓
READY
```

## Current curated tiers

Long Gate deliberately keeps the built-in catalog small and reviewed.

| Tier | Alias | Official model | Quant | File size | Recommended RAM |
|---|---|---|---|---:|---:|
| FAST | `qwen3-4b` | Qwen3-4B-GGUF | Q4_K_M | ~2.5 GB | ~8 GB |
| BALANCED | `qwen3-8b` | Qwen3-8B-GGUF | Q4_K_M | ~5.03 GB | ~16 GB |
| QUALITY | `qwen3-14b` | Qwen3-14B-GGUF | Q4_K_M | ~9 GB | ~24 GB |

The advisor labels each model fit as approximately:

```text
COMFORTABLE
TIGHT
INSUFFICIENT
UNKNOWN
```

The automatically selected default remains RAM-led because GPU offload depends on how `llama-cpp-python` / llama.cpp was built on that machine. Detected GPU/VRAM information is therefore advisory rather than an unsupported promise about acceleration.

Advanced users can still run:

```bash
longgate model recommend
longgate model install qwen3-8b
longgate model verify qwen3-8b
longgate model list
```

## Private processing after setup

The preferred semantic workflow is now:

```bash
longgate deidentify interview.txt \
  --model auto \
  --out deidentified.txt
```

`auto` resolves the verified Model Vault default. It does **not** download a model during private processing.

The lower-level single-pass interface remains available:

```bash
longgate semantic-transform-local interview.txt \
  --model auto \
  --out preview.txt
```

See [Local semantic privacy path](semantic-preview.md) for the difference.

## Why Qwen3 first?

The initial catalog favors a compact multilingual model family with official GGUF releases and Apache-2.0 licensing. The catalog is intentionally curated rather than becoming an unreviewed model marketplace.

## Supply-chain anchors

Long Gate downloads catalog entries from official upstream repositories and pins two anchors per file:

1. an immutable Hugging Face revision;
2. the expected file SHA-256.

The catalog does not track a moving upstream `main` branch for installation. A checksum mismatch causes installation to fail closed.

## Model Vault

Default location:

```text
~/.longgate/models/
├── Qwen3-...-Q4_K_M.gguf
└── manifest.json
```

Override it with:

```bash
export LONGGATE_MODEL_VAULT=/path/to/models
```

PowerShell:

```powershell
$env:LONGGATE_MODEL_VAULT = "D:\LongGate\models"
```

The manifest records source metadata, license, SHA-256, size, and install time. Model provisioning never needs a private dataset path.

## Setup Mode vs Private Processing Mode

### Setup Mode

```text
Internet:       YES
Private mount:  NO
Model Vault:    WRITE
```

Typical commands:

```bash
longgate setup
longgate model install <alias>
```

### Private Processing Mode

```text
Internet:       NO
Private mount:  YES
Model Vault:    READ ONLY
```

Typical command:

```bash
longgate deidentify ... --model auto
```

This separation matters more than the historical fact that a model was originally downloaded from the Internet. The unsafe capability combination is a process that can read raw private data and also has unrestricted network access.

## Let another AI configure Setup Mode

```bash
longgate setup-prompt
```

The maintained prompt tells a coding/computer-use assistant to configure Long Gate and the Model Vault without opening or ingesting private datasets.

## Manual model fallback

Advanced users may provide an already-local GGUF directly:

```bash
longgate deidentify interview.txt \
  --model /absolute/path/model.gguf \
  --out deidentified.txt
```

Manual local files are supported, but the curated Model Vault path is preferred because it carries reproducible upstream source and checksum metadata.
