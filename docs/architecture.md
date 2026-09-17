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
6. Exact statistics run locally; identifier variables, small samples, and unsafe aggregate payloads are blocked. Python and fixed-template R engines share the same aggregate guard.
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

The Python API is a **trusted-local interface**. It is intended to be shared by AI-Ques, AI-persona, research tools, and other local orchestration code without giving those projects direct cloud access to raw data.

A return value from `LongGate.inspect()` or `LongGate.exact()` is **not an egress authorization**. In particular, exact statistics remain exact because they are computed and returned inside the trusted local zone. A network-facing agent must not import this API as a shortcut around release policy; it should receive only artifacts in the approved egress workspace through the MCP + hash/purpose approval boundary.


## Exact execution engines

The default exact executor uses Python/pandas/statsmodels.

An optional R engine supports reviewed fixed templates such as descriptive statistics and OLS. It does not accept arbitrary R code from a networked agent.

See [Local R exact executor](r-executor.md).
