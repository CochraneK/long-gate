from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

_WHITESPACE_RE = re.compile(r"\s+")
SENSITIVE_TYPES = {"DIRECT", "QUASI"}


@dataclass(frozen=True)
class TabMention:
    span_text: str
    identifier_type: str
    entity_type: str | None
    start_offset: int | None
    end_offset: int | None


@dataclass(frozen=True)
class TabDocument:
    doc_id: str
    dataset_type: str
    text: str
    mentions: tuple[TabMention, ...]


def _walk(value: object) -> Iterable[dict[str, Any]]:
    if isinstance(value, dict):
        if "identifier_type" in value and "span_text" in value:
            yield value
        for child in value.values():
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)


def _optional_int(value: object) -> int | None:
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    return None


def extract_mentions(annotations: object) -> tuple[TabMention, ...]:
    """Extract TAB entity mentions without assuming an annotator nesting layout."""
    mentions: list[TabMention] = []
    seen: set[tuple[object, ...]] = set()
    for item in _walk(annotations):
        span = item.get("span_text")
        identifier_type = item.get("identifier_type")
        if not isinstance(span, str) or not span.strip():
            continue
        if not isinstance(identifier_type, str) or not identifier_type.strip():
            continue
        normalized_type = identifier_type.strip().upper()
        start = _optional_int(item.get("start_offset"))
        end = _optional_int(item.get("end_offset"))
        entity_type = item.get("entity_type")
        entity_type = str(entity_type) if entity_type is not None else None
        key = (start, end, span, normalized_type, entity_type)
        if key in seen:
            continue
        seen.add(key)
        mentions.append(
            TabMention(
                span_text=span,
                identifier_type=normalized_type,
                entity_type=entity_type,
                start_offset=start,
                end_offset=end,
            )
        )
    return tuple(mentions)


def load_tab_documents(path: str | Path) -> list[TabDocument]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("TAB split must be a JSON list of document objects.")

    documents: list[TabDocument] = []
    seen_ids: set[str] = set()
    for index, item in enumerate(payload):
        if not isinstance(item, dict):
            raise ValueError(f"TAB document {index} is not an object")
        text = item.get("text")
        doc_id = item.get("doc_id")
        dataset_type = item.get("dataset_type")
        if not isinstance(text, str) or not text:
            raise ValueError(f"TAB document {index} has no text")
        if not isinstance(doc_id, str) or not doc_id:
            raise ValueError(f"TAB document {index} has no doc_id")
        if doc_id in seen_ids:
            raise ValueError(f"duplicate TAB doc_id: {doc_id}")
        seen_ids.add(doc_id)
        documents.append(
            TabDocument(
                doc_id=doc_id,
                dataset_type=str(dataset_type or "unknown"),
                text=text,
                mentions=extract_mentions(item.get("annotations", {})),
            )
        )
    return documents


def normalize_literal(text: str) -> str:
    return _WHITESPACE_RE.sub(" ", text).strip().casefold()


def literal_present(candidate: str, literal: str) -> bool:
    normalized_literal = normalize_literal(literal)
    return bool(normalized_literal) and normalized_literal in normalize_literal(candidate)


def score_candidate(document: TabDocument, candidate: str) -> dict[str, float | int]:
    groups: dict[str, list[TabMention]] = {
        "DIRECT": [],
        "QUASI": [],
        "NO_MASK": [],
    }
    for mention in document.mentions:
        if mention.identifier_type in groups:
            groups[mention.identifier_type].append(mention)

    def retention(mentions: list[TabMention]) -> tuple[int, int, float]:
        total = len(mentions)
        retained = sum(literal_present(candidate, mention.span_text) for mention in mentions)
        rate = retained / total if total else 0.0
        return total, retained, round(rate, 6)

    direct_total, direct_retained, direct_rate = retention(groups["DIRECT"])
    quasi_total, quasi_retained, quasi_rate = retention(groups["QUASI"])
    no_mask_total, no_mask_retained, no_mask_rate = retention(groups["NO_MASK"])
    sensitive_total = direct_total + quasi_total
    sensitive_retained = direct_retained + quasi_retained
    sensitive_retention = sensitive_retained / sensitive_total if sensitive_total else 0.0

    return {
        "sensitive_mentions": sensitive_total,
        "sensitive_literals_retained": sensitive_retained,
        "sensitive_literal_retention_rate": round(sensitive_retention, 6),
        "sensitive_literal_removal_rate": round(1.0 - sensitive_retention, 6)
        if sensitive_total
        else 0.0,
        "direct_mentions": direct_total,
        "direct_literals_retained": direct_retained,
        "direct_literal_retention_rate": direct_rate,
        "quasi_mentions": quasi_total,
        "quasi_literals_retained": quasi_retained,
        "quasi_literal_retention_rate": quasi_rate,
        "no_mask_mentions": no_mask_total,
        "no_mask_literals_retained": no_mask_retained,
        "no_mask_literal_retention_rate": no_mask_rate,
    }
