# Changelog

All notable changes to Long Gate will be documented here.

The project is currently **pre-1.0**. Security behavior may become stricter between minor versions.

## [Unreleased]

### Added
- SafeWorkspace and a minimal FastMCP boundary.
- Purpose-bound disclosure routing.
- Local exact-statistics path with aggregate guards.
- Value-level PII scanning and final egress rescanning.
- MOSTLY AI and SynthCity adapters.
- Offline Trust Report v2.
- CodeQL, Bandit, pip-audit, Trivy, SBOM, and Dependabot workflows.

### Security
- Direct identifiers are excluded from supported synthetic-model training.
- Direct identifier columns are removed from outbound row views.
- Unknown purposes default to BLOCK.
- Row-level synthetic egress remains fail-closed by default.

## [0.1.0]

Initial structured-data trust-loop scaffold.
