# Contributing to Long Gate

Long Gate welcomes contributions, especially from privacy, security, statistics, research-software, synthetic-data, and agent-tooling communities.

## Before writing code

Long Gate prefers **integration over reinvention**.

Before implementing a new privacy algorithm, ask:

1. Does a mature upstream project already implement it?
2. Can Long Gate expose it through a small adapter?
3. What new raw-data, filesystem, process, or network capability would this introduce?
4. What failure should become a regression test?

New integrations should normally use lazy imports and document upstream licenses.

## Local setup

```bash
git clone https://github.com/CochraneK/long-gate.git
cd long-gate

python -m venv .venv
source .venv/bin/activate

pip install -e '.[dev]'
pytest -q
ruff check src tests
```

Use only synthetic/minimal data in tests and bug reports.

## High-value contribution areas

- membership-inference and linkage attacks
- DP-capable backend adapters
- multilingual / Chinese PII detection
- local R and statistical-model executors
- semantic privacy evaluation for narratives
- sandbox / capability-boundary testing
- adversarial benchmark fixtures
- Trust Report UX
- provenance and reproducible research
- documentation for realistic threat models

## Security-sensitive changes

A PR must include tests when it changes any of these:

- egress behavior
- release policy
- privacy thresholds
- filesystem access
- network capability
- PII detection
- synthetic backends
- exact-stat output
- MCP tools
- logs or Trust Report contents

The default-deny posture must remain intact.

## Pull requests

Keep PRs focused. Explain:

- the problem;
- the threat model;
- the new capability;
- the failure mode;
- the test that proves the invariant.

The PR template includes a security checklist.

## Privacy reviews

If the most important part of your proposal is a privacy failure mode rather than code, open a **Privacy / threat-model review** issue.

## Do not upload sensitive data

Real participant, patient, employee, student, customer, or internal datasets do not belong in public issues or PRs.

A privacy project should not require contributors to leak data in order to report a bug.
