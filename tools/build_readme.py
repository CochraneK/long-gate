#!/usr/bin/env python3
"""Build the bilingual root README files from reviewed templates."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "docs" / "readme"


def main() -> int:
    zh = (TEMPLATES / "README.zh-CN.template.md").read_text(encoding="utf-8")
    en = (TEMPLATES / "README.en.template.md").read_text(encoding="utf-8")
    (ROOT / "README.md").write_text(zh.rstrip() + "\n", encoding="utf-8")
    (ROOT / "README.zh-CN.md").write_text(zh.rstrip() + "\n", encoding="utf-8")
    (ROOT / "README.en.md").write_text(en.rstrip() + "\n", encoding="utf-8")
    print("Built README.md, README.zh-CN.md, and README.en.md.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
