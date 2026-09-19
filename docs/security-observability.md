# Security observability

Long Gate now includes a narrow local security-observability layer around the existing privacy boundary.

The goal is not to become a general packet analyzer. The goal is to answer four practical questions without turning raw private content into another log source:

1. **Where is this AI client actually connecting?**
2. **What classes of sensitive information appear in captured outbound requests?**
3. **Are secrets present in the repository or its history?**
4. **Can suspicious input be examined inside a capability-restricted quarantine zone?**

## AI endpoint provenance

Use:

```bash
longgate endpoint inspect https://api.openai.com/v1
```

Long Gate classifies known official endpoints, known routers/aggregators, managed cloud endpoints, and custom/unknown endpoints. By default it also resolves DNS and inspects the server certificate.

For a zero-network classification:

```bash
longgate endpoint inspect https://example.com/v1 --no-connect
```

A custom endpoint is reported as **relay-possible**, not as proof that a relay exists. DNS, IP, certificate, and hostname evidence show the endpoint the client connects to; they cannot prove which upstream model eventually executes a request.

Long Gate never sends a prompt during endpoint inspection.

## Inspect captured outbound HTTP metadata

If a browser or an explicitly configured local proxy has exported a HAR file:

```bash
longgate egress inspect-har capture.har
```

The local report includes:

- destination hosts;
- method and content type;
- request-body byte counts;
- direct-PII counts;
- sensitive header **names**;
- sensitive query-parameter **names**;
- secret-like field-name counts;
- endpoint classification and relay-possible status.

The report intentionally does **not** echo:

- Authorization values;
- API keys or query values;
- cookies;
- request bodies;
- matched PII values.

A HAR can itself contain highly sensitive data. Keep it local and delete it when it is no longer needed.

Long Gate does not currently perform TLS interception itself. Tools such as a browser export or an explicitly configured local inspection proxy can create the HAR; Long Gate then performs local privacy-aware analysis on that artifact.

## Secret scanning

Use a locally installed Gitleaks binary:

```bash
longgate secrets scan .
longgate secrets scan . --history
```

Long Gate returns only:

- finding count;
- affected file paths;
- Gitleaks rule identifiers.

Matched secret values are omitted. The temporary Gitleaks report is requested with full redaction and is deleted after parsing.

CI separately runs a blocking full-history Gitleaks scan. This complements Trivy: a secret deleted from the current working tree may still exist in Git history.

## Quarantine zone

`docker-compose.quarantine.yml` defines a restricted analysis environment for suspicious or untrusted input.

Its contract requires:

- networking disabled;
- read-only container root;
- non-root user;
- all Linux capabilities dropped;
- `no-new-privileges`;
- quarantined input mounted read-only;
- no Model Vault, SafeWorkspace, private workspace, SSH/AWS/cloud config, or Docker socket mounts;
- explicitly blanked common cloud/AI credentials;
- writable state only in bounded tmpfs;
- CPU, memory, and PID limits.

Validate the file structurally through the test suite. The current quarantine zone is intended for bounded local inspection/validation. It is **not** a claim of protection against kernel/container-runtime vulnerabilities or a hostile host administrator.

## Relationship to the Long Gate boundary

These capabilities do not authorize egress.

```text
observe / scan / quarantine
          ↓
local evidence only
          ↓
policy + manifest + local approval
          ↓
approved SafeWorkspace
          ↓
network consumer
```

Security evidence and release authorization remain separate.
