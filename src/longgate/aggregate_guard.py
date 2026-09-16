from __future__ import annotations

import json
from typing import Any

from .pii import scan_text


def validate_aggregate_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Fail closed if a supposedly aggregate result still contains direct PII patterns."""
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    findings = scan_text(text)
    if findings.total_hits:
        raise ValueError(
            "Aggregate result failed final PII scan "
            f"({findings.total_hits} direct-PII pattern hit(s))."
        )
    return payload
