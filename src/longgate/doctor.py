from __future__ import annotations

import importlib.util
import platform
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


def _local_llm_detail() -> str:
    if _has("llama_cpp"):
        return "in-process local GGUF semantic preview; output remains local-only"
    if platform.system() == "Windows" and sys.version_info >= (3, 13):
        return (
            "not installed; Python 3.13 on Windows commonly falls back to a slow "
            "source build. Use Python 3.12 with the CPU wheel, or install the "
            "compiler toolchain."
        )
    return (
        "not installed; install the optional local-llm extra and a compatible "
        "wheel or compiler toolchain"
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
            "local_llm",
            _has("llama_cpp"),
            _local_llm_detail(),
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
            "html",
            True,
            "local visible-text extraction; scripts and styles ignored",
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
