import json
import zipfile
from io import BytesIO
from pathlib import Path

from docx import Document
from openpyxl import Workbook, load_workbook
from openpyxl.comments import Comment

from longgate.document_deidentify import deidentify_file_copy
from longgate.utils import sha256_file


def test_html_preserves_dom_and_shared_identifier_mapping(tmp_path: Path):
    source = tmp_path / "page.html"
    source.write_text(
        """<!doctype html>
<html><head><title>Case</title></head>
<body>
<p>Contact person@example.com</p>
<a href="mailto:person@example.com" aria-label="person@example.com">Email</a>
<table><tr><td>192.0.2.1</td></tr></table>
<script>const hidden = "script@example.com";</script>
</body></html>""",
        encoding="utf-8",
    )
    before = sha256_file(source)

    result = deidentify_file_copy(source)

    output = Path(result.output_path)
    text = output.read_text(encoding="utf-8")
    assert "<table>" in text
    assert text.count("[EMAIL_001]") == 3
    assert "[IP_ADDRESS_001]" in text
    assert "script@example.com" in text
    assert result.status == "LOCAL_ONLY"
    assert result.release_allowed is False
    assert sha256_file(source) == before

    audit = json.loads(Path(result.audit_path).read_text(encoding="utf-8"))
    assert audit["processed_units"]["visible_text_nodes"] >= 1
    assert audit["unprocessed_regions"]["comments_doctype_or_ignored_text_nodes"] >= 1
    assert audit["remaining_direct_pii_hits"] >= 1
    assert "person@example.com" not in json.dumps(audit)


def test_xlsx_processes_all_sheets_comments_links_and_properties(tmp_path: Path):
    source = tmp_path / "study.xlsx"
    workbook = Workbook()
    visible = workbook.active
    visible.title = "Visible"
    visible["A1"] = "person@example.com"
    visible["A2"] = "person@example.com"
    visible["A3"] = '="formula@example.com"'
    visible["B1"] = "Click"
    visible["B1"].hyperlink = "mailto:person@example.com"
    visible["C1"].comment = Comment("person@example.com", "author@example.com")

    hidden = workbook.create_sheet("Hidden")
    hidden.sheet_state = "hidden"
    hidden["A1"] = "person@example.com"
    workbook.properties.creator = "owner@example.com"
    workbook.save(source)
    before = sha256_file(source)

    result = deidentify_file_copy(source)

    output = Path(result.output_path)
    rewritten = load_workbook(output, data_only=False, keep_links=True)
    assert rewritten["Visible"]["A1"].value == "[EMAIL_001]"
    assert rewritten["Visible"]["A2"].value == "[EMAIL_001]"
    assert rewritten["Hidden"]["A1"].value == "[EMAIL_001]"
    assert rewritten["Visible"]["A3"].value == '="formula@example.com"'
    assert rewritten["Visible"]["B1"].hyperlink.target == "mailto:[EMAIL_001]"
    assert rewritten["Visible"]["C1"].comment.text == "[EMAIL_001]"
    assert rewritten["Visible"]["C1"].comment.author == "[EMAIL_002]"
    assert rewritten.properties.creator == "[EMAIL_003]"
    assert result.status == "LOCAL_ONLY"
    assert sha256_file(source) == before

    audit = json.loads(Path(result.audit_path).read_text(encoding="utf-8"))
    assert audit["processed_units"]["worksheets"] == 2
    assert audit["unprocessed_regions"]["formula_cells"] >= 1
    assert audit["remaining_direct_pii_hits"] >= 1
    payload = json.dumps(audit)
    assert "formula@example.com" not in payload
    assert "person@example.com" not in payload


def test_xlsx_without_unprocessed_direct_pii_reaches_manual_review(tmp_path: Path):
    source = tmp_path / "clean-formula.xlsx"
    workbook = Workbook()
    workbook.active["A1"] = "person@example.com"
    workbook.active["A2"] = "=1+1"
    workbook.save(source)

    result = deidentify_file_copy(source)

    assert result.status == "MANUAL_REVIEW_REQUIRED"
    assert result.release_allowed is False


def test_docx_replaces_identifier_split_across_runs_and_preserves_run_styles(tmp_path: Path):
    source = tmp_path / "interview.docx"
    document = Document()
    paragraph = document.add_paragraph()
    first = paragraph.add_run("Contact person@")
    first.bold = True
    second = paragraph.add_run("example.com now")
    second.italic = True

    table = document.add_table(rows=1, cols=1)
    table.cell(0, 0).text = "person@example.com"
    header = document.sections[0].header.paragraphs[0]
    header.text = "person@example.com"
    footer = document.sections[0].footer.paragraphs[0]
    footer.text = "Call +44 7700 900123"
    document.core_properties.author = "owner@example.com"
    document.save(source)
    before = sha256_file(source)

    result = deidentify_file_copy(source)

    rewritten = Document(result.output_path)
    body_runs = rewritten.paragraphs[0].runs
    body_text = "".join(run.text for run in body_runs)
    assert "person@example.com" not in body_text
    assert "[EMAIL_" in body_text
    assert body_runs[0].bold is True
    assert body_runs[1].italic is True

    body_label = next(
        token
        for token in body_text.split()
        if token.startswith("[EMAIL_")
    )
    assert rewritten.tables[0].cell(0, 0).text == body_label
    assert rewritten.sections[0].header.paragraphs[0].text == body_label
    assert "[PHONE_" in rewritten.sections[0].footer.paragraphs[0].text
    assert rewritten.core_properties.author.startswith("[EMAIL_")
    assert result.status == "MANUAL_REVIEW_REQUIRED"
    assert result.release_allowed is False
    assert sha256_file(source) == before

    audit = json.loads(Path(result.audit_path).read_text(encoding="utf-8"))
    payload = json.dumps(audit)
    assert "person@example.com" not in payload
    assert "owner@example.com" not in payload
    assert audit["processed_units"]["paragraphs"] >= 4
    assert audit["remaining_direct_pii_hits"] == 0


def test_docx_embedded_object_forces_local_only(tmp_path: Path):
    base = tmp_path / "base.docx"
    document = Document()
    document.add_paragraph("person@example.com")
    document.save(base)

    source = tmp_path / "embedded.docx"
    source_buffer = BytesIO(base.read_bytes())
    output_buffer = BytesIO()
    with zipfile.ZipFile(source_buffer, "r") as original:
        with zipfile.ZipFile(output_buffer, "w") as rewritten:
            for info in original.infolist():
                rewritten.writestr(info, original.read(info.filename))
            rewritten.writestr("word/embeddings/opaque.bin", b"opaque-private-content")
    source.write_bytes(output_buffer.getvalue())

    result = deidentify_file_copy(source)

    assert result.status == "LOCAL_ONLY"
    audit = json.loads(Path(result.audit_path).read_text(encoding="utf-8"))
    assert audit["unprocessed_regions"]["embedded_entries"] == 1
    with zipfile.ZipFile(result.output_path, "r") as rewritten:
        assert rewritten.read("word/embeddings/opaque.bin") == b"opaque-private-content"


def test_docx_rejects_invalid_zip_package(tmp_path: Path):
    source = tmp_path / "broken.docx"
    source.write_bytes(b"not-a-zip")

    try:
        deidentify_file_copy(source)
    except ValueError as exc:
        assert "valid DOCX" in str(exc)
    else:
        raise AssertionError("Expected invalid DOCX package to fail closed")


def _copy_docx_with_extra_entry(source: Path, destination: Path, name: str, payload: bytes) -> None:
    input_buffer = BytesIO(source.read_bytes())
    output_buffer = BytesIO()
    with zipfile.ZipFile(input_buffer, "r") as original:
        with zipfile.ZipFile(output_buffer, "w") as rewritten:
            for info in original.infolist():
                rewritten.writestr(info, original.read(info.filename))
            rewritten.writestr(name, payload)
    destination.write_bytes(output_buffer.getvalue())


def test_docx_digitally_signed_package_fails_closed(tmp_path: Path):
    base = tmp_path / "base.docx"
    document = Document()
    document.add_paragraph("person@example.com")
    document.save(base)

    signed = tmp_path / "signed.docx"
    _copy_docx_with_extra_entry(
        base,
        signed,
        "_xmlsignatures/sig1.xml",
        b"<Signature/>",
    )

    try:
        deidentify_file_copy(signed)
    except ValueError as exc:
        assert "Digitally signed DOCX" in str(exc)
    else:
        raise AssertionError("Expected signed DOCX rewrite to fail closed")


def test_docx_relationship_pii_forces_local_only(tmp_path: Path):
    source = tmp_path / "linked.docx"
    document = Document()
    paragraph = document.add_paragraph("Visible text")
    part = paragraph.part
    relationship_id = part.relate_to(
        "mailto:person@example.com",
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink",
        is_external=True,
    )
    assert relationship_id
    document.save(source)

    result = deidentify_file_copy(source)

    assert result.status == "LOCAL_ONLY"
    audit = json.loads(Path(result.audit_path).read_text(encoding="utf-8"))
    assert audit["unprocessed_regions"]["relationship_parts_with_direct_pii"] >= 1
    assert audit["remaining_direct_pii_hits"] >= 1
    assert "person@example.com" not in json.dumps(audit)
