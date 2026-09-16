# Local semantic preview

Long Gate includes an experimental **local semantic preview** path for narratives and documents.

It is deliberately **not** called anonymization.

## Why?

A local LLM can remove or generalize obvious identity cues, but it can also:

- repeat source phrases;
- preserve exact dates or numbers;
- reproduce names or contact information;
- preserve rare semantic combinations;
- hallucinate new sensitive details.

Therefore transformed text remains local-only in the current baseline.

## Local GGUF model only

Install the optional in-process llama.cpp binding:

```bash
pip install -e '.[local-llm]'
```

Provide a GGUF file that already exists on the machine:

```bash
longgate semantic-transform-local interview.txt \
  --model /models/local-model.gguf \
  --out preview.txt
```

Long Gate does **not**:

- download a model;
- call Hugging Face;
- accept an Ollama/HTTP endpoint;
- accept a remote provider;
- accept a custom network URL.

The model runs in-process through `llama-cpp-python`.

## Fixed transformation instruction

The current transformer uses a fixed privacy-oriented instruction to:

- remove/generalize direct identifiers;
- avoid exact dates, ages, addresses, and identifiers;
- generalize rare organizations, roles, and event combinations;
- return an identity-detached abstract summary.

Users and networked agents do not supply arbitrary system prompts through this interface.

## Copy-risk audit

Every transformed preview is checked for:

- direct PII patterns;
- exact numeric tokens reused from the source;
- long normalized character n-grams reused from the source.

An audit sidecar is written next to the preview:

```text
preview.txt
preview.txt.audit.json
```

The audit always records:

```text
release_allowed = false
```

Even zero direct PII and zero copy overlap do not prove semantic anonymity.

## Future release criteria

Before unstructured output could ever become network-eligible, Long Gate would need stronger evidence such as:

- local semantic entity/risk models;
- rare-event and relationship leakage tests;
- auxiliary-web/search linkage tests where ethically appropriate;
- multilingual evaluation;
- attack corpora;
- profile-specific thresholds;
- human/policy review for high-risk domains.

Until then, semantic transformation is a **local privacy-development tool**, not an egress mechanism.
