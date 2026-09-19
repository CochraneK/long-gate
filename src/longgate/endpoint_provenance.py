from __future__ import annotations

import hashlib
import socket
import ssl
from dataclasses import asdict, dataclass
from urllib.parse import urlsplit


@dataclass(frozen=True)
class EndpointInspection:
    endpoint: str
    host: str
    port: int
    classification: str
    provider_hint: str | None
    relay_possible: bool
    network_used: bool
    resolved_ips: list[str]
    tls: dict[str, object] | None
    warnings: list[str]
    evidence_limit: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


_OFFICIAL_ENDPOINTS: dict[str, str] = {
    "api.openai.com": "OpenAI",
    "api.anthropic.com": "Anthropic",
    "generativelanguage.googleapis.com": "Google Gemini",
    "api.mistral.ai": "Mistral AI",
    "api.cohere.com": "Cohere",
    "api.groq.com": "Groq",
    "api.deepseek.com": "DeepSeek",
    "api.x.ai": "xAI",
}

_KNOWN_ROUTERS: dict[str, str] = {
    "openrouter.ai": "OpenRouter",
    "api.openrouter.ai": "OpenRouter",
}

_MANAGED_SUFFIXES: tuple[tuple[str, str], ...] = (
    (".openai.azure.com", "Microsoft Azure OpenAI"),
    (".services.ai.azure.com", "Microsoft Azure AI"),
)


def classify_endpoint_host(host: str) -> tuple[str, str | None, bool]:
    normalized = host.rstrip(".").lower()
    if normalized in _OFFICIAL_ENDPOINTS:
        return "OFFICIAL_PROVIDER_ENDPOINT", _OFFICIAL_ENDPOINTS[normalized], False
    if normalized in _KNOWN_ROUTERS:
        return "KNOWN_ROUTER_OR_AGGREGATOR", _KNOWN_ROUTERS[normalized], True
    for suffix, provider in _MANAGED_SUFFIXES:
        if normalized.endswith(suffix):
            return "MANAGED_CLOUD_ENDPOINT", provider, False
    return "CUSTOM_OR_UNKNOWN_ENDPOINT", None, True


def _common_name(name: object) -> str | None:
    if not isinstance(name, tuple):
        return None
    for group in name:
        if not isinstance(group, tuple):
            continue
        for item in group:
            if (
                isinstance(item, tuple)
                and len(item) == 2
                and item[0] == "commonName"
            ):
                return str(item[1])
    return None


def _tls_snapshot(host: str, port: int, timeout: float) -> dict[str, object]:
    context = ssl.create_default_context()
    with socket.create_connection((host, port), timeout=timeout) as raw:
        with context.wrap_socket(raw, server_hostname=host) as conn:
            cert = conn.getpeercert()
            der = conn.getpeercert(binary_form=True)
            sans = [
                value
                for kind, value in cert.get("subjectAltName", ())
                if kind == "DNS"
            ]
            return {
                "version": conn.version(),
                "cipher": conn.cipher()[0] if conn.cipher() else None,
                "subject_common_name": _common_name(cert.get("subject")),
                "issuer_common_name": _common_name(cert.get("issuer")),
                "subject_alt_names": sorted(set(sans))[:50],
                "not_before": cert.get("notBefore"),
                "not_after": cert.get("notAfter"),
                "certificate_sha256": hashlib.sha256(der).hexdigest(),
            }


def inspect_endpoint(
    endpoint: str,
    *,
    connect: bool = True,
    timeout: float = 4.0,
) -> EndpointInspection:
    parsed = urlsplit(endpoint)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("Endpoint must be an http:// or https:// URL with a hostname.")

    host = parsed.hostname.rstrip(".").lower()
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    classification, provider_hint, relay_possible = classify_endpoint_host(host)
    warnings: list[str] = []
    resolved_ips: list[str] = []
    tls: dict[str, object] | None = None

    if connect:
        try:
            infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
            resolved_ips = sorted({str(item[4][0]) for item in infos})
        except OSError as exc:
            warnings.append(f"DNS resolution failed: {exc.__class__.__name__}")

        if parsed.scheme == "https":
            try:
                tls = _tls_snapshot(host, port, timeout)
            except (OSError, ssl.SSLError) as exc:
                warnings.append(f"TLS inspection failed: {exc.__class__.__name__}")
        else:
            warnings.append("Plain HTTP endpoint: request contents are not protected by TLS.")

    return EndpointInspection(
        endpoint=f"{parsed.scheme}://{host}:{port}",
        host=host,
        port=port,
        classification=classification,
        provider_hint=provider_hint,
        relay_possible=relay_possible,
        network_used=connect,
        resolved_ips=resolved_ips,
        tls=tls,
        warnings=warnings,
        evidence_limit=(
            "Hostname, DNS and TLS evidence can identify the endpoint you connect to, "
            "but cannot prove which upstream model ultimately executes the request. "
            "A custom endpoint is therefore marked relay-possible, not proven to be a relay."
        ),
    )
