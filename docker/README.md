# Hardened deployment target

Long Gate's target deployment uses two workers:

- `local-worker`: can mount source data read-only; `network_mode: none`.
- `cloud-worker`: can access the network; can mount only an approved egress directory.

The initial repository does not launch a cloud worker because v0.1 performs no network transmission.
