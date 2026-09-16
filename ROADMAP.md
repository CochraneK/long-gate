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
- CodeQL / Bandit / pip-audit / Trivy / SBOM / Dependabot

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

Still open:
- broader reviewed statistical model adapters
- key-backed signatures for provenance

## v0.4 — agent capability boundary baseline ✅

- SafeWorkspace
- traversal / absolute-path protection
- hardened local-vs-network Compose example
- minimal FastMCP safe-file surface
- no arbitrary shell / Python / raw-path tools
- separate model-setup capability zone
- private worker Model Vault read-only mount

Still open:
- explicit request / approval contracts
- outbound call ledger
- stronger process-level adversarial tests

## v0.5 — unstructured privacy baseline ✅ / semantic path active

Implemented:
- local TXT / Markdown inspection
- DOCX / PDF text-layer inspection
- PII-count reporting without matched values
- local preview redaction
- in-process local GGUF semantic preview
- PII / numeric-token / long-copy audit
- free text remains network-blocked
- curated Model Vault
- one-command local model setup
- copyable AI setup prompt

Still open:
- semantic-safe release criteria
- stronger semantic identity / rare-event attacks
- scanned-PDF OCR privacy path
- image / audio privacy paths

## v0.6 — adversarial evaluation & release hardening (active)

Implemented:
- non-dead-end release ladder: synthetic → aggregate → local-only
- machine-readable blocker codes + remediation actions
- k-anonymity-style equivalence-class diagnostics
- distance-based membership diagnostic
- auxiliary-data linkage diagnostic
- synthetic benchmark fixture
- benchmark CI + machine-readable artifacts
- research / clinical / enterprise engineering profiles
- explicit threshold documentation
- release-readiness CI
- wheel / sdist / clean-venv smoke installation
- curated model supply-chain pins: immutable upstream revision + SHA-256

Still open:
- stronger membership-inference attacks
- attribute inference
- longitudinal linkage
- organization-defined policy files
- key-backed manifest signatures
- release benchmark comparison tables
- production criteria for any row-level synthetic egress

## v0.7 — production trust research

Planned:
- formal release profiles and policy-as-code
- stronger DP backend evaluation
- signed provenance / attestation
- semantic privacy attack corpus
- approved network-agent request protocol
- reproducible end-to-end red-team scenarios

## Guiding rule

Do not reimplement mature privacy or synthesis algorithms when a suitable upstream project exists.

Long Gate should own:

**orchestration · capability boundaries · policy · audit · egress · provenance · agent permissions**

See [docs/benchmarks.md](docs/benchmarks.md).
