# Local Model Guide

Long Gate is designed so a new user does not need to learn GGUF naming, quantization jargon, or model-hosting details before getting started.

## The easiest path

Install the setup and local-inference extras:

```bash
pip install -e '.[models,local-llm]'
```

Then the easiest path is one command:

```bash
longgate model setup
```

It detects system RAM, chooses a curated model, downloads the pinned Hugging Face revision, verifies SHA-256, and sets the verified model as the local default.

Check it:

```bash
longgate model verify auto
longgate model list
```

Private processing can then use the verified default without knowing its filename:

```bash
longgate semantic-transform-local interview.txt \
  --model auto \
  --out preview.txt
```

If you want control instead of automatic selection:

```bash
longgate model recommend
longgate model install qwen3-8b
longgate model verify qwen3-8b
```

The private processing path resolves the alias from the local Model Vault and does **not** download anything.

## Recommended models

Long Gate's initial built-in catalog deliberately stays small.

| Alias | Official model | Quant | File size | Conservative RAM guidance | License |
|---|---|---|---:|---:|---|
| `qwen3-4b` | Qwen3-4B-GGUF | Q4_K_M | ~2.5 GB | ~8 GB | Apache-2.0 |
| `qwen3-8b` | Qwen3-8B-GGUF | Q4_K_M | ~5.03 GB | ~16 GB | Apache-2.0 |
| `qwen3-14b` | Qwen3-14B-GGUF | Q4_K_M | ~9 GB | ~24 GB | Apache-2.0 |

The RAM values are practical guidance, not hard guarantees. Context length, GPU offload, the operating system, and other running applications also matter.

### Why Qwen3 first?

The initial catalog favors a compact, multilingual model family with official GGUF releases and a permissive Apache-2.0 license. The catalog is intentionally curated rather than becoming an unreviewed model marketplace.

## Where the files come from

Long Gate downloads these catalog entries from the official Qwen organization on Hugging Face:

- https://huggingface.co/Qwen/Qwen3-4B-GGUF
- https://huggingface.co/Qwen/Qwen3-8B-GGUF
- https://huggingface.co/Qwen/Qwen3-14B-GGUF

The catalog snapshot currently pins the expected SHA-256 for each Q4_K_M file.

If the upstream file changes and the checksum no longer matches, Long Gate **fails closed** instead of silently trusting the new file.

## Model Vault

Default location:

```text
~/.longgate/models/
├── Qwen3-4B-Q4_K_M.gguf
└── manifest.json
```

Override it with:

```bash
export LONGGATE_MODEL_VAULT=/path/to/models
```

On Windows PowerShell:

```powershell
$env:LONGGATE_MODEL_VAULT = "D:\LongGate\models"
```

The manifest records source, license, SHA-256, size, and install time. It never needs a private dataset path.

## Setup mode vs private mode

### Model Setup Mode

```text
Internet:       YES
Private mount:  NO
Model Vault:    WRITE
```

Used only for model provisioning commands such as:

```bash
longgate model setup
longgate model install <alias>
```

### Private Processing Mode

```text
Internet:       NO
Private mount:  YES
Model Vault:    READ ONLY
```

Used for:

```bash
longgate semantic-transform-local ...
```

This separation is more important than whether the model originally came from the Internet. The unsafe combination is a process that can read raw private data **and** has unrestricted network access.

## Let your own AI configure Long Gate

Run:

```bash
longgate setup-prompt
```

Copy the resulting prompt into your coding assistant or local computer-use agent.

The prompt explicitly tells the AI to configure software and the Model Vault without opening or ingesting any private dataset.

A copy is also available in [AI setup prompt](ai-setup-prompt.md).

## Manual fallback

If you prefer to download manually, place a GGUF anywhere on disk and pass its path:

```bash
longgate semantic-transform-local interview.txt \
  --model /absolute/path/model.gguf \
  --out preview.txt
```

Manual files are supported for advanced users, but the built-in Model Vault path is preferred because it gives you reproducible source and checksum metadata.
