# Vision

## The problem

AI agents are becoming more capable at analysis, coding, research, and interpretation. The easiest integration pattern is also the most dangerous one: give the agent broad access to the same files a human analyst can read and ask it to be careful.

Long Gate assumes that is the wrong trust model for sensitive data.

## The principle

> Anything that can see raw data should not have unrestricted network access. Anything that has network access should not receive raw-data capabilities.

This is an architectural boundary, not a prompt.

## What Long Gate wants to become

A local-first control plane that can sit between sensitive datasets and networked AI systems across research, clinical, education, HR, and other high-sensitivity workflows.

The long-term system has four jobs:

1. **Understand the request.** Decide whether the task needs schema, synthetic rows, or exact local computation.
2. **Transform locally.** Detect sensitive fields, generate privacy-preserving surrogates, or execute exact statistics without exporting source rows.
3. **Prove the boundary.** Audit transformations, log capabilities, and generate a human-readable Trust Report.
4. **Expose only safe tools.** Networked agents receive approved artifacts and narrow capabilities instead of general filesystem access.

## Non-goals

Long Gate is not:
- a new foundation model;
- a replacement for mature PII or synthetic-data libraries;
- a claim that synthetic data is automatically anonymous;
- a compliance certification product;
- permission to upload sensitive data merely because a detector ran.

The project should remain useful even if every third-party privacy backend is replaced.
