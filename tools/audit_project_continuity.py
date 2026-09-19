#!/usr/bin/env python3
"""Audit Long Gate's public-safe project continuity and README contract."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HANDOFF = ROOT / "handoff"
STATUS = ROOT / "project-status.json"

REQUIRED_HANDOFF = {
    "README.md",
    "STATUS.md",
    "TODO.md",
    "DECISIONS.md",
    "CONTEXT.md",
    "CHATLOG.md",
    "AGENT_HANDOFF.md",
    "SESSION_LOG.md",
}
EXPECTED_ASSETS = {
    "hero.svg",
    "trust-boundary.svg",
    "capability-zones.svg",
    "security-observability.svg",
    "capability-maturity.svg",
    "handoff.svg",
}
ALLOWED_STATES = {"hardened", "implemented", "research", "planned"}

SECRET_PATTERNS = {
    "aws_access_key": re.compile(r"AKIA[0-9A-Z]{16}"),
    "github_token": re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    "openai_style_key": re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    "private_key": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "bearer_token": re.compile(r"Bearer\s+[A-Za-z0-9._~-]{20,}"),
}


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def main() -> int:
    errors: list[str] = []

    missing_handoff = sorted(
        name for name in REQUIRED_HANDOFF if not (HANDOFF / name).is_file()
    )
    if missing_handoff:
        fail(errors, f"missing handoff files: {missing_handoff}")

    try:
        status = json.loads(STATUS.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(errors, f"invalid project-status.json: {exc}")
        status = {}

    capabilities = status.get("capabilities", [])
    if not isinstance(capabilities, list) or not capabilities:
        fail(errors, "project-status.json must define a non-empty capabilities list")
        capabilities = []

    seen_ids: set[str] = set()
    for item in capabilities:
        if not isinstance(item, dict):
            fail(errors, "capability entries must be objects")
            continue
        capability_id = item.get("id")
        if not isinstance(capability_id, str) or not capability_id:
            fail(errors, "capability id must be a non-empty string")
            continue
        if capability_id in seen_ids:
            fail(errors, f"duplicate capability id: {capability_id}")
        seen_ids.add(capability_id)

        state = item.get("state")
        if state not in ALLOWED_STATES:
            fail(errors, f"{capability_id}: invalid state {state!r}")

        evidence = item.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            fail(errors, f"{capability_id}: evidence must be a non-empty list")
            continue
        for relative in evidence:
            if not isinstance(relative, str) or not relative:
                fail(errors, f"{capability_id}: invalid evidence path")
                continue
            if not (ROOT / relative).exists():
                fail(errors, f"{capability_id}: missing evidence path {relative}")

    readme_zh = ROOT / "README.md"
    readme_en = ROOT / "README.en.md"
    readme_legacy = ROOT / "README.zh-CN.md"
    for path in (readme_zh, readme_en, readme_legacy):
        if not path.is_file():
            fail(errors, f"missing README surface: {path.name}")

    if readme_zh.is_file() and readme_en.is_file():
        zh_text = readme_zh.read_text(encoding="utf-8")
        en_text = readme_en.read_text(encoding="utf-8")
        if "README.en.md" not in zh_text:
            fail(errors, "Chinese README must link to README.en.md")
        if "README.md" not in en_text:
            fail(errors, "English README must link back to README.md")
        for lang, text in (("zh", zh_text), ("en", en_text)):
            for asset in EXPECTED_ASSETS:
                expected_ref = f"docs/assets/readme/{lang}/{asset}"
                if expected_ref not in text:
                    fail(errors, f"{lang} README missing asset reference {expected_ref}")

    if readme_zh.is_file() and readme_legacy.is_file():
        if readme_zh.read_bytes() != readme_legacy.read_bytes():
            fail(errors, "README.zh-CN.md must remain a compatibility copy of README.md")

    for lang in ("zh", "en"):
        asset_dir = ROOT / "docs" / "assets" / "readme" / lang
        missing = sorted(name for name in EXPECTED_ASSETS if not (asset_dir / name).is_file())
        if missing:
            fail(errors, f"{lang} README assets missing: {missing}")

    if HANDOFF.is_dir():
        for path in HANDOFF.glob("*.md"):
            text = path.read_text(encoding="utf-8")
            for name, pattern in SECRET_PATTERNS.items():
                if pattern.search(text):
                    fail(errors, f"possible {name} in public handoff file {path.name}")

    if errors:
        print("Long Gate continuity audit FAILED")
        for error in errors:
            print(f"- {error}")
        return 1

    print(
        "Long Gate continuity audit passed: "
        f"{len(REQUIRED_HANDOFF)} handoff files, "
        f"{len(capabilities)} capabilities, "
        f"{len(EXPECTED_ASSETS) * 2} bilingual SVG assets."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
