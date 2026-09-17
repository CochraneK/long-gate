from pathlib import Path

from longgate.advisor import hardware_advice, setup_local_ai
from longgate.hardware import GPUInfo, HardwareProfile, detect_hardware, detect_nvidia_gpus


def _profile(ram_gb: float) -> HardwareProfile:
    return HardwareProfile(
        system="TestOS",
        release="1",
        architecture="x86_64",
        processor="Test CPU",
        logical_cpus=8,
        ram_gb=ram_gb,
        free_disk_gb=100.0,
        disk_path="/",
        gpus=[],
    )


def test_hardware_advice_selects_balanced_model_for_16gb(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(
        "longgate.advisor.detect_hardware",
        lambda *_args, **_kwargs: _profile(16.0),
    )

    result = hardware_advice(vault_dir=tmp_path)

    assert result["recommended_model"]["primary"]["alias"] == "qwen3-8b"
    selected = [tier for tier in result["tiers"] if tier["selected"]]
    assert len(selected) == 1
    assert selected[0]["tier"] == "BALANCED"
    assert selected[0]["fit"] == "COMFORTABLE"


def test_detect_nvidia_gpus_is_best_effort(monkeypatch):
    class Result:
        stdout = "NVIDIA Test GPU, 8192\n"

    monkeypatch.setattr("longgate.hardware.shutil.which", lambda _name: "/bin/nvidia-smi")
    monkeypatch.setattr(
        "longgate.hardware.subprocess.run",
        lambda *_args, **_kwargs: Result(),
    )

    gpus = detect_nvidia_gpus()

    assert gpus == [GPUInfo(name="NVIDIA Test GPU", vram_gb=8.0, source="nvidia-smi")]


def test_hardware_output_does_not_expose_full_local_directory(monkeypatch, tmp_path: Path):
    monkeypatch.setattr("longgate.hardware.detect_nvidia_gpus", lambda: [])

    profile = detect_hardware(tmp_path / "private-user" / "models", ram_gb=16)

    assert "private-user" not in profile.disk_path
    assert "models" not in profile.disk_path


def test_setup_local_ai_uses_detected_ram(monkeypatch, tmp_path: Path):
    advice = {
        "hardware": _profile(32.0).to_dict(),
        "recommended_model": {"primary": {"alias": "qwen3-14b"}},
        "tiers": [],
    }
    captured = {}

    monkeypatch.setattr("longgate.advisor.hardware_advice", lambda **_kwargs: advice)

    def fake_setup_model(ram_gb, vault_dir):
        captured["ram_gb"] = ram_gb
        captured["vault_dir"] = vault_dir
        return {"status": "READY", "default_model": "qwen3-14b"}

    monkeypatch.setattr("longgate.advisor.setup_model", fake_setup_model)

    result = setup_local_ai(vault_dir=tmp_path)

    assert captured["ram_gb"] == 32.0
    assert captured["vault_dir"] == tmp_path
    assert result["status"] == "READY"
    assert "longgate deidentify" in result["next"]["deidentify"]
