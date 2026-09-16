# Long Gate

**Local-first privacy orchestration for safe AI data access.**

> Transform locally. Verify completely. Cross safely.

Long Gate is a privacy control plane between sensitive local data and networked AI. Its core rule is stronger than asking an agent not to inspect private files:

> software that can read raw data should not have network access; software that has network access should not receive raw-data capabilities.

The name combines a gate with the long defensive boundary of walls, passes, and checkpoints.

## Current status — v0.2 baseline

Structured data is the primary supported path: CSV, XLSX, JSON, and Parquet.

```text
raw source
   ↓
local schema + value-level PII inspection
   ↓
local synthetic backend
   ↓
privacy audit
   ↓
remove direct identifiers from outbound view
   ↓
deny-by-default policy
   ↓
final egress PII rescan
   ↓
safe workspace + offline Trust Report
```

**Long Gate v0.2 does not perform cloud/network AI requests.** It may stage an eligible artifact locally, but transmission is intentionally absent.

Row-level synthetic egress remains **fail-closed by default** while stronger privacy validation is still being hardened.

## Safety model

| Data class | Network AI |
|---|---|
| Raw row-level data | **Never** |
| Pseudonymized row-level data | **Never** |
| Synthetic row-level data | **Blocked by default in v0.2** |
| Exact real-data statistics | Computed locally; aggregate result only after guards |
| Direct identifiers | Removed from outbound row view |

There is intentionally no `--force-release` switch.

### Synthetic does not mean every scalar must differ

A generated PHQ score of `7` may coincide with a source score of `7`. The privacy objective is not arbitrary cell inequality; it is preventing source-record reuse, deterministic mappings, linkable rare combinations, identifier reuse, and near-copy records.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .

longgate doctor
longgate inspect examples/demo.csv
longgate run examples/demo.csv --backend auto
```

`auto` prefers an installed mature local backend and falls back to `demo`. The demo backend can exercise the pipeline but can never pass row-level egress.

Optional capabilities:

```bash
pip install -e '.[mostlyai]'
pip install -e '.[synthcity]'
pip install -e '.[presidio]'
pip install -e '.[stats]'
pip install -e '.[mcp]'
```

## Purpose-bound disclosure

Long Gate separates “help me understand the dataset” from “compute the official result”:

```text
schema/types         → schema metadata only
exploration          → synthetic path
exact statistics     → local executor → guarded aggregate
unknown purpose      → BLOCK
```

Examples:

```bash
longgate purpose regression
longgate exact study.csv describe
longgate exact study.csv correlation
longgate exact study.csv group-summary --group-by group --value score
longgate exact study.csv ols --outcome score --predictor age --predictor group
```

Exact-stat guards include identifier exclusion, minimum dataset size, small-group suppression, rare categorical-level blocking, and a final aggregate PII scan.

## Synthetic backends

Long Gate treats generators as replaceable adapters:

- `demo` — development-only; never egress eligible.
- `synthcity` — local SynthCity adapter; direct identifiers are removed before training; v0.2 still blocks row-level egress.
- `mostlyai` — MOSTLY AI local-mode adapter; direct identifiers are removed before training; v0.2 still blocks row-level egress.

Long Gate does not claim that synthetic data is automatically anonymous.

## Trust Report

Every pipeline run creates local provenance artifacts such as:

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

The self-contained HTML report uses no CDN, remote fonts, analytics, or network assets. It shows counts, hashes, decisions, privacy checks, identifier removal, and egress-scan status — not source row values.

## Agent boundary

The future network-facing interface uses a separate `SafeWorkspace` capability. Absolute paths and path traversal are rejected.

An optional FastMCP server exposes only:

- `gate_info`
- `list_safe_files`
- `read_safe_text(relative_path)`

It deliberately does **not** expose arbitrary shell/Python execution or a raw-file path tool.

See [docs/agent-boundary.md](docs/agent-boundary.md) and [docker-compose.hardened.yml](docker-compose.hardened.yml).

## Security CI

Pushes and pull requests are checked with:

- unit + privacy invariant tests;
- CodeQL;
- Bandit;
- pip-audit;
- Trivy;
- CycloneDX SBOM generation;
- Dependabot.

See [docs/security-invariants.md](docs/security-invariants.md).

## Architecture and threat model

- [Architecture](docs/architecture.md)
- [Threat model](docs/threat-model.md)
- [Security invariants](docs/security-invariants.md)
- [Agent boundary](docs/agent-boundary.md)
- [Roadmap](ROADMAP.md)

## What Long Gate does not yet claim

- no formal anonymity or differential-privacy proof from the orchestration layer;
- no production certification for row-level synthetic egress;
- no semantic privacy guarantee for free text, PDFs, images, or audio;
- no legal/compliance certification;
- no protection against a compromised host OS or administrator.

Free-text columns remain local-only/block-by-default in the structured pipeline.

## License

Long Gate's own code is Apache-2.0. Third-party projects retain their respective licenses. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
