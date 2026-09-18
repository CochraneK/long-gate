# Format-preserving de-identification

`longgate deidentify` is for producing a reusable local copy, not an abstract summary.

```bash
longgate deidentify notes.md
longgate deidentify page.html
longgate deidentify workbook.xlsx
```

Every current output remains local-review-only. A successful rewrite never creates network-egress permission.

## Current support

| Format | What is processed | Preserved / intentionally untouched | Current limitation |
|---|---|---|---|
| TXT / Markdown | direct identifier literals | all other characters, headings, paragraphs, line breaks | semantic names/orgs/rare combinations require review |
| HTML / HTM | visible text plus selected attributes (`alt`, `title`, `aria-label`, `placeholder`, `value`, `href`, `src`, `action`) | DOM/tag structure; scripts/styles/templates/SVG text are not rewritten | BeautifulSoup may normalize serialization/whitespace; ignored-region PII forces `LOCAL_ONLY` |
| XLSX | all worksheets including hidden sheets; string cells; comments/authors; hyperlink targets; selected workbook properties | formulas and sheet titles are not rewritten | formula/title/defined-name PII forces `LOCAL_ONLY`; OpenPyXL may not preserve unsupported Excel extensions |
| DOCX | not yet supported by this command | — | fails closed rather than flattening the file |
| PDF | not supported as a format-preserving rewrite target | — | use local inspection/OCR or `semantic-summarize` only when abstract text is intended |

## Integrity properties

- input and output may not resolve to the same path;
- output keeps the source extension;
- source bytes/hash are fixed before processing;
- source integrity is checked again before and after output commit;
- output uses a sibling temporary file followed by atomic `os.replace`;
- if the source changes during commit, the generated output is removed and the run fails;
- Trust Reports contain format/hash/count metadata, not source text, transformed text, filenames, or local paths.

## Shared entity map

A `DirectIdentifierMapper` is shared across the complete document adapter. The same direct identifier therefore receives the same placeholder across HTML nodes or across XLSX worksheets/comments/links.

Example:

```text
person@example.com → [EMAIL_001]
same value elsewhere → [EMAIL_001]
different@example.com → [EMAIL_002]
```

The current map is document-scoped. Cross-file batch mapping remains planned.

## Separate semantic abstraction

If the task is to intentionally discard source structure and create an identity-detached abstract narrative, use:

```bash
longgate semantic-summarize interview.txt --model auto --out summary.txt
```

That command uses the verified local GGUF path and bounded semantic remediation. It is deliberately not described as format-preserving de-identification.

## Release boundary

Format-preserving output can end as:

```text
MANUAL_REVIEW_REQUIRED
```

when the direct-PII rescan is quiet, or:

```text
LOCAL_ONLY
```

when direct PII remains in processed or intentionally unmodified regions.

Both states keep:

```text
manual_review_required = true
automatic_release_allowed = false
release_allowed = false
```
