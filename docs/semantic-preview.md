# Local semantic privacy path

Long Gate now separates format-preserving de-identification from semantic abstraction:

- `deidentify` — same-format TXT/Markdown direct-identifier replacement for reusable local copies;
- `semantic-summarize` — product-level deterministic pre-scrub + bounded local semantic abstraction + audit + Semantic Trust Report;
- `semantic-transform-local` — low-level single-pass semantic preview for development/debugging.

None of these paths is called certified anonymization. None automatically grants network egress. The format-preserving `deidentify` path is documented separately because preserving source structure and aggressively abstracting identity are different tasks.

## Why a local LLM is useful — and still not enough

A local LLM can remove or generalize identity cues that simple pattern matching misses, but it can also:

- repeat source phrases;
- preserve exact dates or numbers;
- reproduce names or contact information;
- preserve rare semantic combinations;
- preserve relationships that make a person identifiable;
- hallucinate new sensitive details.

Long Gate therefore treats the model as a **privacy transformation component**, not as the final privacy authority.

---

## Product semantic path: `longgate semantic-summarize`

After installing a verified local model:

```bash
longgate setup
```

run:

```bash
longgate semantic-summarize interview.txt \
  --model auto \
  --out deidentified.txt
```

Supported extractable-text inputs are TXT, Markdown, HTML, DOCX, and PDF text layers. This command produces an abstract summary, not a format-preserving document copy.

The pipeline is:

```text
source document
      ↓
deterministic local pre-scrub
      ↓
verified local GGUF model
      ↓
semantic identity-detaching transform
      ↓
audit against the ORIGINAL source
      ↓
PII / exact-number / n-gram / distinctive-token checks
      ↓
quiet enough for manual review?
      ├─ yes → MANUAL_REVIEW_CANDIDATE
      └─ no  → another local semantic pass
                   ↓
              maximum 3 total rounds
                   ↓
              LOCAL_ONLY if still failing
```

The current default is two rounds. Users may explicitly choose 1–3:

```bash
longgate semantic-summarize interview.txt \
  --model auto \
  --out deidentified.txt \
  --max-rounds 3
```

The retry loop is intentionally bounded. Privacy failure never triggers an infinite autonomous loop or a lower policy threshold. A llama.cpp completion that ends because the token limit was reached is rejected rather than treated as a valid partial privacy transform.

### Why compare every round to the original source?

A second transform may no longer contain obvious identifiers from the first transformed version while still preserving details from the original source. Long Gate therefore audits the final candidate against the **original** narrative rather than only comparing adjacent transformation rounds.

---

## Local GGUF model only

The semantic transformer runs in-process through `llama-cpp-python`.

Private processing does **not**:

- download a model;
- call Hugging Face;
- accept an Ollama/HTTP endpoint;
- accept a remote provider;
- accept a custom network URL.

Model download happens separately in Setup Mode through the curated Model Vault:

```text
SETUP MODE
network: YES
private data: NO
Model Vault: WRITE

PRIVATE PROCESSING MODE
network: NO
private data: YES
Model Vault: READ ONLY
```

See [Local Model Guide](models.md).

---

## Transformation instruction

The local transformer uses a fixed privacy-oriented instruction to:

- remove/generalize direct identifiers;
- avoid exact dates, ages, addresses, and identifiers;
- generalize rare organizations, roles, and event combinations;
- return an identity-detached abstract summary;
- avoid inventing new identifying details.

Users and networked agents do not supply arbitrary system prompts through this interface.

The product-level `semantic-summarize` command first applies deterministic local pre-scrubbing for supported obvious patterns before sending the text into the verified local model. This reduces avoidable direct-identifier exposure inside the local inference step, but pre-scrubbing itself is never treated as release authorization.

---

## Mechanical semantic evidence

Every semantic candidate is checked for:

- direct PII patterns;
- exact numeric tokens reused from the original source;
- long normalized character n-grams reused from the original source;
- distinctive long source tokens reused in the transformed text.

The current `semantic-release-evidence-v1` manual-review thresholds are:

- direct PII hits = 0;
- reused exact numeric tokens = 0;
- normalized character n-gram reuse ≤ 1%;
- distinctive long-token reuse ≤ 5%;
- transformed output length ≥ 80 characters.

Passing all criteria still means only:

```text
eligible_for_manual_review = true
manual_review_required = true
automatic_release_allowed = false
release_allowed = false
```

A failure after all bounded rounds means:

```text
status = LOCAL_ONLY
automatic_release_allowed = false
release_allowed = false
```

See [Release evidence gates](release-criteria.md).

---

## Semantic Trust Report

`longgate semantic-summarize` writes:

```text
deidentified.txt
deidentified.txt.audit.json
deidentified.txt.trust-report.html
```

The offline report contains:

- input SHA-256;
- local model filename (not its full local path);
- number of remediation rounds;
- per-round PII counts;
- reused-number counts;
- n-gram reuse rates;
- distinctive-token reuse rates;
- failed conditions;
- final status;
- local next actions.

The report deliberately does **not** embed the original narrative or the transformed narrative. The user reviews the transformed output locally as a separate file.

---

## Low-level single-pass command

For development or experiments, the older primitive remains available:

```bash
longgate semantic-transform-local interview.txt \
  --model auto \
  --out preview.txt
```

It writes a single transformed preview and `preview.txt.audit.json`. It does not run the bounded remediation product loop or produce the newer Semantic Trust Report.

---

## Remaining semantic research

The current mechanical gate does **not** prove that a person cannot be identified from meaning or external knowledge. Before any future semantic egress path could be considered, Long Gate still needs stronger evidence such as:

- rare-event leakage attacks;
- relationship leakage attacks;
- combination-uniqueness tests;
- local semantic identity/risk models;
- multilingual attack corpora;
- privacy-aware long-document segmentation with cross-chunk consistency checks;
- auxiliary-data linkage tests where ethically appropriate;
- profile-specific thresholds;
- human/policy review for high-risk domains.

Until such evidence exists, semantic transformation remains a **local privacy-development and review workflow**, not an automatic egress mechanism.
