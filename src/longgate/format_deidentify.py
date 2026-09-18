from __future__ import annotations

import hashlib
import hmac
import html
import json
import ipaddress
import re
from dataclasses import asdict, dataclass
from pathlib import Path

from .pii import CN_ID_RE, EMAIL_RE, UK_POSTCODE_RE, iter_phone_matches, scan_text
from .utils import atomic_write_text, sha256_file, utc_now, write_json

SUPPORTED_PRESERVE_TEXT = {".txt", ".md", ".markdown"}
_IP_CANDIDATE_RE = re.compile(r"(?<![\w:])(?:[0-9A-Fa-f:.]{3,})(?![\w:])")


@dataclass(frozen=True)
class _Span:
    start: int
    end: int
    entity: str
    value: str


ASSISTED_ENTITY_TYPES = {
    "PERSON",
    "ALIAS",
    "ORGANIZATION",
    "LOCATION",
    "PROJECT",
    "DATE",
    "ROLE",
    "EVENT",
    "QUASI_IDENTIFIER",
}


@dataclass(frozen=True)
class AssistedEntityLiteral:
    entity: str
    literal: str


@dataclass(frozen=True)
class MappedIdentifierSpan:
    start: int
    end: int
    entity: str
    label: str


@dataclass(frozen=True)
class FormatPreservingResult:
    status: str
    input_path: str
    output_path: str
    audit_path: str
    report_path: str
    input_sha256: str
    output_sha256: str
    replacements: int
    replacement_entities: dict[str, int]
    original_unchanged: bool
    manual_review_required: bool
    automatic_release_allowed: bool
    release_allowed: bool
    next_actions: list[str]
    entity_assist: dict[str, object] | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def default_output_path(input_path: str | Path) -> Path:
    source = Path(input_path).expanduser().resolve()
    return source.with_name(f"{source.stem}.deidentified{source.suffix}")


def _collect_regex_spans(text: str, pattern: re.Pattern[str], entity: str) -> list[_Span]:
    return [
        _Span(match.start(), match.end(), entity, match.group(0))
        for match in pattern.finditer(text)
    ]


def _collect_ip_spans(text: str) -> list[_Span]:
    spans: list[_Span] = []
    strip_chars = "[](),;."
    for match in _IP_CANDIDATE_RE.finditer(text):
        raw = match.group(0)
        left = len(raw) - len(raw.lstrip(strip_chars))
        right = len(raw.rstrip(strip_chars))
        candidate = raw[left:right]
        if not candidate:
            continue
        try:
            ipaddress.ip_address(candidate)
        except ValueError:
            continue
        spans.append(
            _Span(
                match.start() + left,
                match.start() + right,
                "IP_ADDRESS",
                candidate,
            )
        )
    return spans


def _identifier_spans(text: str) -> list[_Span]:
    phone_spans = [
        _Span(match.start(), match.end(), "PHONE", match.group(0))
        for match in iter_phone_matches(text)
    ]
    spans = [
        *_collect_regex_spans(text, CN_ID_RE, "NATIONAL_ID"),
        *_collect_regex_spans(text, EMAIL_RE, "EMAIL"),
        *_collect_regex_spans(text, UK_POSTCODE_RE, "POSTCODE"),
        *_collect_ip_spans(text),
        *phone_spans,
    ]
    priority = {
        "NATIONAL_ID": 0,
        "EMAIL": 1,
        "POSTCODE": 2,
        "IP_ADDRESS": 3,
        "PHONE": 4,
    }
    spans.sort(
        key=lambda item: (
            item.start,
            -(item.end - item.start),
            priority.get(item.entity, 99),
        )
    )

    accepted: list[_Span] = []
    cursor = -1
    for span in spans:
        if span.start < cursor:
            continue
        accepted.append(span)
        cursor = span.end
    return accepted


def _mapping_key(span: _Span) -> tuple[str, str]:
    value = span.value.casefold() if span.entity in {"EMAIL", "POSTCODE"} else span.value
    return span.entity, value


class DirectIdentifierMapper:
    """Stateful direct-identifier map for one document or explicit batch."""

    def __init__(
        self,
        *,
        key_secret: bytes | None = None,
        state: dict[str, object] | None = None,
    ) -> None:
        self._key_secret = key_secret
        self._counters: dict[str, int] = {}
        self._labels: dict[tuple[str, str], str] = {}
        self._assisted_literals: dict[str, str] = {}
        self.entity_counts: dict[str, int] = {}
        if state is not None:
            self._load_state(state)

    def begin_document(self) -> None:
        """Reset per-document counts/candidates while retaining stable labels."""
        self.entity_counts = {}
        self._assisted_literals = {}

    def _state_key(self, span: _Span) -> tuple[str, str]:
        entity, value = _mapping_key(span)
        if self._key_secret is None:
            return entity, value
        digest = hmac.new(
            self._key_secret,
            f"{entity}\0{value}".encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return entity, digest

    def _load_state(self, state: dict[str, object]) -> None:
        if self._key_secret is None:
            raise ValueError("Persistent mapper state requires a key_secret.")
        expected_keys = {
            "version",
            "key_verifier",
            "state_mac",
            "counters",
            "labels",
        }
        if set(state) != expected_keys or state.get("version") != 1:
            raise ValueError("Unsupported or invalid persistent entity-map state.")

        verifier = state.get("key_verifier")
        expected_verifier = hmac.new(
            self._key_secret,
            b"long-gate-entity-map-state-v1",
            hashlib.sha256,
        ).hexdigest()
        if not isinstance(verifier, str) or not hmac.compare_digest(
            verifier,
            expected_verifier,
        ):
            raise ValueError("Persistent entity-map state/key mismatch.")

        counters = state.get("counters")
        labels = state.get("labels")
        state_mac = state.get("state_mac")
        if (
            not isinstance(counters, dict)
            or not isinstance(labels, list)
            or not isinstance(state_mac, str)
        ):
            raise ValueError("Invalid persistent entity-map state.")

        allowed = {
            "EMAIL",
            "PHONE",
            "NATIONAL_ID",
            "POSTCODE",
            "IP_ADDRESS",
            *ASSISTED_ENTITY_TYPES,
        }
        loaded_counters: dict[str, int] = {}
        for entity, value in counters.items():
            if (
                not isinstance(entity, str)
                or entity not in allowed
                or not isinstance(value, int)
                or value < 0
            ):
                raise ValueError("Invalid persistent entity-map counter.")
            loaded_counters[entity] = value

        loaded_labels: dict[tuple[str, str], str] = {}
        normalized_labels: list[dict[str, str]] = []
        for item in labels:
            if not isinstance(item, dict) or set(item) != {"entity", "digest", "label"}:
                raise ValueError("Invalid persistent entity-map label.")
            entity = item.get("entity")
            digest = item.get("digest")
            label = item.get("label")
            if (
                not isinstance(entity, str)
                or entity not in allowed
                or not isinstance(digest, str)
                or not re.fullmatch(r"[0-9a-f]{64}", digest)
                or not isinstance(label, str)
                or not re.fullmatch(rf"\[{entity}_[0-9]{{3,}}\]", label)
            ):
                raise ValueError("Invalid persistent entity-map label.")
            key = (entity, digest)
            if key in loaded_labels:
                raise ValueError("Duplicate persistent entity-map key.")
            loaded_labels[key] = label
            normalized_labels.append(
                {"entity": entity, "digest": digest, "label": label}
            )

        normalized_payload = {
            "version": 1,
            "key_verifier": verifier,
            "counters": loaded_counters,
            "labels": normalized_labels,
        }
        expected_mac = hmac.new(
            self._key_secret,
            (
                b"long-gate-entity-map-state-v1\0"
                + json.dumps(
                    normalized_payload,
                    sort_keys=True,
                    separators=(",", ":"),
                    ensure_ascii=True,
                ).encode("utf-8")
            ),
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(state_mac, expected_mac):
            raise ValueError("Persistent entity-map state authentication failed.")

        self._counters = loaded_counters
        self._labels = loaded_labels

    def export_state(self) -> dict[str, object]:
        """Export authenticated keyed digests, never raw identifier values."""
        if self._key_secret is None:
            raise ValueError("Persistent export requires a key_secret.")
        payload: dict[str, object] = {
            "version": 1,
            "key_verifier": hmac.new(
                self._key_secret,
                b"long-gate-entity-map-state-v1",
                hashlib.sha256,
            ).hexdigest(),
            "counters": dict(self._counters),
            "labels": [
                {"entity": entity, "digest": digest, "label": label}
                for (entity, digest), label in sorted(self._labels.items())
            ],
        }
        state_mac = hmac.new(
            self._key_secret,
            (
                b"long-gate-entity-map-state-v1\0"
                + json.dumps(
                    payload,
                    sort_keys=True,
                    separators=(",", ":"),
                    ensure_ascii=True,
                ).encode("utf-8")
            ),
            hashlib.sha256,
        ).hexdigest()
        return {**payload, "state_mac": state_mac}

    def register_assisted_literals(
        self,
        candidates: list[AssistedEntityLiteral],
    ) -> None:
        """Register exact source literals for controlled non-generative replacement."""
        priority = {
            "PERSON": 0,
            "ALIAS": 1,
            "ORGANIZATION": 2,
            "LOCATION": 3,
            "PROJECT": 4,
            "DATE": 5,
            "ROLE": 6,
            "EVENT": 7,
            "QUASI_IDENTIFIER": 8,
        }
        for candidate in candidates:
            if candidate.entity not in ASSISTED_ENTITY_TYPES:
                raise ValueError(f"Unsupported assisted entity type: {candidate.entity}")
            existing = self._assisted_literals.get(candidate.literal)
            if existing is None or priority[candidate.entity] < priority[existing]:
                self._assisted_literals[candidate.literal] = candidate.entity

    def _assisted_spans(self, text: str) -> list[_Span]:
        spans: list[_Span] = []
        for literal, entity in self._assisted_literals.items():
            start = 0
            while True:
                index = text.find(literal, start)
                if index < 0:
                    break
                spans.append(
                    _Span(
                        start=index,
                        end=index + len(literal),
                        entity=entity,
                        value=literal,
                    )
                )
                start = index + max(1, len(literal))
        return spans

    @property
    def replacements(self) -> int:
        return sum(self.entity_counts.values())

    def plan(self, text: str) -> list[MappedIdentifierSpan]:
        """Return mapped direct-identifier spans and update document-level counts."""
        mapped: list[MappedIdentifierSpan] = []
        direct_spans = _identifier_spans(text)
        assisted_spans = [
            span
            for span in self._assisted_spans(text)
            if not any(
                span.start < direct.end and direct.start < span.end
                for direct in direct_spans
            )
        ]
        assisted_priority = {
            "PERSON": 0,
            "ALIAS": 1,
            "ORGANIZATION": 2,
            "LOCATION": 3,
            "PROJECT": 4,
            "DATE": 5,
            "ROLE": 6,
            "EVENT": 7,
            "QUASI_IDENTIFIER": 8,
        }
        assisted_spans.sort(
            key=lambda item: (
                item.start,
                -(item.end - item.start),
                assisted_priority.get(item.entity, 99),
            )
        )
        accepted_assisted: list[_Span] = []
        cursor = -1
        for span in assisted_spans:
            if span.start < cursor:
                continue
            accepted_assisted.append(span)
            cursor = span.end

        spans = sorted(
            [*direct_spans, *accepted_assisted],
            key=lambda item: item.start,
        )
        for span in spans:
            key = self._state_key(span)
            label = self._labels.get(key)
            if label is None:
                self._counters[span.entity] = self._counters.get(span.entity, 0) + 1
                label = f"[{span.entity}_{self._counters[span.entity]:03d}]"
                self._labels[key] = label
            mapped.append(
                MappedIdentifierSpan(
                    start=span.start,
                    end=span.end,
                    entity=span.entity,
                    label=label,
                )
            )
            self.entity_counts[span.entity] = self.entity_counts.get(span.entity, 0) + 1
        return mapped

    def replace(self, text: str) -> str:
        pieces: list[str] = []
        cursor = 0
        for span in self.plan(text):
            pieces.append(text[cursor:span.start])
            pieces.append(span.label)
            cursor = span.end
        pieces.append(text[cursor:])
        return "".join(pieces)


def replace_direct_identifiers(text: str) -> tuple[str, dict[str, int]]:
    """Replace direct identifiers with a fresh per-document entity map."""
    mapper = DirectIdentifierMapper()
    return mapper.replace(text), dict(mapper.entity_counts)


def _render_report(
    *,
    file_format: str,
    status: str,
    input_sha256: str,
    output_sha256: str,
    replacements: int,
    entity_counts: dict[str, int],
    remaining_direct_pii_hits: int,
    entity_assist: dict[str, object] | None = None,
) -> str:
    entity_rows = "".join(
        f"<tr><td>{html.escape(entity)}</td><td>{count}</td></tr>"
        for entity, count in sorted(entity_counts.items())
    ) or "<tr><td>none</td><td>0</td></tr>"
    assist_html = ""
    if entity_assist:
        accepted = int(entity_assist.get("accepted_candidates", 0))
        rejected = int(entity_assist.get("rejected_candidates", 0))
        model_file = html.escape(str(entity_assist.get("model_file", "local model")))
        assist_html = (
            "<div class=\"card\"><h2>本地语义实体辅助</h2>"
            f"<p>模型：<code>{model_file}</code></p>"
            f"<p>已接受候选：{accepted}；被拒绝候选：{rejected}</p>"
            "<p>模型只提名原文 literal；Long Gate 不允许模型自由重写正文。"
            "报告不记录候选原文。</p></div>"
        )
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>Long Gate 格式保真脱敏报告</title>
<style>
body{{font-family:system-ui,-apple-system,sans-serif;max-width:960px;margin:40px auto;padding:0 20px;line-height:1.6;color:#18212f}}
.card{{border:1px solid #d8dee8;border-radius:14px;padding:18px;margin:16px 0}}
code{{background:#f2f4f8;padding:2px 5px;border-radius:5px;word-break:break-all}}
table{{border-collapse:collapse;width:100%}}th,td{{border:1px solid #d8dee8;padding:8px;text-align:left}}th{{background:#f4f7fb}}
</style>
</head>
<body>
<h1>Long Gate · 格式保真脱敏报告</h1>
<div class="card">
<p><strong>状态：{html.escape(status)}</strong></p>
<p>本次处理只替换明确识别出的直接标识符，并保持 TXT/Markdown 其余字符、段落和结构不变。</p>
<p>这不是匿名化证明，也不会自动获得联网外发权限。</p>
</div>
<div class="card">
<h2>文件完整性</h2>
<p>文件格式：<code>{html.escape(file_format)}</code></p>
<p>输入/输出文件名和本地目录路径不会写入本报告。</p>
<p>输入 SHA-256：<code>{html.escape(input_sha256)}</code></p>
<p>输出 SHA-256：<code>{html.escape(output_sha256)}</code></p>
</div>
<div class="card">
<h2>直接标识符替换</h2>
<p>总替换次数：{replacements}</p>
<table><thead><tr><th>类型</th><th>出现次数</th></tr></thead><tbody>{entity_rows}</tbody></table>
<p>输出中仍被机械扫描器命中的直接 PII：{remaining_direct_pii_hits}</p>
</div>
{assist_html}
<div class="card">
<h2>仍需人工复核</h2>
<ul>
<li>姓名、组织、地点、别名、罕见事件和组合身份线索目前不保证自动识别。</li>
<li>同一直接标识符在单文件内使用稳定占位符；跨文件批次一致映射将在后续阶段实现。</li>
<li>脱敏质量与是否允许交给联网 AI 是两个独立结论；当前输出仍为 local-only。</li>
</ul>
</div>
<p>报告由 Long Gate 于 {html.escape(utc_now())} 在本地生成，不引用远程资源，也不嵌入原文或脱敏正文。</p>
</body></html>"""


def deidentify_text_copy(
    input_path: str | Path,
    output_path: str | Path | None = None,
    *,
    mapper: DirectIdentifierMapper | None = None,
    entity_assist: dict[str, object] | None = None,
) -> FormatPreservingResult:
    """Create a structure-preserving TXT/Markdown de-identified copy."""
    source = Path(input_path).expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(source)
    if source.suffix.lower() not in SUPPORTED_PRESERVE_TEXT:
        raise ValueError(
            "Format-preserving deidentify currently supports TXT/Markdown only. "
            "Use longgate semantic-summarize for local semantic abstraction of "
            "other extractable document types."
        )

    destination = (
        Path(output_path).expanduser().resolve()
        if output_path is not None
        else default_output_path(source)
    )
    if destination == source:
        raise ValueError("Refusing to overwrite the input file.")
    if destination.suffix.lower() != source.suffix.lower():
        raise ValueError("Format-preserving output must keep the same file extension.")

    source_bytes = source.read_bytes()
    input_sha256 = hashlib.sha256(source_bytes).hexdigest()
    text = source_bytes.decode("utf-8")
    mapper = mapper or DirectIdentifierMapper()
    transformed = mapper.replace(text)
    entity_counts = dict(mapper.entity_counts)
    replacements = mapper.replacements
    remaining = scan_text(transformed)

    if sha256_file(source) != input_sha256:
        raise RuntimeError("Input file changed during processing; no output was written.")

    atomic_write_text(destination, transformed, encoding="utf-8")
    original_unchanged = sha256_file(source) == input_sha256
    if not original_unchanged:
        destination.unlink(missing_ok=True)
        raise RuntimeError(
            "Input file changed while output was being committed; generated output was removed."
        )

    output_sha256 = sha256_file(destination)
    audit_path = destination.with_name(destination.name + ".audit.json")
    report_path = destination.with_name(destination.name + ".trust-report.html")
    assist_rejected = int((entity_assist or {}).get("rejected_candidates", 0))
    status = (
        "LOCAL_ONLY"
        if remaining.total_hits or assist_rejected
        else "MANUAL_REVIEW_REQUIRED"
    )
    next_actions = [
        "人工复核姓名、组织、地点、别名、罕见事件与组合身份线索。",
        "若输出机械扫描仍有直接 PII 命中，保持 LOCAL_ONLY 并修正后重跑。",
        "即使人工确认脱敏质量，也不要把本结果视为自动联网授权。",
    ]
    payload = {
        "format": "long-gate-format-preserving-deidentify-v1",
        "status": status,
        "input_format": source.suffix.lower().lstrip("."),
        "input_sha256": input_sha256,
        "output_sha256": output_sha256,
        "replacements": replacements,
        "replacement_entities": entity_counts,
        "remaining_direct_pii_hits": remaining.total_hits,
        "remaining_direct_pii_by_entity": remaining.by_entity,
        "original_unchanged": True,
        "format_preserved": True,
        "manual_review_required": True,
        "automatic_release_allowed": False,
        "release_allowed": False,
        "next_actions": next_actions,
        "entity_assist": entity_assist,
    }
    write_json(audit_path, payload)
    atomic_write_text(
        report_path,
        _render_report(
            file_format=source.suffix.lower().lstrip("."),
            status=status,
            input_sha256=input_sha256,
            output_sha256=output_sha256,
            replacements=replacements,
            entity_counts=entity_counts,
            remaining_direct_pii_hits=remaining.total_hits,
            entity_assist=entity_assist,
        ),
    )

    return FormatPreservingResult(
        status=status,
        input_path=str(source),
        output_path=str(destination),
        audit_path=str(audit_path),
        report_path=str(report_path),
        input_sha256=input_sha256,
        output_sha256=output_sha256,
        replacements=replacements,
        replacement_entities=entity_counts,
        original_unchanged=True,
        manual_review_required=True,
        automatic_release_allowed=False,
        release_allowed=False,
        next_actions=next_actions,
        entity_assist=entity_assist,
    )
