# Long Gate Status

**Activity:** Active  
**Phase:** pre-1.0 hardening  
**Current focus:** security observability + project continuity / bilingual public surface  
**Canonical capability state:** `../project-status.json`

## Established

- local-first structured privacy workflow;
- raw/pseudonymized row-level data remain network-ineligible;
- row-level synthetic egress is hard-locked pre-1.0;
- purpose + SHA-256-bound structured egress approval;
- narrow SafeWorkspace/MCP boundary;
- capability-separated setup/private/network deployment;
- local model setup and verified Model Vault;
- format-preserving document de-identification;
- local semantic abstraction remains local-only;
- secret scan, endpoint provenance, local HAR inspection, and quarantine baseline are implemented on the current security-observability branch.

## Current gate

The security-observability + continuity/README change set must pass the normal test, security-boundary, security-audit, release-readiness, benchmark, and CodeQL workflows before merge.

## Blocker

No product-design blocker is known. Any failing CI job is treated as an implementation blocker and should be fixed rather than bypassed.
