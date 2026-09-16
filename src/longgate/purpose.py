from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class DisclosureMode(str, Enum):
    SCHEMA_ONLY = "schema_only"
    SYNTHETIC = "synthetic"
    LOCAL_EXACT = "local_exact"
    BLOCK = "block"


@dataclass(frozen=True)
class PurposeDecision:
    purpose: str
    mode: DisclosureMode
    reason: str


_SCHEMA = {"schema", "columns", "types", "inspect"}
_SYNTHETIC = {"explore", "distribution", "prototype", "code_generation", "visualize"}
_LOCAL_EXACT = {"describe", "correlation", "group_summary", "regression", "exact_statistics"}


def route_purpose(purpose: str) -> PurposeDecision:
    p = purpose.strip().lower().replace("-", "_").replace(" ", "_")
    if p in _SCHEMA:
        return PurposeDecision(p, DisclosureMode.SCHEMA_ONLY, "Schema metadata is sufficient.")
    if p in _SYNTHETIC:
        return PurposeDecision(
            p, DisclosureMode.SYNTHETIC, "Use synthetic rows after privacy audit."
        )
    if p in _LOCAL_EXACT:
        return PurposeDecision(
            p,
            DisclosureMode.LOCAL_EXACT,
            "Run exact computation locally and disclose aggregates only.",
        )
    return PurposeDecision(p, DisclosureMode.BLOCK, "Unknown purpose; default deny.")
