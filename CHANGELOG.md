# Changelog

All notable changes to Long Gate will be documented here.

The project is currently **pre-1.0**. Security behavior may become stricter between minor versions.

## [Unreleased]

### Added
- Hash-bound egress approvals and purpose-scoped MCP reads with an observational access log.
- Versioned egress manifests that bind eligible artifacts to their exact filename and SHA-256 before local approval.
- End-to-end README user journeys, command chooser, MCP handoff walkthrough, and Mermaid flow diagrams for real-world use.
- Non-dead-end release ladder: rejected row-level synthetic output falls back to guarded aggregate output or explicit local-only next actions.
- Machine-readable privacy blocker codes and remediation guidance.
- Attribute-inference and exact/fuzzy longitudinal-linkage diagnostics.
- Bounded ensemble membership-inference diagnostics and cross-attack benchmark comparison tables.
- Fail-closed semantic release-evidence criteria with distinctive-token reuse checks.
- Executable row-level production evidence criteria; pre-1.0 remains hard-locked against automatic row-level release.
- Local image metadata, image OCR, scanned-PDF OCR, and WAV metadata privacy paths.
- Capability-based deployment contract validation with adversarial mutation tests.
- Optional Ed25519 provenance signatures and signature-aware verification.
- SafeWorkspace and minimal FastMCP boundary.
- Purpose-bound disclosure routing.
- Local exact-statistics path with aggregate guards.
- Fixed-template local R describe / OLS engine.
- Value-level PII scanning and final egress rescanning.
- MOSTLY AI and SynthCity adapters.
- Privacy profiles: research, clinical, enterprise.
- SHA-256 run provenance and `verify-run`, including aggregate fallback artifacts.
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
- Offline Trust Report v2.
- Private-compatible security CI with Bandit, Ruff security rules, pip-audit, Trivy, SBOM, Dependabot, and release-readiness workflows.

### Security
- Direct identifiers are excluded from supported synthetic-model training.
- Direct identifier columns are removed from outbound row views.
- Unknown purposes default to BLOCK.
- Row-level synthetic egress remains fail-closed by default.
- Free text, semantic previews, OCR output, images, and audio remain local-only by default.
- Passing semantic or row-level evidence criteria never auto-authorizes egress.
- `approve-egress` now rejects arbitrary safe-workspace files unless they are backed by a matching policy-approved Long Gate egress manifest and exact artifact digest.
- Model setup has network capability but no private-data input path.
- Private semantic processing resolves an already-local verified model.
- Curated model downloads are pinned to immutable upstream revisions and file SHA-256.

### Changed
- Retired CodeQL as a required gate after the repository became private; equivalent available local/static security checks remain blocking in CI.
- Retired the public Railway Safe Demo and removed deployable demo assets from the repository.
- Local model onboarding moved from manual GGUF selection to a curated Model Vault with one-command setup.
- Model installation now preflights disk space and moves staged GGUF files into place instead of duplicating them.
- README and Getting Started now lead with concrete user tasks, expected outputs, explicit egress approval, and the network-agent handoff instead of architecture-first documentation.

## [0.1.0]

Initial structured-data trust-loop scaffold.