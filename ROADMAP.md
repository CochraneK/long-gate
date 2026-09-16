# Roadmap

## v0.1 — structured trust loop ✅

- CSV / XLSX / JSON / Parquet ingest
- local schema and sensitivity classification
- synthetic backend interface
- demonstration backend that is permanently blocked from egress
- SynthCity adapter
- row/identifier/near-copy privacy checks
- deny-by-default policy
- safe-payload staging, no transmission
- self-contained Trust Report HTML
- hardened local-worker Docker target with `network_mode: none`

## v0.2 — hardened structured release (active)

- Presidio/value-level detectors and custom recognizers
- MOSTLY AI adapter and backend capability registry
- stronger linkage, uniqueness, rare-combination and membership-risk metrics
- per-column transformation plan preview
- explicit privacy profiles: research / clinical / enterprise
- signed run manifest and backend/version provenance

## v0.3 — exact local computation loop

- local Python/R executor for real-data statistics
- cloud AI receives schema/synthetic data for planning, then aggregate-only real results
- analysis provenance linking generated code to local result hashes

## v0.4 — agent boundary

- MCP/tool interface for `inspect`, `request_access`, `run_local`, `get_safe_result`
- cloud agent receives no raw filesystem capability
- outbound request interceptor and payload ledger
- container/process-level capability tests

## v0.5 — unstructured data

- local free-text PII/semantic risk detection
- relationship-preserving synthetic narrative generation
- document adapters for DOCX/PDF/TXT
- separate policies for transcripts, clinical notes, and open-ended responses

## Guiding rule

Do not reimplement mature privacy or synthesis algorithms when a suitable upstream project exists. Long Gate should own orchestration, capability boundaries, policy, audit, and provenance.


## Implemented in v0.2 baseline

- value-level PII pattern scanning with count-only reporting
- optional local Presidio scanner
- final outbound PII rescan
- direct identifier removal from outbound row view
- MOSTLY AI local-mode adapter
- purpose-bound disclosure router
- local exact describe / correlation / group summaries / OLS
- small-group suppression and identifier exclusion
- CodeQL / Bandit / pip-audit / Trivy / SBOM / Dependabot
- executable privacy security invariants
- `doctor` capability discovery and `auto` backend selection

Row-level synthetic egress remains intentionally fail-closed until the privacy audit is strengthened further.
