from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from pathlib import Path

from .pii import CN_ID_RE, EMAIL_RE, PHONE_RE, UK_POSTCODE_RE, scan_text

SUPPORTED_TEXT = {".txt", ".md", ".markdown"}


@dataclass(frozen=True)
class TextInspection:
    path: str
    characters: int
    lines: int
    pii_hits: int
    pii_by_entity: dict[str, int]
    release_allowed: bool
    reason: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def load_text_file(path: str | Path) -> str:
    p = Path(path)
    if p.suffix.lower() not in SUPPORTED_TEXT:
        raise ValueError(f"Unsupported text type: {p.suffix}. Supported: {sorted(SUPPORTED_TEXT)}")
    return p.read_text(encoding="utf-8")


def inspect_text_file(path: str | Path) -> TextInspection:
    p = Path(path)
    text = load_text_file(p)
    findings = scan_text(text)
    return TextInspection(
        path=p.name,
        characters=len(text),
        lines=text.count("\n") + (1 if text else 0),
        pii_hits=findings.total_hits,
        pii_by_entity=findings.by_entity,
        release_allowed=False,
        reason=(
            "Free text remains local-only in the v0.5 baseline. "
            "Pattern-level redaction is not a semantic privacy guarantee."
        ),
    )


def redact_text_local(text: str) -> str:
    """Local preview redaction only. Output is NOT automatically network-safe."""
    redacted = EMAIL_RE.sub("[EMAIL]", text)
    redacted = PHONE_RE.sub("[PHONE]", redacted)
    redacted = CN_ID_RE.sub("[NATIONAL_ID]", redacted)
    redacted = UK_POSTCODE_RE.sub("[POSTCODE]", redacted)

    ipv4 = re.compile(
        r"(?<!\d)(?:25[0-5]|2[0-4]\d|1?\d?\d)"
        r"(?:\.(?:25[0-5]|2[0-4]\d|1?\d?\d)){3}(?!\d)"
    )
    redacted = ipv4.sub("[IP_ADDRESS]", redacted)
    return redacted


def redact_text_file_local(
    input_path: str | Path,
    output_path: str | Path,
) -> Path:
    text = load_text_file(input_path)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        redact_text_local(text),
        encoding="utf-8",
    )
    return output
