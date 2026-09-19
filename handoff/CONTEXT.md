# Long Gate Context

## What the project is

Long Gate is a local-first privacy gateway and capability boundary for AI workflows.

Its central rule is:

> If a networked AI should not see raw data, do not give it the capability to see raw data.

## Core architecture

```text
SETUP ZONE
network yes · private data no · Model Vault write
        ↓ verified model
PRIVATE ZONE
private data yes · network no · Model Vault read-only
        ↓ audited / minimized artifact
LONG GATE
policy · manifest · purpose · hash · local approval
        ↓
SAFE WORKSPACE
approved artifact only
        ↓
NETWORK ZONE
narrow MCP / network AI
```

A separate quarantine zone exists for suspicious input and has no network.

## Important release posture

- raw row-level: blocked;
- pseudonymized row-level: blocked;
- row-level synthetic: hard-locked pre-1.0;
- semantic de-identification: local-only baseline;
- supported structured aggregate: explicit manifest + hash + purpose approval.

## Security observability terminology

- **official endpoint:** known provider-controlled API hostname;
- **router/aggregator:** known multi-provider routing service;
- **custom/unknown endpoint:** relay-possible, not proof of relay/upstream identity;
- **HAR inspector:** local metadata/sensitive-class analysis, not a general packet sniffer;
- **quarantine:** restricted capability zone, not a VM/kernel security guarantee.

## Product rule

BLOCKED should lead to a safer next action where one exists. Long Gate must not silently weaken a privacy boundary just to produce an output.
