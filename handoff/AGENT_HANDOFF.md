# Long Gate · Immediate Agent Handoff

## Mission

Continue hardening Long Gate as a local-first privacy boundary for AI workflows without weakening the core capability separation.

## Current state

The security-observability + continuity/public-surface baseline from PR #35 is merged to `main`.

It includes:

- local/redacted Gitleaks integration + full-history CI;
- AI endpoint provenance classification;
- local privacy-aware HAR inspection;
- a no-network quarantine contract;
- Chinese-default + full English README;
- rebuildable bilingual SVGs from canonical project state;
- `project-status.json`, `AGENTS.md`, and a public-safe Git-resident handoff package;
- CI continuity/evidence auditing.

The PR head passed test, security-boundary, release-readiness, benchmark-smoke, CodeQL, and security-audit before merge.

## Immediate next action

1. verify the post-merge `main` checkpoint remains green;
2. run repo-auditor on the merged baseline;
3. treat only material findings as blockers;
4. then take one bounded next security-observability unit, preferably process-to-socket/network attribution.

## Do not

- do not claim a hidden upstream AI provider from client-side endpoint evidence alone;
- do not log raw Authorization/API key/cookie/request-body content in observability reports;
- do not give quarantine network access by default;
- do not add a force-release escape hatch;
- do not turn repo-auditor-style repository auditing into Long Gate runtime code;
- do not make README security claims that lack code/test evidence;
- do not add privileged packet-capture requirements to the default Long Gate path.

## Canonical files

- `project-status.json`
- `docs/security-invariants.md`
- `docs/threat-model.md`
- `ROADMAP.md`
- `src/longgate/`
- `tests/`

## Continuity

At the end of a material work unit, update the relevant canonical file first, then synchronize handoff status/TODO/decisions/session log.
