from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import yaml

# This is the container-internal tmpfs mountpoint required by the quarantine
# contract, not a host-side temporary-file creation path.
QUARANTINE_TMP = "/tmp"  # noqa: S108  # nosec B108


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


def _safe_environment(value: object) -> bool:
    """Allow only explicitly blanked variables plus a non-secret HOME override."""
    if value in (None, [], {}):
        return True
    if not isinstance(value, dict):
        return False
    for key, raw in value.items():
        if not isinstance(key, str):
            return False
        if key == "HOME" and raw == QUARANTINE_TMP:
            continue
        if raw not in ("", None):
            return False
    return True


def validate_quarantine_compose(text: str) -> QuarantineContractResult:
    """Validate the dedicated no-network quarantine service.

    This contract is stricter than the general deployment contract: quarantined
    input is read-only, writable state is disposable tmpfs, networking and Linux
    capabilities are removed, the process runs non-root, resource use is bounded,
    and no non-empty credential/environment values are forwarded.
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
    service = services.get("quarantine")
    if not isinstance(service, dict):
        return QuarantineContractResult(False, ["missing_quarantine_service"], {})

    violations: list[str] = []
    if service.get("network_mode") != "none":
        violations.append("network_must_be_disabled")
    if service.get("read_only") is not True:
        violations.append("root_filesystem_must_be_read_only")

    user = service.get("user")
    if not isinstance(user, str) or user.split(":", 1)[0] in {"", "0", "root"}:
        violations.append("quarantine_must_run_non_root")
    if service.get("working_dir") != "/scratch":
        violations.append("working_directory_must_be_scratch")

    try:
        cap_drop = {item.upper() for item in _as_string_list(service.get("cap_drop"))}
        security_opt = {
            item.lower().replace("=", ":")
            for item in _as_string_list(service.get("security_opt"))
        }
        tmpfs = _as_string_list(service.get("tmpfs"))
    except ValueError:
        return QuarantineContractResult(False, ["invalid_security_list_syntax"], {})

    if "ALL" not in cap_drop:
        violations.append("all_linux_capabilities_must_be_dropped")
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
        if any(
            marker in item.lower()
            for marker in (
                ".ssh",
                ".aws",
                ".config/gcloud",
                ".azure",
                ".kube",
                "docker.sock",
            )
        ):
            forbidden_mount = True
    if not input_read_only:
        violations.append("read_only_quarantine_input_required")
    if forbidden_mount:
        violations.append("forbidden_sensitive_mount")

    environment_safe = _safe_environment(service.get("environment"))
    if not environment_safe:
        violations.append("non_empty_environment_value_forbidden")

    scratch_entries = [item for item in tmpfs if item.startswith("/scratch")]
    if not scratch_entries:
        violations.append("bounded_scratch_tmpfs_required")
    elif not any("size=" in item for item in scratch_entries):
        violations.append("scratch_tmpfs_size_limit_required")

    tmp_entries = [item for item in tmpfs if item.startswith(QUARANTINE_TMP)]
    if not tmp_entries:
        violations.append("bounded_tmp_tmpfs_required")

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
        "non_root": isinstance(user, str) and user.split(":", 1)[0] not in {"", "0", "root"},
        "input_read_only": input_read_only,
        "environment_safe": environment_safe,
        "scratch_tmpfs": bool(scratch_entries),
        "pids_limit": pids_limit,
        "mem_limit": mem_limit,
        "cpus": cpus,
    }
    return QuarantineContractResult(not violations, violations, properties)
