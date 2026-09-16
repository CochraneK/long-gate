# Privacy profiles

Long Gate includes engineering presets so thresholds are explicit and reproducible.

They are **not compliance labels**.

A profile named `clinical` does not imply HIPAA, GDPR, NHS, medical-device, ethics-board, or other certification.

## Built-in presets

| Profile | Minimum N | Minimum group | Rare-combination k | Max near-copy rate | Row-level synthetic egress |
|---|---:|---:|---:|---:|---|
| research | 10 | 5 | 5 | 2.0% | blocked |
| clinical | 30 | 10 | 10 | 1.0% | blocked |
| enterprise | 20 | 10 | 10 | 1.5% | blocked |

Inspect them with:

```bash
longgate profiles
```

Use a profile:

```bash
longgate run study.csv --profile clinical
longgate exact study.csv describe --profile clinical
```

## Why presets?

Thresholds hidden in source code are difficult to review and reproduce.

Profiles make the decision surface visible in:
- CLI arguments;
- manifests;
- provenance;
- Trust Reports;
- tests.

Organizations should replace or extend these defaults through reviewed policy rather than treating them as universal safety thresholds.
