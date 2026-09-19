# Long Gate · Agent Instructions

Long Gate is a security/privacy boundary. Treat repository claims as executable contracts, not marketing copy.

## Cold start

Read in this order:

1. `handoff/README.md`
2. `handoff/AGENT_HANDOFF.md`
3. `handoff/STATUS.md`
4. `handoff/TODO.md`
5. `project-status.json`
6. `docs/security-invariants.md`
7. `docs/threat-model.md`
8. code/tests relevant to the task

## Non-negotiable product rules

- A component that can read raw private data must not also receive unrestricted network access.
- Raw and pseudonymized row-level data are network-ineligible.
- Row-level synthetic egress remains fail-closed pre-1.0.
- Semantic de-identification output remains local-only in the current baseline.
- Evidence never creates authorization by itself.
- Do not add a force-release escape hatch.
- Unknown/custom AI endpoints may be relay-possible; do not invent the hidden upstream provider.
- Do not echo secrets, Authorization values, cookies, captured request bodies, or matched PII in security-observability reports.
- BLOCKED should produce safe next actions when possible, not silent policy relaxation.

## Before changing a security boundary

Read the relevant invariant and tests first. Update code + tests + documentation together.

If capability maturity changes, update `project-status.json`.

## Validation

At minimum run:

```bash
pytest -q
ruff check src tests research tools
python tools/build_readme.py
python tools/build_readme_assets.py
python tools/audit_project_continuity.py
```

Security-sensitive changes should also be allowed to pass the repository's security-boundary, security-audit, release-readiness, benchmark, and CodeQL workflows.

## Checkpoint

A material bounded work unit is not complete while its state exists only in chat.

Update canonical files first, then synchronize the public-safe `handoff/` package according to `LONG_GATE_CONTINUITY_STANDARD.md`.
