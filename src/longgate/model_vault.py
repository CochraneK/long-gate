from __future__ import annotations

import json
import os
import platform
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .utils import sha256_file, utc_now, write_json


@dataclass(frozen=True)
class ModelSpec:
    alias: str
    repo_id: str
    filename: str
    sha256: str
    size_gb: float
    min_ram_gb: float
    recommended_ram_gb: float
    license: str
    description: str
    revision: str

    @property
    def source_url(self) -> str:
        return (
            "https://huggingface.co/"
            f"{self.repo_id}/blob/{self.revision}/{self.filename}"
        )

    def to_dict(self) -> dict[str, object]:
        return {
            **asdict(self),
            "source_url": self.source_url,
        }


MODEL_CATALOG: dict[str, ModelSpec] = {
    "qwen3-4b": ModelSpec(
        alias="qwen3-4b",
        repo_id="Qwen/Qwen3-4B-GGUF",
        filename="Qwen3-4B-Q4_K_M.gguf",
        sha256=(
            "7485fe6f11af29433bc51cab58009521"
            "f205840f5b4ae3a32fa7f92e8534fdf5"
        ),
        size_gb=2.50,
        min_ram_gb=6.0,
        recommended_ram_gb=8.0,
        license="Apache-2.0",
        description=(
            "Default lightweight multilingual option. "
            "Recommended for typical laptops and first-time setup."
        ),
        revision="a9a60d009fa7ff9606305047c2bf77ac25dbec49",
    ),
    "qwen3-8b": ModelSpec(
        alias="qwen3-8b",
        repo_id="Qwen/Qwen3-8B-GGUF",
        filename="Qwen3-8B-Q4_K_M.gguf",
        sha256=(
            "d98cdcbd03e17ce47681435b5150e34c"
            "1417f50b5c0019dd560e4882c5745785"
        ),
        size_gb=5.03,
        min_ram_gb=10.0,
        recommended_ram_gb=16.0,
        license="Apache-2.0",
        description=(
            "Balanced local option for machines with more memory."
        ),
        revision="6a569868d07d3bd59e8b97fb001bf8c0b254bb20",
    ),
    "qwen3-14b": ModelSpec(
        alias="qwen3-14b",
        repo_id="Qwen/Qwen3-14B-GGUF",
        filename="Qwen3-14B-Q4_K_M.gguf",
        sha256=(
            "500a8806e85ee9c83f3ae084202955924"
            "51379b4f8cf2d0f41c15dffeb6b81f0"
        ),
        size_gb=9.00,
        min_ram_gb=18.0,
        recommended_ram_gb=24.0,
        license="Apache-2.0",
        description=(
            "Higher-capacity local option for well-provisioned machines."
        ),
        revision="c75e7b2d0234068f674a1bacf548ea32e27ccd29",
    ),
}


def default_vault_dir() -> Path:
    configured = os.environ.get(
        "LONGGATE_MODEL_VAULT"
    )
    if configured:
        return Path(
            configured
        ).expanduser().resolve()
    return (
        Path.home()
        / ".longgate"
        / "models"
    ).resolve()


def _manifest_path(
    vault_dir: str | Path | None = None,
) -> Path:
    root = (
        Path(vault_dir).expanduser().resolve()
        if vault_dir
        else default_vault_dir()
    )
    return root / "manifest.json"


def _load_manifest(
    vault_dir: str | Path | None = None,
) -> dict[str, Any]:
    path = _manifest_path(
        vault_dir
    )
    if not path.is_file():
        return {
            "format": "long-gate-model-vault-v1",
            "default_model": None,
            "models": {},
        }
    data = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )
    if data.get("format") != "long-gate-model-vault-v1":
        raise RuntimeError(
            "Unsupported Model Vault manifest format."
        )
    if not isinstance(
        data.get("models"),
        dict,
    ):
        raise TypeError(
            "Invalid Model Vault manifest."
        )
    return data


def _write_manifest(
    data: dict[str, Any],
    vault_dir: str | Path | None = None,
) -> Path:
    path = _manifest_path(
        vault_dir
    )
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    write_json(
        path,
        data,
    )
    return path


def get_model_spec(
    alias: str,
) -> ModelSpec:
    try:
        return MODEL_CATALOG[
            alias.strip().lower()
        ]
    except KeyError as exc:
        raise ValueError(
            f"Unknown model alias: {alias!r}. "
            f"Available: {', '.join(sorted(MODEL_CATALOG))}"
        ) from exc


def catalog() -> list[dict[str, object]]:
    return [
        MODEL_CATALOG[alias].to_dict()
        for alias in sorted(
            MODEL_CATALOG
        )
    ]


def _windows_ram_gb() -> float | None:
    if platform.system() != "Windows":
        return None
    try:
        import ctypes

        class MemoryStatus(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                (
                    "ullTotalPhys",
                    ctypes.c_ulonglong,
                ),
                (
                    "ullAvailPhys",
                    ctypes.c_ulonglong,
                ),
                (
                    "ullTotalPageFile",
                    ctypes.c_ulonglong,
                ),
                (
                    "ullAvailPageFile",
                    ctypes.c_ulonglong,
                ),
                (
                    "ullTotalVirtual",
                    ctypes.c_ulonglong,
                ),
                (
                    "ullAvailVirtual",
                    ctypes.c_ulonglong,
                ),
                (
                    "ullAvailExtendedVirtual",
                    ctypes.c_ulonglong,
                ),
            ]

        status = MemoryStatus()
        status.dwLength = ctypes.sizeof(
            MemoryStatus
        )
        ok = ctypes.windll.kernel32.GlobalMemoryStatusEx(  # type: ignore[attr-defined]
            ctypes.byref(status)
        )
        if not ok:
            return None
        return round(
            status.ullTotalPhys
            / (1024**3),
            2,
        )
    except (
        AttributeError,
        OSError,
        TypeError,
        ValueError,
    ):
        return None


def detect_system_ram_gb() -> float | None:
    windows = _windows_ram_gb()
    if windows is not None:
        return windows

    try:
        page_size = os.sysconf(
            "SC_PAGE_SIZE"
        )
        pages = os.sysconf(
            "SC_PHYS_PAGES"
        )
        return round(
            (
                int(page_size)
                * int(pages)
            )
            / (1024**3),
            2,
        )
    except (
        AttributeError,
        OSError,
        TypeError,
        ValueError,
    ):
        return None


def recommend_model(
    ram_gb: float | None = None,
) -> dict[str, object]:
    detected = (
        float(ram_gb)
        if ram_gb is not None
        else detect_system_ram_gb()
    )

    if detected is None:
        primary = MODEL_CATALOG[
            "qwen3-4b"
        ]
        reason = (
            "System RAM could not be detected; "
            "use the lightweight default or pass --ram-gb."
        )
    elif detected < 6:
        primary = MODEL_CATALOG[
            "qwen3-4b"
        ]
        reason = (
            "Less than 6 GB RAM was detected. "
            "The 4B model is the smallest built-in option, "
            "but memory pressure may still be high."
        )
    elif detected < 14:
        primary = MODEL_CATALOG[
            "qwen3-4b"
        ]
        reason = (
            "The 4B Q4_K_M model is the conservative fit "
            "for this amount of system RAM."
        )
    elif detected < 24:
        primary = MODEL_CATALOG[
            "qwen3-8b"
        ]
        reason = (
            "The 8B Q4_K_M model is the balanced fit "
            "for this amount of system RAM."
        )
    else:
        primary = MODEL_CATALOG[
            "qwen3-14b"
        ]
        reason = (
            "The 14B Q4_K_M model is the higher-capacity "
            "built-in recommendation for this amount of RAM."
        )

    return {
        "detected_ram_gb": detected,
        "primary": primary.to_dict(),
        "reason": reason,
        "install_command": (
            f"longgate model install {primary.alias}"
        ),
        "verify_command": (
            f"longgate model verify {primary.alias}"
        ),
        "note": (
            "RAM guidance is conservative and approximate. "
            "CPU/GPU speed, context length, and other applications "
            "also affect local inference."
        ),
    }


def list_installed(
    vault_dir: str | Path | None = None,
) -> list[dict[str, object]]:
    manifest = _load_manifest(
        vault_dir
    )
    root = _manifest_path(
        vault_dir
    ).parent
    rows: list[dict[str, object]] = []
    for alias, entry in sorted(
        manifest["models"].items()
    ):
        filename = str(
            entry["filename"]
        )
        path = root / filename
        rows.append(
            {
                "alias": alias,
                **entry,
                "path": str(path),
                "exists": path.is_file(),
                "default": (
                    manifest.get("default_model")
                    == alias
                ),
            }
        )
    return rows


def _disk_preflight(
    root: Path,
    spec: ModelSpec,
) -> dict[str, float]:
    usage = shutil.disk_usage(
        root
    )
    free_gb = round(
        usage.free / 1_000_000_000,
        2,
    )
    required_gb = round(
        spec.size_gb + 1.0,
        2,
    )
    if free_gb < required_gb:
        raise OSError(
            "Not enough free space in the Model Vault. "
            f"Model={spec.alias}, free={free_gb} GB, "
            f"required≈{required_gb} GB. "
            "Choose a smaller model or move LONGGATE_MODEL_VAULT "
            "to a drive with more free space."
        )
    return {
        "free_gb": free_gb,
        "required_gb": required_gb,
    }


def install_model(
    alias: str,
    vault_dir: str | Path | None = None,
) -> dict[str, object]:
    """Download a catalog model in explicit network-enabled setup mode.

    This function accepts no private-data path. Hardened deployments should
    run it in a setup worker that has network access and no private mount.
    """
    spec = get_model_spec(
        alias
    )
    try:
        from huggingface_hub import hf_hub_download
    except ImportError as exc:
        raise RuntimeError(
            "Model installation requires: "
            "pip install 'long-gate[models]'"
        ) from exc

    root = _manifest_path(
        vault_dir
    ).parent
    root.mkdir(
        parents=True,
        exist_ok=True,
    )
    destination = (
        root / spec.filename
    )

    if destination.is_file():
        actual = sha256_file(
            destination
        )
        if actual == spec.sha256:
            manifest = _load_manifest(
                root
            )
            manifest["models"][
                spec.alias
            ] = {
                "filename": spec.filename,
                "sha256": actual,
                "repo_id": spec.repo_id,
                "revision": spec.revision,
                "source_url": spec.source_url,
                "license": spec.license,
                "size_gb": spec.size_gb,
                "installed_at": manifest[
                    "models"
                ].get(
                    spec.alias,
                    {},
                ).get(
                    "installed_at",
                    utc_now(),
                ),
            }
            manifest["default_model"] = spec.alias
            _write_manifest(
                manifest,
                root,
            )
            return {
                "alias": spec.alias,
                "path": str(destination),
                "sha256": actual,
                "verified": True,
                "downloaded": False,
                "network_mode": "setup-only",
            }
        raise RuntimeError(
            "Existing model file failed the catalog SHA-256 check. "
            "Move or delete it before reinstalling."
        )

    disk_preflight = _disk_preflight(
        root,
        spec,
    )

    staging = (
        root
        / ".staging"
        / spec.alias
    )
    if staging.exists():
        shutil.rmtree(
            staging
        )
    staging.mkdir(
        parents=True,
        exist_ok=True,
    )

    try:
        downloaded = Path(
            hf_hub_download(
                repo_id=spec.repo_id,
                filename=spec.filename,
                revision=spec.revision,
                local_dir=staging,
            )
        )
        actual = sha256_file(
            downloaded
        )
        if actual != spec.sha256:
            raise RuntimeError(
                "Downloaded model SHA-256 does not match the "
                "Long Gate catalog. Installation aborted."
            )
        downloaded.replace(
            destination
        )
    finally:
        shutil.rmtree(
            staging,
            ignore_errors=True,
        )

    manifest = _load_manifest(
        root
    )
    manifest["models"][
        spec.alias
    ] = {
        "filename": spec.filename,
        "sha256": spec.sha256,
        "repo_id": spec.repo_id,
        "revision": spec.revision,
        "source_url": spec.source_url,
        "license": spec.license,
        "size_gb": spec.size_gb,
        "installed_at": utc_now(),
    }
    manifest["default_model"] = spec.alias
    _write_manifest(
        manifest,
        root,
    )

    return {
        "alias": spec.alias,
        "path": str(destination),
        "sha256": spec.sha256,
        "verified": True,
        "downloaded": True,
        "network_mode": "setup-only",
        "disk_preflight": disk_preflight,
    }


def _resolve_alias(
    alias: str,
    manifest: dict[str, Any],
) -> str:
    normalized = alias.strip().lower()
    if normalized != "auto":
        return normalized

    default_model = manifest.get(
        "default_model"
    )
    if not default_model:
        raise FileNotFoundError(
            "No default model is configured. "
            "Run: longgate model setup"
        )
    return str(
        default_model
    )


def verify_model(
    alias: str,
    vault_dir: str | Path | None = None,
) -> dict[str, object]:
    manifest = _load_manifest(
        vault_dir
    )
    resolved_alias = _resolve_alias(
        alias,
        manifest,
    )
    entry = manifest[
        "models"
    ].get(
        resolved_alias
    )
    if not entry:
        raise FileNotFoundError(
            f"Model {resolved_alias!r} is not registered in the Model Vault."
        )

    root = _manifest_path(
        vault_dir
    ).parent
    path = (
        root
        / str(
            entry["filename"]
        )
    )
    if not path.is_file():
        return {
            "alias": resolved_alias,
            "path": str(path),
            "exists": False,
            "verified": False,
            "reason": "model file is missing",
        }

    actual = sha256_file(
        path
    )
    expected = str(
        entry["sha256"]
    )
    return {
        "alias": resolved_alias,
        "path": str(path),
        "exists": True,
        "verified": actual == expected,
        "expected_sha256": expected,
        "actual_sha256": actual,
    }


def setup_model(
    ram_gb: float | None = None,
    vault_dir: str | Path | None = None,
) -> dict[str, object]:
    """Recommend, install, verify, and set the local default model."""
    recommendation = recommend_model(
        ram_gb
    )
    primary = recommendation[
        "primary"
    ]
    alias = str(
        primary["alias"]
    )
    installed = install_model(
        alias,
        vault_dir,
    )
    verification = verify_model(
        alias,
        vault_dir,
    )
    if not verification[
        "verified"
    ]:
        raise RuntimeError(
            "Model setup finished downloading but verification failed."
        )

    return {
        "status": "READY",
        "detected_ram_gb": recommendation[
            "detected_ram_gb"
        ],
        "default_model": alias,
        "model": primary,
        "installation": installed,
        "verification": verification,
        "private_processing_example": (
            "longgate semantic-transform-local interview.txt "
            "--model auto --out preview.txt"
        ),
        "security_note": (
            "Setup mode may use the network. "
            "Private processing resolves the verified local default "
            "and performs no model download."
        ),
    }


def resolve_model_path(
    reference: str | Path,
) -> Path:
    """Resolve a manual GGUF path or a verified Model Vault alias.

    This function never downloads anything.
    """
    manual = Path(
        reference
    ).expanduser()
    if manual.is_file():
        return manual.resolve()

    alias = str(
        reference
    ).strip().lower()
    verification = verify_model(
        alias
    )
    if not verification[
        "verified"
    ]:
        raise RuntimeError(
            f"Model Vault entry {alias!r} failed verification."
        )
    return Path(
        str(
            verification["path"]
        )
    ).resolve()
