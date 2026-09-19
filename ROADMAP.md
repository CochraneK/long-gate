# Roadmap

Long Gate is developed in layers. **Implemented does not mean privacy-certified.** Production release criteria remain fail-closed until validation is strong enough.

## v0.1 — structured trust loop ✅

- structured CSV / XLSX / JSON / Parquet ingest
- local schema and sensitivity classification
- backend interface
- demo backend permanently blocked from egress
- deny-by-default policy
- offline Trust Report

## v0.2 — hardened structured privacy baseline ✅

- value-level local PII scanning
- optional Presidio integration
- SynthCity adapter
- MOSTLY AI local-mode adapter
- exact-row / identifier / numeric near-copy checks
- rare quasi-identifier overlap checks
- identifier stripping
- final outbound PII rescan
- private-compatible security CI: Bandit / Ruff security rules / pip-audit / Trivy / SBOM / Dependabot

**Release posture:** row-level synthetic egress remains blocked by default, but the workflow now continues through a guarded aggregate fallback instead of ending at a dead-end `BLOCKED` state.

## v0.3 — exact local computation baseline ✅

- purpose-bound disclosure router
- local describe / correlation / group summaries
- local statsmodels OLS
- fixed-template local R describe / OLS
- identifier exclusion
- minimum-N rules
- small-group suppression
- rare categorical-level blocking
- aggregate PII guard
- SHA-256 run provenance + verification
- optional Ed25519 key-backed provenance signatures + verification

## v0.4 — agent capability boundary baseline ✅

- SafeWorkspace
- traversal / absolute-path protection
- hardened local-vs-network Compose example
- minimal FastMCP safe-file surface
- no arbitrary shell / Python / raw-path tools
- separate model-setup capability zone
- private worker Model Vault read-only mount
- explicit request / approval contracts
- outbound call ledger
- capability-based deployment contract validator
- adversarial mutation tests for dangerous process/mount combinations
- manifest-backed artifact approval bound to filename + SHA-256 + purpose

## v0.5 — local AI privacy workflow ✅ / format-preserving document work active

Implemented:
- local TXT / Markdown inspection
- DOCX / PDF text-layer inspection
- PII-count reporting without matched values
- local preview redaction
- in-process local GGUF semantic transformation
- PII / numeric-token / long-copy / distinctive-token audit
- curated Model Vault
- pinned model revision + SHA-256 verification
- local-only hardware advisor
- top-level setup/hardware/deidentify/semantic-summarize workflows
- format-preserving direct-identifier replacement
- bounded semantic remediation loop
- fail-closed local-only outcomes

Still open:
- larger semantic identity / rare-event / relationship attack corpus
- multilingual semantic privacy evaluation
- local speech-content de-identification path

## v0.6 — adversarial evaluation & release hardening (active)

Implemented:
- non-dead-end release ladder
- blocker codes + remediation actions
- membership/linkage diagnostics
- benchmark fixtures and CI artifacts
- research / clinical / enterprise engineering profiles
- release-readiness CI
- model supply-chain verification
- policy files
- signed manifests
- production evidence criteria
- pre-1.0 hard lock for row-level synthetic release

## v0.6.1 — security observability baseline ✅

- explicit local Gitleaks adapter with redacted results
- blocking full-history secret scan
- AI endpoint provenance classification
- custom endpoints marked relay-possible rather than falsely attributed
- local HAR egress inspection
- no-network quarantine contract
- executable quarantine tests

Still open:
- optional local interactive HTTPS inspection/proxy integration
- process-to-socket attribution across Windows/macOS/Linux
- richer provider/ASN provenance evidence
- privacy-safe redacted request preview UI

## v0.6.2 — project continuity & public surface ✅

- bilingual repository surface
- canonical `project-status.json`
- rebuildable bilingual SVG diagrams
- Git-resident public-safe handoff package
- continuity standard and CI evidence audit

## v0.6.3 — process-to-network attribution (active)

Goal:

Add a metadata-only observability layer answering:

> Which local process created this network connection?

Design principles:

- evidence layer only;
- no packet payload collection by default;
- no credential/prompt/body storage;
- observation never grants egress authorization;
- avoid privileged kernel agents in the default path.

Initial scope:

- Linux adapter first;
- PID/executable/socket/destination metadata;
- endpoint provenance integration;
- policy evidence output.

Specification:

- [Process → Network Attribution Design](docs/process-network-attribution.md)

## v0.7 — production trust research

Planned:
- formal release profiles
- stronger DP backend evaluation
- larger semantic privacy attack corpus
- reproducible semantic red-team scenarios
- multilingual rare-event benchmarks
- evidence for any future transition from manual-review candidate to separately policy-authorized semantic egress

## Product stop line

Long Gate should stop adding broad feature families once the user path is reliable:

```text
longgate setup
      ↓
verified local model ready
      ↓
longgate run / deidentify / semantic-summarize
      ↓
privacy audit + local review
      ↓
Trust Report
      ↓
LOCAL_ONLY / MANUAL_REVIEW_CANDIDATE / approved structured artifact
```

## Guiding rule

Do not reimplement mature privacy or synthesis algorithms when suitable upstream projects exist.

Long Gate owns:

**orchestration · capability boundaries · policy · audit · egress · provenance · agent permissions**
