from __future__ import annotations

from pathlib import Path

from .hardware import HardwareProfile, detect_hardware
from .model_vault import MODEL_CATALOG, default_vault_dir, recommend_model, setup_model


def _existing_disk_root(path: Path) -> Path:
    candidate = path.expanduser().resolve()
    while not candidate.exists() and candidate != candidate.parent:
        candidate = candidate.parent
    return candidate


def _fit_label(ram_gb: float | None, alias: str) -> str:
    spec = MODEL_CATALOG[alias]
    if ram_gb is None:
        return "UNKNOWN"
    if ram_gb < spec.min_ram_gb:
        return "INSUFFICIENT"
    if ram_gb < spec.recommended_ram_gb:
        return "TIGHT"
    return "COMFORTABLE"


def hardware_advice(
    *,
    ram_gb: float | None = None,
    vault_dir: str | Path | None = None,
) -> dict[str, object]:
    vault = (
        Path(vault_dir).expanduser().resolve()
        if vault_dir
        else default_vault_dir()
    )
    profile = detect_hardware(
        _existing_disk_root(vault),
        ram_gb=ram_gb,
    )
    recommendation = recommend_model(profile.ram_gb)
    selected_alias = str(recommendation["primary"]["alias"])

    tier_aliases = [
        ("FAST", "qwen3-4b"),
        ("BALANCED", "qwen3-8b"),
        ("QUALITY", "qwen3-14b"),
    ]
    tiers: list[dict[str, object]] = []
    for tier, alias in tier_aliases:
        spec = MODEL_CATALOG[alias]
        tiers.append(
            {
                "tier": tier,
                "alias": alias,
                "model_file": spec.filename,
                "size_gb": spec.size_gb,
                "min_ram_gb": spec.min_ram_gb,
                "recommended_ram_gb": spec.recommended_ram_gb,
                "fit": _fit_label(profile.ram_gb, alias),
                "selected": alias == selected_alias,
            }
        )

    gpu_note = (
        "Detected NVIDIA GPU information is advisory only; the current model "
        "selection remains conservative and RAM-led because llama.cpp offload "
        "availability depends on the local build."
        if profile.gpus
        else "No NVIDIA GPU was detected through local nvidia-smi; CPU-only use remains supported."
    )

    return {
        "hardware": profile.to_dict(),
        "vault": str(vault),
        "recommended_model": recommendation,
        "tiers": tiers,
        "gpu_note": gpu_note,
        "privacy_note": (
            "Hardware inspection is local-only. Long Gate does not upload hardware "
            "inventory or use a network hardware-detection service."
        ),
    }


def setup_local_ai(
    *,
    ram_gb: float | None = None,
    vault_dir: str | Path | None = None,
) -> dict[str, object]:
    advice = hardware_advice(ram_gb=ram_gb, vault_dir=vault_dir)
    hardware = advice["hardware"]
    detected_ram = hardware["ram_gb"] if isinstance(hardware, dict) else ram_gb
    model_setup = setup_model(
        ram_gb=(float(detected_ram) if detected_ram is not None else None),
        vault_dir=vault_dir,
    )
    return {
        "status": "READY",
        "advisor": advice,
        "model_setup": model_setup,
        "next": {
            "deidentify": (
                "longgate deidentify interview.txt --model auto --out deidentified.txt"
            ),
            "structured": "longgate run study.csv --profile research --backend auto",
        },
        "security_note": (
            "Setup mode may use the network to install the pinned model. Do not "
            "mount or open private data during setup. Private processing resolves "
            "the verified local model and should run without network capability."
        ),
    }
