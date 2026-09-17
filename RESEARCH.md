# Long Gate research track

Long Gate's product surface is now intentionally stable enough that new work should be driven by **research evidence**, not feature count.

The canonical paper-artifact workspace is [`research/`](research/README.md).

Current priorities:

1. freeze research questions and threat model;
2. implement comparable baselines and ablations;
3. evaluate privacy and utility together;
4. add semantic red-team corpora and public dataset adapters;
5. record exact experiment provenance;
6. regenerate paper tables/figures from raw normalized results;
7. prepare a clean/anonymized artifact export when a venue requires it.

Start with:

```bash
make research-check
make research-smoke
```

`research-smoke` verifies the reproducibility plumbing only. It is deliberately labeled **not paper evidence**.

See also:

- [`research/research-questions.md`](research/research-questions.md)
- [`research/protocol.md`](research/protocol.md)
- [`research/experiment-matrix.md`](research/experiment-matrix.md)
- [`research/ARTIFACT_FREEZE.md`](research/ARTIFACT_FREEZE.md)
