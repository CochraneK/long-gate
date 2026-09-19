# Long Gate TODO

## P0 — next gate

- [x] Get PR #35 and its continuity/README follow-up fully green.
- [x] Merge only after required CI/security workflows pass.
- [x] Refresh handoff after merge so the canonical state points to `main`.
- [ ] Keep the post-merge `main` checkpoint green.
- [ ] Run repo-auditor against the merged baseline and fix only material findings.

## P1 — security observability follow-up

- [ ] Add optional process-to-socket/network attribution with platform-specific adapters.
- [ ] Evaluate explicit opt-in HTTPS inspection integration without making Long Gate privileged by default.
- [ ] Add richer endpoint provenance evidence while preserving UNKNOWN when upstream cannot be proven.
- [ ] Add privacy-safe request preview UX without persisting sensitive bodies by default.

## P1 — product quality

- [ ] Keep `project-status.json` aligned with executable evidence.
- [ ] Keep bilingual README visuals rebuildable from repository state.
- [ ] Exercise the handoff package from a cold-start agent perspective after major milestones.

## P2 — research / hardening

- [ ] Larger multilingual semantic identity / rare-event / relationship attack corpus.
- [ ] Stronger DP-backend evaluation.
- [ ] Real-usage red-team scenarios before broadening release policy.
