# Changelog

## Unreleased

- Add hash-bound egress approvals and purpose-scoped MCP reads with an observational access log.

- Add a non-dead-end release ladder: row-level synthetic rejection now falls back to guarded aggregate output or explicit local-only next actions.
- Add machine-readable privacy blocker codes and remediation guidance.

All notable changes to Long Gate will be documented here.

The project is currently **pre-1.0**. Security behavior may become stricter between minor versions.

## [Unreleased]

### Added
- SafeWorkspace and minimal FastMCP boundary.
- Purpose-bound disclosure routing.
- Local exact-statistics path with aggregate guards.
- Fixed-template local R describe / OLS engine.
- Value-level PII scanning and final egress rescanning.
- MOSTLY AI and SynthCity adapters.
- Privacy profiles: research, clinical, enterprise.
- SHA-256 run provenance and `verify-run`.
- k-anonymity-style, membership, and auxiliary-linkage diagnostics.
- Reproducible synthetic benchmark CI with JSON artifacts.
- Local TXT / Markdown / DOCX / PDF inspection.
- Local GGUF semantic preview with copy-risk audit.
- Curated Qwen3 Model Vault.
- RAM-aware `longgate model setup`.
- Immutable Hugging Face revision + SHA-256 model verification.
- `--model auto` verified default-model resolution.
- Copyable `longgate setup-prompt` for AI-assisted machine setup.
- Windows PowerShell and macOS/Linux bootstrap guides/scripts.
- Public synthetic-only Safe Demo.
- Offline Trust Report v2.
- CodeQL, Bandit, pip-audit, Trivy, SBOM, Dependabot, release-readiness workflows.

### Security
- Direct identifiers are excluded from supported synthetic-model training.
- Direct identifier columns are removed from outbound row views.
- Unknown purposes default to BLOCK.
- Row-level synthetic egress remains fail-closed by default.
- Free text and semantic previews remain local-only.
- Model setup has network capability but no private-data input path.
- Private semantic processing resolves an already-local verified model.
- Curated model downloads are pinned to immutable upstream revisions and file SHA-256.

### Changed
- Local model onboarding moved from manual GGUF selection to a curated Model Vault with one-command setup.
- Model installation now preflights disk space and moves staged GGUF files into place instead of duplicating them.
- README and docs emphasize capabilities over prompt-only privacy controls.

## [0.1.0]

Initial structured-data trust-loop scaffold.
