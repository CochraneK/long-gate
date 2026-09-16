import json
from pathlib import Path

from longgate.model_vault import (
    MODEL_CATALOG,
    recommend_model,
    resolve_model_path,
    setup_model,
    verify_model,
)
from longgate.onboarding import AI_SETUP_PROMPT
from longgate.utils import sha256_file


def test_catalog_has_valid_sha256_values():
    for spec in MODEL_CATALOG.values():
        assert len(spec.sha256) == 64
        int(spec.sha256, 16)
        assert spec.license == "Apache-2.0"


def test_recommendations_scale_with_ram():
    assert (
        recommend_model(
            8
        )["primary"]["alias"]
        == "qwen3-4b"
    )
    assert (
        recommend_model(
            16
        )["primary"]["alias"]
        == "qwen3-8b"
    )
    assert (
        recommend_model(
            32
        )["primary"]["alias"]
        == "qwen3-14b"
    )


def test_resolve_manual_model_path(
    tmp_path: Path,
):
    model = (
        tmp_path
        / "manual.gguf"
    )
    model.write_bytes(
        b"GGUF-test"
    )
    assert (
        resolve_model_path(
            model
        )
        == model.resolve()
    )


def test_verify_model_detects_manifest_tampering(
    tmp_path: Path,
    monkeypatch,
):
    model = (
        tmp_path
        / "fake.gguf"
    )
    model.write_bytes(
        b"first"
    )
    manifest = {
        "format": "long-gate-model-vault-v1",
        "models": {
            "fake": {
                "filename": "fake.gguf",
                "sha256": sha256_file(
                    model
                ),
            }
        },
    }
    (
        tmp_path
        / "manifest.json"
    ).write_text(
        json.dumps(
            manifest
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv(
        "LONGGATE_MODEL_VAULT",
        str(tmp_path),
    )

    assert (
        verify_model(
            "fake"
        )["verified"]
        is True
    )

    model.write_bytes(
        b"changed"
    )
    assert (
        verify_model(
            "fake"
        )["verified"]
        is False
    )


def test_ai_setup_prompt_forbids_private_data_access():
    lower = AI_SETUP_PROMPT.lower()
    assert "do not open" in lower
    assert "sensitive data" in lower
    assert "longgate model recommend" in lower
    assert "longgate model verify" in lower


def test_auto_resolution_uses_verified_default_model(
    tmp_path: Path,
    monkeypatch,
):
    model = tmp_path / "default.gguf"
    model.write_bytes(
        b"default-model"
    )
    manifest = {
        "format": "long-gate-model-vault-v1",
        "default_model": "fake",
        "models": {
            "fake": {
                "filename": "default.gguf",
                "sha256": sha256_file(
                    model
                ),
            }
        },
    }
    (
        tmp_path
        / "manifest.json"
    ).write_text(
        json.dumps(
            manifest
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv(
        "LONGGATE_MODEL_VAULT",
        str(tmp_path),
    )

    assert (
        resolve_model_path(
            "auto"
        )
        == model.resolve()
    )


def test_setup_model_uses_recommendation_and_verification(
    monkeypatch,
):
    monkeypatch.setattr(
        "longgate.model_vault.install_model",
        lambda alias, vault: {
            "alias": alias,
            "verified": True,
        },
    )
    monkeypatch.setattr(
        "longgate.model_vault.verify_model",
        lambda alias, vault: {
            "alias": alias,
            "verified": True,
            "path": "/models/fake.gguf",
        },
    )

    result = setup_model(
        ram_gb=8,
        vault_dir="/models",
    )
    assert result["status"] == "READY"
    assert (
        result["default_model"]
        == "qwen3-4b"
    )
    assert "--model auto" in result[
        "private_processing_example"
    ]
