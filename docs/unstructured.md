# Unstructured and document data

Free text is harder than structured tabular data because identity can be carried by meaning rather than obvious PII strings.

Examples:

- “the only neurosurgeon in a small town”;
- a rare event sequence;
- a workplace and job-title combination;
- a relationship description;
- a narrative that is searchable on the public web.

Removing names and phone numbers does not make those narratives anonymous.

## Local text baseline

TXT and Markdown can be inspected locally:

```bash
longgate text-inspect interview.txt
```

A pattern-level local preview redaction is available:

```bash
longgate text-redact-local interview.txt --out redacted.txt
```

The command name intentionally includes **local**. The output does **not** receive network-egress permission.

## DOCX / PDF local inspection

Install optional document parsers:

```bash
pip install -e '.[documents]'
```

Then inspect locally:

```bash
longgate document-inspect report.docx
longgate document-inspect transcript.pdf
```

DOCX extraction reads paragraph and table-cell text.

PDF extraction uses the PDF text layer only. Long Gate does **not** OCR scanned/image-only PDFs in this baseline. A PDF with zero extracted PII hits can therefore still contain visible private information.

Every document result remains:

```text
release_allowed = false
```

## Why zero hits still means BLOCK

Pattern detection cannot reliably identify:

- semantic identity;
- rare occupations/events;
- geographic uniqueness;
- indirect relationship clues;
- text embedded in images;
- content outside the parser's extraction surface.

Therefore a zero-hit local scan is evidence about the detector, not permission to upload the document.

## Future semantic path

The intended higher-assurance design is:

```text
raw narrative / document
   ↓ local-only
local semantic model
   ↓
identity-detached abstraction / synthetic narrative
   ↓
semantic privacy attack suite
   ↓
policy / human review
   ↓
possible safe artifact
```

Until that path has stronger evaluation, unstructured content remains fail-closed for network release.
