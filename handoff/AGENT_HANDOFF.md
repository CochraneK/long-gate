# Long Gate · Immediate Agent Handoff

## Mission

Continue hardening Long Gate as a local-first privacy boundary for AI workflows without weakening the core capability separation.

## Current work

The active branch is `security-observability-v1`, associated with PR #35. It adds:

- local/redacted Gitleaks integration + full-history CI;
- AI endpoint provenance classification;
- local privacy-aware HAR inspection;
- a no-network quarantine contract;
- ARIS4C-inspired continuity and bilingual README infrastructure.

## Immediate next action

1. finish the continuity/README implementation;
2. run/read all PR CI results;
3. fix failures instead of bypassing checks;
4. merge only when the change set is green;
5. update handoff status after merge.

## Do not

- do not claim a hidden upstream AI provider from client-side endpoint evidence alone;
- do not log raw Authorization/API key/cookie/request-body content in observability reports;
- do not give quarantine network access by default;
- do not add a force-release escape hatch;
- do not turn repo-auditor-style repository auditing into Long Gate runtime code;
- do not make README security claims that lack code/test evidence.

## Canonical files

- `project-status.json`
- `docs/security-invariants.md`
- `docs/threat-model.md`
- `ROADMAP.md`
- `src/longgate/`
- `tests/`

## Continuity

At the end of a material work unit, update the relevant canonical file first, then synchronize handoff status/TODO/decisions/session log.
