# Getting Started — 5 minutes

Long Gate's easiest local-AI path is designed for people who do **not** want to learn GGUF filenames, quantization jargon, or model-hosting details.

The workflow has two separate phases:

```text
MODEL SETUP MODE
Internet: YES
Private data: NO
Model Vault: WRITE
        ↓
PRIVATE PROCESSING MODE
Internet: NO
Private data: YES
Model Vault: READ ONLY
```

The separation is deliberate.

---

## Option A — let your own AI set it up

From the Long Gate repository:

```bash
longgate setup-prompt
```

Copy the output into a coding assistant or computer-use agent that can configure your machine.

The prompt explicitly tells the AI:

- not to open or search for private datasets;
- to use the network only for software/model installation;
- to run `longgate model setup`;
- to verify the downloaded model;
- not to configure a cloud/HTTP LLM for private processing.

See [AI setup prompt](ai-setup-prompt.md).

---

## Option B — do it yourself

### Windows PowerShell

```powershell
git clone https://github.com/CochraneK/long-gate.git
cd long-gate

py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e ".[models,local-llm,documents,stats]"

.\.venv\Scripts\longgate.exe doctor
.\.venv\Scripts\longgate.exe model setup
.\.venv\Scripts\longgate.exe model verify auto
```

Or from an already-cloned repository:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/bootstrap.ps1
```

### macOS / Linux

```bash
git clone https://github.com/CochraneK/long-gate.git
cd long-gate

python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e '.[models,local-llm,documents,stats]'

.venv/bin/longgate doctor
.venv/bin/longgate model setup
.venv/bin/longgate model verify auto
```

Or:

```bash
bash scripts/bootstrap.sh
```

---

## What `model setup` does

```bash
longgate model setup
```

Long Gate:

1. detects system RAM when possible;
2. chooses a model from the curated catalog;
3. downloads a pinned immutable Hugging Face revision;
4. verifies the expected SHA-256;
5. records provenance in the Model Vault;
6. sets the verified model as the local default.

Typical defaults:

| Approx. system RAM | Recommended alias |
|---:|---|
| ~8 GB | `qwen3-4b` |
| ~16 GB | `qwen3-8b` |
| ~24 GB+ | `qwen3-14b` |

Override automatic RAM detection:

```bash
longgate model setup --ram-gb 16
```

Inspect the catalog:

```bash
longgate model catalog
```

Inspect installed models:

```bash
longgate model list
```

---

## Process a local document

After setup:

```bash
longgate semantic-transform-local interview.txt \
  --model auto \
  --out preview.txt
```

`auto` resolves the already-installed verified default model.

It does **not** download anything.

The semantic output remains:

```text
release_allowed = false
```

because the current semantic path is still a local privacy-development preview, not an anonymity certification.

---

## Inspect without running an LLM

Structured data:

```bash
longgate inspect study.csv
```

Documents:

```bash
longgate document-inspect report.docx
longgate document-inspect transcript.pdf
```

Exact local statistics:

```bash
longgate exact study.csv describe
longgate exact study.csv ols --outcome score --predictor age
```

---

## Verify everything before using private data

Run:

```bash
longgate doctor
longgate model verify auto
```

You should confirm:

- the intended local model exists;
- SHA-256 verification is true;
- `llama_cpp` is available if using semantic preview;
- the private-processing environment has no network capability when using the hardened deployment.

See [Troubleshooting](troubleshooting.md) if any step fails.
