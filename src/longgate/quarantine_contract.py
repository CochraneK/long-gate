from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import yaml


@dataclass(frozen=True)
class QuarantineContractResult:
    valid: bool
    violations: list[str]
    properties: dict[str, object]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _as_string_list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return value
    raise ValueError("expected a string or list of strings")


def validate_quarantine_compose(text: str) -> QuarantineContractResult:
    """Validate the dedicated no-network quarantine service.

    This contract is intentionally stricter than the general deployment contract:
    the quarantine service receives only a read-only input mount plus bounded tmpfs.
    It does not inherit host secrets, receive Model Vault/safe-workspace mounts,
    or obtain network capability.
    """
    try:
        document = yaml.safe_load(text)
    except yaml.YAMLError:
        return QuarantineContractResult(False, ["invalid_yaml"], {})

    if not isinstance(document, dict):
        return QuarantineContractResult(False, ["invalid_document"], {})
    services = document.get("services")
    if not isinstance(services, dict):
        return QuarantineContractResult(False, ["missing_services"], {})
    service = services.get("quarantine-inspector")
    if not isinstance(service, dict):
        return QuarantineContractResult(False, ["missing_quarantine_service"], {})

    violations: list[str] = []
    if service.get("network_mode") != "none":
        violations.append("network_must_be_disabled")
    if service.get("read_only") is not True:
        violations.append("root_filesystem_must_be_read_only")

    cap_drop = {item.upper() for item in _as_string_list(service.get("cap_drop"))}
    if "ALL" not in cap_drop:
        violations.append("all_linux_capabilities_must_be_dropped")

    security_opt = {
        item.lower().replace("=", ":")
        for item in _as_string_list(service.get("security_opt"))
    }
    if not any(
        item in {"no-new-privileges:true", "no-new-privileges"}
        for item in security_opt
    ):
        violations.append("no_new_privileges_required")

    volumes = service.get("volumes", [])
    if not isinstance(volumes, list):
        violations.append("volumes_must_be_list")
        volumes = []

    input_read_only = False
    forbidden_mount = False
    for item in volumes:
        if not isinstance(item, str):
            violations.append("only_short_read_only_volume_syntax_supported")
            continue
        if ":/quarantine/input:ro" in item:
            input_read_only = True
        if any(target in item for target in (":/private", ":/models", ":/safe")):
            forbidden_mount = True
    if not input_read_only:
        violations.append("read_only_quarantine_input_required")
    if forbidden_mount:
        violations.append("forbidden_sensitive_mount")

    environment = service.get("environment")
    if environment not in (None, [], {}):
        violations.append("quarantine_environment_must_be_empty")

    tmpfs = _as_string_list(service.get("tmpfs"))
    if not any(item.startswith("/scratch") for item in tmpfs):
        violations.append("bounded_scratch_tmpfs_required")

    pids_limit = service.get("pids_limit")
    if not isinstance(pids_limit, int) or pids_limit <= 0 or pids_limit > 64:
        violations.append("pids_limit_must_be_1_to_64")

    mem_limit = service.get("mem_limit")
    if not isinstance(mem_limit, str) or not mem_limit:
        violations.append("memory_limit_required")

    cpus = service.get("cpus")
    if not isinstance(cpus, (str, int, float)) or str(cpus).strip() in {"", "0", "0.0"}:
        violations.append("cpu_limit_required")

    properties: dict[str, Any] = {
        "network_disabled": service.get("network_mode") == "none",
        "root_read_only": service.get("read_only") is True,
        "input_read_only": input_read_only,
        "environment_empty": environment in (None, [], {}),
        "scratch_tmpfs": bool(tmpfs),
        "pids_limit": pids_limit,
        "mem_limit": mem_limit,
        "cpus": cpus,
    }
    return QuarantineContractResult(not violations, violations, properties)
