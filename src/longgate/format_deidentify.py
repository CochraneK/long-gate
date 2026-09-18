from __future__ import annotations

import html
import ipaddress
import re
from dataclasses import asdict, dataclass
from pathlib import Path

from .pii import CN_ID_RE, EMAIL_RE, PHONE_RE, UK_POSTCODE_RE, scan_text
from .utils import atomic_write_text, sha256_file, utc_now, write_json

SUPPORTED_PRESERVE_TEXT = {".txt", ".md", ".markdown"}
_IP_CANDIDATE_RE = re.compile(r"(?<![\w:])(?:[0-9A-Fa-f:.]{3,})(?![\w:])")


@dataclass(frozen=True)
class _Span:
    start: int
    end: int
    entity: str
    value: str


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
    spans = [
        *_collect_regex_spans(text, EMAIL_RE, "EMAIL"),
        *_collect_regex_spans(text, PHONE_RE, "PHONE"),
        *_collect_regex_spans(text, CN_ID_RE, "NATIONAL_ID"),
        *_collect_regex_spans(text, UK_POSTCODE_RE, "POSTCODE"),
        *_collect_ip_spans(text),
    ]
    spans.sort(key=lambda item: (item.start, -(item.end - item.start)))

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


def replace_direct_identifiers(text: str) -> tuple[str, dict[str, int]]:
    """Replace direct identifier literals while preserving all other characters."""
    spans = _identifier_spans(text)
    counters: dict[str, int] = {}
    labels: dict[tuple[str, str], str] = {}
    entity_counts: dict[str, int] = {}
    pieces: list[str] = []
    cursor = 0

    for span in spans:
        key = _mapping_key(span)
        label = labels.get(key)
        if label is None:
            counters[span.entity] = counters.get(span.entity, 0) + 1
            label = f"[{span.entity}_{counters[span.entity]:03d}]"
            labels[key] = label
        pieces.append(text[cursor:span.start])
        pieces.append(label)
        cursor = span.end
        entity_counts[span.entity] = entity_counts.get(span.entity, 0) + 1

    pieces.append(text[cursor:])
    return "".join(pieces), entity_counts


def _render_report(
    *,
    input_name: str,
    output_name: str,
    input_sha256: str,
    output_sha256: str,
    replacements: int,
    entity_counts: dict[str, int],
    remaining_direct_pii_hits: int,
) -> str:
    entity_rows = "".join(
        f"<tr><td>{html.escape(entity)}</td><td>{count}</td></tr>"
        for entity, count in sorted(entity_counts.items())
    ) or "<tr><td>none</td><td>0</td></tr>"
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
<p><strong>状态：MANUAL_REVIEW_REQUIRED</strong></p>
<p>本次处理只替换明确识别出的直接标识符，并保持 TXT/Markdown 其余字符、段落和结构不变。</p>
<p>这不是匿名化证明，也不会自动获得联网外发权限。</p>
</div>
<div class="card">
<h2>文件完整性</h2>
<p>输入文件：<code>{html.escape(input_name)}</code></p>
<p>输出文件：<code>{html.escape(output_name)}</code></p>
<p>输入 SHA-256：<code>{html.escape(input_sha256)}</code></p>
<p>输出 SHA-256：<code>{html.escape(output_sha256)}</code></p>
</div>
<div class="card">
<h2>直接标识符替换</h2>
<p>总替换次数：{replacements}</p>
<table><thead><tr><th>类型</th><th>出现次数</th></tr></thead><tbody>{entity_rows}</tbody></table>
<p>输出中仍被机械扫描器命中的直接 PII：{remaining_direct_pii_hits}</p>
</div>
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

    input_sha256 = sha256_file(source)
    text = source.read_text(encoding="utf-8")
    transformed, entity_counts = replace_direct_identifiers(text)
    replacements = sum(entity_counts.values())
    remaining = scan_text(transformed)

    atomic_write_text(destination, transformed, encoding="utf-8")
    original_unchanged = sha256_file(source) == input_sha256
    if not original_unchanged:
        raise RuntimeError("Input file changed during processing; refusing to report success.")

    output_sha256 = sha256_file(destination)
    audit_path = destination.with_name(destination.name + ".audit.json")
    report_path = destination.with_name(destination.name + ".trust-report.html")
    next_actions = [
        "人工复核姓名、组织、地点、别名、罕见事件与组合身份线索。",
        "若输出机械扫描仍有直接 PII 命中，保持 LOCAL_ONLY 并修正后重跑。",
        "即使人工确认脱敏质量，也不要把本结果视为自动联网授权。",
    ]
    payload = {
        "format": "long-gate-format-preserving-deidentify-v1",
        "status": "MANUAL_REVIEW_REQUIRED",
        "input_name": source.name,
        "output_name": destination.name,
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
    }
    write_json(audit_path, payload)
    atomic_write_text(
        report_path,
        _render_report(
            input_name=source.name,
            output_name=destination.name,
            input_sha256=input_sha256,
            output_sha256=output_sha256,
            replacements=replacements,
            entity_counts=entity_counts,
            remaining_direct_pii_hits=remaining.total_hits,
        ),
    )

    return FormatPreservingResult(
        status="MANUAL_REVIEW_REQUIRED",
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
    )
