from __future__ import annotations

import ipaddress
import re
from pathlib import Path

from longgate.pii import CN_ID_RE, EMAIL_RE, PHONE_RE, UK_POSTCODE_RE
from longgate.semantic import LocalLlamaCppTransformer

_IP_CANDIDATE_RE = re.compile(r"(?<![\w:])(?:[0-9A-Fa-f:.]{3,})(?![\w:])")


def identity_baseline(text: str) -> str:
    """Negative control: preserve the source exactly."""
    return text


def deterministic_regex_baseline(text: str) -> str:
    """Simple deterministic direct-identifier baseline.

    This intentionally removes only direct patterns already represented by
    Long Gate's deterministic scanner. It is not intended to solve semantic
    re-identification and therefore provides a useful lower baseline.
    """
    result = EMAIL_RE.sub("[EMAIL]", text)
    result = PHONE_RE.sub("[PHONE]", result)
    result = CN_ID_RE.sub("[NATIONAL_ID]", result)
    result = UK_POSTCODE_RE.sub("[POSTCODE]", result)

    chunks: list[str] = []
    cursor = 0
    for match in _IP_CANDIDATE_RE.finditer(result):
        candidate = match.group(0).strip("[](),;")
        try:
            ipaddress.ip_address(candidate)
        except ValueError:
            continue
        chunks.append(result[cursor : match.start()])
        chunks.append("[IP_ADDRESS]")
        cursor = match.end()
    if not chunks:
        return result
    chunks.append(result[cursor:])
    return "".join(chunks)


def presidio_baseline(text: str, language: str = "en") -> str:
    """Optional Presidio anonymization baseline, executed locally."""
    try:
        from presidio_analyzer import AnalyzerEngine
        from presidio_anonymizer import AnonymizerEngine
    except ImportError as exc:
        raise RuntimeError(
            "Presidio baseline requires: pip install -e '.[research-presidio]'"
        ) from exc

    analyzer = AnalyzerEngine()
    findings = analyzer.analyze(text=text, language=language)
    anonymizer = AnonymizerEngine()
    return str(anonymizer.anonymize(text=text, analyzer_results=findings).text)


def one_pass_local_llm_baseline(
    text: str,
    model_path: str | Path,
    *,
    max_tokens: int = 512,
) -> str:
    """One-pass local LLM baseline without audit-guided remediation."""
    transformer = LocalLlamaCppTransformer(model_path)
    return transformer.transform(text, max_tokens=max_tokens, risk_focus=None)


def transform_baseline(
    name: str,
    text: str,
    *,
    model_path: str | Path | None = None,
    language: str = "en",
) -> str:
    if name == "identity":
        return identity_baseline(text)
    if name == "deterministic-regex":
        return deterministic_regex_baseline(text)
    if name == "presidio":
        return presidio_baseline(text, language=language)
    if name == "one-pass-local-llm":
        if model_path is None:
            raise ValueError("one-pass-local-llm baseline requires model_path")
        return one_pass_local_llm_baseline(text, model_path)
    raise ValueError(f"unsupported semantic baseline: {name}")
