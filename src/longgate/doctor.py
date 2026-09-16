from __future__ import annotations

import importlib.util
import shutil
import sys
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Capability:
    name: str
    available: bool
    detail: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _has(
    module: str,
) -> bool:
    return (
        importlib.util.find_spec(module)
        is not None
    )


def capabilities() -> list[Capability]:
    return [
        Capability(
            "python",
            True,
            sys.version.split()[0],
        ),
        Capability(
            "mostlyai",
            _has("mostlyai"),
            "local synthetic backend",
        ),
        Capability(
            "synthcity",
            _has("synthcity"),
            "local synthetic backend",
        ),
        Capability(
            "presidio",
            _has("presidio_analyzer"),
            "enhanced local PII detection",
        ),
        Capability(
            "statsmodels",
            _has("statsmodels"),
            "local exact Python OLS",
        ),
        Capability(
            "rscript",
            shutil.which("Rscript")
            is not None,
            (
                "fixed-template local R exact engine; "
                "no arbitrary R code"
            ),
        ),
        Capability(
            "documents",
            (
                _has("docx")
                and _has("pypdf")
            ),
            "local DOCX/PDF text-layer inspection",
        ),
        Capability(
            "pyarrow",
            _has("pyarrow"),
            "Parquet support",
        ),
    ]


def choose_backend() -> str:
    """Prefer mature local backends; demo fallback stays fail-closed."""
    if _has("mostlyai"):
        return "mostlyai"
    if _has("synthcity"):
        return "synthcity"
    return "demo"
