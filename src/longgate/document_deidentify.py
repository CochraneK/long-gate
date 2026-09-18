from __future__ import annotations

import hashlib
import html
from io import BytesIO
from pathlib import Path

from .format_deidentify import (
    DirectIdentifierMapper,
    FormatPreservingResult,
    SUPPORTED_PRESERVE_TEXT,
    default_output_path,
    deidentify_text_copy,
)
from .pii import scan_text
from .utils import atomic_write_bytes, atomic_write_text, sha256_file, utc_now, write_json

_HTML_SUFFIXES = {".html", ".htm"}
_XLSX_SUFFIXES = {".xlsx"}


def _paths_and_snapshot(
    input_path: str | Path,
    output_path: str | Path | None,
    allowed_suffixes: set[str],
) -> tuple[Path, Path, bytes, str]:
    source = Path(input_path).expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(source)
    suffix = source.suffix.lower()
    if suffix not in allowed_suffixes:
        raise ValueError(f"Unsupported format-preserving input type: {suffix}")

    destination = (
        Path(output_path).expanduser().resolve()
        if output_path is not None
        else default_output_path(source)
    )
    if destination == source:
        raise ValueError("Refusing to overwrite the input file.")
    if destination.suffix.lower() != suffix:
        raise ValueError("Format-preserving output must keep the same file extension.")

    source_bytes = source.read_bytes()
    digest = hashlib.sha256(source_bytes).hexdigest()
    return source, destination, source_bytes, digest


def _render_report(
    *,
    format_kind: str,
    status: str,
    input_sha256: str,
    output_sha256: str,
    replacements: int,
    entity_counts: dict[str, int],
    remaining_direct_pii_hits: int,
    processed_units: dict[str, int],
    unprocessed_regions: dict[str, int],
    note: str,
) -> str:
    entity_rows = "".join(
        f"<tr><td>{html.escape(entity)}</td><td>{count}</td></tr>"
        for entity, count in sorted(entity_counts.items())
    ) or "<tr><td>none</td><td>0</td></tr>"
    processed = "".join(
        f"<li>{html.escape(name)}: {count}</li>"
        for name, count in sorted(processed_units.items())
    ) or "<li>none</li>"
    unprocessed = "".join(
        f"<li>{html.escape(name)}: {count}</li>"
        for name, count in sorted(unprocessed_regions.items())
    ) or "<li>none</li>"
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>Long Gate 格式保真脱敏报告</title>
<style>
body{{font-family:system-ui,-apple-system,sans-serif;max-width:980px;margin:40px auto;padding:0 20px;line-height:1.6;color:#18212f}}
.card{{border:1px solid #d8dee8;border-radius:14px;padding:18px;margin:16px 0}}
code{{background:#f2f4f8;padding:2px 5px;border-radius:5px;word-break:break-all}}
table{{border-collapse:collapse;width:100%}}th,td{{border:1px solid #d8dee8;padding:8px;text-align:left}}th{{background:#f4f7fb}}
</style>
</head>
<body>
<h1>Long Gate · 格式保真脱敏报告</h1>
<div class="card">
<p><strong>状态：{html.escape(status)}</strong></p>
<p>格式：<code>{html.escape(format_kind)}</code></p>
<p>{html.escape(note)}</p>
<p>这不是匿名化证明，也不会自动获得联网外发权限。</p>
</div>
<div class="card">
<h2>完整性</h2>
<p>输入/输出文件名和本地目录路径不会写入本报告。</p>
<p>输入 SHA-256：<code>{html.escape(input_sha256)}</code></p>
<p>输出 SHA-256：<code>{html.escape(output_sha256)}</code></p>
</div>
<div class="card">
<h2>替换</h2>
<p>总替换次数：{replacements}</p>
<table><thead><tr><th>类型</th><th>出现次数</th></tr></thead><tbody>{entity_rows}</tbody></table>
<p>仍检测到的直接 PII：{remaining_direct_pii_hits}</p>
</div>
<div class="card"><h2>已处理区域</h2><ul>{processed}</ul></div>
<div class="card"><h2>未自动改写 / 需复核区域</h2><ul>{unprocessed}</ul></div>
<div class="card">
<h2>人工复核重点</h2>
<ul>
<li>姓名、组织、地点、别名、罕见事件和组合身份线索仍需复核。</li>
<li>结构保真不等于语义匿名；任何 remaining direct PII 都会保持 LOCAL_ONLY。</li>
<li>脱敏质量判断与网络外发授权相互独立。</li>
</ul>
</div>
<p>报告由 Long Gate 于 {html.escape(utc_now())} 在本地生成，不嵌入原文、脱敏正文、文件名或本地路径。</p>
</body></html>"""


def _commit_result(
    *,
    source: Path,
    destination: Path,
    source_sha256: str,
    payload: bytes,
    format_kind: str,
    mapper: DirectIdentifierMapper,
    remaining_direct_pii_hits: int,
    remaining_by_entity: dict[str, int],
    processed_units: dict[str, int],
    unprocessed_regions: dict[str, int],
    note: str,
) -> FormatPreservingResult:
    if sha256_file(source) != source_sha256:
        raise RuntimeError("Input file changed during processing; no output was written.")

    atomic_write_bytes(destination, payload)
    if sha256_file(source) != source_sha256:
        destination.unlink(missing_ok=True)
        raise RuntimeError(
            "Input file changed while output was being committed; generated output was removed."
        )

    output_sha256 = sha256_file(destination)
    status = "LOCAL_ONLY" if remaining_direct_pii_hits else "MANUAL_REVIEW_REQUIRED"
    audit_path = destination.with_name(destination.name + ".audit.json")
    report_path = destination.with_name(destination.name + ".trust-report.html")
    next_actions = [
        "人工复核姓名、组织、地点、别名、罕见事件与组合身份线索。",
        "检查报告中的未自动改写区域；任何剩余直接 PII 都必须保持 LOCAL_ONLY。",
        "不要把格式保真处理结果视为自动联网授权。",
    ]
    payload_json = {
        "format": "long-gate-format-preserving-deidentify-v2",
        "status": status,
        "input_format": format_kind,
        "input_sha256": source_sha256,
        "output_sha256": output_sha256,
        "replacements": mapper.replacements,
        "replacement_entities": dict(mapper.entity_counts),
        "remaining_direct_pii_hits": remaining_direct_pii_hits,
        "remaining_direct_pii_by_entity": remaining_by_entity,
        "processed_units": processed_units,
        "unprocessed_regions": unprocessed_regions,
        "original_unchanged": True,
        "format_preserved": True,
        "manual_review_required": True,
        "automatic_release_allowed": False,
        "release_allowed": False,
        "next_actions": next_actions,
    }
    write_json(audit_path, payload_json)
    atomic_write_text(
        report_path,
        _render_report(
            format_kind=format_kind,
            status=status,
            input_sha256=source_sha256,
            output_sha256=output_sha256,
            replacements=mapper.replacements,
            entity_counts=dict(mapper.entity_counts),
            remaining_direct_pii_hits=remaining_direct_pii_hits,
            processed_units=processed_units,
            unprocessed_regions=unprocessed_regions,
            note=note,
        ),
    )
    return FormatPreservingResult(
        status=status,
        input_path=str(source),
        output_path=str(destination),
        audit_path=str(audit_path),
        report_path=str(report_path),
        input_sha256=source_sha256,
        output_sha256=output_sha256,
        replacements=mapper.replacements,
        replacement_entities=dict(mapper.entity_counts),
        original_unchanged=True,
        manual_review_required=True,
        automatic_release_allowed=False,
        release_allowed=False,
        next_actions=next_actions,
    )


def deidentify_html_copy(
    input_path: str | Path,
    output_path: str | Path | None = None,
) -> FormatPreservingResult:
    try:
        from bs4 import BeautifulSoup, Comment, Doctype, NavigableString
    except ImportError as exc:
        raise RuntimeError(
            "HTML format-preserving de-identification requires: "
            "pip install 'long-gate[documents]'"
        ) from exc

    source, destination, source_bytes, source_sha256 = _paths_and_snapshot(
        input_path, output_path, _HTML_SUFFIXES
    )
    try:
        source_text = source_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("HTML format-preserving path currently requires UTF-8 input.") from exc

    soup = BeautifulSoup(source_text, "html.parser")
    mapper = DirectIdentifierMapper()
    ignored_tags = {"script", "style", "noscript", "template", "svg"}
    processed_text_nodes = 0
    ignored_text_nodes = 0

    for node in list(soup.find_all(string=True)):
        if isinstance(node, (Comment, Doctype)):
            ignored_text_nodes += 1
            continue
        if any(getattr(parent, "name", None) in ignored_tags for parent in node.parents):
            ignored_text_nodes += 1
            continue
        transformed = mapper.replace(str(node))
        if transformed != str(node):
            node.replace_with(NavigableString(transformed))
        processed_text_nodes += 1

    processed_attributes = 0
    attribute_names = {
        "alt",
        "title",
        "aria-label",
        "placeholder",
        "value",
        "href",
        "src",
        "action",
    }
    for tag in soup.find_all(True):
        for name in list(tag.attrs):
            if name not in attribute_names:
                continue
            value = tag.attrs.get(name)
            if isinstance(value, str):
                tag.attrs[name] = mapper.replace(value)
                processed_attributes += 1
            elif isinstance(value, list):
                tag.attrs[name] = [mapper.replace(str(item)) for item in value]
                processed_attributes += len(value)

    output_text = str(soup)
    remaining = scan_text(output_text)
    return _commit_result(
        source=source,
        destination=destination,
        source_sha256=source_sha256,
        payload=output_text.encode("utf-8"),
        format_kind="html",
        mapper=mapper,
        remaining_direct_pii_hits=remaining.total_hits,
        remaining_by_entity=remaining.by_entity,
        processed_units={
            "visible_text_nodes": processed_text_nodes,
            "selected_attributes": processed_attributes,
        },
        unprocessed_regions={
            "comments_doctype_or_ignored_text_nodes": ignored_text_nodes,
        },
        note=(
            "HTML DOM and tag structure are retained, but BeautifulSoup may normalize "
            "source serialization/whitespace. Visible text and selected user-facing/link "
            "attributes are processed; scripts/styles/templates/SVG text are not rewritten."
        ),
    )


def _add_findings(
    text: str,
    total: int,
    by_entity: dict[str, int],
) -> tuple[int, dict[str, int]]:
    findings = scan_text(text)
    total += findings.total_hits
    for entity, count in findings.by_entity.items():
        by_entity[entity] = by_entity.get(entity, 0) + count
    return total, by_entity


def deidentify_xlsx_copy(
    input_path: str | Path,
    output_path: str | Path | None = None,
) -> FormatPreservingResult:
    from openpyxl import load_workbook

    source, destination, source_bytes, source_sha256 = _paths_and_snapshot(
        input_path, output_path, _XLSX_SUFFIXES
    )
    workbook = load_workbook(BytesIO(source_bytes), data_only=False, keep_links=True)
    mapper = DirectIdentifierMapper()
    processed_cells = 0
    processed_comments = 0
    processed_hyperlinks = 0
    processed_properties = 0
    formulas_unmodified = 0
    sheet_titles_unmodified = 0
    defined_names_unmodified = 0
    remaining_total = 0
    remaining_by_entity: dict[str, int] = {}

    for sheet in workbook.worksheets:
        title_findings = scan_text(sheet.title)
        if title_findings.total_hits:
            sheet_titles_unmodified += 1
            remaining_total += title_findings.total_hits
            for entity, count in title_findings.by_entity.items():
                remaining_by_entity[entity] = remaining_by_entity.get(entity, 0) + count

        for row in sheet.iter_rows():
            for cell in row:
                value = cell.value
                if isinstance(value, str):
                    if cell.data_type == "f" or value.startswith("="):
                        formulas_unmodified += 1
                        remaining_total, remaining_by_entity = _add_findings(
                            value, remaining_total, remaining_by_entity
                        )
                    else:
                        cell.value = mapper.replace(value)
                        processed_cells += 1

                if cell.comment is not None:
                    cell.comment.text = mapper.replace(cell.comment.text or "")
                    cell.comment.author = mapper.replace(cell.comment.author or "")
                    processed_comments += 1

                if cell.hyperlink is not None and cell.hyperlink.target:
                    cell.hyperlink.target = mapper.replace(str(cell.hyperlink.target))
                    processed_hyperlinks += 1

    for name in (
        "creator",
        "lastModifiedBy",
        "title",
        "subject",
        "description",
        "keywords",
        "category",
    ):
        value = getattr(workbook.properties, name, None)
        if isinstance(value, str) and value:
            transformed = mapper.replace(value)
            setattr(workbook.properties, name, transformed)
            processed_properties += 1
            remaining_total, remaining_by_entity = _add_findings(
                transformed, remaining_total, remaining_by_entity
            )

    for defined_name in workbook.defined_names.values():
        value = getattr(defined_name, "attr_text", None)
        if isinstance(value, str) and value:
            findings = scan_text(value)
            if findings.total_hits:
                defined_names_unmodified += 1
                remaining_total += findings.total_hits
                for entity, count in findings.by_entity.items():
                    remaining_by_entity[entity] = remaining_by_entity.get(entity, 0) + count

    for sheet in workbook.worksheets:
        for row in sheet.iter_rows():
            for cell in row:
                for value in (
                    cell.value,
                    cell.comment.text if cell.comment is not None else None,
                    cell.comment.author if cell.comment is not None else None,
                    cell.hyperlink.target if cell.hyperlink is not None else None,
                ):
                    if isinstance(value, str) and not (
                        cell.data_type == "f" and value == cell.value
                    ):
                        remaining_total, remaining_by_entity = _add_findings(
                            value, remaining_total, remaining_by_entity
                        )

    out = BytesIO()
    workbook.save(out)
    return _commit_result(
        source=source,
        destination=destination,
        source_sha256=source_sha256,
        payload=out.getvalue(),
        format_kind="xlsx",
        mapper=mapper,
        remaining_direct_pii_hits=remaining_total,
        remaining_by_entity=remaining_by_entity,
        processed_units={
            "worksheets": len(workbook.worksheets),
            "string_cells": processed_cells,
            "comments": processed_comments,
            "hyperlink_targets": processed_hyperlinks,
            "workbook_properties": processed_properties,
        },
        unprocessed_regions={
            "formula_cells": formulas_unmodified,
            "sheet_titles_with_direct_pii": sheet_titles_unmodified,
            "defined_names_with_direct_pii": defined_names_unmodified,
        },
        note=(
            "All worksheets, including hidden sheets, are traversed. String cells, comments, "
            "hyperlink targets, and selected workbook properties are processed. Formulas and "
            "sheet titles/defined names are preserved and reported for manual review."
        ),
    )


def deidentify_file_copy(
    input_path: str | Path,
    output_path: str | Path | None = None,
) -> FormatPreservingResult:
    suffix = Path(input_path).suffix.lower()
    if suffix in SUPPORTED_PRESERVE_TEXT:
        return deidentify_text_copy(input_path, output_path)
    if suffix in _HTML_SUFFIXES:
        return deidentify_html_copy(input_path, output_path)
    if suffix in _XLSX_SUFFIXES:
        return deidentify_xlsx_copy(input_path, output_path)
    raise ValueError(
        "Format-preserving deidentify supports TXT/Markdown, HTML, and XLSX in the "
        "current phase. DOCX/PDF are not silently flattened; use semantic-summarize "
        "only when an abstract text output is actually intended."
    )
