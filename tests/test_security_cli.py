import json
import sys
from types import SimpleNamespace

from longgate import app


def _result(**payload):
    return SimpleNamespace(to_dict=lambda: payload)


def test_endpoint_cli_dispatches_without_prompt(monkeypatch, capsys):
    captured = {}

    def fake_inspect(url, *, connect, timeout):
        captured.update(url=url, connect=connect, timeout=timeout)
        return _result(classification="CUSTOM_OR_UNKNOWN_ENDPOINT", relay_possible=True)

    monkeypatch.setattr(app, "inspect_endpoint", fake_inspect)
    monkeypatch.setattr(
        sys,
        "argv",
        ["longgate", "endpoint", "inspect", "https://relay.example.test/v1", "--no-connect"],
    )

    app.main()

    payload = json.loads(capsys.readouterr().out)
    assert captured["url"] == "https://relay.example.test/v1"
    assert captured["connect"] is False
    assert payload["relay_possible"] is True


def test_egress_har_cli_dispatches(monkeypatch, capsys):
    monkeypatch.setattr(
        app,
        "inspect_har",
        lambda path: _result(source=path, entries=2, release_allowed=False),
    )
    monkeypatch.setattr(
        sys,
        "argv",
        ["longgate", "egress", "inspect-har", "capture.har"],
    )

    app.main()

    payload = json.loads(capsys.readouterr().out)
    assert payload["source"] == "capture.har"
    assert payload["release_allowed"] is False


def test_secret_cli_dispatches_history_mode(monkeypatch, capsys):
    captured = {}

    def fake_scan(path, *, history):
        captured.update(path=path, history=history)
        return _result(engine="gitleaks", findings=0, release_allowed=False)

    monkeypatch.setattr(app, "scan_secrets_with_gitleaks", fake_scan)
    monkeypatch.setattr(
        sys,
        "argv",
        ["longgate", "secrets", "scan", ".", "--history"],
    )

    app.main()

    payload = json.loads(capsys.readouterr().out)
    assert captured == {"path": ".", "history": True}
    assert payload["engine"] == "gitleaks"
