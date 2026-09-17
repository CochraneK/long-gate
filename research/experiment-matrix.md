# Paper experiment matrix

This matrix separates implemented infrastructure from scientific evidence still required.

| Track | Variant / attack | Main metric family | Status |
|---|---|---|---|
| Release boundary | Directory-only workspace baseline | unsafe file exposure | synthetic harness available |
| Release boundary | Long Gate capability separation | unsafe raw/artifact exposure | synthetic harness available; external comparison pending |
| Release boundary | Arbitrary file copied to egress | approval success/failure | synthetic harness available |
| Release boundary | Post-approval mutation / TOCTOU | stale approval success/failure | synthetic harness available |
| Release boundary | Purpose mismatch | unauthorized read success/failure | synthetic harness available |
| Release boundary | Manifest hash mismatch | unauthorized approval success/failure | synthetic harness available |
| Semantic baseline | Identity / no transformation | privacy + utility | negative control available |
| Semantic baseline | Deterministic PII removal | privacy + utility | adapter + synthetic evaluation available |
| Semantic baseline | NER/Presidio | privacy + utility | adapter available; full evaluation pending |
| Semantic baseline | One-pass local LLM | privacy + utility | adapter available; model evaluation pending |
| Semantic ablation | Deterministic + local LLM | privacy + utility | harness pending |
| Semantic ablation | + independent audit | privacy + utility | harness pending |
| Semantic ablation | + bounded remediation | privacy + utility + cost | product mechanism exists; paper harness pending |
| Semantic attack | Direct PII patterns | attack success | synthetic corpus/evaluator available |
| Semantic attack | Exact number/date reuse | attack success | synthetic corpus + mechanical evaluator available |
| Semantic attack | Source phrase / n-gram reuse | attack success | mechanical evaluator available |
| Semantic attack | Distinctive token reuse | attack success | mechanical evaluator available |
| Semantic attack | Rare-event leakage | attack success | synthetic corpus/literal evaluator available; stronger inference attacker pending |
| Semantic attack | Relationship leakage | attack success | synthetic corpus/literal evaluator available; stronger inference attacker pending |
| Semantic attack | Combination uniqueness | attack success | synthetic corpus/literal evaluator available; stronger inference attacker pending |
| Semantic attack | Auxiliary-data linkage | attack success | evaluator pending |
| Semantic attack | Embedded prompt/instruction attack | leakage / policy violation | synthetic corpus available; local-LLM evaluation pending |
| Systems | Qwen3-4B tier | latency / memory / privacy / utility | harness pending |
| Systems | Qwen3-8B tier | latency / memory / privacy / utility | harness pending |
| Systems | Qwen3-14B tier | latency / memory / privacy / utility | harness pending |

## Dataset slots

| Dataset | Role | Redistribution status | Integration |
|---|---|---|---|
| Long Gate synthetic adversarial fixture | CI/development only | generated locally | available |
| Public text-anonymization benchmark(s) | main semantic evaluation | verify per dataset | adapter pending |
| Long Gate semantic red-team corpus | attack evaluation | synthetic/non-sensitive | v1 available |
| Structured privacy synthetic corpus | release/attack evaluation | generated locally | partial |

## Interpretation boundary

The synthetic red-team suite is useful for regression, ablation plumbing, and controlled counterexamples. It is **not** a substitute for an independent public evaluation dataset or a realistic auxiliary-information attacker. Rows marked "synthetic harness available" are therefore not automatically "paper-ready."

## Completion rule

A row may move to **paper-ready** only when:

1. the experiment is executable from a frozen config;
2. raw normalized outputs are preserved;
3. provenance contains code/config/model/dataset identity;
4. the analysis code can regenerate the corresponding reported metric;
5. failures are included rather than manually removed;
6. development/synthetic fixtures are clearly separated from independent evaluation evidence.
