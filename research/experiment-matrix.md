# Paper experiment matrix

This matrix separates implemented infrastructure from scientific evidence still required.

| Track | Variant / attack | Main metric family | Status |
|---|---|---|---|
| Release boundary | Direct networked-agent access | unsafe raw exposure | protocol defined |
| Release boundary | Long Gate capability separation | unsafe raw exposure | implementation exists; paper harness pending |
| Release boundary | Arbitrary file copied to egress | approval success/failure | engineering regression exists; paper harness pending |
| Release boundary | Post-approval mutation / TOCTOU | stale approval success/failure | engineering regression exists; paper harness pending |
| Release boundary | Purpose mismatch | unauthorized read success/failure | engineering regression exists; paper harness pending |
| Semantic baseline | Deterministic PII removal | privacy + utility | implementation exists; evaluation pending |
| Semantic baseline | NER/Presidio | privacy + utility | adapter pending |
| Semantic baseline | One-pass local LLM | privacy + utility | harness pending |
| Semantic ablation | Deterministic + local LLM | privacy + utility | harness pending |
| Semantic ablation | + independent audit | privacy + utility | harness pending |
| Semantic ablation | + bounded remediation | privacy + utility + cost | product mechanism exists; harness pending |
| Semantic attack | Exact number/date reuse | attack success | mechanical check exists |
| Semantic attack | Source phrase / n-gram reuse | attack success | mechanical check exists |
| Semantic attack | Distinctive token reuse | attack success | mechanical check exists |
| Semantic attack | Rare-event leakage | attack success | corpus/evaluator pending |
| Semantic attack | Relationship leakage | attack success | corpus/evaluator pending |
| Semantic attack | Combination uniqueness | attack success | corpus/evaluator pending |
| Semantic attack | Auxiliary-data linkage | attack success | evaluator pending |
| Semantic attack | Embedded prompt/instruction attack | leakage / policy violation | red-team corpus pending |
| Systems | Qwen3-4B tier | latency / memory / privacy / utility | harness pending |
| Systems | Qwen3-8B tier | latency / memory / privacy / utility | harness pending |
| Systems | Qwen3-14B tier | latency / memory / privacy / utility | harness pending |

## Dataset slots

| Dataset | Role | Redistribution status | Integration |
|---|---|---|---|
| Long Gate synthetic adversarial fixture | CI/development only | generated locally | available |
| Public text-anonymization benchmark(s) | main semantic evaluation | verify per dataset | adapter pending |
| Long Gate semantic red-team corpus | attack evaluation | should contain synthetic/non-sensitive cases | pending |
| Structured privacy synthetic corpus | release/attack evaluation | generated locally | partial |

## Completion rule

A row may move to **paper-ready** only when:

1. the experiment is executable from a frozen config;
2. raw normalized outputs are preserved;
3. provenance contains code/config/model/dataset identity;
4. the analysis code can regenerate the corresponding reported metric;
5. failures are included rather than manually removed.
