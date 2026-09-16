from __future__ import annotations

from typing import Any

from .pii import scan_structured_strings


def validate_aggregate_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Fail closed if a supposedly aggregate result still contains direct PII patterns."""
    findings = scan_structured_strings(payload)
    if findings.total_hits:
        raise ValueError(
            "Aggregate result failed final PII scan "
            f"({findings.total_hits} direct-PII pattern hit(s))."
        )
    return payload
