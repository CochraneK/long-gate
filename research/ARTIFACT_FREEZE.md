# Paper artifact freeze checklist

Use this only when preparing a real submission or artifact review.

## Freeze inputs

- [ ] Tag/freeze the exact Long Gate commit used for evaluation.
- [ ] Freeze experiment configuration files.
- [ ] Record dataset versions, source links, terms, preprocessing, and checksums.
- [ ] Record local model repository/revision, GGUF filename, and SHA-256.
- [ ] Record decoding/context settings.
- [ ] Record the declared seed list.

## Freeze evidence

- [ ] Preserve every normalized run record, including failed/`LOCAL_ONLY` cases.
- [ ] Preserve environment/hardware provenance.
- [ ] Preserve raw aggregate metric outputs used by analysis code.
- [ ] Regenerate every manuscript table/figure from the frozen result directory.
- [ ] Confirm no figure/table was manually edited in a way that changes reported values.

## Privacy and licensing review

- [ ] No raw private source rows or narratives are embedded in manifests/results.
- [ ] No secrets, usernames, local absolute paths, or credentials are included unnecessarily.
- [ ] Third-party datasets/models are redistributed only when their terms allow it.
- [ ] Any real sensitive dataset remains outside the public artifact unless explicit authorization permits release.

## Anonymous review export

If the venue requires double-blind/anonymized artifacts:

- [ ] remove author-identifying metadata from artifact-facing docs/configs;
- [ ] use an anonymous repository/archive mechanism approved by the venue;
- [ ] scrub local paths/usernames from frozen outputs;
- [ ] do not rewrite or falsify scientific provenance — replace identifying repository references with stable anonymous placeholders;
- [ ] verify that links, Git metadata, package metadata, result manifests, and generated HTML/PDF do not reveal author identity;
- [ ] freeze the anonymous artifact for the review period if the venue requires no updates.

## Reproduction test

On a clean environment:

1. install the documented dependencies;
2. run the artifact checker;
3. run the smoke suite;
4. run the frozen paper suite on the documented datasets/models;
5. regenerate tables/figures;
6. compare generated outputs/checksums with the archived artifact.

A submission should not claim full reproducibility until this clean-environment test has been performed.
