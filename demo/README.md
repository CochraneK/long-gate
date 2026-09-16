# Public safe demo

This directory is intentionally deployable without any private-data capability.

It contains:
- a static Long Gate explainer;
- a static synthetic Trust Report example;
- no upload endpoint;
- no API key;
- no cloud-model client;
- no source-data worker.

For Railway, configure this directory as the service root and use `Dockerfile`.

The real local worker must **never** be deployed as part of this public demo.
