import json
import sys
from pathlib import Path

from longgate import app
from longgate.deidentify import DeidentifyResult


def test_top_level_help_surfaces_product_commands(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["longgate", "--help"])

    app.main()

    output = capsys.readouterr().out
    assert "longgate setup" in output
    assert "longgate hardware" in output
    assert "longgate deidentify" in output
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


def test_deidentify_dispatches_bounded_product_path(monkeypatch, capsys, tmp_path: Path):
    captured = {}

    def fake_deidentify(input_path, model_path, output_path, *, max_rounds, max_tokens):
        captured.update(
            {
                "input": input_path,
                "model": model_path,
                "output": output_path,
                "max_rounds": max_rounds,
                "max_tokens": max_tokens,
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
    output = tmp_path / "out.txt"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "longgate",
            "deidentify",
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
    assert payload["release_allowed"] is False


def test_doctor_explains_python_313_windows_local_llm_gap(monkeypatch):
    from longgate import doctor

    monkeypatch.setattr(doctor, "_has", lambda module: False)
    monkeypatch.setattr(doctor.platform, "system", lambda: "Windows")
    monkeypatch.setattr(doctor.sys, "version_info", (3, 13, 0))

    detail = doctor._local_llm_detail()

    assert "Python 3.13 on Windows" in detail
    assert "Python 3.12" in detail
