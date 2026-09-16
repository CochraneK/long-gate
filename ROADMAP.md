# Roadmap

Long Gate is developed in layers. “Implemented” does not mean “privacy-certified”; release criteria stay fail-closed until validation is strong enough.

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

**Current release posture:** row-level synthetic egress remains blocked by default.

## v0.3 — exact local computation baseline ✅

- purpose-bound disclosure router
- local describe / correlation / group summaries
- local statsmodels OLS
- identifier exclusion
- minimum-N rules
- small-group suppression
- rare categorical-level blocking
- aggregate PII guard

Next:
- R executor
- broader statistical model adapters
- code/provenance hashing

## v0.4 — agent capability boundary baseline ✅

- SafeWorkspace
- traversal / absolute-path protection
- hardened local-vs-network Compose example
- minimal FastMCP safe-file surface
- no arbitrary shell/Python/raw-path tools

Next:
- explicit request/approval contracts
- outbound call ledger
- signed safe manifests
- stronger process-level tests

## v0.5 — unstructured privacy baseline ✅ / semantic path active

Implemented:
- local TXT / Markdown inspection
- PII-count reporting without matched values
- local preview redaction
- free text remains network-blocked

Next:
- local semantic risk model
- identity-detached abstraction
- synthetic narrative evaluation
- DOCX / PDF adapters
- image / audio privacy paths

## v0.6 — adversarial evaluation and release hardening

- membership-inference evaluation
- auxiliary-data linkage tests
- attack corpus with reproducible fixtures
- explicit research / clinical / enterprise policy profiles
- configurable thresholds with rationale
- signed manifests / provenance
- release benchmark tables

## Guiding rule

Do not reimplement mature privacy or synthesis algorithms when a suitable upstream project exists.

Long Gate should own:

**orchestration · capability boundaries · policy · audit · egress · provenance · agent permissions**

See [docs/benchmarks.md](docs/benchmarks.md) for the adversarial evaluation scaffold.
