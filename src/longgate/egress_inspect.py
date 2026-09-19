from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import parse_qsl, urlsplit

from .endpoint_provenance import classify_endpoint_host
from .pii import scan_text


MAX_HAR_BYTES = 25 * 1024 * 1024
_SENSITIVE_HEADER_NAMES = {
    "authorization",
    "proxy-authorization",
    "x-api-key",
    "api-key",
    "cookie",
    "set-cookie",
}
_SENSITIVE_QUERY_RE = re.compile(
    r"(?:api[_-]?key|access[_-]?token|refresh[_-]?token|auth|signature|secret|password|code)",
    re.IGNORECASE,
)
_SECRET_FIELD_RE = re.compile(
    r"(?<![A-Za-z0-9])(?:api[_-]?key|access[_-]?token|refresh[_-]?token|"
    r"client[_-]?secret|authorization|password|secret)(?![A-Za-z0-9])",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class HarEntrySummary:
    host: str
    method: str
    endpoint_classification: str
    provider_hint: str | None
    relay_possible: bool
    content_type: str | None
    request_body_bytes: int
    pii_hits: int
    pii_by_entity: dict[str, int]
    sensitive_header_names: list[str]
    sensitive_query_names: list[str]
    secret_field_name_hits: int
    cookie_count: int

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class HarInspection:
    source: str
    entries: int
    hosts: list[str]
    total_request_body_bytes: int
    total_pii_hits: int
    entries_with_sensitive_headers: int
    entries_with_sensitive_query: int
    entries_with_secret_field_names: int
    requests: list[HarEntrySummary]
    release_allowed: bool
    note: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _headers(request: dict[str, object]) -> tuple[list[str], str | None]:
    sensitive: set[str] = set()
    content_type: str | None = None
    raw_headers = request.get("headers", [])
    if not isinstance(raw_headers, list):
        return [], None
    for item in raw_headers:
        if not isinstance(item, dict):
            continue
        raw_name = item.get("name")
        if not isinstance(raw_name, str):
            continue
        name = raw_name.strip().lower()
        if name in _SENSITIVE_HEADER_NAMES:
            sensitive.add(name)
        if name == "content-type":
            raw_value = item.get("value")
            if isinstance(raw_value, str):
                content_type = raw_value.split(";", 1)[0].strip().lower()
    return sorted(sensitive), content_type


def _post_text(request: dict[str, object]) -> str:
    post_data = request.get("postData")
    if not isinstance(post_data, dict):
        return ""
    value = post_data.get("text")
    return value if isinstance(value, str) else ""


def inspect_har(path: str | Path) -> HarInspection:
    source = Path(path)
    size = source.stat().st_size
    if size > MAX_HAR_BYTES:
        raise ValueError(
            f"HAR is too large for bounded local inspection ({size} bytes > {MAX_HAR_BYTES})."
        )

    document = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        raise ValueError("HAR root must be a JSON object.")
    log = document.get("log")
    if not isinstance(log, dict):
        raise ValueError("HAR must contain a log object.")
    raw_entries = log.get("entries")
    if not isinstance(raw_entries, list):
        raise ValueError("HAR log must contain an entries array.")

    summaries: list[HarEntrySummary] = []
    hosts: set[str] = set()
    total_body_bytes = 0
    total_pii_hits = 0
    sensitive_header_entries = 0
    sensitive_query_entries = 0
    secret_field_entries = 0

    for raw_entry in raw_entries:
        if not isinstance(raw_entry, dict):
            continue
        request = raw_entry.get("request")
        if not isinstance(request, dict):
            continue
        raw_url = request.get("url")
        if not isinstance(raw_url, str):
            continue

        parsed = urlsplit(raw_url)
        host = (parsed.hostname or "").rstrip(".").lower()
        if not host:
            continue
        hosts.add(host)

        classification, provider_hint, relay_possible = classify_endpoint_host(host)
        method = str(request.get("method") or "UNKNOWN").upper()
        sensitive_headers, content_type = _headers(request)
        query_names = sorted(
            {
                name
                for name, _value in parse_qsl(parsed.query, keep_blank_values=True)
                if _SENSITIVE_QUERY_RE.search(name)
            }
        )
        body = _post_text(request)
        body_bytes = len(body.encode("utf-8"))
        pii = scan_text(body)
        secret_field_name_hits = len(_SECRET_FIELD_RE.findall(body))

        raw_cookies = request.get("cookies", [])
        cookie_count = len(raw_cookies) if isinstance(raw_cookies, list) else 0

        total_body_bytes += body_bytes
        total_pii_hits += pii.total_hits
        sensitive_header_entries += int(bool(sensitive_headers))
        sensitive_query_entries += int(bool(query_names))
        secret_field_entries += int(secret_field_name_hits > 0)

        summaries.append(
            HarEntrySummary(
                host=host,
                method=method,
                endpoint_classification=classification,
                provider_hint=provider_hint,
                relay_possible=relay_possible,
                content_type=content_type,
                request_body_bytes=body_bytes,
                pii_hits=pii.total_hits,
                pii_by_entity=pii.by_entity,
                sensitive_header_names=sensitive_headers,
                sensitive_query_names=query_names,
                secret_field_name_hits=secret_field_name_hits,
                cookie_count=cookie_count,
            )
        )

    return HarInspection(
        source=source.name,
        entries=len(summaries),
        hosts=sorted(hosts),
        total_request_body_bytes=total_body_bytes,
        total_pii_hits=total_pii_hits,
        entries_with_sensitive_headers=sensitive_header_entries,
        entries_with_sensitive_query=sensitive_query_entries,
        entries_with_secret_field_names=secret_field_entries,
        requests=summaries,
        release_allowed=False,
        note=(
            "Local HAR inspection reports metadata and sensitive-data counts only. "
            "It intentionally does not echo header values, query values, cookies, or request bodies."
        ),
    )
