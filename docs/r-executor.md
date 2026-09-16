# Local R exact executor

Long Gate supports a constrained local R engine for exact analysis.

The design goal is explicit:

> **Use R locally without turning Long Gate into an arbitrary-code execution service.**

## Current fixed analyses

```bash
longgate exact study.csv describe --engine r

longgate exact study.csv ols \
  --engine r \
  --outcome score \
  --predictor age \
  --predictor group
```

R must already be installed locally and `Rscript` must be on `PATH`.

Check with:

```bash
longgate doctor
```

## Security design

The R engine:

- does not accept an R script from the user or networked AI;
- writes only the selected analysis frame to a temporary local directory;
- renames source columns to safe aliases such as `y`, `x0`, and `x1`;
- runs a fixed Long Gate R template with `shell=False`;
- applies identifier / small-N / rare categorical checks in Python first;
- sends the resulting aggregate back through Long Gate's aggregate PII guard;
- inherits the local worker's `network_mode: none` in hardened deployments.

Current R support is intentionally narrow: `describe` and `ols`.

Broader R models should be added as reviewed fixed analysis specifications, not arbitrary script execution.
