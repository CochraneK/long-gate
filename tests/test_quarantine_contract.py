from pathlib import Path

from longgate.quarantine_contract import validate_quarantine_compose


ROOT = Path(__file__).parents[1]


def test_quarantine_compose_meets_strict_contract():
    text = (ROOT / "docker-compose.quarantine.yml").read_text(encoding="utf-8")
    result = validate_quarantine_compose(text)

    assert result.valid is True
    assert result.violations == []
    assert result.properties["network_disabled"] is True
    assert result.properties["non_root"] is True
    assert result.properties["input_read_only"] is True
    assert result.properties["environment_safe"] is True


def test_quarantine_contract_rejects_network_and_secret_environment():
    text = """services:
  quarantine:
    read_only: true
    user: "65534:65534"
    working_dir: /scratch
    cap_drop: [ALL]
    security_opt: ["no-new-privileges:true"]
    environment:
      OPENAI_API_KEY: real-secret
    volumes:
      - ./samples:/quarantine/input:ro
    tmpfs:
      - /tmp:size=64m
      - /scratch:size=256m
    pids_limit: 64
    mem_limit: 512m
    cpus: "1.0"
"""
    result = validate_quarantine_compose(text)

    assert result.valid is False
    assert "network_must_be_disabled" in result.violations
    assert "non_empty_environment_value_forbidden" in result.violations


def test_quarantine_contract_rejects_sensitive_mounts_and_root():
    text = """services:
  quarantine:
    network_mode: none
    read_only: true
    user: "0:0"
    working_dir: /scratch
    cap_drop: [ALL]
    security_opt: ["no-new-privileges:true"]
    environment: []
    volumes:
      - ./samples:/quarantine/input:ro
      - ./models:/models:ro
    tmpfs:
      - /tmp:size=64m
      - /scratch:size=256m
    pids_limit: 64
    mem_limit: 512m
    cpus: "1.0"
"""
    result = validate_quarantine_compose(text)

    assert result.valid is False
    assert "forbidden_sensitive_mount" in result.violations
    assert "quarantine_must_run_non_root" in result.violations
