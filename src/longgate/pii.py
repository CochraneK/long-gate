from __future__ import annotations

import ipaddress
import re
from collections.abc import Iterable
from dataclasses import asdict, dataclass

import pandas as pd

EMAIL_RE = re.compile(r"(?<![\w.+-])[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}(?![\w.-])", re.IGNORECASE)
PHONE_RE = re.compile(r"(?<!\d)(?:\+?\d[\d ()-]{7,}\d)(?!\d)")
CN_ID_RE = re.compile(r"(?<!\d)\d{17}[\dXx](?!\d)")
UK_POSTCODE_RE = re.compile(r"\b(?:GIR ?0AA|[A-Z]{1,2}\d[A-Z\d]? ?\d[A-Z]{2})\b", re.IGNORECASE)


@dataclass
class PiiFindingSummary:
    total_hits: int
    by_entity: dict[str, int]
    by_column: dict[str, int]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _iter_text(values: Iterable[object]) -> Iterable[str]:
    for value in values:
        if pd.isna(value):
            continue
        text = str(value)
        if text:
            yield text


def _count_text(text: str) -> dict[str, int]:
    counts = {
        "email": len(EMAIL_RE.findall(text)),
        "phone": len(PHONE_RE.findall(text)),
        "cn_national_id": len(CN_ID_RE.findall(text)),
        "uk_postcode": len(UK_POSTCODE_RE.findall(text)),
        "ip_address": 0,
    }
    for token in re.findall(r"(?<![\w:])(?:[0-9A-Fa-f:.]{3,})(?![\w:])", text):
        try:
            ipaddress.ip_address(token.strip("[](),;"))
            counts["ip_address"] += 1
        except ValueError:
            pass
    return counts


def scan_dataframe_values(df: pd.DataFrame) -> PiiFindingSummary:
    """Local, value-level scan which returns counts only, never matched values."""
    by_entity: dict[str, int] = {}
    by_column: dict[str, int] = {}
    for col in df.columns:
        col_hits = 0
        for text in _iter_text(df[col].tolist()):
            counts = _count_text(text)
            for entity, count in counts.items():
                if count:
                    by_entity[entity] = by_entity.get(entity, 0) + count
                    col_hits += count
        if col_hits:
            by_column[str(col)] = col_hits
    return PiiFindingSummary(sum(by_entity.values()), by_entity, by_column)


def scan_text(text: str) -> PiiFindingSummary:
    counts = {k: v for k, v in _count_text(text).items() if v}
    return PiiFindingSummary(
        sum(counts.values()), counts, {"payload": sum(counts.values())} if counts else {}
    )


def scan_dataframe_values_presidio(
    df: pd.DataFrame,
    language: str = "en",
) -> PiiFindingSummary:
    """Optional local Presidio scan. Only entity counts leave this function."""
    try:
        from presidio_analyzer import AnalyzerEngine
    except ImportError as exc:
        raise RuntimeError(
            "Presidio scanner requested but not installed. Run: pip install 'long-gate[presidio]'"
        ) from exc

    analyzer = AnalyzerEngine()
    by_entity: dict[str, int] = {}
    by_column: dict[str, int] = {}
    for col in df.columns:
        col_hits = 0
        for text in _iter_text(df[col].tolist()):
            for result in analyzer.analyze(text=text, language=language):
                entity = str(result.entity_type).lower()
                by_entity[entity] = by_entity.get(entity, 0) + 1
                col_hits += 1
        if col_hits:
            by_column[str(col)] = col_hits
    return PiiFindingSummary(sum(by_entity.values()), by_entity, by_column)


def scan_structured_strings(value: object) -> PiiFindingSummary:
    """Scan string keys and leaves in structured data.

    Numeric aggregate values are not text identifiers. Scanning their JSON
    rendering with phone-number regexes can create false positives on long
    decimal expansions. Dictionary keys are scanned because source-derived
    column names and labels can themselves contain direct identifiers.
    """
    totals: dict[str, int] = {}

    def visit(item: object) -> None:
        if isinstance(item, str):
            counts = _count_text(item)
            for entity, count in counts.items():
                if count:
                    totals[entity] = totals.get(entity, 0) + count
            return
        if isinstance(item, dict):
            for key, child in item.items():
                if isinstance(key, str):
                    visit(key)
                visit(child)
            return
        if isinstance(item, (list, tuple, set)):
            for child in item:
                visit(child)

    visit(value)
    total = sum(totals.values())
    return PiiFindingSummary(
        total,
        totals,
        {"payload": total} if total else {},
    )
