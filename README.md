# Long Gate

**Local-first privacy orchestration for safe AI data access.**

> Transform locally. Verify completely. Cross safely.

Long Gate is a privacy control plane between sensitive local data and networked AI. It does **not** ask a cloud model to "please ignore" private files. Instead, it is designed around a stronger boundary:

- software that can read source data should run locally;
- networked AI should never receive raw or pseudonymized row-level data;
- row-level exports must be synthetic, audited, and explicitly allowed by policy;
- exact computation can stay local and expose only safe aggregate results;
- every run produces a self-contained offline **Trust Report** showing what happened.

## Why Long Gate?

The name combines the idea of a gate with the long defensive boundary of walls, passes, and checkpoints. The project is not a new synthetic-data model. It is the gatekeeper and orchestrator around existing privacy technologies.

## v0.2 scope

Long Gate v0.2 focuses on **structured data**: CSV, XLSX, JSON, and Parquet.

```text
source file
   ↓
local schema + sensitivity inspection
   ↓
synthetic backend adapter
   ↓
privacy audit
   ↓
deny-by-default policy
   ↓
safe payload staging
   ↓
offline Trust Report
```

Important: **v0.2 never performs a network request.** Even when a dataset passes, Long Gate only stages `safe_payload.json`. Cloud-agent integration comes after the isolation and egress contracts are hardened.

## Safety model

Long Gate distinguishes four release classes:

| Class | Network AI |
|---|---|
| Raw row-level data | **Never** |
| Pseudonymized row-level data | **Never** |
| Audited synthetic row-level data | Eligible after policy approval |
| Safe aggregates | Eligible after egress scan |

The policy is deny-by-default. There is intentionally no `--force-release` switch.

### "Every value is synthetic" does not mean "no scalar may ever coincide"

A generated PHQ score of `7` may coincide with a source score of `7` simply because the domain contains only a small number of possible values. The relevant security goal is to prevent source-record reuse, deterministic identity mappings, and linkable row-level copies. Long Gate therefore audits row overlap, source identifier overlap, near-copy risk, and linkage-related structure rather than requiring every scalar to be numerically unique.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .
longgate doctor\nlonggate inspect examples/demo.csv\nlonggate run examples/demo.csv --backend auto
```

The default `auto` mode prefers an installed mature local backend and otherwise falls back to `demo`. The `demo` backend exercises the full pipeline but is **never allowed through the egress gate**.

To use the SynthCity adapter:

```bash
pip install -e '.[synthcity]'
longgate run examples/demo.csv --backend synthcity
```

You can select another SynthCity plugin:

```bash
longgate run examples/demo.csv --backend synthcity:ctgan
```

## Trust Report

Every run creates:

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

If the privacy gate passes, `egress/safe_payload.json` is also staged locally.

The HTML report is deliberately self-contained: no CDN, analytics, remote fonts, or external assets. It contains schema and audit metadata, not source row values.

## Backends

Long Gate treats generators as adapters, not project identity.

- `demo` — lightweight local demonstration backend. **Never eligible for egress.**
- `synthcity` — adapter to the Apache-2.0 SynthCity project for joint-distribution synthesis.
- planned adapters — MOSTLY AI, DP/twin backends, and organization-specific generators.

The orchestration layer remains stable if any one synthetic-data engine changes.

## What Long Gate does not claim

Long Gate does not claim that synthetic data is automatically anonymous. The v0.1 audit is an engineering safeguard, not a formal privacy proof. For high-risk datasets, use a privacy backend with explicit guarantees and organization-specific review.

Free-text columns are blocked from network release in v0.1. A future local semantic path will handle interview text and documents separately.

## Architecture

See [docs/architecture.md](docs/architecture.md) and [docs/threat-model.md](docs/threat-model.md).

## License

Long Gate's own code is Apache-2.0. Third-party projects remain under their respective licenses. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).


## Purpose-bound disclosure

Long Gate separates exploration from official inference:

```text
schema question      -> schema metadata only
exploration          -> synthetic twin path
exact statistics     -> local executor -> aggregate result
unknown purpose      -> BLOCK
```

Local exact examples:

```bash
longgate exact study.csv describe
longgate exact study.csv correlation
longgate exact study.csv group-summary --group-by group --value score
longgate exact study.csv ols --outcome score --predictor age --predictor group
```

Identifier columns are excluded from released numeric summaries. Small groups are suppressed.

## Security CI

Every push/PR runs a security baseline including CodeQL, Bandit, pip-audit, Trivy, SBOM generation, dependency updates, and Long Gate's own executable privacy invariants.

See [docs/security-invariants.md](docs/security-invariants.md).
