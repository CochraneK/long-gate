from __future__ import annotations

import re
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class ServiceCapabilities:
    service: str
    network_disabled: bool
    private_data_capability: bool
    model_vault_read: bool
    model_vault_write: bool
    safe_workspace_read: bool

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class DeploymentContractResult:
    valid: bool
    services: list[ServiceCapabilities]
    violations: list[dict[str, str]]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


_SERVICE_RE = re.compile(r"^  ([A-Za-z0-9_.-]+):\s*$", re.MULTILINE)


def _service_blocks(text: str) -> dict[str, str]:
    matches = list(_SERVICE_RE.finditer(text))
    blocks: dict[str, str] = {}
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        blocks[match.group(1)] = text[start:end]
    return blocks


def validate_compose_capability_contract(text: str) -> DeploymentContractResult:
    """Detect dangerous capability combinations in a Compose document.

    This intentionally checks capabilities rather than service names. A future
    rename cannot silently bypass the invariant.
    """
    services: list[ServiceCapabilities] = []
    violations: list[dict[str, str]] = []

    for service, block in _service_blocks(text).items():
        network_disabled = "network_mode: none" in block
        private_data = (
            "/private" in block
            or "LONGGATE_PRIVATE_DIR" in block
        )
        model_read = (
            "/models:ro" in block
            or "LONGGATE_MODEL_VAULT: /models" in block
        )
        model_write = (
            re.search(r":/models(?:\s|$)", block) is not None
            and ":/models:ro" not in block
        )
        safe_read = "/safe:ro" in block

        capability = ServiceCapabilities(
            service=service,
            network_disabled=network_disabled,
            private_data_capability=private_data,
            model_vault_read=model_read,
            model_vault_write=model_write,
            safe_workspace_read=safe_read,
        )
        services.append(capability)

        if private_data and not network_disabled:
            violations.append(
                {
                    "service": service,
                    "code": "private_data_with_network",
                }
            )
        if private_data and model_write:
            violations.append(
                {
                    "service": service,
                    "code": "private_data_with_model_vault_write",
                }
            )
        if private_data and safe_read:
            violations.append(
                {
                    "service": service,
                    "code": "private_data_with_network_safe_workspace",
                }
            )

    return DeploymentContractResult(
        valid=not violations,
        services=services,
        violations=violations,
    )
