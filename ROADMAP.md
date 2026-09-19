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

Still open:
- broader reviewed statistical model adapters

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
- local-only hardware advisor: OS / architecture / CPU / RAM / disk + best-effort NVIDIA GPU/VRAM
- FAST / BALANCED / QUALITY model-fit guidance
- top-level `longgate setup`, `longgate hardware`, `longgate deidentify`, and `longgate semantic-summarize`
- TXT/Markdown/HTML/XLSX format-preserving direct-identifier replacement with stable document-scoped placeholders
- HTML visible-text/selected-attribute traversal with explicit ignored-region reporting
- XLSX all-worksheet traversal including hidden sheets, comments, hyperlinks, and selected workbook metadata
- DOCX OOXML text-node traversal with cross-run direct-identifier replacement and unresolved binary-surface reporting
- cross-file batch entity maps with HMAC-minimized authenticated state and hash-verified resume
- structured local-model entity nomination for names/aliases/organizations/locations/dates/projects/roles/events/quasi-identifiers with exact-literal validation and controlled replacement
- source-overwrite rejection, source-hash consistency checks, and atomic local output writes
- deterministic pre-scrub before semantic transformation
- fail-closed detection of token-limit-truncated local model completions
- bounded semantic remediation loop (maximum three local model rounds)
- fail-closed `MANUAL_REVIEW_CANDIDATE` / `LOCAL_ONLY` outcomes
- offline Semantic Trust Report without source/transformed narrative content
- free text remains network-blocked; a manual-review candidate is not an egress authorization
- scanned-PDF local OCR privacy path
- image metadata + local OCR privacy path
- WAV audio metadata privacy path
- copyable AI setup prompt

Still open:
- larger semantic identity / rare-event / relationship attack corpus
- multilingual semantic privacy evaluation
- privacy-aware long-document segmentation + cross-chunk consistency audit
- local speech-content de-identification path

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
- bounded ensemble membership-inference diagnostics
- attribute inference
- exact + fuzzy longitudinal linkage
- organization-defined policy files
- key-backed manifest signatures
- machine-readable + Markdown cross-attack comparison tables
- executable production evidence criteria for row-level synthetic egress
- pre-1.0 hard lock: criteria can pass, but row-level release remains disabled

Still open:
- shadow-model membership inference where justified
- stronger DP-backend evaluation

## v0.6.1 — security observability baseline ✅

- explicit local Gitleaks adapter with redacted machine-readable results
- blocking full-history Gitleaks CI
- AI endpoint provenance classification with optional DNS/TLS evidence
- custom/unknown endpoints marked relay-possible rather than falsely attributed
- local HAR egress inspection with PII/sensitive-header/query counts and no payload echo
- dedicated no-network, non-root, resource-bounded quarantine Compose contract
- executable quarantine contract tests

Still open:
- optional local interactive HTTPS inspection/proxy integration
- process-to-socket attribution across Windows/macOS/Linux
- richer provider/ASN provenance evidence
- privacy-safe redacted request preview UI

## v0.7 — production trust research

Planned:
- formal release profiles and policy-as-code beyond the current JSON profile baseline
- stronger DP backend evaluation
- larger semantic privacy attack corpus
- reproducible end-to-end semantic red-team scenarios
- multilingual rare-event / relationship / combination-uniqueness benchmarks
- evidence for any future transition from manual-review candidate to a separately policy-authorized semantic egress path

## Product stop line

Long Gate should stop adding broad new feature families once this user path is reliable:

```text
longgate setup
      ↓
verified local model ready
      ↓
longgate run / longgate deidentify / longgate semantic-summarize
      ↓
privacy audit + local review / bounded remediation
      ↓
Trust Report
      ↓
LOCAL_ONLY / MANUAL_REVIEW_CANDIDATE / approved structured artifact
      ↓
when supported: explicit local approval → narrow MCP → network AI
```

After that point, development should be driven primarily by real usage, red-team evidence, and clearly scoped adapters rather than feature accumulation.

## Guiding rule

Do not reimplement mature privacy or synthesis algorithms when a suitable upstream project exists.

Long Gate should own:

**orchestration · capability boundaries · policy · audit · egress · provenance · agent permissions**

See [docs/benchmarks.md](docs/benchmarks.md).
