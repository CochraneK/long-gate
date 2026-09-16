# Unstructured data

Free text is harder than structured tabular data because identity can be carried by meaning rather than obvious PII strings.

Examples:

- “the only neurosurgeon in a small town”;
- a rare event sequence;
- a workplace and job-title combination;
- a relationship description;
- a narrative that is searchable on the public web.

Removing names and phone numbers does not make those narratives anonymous.

## v0.5 baseline

Long Gate supports local-only inspection for UTF-8 TXT and Markdown files:

```bash
longgate text-inspect interview.txt
```

It reports counts and file metadata without returning matched PII values.

A local preview redaction is also available:

```bash
longgate text-redact-local interview.txt --out redacted.txt
```

The command name intentionally includes **local**. The output does **not** receive network-egress permission.

## Future semantic path

The intended higher-assurance design is:

```text
raw narrative
   ↓ local-only
local semantic model
   ↓
identity-detached abstraction / synthetic narrative
   ↓
semantic privacy audit
   ↓
human / policy review
   ↓
possible safe artifact
```

Until that path has stronger evaluation, free text remains fail-closed for network release.
