# Long Gate Status

**Activity:** Active  
**Phase:** pre-1.0 hardening  
**Current focus:** post-merge validation + next security-observability layer  
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
- secret scan, endpoint provenance, local HAR inspection, and quarantine baseline are on `main`;
- Chinese-default + full English README, generated bilingual SVGs, canonical project status, AGENTS.md, and public-safe cross-agent handoff are on `main`;
- PR #35 was squash-merged after test, security-boundary, release-readiness, benchmark-smoke, CodeQL, and security-audit all passed on the PR head.

## Current gate

Keep the post-merge `main` checkpoint green, then move to the next bounded security-observability unit rather than broad feature accumulation.

## Next focus

Process-to-socket/network attribution is the next concrete observability gap. Any future HTTPS inspection integration must remain explicit opt-in and must not make Long Gate privileged by default.

## Blocker

No known product-design blocker.
