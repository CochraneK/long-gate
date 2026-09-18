# Format-preserving de-identification

`longgate deidentify` is for producing a reusable local copy, not an abstract summary.

```bash
longgate deidentify notes.md
longgate deidentify page.html
longgate deidentify workbook.xlsx
longgate deidentify report.docx
```

Every current output remains local-review-only. A successful rewrite never creates network-egress permission.

## Current support

| Format | What is processed | Preserved / intentionally untouched | Current limitation |
|---|---|---|---|
| TXT / Markdown | direct identifier literals | all other characters, headings, paragraphs, line breaks | semantic names/orgs/rare combinations require review |
| HTML / HTM | visible text plus selected attributes (`alt`, `title`, `aria-label`, `placeholder`, `value`, `href`, `src`, `action`) | DOM/tag structure; scripts/styles/templates/SVG text are not rewritten | BeautifulSoup may normalize serialization/whitespace; ignored-region PII forces `LOCAL_ONLY` |
| XLSX | all worksheets including hidden sheets; string cells; comments/authors; hyperlink targets; selected workbook properties | formulas and sheet titles are not rewritten | formula/title/defined-name PII forces `LOCAL_ONLY`; OpenPyXL may not preserve unsupported Excel extensions |
| DOCX | OOXML paragraph text across body/tables/headers/footers/comments/footnotes/endnotes; core/app properties | run/paragraph/table/package structure and non-target ZIP entries are retained | direct identifiers split across runs are replaced; hyperlink relationship targets are scanned but not rewritten; media/embeddings/ActiveX/non-XML custom parts force `LOCAL_ONLY`; parseable custom XML is residual-scanned |
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

A `DirectIdentifierMapper` is shared across the complete document adapter. The same direct identifier therefore receives the same placeholder across HTML nodes, XLSX worksheets/comments/links, or DOCX OOXML text parts.

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

## DOCX-specific boundary

DOCX is treated as an OOXML ZIP package rather than flattened through `paragraph.text`.

- direct identifiers are planned against the concatenated text of each Word paragraph;
- replacements are projected back into the original `w:t` nodes, so an identifier split across runs can be replaced without collapsing all paragraph runs;
- body, tables, headers, footers, comments, footnotes and endnotes are handled through their WordprocessingML paragraphs;
- package entries are copied rather than rebuilt from a new Word document;
- document/core properties are processed for direct identifier literals;
- external relationship targets are not silently rewritten; if direct PII remains there, the result is `LOCAL_ONLY`;
- images, embedded objects, ActiveX and non-XML custom parts are unresolved content surfaces and force `LOCAL_ONLY`; parseable custom XML is scanned for residual direct PII;
- DOCX packages with more than 10,000 entries or more than 256 MiB total uncompressed size fail closed before processing.

Run formatting is preserved on unaffected text nodes; a replacement label inherits the starting run's position/style while covered identifier characters in subsequent runs are removed.
## Cross-file batch consistency

For related files that must reuse the same direct-identifier placeholders:

```bash
longgate deidentify-batch private/ --out-dir deidentified/ --recursive
```

Batch mode uses one shared `DirectIdentifierMapper` across the batch. The same direct identifier therefore keeps the same label across TXT/Markdown, HTML, XLSX, and DOCX files.

Persistent state is deliberately privacy-minimized:

```text
.longgate-batch.key
  32-byte local secret

.longgate-batch-state.json
  authenticated checkpoint
  HMAC(relative path) → input/output hashes + status
  HMAC(entity type + normalized identifier) → placeholder
```

The checkpoint does **not** store raw direct identifiers or source filenames. The mapping state and the entire checkpoint are authenticated with the local secret, so state/key mismatch or checkpoint tampering fails closed.

Treat both state files as private local material. Do not commit, upload, email, or place them in a network-facing workspace.

### Resume semantics

```bash
longgate deidentify-batch private/ \
  --out-dir deidentified/ \
  --recursive \
  --resume
```

A previous file is skipped only when all of these match:

- authenticated checkpoint;
- same input root;
- current input SHA-256;
- current output file exists;
- current output SHA-256.

If a file fails, the batch stops. Only files successfully completed before the failure remain checkpointed. After fixing the failing input, `--resume` skips verified completed outputs and retries the rest.

Fresh batch output must be a separate empty directory outside the source tree. Symlink files are not processed.
