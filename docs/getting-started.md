# Getting Started — 5 minutes

This guide is for a first-time user who wants to process a real private dataset safely.

The shortest mental model is:

```text
inspect locally
    ↓
run Long Gate
    ↓
review Trust Report
    ↓
if a safe egress artifact exists:
approve exact artifact locally
    ↓
network AI reads only that approved artifact
```

For unstructured text, PDFs, images, OCR, and audio, the current baseline remains local-only.

---

## 0. Choose your path

| Goal | Path |
|---|---|
| Inspect a private table | `inspect` |
| Run full privacy workflow | `run` |
| Compute real statistics | `exact` |
| Let a network AI interpret a safe result | `run` → review → `approve-egress` → `longgate-mcp` |
| Process private text with a local LLM | `model setup` → `semantic-transform-local` |
| Inspect DOCX/PDF/image/audio locally | document/media commands |

---

# 1. Install

## Windows PowerShell

```powershell
git clone https://github.com/CochraneK/long-gate.git
cd long-gate

py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\longgate.exe doctor
```

Or:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/bootstrap.ps1
```

## macOS / Linux

```bash
git clone https://github.com/CochraneK/long-gate.git
cd long-gate

python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e .
.venv/bin/longgate doctor
```

Or:

```bash
bash scripts/bootstrap.sh
```

---

# 2. Inspect your private table

```bash
longgate inspect study.csv
```

This is local-only inspection.

Check whether important columns are classified sensibly:

- direct identifiers;
- quasi-identifiers;
- sensitive variables;
- free text;
- general variables.

The inspection output reports counts/classifications rather than matched private values.

---

# 3. Run the structured privacy workflow

```bash
longgate run study.csv --profile research --backend auto
```

The result includes fields such as:

```json
{
  "run_id": "LG-...",
  "status": "...",
  "output": "longgate-runs/LG-...",
  "report": "longgate-runs/LG-.../report/trust-report.html",
  "release_class": "aggregate",
  "next_actions": [],
  "safe_payload": "longgate-runs/LG-.../egress/safe_aggregate.json"
}
```

The exact result depends on your data.

The release ladder is:

```text
row-level synthetic
      ↓ blocked / pre-1.0 hard-lock
disclosure-limited aggregate
      ↓ if not justified
LOCAL_ONLY + next_actions
```

A block is not a request to weaken the policy.

---

# 4. Review the Trust Report

Open the returned `report` path.

Review:

- column classifications;
- privacy-audit findings;
- row-level blockers;
- aggregate fallback;
- final egress scan;
- release class;
- staged artifact;
- provenance.

If `safe_payload` is null, there is nothing to approve for network access.

---

# 5. If you need a network AI, approve the exact artifact

Suppose the run produced:

```text
longgate-runs/LG-123/egress/safe_aggregate.json
```

Run:

```bash
longgate approve-egress \
  longgate-runs/LG-123/egress/safe_aggregate.json \
  --workspace longgate-runs/LG-123/egress \
  --ledger ./longgate-policy/approvals.jsonl \
  --purpose "interpret aggregate statistics"
```

Approval requires a matching Long Gate egress manifest.

The manifest must prove:

- policy `allow = true`;
- final scan passed;
- release class is currently an allowed aggregate;
- artifact filename matches;
- artifact SHA-256 matches.

Then the approval additionally binds:

```text
relative path + SHA-256 + exact purpose
```

Copying an arbitrary file into the egress directory does not make it approvable.

Changing the artifact after approval invalidates the hash match.

---

# 6. Start the MCP boundary

Install:

```bash
pip install -e '.[mcp]'
```

## macOS / Linux

```bash
export LONGGATE_SAFE_WORKSPACE=/absolute/path/to/longgate-runs/LG-123/egress
export LONGGATE_APPROVAL_LEDGER=/absolute/path/to/longgate-policy/approvals.jsonl
export LONGGATE_ACCESS_LOG=/absolute/path/to/longgate-policy/access.jsonl

longgate-mcp
```

## Windows PowerShell

```powershell
$env:LONGGATE_SAFE_WORKSPACE="C:\path\to\longgate-runs\LG-123\egress"
$env:LONGGATE_APPROVAL_LEDGER="C:\path\to\longgate-policy\approvals.jsonl"
$env:LONGGATE_ACCESS_LOG="C:\path\to\longgate-policy\access.jsonl"

longgate-mcp
```

Configure your MCP-compatible AI client to launch that command with those environment variables.

The network-side tools are intentionally narrow:

```text
gate_info()
list_safe_files(purpose)
read_safe_text(relative_path, purpose)
```

The server cannot create approvals and cannot browse arbitrary local paths.

---

# 7. Exact local statistics

For real statistics:

```bash
longgate exact study.csv describe

longgate exact study.csv correlation

longgate exact study.csv group-summary \
  --group-by group \
  --value score

longgate exact study.csv ols \
  --outcome score \
  --predictor age \
  --predictor group
```

Fixed-template local R:

```bash
longgate exact study.csv ols \
  --engine r \
  --outcome score \
  --predictor age
```

The real table stays local.

---

# 8. Local LLM setup

Long Gate separates network-enabled model installation from private processing.

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

Install:

```bash
pip install -e '.[models,local-llm]'
```

Then:

```bash
longgate model setup
longgate model verify auto
```

Private transformation:

```bash
longgate semantic-transform-local interview.txt \
  --model auto \
  --out preview.txt
```

The semantic output is still local-only in the current baseline.

---

# 9. Documents, OCR, images, and audio

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

No network OCR fallback is used.

These commands do not grant network egress.

---

# 10. Verify provenance

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

Unsigned verification proves internal artifact/manifest consistency only.

---

# Let another AI configure Long Gate

Run:

```bash
longgate setup-prompt
```

Copy the output into a coding assistant or computer-use agent.

The maintained prompt tells it not to open private datasets during setup.

---

# Before using highly sensitive data

Check:

```bash
longgate doctor
```

If using a local model:

```bash
longgate model verify auto
```

For the strongest deployment boundary, use the hardened Compose pattern:

- private worker: raw-data access + no network;
- network worker: network + safe read-only workspace;
- no service receives both capabilities.

See:

- [Threat model](threat-model.md)
- [Security invariants](security-invariants.md)
- [Agent boundary](agent-boundary.md)
- [Egress approval ledger](approval-ledger.md)
- [Troubleshooting](troubleshooting.md)
