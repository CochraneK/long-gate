from pathlib import Path

from longgate.deidentify import deidentify_local


class _ProgressiveTransformer:
    def __init__(self, _model_path):
        self.model_path = Path("/models/fake.gguf")
        self.calls = 0

    def transform(self, _text: str, max_tokens: int = 512) -> str:
        assert max_tokens == 512
        self.calls += 1
        if self.calls == 1:
            return (
                "The participant described HyperSpecificVillageName and the event "
                "on 2026-09-16 in a highly specific setting that still resembles "
                "the original account and therefore requires another privacy pass."
            )
        return (
            "An adult described a past personal experience in a generalized institutional "
            "context. Specific timing, organizations, locations, identifiers, and unusual "
            "role combinations were intentionally abstracted while preserving only the "
            "broad topic needed for later interpretation."
        )


class _AlwaysRiskyTransformer:
    def __init__(self, _model_path):
        self.model_path = Path("/models/fake.gguf")

    def transform(self, text: str, max_tokens: int = 512) -> str:
        return text


def test_deidentify_retries_until_manual_review_candidate(monkeypatch, tmp_path: Path):
    source = tmp_path / "interview.txt"
    source.write_text(
        "The participant from HyperSpecificVillageName reported an event on 2026-09-16. "
        "Contact person@example.com for a deliberately distinctive follow-up narrative.",
        encoding="utf-8",
    )
    output = tmp_path / "deidentified.txt"
    monkeypatch.setattr(
        "longgate.deidentify.LocalLlamaCppTransformer",
        _ProgressiveTransformer,
    )

    result = deidentify_local(source, "auto", output, max_rounds=3)

    assert result.status == "MANUAL_REVIEW_CANDIDATE"
    assert result.attempts == 2
    assert result.eligible_for_manual_review is True
    assert result.release_allowed is False
    assert Path(result.audit_path).is_file()
    assert Path(result.report_path).is_file()

    report = Path(result.report_path).read_text(encoding="utf-8")
    assert "person@example.com" not in report
    assert "Specific timing, organizations" not in report
    assert "never grants network egress automatically" in report


def test_deidentify_stays_local_only_when_bounded_retries_fail(monkeypatch, tmp_path: Path):
    source = tmp_path / "interview.txt"
    source.write_text(
        "This deliberately distinctive interview narrative contains a long unique phrase "
        "about a participant and their unusually specific experience in one local setting.",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "longgate.deidentify.LocalLlamaCppTransformer",
        _AlwaysRiskyTransformer,
    )

    result = deidentify_local(
        source,
        "auto",
        tmp_path / "out.txt",
        max_rounds=2,
    )

    assert result.status == "LOCAL_ONLY"
    assert result.attempts == 2
    assert result.eligible_for_manual_review is False
    assert result.automatic_release_allowed is False
    assert result.release_allowed is False
    assert any("failed_conditions" in action for action in result.next_actions)


def test_deidentify_rejects_unbounded_round_count(tmp_path: Path):
    source = tmp_path / "interview.txt"
    source.write_text("Some private text.", encoding="utf-8")

    try:
        deidentify_local(source, "auto", tmp_path / "out.txt", max_rounds=4)
    except ValueError as exc:
        assert "between 1 and 3" in str(exc)
    else:
        raise AssertionError("Expected bounded remediation validation to fail")
