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


## Blocked row-level does not mean blocked workflow

The built-in presets deliberately keep row-level synthetic egress disabled.

When `longgate run` cannot justify row-level release, it does **not** lower the profile thresholds. It moves down the [release ladder](release-ladder.md):

1. keep the synthetic rows local;
2. attempt a guarded aggregate artifact;
3. if that is also inappropriate, remain `LOCAL_ONLY` with machine-readable next actions.

This preserves the privacy posture without turning `BLOCKED` into a user dead end.
