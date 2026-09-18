from __future__ import annotations

import importlib
import platform
import shutil
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class Capability:
    name: str
    available: bool
    detail: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _has(module: str) -> bool:
    """Perform a real import check instead of trusting import metadata alone."""
    try:
        importlib.import_module(module)
    except (ImportError, OSError):
        return False
    return True


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
        Capability("python", True, sys.version.split()[0]),
        Capability("mostlyai", _has("mostlyai"), "local synthetic backend"),
        Capability("synthcity", _has("synthcity"), "local synthetic backend"),
        Capability("presidio", _has("presidio_analyzer"), "enhanced local PII detection"),
        Capability("statsmodels", _has("statsmodels"), "local exact Python OLS"),
        Capability(
            "rscript",
            shutil.which("Rscript") is not None,
            "fixed-template local R exact engine; no arbitrary R code",
        ),
        Capability("local_llm", _has("llama_cpp"), _local_llm_detail()),
        Capability(
            "documents",
            _has("docx") and _has("pypdf"),
            "local DOCX/PDF text-layer inspection",
        ),
        Capability(
            "html",
            True,
            "local visible-text extraction; scripts and styles ignored",
        ),
        Capability("pyarrow", _has("pyarrow"), "Parquet support"),
    ]


def deep_local_llm_check(model_path: str | Path = "auto") -> Capability:
    """Verify import, model resolution, file presence, and a tiny local inference."""
    if not _has("llama_cpp"):
        return Capability(
            "local_llm_deep",
            False,
            "llama_cpp could not be imported; no model inference attempted",
        )

    try:
        from .model_vault import resolve_model_path
        from .semantic import LocalLlamaCppTransformer

        resolved = resolve_model_path(model_path)
        if not resolved.is_file():
            return Capability("local_llm_deep", False, "resolved model file is missing")
        transformer = LocalLlamaCppTransformer(resolved, n_ctx=512, max_input_characters=1000)
        output = transformer.transform(
            "A generic non-sensitive system-check sentence for local inference.",
            max_tokens=64,
        )
    except Exception as exc:
        return Capability(
            "local_llm_deep",
            False,
            f"{type(exc).__name__}: local import/model/inference check failed",
        )

    return Capability(
        "local_llm_deep",
        bool(output.strip()),
        f"verified local model file and minimal inference: {resolved.name}",
    )


def choose_backend() -> str:
    """Prefer mature local backends; demo fallback stays fail-closed."""
    if _has("mostlyai"):
        return "mostlyai"
    if _has("synthcity"):
        return "synthcity"
    return "demo"
