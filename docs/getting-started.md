# Getting Started — 5 minutes

Long Gate has two first-class paths:

```text
PRIVATE TABLE                         PRIVATE TXT / MD / HTML / XLSX
     │                                        │
     ▼                                        ▼
longgate run                         longgate deidentify
     │                                        │
     ▼                                        ▼
structured Trust Report             same-format local copy + Trust Report
     │                                        │
     ▼                                        ▼
approved aggregate or LOCAL_ONLY    MANUAL_REVIEW_REQUIRED / LOCAL_ONLY
```

The semantic path is deliberately stricter: **a manual-review candidate is still local-only and is not automatically eligible for network egress.**

---

## 1. Install

### Windows PowerShell

```powershell
git clone https://github.com/CochraneK/long-gate.git
cd long-gate

py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e ".[models,documents]"
```

### macOS / Linux

```bash
git clone https://github.com/CochraneK/long-gate.git
cd long-gate

python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e '.[models,documents]'
```

`local-llm` is optional because `llama-cpp-python` may compile native C++ code
when no matching wheel exists. On Windows, Python 3.12 plus the upstream CPU
wheel is usually the quickest route:

```powershell
py -3.12 -m venv .venv312
.\.venv312\Scripts\python.exe -m pip install -U pip
.\.venv312\Scripts\python.exe -m pip install -e ".[models,documents,local-llm]"
.\.venv312\Scripts\python.exe -m pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu
```

Run `longgate doctor` before private processing.

Existing bootstrap scripts remain available:

```bash
bash scripts/bootstrap.sh
```

or on Windows:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/bootstrap.ps1
```

---

# 2. Start with `longgate setup`

```bash
longgate setup --recommend-only
```

This performs **local-only** hardware inspection and reports:

- operating system and architecture;
- logical CPU count;
- system RAM;
- free disk space for the Model Vault;
- NVIDIA GPU / VRAM when local `nvidia-smi` is available;
- FAST / BALANCED / QUALITY model-fit guidance.

GPU detection is advisory only. Failure to detect a GPU does not block CPU-only use and does not trigger a remote hardware-detection service.

Example model tiers:

| Tier | Current catalog choice | Typical role |
|---|---|---|
| FAST | Qwen3-4B Q4_K_M | lighter / faster local transform |
| BALANCED | Qwen3-8B Q4_K_M | default balance on mid-memory machines |
| QUALITY | Qwen3-14B Q4_K_M | higher-capacity local semantic transform |

The selected model remains RAM-led and conservative because actual GPU offload depends on the local llama.cpp build.

To install the recommended model:

```bash
longgate setup
```

Long Gate then:

```text
local hardware inspection
        ↓
model recommendation
        ↓
pinned Hugging Face revision download
        ↓
SHA-256 verification
        ↓
Model Vault default
        ↓
READY
```

**Setup mode may use the network but should not have private data mounted or opened.**

If you only want the hardware report later:

```bash
longgate hardware
```

The advanced model commands still exist:

```bash
longgate model recommend
longgate model setup
longgate model verify auto
longgate model list
```

---

# 3A. Private structured data

Inspect a table locally:

```bash
longgate inspect study.csv
```

Run the full structured privacy workflow:

```bash
longgate run study.csv --profile research --backend auto
```

The release ladder remains:

```text
row-level synthetic
      ↓ blocked / pre-1.0 hard-lock
disclosure-limited aggregate
      ↓ if not justified
LOCAL_ONLY + next_actions
```

The command returns a run directory and offline Trust Report. If a disclosure-limited aggregate is justified, an egress artifact may be staged. Raw rows, pseudonymized rows, and pre-1.0 row-level synthetic data remain network-ineligible.

For real statistics without uploading the source table:

```bash
longgate exact study.csv describe
longgate exact study.csv correlation
longgate exact study.csv group-summary --group-by group --value score
longgate exact study.csv ols --outcome score --predictor age --predictor group
```

---

# 3B. Private documents: format-preserving de-identification

For TXT/Markdown/HTML/XLSX that must remain reusable after de-identification:

```bash
longgate deidentify interview.md
```

`--out` is optional. By default Long Gate writes `interview.deidentified.md` beside the source. The source is never overwritten.

The preserve-first pipeline is:

```text
supported source document
      ↓
fix source SHA-256 before any write
      ↓
detect explicit direct identifiers
      ↓
stable per-document placeholders
      ↓
same-format atomic output
      ↓
scan output again
      ↓
MANUAL_REVIEW_REQUIRED
```

Names, organizations, locations, aliases, rare events, and combination uniqueness are not guaranteed to be removed. HTML scripts/styles/templates/SVG text and XLSX formulas/sheet titles/defined names are intentionally not silently rewritten. If direct PII remains in those regions the result is `LOCAL_ONLY`. See [Format-preserving de-identification](format-preserving.md).

For stronger semantic abstraction, use the separate command:

```bash
longgate semantic-summarize interview.txt \
  --model auto \
  --out summary.txt
```

`semantic-summarize` is the previous bounded local-GGUF transformation pipeline. It supports extractable TXT/Markdown/HTML/DOCX/PDF text, audits every candidate against the original source, rejects token-limit truncation, and remains local-only.

Use a real model/inference health check when needed:

```bash
longgate doctor --deep --model auto
```

Neither path grants network egress automatically.

---
# 4. Review before any network use

For structured runs, open:

```text
longgate-runs/LG-.../report/trust-report.html
```

Review:

- classifications;
- privacy-audit findings;
- release class;
- final egress scan;
- staged artifact;
- provenance.

For format-preserving de-identification, open the generated `*.trust-report.html` and inspect the same-format copy locally. For semantic abstraction, inspect the `semantic-summarize` output and its Semantic Trust Report. Both remain local-only.

---

# 5. Structured safe artifact → explicit local approval → MCP

This step applies only to a supported Long Gate egress artifact, currently the disclosure-limited aggregate path.

Example:

```bash
longgate approve-egress \
  longgate-runs/LG-123/egress/safe_aggregate.json \
  --workspace longgate-runs/LG-123/egress \
  --ledger ./longgate-policy/approvals.jsonl \
  --purpose "interpret aggregate statistics"
```

Approval requires a matching Long Gate egress manifest proving:

- policy `allow = true`;
- final scan passed;
- an allowed aggregate release class;
- exact artifact filename;
- exact artifact SHA-256.

The approval then additionally binds:

```text
relative path + SHA-256 + exact purpose
```

An arbitrary file copied into the workspace cannot be approved.

Start the narrow MCP surface:

```bash
pip install -e '.[mcp]'

export LONGGATE_SAFE_WORKSPACE=/absolute/path/to/longgate-runs/LG-123/egress
export LONGGATE_APPROVAL_LEDGER=/absolute/path/to/longgate-policy/approvals.jsonl
export LONGGATE_ACCESS_LOG=/absolute/path/to/longgate-policy/access.jsonl
longgate-mcp
```

PowerShell uses the equivalent `$env:...` variables.

The network-facing server exposes only:

```text
gate_info()
list_safe_files(purpose)
read_safe_text(relative_path, purpose)
```

It cannot create approvals or browse arbitrary local paths.

---

# 6. Other local-only media paths

Install:

```bash
pip install -e '.[documents,media,ocr]'
```

Examples:

```bash
longgate document-inspect report.docx
longgate document-inspect transcript.pdf
longgate image-inspect photo.jpg
longgate image-ocr-local scan.png
longgate pdf-ocr-local scanned.pdf --max-pages 50
longgate audio-inspect interview.wav
```

There is no cloud OCR fallback. These commands do not grant network egress.

---

# 7. Verify structured-run provenance

```bash
longgate verify-run longgate-runs/LG-...
```

Optional signed provenance:

```bash
longgate sign-run longgate-runs/LG-... \
  --signing-key /secure/location/signing-key.pem

longgate verify-run longgate-runs/LG-... \
  --public-key /trusted/location/public-key.pem
```

Unsigned verification checks internal artifact/manifest consistency only. Authenticated provenance depends on independently trusting the verification public key.

---

# Let another AI configure the setup phase

```bash
longgate setup-prompt
```

The maintained prompt tells a coding/computer-use assistant not to open private datasets during setup.

---

# Before highly sensitive use

```bash
longgate doctor
longgate model verify auto
```

For the strongest process boundary:

- setup worker: network + Model Vault write, no private mount;
- private worker: private data + Model Vault read-only, no network;
- network worker: network + approved safe workspace only.

See:

- [Threat model](threat-model.md)
- [Security invariants](security-invariants.md)
- [Agent boundary](agent-boundary.md)
- [Semantic preview](semantic-preview.md)
- [Egress approval ledger](approval-ledger.md)
- [Troubleshooting](troubleshooting.md)
