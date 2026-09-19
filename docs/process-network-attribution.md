# Process → Network Attribution Design

## Purpose

Long Gate already knows endpoint evidence and egress policy. This layer adds another evidence dimension:

> Which local process created a network connection?

It is an observability layer, not a packet-content monitor and not an EDR replacement.

## Security boundary

The module must:

- report process/socket/destination metadata;
- avoid collecting request bodies by default;
- avoid storing credentials, cookies, prompts, or payload content;
- never convert observation into egress authorization.

The invariant remains:

```
Evidence != Authorization
```

## Architecture

```
Process
  |
  | PID / executable metadata
  v
Socket observation
  |
  | destination IP + port
  v
DNS / TLS endpoint evidence
  |
  v
Endpoint classification
  |
  v
Policy evaluation
```

## Adapter model

The first implementation should use platform adapters:

```
src/longgate/attribution/

interface.py

linux/
  proc_net.py
  ss_adapter.py

macos/
  lsof_adapter.py

windows/
  netstat_adapter.py
```

A platform adapter may return:

```json
{
  "process": "python",
  "pid": 1234,
  "destination": "api.example.com:443",
  "evidence": "socket metadata",
  "confidence": "medium"
}
```

## Initial implementation scope

Start with metadata-only Linux support:

- process id;
- executable name;
- local address;
- remote address;
- timestamp.

Do not begin with:

- privileged packet interception;
- TLS decryption;
- full traffic capture;
- kernel-level agents.

## Future maturity

planned → research → implemented → hardened

A capability is promoted only when tests demonstrate that the implementation preserves Long Gate's privacy invariants.
