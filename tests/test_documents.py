from pathlib import Path

import pytest

from longgate.documents import (
    inspect_document_file,
)


def test_text_document_inspection_stays_local(
    tmp_path: Path,
):
    path = tmp_path / "notes.txt"
    path.write_text(
        "Contact person@example.com after the study.",
        encoding="utf-8",
    )
    result = inspect_document_file(
        path
    )
    assert result.kind == "txt"
    assert result.pii_hits >= 1
    assert result.release_allowed is False
    assert (
        "person@example.com"
        not in str(result.to_dict())
    )


def test_document_inspection_rejects_unknown_type(
    tmp_path: Path,
):
    path = tmp_path / "data.bin"
    path.write_bytes(b"hello")
    with pytest.raises(ValueError):
        inspect_document_file(
            path
        )


def test_html_extraction_ignores_scripts_and_styles(tmp_path: Path):
    path = tmp_path / "note.html"
    path.write_text(
        "<html><style>hidden-css</style><body><h1>Visible</h1>"
        "<script>secret-script</script><p>Body text</p></body></html>",
        encoding="utf-8",
    )

    result = inspect_document_file(path)

    assert result.kind == "html"
    assert result.characters > 0
    assert "scripts" in result.extraction_note
