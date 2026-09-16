# Security policy

Long Gate treats privacy-boundary failures as security issues.

## Reporting a vulnerability

Do not open a public issue containing exploit details if the issue could expose raw/private data, bypass egress policy, escape SafeWorkspace, or create unintended network access.

Use GitHub's private vulnerability-reporting flow when it is available for the repository. If it is not available, contact the maintainer privately through an existing trusted channel before publishing details.

## Never attach real sensitive datasets

Use synthetic/minimal reproductions.

Long Gate maintainers should not need raw research, clinical, HR, student, customer, identity, or internal business data to reproduce an ordinary defect.

## Examples of security-sensitive findings

- raw or pseudonymized rows becoming network eligible;
- a policy or scanner failure that fails open;
- path traversal or symlink escape from SafeWorkspace;
- a cloud/network worker receiving a private-data mount;
- source values appearing in Trust Reports or logs;
- an identifier entering a synthetic backend despite policy;
- small-group or aggregate disclosure;
- MCP tools exposing arbitrary file/shell/code capabilities;
- dependency or workflow compromise that affects the trust boundary.

## Design principle

> A component that can read raw data should not also have unrestricted network egress.

Long Gate's threat model and executable invariants are documented in:

- [docs/threat-model.md](docs/threat-model.md)
- [docs/security-invariants.md](docs/security-invariants.md)

## Scope

Long Gate is pre-1.0 and is not a compliance certification product. Reports that demonstrate a concrete boundary failure are especially valuable.
