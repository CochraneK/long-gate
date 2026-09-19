# Long Gate Decision Log

## 2026-09-19 · Git is the continuity source of truth

Long-running Long Gate state must not exist only in a chat. Public-safe status, decisions, next actions, and execution checkpoints are persisted in `handoff/` and canonical project files.

## 2026-09-19 · Bilingual repository surface

The GitHub repository uses Chinese as the default README with a first-class English README. Python package metadata can continue pointing at the English README so package-registry users receive an international-facing description.

## 2026-09-19 · Generated SVG over decorative Mermaid

Core README diagrams should be repository-native SVG generated from canonical project state where practical. Mermaid remains useful in technical docs, but the public README should prioritize readable, purpose-built visuals.

## 2026-09-19 · Observability is not attribution certainty

Endpoint/DNS/TLS evidence may show where a client connects. A custom endpoint can be marked relay-possible, but Long Gate must not claim to know the hidden upstream provider without evidence.

## 2026-09-19 · Captured traffic must not become a second leak

HAR/traffic analysis should report destination metadata, sensitive field names, body sizes, and PII counts without echoing credentials, cookies, query values, matched PII, or raw prompt/request bodies by default.

## 2026-09-19 · Quarantine is a capability zone

Quarantine defaults to no network, non-root, read-only source/root, dropped Linux capabilities, no-new-privileges, bounded tmpfs/resources, and no credential-bearing mounts. It is not marketed as protection against a compromised kernel or host administrator.

## 2026-09-19 · Audit agent vs runtime boundary

Repository-wide multi-stage security review belongs primarily in repo-auditor. Long Gate owns runtime data/AI trust boundaries, egress controls, observability, and quarantine. This avoids turning Long Gate into a generic security-agent kitchen sink.
