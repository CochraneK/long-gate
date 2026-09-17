# Changelog

All notable changes to Long Gate will be documented here.

The project is currently **pre-1.0**. Security behavior may become stricter between minor versions.

## [Unreleased]

### Added
- Top-level `longgate setup` product entrypoint that combines local hardware advice with curated Model Vault installation and verification.
- Top-level `longgate hardware` local-only advisor for OS/architecture/CPU/RAM/disk plus best-effort NVIDIA GPU/VRAM detection.
- FAST / BALANCED / QUALITY model-fit guidance while keeping automatic selection conservative and RAM-led.
- Top-level `longgate deidentify` for deterministic pre-scrub, local GGUF semantic transformation, original-source privacy auditing, bounded remediation, and offline Semantic Trust Reports.
- Bounded semantic remediation loop with a maximum of three local model rounds and fail-closed `MANUAL_REVIEW_CANDIDATE` / `LOCAL_ONLY` outcomes.
- Semantic Trust Reports that record hashes, model metadata, per-round privacy evidence, failed conditions, and next actions without embedding source or transformed narrative content.
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
- Semantic de-identification candidates remain local-only even when mechanical evidence qualifies them for manual review.
- Semantic remediation is bounded to at most three rounds and never lowers privacy thresholds automatically.
- Semantic Trust Reports do not copy source or transformed narrative content into the report.
- Hardware inspection has no remote fallback; GPU detection uses only a fixed local `nvidia-smi` query when available.
- Free text, semantic previews, OCR output, images, and audio remain local-only by default.
- Passing semantic or row-level evidence criteria never auto-authorizes egress.
- `approve-egress` rejects arbitrary safe-workspace files unless they are backed by a matching policy-approved Long Gate egress manifest and exact artifact digest.
- Model setup has network capability but no private-data input path.
- Private semantic processing resolves an already-local verified model.
- Curated model downloads are pinned to immutable upstream revisions and file SHA-256.

### Changed
- The installed `longgate` CLI now routes through a product-level entrypoint while preserving all existing advanced commands through the legacy dispatcher.
- README / Chinese README / Getting Started now lead with `longgate setup`, the structured-data path, and the iterative local semantic de-identification path.
- Retired CodeQL as a required gate after the repository became private; equivalent available local/static security checks remain blocking in CI.
- Retired the public Railway Safe Demo and removed deployable demo assets from the repository.
- Local model onboarding moved from manual GGUF selection to a curated Model Vault with one-command setup.
- Model installation preflights disk space and moves staged GGUF files into place instead of duplicating them.

## [0.1.0]

Initial structured-data trust-loop scaffold.
