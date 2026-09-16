from __future__ import annotations

import importlib.util
import sys
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Capability:
    name: str
    available: bool
    detail: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _has(module: str) -> bool:
    return importlib.util.find_spec(module) is not None


def capabilities() -> list[Capability]:
    return [
        Capability("python", True, sys.version.split()[0]),
        Capability("mostlyai", _has("mostlyai"), "local synthetic backend"),
        Capability("synthcity", _has("synthcity"), "local synthetic backend"),
        Capability("presidio", _has("presidio_analyzer"), "enhanced local PII detection"),
        Capability("statsmodels", _has("statsmodels"), "local exact OLS"),
        Capability("pyarrow", _has("pyarrow"), "Parquet support"),
    ]


def choose_backend() -> str:
    """Prefer local mature backends. Fallback remains demo and therefore fail-closed."""
    if _has("mostlyai"):
        return "mostlyai"
    if _has("synthcity"):
        return "synthcity"
    return "demo"
