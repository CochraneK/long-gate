# Generated research results

Development-time outputs under this directory are ignored by Git.

For a paper artifact freeze, archive a **deliberately selected complete run directory** containing at minimum:

- `manifest.json`;
- frozen experiment config;
- normalized `runs.jsonl`;
- `summary.json` and regenerated paper tables/figures;
- dataset/model provenance references and checksums;
- notes for any failed or excluded run.

Do not commit raw private input rows, private narratives, secret paths, API credentials, or model files here.

A paper-facing result directory should be reproducible from the tagged code/configuration rather than hand-edited to match the manuscript.
