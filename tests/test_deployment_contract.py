from pathlib import Path

from longgate.deployment_contract import validate_compose_capability_contract

ROOT = Path(__file__).parents[1]


def test_hardened_compose_separates_raw_and_network_capabilities():
    text = (
        ROOT
        / "docker-compose.hardened.yml"
    ).read_text(
        encoding="utf-8"
    )

    local_block, cloud_block = text.split(
        "  cloud-worker:",
        maxsplit=1,
    )

    assert "network_mode: none" in local_block
    assert "/private:ro" in local_block
    assert "/models:ro" in local_block
    assert "LONGGATE_MODEL_VAULT: /models" in local_block

    assert "/private:ro" not in cloud_block
    assert "/models" not in cloud_block
    assert (
        "LONGGATE_PRIVATE_DIR"
        not in cloud_block.split(
            "# Security invariant:",
            maxsplit=1,
        )[0]
    )
    assert "/safe:ro" in cloud_block
    assert "/policy/approvals.jsonl:ro" in cloud_block
    assert "LONGGATE_APPROVAL_LEDGER: /policy/approvals.jsonl" in cloud_block
    assert "LONGGATE_ACCESS_LOG: /access/access.jsonl" in cloud_block
    assert "Dockerfile.network" in cloud_block


def test_model_setup_worker_has_network_but_no_private_mount():
    text = (
        ROOT
        / "docker-compose.model-setup.yml"
    ).read_text(
        encoding="utf-8"
    )

    service_block = text.split(
        "# Security boundary:",
        maxsplit=1,
    )[0]

    assert "network_mode: none" not in service_block
    assert "LONGGATE_MODEL_VAULT: /models" in service_block
    assert ":/models" in service_block
    assert "LONGGATE_PRIVATE_DIR" not in service_block
    assert "/private" not in service_block

    assert "      - model\n      - setup" in service_block


def test_private_and_setup_workers_never_share_capability_sets():
    private_text = (
        ROOT
        / "docker-compose.hardened.yml"
    ).read_text(
        encoding="utf-8"
    )
    setup_text = (
        ROOT
        / "docker-compose.model-setup.yml"
    ).read_text(
        encoding="utf-8"
    )

    private_block = private_text.split(
        "  cloud-worker:",
        maxsplit=1,
    )[0]
    setup_block = setup_text.split(
        "# Security boundary:",
        maxsplit=1,
    )[0]

    assert "network_mode: none" in private_block
    assert "/private:ro" in private_block
    assert "/models:ro" in private_block

    assert "network_mode: none" not in setup_block
    assert "/private" not in setup_block
    assert ":/models" in setup_block
    assert ":/models:ro" not in setup_block



def test_capability_validator_accepts_hardened_compose():
    text = (
        ROOT
        / "docker-compose.hardened.yml"
    ).read_text(encoding="utf-8")
    result = validate_compose_capability_contract(text)
    assert result.valid is True
    assert result.violations == []


def test_capability_validator_rejects_mutated_cloud_private_mount():
    text = (
        ROOT
        / "docker-compose.hardened.yml"
    ).read_text(encoding="utf-8")
    mutated = text.replace(
        "      - ./safe:/safe:ro",
        "      - ./safe:/safe:ro\n      - ./private:/private:ro",
        1,
    )
    result = validate_compose_capability_contract(mutated)
    assert result.valid is False
    assert any(
        item["code"] == "private_data_with_network"
        for item in result.violations
    )


def test_capability_validator_rejects_private_model_write_combo():
    text = """services:
  worker:
    network_mode: none
    volumes:
      - ./private:/private:ro
      - ./models:/models
"""
    result = validate_compose_capability_contract(text)
    assert result.valid is False
    assert any(
        item["code"] == "private_data_with_model_vault_write"
        for item in result.violations
    )
