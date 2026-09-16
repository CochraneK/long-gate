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

PDF text-layer extraction remains available through `document-inspect`. For scanned/image-only PDFs, Long Gate now also has an **optional local OCR path** (`pdf-ocr-local`) using PDFium + a local Tesseract executable. OCR text remains local-only and zero hits still do not grant egress permission.

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

## Local image / scanned-PDF / audio paths

See [Local unstructured media privacy paths](unstructured-media.md).

The baseline can:
- inspect image dimensions/EXIF presence without returning EXIF values;
- OCR images locally and return aggregate PII counts only;
- render + OCR scanned PDFs locally with an explicit page cap;
- inspect WAV metadata locally.

All of these paths remain `release_allowed = false`.

## Semantic release evidence

Semantic transformation now records a conservative mechanical evidence gate (direct PII, exact number reuse, character n-gram reuse, distinctive long-token reuse, and minimum output length). Passing it means **eligible for manual review**, not safe to upload. See [Release evidence gates](release-criteria.md).

The longer-term higher-assurance design remains:

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
