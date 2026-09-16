<div align="center">

<img src="docs/assets/long-gate-banner.svg" alt="Long Gate — sensitive data stays local, safe artifacts cross" width="100%">

# Long Gate

### Let AI reason about sensitive data without giving AI the sensitive data.

**A local-first privacy gateway and capability boundary for AI agents.**

[![License](https://img.shields.io/badge/license-Apache--2.0-7ee2a8)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-86a7ff)](pyproject.toml)
[![Status](https://img.shields.io/badge/status-pre--1.0-ffd479)](ROADMAP.md)
[![Security model](https://img.shields.io/badge/security-fail--closed-ff7d8b)](docs/security-invariants.md)

**[Quick start](#quick-start) · [Architecture](#architecture) · [Threat model](docs/threat-model.md) · [Roadmap](ROADMAP.md) · [Contributing](CONTRIBUTING.md)**

</div>

---

## The 30-second version

Most AI integrations protect sensitive data with instructions:

> “The agent can access the file, but please don't reveal it.”

Long Gate takes a different position:

> **If a networked AI should not see raw data, do not give it the capability to see raw data.**

Long Gate sits between private local datasets and networked AI systems. It inspects data locally, routes each task to the minimum necessary representation, runs exact statistics locally when needed, and exposes only policy-approved artifacts through a narrow safe workspace.

```text
PRIVATE / LOCAL                                   NETWORKED AI

Raw data
   │
   ├── schema question ───────────────► metadata only
   │
   ├── exploration ─► synthetic twin ─► privacy audit ─┐
   │                                                    │
   └── exact analysis ─► local executor ─► aggregates ──┤
                                                        ▼
                                                ┌──────────────┐
                                                │  LONG GATE   │
                                                │ egress guard │
                                                └──────┬───────┘
                                                       │
                                                  safe artifacts
                                                       │
                                                       ▼
                                                   AI agent
```

**Raw and pseudonymized row-level data are network-ineligible by policy.**

> Long Gate is currently pre-1.0. Row-level synthetic egress remains fail-closed by default while stronger privacy validation is being hardened.

---

## Why this exists

AI agents are getting very good at analysis, coding, interpretation, and research. The obvious integration pattern is to mount a folder, connect an API, and let the agent work.

That pattern becomes dangerous when the folder contains:

- research participants;
- mental-health or clinical variables;
- employee or student records;
- interviews and narratives;
- longitudinal identifiers;
- internal business data;
- any dataset where “remove the name column” is not enough.

Long Gate is built around one architectural invariant:

> **Anything that can read raw data should not have unrestricted network access. Anything that has network access should not receive raw-data capabilities.**

That is a system boundary, not a prompt.

---

## What makes Long Gate different

| Common approach | What it does well | What Long Gate adds |
|---|---|---|
| **Mask / pseudonymize IDs** | Hides obvious identity strings | Pseudonymized rows stay local; frequency/linkage structure is treated as sensitive |
| **PII redaction** | Finds names, emails, phones, IDs | PII scanning is one layer, not the whole release policy |
| **Synthetic data** | Produces useful surrogate rows | Generation is wrapped in overlap/linkage audits, policy, identifier stripping, and egress rescanning |
| **Differential privacy** | Can provide formal guarantees | DP-capable engines can be plugged in without defining the whole architecture |
| **Prompt guardrails** | Easy to add | Long Gate removes capabilities instead of relying on compliance |
| **Secure sandbox** | Isolates processes | Long Gate also decides *what representation* the AI is allowed to receive |

Long Gate does **not** try to replace mature synthetic-data, PII, or statistical libraries.

Its job is the missing control plane around them:

**purpose → representation → local computation → privacy audit → egress policy → safe capability → provenance**

See [How Long Gate differs](docs/comparison.md).

---

## Architecture

```mermaid
flowchart LR
  subgraph LOCAL["Trusted Local Zone"]
    RAW["Raw Data"]
    INSPECT["Schema + Value-level PII"]
    PURPOSE["Purpose Router"]
    SYNTH["Synthetic Twin Backend"]
    EXACT["Local Exact Executor"]
    AUDIT["Privacy Audit"]
    REPORT["Offline Trust Report"]
  end

  subgraph GATE["LONG GATE"]
    POLICY["Deny-by-default Policy"]
    STRIP["Remove Direct IDs"]
    RESCAN["Final Egress Rescan"]
    SAFE["SafeWorkspace"]
  end

  subgraph NETWORK["Network AI Zone"]
    MCP["Narrow MCP Tools"]
    AI["Networked AI Agent"]
  end

  RAW --> INSPECT --> PURPOSE
  PURPOSE -->|exploration| SYNTH --> AUDIT --> POLICY
  PURPOSE -->|exact statistics| EXACT --> POLICY
  PURPOSE -->|unknown purpose| POLICY
  POLICY --> STRIP --> RESCAN --> SAFE --> MCP --> AI

  INSPECT --> REPORT
  AUDIT --> REPORT
  POLICY --> REPORT
  RESCAN --> REPORT

  RAW -. "never mounted here" .-> NETWORK
```

The hardened deployment mirrors the same rule at process level:

- **local worker** → private mount + `network_mode: none`
- **network worker** → network capability + safe read-only mount
- no worker gets both capabilities

See [Architecture](docs/architecture.md) and [Agent boundary](docs/agent-boundary.md).

---

## A concrete example

Imagine this source table exists only on your machine:

```text
name      phone          age   PHQ   reaction_time   group
Alice     +44...          23    15       612          A
...
```

A weak privacy layer might produce:

```text
P001      PHONE001        23    15       612          A
```

The identity strings changed, but the row is still effectively the same person.

Long Gate is designed for a stronger workflow:

1. identify direct and quasi-identifiers locally;
2. exclude direct identifiers from supported synthetic-model training;
3. generate surrogate structure locally;
4. test for exact-row, identifier, near-copy, and rare quasi-identifier overlap;
5. remove direct identifier columns from the outbound row view;
6. run a final value-level PII scan;
7. expose only the approved artifact;
8. keep an offline audit trail showing what happened.

For exact inference, Long Gate does something different:

```text
AI proposes analysis
        ↓
real data stays local
        ↓
local exact executor
        ↓
β / SE / CI / p / N / R²
        ↓
aggregate guard
        ↓
AI interprets safe result
```

Synthetic data is for **exploration and planning**. Official statistics can stay exact and local.

---

## Quick start

### 1. Install

```bash
git clone https://github.com/CochraneK/long-gate.git
cd long-gate

python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

pip install -e .
```

### 2. See what your machine can do

```bash
longgate doctor
```

### 3. Inspect locally

```bash
longgate inspect examples/demo.csv
```

The output contains schema and PII **counts**, not matched private values.

### 4. Run the privacy pipeline

```bash
longgate run examples/demo.csv --backend auto
```

`auto` prefers an installed mature local backend and otherwise falls back to the demo backend.

The demo backend is intentionally **never eligible for row-level egress**. A `BLOCKED` result is expected and demonstrates fail-closed behavior.

---

## Optional engines

Install only the capabilities you need:

```bash
pip install -e '.[mostlyai]'   # local synthetic backend
pip install -e '.[synthcity]'  # local synthetic backend
pip install -e '.[presidio]'   # enhanced local PII analysis
pip install -e '.[stats]'      # local OLS/statistics
pip install -e '.[mcp]'        # safe-workspace MCP boundary
```

Long Gate currently includes adapters for:

| Capability | Integration | Default row-level egress |
|---|---|---|
| Demo synthesis | built-in | **BLOCKED** |
| Synthetic data | SynthCity | **BLOCKED in v0.2** |
| Synthetic data | MOSTLY AI local mode | **BLOCKED in v0.2** |
| PII analysis | built-in local scanner | local only |
| PII analysis | Microsoft Presidio | local only |
| Exact statistics | pandas / statsmodels | guarded aggregate only |
| Agent access | FastMCP | SafeWorkspace only |

---

## Purpose-bound disclosure

Different questions should not receive the same amount of data.

```bash
longgate purpose regression
```

Current routing philosophy:

| Purpose | Representation |
|---|---|
| “What columns exist?” | schema metadata |
| “Help me prototype an analysis” | synthetic path |
| “Show distributions” | synthetic path / safe summaries |
| “Compute the real regression” | exact local executor |
| unknown / ambiguous purpose | **BLOCK** |

Exact local examples:

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

Exact-stat release guards include:

- identifier exclusion;
- minimum dataset size;
- small-group suppression;
- rare categorical-level blocking;
- final aggregate PII scanning.

---

## The Trust Report

Every run generates a self-contained offline HTML report.

```text
longgate-runs/LG-.../
├── manifest.json
├── audit.json
├── safe/
│   └── synthetic.csv
├── egress/
│   └── egress_manifest.json
└── report/
    └── trust-report.html
```

The report answers:

- **What stayed local?**
- **Which columns were treated as identifiers or sensitive?**
- **Which privacy attacks were checked?**
- **Were direct identifiers removed?**
- **Did the final egress scan pass?**
- **Did any network transmission occur?**
- **Which code/policy version produced this decision?**

It is deliberately offline: no CDN, analytics, remote fonts, or external assets.

Open the committed [Trust Report example](examples/trust-report-demo.html) to see the current direction.

---

## Agent boundary

The optional MCP server does **not** expose your filesystem.

It exposes only:

```text
gate_info()
list_safe_files()
read_safe_text(relative_path)
```

The `SafeWorkspace` rejects:

- absolute paths;
- `../` traversal;
- resolved paths that escape the approved root.

There is intentionally no:

- arbitrary shell tool;
- arbitrary Python tool;
- raw-file path tool;
- “force release” tool.

```bash
pip install -e '.[mcp]'

export LONGGATE_SAFE_WORKSPACE=/path/to/approved/egress
longgate-mcp
```

---

## Security invariants

Long Gate treats security promises as executable requirements.

A few examples:

```text
RAW rows                 → NEVER network eligible
PSEUDONYMIZED rows       → NEVER network eligible
UNKNOWN purpose          → BLOCK
PII found at final scan  → BLOCK
demo backend             → BLOCK
small unsafe group       → SUPPRESS / BLOCK
path escapes safe root   → BLOCK
```

CI includes:

- unit + privacy invariant tests;
- CodeQL;
- Bandit;
- pip-audit;
- Trivy;
- CycloneDX SBOM generation;
- Dependabot.

See the full [Security invariants](docs/security-invariants.md) and [Threat model](docs/threat-model.md).

If you find a vulnerability, **do not attach real sensitive data to a public issue**. Follow [SECURITY.md](SECURITY.md).

---

## Current status

Long Gate is deliberately conservative.

### Implemented baseline

- [x] CSV / XLSX / JSON / Parquet ingest
- [x] schema-level privacy classification
- [x] value-level direct-PII scanning
- [x] optional Presidio integration
- [x] SynthCity adapter
- [x] MOSTLY AI local-mode adapter
- [x] exact-row / identifier / near-copy checks
- [x] rare quasi-identifier overlap checks
- [x] identifier stripping before outbound staging
- [x] final egress PII rescan
- [x] purpose-bound disclosure
- [x] local describe / correlation / group summaries / OLS
- [x] aggregate guard
- [x] SafeWorkspace boundary
- [x] minimal FastMCP surface
- [x] offline Trust Report
- [x] security CI and SBOM

### Still being hardened

- [ ] formal production criteria for row-level synthetic egress
- [ ] stronger membership-inference / linkage testing
- [ ] explicit privacy profiles and threshold configuration
- [ ] signed manifests and stronger provenance
- [ ] local R execution
- [ ] unstructured interview / document privacy path
- [ ] broader adversarial test corpus

See the [Roadmap](ROADMAP.md).

---

## What Long Gate does **not** claim

Long Gate does not currently claim:

- that synthetic data is automatically anonymous;
- a formal differential-privacy guarantee from the orchestration layer itself;
- legal or regulatory compliance certification;
- production certification for row-level synthetic egress;
- protection against a compromised host OS or administrator;
- semantic privacy guarantees for arbitrary free text, images, audio, or PDFs.

Those boundaries are features, not footnotes. Security tooling becomes less trustworthy when it hides its assumptions.

---

## Designed for integration

Long Gate is intended to sit underneath other projects.

```python
from longgate import LongGate

gate = LongGate()

inspection = gate.inspect("study.csv")

decision = gate.route("regression")

result = gate.exact(
    "study.csv",
    "ols",
    outcome="score",
    predictors=["age", "group"],
)
```

The goal is for downstream applications to call **Long Gate**, not cloud AI APIs directly, when sensitive local data is involved.

---

## Project philosophy

Three rules guide development:

1. **Capabilities beat prompts.**  
   If the agent must not read raw data, remove raw-data access.

2. **Purpose determines disclosure.**  
   A schema question should not receive rows. Exact statistics should not require cloud access to the source table.

3. **Integrate mature privacy tech; don't reinvent it.**  
   Long Gate should own orchestration, trust boundaries, policy, egress, provenance, and agent permissions — not reimplement every PII detector or synthetic model.

Read the longer [Vision](docs/vision.md).

---

## Contributing

Long Gate especially welcomes contributions in:

- privacy attacks and evaluation;
- synthetic-data adapters;
- differential-privacy backends;
- local execution sandboxes;
- Chinese / multilingual PII detection;
- threat modeling;
- adversarial tests;
- Trust Report UX;
- research reproducibility.

Start with [CONTRIBUTING.md](CONTRIBUTING.md).

For a privacy design concern, use the dedicated **Privacy / threat-model review** issue template.

---

## Research use

If you use Long Gate in research, please cite the repository using [CITATION.cff](CITATION.cff).

Long Gate also records input hashes, policy decisions, backend names, audit outcomes, and run provenance so privacy processing can become part of the reproducible research record.

---

## License

Long Gate's own code is licensed under **Apache-2.0**.

Third-party libraries retain their respective licenses. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

---

<div align="center">

### Build AI workflows where sensitive data has a boundary.

If that is a problem you care about, **⭐ star Long Gate** and help pressure-test the threat model.

</div>
