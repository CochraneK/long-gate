import json

from longgate import secret_scan


def test_missing_gitleaks_fails_closed_without_remote_fallback(monkeypatch, tmp_path):
    monkeypatch.setattr(secret_scan.shutil, "which", lambda _name: None)
    result = secret_scan.scan_secrets_with_gitleaks(tmp_path)

    assert result.engine_available is False
    assert result.release_allowed is False
    assert result.findings == 0
    assert "does not upload" in result.note


def test_gitleaks_report_omits_matched_secret_values(monkeypatch, tmp_path):
    source = tmp_path / "repo"
    source.mkdir()
    leaked_value = "very-secret-value"

    monkeypatch.setattr(secret_scan.shutil, "which", lambda _name: "/usr/bin/gitleaks")

    def fake_run(command, **_kwargs):
        report_path = command[command.index("--report-path") + 1]
        findings = [
            {
                "RuleID": "generic-api-key",
                "File": str(source / "config.py"),
                "Secret": leaked_value,
                "Match": f'API_KEY="{leaked_value}"',
            }
        ]
        with open(report_path, "w", encoding="utf-8") as handle:
            json.dump(findings, handle)

        class Completed:
            returncode = 0

        return Completed()

    monkeypatch.setattr(secret_scan.subprocess, "run", fake_run)
    result = secret_scan.scan_secrets_with_gitleaks(source)
    rendered = json.dumps(result.to_dict())

    assert result.engine_available is True
    assert result.findings == 1
    assert result.files == ["config.py"]
    assert result.rules == {"generic-api-key": 1}
    assert leaked_value not in rendered
