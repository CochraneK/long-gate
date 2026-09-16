from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).parents[1]


def _match(
    pattern: str,
    text: str,
    label: str,
) -> str:
    match = re.search(
        pattern,
        text,
        re.MULTILINE,
    )
    if not match:
        raise SystemExit(
            f"Could not find {label}."
        )
    return match.group(1)


def main() -> None:
    pyproject = (
        ROOT / "pyproject.toml"
    ).read_text(
        encoding="utf-8"
    )
    init_file = (
        ROOT
        / "src"
        / "longgate"
        / "__init__.py"
    ).read_text(
        encoding="utf-8"
    )
    citation = (
        ROOT / "CITATION.cff"
    ).read_text(
        encoding="utf-8"
    )

    package_version = _match(
        r'^version = "([^"]+)"$',
        pyproject,
        "pyproject version",
    )
    runtime_version = _match(
        r'^__version__ = "([^"]+)"$',
        init_file,
        "runtime version",
    )
    citation_version = _match(
        r"^version: ([^\s]+)$",
        citation,
        "citation version",
    )

    versions = {
        package_version,
        runtime_version,
        citation_version,
    }
    if len(versions) != 1:
        raise SystemExit(
            "Version mismatch: "
            f"pyproject={package_version}, "
            f"runtime={runtime_version}, "
            f"citation={citation_version}"
        )

    readme = (
        ROOT / "README.md"
    ).read_text(
        encoding="utf-8"
    )
    required_phrases = [
        "row-level synthetic egress remains fail-closed",
        "not a digital signature",
        "not certifications",
    ]
    missing = [
        phrase
        for phrase in required_phrases
        if phrase.lower()
        not in readme.lower()
    ]
    if missing:
        raise SystemExit(
            "README is missing release-safety language: "
            + ", ".join(missing)
        )

    print(
        "Release metadata consistent: "
        f"{package_version}"
    )


if __name__ == "__main__":
    main()
