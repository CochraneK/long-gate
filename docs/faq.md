# FAQ

## Does “local model” mean Long Gate never downloads a model?

No.

Long Gate separates **model provisioning** from **private processing**.

Model Setup Mode may access the Internet and write to the Model Vault, but it should not receive a private-data mount.

Private Processing Mode may read private data and the Model Vault read-only, but should have network access disabled.

---

## Which local model should I use?

Start with:

```bash
longgate model setup
```

The current curated defaults are:

| Approx. RAM | Default |
|---:|---|
| ~8 GB | `qwen3-4b` |
| ~16 GB | `qwen3-8b` |
| ~24 GB+ | `qwen3-14b` |

The recommendation is intentionally simple and conservative. CPU/GPU performance, context length, and other applications still matter.

---

## Where does Long Gate download models from?

The initial catalog uses official Qwen GGUF repositories on Hugging Face.

Each curated model entry pins:

1. an immutable upstream revision;
2. an expected SHA-256.

A mismatch fails closed.

See [Local Model Guide](models.md).

---

## Can I use my own GGUF?

Yes.

```bash
longgate semantic-transform-local interview.txt \
  --model /absolute/path/custom.gguf \
  --out preview.txt
```

For reproducibility and supply-chain metadata, curated Model Vault entries are preferred.

---

## Can I use Ollama?

Long Gate's built-in private semantic path currently does **not** use an Ollama/HTTP endpoint.

That is deliberate: a configurable URL creates a risk that a supposedly local endpoint is accidentally pointed at another host.

The built-in path loads a GGUF in-process through `llama-cpp-python`.

Ollama integration could be considered later if the capability boundary can be made explicit and testable.

---

## Do I need a GPU?

No. llama.cpp can run on CPU, though larger models may be slow.

GPU/Metal/CUDA acceleration is an optional performance optimization, not a security requirement.

See [Troubleshooting](troubleshooting.md).

---

## Is synthetic data automatically anonymous?

No.

Long Gate checks specific risks such as:

- exact row overlap;
- identifier reuse;
- rare quasi-identifier combinations;
- numeric near copies;
- equivalence-class risk;
- defined membership/linkage attacks.

Passing those checks is evidence about those checks — not a universal anonymity proof.

Row-level synthetic egress remains blocked by default.

---

## Why not simply pseudonymize IDs?

Replacing:

```text
Alice → P001
```

can preserve the rest of the person's row, frequency, chronology, and linkage structure.

Long Gate treats pseudonymized row-level data as local-only.

---

## Why can cloud AI still help if it cannot see the raw table?

Because many tasks need less than the raw table.

Examples:

- schema questions → schema metadata;
- exploration → synthetic representation;
- exact regression → cloud can propose the analysis, local executor runs it on real data, aggregate result returns;
- interpretation → safe statistical output.

This is purpose-bound disclosure.

---

## Is the `clinical` profile HIPAA/GDPR/NHS compliant?

No.

`research`, `clinical`, and `enterprise` are engineering presets with visible thresholds.

They are not compliance certifications.

---

## Can I upload a PDF after `document-inspect` reports zero PII hits?

No automatic permission is granted.

PDF extraction currently reads the text layer and does not OCR scanned/image-only pages.

Even a text-complete PDF can leak identity semantically.

The document path remains local-only.

---

## Does semantic-transform-local anonymize interviews?

Not yet.

It produces a local identity-detached **preview** and audits direct PII, reused number tokens, and long source-copy overlap.

It still returns:

```text
release_allowed = false
```

Stronger semantic attack evaluation is still active research.

---

## Can Long Gate send raw data to GPT/Claude/Gemini if I promise not to log it?

Not through the intended architecture.

The point of Long Gate is to remove the raw-data capability from the networked agent, not to rely on provider promises or prompt instructions.

---

## What can safely be deployed to Railway/Vercel/etc.?

The public demo is static and synthetic-only.

Do **not** deploy the private worker, private source mount, or Model Vault containing private-processing assets as part of a public demo.

---

## Why does Long Gate block so much?

Because uncertainty in a privacy gateway should usually fail closed.

Unknown purpose, unsupported modality, unsafe aggregate, final PII hit, path traversal, or unapproved row-level release should stop rather than silently lower the bar.
