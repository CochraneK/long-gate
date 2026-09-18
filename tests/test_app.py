import json
import sys
from pathlib import Path

from longgate import app
from longgate.deidentify import DeidentifyResult
from longgate.format_deidentify import FormatPreservingResult


def test_top_level_help_surfaces_product_commands(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["longgate", "--help"])

    app.main()

    output = capsys.readouterr().out
    assert "longgate setup" in output
    assert "longgate hardware" in output
    assert "longgate deidentify" in output
    assert "longgate semantic-summarize" in output
    assert "longgate run" in output


def test_setup_recommend_only_does_not_call_installer(monkeypatch, capsys):
    monkeypatch.setattr(
        app,
        "hardware_advice",
        lambda **_kwargs: {"hardware": {"ram_gb": 16.0}, "mode": "recommend-only"},
    )
    monkeypatch.setattr(
        app,
        "setup_local_ai",
        lambda **_kwargs: (_ for _ in ()).throw(AssertionError("installer must not run")),
    )
    monkeypatch.setattr(sys, "argv", ["longgate", "setup", "--recommend-only"])

    app.main()

    payload = json.loads(capsys.readouterr().out)
    assert payload["mode"] == "recommend-only"


def test_deidentify_dispatches_format_preserving_path(monkeypatch, capsys, tmp_path: Path):
    captured = {}

    def fake_deidentify(input_path, output_path):
        captured.update({"input": input_path, "output": output_path})
        output = Path(output_path)
        return FormatPreservingResult(
            status="MANUAL_REVIEW_REQUIRED",
            input_path=str(input_path),
            output_path=str(output),
            audit_path=str(output) + ".audit.json",
            report_path=str(output) + ".trust-report.html",
            input_sha256="a" * 64,
            output_sha256="b" * 64,
            replacements=2,
            replacement_entities={"EMAIL": 2},
            original_unchanged=True,
            manual_review_required=True,
            automatic_release_allowed=False,
            release_allowed=False,
            next_actions=["review"],
        )

    monkeypatch.setattr(app, "deidentify_file_copy", fake_deidentify)
    output = tmp_path / "out.txt"
    monkeypatch.setattr(
        sys,
        "argv",
        ["longgate", "deidentify", "interview.txt", "--out", str(output)],
    )

    app.main()

    payload = json.loads(capsys.readouterr().out)
    assert captured["input"] == "interview.txt"
    assert captured["output"] == str(output)
    assert payload["original_unchanged"] is True
    assert payload["release_allowed"] is False


def test_semantic_summarize_dispatches_bounded_product_path(
    monkeypatch, capsys, tmp_path: Path
):
    captured = {}

    def fake_deidentify(
        input_path,
        model_path,
        output_path,
        *,
        max_rounds,
        max_tokens,
        chunking,
        chunk_size,
    ):
        captured.update(
            {
                "input": input_path,
                "model": model_path,
                "output": output_path,
                "max_rounds": max_rounds,
                "max_tokens": max_tokens,
                "chunking": chunking,
                "chunk_size": chunk_size,
            }
        )
        return DeidentifyResult(
            status="LOCAL_ONLY",
            output_path=str(output_path),
            audit_path=str(output_path) + ".audit.json",
            report_path=str(output_path) + ".trust-report.html",
            model_path="/models/fake.gguf",
            attempts=2,
            eligible_for_manual_review=False,
            manual_review_required=True,
            automatic_release_allowed=False,
            release_allowed=False,
            next_actions=["keep local"],
        )

    monkeypatch.setattr(app, "deidentify_local", fake_deidentify)
    output = tmp_path / "summary.txt"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "longgate",
            "semantic-summarize",
            "interview.txt",
            "--out",
            str(output),
            "--max-rounds",
            "2",
        ],
    )

    app.main()

    payload = json.loads(capsys.readouterr().out)
    assert captured["input"] == "interview.txt"
    assert captured["model"] == "auto"
    assert captured["max_rounds"] == 2
    assert captured["max_tokens"] == 512
    assert captured["chunking"] == "none"
    assert payload["release_allowed"] is False


def test_doctor_explains_python_313_windows_local_llm_gap(monkeypatch):
    from longgate import doctor

    monkeypatch.setattr(doctor, "_has", lambda module: False)
    monkeypatch.setattr(doctor.platform, "system", lambda: "Windows")
    monkeypatch.setattr(doctor.sys, "version_info", (3, 13, 0))

    detail = doctor._local_llm_detail()

    assert "Python 3.13 on Windows" in detail
    assert "Python 3.12" in detail


def test_doctor_deep_reports_failed_local_check_without_crashing(monkeypatch, capsys):
    from longgate.doctor import Capability

    monkeypatch.setattr(
        app,
        "capabilities",
        lambda: [Capability("python", True, "test")],
    )
    monkeypatch.setattr(
        app,
        "deep_local_llm_check",
        lambda _model: Capability("local_llm_deep", False, "model unavailable"),
    )
    monkeypatch.setattr(sys, "argv", ["longgate", "doctor", "--deep"])

    app.main()

    payload = json.loads(capsys.readouterr().out)
    assert payload[-1]["name"] == "local_llm_deep"
    assert payload[-1]["available"] is False
