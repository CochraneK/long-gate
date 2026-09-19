# Long Gate Continuity & Agent Handoff Standard · v1

**Effective:** 2026-09-19  
**Scope:** Long Gate repository development, review, release preparation, and security-boundary changes.

Long Gate treats Git as the canonical cross-session, cross-device, cross-account, and cross-agent state. A feature is not operationally complete if another maintainer or agent can see the code but cannot reconstruct the current security posture, pending work, important decisions, validation state, and next action.

## Required handoff package

```text
handoff/
├── README.md
├── STATUS.md
├── TODO.md
├── DECISIONS.md
├── CONTEXT.md
├── CHATLOG.md
├── AGENT_HANDOFF.md
└── SESSION_LOG.md
```

The handoff package summarizes canonical sources. It never overrides code, executable tests, security invariants, or release artifacts.

## Canonical-source rule

- Product capability state: `project-status.json`
- Security requirements: `docs/security-invariants.md`
- Threat assumptions: `docs/threat-model.md`
- Product direction: `ROADMAP.md`
- Runtime truth: `src/longgate/` + tests
- Release history: `CHANGELOG.md`
- Cross-agent continuity: `handoff/`

When these disagree, fix the stale summary rather than treating the handoff package as a second technical truth.

## Cold-start read order

1. `handoff/README.md`
2. `handoff/AGENT_HANDOFF.md`
3. `handoff/STATUS.md`
4. `handoff/TODO.md`
5. `handoff/DECISIONS.md`
6. `handoff/CHATLOG.md`
7. referenced code/tests/security documents

## Checkpoint rule

After a bounded unit changes a security boundary, product capability, release posture, architecture, blocker, or next action:

1. update canonical code/tests/docs first;
2. update `project-status.json` if capability state changed;
3. synchronize handoff status and immediate next action;
4. record material decisions;
5. append a public-safe conversation summary when useful;
6. append validation/commit details to the session log;
7. commit before intentionally switching execution context.

## Public-repository safety

Continuity must never leak what Long Gate exists to protect.

Do not commit:

- API keys, tokens, cookies, credentials, private signing keys;
- captured raw prompts, HAR bodies, Authorization values, or sensitive datasets;
- unnecessary personal information;
- hidden model chain-of-thought;
- confidential third-party content.

Use concise public-safe summaries. Git continuity is a control plane, not a data lake.

## Completion gate

A meaningful Long Gate milestone is continuity-complete only when:

- code and tests represent the claimed capability;
- README claims are supported by canonical status/evidence;
- no handoff P0 contradicts the declared state;
- another agent can identify the next action without relying on a private chat.
