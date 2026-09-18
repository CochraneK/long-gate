import json
from pathlib import Path

import pytest

from longgate.format_deidentify import (
    deidentify_text_copy,
    default_output_path,
    replace_direct_identifiers,
)
from longgate.utils import sha256_file


def test_format_preserving_replaces_direct_identifiers_and_keeps_structure(tmp_path: Path):
    source = tmp_path / "notes.md"
    source.write_text(
        "# 访谈\n\n第一段保持不变。\n\n"
        "邮箱 avery@example.com，再次出现 Avery@example.com。\n"
        "电话 +44 7700 900123，邮编 SW1A 1AA，IP 192.0.2.1。\n",
        encoding="utf-8",
    )
    before = sha256_file(source)

    result = deidentify_text_copy(source)

    output = Path(result.output_path)
    text = output.read_text(encoding="utf-8")
    assert output == default_output_path(source)
    assert output.suffix == source.suffix
    assert "# 访谈\n\n第一段保持不变。\n\n" in text
    assert "avery@example.com" not in text.lower()
    assert text.count("[EMAIL_001]") == 2
    assert "[PHONE_001]" in text
    assert "[POSTCODE_001]" in text
    assert "[IP_ADDRESS_001]" in text
    assert sha256_file(source) == before
    assert result.original_unchanged is True
    assert result.release_allowed is False

    audit = json.loads(Path(result.audit_path).read_text(encoding="utf-8"))
    audit_text = json.dumps(audit, ensure_ascii=False)
    assert "avery@example.com" not in audit_text.lower()
    assert "+44 7700 900123" not in audit_text
    assert audit["format_preserved"] is True


def test_format_preserving_refuses_source_overwrite(tmp_path: Path):
    source = tmp_path / "private.txt"
    source.write_text("person@example.com", encoding="utf-8")
    before = sha256_file(source)

    with pytest.raises(ValueError, match="overwrite"):
        deidentify_text_copy(source, source)

    assert sha256_file(source) == before
    assert source.read_text(encoding="utf-8") == "person@example.com"


def test_format_preserving_requires_same_extension(tmp_path: Path):
    source = tmp_path / "private.md"
    source.write_text("person@example.com", encoding="utf-8")

    with pytest.raises(ValueError, match="same file extension"):
        deidentify_text_copy(source, tmp_path / "private.txt")


def test_format_preserving_fails_closed_for_unsupported_format(tmp_path: Path):
    source = tmp_path / "private.html"
    source.write_text("<p>person@example.com</p>", encoding="utf-8")

    with pytest.raises(ValueError, match="TXT/Markdown only"):
        deidentify_text_copy(source)


def test_direct_identifier_mapping_is_stable_within_document():
    transformed, counts = replace_direct_identifiers(
        "a@example.com then a@example.com and b@example.com"
    )

    assert transformed == "[EMAIL_001] then [EMAIL_001] and [EMAIL_002]"
    assert counts == {"EMAIL": 3}


def test_direct_identifier_replacement_is_idempotent():
    first, _ = replace_direct_identifiers("Contact person@example.com or 192.0.2.1.")
    second, _ = replace_direct_identifiers(first)
    assert second == first


def test_national_id_takes_priority_over_phone_pattern():
    transformed, counts = replace_direct_identifiers("ID 11010519491231002X")
    assert transformed == "ID [NATIONAL_ID_001]"
    assert counts == {"NATIONAL_ID": 1}
