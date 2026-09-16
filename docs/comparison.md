# How Long Gate differs

Long Gate is primarily an **orchestration and capability-boundary project**.

| Approach | Typical strength | Typical weakness | Long Gate's role |
|---|---|---|---|
| Mask / pseudonymize identifiers | Simple and fast | Frequency and linkage structure may remain | Treat pseudonymized rows as local-only |
| PII redaction | Good for obvious identifiers | Quasi-identifiers and semantics can still leak | Use as one local inspection layer, not the whole policy |
| Synthetic data generator | Preserves useful structure without copying the source table directly | Synthetic does not automatically mean anonymous | Wrap generation with privacy audits and fail-closed egress |
| Differential privacy | Formal privacy guarantees when correctly configured | Utility/configuration trade-offs; not every workflow fits | Support DP-capable backends as adapters |
| Prompt-only guardrails | Easy to deploy | The agent still has the capability to access the data | Remove the capability instead |
| Generic secure sandbox | Strong process isolation | Does not decide what data representation is appropriate | Add purpose routing, privacy policy, egress checks, and provenance |

## The key distinction

Long Gate separates **who can see raw data** from **who can access the network**.

That means a networked model is not merely instructed to avoid a raw file. The raw file is absent from the capability surface it receives.
