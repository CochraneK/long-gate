from __future__ import annotations

import math
from typing import Any

from .pii import scan_structured_strings


def _count_bucket(value: int, step: int) -> str:
    if value < 0:
        raise ValueError("Aggregate counts cannot be negative.")
    step = max(10, int(step))
    lower = (value // step) * step
    upper = lower + step - 1
    return f"{lower}-{upper}"


def build_release_safe_describe(
    summary: dict[str, Any],
    *,
    min_release_n: int,
    count_bucket_size: int,
    decimals: int = 2,
) -> dict[str, Any]:
    """Project a local exact describe result into a disclosure-limited release view.

    The local executor may compute exact descriptive statistics. The network-
    eligible aggregate fallback deliberately reveals less: exact extrema and
    exact counts are removed, counts are bucketed, and continuous statistics are
    rounded. Columns with too few non-missing observations are suppressed.
    """
    if min_release_n < 2:
        raise ValueError("min_release_n must be >= 2.")
    if decimals < 0 or decimals > 6:
        raise ValueError("decimals must be between 0 and 6.")

    columns = summary.get("columns")
    if not isinstance(columns, dict):
        raise TypeError("Describe summary must contain a columns mapping.")

    released: dict[str, Any] = {}
    for raw_name, stats in columns.items():
        if not isinstance(stats, dict):
            continue
        n = stats.get("n")
        if isinstance(n, bool) or not isinstance(n, int) or n < min_release_n:
            continue

        mean = stats.get("mean")
        std = stats.get("std")
        if mean is None or std is None:
            continue
        if not isinstance(mean, (int, float)) or not isinstance(std, (int, float)):
            continue
        if not math.isfinite(float(mean)) or not math.isfinite(float(std)):
            continue

        released[str(raw_name)] = {
            "n_bucket": _count_bucket(n, count_bucket_size),
            "mean": round(float(mean), decimals),
            "std": round(float(std), decimals),
        }

    if not released:
        raise ValueError(
            "No numeric column has enough non-missing observations for aggregate release."
        )

    n_rows = summary.get("n_rows")
    if isinstance(n_rows, bool) or not isinstance(n_rows, int) or n_rows < min_release_n:
        raise ValueError("Dataset is too small for aggregate release.")

    return {
        "n_rows_bucket": _count_bucket(n_rows, count_bucket_size),
        "columns": released,
        "disclosure_controls": {
            "exact_counts_released": False,
            "extrema_released": False,
            "rounding_decimals": decimals,
            "minimum_non_missing_n": min_release_n,
            "count_bucket_size": max(10, int(count_bucket_size)),
        },
    }


def validate_aggregate_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Fail closed if a supposedly aggregate result still contains direct PII patterns."""
    findings = scan_structured_strings(payload)
    if findings.total_hits:
        raise ValueError(
            "Aggregate result failed final PII scan "
            f"({findings.total_hits} direct-PII pattern hit(s))."
        )
    return payload
