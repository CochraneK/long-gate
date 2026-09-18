from pathlib import Path

import pytest

from longgate.semantic import (
    LocalLlamaCppTransformer,
    _completion_text,
    _safe_chunks,
    audit_semantic_preview,
    evaluate_semantic_release_evidence,
)


def test_semantic_preview_detects_direct_pii():
    audit = audit_semantic_preview(
        "The participant can be contacted later.",
        "Email person@example.com for details.",
    )
    assert audit.direct_pii_hits >= 1
    assert audit.release_allowed is False


def test_semantic_preview_detects_long_exact_reuse():
    source = (
        "This is a deliberately long sentence about a participant "
        "and their experience in a highly specific research setting."
    )
    audit = audit_semantic_preview(
        source,
        source,
        character_ngram_size=16,
    )
    assert (
        audit.character_ngram_reuse_rate
        > 0.9
    )
    assert audit.release_allowed is False


def test_semantic_preview_detects_reused_numbers():
    audit = audit_semantic_preview(
        "The event occurred on 2026-09-16 and code 12345.",
        "An event occurred on 2026-09-16.",
    )
    assert audit.reused_number_tokens >= 1


def test_local_transformer_requires_existing_model(
    tmp_path: Path,
):
    with pytest.raises(FileNotFoundError):
        LocalLlamaCppTransformer(
            tmp_path / "missing.gguf"
        )



def test_semantic_release_evidence_can_only_qualify_manual_review():
    evidence = evaluate_semantic_release_evidence(
        direct_pii_hits=0,
        reused_number_tokens=0,
        character_ngram_reuse_rate=0.0,
        distinctive_token_reuse_rate=0.0,
        transformed_characters=200,
    )
    assert evidence.eligible_for_manual_review is True
    assert evidence.manual_review_required is True
    assert evidence.automatic_release_allowed is False


def test_semantic_release_evidence_fails_on_short_or_reused_output():
    evidence = evaluate_semantic_release_evidence(
        direct_pii_hits=1,
        reused_number_tokens=1,
        character_ngram_reuse_rate=0.2,
        distinctive_token_reuse_rate=0.5,
        transformed_characters=20,
    )
    assert evidence.eligible_for_manual_review is False
    assert evidence.automatic_release_allowed is False
    assert set(evidence.failed_conditions) == {
        "direct_pii_detected",
        "source_number_reuse",
        "character_ngram_reuse",
        "distinctive_token_reuse",
        "output_too_short",
    }


def test_semantic_preview_detects_distinctive_long_token_reuse():
    source = (
        "The participant described HyperSpecificVillageName during "
        "an otherwise ordinary interview about daily routines."
    )
    transformed = (
        "HyperSpecificVillageName appeared in the account while the "
        "rest of the narrative was generalized into ordinary routines."
    )
    audit = audit_semantic_preview(
        source,
        transformed,
        character_ngram_size=16,
    )
    assert audit.reused_distinctive_tokens >= 1
    assert audit.distinctive_token_reuse_rate > 0
    assert audit.release_allowed is False


def test_safe_chunks_respects_paragraph_boundaries():
    chunks = _safe_chunks("a" * 4000 + "\n" + "b" * 4000, 5000)

    assert len(chunks) == 2
    assert all(len(chunk) <= 5000 for chunk in chunks)


def test_completion_text_rejects_truncation():
    with pytest.raises(RuntimeError, match="truncated"):
        _completion_text(
            {
                "choices": [
                    {
                        "text": "partial result",
                        "finish_reason": "length",
                    }
                ]
            }
        )


def test_completion_text_accepts_stopped_completion():
    assert (
        _completion_text(
            {
                "choices": [
                    {
                        "text": "  generalized result  ",
                        "finish_reason": "stop",
                    }
                ]
            }
        )
        == "generalized result"
    )
