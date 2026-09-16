# Provenance, integrity, and signatures

Long Gate records SHA-256 hashes for run artifacts so later changes can be detected.

Each structured run writes:

```text
provenance.json
```

Verify integrity:

```bash
longgate verify-run longgate-runs/LG-...
```

The provenance manifest covers available artifacts such as:

- manifest;
- audit result;
- synthetic local preview;
- row-level egress manifest / payload when present;
- aggregate egress manifest / safe aggregate when the release ladder falls back;
- Trust Report.

## Integrity is the default

A SHA-256 provenance manifest detects post-run modification, but by itself it does **not** authenticate who created the run.

That remains the default because Long Gate should not silently create or manage long-lived signing secrets.

## Optional Ed25519 signature

Install the optional dependency:

```bash
pip install 'long-gate[attestation]'
```

Use an Ed25519 PEM signing key that you manage outside Long Gate:

```bash
longgate sign-run longgate-runs/LG-... \
  --signing-key /secure/location/signing-key.pem
```

This writes:

```text
provenance.sig.json
```

The signature is bound to the provenance integrity digest using a domain-separated message:

```text
long-gate-provenance-v1
<integrity_digest>
```

Long Gate does not copy the signing key into the run directory.

Verify integrity **and** authenticity against an independently trusted public key:

```bash
longgate verify-run longgate-runs/LG-... \
  --public-key verification-key.pem
```

When `--public-key` is supplied, a missing, mismatched, or invalid signature makes the overall verification fail.

## Key identity

`provenance.sig.json` records a `key_id` equal to SHA-256 of the raw Ed25519 public key.

The key ID helps identify which verification key was used. It does not establish that the key belongs to a particular person or organization.

## What a valid signature means

A valid Ed25519 signature can establish:

- the provenance digest was signed by the holder of the corresponding signing key;
- the signed digest has not been substituted without invalidating verification;
- the artifacts covered by `provenance.json` still match their recorded hashes.

It does **not** establish:

- that the host OS was uncompromised;
- that the private source data was accurate;
- that a privacy decision was legally compliant;
- that the signer is trustworthy merely because the signature verifies;
- that the signing key was stored securely.

Trust in the public key must be established independently.

## Secret-management boundary

Long Gate deliberately does not provide a command that generates a long-lived production signing key.

Key generation, hardware-backed storage, rotation, revocation, identity binding, and organization PKI are separate operational responsibilities. This keeps the privacy gateway from becoming an implicit key-management system.
