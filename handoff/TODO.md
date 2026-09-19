# Long Gate TODO

## P0 — next gate

- [ ] Get PR #35 and its follow-up continuity/README commits fully green.
- [ ] Merge only after required CI/security workflows pass.
- [ ] After merge, refresh this handoff so it no longer describes the feature branch as pending.

## P1 — security observability follow-up

- [ ] Add optional process-to-socket/network attribution with platform-specific adapters.
- [ ] Evaluate explicit opt-in HTTPS inspection integration without making Long Gate privileged by default.
- [ ] Add richer endpoint provenance evidence while preserving UNKNOWN when upstream cannot be proven.
- [ ] Add privacy-safe request preview UX without persisting sensitive bodies by default.

## P1 — product quality

- [ ] Keep `project-status.json` aligned with executable evidence.
- [ ] Keep bilingual README visuals rebuildable from repository state.
- [ ] Run repo-auditor after the current PR reaches a stable green state.

## P2 — research / hardening

- [ ] Larger multilingual semantic identity / rare-event / relationship attack corpus.
- [ ] Stronger DP-backend evaluation.
- [ ] Real-usage red-team scenarios before broadening release policy.
