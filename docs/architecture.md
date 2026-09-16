# Architecture

## Two trust zones

```text
TRUSTED LOCAL ZONE

Raw data
  ↓
Schema + value-level PII inspection
  ↓
Purpose router
  ├──────── exploration ───────→ synthetic backend → privacy audit
  └──────── exact inference ───→ local exact executor
                                      ↓
                               aggregate guard
                                      ↓
                             deny-by-default policy
                                      ↓
                          remove direct identifiers
                                      ↓
                           final egress PII rescan
                                      ↓
                               safe workspace

==================== LONG GATE / NETWORK BOUNDARY ====================

NETWORK AI ZONE

SafeWorkspace / MCP tools only
No raw filesystem capability
```

The diagram source is also available in [architecture.mmd](architecture.mmd).

## Core invariants

1. Raw and pseudonymized row-level data are never network eligible.
2. The cloud worker must not receive a filesystem mount containing raw data.
3. The local worker runs with `network_mode: none` in the hardened deployment.
4. Row-level synthetic backends remain fail-closed in v0.2.
5. Direct identifiers are excluded from supported synthetic-model training and removed from outbound row views.
6. Exact statistics run locally; identifier variables, small samples, and unsafe aggregate payloads are blocked.
7. Policy approval is followed by a final egress PII rescan.
8. Audit/scanner failures are fail-closed.
9. Trust Reports never embed source row values.
10. Long Gate v0.2 performs no cloud API transmission.

## Adapter boundary

Synthetic engines implement a stable interface:

```python
class SyntheticBackend:
    name: str
    certified_for_egress: bool
    def generate(df, profiles, seed): ...
```

Third-party generators are plugins, not Long Gate's identity.

## Programmatic API

```python
from longgate import LongGate

gate = LongGate()
inspection = gate.inspect("study.csv")
decision = gate.route("regression")
result = gate.exact(
    "study.csv",
    "ols",
    outcome="score",
    predictors=["age", "group"],
)
```

The API is intended to be shared by AI-Ques, AI-persona, research tools, and future agents without giving those projects direct cloud access to raw data.
