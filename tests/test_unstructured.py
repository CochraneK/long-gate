from pathlib import Path

from longgate.unstructured import (
    inspect_text_file,
    redact_text_local,
)


def test_text_inspection_never_marks_free_text_release_safe(tmp_path: Path):
    p = tmp_path / "interview.txt"
    p.write_text(
        "Contact person@example.com after the interview.",
        encoding="utf-8",
    )
    result = inspect_text_file(p)
    assert result.pii_hits >= 1
    assert result.release_allowed is False
    assert "person@example.com" not in str(result.to_dict())


def test_local_redaction_is_preview_only():
    text = "Email person@example.com or call +44 7700 900123."
    redacted = redact_text_local(text)
    assert "person@example.com" not in redacted
    assert "[EMAIL]" in redacted
