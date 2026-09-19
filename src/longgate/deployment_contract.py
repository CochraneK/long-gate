from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any

import yaml


@dataclass(frozen=True)
class ServiceCapabilities:
    service: str
    network_disabled: bool
    private_data_capability: bool
    model_vault_read: bool
    model_vault_write: bool
    safe_workspace_read: bool
    safe_workspace_write: bool
    all_capabilities_dropped: bool
    no_new_privileges: bool

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class DeploymentContractResult:
    valid: bool
    services: list[ServiceCapabilities]
    violations: list[dict[str, str]]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


_VOLUME_TARGET_RE = re.compile(
    r":(?P<target>/[^:\n]+)(?::(?P<mode>[^:\n]+))?$"
)


def _string_volume(spec: str) -> tuple[str, str, bool] | None:
    match = _VOLUME_TARGET_RE.search(spec.strip())
    if match is None:
        return None
    target = match.group("target")
    mode = match.group("mode") or "rw"
    read_only = "ro" in {part.strip().lower() for part in mode.split(",")}
    source = spec[: match.start()]
    return source, target, read_only


def _volume_mounts(config: dict[str, Any]) -> list[tuple[str, str, bool]]:
    volumes = config.get("volumes", [])
    if volumes is None:
        return []
    if not isinstance(volumes, list):
        raise ValueError("service volumes must be a list")

    mounts: list[tuple[str, str, bool]] = []
    for volume in volumes:
        if isinstance(volume, str):
            parsed = _string_volume(volume)
            if parsed is None:
                raise ValueError(f"unsupported volume syntax: {volume!r}")
            mounts.append(parsed)
            continue
        if isinstance(volume, dict):
            target = volume.get("target")
            source = volume.get("source", "")
            read_only = volume.get("read_only", False)
            if not isinstance(target, str) or not target.startswith("/"):
                raise ValueError("long-form volume target must be an absolute path")
            if not isinstance(source, str):
                raise ValueError("long-form volume source must be a string")
            if not isinstance(read_only, bool):
                raise ValueError("long-form volume read_only must be boolean")
            mounts.append((source, target, read_only))
            continue
        raise ValueError("service volume entries must be strings or mappings")
    return mounts


def _targets_path(target: str, root: str) -> bool:
    normalized = target.rstrip("/") or "/"
    return normalized == root or normalized.startswith(root + "/")


def _string_list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return value
    raise ValueError("security option must be a string or list of strings")


def _compose_mapping(text: str) -> dict[str, Any]:
    try:
        document = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise ValueError("invalid Compose YAML") from exc
    if not isinstance(document, dict):
        raise ValueError("Compose document must be a mapping")
    services = document.get("services")
    if not isinstance(services, dict) or not services:
        raise ValueError("Compose document must define a non-empty services mapping")
    return services


def validate_compose_capability_contract(text: str) -> DeploymentContractResult:
    """Detect dangerous capability combinations in a Compose document.

    Compose is parsed structurally rather than inspected as text so quoting,
    long-form volume syntax, and YAML merge keys cannot silently bypass the
    capability checks. Features requiring external Compose resolution, such as
    ``extends``, fail closed.
    """
    services: list[ServiceCapabilities] = []
    violations: list[dict[str, str]] = []

    try:
        service_mapping = _compose_mapping(text)
    except ValueError as exc:
        return DeploymentContractResult(
            valid=False,
            services=[],
            violations=[
                {
                    "service": "<compose>",
                    "code": "invalid_or_unsupported_compose",
                    "detail": str(exc),
                }
            ],
        )

    for service, raw_config in service_mapping.items():
        service_name = str(service)
        if not isinstance(raw_config, dict):
            violations.append(
                {
                    "service": service_name,
                    "code": "invalid_service_config",
                }
            )
            continue
        config: dict[str, Any] = raw_config
        if "extends" in config:
            violations.append(
                {
                    "service": service_name,
                    "code": "unresolved_extends",
                }
            )
            continue

        try:
            mounts = _volume_mounts(config)
            cap_drop = {item.upper() for item in _string_list(config.get("cap_drop"))}
            security_opt = {
                item.lower().replace("=", ":")
                for item in _string_list(config.get("security_opt"))
            }
        except ValueError as exc:
            violations.append(
                {
                    "service": service_name,
                    "code": "unsupported_service_syntax",
                    "detail": str(exc),
                }
            )
            continue

        network_disabled = config.get("network_mode") == "none"
        private_data = any(
            _targets_path(target, "/private")
            or _targets_path(target, "/quarantine/input")
            or "LONGGATE_PRIVATE_DIR" in source
            or "LONGGATE_QUARANTINE_INPUT" in source
            for source, target, _read_only in mounts
        )
        model_mounts = [
            (target, read_only)
            for _source, target, read_only in mounts
            if _targets_path(target, "/models")
        ]
        safe_mounts = [
            (target, read_only)
            for _source, target, read_only in mounts
            if _targets_path(target, "/safe")
        ]
        model_read = any(read_only for _target, read_only in model_mounts)
        model_write = any(not read_only for _target, read_only in model_mounts)
        safe_read = bool(safe_mounts)
        safe_write = any(not read_only for _target, read_only in safe_mounts)
        caps_dropped = "ALL" in cap_drop
        no_new_privileges = any(
            item in {"no-new-privileges:true", "no-new-privileges"}
            for item in security_opt
        )

        capability = ServiceCapabilities(
            service=service_name,
            network_disabled=network_disabled,
            private_data_capability=private_data,
            model_vault_read=model_read,
            model_vault_write=model_write,
            safe_workspace_read=safe_read,
            safe_workspace_write=safe_write,
            all_capabilities_dropped=caps_dropped,
            no_new_privileges=no_new_privileges,
        )
        services.append(capability)

        if private_data and not network_disabled:
            violations.append(
                {
                    "service": service_name,
                    "code": "private_data_with_network",
                }
            )
        if private_data and model_write:
            violations.append(
                {
                    "service": service_name,
                    "code": "private_data_with_model_vault_write",
                }
            )
        if private_data and safe_read:
            violations.append(
                {
                    "service": service_name,
                    "code": "private_data_with_network_safe_workspace",
                }
            )
        if safe_write:
            violations.append(
                {
                    "service": service_name,
                    "code": "network_safe_workspace_must_be_read_only",
                }
            )

        sensitive_boundary = private_data or safe_read
        if sensitive_boundary and not caps_dropped:
            violations.append(
                {
                    "service": service_name,
                    "code": "linux_capabilities_not_dropped",
                }
            )
        if sensitive_boundary and not no_new_privileges:
            violations.append(
                {
                    "service": service_name,
                    "code": "no_new_privileges_missing",
                }
            )

    return DeploymentContractResult(
        valid=not violations,
        services=services,
        violations=violations,
    )
