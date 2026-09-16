from pathlib import Path


def test_hardened_compose_separates_raw_and_network_capabilities():
    text = (Path(__file__).parents[1] / "docker-compose.hardened.yml").read_text(encoding="utf-8")

    local_block, cloud_block = text.split("  cloud-worker:", maxsplit=1)
    assert "network_mode: none" in local_block
    assert "/private:ro" in local_block

    assert "/private:ro" not in cloud_block
    assert (
        "LONGGATE_PRIVATE_DIR"
        not in cloud_block.split(
            "# Security invariant:",
            maxsplit=1,
        )[0]
    )
    assert "/safe:ro" in cloud_block
