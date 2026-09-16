# Architecture

## Trust zones

Long Gate is designed around two separate trust zones.

```text
TRUSTED LOCAL ZONE

Raw data → Inspector → Synthetic backend → Privacy audit → Policy → Egress staging
                                                          |
                                                          v
                                                   Trust Report

=========================== NETWORK BOUNDARY ===========================

NETWORK AI ZONE (future)

Only a policy-approved payload is mounted or transmitted here.
```

## Core invariants

1. Raw and pseudonymized row-level data are never network-eligible.
2. The cloud worker must not receive a filesystem mount containing raw data.
3. The local worker should run without network access in hardened deployments.
4. A synthetic backend must be explicitly marked egress-eligible; demo/fallback algorithms are blocked.
5. Audit failure is fail-closed.
6. The Trust Report never embeds source row values.
7. Long Gate v0.1 stages but does not transmit network payloads.

## Adapter boundary

Synthetic engines implement one interface:

```python
class SyntheticBackend:
    name: str
    certified_for_egress: bool
    def generate(df, profiles, seed): ...
```

This avoids coupling Long Gate to one third-party generator.

## Future exact-computation path

Formal statistics should not be silently run on synthetic data and presented as source-data results. The target architecture is:

```text
Cloud AI → analysis plan/code → local executor → safe aggregate result → Cloud AI explanation
```

The network model can help reason about the analysis without receiving source rows.
